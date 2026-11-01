"""The confidence sequence: wider than a fixed-sample interval, and valid at every sample size at once."""

import random

from pipit.checks import wilson
from pipit.sequential import confidence_sequence


def test_edges_and_width() -> None:
    assert confidence_sequence(0, 0) == (0.0, 1.0)
    lo, hi = confidence_sequence(0, 60)
    assert lo == 0.0 and 0.06 < hi < 0.1
    assert confidence_sequence(10, 10)[1] == 1.0
    for fail, n in [(0, 22), (5, 10), (30, 100)]:
        s_lo, s_hi = confidence_sequence(fail, n)
        w_lo, w_hi = wilson(fail, n)
        assert s_lo <= w_lo and s_hi >= w_hi  # the price of looking after every case


def test_true_rate_stays_inside_at_every_look_far_more_often_than_with_wilson() -> None:
    rng = random.Random(3)
    rate, runs, looks = 0.3, 300, 200
    left_sequence = left_wilson = 0
    for _ in range(runs):
        fail = 0
        out_s = out_w = False
        for n in range(1, looks + 1):
            fail += rng.random() < rate
            lo, hi = confidence_sequence(fail, n)
            out_s = out_s or not lo <= rate <= hi
            lo, hi = wilson(fail, n)
            out_w = out_w or not lo <= rate <= hi
        left_sequence += out_s
        left_wilson += out_w
    assert left_sequence / runs <= 0.05
    assert left_wilson / runs > 0.2  # checking a fixed-sample interval after every case breaks its promise
