"""Run study V1: each model on the MedCalc-Bench sample and on P1's cases.
Usage: uv run python studies/v1_medcalc/run.py studies/v1_medcalc/models/*.yaml [--limit N]"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "p1_clinical"))
import medcalc  # noqa: E402
import study as p1  # noqa: E402

from pipit.adapters.openai_compat import LETTERS, render  # noqa: E402
from pipit.env import load_dotenv  # noqa: E402
from pipit.ledger import Ledger  # noqa: E402
from pipit.manifest import Context, load_manifest, resolve  # noqa: E402
from pipit.questions import choice  # noqa: E402

RUNS = HERE / "runs"


def letter(reply: str, n: int) -> int | None:
    m = re.search(rf"\b([{LETTERS[:n]}])\b", reply.strip())
    return LETTERS.index(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    load_dotenv(HERE.parents[1] / ".env")
    RUNS.mkdir(exist_ok=True)
    items = (
        medcalc.sample(medcalc.test_rows())[: args.limit]
        if args.limit
        else medcalc.sample(medcalc.test_rows())
    )
    cases = p1.adjudicated(p1.load_cases())
    p1_cases = (
        [c for c in cases.values() if c["eligible"]][: args.limit]
        if args.limit
        else [c for c in cases.values() if c["eligible"]]
    )
    for path in args.manifests:
        m = load_manifest(path)
        model = resolve(m, Context(ledger=Ledger(RUNS / "ledger.jsonl"), cache_dir=HERE / "cache"))

        def calc(row: dict[str, Any], model: Any = model, name: str = m.name) -> dict[str, Any]:
            meta = {"subject": name, "arm": "medcalc", "row": row["Row Number"]}
            out = {
                "row": row["Row Number"],
                "category": row["Category"],
                "calculator": row["Calculator Name"],
            }
            try:
                r = model(
                    medcalc.user(row["Patient Note"], row["Question"]),
                    system=medcalc.SYSTEM,
                    temperature=0.0,
                    max_tokens=4096,
                    role="candidate",
                    meta=meta,
                )
            except Exception as e:  # recorded, never dropped
                return {**out, "answer": None, "correct": False, "error": f"{type(e).__name__}: {e}"[:300]}
            got = medcalc.answer(r["text"])
            return {**out, "answer": got, "correct": medcalc.correct(row, got), "provider": r["provider"]}

        def decide(case: dict[str, Any], model: Any = model, name: str = m.name) -> dict[str, Any]:
            text, names = render(case["note"], choice(case["decision"], case["criteria"]))
            meta = {"subject": name, "arm": "p1", "case_id": case["id"]}
            out = {"case_id": case["id"], "expected": case["expected"]}
            try:
                r = model(text, temperature=0.0, max_tokens=2048, role="candidate", meta=meta)
            except Exception as e:
                return {**out, "choice": None, "error": f"{type(e).__name__}: {e}"[:300]}
            i = letter(r["text"], len(names))
            return {
                **out,
                "choice": None if i is None else names[i],
                "reply": r["text"][-120:],
                "provider": r["provider"],
            }

        with ThreadPoolExecutor(args.workers) as pool:
            calc_rows = list(pool.map(calc, items))
            p1_rows = list(pool.map(decide, p1_cases))
        (RUNS / f"medcalc_{m.name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in calc_rows))
        (RUNS / f"p1_{m.name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in p1_rows))
        right = sum(r["correct"] for r in calc_rows)
        failed = sum(r.get("error") is not None for r in calc_rows + p1_rows)
        unparsed = sum(r["choice"] is None for r in p1_rows)
        print(
            f"{m.name}: MedCalc {right}/{len(calc_rows)}; P1 answered {len(p1_rows) - unparsed}/{len(p1_rows)}; {failed} failed calls"
        )


if __name__ == "__main__":
    main()
