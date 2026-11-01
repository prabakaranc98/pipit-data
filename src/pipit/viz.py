"""Pictures of a study, drawn as plain SVG: the funnel from hypotheses to answers, and the hypothesis tree
with every model's evidence on each key question. No plotting library; the core stays dependency-free."""

from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

INK, MUTED, LINE, BG, PANEL = "#111111", "#3d4a40", "#9aa59d", "#fcfcfa", "#f2f5ef"
STATUS = {
    "supported": ("#b5452b", "limitation found"),
    "insufficient": ("#c48a1a", "not enough evidence yet"),
    "refuted": ("#4f7942", "no failure, enough evidence"),
    "no data": ("#9aa59d", "not run"),
}
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"


def _wrap(text: str, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


class _Canvas:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def text(
        self,
        x: float,
        y: float,
        s: str,
        size: float = 12.5,
        weight: str = "normal",
        fill: str = INK,
        anchor: str = "start",
    ) -> None:
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(s)}</text>'
        )

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str = "white",
        stroke: str = INK,
        rx: float = 6,
        width: float = 1.2,
    ) -> None:
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
        )

    def line(
        self, x1: float, y1: float, x2: float, y2: float, stroke: str = LINE, width: float = 1.2
    ) -> None:
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{width}"/>'
        )

    def circle(self, x: float, y: float, r: float, fill: str) -> None:
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>')


def tree_svg(
    title: str,
    subtitle: str,
    funnel: list[tuple[str, str]],
    hypotheses: list[dict[str, Any]],
    subjects: list[tuple[str, str]],
) -> str:
    """Draw the funnel and the tree.

    `hypotheses`: [{id, title, questions: [{id, title, detail, results}]}], where `results` maps each
    subject to {fail, n, lo, hi, status}.
    `subjects`: [(key, label)] in display order. `funnel`: [(count, label)] left to right."""
    c = _Canvas()
    W = 1520
    x_h, w_h = 40, 300
    x_q, w_q = 370, 380
    x_e, w_bar = 790, 300
    row_head, per_subject = 34, 17
    q_height = max(row_head + per_subject * len(subjects) + 10, 76)

    c.text(40, 40, title, size=21, weight="600")
    for i, line in enumerate(_wrap(subtitle, 190)):
        c.text(40, 64 + i * 17, line, size=13, fill=MUTED)
    y = 64 + 17 * len(_wrap(subtitle, 190)) + 14

    # funnel
    fx = 40
    box_w = (W - 80 - 18 * (len(funnel) - 1)) / max(1, len(funnel))
    for i, (count, label) in enumerate(funnel):
        c.rect(fx, y, box_w, 54, fill=PANEL, stroke=PANEL)
        c.text(fx + box_w / 2, y + 24, count, size=18, weight="600", anchor="middle")
        for j, ln in enumerate(_wrap(label, int(box_w / 6.6))[:2]):
            c.text(fx + box_w / 2, y + 40 + j * 12, ln, size=11, fill=MUTED, anchor="middle")
        if i < len(funnel) - 1:
            c.text(fx + box_w + 9, y + 32, "›", size=18, fill=MUTED, anchor="middle")
        fx += box_w + 18
    y += 80

    # legend
    lx = x_e
    c.text(x_h, y, "HYPOTHESIS", size=10.5, weight="600", fill=MUTED)
    c.text(x_q, y, "KEY QUESTION AND ITS CASES", size=10.5, weight="600", fill=MUTED)
    c.text(lx, y, "FAILURE RATE PER MODEL, WITH ITS 95% RANGE", size=10.5, weight="600", fill=MUTED)
    for cx, (_key, (colour, label)) in zip(
        (lx + 300, lx + 425, lx + 590), list(STATUS.items())[:3], strict=True
    ):
        c.circle(cx, y - 4, 5, colour)
        c.text(cx + 9, y, label, size=10.5, fill=MUTED)
    y += 16

    for h in hypotheses:
        qs = h["questions"]
        top = y
        h_bottom = top + q_height * len(qs) - 10
        c.rect(x_h, top, w_h, h_bottom - top, fill="white")
        c.text(x_h + 12, top + 22, h["id"], size=14, weight="600")
        title_lines = _wrap(h["title"], 40)[:6]
        for j, ln in enumerate(title_lines):
            c.text(x_h + 12, top + 42 + j * 16, ln, size=12.5)
        ry = top + 42 + len(title_lines) * 16 + 14
        if h.get("results") and ry + 16 * len(subjects) < h_bottom:
            c.text(x_h + 12, ry, "All its cases, per model:", size=11, fill=MUTED)
            for si, (key, label) in enumerate(subjects):
                r = h["results"].get(key)
                if not r or not r.get("n"):
                    continue
                colour = STATUS.get(r["status"], STATUS["insufficient"])[0]
                c.circle(x_h + 17, ry + 14 + si * 16, 4, colour)
                c.text(x_h + 27, ry + 18 + si * 16, f"{label}: {r['fail']} of {r['n']} wrong", size=11)
        for qi, q in enumerate(qs):
            qy = top + qi * q_height
            c.line(x_h + w_h, top + 20, x_q, qy + 20)
            c.rect(x_q, qy, w_q, q_height - 10, fill="white")
            c.text(x_q + 12, qy + 19, q["id"], size=12.5, weight="600")
            wrapped = _wrap(q["title"], 48)
            for j, ln in enumerate(wrapped[:2]):
                c.text(x_q + 60, qy + 19 + j * 15, ln, size=12)
            c.text(x_q + 12, qy + q_height - 18, q.get("detail", ""), size=11, fill=MUTED)
            c.line(
                x_q + w_q, qy + (q_height - 10) / 2, x_e - 12, qy + (q_height - 10) / 2, stroke=PANEL, width=1
            )
            for si, (key, label) in enumerate(subjects):
                sy = qy + 12 + si * per_subject
                r = q.get("results", {}).get(key)
                c.text(x_e, sy + 4, label, size=11, fill=MUTED)
                bx = x_e + 150
                c.line(bx, sy, bx + w_bar, sy, stroke=PANEL, width=6)
                if not r or not r.get("n"):
                    c.text(bx + w_bar + 10, sy + 4, "not run", size=11, fill=MUTED)
                    continue
                colour = STATUS.get(r["status"], STATUS["insufficient"])[0]
                c.line(bx + r["lo"] * w_bar, sy, bx + r["hi"] * w_bar, sy, stroke=colour, width=3)
                c.circle(bx + (r["fail"] / r["n"]) * w_bar, sy, 4.5, colour)
                c.text(bx + w_bar + 10, sy + 4, f"{r['fail']} of {r['n']} wrong", size=11, fill=INK)
        y = h_bottom + 18
    c.text(
        40,
        y + 6,
        "0% at the left edge of each bar, 100% at the right. A dot is the observed failure rate; the "
        "line is the range the true rate could lie in, given how few cases were run.",
        size=11.5,
        fill=MUTED,
    )
    H = y + 30
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" '
        f'role="img"><rect x="0" y="0" width="{W}" height="{H:.0f}" fill="{BG}"/>'
        + "".join(c.parts)
        + "</svg>"
    )
