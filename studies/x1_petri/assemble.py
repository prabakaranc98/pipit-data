"""Write X1's report.md from its parts, so it is never edited by hand: the header (report_head.md, by hand),
the pressure test's section (pressure.py analyse), a note on how Petri's audits are numbered
(report_petri_note.md, by hand) and Petri's section (summarise_petri.py, which needs a Petri environment).
Run after any of them. Usage: python studies/x1_petri/assemble.py"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
PARTS = ("report_head.md", "runs/pressure_section.md", "report_petri_note.md", "runs/petri_section.md")


def main() -> None:
    # One newline between parts, as cat with an echo between them would join them.
    text = "\n".join((HERE / part).read_text() for part in PARTS)
    (HERE / "report.md").write_text(text)
    print(f"report.md written from {len(PARTS)} parts")


if __name__ == "__main__":
    main()
