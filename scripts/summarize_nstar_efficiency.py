"""n* efficiency vs the sequential information lower bound (derived analysis).

Contextualizes the E06 certification landscape: for every resolved claim cell,
compare the measured median stopping time n*_q50 against the Wald
information-theoretic yardstick

    n_oracle = log(1/alpha) / KL( Ber(p) || Ber(tau) )

where p = the environment's true stream mean (m_target) and tau = M_S - delta
is the claim threshold. Any sequential procedure with type-I error <= alpha
needs on the order of n_oracle samples to resolve the claim; the ratio
n*_q50 / n_oracle measures how much of the near-boundary label explosion is
fundamental statistics (KL ~ 2*margin^2 for small margins) versus slack in our
empirical-Bernstein confidence sequence (which pays a known iterated-logarithm
/ variance-adaptivity price; WSR 2020). Both components are reported honestly
— no minimax-optimality claim is made (D-028).

Sources (read-only): results/tables/E06_nstar.json.
Output: results/tables/E06_nstar_efficiency.json.
No new randomness (D-028 decision-note analysis).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

BUCKETS = [(0.0, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, 0.04),
           (0.04, 0.08), (0.08, np.inf)]


def kl_bernoulli(p: float, q: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    q = min(max(q, 1e-12), 1 - 1e-12)
    return p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))


def bucket_of(m: float) -> str:
    for lo, hi in BUCKETS:
        if lo <= m < hi:
            return f"[{lo}, {hi})" if np.isfinite(hi) else f">={lo}"
    return "?"


def main() -> int:
    src = REPO / "results/tables/E06_nstar.json"
    d = json.loads(src.read_text())
    alpha = d["alpha"]
    log_inv_alpha = float(np.log(1.0 / alpha))

    records = []
    for env_name, env in d["environments"].items():
        for model, cell in env["models"].items():
            p = cell["m_target"]
            for delta, claim in cell["claims"].items():
                q50 = claim["n_star_quantiles"]["q50"]
                if q50 is None:
                    continue  # unresolved cells have no stopping time
                tau = claim["tau"]
                margin = claim["margin"]
                kl = kl_bernoulli(p, tau)
                if kl <= 0:
                    continue
                n_oracle = log_inv_alpha / kl
                records.append({
                    "env": env_name, "model": model, "delta": delta,
                    "truth": claim["truth"], "margin": margin,
                    "n_star_q50": q50,
                    "n_oracle": round(n_oracle, 1),
                    "efficiency_ratio": round(q50 / n_oracle, 3),
                })

    ratios = np.array([r["efficiency_ratio"] for r in records])
    margins = np.array([abs(r["margin"]) for r in records])

    by_bucket: dict = {}
    for (lo, hi) in BUCKETS:
        name = f"[{lo}, {hi})" if np.isfinite(hi) else f">={lo}"
        sel = (margins >= lo) & (margins < hi)
        if sel.sum() == 0:
            continue
        rr = ratios[sel]
        by_bucket[name] = {
            "n_cells": int(sel.sum()),
            "ratio_q25": round(float(np.percentile(rr, 25)), 2),
            "ratio_q50": round(float(np.percentile(rr, 50)), 2),
            "ratio_q75": round(float(np.percentile(rr, 75)), 2),
        }

    by_truth = {}
    for tv in (True, False):
        rr = np.array([r["efficiency_ratio"] for r in records
                       if r["truth"] is tv])
        if len(rr):
            by_truth["certification" if tv else "refutation"] = {
                "n_cells": int(len(rr)),
                "ratio_q50": round(float(np.median(rr)), 2),
                "ratio_iqr": [round(float(np.percentile(rr, 25)), 2),
                              round(float(np.percentile(rr, 75)), 2)],
            }

    out = {
        "experiment": "E06_nstar_efficiency (derived analysis; D-028 "
                      "decision-note)",
        "sources_sha256": {"E06_nstar.json":
                           hashlib.sha256(src.read_bytes()).hexdigest()},
        "alpha": alpha,
        "definition": {
            "n_oracle": "log(1/alpha) / KL(Ber(m_target) || Ber(tau)) — "
                        "Wald information yardstick for any sequential "
                        "procedure with type-I error <= alpha",
            "efficiency_ratio": "n_star_q50 / n_oracle (conditional on "
                                "resolution, as E06's n* quantiles are)",
            "caveats": "no minimax claim; the EB-CS pays a known "
                       "variance-adaptivity/iterated-logarithm factor; "
                       "n* medians are over resolved streams only",
        },
        "overall": {
            "n_cells": len(records),
            "ratio_q25": round(float(np.percentile(ratios, 25)), 2),
            "ratio_q50": round(float(np.median(ratios)), 2),
            "ratio_q75": round(float(np.percentile(ratios, 75)), 2),
        },
        "by_margin_bucket": by_bucket,
        "by_direction": by_truth,
        "cells": records,
    }
    dest = REPO / "results/tables/E06_nstar_efficiency.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}  ({len(records)} resolved cells)")
    print(f"\noverall efficiency ratio n*_q50 / n_oracle: "
          f"median {out['overall']['ratio_q50']}  "
          f"IQR [{out['overall']['ratio_q25']}, {out['overall']['ratio_q75']}]")
    print("\nby |margin| bucket:")
    for name, b in by_bucket.items():
        print(f"  {name:>14}: n={b['n_cells']:4d}  "
              f"q50={b['ratio_q50']:6.2f}  "
              f"[{b['ratio_q25']:.2f}, {b['ratio_q75']:.2f}]")
    print("\nby direction:")
    for name, b in by_truth.items():
        print(f"  {name}: n={b['n_cells']}  q50={b['ratio_q50']}  "
              f"IQR {b['ratio_iqr']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
