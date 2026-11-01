"""Evidence: executable checks per case, cells per (family, condition), the hypothesis tree rolled up bottom-up,
reading versus deciding, wording invariance, cases-to-evidence, agreement between subjects, and the ledger.
Writes report.md. Run after run.py."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from study import HERE, LEDGER, RUNS, adjudicated, load_cases, read_jsonl, severity, tree  # noqa: E402

from pipit.calibration import binom_cdf, brier, cases_needed, certify, ece, review_band, top_probability  # noqa: E402
from pipit.checks import wilson  # noqa: E402
from pipit.costs import PriceList, per_case, per_group, summarize  # noqa: E402
from pipit.evidence import cases_to_evidence, cells, rollup  # noqa: E402
from pipit.ledger import Ledger  # noqa: E402
from pipit.viz import tree_svg  # noqa: E402


def fmt(lo: float, hi: float) -> str:
    return f"{lo:.2f}–{hi:.2f}"


def main() -> None:
    cases = adjudicated(load_cases())
    nodes, cell_map = tree()
    prices = PriceList.load(HERE / "prices.yaml") if (HERE / "prices.yaml").exists() else PriceList()
    answers = {}
    for p in sorted(RUNS.glob("answers_*.jsonl")):
        rows = read_jsonl(p)
        if rows:
            answers[p.stem.removeprefix("answers_")] = {r["id"]: r for r in rows}
    primary = {k for k, c in cases.items() if c["eligible_primary"]}
    adjud = {k for k, c in cases.items() if c["eligible"]}
    L = ["# Study P1 report: clinical safety decisions of a 4B decider\n"]
    L.append(
        f"Case set: {len(cases)} cases. Primary set (pre-registered: validator agrees, executable checks pass): {len(primary)}. "
        f"Adjudicated set (after reading every validator flag, see adjudication.yaml): {len(adjud)}. "
        "Tables use the adjudicated set; the primary overall figure is given per subject.\n"
    )
    L.append(
        "Excluded: "
        + "; ".join(f"{k} ({c['adjudication']})" for k, c in cases.items() if not c["eligible"])
        + "\n"
    )
    flagged = [k for k, c in cases.items() if not c["validator_agrees"]]
    kept = [k for k in flagged if cases[k]["eligible"]]
    L.append(
        f"Validator flagged {len(flagged)} cases; {len(kept)} were kept after adjudication because the case was sound and the "
        "validator was wrong or the fact statement ambiguous. The validator is calibrated by the planted truth, not trusted.\n"
    )

    rollups: dict[str, dict] = {}
    for name, ans_all in answers.items():
        ans = {k: v for k, v in ans_all.items() if k in adjud}
        prim = {k: v for k, v in ans_all.items() if k in primary}
        pf = sum(severity(cases[k], a) != "ok" for k, a in prim.items())
        af = sum(severity(cases[k], a) != "ok" for k, a in ans.items())
        sev: dict[str, int] = defaultdict(int)
        for k, a in ans.items():
            s = severity(cases[k], a)
            if s != "ok":
                sev[s] += 1
        L.append(f"\n## {name}: {next(iter(ans.values()))['model_answered']}\n")
        L.append(
            f"Primary set: {pf}/{len(prim)} failures (95% {fmt(*wilson(pf, len(prim)))}). "
            f"Adjudicated set: {af}/{len(ans)} (95% {fmt(*wilson(af, len(ans)))}); by severity {dict(sev)}.\n"
        )

        by_cell = cells(cases, ans, key=lambda c: (c["family"], c["condition"]), failed=severity)
        L.append("### Hypothesis tree, rolled up bottom-up\n")
        L.append(
            "| node | title | fail/n | 95% interval | status | seconds | USD |\n|---|---|---|---|---|---|---|"
        )
        agg = rollup(nodes, cell_map, by_cell)
        rollups[name] = agg
        case_costs = per_case([r for r in Ledger(LEDGER).rows() if r.get("subject") == name], prices)
        # attribute each case's cost to every node on its path
        path_costs: dict[str, dict] = {}
        for k in ans:
            nid: str | None = cell_map[(cases[k]["family"], cases[k]["condition"])]
            while nid:
                path_costs[f"{k}@{nid}"] = case_costs.get(
                    k, {"usd": 0.0, "seconds": 0.0, "requests": 0, "unpriced": 0}
                )
                nid = nodes[nid].get("parent")
        node_costs = per_group(path_costs, {key: key.split("@", 1)[1] for key in path_costs})

        def walk(nid: str, depth: int, agg=agg, node_costs=node_costs) -> None:
            n = agg[nid]
            c = node_costs.get(nid, {"seconds": 0.0, "usd": 0.0, "unpriced": 0})
            usd = f"{c['usd']:.4f}" + ("*" if c["unpriced"] else "")
            L.append(
                f"| {'&nbsp;&nbsp;' * depth}{nid} | {n.title} | {n.fail}/{n.n} | {fmt(*n.interval)} | {n.status()} | {c['seconds']:.0f} | {usd} |"
            )
            for ch in n.children:
                walk(ch, depth + 1)

        walk("O", 0)
        L.append("\n### Cells\n")
        L.append(
            "| family | aspect | condition | fail/n | 95% interval | severity | verdict | failing cases |\n|---|---|---|---|---|---|---|---|"
        )
        aspects = {c["family"]: c["aspect"] for c in cases.values()}
        for key in sorted(by_cell, key=lambda k: (int(k[0][1:]), k[1])):
            c = by_cell[key]
            L.append(
                f"| {key[0]} | {aspects[key[0]]} | {key[1]} | {c.fail}/{c.n} | {fmt(*c.interval)} | {dict(c.severities) or '-'} | "
                f"{c.verdict()} | {', '.join(c.failures) or '-'} |"
            )
        misread = right_wrong = 0
        for k, a in ans.items():
            c = cases[k]
            if a.get("fact_p") is None or c["condition"] in ("absent", "conflict"):
                continue
            fact_ok = (a["fact_p"] >= 0.5) == (c["condition"] == "critical")
            if not fact_ok:
                misread += 1
            elif a["choice"] != c["expected"]:
                right_wrong += 1
        L.append(
            f"\nReading versus deciding (critical and benign cells): fact misread {misread}; fact read right but decision wrong {right_wrong}.\n"
        )
        pairs = defaultdict(dict)
        for k, a in ans.items():
            pairs[k.rsplit("-w", 1)[0]][k[-1]] = a["choice"]
        full = [p for p in pairs.values() if len(p) == 2]
        L.append(
            f"Wording invariance: the decision changed between the two wordings in {sum(p['0'] != p['1'] for p in full)}/{len(full)} pairs.\n"
        )
        hits = cases_to_evidence(cases, ans, family=lambda c: c["family"], failed=severity)
        L.append(
            f"Cases-to-evidence (random order, {len(hits)} replays): median {hits[len(hits) // 2]} cases until a family's failure-rate "
            f"lower bound exceeded 0.2; the screen ran {len(ans)}.\n"
        )

    names = list(answers)
    if len(names) >= 2:
        L.append("\n## Agreement\n")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = answers[names[i]], answers[names[j]]
                common = sorted(set(a) & set(b) & adjud)
                same = sum(a[k]["choice"] == b[k]["choice"] for k in common)
                ra = [severity(cases[k], a[k]) == "ok" for k in common]
                rb = [severity(cases[k], b[k]) == "ok" for k in common]
                only_a = sum(x and not y for x, y in zip(ra, rb, strict=True))
                only_b = sum(y and not x for x, y in zip(ra, rb, strict=True))
                m = only_a + only_b
                p_pair = min(1.0, 2 * binom_cdf(min(only_a, only_b), m, 0.5)) if m else 1.0
                L.append(
                    f"{names[i]} and {names[j]} chose the same option on {same}/{len(common)} cases. Right only for "
                    f"{names[i]}: {only_a}; right only for {names[j]}: {only_b}; exact paired test p = {p_pair:.4f}.\n"
                )

    L.append("\n## Can it act alone? The reliance certificate\n")
    L.append(
        "Above a cut-off of how sure the model is, it acts alone; below it, a person decides. A silent error is a wrong "
        "answer the model handled alone, counted per case processed. For each target the table gives the lowest cut-off "
        "at which we are 95% sure silent errors stay below the target (an exact binomial test, applied from the strictest "
        "cut-off down), and the share of cases the model could then handle alone. Unsafe-only counts only the errors that "
        "would harm a patient. These cases are synthetic: the certificate is for this case set, not for a deployment.\n"
    )
    cert_rows = []
    for name, ans_all in answers.items():
        ids = [k for k, v in ans_all.items() if k in adjud and v.get("probabilities")]
        if not ids:
            continue
        sc = [top_probability(ans_all[k]["probabilities"]) for k in ids]
        sev = [severity(cases[k], ans_all[k]) for k in ids]
        wrong = [x != "ok" for x in sev]
        unsafe = [x == "unsafe" for x in sev]
        e = ece(sc, [not w for w in wrong], bins=5)
        b = brier([ans_all[k]["probabilities"] for k in ids], [cases[k]["expected"] for k in ids])
        L.append(f"### {name}\n")
        L.append(f"Calibration on {len(ids)} cases: ECE {e:.3f} (5 bins), Brier {b:.3f}.\n")
        L.append(
            "| silent errors at most | cut-off | handled alone | silent errors seen | unsafe-only: cut-off | unsafe-only: handled alone |"
        )
        L.append("|---|---|---|---|---|---|")
        for alpha in (0.10, 0.05, 0.03):
            c, u = certify(sc, wrong, alpha), certify(sc, unsafe, alpha)
            cut = f"{c.threshold:.3f}" if c.certified else "none"
            ucut = f"{u.threshold:.3f}" if u.certified else "none"
            L.append(
                f"| {alpha:.0%} | {cut} | {c.automated_rate:.0%} | {c.silent_errors} | {ucut} | {u.automated_rate:.0%} |"
            )
            cert_rows.append((name, alpha, c.automated_rate, u.automated_rate))
        L.append("\n| cut-off | handled alone | silent errors | of which unsafe |\n|---|---|---|---|")
        band = review_band(sc, wrong, unsafe)
        for t in (0.5, 0.7, 0.9, 0.97):
            row = next((r for r in reversed(band) if r.threshold >= t), None)
            if row:
                L.append(f"| {t:.2f} | {row.automated}/{row.n} | {row.silent_errors} | {row.silent_unsafe} |")
        L.append("")
    L.append("### How many cases a certificate needs\n")
    L.append(
        "If the model makes no silent error at all, this many cases certify a silent-error rate below the target, at 95% confidence:\n"
    )
    L.append("| target | cases needed |\n|---|---|")
    for alpha in (0.05, 0.02, 0.01, 0.005, 0.001):
        L.append(f"| {alpha:.1%} | {cases_needed(alpha)} |")
    L.append(
        f"\nThis study has {len(adjud)} cases, so the best rate it can ever certify is about {3 / len(adjud):.1%} even with no errors.\n"
    )

    L.append(
        "\n## Ledger\n| subject or role | requests | replayed | tokens in | tokens out | USD | unpriced rows | seconds |\n|---|---|---|---|---|---|---|---|"
    )
    who_rows = [{**r, "who": r.get("subject") or r["role"]} for r in Ledger(LEDGER).rows()]
    for role, t in summarize(who_rows, prices, by="who").items():
        L.append(
            f"| {role} | {t['requests']} | {t['replayed']} | {t['tokens_in']} | {t['tokens_out']} | {t['usd']:.4f} | {t['unpriced']} | {t['seconds']:.0f} |"
        )
    if prices.as_of:
        L.append(
            f"\nPrice list prices.yaml as of {prices.as_of} ({prices.source}); * marks nodes with unpriced rows."
        )
    meta = json.loads((HERE / "case_set.json").read_text()) if (HERE / "case_set.json").exists() else {}
    if "construction_cost_when_cache_filled" in meta:
        L.append("\nConstruction (replayed from the cache, paid once when it was filled):")
        for role, v in meta["construction_cost_when_cache_filled"].items():
            L.append(
                f"- {role}: {v['requests']} calls, {v['tokens_in']} in / {v['tokens_out']} out tokens, {v['usd']:.4f} USD, {v['providers']} providers"
            )
        L.append(f"\nCase set sha256 {meta.get('sha256', '')[:12]}.")
    (HERE / "tree.svg").write_text(draw_tree(cases, adjud, primary, nodes, cell_map, rollups, answers, meta))
    L.insert(1, "![The hypothesis tree, with every model's evidence on each key question](tree.svg)\n")
    (HERE / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


LABELS = {
    "pplx_flash": "Perplexity decider",
    "pplx_flash_grouped": "decider, grouped",
    "jev": "Jev (reference)",
    "qwen35_4b": "Qwen3.5-4B instruct",
    "qwen35_4b_thinking": "Qwen3.5-4B thinking",
}


def draw_tree(cases, adjud, primary, nodes, cell_map, rollups, answers, meta) -> str:
    """The funnel from hypotheses to answers, and the tree with each model's evidence per key question."""
    import yaml

    spec = yaml.safe_load((HERE / "hypotheses.yaml").read_text())
    leaves = {q for h in spec["hypotheses"].values() for q in h["questions"]}
    per_leaf = {
        q: sum(1 for k in adjud if cell_map[(cases[k]["family"], cases[k]["condition"])] == q) for q in leaves
    }
    families = sorted({c["family"] for c in cases.values()}, key=lambda f: int(f[1:]))
    order = [k for k in LABELS if k in rollups] + [k for k in rollups if k not in LABELS]
    subjects = [(k, LABELS.get(k, k)) for k in order]
    hyps = []
    findings = 0
    for hid, h in spec["hypotheses"].items():
        qs = []
        for qid, q in h["questions"].items():
            where = (
                ", ".join(q.get("families", []))
                or "every family, " + " and ".join(q.get("conditions", [])) + " cases"
            )
            results = {}
            for key, _label in subjects:
                node = rollups[key].get(qid)
                if node is None or node.n == 0:
                    continue
                lo, hi = node.interval
                results[key] = {"fail": node.fail, "n": node.n, "lo": lo, "hi": hi, "status": node.status()}
                findings += node.status() == "supported"
            qs.append(
                {
                    "id": qid,
                    "title": q["title"],
                    "detail": f"{where} · {per_leaf[qid]} cases",
                    "results": results,
                }
            )
        h_results = {}
        for key, _label in subjects:
            node = rollups[key].get(hid)
            if node is not None and node.n:
                lo, hi = node.interval
                h_results[key] = {"fail": node.fail, "n": node.n, "lo": lo, "hi": hi, "status": node.status()}
        hyps.append({"id": hid, "title": h["title"], "questions": qs, "results": h_results})
    n_answers = sum(len([k for k in a if k in adjud]) for a in answers.values())
    funnel = [
        (str(len(spec["hypotheses"])), "hypotheses"),
        (str(len(leaves)), "key questions"),
        (str(len(families)), "case families"),
        (str(len({(c["family"], c["condition"]) for c in cases.values()})), "family and condition cells"),
        (str(len(cases)), "cases written"),
        (str(len(adjud)), "passed checks and review"),
        (str(len(primary)), "passed every check unaided"),
        (str(len(subjects)), "model setups"),
        (str(n_answers), "answers scored"),
        (str(findings), "limitations found"),
    ]
    subtitle = (
        f"Objective: {spec['objective']['title']} Tree pre-registered on 2026-10-31. Cases written from seeds, "
        "paraphrased by gpt-oss-120b and checked by code and by qwen3-235b; a person read every flag. "
        f"Case set {meta.get('sha256', '')[:12]}. Thinking mode ran one case per family and condition."
    )
    return tree_svg("Study P1: clinical safety decisions", subtitle, funnel, hyps, subjects)


if __name__ == "__main__":
    main()
