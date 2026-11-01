"""Rules the first studies exposed: a tree must partition its cases (#45), no model may filter or grade for a
candidate of its own family (#43), and a model served by several providers is flagged (#44)."""

import sys
from pathlib import Path

import yaml

from pipit.ledger import mixed_providers, providers
from pipit.manifest import Manifest, family_conflicts, load_manifest, undeclared
from pipit.tree import Rule, partition, rules

P1 = Path(__file__).parents[1] / "studies" / "p1_clinical"


def _case(cid: str, family: str, condition: str) -> dict:
    return {"id": cid, "family": family, "condition": condition}


def test_partition_reports_cases_claimed_twice_or_never() -> None:
    cases = [_case("a", "F1", "critical"), _case("b", "F1", "absent"), _case("c", "F9", "critical")]
    overlapping = [Rule("Q1", frozenset({"F1"})), Rule("Q4", None, frozenset({"absent"}))]
    split = partition(cases, overlapping)
    assert not split.ok
    assert split.claimed_twice == {"b": ["Q1", "Q4"]} and split.unclaimed == ["c"]
    fixed = [
        Rule("Q1", frozenset({"F1", "F9"}), frozenset({"critical"})),
        Rule("Q4", None, frozenset({"absent"})),
    ]
    split = partition(cases, fixed)
    assert split.ok and split.leaf_of == {"a": "Q1", "b": "Q4", "c": "Q1"}


def test_p1_tree_partitions_its_cases() -> None:
    sys.path.insert(0, str(P1))
    from study import load_cases

    spec = yaml.safe_load((P1 / "hypotheses.yaml").read_text())
    split = partition(load_cases().values(), rules(spec))
    assert split.ok and len(split.leaf_of) == len(load_cases())


def _m(name: str, family: str | None) -> Manifest:
    return Manifest(name=name, id=name, revision="r", adapter="m:f", placement="api", family=family)


def test_family_rule_flags_instruments_from_a_candidate_family() -> None:
    candidates = [_m("qwen_4b", "qwen"), _m("decider", "qwen")]
    instruments = [_m("validator", "qwen"), _m("judge", "deepseek"), _m("helper", None)]
    assert family_conflicts(candidates, instruments) == [
        ("validator", "qwen_4b", "qwen"),
        ("validator", "decider", "qwen"),
    ]
    assert undeclared(candidates + instruments) == ["helper"]


def test_p1_roster_breaks_the_family_rule_through_its_validator() -> None:
    load = lambda n: load_manifest(P1 / "models" / f"{n}.yaml")  # noqa: E731
    candidates = [load(n) for n in ("pplx_flash", "pplx_flash_grouped", "qwen35_4b")]
    instruments = [load(n) for n in ("paraphraser", "paraphraser_fallback", "validator", "proposer")]
    conflicts = family_conflicts(candidates, instruments)
    assert {c[0] for c in conflicts} == {"validator"} and len(conflicts) == 3


def test_models_served_by_several_providers_are_flagged() -> None:
    rows = [
        {"subject": "judge_a", "provider": "Baidu"},
        {"subject": "judge_a", "provider": "Relace"},
        {"subject": "judge_a", "provider": "Relace", "cached": True},
        {"subject": "judge_b", "provider": "DeepInfra"},
        {"subject": "judge_b", "provider": "DeepInfra"},
        {"subject": "judge_c"},
    ]
    assert providers(rows)["judge_a"] == {"Baidu": 1, "Relace": 1}
    assert set(mixed_providers(rows)) == {"judge_a"}
