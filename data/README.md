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
