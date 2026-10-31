"""Run one subject over the eligible cases of the committed case set. Usage:
    uv run python studies/p1_clinical/run.py models/pplx_flash.yaml --role candidate
Answers are merged into runs/answers_<name>.jsonl, so a rerun only covers cases not yet answered."""

from __future__ import annotations

import argparse
import sys
import time
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
    args = ap.parse_args()
    manifest, model = subject(HERE / args.manifest, args.max_calls)
    cases = adjudicated(load_cases())
    out_path = RUNS / f"answers_{manifest.name}.jsonl"
    done = {r["id"]: r for r in read_jsonl(out_path)}
    todo = [c for c in cases.values() if c[args.set] and c["id"] not in done]
    print(f"{manifest.name}: {len(todo)} cases to run, {len(done)} already answered", flush=True)
    rows = list(done.values())
    for i, c in enumerate(todo, 1):
        questions = {"fact": noul(c["fact"]), "decision": choice(c["decision"], c["criteria"])}
        t0 = time.perf_counter()
        answers = model(
            c["note"], questions, role=args.role, meta={"case_id": c["id"], "subject": manifest.name}
        )
        rows.append(
            {
                "id": c["id"],
                "subject": manifest.name,
                "role": args.role,
                "model_answered": getattr(model, "answered_by", lambda: manifest.revision)(),
                "fact_p": p_true(answers["fact"]),
                "choice": chosen(answers["decision"]),
                "probabilities": probabilities(answers["decision"]),
                "seconds": round(time.perf_counter() - t0, 3),
            }
        )
        if i % 20 == 0 or i == len(todo):
            write_jsonl(out_path, rows)
            print(f"  {i}/{len(todo)}", flush=True)
    write_jsonl(out_path, rows)
    print(f"{manifest.name}: {len(rows)} answers in {out_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()
