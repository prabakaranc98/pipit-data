# Changelog

All notable changes to Pipit are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Found by three independent verification agents, which checked every claim of 0.0.3 and 0.0.4 (#68):
  - Thinking mode: each option's probability is its share of all samples, so samples cut off at the token budget count against confidence; reasoning cut off before its end gives no answer. P1's thinking-mode answers were recounted from the recorded votes with no model call: 8 of 30 rows change confidence, no choice changes, calibration error falls from 0.100 to 0.011, and at 10% silent errors the model can act alone on 63% of cases.
  - The OpenRouter adapter: one time limit across all of a call's attempts, so a reply that stalls uses the call's whole time and is not tried again, where in 0.0.4 it had one more try; a rejected key (HTTP 401) stops at once.
  - `pipit.preflight`: pinned means exactly one provider; pinning and prices are required only of models whose provider varies per call, so TypeSafe's own API can pass; an OpenRouter model without prices is flagged; the cost check is called an estimate.
  - `pipit.results`: a half-written last row no longer blocks a resume, and files are rewritten in one step.
  - Every committed manifest declares a family (seven did not). V1's runner records each run, including whether unpinned models were allowed and which models were pinned, and its report reads the pinning from that record and the ledger (#70). X1 uses the core's exact paired test. P1's case builder keeps the fields written by hand.
  - Docs: P3 sent the crisis message to the vulnerable-customer team, not "to billing", and missed no crisis outright; on I1, two other families also barely move, so that is not unique to doses; P1 settles one or two of twelve key questions; X1's header (realism 6 to 10 on sycophancy, $0.014 of helper calls to build P1's cases, seven cut-off replies, 12 and 22 minutes per arm); install with `uv sync --all-extras`, since a plain sync removes the adapters' libraries; P1's case cache is local; finance comes next in the plan and the grid; G1 is marked as local, unmerged work; stale plan text.
- Found by the independent review of #69 (#70):
  - Thinking mode: a yes/no answer is one number, the probability of yes, so an unanswered sample now counts half yes and half no instead of as a no; a reply stopped at the token budget gives no answer even when a stray letter is in it. No committed result changes: no thinking run asked a yes/no question, and the 11 recorded samples stopped at the budget already gave none.
  - `pipit.results`: a last row cut off before its newline is kept and given its newline, so the next resume neither fails nor asks rows again; the file is rewritten only when it needs that repair.
  - The OpenRouter adapter: when waiting after an error uses up a call's time, TooSlow is raised from that error and names it. `pipit.preflight`: OpenRouter reached through `openai_compat` varies by provider too; a run replayed wholly from the cache still needs prices, a known limit.
  - CI runs the docstring examples of `pipit.preflight` and `pipit.results`. X1's report is written by `assemble.py` from its parts. V1's report reads which calls were pinned from its run log and ledger, not from today's manifests, and no longer stops at a results file with no manifest; its reading says Llama 3.1 70B's 39% is near the paper's 36% for a different model. P1's `propose.py` no longer says a person must read every proposal.
  - Docs: "no step waits for a person" now holds for the loop in the methodology, engine, architecture, agentic, design, landscape and programme docs and in the four diagrams they show. #69 claimed it for five of the docs, but the agentic and design docs, lines in four others and the diagrams still put a person at a step. Gates are rules registered in advance. Where a person still acts, the docs say so as such: the study owner chooses the question before the loop starts, the columns that describe today's build list what is still done by hand with what replaces it, and the design doc records that a person read P1's validator flags. Also: the time limit and the stop at a refused key apply to every OpenRouter call, not only V1's; building P1's cases cost $0.014 of helper calls, now the one figure in X1's report, the design doc and the plan, which said 0.015 and one and a half cents (the gap is the proposer's $0.0006, recorded only in the local cache); the design doc's eight research passes; finance before legal in the plan's list of industries; the suite's reading list holds 127 quotes over 125 references, not 135; 0.0.3's closed issues sit in milestones M1, M3, M4 and M6, and three it began stay open; a sentence the engine doc repeated.
