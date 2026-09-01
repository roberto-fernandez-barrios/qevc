# npj Quantum Information submission release manifest

- Version: `0.3.6`
- Git tag: `npjqi-submission-v1.6`
- Release date: 2026-09-01
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22235287`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical submission-hygiene patch retained: `0.3.5` /
  `npjqi-submission-v1.5` / `10.5281/zenodo.22231469`
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
| `output/pdf/npjqi_manuscript.pdf` | 30 | `9F5E59F1A54CBDB93D0B55D7B65D07CD9CABA72375140EFC6B8D58DA629DE87F` |
| `output/pdf/npjqi_supplementary_information.pdf` | 18 | `EC8AE562B1516AEBEDF6F69C62CEACD53F227E3FF5528ADF77D4B07B16082D4E` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `2E7BE8DA767664DE104FA9A4087D8F893BD84EDD2DFCB3AA33072666247F632F` |
| `dist/npjqi-submission.zip` | source + three PDFs | `ECBC312C8BD145A15FCB123B3BC54CF8196D2C63C493763FBE7C7656E14B23D3` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | 30 noisy-kernel deployments | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |
| `results/tables/E16_stage_decomposition.json` | 30 RAW + 30 PSD deployments, 4 stages | `F91D4200D2375368E8E21553B00E81F63071C85288FEEB83A848AC82DB6826D5` |
| `results/tables/E16_prop3_margin_stratification.json` | 7,200 condition cells | `8C3A654B7B6C7C7B50CA13104F37A117D7F54F0C942799203D12CD7E96692043` |
| `results/tables/E13_wmax_nominal_bound_sensitivity.json` | E13 Part B + E19 weighted arm | `8B72B4F9B9CC646473E1DAF707D68BA3BCF9516CA10F210E6B69674408C4ADB5` |

The machine-readable checksum source is `npjqi_checksums.sha256`. The public
GitHub release and Zenodo version must expose byte-identical copies of these
ten artifacts. The Zenodo upload additionally contains this checksum file,
release manifest, metadata record and release README.

## Scope integrity

The bounded 0.3.6 patch is the mechanistic-clarity / derived-analysis patch.
It adds three deterministic derived analyses of already frozen artifacts (the
E16 stage decomposition, the Proposition-3 margin stratification and the
sharp-nominal-bound sensitivity of the weighted certification), the
corresponding framing corrections (C3 mechanism, common-mode cancellation,
non-monotonicity demoted to deployment heterogeneity, C2 adverse result as
headline, plain-language abstract) and objective editorial corrections. It
retains the 0.3.5 scientific baseline: no dataset, primary result, QPU raw
record, model implementation, frozen experimental configuration, seed,
repair strategy, CMS result or E20 result changed, and no scientific result
was regenerated with new randomness. Historical artifact filenames containing
`proposition4` remain unchanged.
