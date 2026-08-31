"""Derive deployment-level E16 summaries from the immutable E16 artifact.

The independent empirical unit is one noisy-kernel deployment.  Claim-level
verdicts within a deployment share the same realized Gram matrix, refit,
calibration, threshold and audit streams, so they are not treated as IID
replicates.  This script performs no experiment and consumes no raw QPU data.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "tables" / "E16_quantum_uncertainty.json"
OUTPUT = ROOT / "results" / "tables" / "E16_deployment_level.json"


def rounded(value: float) -> float:
    return round(float(value), 4)


def summarize(values: list[float]) -> dict[str, float | int | list[float]]:
    loo = [statistics.mean(values[:i] + values[i + 1 :]) for i in range(len(values))]
    return {
        "n_deployments": len(values),
        "mean": rounded(statistics.mean(values)),
        "sample_sd": rounded(statistics.stdev(values)),
        "median": rounded(statistics.median(values)),
        "range": [rounded(min(values)), rounded(max(values))],
        "nonzero_deployments": sum(value > 0 for value in values),
        "leave_one_deployment_out_mean_range": [rounded(min(loo)), rounded(max(loo))],
    }


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    source = json.loads(source_bytes)
    by_shots: dict[str, object] = {}

    metrics = {
        "far_flip_rate_own_tau": ("far", "flip_rate_own_tau"),
        "far_flip_rate_fixed_tau": ("far", "flip_rate_fixed_tau"),
        "moderate_flip_rate_own_tau": ("moderate", "flip_rate_own_tau"),
        "moderate_flip_rate_fixed_tau": ("moderate", "flip_rate_fixed_tau"),
        "near_abstention": ("near", "abstention"),
    }

    for shots in (128, 256, 512, 1024, 2048, 4096):
        deployments = []
        for seed in range(1, 6):
            row = source["per_config"][f"shots{shots}|k{seed}"]
            deployment = {
                "kernel_seed": seed,
                "frob_rel_err": row["kernel"]["frob_rel_err"],
                "nominal_auc": row["nominal_auc"],
                "m_s_shift_w": row["m_s_shift_w"],
            }
            for name, (stratum, field) in metrics.items():
                deployment[name] = row["strata"][stratum][field]
            deployments.append(deployment)

        summaries = {
            name: summarize([float(row[name]) for row in deployments])
            for name in metrics
        }
        by_shots[str(shots)] = {
            "n_independent_deployments": len(deployments),
            "claims_evaluated_per_deployment": {"far": 200, "moderate": 170, "near": 230},
            "per_seed": deployments,
            "deployment_level_summary": summaries,
        }

    out = {
        "analysis": "E16 deployment-level descriptive reanalysis",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
        "independent_unit": "one noisy quantum-kernel deployment",
        "dependence_note": (
            "Claims within a deployment share the realized Gram matrix, refit, "
            "calibration, threshold and audit streams; claim counts are not IID replicates. "
            "Kernel realizations use independent RNG keys, while audit streams are paired "
            "across deployments, so cross-deployment verdict comparisons also share CRN."
        ),
        "scope": (
            "Descriptive mean, sample SD, range and leave-one-deployment-out "
            "sensitivity across five deployments per shot budget; no population "
            "confidence interval or monotonic trend claim."
        ),
        "n_independent_deployments_total": 30,
        "by_shots": by_shots,
    }
    OUTPUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
