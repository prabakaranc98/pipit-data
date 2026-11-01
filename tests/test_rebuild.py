import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _rebuild():
    spec = importlib.util.spec_from_file_location("studies_rebuild", ROOT / "studies" / "rebuild.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # a dataclass looks its module up here
    spec.loader.exec_module(module)
    return module


def test_every_report_has_a_step_that_writes_it() -> None:
    written = {path for step in _rebuild().STEPS for path in step.outputs}
    reports = {str(p.relative_to(ROOT)) for p in ROOT.glob("studies/*/*report.md")}
    assert reports and reports <= written, f"reports no step rebuilds: {sorted(reports - written)}"


def test_a_step_names_what_this_machine_lacks() -> None:
    rebuild = _rebuild()
    step = rebuild.Step(
        "x", ("x.py",), ("x.md",), modules=("no_such_module_here", "json"), files=("no/such/file",)
    )
    assert rebuild.missing(step) == ["no_such_module_here", "no/such/file"]
