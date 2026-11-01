"""Shared pieces for I1: P1's cases, the prompt P1's adapter sent, and Qwen3.5-4B in PyTorch with its layers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "p1_clinical"))
# P1's study module: its cases, adjudication and option sets.
import study as p1  # noqa: E402

from pipit.adapters.openai_compat import LETTERS, render  # noqa: E402
from pipit.questions import choice  # noqa: E402

SNAPSHOT = (
    Path.home()
    / ".cache/huggingface/hub/models--Qwen--Qwen3.5-4B/snapshots/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
)


def cases(conditions: tuple[str, ...] = ("critical", "benign")) -> list[dict[str, Any]]:
    all_cases = p1.adjudicated(p1.load_cases())
    return [c for _, c in sorted(all_cases.items()) if c["eligible"] and c["condition"] in conditions]


def prompt_and_names(case: dict[str, Any]) -> tuple[str, list[str]]:
    return render(case["note"], choice(case["decision"], case["criteria"]))


def load_model():
    import torch
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(SNAPSHOT)
    try:
        from transformers import AutoModelForCausalLM

        model = AutoModelForCausalLM.from_pretrained(SNAPSHOT, dtype=torch.bfloat16)
    except (ValueError, KeyError):
        from transformers import AutoModelForImageTextToText

        model = AutoModelForImageTextToText.from_pretrained(SNAPSHOT, dtype=torch.bfloat16)
    model = model.to("mps").eval()
    return tok, model


def layers(model) -> Any:
    """The decoder layers: the first module list as long as the model has hidden layers."""
    import torch

    n = getattr(model.config, "text_config", model.config).num_hidden_layers
    for _, module in model.named_modules():
        if isinstance(module, torch.nn.ModuleList) and len(module) == n:
            return module
    raise RuntimeError("decoder layers not found")


def encode(tok, text: str):
    ids = tok.apply_chat_template(
        [{"role": "user", "content": text}],
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
    )
    import torch

    return ids if torch.is_tensor(ids) else ids["input_ids"]


def letter_ids(tok, n: int) -> list[int]:
    return [tok.convert_tokens_to_ids(LETTERS[i]) for i in range(n)]
