"""E20 offline GO/NO-GO gate — never connects to IBM or submits QPU work.

The protocol and thresholds are frozen in
``configs/experiments/E20_offline_gate.yaml``.  This script evaluates the
fixed A48/B64/C80 event designs with the existing exact fidelity kernel and
the existing binomial compute--uncompute finite-shot law.  Only A48 receives
the full C3 audit because it is the sole preregistered hardware-eligible
candidate; B64/C80 are scaling diagnostics and cannot become post-hoc
fallbacks.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import yaml
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.svm import SVC

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from qevc.auditing.claims import Claim, resolve_claim  # noqa: E402
from qevc.geometry.descriptors import effective_rank, psd_violation  # noqa: E402
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

CONFIG_PATH = REPO / "configs/experiments/E20_offline_gate.yaml"
E20 = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
E01 = yaml.safe_load((REPO / "configs/experiments/E01.yaml").read_text())
FROZEN = yaml.safe_load(
    (REPO / "configs/frozen/frozen_deployment_v1.yaml").read_text()
)
E13 = json.loads((REPO / "results/tables/E13_weighted_cs.json").read_text())
W_MAX = float(E13["part_b_benchmark"]["w_max"]["value"])
OUT_PATH = REPO / "results/tables/E20_offline_gate.json"


def stable_rng(*parts: object) -> np.random.Generator:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def parse_params(raw: dict) -> dict:
    out = {}
    for key, value in raw.items():
        try:
            out[key] = eval(value, {"__builtins__": {}})  # noqa: S307
        except Exception:
            out[key] = value
    return out


def stratified_order(labels: np.ndarray, seed: int, tag: str) -> tuple[np.ndarray, np.ndarray]:
    rng = stable_rng("E20", seed, tag)
    pos = rng.permutation(np.flatnonzero(labels == 1))
    neg = rng.permutation(np.flatnonzero(labels == 0))
    return pos, neg


def nested_indices(pos: np.ndarray, neg: np.ndarray, n: int) -> np.ndarray:
    n_pos = n // 2
    idx = np.concatenate([pos[:n_pos], neg[: n - n_pos]])
    return np.sort(idx)


def sample_matrix(
    exact: np.ndarray, shots: int, rng: np.random.Generator, symmetric: bool
) -> np.ndarray:
    if not symmetric:
        return rng.binomial(shots, np.clip(exact, 0.0, 1.0)) / shots
    out = np.eye(len(exact), dtype=float)
    iu = np.triu_indices(len(exact), 1)
    out[iu] = rng.binomial(shots, np.clip(exact[iu], 0.0, 1.0)) / shots
    out[(iu[1], iu[0])] = out[iu]
    return out


def weighted_accuracy(correct: np.ndarray, weights: np.ndarray) -> float:
    return float(np.dot(correct, weights) / weights.sum())


def majority(counts: Counter) -> str:
    best = max(counts.values())
    winners = [name for name, value in counts.items() if value == best]
    return winners[0] if len(winners) == 1 else "UNRESOLVED"


def audit_deployment(
    correct_by_env: dict[str, np.ndarray],
    weights_by_env: dict[str, np.ndarray],
    source_refs: dict[str, float],
) -> dict[str, dict]:
    cfg = E20["frozen_protocol"]["claims"]
    out: dict[str, dict] = {}
    for env, correct in correct_by_env.items():
        weights = weights_by_env[env]
        target = {
            "unweighted_accuracy": float(correct.mean()),
            "weighted_accuracy": weighted_accuracy(correct, weights),
        }
        for family in cfg["metric_families"]:
            source = source_refs[family]
            for delta in cfg["deltas"]:
                tau = float(np.clip(source - delta, 0.0, 1.0))
                truth = target[family] >= tau
                counts: Counter = Counter()
                false_cert = 0
                for audit_seed in range(cfg["audit_seeds"]):
                    rng = stable_rng("E20-audit", env, family, delta, audit_seed)
                    idx = rng.integers(0, len(correct), size=cfg["n_max"])
                    if family == "unweighted_accuracy":
                        cs = empirical_bernstein_cs(correct[idx], alpha=cfg["alpha"])
                        resolution = resolve_claim(Claim("accuracy", tau), cs)
                    else:
                        resolution = resolve_weighted_claim(
                            correct[idx], weights[idx], tau, W_MAX, alpha=cfg["alpha"]
                        )
                    verdict = resolution.verdict.value
                    counts[verdict] += 1
                    false_cert += int((not truth) and verdict == "SUPPORTED")
                key = f"{env}|{family}|delta={delta}"
                out[key] = {
                    "environment": env,
                    "family": family,
                    "delta": delta,
                    "source": source,
                    "target": target[family],
                    "tau": tau,
                    "margin": target[family] - tau,
                    "truth": bool(truth),
                    "verdict_counts": dict(counts),
                    "majority_verdict": majority(counts),
                    "false_certifications": false_cert,
                    "false_claim_audits": cfg["audit_seeds"] if not truth else 0,
                }
    return out


def audit_summary(audit: dict[str, dict]) -> dict:
    composition = Counter(v["majority_verdict"] for v in audit.values())
    false_cert = sum(v["false_certifications"] for v in audit.values())
    false_total = sum(v["false_claim_audits"] for v in audit.values())
    far_cut = E20["frozen_protocol"]["claims"]["margin_strata"]["far"]
    return {
        "unique_claims": len(audit),
        "composition": dict(composition),
        "unresolved_fraction": composition["UNRESOLVED"] / len(audit),
        "far_unique_claims": sum(abs(v["margin"]) >= far_cut for v in audit.values()),
        "false_certifications": false_cert,
        "false_claim_audits": false_total,
        "false_certification_fraction": false_cert / false_total if false_total else None,
    }


def relative_frob(observed: np.ndarray, exact: np.ndarray) -> float:
    return float(np.linalg.norm(observed - exact) / np.linalg.norm(exact))


def build_deployment(
    K_train: np.ndarray,
    K_cal: np.ndarray,
    K_targets: dict[str, np.ndarray],
    y_train: np.ndarray,
    w_train: np.ndarray,
    y_cal: np.ndarray,
    w_cal: np.ndarray,
    targets: dict[str, dict[str, np.ndarray]],
) -> dict:
    model = SVC(kernel="precomputed", C=1.0)
    model.fit(
        K_train,
        y_train,
        sample_weight=class_balanced_weights(y_train, w_train),
    )
    cal_scores = model.decision_function(K_cal.T)
    calibrator = PlattCalibrator().fit(cal_scores, y_cal, w_cal)
    cal_prob = calibrator.predict_proba(cal_scores)
    threshold = ba_optimal_threshold(y_cal, cal_prob, w_cal)
    cal_correct = ((cal_prob >= threshold).astype(int) == y_cal).astype(float)
    source_refs = {
        "unweighted_accuracy": float(cal_correct.mean()),
        "weighted_accuracy": weighted_accuracy(cal_correct, w_cal),
    }
    cal_pred = (cal_prob >= threshold).astype(int)
    source_metrics = {
        "n": len(y_cal),
        "auc": float(roc_auc_score(y_cal, cal_prob)),
        "weighted_auc": float(weighted_auc(y_cal, cal_prob, sample_weight=w_cal)),
        "balanced_accuracy": float(balanced_accuracy_score(y_cal, cal_pred)),
        "accuracy": float(cal_correct.mean()),
        "weighted_accuracy": weighted_accuracy(cal_correct, w_cal),
        "predicted_positive_fraction": float(cal_pred.mean()),
    }
    correct_by_env: dict[str, np.ndarray] = {}
    weights_by_env: dict[str, np.ndarray] = {}
    metrics = {}
    for env, K_cross in K_targets.items():
        y = targets[env]["y"]
        weights = targets[env]["w"]
        scores = model.decision_function(K_cross.T)
        prob = calibrator.predict_proba(scores)
        pred = (prob >= threshold).astype(int)
        correct = (pred == y).astype(float)
        correct_by_env[env] = correct
        weights_by_env[env] = weights
        metrics[env] = {
            "n": len(y),
            "auc": float(roc_auc_score(y, prob)),
            "weighted_auc": float(weighted_auc(y, prob, sample_weight=weights)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "accuracy": float(correct.mean()),
            "weighted_accuracy": weighted_accuracy(correct, weights),
            "predicted_positive_fraction": float(pred.mean()),
            "true_positive_rate": float(pred[y == 1].mean()),
            "true_negative_rate": float((1 - pred[y == 0]).mean()),
        }
    return {
        "threshold": float(threshold),
        "source_refs": source_refs,
        "source_metrics": source_metrics,
        "target_metrics": metrics,
        "correct_by_env": correct_by_env,
        "weights_by_env": weights_by_env,
    }


def strip_arrays(deployment: dict) -> dict:
    return {
        "threshold": deployment["threshold"],
        "source_refs": deployment["source_refs"],
        "source_metrics": deployment["source_metrics"],
        "target_metrics": deployment["target_metrics"],
    }


def movement_and_stability(
    exact_deployment: dict,
    noisy_deployment: dict,
    exact_audit: dict[str, dict],
    own_audit: dict[str, dict],
    fixed_audit: dict[str, dict],
) -> dict:
    source_moves = {
        family: noisy_deployment["source_refs"][family]
        - exact_deployment["source_refs"][family]
        for family in exact_deployment["source_refs"]
    }
    target_moves = {}
    conditions = {}
    informative = 0
    for key, ideal in exact_audit.items():
        env, family = ideal["environment"], ideal["family"]
        if (env, family) not in target_moves:
            exact_target = ideal["target"]
            if family == "unweighted_accuracy":
                noisy_target = float(noisy_deployment["correct_by_env"][env].mean())
            else:
                noisy_target = weighted_accuracy(
                    noisy_deployment["correct_by_env"][env],
                    noisy_deployment["weights_by_env"][env],
                )
            target_moves[(env, family)] = noisy_target - exact_target
        dmt = target_moves[(env, family)]
        dms = source_moves[family]
        m_star = ideal["margin"]
        dep_move = dmt - dms
        ideal_holds = abs(m_star) > abs(dmt)
        dep_holds = abs(m_star) > abs(dep_move)
        conditions[key] = {
            "m_star": m_star,
            "delta_m_s": dms,
            "delta_m_t": dmt,
            "delta_m_t_minus_delta_m_s": dep_move,
            "ideal_condition_holds": bool(ideal_holds),
            "deployment_condition_holds": bool(dep_holds),
            "ideal_truth_stable": ideal["truth"] == fixed_audit[key]["truth"],
            "deployment_truth_stable": ideal["truth"] == own_audit[key]["truth"],
            "ideal_verdict_stable": ideal["majority_verdict"]
            == fixed_audit[key]["majority_verdict"],
            "deployment_verdict_stable": ideal["majority_verdict"]
            == own_audit[key]["majority_verdict"],
        }
        verdicts = (
            ideal["majority_verdict"],
            own_audit[key]["majority_verdict"],
            fixed_audit[key]["majority_verdict"],
        )
        informative += int(all(v != "UNRESOLVED" for v in verdicts))
    return {
        "source_movements": source_moves,
        "target_movements": {
            f"{env}|{family}": value
            for (env, family), value in target_moves.items()
        },
        "informative_pairs": informative,
        "condition_summary": {
            "ideal_holds": sum(v["ideal_condition_holds"] for v in conditions.values()),
            "deployment_holds": sum(
                v["deployment_condition_holds"] for v in conditions.values()
            ),
            "n_claims": len(conditions),
        },
        "per_claim": conditions,
    }


def cost_and_memory(n_train: int) -> dict:
    protocol = E20["frozen_protocol"]
    n_cross_cols = protocol["n_calibration"] + 2 * protocol["n_target_per_environment"]
    train_circuits = n_train * (n_train - 1) // 2
    cross_circuits = n_train * n_cross_cols
    total = train_circuits + cross_circuits
    cost = E20["qpu_cost_model"]["seconds_per_circuit_at_1024"]
    shots = E20["offline_estimation"]["shots"]
    dense_bytes = 8 * (n_train * n_train + n_train * n_cross_cols)
    states_bytes = 16 * (n_train + n_cross_cols) * (2**8)
    raw_bytes = total * (2_132_199 / 714)  # empirical E16 raw-count density
    return {
        "n_cross_columns": n_cross_cols,
        "train_circuits": train_circuits,
        "cross_circuits": cross_circuits,
        "total_circuits": total,
        "total_shots": total * shots,
        "dense_matrix_megabytes": dense_bytes / 1e6,
        "statevector_working_megabytes": states_bytes / 1e6,
        "estimated_raw_counts_megabytes": raw_bytes / 1e6,
        "qpu_minutes_per_deployment": {
            name: total * seconds / 60 for name, seconds in cost.items()
        },
        "qpu_minutes_three_deployments": {
            name: 3 * total * seconds / 60 for name, seconds in cost.items()
        },
        "qpu_minutes_four_deployments": {
            name: 4 * total * seconds / 60 for name, seconds in cost.items()
        },
    }


def evaluate_candidate(
    candidate: dict,
    train_frame,
    train_order: tuple[np.ndarray, np.ndarray],
    calibration,
    targets,
    scaler,
    feature_map,
    full_audit: bool,
) -> dict:
    started = time.time()
    n_train = candidate["n_train"]
    idx = nested_indices(*train_order, n_train)
    train = train_frame.iloc[idx]
    q_cols = FROZEN["features"]["quantum"]
    Z_train = scaler.transform(train[q_cols].to_numpy(float))
    Z_cal = calibration["Z"]
    Z_targets = {env: data["Z"] for env, data in targets.items()}
    exact_started = time.time()
    K_train = kernel_exact(Z_train, feature_map)
    K_cal = kernel_exact(Z_train, feature_map, Z_cal)
    K_targets = {
        env: kernel_exact(Z_train, feature_map, Z) for env, Z in Z_targets.items()
    }
    exact_kernel_seconds = time.time() - exact_started
    exact = build_deployment(
        K_train,
        K_cal,
        K_targets,
        train["labels"].to_numpy(),
        train["weights"].to_numpy(),
        calibration["y"],
        calibration["w"],
        targets,
    )
    exact_audit = audit_deployment(
        exact["correct_by_env"], exact["weights_by_env"], exact["source_refs"]
    ) if full_audit else None
    shot_entries = []
    shots = E20["offline_estimation"]["shots"]
    for seed in E20["offline_estimation"]["kernel_seeds"]:
        noisy_train = sample_matrix(
            K_train, shots, stable_rng("E20", candidate["name"], seed, "train"), True
        )
        noisy_cal = sample_matrix(
            K_cal, shots, stable_rng("E20", candidate["name"], seed, "cal"), False
        )
        noisy_targets = {
            env: sample_matrix(
                matrix,
                shots,
                stable_rng("E20", candidate["name"], seed, "target", env),
                False,
            )
            for env, matrix in K_targets.items()
        }
        noisy = build_deployment(
            noisy_train,
            noisy_cal,
            noisy_targets,
            train["labels"].to_numpy(),
            train["weights"].to_numpy(),
            calibration["y"],
            calibration["w"],
            targets,
        )
        entry = {
            "seed": seed,
            "deployment": strip_arrays(noisy),
            "kernel": {
                "train_frob_rel_err": relative_frob(noisy_train, K_train),
                "calibration_frob_rel_err": relative_frob(noisy_cal, K_cal),
                "target_frob_rel_err": {
                    env: relative_frob(noisy_targets[env], K_targets[env])
                    for env in K_targets
                },
                "psd_violation": float(psd_violation(noisy_train)),
                "effective_rank": float(effective_rank(noisy_train)),
                "effective_rank_exact": float(effective_rank(K_train)),
            },
        }
        if full_audit:
            own = audit_deployment(
                noisy["correct_by_env"], noisy["weights_by_env"], noisy["source_refs"]
            )
            fixed = audit_deployment(
                noisy["correct_by_env"], noisy["weights_by_env"], exact["source_refs"]
            )
            entry["audit_own"] = audit_summary(own)
            entry["audit_fixed"] = audit_summary(fixed)
            entry["movement_and_stability"] = movement_and_stability(
                exact, noisy, exact_audit, own, fixed
            )
            entry["majority_flips"] = {
                "deployment_relative": sum(
                    own[k]["majority_verdict"] != exact_audit[k]["majority_verdict"]
                    for k in exact_audit
                ),
                "ideal_anchored": sum(
                    fixed[k]["majority_verdict"] != exact_audit[k]["majority_verdict"]
                    for k in exact_audit
                ),
            }
        shot_entries.append(entry)
    result = {
        "candidate": candidate,
        "train_row_ids": train["row_id"].to_numpy().tolist(),
        "cost_and_memory": cost_and_memory(n_train),
        "exact": {
            "deployment": strip_arrays(exact),
            "kernel": {
                "effective_rank": float(effective_rank(K_train)),
                "psd_violation": float(psd_violation(K_train)),
            },
            "audit": audit_summary(exact_audit) if full_audit else None,
        },
        "shot_deployments": shot_entries,
        "runtime": {
            "exact_kernel_seconds": exact_kernel_seconds,
            "candidate_total_seconds": time.time() - started,
        },
    }
    return result


def quantiles(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=float)
    return {
        "min": float(arr.min()),
        "q10": float(np.quantile(arr, 0.10)),
        "median": float(np.median(arr)),
        "q90": float(np.quantile(arr, 0.90)),
        "max": float(arr.max()),
    }


def aggregate_candidate(result: dict) -> dict:
    nominal_auc = [
        d["deployment"]["target_metrics"]["nominal"]["auc"]
        for d in result["shot_deployments"]
    ]
    worst_ba = [
        min(
            env["balanced_accuracy"]
            for env in d["deployment"]["target_metrics"].values()
        )
        for d in result["shot_deployments"]
    ]
    chance = [auc <= 0.55 or ba <= 0.50 for auc, ba in zip(nominal_auc, worst_ba)]
    out = {
        "nominal_auc": quantiles(nominal_auc),
        "worst_environment_ba": quantiles(worst_ba),
        "chance_fraction": float(np.mean(chance)),
        "train_frob_rel_err": quantiles(
            [d["kernel"]["train_frob_rel_err"] for d in result["shot_deployments"]]
        ),
        "effective_rank": quantiles(
            [d["kernel"]["effective_rank"] for d in result["shot_deployments"]]
        ),
    }
    if result["exact"]["audit"] is not None:
        out.update(
            {
                "supported_unique_claims": quantiles(
                    [
                        d["audit_own"]["composition"].get("SUPPORTED", 0)
                        for d in result["shot_deployments"]
                    ]
                ),
                "unresolved_fraction": quantiles(
                    [d["audit_own"]["unresolved_fraction"] for d in result["shot_deployments"]]
                ),
                "informative_pairs": quantiles(
                    [
                        d["movement_and_stability"]["informative_pairs"]
                        for d in result["shot_deployments"]
                    ]
                ),
                "deployment_relative_flips": quantiles(
                    [d["majority_flips"]["deployment_relative"] for d in result["shot_deployments"]]
                ),
                "ideal_anchored_flips": quantiles(
                    [d["majority_flips"]["ideal_anchored"] for d in result["shot_deployments"]]
                ),
            }
        )
    return out


def apply_primary_gate(primary: dict, aggregate: dict) -> dict:
    thresholds = E20["go_no_go"]
    exact_metrics = primary["exact"]["deployment"]["target_metrics"]
    exact_audit = primary["exact"]["audit"]
    cost = primary["cost_and_memory"]["qpu_minutes_three_deployments"]
    checks = {
        "exact_nominal_auc": exact_metrics["nominal"]["auc"]
        >= thresholds["exact_min_nominal_auc"],
        "exact_each_environment_auc": min(v["auc"] for v in exact_metrics.values())
        >= thresholds["exact_min_each_environment_auc"],
        "exact_each_environment_ba": min(
            v["balanced_accuracy"] for v in exact_metrics.values()
        )
        >= thresholds["exact_min_each_environment_ba"],
        "shot_median_nominal_auc": aggregate["nominal_auc"]["median"]
        >= thresholds["shot_min_median_nominal_auc"],
        "shot_q10_nominal_auc": aggregate["nominal_auc"]["q10"]
        >= thresholds["shot_min_q10_nominal_auc"],
        "shot_median_worst_environment_ba": aggregate["worst_environment_ba"]["median"]
        >= thresholds["shot_min_median_worst_environment_ba"],
        "shot_chance_fraction": aggregate["chance_fraction"]
        <= thresholds["shot_max_chance_fraction"],
        "exact_supported_unique_claims": exact_audit["composition"].get("SUPPORTED", 0)
        >= thresholds["exact_min_supported_unique_claims"],
        "exact_unresolved_fraction": exact_audit["unresolved_fraction"]
        <= thresholds["exact_max_unresolved_fraction"],
        "exact_far_unique_claims": exact_audit["far_unique_claims"]
        >= thresholds["exact_min_far_unique_claims"],
        "shot_median_supported_unique_claims": aggregate["supported_unique_claims"]["median"]
        >= thresholds["shot_min_median_supported_unique_claims"],
        "shot_median_unresolved_fraction": aggregate["unresolved_fraction"]["median"]
        <= thresholds["shot_max_median_unresolved_fraction"],
        "shot_median_informative_pairs": aggregate["informative_pairs"]["median"]
        >= thresholds["shot_min_median_informative_pairs"],
        "three_deployment_central_cost": cost["central"]
        <= thresholds["cost_max_three_deployment_central_minutes"],
        "three_deployment_high_cost": cost["high"]
        <= thresholds["cost_max_three_deployment_high_minutes"],
        "proposition4_quantities_archivable": all(
            d["movement_and_stability"]["per_claim"] for d in primary["shot_deployments"]
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "checks": checks,
        "failed": failed,
        "mechanical_decision": "GO" if not failed else "NO-GO",
    }


def main() -> int:
    started = time.time()
    config_hash = hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
    raw = load_raw_subset(REPO, E01["subset"])
    splits = get_raw_splits(REPO, raw, E01["splits"], experiment_tag="E01")
    nominal = build_environment_dataset(raw, Environment())
    train_role = nominal[np.isin(nominal["row_id"].to_numpy(), splits["train"])]
    train_frame = tier_a_frame(train_role, E01["tier_a"]["n_train"], E01["tier_a"]["seed"])
    source_val = nominal[np.isin(nominal["row_id"].to_numpy(), splits["source_val"])]
    nominal_test = nominal[np.isin(nominal["row_id"].to_numpy(), splits["nominal_test"])]
    seed = E20["frozen_protocol"]["event_seed"]

    train_order = stratified_order(train_frame["labels"].to_numpy(), seed, "train")
    cal_order = stratified_order(source_val["labels"].to_numpy(), seed, "calibration")
    target_order = stratified_order(nominal_test["labels"].to_numpy(), seed, "target")
    cal_idx = nested_indices(*cal_order, E20["frozen_protocol"]["n_calibration"])
    target_idx = nested_indices(
        *target_order, E20["frozen_protocol"]["n_target_per_environment"]
    )
    calibration_df = source_val.iloc[cal_idx].sort_values("row_id")
    target_row_ids = np.sort(nominal_test.iloc[target_idx]["row_id"].to_numpy())

    q_cols = FROZEN["features"]["quantum"]
    scaler = AngleScaler().fit(train_frame[q_cols].to_numpy(float))
    params = parse_params(FROZEN["hyperparameters"]["tier_a"]["qksvc"])
    feature_map = build_feature_map(
        len(q_cols),
        reps=params["reps"],
        entanglement=params["entanglement"],
        scale=params["scale"],
    )
    calibration = {
        "Z": scaler.transform(calibration_df[q_cols].to_numpy(float)),
        "y": calibration_df["labels"].to_numpy(),
        "w": calibration_df["weights"].to_numpy(),
        "row_ids": calibration_df["row_id"].to_numpy().tolist(),
    }
    targets = {}
    for env, environment in {
        "nominal": Environment(),
        "tes=0.98": Environment(tes=0.98),
    }.items():
        frame = build_environment_dataset(raw, environment, row_ids=target_row_ids).sort_values("row_id")
        targets[env] = {
            "Z": scaler.transform(frame[q_cols].to_numpy(float)),
            "y": frame["labels"].to_numpy(),
            "w": frame["weights"].to_numpy(),
            "row_ids": frame["row_id"].to_numpy().tolist(),
        }

    results = {}
    primary_name = E20["frozen_protocol"]["primary_hardware_candidate"]
    for candidate in E20["frozen_protocol"]["candidates"]:
        print(f"E20 offline: evaluating {candidate['name']}", flush=True)
        result = evaluate_candidate(
            candidate,
            train_frame,
            train_order,
            calibration,
            targets,
            scaler,
            feature_map,
            full_audit=candidate["name"] == primary_name,
        )
        result["aggregate"] = aggregate_candidate(result)
        results[candidate["name"]] = result
        print(
            f"  exact nominal AUC={result['exact']['deployment']['target_metrics']['nominal']['auc']:.3f}; "
            f"shot median={result['aggregate']['nominal_auc']['median']:.3f}",
            flush=True,
        )

    primary = results[primary_name]
    gate = apply_primary_gate(primary, primary["aggregate"])
    out = {
        "experiment": "E20",
        "arm": "offline_gate_only",
        "qpu_jobs_submitted": 0,
        "config_path": str(CONFIG_PATH.relative_to(REPO)).replace("\\", "/"),
        "config_sha256": config_hash,
        "event_provenance": {
            "seed": seed,
            "calibration_row_ids": calibration["row_ids"],
            "calibration_weight_diagnostics": {
                "sum": float(calibration["w"].sum()),
                "max_over_mean": float(calibration["w"].max() / calibration["w"].mean()),
                "effective_sample_size": float(
                    calibration["w"].sum() ** 2 / np.square(calibration["w"]).sum()
                ),
                "positive_weight_fraction": float(
                    calibration["w"][calibration["y"] == 1].sum()
                    / calibration["w"].sum()
                ),
            },
            "target_row_ids": target_row_ids.tolist(),
            "target_rows_paired_across_environments": True,
        },
        "candidates": results,
        "primary_gate": gate,
        "wall_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(gate, indent=2), flush=True)
    print(f"wrote {OUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
