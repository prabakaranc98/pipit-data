"""MedCalc-Bench v1.2 for study V1: the stratified sample, the paper's zero-shot chain-of-thought prompt, and
scoring written from the dataset card's rules. The data is CC BY-SA 4.0 and is downloaded at run time."""

from __future__ import annotations

import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
SAMPLE = HERE / "sample_rows.json"
PER_CALCULATOR = 4

# The paper's zero-shot chain-of-thought prompt (Khandekar et al., 2024, MedCalc-Bench, evaluation/run.py), quoted
# exactly so the result is comparable.
SYSTEM = (
    "You are a helpful assistant for calculating a score for a given patient note. Please think step-by-step to "
    "solve the question and then generate the required score. Your output should only contain a JSON dict formatted "
    'as {"step_by_step_thinking": str(your_step_by_step_thinking_procress_to_solve_the_question), "answer": '
    "str(short_and_direct_answer_of_the_question)}."
)


def user(note: str, question: str) -> str:
    return (
        f"Here is the patient note:\n{note}\n\nHere is the task:\n{question}\n\nPlease directly output the JSON dict "
        'formatted as {"step_by_step_thinking": str(your_step_by_step_thinking_procress_to_solve_the_question), '
        '"answer": str(short_and_direct_answer_of_the_question)}:'
    )


def test_rows() -> list[dict[str, Any]]:
    from huggingface_hub import hf_hub_download

    path = hf_hub_download("ncbi/MedCalc-Bench-v1.2", "test_data_11_18_final.csv", repo_type="dataset")
    return list(csv.DictReader(open(path, newline="")))


def sample(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Four items per calculator, drawn with a fixed seed; the row numbers are kept in sample_rows.json."""
    if SAMPLE.exists():
        keep = set(json.loads(SAMPLE.read_text()))
        return [r for r in rows if r["Row Number"] in keep]
    by_calc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_calc[r["Calculator ID"]].append(r)
    rng = random.Random("pipit-v1")
    picked = [r for calc in sorted(by_calc, key=int) for r in rng.sample(by_calc[calc], PER_CALCULATOR)]
    SAMPLE.write_text(json.dumps(sorted((r["Row Number"] for r in picked), key=int)))
    return picked


def answer(reply: str) -> str | None:
    """The value of the reply's "answer" field."""
    text = re.sub(r"^```(?:json)?|```$", "", reply.strip(), flags=re.MULTILINE).strip()
    try:
        value = json.loads(text).get("answer")
        return None if value is None else str(value)
    except (ValueError, AttributeError):
        found = re.findall(r'"[Aa]nswer"\s*:\s*"?([^"}\n]+)"?', reply)
        return found[-1].strip() if found else None


def _number(text: str) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(m.group()) if m else None


def _date(text: str) -> str | None:
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    return f"{int(m.group(1)):02}/{int(m.group(2)):02}/{m.group(3)}" if m else None


def correct(row: dict[str, Any], reply_answer: str | None) -> bool:
    """The card's rules: decimals within the lower and upper limits, integers and dates exact."""
    if reply_answer is None:
        return False
    kind = row["Output Type"]
    if kind == "date":
        return _date(reply_answer) == _date(row["Ground Truth Answer"])
    value = _number(reply_answer)
    if value is None:
        return False
    if kind == "integer":
        return round(value) == round(float(row["Ground Truth Answer"]))
    return float(row["Lower Limit"]) <= value <= float(row["Upper Limit"])