- Found by the independent review of #71 (#72):
  - V1's report credits a call to a run that pinned providers only when that run held the call's model, since V1 ran several runs at once; today's report has no run log, so nothing in it changes. The OpenRouter adapter no longer blames a stall on an error the call had already got past, and a stall on the last attempt names the model.
  - Docs: the last lines that put a person at a step of the loop, or read that way. Deep Agents' approval on tool calls stays off; Pipit aligns its checkers with planted truth in place of human corrections; judges are scored against published human labels, not "against people"; the engine's policy table names what is done today, and the bench is to set a scripted baseline for proposing, splitting and writing. The design doc's AdaTest row says a person read P1's flags, as its pipeline table does. P1's `propose.py` no longer writes "for human review" into the proposals it generates; the committed proposals.md keeps its old header until proposals are generated again. The suite's reading list has 125 entries citing 123 sources, with 127 quotes, each word for word from the research draft; a script checked 135 quotes gathered for that draft, these among them, against their saved sources. The README's status line.
  - `openai_compat` reuses `pipit.checks.stopped_on_length`; `pipit.preflight` counts only OpenRouter's host or a subdomain, whatever its case; CI runs the docstring examples of the whole package, not two named modules.
- Found by the re-review of #73 (#80): the suite said its quotes were exact substrings of their saved sources; 131 of 135 are, and all 135 once quote marks, dashes and spaces are evened out, which is what it now says. The landscape's four short lines on judges now give the fallback its main text gives: planted items and a measured panel where no published human labels fit.
- Docs, found while re-planning (#80): the plan said CI rebuilds every report; it rebuilds six of the seven, and the release gate rebuilds I1's. CONTRIBUTING's list of what CI must pass now names the docstring examples and the rebuild check. The architecture page pointed at numbered plan steps the plan no longer has, and drew the pictures, which P1's report uses, as planned; it now names releases and draws them as built. The methodology's table of cases per node holds for fixed intervals; it now also gives the confidence sequence the loop stops by, about twice as many per node, so with an even spread 500 cases settle about half as many key questions.

### Added

- `studies/rebuild.py` (#74): rebuilds every study's report from its recorded runs and fails when one differs from what its script writes, when a script does not write it, or when a script writes a file no step declares; it will not run over uncommitted edits to a report, and it names each step it skips and why. CI runs it on every pull request, where seven of its eight steps (six reports, P1's tree and X1's pressure section) rebuild byte-identical in about 40 seconds; I1 needs numpy and its activations file, which git does not keep, so CI names it as skipped. `--all` fails on a skipped step too, for the release gate. Tests check that drift, a script that writes nothing, a stray file, an unsaved edit and a skipped step under `--all` are each caught, and that every committed report has a step. After its re-review (#79), it reads its scripts' output as UTF-8 whatever the machine's locale, and still catches a script that writes nothing on drives that store a zero timestamp as 1980, such as exFAT.
- `docs/suite.md` (#68): the reference problem suite. Fourteen problems and four industries, each with its source, its documented finding, Pipit's status and what is missing, and a reading list of 125 references with quotes checked against their sources.
- `CONTRIBUTING.md` (#68): an independent review of every pull request before it merges, and the release gate that every release must pass before it is tagged.

### Changed

- The plan (#80): the releases are reordered so the evidence loop closes first, for one cell, clinical × reliability. 0.0.6 now asks "Does the loop close?" and takes the family spec (#22) and the stopping rule that stays valid when the loop stops early (#25); 0.0.7 confirms every finding the dossier relies on, on fresh, held-back families, the dose finding first; 0.0.8 is the reliance dossier, which with the dataset and one write-up is this cycle's finish line. `report.json`, the study registry, the model inventory and the programme tables (#18, #54, #20, #17) move to 0.0.14, and the renames, type checks and importable studies to 0.1.0. New code follows the naming rules in `CONTRIBUTING.md` from now on.

### Corrections to earlier entries

- 0.0.3: Qwen3.5-4B against the decider gives p = 0.041 counted once per case, not the per-wording 0.006 written before that release's own fix. The landscape came from eight research passes over about 160 tools and papers, not six over about seventy.
- 0.0.4: the checks before a run and the results saved per item ran in V1's runner only, while the time limit and the stop at a refused key, in the OpenRouter adapter, applied to every OpenRouter call; the time limit applied per attempt; the cost check was an estimate, not an upper bound; the `--allow-unpinned` flag was not recorded; Llama 3.1 70B's 39% is near the paper's 36% for a different model, Llama 3 70B.

## [0.0.4] - 2026-11-01

### Added

- `pipit.preflight` (#66): checks before a run. Every model declares a family, every API model is pinned to a provider (otherwise an explicit flag, recorded only from 0.0.5), no helper shares a candidate's family, and an estimate of the cost fits the key's budget. Only V1's runner calls it.
- `pipit.results` (#66): results saved as each item finishes, so a run that stops resumes where it stopped.
- The OpenRouter adapter (#66): a refused key raises `KeyRefused` at once instead of being retried; each call has a time limit, `settings.deadline_s` (600 s unless set; per attempt until 0.0.5), because keep-alive padding defeats the socket's timeout; `budget_left` reads what is left on the key. V1's runner uses all of them, and its result files replay unchanged.
- Study V1's results (`studies/v1_medcalc`, #57): twelve models on 220 MedCalc-Bench items and on P1's 112 cases, for $6.90. Across 12 models the two do not rank the models alike overall (Spearman 0.21, p = 0.25); where both measure calculation they agree (0.61, p = 0.020). Llama 3.1 70B scores 39%, near the paper's 36% for Llama 3 70B, a different model. Every model scores lower on the 19 calculators whose code an audit corrected. The report shows the providers behind each model, up to 18, and ends with a hand-written reading.
- `run.py --resume` in V1: after the API key's spending limit refused 1,385 calls, only those were sent again; a run now stops at the first refusal. Every V1 manifest declares its `family`.
- `docs/landscape.md`: the five uses as the field defines them, with their borders, and the loop as others built it in 2025 and 2026.

### Changed

- `docs/plan.md` (#66): no step waits for a person. Each human check is replaced by an automatic one grounded in a reference, and a panel of measured model families and decision models such as Jev stands in for reviewers; finance comes after clinical. `docs/methodology.md`: the new checks.
- `docs/plan.md`: the five uses' definitions from the field; 0.0.8 now asks whether a small model can approve alone at a stated clinical error rate across reruns; the registry, model inventory and programme tables move to 0.0.5, the viewer to 0.0.14; V1 is reported as run. README: the industries by uses grid, V1's result, and the releases in place of milestones M0 to M6.

## [0.0.3] - 2026-11-01

### Fixed

- Intervals, replays, paired tests and the reliance certificate now count a case and its rewordings once (`pipit.evidence`, `pipit.calibration`). In P1 the two wordings of a case agreed in 51 to 53 of 53 pairs, so counting both claimed too much: 8 of 68 verdicts move to insufficient, grouping the questions is no longer shown to hurt (p = 0.021 becomes 0.18), and certificates at 5% silent errors shrink (Jev 64% to 60%). Two simulations in `tests/test_units.py` show the old counting covering 88% instead of 95%, and certifying 12% of models that sit at the limit instead of at most 5%.

### Added

- Study V1's amendment before any accuracy was computed (#64): its report counts the replies cut off at the token cap and the failed calls for each model, and its permutation test states how it was run.
- `CONTRIBUTING.md`: how work moves, plain names, code, studies and reports, data, and a glossary of Pipit's words (#62).
- `pipit.allocate`: where the next cases go. An even spread, the thresholding rule, and a rule that samples the open question nearest to a verdict (#9).
- `pipit.sequential`: a confidence sequence for a failure rate, valid at every sample size, so a question may stop as soon as its evidence clears; the node rule reads it with `sequential=True` (#25).
- Study B1 (`studies/b1_bench`): the bench, synthetic subjects with planted failure rates (#8). Sampling nearest to a verdict on ordinary intervals settles up to 15 times as many questions as an even spread but claims falsely in up to 25% of runs. On the confidence sequence it settles 4 to 44 times as many as an even spread on the same sequence at 240 units and under twice as many at 60, with a false claim in at most 1.3% of runs; at 60 units it settles fewer than an even spread on ordinary intervals.
- `docs/engine.md` and `public/assets/overview.svg`: the method as computation. The tree as a partition of the case space, the loop as a sequential experiment with explore and confirm kept apart, feedback paths with their guards, statistics at three levels, judges measured like any model, the team's models, and experiments E1 to E5.
- `docs/plan.md` by module: scientific, algorithmic, build and use modules with their state; dataset styles; evaluation aspects after the SAgE group's reliability dimensions; who does what, with each role's model, evidence and next test; the build order mapped to issues #38 to #52.
- `docs/methodology.md`: how a study goes from a gap to a Hub release, with the independent cases a node needs to be settled, which sets a tree's width and depth.
- Study J1 (`studies/j1_judges`): four judges measured on 177 planted items from P1. DeepSeek V4.1 Flash is the best default; V4 Pro passed 14 of 20 unsafe proposals when the reply told it to; Jev failed as an injection guard; Nemotron 3 Ultra raised the most false alarms. None can be certified on 20 unsafe items.
- Study X1 (`studies/x1_petri`): Pipit and Petri 3.1.1 on Qwen3.5-4B, on clinical decisions and on sycophancy. Pipit's pressure test flipped 18 of 39 right decisions when a doctor insisted (exact paired test p = 0.0015), with no judge and no cost.
- Study I1 (`studies/i1_interp`): a probe, last-position patching and the Explain step on P1's minimal pairs, each registered before it ran. Qwen3.5-4B holds the planted fact at the decision point from about layer 16, on 11 of 13 wrong decisions too; patching shows the decision gathered there from layer 18; stating the computed dose per kilogram changed no dose decision.
- Native setups for LLM candidates (#35, merged in #58): thinking mode in `pipit.adapters.openai_compat`, at the sampling settings the model card recommends, with confidence from how often several samples agree; a request timeout per manifest; P1's runner asks one question, runs cases in parallel and can take a few cases per cell. Qwen3.5-4B in thinking mode made 5 mistakes in 30 against 8 in instruct mode on the same cases (exact paired test p = 0.51), for 5.8 hours of local compute. `pipit.viz` draws a hypothesis tree with each node's evidence and status.
- `pipit.tree`: checks that a hypothesis tree partitions its cases; P1's tree is now built through it, and its spec states the conditions each key question covers (#45).
- The family rule: manifests declare a `family`, and `pipit.manifest.family_conflicts` reports any helper, judge or council member sharing a family with a candidate; P1's Qwen validator is the first case it catches (#43).
- `pipit.ledger.providers` and `mixed_providers`: which providers served each API model, so a model routed to several can be pinned (#44).
- `docs/landscape.md`: Pipit against the field, from eight research passes over about 160 tools and papers: what it gets wrong, ranked; what it adds and what is prior art; the literature by line of work, kept apart as known, open and ours; the loop for automatic data research; why item banks wait for a population of models.
- `pipit.checks.mcnemar_exact`: the exact paired test, moved from the study scripts into the core.

- `docs/architecture.md`: the components by layer (interfaces, control plane, agent team, core, engines, data, quality), built or planned; three loops at three speeds; how configuration flows from a machine profile to a study file to manifests; memory on a laptop, measured, and the rules that keep a run out of swap; one diagram.
- `docs/methodology.md`: the playbook. Models write, statistics allocate, code grades, people decide; eight steps from framing to report, each with an owner and a check; how agents carry it through skills, tested prompts, scoped context and coordination through the record; what it enables for research; and three experiments that will show whether it works. `docs/plan.md`: the path to 0.1.0 reordered around it.
- `pipit.adapters.openai_compat`: any LLM behind an OpenAI-style endpoint (MLX, vLLM, SGLang, llama.cpp, Ollama, OpenRouter) answers typed questions as single-letter multiple choice, with option probabilities from the first answer token's log-probabilities, the share of probability on the letters recorded, a request cache, ledger rows per question, and an optional local server launched from the manifest. An `mlx` extra for Apple silicon. P1 run on Qwen3.5-4B in BF16 through MLX, next to the decider trained from it: 36 mistakes against 19 of 112 (exact paired test p = 0.041, counted once per case); the LLM reads facts about as well but turns them into wrong decisions more often, fails indirect clues (10 of 16 against 0), and shares the decider's weakness on weight-based doses.
- `docs/plan.md`: the plan to 0.1.0: who Pipit helps, why a few hundred planted cases instead of tens of thousands, any model on any engine, studies as data, the measurement science, the developer experience, ten steps, and what 0.1.0 means. `docs/agentic.md`: the study team, for 0.2. README: a reading order, milestone M6 and the 0.1.0 definition.
- `docs/programme.md`: the five-study programme on one candidate and its shared protocol; milestones M4 and M5 in the README.
- `pipit.calibration`: calibration error, Brier score, the review band, an exact binomial reliance certificate tested from the strictest cut-off down, and the number of cases a certificate needs. The P1 report gains the certificate, an exact paired test between subjects, a ledger by subject, and the Perplexity model run with its two questions grouped.
- Study P3 pilot (`studies/p3_support_crisis/`): crisis triage in a messy support queue, 24 hand-written cases in four families (danger inside a complaint, account takeover under pressure, a customer in crisis, someone else's data exposed), each clear, buried and look-alike; both subjects run; the report counts missed crises, false alarms and wrong crisis teams, checks the two answers against each other, and tests combining them in code.

### Changed

- `docs/plan.md` (#62): the road to 0.1.0 as small releases, one question each; Pipit's five uses, with data as the central artifact; what Pipit makes for each post-training step (it makes the data and measures the result, the training runs elsewhere); NeMo Data Designer as a comparison, not a dependency; agentic tasks at 0.2.5 to 0.3; five industries; the gaps found on 2026-11-01; the decisions taken and open; plain names proposed for 0.0.6.

## [0.0.2] - 2026-10-31

### Added

- `pipit` core: typed questions, YAML manifests resolved through edge adapters, a request cache, a cost ledger, executable checks (completeness, token-limit stops, severity, Wilson intervals), evidence cells with verdicts and a hypothesis-tree roll-up. The core imports no model library; `local` and `typesafe` extras carry the adapters' dependencies.
- Adapters: OpenRouter chat (cost from the response, empty content retried and never cached), TypeSafe Jev, and the Perplexity decider run locally in BF16.
- Study P1 (`studies/p1_clinical/`): pre-registration, hypothesis tree, ten clinical case families, a 120-case set built with two lab models and reproduced from the cache, candidate and reference runs, adjudication, report and proposals.
- `docs/design.md`: the loop, the instrument, what P1 showed, references and differences.

## [0.0.1] - 2026-10-31

### Added

- M0, the repository contract: the `pipit` package skeleton at version 0.0.1, lint and tests in CI, issue and pull-request templates, and the README with the discipline, the two model roles, the milestone ladder and the versioning scheme.
- Lab models reach Pipit through hosted APIs: TypeSafe for decision models, OpenRouter for LLMs of every size.

[Unreleased]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.4...HEAD
[0.0.4]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/prabakaranc98/pipit-data/releases/tag/v0.0.1
