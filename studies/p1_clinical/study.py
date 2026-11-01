"""Shared study plumbing: paths, eligibility, severity sets and the hypothesis tree."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from pipit.checks import severity as _severity
from pipit.env import load_dotenv
from pipit.ledger import Ledger
from pipit.manifest import Context, Manifest, load_manifest, resolve
from pipit.tree import partition, rules

HERE = Path(__file__).parent
CASES = HERE / "cases.jsonl"
RUNS = HERE / "runs"
LEDGER = HERE / "runs" / "ledger.jsonl"
CAUTIOUS = {"avoid", "escalate_now", "required", "treat_as_neutropenic_sepsis", "withhold_and_recheck"}
PROCEED = {"proceed", "routine", "not_required", "standard_fever_pathway", "administer"}
PLANTED = {"critical": "TRUE", "benign": "FALSE", "absent": "UNDETERMINED", "conflict": "UNDETERMINED"}


def context(max_calls: int | None = None) -> Context:
    load_dotenv(HERE.parents[1] / ".env")
    return Context(ledger=Ledger(LEDGER), cache_dir=HERE / "cache", max_calls=max_calls)


def subject(manifest_path: str | Path, max_calls: int | None = None) -> tuple[Manifest, Any]:
    m = load_manifest(manifest_path)
    return m, resolve(m, context(max_calls))


def load_cases() -> dict[str, dict[str, Any]]:
    cases = {}
    for line in CASES.read_text().splitlines():
        if line.strip():
            c = json.loads(line)
            cases[c["id"]] = c
    return cases


def adjudicated(cases: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Mark each case: eligible_primary (pre-registered rule: validator agrees and executable checks pass) and
    eligible (after human adjudication of the validator's flags). Returns the same dict, annotated."""
    adj = yaml.safe_load((HERE / "adjudication.yaml").read_text()) or {}
    keep = adj.get("keep_when_validator_said", {})
    exclude = adj.get("exclude", {})
    for cid, c in cases.items():
        executable_ok = c.get("defective_reason") is None
        agrees = c.get("validator") == PLANTED[c["condition"]]
        c["eligible_primary"] = executable_ok and agrees and cid not in exclude
        if cid in exclude:
            c["eligible"], c["adjudication"] = False, exclude[cid]
        elif not executable_ok:
            c["eligible"], c["adjudication"] = False, c["defective_reason"]
        elif agrees:
            c["eligible"], c["adjudication"] = True, "validator agreed with the planted condition"
        else:
            reason = keep.get(f"{c['condition']}/{c['validator']}")
            c["eligible"] = reason is not None
            c["adjudication"] = reason or f"validator said {c['validator']}; not adjudicated, excluded"
    return cases


def severity(case: dict[str, Any], answer: dict[str, Any]) -> str:
    return _severity(case["expected"], answer.get("choice"), CAUTIOUS, PROCEED)


def tree() -> tuple[dict[str, dict[str, Any]], dict[tuple, str]]:
    """The hypothesis tree as {node: {title, parent}} and the map from (family, condition) cells to leaves. Every
    case must be claimed by exactly one key question, or this raises."""
    spec = yaml.safe_load((HERE / "hypotheses.yaml").read_text())
    nodes: dict[str, dict[str, Any]] = {spec["objective"]["id"]: {"title": spec["objective"]["title"]}}
    for hid, h in spec["hypotheses"].items():
        nodes[hid] = {"title": h["title"], "parent": spec["objective"]["id"]}
        for qid, q in h["questions"].items():
            nodes[qid] = {"title": q["title"], "parent": hid}
    cases = load_cases()
    split = partition(cases.values(), rules(spec))
    if not split.ok:
        raise ValueError(
            f"the tree does not partition the cases: {len(split.unclaimed)} unclaimed, "
            f"{len(split.claimed_twice)} claimed twice, e.g. {list(split.claimed_twice.items())[:2]}"
        )
    cell_map = {(c["family"], c["condition"]): split.leaf_of[cid] for cid, c in cases.items()}
    return nodes, cell_map


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
