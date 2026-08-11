"""E12 — Fresh confirmatory holdout (registry E12; D-020/D-021).

Post-development confirmatory evidence: with every analysis choice frozen in
configs/frozen/frozen_deployment_v1.yaml (committed before this run), draw a
virgin 300k subset provably disjoint from every previously used parquet row,
build a fresh five-role partition, and replicate ONLY the registered headline
results: nominal contrasts, TES/combo degradations, geometry->degradation,
auditor error control, physics decoupling flagships. The five falsifier arms
are evaluated in-run and written into the output table.

Nothing is tuned, selected, or thresholded on E12 data. Anything that fails
is reported as failed.

Outputs: results/tables/E12_confirmatory.json (+ index archives under
data/processed/used_rows/, split file, score archive, manifest).
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
from sklearn.preprocessing import StandardScaler  # noqa: E402

from qevc.auditing.claims import Claim, Verdict, resolve_claim  # noqa: E402
from qevc.data.fair_universe_loader import FairUniverseLoader  # noqa: E402
from qevc.geometry.descriptors import mean_similarity_shift  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import metric_suite, weighted_auc  # noqa: E402
from qevc.models.classical.suite import build  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.models.quantum.qksvc import qksvc_builder  # noqa: E402
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    features_for,
    get_raw_splits,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.statistics.bootstrap import bootstrap_metric  # noqa: E402
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.systematics.fair_universe import (  # noqa: E402
    DER_COLUMNS,
    PRI_COLUMNS,
    Environment,
)
from qevc.utils.repro import RunManifest, file_sha256  # noqa: E402

E12 = yaml.safe_load((REPO / "configs/experiments/E12.yaml").read_text())
FROZEN = yaml.safe_load((REPO / E12["frozen_source"]).read_text())
E02R = json.loads((REPO / "results/tables/E02R_multiseed.json").read_text())
FEATURES_ALL = PRI_COLUMNS + DER_COLUMNS
SCORES_DIR = REPO / "results/raw/E12_scores"
USED_ROWS = REPO / "data/processed/used_rows"
WEIGHT_ONLY = ("ttbar_scale", "diboson_scale", "bkg_scale")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def parse_params(raw: dict) -> dict:
    """Frozen params keep E01's stringified encoding; identical revival."""
    out = {}
    for k, v in raw.items():
        try:
            out[k] = eval(v, {"__builtins__": {}})  # literals only
        except Exception:
            out[k] = v
    return out


def environments() -> list[tuple[str, Environment]]:
    """Frozen grid (D-020 snapshot) — same expansion logic as E02."""
    eg = FROZEN["environment_grid"]
    envs: list[tuple[str, Environment]] = []
    for nuisance, values in eg["grid"].items():
        for v in values:
            if nuisance == "soft_met":
                for s in eg["env_seeds"]:
                    envs.append((f"soft_met={v}/seed{s}",
                                 Environment(soft_met=v, seed=s)))
            else:
                envs.append((f"{nuisance}={v}", Environment(**{nuisance: v})))
    for i, combo in enumerate(eg["combos"]):
        if "soft_met" in combo:
            for s in eg["env_seeds"]:
                envs.append((f"combo{i}/seed{s}", Environment(**combo, seed=s)))
        else:
            envs.append((f"combo{i}", Environment(**combo)))
    return envs


def rbf_gram(A: np.ndarray, B: np.ndarray, gamma: float) -> np.ndarray:
    aa = (A * A).sum(1)[:, None]
    bb = (B * B).sum(1)[None, :]
    return np.exp(-gamma * np.clip(aa + bb - 2.0 * A @ B.T, 0.0, None))


# ---------------------------------------------------------------------------
# Phase 1 — provably disjoint data
# ---------------------------------------------------------------------------

