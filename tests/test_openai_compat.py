import math

import pytest

from pipit.adapters.openai_compat import LLMSubject, option_probabilities, render
from pipit.ledger import Ledger
from pipit.manifest import Context, Manifest

CHOICE = {
    "type": "choice",
    "instructions": "Which team?",
    "criteria": {"billing": "Charges", "support": None, "sales": "Buying"},
}
NOUL = {"type": "noul", "instructions": "The customer is blocked right now."}


def test_render_choice_and_noul() -> None:
    prompt, names = render("My key stopped working.", CHOICE)
    assert names == ["billing", "support", "sales"]
    assert "A. Charges" in prompt and "B. support" in prompt and "C. Buying" in prompt
    assert prompt.endswith("Answer with the letter only.") and "Question: Which team?" in prompt
    prompt, names = render({"ticket": 1}, NOUL)
    assert names == ["yes", "no"] and "A. Yes" in prompt and "Is this statement true?" in prompt
    assert '{"ticket": 1}' in prompt


def test_option_probabilities_renormalise_and_report_mass() -> None:
    tops = [
        {"token": "B", "logprob": math.log(0.6)},
        {"token": " A", "logprob": math.log(0.3)},
        {"token": "<think>", "logprob": math.log(0.1)},
    ]
    probs, mass = option_probabilities(tops, ["billing", "support", "sales"])
    assert probs["support"] == pytest.approx(2 / 3) and probs["billing"] == pytest.approx(1 / 3)
    assert probs["sales"] == 0.0 and mass == pytest.approx(0.9)
    assert option_probabilities([{"token": "Hello", "logprob": 0.0}], ["yes", "no"]) == ({}, 0.0)


def _manifest():
    return Manifest(
        name="llm",
        id="org/llm-4b",
        revision="abc12345",
        adapter="pipit.adapters.openai_compat:load",
        placement="local",
        device="metal",
        dtype="bf16",
        settings={
            "base_url": "http://local/v1",
            "engine": "not-installed-engine",
            "served_model": "llm",
            "request": {"chat_template_kwargs": {"enable_thinking": False}},
        },
    )


def _reply(letter_logprobs):
    return {
        "model": "llm",
        "choices": [
            {
                "logprobs": {
                    "content": [{"top_logprobs": [{"token": t, "logprob": lp} for t, lp in letter_logprobs]}]
                }
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 1},
    }


def test_subject_answers_caches_and_records(tmp_path) -> None:
    sent = []

    def transport(url, body, headers):
        sent.append(body)
        assert (
            url == "http://local/v1/chat/completions" and body["model"] == "llm" and body["max_tokens"] == 1
        )
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
        if "Is this statement true?" in body["messages"][0]["content"]:
            return _reply([("A", math.log(0.8)), ("B", math.log(0.2))])
        return _reply([("C", math.log(0.7)), ("A", math.log(0.2))])

    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    subject = LLMSubject(_manifest(), ctx, transport=transport)
    out = subject("state", {"team": CHOICE, "blocked": NOUL}, meta={"case_id": "c1", "subject": "llm"})
    assert out["team"]["choice"] == "sales" and out["team"]["probabilities"]["support"] == 0.0
    assert out["blocked"]["noul"] == pytest.approx(0.8) and out["blocked"]["letter_mass"] == pytest.approx(
        1.0
    )
    subject("state", {"team": CHOICE, "blocked": NOUL}, meta={"case_id": "c1", "subject": "llm"})
    assert len(sent) == 2
    rows = ctx.ledger.rows()
    assert len(rows) == 4 and [r["cached"] for r in rows] == [False, False, True, True]
    assert (
        rows[0]["usd"] == 0.0
        and rows[0]["case_id"] == "c1"
        and rows[0]["model_answered"].startswith("org/llm-4b@abc12345")
    )


def test_subject_reports_no_answer_when_no_letter_comes_back(tmp_path) -> None:
    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    subject = LLMSubject(_manifest(), ctx, transport=lambda u, b, h: _reply([("<think>", 0.0)]))
    out = subject("state", {"team": CHOICE, "blocked": NOUL})
    assert (
        out["team"]["choice"] is None and out["blocked"]["noul"] is None and out["team"]["letter_mass"] == 0.0
    )


def _reasoned(text, finish="stop"):
    return {
        "model": "llm",
        "choices": [{"finish_reason": finish, "message": {"content": text, "reasoning": "18 x 15 = 270"}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 900},
    }


def test_reasoned_letter_reads_the_final_answer() -> None:
    from pipit.adapters.openai_compat import reasoned_letter

    names = ["administer", "withhold", "ask"]
    assert reasoned_letter(_reasoned("B"), names) == "withhold"
    assert reasoned_letter(_reasoned("<think>A or C?</think>\n\nAnswer: **C**."), names) == "ask"
    assert reasoned_letter(_reasoned("I choose A"), names) == "administer"
    assert reasoned_letter(_reasoned("", finish="length"), names) is None
    assert reasoned_letter(_reasoned("D"), names) is None


def test_thinking_mode_votes_across_samples_in_parallel(tmp_path) -> None:
    import threading

    replies = iter(["C", "C", "A", "C", ""])
    lock = threading.Lock()
    sent = []

    def transport(url, body, headers):
        with lock:
            sent.append(body)
            text = next(replies)
        assert body["max_tokens"] == 4096 and body["logprobs"] is False and body["temperature"] == 1.0
        assert body["chat_template_kwargs"] == {"enable_thinking": True}
        return _reasoned(text, finish="stop" if text else "length")

    m = _manifest()
    settings = {
        **m.settings,
        "answer": "after_reasoning",
        "max_tokens": 4096,
        "samples": 5,
        "concurrency": 3,
        "sampling": {"temperature": 1.0, "top_p": 0.95},
        "request": {"chat_template_kwargs": {"enable_thinking": True}},
    }
    m = Manifest(**{**m.__dict__, "settings": settings})
    ctx = Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path)
    subject = LLMSubject(m, ctx, transport=transport)
    out = subject("state", {"team": CHOICE}, meta={"case_id": "c1", "subject": "llm"})["team"]
    assert out["choice"] == "sales" and out["answered"] == 4 and out["agreement"] == 0.75 and not out["tie"]
    assert out["probabilities"] == {"billing": 0.25, "support": 0.0, "sales": 0.75}
    assert len(sent) == 5 and subject.answered_by().endswith("thinking, 5 samples")
    again = subject("state", {"team": CHOICE})["team"]
    assert again["probabilities"] == out["probabilities"] and len(sent) == 5
    rows = ctx.ledger.rows()
    assert sorted(r["sample"] for r in rows[:5]) == [0, 1, 2, 3, 4] and rows[0]["tokens_out"] == 900


def test_thinking_mode_split_vote_gives_no_answer(tmp_path) -> None:
    replies = iter(["A", "C", "B", "B", "A", "C"])
    m = _manifest()
    m = Manifest(
        **{
            **m.__dict__,
            "settings": {**m.settings, "answer": "after_reasoning", "samples": 2, "concurrency": 1},
        }
    )
    subject = LLMSubject(
        m,
        Context(ledger=Ledger(tmp_path / "l.jsonl"), cache_dir=tmp_path),
        transport=lambda u, b, h: _reasoned(next(replies)),
    )
    out = subject("state", {"team": CHOICE})["team"]
    assert out["tie"] and out["choice"] is None and out["agreement"] == 0.5
