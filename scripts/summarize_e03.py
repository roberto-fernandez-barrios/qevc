"""Join E03 geometry descriptors with E02 degradation (dev aid; formal
out-of-environment test is E04)."""

import json
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
e02 = json.loads((REPO / "results/tables/E02_landscape.json").read_text())
e03 = json.loads((REPO / "results/tables/E03_geometry.json").read_text())

rows = []
for env, g in e03["environments"].items():
    if env == "nominal" or env not in e02["environments"]:
        continue
    q, r = g["kernels"]["quantum"], g["kernels"]["rbf"]
    d = e02["environments"][env]["delta_auc"]
    rows.append({
        "env": env,
        "q_mmd2": q["mmd2"], "q_erank_ratio": q["eff_rank_ratio"],
        "r_mmd2": r["mmd2"],
        "d_qk": d["A:qksvc"], "d_xgb": d["A:xgboost"], "d_rbf": d["A:rbf_svc"],
    })

print(f"{'env':32s} {'q_mmd2':>9s} {'q_erankR':>9s} {'r_mmd2':>9s} {'dAUC_qk':>9s}")
for x in sorted(rows, key=lambda x: -x["q_mmd2"]):
    print(f"{x['env']:32s} {x['q_mmd2']:9.5f} {x['q_erank_ratio']:9.4f} "
          f"{x['r_mmd2']:9.5f} {x['d_qk']:+9.4f}")

print("\nSpearman rho across environments (n=%d):" % len(rows))
for gcol in ("q_mmd2", "q_erank_ratio", "r_mmd2"):
    for dcol in ("d_qk", "d_xgb", "d_rbf"):
        v = [x[gcol] for x in rows]
        u = [abs(x[dcol]) for x in rows]  # magnitude of degradation
        rho, p = stats.spearmanr(v, u)
        print(f"  {gcol:14s} vs |{dcol}|: rho={rho:+.3f} (p={p:.3g})")
