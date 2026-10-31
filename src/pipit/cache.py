"""A request cache keyed by the hash of the request. Reruns and warm-ups cost nothing, and the outputs behind
a result are kept. Append-only JSONL, one file per subject."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def request_key(request: Any) -> str:
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


class JsonlCache:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._rows: dict[str, Any] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self._rows[row["key"]] = row["response"]

    def __len__(self) -> int:
        return len(self._rows)

    def __contains__(self, key: str) -> bool:
        return key in self._rows

    def get(self, key: str) -> Any | None:
        return self._rows.get(key)

    def put(self, key: str, response: Any) -> None:
        self._rows[key] = response
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps({"key": key, "response": response}, ensure_ascii=False) + "\n")

    def drop(self, key: str) -> None:
        """Forget an entry in memory; the file keeps its history and the next put appends a fresh row."""
        self._rows.pop(key, None)
