"""Typed questions and answers: the contract between a case and a subject.

A subject is called with a state and a mapping of question id to question, and returns a mapping of question
id
to answer. Two question types are enough for the first studies: a `noul` (a yes/no probability) and a `choice`
(one option among named criteria). The wire shape is the one typed decision models already speak.
"""

from __future__ import annotations

from typing import Any

Question = dict[str, Any]
Answer = dict[str, Any]


def noul(instructions: str) -> Question:
    return {"type": "noul", "instructions": instructions}


def choice(instructions: str, criteria: dict[str, str | None]) -> Question:
    if len(criteria) < 2:
        raise ValueError("a choice needs at least two criteria")
    return {"type": "choice", "instructions": instructions, "criteria": dict(criteria)}


def validate_question(question: Question) -> None:
    kind = question.get("type")
    if kind == "noul":
        return
    if kind == "choice":
        criteria = question.get("criteria")
        if not isinstance(criteria, dict) or len(criteria) < 2:
            raise ValueError("a choice question needs a criteria mapping with at least two options")
        return
    raise ValueError(f"unknown question type {kind!r}")


def chosen(answer: Answer) -> str | None:
    """The option a choice answer picked, or None."""
    return answer.get("choice")


def p_true(answer: Answer) -> float | None:
    """The probability a noul answer gives to yes, or None."""
    value = answer.get("noul")
    return None if value is None else float(value)


def probabilities(answer: Answer) -> dict[str, float] | None:
    """Per-option probabilities of a choice answer when the subject reports them."""
    probs = answer.get("probabilities") or answer.get("scores")
    return {k: float(v) for k, v in probs.items()} if isinstance(probs, dict) else None
