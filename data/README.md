# Data directory

Nothing under `raw/`, `interim/` or `processed/` is committed to git.
Every dataset must be registered here with provenance before use.

| Subdir | Contents |
|---|---|
| `raw/` | Immutable downloads exactly as obtained (checksummed) |
| `interim/` | Deterministic intermediate transforms (regenerable from raw + configs) |
| `processed/` | Final model-ready splits (regenerable; split indices stored) |

## Registered datasets

Populated as datasets pass the audit in `docs/dataset_audit.md`.
Each entry must record: source URL, version/DOI, download date, SHA-256 of the
archive, license, and the exact script that produced any derived files.

### fair_universe (Level I)

- Source: Zenodo record 15131565, `FAIR_Universe_HiggsML_data.zip`
  (DOI 10.5281/zenodo.15131565), downloaded 2026-08-10.
- Archive SHA-256: `adaa3dd81a02663051aa93f960bc1c5ee67a78d25c091015bb020b1f9cd7dcb5`
  (zip deleted after verified extraction; parquet + metadata JSON kept).
- Contents: `FAIR_Universe_HiggsML_data.parquet` — 220,099,101 rows × 31 cols,
  16.80 GB; `FAIR_Universe_HiggsML_data_metadata.json`.
- License: CC-BY-4.0. Cite arXiv:2410.02867.
- Validation: experiments/E00 (see `docs/experiment_registry.md`).

### cms_htautau_mirror (Level II, development working set)

- Source: root.cern verified mirror of the CMS Open Data H→ττ reduced
  NanoAOD outreach files, `https://root.cern/files/HiggsTauTauReduced/`
  (~10% subsets, identical 69-branch schema), downloaded 2026-08-10 via
  `scripts/download_cms_mirror.ps1` into `raw/cms_htautau_mirror/`.
- Canonical records: CERN Open Data 12350–12359 (CC0-1.0); reference
  analysis HIG-13-004 via HiggsTauTauNanoAODOutreachAnalysis.
- Derived: `interim/cms/*.parquet` via `scripts/ingest_cms_all.py`
  (selection + features per `src/qevc/data/cms_htautau.py`; MC weights at
  the mirror's effective luminosity, D-026 context). Used by E11 v1.
- Per-file SHA-256 of the derived parquets recorded in the E11 manifests.

### cms_htautau_full (Level II, E11v2 collision data)

- Source: CERN Open Data records 12358 (`Run2012B_TauPlusX.root`,
  10,918,632,568 B) and 12359 (`Run2012C_TauPlusX.root`), full files from
  `https://opendata.cern.ch/eos/opendata/cms/derived-data/AOD2NanoAODOutreachTool/`,
  downloaded 2026-08-11 into `raw/cms_htautau_full/`. License CC0-1.0.
- Derived: `interim/cms_full/*.parquet` via `scripts/ingest_cms_full.py`
  (D-026: full data + mirror MC re-weighted to LUMI_PB = 11,467 pb⁻¹).
- Per-file SHA-256 recorded in the E11v2 manifest.
