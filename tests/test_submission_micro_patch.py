"""Regression tests for the bounded 0.3.4 submission micro-patch."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "manuscript" / "latex" / "main.tex").read_text(encoding="utf-8")
SUPP = (ROOT / "manuscript" / "supplementary" / "supplement.tex").read_text(
    encoding="utf-8"
)
BIB = (ROOT / "manuscript" / "bibliography" / "references.bib").read_text(
    encoding="utf-8"
)


def test_historical_alpha_plus_three_sigma_is_not_an_iid_boundary() -> None:
    assert r"$\alpha+3\sigma$ boundary" not in SUPP
    assert "Historical heuristic gate" in SUPP
    assert "not interpreted as an IID sampling standard" in SUPP
    assert re.search(r"historical\s+implementation-falsifier threshold", SUPP)
    assert "per-claim confidence-sequence result" in SUPP


def test_two_finite_shot_kernel_references_are_cited() -> None:
    for key in ("shastry2023shotfrugal", "gentinetta2024complexity"):
        assert key in MAIN
        assert f"{{{key}," in BIB
    assert "10.48550/arXiv.2210.06971" in BIB
    assert "10.22331/q-2024-01-11-1225" in BIB


def test_proposition_four_is_a_retrospective_diagnostic() -> None:
    assert "Its E16 instantiation is retrospective" in MAIN
    assert "diagnostic of observed" in MAIN
    assert "not as an operational pre-audit certificate" in MAIN
    assert "retrospective diagnostic" in SUPP
    assert "does not predict a flip" in SUPP


def test_tier_a_resource_count_is_exact() -> None:
    entries = 2000 * 1999 // 2
    assert entries == 1_999_000
    assert entries * 128 == 255_872_000
    assert entries * 4096 == 8_187_904_000
    for token in (
        "n(n-1)/2=1{,}999{,}000",
        "255{,}872{,}000\\simeq2.56\\times10^8",
        "8{,}187{,}904{,}000\\simeq8.19\\times10^9",
        "not a linear wall-clock estimate",
    ):
        assert token in MAIN


DERIVED_0_3_6 = {
    "results/tables/E16_stage_decomposition.json",
    "results/tables/E16_prop3_margin_stratification.json",
    "results/tables/E13_wmax_nominal_bound_sensitivity.json",
}


def test_protected_scientific_artifacts_match_v033() -> None:
    protected = (
        "configs",
        "data",
        "experiments",
        "results",
        "src",
        "scripts/analyze_e16_psd_sensitivity.py",
        "scripts/summarize_e16_proposition4_deployments.py",
    )
    completed = subprocess.run(
        ["git", "diff", "--name-only", "npjqi-submission-v1.3", "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {line.replace("\\", "/") for line in completed.stdout.split()}
    assert changed <= DERIVED_0_3_6, changed - DERIVED_0_3_6
