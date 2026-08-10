"""Console summary of E07 (dev aid): active vs uniform n*."""

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E07_active.json").read_text())

print("Type-I per strategy:", json.dumps(d["error_rates"], indent=1))

rows = []
for env, v in d["environments"].items():
    for key, m in v["models"].items():
        for dd in m["strategies"]["uniform"]:
            u = m["strategies"]["uniform"][dd]
            a = m["strategies"]["uncertainty_mix"][dd]
            rows.append({
                "env": env, "model": key, "delta": float(dd),
                "u_q50": u["n_star_q50"], "a_q50": a["n_star_q50"],
                "u_res20k": u["resolved_frac_at_budget"]["20000"],
                "a_res20k": a["resolved_frac_at_budget"]["20000"],
            })

both = [(r["u_q50"], r["a_q50"]) for r in rows
        if r["u_q50"] is not None and r["a_q50"] is not None]
ratios = [a / u for u, a in both]
print(f"\ncells with both strategies resolved (median n*): {len(both)}")
print(f"  n* ratio active/uniform: median {np.median(ratios):.3f}, "
      f"IQR [{np.percentile(ratios, 25):.3f}, {np.percentile(ratios, 75):.3f}]")
print(f"  active strictly better: {np.mean(np.array(ratios) < 1):.2%}")

res_u = np.mean([r["u_res20k"] for r in rows])
res_a = np.mean([r["a_res20k"] for r in rows])
print(f"  mean resolved@20k: uniform {res_u:.3f} vs active {res_a:.3f}")

only_u = sum(1 for r in rows if r["u_q50"] is not None and r["a_q50"] is None)
only_a = sum(1 for r in rows if r["u_q50"] is None and r["a_q50"] is not None)
print(f"  resolved only by uniform: {only_u}; only by active: {only_a}")
