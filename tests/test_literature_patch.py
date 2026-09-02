"""Regression tests for the 0.3.9 final literature / prior-art patch."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "manuscript" / "latex" / "main.tex").read_text(encoding="utf-8")
BIB = (ROOT / "manuscript" / "bibliography" / "references.bib").read_text(
    encoding="utf-8"
)
FLAT_MAIN = " ".join(MAIN.split())


def test_final_literature_patch_references_are_cited() -> None:
    for key in ("arxiv2401.10542", "arxiv2605.22275", "arxiv1810.08240"):
        assert key in MAIN
        assert f"{{{key}," in BIB


def test_version_of_record_updates() -> None:
    # FAIR Universe: NeurIPS 2025 Datasets and Benchmarks version of record.
    assert "Advances in Neural Information Processing Systems 38" in BIB
    assert "10.52202/085713-2767" in BIB
    assert "92065--92101" in BIB
    # Waudby-Smith & Ramdas WoR: NeurIPS 2020 version of record with the
    # arXiv identifier retained as a complementary identifier.
    assert "Advances in Neural Information Processing Systems 33" in BIB
    assert "2006.04347" in BIB


def test_new_reference_metadata_is_exact() -> None:
    assert "10.1016/j.nima.2026.171360" in BIB
    assert "10.1214/20-AOS1991" in BIB
    assert "10.48550/arXiv.2605.22275" in BIB
    # No journal invented for the arXiv-only Miroszewski 2026 item.
    assert "journal" not in BIB.split("@misc{arxiv2605.22275,")[1].split("}")[0]


def test_positioning_sentences_present_without_priority_claims() -> None:
    assert (
        "Finite-simulation fluctuations are already known to induce"
        " under-coverage in profile-likelihood inference" in FLAT_MAIN
    )
    assert "support-vector active-set instability" in FLAT_MAIN
    assert (
        "The general time-uniform confidence-sequence framework is developed"
        " by Howard et al." in FLAT_MAIN
    )
    assert "not a priority claim" in FLAT_MAIN
    assert "we are the first" not in FLAT_MAIN.lower()


def test_novelty_boundary_phrase_preserved() -> None:
    assert (
        "combined scientific object rather than priority over its ingredients"
        in FLAT_MAIN
    )
