"""Any LLM behind an OpenAI-style endpoint, answering Pipit's typed questions.

MLX's server on Apple silicon, vLLM, SGLang, llama.cpp, Ollama and OpenRouter speak the same interface. Each
typed question is asked on its own as a multiple-choice prompt, in one of two modes, set by the manifest:

- **first_token** (instruct mode): one answer token; the option probabilities are read from its
  log-probabilities, renormalised over the option letters, and the share on the letters is recorded.
- **after_reasoning** (thinking mode): the model reasons within a token budget at the sampling settings its
  card recommends; the answer is read after the reasoning. A reasoned answer is always certain, so each
  question is sampled several times in parallel. Each option's probability is its share of all samples,
  so a sample cut off at the token budget counts against confidence. The answer is the most common one; an
  exact tie gives no answer.

With `settings.launch`, the adapter starts a local server for the manifest and stops it at exit.
"""

from __future__ import annotations

import atexit
import importlib.metadata
import json
import math
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from pipit.cache import JsonlCache, request_key
from pipit.manifest import Context, Manifest

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
Transport = Callable[[str, dict[str, Any], dict[str, str]], dict[str, Any]]


def render(state: Any, question: dict[str, Any]) -> tuple[str, list[str]]:
    """The prompt for one typed question, and the option names in letter order."""
    text = state if isinstance(state, str) else json.dumps(state, ensure_ascii=False)
    instructions = question.get("instructions") or "Choose the best matching option."
    if question["type"] == "noul":
        names, labels = ["yes", "no"], ["Yes", "No"]
        ask = (
            instructions if instructions.rstrip().endswith("?") else f"Is this statement true? {instructions}"
        )
    elif question["type"] == "choice":
        names = list(question["criteria"])
        labels = [question["criteria"][k] or k for k in names]
        ask = instructions
    else:
        raise ValueError(f"unsupported question type {question['type']!r}")
    if len(names) > len(LETTERS):
        raise ValueError("too many options for single-letter answers")
    lines = [text, "", f"Question: {ask}", "Options:"]
    lines += [f"{LETTERS[i]}. {label}" for i, label in enumerate(labels)]
    lines.append("Answer with the letter only.")
    return "\n".join(lines), names


def option_probabilities(
    top_logprobs: list[dict[str, Any]], names: list[str]
) -> tuple[dict[str, float], float]:
    """Probabilities for every option from the first token's top log-probabilities, renormalised over the
    option letters (an option missing from the top list gets 0), and the share of the token's probability that
    fell on the letters."""
    letters = LETTERS[: len(names)]
    mass: dict[str, float] = {}
    for item in top_logprobs:
        token = (item.get("token") or "").strip()
        if token in letters:
            mass[token] = mass.get(token, 0.0) + math.exp(item["logprob"])
    total = sum(mass.values())
    if total == 0:
        return {}, 0.0
    return {name: mass.get(letters[i], 0.0) / total for i, name in enumerate(names)}, min(total, 1.0)


def reasoned_letter(
    response: dict[str, Any], names: list[str], reasoning_end: str = "</think>"
) -> str | None:
    """The option a reasoning model chose: the first standalone option letter of its final answer. Servers
    that split the reasoning out (MLX, and vLLM or SGLang with a reasoning parser) return the answer alone;
    otherwise the text after the end-of-reasoning marker is read. Reasoning that opens and never closes
    was cut off, so it gives no answer. A capital letter used as a word, such as the article "A", can still
    be misread."""
    first = (response.get("choices") or [{}])[0]
    text = (first.get("message") or {}).get("content") or ""
    if reasoning_end and reasoning_end in text:
        text = text.split(reasoning_end)[-1]
    elif reasoning_end.startswith("</") and reasoning_end.replace("/", "", 1) in text:
        return None
    allowed = LETTERS[: len(names)]
    for match in re.finditer(r"(?<![A-Za-z])([A-Z])(?![A-Za-z])", text):
        if match.group(1) in allowed:
            return names[allowed.index(match.group(1))]
    return None


def _urllib_transport(
    url: str, body: dict[str, Any], headers: dict[str, str], timeout: float = 180.0
) -> dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


