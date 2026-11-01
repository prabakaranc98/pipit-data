"""I1 step 2: for each scenario's critical and benign wording-0 pair, write the critical run's last-position output
of one layer into the benign run, layer by layer, and record the logit difference (cautious minus proceed letter).
Usage: python studies/i1_interp/patch.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parent))
from common import HERE, cases, encode, layers, letter_ids, load_model, p1, prompt_and_names  # noqa: E402


def main() -> None:
    tok, model = load_model()
    decoder = layers(model)
    by = {(c["family"], c["scenario"], c["condition"], c["wording"]): c for c in cases()}
    pairs = [
        (c, by[(f, s, "benign", 0)])
        for (f, s, cond, w), c in sorted(by.items())
        if cond == "critical" and w == 0 and (f, s, "benign", 0) in by
    ]
    results = []
    with torch.no_grad():
        for crit, ben in pairs:
            text_c, names = prompt_and_names(crit)
            text_b, _ = prompt_and_names(ben)
            ids = letter_ids(tok, len(names))
            cautious = ids[names.index(next(o for o in names if o in p1.CAUTIOUS))]
            proceed = ids[names.index(next(o for o in names if o in p1.PROCEED))]

            def diff(logits: torch.Tensor, cautious: int = cautious, proceed: int = proceed) -> float:
                return float(logits[cautious] - logits[proceed])

            captured: list[torch.Tensor] = []

            def capture(module, args, output, store=captured):
                h = output[0] if isinstance(output, tuple) else output
                store.append(h[0, -1].clone())

            handles = [layer.register_forward_hook(capture) for layer in decoder]
            try:
                ld_critical = diff(model(input_ids=encode(tok, text_c).to("mps")).logits[0, -1].float())
            finally:
                for h in handles:
                    h.remove()
            ids_b = encode(tok, text_b).to("mps")
            ld_benign = diff(model(input_ids=ids_b).logits[0, -1].float())
            curve = []
            for i, layer in enumerate(decoder):

                def patch(module, args, output, value=captured[i]):
                    h = output[0] if isinstance(output, tuple) else output
                    h[0, -1] = value.to(h.dtype)
                    return output

                handle = layer.register_forward_hook(patch)
                try:
                    curve.append(diff(model(input_ids=ids_b).logits[0, -1].float()))
                finally:
                    handle.remove()
            results.append(
                {
                    "pair": f"{crit['family']}-{crit['scenario']}",
                    "ld_critical": ld_critical,
                    "ld_benign": ld_benign,
                    "ld_patched": curve,
                }
            )
            print(results[-1]["pair"], round(ld_critical, 2), round(ld_benign, 2), flush=True)
    (HERE / "runs" / "patching.json").write_text(json.dumps(results))


if __name__ == "__main__":
    main()
