"""E04v3 — Out-of-grid generalization of the frozen geometry sensor
(registry E04v3; D-025, D-021).

60 NEW environments (36 off-grid single-nuisance + 24 official-prior draws,
frozen in configs/experiments/E04v3.yaml) that no development ever saw.
Order-of-operations discipline: sensor values (MMD^2 of the frozen quantum
and rbf8 kernels, CRN draws from auditor_dev) are computed and ARCHIVED for
every environment BEFORE any frozen model is scored — target labels cannot
touch the sensor pipeline.

Two worlds: primary = the frozen seed-101 deployment; secondary = the E12
deployment (cross-partition evaluation only, no tuning anywhere).

Outputs: results/tables/E04v3_out_of_grid.json
         (+ results/raw/E04v3_sensor_{world}.json archived first).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from scipy import stats  # noqa: E402
from sklearn.isotonic import IsotonicRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.geometry.descriptors import mean_similarity_shift  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import PlattCalibrator, class_balanced_weights  # noqa: E402
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    features_for,
    get_raw_splits,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E12 = yaml.safe_load((REPO / "configs/experiments/E12.yaml").read_text())
V3 = yaml.safe_load((REPO / "configs/experiments/E04v3.yaml").read_text())
FROZEN = yaml.safe_load((REPO / V3["frozen_source"]).read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
Q_COLS = FROZEN["features"]["quantum"]
WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_params(raw: dict) -> dict:
    out = {}
    for k, v in raw.items():
        try:
            out[k] = eval(v, {"__builtins__": {}})
        except Exception:
            out[k] = v
    return out


def new_environments() -> list[tuple[str, str, Environment]]:
    """(name, family, Environment) for the 60 frozen out-of-grid points."""
    envs: list[tuple[str, str, Environment]] = []
    og = V3["off_grid"]
    for v in og["tes"]:
        envs.append((f"og_tes={v}", "tes", Environment(tes=v)))
    for v in og["jes"]:
        envs.append((f"og_jes={v}", "jes", Environment(jes=v)))
    for v in og["soft_met"]["values"]:
        for s in og["soft_met"]["seeds"]:
            envs.append((f"og_soft_met={v}/seed{s}", "soft_met",
                         Environment(soft_met=v, seed=s)))
    for fam in WEIGHT_ONLY:
        for v in og[fam]:
            envs.append((f"og_{fam}={v}", "weight_only",
                         Environment(**{fam: v})))
    for i, d in enumerate(V3["prior_draws"]):
        d = dict(d)
        seed = d.pop("seed")
        envs.append((f"prior{i:02d}", "prior", Environment(**d, seed=seed)))
    assert len(envs) == 60, len(envs)
    return envs


def rbf_gram(A, B, gamma):
    aa = (A * A).sum(1)[:, None]
    bb = (B * B).sum(1)[None, :]
    return np.exp(-gamma * np.clip(aa + bb - 2.0 * A @ B.T, 0.0, None))


def load_world(tag: str, loader: FairUniverseLoader):
    if tag == "s101":
        raw = loader.load_subset(E01["subset"]["n_total"], E01["subset"]["seed"])
        splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
        ta_seed = E01["tier_a"]["seed"]
    else:
        exclusion = np.union1d(
            np.load(REPO / "data/processed/used_rows/seed101_subset_n300000_indices.npy"),
            np.load(REPO / "data/processed/used_rows/e00_validation_rowgroup_indices.npy"))
        raw = loader.load_subset(E12["subset"]["n_total"], E12["subset"]["seed"],
                                 exclude=exclusion, tag=E12["subset"]["tag"])
        splits = get_raw_splits(REPO, raw, E12["splits"], experiment_tag="E12")
        ta_seed = E12["tier_a_seed"]
    return raw, splits, ta_seed


def sensor_phase(world: str, raw, splits, df_a) -> dict:
    """MMD^2 per environment (frozen kernels, auditor_dev CRN draws).
    ARCHIVED before any target computation."""
    qp = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    r8 = parse_params(FROZEN["hyperparameters"]["tier_a"]["rbf_svc_8f"])
    ang = AngleScaler().fit(df_a[Q_COLS].to_numpy(float))
    fm = build_feature_map(len(Q_COLS), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    std8 = StandardScaler().fit(df_a[Q_COLS].to_numpy(float))
    gamma8 = float(r8["gamma"])
    Zq_src = ang.transform(df_a[Q_COLS].to_numpy(float))
    Z8_src = std8.transform(df_a[Q_COLS].to_numpy(float))
    K_ss = {"quantum": kernel_exact(Zq_src, fm),
            "rbf8": rbf_gram(Z8_src, Z8_src, gamma8)}

    ad_ids = splits["auditor_dev"]
    draw_ids = {s: np.sort(np.random.default_rng(s).choice(
                    ad_ids, size=V3["sensor"]["n_base_rows"], replace=False))
                for s in V3["sensor"]["draw_seeds"]}
    union_ids = np.unique(np.concatenate(list(draw_ids.values())))

    envs = [("nominal", "nominal", Environment())] + new_environments()
    mmd: dict[str, dict[str, list[float]]] = {}
    for env_name, _fam, env in envs:
        te = build_environment_dataset(raw, env, row_ids=union_ids)
        rid = te["row_id"].to_numpy()
        mmd[env_name] = {"quantum": [], "rbf8": []}
        for s, ids in draw_ids.items():
            sub = te[np.isin(rid, ids)]
            Zq_t = ang.transform(sub[Q_COLS].to_numpy(float))
            Z8_t = std8.transform(sub[Q_COLS].to_numpy(float))
            mmd[env_name]["quantum"].append(mean_similarity_shift(
                K_ss["quantum"], kernel_exact(Zq_src, fm, Zq_t),
                kernel_exact(Zq_t, fm))["mmd2"])
            mmd[env_name]["rbf8"].append(mean_similarity_shift(
                K_ss["rbf8"], rbf_gram(Z8_src, Z8_t, gamma8),
                rbf_gram(Z8_t, Z8_t, gamma8))["mmd2"])
        log(f"[{world}] sensor {env_name}: done")
    archive = REPO / "results/raw" / f"E04v3_sensor_{world}.json"
    archive.write_text(json.dumps(mmd, indent=1), encoding="utf-8")
    log(f"[{world}] sensor archived: {archive.name} "
        f"sha256={file_sha256(archive)[:16]}...")
    return mmd


def target_phase(world: str, raw, splits, df_a) -> dict:
    """Frozen-model |dAUC| per environment — computed AFTER the sensor
    archive exists."""
    seed = FROZEN["training_protocol"]["init_seed"]
    sv_ids = splits["source_val"]
    d0 = build_environment_dataset(raw, Environment())
    sv = d0[np.isin(d0["row_id"].to_numpy(), sv_ids)]
    models = {}
    for key in V3["targets"]["models"]:
        tier, name = key.split(":")
        params = parse_params(
            FROZEN["hyperparameters"]["tier_a" if tier == "A" else "tier_b"][name])
        cols = features_for(name, Q_COLS, FEATURES_ALL)
        X = df_a[cols].to_numpy(float)
        y, w = df_a["labels"].to_numpy(), df_a["weights"].to_numpy()
        model = (qksvc_builder(params, seed) if name == "qksvc"
                 else build(name, params, seed))
        model.fit(X, y, sample_weight=class_balanced_weights(y, w))
        cal = PlattCalibrator().fit(model.scores(sv[cols].to_numpy(float)),
                                    sv["labels"].to_numpy(),
                                    sv["weights"].to_numpy())
        models[key] = (model, cal, cols)
        log(f"[{world}] trained {key}")

    test_ids = splits["nominal_test"]
    envs = [("nominal", "nominal", Environment())] + new_environments()
    auc: dict[str, dict[str, float]] = {}
    for env_name, _fam, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        y, w = te["labels"].to_numpy(), te["weights"].to_numpy()
        auc[env_name] = {}
        for key, (model, cal, cols) in models.items():
            p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
            auc[env_name][key] = float(weighted_auc(y, p, sample_weight=w))
        log(f"[{world}] targets {env_name}: done")
    return auc


def analyze(mmd: dict, auc: dict) -> dict:
    envs = new_environments()
    fam = {name: f for name, f, _ in envs}
    shift = [n for n, f, _ in envs if f != "weight_only"]
    wo = [n for n, f, _ in envs if f == "weight_only"]
    avg = {e: {k: float(np.mean(v)) for k, v in d.items()}
           for e, d in mmd.items()}
    nom_auc = auc["nominal"]
    delta = {e: {k: abs(auc[e][k] - nom_auc[k]) for k in nom_auc}
             for e in [n for n, _, _ in envs]}

    kernel_targets = {"quantum": "A:qksvc", "rbf8": "A:rbf_svc_8f"}
    out: dict = {"pooled": {}, "per_family": {}, "lofo_magnitude": {},
                 "floor": {}, "blindness": {}}
    families = sorted({fam[e] for e in shift})
    for kern, own in kernel_targets.items():
        for target in (own, "A:xgboost"):
            x = np.array([avg[e][kern] for e in shift])
            y = np.array([delta[e][target] for e in shift])
            rho, p = stats.spearmanr(x, y)
            out["pooled"][f"{kern}->{target}"] = {
                "rho": round(float(rho), 3), "p": round(float(p), 5),
                "n": len(shift)}
            per_fam = {}
            for f in families:
                idx = [i for i, e in enumerate(shift) if fam[e] == f]
                rho_f, p_f = stats.spearmanr(x[idx], y[idx])
                per_fam[f] = {"rho": round(float(rho_f), 3),
                              "p": round(float(p_f), 4), "n": len(idx)}
            out["per_family"][f"{kern}->{target}"] = per_fam
            # LOFO magnitude calibration (isotonic on other families)
            lofo = {}
            for held in families:
                tr = [i for i, e in enumerate(shift) if fam[e] != held]
                va = [i for i, e in enumerate(shift) if fam[e] == held]
                iso = IsotonicRegression(increasing=True,
                                         out_of_bounds="clip").fit(x[tr], y[tr])
                pred = iso.predict(x[va])
                mae = float(np.mean(np.abs(pred - y[va])))
                bias = float(np.mean(pred - y[va]))
                lofo[held] = {"mae": round(mae, 5), "bias": round(bias, 5),
                              "target_mean": round(float(np.mean(y[va])), 5)}
            out["lofo_magnitude"][f"{kern}->{target}"] = lofo

    # floor + blindness (weight-only)
    rng = np.random.default_rng(4242)
    for kern in kernel_targets:
        wo_vals = np.array([[v for v in mmd[e][kern]] for e in wo])  # (12, 3)
        floor_point = float(np.max(wo_vals.mean(axis=1)))
        boots = []
        for _ in range(V3["sensor"]["floor_bootstrap"]):
            env_idx = rng.integers(0, len(wo), size=len(wo))
            draw_idx = rng.integers(0, wo_vals.shape[1], size=(len(wo),
                                                              wo_vals.shape[1]))
            sample = np.take_along_axis(wo_vals[env_idx], draw_idx, axis=1)
            boots.append(float(np.max(sample.mean(axis=1))))
        out["floor"][kern] = {
            "point_max_of_means": round(floor_point, 7),
            "bootstrap_q50": round(float(np.percentile(boots, 50)), 7),
            "bootstrap_q05": round(float(np.percentile(boots, 5)), 7),
            "bootstrap_q95": round(float(np.percentile(boots, 95)), 7),
            "nominal_mmd2": round(float(np.mean(mmd["nominal"][kern])), 7)}
        alarms_point = sorted(e for e in shift if avg[e][kern] > floor_point)
        alarms_q95 = sorted(e for e in shift
                            if avg[e][kern] > out["floor"][kern]["bootstrap_q95"])
        out["floor"][kern]["n_alarms_point"] = len(alarms_point)
        out["floor"][kern]["n_alarms_q95"] = len(alarms_q95)
        # blindness: weight-only MMD^2 indistinguishable from nominal scale
        out["blindness"][kern] = {
            "weight_only_mean": round(float(wo_vals.mean()), 7),
            "weight_only_max_env_mean": round(floor_point, 7),
            "shift_env_median": round(float(np.median(
                [avg[e][kern] for e in shift])), 7)}
    return out


def main() -> int:
    t0 = time.time()
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")
    out: dict = {"experiment": "E04v3", "worlds": {}}
    world_tags = [V3["worlds"]["primary"], V3["worlds"]["secondary"]]
    for world in world_tags:
        raw, splits, ta_seed = load_world(world, loader)
        d0 = build_environment_dataset(raw, Environment())
        train_df = d0[np.isin(d0["row_id"].to_numpy(), splits["train"])]
        df_a = tier_a_frame(train_df,
                            FROZEN["training_protocol"]["tier_a_budget"]["n_train"],
                            ta_seed)
        mmd = sensor_phase(world, raw, splits, df_a)      # archived FIRST
        auc = target_phase(world, raw, splits, df_a)
        analysis = analyze(mmd, auc)
        out["worlds"][world] = {
            "sensor_archive_sha256": file_sha256(
                REPO / "results/raw" / f"E04v3_sensor_{world}.json"),
            "nominal_auc": {k: round(v, 5) for k, v in auc["nominal"].items()},
            "analysis": analysis,
            "mmd2_mean": {e: {k: round(float(np.mean(v)), 7)
                              for k, v in d.items()} for e, d in mmd.items()},
            "abs_delta_auc": {e: {k: round(abs(auc[e][k] - auc["nominal"][k]), 5)
                                  for k in auc[e]}
                              for e in auc if e != "nominal"},
        }
        log(f"[{world}] world complete")

    out["wall_seconds"] = round(time.time() - t0, 1)
    out_path = REPO / "results/tables/E04v3_out_of_grid.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E04v3", config={"E04v3": V3}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E04v3 complete in {out['wall_seconds']} s -> {out_path}")
    for world in world_tags:
        log(f"[{world}] pooled: "
            f"{json.dumps(out['worlds'][world]['analysis']['pooled'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
