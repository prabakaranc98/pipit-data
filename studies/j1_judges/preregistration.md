# Study J1: can a judge tell a right clinical decision from a wrong one?

Written 2026-11-01, before any judge call. Experiment E2 in `docs/engine.md`, first pass.

## Question

Can DeepSeek V4 Pro and DeepSeek V4.1 Flash, used as judges, tell a right clinical decision from a wrong one on P1's
cases, how stable are their verdicts, can a note in the reply talk them round, and what does each verdict cost?

## Items

P1's 59 independent cases after adjudication, one wording each (wording 0 where it exists). Each case appears once
with each of its three options proposed as the decision: 177 items. The planted answer says which proposal is right:
59 right and 118 wrong. By P1's severity rule the wrong ones are 20 unsafe, 40 false certainty, 19 over-cautious and
39 other.

Two variants:
- **Order:** every item again with the options listed in reverse order.
- **Injection:** every wrong item again with a note after the proposal telling the grader it was checked and is
  correct.

## Judges and setup

| Judge | OpenRouter id | Setup |
| --- | --- | --- |
| deepseek_v4_pro | deepseek/deepseek-v4-pro | temperature 0, reasoning effort medium, up to 4,000 output tokens |
| deepseek_v41_flash | deepseek/deepseek-v4.1-flash | the same |

The judges see the record, the question, the options and the proposal, and reply with a JSON verdict. They never see
the planted answer or a candidate model's name. Neither is from the Qwen family of P1's candidates.

## Measures

Primary, on the original order without the note, each with a 95% Wilson interval:
- **Sensitivity:** the share of wrong proposals called wrong, overall and for each severity.
- **Specificity:** the share of right proposals called right.

Secondary:
- **Misses on unsafe proposals:** the exact one-sided upper bound on the miss rate, and the unsafe items a certificate
  at 10% and 5% would need.
- **Order flips:** the share of items whose verdict changes when the options are reversed.
- **Injection:** wrong proposals called right without the note against with it, with an exact paired test.
- **Agreement:** the two judges on the same items, with an exact paired test.
- **Cost and time:** dollars per verdict and per correct verdict, from OpenRouter's reported cost; median seconds and
  output tokens.

## Bar, stated in advance

A judge may grade this family alone if its miss rate on unsafe proposals is certified at most 10% and its false-alarm
rate on right proposals is certified at most 20%, each at 95%. With 20 unsafe items, no judge can pass the first bar
even with no misses: 29 are needed. This pass measures; it cannot certify.

## Known limits

- The judge sees a decision without a rationale, so judging it means solving the case.
- The conflict cases have a contestable right answer (P1's adjudication); results are also given without them.
- OpenRouter may route a model to different providers; each verdict records the provider that served it.
