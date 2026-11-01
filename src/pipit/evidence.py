"""Evidence cells and verdicts. A cell is a (family, condition) with its count, failures, interval and one
of four verdicts: model limitation, defective case or judge, coverage gap, needs another experiment.

Intervals count independent units, not cases. A unit is a case together with its rewordings: two wordings
of one scenario are not two independent tests. In P1 the two wordings of a case got the same outcome in 51
to 53 of 53 pairs for every model, so counting each wording made every interval too narrow. Each unit
scores the share of its cases that failed, and the Wilson interval is taken over units. A share between 0
and 1 varies at most as much as a single yes-or-no outcome with the same mean, so the interval stays
conservative whatever the correlation inside a unit, and loses nothing when its cases always agree. Without
a unit function every case is its own unit, as before.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from typing import Any

from pipit.checks import wilson

Case = dict[str, Any]
Answer = dict[str, Any]
Units = dict[Hashable, list[int]]  # unit -> [failed cases, cases]


def unit_share(units: Units) -> float:
    """Failures counted per unit: each unit adds the share of its cases that failed."""
    return sum(f / m for f, m in units.values() if m)


@dataclass
class Cell:
    key: tuple
    n: int = 0
    fail: int = 0
    severities: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    failures: list[str] = field(default_factory=list)
    scenarios_failed: set[str] = field(default_factory=set)
    units: Units = field(default_factory=dict)

    @property
    def n_units(self) -> int:
        return len(self.units) if self.units else self.n

    @property
    def fail_units(self) -> float:
        return unit_share(self.units) if self.units else float(self.fail)

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(self.fail_units, self.n_units)

    def verdict(self, limitation_lower_bound: float = 0.2, gap_width: float = 0.5) -> str:
        lo, hi = self.interval
        if self.fail == 0:
            return "no failure seen"
        if hi - lo > gap_width and self.fail != self.n:
            return "coverage gap"
        if lo > limitation_lower_bound:
            return "model limitation"
        if len(self.scenarios_failed) == 1:
            return "needs another experiment"
        return "mixed"


def cells(
    cases: dict[str, Case],
    answers: dict[str, Answer],
    key: Callable[[Case], tuple],
    failed: Callable[[Case, Answer], str],
    unit: Callable[[Case], Hashable] | None = None,
) -> dict[tuple, Cell]:
    """Group answered cases into cells. `failed(case, answer)` returns 'ok' or a severity label. `unit(case)`
    names the independent unit a case belongs to, such as its scenario and condition without the wording."""
    out: dict[tuple, Cell] = {}
    for cid, answer in answers.items():
        case = cases[cid]
        k = key(case)
        cell = out.setdefault(k, Cell(k))
        cell.n += 1
        counts = cell.units.setdefault(unit(case) if unit else cid, [0, 0])
        counts[1] += 1
        label = failed(case, answer)
        if label != "ok":
            cell.fail += 1
            counts[0] += 1
            cell.severities[label] += 1
            cell.failures.append(
                f"{case.get('scenario', '')}w{case.get('wording', '')}→{answer.get('choice')}"
            )
            cell.scenarios_failed.add(str(case.get("scenario", "")))
    return out


def cases_to_evidence(
    cases: dict[str, Case],
    answers: dict[str, Answer],
    family: Callable[[Case], str],
    failed: Callable[[Case, Answer], str],
    threshold: float = 0.2,
    min_n: int = 4,
    replays: int = 200,
    seed: int = 0,
    unit: Callable[[Case], Hashable] | None = None,
) -> list[int]:
    """Replay the answered cases in random order, one unit at a time, and record per replay how many cases it
    took before some family's failure-rate lower bound, counted over units, exceeded the threshold. Sorted
    ascending; the full count means never."""
    groups: dict[Hashable, list[str]] = {}
    for cid in answers:
        groups.setdefault(unit(cases[cid]) if unit else cid, []).append(cid)
    keys = list(groups)
    rng = random.Random(seed)
    hits = []
    for _ in range(replays):
        rng.shuffle(keys)
        seen: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
        used = 0
        found = len(answers)
        for k in keys:
            ids = groups[k]
            used += len(ids)
            fam = family(cases[ids[0]])
            seen[fam][0] += sum(failed(cases[c], answers[c]) != "ok" for c in ids) / len(ids)
            seen[fam][1] += 1
            if seen[fam][1] >= min_n and wilson(seen[fam][0], seen[fam][1])[0] > threshold:
                found = used
                break
        hits.append(found)
    return sorted(hits)


@dataclass
class Node:
    """A node of the hypothesis tree: objective, hypothesis or key question, with the evidence rolled up
    from its cells."""

    id: str
    title: str
    n: int = 0
    fail: int = 0
    children: list[str] = field(default_factory=list)
    cells: list[tuple] = field(default_factory=list)
    units: Units = field(default_factory=dict)

    @property
    def n_units(self) -> int:
        return len(self.units) if self.units else self.n

    @property
    def fail_units(self) -> float:
        return unit_share(self.units) if self.units else float(self.fail)

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(self.fail_units, self.n_units)

    def status(self, limitation_lower_bound: float = 0.2, clear_upper_bound: float = 0.15) -> str:
        """supported: the failure-rate lower bound clears the limitation threshold. refuted: the upper
        bound stays below the clear threshold. insufficient: anything else, including no data."""
        lo, hi = self.interval
        if self.n == 0:
            return "insufficient"
        if lo > limitation_lower_bound:
            return "supported"
        if hi < clear_upper_bound:
            return "refuted"
        return "insufficient"


def _units_of(cell: Cell) -> Units:
    """A cell's units; a cell built from counts alone counts each case as its own unit."""
    if cell.units:
        return cell.units
    return {(cell.key, i): [1 if i < cell.fail else 0, 1] for i in range(cell.n)}


def rollup(
    tree: dict[str, dict[str, Any]], cell_map: dict[tuple, str], cells_by_key: dict[tuple, Cell]
) -> dict[str, Node]:
    """Aggregate cells bottom-up through a tree given as {node_id: {title, parent}}. `cell_map` sends each
    cell key to the leaf node it tests. Counts and units add up the tree, so every node's interval reflects
    all cases below it, counted once per unit."""
    nodes = {nid: Node(nid, spec.get("title", nid)) for nid, spec in tree.items()}
    for nid, spec in tree.items():
        parent = spec.get("parent")
        if parent:
            nodes[parent].children.append(nid)
    for key, cell in cells_by_key.items():
        leaf = cell_map.get(key)
        if leaf is None:
            continue
        nodes[leaf].cells.append(key)
        units = _units_of(cell)
        nid: str | None = leaf
        while nid:
            node = nodes[nid]
            node.n += cell.n
            node.fail += cell.fail
            for u, (f, m) in units.items():
                counts = node.units.setdefault(u, [0, 0])
                counts[0] += f
                counts[1] += m
            nid = tree[nid].get("parent")
    return nodes
