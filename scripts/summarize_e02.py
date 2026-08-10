"""Quick console summary of the E02 landscape (dev aid, not a paper artifact)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E02_landscape.json").read_text())
nom, envs = d["nominal"]["models"], d["environments"]
models = list(nom.keys())

print("nominal AUC:")
for m in models:
    print(f"  {m:12s} {nom[m]['auc']:.4f}  ci {nom[m]['auc_ci95']}")

cols = ["A:qksvc", "A:xgboost", "A:rbf_svc", "A:lightgbm", "B:xgboost", "B:mlp"]
print(f"\n{'environment':32s} {'n':>7s}  " + "  ".join(f"{c:>10s}" for c in cols))
for name, e in envs.items():
    da = e["delta_auc"]
    flag = "*" if max(abs(v) for v in da.values()) > 0.004 else " "
    row = "  ".join(f"{da[c]:+10.4f}" for c in cols)
    print(f"{flag}{name:31s} {e['n_events']:7d}  {row}")

print("\nmax |dAUC| per model:")
for m in models:
    worst = max(envs.items(), key=lambda kv: abs(kv[1]["delta_auc"][m]))
    print(f"  {m:12s} {worst[1]['delta_auc'][m]:+.4f}  at {worst[0]}")
