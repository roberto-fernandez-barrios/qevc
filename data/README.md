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
