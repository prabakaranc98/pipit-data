# Pipit 0.1: the plan

Written 2026-11-01. This is the plan to reach version 0.1.0, the first version someone else can pick up and use.
Each step below is one issue and one pull request, merged one at a time.

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
| A model builder | Did a change fix the failure without breaking something else? | before and after on the same frozen cases |

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
  be, numbers are computed by code, and a person reviews a sample instead of every case. P1 built 120 checked cases
  for about one and a half cents of helper-model calls.

## What we take, and what is ours

| Reference | What it does well | What Pipit does with it |
| --- | --- | --- |
| Bloom (Anthropic) | starts from a behaviour, writes scenarios, judges transcripts | starts from a decision and its cost; the answer is planted, so no judge scores it |
| NeMo Data Designer | declares data as a spec with generators and validators | the family spec: the person, the stake, the planted fact, the conditions, the expected answers, the checks |
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

**Tested on this Mac on 2026-11-01, then run in full as step 1.** Qwen3.5-4B in BF16, at the revision the
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
| A stopping rule that stays valid when we look early | when the evidence is enough, even in an adaptive loop | 0.1 (#25) |
| Adaptive allocation against uniform at equal budget | where to spend the next cases | 0.1 (#9) |
| Anchors to public benchmarks | where the model stands on an established benchmark, from about 100 items | 0.1 (new) |
| The bench | whether all of the above give the right verdicts when the truth is known | 0.1 (#8) |
| Transfer to real traffic | whether results on written cases predict a real stream | 0.2 (#28) |

## Developer and user experience

- **One command per step:** `pipit models check` (does it load, how much memory, how fast, does it agree with a
  second engine), `pipit build`, `pipit run`, `pipit report`, `pipit certify`, `pipit view`.
- **YAML first, Python when you want it.** Everything the command line does is a typed function as well.
- **Local first, cheap by default.** Every call is cached by its hash and priced in the ledger, so a rerun costs
  nothing.
- **Reports anyone can read:** the reliance dossier told for a student, an engineer and a leader, and a static
  viewer of the tree, the cells, the certificate and the cost.
- **Install in one line** with the extras you need: `local` for PyTorch models, `mlx` for Apple silicon, `typesafe`,
  and later `agents`.

## The study team, in 0.2

The agentic design in `docs/agentic.md` comes after 0.1, on purpose: a lead model, specialists, small models as
workers, a council, a person at the gates, modes, a shared record, a business's context through MCP, and an
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
| S5 Experiments on the method | E1 to E4 in `docs/engine.md` | E2 running as study J1 |

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
| Extraction into fields | planted field values | G1, handover notes | built, not yet run |
| A computed number | code computes it | G1, a child's dose | built, not yet run |
| Judge items | a proposal whose verdict is planted | J1 | running |
| A difficulty ladder | a setting whose difficulty is known | the dose-ratio staircase | planned |
| Multi-turn, fact stated early | a fact given early and needed late | none yet | planned |
| Agent task, state checked | code checks the final state or a planted secret | none yet | planned |
| Attack against baseline | the same case with and without an attack | J1's injected note | started |
| Interpretability pairs | one variable changed, tokens aligned | P1's minimal pairs | planned |

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
| Validity | judges against planted truth and people; realism; transfer to real traffic | J1; #28 |

## Who does what: roles and models

Every role is filled by a model only after that model is measured in that role, on planted items, and its cost is in
the ledger.

| Role | Does | Model today | Evidence so far | Next test |
| --- | --- | --- | --- | --- |
| Candidate | is measured | Perplexity's decider, Qwen3.5-4B in both modes; Jev as reference | P1, P3, X1 | G1 (#47) |
| Lead | drafts and grows the tree, chooses the next action | not built; DeepSeek V4 Pro proposed | none | E1 on the bench (#8, #9) |
| Case writer | writes families from specs | gpt-oss-120b paraphrases today | P1: code caught 6 broken paraphrases | family specs (#22) |
| Validator | checks a planted fact survives a rewrite | qwen3-235b, the same family as P1's candidates | wrong on 25 of its 31 flags; the family rule now flags it (#43) | E3: the same cases checked by another family |
| Judge | grades where code cannot | DeepSeek V4.1 Flash first; V4 Pro only where replies cannot instruct it | J1 | injection resistance in the bar (#41) |
| Scorer and ranker | scores, compares and ranks cases, situations and hypotheses at volume: realism, severity, priority | Jev, once measured in each of these roles | J1: 0.1 s per verdict, a little less accurate than DeepSeek | pairwise realism (#50); hypothesis priority on the bench |
| Guard | keeps instructions written in a reply away from a judge | none yet: Jev, asked one question, flagged plain proposals more often than injected ones | J1 | quote replies as data, then test again (#41) |
| Council | reviews findings before they count | three families, never the candidate's | none | 0.2 |
| Person | signs claims and makes the decisions listed below | the study owner | | |

## The build order, one pull request at a time

1. **The comparison with the field, and counting a case once** (#38): merged in #39.
2. **Thinking mode in its native setup** (#35): merged in #58. 5 mistakes in 30 against 8 in instruct mode,
   exact paired test p = 0.51, for 5.8 hours of compute.
3. **The engine design, J1, X1 and I1** (#40, #41, #42; pull request #59): the method as computation, judges
   measured, Pipit beside Petri on the same model, and what the model holds when its decision ignores a fact.
4. **Rules the studies exposed:** the family rule (#43), provider pinning (#44), the partition check (#45). Merged
   in #56.
5. **The platform under the loop:** the supervisor that owns model servers and resumes jobs (#53), and the study
   registry (#54).
6. **Dataset styles and variants:** extraction and a computed number (#47); pressure and injection variants (#48).
7. **The bench and adaptive measurement** (E1; #8, #9, #25; pull request #60), with a confidence sequence;
   adaptive spending is adopted only with it.
8. **The evaluation aspects in `report.json`,** with a schema (#18).
9. **The first release and the examples** (#51, #52).
10. **Study configuration** (#12), after the decision on Inspect (#46); remote engines (#55).
11. **Multi-turn and agent styles** (#49), realism and test awareness (#50), the viewer (#19), and the agent team in
    0.2.

Then release 0.1.0.

## Where this is still weak against the real world

Honest gaps, as of 2026-11-01, each with the work that closes it:

| Gap | Why it matters | Closed by |
| --- | --- | --- |
| Every result is on cases we wrote | a model can pass written cases and fail on real traffic | the transfer study on real complaints from the Hub (#28) |
| One person set the clinical truth | a planted answer is only as right as its author | a clinician's review of P1's answers before any release |
| Nothing has been confirmed | every claim so far is exploratory | the first confirm round on held-back families (S4) |
| Studies are small | P1 settles one of twelve key questions per model | fewer, deeper key questions per budget, and adaptive spending (#9) |
| No judge is certified | where code cannot grade, the number is only as good as the judge | J1 with 30 to 60 more unsafe items, and injection resistance in the bar (#41) |
| The platform is fragile | a stopped server or a sleeping laptop cost hours today | the supervisor and resumable jobs (#53) |
| Work waits on review | building outpaces review, and context drifts | one pull request at a time, against main: #39, #56, #58 and #59 merged on 2026-11-01; #60 and #61 wait |

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

## Not in 0.1

The study team, a business's context through MCP, the knowledge graph and the autoresearch loop (all 0.2); P2, P4
and P5; the transfer study; repair data; images and multi-turn agents.

## Decisions

Taken on 2026-11-01:

1. The agent team is built in 0.2, after the bench and the commands exist.
2. The LLM is Qwen3.5-4B, the instruction-tuned model Perplexity's decider was trained from, run in its native
   setup.
3. Remote GPUs wait: everything is tested on this Mac first, and an SSH host plugs in when one is available.
4. On a self-contradicting record, asking for more information and refusing both count as right; asking is
   preferred, and both readings are reported (#11).
5. DeepSeek V4 Pro and V4.1 Flash are the first judges.
6. The family rule is in code, merged in #56: no helper, judge or council member shares a family with a candidate
   (#43).

Open:

1. Runner: run on Inspect with Pipit as the statistics on top, or keep our runner and read Inspect logs.
2. Case generator: NeMo Data Designer or our own (#22).
3. The explore split on the Hub: public, or gated behind accepted terms.
4. The confirm split: run only by us, or shared under agreement.
5. The lead agent: may it be a model behind an API for studies that touch a business's data?
6. Examples: notebooks or scripts.
