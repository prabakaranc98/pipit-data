"""Run study V1: each model on the MedCalc-Bench sample and on P1's cases.
Usage: uv run python studies/v1_medcalc/run.py studies/v1_medcalc/models/*.yaml [--limit N] [--allow-unpinned]

Before the first call the run checks every model's family and provider pin, and that the key's budget covers an
upper bound on the cost. V1's models were run unpinned, so running them again needs --allow-unpinned, and the
report says so. Each result is saved as it finishes. A run keeps every recorded result and asks only the items not
yet answered or refused by the key (the pre-registration's --resume is this default); --fresh starts over. Once the
key refuses a call, no further calls are sent and the run stops."""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "p1_clinical"))
import medcalc  # noqa: E402
import study as p1  # noqa: E402

from pipit import preflight  # noqa: E402
from pipit.adapters import openrouter  # noqa: E402
from pipit.adapters.openai_compat import LETTERS, render  # noqa: E402
from pipit.env import load_dotenv  # noqa: E402
from pipit.ledger import Ledger  # noqa: E402
from pipit.manifest import Context, load_manifest, resolve  # noqa: E402
from pipit.questions import choice  # noqa: E402
from pipit.results import Results  # noqa: E402

RUNS = HERE / "runs"
# What the runner records when the key refuses a call, and for the items it then holds back. Neither is the model's
# answer, so a later run asks them again.
REFUSED = ("HTTP Error 403", "KeyRefused", "not sent: the API key's limit was reached")
# Upper bounds for the cost check: tokens in per request, and the reply caps used below.
TOKENS = {"medcalc": (1000, 4096), "p1": (300, 2048)}


def refused(row: dict[str, Any]) -> bool:
    return any(mark in (row.get("error") or "") for mark in REFUSED)


def done(row: dict[str, Any] | None) -> bool:
    return row is not None and not refused(row)


