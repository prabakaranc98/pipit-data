"""Study V1's report: MedCalc-Bench and P1 per model, their rank agreement, the reproduction check and cost.
Usage: python studies/v1_medcalc/analyse.py"""

from __future__ import annotations

import itertools
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "p1_clinical"))
import study as p1  # noqa: E402

from pipit.checks import wilson  # noqa: E402
from pipit.evidence import unit_share  # noqa: E402
from pipit.ledger import Ledger  # noqa: E402

RUNS = HERE / "runs"
CATEGORIES = ["lab test", "physical", "dosage", "date", "risk", "severity", "diagnosis"]
# Calculators whose code Krohn-Grimberghe (2026, arXiv 2603.02222) reports correcting; their answer keys may be
# wrong. Registered in preregistration.md before any accuracy was computed.
AUDITED = {
    "APACHE II Score",
    "CKD-EPI Equations for Glomerular Filtration Rate",
    "CURB-65 Score for Pneumonia Severity",
    "Charlson Comorbidity Index (CCI)",
    "Child-Pugh Score for Cirrhosis Mortality",
    "Fibrosis-4 (FIB-4) Index for Liver Fibrosis",
    "Framingham Risk Score for Hard Coronary Heart Disease",
    "Glasgow Coma Score (GCS)",
    "Glasgow-Blatchford Bleeding Score (GBS)",
    "HEART Score for Major Cardiac Events",
    "HOMA-IR (Homeostatic Model Assessment for Insulin Resistance)",
    "MDRD GFR Equation",
    "MELD Na (UNOS/OPTN)",
    "Morphine Milligram Equivalents (MME) Calculator",
    "QTc Framingham Calculator",
    "Revised Cardiac Risk Index for Pre-Operative Risk",
    "SIRS Criteria",
    "Sequential Organ Failure Assessment (SOFA) Score",
    "Steroid Conversion Calculator",
}
# The paper's Table 2, zero-shot chain of thought, Llama 3 70B, on v1.0's 1,047 items.
PAPER_LLAMA3_70B = {
    "lab test": 33.94,
    "physical": 66.25,
    "date": 25.00,
    "dosage": 20.00,
    "risk": 18.33,
    "severity": 16.25,
    "diagnosis": 36.67,
    "overall": 35.53,
}


def share(k: float, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k / n:.0%} ({lo:.0%}–{hi:.0%})" if n else "–"


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    r = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x: list[float], y: list[float]) -> float:
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def permutation_p(x: list[float], y: list[float], draws: int = 100_000) -> tuple[float, str]:
    """One-sided p-value: the share of orderings of y with a correlation at least as large. Exact over every
    ordering up to eight models; above that, over a seeded sample of orderings."""
    observed = spearman(x, y)
    if len(y) <= 8:
        perms = list(itertools.permutations(y))
        return sum(spearman(x, list(p)) >= observed - 1e-12 for p in perms) / len(perms), "every ordering"
    rng = random.Random("pipit-v1-permutations")
    hits = 0
    for _ in range(draws):
        shuffled = y[:]
        rng.shuffle(shuffled)
        hits += spearman(x, shuffled) >= observed - 1e-12
    return (hits + 1) / (draws + 1), f"{draws:,} random orderings"


def capped(ledger: list[dict], name: str, arm: str, key: str) -> set:
    """Items whose last call for this model stopped at the token cap."""
    last = {}
    for r in ledger:
        if r.get("subject") == name and r.get("arm") == arm and not r.get("cached"):
            last[r.get(key)] = r.get("finish_reason")
    return {k for k, v in last.items() if v == "length"}


