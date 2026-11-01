# Study V1: do Pipit's written cases rank models the way MedCalc-Bench's real notes do?

Setup in `preregistration.md`. MedCalc-Bench: 220 items, four per calculator. P1: 112 cases, counted once per independent case. Intervals are 95% Wilson.

| model | MedCalc-Bench right | P1 right, per case | P1 computing right | P1 unparsed | USD |
|---|---|---|---|---|---|
| deepseek_v41_flash | 83% (77%–87%) | 90% (80%–95%) | 80% (55%–93%) | 3 | 0.23 |
| deepseek_v4_pro | 80% (74%–84%) | 91% (81%–96%) | 87% (62%–96%) | 0 | 0.72 |
| gemma4_26b_a4b | 58% (52%–65%) | 86% (74%–92%) | 73% (48%–89%) | 0 | 0.04 |
| gemma4_31b | 60% (53%–66%) | 83% (72%–91%) | 77% (51%–91%) | 0 | 0.06 |
| granite42_8b | 22% (17%–28%) | 90% (80%–95%) | 80% (55%–93%) | 3 | 0.08 |
| lfm25_24b_a2b | 48% (41%–54%) | 74% (61%–83%) | 77% (51%–91%) | 16 | 0.42 |
| llama31_70b | 39% (32%–45%) | 82% (71%–90%) | 73% (48%–89%) | 0 | 0.15 |
| qwen35_27b | 79% (73%–84%) | 89% (79%–95%) | 83% (58%–95%) | 0 | 2.19 |
| qwen35_397b | 81% (76%–86%) | 58% (45%–69%) | 83% (58%–95%) | 39 | 1.46 |
| qwen35_9b | 70% (63%–75%) | 75% (62%–84%) | 77% (51%–91%) | 11 | 0.01 |
| qwen36_35b_a3b | 75% (69%–81%) | 87% (76%–94%) | 90% (66%–98%) | 1 | 0.67 |
| qwen38_27b | 72% (66%–77%) | 92% (82%–96%) | 87% (62%–96%) | 6 | 0.85 |

## Replies cut off at the cap, and failed calls

Both count as wrong above. The cap counts any reasoning the provider runs by default: 4,096 tokens on MedCalc-Bench, 2,048 on P1. A failed call failed four times.

| model | MedCalc-Bench cut off | failed | MedCalc-Bench right without them | P1 cut off | failed |
|---|---|---|---|---|---|
| deepseek_v41_flash | 2 | 4 | 85% (80%–89%) | 0 | 3 |
| deepseek_v4_pro | 2 | 3 | 81% (76%–86%) | 0 | 0 |
| gemma4_26b_a4b | 13 | 0 | 62% (55%–68%) | 0 | 0 |
| gemma4_31b | 3 | 0 | 61% (54%–67%) | 0 | 0 |
| granite42_8b | 8 | 97 | 42% (33%–51%) | 1 | 3 |
| lfm25_24b_a2b | 20 | 48 | 69% (61%–76%) | 0 | 16 |
| llama31_70b | 2 | 0 | 39% (33%–46%) | 0 | 0 |
| qwen35_27b | 11 | 4 | 85% (79%–89%) | 0 | 0 |
| qwen35_397b | 1 | 1 | 82% (76%–87%) | 0 | 39 |
| qwen35_9b | 12 | 0 | 74% (67%–79%) | 1 | 11 |
| qwen36_35b_a3b | 16 | 15 | 88% (82%–92%) | 0 | 1 |
| qwen38_27b | 4 | 19 | 80% (74%–85%) | 0 | 6 |

## Calculators whose code an audit corrected

Krohn-Grimberghe (2026) reports fixing errors in the code of 19 of MedCalc-Bench's 55 calculators, without saying how many test answers each changes. Their items are shown apart here; the registered score above keeps them.

