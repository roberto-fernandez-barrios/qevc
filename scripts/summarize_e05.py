"""Console summary of E05 (dev aid)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E05_auditor.json").read_text())

print("frozen:", d["frozen"])
print("error rates:", d["error_rates"])
print()

# accuracy degradation range per model
for key in d["frozen"]:
    m_ts = [v["models"][key]["m_target"] for v in d["environments"].values()]
    m_s = d["frozen"][key]["m_source"]
    print(f"{key}: M_S={m_s:.4f}  M_T range [{min(m_ts):.4f}, {max(m_ts):.4f}] "
          f"worst acc drop {m_s - min(m_ts):+.4f}")

print("\nverdict summary at delta=0.02 (20 seeds each):")
print(f"{'env':32s} {'model':10s} {'margin':>8s} {'S':>3s} {'R':>3s} {'U':>3s} "
      f"{'veto':>4s} {'n*med':>6s}")
for env, v in d["environments"].items():
    for key, m in v["models"].items():
        c = m["claims"]["0.02"]
        vd = c["verdicts"]
        interesting = vd["UNRESOLVED"] > 0 or c["vetoed"] > 0 or env == "nominal"
        if interesting or abs(c["margin"]) < 0.02:
            print(f"{env:32s} {key:10s} {c['margin']:+8.4f} {vd['SUPPORTED']:3d} "
                  f"{vd['REFUTED']:3d} {vd['UNRESOLVED']:3d} {c['vetoed']:4d} "
                  f"{str(c['n_star_median']):>6s}")
