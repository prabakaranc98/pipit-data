# Programme P: five studies on one model

## In plain words

We take one small decision model, Perplexity's 4B decider, and test it on the jobs these models are actually sold
for. We read the vendors' own documentation to find those jobs, and the vendors' own lists of known weak spots.
Then we pick, for each job, one narrow thing that is easy to get wrong, matters when it is wrong, and has not
already been measured by the decision-models lab. For each we build cases where the right answer is known in
advance, run the model, count the mistakes, say how sure we are, say what it cost, and let a finding open a deeper
study. Five studies, one protocol, one report across them.

## What the reading showed (2026-10-31)

**What the models are for.** TypeSafe's use-case map and cookbooks, and Perplexity's Decisions API docs, describe
the same five jobs: routing and labelling at volume; verifying another model's work (extractions, citations,
tool-call traces); guardrails and moderation; scoring retrieved passages before they reach an answering model;
choosing and filling tools or skills for an agent. Perplexity says the Flash model is for "routing, labeling, or
filtering" at volume and that it answers each question separately. Both vendors say: keep thresholds in your code,
set them on your own labelled data, and send uncertain cases to a person.

**What the vendors admit.** TypeSafe's own page on Jev 1.13's rough edges lists: literal reading of scoping words
and negation; arithmetic, counting and dates; double negatives and multi-hop; large state full of irrelevant
detail; adversarial content in the state; contradictory criteria; a lean toward the first option. Perplexity's
card says grouped questions influence each other, long inputs beyond 32k tokens are only spot-checked, held-out
calibration error is about 0.05, and the API's response echoes the model name you sent, not the version that
served it, so aliases can move under you.

**What the lab already measured on 15 models, this one included.** Rule application and date arithmetic on a
return-window policy; the spike at the policy's number; abstention on missing and on conflicting records (this
model never abstains on conflicts, Jev does 60% of the time); forged evidence and nine attack families; option
order and yes/no against three-way; calibration (this model 0.052); recognition against decision; the Decision
Index against its own measures; an agent's shell-command gate; and when a model can be left alone at a stated
error rate. P1's conflict result reproduces the lab's. Pipit does not repeat any of this; it cites it.

**Where that leaves the five.** Each study below is a job the vendors sell, a weakness they admit or a limit they
flag, and a question the lab has not asked.

## The five studies

| Study | The job | The narrow question | Example case |
| --- | --- | --- | --- |
| P1 clinical, done | routing a safety decision | reading, computing, inferring, calibrating on a clinical record | 18 kg child, 540 mg on the chart: give, hold, or ask? |
| P2 verification | checking another model's extraction or citation | does the checker catch answers that look right but are wrong: a schema-valid field that was invented, a quote that exists but whose context contradicts the claim, a field wrongly left blank | the invoice total "1,250.00" was copied from a different line; the quote is verbatim but the section says the opposite |
| P3 guardrails | screening messages in and out of an LLM | does the guard decide on the words or on the intent: scary words with benign intent, polite words with harmful intent, the same request obfuscated, code-switched or spread over turns | a novelist asks how a detective would describe a poisoning; a user asks the same thing without the frame |
| P4 retrieval gating | scoring passages before they reach the answering model | does relevance track support for the claim or topical overlap: passages that support, contradict, only share the topic, or are irrelevant, alone and grouped with competitors, short and long | a passage names every term in the question and then says the opposite |
| P5 agent tools | choosing and filling a tool from a catalogue | with many near-duplicate tools, does it pick the right one and leave unmentioned arguments at their defaults instead of guessing, alone and grouped, as the catalogue grows | "show nvda for the last hour": which of 60 chart tools, and is the window stated? |

Each study keeps the four hypotheses of P1 (misread, cannot compute, cannot infer, commits when it should ask)
and adds the two knobs the vendors flag: grouped against one question per request, and state length from a few
hundred to 32k tokens with the deciding fact at a known position.

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

These are the pieces the method lacks today, each taken from a named reference and each with a test.

| Gap in Pipit today | Taken from | What we build | How we know it works |
| --- | --- | --- | --- |
| Cases are hand-written Python | NeMo Data Designer, Distilabel | a declarative family spec (slots, conditions, expected answers, validators) that a generator compiles to cases with lineage | P1's 120 cases regenerate byte for byte from the spec |
| The stop rule uses fixed-sample intervals, but the loop stops when evidence looks sufficient | anytime-valid confidence sequences (Howard et al.), the lab's e-values | a sufficiency gate that stays valid under optional stopping; Wilson stays for reporting cells | on M1's synthetic subject, the false-claim rate stays at the stated level however often we peek |
| The focus stage spends budget by gut | tinyBenchmarks, SubLIME | choose the next cases by how much they would change the estimate (IRT or anchor cases), against uniform at equal budget | M2's keep-or-kill curve |
| Scenario ideation is one prompt | Bloom, AdaTest, Petri | behaviour-first ideation with diversity control, scored by planted truth, gated by a person; multi-turn and simulated tools for P3 and P5 | the accepted-proposal rate after review, per study |
| Graders live inside study scripts | OpenAI evals, Inspect | graders as code in `pipit.checks`, separate from samples; a study is a spec plus manifests | a new study needs no new Python |
| Confidence is reported, not certified | the vendors' own threshold guidance, the lab's E17 | a calibration certificate per study: error against confidence, and the review-band curve (how many cases go to a person for a stated residual error) | the curve is the number an operator asks for |
| As-served models drift and the API echoes the alias | Perplexity and TypeSafe docs; our Jev run moved from 16 to 15 failures between runs | a canary set re-run at the start of every study; drift is a recorded fact, and a threshold is revalidated when it moves | the canary catches a version change before a study runs on it |

## Order of work

1. M1, the synthetic subject, now also the test for the new gate: planted failure rates, repeated peeking, the
   stated false-claim level held.
2. The P1 child study on dose arithmetic, as diagnosis and intervention: does supplying the computed ratio in the
   state fix the failure, as the lab's "decompose, compute, decide" predicts.
3. The protocol pieces above, each its own issue and pull request: family spec, canary set, calibration certificate,
   gate.
4. P2 to P5, then the programme report and the viewer.

## Sources read

TypeSafe docs: introduction, primitives, confidence, how to build with System One, use-case map, patterns,
cookbooks (guardrails, function calling, citation check, SDE cascade), Jev 1.13 jaggedness. Perplexity: the
pplx-decider-v1.2 and flash model cards, the Decisions API docs. The decision-models lab: research map, landscape,
scenarios, log, E14, E14b, E17. Third-party guides were read but not relied on.
