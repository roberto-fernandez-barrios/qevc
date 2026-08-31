"""Post-hoc PSD robustness analysis of the 30 frozen E16 realizations.

This script does not create new independent noisy-kernel deployments.  It
deterministically replays the six frozen shot budgets and five frozen kernel
seeds from E16's stable RNG, requires every historical primary summary to
match, and then refits the same deployment after minimum diagonal loading of
the realized training Gram.  Calibration/target cross-Grams, roles, claim
grids, and audit streams are unchanged.

Output: results/tables/E16_psd_sensitivity.json
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
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
E01_PATH = ROOT / "configs" / "experiments" / "E01.yaml"
E16_PATH = ROOT / "configs" / "experiments" / "E16.yaml"
FROZEN_PATH = ROOT / "configs" / "frozen" / "frozen_deployment_v1.yaml"
E16_MODULE_PATH = ROOT / "experiments" / "E16_quantum_uncertainty" / "run_e16.py"


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
        correct, weights = {}, {}
        for name, data in environment_data.items():
            probability = calibrator.predict_proba(
                svc.decision_function(K_environment[name].T)
            )
            prediction = (probability >= threshold).astype(int)
            corr = (prediction == data["y"]).astype(float)
            correct[name] = corr
            weights[name] = data["w"]
            targets[name] = {
                "auc": rounded(weighted_auc(data["y"], probability, data["w"])),
                "balanced_accuracy": rounded(
                    weighted_balanced_accuracy(data["y"], prediction, data["w"])
                ),
                "metric_unweighted_accuracy": rounded(corr.mean()),
                "metric_weighted_accuracy": rounded(np.average(corr, weights=data["w"])),
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
                raise RuntimeError(f"raw deterministic replay mismatch for {key}")

            repair = minimum_diagonal_loading(
                K_train_raw, epsilon_relative=DEFAULT_EPSILON_REL
            )
            repaired_result = build_deployment(
                repair.matrix, K_source_raw, K_environment_raw, fixed_refs=ideal["refs"]
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
    if primary_hash_before != primary_hash_after:
        raise RuntimeError("primary E16 artifact changed during derived analysis")
    if hardware_hashes_before != hardware_hashes_after:
        raise RuntimeError("E16 hardware raw artifacts changed during derived analysis")

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
                "The loaded full-rank training block restores the convex PSD-SVM training "
                "problem; unchanged cross columns define the same measured out-of-sample "
                "similarities through the training span."
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
