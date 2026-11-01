# Study V1: do Pipit's written cases rank models the way MedCalc-Bench's real notes do?

Written 2026-11-01, before any run. Issue #57.

## Why

Every Pipit result so far is on cases we wrote. MedCalc-Bench (Khandekar et al., 2024; NCBI; CC BY-SA 4.0) has 1,100
clinical calculation items in its v1.2 test set, 677 of them on real patient notes from published case reports, with
answers computed by formula and published accuracy per model. If Pipit's planted-truth clinical cases rank models
the way MedCalc-Bench does, they measure something real; where they disagree, we learn how.

## Models

Six, through OpenRouter, each in its provider's default setup: Llama 3.1 70B, Qwen3.5 9B, 27B and 397B, DeepSeek V4.1
Flash and V4 Pro.

## MedCalc-Bench arm

- Items: v1.2's test set, four per calculator, drawn with a fixed seed: 220 items. The row numbers are committed;
  the data is downloaded from the Hub at run time and not redistributed.
- Prompt: the paper's zero-shot chain of thought, its system and user text quoted exactly.
- Scoring, written from the dataset card's rules: the reply's "answer" value; decimals right within the card's lower
  and upper limits (95% to 105% of the truth); integers and dates exact.
- Reproduction check: Llama 3.1 70B against the paper's Llama 3 70B, 35.53% overall on v1.0's 1,047 items. The model
  and the data version both differ, so only a large gap would signal a broken harness.

## Pipit arm

P1's 112 adjudicated cases, the decision question rendered as P1's adapter renders it, the letter parsed from the
reply. Failures counted once per independent case, overall and for the computing hypothesis.

## Measures

- Per model: MedCalc-Bench accuracy with a Wilson interval, overall and per category; P1 accuracy counted once per
  case, overall and for computing.
- Rank agreement across the six models: Spearman's correlation between MedCalc-Bench and P1 accuracy, and between
  MedCalc-Bench's lab and dosage accuracy and P1's computing accuracy, each with an exact one-sided permutation test.

## Known limits

Six models is little for a correlation: only a strong agreement can show. Hosted models change without notice; each
call records the provider that served it.

## Amendment, before the second batch ran

Six of the newest small and medium open models are added, before any result from the first batch was read: Qwen 3.8
27B (August 2026), Qwen 3.6 35B with 3B active, Gemma 4 31B and Gemma 4 26B with 4B active (April 2026), Granite 4.2
8B (August 2026) and Liquid LFM 2.5 24B with 2B active (October 2026). With twelve models the permutation test runs
over 100,000 seeded random orderings instead of every ordering.
