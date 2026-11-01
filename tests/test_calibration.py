import math

import pytest

from pipit.calibration import (
    binom_cdf,
    brier,
    cases_needed,
    certify,
    ece,
    review_band,
    top_probability,
    upper_bound,
    vendor_confidence,
)


def test_binomial_and_bounds() -> None:
    assert binom_cdf(0, 10, 0.5) == pytest.approx(1 / 1024)
    assert binom_cdf(10, 10, 0.3) == 1.0 and binom_cdf(-1, 10, 0.3) == 0.0
    assert upper_bound(0, 299) <= 0.01 < upper_bound(0, 298)
    assert upper_bound(3, 100) > 0.03 and upper_bound(3, 100) > upper_bound(3, 200)
    assert upper_bound(5, 100) > upper_bound(3, 100)
    assert upper_bound(4, 4) == 1.0 and upper_bound(0, 0) == 1.0


def test_cases_needed_follows_the_rule_of_three() -> None:
    assert cases_needed(0.05) == 59
    assert cases_needed(0.01) == 299
    assert cases_needed(0.01, events=1) > 299


def test_confidence_readers() -> None:
    assert top_probability({"a": 0.6, "b": 0.3, "c": 0.1}) == 0.6
    assert vendor_confidence({"a": 0.6, "b": 0.3, "c": 0.1}) == pytest.approx(0.4)
    assert vendor_confidence({"a": 1.0}) == 1.0


def test_ece_and_brier() -> None:
    assert ece([0.9] * 10, [True] * 9 + [False]) == pytest.approx(0.0)
    assert ece([0.9] * 10, [True] * 5 + [False] * 5) == pytest.approx(0.4)
    assert brier([{"a": 1.0, "b": 0.0}], ["a"]) == 0.0
    assert brier([{"a": 1.0, "b": 0.0}], ["b"]) == 2.0


def test_review_band_is_cumulative_and_handles_ties() -> None:
    rows = review_band([0.9, 0.9, 0.8, 0.5], [False, True, False, True], [False, True, False, False])
    assert [r.automated for r in rows] == [2, 3, 4]
    assert [r.silent_errors for r in rows] == [1, 1, 2]
    assert [r.silent_unsafe for r in rows] == [1, 1, 1]


def test_certify_stops_where_errors_start_and_refuses_on_too_few_cases() -> None:
    scores = [1 - i / 1000 for i in range(400)]
    losses = [False] * 300 + [True] * 100
    cert = certify(scores, losses, alpha=0.05)
    assert cert.certified and 300 <= cert.automated <= 315 and cert.silent_errors <= 13
    assert cert.silent_upper <= 0.05 + 1e-9
    tiny = certify([0.9] * 10, [False] * 10, alpha=0.05)
    assert not tiny.certified and tiny.automated == 0 and tiny.threshold == math.inf
