# npj Quantum Information submission release manifest

- Version: `0.3.0`
- Git tag: `npjqi-submission-v1`
- Release date: 2026-08-31
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22206235`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical release retained: `0.2.0` / `arxiv-v1` /
  `10.5281/zenodo.21894292`

## Frozen artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 26 | `30CB232B95119CB593DD927A909CD78269B40F8C44F9D69BF04E4E7411A42BD7` |
| `output/pdf/npjqi_supplementary_information.pdf` | 11 | `52904EB164AC6E24409F16911A98639968E726AE6F685023F87F71547513C8AC` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `895AF4A38561D70889863C7C81CBF0F9482455988C25ED9E754D6B2FCBF08E01` |
| `dist/npjqi-submission.zip` | source + three PDFs | `B8CF241218C8D472CAC8D7637D706E22120A9F26426CE019CD10D411429BDA96` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
four artifacts. The Zenodo upload additionally contains this checksum file and
the release README.

## Scope integrity

The final 2026-08-31 patch changed literature positioning, claim hierarchy,
methodological exposition, typography, release metadata and generated
publication artifacts. The baseline snapshot in
`docs/audits/final_patch_release_snapshot_2026-08-31.md` predates those edits.
No dataset, primary result, QPU raw record, model implementation, or frozen
experimental configuration was changed by the patch. E20 remains the
preregistered offline NO-GO and no hardware job was run.