def draw_disjoint_subset(loader: FairUniverseLoader) -> tuple:
    """Archive historical row usage, draw the E12 subset from the complement,
    and record the disjointness proof."""
    USED_ROWS.mkdir(parents=True, exist_ok=True)

    # (1) Reconstruct THE historical draw (the only one ever made) and verify
    # it against the cached subset parquet that produced every prior result.
    idx101 = loader.stratified_indices(300000, 101)
    cached = loader.cache_dir / "subsets" / "subset_n300000_seed101_renorm.parquet"
    import pandas as pd  # noqa: PLC0415
    df_cached = pd.read_parquet(cached)
    df_rec = loader.load_rows(idx101)
    for col in ("PRI_had_pt", "PRI_met"):
        if not np.allclose(df_rec[col].to_numpy(), df_cached[col].to_numpy()):
            raise RuntimeError(f"seed-101 reconstruction mismatch on {col}")
    if not (df_rec["detailed_labels"].to_numpy()
            == df_cached["detailed_labels"].to_numpy()).all():
        raise RuntimeError("seed-101 reconstruction mismatch on detailed_labels")
    log("seed-101 draw reconstructed and verified against the cached subset")
    np.save(USED_ROWS / "seed101_subset_n300000_indices.npy", idx101)

    # (2) E00 validation row groups (aggregate-only reads, excluded anyway).
    bounds = np.cumsum([0] + [loader._pf.metadata.row_group(g).num_rows
                              for g in range(loader._pf.metadata.num_row_groups)])
    e00_rows = np.concatenate([np.arange(bounds[g], bounds[g + 1])
                               for g in E12["exclusions"]["e00_row_groups"]])
    np.save(USED_ROWS / "e00_validation_rowgroup_indices.npy", e00_rows)

    exclusion = np.union1d(idx101, e00_rows)

    # (3) The fresh draw, from the verified complement.
    sub = loader.load_subset(E12["subset"]["n_total"], E12["subset"]["seed"],
                             renormalize=True, exclude=exclusion,
                             tag=E12["subset"]["tag"])
    tagname = (f"subset_n{E12['subset']['n_total']}_seed{E12['subset']['seed']}"
               f"_renorm_{E12['subset']['tag']}")
    idx12 = np.load(loader.cache_dir / "subsets" / f"{tagname}.indices.npy")
    np.save(USED_ROWS / "e12_subset_n300000_seed121_indices.npy", idx12)

    overlap101 = int(np.intersect1d(idx12, idx101).size)
    overlap_e00 = int(np.intersect1d(idx12, e00_rows).size)
    if overlap101 or overlap_e00:
        raise RuntimeError("E12 draw is NOT disjoint — aborting")
    proof = {
        "seed101_indices_sha256": file_sha256(
            USED_ROWS / "seed101_subset_n300000_indices.npy"),
        "e00_rowgroup_indices_sha256": file_sha256(
            USED_ROWS / "e00_validation_rowgroup_indices.npy"),
        "e12_indices_sha256": file_sha256(
            USED_ROWS / "e12_subset_n300000_seed121_indices.npy"),
        "n_excluded": int(exclusion.size),
        "overlap_with_seed101": overlap101,
        "overlap_with_e00_rowgroups": overlap_e00,
        "seed101_reconstruction_verified": True,
    }
    log(f"E12 subset drawn: n={len(sub)}, excluded {exclusion.size} rows, "
        f"overlaps 0/0")
    return sub, proof


# ---------------------------------------------------------------------------
# Phase 2 — frozen deployment on the fresh partition
# ---------------------------------------------------------------------------

def train_frozen(frames: dict) -> dict[str, tuple]:
    sv_df = frames["source_val"]
    seed = FROZEN["training_protocol"]["init_seed"]
    q_cols = FROZEN["features"]["quantum"]
    df_a = tier_a_frame(frames["train"],
                        FROZEN["training_protocol"]["tier_a_budget"]["n_train"],
                        E12["tier_a_seed"])
    jobs = ([("A", n) for n in E12["models"]["tier_a"]] +
            [("B", n) for n in E12["models"]["tier_b"]])
    models: dict[str, tuple] = {}
    for tier, name in jobs:
        params = parse_params(
            FROZEN["hyperparameters"]["tier_a" if tier == "A" else "tier_b"][name])
        train_df = df_a if tier == "A" else frames["train"]
        cols = features_for(name, q_cols, FEATURES_ALL)
        X = train_df[cols].to_numpy(float)
        y, w = train_df["labels"].to_numpy(), train_df["weights"].to_numpy()
        model = (qksvc_builder(params, seed) if name == "qksvc"
                 else build(name, params, seed))
        model.fit(X, y, sample_weight=class_balanced_weights(y, w))
        s_sv = model.scores(sv_df[cols].to_numpy(float))
        y_sv, w_sv = sv_df["labels"].to_numpy(), sv_df["weights"].to_numpy()
        cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
        p_sv = cal.predict_proba(s_sv)
        thr = ba_optimal_threshold(y_sv, p_sv, w_sv)
        m_s_unw = float(np.mean((p_sv >= thr).astype(int) == y_sv))
        models[f"{tier}:{name}"] = (model, cal, thr, cols, m_s_unw)
        log(f"trained+froze {tier}:{name} (thr {thr:.4f}, M_S {m_s_unw:.4f})")
    return models, df_a


