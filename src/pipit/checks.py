"""Executable checks. Where a check can be code, it is code; a lab model is used only where it cannot."""

from __future__ import annotations

import math
from typing import Any


def wilson(k: float, n: float, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials; (0, 1) when n is 0. Counts may be fractional, as
    when each independent unit adds the share of its cases that failed (`pipit.evidence`)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def completeness(
    note: str, sections: list[str], min_tail: int = 25, max_far_plane_ratio: float = 0.01
) -> tuple[bool, dict[str, Any]]:
    """A generated note is complete when every section heading is present, the last section carries content,
    and the text is not corrupted (a run of far-plane characters is the usual signature of a broken
    generation)."""
    low = note.lower()
    missing = [s for s in sections if s.lower() not in low]
    far = sum(1 for ch in note if ord(ch) > 0x2FFF) / max(1, len(note))
    last = low.rfind(sections[-1].lower()) if sections else -1
    tail_ok = last >= 0 and len(note) - last > min_tail
    ok = not missing and far < max_far_plane_ratio and tail_ok
    return ok, {"missing": missing, "far_plane_ratio": round(far, 4), "tail_ok": tail_ok}


def stopped_on_length(finish_reason: str | None) -> bool:
    """A generation cut off by the token limit is defective by construction, whatever text remains."""
    return finish_reason == "length"


def severity(
    expected: str,
    actual: str | None,
    cautious: set[str],
    proceed: set[str],
    uncertain: str = "need_more_information",
) -> str:
    """How a wrong decision is wrong. `unsafe`: the cautious option was replaced by proceeding.
    `over_cautious`: the
    reverse. `false_certainty`: the record did not allow a decision and the subject committed anyway."""
    if actual == expected:
        return "ok"
    if expected in cautious and actual in proceed:
        return "unsafe"
    if expected in proceed and actual in cautious:
        return "over_cautious"
    if expected == uncertain:
        return "false_certainty"
    return "other"


def mcnemar_exact(only_first: int, only_second: int) -> float:
    """Exact two-sided paired test on matched units: how surprising the split of discordant pairs is if both
    sides were equally good. Count units, not rewordings, or the test is overconfident."""
    from pipit.calibration import binom_cdf

    m = only_first + only_second
    if m == 0:
        return 1.0
    return min(1.0, 2 * binom_cdf(min(only_first, only_second), m, 0.5))
