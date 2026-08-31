# npj Quantum Information submission release manifest

- Version: `0.3.2`
- Git tag: `npjqi-submission-v1.2`
- Release date: 2026-08-31
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22214449`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical PSD-audited release retained: `0.3.1` /
  `npjqi-submission-v1.1` / `10.5281/zenodo.22209367`
- Historical release retained: `0.2.0` / `arxiv-v1` /
  `10.5281/zenodo.21894292`
- Historical npj release retained: `0.3.0` / `npjqi-submission-v1` /
  `10.5281/zenodo.22206235`

## Frozen artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 27 | `E860D76B2AF5A7E3804722EF845B57F7A916261DBEB655DF3293762E1226DCC5` |
| `output/pdf/npjqi_supplementary_information.pdf` | 12 | `619DDEFD3D697FD1E42F0CC91B6BD51365E27597FE6CE986833382CA17C2D542` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `A9589B2630BA908FE31F831F33BA9DF22566A15F45B5A15B08475FB95DBE3E19` |
| `dist/npjqi-submission.zip` | source + three PDFs | `EF85DC6811F9C9207DC072A34A570E873FB3C23887A8ECAC4C869700DE27699C` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
six artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.2 patch adds only the deterministic instantiation of
Proposition 4 from the already reconstructed E16 deployments and the associated
logical, semantics and metadata corrections. It retains the 0.3.1
minimum-diagonal-loading sensitivity unchanged. The baseline snapshot in
`docs/audits/final_patch_release_snapshot_2026-08-31.md` predates those edits.
No dataset, primary result, QPU raw record, model implementation, or frozen
experimental configuration was changed by the patch. E20 remains the
preregistered offline NO-GO and no hardware job was run.
