"""Intervals that stay valid when a study looks at its evidence after every case and stops when it likes.

A fixed-sample interval, such as Wilson's, promises 95% coverage at one sample size chosen in advance.
Checking it after every case and stopping when it clears a threshold breaks that promise: study B1 measured
false claims in up to a quarter of runs. A confidence sequence holds at every sample size at once.

Here, for a failure rate: a beta mixture of likelihood ratios, the conjugate-mixture method of Robbins (1970)
and Howard, Ramdas, McAuliffe and Sekhon (2021), not yet read for this project. The sequence is every rate p
whose mixture likelihood ratio stays below 1 / alpha; Ville's inequality bounds the chance that the true rate
ever leaves it by alpha. Counts may be fractional, as when a unit adds the share of its cases that failed."""

from __future__ import annotations

import math
from functools import lru_cache


def _log_mixture_ratio(p: float, fail: float, n: float, a: float, b: float) -> float:
    log_mix = (
        math.lgamma(a + fail)
        + math.lgamma(b + n - fail)
        - math.lgamma(a + b + n)
        - (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
    )
    log_lik = (fail * math.log(p) if fail else 0.0) + ((n - fail) * math.log1p(-p) if n - fail else 0.0)
    return log_mix - log_lik


@lru_cache(maxsize=200_000)
def confidence_sequence(
    fail: float, n: float, alpha: float = 0.05, a: float = 0.5, b: float = 0.5
) -> tuple[float, float]:
    """The bounds on a failure rate after `fail` failures in `n` units, valid at every n at once."""
    if n == 0:
        return (0.0, 1.0)
    target = math.log(1 / alpha)
    rate = min(max(fail / n, 1e-12), 1 - 1e-12)

    def outside(p: float) -> bool:
        return _log_mixture_ratio(p, fail, n, a, b) >= target

    def search(inside: float, edge: float) -> float:
        if not outside(edge):
            return edge
        lo, hi = inside, edge
        for _ in range(50):
            mid = (lo + hi) / 2
            if outside(mid):
                hi = mid
            else:
                lo = mid
        return lo

    lower = 0.0 if fail == 0 else search(rate, 1e-12)
    upper = 1.0 if fail == n else search(rate, 1 - 1e-12)
    return (lower, upper)
