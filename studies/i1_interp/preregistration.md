# Study I1: does Qwen3.5-4B hold the planted fact when its decision ignores it?

Written 2026-11-01, before any run. The first interpretability study on Pipit's minimal pairs.

## Why

P1 found that Qwen3.5-4B often reads the clinical fact correctly when asked about it, yet decides wrong. Two
readings fit that: the fact never reaches the place where the decision is made, or it is there and the decision
does not use it. Minimal pairs with planted truth can tell these apart, and Pipit has them.

## Data

P1's adjudicated cases in the critical and benign conditions: the same scenario with the planted fact present, so the
plan is unsafe, or absent, so it is safe. Both wordings; the independent unit is the scenario under one condition.

## Model and prompt

Qwen3.5-4B at P1's revision, in PyTorch on this Mac's GPU, BF16, thinking off. The prompt is exactly what P1's adapter
sent: the record, the decision question, the lettered options, "Answer with the letter only", in the model's chat
template. Check before anything else: the option chosen here agrees with P1's recorded answer on most cases.

## Semantic: a probe

At the last prompt token, for each of the 33 hidden-state layers, a ridge classifier (penalty 1, features standardised
on the training folds) predicts critical against benign. Folds leave one family out, so the probe must work on a
surface it never saw. Reported per layer: held-out accuracy with a Wilson interval over units, and accuracy split by
whether P1's decision on that case was right or wrong.

If the probe reads the fact as well on the wrong decisions as on the right ones, the fact reaches the decision point
and is not used.

## Mechanistic: patching the last position

For each scenario with both a critical and a benign wording-0 case, the logit difference is the cautious option's
letter minus the proceed option's letter. For each layer, the benign run's last-position state is replaced by the
critical run's, and the share of the gap restored is recorded. Pairs whose two runs differ by under one logit are
left out, since there is nothing to restore. Reported: mean share restored per layer, with a bootstrap interval over
pairs.

## Known limits

- Only the last position is patched, so this shows where the decision is gathered at the readout, not which earlier
  tokens carry the fact.
- About 20 pairs; the intervals will be wide.
- PyTorch on MPS and MLX can differ slightly in BF16; the agreement check measures how much.

## Amendment, the Explain step, before its run

The dose family's decision barely moved between a safe and a double dose. Three causes fit: the model cannot do the
arithmetic, does not know the usual dose, or does not act on a fact once stated. On the dose family's critical and
benign cases, each wording, the record gets one added line in two versions: the computed dose per kilogram only; and
the computed dose with the usual dose. Reported per case: the option chosen and the cautious-minus-proceed logit
difference, in the original and in each version. Two scenarios and eight cases: counts and logit shifts only, no
significance claimed.
