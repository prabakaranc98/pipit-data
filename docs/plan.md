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

## The path to 0.1.0, one pull request at a time

The order follows `docs/methodology.md`: prove the method on the bench first, then build what makes it easy to use,
then run real studies under it.

1. **Any LLM through one adapter, in its native setup:** instruct mode (#33, done), then thinking mode with
   confidence from agreement across samples (#35).
2. **The playbook:** the rules every study and every agent follows (#36).
3. **The bench:** synthetic subjects with planted failure surfaces, run in CI. (#8)
4. **Adaptive measurement on the bench:** allocation by evidence and stakes, staircases for difficulty settings, and
   a stopping rule that stays valid when we look early, each kept only if it beats an even spread at equal budget.
   (#9, #25)
5. **The evidence rule, `report.json` and the interactive viewer.** (#18, #19)
6. **Family specs,** with two independent families per key question. (#22)
7. **Study configuration:** models per role, parallel workers, budgets, profiles, and a cost estimate before a run.
   (#12)
8. **On real models:** the dose-ratio staircase and the replication of the dose finding. (new issue)
9. **The P3 screen end to end under the playbook,** confirmed on fresh families: the first full reliance dossier,
   and M3's done-when. (#14)
10. **The canary** for moved aliases and drifting models (#23); remote engines when a GPU host is available; anchors
    to public benchmarks.

Then release 0.1.0.

## What 0.1.0 means

- Someone else can register a decision model or an LLM, local or remote, in one manifest, and check it with one
  command.
- A new study is YAML only: a study file, family specs and manifests.
- The bench passes in CI: planted failures are found, and false claims stay at or below the stated level.
- On the bench, adaptive measurement beats an even spread at equal budget, or the report says it does not.
- One reliance dossier is complete and confirmed on fresh cases: P3, for both the decider and the LLM.
- Every artifact has a schema version, every case set and run is hashed, and every call is in the ledger.

## Not in 0.1

The study team, a business's context through MCP, the knowledge graph and the autoresearch loop (all 0.2); P2, P4
and P5; the transfer study; repair data; images and multi-turn agents.

## Decisions taken (2026-11-01)

1. The agent team is built in 0.2, after the bench and the commands exist.
2. The LLM is Qwen3.5-4B, the instruction-tuned model Perplexity's decider was trained from, run in its native
   setup.
3. Remote GPUs wait: everything is tested on this Mac first, and an SSH host plugs in when one is available.
4. On a self-contradicting record, asking for more information and refusing both count as right; asking is
   preferred, and both readings are reported (#11).
