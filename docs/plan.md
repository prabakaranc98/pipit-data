# Pipit 0.1: the plan

Written 2026-11-01 and revised the same day; on 2026-11-02 the releases were reordered to close the evidence loop
first (decision 15). This is the plan to reach version 0.1.0, the first version someone else can pick up and use,
through small releases that each answer one question: 0.0.3, 0.0.4 and so on. Each step gets its issue when it
starts, and its pull requests merge one at a time.

## In plain words

A team about to rely on an AI model needs to know what it can and cannot do before its customers find out. Today
it either trusts a leaderboard that never saw its job, or tries to build a test set of thousands of cases that it
cannot write, check or afford. Pipit gives it a third way. The team describes the decision the model will make and
what a wrong answer costs. Pipit builds a few hundred cases where the right answer is planted, runs any model on
them, wherever that model runs, and reports where it breaks, how much it can be trusted to do alone, how sure we
are, and what finding out cost.

## Who it helps, and what they get

| Who | Their question | What Pipit gives them |
| --- | --- | --- |
| An engineer choosing a model | Which model, at what size and cost, for this job? | the same cases run on every option, compared pair by pair, with intervals and cost |
| A risk or model-validation team | Can it act alone, and how will we know when that stops being true? | the reliance certificate, the human-review load it implies, and a canary that says when it expires |
| A researcher | Where exactly does this model break, and why? | the failure map by mechanism, with the cases that show it |
| A post-training team | Which data fixes this gap, and did training fix it without breaking something else? | training data built from the measured gap, in the formats trainers read and held apart from evaluation; before and after on the same frozen cases |

## Five uses, one engine

Models are becoming easier to swap; the data a team builds around its job is what lasts. Pipit treats that data as the
central artifact: designed, studied, measured and versioned the way an experiment is. It finds what a model cannot yet
do, builds trusted data around exactly that, and measures what changed. The same cases and evidence serve five uses:

1. **Data for post-training and distillation:** training data built from a measured gap and held apart from every
   evaluation set. Pipit makes the data and measures the result; the training runs in the team's own stack, such as
   TRL, NeMo RL, verl or an in-house pipeline. Pipit ships at most one tutorial per use case.
2. **Evaluation that keeps up:** a few hundred cases chosen for what they tell us, new held-out families each round,
   and every claim with its interval.
3. **Auditing and behavioural analysis:** pressure, injection and other variants of cases whose answer is planted, so a
   finding is a count, not a judge's score.
4. **Alignment, interpretability and safety:** minimal pairs with planted truth, ready for probes and patching.
5. **Reliability, trust, decisions and routing:** which model may do a job alone, at a stated error rate, and when it
   should hand a case to a larger model or a person; for decision models and LLMs alike.

**As the field defines them** (read at abstract level on 2026-11-01; borders, open problems and sources in
`docs/landscape.md`):

| Use | The field's definition | Source |
| --- | --- | --- |
| Data for post-training | examples used after pre-training to change behaviour: demonstrations, better-and-worse pairs, prompts with a checker or a rubric | Tülu 3 (Lambert et al., 2024); Rubrics as Rewards (Gunjal et al., 2025) |
| Evaluation | "scenarios (i.e. use cases) and metrics (i.e. desiderata)", held to construct validity | HELM (Liang et al., 2022); Bean et al., 2025 |
| Auditing | "a systematic and independent process of obtaining and evaluating evidence regarding an entity's actions or properties and communicating the results of that evaluation to relevant stakeholders" | Mökander et al., 2023 |
| Alignment, interpretability, safety | aligned when "'trying' to behave as intended"; interpretability seeks "the computational mechanisms underlying neural networks' capabilities" | Anwar et al., 2024; Sharkey et al., 2025 |
| Reliability and routing | "ability of an item to perform as required, without failure, for a given time interval, under given conditions"; selective prediction "rejects instances as needed, to grant the desired risk" | NIST AI RMF 1.0, quoting ISO; Geifman and El-Yaniv, 2017 |

The scope for now is instruction following, reasoning, preferences and decisions. Agentic work, with environments and
rubrics for multi-step tasks, comes at 0.2.5 to 0.3.

