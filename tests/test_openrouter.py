import urllib.error

import pytest

from pipit.adapters.openrouter import (
    EmptyContent,
    KeyRefused,
    OpenRouterChat,
    TooSlow,
    _read_within,
    budget_left,
)
from pipit.ledger import Ledger
from pipit.manifest import Context, Manifest


def _manifest():
    return Manifest(
        name="para",
        id="vendor/model",
        revision="as-served",
        adapter="pipit.adapters.openrouter:load",
        placement="api",
        key_env="PIPIT_TEST_OR_KEY",
    )


def _response(content, finish="stop", cost=1e-6, provider="P1"):
    return {
        "id": "gen-1",
        "model": "vendor/model",
        "provider": provider,
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": cost},
    }


def test_empty_content_is_retried_and_never_cached(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    served = [_response(None, finish="length"), _response("hello")]
    calls = []

    def transport(body, headers):
        calls.append(body)
        assert headers["Authorization"] == "Bearer k"
        return served.pop(0)

    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    chat = OpenRouterChat(_manifest(), ctx, transport=transport)
    r = chat("say hello", role="paraphraser")
    assert r["text"] == "hello" and r["cached"] is False and len(calls) == 2
    assert chat("say hello", role="paraphraser")["cached"] is True and len(calls) == 2
    rows = ctx.ledger.rows()
    assert len(rows) == 2
    assert rows[0]["attempts"] == 2 and rows[0]["usd"] == 1e-6 and rows[0]["provider"] == "P1"
    assert rows[1]["cached"] is True and rows[1]["usd"] is None  # a replay is recorded, priced at nothing


def test_persistent_empty_content_raises_and_ceiling_holds(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path, max_calls=1)
    chat = OpenRouterChat(_manifest(), ctx, transport=lambda body, headers: _response("", finish="length"))
    with pytest.raises(EmptyContent):
        chat("x", retries=2)
    with pytest.raises(RuntimeError, match="ceiling"):
        chat("y")


def test_a_system_message_is_sent_first_and_keys_its_own_cache_entry(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    bodies = []

    def transport(body, headers):
        bodies.append(body)
        return _response("ok")

    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    chat = OpenRouterChat(_manifest(), ctx, transport=transport)
    chat("the task", system="the rules")
    assert bodies[0]["messages"] == [
        {"role": "system", "content": "the rules"},
        {"role": "user", "content": "the task"},
    ]
    chat("the task")  # without a system message: a different request, not a cache hit
    assert len(bodies) == 2 and bodies[1]["messages"] == [{"role": "user", "content": "the task"}]


def test_a_refused_key_stops_at_once_without_retries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    calls = []

    def transport(body, headers):
        calls.append(body)
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, None)  # type: ignore[arg-type]

    chat = OpenRouterChat(
        _manifest(), Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path), transport
    )
    with pytest.raises(KeyRefused, match="HTTP 403"):
        chat("x")
    assert len(calls) == 1


def test_a_reply_that_never_finishes_hits_the_time_limit() -> None:
    class Padding:  # a connection kept alive with whitespace that never ends
        def read1(self, n):
            return b" "

    ticks = iter(range(0, 10_000, 30))
    with pytest.raises(TooSlow, match="within 600 s"):
        _read_within(Padding(), deadline_s=600, clock=lambda: next(ticks))

    class Whole:
        def __init__(self):
            self.parts = [b'{"ok":', b" 1}", b""]

        def read1(self, n):
            return self.parts.pop(0)

    assert _read_within(Whole(), deadline_s=600) == b'{"ok": 1}'


def test_a_slow_call_is_tried_again_while_its_time_lasts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    served = [TooSlow("slow"), _response("ok")]

    def transport(body, headers):
        item = served.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    assert OpenRouterChat(_manifest(), ctx, transport)("x")["text"] == "ok"

    def always_slow(body, headers):
        raise TooSlow("slow")

    with pytest.raises(TooSlow):
        OpenRouterChat(_manifest(), ctx, always_slow)("y")


def test_the_budget_left_on_a_key(monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    seen = {}

    def fetch(url, headers):
        seen.update(url=url, auth=headers["Authorization"])
        return {"data": {"limit": 25, "limit_remaining": 14.85}}

    assert budget_left("PIPIT_TEST_OR_KEY", fetch=fetch) == 14.85
    assert seen == {"url": "https://openrouter.ai/api/v1/key", "auth": "Bearer k"}
    assert budget_left("PIPIT_TEST_OR_KEY", fetch=lambda u, h: {"data": {"limit_remaining": None}}) is None


def test_the_time_limit_covers_the_whole_call_not_each_attempt(tmp_path, monkeypatch) -> None:
    import time

    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    attempts = []

    def stalls(body, headers):
        attempts.append(1)
        time.sleep(0.06)
        raise TimeoutError("socket stalled")

    m = _manifest()
    m = type(m)(**{**m.__dict__, "settings": {"deadline_s": 0.1}})
    chat = OpenRouterChat(m, Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path), stalls)
    start = time.perf_counter()
    with pytest.raises((TooSlow, TimeoutError)):
        chat("x")
    assert time.perf_counter() - start < 0.3 and len(attempts) <= 2


def test_a_rejected_key_stops_at_once(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PIPIT_TEST_OR_KEY", "k")
    calls = []

    def transport(body, headers):
        calls.append(body)
        raise urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)  # type: ignore[arg-type]

    chat = OpenRouterChat(
        _manifest(), Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path), transport
    )
    with pytest.raises(KeyRefused, match="rejected"):
        chat("x")
    assert len(calls) == 1
