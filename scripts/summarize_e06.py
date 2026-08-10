"""Console summary of E06 (dev aid): margin vs n* landscape."""

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
d = json.loads((REPO / "results/tables/E06_nstar.json").read_text())

rows = []
for env, v in d["environments"].items():
    for key, m in v["models"].items():
        for dd, c in m["claims"].items():
            rows.append({
                "env": env, "model": key, "delta": float(dd),
                "margin": c["margin"], "truth": c["truth"],
                "q50": c["n_star_quantiles"]["q50"],
                "res20k": c["resolved_frac_at_budget"]["20000"],
                "res500": c["resolved_frac_at_budget"]["500"],
                "verd": c["final_verdicts"],
            })

# n* as a function of |margin| — the universal landscape axis
print("median n* by |margin| bucket (all models/envs, resolved streams):")
buckets = [(0, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, 0.04), (0.04, 0.08), (0.08, 0.2)]
for lo, hi in buckets:
    sel = [r for r in rows if lo <= abs(r["margin"]) < hi]
    q50s = [r["q50"] for r in sel if r["q50"] is not None]
    res = float(np.mean([r["res20k"] for r in sel])) if sel else float("nan")
    med = int(np.median(q50s)) if q50s else None
    print(f"  |margin| in [{lo:.3f},{hi:.3f}): n={len(sel):4d}  "
          f"resolved@20k={res:.2f}  median n*={med}")

print("\nfalse-cert check at n_max=20000:")
fc = sum(r["verd"]["SUPPORTED"] for r in rows if not r["truth"])
tot_false = sum(sum(r["verd"].values()) for r in rows if not r["truth"])
print(f"  SUPPORTED on false claims: {fc}/{tot_false} = {fc/tot_false:.4f} (alpha=0.05)")
fr = sum(r["verd"]["REFUTED"] for r in rows if r["truth"])
tot_true = sum(sum(r["verd"].values()) for r in rows if r["truth"])
print(f"  REFUTED on true claims:  {fr}/{tot_true} = {fr/tot_true:.5f}")

print("\nexample (A:qksvc, delta=0.02) resolution across environments:")
for r in rows:
    if r["model"] == "A:qksvc" and r["delta"] == 0.02 and r["env"] in (
            "nominal", "tes=1.02", "combo3/seed13", "soft_met=5.0/seed12"):
        print(f"  {r['env']:22s} margin={r['margin']:+.4f} q50={r['q50']} "
              f"res@500={r['res500']:.2f} res@20k={r['res20k']:.2f}")
