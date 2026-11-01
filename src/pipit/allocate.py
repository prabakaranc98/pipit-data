"""Where the next cases go. A study spends its budget across the key questions of its tree; a policy
sees only the counts so far, independent units and failures per question, and names the question to sample
next.

- `even`: the same number of units for every question, fixed in advance. P1 spent its budget this way.
- `thresholding`: a short pilot for every question, then the next unit goes to the unsettled question whose
  estimate sits closest to the threshold relative to how much evidence it has, by the index
  sqrt(n) * (|rate - threshold| + eps) of the anytime parameter-free thresholding rule (Locatelli, Gutzeit and
  Carpentier, 2016; not yet read for this project). A question stops receiving units once it is settled.

Stopping a question as soon as its interval clears is optional stopping: with fixed-sample intervals it can
raise the false-claim rate. The bench measures by how much; intervals valid under early stopping are #25."""

from __future__ import annotations

import math
from collections.abc import Mapping

from pipit.checks import wilson

LIMITATION, CLEAR = 0.20, 0.15


def status(fail: float, n: float, limitation: float = LIMITATION, clear: float = CLEAR) -> str:
    """The node rule: supported when the lower bound clears `limitation`, refuted when the upper bound stays
    below `clear`, insufficient otherwise."""
    if n == 0:
        return "insufficient"
    lo, hi = wilson(fail, n)
    if lo > limitation:
        return "supported"
    if hi < clear:
        return "refuted"
    return "insufficient"


def even(questions: list[str], budget: int) -> dict[str, int]:
    """Units per question when the budget is spread evenly, the remainder going to the first questions."""
    base, extra = divmod(budget, len(questions))
    return {q: base + (i < extra) for i, q in enumerate(questions)}


def thresholding(
    counts: Mapping[str, tuple[float, int]],
    pilot: int = 3,
    threshold: float = (LIMITATION + CLEAR) / 2,
    eps: float = 0.02,
) -> str | None:
    """The question to sample next, given {question: (failures, units)}; None when every question is settled.
    Questions below the pilot size come first, in order."""
    for q, (_, n) in counts.items():
        if n < pilot:
            return q
    open_questions = [q for q, (f, n) in counts.items() if status(f, n) == "insufficient"]
    if not open_questions:
        return None
    return min(
        open_questions,
        key=lambda q: math.sqrt(counts[q][1]) * (abs(counts[q][0] / counts[q][1] - threshold) + eps),
    )


def units_to_settle(fail: float, n: int, cap: int = 4000) -> int | None:
    """If the observed rate held, how many more units until the question settles; None when it never would,
    because the rate sits between the two thresholds. Wilson bounds tighten as units grow, so a binary search
    finds the smallest total."""
    if n == 0:
        return None
    rate = fail / n
    if status(rate * cap, cap) == "insufficient":
        return None
    lo, hi = n, cap
    while lo < hi:
        mid = (lo + hi) // 2
        if status(rate * mid, mid) == "insufficient":
            lo = mid + 1
        else:
            hi = mid
    return lo - n


def nearest_to_settle(counts: Mapping[str, tuple[float, int]], pilot: int = 3) -> str | None:
    """The question to sample next: after a pilot, the open question that would settle soonest if its rate
    held. Open questions that could never settle at their current rate are sampled only when nothing else is
    left, fewest units first. None when every question is settled."""
    for q, (_, n) in counts.items():
        if n < pilot:
            return q
    open_questions = [q for q, (f, n) in counts.items() if status(f, n) == "insufficient"]
    if not open_questions:
        return None
    reachable = {q: units_to_settle(*counts[q]) for q in open_questions}
    finite = [q for q in open_questions if reachable[q] is not None]
    if finite:
        return min(finite, key=lambda q: reachable[q])
    return min(open_questions, key=lambda q: counts[q][1])
