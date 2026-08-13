# arXiv v1 release manifest

Freeze date: 2026-08-12

## Publication metadata

- Title: *When Can Quantum Event Classifiers Be Trusted? Conditional
  Validity under Collider Systematics and Quantum Estimation Uncertainty*
- Authors: Roberto Fernández-Barrios; Iker Pastor-López; Asier
  González-Santocildes; Pablo García Bringas
- Affiliation: Faculty of Engineering, University of Deusto, Avda. de las
  Universidades 24, 48007 Bilbao, Spain
- arXiv categories: `quant-ph` (primary), `hep-ph`, `stat.ME`
- Preprint license: CC BY 4.0
- Code and artifact license: MIT
- Zenodo DOI: 10.5281/zenodo.21894292 (deposition 21894292)
- Git tag: `arxiv-v1`

## Frozen deliverables

| Artifact | Pages | Bytes | SHA-256 |
|---|---:|---:|---|
| `manuscript/latex/main.pdf` | 27 | 858,056 | `6D36CE51E8540518563ABC1783DA768B3F60E91A7938CDA757751D7A8AA0A3F3` |
| `manuscript/supplementary/supplement.pdf` | 8 | 417,508 | `67012F90E479C56831A15275E6286776AD2E7F0E831E0DAA49B31A73F37B541E` |
| `dist/arxiv-v1-source.zip` | — | 632,167 | `2C50C6198DACA0FACB64B7A9802D0D63BBF9E8F9710FA840A4F915C318D4FA33` |

The source archive contains `main.tex`, its generated `main.bbl`, all 11
main-document figure PDFs, and the supplement PDF plus source and Figure S16
under `anc/`. Both top-level and ancillary sources independently compile to
the page counts above with zero unresolved citations/references or overfull
boxes.

## Verification gate

- F8.2 executable audit: 97/97 checks passed.
- Semantic four-gram coverage: 90.4294% Markdown→LaTeX and 92.1970%
  LaTeX→Markdown.
- Repository test suite: 127/127 passed.
- Both repository PDFs and both sources in the arXiv package compile with no
  unresolved references/citations, overfull boxes, or LaTeX warnings.
- All 35 final PDF pages visually inspected.
- seed-101 and seed-121 `final_eval` remain sealed for journal review.
- Nine registered falsifier firings are retained and disclosed.

## Remote publication

- GitHub release:
  <https://github.com/roberto-fernandez-barrios/qevc/releases/tag/arxiv-v1>
- Zenodo record: <https://doi.org/10.5281/zenodo.21894292>
- Zenodo state: the earlier D-035 release was published 2026-08-12; D-036
  supersedes it for submission and the hashes above are the current source of
  truth.
- arXiv: the D-036 source and metadata are ready but not submitted.
