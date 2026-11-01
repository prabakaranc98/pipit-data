"""Run each judge over every J1 item: the original order, the reversed order, and the wrong proposals with the
injected note. Usage: uv run python studies/j1_judges/run.py studies/j1_judges/models/deepseek_v4_pro.yaml ..."""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from judges import RUNS, cases, context, items, parse, prompt  # noqa: E402

from pipit.manifest import load_manifest, resolve  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None, help="only the first N items, for a smoke test")
    ap.add_argument("--max-tokens", type=int, default=4000)
    args = ap.parse_args()
    all_cases = cases()
    base = items()[: args.limit] if args.limit else items()
    jobs = [(it, False, False) for it in base] + [(it, True, False) for it in base]
    jobs += [(it, False, True) for it in base if it["truth"] == "wrong"]
    RUNS.mkdir(exist_ok=True)
    for path in args.manifests:
        m = load_manifest(path)
        judge = resolve(m, context())

        def one(
            job: tuple[dict[str, Any], bool, bool], judge: Any = judge, name: str = m.name
        ) -> dict[str, Any]:
            it, reverse, inject = job
            text = prompt(all_cases[it["case_id"]], it["option"], reverse=reverse, inject=inject)
            meta = {
                "judge": name,
                "case_id": it["case_id"],
                "option": it["option"],
                "reverse": reverse,
                "inject": inject,
            }
            row = {**it, "reverse": reverse, "inject": inject}
            try:
                r = judge(text, temperature=0.0, max_tokens=args.max_tokens, role="judge", meta=meta)
            except Exception as e:  # a failed call is recorded in the verdicts, never dropped
                return {**row, "verdict": None, "error": f"{type(e).__name__}: {e}"[:300]}
            return {
                **row,
                "verdict": parse(r["text"]),
                "reply": r["text"][-300:],
                "cached": r["cached"],
                "finish_reason": r["finish_reason"],
                "provider": r["provider"],
                "model": r["model"],
            }

        with ThreadPoolExecutor(args.workers) as pool:
            rows = list(pool.map(one, jobs))
        out = RUNS / f"verdicts_{m.name}.jsonl"
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        failed = sum(r["verdict"] is None for r in rows)
        print(f"{m.name}: {len(rows)} verdicts, {failed} unparsed or failed, written to {out}")


if __name__ == "__main__":
    main()
