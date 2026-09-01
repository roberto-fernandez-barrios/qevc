"""Synchronize the README and release-manifest artifact tables from the
authoritative checksum file and the real PDF page counts.  Writes nothing else.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKSUMS = ROOT / "docs" / "submission" / "npjqi_checksums.sha256"
README = ROOT / "README.md"
MANIFEST = ROOT / "docs" / "submission" / "npjqi_release_manifest.md"
DESCRIPTIONS = {
    "output/pdf/npjqi_manuscript.pdf": None,
    "output/pdf/npjqi_supplementary_information.pdf": None,
    "output/pdf/npjqi_cover_letter.pdf": None,
    "dist/npjqi-submission.zip": "source + 3 PDFs",
    "results/tables/E16_psd_sensitivity.json": "30 deployments",
    "results/tables/E16_proposition4_instantiation.json": "7,200 condition cells",
    "results/tables/E16_proposition4_deployment_summary.json": "30 noisy-kernel deployments",
    "results/tables/E16_stage_decomposition.json": "30 RAW + 30 PSD deployments, 4 stages",
    "results/tables/E16_prop3_margin_stratification.json": "7,200 condition cells",
    "results/tables/E13_wmax_nominal_bound_sensitivity.json": "E13 Part B + E19 weighted arm",
}


def pdf_pages(path: Path) -> int:
    out = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)", out, re.MULTILINE).group(1))


def main() -> int:
    entries = {}
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, path = line.split("  ", 1)
            entries[path.replace("\\", "/")] = digest.upper()
    rows = []
    for relpath, description in DESCRIPTIONS.items():
        pages = description if description else str(pdf_pages(ROOT / relpath))
        rows.append(f"| `{relpath}` | {pages} | `{entries[relpath]}` |")
    table = "| Artifact | Pages | SHA-256 |\n|---|---:|---|\n" + "\n".join(rows) + "\n"
    pattern = re.compile(r"\| Artifact \| Pages \| SHA-256 \|\n\|---\|---:\|---\|\n(?:\|[^\n]*\|\n)+")
    for path in (README, MANIFEST):
        text = path.read_text(encoding="utf-8")
        if len(pattern.findall(text)) != 1:
            raise SystemExit(f"{path.name}: expected exactly one artifact table")
        manifest_table = table.replace("source + 3 PDFs", "source + three PDFs") if path is MANIFEST else table
        path.write_text(pattern.sub(lambda _m: manifest_table, text), encoding="utf-8")
        print(f"synchronized {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
