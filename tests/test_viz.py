import xml.etree.ElementTree as ET

from pipit.viz import tree_svg


def test_tree_svg_is_well_formed_and_shows_every_node() -> None:
    hyps = [
        {
            "id": "H1",
            "title": "Reading fails",
            "questions": [
                {
                    "id": "Q1.1",
                    "title": "negation",
                    "detail": "F1 · 8 cases",
                    "results": {"a": {"fail": 2, "n": 8, "lo": 0.07, "hi": 0.59, "status": "insufficient"}},
                },
                {"id": "Q1.2", "title": "buried & <odd> text", "detail": "F6 · 7 cases", "results": {}},
            ],
        },
        {
            "id": "H2",
            "title": "Computing fails",
            "questions": [
                {
                    "id": "Q2.1",
                    "title": "doses",
                    "detail": "F9 · 7 cases",
                    "results": {"a": {"fail": 5, "n": 7, "lo": 0.36, "hi": 0.92, "status": "supported"}},
                },
            ],
        },
    ]
    svg = tree_svg(
        "Study X", "subtitle", [("2", "hypotheses"), ("3", "key questions")], hyps, [("a", "Model A")]
    )
    root = ET.fromstring(svg)
    texts = " ".join(t.text or "" for t in root.iter("{http://www.w3.org/2000/svg}text"))
    for token in ["H1", "H2", "Q1.1", "Q1.2", "Q2.1", "2 of 8 wrong", "5 of 7 wrong", "not run", "<odd>"]:
        assert token in texts
