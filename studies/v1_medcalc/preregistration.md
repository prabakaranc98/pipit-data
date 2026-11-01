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

## Amendment, before any accuracy was computed

Written while the batches ran, after the ledger showed that 12 of Qwen3.5 9B's first 219 MedCalc-Bench replies and 4
of Qwen 3.8 27B's first 169 had stopped at the token cap; no reply had been scored yet.

Replies are capped at 4,096 tokens on MedCalc-Bench and 2,048 on P1, and the cap counts any reasoning a provider runs
by default. A reply cut off at the cap, or a call that still fails after four attempts, counts as wrong, as the code
already did. Reasoning models reach the cap more often, so the report adds, per model, how many replies hit the cap
and how many calls failed, and MedCalc-Bench accuracy with those items left out. The rank correlations stay on the
registered scores.

Found while writing this: the permutation test returned its p-value with a note on how it was computed, and the
report did not unpack it, so the analysis would have stopped at the correlations. Fixed before the first analysis.

## Amendment, before any accuracy was computed: an audit of MedCalc-Bench's answer key

Krohn-Grimberghe (2026), "MedCalc-Bench Doesn't Measure What You Think" (arXiv 2603.02222), audited the code behind
all 55 calculators on the 1,100-row test split and reports "fixing over 20 errors ranging from critical formula
inaccuracies to runtime bugs". It names 19 calculators. For two, the Charlson Comorbidity Index and APACHE II, it says
the error changes the answer for every patient it touches; for the others it does not say how many test answers
change, and no corrected labels are linked. Found by a literature search on 2026-11-01, while the runs were going.

The 19 calculators, as named in the test set: APACHE II Score; CKD-EPI Equations for Glomerular Filtration Rate; CURB-65 Score for Pneumonia Severity; Charlson Comorbidity Index (CCI); Child-Pugh Score for Cirrhosis Mortality; Fibrosis-4 (FIB-4) Index for Liver Fibrosis; Framingham Risk Score for Hard Coronary Heart Disease; Glasgow Coma Score (GCS); Glasgow-Blatchford Bleeding Score (GBS); HEART Score for Major Cardiac Events; HOMA-IR (Homeostatic Model Assessment for Insulin Resistance); MDRD GFR Equation; MELD Na (UNOS/OPTN); Morphine Milligram Equivalents (MME) Calculator; QTc Framingham Calculator; Revised Cardiac Risk Index for Pre-Operative Risk; SIRS Criteria; Sequential Organ Failure Assessment (SOFA) Score; Steroid Conversion Calculator. They hold 76 of the 220 items.

The registered scores stay on all 220 items. The report adds, per model, accuracy on the 144 items from the other 36
calculators and on the 76 audited items alone, and the rank correlation with P1 using the 144. A reader can then see
how much a possibly wrong answer key could move each result.
