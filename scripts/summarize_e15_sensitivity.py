"""Nuisance-sensitivity summary ∂μ̂/∂θ from archived inference tables.

Closes SAP §1.2's nuisance-sensitivity deliverable (D-017 deviation 5) as a
derived analysis: finite differences of the stored per-cell μ̂ bias across each
single-nuisance environment axis, at every inference level.

Sources (read-only, archived):
  - results/tables/E08_physics.json   (L1, D-015 counting; 4 audit models)
  - results/tables/E15_inference.json (L2/L3 profile likelihood; gated models)

No new randomness is consumed (D-028: decision-note analysis, not a registered
experiment). Combos are excluded — they have no single-θ axis.

Output: results/tables/E15_sensitivity.json
  slope_at_nominal : central difference on the innermost bracket around θ=0
                     (one-sided for soft_met, whose grid starts at 0 GeV)
  slope_lsq        : least-squares slope over the full family grid
  tracking_L2/L3   : ∂θ̂_fam/∂θ_fam from the stored mean fitted nuisances
                     (how well profiling tracks the true shift; absent where
                     the family is not profiled, e.g. its own L3).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]

MU_GRID = ["0.5", "1.0", "1.5", "2.0", "3.0"]

# family -> (unit, {env_name_or_nominal: theta}); soft_met envs carry 3 seeds.
FAMILIES: dict[str, tuple[str, dict[str, float]]] = {
    "tes": ("mu per sigma", {"tes=0.98": -2.0, "tes=0.99": -1.0, "nominal": 0.0,
                             "tes=1.01": 1.0, "tes=1.02": 2.0}),
    "jes": ("mu per sigma", {"jes=0.98": -2.0, "jes=0.99": -1.0, "nominal": 0.0,
                             "jes=1.01": 1.0, "jes=1.02": 2.0}),
    "soft_met": ("mu per GeV", {"nominal": 0.0, "soft_met=1.0": 1.0,
                                "soft_met=2.0": 2.0, "soft_met=3.0": 3.0,
                                "soft_met=5.0": 5.0}),
    "ttbar_scale": ("mu per unit scale", {"ttbar_scale=0.96": 0.96,
                                          "ttbar_scale=0.98": 0.98,
                                          "nominal": 1.0,
                                          "ttbar_scale=1.02": 1.02,
                                          "ttbar_scale=1.04": 1.04}),
    "diboson_scale": ("mu per unit scale", {"diboson_scale=0.5": 0.5,
                                            "diboson_scale=0.75": 0.75,
                                            "nominal": 1.0,
                                            "diboson_scale=1.25": 1.25,
                                            "diboson_scale=1.5": 1.5}),
    "bkg_scale": ("mu per unit scale", {"bkg_scale=0.998": 0.998,
                                        "bkg_scale=0.999": 0.999,
                                        "nominal": 1.0,
                                        "bkg_scale=1.001": 1.001,
                                        "bkg_scale=1.002": 1.002}),
}

# fitted-nuisance key and the true-θ transform used by the L2/L3 fits
TRACK_THETA = {
    "tes": lambda envs_theta: envs_theta,          # already in sigma units
    "jes": lambda envs_theta: envs_theta,
    "soft_met": lambda envs_theta: envs_theta,     # GeV
    "ttbar_scale": lambda envs_theta: envs_theta,  # scale units
    "diboson_scale": lambda envs_theta: envs_theta,
    "bkg_scale": lambda envs_theta: envs_theta,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_averaged_bias(env_block: dict, family_env: str, model: str,
                       level: str, mu: str) -> float | None:
    """Bias for one grid point; soft_met values average the 3 seed envs."""
    if family_env.startswith("soft_met="):
        vals = []
        for seed in (11, 12, 13):
            name = f"{family_env}/seed{seed}"
            cell = env_block.get(name, {}).get("models", {}).get(model)
            if cell is None or level not in cell:
                return None
            vals.append(cell[level][mu]["bias"])
        return float(np.mean(vals))
    cell = env_block.get(family_env, {}).get("models", {}).get(model)
    if cell is None or level not in cell:
        return None
    return float(cell[level][mu]["bias"])


def seed_averaged_pull(env_block: dict, family_env: str, model: str,
                       level: str, mu: str, fam: str) -> float | None:
    """Mean fitted value of the family's own nuisance at one grid point."""
    def one(name: str) -> float | None:
        cell = env_block.get(name, {}).get("models", {}).get(model)
        if cell is None or level not in cell:
            return None
        return cell[level][mu].get("nuisance_hat_mean", {}).get(fam)
    if family_env.startswith("soft_met="):
        vals = [one(f"{family_env}/seed{s}") for s in (11, 12, 13)]
        if any(v is None for v in vals):
            return None
        return float(np.mean([v for v in vals if v is not None]))
    return one(family_env)


