# The playbook: how Pipit makes evidence

Written 2026-11-01. Every study and every agent follows this. It is the reason a Pipit dataset or audit can be
trusted, so it changes only by pull request, with the reason recorded.

## In plain words

A dataset or an audit is worth something only if it measures what it claims, with enough cases to be sure, in a
way someone else can repeat. Our first studies built the machinery. They also showed where the method is still
weak. This playbook sets the rules that make the output good enough for an enterprise sign-off and for research:
studies of model behaviour, interpretability, alignment and safety evaluation, and benchmarks.

One principle runs through all of it: **models write, statistics allocate, code grades, people decide.** Helper
models and agents draft hypotheses and cases. Statistics, not a model's judgement, decide where the next case goes
and when to stop. Code computes every right answer and grades every reply. A person signs every claim.

## What our own studies showed is weak

| Weakness | Where we saw it | Why it matters |
| --- | --- | --- |
| One template per question | P1's dose finding rests on two drugs in one format | a finding may be a quirk of the template, not of the model |
| Budget spread evenly | 7 or 8 cases per P1 question; most nodes stayed "not enough evidence"; 14 or 15 more clean cases would settle each | the screen cannot say much, and the next cases are not aimed |
| Thresholds with a dead zone, many tests at once | a 15–20% failure rate can never settle; 12 questions × 5 setups is 60 tests with no correction | some "limitations found" will be chance, and some questions never close |
| Helper models trusted beyond what was measured | the validator was wrong on 25 of its 31 flags; the paraphraser cut 6 of 64 notes short | a dataset built by an unmeasured helper carries its errors |
| Hypotheses written by hand, unchecked | the conflict family's right answer was contestable; one "harmless" case was not harmless | the tree may miss mechanisms or test the wrong thing |
| No link from a finding to its cause | we know the decider fails dose checks, not at what dose ratio or why | a finding cannot guide a fix, a deeper study, or interpretability work |

## The playbook, step by step

| Step | What happens | Who does it | Check before moving on |
| --- | --- | --- | --- |
| 1. Frame | the question, the tolerance (the failure rate that matters for this use), and hypotheses by mechanism, grounded in what is already known: earlier findings, vendor-admitted weaknesses, the literature | lead model drafts; a person signs | every hypothesis says what would refute it; together they cover the ways the decision can fail |
| 2. Operationalise | each key question gets at least two independent case families with different surfaces and the same mechanism; cases are minimal pairs that change one factor; a difficulty setting where the mechanism has one (dose ratio, days past a deadline, how deep a fact is buried); right answers computed by code | family writers draft; code computes truth | a finding counts only if it appears in both families |
| 3. Validate items | code checks every case; near-duplicates are removed; wording spread is measured; a person rates a sample for realism; every helper model is scored against planted truth in its role | code, critic models, a person | a dataset card with pass rates; a helper below its bar is not used |
| 4. Pilot and power | a small even pilot estimates failure rates and spread; a power calculation sets the cases each question needs at the tolerance | statistics | the budget is written down before the main run |
| 5. Measure adaptively | the next cases go to questions whose evidence straddles the tolerance, weighted by what a miss costs; where there is a difficulty setting, an adaptive staircase finds the model's threshold and slope with tens of cases instead of a grid; stopping uses confidence sequences that stay valid when we look early | statistics allocate; writers fill the gaps they are asked to fill | the stopping rule fires, or the budget ends and the report says so |
| 6. Confirm | fresh families held out from every earlier step, frozen, with tests registered in advance and a false-discovery correction across all questions | statistics; a person opens and closes it | each claim carries its effect size and interval |
| 7. Explain | ablations and fixes on the same minimal pairs, such as supplying the computed mg/kg to see whether the error disappears; the pairs are exported for interpretability, where activation patching and probes need exactly such contrasts | lead and analyst; code | a cause is claimed only where an intervention changed the outcome |
| 8. Report and keep | the reliance dossier in three voices; datasets versioned with cards; findings, sources and decisions in the record and the knowledge graph | analyst; a person signs | someone else can rebuild every number from the record |

## How agents carry the playbook