Five industries, one at a time, each starting where the right answer can be computed or planted: clinical and
biomedical first; then finance and banking decisions; legal; data and AI work (analytics, analytics engineering and
machine learning, not software engineering at large); and human-centred AI, such as tutoring and collaboration, where
what is planted is the person: a misconception, a level, a goal or a constraint, and the move that serves them.

## Pipit and post-training

What each training step needs, and what Pipit makes for it:

| Training step | What it needs | What Pipit makes |
| --- | --- | --- |
| Supervised fine-tuning | inputs with right outputs | outputs checked by code where possible; new scenarios for each failure mechanism rather than rewordings |
| Preference training | a better and a worse answer to the same input | minimal pairs that differ by one planted factor, so a pair can teach only that factor; worse answers taken from the model's own measured failures; pressure pairs that hold the right answer against a push |
| Reinforcement learning with verifiable rewards | prompts with a checker | the code that plants the truth is the checker, so the reward is exact |
| Rubrics as rewards | a rubric and a judge | each rubric item, with its judge, measured against planted truth before use, as study J1 measured judges |
| Distillation | teacher outputs, filtered | only the outputs the checker passes, from teachers whose licence allows it; never Jev's |
| Evaluation after training | sets that stay held out | confirm families split by a hash of their name, with a canary string and a fingerprint |

Every training set records each item's source, licence and allowed uses, and is checked for leaks against every
evaluation set. Related work, not yet read: verifiable rewards in Tülu 3 (Lambert et al., 2024), on-policy preference
data (Tajwar et al., 2024), length shortcuts in preference data (Singhal et al., 2023), physician-written rubrics in
HealthBench (Arora et al., 2025), and, for human-centred AI, MathDial (Macina et al., 2023), tutor evaluation
(Maurya et al., 2025) and CollabLLM (Wu et al., 2025).

## The bottleneck: nobody can write 50,000 new cases

Public benchmarks are big: MMLU alone has about 14,000 test questions. A company cannot write that many new cases
for its own decision, and if it asks a model to, it gets near-duplicates with unchecked answers. Even with an
unlimited token budget, the hard part is not writing cases. It is knowing that each answer is right.

Pipit's answer has three parts.

- **The claim sets the sample size, not the benchmark.** Showing that a model makes fewer than 5 unnoticed errors per
  100 cases takes about 60 clean cases; fewer than 1 in 100 takes about 300; 1 in 1,000 about 3,000. Most decisions
  need hundreds of cases, not tens of thousands.
- **Every case has to carry information.** A case built around the mechanism of a decision, with the deciding fact
  present, harmless, missing or contradicted, stated plainly or buried, says more than a hundred random ones. Item
  response theory makes the same point for benchmarks: tinyBenchmarks reports that about 100 well-chosen items
  estimate a model's accuracy on a full benchmark within a few points.
- **The right answer is planted, so checking scales.** Each case is built from a spec that says what its answer must
  be, numbers are computed by code, and a second, independent implementation checks the answers (0.0.7). P1 built 120 checked cases
  for $0.014 of helper-model calls, the paraphraser's and the validator's.

## What we take, and what is ours

| Reference | What it does well | What Pipit does with it |
| --- | --- | --- |
| Bloom (Anthropic) | starts from a behaviour, writes scenarios, judges transcripts | starts from a decision and its cost; the answer is planted, so no judge scores it |
| NeMo Data Designer | declares data as a spec with generators and validators | the family spec: the person, the stake, the planted fact, the conditions, the expected answers, the checks; the generator is our own, compared against Data Designer on the same job (0.0.12) |
| CheckList | tests behaviours through controlled changes | conditions and wordings as controlled contrasts inside every family |
| tinyBenchmarks, SubLIME | a few items, chosen for information, estimate a whole benchmark | small anchor sets that place a model on public benchmarks, and adaptive allocation inside a study |
| Learn-then-Test, conformal risk control | guarantees for a threshold from finite data | the reliance certificate: how much a model can do alone at a stated error rate |
| Inspect, OpenAI evals | composable harnesses and logs | the ledger, the cache, graders as code |
| AdaTest, Petri, autoresearch | adaptive, agent-driven testing and improvement | the study team and its frozen judge, in 0.2 |

What is ours, taken as a whole: the decision and its cost as the starting point, planted truth instead of a judge,
a hypothesis tree that gathers evidence together with its cost, and claims with guarantees from a few hundred cases.
None of these references has been read in full for this project; each is read before a claim relies on it.

