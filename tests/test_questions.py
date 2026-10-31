import pytest

from pipit.questions import choice, chosen, noul, p_true, probabilities, validate_question


def test_noul_and_choice_shapes() -> None:
    assert noul("Is it raining?") == {"type": "noul", "instructions": "Is it raining?"}
    q = choice("Which?", {"a": "first", "b": None})
    assert q["type"] == "choice" and set(q["criteria"]) == {"a", "b"}
    validate_question(q)
    validate_question(noul("x"))


def test_choice_needs_two_options() -> None:
    with pytest.raises(ValueError):
        choice("Which?", {"only": None})
    with pytest.raises(ValueError):
        validate_question({"type": "choice", "criteria": {"one": None}})
    with pytest.raises(ValueError):
        validate_question({"type": "score"})


def test_answer_readers() -> None:
    assert chosen({"type": "choice", "choice": "a", "probabilities": {"a": 0.7, "b": 0.3}}) == "a"
    assert probabilities({"type": "choice", "choice": "a", "probabilities": {"a": 0.7, "b": 0.3}}) == {
        "a": 0.7,
        "b": 0.3,
    }
    assert p_true({"type": "noul", "noul": 0.25}) == 0.25
    assert p_true({"type": "choice", "choice": "a"}) is None
