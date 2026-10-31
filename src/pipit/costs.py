"""Cost analysis over the ledger. The ledger records every request, live or replayed from the cache, with the
role, the model asked and answered, tokens, dollars when the response priced itself, seconds, and the case it
served. This module prices the rows that could not price themselves, summarises by role and by model, and
attributes cost and time to cases so a hypothesis node can report what its evidence cost."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

Row = dict[str, Any]


@dataclass(frozen=True)
class Price:
    usd_per_million_in: float
    usd_per_million_out: float

    def of(self, tokens_in: int | None, tokens_out: int | None) -> float:
        return (tokens_in or 0) * self.usd_per_million_in / 1e6 + (
            tokens_out or 0
        ) * self.usd_per_million_out / 1e6


@dataclass
class PriceList:
    """Prices per model identifier, for subjects whose responses carry tokens but no cost. Dated, because
    prices move; `source` says where the numbers came from."""

    prices: dict[str, Price] = field(default_factory=dict)
    as_of: str | None = None
    source: str | None = None

    @classmethod
    def load(cls, path: str | Path) -> PriceList:
        data = yaml.safe_load(Path(path).read_text()) or {}
        prices = {
            model: Price(float(p["usd_per_million_in"]), float(p["usd_per_million_out"]))
            for model, p in (data.get("models") or {}).items()
            if p and p.get("usd_per_million_in") is not None
        }
        as_of = data.get("as_of")
        return cls(prices, None if as_of is None else str(as_of), data.get("source"))

    def price_row(self, row: Row) -> tuple[float | None, str]:
        """(usd, how): 'response' when the row priced itself, 'price_list' when estimated here, 'unpriced'
        when neither; a replayed row costs nothing."""
        if row.get("cached"):
            return 0.0, "replayed"
        if row.get("usd") is not None:
            return float(row["usd"]), "response"
        for key in ("model_answered", "model_asked"):
            p = self.prices.get(row.get(key) or "")
            if p:
                return p.of(row.get("tokens_in"), row.get("tokens_out")), "price_list"
        return None, "unpriced"


def summarize(
    rows: list[Row], prices: PriceList | None = None, by: str = "role"
) -> dict[str, dict[str, Any]]:
    """Totals per `by` (role or model_asked): requests, replayed, tokens, usd, how many rows stayed unpriced,
    seconds. Replayed rows count as requests but add no tokens or dollars."""
    prices = prices or PriceList()
    out: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "requests": 0,
            "replayed": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "usd": 0.0,
            "unpriced": 0,
            "seconds": 0.0,
        }
    )
    for r in rows:
        a = out[str(r.get(by))]
        a["requests"] += r.get("requests", 1)
        a["seconds"] += r.get("seconds") or 0.0
        if r.get("cached"):
            a["replayed"] += 1
            continue
        a["tokens_in"] += r.get("tokens_in") or 0
        a["tokens_out"] += r.get("tokens_out") or 0
        usd, how = prices.price_row(r)
        if how == "unpriced":
            a["unpriced"] += 1
        else:
            a["usd"] += usd or 0.0
    return dict(out)


def per_case(rows: list[Row], prices: PriceList | None = None) -> dict[str, dict[str, Any]]:
    """Cost and time attributed to each case id, across roles. Rows without a case id are left out."""
    prices = prices or PriceList()
    out: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"usd": 0.0, "seconds": 0.0, "requests": 0, "unpriced": 0}
    )
    for r in rows:
        cid = r.get("case_id")
        if not cid:
            continue
        a = out[cid]
        a["requests"] += r.get("requests", 1)
        a["seconds"] += r.get("seconds") or 0.0
        usd, how = prices.price_row(r)
        if how == "unpriced":
            a["unpriced"] += 1
        else:
            a["usd"] += usd or 0.0
    return dict(out)


def per_group(case_costs: dict[str, dict[str, Any]], group_of: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Roll per-case cost up to groups (cells, hypotheses) given a map case id -> group id."""
    out: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"usd": 0.0, "seconds": 0.0, "requests": 0, "cases": 0, "unpriced": 0}
    )
    for cid, c in case_costs.items():
        g = group_of.get(cid)
        if g is None:
            continue
        a = out[g]
        a["cases"] += 1
        for k in ("usd", "seconds", "requests", "unpriced"):
            a[k] += c[k]
    return dict(out)


def cost_to_finding(
    case_costs: dict[str, dict[str, Any]], case_ids_until_finding: list[str]
) -> dict[str, float]:
    """What the cases run until a finding cost, in dollars and seconds: the figure a claim reports against its
    baseline at equal budget."""
    usd = sum(case_costs.get(c, {}).get("usd", 0.0) for c in case_ids_until_finding)
    sec = sum(case_costs.get(c, {}).get("seconds", 0.0) for c in case_ids_until_finding)
    return {"cases": len(case_ids_until_finding), "usd": round(usd, 6), "seconds": round(sec, 3)}
