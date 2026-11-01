"""I1 step 3: the probe per layer and the patching curve; writes report.md. Usage: python studies/i1_interp/analyse.py"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import HERE  # noqa: E402

from pipit.checks import wilson  # noqa: E402

PENALTY = 1.0


def ridge_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    """A ridge classifier in its dual form, on features standardised with the training folds only."""
    mu, sd = x_train.mean(0), x_train.std(0) + 1e-6
    a, b = (x_train - mu) / sd, (x_test - mu) / sd
    alpha = np.linalg.solve(a @ a.T + PENALTY * np.eye(len(a)), y_train)
    return np.sign(b @ (a.T @ alpha))


def share(k: float, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k:g}/{n} ({lo:.2f}–{hi:.2f})" if n else "–"


def main() -> None:
    rows = [json.loads(x) for x in (HERE / "runs" / "extract.jsonl").read_text().splitlines() if x.strip()]
    hidden = np.load(HERE / "runs" / "hidden_last.npy").astype(np.float32)
    y = np.array([1.0 if r["condition"] == "critical" else -1.0 for r in rows])
    families = sorted({r["family"] for r in rows})
    unit = [f"{r['family']}/{r['scenario']}/{r['condition']}" for r in rows]
    decided_right = np.array([r["p1_choice"] == r["expected"] for r in rows])
    known = [r for r in rows if r["p1_choice"]]
    L = ["# Study I1: does Qwen3.5-4B hold the planted fact when its decision ignores it?\n"]
    L.append(
        f"{len(rows)} critical and benign cases from P1 ({len(set(unit))} independent). Setup in `preregistration.md`. "
        f"The option chosen here agrees with P1's recorded answer on {sum(r['chosen'] == r['p1_choice'] for r in known)}/{len(known)} cases.\n"
    )
    L.append("## The probe: is the fact readable at the decision point?\n")
    L.append(
        "Held-out accuracy of a ridge probe for critical against benign, at the last prompt token, leaving one family "
        "out at a time. Counted once per independent case. Split by whether P1's decision on the case was right.\n"
    )
    L.append("| layer | all cases | where P1 decided right | where P1 decided wrong |")
    L.append("|---|---|---|---|")
    best = (-1.0, 0)
    curve = []
    for layer in range(hidden.shape[1]):
        pred = np.zeros(len(rows))
        for fam in families:
            test = np.array([r["family"] == fam for r in rows])
            pred[test] = ridge_predict(hidden[~test, layer], y[~test], hidden[test, layer])
        hit = pred == y
        per_unit: dict[str, list[bool]] = {}
        per_unit_right: dict[str, list[bool]] = {}
        per_unit_wrong: dict[str, list[bool]] = {}
        for u, h, ok in zip(unit, hit, decided_right, strict=True):
            per_unit.setdefault(u, []).append(bool(h))
            (per_unit_right if ok else per_unit_wrong).setdefault(u, []).append(bool(h))

        def score(d: dict[str, list[bool]]) -> tuple[float, int]:
            return sum(sum(v) / len(v) for v in d.values()), len(d)

        k, n = score(per_unit)
        curve.append(k / n)
        if k / n > best[0]:
            best = (k / n, layer)
        if layer % 4 == 0 or layer == hidden.shape[1] - 1:
            L.append(
                f"| {layer} | {share(*score(per_unit))} | {share(*score(per_unit_right))} | {share(*score(per_unit_wrong))} |"
            )
    L.append(f"\nBest layer: {best[1]}, held-out accuracy {best[0]:.2f}.\n")

    patching_path = HERE / "runs" / "patching.json"
    if patching_path.exists():
        pairs = json.loads(patching_path.read_text())
        kept = [p for p in pairs if p["ld_critical"] - p["ld_benign"] > 1.0]
        L.append("## Patching: where does the last position carry the decision?\n")
        L.append(
            f"{len(pairs)} pairs; {len(kept)} kept, whose critical and benign runs differ by more than one logit "
            "(cautious minus proceed letter). Share of that gap restored when one layer's last-position output is "
            "taken from the critical run; 95% bootstrap interval over pairs.\n"
        )
        L.append("| layer | share restored |")
        L.append("|---|---|")
        rng = random.Random(0)
        for layer in range(len(kept[0]["ld_patched"]) if kept else 0):
            r = [
                (p["ld_patched"][layer] - p["ld_benign"]) / (p["ld_critical"] - p["ld_benign"]) for p in kept
            ]
            boots = sorted(sum(rng.choice(r) for _ in r) / len(r) for _ in range(1000))
            if layer % 2 == 0 or layer == len(kept[0]["ld_patched"]) - 1:
                L.append(f"| {layer} | {sum(r) / len(r):.2f} ({boots[25]:.2f} to {boots[974]:.2f}) |")
    # The Explain step's table, written by intervene.py, then the reading that closes the report, written by hand.
    for part in (HERE / "runs" / "intervene_section.md", HERE / "report_tail.md"):
        if part.exists():
            L.extend(["", part.read_text().rstrip("\n")])
    text = "\n".join(L) + "\n"
    (HERE / "report.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
