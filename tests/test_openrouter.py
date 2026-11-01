import pytest

from pipit.adapters.openrouter import EmptyContent, OpenRouterChat
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
