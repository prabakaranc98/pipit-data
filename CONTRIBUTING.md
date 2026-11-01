# Contributing to Pipit

Pipit should be as easy to read and extend as pandas, NumPy or scikit-learn: plain words, names that say what they
do, and one way to do each thing. This guide sets the rules. Where the code does not follow them yet, release 0.0.6 in
`docs/plan.md` brings it in line.

## How work moves

- Each step gets an issue when it starts, not before.
- One branch per issue, named `m<N>/<topic>`. One pull request open at a time, always against `main`.
- CI must pass: lint, format and tests; type checks from 0.0.6.
- Docs change in the same pull request as the code they describe. Every change goes in `CHANGELOG.md`, renames
  included.
- Releases are small: 0.0.3, 0.0.4 and so on, each answering one question. The study owner tags them.

## Names

- **One plain word per concept,** the same in code, docs and reports. The glossary below is the list.
- **A name says what it returns or does:** `wilson_interval`, `verdict`, `load_model`, `question_prompt`.
- **No abbreviations in public names:** `expected_calibration_error`, not `ece`.
- **Plain parameter names:** `failures, total`, not `fail, n`. The mathematical symbol goes in the docstring.
- **No vendor or SDK words in the core.** An engine's own terms stay in its adapter.
- **Study code stays in its study.** The core holds only what more than one study uses.

## Code

- Type hints on every public function and class.
- A docstring on every public function: what it does, its arguments, what it returns, and a short example.
- Each module lists what is public in `__all__`; everything else starts with an underscore.
- A change in behaviour ships with a test. Tests are named after the module they cover.
- Keys come from the environment, never from a file in the repository; `.env` is ignored by git.

## Studies and reports

- A study is a folder: its pre-registration, its code, its recorded runs and its report.
- A report is written by its script from recorded runs and is never edited by hand. A hand-written reading goes in a
  separate file that the script includes.
- Numbers in the README and docs are copied from a report; from 0.0.5 they are checked against its `report.json`.
- An amendment to a pre-registration is written before the results it affects are read, and says what prompted it.

## Data

- Every case records where it came from and its licence. Data whose licence forbids redistribution is downloaded at
  run time and never committed.
- Training data comes only from explore families, never from a set used for evaluation.
- Outputs whose terms restrict reuse, such as Jev's under TypeSafe's terms, are published only as aggregates and are
  never used as training data.

## Glossary

| Word | Meaning |
| --- | --- |
| case | one input with its planted right answer |
| family | the cases built from one spec around one mechanism |
| scenario | one situation within a family: the person, the numbers, the setting |
| condition | how the deciding fact appears: critical, benign, absent or conflicting |
| wording | one phrasing of a case; the wordings of a case are not independent of each other |
| independent case | a scenario under one condition, with all its wordings; every count and interval uses this unit |
| hypothesis | one way a decision can fail, written so that evidence could refute it |
| key question | one factor under a hypothesis, with the cases it claims and its verdict |
| tree | the hypotheses and their key questions; every case belongs to exactly one key question |
| tolerance | the failure rate that matters for this use |
| verdict | supported, refuted or insufficient: the interval read against the tolerance |
| certificate | the share of cases a model can decide alone at a stated rate of silent errors |
| explore, confirm | cases used to find and adapt; held-back cases run once to confirm what was found |
| model | anything that answers, a decision model or an LLM, local or remote, registered in a manifest |
| role | what a model does in a study: candidate, reference, judge, writer or checker |
| manifest | the YAML file that registers a model: identifier, revision, engine, provider and family |
| ledger | one row per call: who asked what, how long it took and what it cost |
| cache | stored replies keyed by their request, so a rerun costs nothing |
