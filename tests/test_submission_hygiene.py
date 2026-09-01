"""Regression tests for the bounded 0.3.5 submission-hygiene patch."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts" / "verify_release_consistency.py"
SPEC = importlib.util.spec_from_file_location("verify_release_consistency", GATE_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_release_consistency_gate_passes_before_tagging() -> None:
    failures = [
        f"{name}: {detail}" for name, ok, detail in GATE.validate(require_tag=False) if not ok
    ]
    assert failures == []


def test_readme_page_count_drift_is_detected(tmp_path, monkeypatch) -> None:
    readme = GATE.README.read_text(encoding="utf-8")
    artifacts = GATE.markdown_artifacts(readme)
    manuscript = "output/pdf/npjqi_manuscript.pdf"
    assert artifacts[manuscript][0] == str(GATE.pdf_pages(GATE.ROOT / manuscript))
    stale = readme.replace(
        f"| `{manuscript}` | {artifacts[manuscript][0]} |",
        f"| `{manuscript}` | 999 |",
        1,
    )
    stale_readme = tmp_path / "README.md"
    stale_readme.write_text(stale, encoding="utf-8")
    monkeypatch.setattr(GATE, "README", stale_readme)
    failures = {name for name, ok, _ in GATE.validate(require_tag=False) if not ok}
    assert f"README page count: {manuscript}" in failures


def test_readme_hash_drift_is_detected(tmp_path, monkeypatch) -> None:
    readme = GATE.README.read_text(encoding="utf-8")
    artifacts = GATE.markdown_artifacts(readme)
    manuscript = "output/pdf/npjqi_manuscript.pdf"
    stale = readme.replace(artifacts[manuscript][1], "0" * 64, 1)
    stale_readme = tmp_path / "README.md"
    stale_readme.write_text(stale, encoding="utf-8")
    monkeypatch.setattr(GATE, "README", stale_readme)
    failures = {name for name, ok, _ in GATE.validate(require_tag=False) if not ok}
    assert f"README matches checksum: {manuscript}" in failures


def test_formal_numbering_has_no_counter_hacks() -> None:
    main = GATE.MAIN_TEX.read_text(encoding="utf-8")
    assert r"\setcounter{theorem}" not in main
    assert r"\setcounter{proposition}" not in main
    assert r"\newtheorem{theorem}{Theorem}" in main
    assert r"\newtheorem{proposition}{Proposition}" in main


def test_current_submission_documents_have_no_stale_proposition_four() -> None:
    readme = GATE.README.read_text(encoding="utf-8").split(
        "## Self-correction record", 1
    )[0]
    metadata = GATE.SUBMISSION_METADATA.read_text(encoding="utf-8")
    formal = GATE.FORMAL_RESULTS.read_text(encoding="utf-8")
    main = GATE.MAIN_TEX.read_text(encoding="utf-8")
    draft = GATE.DRAFT.read_text(encoding="utf-8")
    for text in (readme, metadata, formal, main, draft):
        assert "Proposition 4" not in text


def test_protected_scientific_baseline_matches_v034() -> None:
    protected = ("configs", "data", "experiments", "results", "src")
    completed = subprocess.run(
        ["git", "diff", "--name-only", "npjqi-submission-v1.4", "--", *protected],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == ""
