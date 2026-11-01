"""I1 step 1: the last prompt token's hidden state at every layer for each critical and benign case, and the
option probabilities, checked against P1's recorded answers. Usage: python studies/i1_interp/extract.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
from common import HERE, cases, encode, letter_ids, load_model, p1, prompt_and_names  # noqa: E402


def main() -> None:
    tok, model = load_model()
    recorded = {}
    for line in (p1.RUNS / "answers_qwen35_4b.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            recorded[r["id"]] = r.get("choice")
    rows, states = [], []
    with torch.no_grad():
        for c in cases():
            text, names = prompt_and_names(c)
            out = model(input_ids=encode(tok, text).to("mps"), output_hidden_states=True)
            states.append(
                torch.stack([h[0, -1].float() for h in out.hidden_states]).cpu().numpy().astype(np.float16)
            )
            probs = (
                torch.softmax(out.logits[0, -1].float()[letter_ids(tok, len(names))], dim=0).cpu().tolist()
            )
            rows.append(
                {
                    "id": c["id"],
                    "family": c["family"],
                    "scenario": c["scenario"],
                    "condition": c["condition"],
                    "wording": c["wording"],
                    "expected": c["expected"],
                    "chosen": names[int(np.argmax(probs))],
                    "probabilities": dict(zip(names, probs, strict=True)),
                    "p1_choice": recorded.get(c["id"]),
                }
            )
    np.save(HERE / "runs" / "hidden_last.npy", np.stack(states))
    (HERE / "runs" / "extract.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    known = [r for r in rows if r["p1_choice"]]
    print(
        f"{len(rows)} cases; agrees with P1's recorded choice on {sum(r['chosen'] == r['p1_choice'] for r in known)}/{len(known)}"
    )


if __name__ == "__main__":
    main()