def letter(reply: str, n: int) -> int | None:
    m = re.search(rf"\b([{LETTERS[:n]}])\b", reply.strip())
    return LETTERS.index(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--resume", action="store_true", help="the default; kept for the pre-registered command")
    ap.add_argument("--fresh", action="store_true", help="discard recorded results and ask every item again")
    ap.add_argument(
        "--allow-unpinned", action="store_true", help="run models not pinned to a provider, as V1 was"
    )
    args = ap.parse_args()
    load_dotenv(HERE.parents[1] / ".env")
    RUNS.mkdir(exist_ok=True)
    items = medcalc.sample(medcalc.test_rows())
    p1_cases = [c for c in p1.adjudicated(p1.load_cases()).values() if c["eligible"]]
    if args.limit:
        items, p1_cases = items[: args.limit], p1_cases[: args.limit]
    manifests = [load_manifest(path) for path in args.manifests]
    if args.fresh:
        for m in manifests:
            for arm in ("medcalc", "p1"):
                (RUNS / f"{arm}_{m.name}.jsonl").unlink(missing_ok=True)
    stores = {
        m.name: (
            Results(RUNS / f"medcalc_{m.name}.jsonl", "row"),
            Results(RUNS / f"p1_{m.name}.jsonl", "case_id"),
        )
        for m in manifests
    }
    cost = 0.0
    for m in manifests:
        calc_store, p1_store = stores[m.name]
        for arm, n in (
            ("medcalc", sum(not done(calc_store.get(r["Row Number"])) for r in items)),
            ("p1", sum(not done(p1_store.get(c["id"])) for c in p1_cases)),
        ):
            cost += preflight.estimated_usd(m, n, *TOKENS[arm]) or 0.0
    budget = openrouter.budget_left() if cost and any(m.placement == "api" for m in manifests) else None
    preflight.require(manifests, allow_unpinned=args.allow_unpinned, cost=cost, budget=budget)
    left = "" if budget is None else f", with ${budget:.2f} left on the key"
    print(f"Checks passed. This run is estimated at ${cost:.2f}{left}; cached replies cost nothing.")
    with (RUNS / "run_log.jsonl").open("a") as log:  # what each run was allowed to do, for the report
        log.write(
            json.dumps(
                {
                    "started": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
                    "models": [m.name for m in manifests],
                    "allow_unpinned": args.allow_unpinned,
                    "pinned": [m.name for m in manifests if preflight.pinned(m)],
                    "estimated_usd": round(cost, 4),
                    "budget_left": budget,
                }
            )
            + "\n"
        )
    stop = threading.Event()

    for m in manifests:
        if stop.is_set():
            break
        calc_store, p1_store = stores[m.name]
        model = resolve(m, Context(ledger=Ledger(RUNS / "ledger.jsonl"), cache_dir=HERE / "cache"))

        def ask(call: Any, out: dict[str, Any], store: Results, failure: dict[str, Any]) -> dict[str, Any]:
            """Make one call and record its row; a refused key stops every call after it."""
            if stop.is_set():
                held = {**out, **failure, "error": REFUSED[2]}
                store.add(held)
                return held
            try:
                row = {**out, **call()}
            except Exception as e:  # recorded, never dropped
                row = {**out, **failure, "error": f"{type(e).__name__}: {e}"[:300]}
                if isinstance(e, openrouter.KeyRefused) or refused(row):
                    stop.set()
            store.add(row)
            return row

        def calc(row: dict[str, Any], model: Any = model, store: Results = calc_store) -> dict[str, Any]:
            if done(store.get(row["Row Number"])):
                return store.get(row["Row Number"])

            def call() -> dict[str, Any]:
                r = model(
                    medcalc.user(row["Patient Note"], row["Question"]),
                    system=medcalc.SYSTEM,
                    temperature=0.0,
                    max_tokens=TOKENS["medcalc"][1],
                    role="candidate",
                    meta={"subject": model.manifest.name, "arm": "medcalc", "row": row["Row Number"]},
                )
                got = medcalc.answer(r["text"])
                return {"answer": got, "correct": medcalc.correct(row, got), "provider": r["provider"]}

            out = {
                "row": row["Row Number"],
                "category": row["Category"],
                "calculator": row["Calculator Name"],
            }
            return ask(call, out, store, {"answer": None, "correct": False})

        def decide(case: dict[str, Any], model: Any = model, store: Results = p1_store) -> dict[str, Any]:
            if done(store.get(case["id"])):
                return store.get(case["id"])
            text, names = render(case["note"], choice(case["decision"], case["criteria"]))

            def call() -> dict[str, Any]:
                r = model(
                    text,
                    temperature=0.0,
                    max_tokens=TOKENS["p1"][1],
                    role="candidate",
                    meta={"subject": model.manifest.name, "arm": "p1", "case_id": case["id"]},
                )
                i = letter(r["text"], len(names))
                return {
                    "choice": None if i is None else names[i],
                    "reply": r["text"][-120:],
                    "provider": r["provider"],
                }

            return ask(call, {"case_id": case["id"], "expected": case["expected"]}, store, {"choice": None})

        with ThreadPoolExecutor(args.workers) as pool:
            list(pool.map(calc, items))
            list(pool.map(decide, p1_cases))
        calc_rows = calc_store.compact(r["Row Number"] for r in items)
        p1_rows = p1_store.compact(c["id"] for c in p1_cases)
        right = sum(r["correct"] for r in calc_rows)
        failed = sum(r.get("error") is not None for r in calc_rows + p1_rows)
        unparsed = sum(r["choice"] is None for r in p1_rows)
        held = sum(refused(r) for r in calc_rows + p1_rows)
        print(
            f"{m.name}: MedCalc {right}/{len(calc_rows)}; P1 answered {len(p1_rows) - unparsed}/{len(p1_rows)}; "
            f"{failed} failed calls, {held} of them refused by the key",
            flush=True,
        )
    if stop.is_set():
        sys.exit(
            "Stopped: the API key refused a call, most likely its spending limit. Raise it and run again."
        )


if __name__ == "__main__":
    main()
