"""Results written as each item finishes. A run that stops, for whatever reason, loses nothing, and a rerun
can pick up only the items that are not done.

    >>> import tempfile, pathlib
    >>> path = pathlib.Path(tempfile.mkdtemp()) / "answers.jsonl"
    >>> results = Results(path, key="case_id")
    >>> results.add({"case_id": "a", "choice": "proceed"})
    >>> Results(path, key="case_id").get("a")["choice"]
    'proceed'
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

__all__ = ["Results"]


class Results:
    """One JSON-lines file of result rows, one per item, keyed by `key`. Rows are appended as they arrive and
    a later row for the same item replaces an earlier one, so the file can be read at any moment.

    Opening it repairs a last line that a stop left without its newline: a whole row is kept and given its
    newline, a half-written one is dropped. Only then is the file rewritten, so open it while no other run is
    writing to it."""

    def __init__(self, path: str | Path, key: str):
        self.path = Path(path)
        self.key = key
        self._lock = threading.Lock()
        self._rows: dict[Any, dict[str, Any]] = {}
        if self.path.exists():
            text = self.path.read_text()
            lines = [x for x in text.splitlines() if x.strip()]
            repair = bool(text) and not text.endswith("\n")  # a run stopped before the last row's newline
            for i, line in enumerate(lines):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    if i < len(lines) - 1:
                        raise
                    repair = True  # a run stopped mid-row; drop the partial row
                    break
                self._rows[row[key]] = row
            if repair:
                self._write(list(self._rows.values()))

    def get(self, item: Any) -> dict[str, Any] | None:
        """The latest row recorded for an item, or None."""
        return self._rows.get(item)

    def add(self, row: dict[str, Any]) -> None:
        """Record a row now, from any thread."""
        with self._lock:
            self._rows[row[self.key]] = row
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                f.write(json.dumps(row) + "\n")

    def compact(self, order: Iterable[Any]) -> list[dict[str, Any]]:
        """Rewrite the file with one row per item, in `order`, and return those rows."""
        with self._lock:
            rows = [self._rows[k] for k in order if k in self._rows]
            self._write(rows)
            return rows

    def _write(self, rows: list[dict[str, Any]]) -> None:
        """Replace the file in one step, so a stop mid-write never leaves it half rewritten."""
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text("".join(json.dumps(r) + "\n" for r in rows))
        os.replace(tmp, self.path)
