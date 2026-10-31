"""TypeSafe's Jev through its SDK, as a typed-question subject. Both questions of a case travel in one
request, the
SDK's documented usage. The response names the model that answered; the alias asked for is only an alias."""

from __future__ import annotations

import json
import time
from typing import Any

from pipit.cache import JsonlCache, request_key
from pipit.env import require_key
from pipit.manifest import Context, Manifest


class JevSubject:
    def __init__(self, manifest: Manifest, context: Context):
        from typesafe_sdk import TypeSafeClient  # the SDK appears here and nowhere else

        self.manifest = manifest
        self.context = context
        self.client = TypeSafeClient(
            api_key=require_key(manifest.key_env or "TYPESAFE_API_KEY"),
            timeout=float(manifest.settings.get("timeout", 60.0)),
        )
        self.cache = JsonlCache(context.cache_dir / f"{manifest.name}.jsonl")
        self.calls = 0
        self.last_model: str | None = None

    def answered_by(self) -> str:
        """The model name the last response reported; the manifest's revision is only an alias."""
        return self.last_model or self.manifest.revision

    def _sdk_questions(self, questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        from typesafe_sdk import Choice, Noul

        out = {}
        for qid, q in questions.items():
            if q["type"] == "noul":
                out[qid] = Noul(instructions=q.get("instructions"))
            elif q["type"] == "choice":
                out[qid] = Choice(instructions=q.get("instructions"), criteria=q["criteria"])
            else:
                raise ValueError(f"unsupported question type {q['type']!r}")
        return out

    def __call__(
        self,
        state: Any,
        questions: dict[str, dict[str, Any]],
        role: str = "reference",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        wire = {"model": self.manifest.revision, "state": state, "questions": questions}
        key = request_key(wire)
        hit = self.cache.get(key)
        if hit is not None:
            self.last_model = hit.get("model")
            u = hit.get("usage") or {}
            self.context.ledger.record(
                role,
                provider_api="typesafe",
                model_asked=self.manifest.revision,
                model_answered=hit.get("model"),
                cached=True,
                tokens_in=u.get("input_tokens"),
                tokens_out=u.get("output_tokens"),
                usd=None,
                seconds=0.0,
                **(meta or {}),
            )
            return hit["answers"]
        if self.context.max_calls is not None and self.calls >= self.context.max_calls:
            raise RuntimeError(f"{self.manifest.name}: call ceiling {self.context.max_calls} reached")
        self.calls += 1
        t0 = time.perf_counter()
        r = self.client.system_one(
            state=state, questions=self._sdk_questions(questions), model=self.manifest.revision
        )
        seconds = time.perf_counter() - t0
        d = json.loads(r.model_dump_json())
        d["request_id"] = getattr(r, "request_id", None)
        usage = d.get("usage") or {}
        usd = None
        if (
            self.manifest.price_usd_per_million_in is not None
            and self.manifest.price_usd_per_million_out is not None
        ):
            usd = (
                usage.get("input_tokens", 0) * self.manifest.price_usd_per_million_in / 1e6
                + usage.get("output_tokens", 0) * self.manifest.price_usd_per_million_out / 1e6
            )
        self.last_model = d.get("model")
        self.cache.put(key, d)
        self.context.ledger.record(
            role,
            provider_api="typesafe",
            model_asked=self.manifest.revision,
            model_answered=d.get("model"),
            request_id=d["request_id"],
            tokens_in=usage.get("input_tokens"),
            tokens_out=usage.get("output_tokens"),
            usd=usd,
            seconds=round(seconds, 3),
            **(meta or {}),
        )
        return d["answers"]


def load(manifest: Manifest, context: Context) -> JevSubject:
    return JevSubject(manifest, context)
