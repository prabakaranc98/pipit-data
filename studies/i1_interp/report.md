# Study I1: does Qwen3.5-4B hold the planted fact when its decision ignores it?

74 critical and benign cases from P1 (39 independent). Setup in `preregistration.md`. The option chosen here agrees with P1's recorded answer on 73/74 cases.

## The probe: is the fact readable at the decision point?

Held-out accuracy of a ridge probe for critical against benign, at the last prompt token, leaving one family out at a time. Counted once per independent case. Split by whether P1's decision on the case was right.

| layer | all cases | where P1 decided right | where P1 decided wrong |
|---|---|---|---|
| 0 | 0/39 (0.00–0.09) | 0/26 (0.00–0.13) | 0/13 (0.00–0.23) |
| 4 | 21/39 (0.39–0.68) | 14.5/26 (0.37–0.73) | 6.5/13 (0.26–0.74) |
| 8 | 22.5/39 (0.42–0.72) | 15.5/26 (0.41–0.76) | 7/13 (0.29–0.77) |
| 12 | 21/39 (0.39–0.68) | 15.5/26 (0.41–0.76) | 5.5/13 (0.20–0.68) |
| 16 | 27/39 (0.54–0.81) | 19.5/26 (0.56–0.88) | 7.5/13 (0.32–0.80) |
| 20 | 31/39 (0.64–0.89) | 20/26 (0.58–0.89) | 11/13 (0.58–0.96) |
| 24 | 30/39 (0.62–0.87) | 19/26 (0.54–0.86) | 11/13 (0.58–0.96) |
| 28 | 30.5/39 (0.63–0.88) | 19.5/26 (0.56–0.88) | 11/13 (0.58–0.96) |
| 32 | 30.5/39 (0.63–0.88) | 21/26 (0.62–0.91) | 9.5/13 (0.46–0.90) |

Best layer: 20, held-out accuracy 0.79.

## Patching: where does the last position carry the decision?

19 pairs; 14 kept, whose critical and benign runs differ by more than one logit (cautious minus proceed letter). Share of that gap restored when one layer's last-position output is taken from the critical run; 95% bootstrap interval over pairs.

| layer | share restored |
|---|---|
| 0 | 0.00 (-0.01 to 0.01) |
| 2 | -0.00 (-0.01 to 0.00) |
| 4 | 0.00 (-0.01 to 0.01) |
| 6 | 0.00 (-0.01 to 0.01) |
| 8 | -0.00 (-0.01 to 0.01) |
| 10 | 0.00 (-0.01 to 0.01) |
| 12 | -0.00 (-0.02 to 0.01) |
| 14 | 0.01 (0.00 to 0.02) |
| 16 | 0.03 (0.02 to 0.04) |
| 18 | 0.28 (0.24 to 0.32) |
| 20 | 0.53 (0.49 to 0.56) |
| 22 | 0.51 (0.48 to 0.55) |
| 24 | 0.54 (0.50 to 0.58) |
| 26 | 0.54 (0.51 to 0.57) |
| 28 | 0.63 (0.60 to 0.67) |
| 30 | 0.82 (0.79 to 0.84) |
| 31 | 1.00 (1.00 to 1.00) |

## The Explain step: stating the computed dose

Dose family, critical and benign cases. Right means the planted answer; the gap is the cautious letter's
logit minus the proceed letter's.

| version | right, critical | right, benign | mean gap, critical | mean gap, benign |
|---|---|---|---|---|
| original | 4/4 | 0/3 | 2.88 | 3.08 |
| computed | 4/4 | 0/3 | 2.28 | 2.29 |
| computed and usual | 4/4 | 0/3 | 2.81 | 1.29 |

On the dose family the model withholds in every version, even when the record states the computed dose per kilogram
and the usual dose: the stated facts shift the benign cases' gap by about 1.8 logits but change no decision. In study
X1 the same cases kept withholding when a doctor insisted on giving the dose. Three methods agree: on doses, the
decision is a fixed cautious answer that neither the content, nor stated arithmetic, nor authority moves. Safe in
appearance, it would hold every correct order. Seven cases, two scenarios: a demonstration, not a rate.
