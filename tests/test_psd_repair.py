from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np

from qevc.kernels.psd import minimum_diagonal_loading, spectral_audit


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_e16_psd_sensitivity.py"
PRIMARY = ROOT / "results" / "tables" / "E16_quantum_uncertainty.json"


def test_minimum_diagonal_loading_is_psd_and_does_not_mutate_raw() -> None:
    raw = np.array([[1.0, 1.4, 0.2], [1.4, 1.0, 0.8], [0.2, 0.8, 1.0]])
    frozen = raw.copy()
    repair = minimum_diagonal_loading(raw)

    assert np.array_equal(raw, frozen)
    assert repair.loading > 0.0
    assert repair.lambda_min_after > 0.0
    mask = ~np.eye(len(raw), dtype=bool)
    assert np.array_equal(repair.matrix[mask], raw[mask])
    assert np.allclose(np.diag(repair.matrix), np.diag(raw) + repair.loading)
    assert spectral_audit(repair.matrix)["negative_modes"] == 0


def test_minimum_diagonal_loading_is_deterministic() -> None:
    raw = np.array([[1.0, 1.2], [1.2, 1.0]], dtype=np.float32)
    first = minimum_diagonal_loading(raw)
    second = minimum_diagonal_loading(raw)
    assert first.loading == second.loading
    assert first.epsilon == second.epsilon
    assert np.array_equal(first.matrix, second.matrix)


def test_psd_sensitivity_script_has_no_qpu_submission_path() -> None:
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
    assert "sampler.run(" not in source
    assert "backend.run(" not in source


def test_archived_primary_hash_matches_derived_provenance_when_present() -> None:
    derived = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
    if not derived.exists():
        return
    payload = json.loads(derived.read_text(encoding="utf-8"))
    observed = hashlib.sha256(PRIMARY.read_bytes()).hexdigest().upper()
    assert payload["provenance"]["primary_e16_sha256"] == observed
    assert payload["raw_replay_validation"]["all_30_primary_rows_match"] is True
    missing_raw = [
        relative
        for relative in payload["provenance"]["hardware_raw_sha256"]
        if not (ROOT / relative).is_file()
    ]
    if missing_raw:
        # The hardware raw directory is deliberately gitignored and is not
        # part of a source-only CI checkout.  Its archived hashes remain in
        # the derived artifact and are checked whenever those files exist.
        return
    for relative, expected in payload["provenance"]["hardware_raw_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper() == expected


def test_psd_patch_did_not_reopen_e20() -> None:
    payload = json.loads(
        (ROOT / "results" / "tables" / "E20_offline_gate.json").read_text(encoding="utf-8")
    )
    assert payload["arm"] == "offline_gate_only"
    assert payload["qpu_jobs_submitted"] == 0


def test_archived_summary_is_reproducible_from_per_deployment_rows_when_present() -> None:
    derived = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
    if not derived.exists():
        return
    payload = json.loads(derived.read_text(encoding="utf-8"))
    for shots, summary in payload["aggregate_by_shots"].items():
        rows = [
            row for row in payload["per_deployment"].values()
            if row["shot_budget"] == int(shots)
        ]
        assert len(rows) == summary["n_deployments"] == 5
        raw = np.array([row["raw"]["claims"]["far"]["deployment_relative"]["flip_rate_vs_ideal"] for row in rows])
        repaired = np.array([row["psd_repaired"]["claims"]["far"]["deployment_relative"]["flip_rate_vs_ideal"] for row in rows])
        assert round(float(raw.mean()), 8) == summary["raw_far_c_dep_flip_rate"]["mean"]
        assert round(float(repaired.mean()), 8) == summary["psd_far_c_dep_flip_rate"]["mean"]
