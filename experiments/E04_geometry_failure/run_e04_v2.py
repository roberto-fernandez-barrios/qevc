"""E04 v2 — H2 re-estimated against multi-seed degradation targets (E02R).

The E04 descriptors are unchanged (label-free, deterministic); only the
regression TARGETS change: from single-seed E02 deltas to E02R across-seed
mean |ΔAUC|, which strips partition noise out of the dependent variable.
Registered as the gate on any manuscript H2 claim.

Outputs: results/tables/E04v2_geom_failure_multiseed.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qevc.utils.repro import RunManifest  # noqa: E402

E04 = yaml.safe_load((REPO / "configs/experiments/E04.yaml").read_text())
E04_RESULTS = json.loads((REPO / "results/tables/E04_geom_failure.json").read_text())
E02R_RESULTS = json.loads((REPO / "results/tables/E02R_multiseed.json").read_text())

WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")
KERNEL_TARGETS = {
    "quantum": ["A:qksvc", "A:xgboost"],
    "rbf": ["A:rbf_svc", "A:xgboost"],
}


def env_family(env_name: str) -> str:
    for fam, prefixes in E04["regression"]["families"].items():
        if any(env_name.startswith(p) for p in prefixes):
            return fam
    if any(env_name.startswith(p) for p in WEIGHT_ONLY):
        return "weight_only"
    raise ValueError(env_name)


def main() -> int:
    t0 = time.time()
    feats = E04["regression"]["features"]
    records = E04_RESULTS["records"]
    env_names = sorted({r["env"] for r in records} - {"nominal"})
    fam = {e: env_family(e) for e in env_names}
    shift_envs = [e for e in env_names if fam[e] != "weight_only"]

    def avg_desc(env, kern):
        rows = [r for r in records if r["env"] == env and r["kernel"] == kern]
        return {f: float(np.mean([r[f] for r in rows])) for f in feats}

    summary = E02R_RESULTS["summary"]
    analysis: dict = {}
    for kern, targets in KERNEL_TARGETS.items():
        X_all = np.array([[avg_desc(e, kern)[f] for f in feats] for e in shift_envs])
        mmd = np.array([avg_desc(e, kern)["mmd2"] for e in shift_envs])
        for target in targets:
            y_all = np.array([abs(summary[target]["delta_auc"][e]["mean"])
                              for e in shift_envs])
            per_fold = {}
            pooled_pred = np.full(len(shift_envs), np.nan)
            for held in E04["regression"]["families"]:
                tr = [i for i, e in enumerate(shift_envs) if fam[e] != held]
                va = [i for i, e in enumerate(shift_envs) if fam[e] == held]
                if not va:
                    continue
                sc = StandardScaler().fit(X_all[tr])
                model = Ridge(alpha=E04["regression"]["ridge_alpha"])
                model.fit(sc.transform(X_all[tr]), y_all[tr])
                pred = model.predict(sc.transform(X_all[va]))
                pooled_pred[va] = pred
                if len(va) >= 3:
                    rho, p = stats.spearmanr(pred, y_all[va])
                    per_fold[held] = {"n": len(va), "rho": round(float(rho), 3),
                                      "p": round(float(p), 4)}
                else:
                    per_fold[held] = {"n": len(va), "rho": None, "p": None}
            rho_pool, p_pool = stats.spearmanr(pooled_pred, y_all)
            rho_mmd, p_mmd = stats.spearmanr(mmd, y_all)
            analysis[f"{kern}->{target}"] = {
                "per_fold": per_fold,
                "pooled_rho": round(float(rho_pool), 3),
                "pooled_p": round(float(p_pool), 4),
                "mmd2_only_rho": round(float(rho_mmd), 3),
                "mmd2_only_p": round(float(p_mmd), 4),
            }

    out = {
        "experiment": "E04v2",
        "targets": "E02R across-seed mean |delta AUC| (5 seeds)",
        "n_shift_envs": len(shift_envs),
        "analysis": analysis,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E04v2_geom_failure_multiseed.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E04v2", config={"E04": E04, "targets": "E02R"}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    print(json.dumps(analysis, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
