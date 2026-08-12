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
| `manuscript/latex/main.pdf` | 26 | 850,886 | `9F798522ED240BD7F76915877068291EBBC5FDC9ECEDBDC18EF6115D8DEA4D2F` |
| `manuscript/supplementary/supplement.pdf` | 7 | 411,805 | `83C4279415295313903E1D052FA856C880809740B708DD88AB2A02F3074B1C22` |
| `dist/arxiv-v1-source.zip` | — | 622,685 | `9C439AF7628567F490ABD60AA36A38A2EEC3FC5D85B846AC79DD223235FF8646` |
| `dist/qevc-arxiv-v1.zip` | — | 3,561,869 | `24F350C79AD5585D803D73D241F2389BF07B6C2E963E289B6861ADDD053CD2AB` |

The source archive contains `main.tex`, its generated `main.bbl`, all 11
main-document figure PDFs, and the supplement PDF plus source and Figure S16
under `anc/`. Both top-level and ancillary sources independently compile to
the page counts above with zero unresolved citations/references or overfull
boxes.

## Verification gate

- F8.2 executable audit: 81/81 checks passed.
- Semantic four-gram coverage: 90.5473% Markdown→LaTeX and 92.4084%
  LaTeX→Markdown.
- Repository test suite: 127/127 passed.
- All 33 final PDF pages visually inspected.
- seed-101 and seed-121 `final_eval` remain sealed for journal review.
- Nine registered falsifier firings are retained and disclosed.

## Remote publication

- GitHub release:
  <https://github.com/roberto-fernandez-barrios/qevc/releases/tag/arxiv-v1>
- Zenodo record: <https://doi.org/10.5281/zenodo.21894292>
- Zenodo state: published 2026-08-12 with four files; every remote MD5
  matched its local artifact before the irreversible publish action.
- arXiv: source and metadata ready, but not submitted; publication was
  explicitly deferred by the author on 2026-08-12.
