"""Checks on a hypothesis tree. Each key question claims the cases its rule matches; the tree is only a
partition when every case is claimed by exactly one key question. A rule names the families and the conditions
it covers; leaving either out means any."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Rule:
    leaf: str
    families: frozenset[str] | None = None
    conditions: frozenset[str] | None = None

    def claims(self, case: Mapping[str, Any]) -> bool:
        return (self.families is None or case["family"] in self.families) and (
            self.conditions is None or case["condition"] in self.conditions
        )


@dataclass
class Partition:
    leaf_of: dict[str, str] = field(default_factory=dict)
    unclaimed: list[str] = field(default_factory=list)
    claimed_twice: dict[str, list[str]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.unclaimed and not self.claimed_twice


def rules(spec: Mapping[str, Any]) -> list[Rule]:
    """The key questions of a hypotheses spec: {hypotheses: {H: {questions: {Q: {families, conditions}}}}}."""
    out = []
    for h in spec["hypotheses"].values():
        for qid, q in h["questions"].items():
            fams, conds = q.get("families"), q.get("conditions")
            out.append(Rule(qid, frozenset(fams) if fams else None, frozenset(conds) if conds else None))
    return out


def partition(cases: Iterable[Mapping[str, Any]], leaf_rules: Iterable[Rule]) -> Partition:
    """Which key question claims each case, and which cases are claimed by none or by more than one."""
    leaf_rules = list(leaf_rules)
    result = Partition()
    for case in cases:
        hits = [r.leaf for r in leaf_rules if r.claims(case)]
        if not hits:
            result.unclaimed.append(case["id"])
        elif len(hits) > 1:
            result.claimed_twice[case["id"]] = hits
        else:
            result.leaf_of[case["id"]] = hits[0]
    return result
