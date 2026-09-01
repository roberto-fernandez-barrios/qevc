# npj Quantum Information submission release manifest

- Version: `0.3.7`
- Git tag: `npjqi-submission-v1.7`
- Release date: 2026-09-01
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22236115`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical mechanistic-clarity patch retained: `0.3.6` /
  `npjqi-submission-v1.6` / `10.5281/zenodo.22235287`
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
| `output/pdf/npjqi_manuscript.pdf` | 31 | `462536E01462D21F3295BA06F5BEB960E0B765E4849A7E21D2D5D659A65AE3E3` |
| `output/pdf/npjqi_supplementary_information.pdf` | 18 | `B6399EC4CE6293EDAC37ADC7B367D55DCD5B91E698CF2B7BE90450135140D955` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `C4EDC6199B0AC0FC7BEFD568924CC798E24C932ED0D334A534CB380ABAF60B95` |
| `dist/npjqi-submission.zip` | source + three PDFs | `F770DB073FDE333CFA903BBCA7A7ED579DC357CCC632DA274B0C428F8FFAD021` |
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

The 0.3.7 release is a wording micro-patch on 0.3.6: the Contribution-3
mechanism statement is made regime-specific (primary raw decomposition mixed;
diagonal-loading sensitivity decomposes differently; no universal downstream
mechanism claimed) with no change to any number, JSON artifact, seed, result or
gate expectation. The bounded 0.3.6 patch was the mechanistic-clarity /
derived-analysis patch.
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
