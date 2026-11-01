"""Checks before a run: the rules a study promises, checked before the first call is paid for.

A run that breaks them measures something other than what its report says. A model served by many
providers belongs to no single deployment; a helper of the candidate's own family keeps what that family
reads well; a key that runs out halfway records refusals as failures. Study V1 met all three.

    >>> from pipit.manifest import Manifest
    >>> m = Manifest(name="judge", id="vendor/model", revision="as-served", adapter="a:b", placement="api",
    ...              family="vendor")
    >>> [p.rule for p in problems([m])]
    ['provider']
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pipit.manifest import Manifest, family_conflicts

__all__ = ["PreflightError", "Problem", "estimated_usd", "pinned", "problems", "require"]


@dataclass(frozen=True)
class Problem:
    model: str
    rule: str
    detail: str


class PreflightError(RuntimeError):
    """A run was stopped before its first call because a check failed."""


def pinned(manifest: Manifest) -> bool:
    """Whether an API model's requests name the providers to use, in order, and forbid falling back to others.

    >>> pinned(Manifest(name="m", id="v/m", revision="r", adapter="a:b", placement="api",
    ...                 settings={"request": {"provider": {"order": ["Alibaba"], "allow_fallbacks": False}}}))
    True
    """
    provider = manifest.settings.get("request", {}).get("provider", {})
    return bool(provider.get("order")) and provider.get("allow_fallbacks") is False


def problems(
    candidates: Iterable[Manifest], helpers: Iterable[Manifest] = (), *, allow_unpinned: bool = False
) -> list[Problem]:
    """Every rule the models of a run break: a family not declared, an API model not pinned to a provider
    (unless `allow_unpinned`, which a report must then state), and a helper or judge sharing a candidate's
    family."""
    candidates, helpers = list(candidates), list(helpers)
    found = []
    for m in candidates + helpers:
        if not m.family:
            found.append(
                Problem(m.name, "family", "no family declared, so the family rule cannot be checked")
            )
        if m.placement == "api" and not allow_unpinned and not pinned(m):
            found.append(
                Problem(
                    m.name,
                    "provider",
                    "not pinned: set settings.request.provider.order and allow_fallbacks: false",
                )
            )
    for helper, candidate, family in family_conflicts(candidates, helpers):
        found.append(Problem(helper, "family rule", f"shares the {family} family with candidate {candidate}"))
    return found


def estimated_usd(manifest: Manifest, calls: int, tokens_in: int, tokens_out: int) -> float | None:
    """An upper bound on what `calls` requests cost at the manifest's prices, taking every reply at
    `tokens_out`; None when the manifest has no prices. Replies already in the cache cost nothing, so the
    bound is generous.

    >>> m = Manifest(name="m", id="v/m", revision="r", adapter="a:b", placement="api",
    ...              price_usd_per_million_in=1.0, price_usd_per_million_out=2.0)
    >>> estimated_usd(m, calls=1000, tokens_in=500, tokens_out=1000)
    2.5
    """
    if manifest.price_usd_per_million_in is None or manifest.price_usd_per_million_out is None:
        return None
    per_call = tokens_in * manifest.price_usd_per_million_in + tokens_out * manifest.price_usd_per_million_out
    return calls * per_call / 1e6


def require(
    candidates: Iterable[Manifest],
    helpers: Iterable[Manifest] = (),
    *,
    allow_unpinned: bool = False,
    cost: float | None = None,
    budget: float | None = None,
) -> None:
    """Raise PreflightError naming every problem, and when the estimated `cost` is above the `budget` left on
    the key. A budget of None means the key has no limit."""
    lines = [
        f"{p.model}: {p.rule}: {p.detail}"
        for p in problems(candidates, helpers, allow_unpinned=allow_unpinned)
    ]
    if cost is not None and budget is not None and cost > budget:
        lines.append(f"the run may cost up to ${cost:.2f}, more than the ${budget:.2f} left on the key")
    if lines:
        raise PreflightError("Checks before the run failed:\n  " + "\n  ".join(lines))
