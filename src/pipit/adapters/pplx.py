"""Perplexity's decider, run locally from a pinned snapshot with the package it ships. The model card
documents
CUDA and BF16; off CUDA the package loads FP32, so the backbone and readout are forced to the manifest's
dtype.
The card also says one question per request is more accurate, which the manifest's `one_question_per_request`
setting follows. The weights must already be in the local Hugging Face cache: nothing is fetched here."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from pipit.manifest import Context, Manifest


class PplxSubject:
    def __init__(self, manifest: Manifest, context: Context):
        import torch
        from huggingface_hub import snapshot_download

        self.manifest = manifest
        self.context = context
        t0 = time.perf_counter()
        root = Path(
            snapshot_download(
                manifest.id,
                revision=manifest.revision,
                local_files_only=True,
                ignore_patterns=["*.gguf", "*.onnx", "onnx/*"],
            )
        )
        sys.path.insert(0, str(root / "source" / "src"))
        import pplx_decider.model as pplx

        dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[
            manifest.dtype or "fp32"
        ]
        backbone = pplx.Qwen3_5Model

        class Patched:
            @staticmethod
            def from_pretrained(*args: Any, **kwargs: Any) -> Any:
                return backbone.from_pretrained(*args, **{**kwargs, "dtype": dtype})

        pplx.Qwen3_5Model = Patched
        try:
            self.model = pplx.Decider.from_pretrained(root, device=manifest.device or "cpu")
        finally:
            pplx.Qwen3_5Model = backbone
        self.model.readout.to(dtype)
        self.load_seconds = time.perf_counter() - t0
        self.one_per_request = bool(manifest.settings.get("one_question_per_request", True))
        self.temperature = float(self.model.temperature)
        self._torch = torch
        context.ledger.record(
            "candidate_load",
            provider_api="local",
            model_asked=manifest.id,
            model_answered=self.answered_by(),
            seconds=round(self.load_seconds, 1),
            usd=0.0,
            requests=0,
        )

    def answered_by(self) -> str:
        return f"{self.manifest.id}@{self.manifest.revision[:8]} {self.manifest.dtype} {self.manifest.device}"

    def __call__(
        self,
        state: Any,
        questions: dict[str, dict[str, Any]],
        role: str = "candidate",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        t0 = time.perf_counter()
        answers: dict[str, dict[str, Any]] = {}
        groups = [{k: v} for k, v in questions.items()] if self.one_per_request else [questions]
        for group in groups:
            answers.update(self.model.decide({"state": state, "questions": group})["answers"])
        seconds = time.perf_counter() - t0
        peak = None
        if self.manifest.device == "mps":
            peak = round(self._torch.mps.driver_allocated_memory() / 1e9, 2)
        self.context.ledger.record(
            role,
            provider_api="local",
            model_asked=self.manifest.id,
            model_answered=self.answered_by(),
            requests=len(groups),
            usd=0.0,
            seconds=round(seconds, 3),
            peak_gb=peak,
            **(meta or {}),
        )
        return answers


def load(manifest: Manifest, context: Context) -> PplxSubject:
    return PplxSubject(manifest, context)
