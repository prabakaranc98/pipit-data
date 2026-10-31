"""OpenRouter chat completions as a lab model. The response carries the cost when usage accounting is
requested,
and the provider that served the call, which varies per call and is recorded. Empty content counts as a
failure:
reasoning models return it when the token budget is spent on reasoning, and it is never cached."""

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


def _urllib_transport(body: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(), headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


class OpenRouterChat:
    def __init__(self, manifest: Manifest, context: Context, transport: Transport | None = None):
        self.manifest = manifest
        self.context = context
        self.transport = transport or _urllib_transport
        self.cache = JsonlCache(context.cache_dir / f"{manifest.name}.jsonl")
        self.calls = 0
        self._key: str | None = None

    def _headers(self) -> dict[str, str]:
        if self._key is None:
            self._key = require_key(self.manifest.key_env or "OPENROUTER_API_KEY")
        return {"Authorization": f"Bearer {self._key}"}

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
    ) -> dict[str, Any]:
        body = {
            "model": self.manifest.id,
            "messages": [{"role": "user", "content": prompt}],
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
        attempts = 0
        t0 = time.perf_counter()
        for attempt in range(retries):
            attempts = attempt + 1
            try:
                response = self.transport(body, self._headers())
                if "error" in response:
                    raise urllib.error.HTTPError(
                        URL, int(response["error"].get("code", 500)), str(response["error"]), {}, None
                    )  # type: ignore[arg-type]
                if not self._content(response).strip():
                    finish = (response.get("choices") or [{}])[0].get("finish_reason")
                    raise EmptyContent(f"{self.manifest.id} returned empty content (finish_reason={finish})")
                break
            except EmptyContent:
                if attempt == retries - 1:
                    raise
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
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
