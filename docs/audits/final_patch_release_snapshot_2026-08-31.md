# Final patch-release pre-edit snapshot — 2026-08-31

This snapshot was taken before the D-040-bounded manuscript/release edits. The
working tree already contained the adopted D-038 senior-author revision and the
D-039/E20 offline NO-GO record, but those changes had not been committed to the
public `main` branch.

## Repository state

- HEAD and `origin/main`: `2e57201e729d3f04d3382e6faff8b7b7a58dec40`
- HEAD date/message: `2026-08-13T12:22:03+02:00` — `Freeze npj Quantum
  Information submission package`
- Pre-edit status: 38 modified tracked paths and 9 untracked paths.
- The dirty state comprised the adopted D-038/D-039 manuscript, audit,
  presentation and derived-summary changes. It included no modified dataset,
  primary result table, raw QPU record, model implementation or frozen
  deployment configuration. The untracked E20 files document and implement the
  preregistered offline gate; `results/tables/E20_offline_gate.json` records
  `qpu_jobs_submitted = 0`.

## Frozen artifacts before this patch release

| Artifact | Pages | Page size | Bytes | SHA-256 |
|---|---:|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 25 | A4 | 850808 | `E558035AAC9E4595499AB8CEBCEF25C88017C2CA9891E4C507CB482384618A01` |
| `output/pdf/npjqi_supplementary_information.pdf` | 9 | Letter | 426026 | `9B29938A91771B1622E3C3BB1C0A61CD458FCC04BC90218C73A87A7EA804A565` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | Letter | 85979 | `D353A304B009D3E2B84A2D1F187B39BEE47C3A6C66A5437357368CECCC910189` |
| `dist/npjqi-submission.zip` | — | — | 1375091 | `3F43E7AF707C296C5FC59863C33528F14862D08B967F09FAC2DF674EF44D6F87` |

The manuscript and Supplementary Information therefore had inconsistent page
sizes before this patch release.

## Passing pre-edit verification

- `pytest -q`: 127 passed.
- `scripts/verify_npjqi_submission.py`: 53/53 checks passed.
- `scripts/verify_f8_2.py`: 146/146 checks passed; semantic 4-gram coverage
  draft-to-LaTeX 94.9965%, LaTeX-to-draft 97.1415%.
- The package PDFs were byte-identical to the copies embedded in
  `dist/npjqi-submission.zip`.

These checks establish the baseline for detecting unintended scientific or
release changes; passing them did not resolve the public GitHub/Zenodo version
mismatch that motivates D-040.
