from pipit.cache import JsonlCache, request_key
from pipit.ledger import Ledger


def test_request_key_is_order_independent() -> None:
    assert request_key({"a": 1, "b": [1, 2]}) == request_key({"b": [1, 2], "a": 1})
    assert request_key({"a": 1}) != request_key({"a": 2})


def test_cache_persists_and_drops(tmp_path) -> None:
    c = JsonlCache(tmp_path / "c.jsonl")
    assert c.get("k") is None
    c.put("k", {"v": 1})
    assert "k" in c and c.get("k") == {"v": 1}
    again = JsonlCache(tmp_path / "c.jsonl")
    assert again.get("k") == {"v": 1} and len(again) == 1
    again.drop("k")
    assert again.get("k") is None


def test_ledger_summary_marks_unknown_prices(tmp_path) -> None:
    led = Ledger(tmp_path / "l.jsonl")
    led.record("lab", tokens_in=10, tokens_out=5, usd=0.001, seconds=1.0)
    led.record("lab", tokens_in=20, tokens_out=5, usd=0.002, seconds=0.5)
    led.record("reference", tokens_in=300, tokens_out=60, usd=None, seconds=0.4)
    led.record("candidate", requests=2, usd=0.0, seconds=2.0)
    s = led.summary()
    assert s["lab"]["requests"] == 2 and s["lab"]["tokens_in"] == 30 and abs(s["lab"]["usd"] - 0.003) < 1e-9
    assert s["lab"]["usd_complete"] is True
    assert s["reference"]["usd_complete"] is False
    assert s["candidate"]["requests"] == 2 and s["candidate"]["seconds"] == 2.0
