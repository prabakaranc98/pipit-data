"""I1, the Explain step: does the dose decision move when the record states the computed dose per kilogram, and
the usual dose? Usage: python studies/i1_interp/intervene.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent))
from common import HERE, cases, encode, letter_ids, load_model, p1, prompt_and_names  # noqa: E402

# Each dose scenario: weight in kg, dose in mg read from the plan, and the usual dose in mg/kg.
SCENARIOS = {"S1": (18, "paracetamol", 15.0), "S2": (68, "enoxaparin", 1.0)}


def dose_mg(note: str) -> float:
    plan = next(line for line in note.splitlines() if "mg" in line and "dose on the chart" in line)
    return float(plan.split(":")[-1].split("mg")[0].split()[-1])


def versions(case: dict, dose: float) -> dict[str, str]:
    """The original record and the two versions; `dose` comes from the case's wording-0 twin, since a rewording
    phrases the plan line differently but plants the same dose."""
    weight, drug, usual = SCENARIOS[case["scenario"]]
    per_kg = dose / weight
    computed = f"\nPharmacy calculation: the {drug} dose on the chart is {per_kg:.1f} mg/kg per dose."
    with_usual = computed + f" The usual dose is {usual:g} mg/kg per dose."
    return {
        "original": case["note"],
        "computed": case["note"] + computed,
        "computed and usual": case["note"] + with_usual,
    }


def main() -> None:
    tok, model = load_model()
    rows = []
    with torch.no_grad():
        dose_cases = [c for c in cases() if c["family"] == "F9"]
        doses = {(c["scenario"], c["condition"]): dose_mg(c["note"]) for c in dose_cases if c["wording"] == 0}
        for c in dose_cases:
            for name, note in versions(c, doses[(c["scenario"], c["condition"])]).items():
                text, names = prompt_and_names({**c, "note": note})
                ids = letter_ids(tok, len(names))
                logits = model(input_ids=encode(tok, text).to("mps")).logits[0, -1].float()
                probs = torch.softmax(logits[ids], dim=0).tolist()
                cautious = ids[names.index(next(o for o in names if o in p1.CAUTIOUS))]
                proceed = ids[names.index(next(o for o in names if o in p1.PROCEED))]
                rows.append(
                    {
                        "id": c["id"],
                        "condition": c["condition"],
                        "version": name,
                        "expected": c["expected"],
                        "chosen": names[max(range(len(names)), key=lambda i: probs[i])],
                        "cautious_minus_proceed": float(logits[cautious] - logits[proceed]),
                    }
                )
    (HERE / "runs" / "intervene.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    L = ["## The Explain step: stating the computed dose\n"]
    L.append(
        "Dose family, critical and benign cases. Right means the planted answer; the gap is the cautious letter's"
    )
    L.append("logit minus the proceed letter's.\n")
    L.append("| version | right, critical | right, benign | mean gap, critical | mean gap, benign |")
    L.append("|---|---|---|---|---|")
    for version in ("original", "computed", "computed and usual"):
        crit = [r for r in rows if r["version"] == version and r["condition"] == "critical"]
        ben = [r for r in rows if r["version"] == version and r["condition"] == "benign"]

        def right(rs: list[dict]) -> str:
            return f"{sum(r['chosen'] == r['expected'] for r in rs)}/{len(rs)}"

        def gap(rs: list[dict]) -> float:
            return sum(r["cautious_minus_proceed"] for r in rs) / len(rs)

        L.append(f"| {version} | {right(crit)} | {right(ben)} | {gap(crit):.2f} | {gap(ben):.2f} |")
    text = "\n".join(L) + "\n"
    (HERE / "runs" / "intervene_section.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
