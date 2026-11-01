"""Checks before a run: the rules a study promises, checked before the first call is paid for.

A run that breaks them measures something other than what its report says. A model served by many
providers belongs to no single deployment; a helper of the candidate's own family keeps what that family
reads well; a key that runs out halfway records refusals as failures. Study V1 met all three.

    >>> from pipit.manifest import Manifest
    >>> m = Manifest(name="judge", id="vendor/model", revision="as-served", placement="api", family="vendor",
    ...              adapter="pipit.adapters.openrouter:load", price_usd_per_million_in=1.0,
    ...              price_usd_per_million_out=2.0)
    >>> [p.rule for p in problems([m])]
    ['provider']
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlparse

from pipit.manifest import Manifest, family_conflicts

__all__ = ["PreflightError", "Problem", "estimated_usd", "pinned", "problems", "provider_varies", "require"]


@dataclass(frozen=True)
class Problem:
    model: str
    rule: str
    detail: str


class PreflightError(RuntimeError):
    """A run was stopped before its first call because a check failed."""


def provider_varies(manifest: Manifest) -> bool:
    """Whether the service behind the adapter picks a provider for each call. Today that is OpenRouter,
    through its own adapter or through `openai_compat` with an openrouter.ai `base_url`; a vendor's own API,
    such as TypeSafe's, serves every call itself, so it has nothing to pin."""
    if manifest.adapter.startswith("pipit.adapters.openai_compat"):
        host = urlparse(str(manifest.settings.get("base_url", ""))).hostname or ""
        return host == "openrouter.ai" or host.endswith(".openrouter.ai")
    return manifest.adapter.startswith("pipit.adapters.openrouter")


def pinned(manifest: Manifest) -> bool:
    """Whether an API model's requests name exactly one provider and forbid falling back to any other.

    >>> pinned(Manifest(name="m", id="v/m", revision="r", adapter="a:b", placement="api",
    ...                 settings={"request": {"provider": {"order": ["Alibaba"], "allow_fallbacks": False}}}))
    True
    >>> pinned(Manifest(name="m", id="v/m", revision="r", adapter="a:b", placement="api",
    ...                 settings={"request": {"provider": {"order": ["A", "B"], "allow_fallbacks": False}}}))
    False
    """
    provider = manifest.settings.get("request", {}).get("provider", {})
    return len(provider.get("order") or []) == 1 and provider.get("allow_fallbacks") is False


def problems(
    candidates: Iterable[Manifest], helpers: Iterable[Manifest] = (), *, allow_unpinned: bool = False
) -> list[Problem]:
    """Every rule the models of a run break: a family not declared; a model whose provider varies per call
    that is not pinned to one (unless `allow_unpinned`, which the run must record) or has no prices to
    estimate its cost; and a helper or judge sharing a candidate's family.

    A known limit: the price rule also stops a run that would replay every reply from the cache, which costs
    nothing; give the manifest its prices to run it."""
    candidates, helpers = list(candidates), list(helpers)
    found = []
    for m in candidates + helpers:
        if not m.family:
            found.append(
                Problem(m.name, "family", "no family declared, so the family rule cannot be checked")
            )
        if (
            m.placement == "api"
            and provider_varies(m)
            and (m.price_usd_per_million_in is None or m.price_usd_per_million_out is None)
        ):
            found.append(Problem(m.name, "price", "no prices, so the cost of the run cannot be estimated"))
        if m.placement == "api" and provider_varies(m) and not allow_unpinned and not pinned(m):
            found.append(
                Problem(
                    m.name,
                    "provider",
                    "not pinned: set settings.request.provider.order to one provider, allow_fallbacks: false",
                )
            )
    for helper, candidate, family in family_conflicts(candidates, helpers):
        found.append(Problem(helper, "family rule", f"shares the {family} family with candidate {candidate}"))
    return found


def estimated_usd(manifest: Manifest, calls: int, tokens_in: int, tokens_out: int) -> float | None:
    """An estimate of what `calls` requests cost at the manifest's prices, taking every prompt at `tokens_in`
    and every reply at `tokens_out`; None when the manifest has no prices. It is not a guarantee: prompts can
    run longer, and some providers let reasoning run past the reply cap. Cached replies cost nothing.

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
        lines.append(f"the run is estimated at ${cost:.2f}, more than the ${budget:.2f} left on the key")
    if lines:
        raise PreflightError("Checks before the run failed:\n  " + "\n  ".join(lines))
