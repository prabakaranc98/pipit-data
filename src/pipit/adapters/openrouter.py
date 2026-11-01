"""OpenRouter chat completions as a lab model. The response carries the cost when usage accounting is
requested, and the provider that served the call, which varies per call and is recorded. Empty content counts
as a failure: reasoning models return it when the token budget is spent on reasoning, and it is never cached.

A refused key stops at once: retrying cannot raise a spending limit or fix a wrong key. Each call has one
time limit across all its attempts, `settings.deadline_s` in the manifest (600 seconds unless set), because
OpenRouter keeps a slow connection alive with padding and the socket's own timeout never fires. A reply that
stalls uses up the call's whole time, so it is not tried again. When waiting between attempts after an error
uses up the time instead, the call ends with TooSlow, raised from the last error and naming it."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from pipit.cache import JsonlCache, request_key
from pipit.env import require_key
from pipit.manifest import Context, Manifest

URL = "https://openrouter.ai/api/v1/chat/completions"
Transport = Callable[[dict[str, Any], dict[str, str]], dict[str, Any]]


class EmptyContent(RuntimeError):
    pass


class KeyRefused(RuntimeError):
    """The API refused the key: HTTP 401 for a wrong key, 402 or 403 usually for a spending limit reached."""


class TooSlow(TimeoutError):
    """No complete reply within the time limit per call."""


def _read_within(response: Any, deadline_s: float, clock: Callable[[], float] = time.monotonic) -> bytes:
    """Read a whole reply, giving up once `deadline_s` seconds have passed since reading began."""
    start, chunks = clock(), []
    while True:
        if clock() - start > deadline_s:
            raise TooSlow(f"no complete reply within {deadline_s:.0f} s")
        chunk = response.read1(65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _urllib_transport(
    body: dict[str, Any], headers: dict[str, str], deadline_s: float = 600.0
) -> dict[str, Any]:
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(), headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=min(120.0, deadline_s)) as r:
        return json.loads(_read_within(r, deadline_s))


def _get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
        return json.load(r)


def budget_left(
    key_env: str = "OPENROUTER_API_KEY", fetch: Callable[[str, dict[str, str]], dict[str, Any]] | None = None
) -> float | None:
    """Dollars left on an OpenRouter key, or None when the key has no spending limit."""
    headers = {"Authorization": f"Bearer {require_key(key_env)}"}
    return (
        (fetch or _get_json)("https://openrouter.ai/api/v1/key", headers)
        .get("data", {})
        .get("limit_remaining")
    )


class OpenRouterChat:
    def __init__(self, manifest: Manifest, context: Context, transport: Transport | None = None):
        self.manifest = manifest
        self.context = context
        self.deadline_s = float(manifest.settings.get("deadline_s", 600))
        self._transport = transport
        self.cache = JsonlCache(context.cache_dir / f"{manifest.name}.jsonl")
        self.calls = 0
        self._key: str | None = None

    def _headers(self) -> dict[str, str]:
        if self._key is None:
            self._key = require_key(self.manifest.key_env or "OPENROUTER_API_KEY")
        return {"Authorization": f"Bearer {self._key}"}

    def _send(self, body: dict[str, Any], seconds_left: float) -> dict[str, Any]:
        if self._transport is not None:
            return self._transport(body, self._headers())
        return _urllib_transport(body, self._headers(), seconds_left)

    @staticmethod
    def _content(response: dict[str, Any]) -> str:
        choices = response.get("choices") or []
        return ((choices[0].get("message") or {}).get("content") or "") if choices else ""

    def __call__(
        self,
        prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 600,
        role: str = "lab",
        retries: int = 4,
        meta: dict[str, Any] | None = None,
        system: str | None = None,
    ) -> dict[str, Any]:
        messages = [{"role": "user", "content": prompt}]
        if system is not None:
            messages.insert(0, {"role": "system", "content": system})
        body = {
            "model": self.manifest.id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "usage": {"include": True},
            **self.manifest.settings.get("request", {}),
        }
        key = request_key(body)
        hit = self.cache.get(key)
        if hit is not None and self._content(hit).strip():
            u = hit.get("usage") or {}
            self.context.ledger.record(
                role,
                provider_api="openrouter",
                model_asked=self.manifest.id,
                model_answered=hit.get("model"),
                provider=hit.get("provider"),
                cached=True,
                tokens_in=u.get("prompt_tokens"),
                tokens_out=u.get("completion_tokens"),
                usd=None,
                seconds=0.0,
                **(meta or {}),
            )
            return self._result(hit, cached=True)
        if hit is not None:
            self.cache.drop(key)
        if self.context.max_calls is not None and self.calls >= self.context.max_calls:
            raise RuntimeError(f"{self.manifest.name}: call ceiling {self.context.max_calls} reached")
        self.calls += 1
        delay = 2.0
        response: dict[str, Any] | None = None
        last_error: Exception | None = None  # named if the time runs out, so the record keeps it
        attempts = 0
        t0 = time.perf_counter()
        for attempt in range(retries):
            attempts = attempt + 1
            left = self.deadline_s - (time.perf_counter() - t0)
            if left <= 0:
                message = f"{self.manifest.id}: no complete reply within {self.deadline_s:.0f} s"
                if last_error is not None:
                    message += f"; the last error was {type(last_error).__name__}: {last_error}"
                raise TooSlow(message) from last_error
            try:
                response = self._send(body, left)
                if "error" in response:
                    raise urllib.error.HTTPError(
                        URL, int(response["error"].get("code", 500)), str(response["error"]), {}, None
                    )  # type: ignore[arg-type]
                if not self._content(response).strip():
                    finish = (response.get("choices") or [{}])[0].get("finish_reason")
                    raise EmptyContent(f"{self.manifest.id} returned empty content (finish_reason={finish})")
                break
            except EmptyContent as e:
                if attempt == retries - 1:
                    raise
                last_error = e
            except urllib.error.HTTPError as e:
                if e.code in (401, 402, 403):
                    why = "the key was rejected" if e.code == 401 else "its spending limit may be reached"
                    raise KeyRefused(
                        f"{self.manifest.id}: the API refused the key (HTTP {e.code}); {why}"
                    ) from e
                if attempt == retries - 1:
                    raise
                last_error = e
                time.sleep(min(delay, max(0.0, self.deadline_s - (time.perf_counter() - t0))))
                delay *= 2
            except TooSlow:
                # The real transport raises this only once the call's time is spent, so the next pass stops.
                if attempt == retries - 1:
                    raise
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt == retries - 1:
                    raise
                last_error = e
                time.sleep(min(delay, max(0.0, self.deadline_s - (time.perf_counter() - t0))))
                delay *= 2
        assert response is not None
        seconds = time.perf_counter() - t0
        usage = response.get("usage") or {}
        self.cache.put(key, response)
        self.context.ledger.record(
            role,
            provider_api="openrouter",
            model_asked=self.manifest.id,
            model_answered=response.get("model"),
            provider=response.get("provider"),
            request_id=response.get("id"),
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
            usd=usage.get("cost"),
            seconds=round(seconds, 3),
            attempts=attempts,
            finish_reason=(response.get("choices") or [{}])[0].get("finish_reason"),
            **(meta or {}),
        )
        return self._result(response, cached=False)

    def _result(self, response: dict[str, Any], cached: bool) -> dict[str, Any]:
        choice = (response.get("choices") or [{}])[0]
        return {
            "text": self._content(response),
            "cached": cached,
            "finish_reason": choice.get("finish_reason"),
            "provider": response.get("provider"),
            "model": response.get("model"),
        }


def load(manifest: Manifest, context: Context) -> OpenRouterChat:
    return OpenRouterChat(manifest, context)
