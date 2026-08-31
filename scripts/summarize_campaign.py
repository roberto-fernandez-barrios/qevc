"""Post-campaign summary: matched-kernel control + gated H5 counts (dev aid)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((REPO / f"results/tables/{name}.json").read_text())


e01 = load("E01_nominal")["tiers"]["A"]
print("E01 tier A nominal AUC:")
for m in ("qksvc", "rbf_svc", "rbf_svc_8f", "xgboost"):
    print(f"  {m:12s} {e01[m]['test']['auc']:.4f} ci {e01[m]['auc_ci95']} "
          f"{e01[m]['best_params']}")

s = load("E02R_multiseed")["summary"]
print("\nE02R nominal (5 seeds):")
for m in ("A:qksvc", "A:rbf_svc", "A:rbf_svc_8f", "A:xgboost"):
    print(f"  {m:14s} {s[m]['nominal_auc_mean']:.4f} +- {s[m]['nominal_auc_std']:.4f}")

qk = [load("E02R_multiseed")["per_seed"][k]["environments"]["nominal"]["A:qksvc"]["auc"]
      for k in load("E02R_multiseed")["per_seed"]]
r8 = [load("E02R_multiseed")["per_seed"][k]["environments"]["nominal"]["A:rbf_svc_8f"]["auc"]
      for k in load("E02R_multiseed")["per_seed"]]
diff = [round(a - b, 4) for a, b in zip(qk, r8)]
print(f"  per-seed QK - RBF8: {diff}")

v2 = load("E04v2_geom_failure_multiseed")["analysis"]
print("\nE04v2 sensors (multi-seed targets):")
for k, r in v2.items():
    print(f"  {k:24s} descriptive mmd2-only rho={r['mmd2_only_rho']:+.3f} (IID p omitted)")

e08 = load("E08_physics")
print(f"\nE08 gated decoupling: {len(e08['decoupled_cells_H5'])} cells, "
      f"{len(e08['decoupled_unique_theta_model'])} unique theta|model")
themes = sorted({c.split('|')[0] for c in e08['decoupled_unique_theta_model']})
print("  unique thetas:", themes)
