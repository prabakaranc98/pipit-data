# Study B1: does adaptive spending beat an even spread, without more false claims?

Written 2026-11-01, before any run. Experiment E1 in `docs/engine.md`; issues #8 and #9.

## Subjects

Synthetic subjects with a planted failure surface: twelve key questions, each with a true failure rate. Every unit
fails independently at its question's rate. The rates avoid the gap between the clear threshold (15%) and the
limitation threshold (20%), so every question has a right verdict: supported when the rate is above 20%, refuted when
below 15%.

| Surface | Planted rates |
| --- | --- |
| mixed | 0.60, 0.45, 0.35, 0.30, 0.25, 0.12, 0.10, 0.08, 0.05, 0.03, 0.01, 0.00 |
| mostly clean | 0.40, 0.05, 0.04, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.00, 0.00, 0.00 |
| near the line | 0.30, 0.28, 0.26, 0.25, 0.30, 0.12, 0.11, 0.10, 0.10, 0.09, 0.08, 0.10 |

## Policies, at equal budget

- **Even:** the budget split equally across the twelve questions, as P1 did.
- **Thresholding:** a pilot of three units per question, then each next unit to the unsettled question with the
  smallest sqrt(n) * (|rate - 0.175| + 0.02); a question stops receiving units once settled.

Budgets of 60, 120 and 240 independent units; 300 runs per setting, seeded.

## Measures, per setting

- Questions settled with the right verdict, on average.
- False claims per run: a question supported when its rate is below 15%, or refuted when above 20%.
- The share of runs with at least one false claim.
- Units actually spent: the thresholding policy stops when every question is settled.

## What would count

Adaptive spending wins if it settles more questions at equal budget without raising the false claims. If it settles
more but also claims falsely more often, the fixed-sample intervals are the problem, and issue #25 is next.

## Amendment, after the first run

The thresholding rule starved the easy questions and raised false claims. A third policy, written for Pipit's
interval-based verdicts, is added before the second run: after the pilot, each next unit goes to the open question
that would settle soonest if its observed rate held. Both runs are reported.

## Second amendment, after the second run

Nearest-to-settle settled far more questions but stopped on ordinary intervals and claimed falsely in up to a
quarter of runs. Both the even spread and nearest-to-settle are run a third time with the node rule reading a
confidence sequence, `pipit.sequential`, that stays valid when a question stops early. All three runs are reported.
