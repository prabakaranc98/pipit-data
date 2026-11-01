# Pipit and the field

Written 2026-11-01. We compared Pipit with the tools and papers people already use to write evaluation data, run
models, attack them, grade them and build training data: eight research passes over about 160 tools and papers,
including about 90 papers from CVPR, ICCV, ECCV, ACL, EMNLP, NAACL, NeurIPS, ICLR, ICML and COLM. The last section
says how deeply each was read. Everything here is a reading of those sources, except the fix in section 1,
which is measured.

## In plain words

**Most of the machinery exists already, and it is maintained.** Inspect runs models and keeps logs; METR moved its
work onto it, and HELM, in maintenance since June 2026, sends its users there. NeMo Data Designer writes varied
cases from a declared spec. PyRIT, garak and promptfoo attack models with hundreds of techniques. Petri and Bloom
run multi-turn audits. Pipit should plug into these, not rebuild them.

**None of them decides.** No tool we read tests a question against a stated tolerance, certifies how much a model
can handle alone, sets the right answer by construction so that no judge is needed, scores its own helper models
before trusting them, or says how many more cases a question needs. That is Pipit's job.

**We were counting the same evidence twice.** The two wordings of a P1 case got the same outcome in 51 to 53 of 53
pairs, for every model, yet we counted them as two tests. The field knows this mistake (Miller, 2024), and garak's
code makes it too. Pipit now counts a case and its rewordings once. Two P1 results do not survive: grouping the
vendor's questions is no longer shown to hurt, and three hypotheses we had called refuted are open again.

## What we got wrong, ranked

| # | What we got wrong | How we know | What changes |
| --- | --- | --- | --- |
| 1 | Rewordings counted as independent cases | P1's wording pairs agree 96–100%; two simulations | fixed here |
| 2 | Building our own runner, log and viewer | Inspect has them, with 28 providers, agents, sandboxes and a viewer | run on Inspect or read its logs; your decision |
| 3 | Treating planted truth as the end of judging | harm cannot be graded by code; measured judges agree with people 59–93% of the time | judges scored against people, their error carried into the number |
| 4 | Attack rates without their budget | success keeps rising with the number of tries | every attack claim names the attack class and the tries allowed |
| 5 | Item banks fitted by item response theory as a near-term plan | they need hundreds of earlier models answering the same items | adaptive measurement on difficulty set by construction |
| 6 | Two case families per question | two templates are a sample of two | many cheap rewordings, their spread reported |
| 7 | Data quality named but not defined | "near-duplicates" and "wording spread" have no formula | defined, and reported on a dataset card |
| 8 | Many tests, no correction | 68 node verdicts per study | e-BH across the tree, as the playbook plans |
| 9 | Thin provenance | engine, quantisation and endpoint never compared | recorded, and local checked against hosted |

### 1. One case, counted once

A unit is a case together with its rewordings. It scores the share of its cases that failed, and every interval,
replay and paired test is taken over units. The certificate counts a unit as a silent error if any of its cases is
one, which keeps the guarantee whatever the correlation inside a unit. Two simulations in `tests/test_units.py`:

| Check | Counting each wording | Counting each case once |
| --- | --- | --- |
| A 95% interval covers the true rate (30 scenarios, 2 wordings that agree 90% of the time) | 88.2% | 96.0% |
| A model whose silent errors sit exactly at the 5% target gets certified (100 scenarios) | 12.3% | 4.0% |

On P1 (`studies/p1_clinical/report.md`), 59 independent cases instead of 112:

| Result | Counting each wording | Counting each case once |
| --- | --- | --- |
| Grouping the two questions hurts Perplexity | p = 0.021 | p = 0.18, not shown |
| Qwen3.5-4B worse than the decider trained from it | p = 0.006 | p = 0.041 |
| Handled alone at ≤5% silent errors: Jev, Perplexity, grouped, Qwen | 64%, 36%, 29%, 19% | 60%, 33%, 19%, 14% |
| Certified at ≤3% silent errors | all four | none; 59 cases cannot |
| Node verdicts | | 8 of 68 change, all to "insufficient" |

