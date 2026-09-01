# npj Quantum Information submission release manifest

- Version: `0.3.4`
- Git tag: `npjqi-submission-v1.4`
- Release date: 2026-09-01
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22229290`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
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
| `output/pdf/npjqi_manuscript.pdf` | 29 | `76E774B3C30928546DCC6B042F211583EA6E702934A01D609A0C3348A758BBA8` |
| `output/pdf/npjqi_supplementary_information.pdf` | 14 | `9BB1B71BC863C5B9C970B5231B4DE23343046C33EF25524E85364DE55FCB66A4` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `E400C623423E4B5BBBEC842B52BCC23A9B22129A4230A9E527D1C620F5BE6685` |
| `dist/npjqi-submission.zip` | source + three PDFs | `0ADCFC7EC856E39E714794A530F4AD876EAAFBA3E75F7244876A149F4D68A4C1` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | 30 noisy-kernel deployments | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
seven artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.4 patch removes IID uncertainty semantics from historical
alpha-plus-three-sigma implementation gates, adds two directly relevant
finite-shot quantum-kernel references, marks the frozen Proposition 4 replay
as a retrospective diagnostic, and states the Tier-A training-Gram shot count.
It also fixes objective filename wrapping in the Supplement. It retains the
0.3.3 scientific baseline, 0.3.2 instantiation and 0.3.1
minimum-diagonal-loading sensitivity unchanged. No dataset, primary result,
QPU raw record, model implementation, frozen experimental configuration, seed,
repair strategy, CMS result or E20 result changed. E20 remains the
preregistered offline NO-GO and no hardware job was run.
