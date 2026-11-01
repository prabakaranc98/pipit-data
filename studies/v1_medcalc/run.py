"""Run study V1: each model on the MedCalc-Bench sample and on P1's cases.
Usage: uv run python studies/v1_medcalc/run.py studies/v1_medcalc/models/*.yaml [--limit N] [--resume]

Once the API key refuses a call (its spending limit), no further calls are sent; the run stops, and the refused
items are recorded as such. --resume keeps every recorded result and asks again only the items the key refused."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import urllib.request
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
# What the API returns once the key's spending limit is reached, and what the runner records for items it then holds
# back. Neither is the model's answer.
REFUSED = ("HTTP Error 403", "not sent: the API key's limit was reached")


def refused(row: dict[str, Any]) -> bool:
    return any(mark in (row.get("error") or "") for mark in REFUSED)


def key_budget_left() -> float | None:
    """Dollars left on the OpenRouter key, or None when it has no limit."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"].get("limit_remaining")


def recorded(path: Path, key: str) -> dict[Any, dict[str, Any]]:
    if not path.exists():
        return {}
    return {r[key]: r for r in (json.loads(x) for x in path.read_text().splitlines() if x.strip())}


def letter(reply: str, n: int) -> int | None:
    m = re.search(rf"\b([{LETTERS[:n]}])\b", reply.strip())
    return LETTERS.index(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument(
        "--resume", action="store_true", help="keep recorded results; ask again only refused items"
    )
    ap.add_argument("--min-budget", type=float, default=5.0, help="dollars the key must have left to resume")
    args = ap.parse_args()
    load_dotenv(HERE.parents[1] / ".env")
    RUNS.mkdir(exist_ok=True)
    if args.resume:
        left = key_budget_left()
        if left is not None and left < args.min_budget:
            sys.exit(f"The key has ${left:.2f} left, under the ${args.min_budget:.2f} needed to resume.")
    stop = threading.Event()
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
        if stop.is_set():
            break
        m = load_manifest(path)
        old_calc = recorded(RUNS / f"medcalc_{m.name}.jsonl", "row") if args.resume else {}
        old_p1 = recorded(RUNS / f"p1_{m.name}.jsonl", "case_id") if args.resume else {}
        model = resolve(m, Context(ledger=Ledger(RUNS / "ledger.jsonl"), cache_dir=HERE / "cache"))

        def calc(
            row: dict[str, Any], model: Any = model, name: str = m.name, old: dict = old_calc
        ) -> dict[str, Any]:
            meta = {"subject": name, "arm": "medcalc", "row": row["Row Number"]}
            out = {
                "row": row["Row Number"],
                "category": row["Category"],
                "calculator": row["Calculator Name"],
            }
            if row["Row Number"] in old and not refused(old[row["Row Number"]]):
                return old[row["Row Number"]]
            if stop.is_set():
                return {**out, "answer": None, "correct": False, "error": REFUSED[1]}
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
                failed = {**out, "answer": None, "correct": False, "error": f"{type(e).__name__}: {e}"[:300]}
                if refused(failed):
                    stop.set()
                return failed
            got = medcalc.answer(r["text"])
            return {**out, "answer": got, "correct": medcalc.correct(row, got), "provider": r["provider"]}

        def decide(
            case: dict[str, Any], model: Any = model, name: str = m.name, old: dict = old_p1
        ) -> dict[str, Any]:
            text, names = render(case["note"], choice(case["decision"], case["criteria"]))
            meta = {"subject": name, "arm": "p1", "case_id": case["id"]}
            out = {"case_id": case["id"], "expected": case["expected"]}
            if case["id"] in old and not refused(old[case["id"]]):
                return old[case["id"]]
            if stop.is_set():
                return {**out, "choice": None, "error": REFUSED[1]}
            try:
                r = model(text, temperature=0.0, max_tokens=2048, role="candidate", meta=meta)
            except Exception as e:
                failed = {**out, "choice": None, "error": f"{type(e).__name__}: {e}"[:300]}
                if refused(failed):
                    stop.set()
                return failed
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
        held = sum(refused(r) for r in calc_rows + p1_rows)
        print(
            f"{m.name}: MedCalc {right}/{len(calc_rows)}; P1 answered {len(p1_rows) - unparsed}/{len(p1_rows)}; "
            f"{failed} failed calls, {held} of them refused by the key"
        )
    if stop.is_set():
        sys.exit("Stopped: the API key's limit was reached. Raise it, then run again with --resume.")


if __name__ == "__main__":
    main()
