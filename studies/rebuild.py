"""Rebuild every study's report from its recorded runs and check that nothing changed. A report that differs from
what its script writes has drifted from its data; so has one its script no longer writes. A step whose needs are
missing on this machine is skipped and named, never passed in silence. CI runs this on every pull request.

Only reports are rebuilt here. Steps that call a model, or that read logs only another environment can open, make
recorded runs instead: I1's intervention section (`intervene.py`, on the local model) and X1's Petri section
(`summarise_petri.py`, with inspect-petri) are committed as inputs, like the hand-written parts of a report.

Usage: uv run python studies/rebuild.py [--list]"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]
    outputs: tuple[str, ...]
    modules: tuple[str, ...] = ()  # Python modules the step needs beyond the core
    files: tuple[str, ...] = ()  # files the step reads that git does not keep


STEPS = (
    Step(
        "P1",
        ("studies/p1_clinical/analyse.py",),
        ("studies/p1_clinical/report.md", "studies/p1_clinical/tree.svg"),
    ),
    Step("V1", ("studies/v1_medcalc/analyse.py",), ("studies/v1_medcalc/report.md",)),
    Step("J1", ("studies/j1_judges/analyse.py",), ("studies/j1_judges/report.md",)),
    Step(
        "P3", ("studies/p3_support_crisis/pilot.py", "report"), ("studies/p3_support_crisis/pilot_report.md",)
    ),
    Step(
        "X1, pressure test",
        ("studies/x1_petri/pressure.py", "analyse"),
        ("studies/x1_petri/runs/pressure_section.md",),
    ),
    Step("X1", ("studies/x1_petri/assemble.py",), ("studies/x1_petri/report.md",)),
    Step("B1", ("studies/b1_bench/bench.py",), ("studies/b1_bench/report.md",)),
    Step(
        "I1",
        ("studies/i1_interp/analyse.py",),
        ("studies/i1_interp/report.md",),
        modules=("numpy",),
        files=("studies/i1_interp/runs/hidden_last.npy",),
    ),
)


def missing(step: Step) -> list[str]:
    """What this machine lacks for a step: modules that are not installed, then files that are not there."""
    absent = [m for m in step.modules if importlib.util.find_spec(m) is None]
    return absent + [f for f in step.files if not (ROOT / f).exists()]


def changed(paths: list[str] | tuple[str, ...]) -> list[str]:
    """The paths that differ from the last commit, are not in it, or are gone."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [line[3:] for line in status.splitlines()]


def rebuild(step: Step) -> str | None:
    """Run one step and return what went wrong, or None when its outputs are rewritten and match the commit."""
    before = {p: (ROOT / p).stat().st_mtime_ns if (ROOT / p).exists() else None for p in step.outputs}
    done = subprocess.run([sys.executable, *step.command], cwd=ROOT, capture_output=True, text=True)
    if done.returncode != 0:
        return "its script failed:\n" + done.stderr[-3000:]
    not_written = [
        p for p in step.outputs if not (ROOT / p).exists() or (ROOT / p).stat().st_mtime_ns == before[p]
    ]
    if not_written:
        return "its script did not write " + ", ".join(not_written)
    drifted = changed(step.outputs)
    if drifted:
        diff = subprocess.run(
            ["git", "diff", "--", *drifted], cwd=ROOT, capture_output=True, text=True
        ).stdout
        return (
            "differs from what its script writes: "
            + ", ".join(drifted)
            + "\n"
            + "\n".join(diff.splitlines()[:60])
        )
    return None


def main() -> int:
    if "--list" in sys.argv:
        for step in STEPS:
            needs = ", ".join(step.modules + step.files) or "the core only"
            print(
                f"{step.name}: python {' '.join(step.command)} -> {', '.join(step.outputs)} (needs {needs})"
            )
        return 0
    dirty = changed([p for step in STEPS for p in step.outputs])
    if dirty:
        print(
            "Commit or set aside these edits first, so a rebuild cannot overwrite them: " + ", ".join(dirty)
        )
        return 2
    failures = 0
    for step in STEPS:
        lacking = missing(step)
        if lacking:
            print(f"{step.name}: skipped here, needs {', '.join(lacking)}")
            continue
        problem = rebuild(step)
        if problem is None:
            print(f"{step.name}: rebuilt, unchanged")
        else:
            failures += 1
            print(f"{step.name}: {problem}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
