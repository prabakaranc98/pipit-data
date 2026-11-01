"""A case and its rewordings are one independent unit. These tests check that intervals, replays and the
certificate count units, and that counting rewordings as separate cases would claim too much."""

import random

from pipit.calibration import binom_cdf, cases_needed, certify
from pipit.checks import mcnemar_exact, wilson
from pipit.evidence import Cell, cases_to_evidence, cells, rollup, unit_share


def _pairs(outcomes: list[bool], family: str = "F1") -> tuple[dict, dict]:
    """Two wordings per scenario, both with the given outcome (True means the model failed)."""
    cases, answers = {}, {}
    for i, bad in enumerate(outcomes):
        for w in (0, 1):
            cid = f"{family}-S{i}-critical-w{w}"
            cases[cid] = {"family": family, "scenario": f"S{i}", "condition": "critical", "wording": w}
            answers[cid] = {"choice": "proceed" if bad else "avoid"}
    return cases, answers


def _failed(case, answer):
    return "unsafe" if answer["choice"] == "proceed" else "ok"


def _unit(case):
    return (case["family"], case["scenario"], case["condition"])


def test_agreeing_rewordings_count_once() -> None:
    cases, answers = _pairs([True, False, False, False])
    key = lambda c: (c["family"], c["condition"])  # noqa: E731
    pooled = cells(cases, answers, key=key, failed=_failed)[("F1", "critical")]
    by_unit = cells(cases, answers, key=key, failed=_failed, unit=_unit)[("F1", "critical")]
    assert (pooled.n, pooled.fail) == (by_unit.n, by_unit.fail) == (8, 2)
    assert (pooled.n_units, pooled.fail_units) == (8, 2.0)
    assert (by_unit.n_units, by_unit.fail_units) == (4, 1.0)
    assert by_unit.interval == wilson(1, 4)
    assert by_unit.interval[1] - by_unit.interval[0] > pooled.interval[1] - pooled.interval[0]


def test_a_split_unit_adds_its_share() -> None:
    assert unit_share({"a": [1, 2], "b": [0, 2], "c": [2, 2]}) == 1.5
    assert Cell(("x",), n=6, fail=3).fail_units == 3.0  # built from counts: each case is a unit


def test_rollup_merges_units_up_the_tree() -> None:
    cases, answers = _pairs([True, True, False])
    more, more_answers = _pairs([False, False], family="F2")
    cases.update(more)
    answers.update(more_answers)
    by_cell = cells(cases, answers, key=lambda c: (c["family"], c["condition"]), failed=_failed, unit=_unit)
    tree = {"O": {"title": "o"}, "Q1": {"title": "q1", "parent": "O"}, "Q2": {"title": "q2", "parent": "O"}}
    nodes = rollup(tree, {("F1", "critical"): "Q1", ("F2", "critical"): "Q2"}, by_cell)
    assert (nodes["O"].n, nodes["O"].fail, nodes["O"].n_units, nodes["O"].fail_units) == (10, 4, 5, 2.0)
    assert nodes["O"].interval == wilson(2, 5)


def test_replay_draws_whole_units_and_counts_cases() -> None:
    cases, answers = _pairs([True] * 6)
    hits = cases_to_evidence(cases, answers, family=lambda c: c["family"], failed=_failed, unit=_unit)
    assert all(h % 2 == 0 for h in hits)  # a unit brings both of its wordings
    assert min(hits) == 8  # four units, not four cases, before the lower bound can clear 0.2
    per_case = cases_to_evidence(cases, answers, family=lambda c: c["family"], failed=_failed)
    assert min(per_case) == 4


def test_certificate_counts_units() -> None:
    def run(units_clean: int) -> tuple[bool, bool]:
        scores = [0.99] * (2 * units_clean)
        losses = [False] * (2 * units_clean)
        units = [i // 2 for i in range(2 * units_clean)]
        return certify(scores, losses, 0.05).certified, certify(scores, losses, 0.05, units=units).certified

    assert cases_needed(0.05) == 59
    assert run(59) == (True, True)  # 59 clean units certify 5%
    assert run(58) == (True, False)  # 116 cases are 58 units: counting cases would certify too early
    losses = [False] * 200
    losses[0] = losses[1] = True  # both wordings of one unit are silent errors
    cert = certify([0.99] * 200, losses, 0.10, units=[i // 2 for i in range(200)])
    assert cert.certified and cert.automated == 200
    assert (cert.units, cert.silent_units, cert.silent_errors) == (100, 1, 2)


def test_paired_test_on_units() -> None:
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(5, 0) == min(1.0, 2 * binom_cdf(0, 5, 0.5))
    # the same 5-to-0 split counted twice, once per wording, looks far more significant than it is
    assert mcnemar_exact(10, 0) < 0.01 < mcnemar_exact(5, 0)


def _clustered(rng: random.Random, units: int, p: float, agree: float) -> list[list[bool]]:
    """Two wordings per unit: each copies the unit's outcome with probability `agree`, else draws afresh.
    Every wording fails with probability p; wordings correlate at agree squared."""
    out = []
    for _ in range(units):
        base = rng.random() < p
        out.append([base if rng.random() < agree else rng.random() < p for _ in range(2)])
    return out


def test_pooled_intervals_undercover_when_rewordings_agree() -> None:
    rng = random.Random(7)
    p, reps, hit_pooled, hit_units = 0.2, 2000, 0, 0
    for _ in range(reps):
        data = _clustered(rng, units=30, p=p, agree=0.9)
        fails = sum(sum(u) for u in data)
        lo, hi = wilson(fails, 60)
        hit_pooled += lo <= p <= hi
        lo, hi = wilson(sum(sum(u) / 2 for u in data), 30)
        hit_units += lo <= p <= hi
    assert hit_pooled / reps < 0.90  # a nominal 95% interval that covers far less often
    assert hit_units / reps >= 0.93


def test_counting_rewordings_certifies_a_model_at_the_limit_too_often() -> None:
    rng = random.Random(11)
    reps, pooled, by_unit = 2000, 0, 0
    units = [i // 2 for i in range(200)]
    for _ in range(reps):
        data = _clustered(rng, units=100, p=0.05, agree=1.0)  # silent errors exactly at the 5% target
        losses = [x for u in data for x in u]
        pooled += certify([0.99] * 200, losses, 0.05).certified
        by_unit += certify([0.99] * 200, losses, 0.05, units=units).certified
    assert pooled / reps > 0.09  # well above the promised 5%
    assert by_unit / reps <= 0.06
