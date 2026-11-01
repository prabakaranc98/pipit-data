# Programme P: can a business let this model act alone?

## In plain words

Before a business switches on a small decision model, it has to answer one question, and its risk team and its
regulator will ask it again afterwards: on which cases can the model act alone, how often will it be wrong without
anyone noticing, how many cases still need a person, and how long does that answer stay true?

Pipit answers that question for one model, Perplexity's 4B decider, on five jobs these models are actually sold
for. Each study ends in a **reliance dossier**: where the model breaks, how much it can handle alone at a stated
error rate, which settings change that, what finding it out cost, and the check that says when the answer expires.

## What the first tests showed (2026-11-01)

- **How much it can do alone, on the clinical cases.** Allowing at most 5 silent errors per 100 cases, Jev could
  handle 64% of P1's cases alone, Perplexity asked one question at a time 36%, and Perplexity with its two
  questions grouped 29%. A silent error is a wrong answer nobody reviewed.
- **The setting matters as much as the model.** Grouping the two questions, an option the vendor offers, raised
  Perplexity's mistakes from 19 to 29 of 112 and its calibration error from 0.02 to 0.17 (paired test p = 0.02).
  Jev and Perplexity one-at-a-time are not distinguishable overall on these cases (p = 0.39).
- **Well calibrated on average does not mean safe to automate.** Perplexity's average calibration error is lower
  than Jev's, yet it can be trusted alone on far fewer cases, because its few mistakes are made with high
  confidence.
- **Certificates need cases.** 112 cases can never certify better than about 3 silent errors per 100. One in 100
  needs about 300 clean cases; one in 1,000 about 3,000. The candidate runs a case in about 1.3 seconds on this
  laptop, so the cost of a certificate is in building enough valid cases, not in running them.
- **In a messy support queue** (24-case pilot), both models caught every gas leak, overheating battery, account
  takeover and data exposure, even buried in an angry complaint. Both failed on the most dangerous message: a
  customer who writes "I don't see the point of going on anymore" inside a payment complaint was sent to the
  vulnerability team, not the emergency protocol. Perplexity's own danger answer gave that message 0.07. Both also
  sent a verified customer's urgent request to the fraud team, ignoring the account notes showing the identity
  check had passed.
- **Combining narrow answers in code, as the vendors advise, is not a free fix.** Sending anything the danger
  answer flags to the emergency team fixed one miss for each model; for Jev it also sent two customers under a
  partner's control to the emergency team instead of the specialist team.

The evidence is in `studies/p1_clinical/report.md` and `studies/p3_support_crisis/pilot_report.md`.

## The five jobs, as business questions

| Study | The question a business asks | Where it bites |
| --- | --- | --- |
| P1 clinical medication check (screen done) | Can a hospital let the model clear routine medication orders and send only risky ones to a pharmacist? | a double dose cleared; a conflicting allergy record decided without asking |
| P2 document verification | Can a finance team let the checker pass extracted invoice and contract fields without a person? | payment on an invented or misread number |
| P3 support crisis triage (pilot done) | Can a contact centre let the model sort the queue without missing an emergency, a takeover or a customer at risk? | a risk of self-harm filed as a payment query; verified customers blocked as fraud |
| P4 retrieval gating for regulated answers | Can an insurer's or a bank's assistant rely on the gate to keep contradicting passages out of its answers? | a confident answer built on a passage that says the opposite |
| P5 agent tools in operations | Can an operations agent pick and fill tools from a large catalogue without guessing? | the wrong action run, or an argument nobody gave filled in |

## The reliance dossier: what every study delivers

1. **Where it breaks:** the failure map by mechanism (misreads, cannot compute, cannot infer, commits when it
   should ask), with intervals.
2. **How much it can do alone:** the certificate at stated silent-error targets, for all errors and for harmful
   ones only, and the human-review load per 10,000 cases.
3. **Which settings matter:** the vendor's knobs (grouped or one question at a time, input length, option order)
   and composition rules, as paired comparisons on the same cases.
4. **What it cost:** cases, model time, helper-model dollars and human review time.
5. **When it expires:** a canary set that detects a moved alias or a changed model; the certificate is re-run when
   it fires.
6. **What is still unknown,** in plain words, and the deeper study a finding opens.

## The biggest risk, stated plainly

Every number above is on cases we wrote. A business runs on real traffic. A certificate transfers only if the
cases are drawn like the traffic, and written cases are not. Two ways to close the gap: run the same engine on a
real stream with known outcomes and compare; and let a business run Pipit on its own labelled traffic, with the
written cases as the stress test that real traffic rarely contains. Until then a certificate is about the case set,
and every report says so. The transfer study has its own issue.

## What is known, what is open, what is ours

