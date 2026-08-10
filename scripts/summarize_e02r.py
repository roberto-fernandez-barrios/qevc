"""Console summary of E02R (dev aid)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E02R_multiseed.json").read_text())
s = d["summary"]

print("nominal AUC across 5 seeds (mean +- std):")
for k, v in s.items():
    print(f"  {k}: {v['nominal_auc_mean']:.4f} +- {v['nominal_auc_std']:.4f}")

print("\nQK - XGB(A) nominal per seed:", d["nominal_qk_minus_xgbA"]["per_seed"])
print("  mean +- std:", d["nominal_qk_minus_xgbA"]["mean"], "+-",
      d["nominal_qk_minus_xgbA"]["std"])

print("\nTES pattern for A:qksvc (delta_auc mean +- std, sign_consistent):")
for e, v in d["tes_sign_pattern_qk"].items():
    print(f"  {e}: {v['mean']:+.4f} +- {v['std']:.4f}  "
          f"sign_consistent={v['sign_consistent']}")
print("TES monotone in fraction of seeds:", d["tes_monotone_fraction_of_seeds"])

print("\nsign-consistent deltas per model:")
for k, v in s.items():
    n_cons = sum(1 for e in v["delta_auc"].values() if e["sign_consistent"])
    print(f"  {k}: {n_cons}/{len(v['delta_auc'])} envs sign-consistent")

print("\nlargest replicated |delta| per model (mean, std, consistent):")
for k, v in s.items():
    e, dd = max(v["delta_auc"].items(), key=lambda kv: abs(kv[1]["mean"]))
    print(f"  {k}: {e} {dd['mean']:+.4f} +- {dd['std']:.4f} "
          f"cons={dd['sign_consistent']}")
