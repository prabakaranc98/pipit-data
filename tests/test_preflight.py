import pytest

from pipit.manifest import Manifest
from pipit.preflight import PreflightError, estimated_usd, pinned, problems, require


def _model(
    name="m",
    placement="api",
    family="vendor",
    provider=None,
    prices=(1.0, 2.0),
    adapter="pipit.adapters.openrouter:load",
):
    settings = {"request": {"provider": provider}} if provider is not None else {}
    return Manifest(
        name=name,
        id=f"vendor/{name}",
        revision="as-served",
        adapter=adapter,
        placement=placement,
        family=family,
        price_usd_per_million_in=prices[0],
        price_usd_per_million_out=prices[1],
        settings=settings,
    )


PIN = {"order": ["Alibaba"], "allow_fallbacks": False}


def test_a_model_is_pinned_only_with_an_order_and_no_fallbacks() -> None:
    assert pinned(_model(provider=PIN))
    assert not pinned(_model())
    assert not pinned(_model(provider={"order": ["Alibaba"]}))  # fallbacks allowed by default
    assert not pinned(_model(provider={"allow_fallbacks": False}))


def test_problems_name_each_broken_rule() -> None:
    assert problems([_model(provider=PIN)]) == []
    assert [p.rule for p in problems([_model()])] == ["provider"]
    assert problems([_model()], allow_unpinned=True) == []
    assert problems([_model(placement="local")]) == []  # a local model has no provider to pin
    assert [p.rule for p in problems([_model(family=None, provider=PIN)])] == ["family"]
    judge = _model("judge", family="vendor", provider=PIN)
    found = problems([_model(provider=PIN)], [judge])
    assert [(p.model, p.rule) for p in found] == [("judge", "family rule")]


def test_the_cost_bound_and_the_budget() -> None:
    assert estimated_usd(_model(), calls=1000, tokens_in=500, tokens_out=1000) == 2.5
    assert estimated_usd(_model(prices=(None, None)), calls=10, tokens_in=1, tokens_out=1) is None
    require([_model(provider=PIN)], cost=2.0, budget=5.0)
    require([_model(provider=PIN)], cost=2.0, budget=None)  # a key with no limit
    with pytest.raises(PreflightError, match="more than the \\$1.00 left"):
        require([_model(provider=PIN)], cost=2.0, budget=1.0)
    with pytest.raises(PreflightError, match="not pinned"):
        require([_model()])


def test_pinning_means_one_provider_and_applies_only_where_the_provider_varies() -> None:
    assert not pinned(_model(provider={"order": ["A", "B"], "allow_fallbacks": False}))
    jev = _model("jev", adapter="pipit.adapters.typesafe:load", prices=(None, None))
    assert problems([jev]) == []  # a vendor's own API serves every call itself
    unpriced = _model(provider=PIN, prices=(None, None))
    assert [p.rule for p in problems([unpriced])] == ["price"]
