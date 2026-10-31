import pytest

from pipit.env import load_dotenv, require_key


def test_load_dotenv_sets_missing_only(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("PIPIT_TEST_A", raising=False)
    monkeypatch.setenv("PIPIT_TEST_B", "kept")
    env = tmp_path / ".env"
    env.write_text('# comment\nPIPIT_TEST_A = "value a"\nPIPIT_TEST_B=overridden\n\nbroken line\n')
    assert load_dotenv(env) == 1
    assert require_key("PIPIT_TEST_A") == "value a"
    assert require_key("PIPIT_TEST_B") == "kept"


def test_missing_file_and_missing_key(tmp_path, monkeypatch) -> None:
    assert load_dotenv(tmp_path / "absent") == 0
    monkeypatch.delenv("PIPIT_TEST_C", raising=False)
    with pytest.raises(RuntimeError):
        require_key("PIPIT_TEST_C")