Still open: cases from different conditions of one scenario are treated as independent. In P1 they correlate
weakly (0.06 to 0.21 within a scenario). Families are treated as fixed; the playbook's rule that a finding must
appear in two families guards that level.

### 2. Run on Inspect, keep the decision

Inspect (UK AISI with Meridian Labs, MIT, release 0.3.287 on 31 October 2026) is now the field's default runner: a
task is a dataset, solvers and scorers, with a response cache, cost caps per sample, resumable runs, a log that keeps
the task version, git commit and every sample, and a viewer. Petri and Bloom are built on it. Pipit's cache, ledger
and planned viewer repeat much of this. The proposal: Pipit cases become Inspect samples, with family, unit, condition
and planted truth in their metadata; Pipit graders become scorers; and `pipit certify <log>` gives the certificate,
paired tests and tree for any Inspect run, including runs Pipit did not build. That is also how a team that already
uses Inspect would adopt Pipit. Pipit keeps what Inspect lacks: case construction with planted truth, helpers scored
before use, the statistics, cost per role, and a hash of the case set in every number. Inspect has no MLX provider;
MLX serves an OpenAI-style endpoint, which Inspect reads.

### 3. Judges, where code cannot grade

Planted truth covers decisions with a right answer: P1's choices, a planted secret, a forbidden tool call. It does
not cover "was this reply harmful?", and there the field's judges disagree with people often. On JailbreakBench's 300
human-labelled replies, by our recount of its published labels, a Llama-3-70B judge agreed with the human majority
90.7% of the time, and HarmBench's classifier 78.3%, calling 49% of replies jailbroken where people said 37%.
PyRIT's own judges score 0.59 to 0.90 accuracy across 32 configurations. Adopt two practices: score every judge
against human labels for each case family before use, as PyRIT's `ScorerEvaluator` does, and correct a measured rate
for the judge's sensitivity and specificity, as garak does, carrying the judge's error into the interval.
Prediction-powered inference (Angelopoulos et al., 2023) is the formal route: a small gold set plus many judge labels
give a valid interval.

### 4. Attack claims state their budget

Attack success keeps rising with the number of tries, so "2% of attacks succeed" means nothing without the attack
class and the tries allowed. A Pipit attack claim reads: for attacks of class C, within K tries per case, failures stay
below x, measured on fresh seeds. With no failures, certifying 5%, 2% or 1% takes 59, 149 or 299 independent seeds;
promptfoo's default of 5 seeds per plugin cannot rule out 45%. Search and measurement stay apart. Attackers such as
PyRIT, garak, GOAT and Crescendo find failures; rates are measured on held-out cases. Rainbow Teaming shows why: after
fine-tuning on the prompts it found, attack success fell from 92% to 0.3%, yet a fresh search still reached 39%.

### 5. Item response theory needs a population

See "Sample-efficient evaluation without a population of earlier models" below.

### 6. Many rewordings, two families

PromptEval estimates the spread of one model's accuracy across 100 prompt templates for about the cost of two
templates. Rainbow Teaming keeps an archive over two axes, risk and attack style, with a similarity filter, so search
fills the cells instead of collapsing onto one trick; an earlier reinforcement-learning red-teamer put the word
"invisible" in 78% of its prompts. For Pipit: an archive keyed to the tree (mechanism by surface), many cheap
rewordings per case with their spread reported, and two families kept for replicating a mechanism. Rewordings count
as one unit (section 1): spread is a measure of its own, not more evidence.

### 7. Data quality, defined

