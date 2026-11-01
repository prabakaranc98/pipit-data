"""B1: the bench. Even spread against the thresholding rule on synthetic subjects with planted failure rates.
Writes report.md. Usage: uv run python studies/b1_bench/bench.py"""

from __future__ import annotations

import random
from pathlib import Path

from pipit.allocate import even, nearest_to_settle, status, thresholding

HERE = Path(__file__).parent
SURFACES = {
    "mixed": [0.60, 0.45, 0.35, 0.30, 0.25, 0.12, 0.10, 0.08, 0.05, 0.03, 0.01, 0.00],
    "mostly clean": [0.40, 0.05, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00],
    "near the line": [0.30, 0.28, 0.26, 0.25, 0.30, 0.12, 0.11, 0.10, 0.10, 0.09, 0.08, 0.10],
}
BUDGETS = (60, 120, 240)
RUNS = 300


def truth(rate: float) -> str:
    return "supported" if rate > 0.20 else "refuted"


def score(rates: list[float], verdicts: list[str]) -> tuple[int, int]:
    """Right verdicts, and false claims: a verdict opposite to the truth."""
    right = sum(v == truth(r) for r, v in zip(rates, verdicts, strict=True))
    false = sum(v not in ("insufficient", truth(r)) for r, v in zip(rates, verdicts, strict=True))
    return right, false


def run_even(
    rates: list[float], budget: int, rng: random.Random, sequential: bool = False
) -> tuple[list[str], int]:
    names = [f"Q{i}" for i in range(len(rates))]
    units = even(names, budget)
    verdicts = []
    for name, rate in zip(names, rates, strict=True):
        n = units[name]
        verdicts.append(status(sum(rng.random() < rate for _ in range(n)), n, sequential=sequential))
    return verdicts, budget


def run_adaptive(
    rates: list[float], budget: int, rng: random.Random, policy=thresholding, sequential: bool = False
) -> tuple[list[str], int]:
    names = [f"Q{i}" for i in range(len(rates))]
    counts = {name: (0, 0) for name in names}
    spent = 0
    while spent < budget:
        q = policy(counts, sequential=sequential) if sequential else policy(counts)
        if q is None:
            break
        f, n = counts[q]
        counts[q] = (f + (rng.random() < rates[names.index(q)]), n + 1)
        spent += 1
    return [status(*counts[name], sequential=sequential) for name in names], spent


def main() -> None:
    L = ["# Study B1: does adaptive spending beat an even spread, without more false claims?\n"]
    L.append(
        f"Synthetic subjects, twelve key questions each; {RUNS} seeded runs per setting. See `preregistration.md`.\n"
    )
    for surface, rates in SURFACES.items():
        L.append(f"## {surface}\n")
        L.append(
            "| budget | policy | right verdicts, of 12 | false claims per run | runs with a false claim | units spent |"
        )
        L.append("|---|---|---|---|---|---|")
        for budget in BUDGETS:
            policies = (
                ("even", run_even),
                ("thresholding", run_adaptive),
                ("nearest to settle", lambda r, b, g: run_adaptive(r, b, g, nearest_to_settle)),
                ("even, sequence", lambda r, b, g: run_even(r, b, g, sequential=True)),
                (
                    "nearest to settle, sequence",
                    lambda r, b, g: run_adaptive(r, b, g, nearest_to_settle, True),
                ),
            )
            for policy, fn in policies:
                rng = random.Random(f"{surface}-{budget}")
                rights, falses, any_false, spent = 0, 0, 0, 0
                for _ in range(RUNS):
                    verdicts, used = fn(rates, budget, rng)
                    r, f = score(rates, verdicts)
                    rights, falses, any_false, spent = (
                        rights + r,
                        falses + f,
                        any_false + (f > 0),
                        spent + used,
                    )
                L.append(
                    f"| {budget} | {policy} | {rights / RUNS:.2f} | {falses / RUNS:.3f} | {any_false / RUNS:.1%} | "
                    f"{spent / RUNS:.0f} |"
                )
        L.append("")
    text = "\n".join(L) + "\n"
    (HERE / "report.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
