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

from pipit.checks import wilson  # noqa: E402
from pipit.costs import PriceList, per_case, per_group, summarize  # noqa: E402
from pipit.evidence import cases_to_evidence, cells, rollup  # noqa: E402
from pipit.ledger import Ledger  # noqa: E402


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
                common = set(a) & set(b) & adjud
                same = sum(a[k]["choice"] == b[k]["choice"] for k in common)
                L.append(f"{names[i]} and {names[j]} chose the same option on {same}/{len(common)} cases.\n")

    L.append(
        "\n## Ledger\n| role | requests | replayed | tokens in | tokens out | USD | unpriced rows | seconds |\n|---|---|---|---|---|---|---|---|"
    )
    for role, t in summarize(Ledger(LEDGER).rows(), prices).items():
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
    (HERE / "report.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