def run_landscape(raw, test_ids, labels_raw, models) -> dict:
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    out: dict = {"nominal": {}, "environments": {}}
    envs = [("nominal", Environment())] + environments()
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        y, w = te["labels"].to_numpy(), te["weights"].to_numpy()
        entry: dict = {"n_events": int(len(te)), "models": {}}
        store: dict[str, np.ndarray] = {"row_id": te["row_id"].to_numpy()}
        for key, (model, cal, thr, cols, _ms) in models.items():
            p = cal.predict_proba(model.scores(te[cols].to_numpy(float)))
            suite = metric_suite(y, p, thr, w)
            entry["models"][key] = {"auc": round(suite["auc"], 5),
                                    "balanced_accuracy": round(suite["balanced_accuracy"], 5)}
            if env_name == "nominal":
                bs = E12["landscape"]["bootstrap_nominal_only"]
                ci = bootstrap_metric(weighted_auc, y, p, w,
                                      n_resamples=bs["n_resamples"], seed=bs["seed"])
                entry["models"][key]["auc_ci95"] = [round(ci.lower, 5), round(ci.upper, 5)]
            store[key] = p.astype(np.float32)
        if E12["landscape"]["save_scores"]:
            np.savez_compressed(
                SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz",
                **store)
        if env_name == "nominal":
            out["nominal"] = entry
        else:
            out["environments"][env_name] = entry
        log(f"landscape {env_name}: n={len(te):,}")
    for env_name, entry in out["environments"].items():
        entry["delta_auc"] = {
            k: round(out["nominal"]["models"][k]["auc"] - m["auc"], 5)
            for k, m in entry["models"].items()}
    return out


# ---------------------------------------------------------------------------
# Phase 3 — geometry sensors (frozen family, auditor_dev draws, D-021)
# ---------------------------------------------------------------------------

def run_geometry(raw, auditor_dev_ids, df_a, landscape) -> dict:
    q_cols = FROZEN["features"]["quantum"]
    qp = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])
    Zq_src = ang.transform(df_a[q_cols].to_numpy(float))
    std8 = StandardScaler().fit(df_a[q_cols].to_numpy(float))
    Z8_src = std8.transform(df_a[q_cols].to_numpy(float))
    r8 = parse_params(FROZEN["hyperparameters"]["tier_a"]["rbf_svc_8f"])
    gamma8 = float(r8["gamma"])
    K_ss = {"quantum": kernel_exact(Zq_src, fm),
            "rbf8": rbf_gram(Z8_src, Z8_src, gamma8)}

    draw_ids = {s: np.sort(np.random.default_rng(s).choice(
                    auditor_dev_ids, size=E12["geometry"]["n_base_rows"],
                    replace=False))
                for s in E12["geometry"]["draw_seeds"]}
    union_ids = np.unique(np.concatenate(list(draw_ids.values())))

    envs = [("nominal", Environment())] + environments()
    mmd: dict[str, dict[str, list[float]]] = {}
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=union_ids)
        row_ids_env = te["row_id"].to_numpy()
        mmd[env_name] = {"quantum": [], "rbf8": []}
        for s, ids in draw_ids.items():
            sub = te[np.isin(row_ids_env, ids)]
            Zq_t = ang.transform(sub[q_cols].to_numpy(float))
            Z8_t = std8.transform(sub[q_cols].to_numpy(float))
            for kern, (Zs, Zt) in {"quantum": (Zq_src, Zq_t),
                                   "rbf8": (Z8_src, Z8_t)}.items():
                if kern == "quantum":
                    Kst = kernel_exact(Zq_src, fm, Zq_t)
                    Ktt = kernel_exact(Zt, fm)
                else:
                    Kst = rbf_gram(Z8_src, Z8_t, gamma8)
                    Ktt = rbf_gram(Zt, Zt, gamma8)
                mmd[env_name][kern].append(
                    mean_similarity_shift(K_ss[kern], Kst, Ktt)["mmd2"])
        log(f"geometry {env_name}: done")

    env_names = [e for e, _ in envs if e != "nominal"]
    shift_envs = [e for e in env_names
                  if not any(e.startswith(p) for p in WEIGHT_ONLY)]
    wo_envs = [e for e in env_names if any(e.startswith(p) for p in WEIGHT_ONLY)]
    avg = {e: {k: float(np.mean(v)) for k, v in d.items()} for e, d in mmd.items()}
    floors = {k: max(avg[e][k] for e in wo_envs) for k in ("quantum", "rbf8")}
    alarm_envs = {k: sorted(e for e in env_names if avg[e][k] > floors[k])
                  for k in ("quantum", "rbf8")}

    deltas = {e: landscape["environments"][e]["delta_auc"] for e in shift_envs}
    rho_table = {}
    for kern in ("quantum", "rbf8"):
        x = [avg[e][kern] for e in shift_envs]
        for target in E12["geometry"]["targets"]:
            y = [abs(deltas[e][target]) for e in shift_envs]
            rho, p = stats.spearmanr(x, y)
            rho_table[f"{kern}->{target}"] = {"rho": round(float(rho), 3),
                                              "p": round(float(p), 4)}
    return {"mmd2_mean_per_env": {e: {k: round(v, 7) for k, v in d.items()}
                                  for e, d in avg.items()},
            "weight_only_floor": {k: round(v, 7) for k, v in floors.items()},
            "i1_alarm_envs": alarm_envs,
            "spearman": rho_table,
            "n_shift_envs": len(shift_envs)}


