"""Calibration and reliance: when can a model's own confidence let it act alone?

In plain words: sort the cases by how sure the model was of its answer. Above a cut-off the model acts alone;
below it a person decides. A *silent error* is a wrong answer the model handled alone, counted per case
processed. The certificate finds the lowest cut-off at which we can say, at a stated confidence, that silent
errors stay below a stated rate.

Method: an exact binomial test at each cut-off, applied in a fixed sequence from the strictest cut-off
down and stopped at the first cut-off that fails. This is the fixed-sequence procedure of Learn-then-Test
(Angelopoulos, Bates, Candes, Jordan and Lei, 2021; not yet read in full for this project). The guarantee
holds for new cases drawn like the ones measured: a certificate on synthetic cases certifies that case set,
not a deployment.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


def top_probability(probs: dict[str, float]) -> float:
    """How sure the model was of the option it chose."""
    return max(probs.values()) if probs else 0.0


def vendor_confidence(probs: dict[str, float]) -> float:
    """The confidence both vendors document for a choice: (p_top - 1/n) / (1 - 1/n)."""
    n = len(probs)
    if n <= 1:
        return 1.0
    return (max(probs.values()) - 1 / n) / (1 - 1 / n)


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    log_p, log_q = math.log(p), math.log1p(-p)
    log_n = math.lgamma(n + 1)
    total = 0.0
    for i in range(k + 1):
        total += math.exp(log_n - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * log_p + (n - i) * log_q)
    return min(1.0, total)


def upper_bound(k: int, n: int, delta: float = 0.05) -> float:
    """Exact one-sided upper confidence bound (Clopper-Pearson) on a rate after k events in n trials."""
    if n == 0 or k >= n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if binom_cdf(k, n, mid) > delta:
            lo = mid
        else:
            hi = mid
    return hi


def cases_needed(alpha: float, delta: float = 0.05, events: int = 0) -> int:
    """The fewest cases that certify a rate below `alpha` when `events` of them are failures."""
    hi = events + 1
    while upper_bound(events, hi, delta) > alpha:
        hi *= 2
    lo = hi // 2
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if upper_bound(events, mid, delta) <= alpha:
            hi = mid
        else:
            lo = mid
    return hi


def ece(scores: Sequence[float], correct: Sequence[bool], bins: int = 10) -> float:
    """Expected calibration error: the average gap between how sure the model was and how often it was
    right."""
    if not scores:
        return 0.0
    cells = [[0, 0.0, 0.0] for _ in range(bins)]
    for s, c in zip(scores, correct, strict=True):
        cell = cells[min(int(s * bins), bins - 1)]
        cell[0] += 1
        cell[1] += s
        cell[2] += 1.0 if c else 0.0
    n = len(scores)
    return sum(cnt / n * abs(ss / cnt - sc / cnt) for cnt, ss, sc in cells if cnt)


def brier(probabilities: Sequence[dict[str, float]], expected: Sequence[str]) -> float:
    """Mean squared distance between the stated probabilities and the right answer (0 is perfect, 2 is
    worst)."""
    if not expected:
        return 0.0
    total = 0.0
    for probs, exp in zip(probabilities, expected, strict=True):
        options = set(probs) | {exp}
        total += sum((probs.get(o, 0.0) - (1.0 if o == exp else 0.0)) ** 2 for o in options)
    return total / len(expected)


@dataclass(frozen=True)
class BandRow:
    """One cut-off: how many cases the model handles alone, and how many of those are wrong."""

    threshold: float
    automated: int
    silent_errors: int
    silent_unsafe: int
    n: int

    @property
    def automated_rate(self) -> float:
        return self.automated / self.n if self.n else 0.0


def review_band(
    scores: Sequence[float], wrong: Sequence[bool], unsafe: Sequence[bool] | None = None
) -> list[BandRow]:
    """Every distinct cut-off, strictest first, with the cases handled alone and the silent errors among
    them."""
    flags = list(unsafe) if unsafe is not None else [False] * len(scores)
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    rows: list[BandRow] = []
    automated = errors = unsafe_n = i = 0
    n = len(scores)
    while i < n:
        t = scores[order[i]]
        while i < n and scores[order[i]] == t:
            j = order[i]
            automated += 1
            errors += bool(wrong[j])
            unsafe_n += bool(flags[j])
            i += 1
        rows.append(BandRow(t, automated, errors, unsafe_n, n))
    return rows


@dataclass(frozen=True)
class Certificate:
    """The lowest cut-off at which silent errors are certified below `alpha` with confidence 1 - `delta`."""

    alpha: float
    delta: float
    n: int
    certified: bool
    threshold: float
    automated: int
    silent_errors: int

    @property
    def automated_rate(self) -> float:
        return self.automated / self.n if self.n else 0.0

    @property
    def silent_upper(self) -> float:
        return upper_bound(self.silent_errors, self.n, self.delta)


def certify(
    scores: Sequence[float], losses: Sequence[bool], alpha: float, delta: float = 0.05
) -> Certificate:
    """Fixed-sequence test from the strictest cut-off down: reject 'silent errors exceed alpha' while the
    exact binomial p-value P(Binomial(n, alpha) <= k) is at most delta; the last rejected cut-off is
    certified. When even the strictest cut-off fails, nothing is certified: there are too few cases to say
    anything at alpha."""
    n = len(scores)
    best = Certificate(alpha, delta, n, False, math.inf, 0, 0)
    for row in review_band(scores, losses):
        if binom_cdf(row.silent_errors, n, alpha) > delta:
            break
        best = Certificate(alpha, delta, n, True, row.threshold, row.automated, row.silent_errors)
    return best
