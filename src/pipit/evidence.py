"""Evidence cells and verdicts. A cell is a (family, condition) with its count, failures, interval and one
of four
verdicts: model limitation, defective case or judge, coverage gap, needs another experiment."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pipit.checks import wilson

Case = dict[str, Any]
Answer = dict[str, Any]


@dataclass
class Cell:
    key: tuple
    n: int = 0
    fail: int = 0
    severities: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    failures: list[str] = field(default_factory=list)
    scenarios_failed: set[str] = field(default_factory=set)

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(self.fail, self.n)

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
) -> dict[tuple, Cell]:
    """Group answered cases into cells. `failed(case, answer)` returns 'ok' or a severity label."""
    out: dict[tuple, Cell] = {}
    for cid, answer in answers.items():
        case = cases[cid]
        k = key(case)
        cell = out.setdefault(k, Cell(k))
        cell.n += 1
        label = failed(case, answer)
        if label != "ok":
            cell.fail += 1
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
) -> list[int]:
    """Replay the answered cases in random order and record, per replay, how many cases it took before some
    family's failure-rate lower bound exceeded the threshold. Sorted ascending; the full count means never."""
    ids = list(answers)
    rng = random.Random(seed)
    hits = []
    for _ in range(replays):
        rng.shuffle(ids)
        seen: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        found = len(ids)
        for i, cid in enumerate(ids, 1):
            fam = family(cases[cid])
            seen[fam][1] += 1
            seen[fam][0] += failed(cases[cid], answers[cid]) != "ok"
            if seen[fam][1] >= min_n and wilson(seen[fam][0], seen[fam][1])[0] > threshold:
                found = i
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

    @property
    def interval(self) -> tuple[float, float]:
        return wilson(self.fail, self.n)

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


def rollup(
    tree: dict[str, dict[str, Any]], cell_map: dict[tuple, str], cells_by_key: dict[tuple, Cell]
) -> dict[str, Node]:
    """Aggregate cells bottom-up through a tree given as {node_id: {title, parent}}. `cell_map` sends each
    cell key to the leaf node it tests. Counts add up the tree so every node's interval reflects all cases
    below it."""
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
        nid: str | None = leaf
        while nid:
            nodes[nid].n += cell.n
            nodes[nid].fail += cell.fail
            nid = tree[nid].get("parent")
    return nodes
