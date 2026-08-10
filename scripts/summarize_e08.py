"""Console summary of E08 (dev aid): coverage landscape + H5 decoupling."""

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E08_physics.json").read_text())

print("signal regions:", d["signal_regions"])
print("nominal expectations (10 fb^-1):", d["nominal_expectations"])

nom = d["environments"]["nominal"]["models"]
print("\nnominal sanity (coverage should be ~0.68):")
for k, m in nom.items():
    print(f"  {k:10s} coverage_mean={m['coverage_mean']:.3f} "
          f"width@mu=1 {m['per_mu']['1.0']['width']:.3f}")

print("\nworst coverage per model:")
for key in d["signal_regions"]:
    worst = min(((e, v["models"][key]) for e, v in d["environments"].items()
                 if e != "nominal"), key=lambda kv: kv[1]["coverage_mean"])
    e, m = worst
    print(f"  {key:10s} {e:24s} cov={m['coverage_mean']:.3f} "
          f"dAUC={m['delta_auc']:+.4f} bias@mu=1 {m['per_mu']['1.0']['bias']:+.3f} "
          f"(s {m['s_theta']:.0f}/{m['s0']:.0f}, b {m['b_theta']:.0f}/{m['b0']:.0f})")

dec = d["decoupled_cells_H5"]
print(f"\nH5 decoupled cells: {len(dec)}")
by_env: dict = {}
for c in dec:
    by_env.setdefault(c["env"].split("/")[0].split("=")[0], []).append(c)
for fam, cells in sorted(by_env.items()):
    covs = [c["coverage_mean"] for c in cells]
    print(f"  {fam:16s} n={len(cells):3d}  coverage [{min(covs):.3f}, {max(covs):.3f}]")

print("\nmost extreme decoupled cells (classifier flat, physics broken):")
for c in sorted(dec, key=lambda c: c["coverage_mean"])[:8]:
    print(f"  {c['env']:24s} {c['model']:10s} dAUC={c['delta_auc']:+.4f} "
          f"cov={c['coverage_mean']:.3f}")
