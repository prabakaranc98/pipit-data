import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _rebuild():
    spec = importlib.util.spec_from_file_location("studies_rebuild", ROOT / "studies" / "rebuild.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # a dataclass looks its module up here
    spec.loader.exec_module(module)
    return module


def _repo(tmp_path: Path) -> Path:
    """A git repository with one script that writes out.md, committed as the script writes it."""
    (tmp_path / "build.py").write_text(
        "import pathlib, sys\n"
        "pathlib.Path('out.md').write_text(sys.argv[1] if len(sys.argv) > 1 else 'same\\n')\n"
    )
    (tmp_path / "out.md").write_text("same\n")
    for command in (
        ["init", "-q"],
        ["add", "-A"],
        ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "s"],
    ):
        subprocess.run(["git", *command], cwd=tmp_path, check=True)
    return tmp_path


def test_every_report_has_a_step_that_writes_it() -> None:
    written = {path for step in _rebuild().STEPS for path in step.outputs}
    reports = {str(p.relative_to(ROOT)) for p in ROOT.glob("studies/*/*report.md")}
    assert reports and reports <= written, f"reports no step rebuilds: {sorted(reports - written)}"


def test_a_step_names_what_this_machine_lacks() -> None:
    rebuild = _rebuild()
    modules = ("no_such_module_here", "json", "no_such_package.sub")
    step = rebuild.Step("x", ("x.py",), ("x.md",), modules=modules, files=("no/such/file",))
    assert rebuild.missing(step) == ["no_such_module_here", "no_such_package.sub", "no/such/file"]


def test_a_rebuild_finds_drift_a_silent_script_and_stray_files(tmp_path) -> None:
    rebuild, root = _rebuild(), _repo(tmp_path)
    assert rebuild.rebuild(rebuild.Step("same", ("build.py",), ("out.md",)), root) is None
    drift = rebuild.rebuild(rebuild.Step("drift", ("build.py", "changed\n"), ("out.md",)), root)
    assert "out.md differs from the last commit" in drift and "+changed" in drift
    subprocess.run(["git", "checkout", "-q", "--", "out.md"], cwd=root, check=True)
    assert "did not write out.md" in rebuild.rebuild(
        rebuild.Step("silent", ("-c", "pass"), ("out.md",)), root
    )
    writes_more = (
        "import pathlib; pathlib.Path('out.md').write_text('same\\n'); "
        "pathlib.Path('report.json').write_text('{}')"
    )
    stray = rebuild.rebuild(rebuild.Step("stray", ("-c", writes_more), ("out.md",)), root)
    assert "no step declares: report.json" in stray


def test_a_run_refuses_unsaved_edits_and_all_fails_on_a_skipped_step(tmp_path) -> None:
    rebuild, root = _rebuild(), _repo(tmp_path)
    needs = rebuild.Step("needs", ("build.py",), ("out.md",), modules=("no_such_module_here",))
    assert rebuild.main([], steps=(needs,), root=root) == 0
    assert rebuild.main(["--all"], steps=(needs,), root=root) == 1
    (root / "out.md").write_text("edited by hand\n")
    assert rebuild.main([], steps=(needs,), root=root) == 2
