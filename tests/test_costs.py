from pipit.costs import Price, PriceList, cost_to_finding, per_case, per_group, summarize

ROWS = [
    {
        "role": "lab",
        "model_asked": "a",
        "tokens_in": 100,
        "tokens_out": 10,
        "usd": 0.002,
        "seconds": 1.0,
        "case_id": "c1",
    },
    {
        "role": "lab",
        "model_asked": "a",
        "tokens_in": 100,
        "tokens_out": 10,
        "usd": None,
        "seconds": 0.0,
        "case_id": "c1",
        "cached": True,
    },
    {
        "role": "reference",
        "model_asked": "jev-latest",
        "model_answered": "jev-1.14.0",
        "tokens_in": 1000,
        "tokens_out": 100,
        "usd": None,
        "seconds": 0.5,
        "case_id": "c2",
    },
    {"role": "candidate", "model_asked": "local", "requests": 2, "usd": 0.0, "seconds": 2.0, "case_id": "c2"},
]


def test_price_and_price_list(tmp_path) -> None:
    assert Price(1.0, 2.0).of(1_000_000, 500_000) == 2.0
    p = tmp_path / "prices.yaml"
    text = "as_of: 2026-10-31\nsource: vendor page\nmodels:\n"
    text += "  jev-1.14.0: {usd_per_million_in: 1.0, usd_per_million_out: 4.0}\n  unknown: null\n"
    p.write_text(text)
    pl = PriceList.load(p)
    assert pl.as_of == "2026-10-31" and set(pl.prices) == {"jev-1.14.0"}
    assert pl.price_row(ROWS[0]) == (0.002, "response")
    assert pl.price_row(ROWS[1]) == (0.0, "replayed")
    usd, how = pl.price_row(ROWS[2])
    assert how == "price_list" and abs(usd - (0.001 + 0.0004)) < 1e-12
    assert PriceList().price_row(ROWS[2]) == (None, "unpriced")


def test_summaries_separate_replays_and_unpriced() -> None:
    s = summarize(ROWS)
    assert s["lab"]["requests"] == 2 and s["lab"]["replayed"] == 1 and s["lab"]["tokens_in"] == 100
    assert abs(s["lab"]["usd"] - 0.002) < 1e-12 and s["lab"]["unpriced"] == 0
    assert s["reference"]["unpriced"] == 1 and s["reference"]["usd"] == 0.0
    assert s["candidate"]["requests"] == 2 and s["candidate"]["seconds"] == 2.0
    by_model = summarize(ROWS, by="model_asked")
    assert set(by_model) == {"a", "jev-latest", "local"}


def test_attribution_to_cases_groups_and_findings() -> None:
    pl = PriceList({"jev-1.14.0": Price(1.0, 4.0)})
    cc = per_case(ROWS, pl)
    assert set(cc) == {"c1", "c2"} and cc["c1"]["requests"] == 2 and abs(cc["c1"]["usd"] - 0.002) < 1e-12
    assert cc["c2"]["requests"] == 3 and abs(cc["c2"]["usd"] - 0.0014) < 1e-12 and cc["c2"]["seconds"] == 2.5
    g = per_group(cc, {"c1": "H1", "c2": "H2"})
    assert g["H1"]["cases"] == 1 and g["H2"]["seconds"] == 2.5
    f = cost_to_finding(cc, ["c1", "c2"])
    assert f["cases"] == 2 and abs(f["usd"] - 0.0034) < 1e-9 and f["seconds"] == 3.5