class LLMSubject:
    def __init__(self, manifest: Manifest, context: Context, transport: Transport | None = None):
        self.manifest = manifest
        self.context = context
        s = manifest.settings
        self.base_url = str(s.get("base_url", "http://127.0.0.1:8080/v1")).rstrip("/")
        self.engine = str(s.get("engine", "openai-compatible"))
        try:
            self.engine_version = importlib.metadata.version(self.engine)
        except importlib.metadata.PackageNotFoundError:
            self.engine_version = None
        self.top_logprobs = int(s.get("top_logprobs", 10))
        self.extra = dict(s.get("request", {}))
        self.mode = str(s.get("answer", "first_token"))
        if self.mode not in ("first_token", "after_reasoning"):
            raise ValueError(f"{manifest.name}: settings.answer must be first_token or after_reasoning")
        self.max_tokens = int(s.get("max_tokens", 1 if self.mode == "first_token" else 8192))
        self.reasoning_end = str(s.get("reasoning_end", "</think>"))
        self.samples = int(s.get("samples", 1))
        self.concurrency = int(s.get("concurrency", self.samples))
        self.sampling = dict(s.get("sampling", {}))
        self._lock = threading.Lock()
        timeout = float(s.get("timeout", 180))  # seconds per request; reasoning shares the GPU, so allow long
        self.transport = transport or (
            lambda url, body, headers: _urllib_transport(url, body, headers, timeout)
        )
        self.cache = JsonlCache(context.cache_dir / f"{manifest.name}.jsonl")
        self.calls = 0
        self._server: subprocess.Popen | None = None
        self.served_model = self._expand(s["served_model"]) if s.get("served_model") else None
        if s.get("launch") and transport is None:
            self._launch([self._expand(a) for a in s["launch"]], float(s.get("launch_timeout", 300)))

    def answered_by(self) -> str:
        engine = f"{self.engine} {self.engine_version}" if self.engine_version else self.engine
        mode = f", thinking, {self.samples} samples" if self.mode == "after_reasoning" else ""
        return f"{self.manifest.id}@{self.manifest.revision[:8]} {self.manifest.dtype} {engine}{mode}"

    def _expand(self, value: str) -> str:
        if value == "{python}":
            return sys.executable
        if "{snapshot}" in value:
            from huggingface_hub import snapshot_download  # only for local weights

            patterns = self.manifest.settings.get(
                "snapshot_patterns"
            )  # the files the weights need, as downloaded
            path = snapshot_download(
                self.manifest.id,
                revision=self.manifest.revision,
                local_files_only=True,
                allow_patterns=patterns,
            )
            value = value.replace("{snapshot}", path)
        return value

    def _up(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.base_url}/models", timeout=2).read()
            return True
        except (urllib.error.URLError, OSError):
            return False

    def _launch(self, cmd: list[str], timeout: float) -> None:
        if self._up():
            return
        log_path = self.context.cache_dir / f"{self.manifest.name}.server.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()
        self._server = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=log_path.open("w"))
        atexit.register(self.close)
        while not self._up():
            if self._server.poll() is not None:
                raise RuntimeError(f"{self.manifest.name}: server exited; see {log_path}")
            if time.perf_counter() - t0 > timeout:
                self.close()
                raise RuntimeError(
                    f"{self.manifest.name}: server not ready after {timeout:.0f} s; see {log_path}"
                )
            time.sleep(1.0)
        self.context.ledger.record(
            "candidate_load",
            provider_api=self.engine,
            model_asked=self.manifest.id,
            model_answered=self.answered_by(),
            requests=0,
            usd=0.0,
            seconds=round(time.perf_counter() - t0, 1),
        )

    def close(self) -> None:
        if self._server is not None and self._server.poll() is None:
            self._server.terminate()
            try:
                self._server.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self._server.kill()
        self._server = None

    def _headers(self) -> dict[str, str]:
        name = self.manifest.key_env
        return {"Authorization": f"Bearer {os.environ[name]}"} if name and os.environ.get(name) else {}

    def _usd(self, usage: dict[str, Any]) -> float | None:
        if usage.get("cost") is not None:
            return float(usage["cost"])
        m = self.manifest
        if m.price_usd_per_million_in is not None and m.price_usd_per_million_out is not None:
            return (usage.get("prompt_tokens") or 0) * m.price_usd_per_million_in / 1e6 + (
                usage.get("completion_tokens") or 0
            ) * m.price_usd_per_million_out / 1e6
        return 0.0 if m.placement == "local" else None

    def _key(self, body: dict[str, Any], sample: int | None = None) -> str:
        identity = {
            "id": self.manifest.id,
            "revision": self.manifest.revision,
            "dtype": self.manifest.dtype,
            "engine": self.engine,
            "body": body,
        }
        return request_key(identity if sample is None else {**identity, "sample": sample})

    def _fetch(self, key: str, body: dict[str, Any]) -> tuple[dict[str, Any], bool, float]:
        with self._lock:
            hit = self.cache.get(key)
            if hit is None:
                if self.context.max_calls is not None and self.calls >= self.context.max_calls:
                    raise RuntimeError(f"{self.manifest.name}: call ceiling {self.context.max_calls} reached")
                self.calls += 1
        if hit is not None:
            return hit, True, 0.0
        t0 = time.perf_counter()
        response = self.transport(f"{self.base_url}/chat/completions", body, self._headers())
        seconds = time.perf_counter() - t0
        with self._lock:
            self.cache.put(key, response)
        return response, False, seconds

    def _record(
        self,
        role: str,
        response: dict[str, Any],
        cached: bool,
        seconds: float,
        meta: dict[str, Any] | None,
        **extra: Any,
    ) -> None:
        usage = response.get("usage") or {}
        with self._lock:
            self.context.ledger.record(
                role,
                provider_api=self.engine,
                model_asked=self.manifest.id,
                model_answered=self.answered_by(),
                cached=cached,
                tokens_in=usage.get("prompt_tokens"),
                tokens_out=usage.get("completion_tokens"),
                usd=0.0 if cached else self._usd(usage),
                seconds=round(seconds, 3),
                **extra,
                **(meta or {}),
            )

    def _first_token(
        self, prompt: str, names: list[str], question: dict[str, Any], role: str, meta: dict[str, Any] | None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1,
            "temperature": 0.0,
            "logprobs": True,
            "top_logprobs": self.top_logprobs,
            **self.extra,
        }
        key = self._key(body)
        if self.served_model:
            body["model"] = self.served_model
        response, cached, seconds = self._fetch(key, body)
        first = (response.get("choices") or [{}])[0]
        content = (first.get("logprobs") or {}).get("content") or []
        tops = content[0].get("top_logprobs", []) if content else []
        probs, mass = option_probabilities(tops, names)
        self._record(role, response, cached, seconds, meta, letter_mass=round(mass, 4))
        if question["type"] == "noul":
            return {
                "type": "noul",
                "noul": probs.get("yes") if probs else None,
                "letter_mass": round(mass, 4),
            }
        best = max(probs, key=probs.get) if probs else None
        return {
            "type": "choice",
            "choice": best,
            "probabilities": probs or None,
            "letter_mass": round(mass, 4),
        }

    def _after_reasoning(
        self, prompt: str, names: list[str], question: dict[str, Any], role: str, meta: dict[str, Any] | None
    ) -> dict[str, Any]:
        def one(i: int) -> str | None:
            body: dict[str, Any] = {
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens,
                "logprobs": False,
                **self.sampling,
                **self.extra,
            }
            key = self._key(body, sample=i)
            if self.served_model:
                body["model"] = self.served_model
            response, cached, seconds = self._fetch(key, body)
            option = reasoned_letter(response, names, self.reasoning_end)
            finish = (response.get("choices") or [{}])[0].get("finish_reason")
            self._record(role, response, cached, seconds, meta, sample=i, answer=option, finish_reason=finish)
            return option

        with ThreadPoolExecutor(max_workers=max(1, self.concurrency)) as pool:
            options = list(pool.map(one, range(self.samples)))
        votes = Counter(o for o in options if o is not None)
        answered = sum(votes.values())
        probs = {n: votes.get(n, 0) / self.samples for n in names} if answered else None
        top = max(probs.values()) if probs else None
        tie = probs is not None and sum(v == top for v in probs.values()) > 1
        detail = {
            "samples": self.samples,
            "answered": answered,
            "agreement": round(top, 4) if top else None,
            "tie": tie,
        }
        if question["type"] == "noul":
            return {"type": "noul", "noul": probs["yes"] if probs else None, **detail}
        best = None if (probs is None or tie) else max(probs, key=probs.get)
        return {"type": "choice", "choice": best, "probabilities": probs, **detail}

    def __call__(
        self,
        state: Any,
        questions: dict[str, dict[str, Any]],
        role: str = "candidate",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        ask = self._after_reasoning if self.mode == "after_reasoning" else self._first_token
        answers: dict[str, dict[str, Any]] = {}
        for qid, question in questions.items():
            prompt, names = render(state, question)
            answers[qid] = ask(prompt, names, question, role, meta)
        return answers


def load(manifest: Manifest, context: Context) -> LLMSubject:
    return LLMSubject(manifest, context)