Near-duplicates: MinHash over word shingles plus embedding distance; Distilabel ships both. Spread: embedding
dispersion and self-BLEU, as Rainbow Teaming reports. Realism: pairwise ratings, which agreed with people better than
single scores in QuRating (Kendall's τ 0.79 against 0.61). Each goes on the dataset card with its pass rates.

### 8. Many tests at once

A study now gives 68 node verdicts with no correction across them. EvalTree, the nearest relative (a capability tree
built by a model over an existing benchmark, with a binomial test per node), names the same gap. The playbook's
e-BH across the tree, with tests registered before the confirm run, closes it.

### 9. Provenance

Record engine, quantisation, endpoint and speed for every subject, and check a local model against a hosted copy on a
small canary set, as Artificial Analysis's endpoint index does across providers. Version case families the way
inspect_evals versions tasks: the first number changes when results stop being comparable, the second when only
the interface changes.

## Where Pipit adds something, and where it does not

New, as far as these sources show:

- The right answer to the decision itself set by construction, and checked by code on the rendered text.
- Helper models scored against planted truth in their role, continuously, before their output is used. P1's
  validator was wrong on 25 of its 31 flags.
- A verdict per question at a stated tolerance, with the cases still needed.
- The reliance certificate: how much a model can do alone at a stated silent-error rate.
- Exact paired comparisons on matched cases, model against model and attack against no attack. PyRIT collects
  such pairs and runs no test.
- A tree of hypotheses written before any data, with the cost of every node.
- Minimal pairs with planted truth, the format interpretability work needs.

Not new, and cited as prior art:

- Templated minimal pairs and invariance tests: CheckList (Ribeiro et al., 2020).
- A tree of tests grown by a model and a person: AdaTest (Ribeiro and Lundberg, 2022).
- Evaluation items written by models: Perez et al. (2022).
- Intervals and clustered errors: Inspect ships Wilson, t, bootstrap and clustered standard errors.
- Item response theory and adaptive testing: tinyBenchmarks, Fluid Benchmarking, metabench, REEval.

## Who does what

| Stage | Established work | Pipit's part | Decision |
| --- | --- | --- | --- |
| Frame | position papers, open-problem lists | hypotheses by mechanism and a tolerance, written before data | keep |
| Write cases | Data Designer; PyRIT converters; garak probes; promptfoo plugins; Bloom; Petri | planted truth, minimal pairs, difficulty settings | generator: Data Designer or our own (#22), your call |
| Run | Inspect; lm-evaluation-harness; promptfoo | adapters for MLX and the Perplexity decider | runner: Inspect, your call |
| Grade | code scorers; LLM judges; Llama Guard; HarmBench's classifier | code against planted truth; judges measured against people | keep, extend to judges |
| Decide | nothing found | tolerance tests, certificate, paired tests, cases needed, allocation | Pipit's core |
| Keep | Inspect logs; DVC; Hugging Face datasets | cost per role, case-set hash, dataset card | keep; card to build |

## The literature: what is known, what is open, what is ours

For each line of work, three things are kept apart: what the field knows, what it lists as open, and what is only new
to us. "Ours" marks a question these sources leave open that Pipit's planted-truth bench can test.

**Evaluation data written by models.** Known: models write evaluation items at scale and mostly correctly; 93% of
labels were right on Perez et al.'s risk sets, against 97% for human-written ones, and generators narrow diversity
and cannot test what they cannot do. AutoBencher, Task Me Anything, ACD and DyVal build items from declared goals or
graphs, with the answer fixed by construction; people judged 92.8–97% of AutoBencher's items correct. Open: keeping
results comparable as a benchmark changes (Dynabench). Ours: how much search and rewording a planted-truth family
needs before its result transfers to real traffic (#28).

**Red teaming and auditing.** Known: attacker models reach 90% success and more on many targets (PAIR, TAP, GOAT,
Crescendo); quality-diversity archives avoid collapse (Rainbow Teaming); judges err, TAP's with 13% false positives.
Petri gates audits on realism and on whether the target noticed it was being tested; Bloom writes scenarios from a
described behaviour and scores them 1–10, validated on 40 hand-labelled transcripts; AuditBench plants quirks in 56
fine-tuned models. Open: "How can we standardize the evaluation of jailbreak and prompt injection success?" and how an
LLM judging an LLM can mislead (Anwar et al., 2024, questions 115 and 91). Ours: success checked by code where a
target can be planted, paired with a no-attack baseline and certified on fresh seeds with the budget stated; quirks
planted by system prompt as the laptop-sized model organism.

**Sample-efficient evaluation.** Known: item response theory fitted on a population of earlier models cuts the items
needed several-fold to fifty-fold (tinyBenchmarks, metabench, Fluid Benchmarking); active testing picks informative
items and reweights them so the estimate stays unbiased, with about 4 times fewer labels (Kossen et al., 2021).
Open: item response theory after post-training and with few models (Fluid); how good the surrogate must be (active
testing). Ours: whether active testing with a reference model as the surrogate, plus confidence sequences, recovers
planted thresholds with fewer cases than an even spread.

**Data for interpretability.** Known: counterfactual pairs that change one variable, aligned token by token, scored
by a logit difference (IOI, CausalGym); token replacement works better than added noise. Open: how sensitive
interpretability results are to the dataset (Anwar et al., question 107), and methods that build probing datasets
automatically (Sharkey et al., 2025). Ours: two planted-label families per mechanism test that sensitivity directly.
Exports must check tokenisation: "10 mg" and "20 mg" may split differently.

**Training and distillation data.** Known: synthetic instructions work (Self-Instruct, Evol-Instruct, Orca 2,
Magpie, Persona Hub), but their labels are often wrong; Self-Instruct's own audit found 54% of instances fully valid,
and only 11.6 thousand of Persona Hub's 20 thousand held-out problems had teachers agree. Verifiers beat LLM judges
for preference pairs (Nemotron-4). Training on a model's own outputs loses the tails first; adding real data, rather
than replacing it, prevents the collapse (Shumailov et al.; Gerstgrasser et al.). Data is best judged by its effect
under a fixed training recipe (DataComp-LM). Data aimed at failures helps when pre-tested (TDG), and generating from
earlier synthetic items hurt (LLM2LLM: 23.75% to 18.3% on GSM8K). Open: how much rationale quality matters in
distillation (Hsieh et al., 2023). Ours: verified against unverified rationales, as one controlled comparison on P1;
whether data for rare planted failures survives several rounds.

**Automated research loops.** Known: keep-or-discard loops work where an automated evaluator exists (AlphaEvolve,
Karpathy's autoresearch); agents game graders they can see (o3 reward-hacked in 39 of 128 RE-Bench runs, and telling
it not to had "nearly negligible effect"); papers written by agents carry wrong numbers (in an independent check of
the AI Scientist, 5 of 12 experiments failed on coding errors). Open: how often a keep rule based on one run accepts
noise; autoresearch's last kept change was a new random seed. Ours: that false-keep rate, and the cost of replicates,
measured on synthetic subjects with planted effects.

## Automatic data research: the loop these sources point to

The aim: given a question about a model, build the data that answers it, evaluation data first, and training or
distillation data only for a limitation that has been confirmed.

1. One family spec compiles to cases, split by family and scenario into explore, focus and confirm. Confirm never
   feeds training, selection, prompts or the loop.
2. Writers vary only what cannot change the answer, seeded from real material; code sets every label.
3. Every helper is scored against planted truth in its role before use; every judge against published human labels
   where code cannot grade.
4. The allocator sends cases where the evidence straddles the tolerance, reweighted so rates stay unbiased, with
   stopping that stays valid when we look early.
5. Confirm on fresh, frozen families, with tests registered in advance and e-BH across the tree, counted once per
   unit.
6. A training study opens only from a confirmed limitation. Its seeds are the model's failures on original cases,
   never on synthetic ones. Rationales are kept only when their numbers match the computed truth. The hint that
   removes the error goes to the teacher and is erased for the student (Orca 2). Preference pairs take the model's
   wrong answer as rejected and the planted answer as chosen.
7. Before generating at scale, each cell is pre-tested: training on half must help the other half without loss
   elsewhere (TDG).
8. Data is judged by its effect under a fixed recipe on planted-truth evaluation, with paired tests on every cell,
   not only the target.
9. Synthetic data is added, never substituted for real data; frozen seed families stay as anchors; everything is
   checked for near-duplicates of the confirm set.
10. The improvement loop edits recipes, never the bench. It keeps a change only beyond seed-to-seed noise, and accepts
    once, on an untouched split.
11. Graders and planted truth are hashed and hidden from agents; any edit to them is rejected; logs are screened.
12. The confirm split is opened and closed by its registered rules, and a dataset is released only when it passes
    the release gate in `CONTRIBUTING.md`.

## Sample-efficient evaluation without a population of earlier models

tinyBenchmarks fits an item response model on 395 earlier models answering the same items, then estimates a
benchmark from about 100 anchor items, within 1–3% per scenario. Its precondition is that population. Pipit writes new
items for each study and tests a handful of models, so it has none, and an item bank now would be a method looking for
a problem. What fits instead:

- **Difficulty set by construction.** Where a mechanism has a setting, such as dose ratio, days overdue or how deeply
  a fact is buried, an item's difficulty is known before any model answers. A threshold and slope fitted per model,
  with each next case placed where it tells us most, is Fluid Benchmarking's machinery without the population. QUEST
  and Psi do this in psychophysics.
- **Active testing.** Choose cases by a surrogate's expected loss, using the reference model or a lab model, then
  reweight them so the failure rate stays unbiased and the certificate honest.
- **Templates within one model.** PromptEval borrows strength across templates within a single model.

The test is the playbook's first experiment: on synthetic subjects with planted thresholds, does adaptive selection
recover them with fewer cases than an even spread, without more false claims? It comes next (#8, #9). Once tens of
models have answered the same Pipit items, an item bank becomes possible, and the bench will say when it pays.

## What comes next

1. The bench and adaptive measurement (#8, #9): the experiment above.
2. Run on Inspect, or read its logs: a new issue, and your decision.
3. Judges scored against published human labels, with their error carried into the interval: a new issue.
4. Attack claims with their budget, with PyRIT or garak as the attacker: a new issue.
5. The family spec: build on Data Designer or keep our own (#22): your decision.
6. The evidence rule with e-BH and confidence sequences (#25).
7. `report.json` and a viewer (#18, #19), unless Inspect's viewer serves.

## Related work at the main venues

Two passes on 1 November 2026 read about 90 papers from vision, language and machine-learning venues, each venue
confirmed on its official proceedings. By approach, with where Pipit stands:

| Approach | Examples | What they do | Where Pipit stands |
| --- | --- | --- | --- |
| Truth set by construction | CLEVR (CVPR 2017), HANS (ACL 2019), BLiMP (TACL 2020), ARO (ICLR 2023), PUG (NeurIPS 2023), MedCalc-Bench (NeurIPS 2024) | code, templates, rendering or formulas compute every answer | the same principle; none of these reports intervals, a tree or a certificate |
| One factor changed, the pair scored together | contrast sets (EMNLP Findings 2020), Winoground (CVPR 2022), ImageNet-E (CVPR 2023), MMVP (CVPR 2024), NaturalBench (NeurIPS 2024), MSSBench (ICLR 2025) | minimal pairs; contrast sets and MMVP credit a pair only if both halves are right | the same unit as section 1; most of these let people set the truth |
| A fact present or absent fixes the answer | BBQ (ACL Findings 2022), Med-HALT (CoNLL 2023), XSTest (NAACL 2024), MOSSBench (ICLR 2025) | ambiguous against disambiguated contexts; safe prompts that look unsafe | P1's critical, benign and absent conditions follow this design |
| A difficulty setting | ImageNet-C (ICLR 2019), DyVal, CNS-Bench (ICCV 2025) | severity on a scale; CNS-Bench reports a failure point per image | the closest published version of Pipit's planned staircases |
| Searching for failures | Domino (ICLR 2022), AdaVision (ICCV 2023), PromptAttack (ICCV 2023), MultiMon (NeurIPS 2023) | find slices where a model fails; Domino and PromptAttack score their search on planted errors | Pipit writes its tree first; scoring a search on planted errors is what Pipit's bench does |
| Agents and security graded by code | WebArena (ICLR 2024), Tensor Trust (ICLR 2024), AgentDojo (NeurIPS 2024), τ-bench (ICLR 2025), AgentHarm (ICLR 2025) | final state or a planted secret checked by code; τ-bench's pass^k needs all k tries to succeed | the route to planted truth for multi-turn and agent work, which Pipit lacks |
| Planted variables for interpretability | CEBaB (NeurIPS 2022), RAVEL (ACL 2024), InterpBench (NeurIPS 2024), Geometry of Truth (COLM 2024), MIB (ICML 2025) | counterfactual pairs with known values; MIB scores a hidden test set through an API | Pipit's minimal pairs fit this format; none of these is a decision task |
| Fewer items | active testing (ICML 2021), dueling bandits for generation (ACL 2022), Fogliato et al. (ECCV 2024), Sort and Search (NeurIPS 2024), LiveXiv (ICLR 2025) | reweighted or stratified samples, bandits, item response theory | most need earlier models or a fixed pool; the bandit work finds a winner, not a rate |

**Statistics in practice.** Only 63 of 180 experimental ACL 2017 long papers tested significance (Dror et al., ACL
2018). A leave-one-out check found adequate power in 46% of past comparisons (Card et al., EMNLP 2020). Scores moved by
up to 76 points across prompt formats for one model (Sclar et al., ICLR 2024). None of the 45 vision papers reported a
correction for multiple tests or a power analysis; MedSafetyBench (NeurIPS 2024) corrected its 45 paired tests with
Bonferroni.

**Keeping test sets from leaking.** GPQA (COLM 2024) adds a canary string and asks that no example be posted online.
GSM1k (NeurIPS 2024) stayed private until a set date or until three open models reached 95%, with extra items held back
in case of leaks through APIs. AgentHarm (ICLR 2025) keeps a 132-item private split, adds a canary string, and limits
use to safety work in its licence. MIB (ICML 2025) scores a hidden test set through an API. Jacovi et al. (EMNLP 2023)
propose encrypting public test data under a no-derivatives licence. DataDreamer (ACL 2024) writes a card with the
licence and citation of every step and a reproducibility hash, and publishes to the Hub.

**Use cases these papers target:**

- **Clinical:** MedCalc-Bench, MedSafetyBench, Med-HALT; in imaging, ProbMed and CARES.
- **Mental-health crisis:** the CLPsych 2024 shared task; Grabb et al. (COLM 2024) on psychiatric emergencies.
- **Customer support under policy:** ABCD (NAACL 2021) and τ-bench.
- **Agent security:** AgentDojo, InjecAgent, Tensor Trust and AgentHarm.
- **Legal and finance:** LegalBench (NeurIPS 2023) and FinanceBench.
- **Driving, documents, remote sensing and accessibility:** PromptAttack and DriveBench; CharXiv and LiveXiv; VRSBench
  and GEOBench-VLM; VizWiz.
- **Bias and over-refusal:** BBQ, WinoBias, Winogender, CrowS-Pairs and XSTest.

**Open problems these papers state that bear on Pipit:**

- Passing a finite test suite shows no general strength; only a failure shows a weakness (XSTest, after Gardner et al.).
- Five safe conversations cannot show a model is safe for mental-health use (Grabb et al.).
- Test items are rarely independent, and testing significance under that dependence is open (Dror et al.).
- Small sets lack power: GPQA's 448 items detect only large effects.
- Static security benchmarks are of limited use, because attacks adapt (AgentDojo).
- Model judges pass answers made up without the image (DriveBench).
- A fresh test set is only "highly similar, but not identically distributed" to the original (GSM1k).

## The five uses, as the field defines them

Read on 2026-11-01 at abstract or named-section level, by research agents; quotes are verbatim.

| Use | The field's definition | Open problems the field states | Sources |
| --- | --- | --- | --- |
| Data for post-training and distillation | examples used after pre-training to change behaviour: demonstrations, better-and-worse pairs, prompts with a checker or a rubric; in distillation a stronger teacher writes or scores them | correct labels at scale; rewards beyond checkable answers; reworded test items leaking into training; forgetting | Lambert et al., 2024 (Tülu 3); Gunjal et al., 2025 (Rubrics as Rewards); Xu et al., 2024; Liu et al., 2024 |
| Evaluation | "scenarios (i.e. use cases) and metrics (i.e. desiderata)"; "Fundamentally, evaluations are experiments"; held to construct validity | validity; missing statistics, with 16% of 445 benchmarks running any test; contamination; cost | Liang et al., 2022 (HELM); Miller, 2024; Bean et al., 2025; Alaa et al., 2025, for medicine |
| Auditing | "a systematic and independent process of obtaining and evaluating evidence regarding an entity's actions or properties and communicating the results of that evaluation to relevant stakeholders" | conclusions from outputs alone mislead; realism and test awareness; inconsistent judges | Mökander et al., 2023; Raji et al., 2020; Casper et al., 2024; Petri, 2025 |
| Alignment, interpretability, safety | aligned when "'trying' to behave as intended"; interpretability seeks "the computational mechanisms underlying neural networks' capabilities" | hidden goals; explanations that misstate the real reason; checking interpretability methods | Anwar et al., 2024; Sharkey et al., 2025; Hendrycks et al., 2021; Marks et al., 2025 |
| Reliability and routing | "ability of an item to perform as required, without failure, for a given time interval, under given conditions"; selective prediction "rejects instances as needed, to grant the desired risk" | checking LLM confidence; guarantees when cases change; repeatability; handing cases to imperfect receivers | NIST AI RMF 1.0, 2023; Guo et al., 2017; Geifman and El-Yaniv, 2017; Dvijotham et al., 2023 (CoDoC) |

**Borders.** Post-training data and evaluation are split by held-out data. Evaluation gives an average; reliability
gives the error rate among the cases a model decides alone. Auditing looks from outside, for whoever approves a
deployment, usually with outputs only; alignment, interpretability and safety look inside, for the developer, with
weights. NIST lists "safe" apart from "valid and reliable".

**MedCalc-Bench, which study V1 uses:** Krohn-Grimberghe (2026, arXiv 2603.02222) reports fixing over 20 errors in
the code behind its calculators and names 19 calculators.

## The loop as others have built it, 2025 and 2026

| Step | Systems | What their builders say is missing |
| --- | --- | --- |
| Generate cases with known answers | Reasoning Gym (Stojanovski et al., 2025); RLVE (Zeng et al., 2025); AutoBencher (Li et al., 2025); LiveBench (White et al., 2025) | domains that need deep knowledge; about 5% wrong labels in AutoBencher |
| Find where the model fails | EvalTree (Zeng et al., 2025); task elicitation (Brown et al., 2025); investigator agents (Li et al., 2025); Petri and Bloom (2025); AuditBench (Sheshadri et al., 2026) | ground truth for failure explanations on real models; judges that cannot check correctness or change one word; better tools do not make better auditors |
| Decide when the evidence is enough | Fluid Benchmarking (Hofmann et al., 2025); CELEUS (Zhou et al., 2026); adaptive auditing with anytime-valid guarantees (S. Zhou et al., 2026) | a cold start without earlier models; adaptive picking often barely beats uniform sampling for one average |
| Turn failures into training data | SwS (Liang et al., 2025); failure-driven synthesis (Rajbahadur et al., 2026); LIMO and s1 (2025); Rubrics as Rewards and checklists (2025) | what the data fixed and what it broke; rubric rewards gamed during training; what a rejected answer teaches |

What Pipit can add, as experiments for the releases ahead: failure profilers and auditors scored against known
causes planted in real models' inputs (EvalTree checked its profiles only on simulated scores); Petri with and
without Pipit's code checker; whether discovered failure rates hold on fresh cases, which no paper we found
measures for failure discovery; the
hypothesis tree as an anytime-valid auditor with generated cases; and training data checked on its twins. Not to be
rebuilt: generators with difficulty dials, trees with a test at each node, intervals that survive early stopping, and
the recipe that turns failures into training data.

## Sources, and how deeply each was read

Research agents working for this project read every source below on 1 November 2026, mostly through a tool that
summarises long pages; quoted numbers were checked against the raw text. No person on the project has yet read any of
them in full, so each stays unverified until someone does.

- **Code and documentation, read on GitHub:** Inspect and inspect_evals; inspect_petri and petri_bloom (Meridian
  Labs); lm-evaluation-harness; HELM; METR's task standard, Vivaria and Hawk; NeMo Data Designer; Distilabel;
  Curator (Bespoke Labs); tinyBenchmarks; Fluid Benchmarking; PromptEval; CheckList; AdaTest; garak; PyRIT; promptfoo;
  DeepEval and DeepTeam; Giskard; HarmBench; JailbreakBench, including its 300 human labels, recounted; Ragas;
  Karpathy's autoresearch. Web pages: Artificial Analysis's methodology; METR's time-horizon and reward-hacking posts;
  Anthropic's posts on Bloom, Petri, automated auditing and statistical evaluation.
- **Papers, method, results and limitations sections:** Perez et al. 2022 (model-written evaluations; red teaming
  with LMs); Rainbow Teaming; PAIR; TAP; GOAT; Crescendo; AutoBencher; Task Me Anything; ACD; EvalTree; DyVal;
  Dynabench; LiveBench; Kossen et al. 2021; Fluid Benchmarking; Flash-HELM; tinyBenchmarks; PromptEval; IOI;
  CausalGym; Zhang and Nanda 2023; Heimersheim and Nanda 2024; Anwar et al. 2024 (parts); Sharkey et al. 2025
  (parts); Self-Instruct; Evol-Instruct; Orca and Orca 2; Magpie; phi-1; Nemotron-4 340B; Persona Hub; distilling
  step-by-step; Wang et al. 2021; ZeroGen; AttrPrompt; Li et al. 2023; Gudibande et al. 2023; TDG; LLM2LLM; LESS;
  DSIR; QuRating; DataComp-LM; Shumailov et al.; Gerstgrasser et al.; Guo et al.; Northcutt et al.; the AI Scientist
  and its second version; Beel et al.; AlphaEvolve; MLE-bench; METR's time-horizon paper (about half); Miller 2024.
- **Abstract or summary only:** prediction-powered inference; metabench; REEval; Anchor Points; HarmBench and
  JailbreakBench papers; Cosmopedia; AuditBench.
- **Not read:** Hughes et al. on best-of-N jailbreaking; QUEST and Psi; Data Designer's technical report; the CheckList
  and AdaTest papers.
- **The venue passes:** for most of the about 90 papers, the abstract plus the method, results and limitations passages
  found by searching the full text; for some, the abstract only. Venues were confirmed on the CVF open-access site,
  ecva.net, the ACL Anthology, OpenReview, the NeurIPS proceedings and PMLR.