# ---------------------------------------------------------------------------
# Phase 4 — auditor (frozen E05 v1.1 protocol)
# ---------------------------------------------------------------------------

def run_auditor(labels_raw, models, geometry) -> dict:
    deltas = FROZEN["claims"]["deltas"]
    alpha = FROZEN["claims"]["alpha"]
    n_max, n_seeds = E12["auditor"]["n_max"], E12["auditor"]["audit_seeds"]
    salt = E12["auditor"]["seed_salt"]
    alarms = set(geometry["i1_alarm_envs"]["quantum"])  # as E05 (quantum sensor)

    err = {"false_cert": 0, "false_refute": 0,
           "streams_claim_false": 0, "streams_claim_true": 0}
    per_env: dict = {}
    envs = [("nominal", None)] + [(e, None) for e, _ in environments()]
    for env_name, _ in envs:
        npz = np.load(SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz")
        y_env = labels_raw[npz["row_id"]]
        alarm = env_name in alarms
        per_env[env_name] = {"i1_alarm": bool(alarm), "models": {}}
        for key in E12["auditor"]["models"]:
            _m, _c, thr, _cols, m_s = models[key]
            p = npz[key]
            correct = ((p >= thr).astype(int) == y_env).astype(float)
            m_t = float(correct.mean())
            claims = {}
            for d in deltas:
                tau = m_s - d
                truth = m_t >= tau
                verdicts = {"SUPPORTED": 0, "REFUTED": 0, "UNRESOLVED": 0}
                for s in range(n_seeds):
                    digest = hashlib.sha256(
                        f"{salt}|{env_name}|{key}|{s}".encode()).digest()
                    rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
                    x = correct[rng.integers(0, len(correct), size=n_max)]
                    cs = empirical_bernstein_cs(x, alpha=alpha)
                    res = resolve_claim(Claim("acc", tau), cs, heuristic_alarm=alarm)
                    verdicts[res.verdict.value] += 1
                    if not truth:
                        err["streams_claim_false"] += 1
                        if res.verdict is Verdict.SUPPORTED:
                            err["false_cert"] += 1
                    else:
                        err["streams_claim_true"] += 1
                        if res.verdict is Verdict.REFUTED:
                            err["false_refute"] += 1
                claims[str(d)] = {"truth": bool(truth),
                                  "margin": round(m_t - tau, 5),
                                  "verdicts": verdicts}
            per_env[env_name]["models"][key] = {
                "m_target": round(m_t, 5), "m_source": round(m_s, 5),
                "claims": claims}
        log(f"audited {env_name}")
    fc = err["false_cert"] / err["streams_claim_false"] if err["streams_claim_false"] else None
    fr = err["false_refute"] / err["streams_claim_true"] if err["streams_claim_true"] else None
    return {"error_rates": {"false_certification": fc, "false_refutation": fr, **err,
                            "alpha": alpha},
            "environments": per_env}


# ---------------------------------------------------------------------------
# Phase 5 — physics inference (frozen D-015 estimator)
# ---------------------------------------------------------------------------

def run_physics(raw, frames, test_ids, labels_raw, models, loader, landscape) -> dict:
    pe = FROZEN["physics_estimator"]
    full = loader.process_stats()["weight_sums"]
    got = frames["nominal_test"].groupby("detailed_labels", observed=True)["weights"].sum()
    factors = {proc: full[proc] / float(got[proc]) for proc in got.index}

    def rescaled(df):
        w = df["weights"].to_numpy(copy=True)
        dl = df["detailed_labels"].to_numpy()
        for proc, f in factors.items():
            w[dl == proc] *= f
        return w

    sv_df = frames["source_val"]
    w_sv = rescaled(sv_df)
    y_sv = sv_df["labels"].to_numpy()
    qs = np.linspace(0.5, 0.999, pe["signal_region"]["threshold_grid_quantiles"])
    sr: dict[str, float] = {}
    for key in E12["physics"]["models"]:
        model, cal, _t, cols, _m = models[key]
        p_sv = cal.predict_proba(model.scores(sv_df[cols].to_numpy(float)))
        best_t, best_obj = None, -np.inf
        for t in np.unique(np.quantile(p_sv, qs)):
            sel = p_sv >= t
            s = w_sv[sel & (y_sv == 1)].sum()
            b = w_sv[sel & (y_sv == 0)].sum()
            if b < pe["signal_region"]["b_floor"]:
                continue
            if s / np.sqrt(b) > best_obj:
                best_obj, best_t = s / np.sqrt(b), float(t)
        sr[key] = best_t
        log(f"SR({key}): t={best_t:.5f}")

    rng = np.random.default_rng(E12["physics"]["seed"])
    envs = [("nominal", Environment())] + environments()
    nominal_exp: dict[str, tuple[float, float]] = {}
    out_envs: dict = {}
    for env_name, env in envs:
        te = build_environment_dataset(raw, env, row_ids=test_ids)
        npz = np.load(SCORES_DIR / f"{env_name.replace('/', '_').replace('=', '_')}.npz")
        if not np.array_equal(npz["row_id"], te["row_id"].to_numpy()):
            raise RuntimeError(f"row alignment mismatch in {env_name}")
        w = rescaled(te)
        y = labels_raw[te["row_id"].to_numpy()]
        out_envs[env_name] = {}
        for key in E12["physics"]["models"]:
            p = npz[key]
            sel = p >= sr[key]
            s_th = float(w[sel & (y == 1)].sum())
            b_th = float(w[sel & (y == 0)].sum())
            if env_name == "nominal":
                nominal_exp[key] = (s_th, b_th)
            s0, b0 = nominal_exp[key]
            covs = []
            for mu in pe["mu_true_grid"]:
                N = rng.poisson(mu * s_th + b_th, size=pe["pseudo_experiments"])
                mu_hat = (N - b0) / s0
                sigma = np.sqrt(np.maximum(N, 1.0)) / s0
                covs.append(float(np.mean(np.abs(mu_hat - mu) <= sigma)))
            entry = {"s_theta": round(s_th, 2), "b_theta": round(b_th, 2),
                     "coverage_mean": round(float(np.mean(covs)), 4)}
            if env_name != "nominal":
                entry["delta_auc"] = landscape["environments"][env_name]["delta_auc"][key]
            out_envs[env_name][key] = entry
        log(f"physics {env_name}: done")
    return {"signal_regions": {k: round(v, 5) for k, v in sr.items()},
            "environments": out_envs}


# ---------------------------------------------------------------------------
# Phase 6 — acceptance (the five frozen falsifier arms)
# ---------------------------------------------------------------------------

def evaluate_acceptance(landscape, geometry, auditor, physics) -> dict:
    acc = E12["acceptance"]
    nom = landscape["nominal"]["models"]

    def e02r_paired(model_a: str, model_b: str) -> tuple[float, float]:
        diffs = [E02R["per_seed"][s]["environments"]["nominal"][model_a]["auc"]
                 - E02R["per_seed"][s]["environments"]["nominal"][model_b]["auc"]
                 for s in E02R["per_seed"]]
        return float(np.mean(diffs)), float(np.std(diffs))

    arms: dict = {}
    # (a) nominal contrasts
    d_qk_xgb = nom["A:qksvc"]["auc"] - nom["A:xgboost"]["auc"]
    d_qk_rbf8 = nom["A:qksvc"]["auc"] - nom["A:rbf_svc_8f"]["auc"]
    m_xgb, s_xgb = e02r_paired("A:qksvc", "A:xgboost")
    m_r8, s_r8 = e02r_paired("A:qksvc", "A:rbf_svc_8f")
    k = acc["nominal_contrast_sigma"]
    arms["a_nominal"] = {
        "qk_minus_xgb": round(d_qk_xgb, 5),
        "e02r_qk_minus_xgb": [round(m_xgb, 5), round(s_xgb, 5)],
        "qk_minus_rbf8": round(d_qk_rbf8, 5),
        "e02r_qk_minus_rbf8": [round(m_r8, 5), round(s_r8, 5)],
        "pass": bool(d_qk_xgb <= 0 and abs(d_qk_rbf8 - m_r8) <= k * s_r8),
    }
    # (b) degradation signs
    tes = landscape["environments"]["tes=0.98"]["delta_auc"]["A:qksvc"]
    combo3 = float(np.mean(
        [landscape["environments"][f"combo3/seed{s}"]["delta_auc"]["A:qksvc"]
         for s in FROZEN["environment_grid"]["env_seeds"]]))
    arms["b_degradation"] = {"tes098_delta_qk": tes, "combo3_mean_delta_qk": round(combo3, 5),
                             "pass": bool(tes >= 0 and combo3 >= 0)}
    # (c) sensor
    rq = geometry["spearman"]["quantum->A:qksvc"]["rho"]
    r8_ = geometry["spearman"]["rbf8->A:rbf_svc_8f"]["rho"]
    arms["c_sensor"] = {"quantum_own_rho": rq, "rbf8_own_rho": r8_,
                        "pass": bool(rq > 0 or r8_ > 0)}
    # (d) auditor error control
    er = auditor["error_rates"]
    n_false = er["streams_claim_false"]
    alpha = er["alpha"]
    slack = alpha + 3 * np.sqrt(alpha * (1 - alpha) / n_false) if n_false else None
    arms["d_error_control"] = {
        "false_certification": er["false_certification"],
        "threshold_alpha_plus_3sigma": round(slack, 5) if slack else None,
        "pass": bool(n_false and er["false_certification"] <= slack)}
    # (e) flagship decoupling cells
    cells = []
    ok = True
    for cell in acc["flagship_cells"]:
        env, model = cell["env"], cell["model"]
        d = abs(landscape["environments"][env]["delta_auc"][model])
        cov = physics["environments"][env][model]["coverage_mean"]
        cell_ok = (d < acc["flagship_delta_auc_max"]
                   and cov < acc["flagship_coverage_below"])
        cells.append({"env": env, "model": model, "abs_delta_auc": d,
                      "coverage_mean": cov, "pass": bool(cell_ok)})
        ok = ok and cell_ok
    arms["e_flagship_decoupling"] = {"cells": cells, "pass": bool(ok)}

    arms["all_pass"] = bool(all(v["pass"] for v in arms.values()
                                if isinstance(v, dict) and "pass" in v))
    return arms


def main() -> int:
    t0 = time.time()
    loader = FairUniverseLoader(
        REPO / "data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet",
        REPO / "data/interim/fair_universe")

    raw, proof = draw_disjoint_subset(loader)
    raw_splits = get_raw_splits(REPO, raw, E12["splits"], experiment_tag="E12")
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    labels_raw = raw["labels"].to_numpy().astype(int)
    log(f"partition sizes: { {r: len(v) for r, v in frames.items()} }")

    models, df_a = train_frozen(frames)
    landscape = run_landscape(raw, raw_splits["nominal_test"], labels_raw, models)
    geometry = run_geometry(raw, raw_splits["auditor_dev"], df_a, landscape)
    auditor = run_auditor(labels_raw, models, geometry)
    physics = run_physics(raw, frames, raw_splits["nominal_test"], labels_raw,
                          models, loader, landscape)
    acceptance = evaluate_acceptance(landscape, geometry, auditor, physics)

    out = {
        "experiment": "E12",
        "declared_status": "post-development confirmatory evidence "
                           "(protocol frozen before draw; not preregistration)",
        "disjointness_proof": proof,
        "frozen_source": E12["frozen_source"],
        "landscape": landscape,
        "geometry": geometry,
        "auditor": auditor,
        "physics": physics,
        "acceptance": acceptance,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E12_confirmatory.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E12", config={"E12": E12, "frozen": FROZEN},
        seed=E12["subset"]["seed"],
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E12 complete in {out['wall_seconds']} s -> {out_path}")
    log(f"ACCEPTANCE: {json.dumps({k: v.get('pass') if isinstance(v, dict) else v for k, v in acceptance.items()})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
