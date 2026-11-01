## Reading

Written by hand after the analysis ran. The tables above are the record; this section says what they show.

**Overall, the two do not rank the models alike.** Across twelve models, P1's 59 written clinical cases and
MedCalc-Bench's 220 items from published case reports give a Spearman correlation of 0.21 (one-sided p = 0.25), the
registered primary test. P1 is mostly reading a planted fact and deciding, which small models do well; MedCalc-Bench
is mostly calculation. Granite 4.2 8B shows the difference: 90% on P1, 22% on MedCalc-Bench.

**Where the two measure the same mechanism, they agree.** MedCalc-Bench's lab and dosage calculations against P1's
computing questions give 0.61 (p = 0.020), the registered secondary test. A written case set can stand in for a real
benchmark at the level of one mechanism, not as one overall score.

**The token caps shape two results.** Granite 4.2 8B failed or was cut off on 105 of its 220 MedCalc-Bench items, and
Qwen3.5 397B on 39 of its 112 P1 cases, so the registered score partly measures whether a model finishes within the
cap. Not registered, and decided after seeing the results: with cut-off and failed replies set aside on both sides,
the correlation is 0.47 (p = 0.064). Providers did not apply the caps alike; one reply used 12,210 tokens against a
cap of 4,096.

**The overall score is near the paper's, for a different model.** Llama 3.1 70B scores 39% against the paper's 36% for
Llama 3 70B, and the data version differs too. Categories with 8 to 16 items do not reproduce.

**The answer key matters.** Every model scores lower on the 19 calculators whose code Krohn-Grimberghe (2026)
corrected, by 8 to 38 points. Wrong answers in the key and harder calculators cannot be told apart here.

**Limits.** Twelve models and one-sided tests; exploratory, with nothing confirmed; P1's cases have one author; no
model was pinned to a provider, and one was served by 18; the key's spending limit refused 1,385 calls, which were sent
again once it was raised, with every other recorded result kept. The study cost $6.90.
