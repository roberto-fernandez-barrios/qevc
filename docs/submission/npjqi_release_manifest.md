# npj Quantum Information submission release manifest

- Version: `0.3.5`
- Git tag: `npjqi-submission-v1.5`
- Release date: 2026-09-01
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22231469`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical statistical/bibliographic patch retained: `0.3.4` /
  `npjqi-submission-v1.4` / `10.5281/zenodo.22229290`
- Historical final micro-patch retained: `0.3.3` /
  `npjqi-submission-v1.3` / `10.5281/zenodo.22227158`
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
| `output/pdf/npjqi_manuscript.pdf` | 28 | `FAC684BD7173972E4941DD323D53ED0B96A97BB96AC7DC881A2FD5E538447D79` |
| `output/pdf/npjqi_supplementary_information.pdf` | 14 | `D56B56549F10AB312ED7890702527FA21C789829D677217772209EEDD7D0ADFB` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `4692B5C4CE27211F8D49E7C63D067BAA35E0F7D145E5C99CF3669560AE8B713A` |
| `dist/npjqi-submission.zip` | source + three PDFs | `B5E4256A1583AB345D67E0FAA6EB0C14DD097A1B4298068E2EDF74E19DF68A2A` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | 30 noisy-kernel deployments | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
seven artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.5 patch changes submission hygiene only. It synchronizes
release documentation with the built artifacts, updates the cover-letter date,
uses natural theorem/proposition numbering with counters separated by type, and
applies a 0.5 pt bibliography-spacing microadjustment to remove a two-line
orphan final page. It retains the 0.3.4 scientific baseline, all derived JSON
artifacts and every historical release unchanged. No dataset, primary result,
QPU raw record, model implementation, frozen experimental configuration, seed,
repair strategy, CMS result or E20 result changed. No scientific result was
regenerated.