## Any model, on any engine

One contract for every model: a state and typed questions go in, typed answers with probabilities come out. How a
model is reached is its manifest's business.

| Kind of model | Example | How Pipit reaches it |
| --- | --- | --- |
| Decision model, local | Perplexity's 4B decider in BF16 | its own package, on PyTorch with Apple's MPS (built) |
| Decision model, hosted | Jev; Perplexity's Decisions API | the vendor's API (Jev built) |
| LLM, local on a Mac | Qwen3.5-4B in BF16 | Apple's MLX server, which speaks the OpenAI interface and returns token probabilities |
| LLM on a GPU machine | the same, or a 27B model | vLLM or SGLang on a CUDA machine, reached directly or through an SSH tunnel |
| LLM, hosted | any OpenRouter model | the OpenAI interface (built, for helper models) |

- **One adapter covers every LLM engine.** MLX, vLLM, SGLang, llama.cpp, Ollama and OpenRouter all expose the same
  OpenAI-style interface. Pipit asks a typed question as a multiple-choice prompt and reads the option
  probabilities from the first answer token's log-probabilities. Where an engine returns none, it falls back to a
  constrained choice and repeated sampling, and the report says so.
- **Candidates are chosen by the job, in their native setup.** LLM candidates are instruction-tuned or thinking
  models, run the way their model card recommends: thinking on when that is the default, and the card's sampling
  settings. A base model appears only as a control for a question about post-training. Two models meet on the same
  cases only when a business is choosing between them for one job, or when the pair isolates one cause.
  Qwen3.5-4B and Perplexity's 4B decider share a backbone, so their pair shows what decision training adds.
- **Confidence depends on the mode.** In instruct mode the option probabilities are read from the first answer
  token. A reasoned answer is always certain, so in thinking mode each question is asked several times and
  confidence is how often the answers agree.
- **On this Mac,** one 4B model in BF16 at a time, about 9 GB of the 24. Placement follows the measured footprint,
  and nothing falls back silently.
- **On a remote GPU,** you give an SSH host; Pipit uses a vLLM or SGLang server there, its own or yours, through a
  tunnel, and the manifest records the host, the engine and its version. vLLM also runs on Apple silicon now,
  through the community vllm-metal plugin, and SGLang has an early MLX backend.
- **Engines are checked against each other.** The same model on two engines answers the same cases, and the
  agreement and the size of the probability differences are recorded before a study relies on the faster one.

