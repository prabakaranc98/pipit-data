"""Run one subject over the eligible cases of the committed case set. Usage:
    uv run python studies/p1_clinical/run.py models/pplx_flash.yaml --role candidate
    uv run python studies/p1_clinical/run.py models/qwen35_4b_thinking.yaml --questions decision --workers 2
Answers are merged into runs/answers_<name>.jsonl, so a rerun only covers cases not yet answered. --workers runs
cases in parallel (useful when the subject's server batches requests); --limit runs a pilot of the first N."""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from study import HERE, RUNS, adjudicated, load_cases, read_jsonl, subject, write_jsonl  # noqa: E402

from pipit.questions import choice, chosen, noul, p_true, probabilities  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--role", default="candidate", choices=["candidate", "reference"])
    ap.add_argument("--max-calls", type=int, default=None)
    ap.add_argument("--set", default="eligible", choices=["eligible", "eligible_primary"])
    ap.add_argument(
        "--questions", default="fact,decision", help="which questions to ask: fact, decision or both"
    )
    ap.add_argument("--workers", type=int, default=1, help="cases run in parallel")
    ap.add_argument(
        "--limit", type=int, default=None, help="run only the first N cases still to do (a pilot)"
    )
    args = ap.parse_args()
    which = {q.strip() for q in args.questions.split(",") if q.strip()}
    if not which <= {"fact", "decision"}:
        raise SystemExit("--questions takes fact, decision or both")
    manifest, model = subject(HERE / args.manifest, args.max_calls)
    cases = adjudicated(load_cases())
    out_path = RUNS / f"answers_{manifest.name}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_path)}
    todo = [c for c in cases.values() if c[args.set] and c["id"] not in done][: args.limit]
    print(f"{manifest.name}: {len(todo)} cases to run, {len(done)} already answered", flush=True)

    def ask(c: dict) -> dict:
        questions = {}
        if "fact" in which:
            questions["fact"] = noul(c["fact"])
        if "decision" in which:
            questions["decision"] = choice(c["decision"], c["criteria"])
        t0 = time.perf_counter()
        answers = model(
            c["note"], questions, role=args.role, meta={"case_id": c["id"], "subject": manifest.name}
        )
        decision = answers.get("decision", {})
        row = {
            "id": c["id"],
            "subject": manifest.name,
            "role": args.role,
            "model_answered": getattr(model, "answered_by", lambda: manifest.revision)(),
            "fact_p": p_true(answers["fact"]) if "fact" in answers else None,
            "choice": chosen(decision) if decision else None,
            "probabilities": probabilities(decision) if decision else None,
            "seconds": round(time.perf_counter() - t0, 3),
        }
        if "agreement" in decision:
            row.update(agreement=decision["agreement"], answered=decision["answered"], tie=decision["tie"])
        return row

    rows = list(done.values())
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(ask, c) for c in todo]
        for i, future in enumerate(as_completed(futures), 1):
            rows.append(future.result())
            if i % 10 == 0 or i == len(todo):
                write_jsonl(out_path, sorted(rows, key=lambda r: r["id"]))
                print(f"  {i}/{len(todo)}", flush=True)
    write_jsonl(out_path, sorted(rows, key=lambda r: r["id"]))
    print(f"{manifest.name}: {len(rows)} answers in {out_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
