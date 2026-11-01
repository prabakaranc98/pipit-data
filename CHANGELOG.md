# Changelog

All notable changes to Pipit are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
