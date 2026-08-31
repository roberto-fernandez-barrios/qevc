"""Build the reviewer-facing npj Quantum Information submission package."""

from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_DIR = ROOT / "manuscript" / "latex"
SUPP_DIR = ROOT / "manuscript" / "supplementary"
COVER_DIR = ROOT / "manuscript" / "npjqi"
FIGURE_DIR = ROOT / "results" / "figures"
OUT_DIR = ROOT / "output" / "pdf"
DIST_DIR = ROOT / "dist"
CHECKSUM_FILE = ROOT / "docs" / "submission" / "npjqi_checksums.sha256"
PSD_ANALYSIS = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
PROPOSITION4_ANALYSIS = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def figure_names(tex: str) -> list[str]:
    return sorted(
        set(re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^{}]+)\}", tex))
    )


def main() -> None:
    inputs = {
        "main": MAIN_DIR / "main.pdf",
        "supplement": SUPP_DIR / "supplement.pdf",
        "cover": COVER_DIR / "cover_letter.pdf",
        "bbl": MAIN_DIR / "main.bbl",
    }
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise SystemExit("Missing compiled input(s): " + ", ".join(missing))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "main": OUT_DIR / "npjqi_manuscript.pdf",
        "supplement": OUT_DIR / "npjqi_supplementary_information.pdf",
        "cover": OUT_DIR / "npjqi_cover_letter.pdf",
    }
    for key in ("main", "supplement", "cover"):
        shutil.copy2(inputs[key], outputs[key])

    main_tex = (MAIN_DIR / "main.tex").read_text(encoding="utf-8")
    supp_tex = (SUPP_DIR / "supplement.tex").read_text(encoding="utf-8")
    figures = figure_names(main_tex)
    supplement_figures = figure_names(supp_tex)
    for name in figures + supplement_figures:
        path = FIGURE_DIR / name
        if not path.is_file():
            raise SystemExit(f"Missing included figure: {path}")

    archive = DIST_DIR / "npjqi-submission.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in outputs.values():
            zf.write(path, f"submission/{path.name}")
        source_files = {
            MAIN_DIR / "main.tex": "source/manuscript/latex/main.tex",
            MAIN_DIR / "main.bbl": "source/manuscript/latex/main.bbl",
            MAIN_DIR / "sn-jnl.cls": "source/manuscript/latex/sn-jnl.cls",
            MAIN_DIR / "sn-nature.bst": "source/manuscript/latex/sn-nature.bst",
            ROOT / "manuscript" / "bibliography" / "references.bib": "source/manuscript/bibliography/references.bib",
            SUPP_DIR / "supplement.tex": "source/manuscript/supplementary/supplement.tex",
            COVER_DIR / "cover_letter.tex": "source/manuscript/npjqi/cover_letter.tex",
            ROOT / "docs" / "submission" / "npjqi_submission_metadata.md": "submission/npjqi_submission_metadata.md",
            ROOT / "results" / "tables" / "E16_psd_sensitivity.json": "source/results/tables/E16_psd_sensitivity.json",
            ROOT / "results" / "tables" / "E16_proposition4_instantiation.json": "source/results/tables/E16_proposition4_instantiation.json",
        }
        for source, arcname in source_files.items():
            zf.write(source, arcname)
        for name in figures:
            zf.write(FIGURE_DIR / name, f"source/results/figures/{Path(name).name}")
        for name in supplement_figures:
            zf.write(
                FIGURE_DIR / name,
                f"source/results/figures/{Path(name).name}",
            )

    checksum_targets = [*outputs.values(), archive, PSD_ANALYSIS, PROPOSITION4_ANALYSIS]
    lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in checksum_targets]
    CHECKSUM_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Built {archive.relative_to(ROOT)}")
    for line in lines:
        print(line)


if __name__ == "__main__":
    main()
