"""Recount P1's thinking-mode answers under the corrected confidence rule (#68).

Each option's probability is now its share of all samples, so a sample cut off at the token budget counts against
confidence; before, it was a share of the samples that answered, and one answer out of three scored 1.0. The votes
are recovered exactly from the recorded shares (share times samples answered), so no model is called and no choice
changes. Rows already recounted are left alone, so running it twice changes nothing.
Usage: python studies/p1_clinical/recount_thinking.py"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
PATH = HERE / "runs" / "answers_qwen35_4b_thinking.jsonl"
MARK = "shares of all samples (#68)"


def recount(row: dict[str, Any]) -> dict[str, Any]:
    samples = int(re.search(r"(\d+) samples", row["model_answered"]).group(1))
    answered = row.get("answered") or 0
    if row.get("recounted") or not row.get("probabilities") or answered == samples:
        return row
    probs = {name: share * answered / samples for name, share in row["probabilities"].items()}
    return {**row, "probabilities": probs, "agreement": round(max(probs.values()), 4), "recounted": MARK}


def main() -> None:
    rows = [json.loads(line) for line in PATH.read_text().splitlines() if line.strip()]
    new = [recount(r) for r in rows]
    PATH.write_text("".join(json.dumps(r) + "\n" for r in new))
    print(f"{sum(a != b for a, b in zip(rows, new, strict=True))} of {len(rows)} rows recounted")


if __name__ == "__main__":
    main()
