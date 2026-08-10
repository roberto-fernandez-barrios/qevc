"""E08 — Physics-level inference (spec §16, §28; H5). Estimator per D-015.

Chain: frozen classifier → signal region → pseudo-experiments under shifted
truth θ → deployment-blind μ̂ (believes nominal expectations) → bias / RMSE /
interval width / empirical coverage. The H5 question: do environments exist
where classifier metrics look fine (|ΔAUC| small) while coverage is damaged?

Outputs: results/tables/E08_physics.json (Fig. 7 data).
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

from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
)
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E08 = yaml.safe_load((REPO / "configs/experiments/E08.yaml").read_text())
E02_RESULTS = json.loads((REPO / "results/tables/E02_landscape.json").read_text())
SCORES_DIR = REPO / "results/raw/E02_scores"

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def env_filename(env_name: str) -> Path:
    return SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz"


def lumi_factors(nominal_test, loader) -> dict[str, float]:
    """Per-process rescale: test-role yields → full 10 fb⁻¹ yields (D-015)."""
    full = loader.process_stats()["weight_sums"]
    got = nominal_test.groupby("detailed_labels", observed=True)["weights"].sum()
    return {proc: full[proc] / float(got[proc]) for proc in got.index}


def rescaled_weights(df, factors) -> np.ndarray:
    w = df["weights"].to_numpy(copy=True)
    dl = df["detailed_labels"].to_numpy()
    for proc, f in factors.items():
        w[dl == proc] *= f
    return w


def choose_sr(p_sv: np.ndarray, y_sv: np.ndarray, w_sv: np.ndarray) -> float:
    """t_SR maximizing s/sqrt(b) on source_val with the b floor (D-015)."""
    qs = np.linspace(0.5, 0.999, E08["signal_region"]["threshold_grid_quantiles"])
    best_t, best_obj = None, -np.inf
    for t in np.unique(np.quantile(p_sv, qs)):
        sel = p_sv >= t
        s = w_sv[sel & (y_sv == 1)].sum()
        b = w_sv[sel & (y_sv == 0)].sum()
        if b < E08["signal_region"]["b_floor"]:
            continue
        obj = s / np.sqrt(b)
        if obj > best_obj:
            best_obj, best_t = obj, float(t)
    if best_t is None:
        raise RuntimeError("no SR threshold satisfies the b floor")
    return best_t


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")

    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    factors = lumi_factors(frames["nominal_test"], loader)
    log(f"lumi rescale factors: { {k: round(v, 2) for k, v in factors.items()} }")

    # Signal regions need source_val probabilities, which the archive does not
    # cover (test role only) — rebuild the frozen models once (deterministic).
    from run_e02 import train_frozen_models  # noqa: PLC0415
    models = train_frozen_models(frames)
    sv_df = frames["source_val"]
    w_sv_resc = rescaled_weights(sv_df, factors)
    y_sv = sv_df["labels"].to_numpy()

    sr: dict[str, float] = {}
    for key in E08["models"]:
        model, cal, _thr, cols = models[key]
        p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
        sr[key] = choose_sr(p_sv, y_sv, w_sv_resc)
        log(f"SR({key}): t={sr[key]:.5f}")

    rng = np.random.default_rng(E08["seed"])
    z = 1.0  # 68.27% Gaussian interval
    test_ids = raw_splits["nominal_test"]
    env_list = [("nominal", Environment())] + environments()
    labels_raw = raw["labels"].to_numpy().astype(int)

    # Nominal expectations (deployment's belief) per model.
    nominal_exp: dict[str, tuple[float, float]] = {}
    out_envs: dict = {}
    for env_name, env in env_list:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(env_filename(env_name))
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        w = rescaled_weights(te, factors)
        y = labels_raw[te["row_id"].to_numpy()]
        out_envs[env_name] = {"models": {}}
        for key in E08["models"]:
            p = npz[key]
            sel = p >= sr[key]
            s_th = float(w[sel & (y == 1)].sum())
            b_th = float(w[sel & (y == 0)].sum())
            if env_name == "nominal":
                nominal_exp[key] = (s_th, b_th)
            s0, b0 = nominal_exp[key]
            per_mu = {}
            for mu in E08["mu_true_grid"]:
                lam = mu * s_th + b_th
                N = rng.poisson(lam, size=E08["pseudo_experiments"])
                mu_hat = (N - b0) / s0
                sigma = np.sqrt(np.maximum(N, 1.0)) / s0
                cover = np.abs(mu_hat - mu) <= z * sigma
                per_mu[str(mu)] = {
                    "bias": round(float(mu_hat.mean() - mu), 4),
                    "rmse": round(float(np.sqrt(((mu_hat - mu) ** 2).mean())), 4),
                    "width": round(float(2 * z * sigma.mean()), 4),
                    "coverage": round(float(cover.mean()), 4),
                }
            cov_mean = float(np.mean([v["coverage"] for v in per_mu.values()]))
            entry = {
                "s_theta": round(s_th, 2), "b_theta": round(b_th, 2),
                "s0": round(s0, 2), "b0": round(b0, 2),
                "per_mu": per_mu, "coverage_mean": round(cov_mean, 4),
            }
            if env_name != "nominal":
                entry["delta_auc"] = E02_RESULTS["environments"][env_name][
                    "delta_auc"][key]
            out_envs[env_name]["models"][key] = entry
        log(f"{env_name}: done")

    # Decoupling scan (SAP §6 / H5) — E02R-gated (Phase 10 finding 4):
    # "classifier flat" requires the 5-seed replication evidence
    # |mean ΔAUC| + std < threshold, never a single-seed point estimate.
    # Seed-replicated environments (soft_met/combo seeds) are deduplicated to
    # unique θ via their base name.
    flat = E08["decoupling"]["delta_auc_flat"]
    dmg = E08["decoupling"]["coverage_damaged_below"]
    e02r = json.loads(
        (REPO / "results/tables/E02R_multiseed.json").read_text())["summary"]
    decoupled, seen_theta = [], set()
    for env_name, v in out_envs.items():
        if env_name == "nominal":
            continue
        base_theta = env_name.split("/")[0]
        for key, m in v["models"].items():
            rep = e02r.get(key, {}).get("delta_auc", {}).get(env_name)
            if rep is None:
                continue  # model not in the replication set -> not gated in
            flat_replicated = abs(rep["mean"]) + rep["std"] < flat
            if flat_replicated and m["coverage_mean"] < dmg:
                decoupled.append({
                    "env": env_name, "theta_unique": base_theta, "model": key,
                    "delta_auc_e02r_mean": rep["mean"],
                    "delta_auc_e02r_std": rep["std"],
                    "coverage_mean": m["coverage_mean"],
                })
                seen_theta.add((base_theta, key))

    out = {
        "experiment": "E08",
        "signal_regions": {k: round(v, 5) for k, v in sr.items()},
        "nominal_expectations": {k: {"s0": round(v[0], 2), "b0": round(v[1], 2)}
                                 for k, v in nominal_exp.items()},
        "decoupled_cells_H5": decoupled,
        "decoupled_unique_theta_model": sorted(
            f"{t}|{k}" for t, k in seen_theta),
        "decoupling_gate": "E02R |mean|+std < flat threshold (finding 4)",
        "environments": out_envs,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E08_physics.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E08", config={"E01": E01, "E08": E08},
        seed=E08["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E08 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"H5 decoupled cells: {len(decoupled)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