def main() -> None:
    cases = p1.adjudicated(p1.load_cases())
    nodes, cell_map = p1.tree()
    hypothesis = {}
    for cid, c in cases.items():
        leaf = cell_map[(c["family"], c["condition"])]
        hypothesis[cid] = nodes[leaf].get("parent", leaf)
    ledger = Ledger(RUNS / "ledger.jsonl").rows()
    names = sorted(p.stem.removeprefix("medcalc_") for p in RUNS.glob("medcalc_*.jsonl"))
    table = {}
    for name in names:
        calc = [json.loads(x) for x in (RUNS / f"medcalc_{name}.jsonl").read_text().splitlines() if x.strip()]
        dec = [json.loads(x) for x in (RUNS / f"p1_{name}.jsonl").read_text().splitlines() if x.strip()]
        by_cat = defaultdict(list)
        for r in calc:
            by_cat[r["category"]].append(r["correct"])
        units: dict = {}
        units_h2: dict = {}
        for r in dec:
            c = cases[r["case_id"]]
            ok = r["choice"] is not None and p1.severity(c, {"choice": r["choice"]}) == "ok"
            for d in [units] + ([units_h2] if hypothesis[r["case_id"]] == "H2" else []):
                u = d.setdefault(p1.unit(c), [0, 0])
                u[0] += ok
                u[1] += 1
        usd = sum(r.get("usd") or 0.0 for r in ledger if r.get("subject") == name and not r.get("cached"))
        cut = capped(ledger, name, "medcalc", "row") & {r["row"] for r in calc}
        cut_p1 = capped(ledger, name, "p1", "case_id") & {r["case_id"] for r in dec}
        clean = [r for r in calc if r["row"] not in cut and r.get("error") is None]
        table[name] = {
            "medcalc": (sum(r["correct"] for r in calc), len(calc)),
            "by_cat": {k: (sum(v), len(v)) for k, v in by_cat.items()},
            "p1": (unit_share(units), len(units)),
            "p1_h2": (unit_share(units_h2), len(units_h2)),
            "unparsed": sum(r["choice"] is None for r in dec),
            "usd": usd,
            "cut": (len(cut), len(cut_p1)),
            "failed": (
                sum(r.get("error") is not None for r in calc),
                sum(r.get("error") is not None for r in dec),
            ),
            "medcalc_clean": (sum(r["correct"] for r in clean), len(clean)),
            "medcalc_unaudited": (
                sum(r["correct"] for r in calc if r["calculator"] not in AUDITED),
                sum(r["calculator"] not in AUDITED for r in calc),
            ),
            "medcalc_audited": (
                sum(r["correct"] for r in calc if r["calculator"] in AUDITED),
                sum(r["calculator"] in AUDITED for r in calc),
            ),
        }
    L = ["# Study V1: do Pipit's written cases rank models the way MedCalc-Bench's real notes do?\n"]
    L.append(
        "Setup in `preregistration.md`. MedCalc-Bench: 220 items, four per calculator. P1: 112 cases, counted once per independent case. Intervals are 95% Wilson.\n"
    )
    L.append("| model | MedCalc-Bench right | P1 right, per case | P1 computing right | P1 unparsed | USD |")
    L.append("|---|---|---|---|---|---|")
    for name in names:
        t = table[name]
        L.append(
            f"| {name} | {share(*t['medcalc'])} | {share(*t['p1'])} | {share(*t['p1_h2'])} | {t['unparsed']} | {t['usd']:.2f} |"
        )
    L.append("\n## Replies cut off at the cap, and failed calls\n")
    L.append(
        "Both count as wrong above. The cap counts any reasoning the provider runs by default: 4,096 tokens on "
        "MedCalc-Bench, 2,048 on P1. A failed call failed four times.\n"
    )
    L.append(
        "| model | MedCalc-Bench cut off | failed | MedCalc-Bench right without them | P1 cut off | failed |"
    )
    L.append("|---|---|---|---|---|---|")
    for name in names:
        t = table[name]
        L.append(
            f"| {name} | {t['cut'][0]} | {t['failed'][0]} | {share(*t['medcalc_clean'])} | {t['cut'][1]} | "
            f"{t['failed'][1]} |"
        )
    L.append("\n## Calculators whose code an audit corrected\n")
    L.append(
        "Krohn-Grimberghe (2026) reports fixing errors in the code of 19 of MedCalc-Bench's 55 calculators, without "
        "saying how many test answers each changes. Their items are shown apart here; the registered score above "
        "keeps them.\n"
    )
    L.append("| model | all items | without the 19 audited calculators | the 19 audited calculators only |")
    L.append("|---|---|---|---|")
    for name in names:
        t = table[name]
        L.append(
            f"| {name} | {share(*t['medcalc'])} | {share(*t['medcalc_unaudited'])} | {share(*t['medcalc_audited'])} |"
        )
    L.append("\n## Providers that served each model\n")
    L.append(
        "OpenRouter routed each call to a provider of its choosing; no model was pinned. A model's score mixes "
        "every provider that served it.\n"
    )
    L.append("| model | providers | the one that served the most calls |")
    L.append("|---|---|---|")
    for name in names:
        served = Counter(
            r.get("provider") for r in ledger if r.get("subject") == name and not r.get("cached")
        )
        top, n = served.most_common(1)[0]
        L.append(f"| {name} | {len(served)} | {top}, {n} of {sum(served.values())} calls |")
    L.append("\n## MedCalc-Bench by category\n")
    L.append("| model | " + " | ".join(CATEGORIES) + " |")
    L.append("|---|" + "---|" * len(CATEGORIES))
    for name in names:
        L.append(
            f"| {name} | "
            + " | ".join(share(*table[name]["by_cat"].get(c, (0, 0))) for c in CATEGORIES)
            + " |"
        )
    if "llama31_70b" in table:
        t = table["llama31_70b"]
        L.append("\n## Reproduction check\n")
        L.append(
            "Llama 3.1 70B here against the paper's Llama 3 70B, zero-shot chain of thought on v1.0. The model and the data version both differ.\n"
        )
        L.append("| | " + " | ".join(CATEGORIES) + " | overall |")
        L.append("|---|" + "---|" * (len(CATEGORIES) + 1))
        here = [
            f"{t['by_cat'][c][0] / t['by_cat'][c][1]:.0%}" if c in t["by_cat"] else "–" for c in CATEGORIES
        ]
        L.append("| this study | " + " | ".join(here) + f" | {t['medcalc'][0] / t['medcalc'][1]:.0%} |")
        L.append(
            "| the paper | "
            + " | ".join(f"{PAPER_LLAMA3_70B[c]:.0f}%" for c in CATEGORIES)
            + f" | {PAPER_LLAMA3_70B['overall']:.0f}% |"
        )
    if len(names) >= 3:
        mc = [table[n]["medcalc"][0] / table[n]["medcalc"][1] for n in names]
        pp = [table[n]["p1"][0] / table[n]["p1"][1] for n in names]
        lab = [
            sum(table[n]["by_cat"].get(c, (0, 0))[0] for c in ("lab test", "dosage"))
            / max(1, sum(table[n]["by_cat"].get(c, (0, 0))[1] for c in ("lab test", "dosage")))
            for n in names
        ]
        h2 = [table[n]["p1_h2"][0] / table[n]["p1_h2"][1] for n in names]
        kept = [table[n]["medcalc_unaudited"][0] / max(1, table[n]["medcalc_unaudited"][1]) for n in names]
        L.append("\n## Do the two rank the models alike?\n")
        (p_all, how), (p_h2, _) = permutation_p(mc, pp), permutation_p(lab, h2)
        p_kept, _ = permutation_p(kept, pp)
        L.append(
            f"Spearman's correlation across {len(names)} models, with a one-sided permutation test over {how}:\n"
        )
        L.append(f"- MedCalc-Bench overall against P1 overall: {spearman(mc, pp):.2f}, p = {p_all:.3f}.")
        L.append(
            f"- MedCalc-Bench lab and dosage against P1's computing hypothesis: {spearman(lab, h2):.2f}, "
            f"p = {p_h2:.3f}."
        )
        L.append(
            f"- MedCalc-Bench without the 19 audited calculators against P1 overall: {spearman(kept, pp):.2f}, "
            f"p = {p_kept:.3f}.\n"
        )
    # The reading that closes the report, written by hand after the analysis ran.
    tail = HERE / "report_tail.md"
    if tail.exists():
        L.extend(["", tail.read_text().rstrip("\n")])
    text = "\n".join(L) + "\n"
    (HERE / "report.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
