"""Post-hoc PSD robustness analysis of the 30 frozen E16 realizations.

This script does not create new independent noisy-kernel deployments.  It
deterministically replays the six frozen shot budgets and five frozen kernel
seeds from E16's stable RNG, requires every historical primary summary to
match, and then refits the same deployment after minimum diagonal loading of
the realized training Gram.  Calibration/target cross-Grams, roles, claim
grids, and audit streams are unchanged.

Outputs:
  results/tables/E16_psd_sensitivity.json
  results/tables/E16_proposition4_instantiation.json
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import yaml
from sklearn.svm import SVC


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "E02_systematic_landscape"))

from qevc.geometry.descriptors import effective_rank  # noqa: E402
from qevc.auditing.stability import (  # noqa: E402
    FAILS,
    HOLDS,
    canonical_json_sha256,
    opposite_resolved_verdict,
    sufficient_condition_status,
    summarize_proposition4_cases,
)
from qevc.kernels.psd import (  # noqa: E402
    DEFAULT_EPSILON_REL,
    DEFAULT_NEGATIVE_TOL_REL,
    minimum_diagonal_loading,
    spectral_audit,
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


PRIMARY = ROOT / "results" / "tables" / "E16_quantum_uncertainty.json"
OUTPUT = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
PROPOSITION4_OUTPUT = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
E01_PATH = ROOT / "configs" / "experiments" / "E01.yaml"
E16_PATH = ROOT / "configs" / "experiments" / "E16.yaml"
FROZEN_PATH = ROOT / "configs" / "frozen" / "frozen_deployment_v1.yaml"
E16_MODULE_PATH = ROOT / "experiments" / "E16_quantum_uncertainty" / "run_e16.py"
E13_RESULTS_PATH = ROOT / "results" / "tables" / "E13_weighted_cs.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def load_e16_module():
    spec = importlib.util.spec_from_file_location("frozen_e16_runner", E16_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen E16 runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rounded(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def descriptive(values: list[float], *, worst: str = "max") -> dict[str, float | list[float]]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        raise ValueError("cannot summarize an empty list")
    worst_value = array.min() if worst == "min" else array.max()
    return {
        "mean": rounded(array.mean()),
        "median": rounded(np.median(array)),
        "range": [rounded(array.min()), rounded(array.max())],
        "worst_case": rounded(worst_value),
        "sample_sd": rounded(array.std(ddof=1)) if len(array) > 1 else 0.0,
    }


def verdict_summary(audit: dict, ideal: dict, cell_stratum: dict, stratum: str) -> dict:
    keys = [key for key in audit if cell_stratum[(key[0], key[1], key[2])] == stratum]
    verdicts = Counter(audit[key]["verdict"] for key in keys)
    flips = sum(audit[key]["verdict"] != ideal[key]["verdict"] for key in keys)
    false_cert = sum(
        not audit[key]["truth"] and audit[key]["verdict"] == "SUPPORTED" for key in keys
    )
    return {
        "n_cells": len(keys),
        "flip_rate_vs_ideal": rounded(flips / len(keys)),
        "abstention_rate": rounded(verdicts["UNRESOLVED"] / len(keys)),
        "verdict_composition": {
            verdict: int(verdicts[verdict])
            for verdict in ("SUPPORTED", "REFUTED", "UNRESOLVED")
        },
        "false_certifications": int(false_cert),
        "false_claim_cells": int(sum(not audit[key]["truth"] for key in keys)),
    }


def transition_summary(left: dict, right: dict, cell_stratum: dict, stratum: str) -> dict:
    keys = [key for key in left if cell_stratum[(key[0], key[1], key[2])] == stratum]
    transitions = Counter(
        f"{left[key]['verdict']}->{right[key]['verdict']}"
        for key in keys
        if left[key]["verdict"] != right[key]["verdict"]
    )
    truth_changes = sum(left[key]["truth"] != right[key]["truth"] for key in keys)
    return {
        "n_changed": int(sum(transitions.values())),
        "change_rate": rounded(sum(transitions.values()) / len(keys)),
        "truth_changes": int(truth_changes),
        "transitions": dict(sorted(transitions.items())),
    }


def deployment_payload(result: dict, ideal_audit: dict, cell_stratum: dict) -> dict:
    return {
        "threshold": rounded(result["refs"]["thr"]),
        "source_metric_unweighted_accuracy": rounded(result["refs"]["m_s_unw"]),
        "source_metric_weighted_accuracy": rounded(result["refs"]["m_s_w"]),
        "source_balanced_accuracy": rounded(result["source_balanced_accuracy"]),
        "targets": result["targets"],
        "claims": {
            stratum: {
                "deployment_relative": verdict_summary(
                    result["audit_own"], ideal_audit, cell_stratum, stratum
                ),
                "ideal_anchored": verdict_summary(
                    result["audit_fixed"], ideal_audit, cell_stratum, stratum
                ),
            }
            for stratum in ("far", "moderate", "near")
        },
    }


def proposition4_cases_for_deployment(
    *,
    deployment_id: str,
    shot_budget: int,
    kernel_seed: int,
    regime: str,
    result: dict,
    ideal: dict,
    ideal_audit: dict,
    cell_stratum: dict,
) -> list[dict]:
    """Instantiate Proposition 4 for every E16 claim cell and paired stream."""

    cases = []
    base_cells = sorted({(key[0], key[1], key[2]) for key in ideal_audit})
    for environment, family, delta in base_cells:
        source_key = "m_s_unw" if family == "unweighted" else "m_s_w"
        target_key = (
            "metric_unweighted_accuracy"
            if family == "unweighted"
            else "metric_weighted_accuracy"
        )
        metric_name = (
            "unweighted accuracy"
            if family == "unweighted"
            else "raw-physical-weighted accuracy"
        )
        ideal_source = float(ideal["refs"][source_key])
        realized_source = float(result["refs"][source_key])
        ideal_target = float(ideal["targets_exact"][environment][target_key])
        realized_target = float(result["targets_exact"][environment][target_key])
        delta_m_source = realized_source - ideal_source
        delta_m_target = realized_target - ideal_target
        differential_movement = delta_m_target - delta_m_source

        ideal_unclipped_threshold = ideal_source - float(delta)
        ideal_threshold = float(np.clip(ideal_unclipped_threshold, 0.0, 1.0))
        realized_unclipped_threshold = realized_source - float(delta)
        realized_threshold = float(np.clip(realized_unclipped_threshold, 0.0, 1.0))
        ideal_threshold_clipped = ideal_threshold != ideal_unclipped_threshold
        realized_threshold_clipped = realized_threshold != realized_unclipped_threshold
        ideal_margin = ideal_target - ideal_threshold

        for claim_semantics in ("deployment_relative", "ideal_anchored"):
            if claim_semantics == "deployment_relative":
                audit = result["audit_own"]
                realized_margin = realized_target - realized_threshold
                movement = differential_movement
                threshold_clipped = ideal_threshold_clipped or realized_threshold_clipped
                realized_claim_threshold = realized_threshold
            else:
                audit = result["audit_fixed"]
                realized_margin = realized_target - ideal_threshold
                movement = delta_m_target
                threshold_clipped = ideal_threshold_clipped
                realized_claim_threshold = ideal_threshold

            identity_residual = (realized_margin - ideal_margin) - movement
            identity_verified = math.isclose(
                identity_residual, 0.0, rel_tol=0.0, abs_tol=1e-12
            )
            evaluable = not threshold_clipped and identity_verified
            condition_status = sufficient_condition_status(
                ideal_margin, movement, evaluable=evaluable
            )
            stream_rows = []
            for audit_seed in sorted(key[3] for key in ideal_audit if key[:3] == (
                environment, family, delta
            )):
                key = (environment, family, delta, audit_seed)
                ideal_row = ideal_audit[key]
                realized_row = audit[key]
                if not math.isclose(
                    float(ideal_row["margin"]), ideal_margin, rel_tol=0.0, abs_tol=1e-12
                ):
                    raise RuntimeError(f"ideal-margin reconstruction mismatch for {key}")
                if bool(ideal_row["truth"]) != (ideal_margin >= 0.0):
                    raise RuntimeError(f"ideal-truth reconstruction mismatch for {key}")
                if bool(realized_row["truth"]) != (realized_margin >= 0.0):
                    raise RuntimeError(f"realized-truth reconstruction mismatch for {key}")
                verdict_flip = realized_row["verdict"] != ideal_row["verdict"]
                stream_rows.append(
                    {
                        "audit_seed": int(audit_seed),
                        "ideal_verdict": ideal_row["verdict"],
                        "realized_verdict": realized_row["verdict"],
                        "verdict_flip": verdict_flip,
                        "opposite_resolved_verdict": opposite_resolved_verdict(
                            ideal_row["verdict"], realized_row["verdict"]
                        ),
                        "truth_sign_flip": bool(ideal_row["truth"]) != bool(
                            realized_row["truth"]
                        ),
                        "ideal_n_star": ideal_row["n_star"],
                        "realized_n_star": realized_row["n_star"],
                    }
                )

            cases.append(
                {
                    "deployment_id": deployment_id,
                    "shot_budget": int(shot_budget),
                    "kernel_seed": int(kernel_seed),
                    "regime": regime,
                    "raw_indefinite": regime == "raw",
                    "psd_repaired": regime == "psd_repaired",
                    "claim_semantics": claim_semantics,
                    "environment": environment,
                    "metric_family": family,
                    "metric": metric_name,
                    "delta": float(delta),
                    "stratum": cell_stratum[(environment, family, delta)],
                    "ideal_source_metric": ideal_source,
                    "realized_source_metric": realized_source,
                    "ideal_target_metric": ideal_target,
                    "realized_target_metric": realized_target,
                    "delta_M_S": delta_m_source,
                    "delta_M_T": delta_m_target,
                    "delta_M_T_minus_delta_M_S": differential_movement,
                    "ideal_threshold": ideal_threshold,
                    "realized_claim_threshold": realized_claim_threshold,
                    "ideal_margin": ideal_margin,
                    "realized_margin": realized_margin,
                    "condition_movement": movement,
                    "condition_inequality": "abs(ideal_margin) > abs(condition_movement)",
                    "sufficient_condition_status": condition_status,
                    "ideal_threshold_clipped": ideal_threshold_clipped,
                    "realized_threshold_clipped": realized_threshold_clipped,
                    "margin_identity_residual": identity_residual,
                    "margin_identity_verified": identity_verified,
                    "ideal_truth": ideal_margin >= 0.0,
                    "realized_truth": realized_margin >= 0.0,
                    "audit_streams": stream_rows,
                }
            )
    return cases


def aggregate_proposition4(cases: list[dict]) -> dict:
    """Return all requested descriptive cuts of the normalized case table."""

    def selected(**filters) -> list[dict]:
        return [
            row for row in cases
            if all(row[field] == value for field, value in filters.items())
        ]

    regimes = ("raw", "psd_repaired")
    semantics = ("deployment_relative", "ideal_anchored")
    strata = ("far", "moderate", "near")
    return {
        "overall": summarize_proposition4_cases(cases),
        "by_regime": {
            regime: summarize_proposition4_cases(selected(regime=regime))
            for regime in regimes
        },
        "by_claim_semantics": {
            claim: summarize_proposition4_cases(selected(claim_semantics=claim))
            for claim in semantics
        },
        "by_stratum": {
            stratum: summarize_proposition4_cases(selected(stratum=stratum))
            for stratum in strata
        },
        "by_regime_and_claim_semantics": {
            regime: {
                claim: summarize_proposition4_cases(
                    selected(regime=regime, claim_semantics=claim)
                )
                for claim in semantics
            }
            for regime in regimes
        },
        "by_regime_and_stratum": {
            regime: {
                stratum: summarize_proposition4_cases(
                    selected(regime=regime, stratum=stratum)
                )
                for stratum in strata
            }
            for regime in regimes
        },
        "by_claim_semantics_and_stratum": {
            claim: {
                stratum: summarize_proposition4_cases(
                    selected(claim_semantics=claim, stratum=stratum)
                )
                for stratum in strata
            }
            for claim in semantics
        },
        "by_regime_claim_semantics_and_stratum": {
            regime: {
                claim: {
                    stratum: summarize_proposition4_cases(
                        selected(
                            regime=regime,
                            claim_semantics=claim,
                            stratum=stratum,
                        )
                    )
                    for stratum in strata
                }
                for claim in semantics
            }
            for regime in regimes
        },
    }


def primary_projection(
    e16,
    K_train: np.ndarray,
    K_train_exact: np.ndarray,
    exact_effective_rank: float,
    result: dict,
    ideal_result: dict,
    ideal_audit: dict,
    cell_stratum: dict,
) -> dict:
    frobenius = float(np.linalg.norm(K_train - K_train_exact) / np.linalg.norm(K_train_exact))
    entry = {
        "kernel": {
            "frob_rel_err": round(frobenius, 5),
            "eff_rank": round(float(effective_rank(K_train.astype(np.float64))), 2),
            "eff_rank_exact": round(float(exact_effective_rank), 2),
            "psd_violation": round(float(e16.psd_violation(K_train)), 6),
        },
        "nominal_auc": round(result["targets"]["nominal"]["auc"], 5),
        "nominal_auc_ideal": round(ideal_result["targets"]["nominal"]["auc"], 5),
        "m_s_shift_unw": round(
            result["refs"]["m_s_unw"] - ideal_result["refs"]["m_s_unw"], 5
        ),
        "m_s_shift_w": round(
            result["refs"]["m_s_w"] - ideal_result["refs"]["m_s_w"], 5
        ),
        "strata": {},
    }
    for stratum in ("far", "moderate", "near"):
        keys = [
            key for key in result["audit_own"]
            if cell_stratum[(key[0], key[1], key[2])] == stratum
        ]
        own = result["audit_own"]
        fixed = result["audit_fixed"]
        ratios = [
            own[key]["n_star"] / ideal_audit[key]["n_star"]
            for key in keys
            if own[key]["n_star"] and ideal_audit[key]["n_star"]
        ]
        entry["strata"][stratum] = {
            "n_cells": len(keys),
            "flip_rate_own_tau": round(
                sum(own[key]["verdict"] != ideal_audit[key]["verdict"] for key in keys)
                / len(keys),
                4,
            ),
            "flip_rate_fixed_tau": round(
                sum(fixed[key]["verdict"] != ideal_audit[key]["verdict"] for key in keys)
                / len(keys),
                4,
            ),
            "abstention": round(
                sum(own[key]["verdict"] == "UNRESOLVED" for key in keys) / len(keys), 4
            ),
            "abstention_ideal": round(
                sum(ideal_audit[key]["verdict"] == "UNRESOLVED" for key in keys)
                / len(keys),
                4,
            ),
            "false_cert": int(sum(
                not own[key]["truth"] and own[key]["verdict"] == "SUPPORTED" for key in keys
            )),
            "n_claim_false": int(sum(not own[key]["truth"] for key in keys)),
            "false_cert_fixed_tau": int(sum(
                not fixed[key]["truth"] and fixed[key]["verdict"] == "SUPPORTED"
                for key in keys
            )),
            "n_claim_false_fixed_tau": int(sum(not fixed[key]["truth"] for key in keys)),
            "n_star_ratio_median": round(float(np.median(ratios)), 3) if ratios else None,
        }
    return entry


def aggregate_by_shots(per_deployment: dict, shots_grid: list[int]) -> dict:
    aggregate = {}
    for shots in shots_grid:
        rows = [row for row in per_deployment.values() if row["shot_budget"] == shots]
        spectral_metrics = {
            "lambda_min": "min",
            "lambda_max": "max",
            "negative_modes": "max",
            "negative_mass": "max",
            "negative_mass_fraction": "max",
            "negative_mass_trace_ratio": "max",
            "relative_indefiniteness": "max",
            "positive_spectrum_condition": "max",
        }
        spectrum = {
            metric: descriptive(
                [float(row["spectrum_raw"][metric]) for row in rows], worst=worst
            )
            for metric, worst in spectral_metrics.items()
        }

        def field(regime: str, stratum: str, claim_class: str, metric: str) -> list[float]:
            return [
                float(row[regime]["claims"][stratum][claim_class][metric]) for row in rows
            ]

        summary = {
            "n_deployments": len(rows),
            "spectrum_raw": spectrum,
            "diagonal_loading": descriptive(
                [float(row["repair"]["diagonal_loading"]) for row in rows]
            ),
            "raw_nominal_auc": descriptive(
                [float(row["raw"]["targets"]["nominal"]["auc"]) for row in rows]
            ),
            "psd_nominal_auc": descriptive(
                [float(row["psd_repaired"]["targets"]["nominal"]["auc"]) for row in rows]
            ),
            "raw_threshold": descriptive([float(row["raw"]["threshold"]) for row in rows]),
            "psd_threshold": descriptive(
                [float(row["psd_repaired"]["threshold"]) for row in rows]
            ),
        }
        for label, regime, claim_class in (
            ("raw_far_c_dep_flip_rate", "raw", "deployment_relative"),
            ("psd_far_c_dep_flip_rate", "psd_repaired", "deployment_relative"),
            ("raw_far_c_ideal_flip_rate", "raw", "ideal_anchored"),
            ("psd_far_c_ideal_flip_rate", "psd_repaired", "ideal_anchored"),
        ):
            summary[label] = descriptive(field(regime, "far", claim_class, "flip_rate_vs_ideal"))
        for stratum in ("far", "moderate", "near"):
            summary[f"raw_vs_psd_{stratum}_deployment_relative_change_rate"] = descriptive(
                [float(row["raw_vs_psd"][stratum]["deployment_relative"]["change_rate"])
                 for row in rows]
            )
            summary[f"raw_vs_psd_{stratum}_ideal_anchored_change_rate"] = descriptive(
                [float(row["raw_vs_psd"][stratum]["ideal_anchored"]["change_rate"])
                 for row in rows]
            )
        aggregate[str(shots)] = summary
    return aggregate


def main() -> int:
    start = time.time()
    e16 = load_e16_module()
    e01_cfg = yaml.safe_load(E01_PATH.read_text(encoding="utf-8"))
    e16_cfg = yaml.safe_load(E16_PATH.read_text(encoding="utf-8"))
    frozen = yaml.safe_load(FROZEN_PATH.read_text(encoding="utf-8"))
    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))
    primary_hash_before = sha256(PRIMARY)
    protected_table_paths = [
        ROOT / "results" / "tables" / name
        for name in (
            "E16_quantum_uncertainty.json",
            "E16_deployment_level.json",
            "E16_hw.json",
            "E20_offline_gate.json",
            "E11_cms_case_study.json",
            "E11v2_cms_full.json",
            "E11v3_cms_stats.json",
        )
    ]
    protected_hashes_before = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in protected_table_paths
    }
    hardware_raw_paths = sorted((ROOT / "results" / "raw" / "E16_hw").glob("*"))
    hardware_hashes_before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
                              for path in hardware_raw_paths if path.is_file()}

    raw = load_raw_subset(ROOT, e01_cfg["subset"])
    raw_splits = get_raw_splits(ROOT, raw, e01_cfg["splits"], experiment_tag="E01")
    labels_raw = raw["labels"].to_numpy().astype(int)
    nominal = build_environment_dataset(raw, Environment())
    frames = {
        role: nominal[np.isin(nominal["row_id"].to_numpy(), ids)]
        for role, ids in raw_splits.items()
    }
    train = tier_a_frame(
        frames["train"], e01_cfg["tier_a"]["n_train"], e01_cfg["tier_a"]["seed"]
    )
    columns = frozen["features"]["quantum"]
    params = parse_params(frozen["hyperparameters"]["tier_a"]["qksvc"])
    scaler = AngleScaler().fit(train[columns].to_numpy(float))
    feature_map = build_feature_map(
        len(columns), reps=params["reps"], entanglement=params["entanglement"],
        scale=params["scale"]
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
        frame = build_environment_dataset(
            raw, environment_map[name], row_ids=raw_splits["nominal_test"]
        )
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

    def build_deployment(K_train, K_source, K_environment, fixed_refs=None) -> dict:
        svc = SVC(kernel="precomputed", C=float(params["C"]))
        svc.fit(K_train, y_train, sample_weight=training_weights)
        source_scores = svc.decision_function(K_source.T)
        calibrator = PlattCalibrator().fit(source_scores, y_source, w_source)
        source_prob = calibrator.predict_proba(source_scores)
        threshold = ba_optimal_threshold(y_source, source_prob, w_source)
        source_pred = (source_prob >= threshold).astype(int)
        refs = {
            "m_s_unw": float(np.mean(source_pred == y_source)),
            "m_s_w": float(np.average(source_pred == y_source, weights=w_source)),
            "thr": float(threshold),
        }
        targets = {}
        targets_exact = {}
        correct, weights = {}, {}
        for name, data in environment_data.items():
            probability = calibrator.predict_proba(
                svc.decision_function(K_environment[name].T)
            )
            prediction = (probability >= threshold).astype(int)
            corr = (prediction == data["y"]).astype(float)
            correct[name] = corr
            weights[name] = data["w"]
            auc = float(weighted_auc(data["y"], probability, data["w"]))
            balanced_accuracy = float(
                weighted_balanced_accuracy(data["y"], prediction, data["w"])
            )
            unweighted_accuracy = float(corr.mean())
            weighted_accuracy = float(np.average(corr, weights=data["w"]))
            targets_exact[name] = {
                "auc": auc,
                "balanced_accuracy": balanced_accuracy,
                "metric_unweighted_accuracy": unweighted_accuracy,
                "metric_weighted_accuracy": weighted_accuracy,
            }
            targets[name] = {
                metric: rounded(value)
                for metric, value in targets_exact[name].items()
            }
        audit_own = e16.audit_deployment(
            correct, weights, refs["m_s_unw"], refs["m_s_w"], e16_cfg["alpha"]
        )
        audit_fixed = None
        if fixed_refs is not None:
            audit_fixed = e16.audit_deployment(
                correct, weights, fixed_refs["m_s_unw"], fixed_refs["m_s_w"],
                e16_cfg["alpha"]
            )
        return {
            "audit_own": audit_own,
            "audit_fixed": audit_fixed,
            "refs": refs,
            "source_balanced_accuracy": weighted_balanced_accuracy(
                y_source, source_pred, w_source
            ),
            "targets": targets,
            "targets_exact": targets_exact,
        }

    ideal = build_deployment(
        K_train_exact, K_source_exact, K_environment_exact, fixed_refs=None
    )
    ideal_audit = ideal["audit_own"]
    cell_stratum = {
        (key[0], key[1], key[2]): e16.stratum(value["margin"])
        for key, value in ideal_audit.items()
    }
    log(f"ideal deployment reconstructed: nominal AUC={ideal['targets']['nominal']['auc']:.5f}")

    per_deployment = {}
    proposition4_cases = []
    replay_mismatches = {}
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
            spectrum = spectral_audit(
                K_train_raw, negative_tolerance_relative=DEFAULT_NEGATIVE_TOL_REL
            )
            raw_result = build_deployment(
                K_train_raw, K_source_raw, K_environment_raw, fixed_refs=ideal["refs"]
            )
            observed_primary = primary_projection(
                e16, K_train_raw, K_train_exact, exact_effective_rank, raw_result,
                ideal, ideal_audit, cell_stratum
            )
            if observed_primary != primary["per_config"][key]:
                replay_mismatches[key] = {
                    "expected": primary["per_config"][key],
                    "observed": observed_primary,
                }
                log(json.dumps(replay_mismatches[key], indent=2, sort_keys=True))
                raise RuntimeError(f"raw deterministic replay mismatch for {key}")

            repair = minimum_diagonal_loading(
                K_train_raw, epsilon_relative=DEFAULT_EPSILON_REL
            )
            repaired_result = build_deployment(
                repair.matrix, K_source_raw, K_environment_raw, fixed_refs=ideal["refs"]
            )
            proposition4_cases.extend(
                proposition4_cases_for_deployment(
                    deployment_id=key,
                    shot_budget=shots,
                    kernel_seed=kernel_seed,
                    regime="raw",
                    result=raw_result,
                    ideal=ideal,
                    ideal_audit=ideal_audit,
                    cell_stratum=cell_stratum,
                )
            )
            proposition4_cases.extend(
                proposition4_cases_for_deployment(
                    deployment_id=key,
                    shot_budget=shots,
                    kernel_seed=kernel_seed,
                    regime="psd_repaired",
                    result=repaired_result,
                    ideal=ideal,
                    ideal_audit=ideal_audit,
                    cell_stratum=cell_stratum,
                )
            )
            raw_payload = deployment_payload(raw_result, ideal_audit, cell_stratum)
            repaired_payload = deployment_payload(repaired_result, ideal_audit, cell_stratum)
            raw_vs_psd = {
                stratum: {
                    "deployment_relative": transition_summary(
                        raw_result["audit_own"], repaired_result["audit_own"],
                        cell_stratum, stratum
                    ),
                    "ideal_anchored": transition_summary(
                        raw_result["audit_fixed"], repaired_result["audit_fixed"],
                        cell_stratum, stratum
                    ),
                }
                for stratum in ("far", "moderate", "near")
            }
            per_deployment[key] = {
                "shot_budget": int(shots),
                "kernel_seed": int(kernel_seed),
                "spectrum_raw": {
                    name: rounded(value) if isinstance(value, float) else value
                    for name, value in spectrum.items()
                },
                "repair": {
                    "epsilon_relative": DEFAULT_EPSILON_REL,
                    "epsilon_absolute": rounded(repair.epsilon, 12),
                    "diagonal_loading": rounded(repair.loading),
                    "lambda_min_after": rounded(repair.lambda_min_after, 12),
                    "off_diagonal_and_cross_grams_unchanged": True,
                },
                "raw": raw_payload,
                "psd_repaired": repaired_payload,
                "raw_vs_psd": raw_vs_psd,
            }
            log(
                f"{key}: lambda_min={spectrum['lambda_min']:.5g}, "
                f"negative_modes={spectrum['negative_modes']}, load={repair.loading:.5g}, "
                f"far C_dep raw/PSD="
                f"{raw_payload['claims']['far']['deployment_relative']['flip_rate_vs_ideal']:.4f}/"
                f"{repaired_payload['claims']['far']['deployment_relative']['flip_rate_vs_ideal']:.4f}"
            )

    aggregate = aggregate_by_shots(per_deployment, e16_cfg["shots_grid"])
    primary_hash_after = sha256(PRIMARY)
    hardware_hashes_after = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
                             for path in hardware_raw_paths if path.is_file()}
    protected_hashes_after = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in protected_table_paths
    }
    if primary_hash_before != primary_hash_after:
        raise RuntimeError("primary E16 artifact changed during derived analysis")
    if hardware_hashes_before != hardware_hashes_after:
        raise RuntimeError("E16 hardware raw artifacts changed during derived analysis")
    if protected_hashes_before != protected_hashes_after:
        raise RuntimeError("a protected primary/CMS/E20 table changed during derived analysis")

    output = {
        "analysis": "E16 post-hoc PSD robustness analysis",
        "status": "post-hoc robustness analysis prompted by the final technical audit",
        "independent_unit": "one deterministically replayed frozen noisy-kernel deployment",
        "n_independent_deployments": len(per_deployment),
        "repair": {
            "name": "minimum diagonal loading",
            "formula": "K_psd = K_raw + max(0, -lambda_min + epsilon) I",
            "epsilon_relative": DEFAULT_EPSILON_REL,
            "epsilon_definition": "epsilon = 1e-10 * max(1, abs(lambda_max(K_raw)))",
            "negative_mode_tolerance_relative": DEFAULT_NEGATIVE_TOL_REL,
            "cross_gram_rule": "all source-validation and target cross-Grams remain raw and unchanged",
            "interpretation": (
                "Minimum diagonal loading restores a PSD training block and therefore a "
                "convex precomputed-SVM training problem. The loaded matrix is a post-hoc "
                "regularized similarity matrix, not a normalized fidelity Gram; cross-Gram "
                "estimates remain unchanged and no global Mercer extension is claimed."
            ),
        },
        "provenance": {
            "primary_e16_path": str(PRIMARY.relative_to(ROOT)).replace("\\", "/"),
            "primary_e16_sha256": primary_hash_before,
            "e16_config_sha256": sha256(E16_PATH),
            "frozen_deployment_sha256": sha256(FROZEN_PATH),
            "frozen_e16_runner_sha256": sha256(E16_MODULE_PATH),
            "hardware_raw_sha256": hardware_hashes_before,
            "no_new_randomness": True,
            "no_new_qpu_jobs": True,
            "primary_and_hardware_hashes_unchanged_after_analysis": True,
        },
        "raw_replay_validation": {
            "all_30_primary_rows_match": not replay_mismatches,
            "mismatches": replay_mismatches,
            "note": (
                "E16 did not persist the large Gram arrays. The original stable RNG, frozen "
                "inputs, six shot budgets and five kernel seeds were replayed; every archived "
                "primary per-configuration summary matched before PSD repair was evaluated."
            ),
        },
        "per_deployment": per_deployment,
        "aggregate_by_shots": aggregate,
        "wall_seconds": rounded(time.time() - start, 1),
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {OUTPUT.relative_to(ROOT)} ({output['wall_seconds']:.1f} s)")

    proposition4_cases.sort(
        key=lambda row: (
            row["shot_budget"],
            row["kernel_seed"],
            row["regime"],
            row["claim_semantics"],
            row["environment"],
            row["metric_family"],
            row["delta"],
        )
    )
    proposition4_aggregate = aggregate_proposition4(proposition4_cases)
    overall = proposition4_aggregate["overall"]
    matrix = overall["verdict_flip_contingency"]

    def flip_rate(status: str) -> float | None:
        denominator = matrix[status]["flip"] + matrix[status]["no_flip"]
        return matrix[status]["flip"] / denominator if denominator else None

    fraction_holds = overall["fraction_holds_among_evaluable"]
    holds_rate = flip_rate(HOLDS)
    fails_rate = flip_rate(FAILS)
    if (
        fraction_holds is not None
        and fraction_holds >= 0.10
        and holds_rate is not None
        and fails_rate is not None
        and holds_rate < fails_rate
    ):
        interpretation = "INFORMATIVELY INSTANTIATED"
    elif overall["condition_cell_counts"][HOLDS] > 0:
        interpretation = "CONSERVATIVE BUT VALID"
    else:
        interpretation = "EMPIRICALLY UNINFORMATIVE"

    proposition4_output = {
        "analysis": "E16 Proposition 4 deterministic instantiation",
        "status": "derived-only closure analysis over the 30 frozen E16 deployments",
        "interpretation": interpretation,
        "independent_descriptive_unit": "deployment",
        "correlation_warning": (
            "Claims, thresholds and paired audit streams within a deployment are correlated; "
            "the cell and stream counts below are descriptive, not independent replications."
        ),
        "definitions": {
            "f_star": "the exact ideal E16 deployment",
            "f_tilde_omega": (
                "the realized deployment for omega, either historical raw-indefinite or the "
                "minimum-diagonal-loading PSD sensitivity"
            ),
            "M_unweighted": "mean target/source correctness over the corresponding frozen rows",
            "M_weighted": (
                "raw-physical-weighted mean correctness over the corresponding frozen rows"
            ),
            "delta_M_S": "M_S(f_tilde_omega) - M_S(f_star)",
            "delta_M_T": "M_T(f_tilde_omega) - M_T(f_star)",
            "deployment_relative_movement": "delta_M_T - delta_M_S",
            "ideal_anchored_movement": "delta_M_T",
            "ideal_margin": "M_T(f_star) - (M_S(f_star) - delta)",
            "sufficient_condition": "abs(ideal_margin) > abs(condition_movement)",
            "condition_scope": (
                "strict sufficient sign-stability bound; failure is not a predicted flip and "
                "holding is not empirical proof of a general law"
            ),
            "verdict_flip": (
                "any change among SUPPORTED, REFUTED and UNRESOLVED relative to the paired "
                "ideal audit stream"
            ),
            "opposite_resolved_verdict": (
                "SUPPORTED<->REFUTED only; transitions involving UNRESOLVED are excluded"
            ),
        },
        "provenance": {
            "input_sha256": {
                "primary_e16": primary_hash_before,
                "e01_config": sha256(E01_PATH),
                "e16_config": sha256(E16_PATH),
                "frozen_deployment": sha256(FROZEN_PATH),
                "frozen_e16_runner": sha256(E16_MODULE_PATH),
                "weighted_cs_results": sha256(E13_RESULTS_PATH),
                "instantiation_script": sha256(Path(__file__).resolve()),
            },
            "protected_table_sha256": protected_hashes_before,
            "hardware_raw_sha256": hardware_hashes_before,
            "no_new_randomness": True,
            "deterministic_replay_of_archived_seed_schedule_only": True,
            "no_new_qpu_jobs": True,
            "no_new_datasets_models_feature_maps_hyperparameters_or_likelihoods": True,
            "primary_artifacts_unchanged_after_analysis": (
                primary_hash_before == primary_hash_after
                and hardware_hashes_before == hardware_hashes_after
                and protected_hashes_before == protected_hashes_after
            ),
            "raw_replay_all_30_primary_rows_match": not replay_mismatches,
        },
        "case_accounting": {
            "n_frozen_deployments": len(per_deployment),
            "n_regimes_per_deployment": 2,
            "n_claim_semantics_per_metric_cell": 2,
            "n_unique_environment_family_delta_cells_per_deployment": 60,
            "n_paired_audit_streams_per_cell": int(e16_cfg["audit_seeds"]),
            "n_condition_cells": len(proposition4_cases),
            "n_audit_stream_cases": sum(
                len(row["audit_streams"]) for row in proposition4_cases
            ),
        },
        "cases": proposition4_cases,
        "aggregate_summaries": proposition4_aggregate,
        "reproducibility": {
            "canonical_encoding": "UTF-8 JSON, sorted keys, compact separators, no NaN",
        },
    }
    proposition4_output["reproducibility"]["canonical_payload_sha256"] = (
        canonical_json_sha256(proposition4_output)
    )
    PROPOSITION4_OUTPUT.write_text(
        json.dumps(proposition4_output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    log(
        f"wrote {PROPOSITION4_OUTPUT.relative_to(ROOT)}: "
        f"{len(proposition4_cases)} condition cells, interpretation={interpretation}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