- **Known in the field:** finite-sample guarantees for a threshold on data drawn like the calibration data, from
  conformal prediction and risk control (Angelopoulos and Bates; Learn-then-Test; conformal risk control) and
  selective prediction. The decision-models lab applied split conformal to one world (its E17); Pipit does not
  repeat it.
- **Open in the field:** guarantees that survive drift and the move from test cases to real traffic; evaluation as
  a measurement science (Weidinger et al., 2025, position paper); error bars on evaluations (Miller, 2024).
- **Ours:** what a reliance certificate costs for a typed decision model, how far a vendor setting moves it, and
  whether written cases predict real traffic.
- **Standards a business will hold this to:** model risk management (US supervisory guidance SR 11-7), the EU AI
  Act's requirements on human oversight and accuracy for high-risk systems, the NIST AI Risk Management Framework,
  and, for P3, the UK FCA's guidance on vulnerable customers.

None of these sources has been read in full for this project yet; each is read before a claim relies on it.

## Cases anyone can read

A rule of the protocol, not a preference. Every study is read by students, engineers, practitioners, leaders and
buyers, so:

- **Every family opens with the person and the stake.** One sentence: who faces this decision, and what a wrong
  answer costs them. "A pharmacist checking a child's dose before the nurse gives it."
- **Every case reads like a real record.** A ticket a customer would send, a note a clinician would write, a
  contract clause a lawyer would recognise, a tool catalogue an engineer would ship. No placeholders, no codes in
  the text, no synthetic filler. The lab models paraphrase into the voice of that workplace, and a person reads a
  sample before the study runs.
- **Every result is told three ways.** One line for a student (what the model got wrong and why it matters), one
  for an engineer (which condition, how often, with what confidence), one for a leader (what it means for relying
  on the model, and what it cost to find out).
- **Names say what they mean.** Families, conditions and options are plain phrases, not codes, in the report.

## What the references add to the engine

| Gap in Pipit | Taken from | What we build | How we know it works |
| --- | --- | --- | --- |
| Cases are hand-written Python | NeMo Data Designer, Distilabel | a declarative family spec (slots, conditions, expected answers, validators) compiled to cases with lineage | P1's 120 cases regenerate byte for byte from the spec |
| The loop stops when evidence looks sufficient, but its intervals assume a fixed sample | anytime-valid confidence sequences (Howard et al.), the lab's e-values | a stopping rule that stays valid however often the loop checks | on M1's synthetic subject, the false-claim rate holds at the stated level |
| The focus stage spends budget by judgment | tinyBenchmarks, SubLIME | choose the next cases by how much they would change the estimate, against uniform at equal budget | M2's keep-or-kill curve |
| Scenario ideas come from one prompt | Bloom, AdaTest, Petri | behaviour-first ideation with diversity control, scored by planted truth, gated by a person; multi-turn for P3 and P5 | the share of proposals a person keeps |
| Graders live inside study scripts | OpenAI evals, Inspect | graders as code in `pipit.checks`; a study is a spec plus manifests | a new study needs no new Python |
| Confidence was reported, not certified | the vendors' own threshold advice, Learn-then-Test, the lab's E17 | built: `pipit.calibration`, an exact binomial certificate tested from the strictest cut-off down (#24) | first results on P1 above |
| Hosted models drift and the API echoes the alias | Perplexity and TypeSafe docs; our Jev run moved from 16 to 15 failures | a canary set run at the start of every study | it catches a version change before a study runs on it |

## Later (thought through, not scheduled)

- **Repair data.** Once a limitation is confirmed on fresh cases, build targeted examples to fix it and test that
  the fix breaks nothing else (A3's pattern). The first candidate is dose arithmetic.
- **More domains from the first plan.** Legal deadline arithmetic, economics units and bases, and behavioural
  framing, as families inside the five jobs where they fit.
- **Chatbot guardrails, multi-turn agents and images.**
- **The viewer** (milestone M5).
- **An agentic study team** that plans, writes and checks studies in modes, proposed in `docs/agentic.md` (milestone M6).

## Order of work

1. M1, the instrument proof, now also the test for the stopping rule.
2. The P1 follow-up on dose arithmetic, as a fix test: does putting the computed mg/kg in the record fix it?
3. The P3 screen, built around what the pilot found: self-harm signals inside complaints, trusted account notes
   against customer pressure, and the two answers contradicting each other.
4. The protocol pieces: family spec, canary set, stopping rule.
5. P2, P4 and P5, then the transfer study on one real stream.

## Sources read

TypeSafe docs: introduction, primitives, confidence, how to build with System One, use-case map, patterns,
cookbooks (guardrails, function calling, citation check, SDE cascade), Jev 1.13 jaggedness. Perplexity: the
pplx-decider-v1.2 and flash model cards, the Decisions API docs. The decision-models lab: research map, landscape,
scenarios, log, E14, E14b, E17. Third-party guides were read but not relied on.