**Tested on this Mac on 2026-11-01, then run in full for 0.0.3 (#58).** Qwen3.5-4B in BF16, at the revision the
decision-models lab pinned, served by MLX through its OpenAI-style endpoint and launched by its own manifest: ready in
about 5 seconds, about 9.4 GB of memory, about 0.4 seconds per question. On every one of P1's 224 questions the answer
letters carried at least 94% of the first token's probability, so option probabilities are read directly. The
adapter switches thinking off in the chat template and renormalises the coarse BF16 log-probabilities over the
options. On P1's 112 cases the LLM made 36 mistakes against its decision-trained sibling's 19. Counted once per
independent case (59), the LLM did worse on 15 and better on 5: exact paired test p = 0.04, where counting each
wording had given 0.006. `studies/p1_clinical/report.md` has the breakdown.

## Studies as data

A new study should need no new Python. It is three kinds of file:

- **Manifests,** one per model, as today.
- **A study file:** the business question, the hypothesis tree, which model plays which role, the budget, and the
  thresholds fixed in advance.
- **Family specs:** each says who faces the decision, what a miss costs, the planted fact, the conditions, the
  expected answer for each, how cases are worded, and which checks they must pass.

A family spec, cut down:

```yaml
family: danger inside a complaint
who: an energy supplier's contact centre
stake: a gas leak handled as a billing ticket
tests: H1 reading                       # its node in the hypothesis tree
question: {route: [emergency, fraud_or_security, vulnerable_customer, standard]}
scenario: "Channel: email ... You billed me £412 for March ... {cue} SORT OUT THE BILL."
conditions:
  clear:      {cue: "There's a strong smell of gas since your engineer swapped the meter.", expect: emergency}
  buried:     {cue: "also the kitchen has smelt of gas since your guy swapped the meter", expect: emergency}
  look-alike: {cue: "honestly these gas prices are suffocating us", expect: standard}
wordings: {per_case: 2, styles: [voice-to-text, text message, second-language English]}
checks: [complete, not cut off, cue present, validator agrees with the plant]
```

Every case it produces carries its lineage: the spec and its hash, the writer, the paraphraser, every check it
passed, and its own hash. A case set is frozen once a claim cites it, and every artifact carries a
`schema_version`.

## Few cases, strong claims

| Method | What it answers | Status |
| --- | --- | --- |
| Intervals on every cell | how sure we are about a failure rate | built |
| Exact paired tests | whether one model or setting really differs from another on the same cases | built |
| The reliance certificate | how much a model can do alone at a stated error rate, and how many cases that needs | built |
| Calibration | whether its confidence means what it says | built |
| A stopping rule that stays valid when we look early | when the evidence is enough, even in an adaptive loop | 0.0.6 (#25) |
| Adaptive allocation against uniform at equal budget | where to spend the next cases | 0.1 (#9) |
| Anchors to public benchmarks | where the model stands on an established benchmark, from about 100 items | after 0.1.0; V1 is the first comparison |
| The bench | whether all of the above give the right verdicts when the truth is known | 0.1 (#8) |
| Transfer to real traffic | whether results on written cases predict a real stream | 0.2 (#28) |

## Developer and user experience

- **One command per step:** `pipit models check` (does it load, how much memory, how fast, does it agree with a
  second engine), `pipit build`, `pipit run`, `pipit report`, `pipit certify`, `pipit view`.
- **YAML first, Python when you want it.** Everything the command line does is a typed function as well.
- **Plain names.** Modules and functions read the way pandas, NumPy and scikit-learn do: one plain word per
  concept, names that say what they return, no abbreviations. The rules and the glossary are in `CONTRIBUTING.md`.
- **Local first, cheap by default.** Every call is cached by its hash and priced in the ledger, so a rerun costs
  nothing.
- **Reports anyone can read:** the reliance dossier told for a student, an engineer and a leader, and a static
  viewer of the tree, the cells, the certificate and the cost.
- **Install in one line** with the extras you need: `local` for PyTorch models, `mlx` for Apple silicon, `typesafe`,
  and later `agents`.

## The study team, in 0.2

The agentic design in `docs/agentic.md` comes after 0.1, on purpose: a lead model, specialists, small models as
workers, a council, gates registered in advance, modes, a shared record, a business's context through MCP, and an
autoresearch loop with a frozen judge. The team acts through the commands above and is judged on the bench, and
neither exists yet. Version 0.1 builds both, so the team has something to act with and something that can rule it
out.

## The plan by module

Pipit is built from four kinds of module. Each pull request delivers one or two of them with their tests and one
small experiment: one question, one baseline, one change, one evaluation.

**Scientific: what we measure and claim**

| Module | What it holds | State |
| --- | --- | --- |
| S1 Question and tolerance | the job question, a tolerance per node, what would refute each hypothesis | built in P1 and P3 |
| S2 The tree | a partition of the case space by mechanism; every case in exactly one key question | built, and checked in code (#45) |
| S3 Evaluation aspects | correctness, consistency, robustness, predictability, safety, cost, validity | partly built; see below |
| S4 Claims | explore, then confirm on held-back families with tests registered first | planned |
| S5 Experiments on the method | E1 to E5 in `docs/engine.md` | results for E1 (B1), E2 (J1) and E5 (X1) |

**Algorithmic: how evidence becomes a decision**

| Module | What it does | State |
| --- | --- | --- |
| A1 Units | a case and its rewordings count once | built (#39) |
| A2 Intervals and paired tests | Wilson intervals; exact paired tests | built |
| A3 The certificate | a fixed-sequence exact binomial test over units | built |
| A4 Allocation | a pilot for every node, then the thresholding rule or active testing | on the bench: an even spread, the thresholding rule, nearest to settle (#9); active testing planned |
| A5 Stopping | intervals that stay valid when we look early | a confidence sequence the node rule can read (#25); not yet read by `pipit.evidence` |
| A6 Growing the tree | splits tested on recorded factors, with false discoveries controlled; failure clustering | planned |
| A7 Thresholds | staircases on difficulty settings | planned |
| A8 Judged rates | correction for a judge's sensitivity and specificity; prediction-powered inference | planned |
| A9 Many claims | e-BH across claims; children tested only after their parent | planned |

**Build: what we engineer**

| Module | What it is | State |
| --- | --- | --- |
| B1 Models as manifests | adapters for PyTorch, MLX, OpenRouter and TypeSafe; vLLM and SGLang through the OpenAI-style adapter | built |
| B2 Case families | specs compiled to cases with planted truth and lineage | partly: P1's seeds are code (#22) |
| B3 Runner | a run script per study; a bridge to Inspect if chosen | built as scripts |
| B4 Record | cache, ledger, cost per role | built |
| B5 Report | `report.json` with a schema, and a viewer | planned (#18, #19) |
| B6 Versions and releases | git; DVC for heavy parts; Hub datasets with tags and a collection, a canary, a fingerprint, confirm held back | planned |
| B7 Agent team | lead, case writers, critics, workers, council | 0.2 |

**Use: how people work with it**

| Module | What it is | State |
| --- | --- | --- |
| U1 Study configuration | one YAML per study: roles and models, tolerances, variants, budgets, machine profile, judge panel | planned (#12) |
| U2 Dataset styles | the table below | partly built |
| U3 Examples | walkthroughs that start from released data and end in a decision | planned |
| U4 Overview and docs | the design page, the playbook, the comparison with the field | built |

## Dataset styles

| Style | Right answer set by | Example | State |
| --- | --- | --- | --- |
| Typed decision | a planted fact | P1, medication decisions | built |
| Routing a messy queue | the planted kind of message | P3, support triage | pilot |
| Extraction into fields | planted field values | G1, handover notes | local work, not merged (0.0.13, #47) |
| A computed number | code computes it | G1, a child's dose | local work, not merged (0.0.13, #47) |
| Judge items | a proposal whose verdict is planted | J1 | running |
| A difficulty ladder | a setting whose difficulty is known | the dose-ratio staircase | planned |
| Multi-turn, fact stated early | a fact given early and needed late | none yet | planned |
| Agent task, state checked | code checks the final state or a planted secret | none yet | planned |
| Attack against baseline | the same case with and without an attack | J1's injected note | started |
| Interpretability pairs | one variable changed, tokens aligned | P1's minimal pairs | built for I1 |

Every style takes the same variants: rewordings, option order, an injected instruction, a different surface or
persona, and a difficulty setting where the mechanism has one.

## Evaluation aspects

Reliability is split into consistency, robustness, predictability and safety, after "Towards a Science of AI Agent
Reliability" (Rabanser et al., ICML 2026), and cost is weighed against accuracy, after "AI Agents That Matter"
(Kapoor et al., 2024), both from Princeton's Science of Agent Evaluation group. Only the abstracts have been read.

| Aspect | Pipit's measure | Where it exists today |
| --- | --- | --- |
| Correctness | failure rate per node, per independent case | P1 |
| Consistency | agreement across repeated samples of one case | P1 in thinking mode |
| Robustness | change under rewording, option order and perturbation | P1's wording pairs; J1's order flips |
| Predictability | calibration, and the reliance certificate | P1 |
| Safety | errors by severity; a certificate on unsafe errors alone | P1 |
| Cost | dollars, tokens and seconds per case and per claim; accuracy against cost | the ledger |
| Validity | judges against planted truth and published human labels; realism; transfer to real traffic | J1; #28 |

## Who does what: roles and models

Every role is filled by a model only after that model is measured in that role, on planted items, and its cost is in
the ledger.

| Role | Does | Model today | Evidence so far | Next test |
| --- | --- | --- | --- | --- |
| Candidate | is measured | Perplexity's decider, Qwen3.5-4B in both modes; Jev as reference | P1, P3, X1 | G1 (#47) |
| Lead | drafts and grows the tree, chooses the next action | not built; DeepSeek V4 Pro proposed | none | proposing key questions, on planted items, in 0.0.6; E1 on the bench (#8, #9) |
| Case writer | writes families from specs | gpt-oss-120b paraphrases today | P1: code caught 6 broken paraphrases | family specs (#22) |
| Validator | checks a planted fact survives a rewrite | qwen3-235b, the same family as P1's candidates | wrong on 25 of its 31 flags; the family rule now flags it (#43) | E3: the same cases checked by another family |
| Judge | grades where code cannot | DeepSeek V4.1 Flash first; V4 Pro only where replies cannot instruct it | J1 | injection resistance in the bar (#41) |
| Scorer and ranker | scores, compares and ranks cases, situations and hypotheses at volume: realism, severity, priority | Jev, once measured in each of these roles | J1: 0.1 s per verdict, a little less accurate than DeepSeek | pairwise realism (#50); hypothesis priority on the bench |
| Guard | keeps instructions written in a reply away from a judge | none yet: Jev, asked one question, flagged plain proposals more often than injected ones | J1 | quote replies as data, then test again (#41) |
| Council | reviews findings before they count | three families, never the candidate's | none | 0.2 |
| Gates | accept a claim only by rules registered in advance: the confidence sequence, the confirm round, agreement with a benchmark where one exists | code | V1 | the confirm round (0.0.7) |
| Study owner | makes the decisions listed below; no step waits for a person | | | |

## Releases on the way to 0.1.0

Each release answers one question. It is tagged only when it passes the release gate in `CONTRIBUTING.md`, and it
is measured against the reference problem suite in `docs/suite.md`, whose statuses its notes report.

**This cycle's finish line**, set on 2026-11-01: one cell, clinical × reliability, end to end with no person in the
loop. May a 4B model act alone on a medication order, and where must it hand off? The loop closes in 0.0.6, its
findings face fresh, held-back families in 0.0.7, and 0.0.8 delivers the reliance dossier on about 500 cases, with
the dataset and one write-up of what changed in our understanding. About 500 is a planned budget, not a guarantee:
on the confidence sequence the loop stops by, refuting a key question takes at least 33 independent cases even with
no failures (22 on fixed intervals), P1's tree has twelve, and a question whose failure rate sits near the line can
take hundreds of cases or stay insufficient.

| Release | The question | The work |
| --- | --- | --- |
| 0.0.3 | Can Pipit's numbers be trusted? | counting a case once and the comparison with the field (#39); the rules in code (#56); native setups (#58); the engine design with J1, X1 and I1 (#59); the bench (#60); V1 registered (#61); this plan (#62) |
| 0.0.4 | Can we trust a run? | V1's results, with the providers that served each model; one time limit per call and a stop at a refused key, in the OpenRouter adapter, for every study; checks before a run and results saved per item, in V1's runner, which the other runners adopt when they next run, and the loop runner (0.0.6) from the start |
| 0.0.5 | Can a report drift from its data? | every report rebuilt from its recorded runs by one script: six of the seven in CI on every pull request, and I1's, which needs its activations file, at the release gate (#74); the numbers in the README and docs checked against the reports |
| 0.0.6 | Does the loop close? | one runner for one cell, clinical × reliability, joining the steps the studies ran apart: new cases go to the key question nearest a verdict (B1's rule), are answered by the candidate and graded by code, and update the evidence; a question stops early only by a rule that stays valid when the loop looks early (#25); the proposer, once measured in its role on planted items, adds key questions through the partition check; cases come from family specs with answers computed by code (#22), starting with four families: renal threshold, urgent result, weight-based dose and drug interaction; checks before a run and results saved per item; done when one command takes the specs to verdicts with no person in between, and the report rebuilds from its records |
| 0.0.7 | Is the dose finding real? | the confirm round on fresh, held-back families for every finding the 0.0.8 dossier relies on, the dose finding first (#10), scored with more than one right answer where the record allows it (#11); a second, independent writer for each family, and how much the writer changes the result; P1's planted answers checked by a second, independent implementation and against published reference values |
| 0.0.8 | Can a small model approve alone at a stated clinical error rate, across reruns? | the reliance dossier from the confirmed run: the certificate for Qwen3.5-4B, with reruns to measure consistency, and the cases it hands on; the dataset, kept in this repository until the Hub release (0.0.14), and one write-up of what changed in our understanding; routing between models is not new (FrugalGPT, RouteLLM), so it is not claimed |
| 0.0.9 | Is Pipit more efficient than random sampling? | Pipit's allocation against random subsets of MedCalc-Bench, on V1's data; the bench with failures that cluster by family and writer, its defects and thin families, and a CI job (#8); P1's dose family (#9) |
| 0.0.10 | Can it run unattended? | the supervisor (#53), the canary set (#23), and the decision on Inspect (#46) |
| 0.0.11 | Does data built from a confirmed gap fix it? | training data in the formats above, with source, licence and leak checks; one tutorial that trains with an outside tool and hands the model back to be measured; the judges' bar with injection resistance (#41); the panel that stands in for human reviewers: model families and decision models such as Jev, each measured on planted items, with votes weighted by their measured error rates |
| 0.0.12 | Is our case design better than NeMo Data Designer's? | the same job and budget: labels verifiably right, real failures found, near-duplicates, realism measured by whether a classifier can tell the cases from real records (#50), leaks and cost |
| 0.0.13 | Does the engine carry over to other industries? | extraction and a computed number (G1, #47); pressure and injection variants (#48) |
| 0.0.14 | Can others use the data? | `report.json` with a schema (#18), which the numbers check then reads, and the study registry (#54), the model inventory (#20) and the programme tables (#17) generated from it; the first Hub release (#51), the examples (#52) and the viewer (#19) |
| 0.1.0 | Can someone else pick it up? | the rest of the definition below: one manifest and one command; a study as YAML only (#12); remote engines (#55); P3's dossier confirmed (#14); modules by concept and plain names, below; type checks and docstrings in CI; studies importable without editing `sys.path` |

**Plain names, proposed for 0.1.0, for the study owner to approve.** New code follows the naming rules in
`CONTRIBUTING.md` from now on; existing code is renamed in 0.1.0. Modules by concept: `models` (manifests, loading,
roles), `adapters` (one per engine), `cases` (questions and families), `stats` (intervals, exact tests, confidence
sequences, certificates), `tree` (hypotheses, partition, evidence, verdicts), `allocation` (where the next cases go),
`record` (cache, ledger, costs, providers) and `report` (tables, `report.json`, pictures). The names that change most:

| Now | Proposed | Why |
| --- | --- | --- |
| `checks.wilson` | `stats.wilson_interval` | says what it returns |
| `allocate.status` | `tree.verdict` | it returns supported, refuted or insufficient |
| `manifest.resolve` | `models.load_model` | it loads a model |
| `openai_compat.render` | `question_prompt` | it builds the prompt |
| `calibration.ece`, `calibration.brier` | `expected_calibration_error`, `brier_score` | no abbreviations |
| `evidence.unit_share` | `failures_per_independent_case` | the concept, in words |
| `questions.noul` | `questions.yes_no` | "noul" is TypeSafe's word |
| `checks.severity`, `checks.completeness` | P1's and P3's own code | the rules belong to the studies that use them |

**Methods are read when the release that relies on them starts:** confidence sequences before 0.0.6; conformal risk
control before 0.0.8; thresholding bandits and tinyBenchmarks before 0.0.9. Each gets a short note: its claim, its
conditions and where Pipit departs from it.

## Where this is still weak against the real world

Honest gaps, as of 2026-11-01, each with the work that closes it:

| Gap | Why it matters | Closed by |
| --- | --- | --- |
| Every result is on cases we wrote | a model can pass written cases and fail on real traffic | V1 against MedCalc-Bench's real notes (0.0.4), then the transfer study on real complaints (#28) |
| One person set the clinical truth | a planted answer is only as right as its author | no reviewer is available, so each planted answer is checked by a second, independent implementation and against published reference values, and each family gets a second writer (0.0.7) |
| Nothing has been confirmed | every claim so far is exploratory | the confirm round on fresh dose families (0.0.7, #10) |
| The loop does not close | each study ran its own script, and no result chooses the next cases; sending cases where a verdict is closest has been tested only on simulated models (B1) | the loop runner (0.0.6) |
| Studies are small, and rewordings add little | P1 settles one or two of twelve key questions per model; its two wordings agreed on 51 to 53 of 53 cases | new scenarios from family specs instead of rewordings (#22) and cases sent where a verdict is closest, both in the loop (0.0.6); fewer and deeper key questions |
| Reports and docs can drift from the data | I1's report could not be rebuilt from its script, and the docs overstated B1 | every report rebuilt from its recorded runs, six of the seven in CI and I1's at the release gate, and the numbers checked (0.0.5) |
| No judge is certified | where code cannot grade, the number is only as good as the judge | J1 with 30 to 60 more unsafe items, and injection resistance in the bar (#41) |
| The platform is fragile | a stopped server, a sleeping laptop or one stuck call cost hours | a time limit and a stop at a refused key on every OpenRouter call; checks before a run and results saved per item in V1's runner (0.0.4); the supervisor (0.0.10, #53) |

What moved toward the real world on 2026-11-01: evidence counted once per case, which corrected overclaims;
judges measured before use; Pipit tested beside Petri on the same model; three methods agreeing on why the dose
decision fails; and adaptive spending kept honest by intervals valid under early stopping.

## What 0.1.0 means

- Someone else can register a decision model or an LLM, local or remote, in one manifest, and check it with one
  command.
- A new study is YAML only: a study file, family specs and manifests.
- The bench passes in CI: planted failures are found, and false claims stay at or below the stated level.
- On the bench, adaptive measurement beats an even spread at equal budget, or the report says it does not.
- One reliance dossier is complete and confirmed on fresh cases: P3, for both the decider and the LLM.
- Every artifact has a schema version, every case set and run is hashed, and every call is in the ledger.
- Every report shows the evaluation aspects: correctness, consistency, robustness, predictability, safety and cost.
- The first Pipit benchmark is on the Hub with its confirm set held back.

## After 0.1.0

- One industry at a time, each starting the way V1 did: reproduce one public benchmark, then write planted-truth
  families for one job where the right answer can be computed or planted.
- The study team, a business's context through MCP, the knowledge graph and the autoresearch loop in 0.2, built only
  if the bench shows the scripted loop is the bottleneck.
- Agentic tasks as the thing being measured, with environments and rubrics for multi-step work, at 0.2.5 to 0.3.
- P2, P4 and P5; the transfer study (#28); images.

## Decisions

Taken on 2026-11-01:

1. The agent team is built in 0.2, after the bench and the commands exist.
2. The LLM is Qwen3.5-4B, the instruction-tuned model Perplexity's decider was trained from, run in its native
   setup; its instruct-mode runs, in P1 and X1, are controls.
3. Remote GPUs wait: everything is tested on this Mac first, and an SSH host plugs in when one is available.
4. On a self-contradicting record, asking for more information and refusing both count as right; asking is
   preferred, and both readings are reported (#11).
5. DeepSeek V4.1 Flash is the default judge where code cannot grade, reported with its measured error rates. No
   judge yet passes the bar set in J1, so a judged number is never a claim on its own (#41).
6. The family rule is in code, merged in #56: no helper, judge or council member shares a family with a candidate
   (#43).
7. Releases are small: 0.0.3, 0.0.4 and so on, each answering one question, up to 0.1.0.
8. Pipit's case generator is its own (#22); NeMo Data Designer is a comparison, not a dependency (0.0.12).
9. Pipit makes training data and measures its effect; the training runs in the team's own stack, and Pipit ships at
   most one tutorial per use case.
10. Until 0.2.5 to 0.3 the scope is instruction following, reasoning, preferences and decisions; agentic tasks come
    then.
11. The five industries: clinical and biomedical, finance and banking decisions, legal, data and AI work, and
    human-centred AI.
12. V1 is reported as run, with the providers that served each model shown, and finished runs are not rerun. The
    calls the API key refused were sent again once its limit was raised, which completes the run.
13. No step waits for a person. Each human check is replaced by an automatic one grounded in a reference: planted
    answers checked by a second, independent implementation and against published values; realism measured
    against real records; claims accepted only by gates registered in advance. Where a model must judge, a panel of
    model families and decision models such as Jev does it, each measured on planted items first.
14. Industries open one at a time, and finance comes after clinical.
15. The loop closes first. One cell, clinical × reliability, goes end to end before anything else: the loop runner
    (0.0.6), the confirm round (0.0.7) and the reliance dossier (0.0.8). Sending cases where a verdict is closest
    had sat at 0.0.9 and growing the tree at 0.2, and seven studies each proved one piece with nothing joining them.
    `report.json`, the study registry, the model inventory and the programme tables move to 0.0.14, and the renames
    to 0.1.0.

Open:

1. Runner: run on Inspect with Pipit as the statistics on top, or keep our runner and read Inspect logs (#46).
2. The renames and module layout proposed for 0.1.0; `CONTRIBUTING.md` sets the naming rules, and the table above
   lists the changes.
3. The explore split on the Hub: public, or gated behind accepted terms.
4. The confirm split: run only by us, or shared under agreement.
5. The lead agent: may it be a model behind an API for studies that touch a business's data?
6. Examples: notebooks or scripts.
