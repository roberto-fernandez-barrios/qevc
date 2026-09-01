"""Regression tests for the bounded 0.3.6 mechanistic-clarity / derived-analysis patch.

Every check here is deterministic and reads only committed artifacts; none of
the tests runs a replay, a QPU job or any randomness.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
MAIN = (ROOT / "manuscript" / "latex" / "main.tex").read_text(encoding="utf-8")
SUPP = (ROOT / "manuscript" / "supplementary" / "supplement.tex").read_text(encoding="utf-8")
BIB = (ROOT / "manuscript" / "bibliography" / "references.bib").read_text(encoding="utf-8")
FLAT_MAIN = re.sub(r"\s+", " ", MAIN)

STAGE_SCRIPT = ROOT / "scripts" / "analyze_e16_stage_decomposition.py"
STRAT_SCRIPT = ROOT / "scripts" / "summarize_e16_prop3_margin_stratification.py"
WMAX_SCRIPT = ROOT / "scripts" / "analyze_wmax_nominal_bound_sensitivity.py"
STAGE = json.loads((TABLES / "E16_stage_decomposition.json").read_text(encoding="utf-8"))
STRAT = json.loads((TABLES / "E16_prop3_margin_stratification.json").read_text(encoding="utf-8"))
WMAX = json.loads((TABLES / "E13_wmax_nominal_bound_sensitivity.json").read_text(encoding="utf-8"))

DERIVED_0_3_6 = {
    "results/tables/E16_stage_decomposition.json",
    "results/tables/E16_prop3_margin_stratification.json",
    "results/tables/E13_wmax_nominal_bound_sensitivity.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


# --------------------------------------------------------------------- E16 stage decomposition

def test_stage_decomposition_reproduces_all_30_original_deployments() -> None:
    rep = STAGE["reproduction"]
    assert rep["all_raw_stage_D_match_primary"] is True
    assert len(rep["raw_stage_D_matches_primary_per_config"]) == 30
    assert all(rep["raw_stage_D_matches_primary_per_config"].values())
    assert rep["all_raw_stage_D_match_psd_archive"] is True
    assert rep["all_psd_stage_D_match_psd_archive"] is True
    assert len(rep["psd_stage_D_matches_psd_archive_payload"]) == 30
    assert rep["prop3_movement_max_abs_residual"] == {"raw": 0.0, "psd_repaired": 0.0}
    assert rep["prop3_movement_cells_compared"] == {"raw": 1800, "psd_repaired": 1800}
    assert rep["platt_slopes_positive"] is True


def test_stage_decomposition_telescoping_identities() -> None:
    for key, entry in STAGE["per_deployment"].items():
        for regime in ("raw", "psd_repaired"):
            stages = entry[regime]["stages"]
            for family_key, field in (("m_s_unw", "unweighted_accuracy"), ("m_s_w", "weighted_accuracy")):
                inc = entry[regime]["source_metric_increments"][family_key]
                ideal = STAGE["ideal"]["source"][field]
                path = [ideal] + [stages[s]["source"][field] for s in ("B0", "B", "C", "D")]
                increments = [b - a for a, b in zip(path[:-1], path[1:])]
                for name, value in zip(("fit", "eval", "cal", "thr"), increments):
                    assert abs(inc[name] - value) < 1e-12, (key, regime, name)
                assert abs(inc["total_delta_M_S"] - (path[-1] - path[0])) < 1e-12
                assert abs(inc["telescoping_residual"]) < 1e-12
    assert len(STAGE["per_deployment"]) == 30


def test_stage_decomposition_classification_is_predeclared_and_recomputable() -> None:
    rule = STAGE["classification"]["rule"]
    assert rule["dominance_share"] == 0.5
    for regime in ("raw", "psd_repaired"):
        agg = STAGE["aggregate_by_regime"][regime]
        families = STAGE["classification"]["by_regime"][regime]["families"]
        for family_key in ("m_s_unw", "m_s_w"):
            metric_share = agg["group_metric_shares"][family_key]
            flip_share = agg["ideal_anchored_flip_path"]["far"]["positive_share"]
            dominant = [
                g for g in ("MODEL/RANKING", "CALIBRATION", "THRESHOLD")
                if metric_share[g] >= 0.5 and flip_share[g] >= 0.5
            ]
            expected = dominant[0] if len(dominant) == 1 else None
            assert families[family_key]["dominant_group"] == expected
    assert STAGE["classification"]["by_regime"]["raw"]["label"] == "MIXED"
    assert STAGE["classification"]["by_regime"]["psd_repaired"]["label"] == "MODEL/RANKING-DOMINATED"
    assert STAGE["classification"]["overall"] == "MIXED"


def test_stage_decomposition_declares_provenance_and_no_new_randomness() -> None:
    prov = STAGE["provenance"]
    assert prov["no_new_randomness"] is True
    assert prov["no_new_qpu_jobs"] is True
    assert prov["deterministic_replay_of_archived_seed_schedule_only"] is True
    assert prov["protected_artifacts_unchanged_after_analysis"] is True
    assert STAGE["status"] == "DERIVED / NO NEW RANDOMNESS"
    for name, relpath in (
        ("primary_e16", "results/tables/E16_quantum_uncertainty.json"),
        ("psd_sensitivity", "results/tables/E16_psd_sensitivity.json"),
        ("proposition3_instantiation", "results/tables/E16_proposition4_instantiation.json"),
        ("e16_config", "configs/experiments/E16.yaml"),
        ("frozen_deployment", "configs/frozen/frozen_deployment_v1.yaml"),
        ("frozen_e16_runner", "experiments/E16_quantum_uncertainty/run_e16.py"),
        ("weighted_cs_results", "results/tables/E13_weighted_cs.json"),
        ("stage_decomposition_script", "scripts/analyze_e16_stage_decomposition.py"),
    ):
        assert prov["input_sha256"][name] == sha256(ROOT / relpath), name
    for relpath, digest in prov["protected_table_sha256"].items():
        assert sha256(ROOT / relpath) == digest, relpath


def test_derived_scripts_introduce_no_new_seeds_and_no_qpu_path() -> None:
    for script in (STAGE_SCRIPT, STRAT_SCRIPT, WMAX_SCRIPT):
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert not imports & {"qiskit_ibm_runtime", "IBMRuntimeService", "SamplerV2"}
        assert "qiskit_ibm_runtime" not in source
        assert "sampler.run(" not in source and "backend.run(" not in source
        # No fresh generator is seeded anywhere in the derived scripts: the only RNG
        # use is the frozen E16 schedule (e16.stable_rng) and the frozen E13/E19
        # stream salts inside the frozen runners.
        assert "default_rng(" not in source
        assert "np.random.seed" not in source and "random.seed" not in source


# --------------------------------------------------------------------- Proposition 3 stratification

def test_margin_stratification_reproduces_all_7200_cells() -> None:
    completed = subprocess.run(
        [sys.executable, str(STRAT_SCRIPT), "--check"],
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert STRAT["totals"] == {
        "condition_cells": 7200, "audit_streams": 72000,
        "holds_cells": 4943, "fails_cells": 2257,
    }
    for claim in ("deployment_relative", "ideal_anchored"):
        cells = sum(
            STRAT["by_claim_semantics"][claim][b][s]["cells"]
            for b in STRAT["bins"]["labels"] for s in ("HOLDS", "FAILS")
        )
        assert cells == 3600
    assert STRAT["largest_abs_ideal_margin_among_FAILS_cells"]["deployment_relative"] < 0.005
    assert STRAT["source_sha256"] == sha256(TABLES / "E16_proposition4_instantiation.json")


# --------------------------------------------------------------------- w_max sensitivity

def test_wmax_historical_results_unchanged_and_sensitivity_marked_post_hoc() -> None:
    assert WMAX["E13_part_b"]["historical_replay_exact"] is True
    assert WMAX["E19_weighted_arm"]["historical_replay_exact"] is True
    assert "POST-HOC" in WMAX["status"]
    assert WMAX["kappa"] == {"historical": 2.05, "sharp": 1.0}
    assert WMAX["mathematical_necessity_audit"]["kappa_2_05_required_for_executed_nominal_claims"] is False
    for relpath, digest in WMAX["provenance"]["protected_sha256"].items():
        assert sha256(ROOT / relpath) == digest, relpath
    archived = json.loads((TABLES / "E13_weighted_cs.json").read_text(encoding="utf-8"))
    assert archived["part_b_benchmark"]["w_max"]["kappa_norm"] == 2.05
    assert archived["part_b_benchmark"]["error_rates"]["w"]["false_cert"] == 2
    assert archived["part_b_benchmark"]["n_star_ratio_w_over_unw"]["median"] == 1.664
    e19 = json.loads((TABLES / "E19_fresh_world_validity.json").read_text(encoding="utf-8"))
    assert e19["error_rates"]["weighted"]["counts"] == [6, 7980]


# --------------------------------------------------------------------- manuscript and provenance hygiene

def test_historical_artifact_filenames_unchanged() -> None:
    for name in (
        "E16_proposition4_instantiation.json",
        "E16_proposition4_deployment_summary.json",
        "E16_psd_sensitivity.json",
        "E16_quantum_uncertainty.json",
    ):
        assert (TABLES / name).is_file(), name
    assert (ROOT / "scripts" / "summarize_e16_proposition4_deployments.py").is_file()
    assert "historical identifier `proposition4'" in MAIN
    assert "historical identifier `proposition4'" in SUPP


def test_proposition_numbering_natural_and_sec_related_resolved() -> None:
    order = re.findall(r"\\begin\{(theorem|proposition)\}", MAIN)
    assert order == ["proposition", "theorem", "proposition", "proposition"]
    assert re.search(r"\\setcounter\{(?:theorem|proposition)\}", MAIN) is None
    assert "\\ref{sec:related}" not in MAIN and "\\label{sec:related}" not in MAIN
    for label in ("sec:results", "sec:limitations", "sec:conclusion"):
        assert f"\\label{{{label}}}" not in MAIN
    assert "Sec. 1)" not in MAIN
    aux = ROOT / "manuscript" / "latex" / "main.aux"
    if aux.is_file():
        assert "newlabel{sec:related}" not in aux.read_text(encoding="utf-8")


def test_no_undefined_references_or_citations_in_build_log() -> None:
    log_path = ROOT / "manuscript" / "latex" / "main.log"
    if not log_path.is_file():
        return
    log = log_path.read_text(encoding="utf-8", errors="replace").lower()
    assert "undefined references" not in log
    assert "undefined citations" not in log
    assert "citation(s) may have changed" not in log


def test_c3_wording_matches_measured_mechanism() -> None:
    assert "threshold-dominated" not in MAIN.lower()
    assert "\\textsc{mixed}" in MAIN
    assert "amplified downstream through recalibration and operating-threshold selection" in FLAT_MAIN
    assert "need not itself be quantum-specific" in FLAT_MAIN
    assert "non-monotonic" not in MAIN and "non-monotonic" not in SUPP
    assert "common-mode cancellation" in FLAT_MAIN
    assert "INFERNO \\citep{arxiv1806.04743}" in MAIN
    assert "\\citealp{arxiv1806.04743}" not in MAIN
    assert "Elharrauss, Salah Eddine" in BIB
    assert "waudbysmith2020wor" in BIB and "waudbysmith2020wor" in MAIN


def test_protected_scientific_inputs_unchanged_from_v1_5() -> None:
    protected = (
        "configs", "data", "experiments", "src",
        "results/tables", "results/raw", "results/manifests",
        "scripts/analyze_e16_psd_sensitivity.py",
        "scripts/summarize_e16_proposition4_deployments.py",
        "experiments/E16_quantum_uncertainty/run_e16.py",
    )
    completed = subprocess.run(
        ["git", "diff", "--name-only", "npjqi-submission-v1.5", "--", *protected],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    changed = {line.replace("\\", "/") for line in completed.stdout.split()}
    assert changed <= DERIVED_0_3_6, changed - DERIVED_0_3_6
