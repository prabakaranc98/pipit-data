"""The cost ledger: one row per call, per role. Every claim's budget is read from here, never estimated."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


class Ledger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def record(self, role: str, **row: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps({"t": round(time.time(), 3), "role": role, **row}, ensure_ascii=False) + "\n")

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def summary(self) -> dict[str, dict[str, Any]]:
        """Per role: requests, tokens in and out, dollars (and whether every row priced itself), seconds."""
        agg: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "usd": 0.0,
                "usd_complete": True,
                "seconds": 0.0,
            }
        )
        for r in self.rows():
            a = agg[r["role"]]
            a["requests"] += r.get("requests", 1)
            a["tokens_in"] += r.get("tokens_in") or 0
            a["tokens_out"] += r.get("tokens_out") or 0
            a["seconds"] += r.get("seconds") or 0.0
            if r.get("usd") is None:
                a["usd_complete"] = False
            else:
                a["usd"] += r["usd"]
        return dict(agg)
