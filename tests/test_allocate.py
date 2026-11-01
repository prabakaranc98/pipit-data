"""The allocation policies' mechanics. Whether a policy helps is the bench's question, in studies/b1_bench,
not a test's."""

from pipit.allocate import even, nearest_to_settle, status, thresholding, units_to_settle


def test_status_matches_the_node_rule() -> None:
    assert status(10, 10) == "supported"
    assert status(0, 22) == "refuted" and status(0, 21) == "insufficient"
    assert status(1, 5) == "insufficient" and status(0, 0) == "insufficient"


def test_even_spreads_the_remainder_over_the_first_questions() -> None:
    assert even(["a", "b", "c"], 10) == {"a": 4, "b": 3, "c": 3}


def test_thresholding_pilots_first_then_takes_the_closest_open_question() -> None:
    assert thresholding({"a": (0, 3), "b": (0, 1)}) == "b"
    counts = {"far": (0, 3), "near": (1, 6), "settled": (10, 10)}
    assert thresholding(counts) == "near"
    assert thresholding({"a": (10, 10), "b": (0, 30)}) is None


def test_units_to_settle_follows_the_wilson_bounds() -> None:
    assert units_to_settle(0, 3) == 19  # 0 failures in 22 clears the 15% upper bound
    assert units_to_settle(0.5 * 4, 4) is not None and units_to_settle(0.5 * 4, 4) < 19
    assert units_to_settle(0.17 * 100, 100) is None  # between the thresholds it never settles
    assert units_to_settle(0, 0) is None


def test_nearest_to_settle_prefers_the_question_closest_to_a_verdict() -> None:
    assert nearest_to_settle({"a": (0, 2), "b": (0, 9)}) == "a"
    counts = {"clean": (0, 18), "half": (2, 4), "stuck": (17, 100)}
    assert nearest_to_settle(counts) == "half"
    assert nearest_to_settle({"stuck": (17, 100), "stuck_too": (34, 200)}) == "stuck"
    assert nearest_to_settle({"a": (10, 10), "b": (0, 30)}) is None
