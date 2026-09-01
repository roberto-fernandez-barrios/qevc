"""Deterministic stage decomposition of the 30 frozen E16 deployments.

DERIVED / NO NEW RANDOMNESS.  This script does not create a noisy-kernel
realization, seed, sample, model, feature map, hyperparameter, claim,
threshold rule, likelihood, PSD repair or QPU job.  It replays the six frozen
shot budgets and five frozen kernel seeds from E16's stable RNG exactly as
``analyze_e16_psd_sensitivity.py`` does, requires the replayed full deployment
(stage D) to reproduce the archived RAW primary summaries and the archived
minimum-diagonal-loading sensitivity summaries, and then evaluates
*diagnostic counterfactual* intermediate stages of the same realized
deployment:

    A   IDEAL              exact SVC + exact Platt map + exact threshold
    B0  FIT-ONLY           SVC refitted on the realized (noisy) training Gram,
                           evaluated on the EXACT source/target cross-Grams,
                           exact Platt map, exact threshold
    B   MODEL-ONLY         realized decision function (noisy fit AND noisy
                           cross-Grams), exact Platt map, exact threshold
    C   MODEL+CALIBRATION  realized decision function, deployment-specific
                           Platt map, exact (ideal) probability threshold
    D   FULL DEPLOYMENT    realized decision function, deployment-specific
                           Platt map, deployment-specific refrozen threshold
                           (this is the archived pipeline)

Stages B0, B and C are counterfactuals that were never deployed; they are
reported only to locate where the finite-shot perturbation is amplified.
The attribution is sequential and ORDER-DEPENDENT: interventions are applied
in pipeline order (fit -> evaluation -> calibration -> operating threshold)
and a different order could redistribute the increments.  Telescoping is
exact by construction: the sum of the four increments equals the full
deployment movement.

Predeclared classification rule (fixed before the replay was run):

    increments of the source metric M_S (unweighted accuracy, and separately
    nominal-weighted accuracy):
        i_fit = M_S(B0) - M_S(A); i_eval = M_S(B) - M_S(B0);
        i_cal = M_S(C) - M_S(B);  i_thr = M_S(D) - M_S(C).
    metric share of stage k = mean_dep |i_k| / sum_k mean_dep |i_k|.
    far ideal-anchored flip rate f_X at cumulative stage X (f_A = 0):
        flip increment g_k = mean_dep (f_k - f_prev), positive parts only;
    flip share of stage k = g_k^+ / sum_k g_k^+.
    groups: MODEL/RANKING = fit + eval; CALIBRATION = cal; THRESHOLD = thr.
    A group is DOMINANT for a regime and metric family when BOTH its metric
    share and its flip share are >= 0.5.  The regime label is the dominant
    group when the unweighted and weighted families agree, otherwise MIXED.
    NOT IDENTIFIABLE if stage D fails to reproduce the archived endpoints, if
    a Platt slope is non-positive, or if any stage quantity is undefined.

Outputs:
  results/tables/E16_stage_decomposition.json
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import kendalltau, spearmanr
from sklearn.svm import SVC


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "E02_systematic_landscape"))
sys.path.insert(0, str(ROOT / "scripts"))

from qevc.geometry.descriptors import effective_rank  # noqa: E402
from qevc.kernels.psd import (  # noqa: E402
    DEFAULT_EPSILON_REL,
    minimum_diagonal_loading,
)
from qevc.kernels.quantum import build_feature_map, kernel_exact  # noqa: E402
from qevc.metrics.classifier import weighted_auc, weighted_balanced_accuracy  # noqa: E402
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
from qevc.systematics.fair_universe import Environment  # noqa: E402

from run_e02 import environments, parse_params  # noqa: E402

import analyze_e16_psd_sensitivity as psd  # noqa: E402


PRIMARY = ROOT / "results" / "tables" / "E16_quantum_uncertainty.json"
PSD_SENSITIVITY = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
PROP3_INSTANTIATION = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
OUTPUT = ROOT / "results" / "tables" / "E16_stage_decomposition.json"
E01_PATH = ROOT / "configs" / "experiments" / "E01.yaml"
E16_PATH = ROOT / "configs" / "experiments" / "E16.yaml"
FROZEN_PATH = ROOT / "configs" / "frozen" / "frozen_deployment_v1.yaml"
E16_MODULE_PATH = ROOT / "experiments" / "E16_quantum_uncertainty" / "run_e16.py"
E13_RESULTS_PATH = ROOT / "results" / "tables" / "E13_weighted_cs.json"

STAGES = ("A", "B0", "B", "C", "D")
INCREMENTS = (("fit", "A", "B0"), ("eval", "B0", "B"), ("cal", "B", "C"), ("thr", "C", "D"))
GROUPS = {
    "MODEL/RANKING": ("fit", "eval"),
    "CALIBRATION": ("cal",),
    "THRESHOLD": ("thr",),
}
STRATA = ("far", "moderate", "near")
DOMINANCE_SHARE = 0.5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def rounded(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def summary_stats(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "n": int(array.size),
        "mean": rounded(array.mean()),
        "median": rounded(np.median(array)),
        "q25": rounded(np.percentile(array, 25)),
        "q75": rounded(np.percentile(array, 75)),
        "min": rounded(array.min()),
        "max": rounded(array.max()),
    }


def rank_stability(reference: np.ndarray, realized: np.ndarray) -> dict:
    spearman = spearmanr(reference, realized).statistic
    kendall = kendalltau(reference, realized).statistic
    return {"spearman": rounded(spearman, 6), "kendall_tau_b": rounded(kendall, 6)}


def main() -> int:
    start = time.time()
    e16 = psd.load_e16_module()
    e01_cfg = yaml.safe_load(E01_PATH.read_text(encoding="utf-8"))
    e16_cfg = yaml.safe_load(E16_PATH.read_text(encoding="utf-8"))
    frozen = yaml.safe_load(FROZEN_PATH.read_text(encoding="utf-8"))
    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
    psd_archive = json.loads(PSD_SENSITIVITY.read_text(encoding="utf-8"))
    prop3 = json.loads(PROP3_INSTANTIATION.read_text(encoding="utf-8"))
    alpha = float(e16_cfg["alpha"])

    input_paths = {
        "primary_e16": PRIMARY,
        "psd_sensitivity": PSD_SENSITIVITY,
        "proposition3_instantiation": PROP3_INSTANTIATION,
        "e01_config": E01_PATH,
        "e16_config": E16_PATH,
        "frozen_deployment": FROZEN_PATH,
        "frozen_e16_runner": E16_MODULE_PATH,
        "weighted_cs_results": E13_RESULTS_PATH,
        "psd_sensitivity_script": ROOT / "scripts" / "analyze_e16_psd_sensitivity.py",
        "stage_decomposition_script": Path(__file__).resolve(),
    }
    input_hashes = {name: sha256(path) for name, path in input_paths.items()}
    protected_paths = [
        ROOT / "results" / "tables" / name
        for name in (
            "E16_quantum_uncertainty.json",
            "E16_deployment_level.json",
            "E16_hw.json",
            "E16_psd_sensitivity.json",
            "E16_proposition4_instantiation.json",
            "E16_proposition4_deployment_summary.json",
            "E20_offline_gate.json",
            "E11_cms_case_study.json",
            "E11v2_cms_full.json",
            "E11v3_cms_stats.json",
        )
    ]
    protected_before = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in protected_paths
    }

    # Prop-3 case lookup: (deployment, regime, env, family, delta) -> (dM_S, dM_T)
    prop3_lookup = {}
    for case in prop3["cases"]:
        if case["claim_semantics"] != "deployment_relative":
            continue
        prop3_lookup[(
            case["deployment_id"], case["regime"], case["environment"],
            case["metric_family"], float(case["delta"]),
        )] = (float(case["delta_M_S"]), float(case["delta_M_T"]))

    # ---- frozen inputs, identical to the PSD replay ------------------------
    raw = load_raw_subset(ROOT, e01_cfg["subset"])
    raw_splits = get_raw_splits(ROOT, raw, e01_cfg["splits"], experiment_tag="E01")
    labels_raw = raw["labels"].to_numpy().astype(int)
    nominal = build_environment_dataset(raw, Environment())
    frames = {
        role: nominal[np.isin(nominal["row_id"].to_numpy(), ids)]
        for role, ids in raw_splits.items()
    }
    train = tier_a_frame(frames["train"], e01_cfg["tier_a"]["n_train"], e01_cfg["tier_a"]["seed"])
    columns = frozen["features"]["quantum"]
    params = parse_params(frozen["hyperparameters"]["tier_a"]["qksvc"])
    scaler = AngleScaler().fit(train[columns].to_numpy(float))
    feature_map = build_feature_map(
        len(columns), reps=params["reps"], entanglement=params["entanglement"],
        scale=params["scale"],
    )
    Z_train = scaler.transform(train[columns].to_numpy(float))
    y_train = train["labels"].to_numpy()
    training_weights = class_balanced_weights(y_train, train["weights"].to_numpy())
    source = frames["source_val"]
    Z_source = scaler.transform(source[columns].to_numpy(float))
    y_source = source["labels"].to_numpy()
    w_source = source["weights"].to_numpy()

    environment_map = dict([("nominal", Environment())] + environments())
    environment_data = {}
    for name in e16_cfg["environments"]:
        frame = build_environment_dataset(raw, environment_map[name], row_ids=raw_splits["nominal_test"])
        environment_data[name] = {
            "Z": scaler.transform(frame[columns].to_numpy(float)),
            "y": labels_raw[frame["row_id"].to_numpy()],
            "w": frame["weights"].to_numpy(),
        }
        log(f"prepared environment {name}: n={len(frame)}")

    K_train_exact = kernel_exact(Z_train, feature_map)
    K_source_exact = kernel_exact(Z_train, feature_map, Z_source).astype(np.float32)
    K_environment_exact = {
        name: kernel_exact(Z_train, feature_map, data["Z"]).astype(np.float32)
        for name, data in environment_data.items()
    }
    exact_effective_rank = effective_rank(K_train_exact)
    log("exact reference blocks reconstructed")

    def fit_svc(K_fit: np.ndarray) -> SVC:
        svc = SVC(kernel="precomputed", C=float(params["C"]))
        svc.fit(K_fit, y_train, sample_weight=training_weights)
        return svc

    def scores_of(svc: SVC, K_source: np.ndarray, K_environment: dict) -> tuple[np.ndarray, dict]:
        return (
            svc.decision_function(K_source.T),
            {name: svc.decision_function(K_environment[name].T) for name in environment_data},
        )

    def platt_slope(calibrator: PlattCalibrator) -> float:
        return float(calibrator._lr.coef_[0][0])

    def evaluate(
        source_scores: np.ndarray,
        env_scores: dict,
        calibrator: PlattCalibrator,
        threshold: float,
        fixed_refs: dict | None,
    ) -> dict:
        """Metrics, exact targets and (own/fixed) audits for one stage."""
        source_prob = calibrator.predict_proba(source_scores)
        source_pred = (source_prob >= threshold).astype(int)
        source_correct = (source_pred == y_source).astype(float)
        refs = {
            "m_s_unw": float(np.mean(source_correct)),
            "m_s_w": float(np.average(source_correct, weights=w_source)),
            "thr": float(threshold),
        }
        source_ba = float(weighted_balanced_accuracy(y_source, source_pred, w_source))
        targets, targets_exact, correct, weights = {}, {}, {}, {}
        for name, data in environment_data.items():
            probability = calibrator.predict_proba(env_scores[name])
            prediction = (probability >= threshold).astype(int)
            corr = (prediction == data["y"]).astype(float)
            correct[name] = corr
            weights[name] = data["w"]
            targets_exact[name] = {
                "auc": float(weighted_auc(data["y"], probability, data["w"])),
                "balanced_accuracy": float(weighted_balanced_accuracy(data["y"], prediction, data["w"])),
                "metric_unweighted_accuracy": float(corr.mean()),
                "metric_weighted_accuracy": float(np.average(corr, weights=data["w"])),
            }
            targets[name] = {metric: rounded(value) for metric, value in targets_exact[name].items()}
        audit_own = e16.audit_deployment(correct, weights, refs["m_s_unw"], refs["m_s_w"], alpha)
        audit_fixed = None
        if fixed_refs is not None:
            audit_fixed = e16.audit_deployment(
                correct, weights, fixed_refs["m_s_unw"], fixed_refs["m_s_w"], alpha
            )
        return {
            "audit_own": audit_own,
            "audit_fixed": audit_fixed,
            "refs": refs,
            "source_balanced_accuracy": source_ba,
            "targets": targets,
            "targets_exact": targets_exact,
        }

    # ---- ideal deployment (stage A) ----------------------------------------
    svc_ideal = fit_svc(K_train_exact)
    ideal_source_scores, ideal_env_scores = scores_of(svc_ideal, K_source_exact, K_environment_exact)
    cal_ideal = PlattCalibrator().fit(ideal_source_scores, y_source, w_source)
    thr_ideal = ba_optimal_threshold(y_source, cal_ideal.predict_proba(ideal_source_scores), w_source)
    ideal = evaluate(ideal_source_scores, ideal_env_scores, cal_ideal, thr_ideal, None)
    ideal["audit_fixed"] = ideal["audit_own"]
    ideal_audit = ideal["audit_own"]
    ideal_refs = ideal["refs"]
    cell_stratum = {
        (key[0], key[1], key[2]): e16.stratum(value["margin"]) for key, value in ideal_audit.items()
    }
    ideal_platt_slope = platt_slope(cal_ideal)
    log(
        f"ideal deployment: thr={thr_ideal:.6f} M_S_unw={ideal_refs['m_s_unw']:.5f} "
        f"BA_w={ideal['source_balanced_accuracy']:.5f} AUC={ideal['targets']['nominal']['auc']:.5f}"
    )

    base_cells = sorted({(key[0], key[1], key[2]) for key in ideal_audit})

    def stage_record(result: dict, stage: str, extra: dict | None = None) -> dict:
        """Serializable per-stage record with movements relative to the ideal."""
        movements = {}
        truth_changes = {"ideal_anchored": 0, "deployment_relative": 0}
        for environment, family, delta in base_cells:
            source_key = "m_s_unw" if family == "unweighted" else "m_s_w"
            target_key = (
                "metric_unweighted_accuracy" if family == "unweighted" else "metric_weighted_accuracy"
            )
            d_s = result["refs"][source_key] - ideal_refs[source_key]
            d_t = (
                result["targets_exact"][environment][target_key]
                - ideal["targets_exact"][environment][target_key]
            )
            movements.setdefault(environment, {})[family] = {
                "delta_M_S": d_s,
                "delta_M_T": d_t,
                "delta_M_T_minus_delta_M_S": d_t - d_s,
            }
            ideal_tau = float(np.clip(ideal_refs[source_key] - delta, 0.0, 1.0))
            stage_tau = float(np.clip(result["refs"][source_key] - delta, 0.0, 1.0))
            ideal_truth = ideal["targets_exact"][environment][target_key] >= ideal_tau
            anchored_truth = result["targets_exact"][environment][target_key] >= ideal_tau
            relative_truth = result["targets_exact"][environment][target_key] >= stage_tau
            truth_changes["ideal_anchored"] += int(anchored_truth != ideal_truth)
            truth_changes["deployment_relative"] += int(relative_truth != ideal_truth)
        claims = {
            stratum: {
                "deployment_relative": psd.verdict_summary(
                    result["audit_own"], ideal_audit, cell_stratum, stratum
                ),
                "ideal_anchored": psd.verdict_summary(
                    result["audit_fixed"], ideal_audit, cell_stratum, stratum
                ),
            }
            for stratum in STRATA
        }
        record = {
            "stage": stage,
            "threshold": result["refs"]["thr"],
            "source": {
                "unweighted_accuracy": result["refs"]["m_s_unw"],
                "weighted_accuracy": result["refs"]["m_s_w"],
                "weighted_balanced_accuracy": result["source_balanced_accuracy"],
            },
            "targets": result["targets"],
            "movements_vs_ideal": movements,
            "truth_sign_changes_vs_ideal_over_60_cells": truth_changes,
            "claims": claims,
        }
        if extra:
            record.update(extra)
        return record

    per_deployment = {}
    reproduction = {
        "raw_stage_D_matches_primary_per_config": {},
        "raw_stage_D_matches_psd_archive_payload": {},
        "psd_stage_D_matches_psd_archive_payload": {},
        "prop3_movement_max_abs_residual": {"raw": 0.0, "psd_repaired": 0.0},
        "prop3_movement_cells_compared": {"raw": 0, "psd_repaired": 0},
        "platt_slopes_positive": True,
    }

    for shots in e16_cfg["shots_grid"]:
        for kernel_seed in e16_cfg["kernel_seeds"]:
            key = f"shots{shots}|k{kernel_seed}"
            rng = e16.stable_rng(e16_cfg["seed_salt"], "kernel", shots, kernel_seed)
            K_train_raw = e16.sample_gram(K_train_exact, shots, rng, symmetric=True)
            K_source_raw = e16.sample_gram(K_source_exact, shots, rng, symmetric=False)
            K_environment_raw = {
                name: e16.sample_gram(K, shots, rng, symmetric=False)
                for name, K in K_environment_exact.items()
            }
            repair = minimum_diagonal_loading(K_train_raw, epsilon_relative=DEFAULT_EPSILON_REL)
            entry = {"shot_budget": int(shots), "kernel_seed": int(kernel_seed)}

            for regime, K_fit in (("raw", K_train_raw), ("psd_repaired", repair.matrix)):
                svc = fit_svc(K_fit)
                # B0: noisy fit, exact evaluation blocks.
                b0_source_scores, b0_env_scores = scores_of(svc, K_source_exact, K_environment_exact)
                # B/C/D: realized decision function (noisy fit + noisy cross-Grams).
                real_source_scores, real_env_scores = scores_of(svc, K_source_raw, K_environment_raw)
                cal_real = PlattCalibrator().fit(real_source_scores, y_source, w_source)
                thr_real = ba_optimal_threshold(
                    y_source, cal_real.predict_proba(real_source_scores), w_source
                )
                slope_real = platt_slope(cal_real)
                if not (ideal_platt_slope > 0 and slope_real > 0):
                    reproduction["platt_slopes_positive"] = False

                stage_results = {
                    "B0": evaluate(b0_source_scores, b0_env_scores, cal_ideal, thr_ideal, ideal_refs),
                    "B": evaluate(real_source_scores, real_env_scores, cal_ideal, thr_ideal, ideal_refs),
                    "C": evaluate(real_source_scores, real_env_scores, cal_real, thr_ideal, ideal_refs),
                    "D": evaluate(real_source_scores, real_env_scores, cal_real, thr_real, ideal_refs),
                }

                # ---- F1: stage D must reproduce the archived endpoints exactly.
                d_payload = psd.deployment_payload(stage_results["D"], ideal_audit, cell_stratum)
                archived_payload = psd_archive["per_deployment"][key][regime]
                payload_match = d_payload == archived_payload
                if regime == "raw":
                    observed_primary = psd.primary_projection(
                        e16, K_train_raw, K_train_exact, exact_effective_rank,
                        stage_results["D"], ideal, ideal_audit, cell_stratum,
                    )
                    primary_match = observed_primary == primary["per_config"][key]
                    reproduction["raw_stage_D_matches_primary_per_config"][key] = primary_match
                    reproduction["raw_stage_D_matches_psd_archive_payload"][key] = payload_match
                    if not (primary_match and payload_match):
                        raise RuntimeError(f"F1: raw stage-D replay mismatch for {key}")
                else:
                    reproduction["psd_stage_D_matches_psd_archive_payload"][key] = payload_match
                    if not payload_match:
                        raise RuntimeError(f"F1: PSD stage-D replay mismatch for {key}")

                # ---- Prop-3 movement cross-check against the frozen instantiation.
                for environment, family, delta in base_cells:
                    archived_ds, archived_dt = prop3_lookup[(key, regime, environment, family, delta)]
                    source_key = "m_s_unw" if family == "unweighted" else "m_s_w"
                    target_key = (
                        "metric_unweighted_accuracy" if family == "unweighted"
                        else "metric_weighted_accuracy"
                    )
                    d_s = stage_results["D"]["refs"][source_key] - ideal_refs[source_key]
                    d_t = (
                        stage_results["D"]["targets_exact"][environment][target_key]
                        - ideal["targets_exact"][environment][target_key]
                    )
                    residual = max(abs(d_s - archived_ds), abs(d_t - archived_dt))
                    reproduction["prop3_movement_max_abs_residual"][regime] = max(
                        reproduction["prop3_movement_max_abs_residual"][regime], residual
                    )
                    reproduction["prop3_movement_cells_compared"][regime] += 1
                    if residual > 1e-12:
                        raise RuntimeError(f"F1: Proposition-3 movement mismatch for {key}/{regime}")

                ranking = {
                    "B0_vs_ideal": {
                        "source_val": rank_stability(ideal_source_scores, b0_source_scores),
                        **{
                            name: rank_stability(ideal_env_scores[name], b0_env_scores[name])
                            for name in environment_data
                        },
                    },
                    "B_vs_ideal": {
                        "source_val": rank_stability(ideal_source_scores, real_source_scores),
                        **{
                            name: rank_stability(ideal_env_scores[name], real_env_scores[name])
                            for name in environment_data
                        },
                    },
                }
                stages = {
                    stage: stage_record(result, stage)
                    for stage, result in stage_results.items()
                }
                # telescoping increments of the source metrics
                path = {"A": ideal, **stage_results}
                increments = {}
                for family_key in ("m_s_unw", "m_s_w"):
                    incs = {
                        name: path[right]["refs"][family_key] - path[left]["refs"][family_key]
                        for name, left, right in INCREMENTS
                    }
                    total = path["D"]["refs"][family_key] - path["A"]["refs"][family_key]
                    incs["total_delta_M_S"] = total
                    incs["telescoping_residual"] = total - sum(
                        incs[name] for name, _, _ in INCREMENTS
                    )
                    increments[family_key] = incs
                ba_path = {
                    stage: path[stage]["source_balanced_accuracy"] for stage in STAGES
                }
                entry[regime] = {
                    "platt_slope_realized": slope_real,
                    "ranking_stability": ranking,
                    "stages": stages,
                    "source_metric_increments": increments,
                    "source_weighted_balanced_accuracy_by_stage": ba_path,
                    "reproduction": {
                        "stage_D_matches_archived_payload": payload_match,
                    },
                }
                log(
                    f"{key}/{regime}: dM_S(unw) B0={increments['m_s_unw']['fit']:+.4f} "
                    f"B={increments['m_s_unw']['eval']:+.4f} C={increments['m_s_unw']['cal']:+.4f} "
                    f"D={increments['m_s_unw']['thr']:+.4f} | far ideal flips "
                    + "/".join(
                        f"{stages[s]['claims']['far']['ideal_anchored']['flip_rate_vs_ideal']:.3f}"
                        for s in ("B0", "B", "C", "D")
                    )
                    + f" | rho_src={ranking['B_vs_ideal']['source_val']['spearman']:.4f}"
                )
            per_deployment[key] = entry

    # ---- aggregation and predeclared classification ------------------------
    ideal_record = stage_record(ideal, "A")

    def deployments_in(regime: str):
        return [(key, entry[regime]) for key, entry in per_deployment.items()]

    aggregate = {}
    classification = {"rule": {
        "dominance_share": DOMINANCE_SHARE,
        "metric_share": "mean over deployments of |increment| divided by the sum over increments",
        "flip_share": "positive part of the mean far ideal-anchored flip-rate increment divided by the sum of positive parts",
        "groups": {group: list(names) for group, names in GROUPS.items()},
        "label_rule": "a group dominates a regime and metric family when both shares are >= 0.5; "
                      "the regime label requires the unweighted and weighted families to agree, else MIXED; "
                      "NOT IDENTIFIABLE if stage D does not reproduce the archived endpoints, a Platt "
                      "slope is non-positive, or any stage quantity is undefined",
    }, "by_regime": {}}

    for regime in ("raw", "psd_repaired"):
        rows = deployments_in(regime)
        by_stage = {}
        for stage in ("B0", "B", "C", "D"):
            recs = [entry["stages"][stage] for _, entry in rows]
            by_stage[stage] = {
                "delta_M_S_unweighted": summary_stats(
                    [r["source"]["unweighted_accuracy"] - ideal_refs["m_s_unw"] for r in recs]
                ),
                "abs_delta_M_S_unweighted": summary_stats(
                    [abs(r["source"]["unweighted_accuracy"] - ideal_refs["m_s_unw"]) for r in recs]
                ),
                "delta_M_S_weighted": summary_stats(
                    [r["source"]["weighted_accuracy"] - ideal_refs["m_s_w"] for r in recs]
                ),
                "delta_source_weighted_balanced_accuracy": summary_stats(
                    [
                        r["source"]["weighted_balanced_accuracy"]
                        - ideal["source_balanced_accuracy"]
                        for r in recs
                    ]
                ),
                "abs_delta_source_weighted_balanced_accuracy": summary_stats(
                    [
                        abs(r["source"]["weighted_balanced_accuracy"]
                            - ideal["source_balanced_accuracy"])
                        for r in recs
                    ]
                ),
                "delta_nominal_auc": summary_stats(
                    [r["targets"]["nominal"]["auc"] - ideal["targets"]["nominal"]["auc"] for r in recs]
                ),
                "threshold": summary_stats([r["threshold"] for r in recs]),
                "truth_sign_changes_ideal_anchored": summary_stats(
                    [r["truth_sign_changes_vs_ideal_over_60_cells"]["ideal_anchored"] for r in recs]
                ),
                "truth_sign_changes_deployment_relative": summary_stats(
                    [r["truth_sign_changes_vs_ideal_over_60_cells"]["deployment_relative"] for r in recs]
                ),
                **{
                    f"{stratum}_{semantics}_flip_rate": summary_stats(
                        [r["claims"][stratum][semantics]["flip_rate_vs_ideal"] for r in recs]
                    )
                    for stratum in STRATA
                    for semantics in ("ideal_anchored", "deployment_relative")
                },
            }
        # increments
        increment_summary = {}
        shares = {}
        for family_key in ("m_s_unw", "m_s_w"):
            means = {
                name: float(np.mean([abs(entry["source_metric_increments"][family_key][name]) for _, entry in rows]))
                for name, _, _ in INCREMENTS
            }
            total = sum(means.values())
            increment_summary[family_key] = {
                name: {
                    "signed": summary_stats([entry["source_metric_increments"][family_key][name] for _, entry in rows]),
                    "absolute": summary_stats([abs(entry["source_metric_increments"][family_key][name]) for _, entry in rows]),
                    "share_of_mean_absolute_increment": rounded(means[name] / total) if total else None,
                }
                for name, _, _ in INCREMENTS
            }
            increment_summary[family_key]["max_abs_telescoping_residual"] = rounded(
                max(abs(entry["source_metric_increments"][family_key]["telescoping_residual"]) for _, entry in rows), 15
            )
            shares[family_key] = {
                group: rounded(sum(means[name] for name in names) / total) if total else None
                for group, names in GROUPS.items()
            }
        # far ideal-anchored flip increments along the cumulative path
        flip_path = {}
        for stratum in STRATA:
            prev = 0.0
            incs = {}
            cumulative = {}
            for name, _, right in INCREMENTS:
                mean_rate = float(np.mean([
                    entry["stages"][right]["claims"][stratum]["ideal_anchored"]["flip_rate_vs_ideal"]
                    for _, entry in rows
                ]))
                cumulative[right] = rounded(mean_rate)
                incs[name] = rounded(mean_rate - prev)
                prev = mean_rate
            positive = {name: max(value, 0.0) for name, value in incs.items()}
            pos_total = sum(positive.values())
            flip_path[stratum] = {
                "cumulative_mean_flip_rate_by_stage": cumulative,
                "signed_increment": incs,
                "positive_share": {
                    group: rounded(sum(positive[name] for name in names) / pos_total) if pos_total else None
                    for group, names in GROUPS.items()
                },
            }
        # common-mode statistics at stage D and at each stage
        common_mode = {}
        for stage in ("B0", "B", "C", "D"):
            for family in ("unweighted", "weighted"):
                dts, dss, diffs = [], [], []
                for _, entry in rows:
                    for environment, movement in entry["stages"][stage]["movements_vs_ideal"].items():
                        dts.append(abs(movement[family]["delta_M_T"]))
                        dss.append(abs(movement[family]["delta_M_S"]))
                        diffs.append(abs(movement[family]["delta_M_T_minus_delta_M_S"]))
                common_mode[f"{stage}|{family}"] = {
                    "abs_delta_M_T": summary_stats(dts),
                    "abs_delta_M_S": summary_stats(dss),
                    "abs_delta_M_T_minus_delta_M_S": summary_stats(diffs),
                    "median_ratio_diff_over_abs_delta_M_T": rounded(
                        float(np.median([d / t if t > 0 else 0.0 for d, t in zip(diffs, dts)]))
                    ),
                }
        # ranking stability
        ranking_summary = {
            comparison: {
                block: {
                    stat: summary_stats([entry["ranking_stability"][comparison][block][stat] for _, entry in rows])
                    for stat in ("spearman", "kendall_tau_b")
                }
                for block in ("source_val", *environment_data)
            }
            for comparison in ("B0_vs_ideal", "B_vs_ideal")
        }
        # BA_w versus accuracy at stage D
        ba_vs_acc = {
            "abs_delta_source_weighted_balanced_accuracy_D": summary_stats(
                [abs(entry["stages"]["D"]["source"]["weighted_balanced_accuracy"] - ideal["source_balanced_accuracy"]) for _, entry in rows]
            ),
            "abs_delta_source_unweighted_accuracy_D": summary_stats(
                [abs(entry["stages"]["D"]["source"]["unweighted_accuracy"] - ideal_refs["m_s_unw"]) for _, entry in rows]
            ),
            "abs_delta_source_weighted_accuracy_D": summary_stats(
                [abs(entry["stages"]["D"]["source"]["weighted_accuracy"] - ideal_refs["m_s_w"]) for _, entry in rows]
            ),
            "deployments_with_abs_delta_BA_w_below_abs_delta_unweighted_accuracy": int(sum(
                abs(entry["stages"]["D"]["source"]["weighted_balanced_accuracy"] - ideal["source_balanced_accuracy"])
                < abs(entry["stages"]["D"]["source"]["unweighted_accuracy"] - ideal_refs["m_s_unw"])
                for _, entry in rows
            )),
        }
        aggregate[regime] = {
            "n_deployments": len(rows),
            "by_stage": by_stage,
            "source_metric_increments": increment_summary,
            "group_metric_shares": shares,
            "ideal_anchored_flip_path": flip_path,
            "common_mode": common_mode,
            "ranking_stability": ranking_summary,
            "balanced_accuracy_vs_accuracy": ba_vs_acc,
        }

        # ---- predeclared classification -----------------------------------
        family_labels = {}
        for family_key in ("m_s_unw", "m_s_w"):
            metric_share = shares[family_key]
            flip_share = flip_path["far"]["positive_share"]
            dominant = [
                group for group in GROUPS
                if metric_share[group] is not None and flip_share[group] is not None
                and metric_share[group] >= DOMINANCE_SHARE and flip_share[group] >= DOMINANCE_SHARE
            ]
            family_labels[family_key] = {
                "metric_share": metric_share,
                "far_flip_share": flip_share,
                "dominant_group": dominant[0] if len(dominant) == 1 else None,
            }
        labels = {family_labels[k]["dominant_group"] for k in family_labels}
        reproduced = (
            all(reproduction["raw_stage_D_matches_primary_per_config"].values())
            and all(reproduction["raw_stage_D_matches_psd_archive_payload"].values())
            and all(reproduction["psd_stage_D_matches_psd_archive_payload"].values())
            and reproduction["platt_slopes_positive"]
        )
        if not reproduced:
            label = "NOT IDENTIFIABLE FROM THE FROZEN REPLAY"
        elif len(labels) == 1 and None not in labels:
            label = f"{labels.pop()}-DOMINATED"
        else:
            label = "MIXED"
        classification["by_regime"][regime] = {"families": family_labels, "label": label}

    regime_labels = {classification["by_regime"][r]["label"] for r in ("raw", "psd_repaired")}
    classification["overall"] = regime_labels.pop() if len(regime_labels) == 1 else "MIXED"

    protected_after = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in protected_paths
    }
    if protected_before != protected_after:
        raise RuntimeError("a protected artifact changed during the derived analysis")

    output = {
        "analysis": "E16 deterministic stage decomposition (diagnostic counterfactual replay)",
        "status": "DERIVED / NO NEW RANDOMNESS",
        "unit_of_analysis": (
            "one deterministically replayed frozen noisy-kernel deployment (30 RAW and the 30 "
            "corresponding minimum-diagonal-loading sensitivity deployments); stages within a "
            "deployment share its Gram realization, roles, claim grid and paired audit streams "
            "and are not independent replications; five deployments per shot budget"
        ),
        "stage_definitions": {
            "A": "IDEAL: exact SVC, exact Platt map, exact BA_w-optimal threshold",
            "B0": "FIT-ONLY counterfactual: SVC refitted on the realized training Gram, evaluated on the exact source/target cross-Grams, exact Platt map, exact threshold",
            "B": "MODEL-ONLY counterfactual: realized decision function (noisy fit and noisy cross-Grams), exact Platt map, exact threshold",
            "C": "MODEL+CALIBRATION counterfactual: realized decision function, deployment-specific Platt map, exact probability threshold",
            "D": "FULL DEPLOYMENT (archived pipeline): realized decision function, deployment-specific Platt map, deployment-specific refrozen threshold",
        },
        "intervention_order_note": (
            "Stages B0, B and C are diagnostic counterfactuals that were never deployed. The "
            "attribution is sequential and order-dependent: interventions follow pipeline order "
            "(fit -> evaluation cross-Grams -> calibration -> operating threshold); a different "
            "order could redistribute the increments. Telescoping is exact by construction."
        ),
        "auc_note": "AUC is reported only as a ranking/discrimination diagnostic, not as a synonym of kernel quality.",
        "dependencies": {
            "primary_pipeline": "experiments/E16_quantum_uncertainty/run_e16.py (frozen)",
            "replay_machinery": "scripts/analyze_e16_psd_sensitivity.py (frozen)",
            "audit": "e16.audit_deployment with the archived E13 w_max and paired audit streams",
        },
        "limitations": [
            "diagnostic counterfactuals, not deployed pipelines",
            "sequential attribution depends on the intervention order declared above",
            "five deployments per shot budget; cells and streams within a deployment are correlated",
            "the classification rule is descriptive and predeclared; it is not a population inference",
        ],
        "provenance": {
            "input_sha256": input_hashes,
            "protected_table_sha256": protected_before,
            "no_new_randomness": True,
            "deterministic_replay_of_archived_seed_schedule_only": True,
            "no_new_qpu_jobs": True,
            "no_new_seeds_samples_models_feature_maps_hyperparameters_claims_or_repairs": True,
            "protected_artifacts_unchanged_after_analysis": protected_before == protected_after,
        },
        "reproduction": {
            **reproduction,
            "all_raw_stage_D_match_primary": all(reproduction["raw_stage_D_matches_primary_per_config"].values()),
            "all_raw_stage_D_match_psd_archive": all(reproduction["raw_stage_D_matches_psd_archive_payload"].values()),
            "all_psd_stage_D_match_psd_archive": all(reproduction["psd_stage_D_matches_psd_archive_payload"].values()),
        },
        "ideal": {
            "platt_slope": ideal_platt_slope,
            **{k: v for k, v in ideal_record.items() if k not in ("movements_vs_ideal", "claims", "truth_sign_changes_vs_ideal_over_60_cells")},
        },
        "per_deployment": per_deployment,
        "aggregate_by_regime": aggregate,
        "classification": classification,
        "wall_seconds": rounded(time.time() - start, 1),
    }
    OUTPUT.write_text(json.dumps(output, indent=1) + "\n", encoding="utf-8")
    log(f"wrote {OUTPUT.relative_to(ROOT)} ({output['wall_seconds']:.1f} s); classification={classification['overall']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