| model | all items | without the 19 audited calculators | the 19 audited calculators only |
|---|---|---|---|
| deepseek_v41_flash | 83% (77%–87%) | 87% (80%–91%) | 75% (64%–83%) |
| deepseek_v4_pro | 80% (74%–84%) | 83% (76%–89%) | 72% (61%–81%) |
| gemma4_26b_a4b | 58% (52%–65%) | 62% (54%–69%) | 51% (40%–62%) |
| gemma4_31b | 60% (53%–66%) | 68% (60%–75%) | 45% (34%–56%) |
| granite42_8b | 22% (17%–28%) | 25% (19%–33%) | 16% (9%–26%) |
| lfm25_24b_a2b | 48% (41%–54%) | 55% (47%–63%) | 34% (25%–45%) |
| llama31_70b | 39% (32%–45%) | 44% (36%–52%) | 29% (20%–40%) |
| qwen35_27b | 79% (73%–84%) | 84% (77%–89%) | 70% (59%–79%) |
| qwen35_397b | 81% (76%–86%) | 84% (77%–89%) | 76% (66%–84%) |
| qwen35_9b | 70% (63%–75%) | 83% (76%–88%) | 45% (34%–56%) |
| qwen36_35b_a3b | 75% (69%–81%) | 81% (74%–87%) | 64% (53%–74%) |
| qwen38_27b | 72% (66%–77%) | 80% (73%–86%) | 57% (45%–67%) |

## MedCalc-Bench by category

| model | lab test | physical | dosage | date | risk | severity | diagnosis |
|---|---|---|---|---|---|---|---|
| deepseek_v41_flash | 78% (67%–86%) | 100% (93%–100%) | 62% (31%–86%) | 92% (65%–99%) | 73% (59%–83%) | 94% (72%–99%) | 75% (47%–91%) |
| deepseek_v4_pro | 82% (71%–89%) | 88% (75%–94%) | 50% (22%–78%) | 92% (65%–99%) | 75% (61%–85%) | 75% (51%–90%) | 67% (39%–86%) |
| gemma4_26b_a4b | 57% (45%–67%) | 73% (59%–83%) | 12% (2%–47%) | 83% (55%–95%) | 50% (36%–64%) | 56% (33%–77%) | 50% (25%–75%) |
| gemma4_31b | 64% (53%–74%) | 77% (63%–87%) | 50% (22%–78%) | 92% (65%–99%) | 38% (25%–52%) | 50% (28%–72%) | 42% (19%–68%) |
| granite42_8b | 25% (17%–36%) | 25% (15%–39%) | 12% (2%–47%) | 17% (5%–45%) | 15% (7%–27%) | 12% (3%–36%) | 42% (19%–68%) |
| lfm25_24b_a2b | 46% (35%–57%) | 65% (50%–77%) | 25% (7%–59%) | 67% (39%–86%) | 27% (17%–41%) | 56% (33%–77%) | 58% (32%–81%) |
| llama31_70b | 28% (19%–39%) | 69% (55%–80%) | 12% (2%–47%) | 58% (32%–81%) | 23% (13%–37%) | 25% (10%–49%) | 67% (39%–86%) |
| qwen35_27b | 83% (73%–90%) | 96% (86%–99%) | 50% (22%–78%) | 83% (55%–95%) | 62% (48%–75%) | 75% (51%–90%) | 75% (47%–91%) |
| qwen35_397b | 86% (76%–92%) | 94% (83%–98%) | 38% (14%–69%) | 92% (65%–99%) | 75% (61%–85%) | 50% (28%–72%) | 92% (65%–99%) |
| qwen35_9b | 79% (69%–87%) | 98% (89%–100%) | 38% (14%–69%) | 75% (47%–91%) | 40% (27%–54%) | 31% (14%–56%) | 83% (55%–95%) |
| qwen36_35b_a3b | 78% (67%–86%) | 98% (89%–100%) | 50% (22%–78%) | 83% (55%–95%) | 54% (40%–67%) | 56% (33%–77%) | 92% (65%–99%) |
| qwen38_27b | 79% (69%–87%) | 85% (73%–93%) | 38% (14%–69%) | 92% (65%–99%) | 48% (34%–62%) | 62% (39%–82%) | 83% (55%–95%) |

## Reproduction check

Llama 3.1 70B here against the paper's Llama 3 70B, zero-shot chain of thought on v1.0. The model and the data version both differ.

| | lab test | physical | dosage | date | risk | severity | diagnosis | overall |
|---|---|---|---|---|---|---|---|---|
| this study | 28% | 69% | 12% | 58% | 23% | 25% | 67% | 39% |
| the paper | 34% | 66% | 20% | 25% | 18% | 16% | 37% | 36% |

## Do the two rank the models alike?

Spearman's correlation across 12 models, with a one-sided permutation test over 100,000 random orderings:

- MedCalc-Bench overall against P1 overall: 0.21, p = 0.251.
- MedCalc-Bench lab and dosage against P1's computing hypothesis: 0.61, p = 0.020.
- MedCalc-Bench without the 19 audited calculators against P1 overall: 0.13, p = 0.345.

