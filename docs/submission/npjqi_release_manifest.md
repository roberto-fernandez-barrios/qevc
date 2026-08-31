# npj Quantum Information submission release manifest

- Version: `0.3.1`
- Git tag: `npjqi-submission-v1.1`
- Release date: 2026-08-31
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22209367`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical release retained: `0.2.0` / `arxiv-v1` /
  `10.5281/zenodo.21894292`
- Historical npj release retained: `0.3.0` / `npjqi-submission-v1` /
  `10.5281/zenodo.22206235`

## Frozen artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 26 | `D526AC37DEA363D811A70E5398A9DB67948599ADD24D86ED6AC77418C239A091` |
| `output/pdf/npjqi_supplementary_information.pdf` | 12 | `081209927410106ACEEF39B977DF55E332367E9E154DDAD399549D6C361DBB61` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `00CAF0E240AC896A2E1A1411E886BF7C806790101A2D64F6CFD4DFEA97711D7B` |
| `dist/npjqi-submission.zip` | source + three PDFs | `5202F8E3996BFE44B025FA7319ACAAD05E824FB375640B3EC5168265CF6A4A38` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `31D13A9D2EA739284DD739C1523120B349787D45C9062B9B21C5527CADE7ED7D` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
five artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.1 patch adds only the deterministic E16 spectral audit,
minimum-diagonal-loading deployment sensitivity and the associated technical
wording corrections. The baseline snapshot in
`docs/audits/final_patch_release_snapshot_2026-08-31.md` predates those edits.
No dataset, primary result, QPU raw record, model implementation, or frozen
experimental configuration was changed by the patch. E20 remains the
preregistered offline NO-GO and no hardware job was run.
