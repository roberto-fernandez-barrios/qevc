"""Console summary of E04 (dev aid)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E04_geom_failure.json").read_text())
a = d["analysis"]

print("noise floor (std over weight-only envs x draws):")
for k, v in a["noise_floor_weight_only"].items():
    print(f"  {k}: " + ", ".join(f"{f}={x:.2e}" for f, x in v.items()))

print()
for pair, r in a["lono"].items():
    print(f"{pair}: pooled rho={r['pooled_rho']} (p={r['pooled_p']}), "
          f"mmd2-only rho={r['mmd2_only_rho']} (p={r['mmd2_only_p']})")
    for fam, v in r["per_fold"].items():
        print(f"    {fam:9s} n={v['n']:2d} rho={v['rho']}")