def slopes(thetas: np.ndarray, biases: np.ndarray) -> tuple[float, float]:
    """(slope at nominal via innermost bracket, least-squares slope)."""
    order = np.argsort(thetas)
    t, b = thetas[order], biases[order]
    nom = FAM_NOMINAL  # set per family before calling
    below = t[t < nom]
    above = t[t > nom]
    if len(below) and len(above):
        t_lo, t_hi = below.max(), above.min()
    elif len(above) >= 2:                      # one-sided (soft_met)
        t_lo, t_hi = nom, above.min()
    else:
        t_lo, t_hi = below.max(), nom
    b_lo = b[np.where(t == t_lo)[0][0]]
    b_hi = b[np.where(t == t_hi)[0][0]]
    central = (b_hi - b_lo) / (t_hi - t_lo)
    lsq = float(np.polyfit(t, b, 1)[0])
    return float(central), lsq


def main() -> int:
    e08_path = REPO / "results/tables/E08_physics.json"
    e15_path = REPO / "results/tables/E15_inference.json"
    e08 = json.loads(e08_path.read_text())
    e15 = json.loads(e15_path.read_text())

    # L1 cells: E08 stores per_mu directly; adapt to the L-keyed shape.
    l1_envs: dict = {}
    for env_name, env in e08["environments"].items():
        l1_envs[env_name] = {"models": {}}
        for model, cell in env["models"].items():
            l1_envs[env_name]["models"][model] = {
                "L1": {mu: {"bias": cell["per_mu"][mu]["bias"]}
                       for mu in MU_GRID}}

    sources = {
        "E08_physics.json": sha256(e08_path),
        "E15_inference.json": sha256(e15_path),
    }
    level_blocks = {"L1": (l1_envs, list(next(iter(
        e08["environments"].values()))["models"].keys())),
                    "L2": (e15["environments"],
                           list(e15["environments"]["nominal"]["models"])),
                    "L3": (e15["environments"],
                           list(e15["environments"]["nominal"]["models"]))}

    global FAM_NOMINAL
    out_fam: dict = {}
    for fam, (unit, grid) in FAMILIES.items():
        FAM_NOMINAL = grid.get("nominal", 0.0) if fam != "soft_met" else 0.0
        fam_out = {"unit": unit,
                   "theta_grid": sorted(grid.values()),
                   "levels": {}, "tracking": {}}
        for level, (envs_block, models) in level_blocks.items():
            lv: dict = {}
            for model in models:
                per_mu: dict = {}
                for mu in MU_GRID:
                    ts, bs = [], []
                    for env_name, theta in grid.items():
                        b = seed_averaged_bias(envs_block, env_name, model,
                                               level, mu)
                        if b is not None:
                            ts.append(theta)
                            bs.append(b)
                    if len(ts) < 3:
                        continue
                    c, l = slopes(np.array(ts), np.array(bs))
                    per_mu[mu] = {"slope_at_nominal": round(c, 4),
                                  "slope_lsq": round(l, 4),
                                  "n_grid_points": len(ts)}
                if per_mu:
                    cs = [v["slope_at_nominal"] for v in per_mu.values()]
                    ls = [v["slope_lsq"] for v in per_mu.values()]
                    lv[model] = {"per_mu": per_mu,
                                 "slope_at_nominal_mu_avg": round(
                                     float(np.mean(cs)), 4),
                                 "slope_lsq_mu_avg": round(
                                     float(np.mean(ls)), 4)}
            if lv:
                fam_out["levels"][level] = lv
        # profiling tracking ∂θ̂_fam/∂θ_fam (L2/L3 only; absent if unprofiled)
        for level in ("L2", "L3"):
            envs_block, models = level_blocks[level]
            tr: dict = {}
            for model in models:
                ts, ps = [], []
                for env_name, theta in grid.items():
                    p = seed_averaged_pull(envs_block, env_name, model,
                                           level, mu="1.0", fam=fam)
                    if p is not None:
                        ts.append(theta)
                        ps.append(p)
                if len(ts) >= 3 and np.ptp(ts) > 0:
                    tr[model] = round(float(np.polyfit(ts, ps, 1)[0]), 4)
            if tr:
                fam_out["tracking"][level] = tr
        out_fam[fam] = fam_out

    out = {
        "experiment": "E15_sensitivity (derived analysis; SAP §1.2, "
                      "D-017 deviation 5 closure; D-028 decision-note)",
        "sources_sha256": sources,
        "mu_grid": MU_GRID,
        "definition": {
            "slope_at_nominal": "finite difference of mean μ̂ bias on the "
                                "innermost bracket around θ=0 (one-sided "
                                "for soft_met)",
            "slope_lsq": "least-squares slope over the full family grid",
            "tracking": "least-squares slope of the mean fitted nuisance "
                        "θ̂_fam vs true θ_fam at μ=1.0 (1.0 = perfect "
                        "tracking; only where the family is profiled)",
        },
        "families": out_fam,
    }
    dest = REPO / "results/tables/E15_sensitivity.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest}")

    # console summary: mu-averaged slope at nominal per family x level x model
    for fam, fo in out_fam.items():
        print(f"\n{fam} [{fo['unit']}]")
        for level, lv in fo["levels"].items():
            row = ", ".join(f"{m}: {v['slope_at_nominal_mu_avg']:+.3f}"
                            for m, v in lv.items())
            print(f"  {level}: {row}")
        for level, tr in fo["tracking"].items():
            row = ", ".join(f"{m}: {v:+.3f}" for m, v in tr.items())
            print(f"  tracking {level}: {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