- **Each step is a skill.** A skill has instructions, the shape of its inputs and outputs, a checklist, a worked
  example from P1 or P3, and the failure modes already seen, such as "never ask a model to verify a number".
- **Prompts are versioned and tested.** Each prompt has a set of bench cases and a measured pass rate. A change is
  kept only if the bench improves, through the keep-or-discard loop in `docs/agentic.md`.
- **Context is scoped by role.** Writers see the spec and earlier findings, never another model's answers or the
  confirm set. Critics see cases and their planted truth. The lead sees the record and the allocator's numbers.
- **Coordination goes through the record, not through chat.** Proposals, reviews and decisions are typed entries.
  When critics or council members disagree, a person decides.
- **The allocator decides where to spend; the lead decides what to write.** The lead writes new families only where
  the allocator asks for evidence the existing families cannot give.
- **Each agent is itself measured.** The share of a writer's cases that pass the checks, a critic's agreement with
  planted truth, how many of a proposer's ideas a person keeps: all recorded, all on the bench.

## What this makes possible beyond an enterprise audit

- **Behaviour science:** psychometric curves per model and mechanism, a threshold and a slope, in the way
  psychophysics measures perception.
- **Interpretability:** verified minimal pairs with planted truth, ready for activation patching and probing.
- **Alignment and safety evaluation:** elicitation with planted truth wherever possible, and measured judges only
  where not.
- **Benchmarks:** item banks with difficulty estimated by item response theory, so a hundred well-chosen items say
  what thousands would, and threshold fits in the spirit of METR's time-horizon measurements.
- **Comparisons:** configurations and cost recorded for every endpoint, as Artificial Analysis does, but on the
  cases of the job at hand.

## How we will know the playbook works

1. **On the bench:** synthetic subjects with planted failure surfaces, failure probability rising with a difficulty
   setting. Do adaptive allocation and staircases recover the planted thresholds with fewer cases than an even
   spread, without more false claims?
   First result (`studies/b1_bench`, 2026-11-01): on three planted surfaces of twelve questions, sending each next
   unit to the open question that would settle soonest settles three to fifteen times as many questions as an even
   spread at the same budget, but on ordinary intervals it claims falsely in up to a quarter of runs. With a
   confidence sequence instead, which stays valid when a question stops early, it still settles 4 to 40 times as
   many questions as an even spread on the same sequence, and false claims fall to at most 1% of runs. The textbook
   thresholding rule helped less and erred as often. Adaptive spending is adopted only with the sequence.
2. **On real models:** a dose-ratio staircase on the Perplexity decider and on Qwen3.5-4B in thinking mode: the ratio
   at which each starts to withhold, and how many cases that took against a grid.
3. **Replication:** the dose finding re-tested in an independent family with different drugs, units and wording.
   If it does not replicate, it was the template.

## Supporting pieces, in order after the experiments

- **The evidence rule:** one tolerance per use, tested one-sided, with no dead zone and the cases still needed shown
  on every node.
- **`report.json` and an interactive viewer:** Python writes the report; a static TypeScript viewer built with D3
  reads it, so the tree can be expanded, a node clicked to show its cases with every model's answer and the right
  one, and runs compared.
- **Study configuration:** which models play which role, how many parallel workers and agents, budgets in dollars
  and hours, profiles such as laptop or cloud, and a cost estimate before anything runs.
- **Data versioning:** case sets stay readable in git with cards and diffs; DVC carries the heavy parts, such as
  response caches, raw runs and any customer data, with pipelines and metric diffs across versions.

## References to read

None of these has been read in full for this project; each is read before a claim relies on it. Adaptive
psychophysics: QUEST (Watson and Pelli, 1983) and the Psi method (Kontsevich and Tyler, 1999). Psychometrics: item
response theory and computerised adaptive testing; tinyBenchmarks (Polo et al., 2024). Statistics: confidence
sequences (Howard et al., 2021) and e-BH (Wang and Ramdas, 2022). Interpretability on minimal pairs: Meng et al.
(2022) and Wang et al. (2022). Evaluation practice: METR's time-horizon work (2025) and Artificial Analysis's
methodology.
