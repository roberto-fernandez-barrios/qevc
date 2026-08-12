"""Build the self-contained arXiv-v1 source archive.

The generated tree lives under ``dist/arxiv-v1/`` and is disposable.  The
script deliberately packages the supplementary PDF and its source under
``anc/`` so arXiv treats them as ancillary material rather than a second
top-level TeX submission.
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
TARGET = DIST / "arxiv-v1"
ARCHIVE = DIST / "arxiv-v1-source.zip"

FIGURES = [
    "fig1_framework.pdf",
    "fig2_tes_replicated.pdf",
    "fig3_family_blindness.pdf",
    "fig4_geometry_sensor.pdf",
    "fig4b_out_of_grid_sensor.pdf",
    "fig5_certification_landscape.pdf",
    "fig6_label_economics.pdf",
    "fig7_h5_decoupling.pdf",
    "fig7b_inference_levels.pdf",
    "fig8_shots_hardware.pdf",
    "fig8b_estimation_noise_verdicts.pdf",
]


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    DIST.mkdir(exist_ok=True)
    if TARGET.exists():
        if TARGET.parent.resolve() != DIST.resolve():
            raise RuntimeError(f"refusing to replace unexpected path: {TARGET}")
        shutil.rmtree(TARGET)
    TARGET.mkdir()
    figures_dir = TARGET / "figures"
    ancillary_dir = TARGET / "anc"
    figures_dir.mkdir()
    ancillary_dir.mkdir()

    main_tex = (ROOT / "manuscript" / "latex" / "main.tex").read_text(
        encoding="utf-8"
    )
    main_tex = main_tex.replace(
        r"\graphicspath{{../../results/figures/}}",
        r"\graphicspath{{figures/}}",
    )
    write_text(TARGET / "main.tex", main_tex)
    shutil.copy2(ROOT / "manuscript" / "latex" / "main.bbl", TARGET / "main.bbl")

    source_figures = ROOT / "results" / "figures"
    for filename in FIGURES:
        shutil.copy2(source_figures / filename, figures_dir / filename)

    supplement_tex = (
        ROOT / "manuscript" / "supplementary" / "supplement.tex"
    ).read_text(encoding="utf-8")
    supplement_tex = supplement_tex.replace(
        r"\graphicspath{{../../results/figures/}}",
        r"\graphicspath{{./}}",
    )
    write_text(ancillary_dir / "supplement.tex", supplement_tex)
    shutil.copy2(
        ROOT / "manuscript" / "supplementary" / "supplement.pdf",
        ancillary_dir / "supplement.pdf",
    )
    shutil.copy2(
        source_figures / "figS16_estimation_diagnostics.pdf",
        ancillary_dir / "figS16_estimation_diagnostics.pdf",
    )

    write_text(
        TARGET / "00README.XXX",
        "main.tex is the primary arXiv document.\n"
        "anc/supplement.pdf is the supplementary material; its TeX source and "
        "Figure S16 are included alongside it.\n",
    )

    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(TARGET.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(TARGET).as_posix())

    print(f"Built {ARCHIVE.relative_to(ROOT)} with {len(FIGURES)} main figures")


if __name__ == "__main__":
    main()
