import pytest

from pipit.ledger import Ledger
from pipit.manifest import Context, load_manifest, resolve

GOOD = """
name: toy
id: example/toy-model
revision: abc123
adapter: toy_adapter:load
placement: local
device: cpu
dtype: fp32
settings: {one_question_per_request: true}
"""


def test_load_manifest(tmp_path) -> None:
    p = tmp_path / "toy.yaml"
    p.write_text(GOOD)
    m = load_manifest(p)
    assert m.name == "toy" and m.placement == "local" and m.settings == {"one_question_per_request": True}
    assert m.card()["revision"] == "abc123" and m.source == str(p)


@pytest.mark.parametrize(
    "bad, message",
    [
        (GOOD.replace("revision: abc123\n", ""), "lacks 'revision'"),
        (GOOD.replace("placement: local", "placement: cloud"), "placement must be one of"),
        (GOOD.replace("adapter: toy_adapter:load", "adapter: toy_adapter"), "module:function"),
        (GOOD + "api_key: sk-secret\n", "never carry keys"),
        (GOOD + "colour: blue\n", "unknown manifest fields"),
    ],
)
def test_manifest_rejects(tmp_path, bad, message) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(bad)
    with pytest.raises(ValueError, match=message):
        load_manifest(p)


def test_resolve_imports_the_adapter_at_the_edge(tmp_path, monkeypatch) -> None:
    (tmp_path / "toy_adapter.py").write_text(
        "class Toy:\n"
        "    def __init__(self, manifest, context):\n"
        "        self.manifest = manifest\n"
        "    def __call__(self, state, questions):\n"
        "        return {k: {'type': 'noul', 'noul': 0.5} for k in questions}\n"
        "def load(manifest, context):\n"
        "    return Toy(manifest, context)\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    p = tmp_path / "toy.yaml"
    p.write_text(GOOD)
    subject = resolve(load_manifest(p), Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path))
    assert subject({"x": 1}, {"q": {"type": "noul", "instructions": "?"}}) == {
        "q": {"type": "noul", "noul": 0.5}
    }
