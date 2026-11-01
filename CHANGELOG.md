# Changelog

All notable changes to Pipit are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pipit.adapters.openai_compat`: any LLM behind an OpenAI-style endpoint (MLX, vLLM, SGLang, llama.cpp, Ollama, OpenRouter) answers typed questions as single-letter multiple choice, with option probabilities from the first answer token's log-probabilities, the share of probability on the letters recorded, a request cache, ledger rows per question, and an optional local server launched from the manifest. An `mlx` extra for Apple silicon. P1 run on Qwen3.5-4B in BF16 through MLX, next to the decider trained from it: 36 mistakes against 19 of 112 (exact paired test p = 0.006); the LLM reads facts about as well but turns them into wrong decisions more often, fails indirect clues (10 of 16 against 0), and shares the decider's weakness on weight-based doses.
- `docs/plan.md`: the plan to 0.1.0: who Pipit helps, why a few hundred planted cases instead of tens of thousands, any model on any engine, studies as data, the measurement science, the developer experience, ten steps, and what 0.1.0 means. `docs/agentic.md`: the study team, for 0.2. README: a reading order, milestone M6 and the 0.1.0 definition.
- `docs/programme.md`: the five-study programme on one candidate and its shared protocol; milestones M4 and M5 in the README.
- `pipit.calibration`: calibration error, Brier score, the review band, an exact binomial reliance certificate tested from the strictest cut-off down, and the number of cases a certificate needs. The P1 report gains the certificate, an exact paired test between subjects, a ledger by subject, and the Perplexity model run with its two questions grouped.
- Study P3 pilot (`studies/p3_support_crisis/`): crisis triage in a messy support queue, 24 hand-written cases in four families (danger inside a complaint, account takeover under pressure, a customer in crisis, someone else's data exposed), each clear, buried and look-alike; both subjects run; the report counts missed crises, false alarms and wrong crisis teams, checks the two answers against each other, and tests combining them in code.

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

[Unreleased]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/prabakaranc98/pipit-data/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/prabakaranc98/pipit-data/releases/tag/v0.0.1
