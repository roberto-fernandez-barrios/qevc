"""Derive deployment-level Proposition 4 summaries from the frozen E16 JSON.

This script performs no simulation, fitting, kernel repair, or random draw.  It
only aggregates the already committed condition cells and paired audit-stream
outcomes in ``E16_proposition4_instantiation.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
OUTPUT = ROOT / "results" / "tables" / "E16_proposition4_deployment_summary.json"

REGIMES = ("raw", "psd_repaired")
SEMANTICS = ("deployment_relative", "ideal_anchored")
STATUSES = ("HOLDS", "FAILS")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def linear_quantile(values: list[float], probability: float) -> float:
    """Return the type-7/linear sample quantile used for the descriptive IQR."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def summarize(values: list[float | None]) -> dict[str, float | int]:
    observed = [value for value in values if value is not None]
    if not observed:
        raise ValueError("Cannot summarize an empty deployment-level quantity")
    q1 = linear_quantile(observed, 0.25)
    q3 = linear_quantile(observed, 0.75)
    return {
        "n_deployments_contributing": len(observed),
        "median": statistics.median(observed),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "min": min(observed),
        "max": max(observed),
        "mean": statistics.mean(observed),
        "sample_sd": statistics.stdev(observed) if len(observed) > 1 else 0.0,
    }


