# npj Quantum Information submission release manifest

- Version: `0.3.3`
- Git tag: `npjqi-submission-v1.3`
- Release date: 2026-09-01
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22227158`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical logical-closure release retained: `0.3.2` /
  `npjqi-submission-v1.2` / `10.5281/zenodo.22214449`
- Historical PSD-audited release retained: `0.3.1` /
  `npjqi-submission-v1.1` / `10.5281/zenodo.22209367`
- Historical release retained: `0.2.0` / `arxiv-v1` /
  `10.5281/zenodo.21894292`
- Historical npj release retained: `0.3.0` / `npjqi-submission-v1` /
  `10.5281/zenodo.22206235`

## Frozen artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 28 | `482364C9FC18803DE8159A5C6B15E1ED0EBAE8B13C8037E848400EDFA2BF161B` |
| `output/pdf/npjqi_supplementary_information.pdf` | 13 | `3DD6FC8135250D6DFB6BABCE0308F14EEC9928A18EF15E27253330DB242695AF` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `214B31ECA7F7F3ECF240094D1DA909A0FF8602CE19B550F1189F3C77670FABC6` |
| `dist/npjqi-submission.zip` | source + three PDFs | `3EDDE555413B358EDBA2D1DA859E526A7D5CAEDA5ED70E344F588C1E156FC940` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | 30 noisy-kernel deployments | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
seven artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.3 patch adds two adjacent primary references, exact scope
wording and one deterministic deployment-level summary derived exclusively
from the frozen Proposition 4 JSON. It retains the 0.3.2 instantiation and the
0.3.1 minimum-diagonal-loading sensitivity unchanged. No dataset, primary
result, QPU raw record, model implementation, frozen experimental
configuration, seed, repair strategy, CMS result or E20 result changed. E20
remains the preregistered offline NO-GO and no hardware job was run.
