# npj Quantum Information submission release manifest

- Version: `0.3.9`
- Git tag: `npjqi-submission-v1.9`
- Release date: 2026-09-02
- Journal state: frozen and ready for portal upload; not yet submitted
- Zenodo version DOI: `10.5281/zenodo.22254835`
- Zenodo concept DOI: `10.5281/zenodo.21894291`
- Historical editorial focus / concision patch retained: `0.3.8` /
  `npjqi-submission-v1.8` / `10.5281/zenodo.22250951`
- Historical wording micro-patch retained: `0.3.7` /
  `npjqi-submission-v1.7` / `10.5281/zenodo.22236115`
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
| `output/pdf/npjqi_manuscript.pdf` | 31 | `42E86D13B1AA872EFC1B0C89A8C1D23C6A841D0A89C2BEA7C7EFB66F1FD24BE5` |
| `output/pdf/npjqi_supplementary_information.pdf` | 18 | `F442F1F5A6FF54590B3FEA94929B84DC5ED6E7F4ACBDC436458215D1F788A977` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `CBE6FA5ACC444C149082E795A44628866E2C4E22FC40373E38AB85994AF73FA4` |
| `dist/npjqi-submission.zip` | source + three PDFs | `096393294DDCF9EB3498DBA822E461A3AEA1A3C2099BE9D1B29F143677A9C430` |
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

The 0.3.9 release is a figure-legibility and final literature / prior-art
patch on 0.3.8: seven figure files re-rendered for label legibility (no data
change), panel-label and Supplementary Table S2 layout repairs, three added
references (Alexe et al. 2026; Miroszewski 2026; Howard et al. 2021), two
version-of-record updates (FAIR Universe, NeurIPS 2025 Datasets and
Benchmarks; Waudby-Smith and Ramdas, NeurIPS 2020) and three compact
positioning sentences, with no change to any number, result JSON, seed,
claim or gate semantics and no new priority claim.
The 0.3.8 release is an editorial focus / concision patch on 0.3.7: main-text
shortening and de-jargonization, the Proposition-3 formal statement freed of
the general stability-ordering clause (mathematics unchanged), the abstract's
classical-control scope restricted to nominal-performance and sensing
effects, the finite-template-statistics condition co-located with every
Contribution-2 coverage statement, added Hubregtsen (2022) and
Barlow--Beeston (1993) citations, figure-layout legibility fixes (no figure
file changed) and a freeze/provenance column in Supplementary Table S1, with
no change to any number, JSON artifact, seed, result or gate expectation.
The 0.3.7 release was a wording micro-patch on 0.3.6: the Contribution-3
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
