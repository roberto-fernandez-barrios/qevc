"""E16 (simulation arm) — When does quantum-kernel estimation uncertainty
change a scientific validity verdict? (registry E16; D-007, D-022)

For each (shots, kernel seed) the ENTIRE deployment is rebuilt under
independently-sampled finite-shot Grams (binomial compute-uncompute law,
independent per matrix): SVC refit, Platt recalibration, threshold refrozen,
environments rescored. The auditor then resolves the frozen claim grid
(unweighted D-014 and weighted D-019 families) with label streams PAIRED to
the ideal deployment's streams, and verdicts are compared to C_ideal by
ideal-margin stratum (far / moderate / near).

Reported per stratum: verdict flip rate vs C_ideal, abstention inflation,
empirical false certification against each deployment's own truth, n*
inflation; plus kernel diagnostics (Frobenius error, effective rank, PSD
violation, nominal AUC shift).

Outputs: results/tables/E16_quantum_uncertainty.json.
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

from sklearn.svm import SVC  # noqa: E402

from qevc.auditing.claims import Claim, Verdict, resolve_claim  # noqa: E402
from qevc.geometry.descriptors import effective_rank, psd_violation, raw_spectrum  # noqa: E402
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import weighted_auc  # noqa: E402
from qevc.models.common import (  # noqa: E402
    PlattCalibrator,
    ba_optimal_threshold,
    class_balanced_weights,
)
from qevc.pipeline.common import (  # noqa: E402
    build_environment_dataset,
    get_raw_splits,
    load_raw_subset,
    tier_a_frame,
)
from qevc.preprocessing.scaling import AngleScaler  # noqa: E402
from qevc.statistics.confidence_sequences import empirical_bernstein_cs  # noqa: E402
from qevc.statistics.weighted import resolve_weighted_claim  # noqa: E402
from qevc.systematics.fair_universe import Environment  # noqa: E402
from qevc.utils.repro import RunManifest  # noqa: E402

E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
E16 = yaml.safe_load((REPO / "configs/experiments/E16.yaml").read_text())
FROZEN = yaml.safe_load((REPO / "configs/frozen/frozen_deployment_v1.yaml").read_text())
E13_RESULTS = json.loads((REPO / "results/tables/E13_weighted_cs.json").read_text())
W_MAX = E13_RESULTS["part_b_benchmark"]["w_max"]["value"]

sys.path.insert(0, str(REPO / "experiments/E02_systematic_landscape"))
from run_e02 import environments, parse_params  # noqa: E402


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def stable_rng(*parts) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def sample_gram(K_exact: np.ndarray, shots: int, rng: np.random.Generator,
                symmetric: bool) -> np.ndarray:
    """Binomial compute-uncompute sampling (D-007), independent entries."""
    est = (rng.binomial(shots, np.clip(K_exact, 0.0, 1.0).astype(np.float64))
           / shots).astype(np.float32)
    if symmetric:
        iu = np.triu_indices_from(est, k=1)
        est.T[iu] = est[iu]
        np.fill_diagonal(est, 1.0)
    return est


def stratum(margin: float) -> str:
    m = abs(margin)
    if m >= E16["margin_strata"]["far"]:
        return "far"
    if m < E16["margin_strata"]["near"]:
        return "near"
    return "moderate"


def audit_deployment(correct_by_env: dict, w_by_env: dict, m_s_unw: float,
                     m_s_w: float, alpha: float) -> dict:
    """Resolve the full claim grid for one deployment. Streams are paired
    across deployments via shared (env, family, delta, seed) stream keys."""
    out = {}
    for env_name, corr in correct_by_env.items():
        w_env = w_by_env[env_name]
        m_t_unw = float(corr.mean())
        m_t_w = float((w_env * corr).sum() / w_env.sum())
        for fam in E16["claims"]["families"]:
            m_s, m_t = ((m_s_unw, m_t_unw) if fam == "unweighted"
                        else (m_s_w, m_t_w))
            for d in E16["claims"]["deltas"]:
                tau = float(np.clip(m_s - d, 0.0, 1.0))
                truth = m_t >= tau
                for s in range(E16["audit_seeds"]):
                    rng = stable_rng(E16["seed_salt"], env_name, fam, d, s)
                    idx = rng.integers(0, len(corr), size=E16["n_max"])
                    if fam == "unweighted":
                        cs = empirical_bernstein_cs(corr[idx], alpha=alpha)
                        res = resolve_claim(Claim("acc", tau), cs)
                    else:
                        res = resolve_weighted_claim(corr[idx], w_env[idx],
                                                     tau, W_MAX, alpha=alpha)
                    out[(env_name, fam, d, s)] = {
                        "verdict": res.verdict.value, "n_star": res.n_star,
                        "truth": truth, "margin": m_t - tau}
    return out


def main() -> int:
    t0 = time.time()
    raw = load_raw_subset(REPO, E01["subset"])
    raw_splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    labels_raw = raw["labels"].to_numpy().astype(int)
    d0 = build_environment_dataset(raw, Environment())
    frames = {r: d0[np.isin(d0["row_id"].to_numpy(), ids)]
              for r, ids in raw_splits.items()}
    df_a = tier_a_frame(frames["train"], E01["tier_a"]["n_train"],
                        E01["tier_a"]["seed"])
    q_cols = FROZEN["features"]["quantum"]
    qp = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    ang = AngleScaler().fit(df_a[q_cols].to_numpy(float))
    fm = build_feature_map(len(q_cols), reps=qp["reps"],
                           entanglement=qp["entanglement"], scale=qp["scale"])

    Z_tr = ang.transform(df_a[q_cols].to_numpy(float))
    y_tr = df_a["labels"].to_numpy()
    wb_tr = class_balanced_weights(y_tr, df_a["weights"].to_numpy())
    sv = frames["source_val"]
    Z_sv = ang.transform(sv[q_cols].to_numpy(float))
    y_sv, w_sv = sv["labels"].to_numpy(), sv["weights"].to_numpy()

    env_map = dict([("nominal", Environment())] + environments())
    env_data = {}
    for env_name in E16["environments"]:
        te = build_environment_dataset(raw, env_map[env_name],
                                       row_ids=raw_splits["nominal_test"])
        env_data[env_name] = {
            "Z": ang.transform(te[q_cols].to_numpy(float)),
            "y": labels_raw[te["row_id"].to_numpy()],
            "w": te["weights"].to_numpy()}
        log(f"env {env_name}: n={len(te)}")

    # exact Grams (computed once; noisy deployments sample from them, D-007).
    # Cross-Grams stored float32: 2000 x 41k float64 would be ~0.7 GB each.
    K_tr = kernel_exact(Z_tr, fm)
    K_sv = kernel_exact(Z_tr, fm, Z_sv).astype(np.float32)
    K_env = {e: kernel_exact(Z_tr, fm, d["Z"]).astype(np.float32)
             for e, d in env_data.items()}
    spec_exact = raw_spectrum(K_tr)
    eff_exact = effective_rank(np.clip(spec_exact[::-1], 0, None))
    log("exact Grams ready")

    alpha = E16["alpha"]

    def build_and_audit(K_tr_d, K_sv_d, K_env_d, tag: str) -> tuple:
        svc = SVC(kernel="precomputed", C=float(qp["C"]))
        svc.fit(K_tr_d, y_tr, sample_weight=wb_tr)
        s_sv = svc.decision_function(K_sv_d.T)
        cal = PlattCalibrator().fit(s_sv, y_sv, w_sv)
        p_sv = cal.predict_proba(s_sv)
        thr = ba_optimal_threshold(y_sv, p_sv, w_sv)
        m_s_unw = float(np.mean((p_sv >= thr).astype(int) == y_sv))
        corr_w = (w_sv * ((p_sv >= thr).astype(int) == y_sv)).sum() / w_sv.sum()
        m_s_w = float(corr_w)
        correct, weights, aucs = {}, {}, {}
        for e, d in env_data.items():
            p = cal.predict_proba(svc.decision_function(K_env_d[e].T))
            correct[e] = ((p >= thr).astype(int) == d["y"]).astype(float)
            weights[e] = d["w"]
            aucs[e] = float(weighted_auc(d["y"], p, sample_weight=d["w"]))
        audit = audit_deployment(correct, weights, m_s_unw, m_s_w, alpha)
        return audit, aucs, {"m_s_unw": m_s_unw, "m_s_w": m_s_w, "thr": thr}

    ideal_audit, ideal_aucs, ideal_refs = build_and_audit(K_tr, K_sv, K_env,
                                                          "ideal")
    log(f"C_ideal done: nominal AUC {ideal_aucs['nominal']:.4f}")

    # stratum of each claim cell, by the IDEAL margin
    cell_stratum = {}
    for (env, fam, d, s), v in ideal_audit.items():
        cell_stratum[(env, fam, d)] = stratum(v["margin"])

    results: dict = {"configs": {}}
    for shots in E16["shots_grid"]:
        for ks in E16["kernel_seeds"]:
            rng = stable_rng(E16["seed_salt"], "kernel", shots, ks)
            K_tr_d = sample_gram(K_tr, shots, rng, symmetric=True)
            K_sv_d = sample_gram(K_sv, shots, rng, symmetric=False)
            K_env_d = {e: sample_gram(K, shots, rng, symmetric=False)
                       for e, K in K_env.items()}
            audit, aucs, refs = build_and_audit(K_tr_d, K_sv_d, K_env_d,
                                                f"s{shots}k{ks}")
            frob = float(np.linalg.norm(K_tr_d - K_tr) / np.linalg.norm(K_tr))
            spec_d = raw_spectrum(K_tr_d)
            entry = {
                "kernel": {
                    "frob_rel_err": round(frob, 5),
                    "eff_rank": round(float(effective_rank(
                        np.clip(spec_d[::-1], 0, None))), 2),
                    "eff_rank_exact": round(float(eff_exact), 2),
                    "psd_violation": round(float(psd_violation(K_tr_d)), 6)},
                "nominal_auc": round(aucs["nominal"], 5),
                "nominal_auc_ideal": round(ideal_aucs["nominal"], 5),
                "m_s_shift_unw": round(refs["m_s_unw"] - ideal_refs["m_s_unw"], 5),
                "m_s_shift_w": round(refs["m_s_w"] - ideal_refs["m_s_w"], 5),
                "strata": {},
            }
            for st in ("far", "moderate", "near"):
                keys = [k for k in audit
                        if cell_stratum[(k[0], k[1], k[2])] == st]
                n = len(keys)
                if n == 0:
                    continue
                flips = sum(audit[k]["verdict"] != ideal_audit[k]["verdict"]
                            for k in keys)
                unres = sum(audit[k]["verdict"] == "UNRESOLVED" for k in keys)
                unres_ideal = sum(ideal_audit[k]["verdict"] == "UNRESOLVED"
                                  for k in keys)
                fc = sum(1 for k in keys
                         if not audit[k]["truth"]
                         and audit[k]["verdict"] == "SUPPORTED")
                nfalse = sum(1 for k in keys if not audit[k]["truth"])
                ratios = [audit[k]["n_star"] / ideal_audit[k]["n_star"]
                          for k in keys
                          if audit[k]["n_star"] and ideal_audit[k]["n_star"]]
                entry["strata"][st] = {
                    "n_cells": n, "flip_rate": round(flips / n, 4),
                    "abstention": round(unres / n, 4),
                    "abstention_ideal": round(unres_ideal / n, 4),
                    "false_cert": fc, "n_claim_false": nfalse,
                    "n_star_ratio_median": (round(float(np.median(ratios)), 3)
                                            if ratios else None)}
            results["configs"][f"shots{shots}|k{ks}"] = entry
            log(f"shots={shots} seed={ks}: frob={frob:.4f} "
                f"flips far/mod/near = "
                f"{[entry['strata'].get(s, {}).get('flip_rate') for s in ('far', 'moderate', 'near')]}")

    # aggregate per shots level
    agg = {}
    for shots in E16["shots_grid"]:
        agg[str(shots)] = {}
        for st in ("far", "moderate", "near"):
            cells = [results["configs"][f"shots{shots}|k{ks}"]["strata"].get(st)
                     for ks in E16["kernel_seeds"]]
            cells = [c for c in cells if c]
            if not cells:
                continue
            agg[str(shots)][st] = {
                "flip_rate_mean": round(float(np.mean(
                    [c["flip_rate"] for c in cells])), 4),
                "abstention_mean": round(float(np.mean(
                    [c["abstention"] for c in cells])), 4),
                "abstention_ideal": cells[0]["abstention_ideal"],
                "false_cert_total": int(sum(c["false_cert"] for c in cells)),
                "n_claim_false_total": int(sum(c["n_claim_false"]
                                               for c in cells))}
    out = {
        "experiment": "E16",
        "arm": "simulation",
        "ideal_refs": {k: round(v, 5) for k, v in ideal_refs.items()},
        "ideal_nominal_auc": round(ideal_aucs["nominal"], 5),
        "stratum_definition": E16["margin_strata"],
        "per_config": results["configs"],
        "aggregate_by_shots": agg,
        "wall_seconds": round(time.time() - t0, 1),
    }
    out_path = REPO / "results/tables/E16_quantum_uncertainty.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    checksums = REPO / "data/raw/fair_universe/CHECKSUMS.txt"
    manifest = RunManifest(
        experiment_id="E16", config={"E16": E16}, seed=0,
        dataset_hashes={"FAIR_Universe_HiggsML_data.parquet": checksums.read_text().split()[0]},
    )
    manifest.finalize(outputs=[str(out_path.relative_to(REPO))])
    manifest.write(REPO / "results/manifests")
    log(f"E16 sim arm complete in {out['wall_seconds']} s -> {out_path}")
    log(json.dumps(agg, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
