"""Manifests: how a model is registered. A YAML file declares identifier, revision, configuration and the
adapter
that turns it into a subject. The role (candidate or lab model) is assigned by the study, never here.

Pipit's core imports no model library. Adapters are the only place a model's SDK appears; they are named in
the
manifest as `module:function` and loaded on demand.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

from pipit.ledger import Ledger

PLACEMENTS = ("api", "local", "vm")


@dataclass(frozen=True)
class Manifest:
    name: str
    id: str
    revision: str
    adapter: str
    placement: str
    device: str | None = None
    dtype: str | None = None
    key_env: str | None = None
    price_usd_per_million_in: float | None = None
    price_usd_per_million_out: float | None = None
    settings: dict[str, Any] = field(default_factory=dict)
    source: str | None = None

    def card(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "revision": self.revision,
            "adapter": self.adapter,
            "placement": self.placement,
            "device": self.device,
            "dtype": self.dtype,
            "settings": dict(self.settings),
        }


class Subject(Protocol):
    manifest: Manifest

    def __call__(self, state: Any, questions: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]: ...


@dataclass
class Context:
    """What an adapter needs besides its manifest: where to cache, where to write cost rows, how many paid
    calls at most."""

    ledger: Ledger
    cache_dir: Path
    max_calls: int | None = None


def load_manifest(path: str | Path) -> Manifest:
    p = Path(path)
    data = yaml.safe_load(p.read_text()) or {}
    for required in ("name", "id", "revision", "adapter", "placement"):
        if required not in data:
            raise ValueError(f"{p}: manifest lacks '{required}'")
    if data["placement"] not in PLACEMENTS:
        raise ValueError(f"{p}: placement must be one of {PLACEMENTS}, not {data['placement']!r}")
    if ":" not in data["adapter"]:
        raise ValueError(f"{p}: adapter must be 'module:function'")
    for forbidden in ("key", "api_key", "token"):
        if forbidden in data:
            raise ValueError(f"{p}: manifests never carry keys; name the environment variable in 'key_env'")
    known = {f for f in Manifest.__dataclass_fields__ if f != "source"}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"{p}: unknown manifest fields {sorted(unknown)}")
    return Manifest(source=str(p), **data)


def resolve(manifest: Manifest, context: Context) -> Subject:
    """Import the adapter named in the manifest and let it build the subject."""
    module_name, _, function_name = manifest.adapter.partition(":")
    module = importlib.import_module(module_name)
    load = getattr(module, function_name)
    return load(manifest, context)
