"""Verify that every public submission-release surface describes one build.

The gate is intentionally independent of the package builder: it derives PDF
page counts and SHA-256 digests from the files on disk, then compares those
values with README.md, the checksum file and the release manifest.  A stale
README is therefore a release-blocking error rather than documentation drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.5"
TAG = "npjqi-submission-v1.5"
# Filled with the DOI reserved for the new Zenodo version before final release.
PENDING_DOI = "10.5281/zenodo.00000000"
VERSION_DOI = "10.5281/zenodo.22231469"
CONCEPT_DOI = "10.5281/zenodo.21894291"

README = ROOT / "README.md"
CITATION = ROOT / "CITATION.cff"
PYPROJECT = ROOT / "pyproject.toml"
CHECKSUMS = ROOT / "docs" / "submission" / "npjqi_checksums.sha256"
MANIFEST = ROOT / "docs" / "submission" / "npjqi_release_manifest.md"
SUBMISSION_METADATA = ROOT / "docs" / "submission" / "npjqi_submission_metadata.md"
ZENODO_METADATA = (
    ROOT / "docs" / "submission" / "zenodo_npjqi_submission_v1_5_metadata.json"
)
MAIN_TEX = ROOT / "manuscript" / "latex" / "main.tex"
MAIN_AUX = ROOT / "manuscript" / "latex" / "main.aux"
MAIN_LOG = ROOT / "manuscript" / "latex" / "main.log"
SUPPLEMENT_TEX = ROOT / "manuscript" / "supplementary" / "supplement.tex"
COVER_TEX = ROOT / "manuscript" / "npjqi" / "cover_letter.tex"
BIBLIOGRAPHY = ROOT / "manuscript" / "bibliography" / "references.bib"
DRAFT = ROOT / "manuscript" / "main" / "draft.md"
FORMAL_RESULTS = ROOT / "docs" / "formal_results.md"

PDF_ARTIFACTS = {
    "output/pdf/npjqi_manuscript.pdf": 28,
    "output/pdf/npjqi_supplementary_information.pdf": 14,
    "output/pdf/npjqi_cover_letter.pdf": 1,
}
NON_PDF_ARTIFACTS = (
    "dist/npjqi-submission.zip",
    "results/tables/E16_psd_sensitivity.json",
    "results/tables/E16_proposition4_instantiation.json",
    "results/tables/E16_proposition4_deployment_summary.json",
)
ARTIFACTS = (*PDF_ARTIFACTS, *NON_PDF_ARTIFACTS)
ZIP_PDFS = {
    "submission/npjqi_manuscript.pdf": "output/pdf/npjqi_manuscript.pdf",
    "submission/npjqi_supplementary_information.pdf": (
        "output/pdf/npjqi_supplementary_information.pdf"
    ),
    "submission/npjqi_cover_letter.pdf": "output/pdf/npjqi_cover_letter.pdf",
}
ZIP_SOURCES = {
    "source/manuscript/latex/main.tex": MAIN_TEX,
    "source/manuscript/bibliography/references.bib": BIBLIOGRAPHY,
    "source/manuscript/supplementary/supplement.tex": SUPPLEMENT_TEX,
    "source/manuscript/npjqi/cover_letter.tex": COVER_TEX,
    "submission/npjqi_submission_metadata.md": SUBMISSION_METADATA,
    "source/results/tables/E16_psd_sensitivity.json": (
        ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
    ),
    "source/results/tables/E16_proposition4_instantiation.json": (
        ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
    ),
    "source/results/tables/E16_proposition4_deployment_summary.json": (
        ROOT / "results" / "tables" / "E16_proposition4_deployment_summary.json"
    ),
}
EXPECTED_LABELS = {
    "prop:unident": "1",
    "thm:weighted": "1",
    "prop:marginal": "2",
    "prop:stability": "3",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def pdf_pages(path: Path) -> int:
    """Return the real PDF page count with dependency-free final fallback."""
    try:
        from pypdf import PdfReader

        return len(PdfReader(path).pages)
    except ImportError:
        try:
            completed = subprocess.run(
                ["pdfinfo", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            # pdfTeX emits one uncompressed /Type /Page dictionary per page.
            # This keeps the gate runnable in the pinned Windows CI image
            # without adding a scientific-environment dependency.
            count = len(re.findall(rb"/Type\s*/Page\b", path.read_bytes()))
            if count == 0:
                raise RuntimeError(f"Could not read page count from {path}")
            return count
        match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
        if match is None:
            raise RuntimeError(f"Could not read page count from {path}")
        return int(match.group(1))


def checksum_entries(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9A-Fa-f]{64})\s{2}(.+)", line)
        if match is None:
            raise ValueError(f"Malformed checksum line: {line!r}")
        entries[match.group(2).replace("\\", "/")] = match.group(1).upper()
    return entries


def markdown_artifacts(text: str) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    pattern = re.compile(
        r"^\| `([^`]+)` \| ([^|]+?) \| `([0-9A-Fa-f]{64})` \|$",
        re.MULTILINE,
    )
    for path, pages, digest in pattern.findall(text):
        entries[path.replace("\\", "/")] = (pages.strip(), digest.upper())
    return entries


def aux_label_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for label, value in re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", text):
        values[label] = value
    return values


def git_tag_target(tag: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{}}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode, completed.stdout.strip()


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def validate(
    *,
    require_tag: bool = True,
    require_build_evidence: bool = True,
) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    required = [
        README,
        CITATION,
        PYPROJECT,
        CHECKSUMS,
        MANIFEST,
        SUBMISSION_METADATA,
        ZENODO_METADATA,
        MAIN_TEX,
        SUPPLEMENT_TEX,
        COVER_TEX,
        BIBLIOGRAPHY,
        DRAFT,
        FORMAL_RESULTS,
        *(ROOT / path for path in ARTIFACTS),
    ]
    if require_build_evidence:
        required.extend((MAIN_AUX, MAIN_LOG))
    missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
    check("all release inputs exist", not missing, ", ".join(missing))
    if missing:
        return checks

    readme = README.read_text(encoding="utf-8")
    citation = CITATION.read_text(encoding="utf-8")
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    checksum_text = CHECKSUMS.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    metadata = SUBMISSION_METADATA.read_text(encoding="utf-8")
    zenodo = ZENODO_METADATA.read_text(encoding="utf-8")
    main_tex = MAIN_TEX.read_text(encoding="utf-8")
    main_aux = MAIN_AUX.read_text(encoding="utf-8") if MAIN_AUX.is_file() else ""
    main_log = (
        MAIN_LOG.read_text(encoding="utf-8", errors="replace")
        if MAIN_LOG.is_file()
        else ""
    )
    supplement = SUPPLEMENT_TEX.read_text(encoding="utf-8")
    cover = COVER_TEX.read_text(encoding="utf-8")
    bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")
    draft = DRAFT.read_text(encoding="utf-8")
    formal = FORMAL_RESULTS.read_text(encoding="utf-8")

    citation_version = re.search(r"(?m)^version:\s*([^\s]+)\s*$", citation)
    citation_doi = re.search(r'(?m)^doi:\s*"([^"]+)"\s*$', citation)
    project_version = re.search(r'(?m)^version\s*=\s*"([^"]+)"\s*$', pyproject)
    check(
        "CITATION.cff version",
        citation_version is not None and citation_version.group(1) == VERSION,
        citation_version.group(1) if citation_version else "missing",
    )
    check(
        "pyproject version",
        project_version is not None and project_version.group(1) == VERSION,
        project_version.group(1) if project_version else "missing",
    )
    check(
        "CITATION.cff DOI",
        citation_doi is not None and citation_doi.group(1) == VERSION_DOI,
        citation_doi.group(1) if citation_doi else "missing",
    )
    check("release tag declared", TAG in readme and TAG in manifest and TAG in metadata)
    check(
        "release version synchronized",
        all(
            VERSION in text
            for text in (
                readme,
                citation,
                pyproject,
                manifest,
                metadata,
                zenodo,
                bibliography,
            )
        ),
    )
    check(
        "version DOI synchronized",
        VERSION_DOI != PENDING_DOI
        and all(
            VERSION_DOI in text
            for text in (
                readme,
                citation,
                manifest,
                metadata,
                zenodo,
                main_tex,
                bibliography,
                draft,
            )
        ),
        VERSION_DOI,
    )
    check("concept DOI synchronized", CONCEPT_DOI in manifest and CONCEPT_DOI in zenodo)
    check("cover visible date", "1 September 2026" in cover)
    check("old cover date absent", "31 August 2026" not in cover)
    check(
        "release date synchronized",
        'date-released: "2026-09-01"' in citation
        and "Release date: 2026-09-01" in manifest
        and '"publication_date": "2026-09-01"' in zenodo,
    )

    try:
        zenodo_record = json.loads(zenodo)
    except json.JSONDecodeError as exc:
        check("Zenodo metadata JSON", False, str(exc))
    else:
        check("Zenodo metadata JSON", True)
        check("Zenodo metadata version", zenodo_record.get("version") == f"{VERSION} / {TAG}")
        check("Zenodo DOI reservation requested", zenodo_record.get("prereserve_doi") is True)
        check(
            "Zenodo DOI notes synchronized",
            VERSION_DOI in str(zenodo_record.get("notes", ""))
            and CONCEPT_DOI in str(zenodo_record.get("notes", "")),
        )

    checksum_map = checksum_entries(checksum_text)
    readme_map = markdown_artifacts(readme)
    manifest_map = markdown_artifacts(manifest)
    expected_paths = set(ARTIFACTS)
    check("checksum artifact set", set(checksum_map) == expected_paths, str(sorted(checksum_map)))
    check("README artifact set", set(readme_map) == expected_paths, str(sorted(readme_map)))
    check("manifest artifact set", set(manifest_map) == expected_paths, str(sorted(manifest_map)))

    actual_hashes: dict[str, str] = {}
    for relpath in ARTIFACTS:
        actual = sha256(ROOT / relpath)
        actual_hashes[relpath] = actual
        check(f"checksum matches file: {relpath}", checksum_map.get(relpath) == actual, actual)
        check(
            f"README matches checksum: {relpath}",
            readme_map.get(relpath, ("", ""))[1] == checksum_map.get(relpath),
        )
        check(
            f"manifest matches checksum: {relpath}",
            manifest_map.get(relpath, ("", ""))[1] == checksum_map.get(relpath),
        )

    for relpath, expected_pages in PDF_ARTIFACTS.items():
        pages = pdf_pages(ROOT / relpath)
        readme_pages = readme_map.get(relpath, ("", ""))[0]
        manifest_pages = manifest_map.get(relpath, ("", ""))[0]
        check(f"expected page count: {relpath}", pages == expected_pages, str(pages))
        check(
            f"README page count: {relpath}",
            readme_pages == str(pages),
            f"README={readme_pages}, PDF={pages}",
        )
        check(
            f"manifest page count: {relpath}",
            manifest_pages == str(pages),
            f"manifest={manifest_pages}, PDF={pages}",
        )

    cover_pdf = ROOT / "output/pdf/npjqi_cover_letter.pdf"
    creation_match = re.search(rb"/CreationDate\s*\(D:(\d{8})", cover_pdf.read_bytes())
    cover_creation = creation_match.group(1).decode("ascii") if creation_match else ""
    check(
        "cover PDF metadata date",
        cover_creation == "20260901",
        cover_creation or "unavailable",
    )

    archive = ROOT / "dist" / "npjqi-submission.zip"

    def zip_source_matches(archived: bytes, checked_out: bytes) -> bool:
        if require_build_evidence:
            return archived == checked_out
        # A source-only checkout may apply platform EOL rules to ordinary
        # manuscript text.  Release mode remains byte-strict; CI mode compares
        # only the newline-normalized source while artifact hashes stay exact.
        return archived.replace(b"\r\n", b"\n") == checked_out.replace(
            b"\r\n", b"\n"
        )

    try:
        with zipfile.ZipFile(archive) as bundle:
            bad_member = bundle.testzip()
            check("submission ZIP CRC", bad_member is None, bad_member or "")
            names = set(bundle.namelist())
            for member, relpath in ZIP_PDFS.items():
                check(f"submission ZIP contains {member}", member in names)
                if member in names:
                    check(
                        f"submission ZIP PDF matches {relpath}",
                        sha256_bytes(bundle.read(member)) == actual_hashes[relpath],
                    )
            metadata_member = "submission/npjqi_submission_metadata.md"
            check("submission ZIP contains metadata", metadata_member in names)
            if metadata_member in names:
                check(
                    "submission ZIP metadata synchronized",
                    zip_source_matches(
                        bundle.read(metadata_member),
                        SUBMISSION_METADATA.read_bytes(),
                    ),
                )
            for member, source in ZIP_SOURCES.items():
                check(f"submission ZIP contains {member}", member in names)
                if member in names:
                    check(
                        f"submission ZIP source matches {source.relative_to(ROOT).as_posix()}",
                        zip_source_matches(bundle.read(member), source.read_bytes()),
                    )
    except zipfile.BadZipFile as exc:
        check("submission ZIP readable", False, str(exc))

    main_order = re.findall(r"\\begin\{(theorem|proposition)\}", main_tex)
    labels = re.findall(r"\\label\{((?:thm|prop):[^}]+)\}", main_tex)
    check(
        "formal environment order",
        main_order == ["proposition", "theorem", "proposition", "proposition"],
        str(main_order),
    )
    check("formal label order", labels == list(EXPECTED_LABELS), str(labels))
    check(
        "separate theorem/proposition counters",
        r"\newtheorem{theorem}{Theorem}" in main_tex
        and r"\newtheorem{proposition}{Proposition}" in main_tex,
    )
    check(
        "no artificial theorem/proposition counter reset",
        re.search(r"\\setcounter\{(?:theorem|proposition)\}", main_tex) is None,
    )
    if require_build_evidence:
        aux_values = aux_label_values(main_aux)
        for label, expected in EXPECTED_LABELS.items():
            check(
                f"resolved formal label: {label}",
                aux_values.get(label) == expected,
                aux_values.get(label, "missing"),
            )
        check(
            "no undefined references or citations",
            "undefined references" not in main_log.lower()
            and "undefined citations" not in main_log.lower()
            and "citation(s) may have changed" not in main_log.lower(),
        )
        check("no rendered unresolved markers", "??" not in main_log)

    audit_table = re.search(
        r"\\begin\{table\}\[H\].*?\\label\{tab:audit-trail\}.*?\\end\{table\}",
        supplement,
        re.DOTALL,
    )
    current_supplement = supplement
    if audit_table is not None:
        current_supplement = supplement[: audit_table.start()] + supplement[audit_table.end() :]
    check("historical numbering isolated to audit trail", audit_table is not None)
    check("no stale Proposition 4 in current Supplement", "Proposition 4" not in current_supplement)
    check(
        "no stale Proposition 4 in current formal-results document",
        "Proposition 4" not in formal,
    )
    current_readme = readme.split("## Self-correction record", 1)[0]
    check("no stale Proposition 4 in current README", "Proposition 4" not in current_readme)
    check("no stale Proposition 4 in submission metadata", "Proposition 4" not in metadata)
    check("no stale Proposition 4 in manuscript source", "Proposition 4" not in main_tex)
    check("no stale Proposition 4 in generated draft", "Proposition 4" not in draft)
    check(
        "generated draft has no formal counter reset",
        re.search(r"\\setcounter\{(?:theorem|proposition)\}", draft) is None,
    )
    check("current Proposition 1 documented", "## Proposition 1" in formal)
    check("current Proposition 2 documented", "## Proposition 2" in formal)
    check("current Proposition 3 documented", "## Proposition 3" in formal)

    historical_numbering = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "npjqi-submission-v1.4",
            "--",
            "docs/decisions.md",
            "docs/experiment_registry.md",
            "docs/audits",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    check(
        "historical numbering records preserved",
        historical_numbering.returncode == 0 and not historical_numbering.stdout.strip(),
        historical_numbering.stdout.strip(),
    )

    if require_tag:
        returncode, tag_target = git_tag_target(TAG)
        head = git_head()
        check("release tag exists", returncode == 0, TAG)
        check(
            "release tag targets HEAD",
            returncode == 0 and tag_target == head,
            f"tag={tag_target}, HEAD={head}",
        )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-unreleased",
        action="store_true",
        help="skip the final check that the release tag exists at HEAD",
    )
    args = parser.parse_args()

    checks = validate(require_tag=not args.allow_unreleased)
    failed = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        suffix = f" ({detail})" if detail else ""
        print(f"[{status}] {name}{suffix}")
        failed += not ok
    print(f"\n{len(checks) - failed}/{len(checks)} release-consistency checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
