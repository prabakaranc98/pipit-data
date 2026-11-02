"""Rebuild every study's report from its recorded runs and check that nothing changed. A report that differs from
what its script writes has drifted from its data; so has one its script no longer writes, and so has any file a script
writes that no step declares. A step whose needs are missing on this machine is skipped and named, never passed in
silence; `--all` fails on a skipped step too, which is the release gate's form. CI runs this, without `--all`, on
every pull request.

Steps run in the order listed, and a step may read what an earlier one wrote: X1's assembly reads the pressure test's
section. A failed run leaves the rebuilt files in the working tree, so `git diff` shows what the scripts write: commit
them if the change is meant, or restore them with `git checkout -- <path>`.

Only reports are rebuilt here. A section written together with a model run is committed as an input, like the
hand-written parts of a report: I1's intervention section (`intervene.py`), X1's Petri section (`summarise_petri.py`,
with inspect-petri) and P1's proposals (`propose.py`).

Usage: uv run python studies/rebuild.py [--list] [--all]"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIFF_LINES = 60
TIME_LIMIT_S = 1800


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


def installed(module: str) -> bool:
    """Whether a module can be imported; a dotted name whose package is absent counts as not installed."""
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


def missing(step: Step, root: Path = ROOT) -> list[str]:
    """What this machine lacks for a step: modules that are not installed, then files that are not there."""
    return [m for m in step.modules if not installed(m)] + [f for f in step.files if not (root / f).exists()]


def status(root: Path = ROOT, paths: Sequence[str] = ()) -> dict[str, str]:
    """Each path that differs from the last commit, is not in it, or is gone, with git's two-letter code. Untracked
    files are listed one by one and paths are read literally, whatever the user's git settings."""
    out = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames", "--", *paths],
        cwd=root,
        capture_output=True,
        check=True,
        env={**os.environ, "GIT_LITERAL_PATHSPECS": "1"},
    ).stdout
    return {entry[3:].decode(): entry[:2].decode() for entry in out.split(b"\0") if entry}


def snapshot(root: Path = ROOT) -> dict[str, tuple[str, str | None]]:
    """Every changed or untracked file in the tree, with its status and a hash of its content, so a script that
    touches a file that was already changed is seen too."""

    def digest(path: str) -> str | None:
        file = root / path
        return hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None

    return {path: (code, digest(path)) for path, code in status(root).items()}


def describe(drifted: dict[str, str], root: Path = ROOT) -> str:
    """Name each drifted output and show the start of its diff."""
    words = {"??": "is new, not in the last commit", " D": "is gone"}
    lines = [f"{path} {words.get(code, 'differs from the last commit')}" for path, code in drifted.items()]
    diff = subprocess.run(
        ["git", "diff", "--", *drifted],
        cwd=root,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_LITERAL_PATHSPECS": "1"},
    ).stdout.splitlines()
    if len(diff) > DIFF_LINES:
        diff = diff[:DIFF_LINES] + [f"(the diff is cut at {DIFF_LINES} lines; run git diff for the rest)"]
    return "\n".join(lines + diff)


def rebuild(step: Step, root: Path = ROOT) -> str | None:
    """Run one step and return what went wrong, or None when its outputs are rewritten, match the last commit, and
    nothing else in the tree changed."""
    before = snapshot(root)
    stamps = {}
    for path in step.outputs:
        if (root / path).exists():
            stamps[path] = (root / path).stat().st_mtime_ns
            os.utime(root / path, ns=(0, 0))  # any write moves it, even where timestamps are coarse
    try:
        done = subprocess.run(
            [sys.executable, *step.command],
            cwd=root,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONUTF8": "1"},
            timeout=TIME_LIMIT_S,
        )
    except subprocess.TimeoutExpired:
        done = None
    not_written = [p for p in step.outputs if not (root / p).exists() or (root / p).stat().st_mtime_ns == 0]
    for path in not_written:
        if path in stamps and (root / path).exists():
            os.utime(root / path, ns=(stamps[path], stamps[path]))
    if done is None:
        return f"its script ran past {TIME_LIMIT_S // 60} minutes"
    if done.returncode != 0:
        return "its script failed:\n" + done.stderr[-3000:]
    problems = []
    if not_written:
        problems.append("its script did not write " + ", ".join(not_written))
    after = snapshot(root)
    stray = sorted(
        p for p in set(before) | set(after) if before.get(p) != after.get(p) and p not in step.outputs
    )
    if stray:
        problems.append("its script wrote files no step declares: " + ", ".join(stray))
    drifted = status(root, step.outputs)
    if drifted:
        problems.append(describe(drifted, root))
    return "\n".join(problems) or None


def main(argv: Sequence[str] | None = None, steps: Sequence[Step] = STEPS, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild every study's report and check that nothing changed."
    )
    parser.add_argument(
        "--list", action="store_true", help="print each step, its outputs and its needs, then stop"
    )
    parser.add_argument(
        "--all", action="store_true", help="fail on a skipped step too, as the release gate does"
    )
    args = parser.parse_args(argv)
    if args.list:
        for step in steps:
            needs = ", ".join(step.modules + step.files) or "the core only"
            print(
                f"{step.name}: python {' '.join(step.command)} -> {', '.join(step.outputs)} (needs {needs})"
            )
        return 0
    dirty = status(root, [p for step in steps for p in step.outputs])
    if dirty:
        print(
            "Commit or set aside these edits first, so a rebuild cannot overwrite them: " + ", ".join(dirty)
        )
        return 2
    failures = 0
    for step in steps:
        lacking = missing(step, root)
        if lacking:
            if args.all:
                failures += 1
            print(f"{step.name}: skipped here, needs {', '.join(lacking)}", flush=True)
            continue
        problem = rebuild(step, root)
        if problem is None:
            print(f"{step.name}: rebuilt, unchanged", flush=True)
        else:
            failures += 1
            print(f"{step.name}: {problem}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
