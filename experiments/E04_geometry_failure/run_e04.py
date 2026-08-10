"""E04 — Geometry → failure prediction (spec §28, registry E04; H2 predictive).

Improvements over the E03 first pass (registered follow-ups):
- common random numbers: each draw uses the SAME fixed raw test rows across
  every environment, so cross-env descriptor differences are driven by θ,
  not by sampling;
- 3 independent draws → descriptor averages + per-draw sign-stability;
- weight-only environments excluded from regression (structural blind spot,
  E03 finding) and used to measure the residual noise floor;
- leave-one-nuisance-family-out ridge regression of |ΔAUC| on a small
  predeclared descriptor set, plus an mmd2-only baseline.

No target labels are used anywhere (I1 discipline).
Outputs: results/tables/E04_geom_failure.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from scipy import stats  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from qevc.geometry.descriptors import describe_environment, raw_spectrum  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E04 = yaml.safe_load((REPO / "configs/experiments/E04.yaml").read_text())
E01_RESULTS = json.loads((REPO / "results/tables/E01_nominal.json").read_text())
E02_RESULTS = json.loads((REPO / "results/tables/E02_landscape.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, parse_params  # noqa: E402

WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_family(env_name: str) -> str:
    for fam, prefixes in E04["regression"]["families"].items():
        if any(env_name.startswith(p) for p in prefixes):
            return fam
    if any(env_name.startswith(p) for p in WEIGHT_ONLY):
        return "weight_only"
    raise ValueError(f"unclassified environment: {env_name}")


def rbf_gram(A: np.ndarray, B: np.ndarray, gamma: float) -> np.ndarray:
    aa = (A * A).sum(1)[:, None]
    bb = (B * B).sum(1)[None, :]
    return np.exp(-gamma * np.clip(aa + bb - 2.0 * A @ B.T, 0.0, None))


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    d0 = build_environment_dataset(raw, Environment())
    train_df = d0[np.isin(d0["row_id"].to_numpy(), raw_splits["train"])]
    df_a = tier_a_frame(train_df, E01["tier_a"]["n_train"], E01["tier_a"]["seed"])
    y_src = np.where(df_a["labels"].to_numpy() == 1, 1, -1)

    qp = parse_params(E01_RESULTS["tiers"]["A"]["qksvc"]["best_params"])
    q_cols = E01["features"]["quantum"]
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    Zq_src = ang.transform(df_a[q_cols].to_numpy(float))

    std = StandardScaler().fit(df_a[FEATURES_ALL].to_numpy(float))
    Zc_src = std.transform(df_a[FEATURES_ALL].to_numpy(float))
    rp = parse_params(E01_RESULTS["tiers"]["A"]["rbf_svc"]["best_params"])
    gamma = (1.0 / (Zc_src.shape[1] * Zc_src.var())
             if rp["gamma"] == "scale" else float(rp["gamma"]))

    # Matched-kernel control (finding 3): RBF on the SAME 8 features,
    # mirroring the rbf_svc_8f model's StandardScaler pipeline.
    std8 = StandardScaler().fit(df_a[q_cols].to_numpy(float))
    Z8_src = std8.transform(df_a[q_cols].to_numpy(float))
    r8 = parse_params(E01_RESULTS["tiers"]["A"]["rbf_svc_8f"]["best_params"])
    gamma8 = (1.0 / (Z8_src.shape[1] * Z8_src.var())
              if r8["gamma"] == "scale" else float(r8["gamma"]))

    K_ss = {"quantum": kernel_exact(Zq_src, fm),
            "rbf": rbf_gram(Zc_src, Zc_src, gamma),
            "rbf8": rbf_gram(Z8_src, Z8_src, gamma8)}
    spec_ss = {k: raw_spectrum(v) for k, v in K_ss.items()}
    log(f"source anchors ready (n={len(df_a)})")

    # Fixed base rows per draw, shared across environments (CRN).
    test_ids = raw_splits["nominal_test"]
    draw_ids = {
        s: np.sort(np.random.default_rng(s).choice(
            test_ids, size=E04["draws"]["n_base_rows"], replace=False))
        for s in E04["draws"]["seeds"]
    }
    union_ids = np.unique(np.concatenate(list(draw_ids.values())))

    envs = [("nominal", Environment())] + environments()
    records: list[dict] = []
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=union_ids)
        row_ids_env = te["row_id"].to_numpy()
        for s, ids in draw_ids.items():
            sub = te[np.isin(row_ids_env, ids)]
            Zq_t = ang.transform(sub[q_cols].to_numpy(float))
            Zc_t = std.transform(sub[FEATURES_ALL].to_numpy(float))
            Z8_t = std8.transform(sub[q_cols].to_numpy(float))
            for kern, (Zt, Ks, Kst, gam) in {
                "quantum": (Zq_t, K_ss["quantum"],
                            kernel_exact(Zq_src, fm, Zq_t), None),
                "rbf": (Zc_t, K_ss["rbf"], rbf_gram(Zc_src, Zc_t, gamma), gamma),
                "rbf8": (Z8_t, K_ss["rbf8"], rbf_gram(Z8_src, Z8_t, gamma8), gamma8),
            }.items():
                Ktt = (kernel_exact(Zt, fm) if kern == "quantum"
                       else rbf_gram(Zt, Zt, gam))
                g = describe_environment(Ks, Ktt, Kst, y_source=y_src,
                                         top_eigs=E04["top_eigs"],
                                         source_spectrum=spec_ss[kern])
                g["entropy_diff"] = g["spec_entropy_tt"] - g["spec_entropy_ss"]
                records.append({"env": env_name, "draw": s, "kernel": kern,
                                "n_target": int(len(sub)), **g})
        log(f"{env_name}: done ({len(te)} union rows)")

    # ---- Analysis ---------------------------------------------------------
    feats = E04["regression"]["features"]
    deltas = {e: v["delta_auc"] for e, v in E02_RESULTS["environments"].items()}

    def avg_desc(env, kern):
        rows = [r for r in records if r["env"] == env and r["kernel"] == kern]
        return {f: float(np.mean([r[f] for r in rows])) for f in feats}

    env_names = [e for e, _ in envs if e != "nominal"]
    fam = {e: env_family(e) for e in env_names}
    shift_envs = [e for e in env_names if fam[e] != "weight_only"]
    wo_envs = [e for e in env_names if fam[e] == "weight_only"]

    noise = {
        kern: {f: float(np.std([r[f] for r in records
                                if r["env"] in wo_envs and r["kernel"] == kern]))
               for f in feats}
        for kern in ("quantum", "rbf", "rbf8")
    }

    analysis: dict = {"noise_floor_weight_only": noise, "lono": {}}
    for kern in ("quantum", "rbf", "rbf8"):
        targets = [E04["kernel_model_map"][kern]] + E04["transfer_targets"]
        X_all = np.array([[avg_desc(e, kern)[f] for f in feats] for e in shift_envs])
        for target in targets:
            y_all = np.array([abs(deltas[e][target]) for e in shift_envs])
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
                rho, p = (stats.spearmanr(pred, y_all[va])
                          if len(va) >= 3 else (np.nan, np.nan))
                per_fold[held] = {"n": len(va), "rho": None if np.isnan(rho) else round(float(rho), 3),
                                  "p": None if np.isnan(p) else round(float(p), 4)}
            rho_pool, p_pool = stats.spearmanr(pooled_pred, y_all)
            rho_mmd, p_mmd = stats.spearmanr(
                [avg_desc(e, kern)["mmd2"] for e in shift_envs], y_all)
            analysis["lono"][f"{kern}->{target}"] = {
                "per_fold": per_fold,
                "pooled_rho": round(float(rho_pool), 3), "pooled_p": round(float(p_pool), 4),
                "mmd2_only_rho": round(float(rho_mmd), 3), "mmd2_only_p": round(float(p_mmd), 4),
            }

    out = {
        "experiment": "E04",
        "n_shift_envs": len(shift_envs), "n_weight_only_envs": len(wo_envs),
        "records": records,
        "analysis": analysis,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E04_geom_failure.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E04", config={"E01": E01, "E04": E04},
        seed=E04["draws"]["seeds"][0],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E04 complete in {out['wall_seconds']} s -> {out_path}")
    print(json.dumps(analysis["lono"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
