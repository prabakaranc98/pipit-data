"""Keys live in the environment, never in the repository or a manifest."""

from __future__ import annotations

import os
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> int:
    """Set variables from a KEY=value file into the environment without overriding what is already set.

    Returns the number of variables set. A missing file sets nothing.
    """
    p = Path(path)
    if not p.exists():
        return 0
    n = 0
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value
            n += 1
    return n


def require_key(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set in the environment (or .env)")
    return value
