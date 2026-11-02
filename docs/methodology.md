# The playbook: how Pipit makes evidence

Written 2026-11-01. Every study and every agent follows this. It is the reason a Pipit dataset or audit can be
trusted, so it changes only by pull request, with the reason recorded.

## In plain words

A dataset or an audit is worth something only if it measures what it claims, with enough cases to be sure, in a
way someone else can repeat. Our first studies built the machinery. They also showed where the method is still
weak. This playbook sets the rules that make the output good enough for an enterprise sign-off and for research:
studies of model behaviour, interpretability, alignment and safety evaluation, and benchmarks.

One principle runs through all of it: **models write, statistics allocate, code grades, rules registered in advance decide.** Helper
models and agents draft hypotheses and cases. Statistics, not a model's judgement, decide where the next case goes
and when to stop. Code computes every right answer and grades every reply. A claim is accepted only by gates
registered in advance: the confidence sequence, the confirm round, agreement with a benchmark where one exists. No
step waits for a person.

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
| 1. Frame | the question, the tolerance (the failure rate that matters for this use), and hypotheses by mechanism, grounded in what is already known: earlier findings, vendor-admitted weaknesses, the literature | the question is the study owner's choice, made before the loop starts and outside it; the lead model drafts the rest, and the tree is registered before any case runs | every hypothesis says what would refute it; together they cover the ways the decision can fail |
| 2. Operationalise | each key question gets at least two independent case families with different surfaces and the same mechanism; cases are minimal pairs that change one factor; a difficulty setting where the mechanism has one (dose ratio, days past a deadline, how deep a fact is buried); right answers computed by code | family writers draft; code computes truth | a finding counts only if it appears in both families |
| 3. Validate items | code checks every case; near-duplicates are removed; wording spread is measured; realism is measured by whether a classifier can tell the cases from real records; every helper model is scored against planted truth in its role | code, critic models measured on planted items | a dataset card with pass rates; a helper below its bar is not used |
| 4. Pilot and power | a small even pilot estimates failure rates and spread; a power calculation sets the cases each question needs at the tolerance | statistics | the budget is written down before the main run |
| 5. Measure adaptively | the next cases go to questions whose evidence straddles the tolerance, weighted by what a miss costs; where there is a difficulty setting, an adaptive staircase finds the model's threshold and slope with tens of cases instead of a grid; stopping uses confidence sequences that stay valid when we look early | statistics allocate; writers fill the gaps they are asked to fill | the stopping rule fires, or the budget ends and the report says so |
| 6. Confirm | fresh families held out from every earlier step, frozen, with tests registered in advance and a false-discovery correction across all questions | statistics; opened and closed by the rules registered for it | each claim carries its effect size and interval |
| 7. Explain | ablations and fixes on the same minimal pairs, such as supplying the computed mg/kg to see whether the error disappears; the pairs are exported for interpretability, where activation patching and probes need exactly such contrasts | lead and analyst; code | a cause is claimed only where an intervention changed the outcome |
| 8. Report and keep | the reliance dossier in three voices; datasets versioned with cards; findings, sources and decisions in the record and the knowledge graph | analyst; the release gate in `CONTRIBUTING.md` | someone else can rebuild every number from the record |

## From a gap to a release

How a study is set up, how deep its tree may go, and what reaches the Hub.

**1. The gap.** A study starts from a job someone wants to hand to a model, and the cost of a mistake in it. It names
where the gap comes from: the vendor's own stated weakness, an open problem the field has listed, an earlier
finding, or a failure seen in use. It keeps three things apart: what the field knows, what it lists as open, and what
is new only to us. It is written as one sentence with its tolerance: can model M do job J alone, with errors of
severity S below a stated rate, on inputs like these?

**2. Hypotheses, by mechanism.** Each hypothesis is a way the decision can fail, written so that something could
refute it. Together they partition the cases: every case falls under exactly one. P1's four make a reusable start for
decision jobs: the model fails to read a fact, fails to compute or compare a value, fails to infer a state from
indirect evidence, or commits when the record cannot support a decision.

**3. Key questions.** Each hypothesis splits into two to four key questions, each about one factor: a negated
allergy, a fact buried in a long note, a renal threshold. Each key question gets at least two case families with
different surfaces and the same mechanism, so that a finding has to replicate.

**4. Depth and width are set by the budget.** A node is settled only with enough independent cases:

