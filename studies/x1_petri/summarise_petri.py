"""Summarise X1's Petri audits from their Inspect logs: each seed's judge scores, the judge's summary, time, and
tokens and dollars per role. Run with an environment that has inspect-petri 3.1.1:
  <petri-env>/bin/python studies/x1_petri/summarise_petri.py clinical sycophancy"""

from __future__ import annotations

import sys
from pathlib import Path

from inspect_ai.log import read_eval_log

HERE = Path(__file__).parent
# OpenRouter's list prices on 2026-11-01, dollars per million tokens; cache reads priced as input, an upper bound.
PRICES = {"openrouter/deepseek/deepseek-v4-pro": (1.60, 3.20)}


def cost(model: str, usage) -> float:
    pin, pout = PRICES.get(model, (0.0, 0.0))
    tokens_in = (usage.input_tokens or 0) + (getattr(usage, "input_tokens_cache_read", 0) or 0)
    return (tokens_in * pin + (usage.output_tokens or 0) * pout) / 1e6


def summarise(arm: str) -> str:
    logs = sorted((HERE / "logs" / arm).glob("*.eval"))
    if not logs:
        return f"## Petri, {arm}: no log yet\n"
    return "\n".join(one(arm, i + 1, path) for i, path in enumerate(logs))


def one(arm: str, run: int, path: Path) -> str:
    log = read_eval_log(str(path))
    L = [
        f"## Petri, {arm}, run {run}\n",
        f"Log `{path.name}`, status {log.status}, {len(log.samples or [])} audits.\n",
    ]
    dims: list[str] = []
    for s in log.samples or []:
        for sc in (s.scores or {}).values():
            if isinstance(sc.value, dict):
                dims = sorted(set(dims) | set(sc.value))
    L.append("| seed | " + " | ".join(dims) + " | minutes | USD |")
    L.append("|---|" + "---|" * (len(dims) + 2))
    notes = []
    total = 0.0
    for s in log.samples or []:
        values = next((sc.value for sc in (s.scores or {}).values() if isinstance(sc.value, dict)), {})
        usd = sum(cost(m, u) for m, u in (s.model_usage or {}).items())
        total += usd
        cells = [str(values.get(d, "–")) for d in dims]
        L.append(f"| {s.id} | " + " | ".join(cells) + f" | {(s.total_time or 0) / 60:.1f} | {usd:.3f} |")
        sc = next(iter((s.scores or {}).values()), None)
        summary = ((sc.metadata or {}).get("summary") if sc else None) or (sc.explanation if sc else "") or ""
        notes.append(f"- **{s.id}:** {summary.strip()[:900]}")
    L.append(
        f"\nScores run 1 to 10; for every dimension here except scenario realism, higher is worse. Total {total:.2f} USD at list prices.\n"
    )
    L.append("What the judge wrote for each audit:\n")
    L.extend(notes)
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    text = "\n".join(summarise(arm) for arm in sys.argv[1:] or ["clinical", "sycophancy"])
    (HERE / "runs" / "petri_section.md").write_text(text)
    print(text)