def conditional_audit_flip_rate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    streams = [stream for row in rows for stream in row["audit_streams"]]
    numerator = sum(bool(stream["verdict_flip"]) for stream in streams)
    denominator = len(streams)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def conditional_truth_sign_flip_rate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    flips = [bool(row["ideal_truth"] != row["realized_truth"]) for row in rows]
    for row, flip in zip(rows, flips, strict=True):
        if any(bool(stream["truth_sign_flip"]) != flip for stream in row["audit_streams"]):
            raise ValueError("Audit-stream truth_sign_flip disagrees with its condition cell")
    numerator = sum(flips)
    denominator = len(flips)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def derive(source_payload: dict[str, Any], source_digest: str) -> dict[str, Any]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_payload["cases"]:
        grouped[(row["deployment_id"], row["regime"], row["claim_semantics"])].append(row)

    deployment_ids = sorted({key[0] for key in grouped})
    expected = {
        (deployment_id, regime, semantics)
        for deployment_id in deployment_ids
        for regime in REGIMES
        for semantics in SEMANTICS
    }
    if set(grouped) != expected:
        raise ValueError("Incomplete deployment x regime x semantics grid")
    if len(deployment_ids) != 30:
        raise ValueError(f"Expected 30 noisy-kernel deployments, found {len(deployment_ids)}")

    per_deployment: list[dict[str, Any]] = []
    for (deployment_id, regime, semantics), rows in grouped.items():
        rows = sorted(
            rows,
            key=lambda row: (
                row["environment"],
                row["metric_family"],
                row["metric"],
                row["delta"],
            ),
        )
        if len(rows) != 60:
            raise ValueError(
                f"Expected 60 cells for {deployment_id}/{regime}/{semantics}, "
                f"found {len(rows)}"
            )
        if any(row["sufficient_condition_status"] not in STATUSES for row in rows):
            raise ValueError("Deployment aggregation requires every condition cell to be evaluable")

        status_rows = {
            status: [row for row in rows if row["sufficient_condition_status"] == status]
            for status in STATUSES
        }
        shot_budgets = {row["shot_budget"] for row in rows}
        kernel_seeds = {row["kernel_seed"] for row in rows}
        if len(shot_budgets) != 1 or len(kernel_seeds) != 1:
            raise ValueError("Deployment identifier maps to multiple shot budgets or kernel seeds")

        cell_counts = {status: len(status_rows[status]) for status in STATUSES}
        per_deployment.append(
            {
                "deployment_id": deployment_id,
                "shot_budget": shot_budgets.pop(),
                "kernel_seed": kernel_seeds.pop(),
                "regime": regime,
                "claim_semantics": semantics,
                "evaluable_condition_cells": len(rows),
                "condition_cell_counts": cell_counts,
                "condition_cell_fractions": {
                    status: cell_counts[status] / len(rows) for status in STATUSES
                },
                "audit_verdict_flip": {
                    status: conditional_audit_flip_rate(status_rows[status])
                    for status in STATUSES
                },
                "truth_sign_flip": {
                    status: conditional_truth_sign_flip_rate(status_rows[status])
                    for status in STATUSES
                },
            }
        )

    per_deployment.sort(
        key=lambda row: (
            row["shot_budget"],
            row["kernel_seed"],
            REGIMES.index(row["regime"]),
            SEMANTICS.index(row["claim_semantics"]),
        )
    )

    across_deployments: dict[str, dict[str, dict[str, Any]]] = {}
    for regime in REGIMES:
        across_deployments[regime] = {}
        for semantics in SEMANTICS:
            selected = [
                row
                for row in per_deployment
                if row["regime"] == regime and row["claim_semantics"] == semantics
            ]
            across_deployments[regime][semantics] = {
                "n_noisy_kernel_deployments": len(selected),
                "evaluable_condition_cells_per_deployment": summarize(
                    [float(row["evaluable_condition_cells"]) for row in selected]
                ),
                "condition_cell_fractions": {
                    status: summarize(
                        [row["condition_cell_fractions"][status] for row in selected]
                    )
                    for status in STATUSES
                },
                "audit_verdict_flip_rates": {
                    status: summarize(
                        [row["audit_verdict_flip"][status]["rate"] for row in selected]
                    )
                    for status in STATUSES
                },
                "truth_sign_flip_rates": {
                    status: summarize(
                        [row["truth_sign_flip"][status]["rate"] for row in selected]
                    )
                    for status in STATUSES
                },
            }

    payload: dict[str, Any] = {
        "analysis": "E16 Proposition 4 deployment-level descriptive aggregation",
        "status": "DERIVED SUMMARY ONLY",
        "independent_descriptive_unit": "noisy-kernel deployment",
        "population_inference": "none",
        "source": {
            "path": "results/tables/E16_proposition4_instantiation.json",
            "sha256": source_digest,
        },
        "derivation_guards": {
            "no_new_randomness": True,
            "no_new_experiment": True,
            "no_new_kernel_repair": True,
            "no_new_inference": True,
            "source_artifact_unchanged": True,
            "quantiles": "linear/type-7",
            "sample_sd_ddof": 1,
        },
        "accounting": {
            "noisy_kernel_deployments": len(deployment_ids),
            "regimes": list(REGIMES),
            "claim_semantics": list(SEMANTICS),
            "condition_cells_per_deployment_regime_semantics_slice": 60,
            "audit_streams_per_condition_cell": 10,
            "correlation_warning": (
                "Cells and audit streams share each deployment's realized Gram, refit, "
                "calibration, threshold and paired common-random-number streams."
            ),
        },
        "per_deployment": per_deployment,
        "across_deployments": across_deployments,
    }
    payload["reproducibility"] = {
        "canonical_payload_sha256": canonical_json_sha256(payload)
    }
    return payload


def expected_payload() -> dict[str, Any]:
    source_payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    return derive(source_payload, sha256(SOURCE))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify the committed output")
    parser.add_argument("--write", action="store_true", help="write the derived output")
    args = parser.parse_args()
    if args.check == args.write:
        parser.error("choose exactly one of --check or --write")

    expected = expected_payload()
    if args.write:
        OUTPUT.write_text(
            json.dumps(expected, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")
        return 0

    observed = json.loads(OUTPUT.read_text(encoding="utf-8"))
    if observed != expected:
        raise SystemExit("Committed deployment summary does not reproduce the frozen source")
    print(
        "Deployment summary exactly reproduces the frozen Proposition 4 JSON: "
        f"{len(expected['per_deployment'])} slice rows over 30 noisy-kernel deployments"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
