from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from qevc.auditing.stability import (
    FAILS,
    HOLDS,
    NOT_EVALUABLE,
    canonical_json_sha256,
    opposite_resolved_verdict,
    sufficient_condition_status,
    summarize_proposition4_cases,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_e16_psd_sensitivity.py"
PRIMARY = ROOT / "results" / "tables" / "E16_quantum_uncertainty.json"
ARTIFACT = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
DEPLOYMENT_SUMMARY = (
    ROOT / "results" / "tables" / "E16_proposition4_deployment_summary.json"
)
DEPLOYMENT_SUMMARY_SCRIPT = (
    ROOT / "scripts" / "summarize_e16_proposition4_deployments.py"
)


def _case(status: str, flips: list[bool]) -> dict:
    return {
        "deployment_id": "shots128|k1",
        "sufficient_condition_status": status,
        "audit_streams": [
            {
                "audit_seed": seed,
                "verdict_flip": flip,
                "opposite_resolved_verdict": False,
            }
            for seed, flip in enumerate(flips)
        ],
    }


def test_strict_condition_classification_and_not_evaluable() -> None:
    assert sufficient_condition_status(0.05, 0.049) == HOLDS
    assert sufficient_condition_status(0.05, 0.05) == FAILS
    assert sufficient_condition_status(0.05, 0.08) == FAILS
    assert sufficient_condition_status(float("nan"), 0.01) == NOT_EVALUABLE
    assert sufficient_condition_status(0.05, 0.01, evaluable=False) == NOT_EVALUABLE


def test_failure_is_not_treated_as_a_predicted_flip() -> None:
    summary = summarize_proposition4_cases([_case(FAILS, [False, False])])
    assert summary["verdict_flip_contingency"][FAILS] == {
        "flip": 0,
        "no_flip": 2,
    }


def test_condition_hold_and_flip_outcomes_are_classified_independently() -> None:
    summary = summarize_proposition4_cases(
        [_case(HOLDS, [False, True]), _case(FAILS, [False, True])]
    )
    assert summary["verdict_flip_contingency"][HOLDS] == {
        "flip": 1,
        "no_flip": 1,
    }
    assert summary["verdict_flip_contingency"][FAILS] == {
        "flip": 1,
        "no_flip": 1,
    }


def test_opposite_resolved_verdict_excludes_abstention_transitions() -> None:
    assert opposite_resolved_verdict("SUPPORTED", "REFUTED") is True
    assert opposite_resolved_verdict("REFUTED", "SUPPORTED") is True
    assert opposite_resolved_verdict("SUPPORTED", "UNRESOLVED") is False
    assert opposite_resolved_verdict("UNRESOLVED", "REFUTED") is False


def test_canonical_reproduction_is_exact() -> None:
    payload = {"z": [3, 2, 1], "a": {"beta": 2, "alpha": "ñ"}}
    assert canonical_json_sha256(payload) == canonical_json_sha256(copy.deepcopy(payload))


def test_instantiation_script_has_no_qpu_submission_path() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    forbidden = {
        "qiskit_ibm_runtime",
        "IBMRuntimeService",
        "SamplerV2",
        "run_e16_hw_submit",
    }
    assert not (imports & forbidden)
    assert "qiskit_ibm_runtime" not in source
    assert "IBMRuntimeService" not in source
    assert "SamplerV2" not in source
    assert "sampler.run(" not in source
    assert "backend.run(" not in source


def test_committed_artifact_reproduces_its_canonical_hash_and_primary_input() -> None:
    if not ARTIFACT.exists():
        return
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    expected = payload["reproducibility"].pop("canonical_payload_sha256")
    assert canonical_json_sha256(payload) == expected
    observed_primary = hashlib.sha256(PRIMARY.read_bytes()).hexdigest().upper()
    assert payload["provenance"]["input_sha256"]["primary_e16"] == observed_primary
    assert payload["provenance"]["primary_artifacts_unchanged_after_analysis"] is True
    assert payload["provenance"]["no_new_randomness"] is True
    assert payload["provenance"]["no_new_qpu_jobs"] is True


def test_committed_cases_exactly_reproduce_all_requested_aggregates() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    cases = payload["cases"]
    aggregates = payload["aggregate_summaries"]

    def selected(**filters: str) -> list[dict]:
        return [
            row
            for row in cases
            if all(row[field] == value for field, value in filters.items())
        ]

    assert aggregates["overall"] == summarize_proposition4_cases(cases)
    for regime in ("raw", "psd_repaired"):
        assert aggregates["by_regime"][regime] == summarize_proposition4_cases(
            selected(regime=regime)
        )
    for semantics in ("deployment_relative", "ideal_anchored"):
        assert aggregates["by_claim_semantics"][semantics] == summarize_proposition4_cases(
            selected(claim_semantics=semantics)
        )
    for stratum in ("far", "moderate", "near"):
        assert aggregates["by_stratum"][stratum] == summarize_proposition4_cases(
            selected(stratum=stratum)
        )

    for regime in ("raw", "psd_repaired"):
        for semantics in ("deployment_relative", "ideal_anchored"):
            assert aggregates["by_regime_and_claim_semantics"][regime][semantics] == (
                summarize_proposition4_cases(
                    selected(regime=regime, claim_semantics=semantics)
                )
            )
            for stratum in ("far", "moderate", "near"):
                assert aggregates["by_regime_claim_semantics_and_stratum"][regime][
                    semantics
                ][stratum] == summarize_proposition4_cases(
                    selected(
                        regime=regime,
                        claim_semantics=semantics,
                        stratum=stratum,
                    )
                )
        for stratum in ("far", "moderate", "near"):
            assert aggregates["by_regime_and_stratum"][regime][stratum] == (
                summarize_proposition4_cases(
                    selected(regime=regime, stratum=stratum)
                )
            )

    for semantics in ("deployment_relative", "ideal_anchored"):
        for stratum in ("far", "moderate", "near"):
            assert aggregates["by_claim_semantics_and_stratum"][semantics][stratum] == (
                summarize_proposition4_cases(
                    selected(claim_semantics=semantics, stratum=stratum)
                )
            )

    for row in cases:
        assert row["sufficient_condition_status"] == sufficient_condition_status(
            row["ideal_margin"], row["condition_movement"]
        )
        assert row["margin_identity_verified"] is True


def test_all_recorded_protected_inputs_remain_byte_identical() -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    declared_inputs = {
        "primary_e16": ROOT / "results" / "tables" / "E16_quantum_uncertainty.json",
        "e01_config": ROOT / "configs" / "experiments" / "E01.yaml",
        "e16_config": ROOT / "configs" / "experiments" / "E16.yaml",
        "frozen_deployment": ROOT / "configs" / "frozen" / "frozen_deployment_v1.yaml",
        "frozen_e16_runner": ROOT / "experiments" / "E16_quantum_uncertainty" / "run_e16.py",
        "weighted_cs_results": ROOT / "results" / "tables" / "E13_weighted_cs.json",
        "instantiation_script": SCRIPT,
    }
    for key, path in declared_inputs.items():
        observed = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        assert observed == payload["provenance"]["input_sha256"][key], key

    recorded = {
        **payload["provenance"]["protected_table_sha256"],
        **payload["provenance"]["hardware_raw_sha256"],
    }
    for relative_path, expected in recorded.items():
        protected_path = ROOT / relative_path
        if not protected_path.is_file():
            assert relative_path in payload["provenance"]["hardware_raw_sha256"]
            assert relative_path.startswith("results/raw/E16_hw/")
            continue
        observed = hashlib.sha256(protected_path.read_bytes()).hexdigest().upper()
        assert observed == expected, relative_path


def test_deployment_summary_exactly_reproduces_frozen_instantiation() -> None:
    completed = subprocess.run(
        [sys.executable, str(DEPLOYMENT_SUMMARY_SCRIPT), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    summary = json.loads(DEPLOYMENT_SUMMARY.read_text(encoding="utf-8"))
    assert summary["independent_descriptive_unit"] == "noisy-kernel deployment"
    assert summary["accounting"] == {
        "noisy_kernel_deployments": 30,
        "regimes": ["raw", "psd_repaired"],
        "claim_semantics": ["deployment_relative", "ideal_anchored"],
        "condition_cells_per_deployment_regime_semantics_slice": 60,
        "audit_streams_per_condition_cell": 10,
        "correlation_warning": (
            "Cells and audit streams share each deployment's realized Gram, refit, "
            "calibration, threshold and paired common-random-number streams."
        ),
    }
    assert all(
        row["truth_sign_flip"]["HOLDS"]["numerator"] == 0
        for row in summary["per_deployment"]
    )
