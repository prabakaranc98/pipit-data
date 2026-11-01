# Programme P: five studies on one candidate

One candidate, the Perplexity decider `pplx-decider-flash-v1.2`, studied on five niche objectives with one protocol,
so that findings, costs and lab-model use are comparable, and so that the engine is shaped by five use cases rather
than one. P1 (clinical) is done as the screen; the four others are planned here. Each is an issue under milestone M4.

## The five objectives

| Study | Domain | Niche objective | Decision |
| --- | --- | --- | --- |
| P1 | clinical | where clinical safety decisions break: reading, computing, inferring, calibrating | prescribe / avoid / need more information |
| P2 | legal | exception scope and deadline arithmetic in compliance triage | escalate / compliant / need more information |
| P3 | customer support | policy entitlement with time windows, tiers and exclusions | grant / decline / escalate / need more information |
| P4 | behavioural science | framing invariance and base-rate use in judgments about people | likely / unlikely / undeterminable, plus a probability |
| P5 | economics | units, bases and periods in comparing quantities | A better / B better / equivalent / need more information |

Each objective is narrow on purpose: one mechanism family per domain where a small decider can fail in a way that
matters and that a planted truth can score without a judge.

## One protocol

- **Tree.** Every study starts from the four-hypothesis skeleton of P1 (reading, computing, inferring,
  calibrating) and extends it with domain key questions. The lab-model proposer may add questions and families;
  a person keeps, edits or drops them. The tree is pre-registered before any run.
- **Cases.** Families × two scenarios × three conditions (critical, benign, absent or conflict) × two wordings
  for the screen. Expected answers are fixed by construction. Computed facts (dates, doses, rates) get executable
  checks, not a lab-model validator.
- **Quality gates, all executable or recorded.** Completeness; a generation stopped on the token limit is
  defective; the validator is scored against the planted truth per condition and its flags adjudicated by a
  person; wording invariance is reported; the case set is content-hashed with lineage per case; duplicates by
  hash are rejected.
- **Measurement.** Cells per (family, condition) with Wilson intervals and severity; the tree rolled up with
  the cost of each node; verdict thresholds fixed in advance; the primary and the adjudicated analysis both
  reported; cases-to-evidence replay.
- **Budget.** Screen 120 to 150 uniform → focus by evidence (M2's allocator against uniform) → confirm on a
  protected split by scenario family. A cell that clears the gate opens a child study with the finding as its
  objective, run on the same engine.
- **Record.** Every study emits `report.md` and `report.json` on one schema; the programme report is generated
  from the five, with lab models by role, cost by role, findings and child studies. No live calls to regenerate.

## What the programme must answer at the end

1. For this candidate: capabilities, issues and behaviour, by mechanism, with evidence levels and what is unknown.
2. For the engine: which lab models were worth their cost in which role, how often the validator and proposer were
   right, and how many cases each finding took against uniform sampling.
3. For the references: where the protocol improved on CheckList, AdaTest, tinyBenchmarks, Bloom and the others in
   practice, and where it did not. That comparison is written only after the five reports exist.

## Order of work

M1 (instrument proof) and the P1 child study first, because they cost nothing in lab-model calls and decide
whether the verdict rules can be trusted. Then the programme protocol and `report.json` (M4, M5), then P2 to P5,
then the programme report and the viewer.