| To settle a node | Independent cases for an 80% chance, on fixed intervals | On the confidence sequence the loop stops by (#25), looking after every case |
| --- | --- | --- |
| support a limitation whose true failure rate is 50% | 17 | 31 |
| support one whose true failure rate is 35% | 59 | 126 |
| refute a limitation when the true failure rate is 0% | 22 | 33 |
| refute it when the true failure rate is 5% | 74 | 138 |
| certify silent errors below 5%, with none seen | 59 | 59: the certificate is an exact test on the confirm round |

Computed exactly from the binomial with `pipit.allocate.status`, and the certificate row with
`pipit.calibration.cases_needed`.

So on fixed intervals the number of key questions a study can settle is roughly its budget divided by 30 to 60: a
budget of 500 independent cases settles about a dozen, three or four hypotheses of three or four questions each, a
tree of depth three. The confidence sequence the loop stops by needs about twice as many cases per node, so the same
budget settles about half as many. P1 wrote twelve key questions with 59 independent cases in all, three to five each,
and eleven of the twelve stayed open for Jev. Deeper levels are grown, not written: a node is split only where its
evidence divides or where a supported finding needs its cause, the split is made on explore data, and it is tested on
fresh confirm families.

**5. Cases and splits.** A family crosses scenarios, conditions, difficulty settings and rewordings; the independent
unit is a scenario under one condition. Before anything runs, each family and scenario goes to explore or confirm by
a hash of its name, so the split cannot drift. Confirm families are written and frozen, and never run during
exploration.

**6. Rounds over time.** A round runs explore, lets the tree adapt, then runs confirm once and records the claims.
The next round publishes the old confirm set, writes new confirm families, and repeats a small anchor set so that
results link across rounds. The version's first number changes when results stop being comparable, and the second
when only the interface changes.

**7. What reaches the Hub.** One dataset repository per study, with a tag per round, listed in a "Pipit benchmarks"
collection:

| Part | Published | Held back |
| --- | --- | --- |
| explore cases | the cases, with the tree and the family specs | nothing |
| retired confirm cases | the cases, checkable against the fingerprint published before their run | nothing |
| live confirm cases | a fingerprint of the set | the cases |
| results per model and round | each node's count, interval and status; the certificate; the evaluation aspects; cost; the model's exact setup | per-case answers on live confirm cases |
| the card | the gap, the tree, how truth is planted, "evaluation only, do not train", the licence, a canary string, how to evaluate, known limits | nothing |

Outputs whose terms restrict reuse, such as Jev's under TypeSafe's terms, are published only as aggregates unless
their terms allow more.

## Rules checked in code

Rules that came out of the first studies, each now a check rather than a promise:

| Rule | Why | Where |
| --- | --- | --- |
| A tree must partition its cases: every case claimed by exactly one key question | P1's spec, as written, claimed 40 cases twice, and only the order of the code decided which question got them | `pipit.tree.partition`; P1's `tree()` raises when it fails |
| No model filters or grades for a candidate of its own family | a validator keeps the cases its family reads well; P1's validator is a Qwen model, like all three of its candidates | `family` in every manifest; `pipit.manifest.family_conflicts` |
| An API model is pinned to one provider, and mixed routing is flagged | in study J1, OpenRouter served one judge from 18 providers, so its measured accuracy belonged to no single one | `settings.request.provider` in the manifest; `pipit.preflight.pinned`; `pipit.ledger.mixed_providers` |
| A run starts only when every model declares a family, every API model whose provider varies per call is pinned to one provider, and the estimated cost fits the key's budget; V1's runner checks this today, and each other runner adopts it when it next runs | in study V1, models were served by up to 18 providers each, and the key ran out mid-run | `pipit.preflight.require` before the first call; an unpinned run needs an explicit flag, which its report states |
| A refused key raises at once and each call has one time limit across its attempts, in the OpenRouter adapter, so every study that calls OpenRouter has both; a run that stops at the first refusal and saves each result as it finishes is V1's runner today, and the others adopt it when they next run | in V1, 1,385 refusals were recorded as failures, one call hung for over 20 minutes, and results were written only when a model finished | `openrouter.KeyRefused` and `TooSlow`; `pipit.results.Results` |

## How agents carry the playbook

- **Each step is a skill.** A skill has instructions, the shape of its inputs and outputs, a checklist, a worked
  example from P1 or P3, and the failure modes already seen, such as "never ask a model to verify a number".
- **Prompts are versioned and tested.** Each prompt has a set of bench cases and a measured pass rate. A change is
  kept only if the bench improves, through the keep-or-discard loop in `docs/agentic.md`.
- **Context is scoped by role.** Writers see the spec and earlier findings, never another model's answers or the
  confirm set. Critics see cases and their planted truth. The lead sees the record and the allocator's numbers.
- **Coordination goes through the record, not through chat.** Proposals, reviews and decisions are typed entries.
  When critics or council members disagree, the case gets more checks or is reported as unresolved; it never
  waits for a person.
- **The allocator decides where to spend; the lead decides what to write.** The lead writes new families only where
  the allocator asks for evidence the existing families cannot give.
- **Each agent is itself measured.** The share of a writer's cases that pass the checks, a critic's agreement with
  planted truth, how many of a proposer's ideas survive the gates: all recorded, all on the bench.

## What this makes possible beyond an enterprise audit

- **Behaviour science:** psychometric curves per model and mechanism, a threshold and a slope, in the way
  psychophysics measures perception.
- **Interpretability:** verified minimal pairs with planted truth, ready for activation patching and probing.
- **Alignment and safety evaluation:** elicitation with planted truth wherever possible, and measured judges only
  where not.
- **Benchmarks:** threshold fits on difficulty set by construction, in the spirit of METR's time-horizon
  measurements; item banks fitted by item response theory only once tens of models have answered the same items,
  since that method needs such a population (`docs/landscape.md`).
- **Comparisons:** configurations and cost recorded for every endpoint, as Artificial Analysis does, but on the
  cases of the job at hand.

## How we will know the playbook works

1. **On the bench:** synthetic subjects with planted failure surfaces, failure probability rising with a difficulty
   setting. Do adaptive allocation and staircases recover the planted thresholds with fewer cases than an even
   spread, without more false claims?
   First result (`studies/b1_bench`, 2026-11-01): on three planted surfaces of twelve questions, sending each next
   unit to the open question that would settle soonest settles up to fifteen times as many questions as an even
   spread at the same budget, but on ordinary intervals it claims falsely in up to a quarter of runs. With a
   confidence sequence instead, which stays valid when a question stops early, it settles 4 to 44 times as many
   questions as an even spread on the same sequence at 240 units and under twice as many at 60, with a false claim
   in at most 1.3% of runs. The sequence is stricter, so at 60 units this pair settles fewer questions than an even
   spread on ordinary intervals. The textbook thresholding rule helped less and erred as often. Adaptive spending is
   adopted only with the sequence.
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
