# Wording micro-patch audit (0.3.7) — 2026-09-01

Authorized by D-047. Release `0.3.7 / npjqi-submission-v1.7`, reserved Zenodo
DOI `10.5281/zenodo.22236115` under concept DOI `10.5281/zenodo.21894291`.
Baseline: `npjqi-submission-v1.6` (mechanistic-clarity patch).

## Change

The Contribution-3 mechanism statement was audited for the phrases
"amplified at the operating point", "leaves ranking largely intact",
"recalibration and threshold refreezing relocate the claims", "downstream
amplification" and "dominant mechanism" in the abstract, Introduction,
Results, Discussion, conclusion paragraph, Supplement, cover letter, README and
submission metadata, and reworded so that it cannot imply that calibration or
threshold selection dominates universally in the raw pipeline and the
diagonal-loading sensitivity, or that thresholding causes the finite-shot
effect. Results states once that the primary RAW decomposition is mixed, that
the PSD sensitivity is more model/ranking dominated, that no universal
downstream mechanism is claimed across kernel treatments, and that threshold
refreezing partly compensates rather than generates the far ideal-anchored
flips in the RAW replay. The abstract has 139 words.

## Scientific integrity

No number, JSON artifact, experiment, Gram realization, seed, sample, dataset,
model, quantum kernel, feature map, hyperparameter, claim, threshold rule,
alpha level, likelihood, CMS analysis, QPU job, PSD repair or gate expectation
changed. `git diff npjqi-submission-v1.6 -- configs data experiments src
results` is empty.

## Gates

- `pytest`: 166 passed.
- npj submission gate: 105/105 passed (new checks: the regime-specific
  statement "do not claim a universal downstream mechanism across kernel
  treatments", the RAW compensation sentence, "decomposes differently" in the
  abstract, and the historical 0.3.6 release retained).
- Release-consistency gate: 113/113 passed (version 0.3.7, tag, DOI, ten
  artifacts, ZIP contents; the manuscript is 31 pages because the last
  reference now ends on a final page, with no overfull box).
- Mathematical/scientific/semantic audit (F8.2): 213/213 passed; semantic
  4-gram coverage draft->LaTeX 95.8%, LaTeX->draft 97.6%.
- Clean build: 31-page manuscript, 18-page Supplementary Information and
  one-page cover letter; no undefined references or citations, no rendered
  `??`, no overfull boxes.
- Independent build from the source ZIP: identical page counts and extracted
  text for all three PDFs.
- Full visual inspection: all 31 + 18 + 1 pages rendered and inspected; no
  clipping, overlap, broken glyphs or missing pages.
- `git diff --check`: passed; `git diff npjqi-submission-v1.6 -- configs data
  experiments src results`: empty (zero scientific-artifact changes).

Final SHA-256 hashes:

| Artifact | SHA-256 |
|---|---|
| `output/pdf/npjqi_manuscript.pdf` | `462536E01462D21F3295BA06F5BEB960E0B765E4849A7E21D2D5D659A65AE3E3` |
| `output/pdf/npjqi_supplementary_information.pdf` | `B6399EC4CE6293EDAC37ADC7B367D55DCD5B91E698CF2B7BE90450135140D955` |
| `output/pdf/npjqi_cover_letter.pdf` | `C4EDC6199B0AC0FC7BEFD568924CC798E24C932ED0D334A534CB380ABAF60B95` |
| `dist/npjqi-submission.zip` | `F770DB073FDE333CFA903BBCA7A7ED579DC357CCC632DA274B0C428F8FFAD021` |
| `results/tables/E16_psd_sensitivity.json` | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |
| `results/tables/E16_stage_decomposition.json` | `F91D4200D2375368E8E21553B00E81F63071C85288FEEB83A848AC82DB6826D5` |
| `results/tables/E16_prop3_margin_stratification.json` | `8C3A654B7B6C7C7B50CA13104F37A117D7F54F0C942799203D12CD7E96692043` |
| `results/tables/E13_wmax_nominal_bound_sensitivity.json` | `8B72B4F9B9CC646473E1DAF707D68BA3BCF9516CA10F210E6B69674408C4ADB5` |
