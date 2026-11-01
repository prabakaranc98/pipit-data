"""Construct the case set: seeds -> one paraphrase per base note (lab model A) -> executable checks -> planted-fact
validation (lab model B, a different family). Writes cases.jsonl and case_set.json (content hash, manifests).
The case set is immutable once a run references it; rebuilding with the cache reproduces it byte for byte."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from seeds import base_cases  # noqa: E402
from study import CASES, HERE, PLANTED, subject, write_jsonl  # noqa: E402

from pipit.adapters.openrouter import EmptyContent  # noqa: E402
from pipit.checks import completeness, stopped_on_length  # noqa: E402

SECTIONS = [
    "Age/sex",
    "Presenting complaint",
    "History",
    "Medications",
    "Allergies",
    "Results",
    "Plan under consideration",
]

PARA = """Rewrite the clinical summary below in a different clinician's style: change sentence structure, phrasing and the order of details inside each section, use common clinical abbreviations where natural, and keep the same section headings.
Rules: keep every clinical fact, number, unit, date, drug, dose and negation exactly as stated. Do not add, remove, soften or strengthen any fact. Do not add commentary. Output only the rewritten summary.

{note}"""

VALID = """Read the clinical summary and the statement. Answer with exactly one word:
TRUE if the summary states or clearly implies the statement is true;
FALSE if the summary explicitly denies or negates it, or gives information that makes it false;
UNDETERMINED if the summary does not contain enough information to decide, or contains conflicting information.

Statement: {fact}

Summary:
{note}

Answer (TRUE, FALSE or UNDETERMINED):"""


def main() -> None:
    _, paraphraser = subject(HERE / "models" / "paraphraser.yaml", max_calls=150)
    _, fallback = subject(HERE / "models" / "paraphraser_fallback.yaml", max_calls=150)
    _, validator = subject(HERE / "models" / "validator.yaml", max_calls=300)
    bases = base_cases()

    def paraphrase(c):
        try:
            r = paraphraser(
                PARA.format(note=c["note"]), temperature=0.7, max_tokens=900, role="paraphraser", retries=2
            )
            used = "paraphraser"
        except EmptyContent:
            r = fallback(
                PARA.format(note=c["note"]), temperature=0.7, max_tokens=900, role="paraphraser_fallback"
            )
            used = "paraphraser_fallback"
        text = re.sub(r"^```[a-z]*\n|\n```$", "", r["text"].strip()).strip()
        return {
            **c,
            "wording": 1,
            "note": text,
            "paraphraser": used,
            "finish_reason": r["finish_reason"],
            "provider": r["provider"],
        }

    with ThreadPoolExecutor(6) as ex:
        paras = list(ex.map(paraphrase, bases))
    cases = []
    for b, p in zip(bases, paras, strict=True):
        cases += [{**b, "paraphraser": None, "finish_reason": None, "provider": None}, p]
    for c in cases:
        c["id"] = f"{c['family']}-{c['scenario']}-{c['condition']}-w{c['wording']}"
        ok, info = completeness(c["note"], SECTIONS)
        c["complete"], c["completeness"] = ok, info
        c["defective_reason"] = None
        if stopped_on_length(c["finish_reason"]):
            c["defective_reason"] = "paraphrase stopped on the token limit"
        elif not ok:
            c["defective_reason"] = "paraphrase incomplete or corrupted: " + json.dumps(info)

    def validate(c):
        r = validator(
            VALID.format(fact=c["fact"], note=c["note"]), temperature=0.0, max_tokens=5, role="validator"
        )
        words = re.findall(r"TRUE|FALSE|UNDETERMINED", r["text"].upper())
        return words[0] if words else "UNPARSED"

    with ThreadPoolExecutor(6) as ex:
        verdicts = list(ex.map(validate, cases))
    for c, v in zip(cases, verdicts, strict=True):
        c["validator"] = v
        c["validator_agrees"] = v == PLANTED[c["condition"]]
    write_jsonl(CASES, cases)
    digest = hashlib.sha256(CASES.read_bytes()).hexdigest()
    kept = json.loads((HERE / "case_set.json").read_text()) if (HERE / "case_set.json").exists() else {}
    (HERE / "case_set.json").write_text(
        json.dumps(
            {
                **kept,
                "cases": len(cases),
                "sha256": digest,
                "paraphraser": "models/paraphraser.yaml",
                "validator": "models/validator.yaml",
                "executable_defects": sum(c["defective_reason"] is not None for c in cases),
                "validator_disagreements": sum(not c["validator_agrees"] for c in cases),
            },
            indent=2,
        )
        + "\n"
    )
    print(
        f"{len(cases)} cases; sha256 {digest[:12]}; executable defects {sum(c['defective_reason'] is not None for c in cases)}; "
        f"validator disagreements {sum(not c['validator_agrees'] for c in cases)}; live calls: paraphraser {paraphraser.calls}, "
        f"fallback {fallback.calls}, validator {validator.calls}"
    )


if __name__ == "__main__":
    main()
