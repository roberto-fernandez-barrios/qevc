# Mechanistic-clarity / derived-analysis patch audit — 2026-09-01

This audit records the bounded 0.3.6 patch authorized by D-046. The release is
`0.3.6 / npjqi-submission-v1.6`, with reserved Zenodo DOI
`10.5281/zenodo.22235287` under concept DOI `10.5281/zenodo.21894291`. The
scientific baseline is `npjqi-submission-v1.5`.

## Reproduction of the external report's M1 figures (from frozen JSON only)

| Quantity | Report | Reproduced |
|---|---|---|
| Spearman(ΔM_S, far ideal-anchored flip rate), 30 deployments | −0.92 | −0.923 |
| Spearman(nominal-AUC difference, ΔM_S) | −0.13 | −0.126 |
| `shots256|k5`: nominal AUC / ideal AUC | 0.8436 / 0.8372 | 0.84362 / 0.83724 |
| `shots256|k5`: source accuracy / ideal; BA_w; threshold; far flips | 0.673 / 0.759; 0.769; 0.00069; 88.5% | 0.67348 / 0.75912; 0.76946; 0.00068718; 88.5% |
| \|ΔM_T − ΔM_S\| median / max (RAW deployment-relative cells) | 0.0011 / 0.0052 | 0.0011 / 0.0052 (PSD 0.0012 / 0.0063) |
| \|ΔM_T\| median / max (RAW ideal-anchored cells) | 0.019 / 0.140 | 0.0187 / 0.1403 (PSD 0.0221 / 0.1476) |

No discrepancy. The correlations are descriptive (six shot budgets, five
realizations each); no population inference is drawn from their p-values. The
report's expectation that the 2.05 bound inflates stopping times by ~4× was
NOT confirmed (see the weight-bound section).

## Falsifiers and outcomes

- F1 exact endpoint reproduction: PASSED (30/30 RAW primary rows, 30/30 RAW
  archived payloads, 30/30 PSD archived payloads; Proposition-3 movement
  residual 0.0 over 1,800 + 1,800 cells).
- F2 separability without new choices: PASSED (declared order fit →
  evaluation → calibration → threshold; all Platt slopes positive).
- F3 threshold dominance written only if measured: threshold is NOT dominant;
  the manuscript does not say it is.
- F4 common-mode in RAW and PSD: PASSED in both regimes.
- F5 stratification reproduces 7,200 cells: PASSED (4,943 HOLDS / 2,257 FAILS).
- F6 exact historical replay before the bound sensitivity: PASSED for E13
  Part B and for the E19 weighted arm.

## Stage decomposition (RAW / PSD), 30 deployments each

| Stage | ΔM_S median RAW | far IA flips RAW (%) | ΔM_S median PSD | far IA flips PSD (%) |
|---|---:|---:|---:|---:|
| B0 fit-only | −0.0009 | 0.0 | −0.0535 | 60.3 |
| B model-only | −0.0059 | 0.2 | −0.0608 | 64.9 |
| C model+calibration | −0.0154 | 14.3 | −0.0241 | 31.4 |
| D full deployment | −0.0082 | 9.6 | −0.0096 | 17.9 |

Mean absolute increment shares of source unweighted accuracy (RAW): fit 3.9%,
evaluation 15.1%, calibration 31.0%, threshold 50.0%; positive far-flip
increment shares: model 1.4%, calibration 98.6%, threshold 0%. Predeclared
classification: RAW MIXED; PSD MODEL/RANKING-DOMINATED (decision-function
scale change under diagonal loading; ranking unchanged); overall MIXED.
Ranking stability of the realized decision function on `source_val`: median
Spearman 0.923 (min 0.855), Kendall 0.780 (min 0.675). Weighted balanced
accuracy at stage D moves by a median 0.0073 (RAW) / 0.0065 (PSD) against
0.0139 / 0.0147 for unweighted accuracy and 0.0244 / 0.0287 for weighted
accuracy; it is the smaller movement in 25/30 RAW and 28/30 PSD deployments.
Exact role of the operating threshold: it does not generate the far-margin
flips (they appear at recalibration with the ideal threshold held fixed); its
refreezing carries the largest absolute metric increment with the opposite
sign and partly compensates them.

## Weight-bound audit

For the D-032 nominal-weight estimands the revealed increment never exceeds
max_i w_i^(0); κ_norm = 2.05 is deliberate conservatism, not a validity
requirement. Sharp-bound sensitivity on identical streams (registered analysis
unchanged): E13 resolved A_w streams 7,079 → 6,882 of 19,680; false
certification 2 → 12 of 8,580; median cell n*_w 1,229 → 1,001; per-claim ratio
median 0.85 (IQR 0.67–0.98); n*_w/n*_unw median 1.664 → 1.336. E19 weighted
arm: 6 → 12 of 7,980 false certifications; resolved 34.8% → 33.5%; median n*
682.5 → 558. Resolution shifts toward near-boundary cells (46 → 72 resolved
streams below |margin| 0.01) and away from far cells (6,082 → 5,945 at
|margin| ≥ 0.04), consistent with the capped-λ early regime of the
empirical-Bernstein sequence.

## Editorial corrections (verified individually)

- `Sec.~\ref{sec:related}` self-reference to Section 1: the reference and the
  dangling label were removed (the Introduction keeps no subheading, as the
  journal gate requires); `sec:results`, `sec:limitations` and
  `sec:conclusion` were unreferenced labels and were removed.
- `INFERNO --- \citealp{...}` rendered as "INFERNO — 27"; now `\citep`.
- Historical `proposition4` artifact names unchanged; one correspondence note
  in the main text and one in the Supplement.
- MLP and linear SVC were trained and archived in E01 (not ghosts); their
  nominal test performance is now tabulated (Supplementary Table S17).
- Fig. 8 caption defines a verdict flip and the min–max bars.
- References: Ait Haddou et al. third author spelled "Elharrauss" per the
  PTEP version of record; Brown, He, Agliardi, Shastry, Gentinetta and Casas
  metadata verified against primary sources (no change needed);
  Waudby-Smith & Ramdas (arXiv:2006.04347) added as future work.

## Scientific integrity

No experiment, Gram realization, seed, sample, dataset, model, quantum kernel,
feature map, hyperparameter, claim, threshold rule, alpha level, likelihood,
CMS analysis, QPU job, PSD repair, E16 primary artifact or E20 result was added
or changed. `final_eval` was not used. The three new artifacts are derived
from frozen inputs with no new randomness and declare their provenance.

## Final gates and artifact freeze

- `pytest`: 166 passed (139 pre-existing + 27 of the new
  `tests/test_mechanistic_clarity_patch.py` and the updated protected-artifact
  allowlist), including exact reproduction flags for all 30 original E16
  deployments and both archived endpoint sets, the telescoping identities, the
  recomputable predeclared classification, the 7,200-cell stratification
  `--check`, the historical w_max results, no new RNG seeds, no QPU path,
  unchanged historical filenames, natural proposition numbering, the resolved
  `sec:related`, no undefined references/citations, and the protected-hash
  diff against `npjqi-submission-v1.5`.
- npj submission gate: 104/104 passed (new checks: stage-decomposition
  reproduction and classification synchronization, non-monotonicity demoted,
  common-mode statement, margin-stratification artifact, post-hoc exact
  weight-bound sensitivity, without-replacement future work only,
  measurement-induced semantics, C2 adverse result leads, editorial
  corrections, historical artifact names unchanged, plain-language abstract
  of 130--150 words).
- Release-consistency gate: 113/113 passed (version 0.3.6, tag, DOI, ten
  artifacts, ZIP contents, formal numbering, append-only historical records,
  unchanged historical audit files).
- Mathematical/scientific/semantic audit (F8.2): 213/213 passed, including
  recomputation of every displayed row of Tables S10, S11, S16 and S18 and of
  the stage-decomposition and weight-bound headline numbers from their JSON
  sources; semantic 4-gram coverage draft->LaTeX 95.8%, LaTeX->draft 97.6%.
- Citation audit: 43 cited keys, all defined; the DOI of the new
  Waudby-Smith & Ramdas entry and the PTEP author spelling verified against
  primary sources; the Zenodo artifact entry updated to 0.3.6.
- Clean build: 30-page manuscript, 18-page Supplementary Information and
  one-page cover letter, with no undefined references or citations, no
  rendered `??`, no overfull boxes in the manuscript and none in the
  Supplement after the audit-trail row was shortened.
- Independent build from the source ZIP: all three PDFs have identical page
  counts and identical extracted text; the bytes differ only in the pdfTeX
  creation/modification timestamps and the trailer ID (identical after
  stripping those fields).
- Full visual inspection: all 30 + 18 + 1 pages rendered and inspected; no
  clipping, overlap, broken glyphs, missing pages or illegible final-size
  elements.
- `git diff --check`: passed.
- Protected scientific inputs: zero changed paths under `configs`, `data`,
  `experiments`, `src`, `results/raw`, `results/manifests` and the frozen
  E16 runner/replay scripts against `npjqi-submission-v1.5`; the only
  additions under `results/tables` are the three derived JSON artifacts.
- Derived scripts: no `default_rng` call, no seed assignment, no QPU import;
  the only RNG use is the frozen E16 schedule and the frozen E13/E19 stream
  salts inside the frozen runners.

The Git commit/tag and the GitHub/Zenodo byte-for-byte public-asset
verification are reported in the final release handoff, because they occur
after this audit file is frozen into the release commit.

Final SHA-256 hashes:

| Artifact | SHA-256 |
|---|---|
| Manuscript PDF (30 pages) | `9F5E59F1A54CBDB93D0B55D7B65D07CD9CABA72375140EFC6B8D58DA629DE87F` |
| Supplementary Information PDF (18 pages) | `EC8AE562B1516AEBEDF6F69C62CEACD53F227E3FF5528ADF77D4B07B16082D4E` |
| Cover letter PDF (1 page) | `2E7BE8DA767664DE104FA9A4087D8F893BD84EDD2DFCB3AA33072666247F632F` |
| Submission ZIP | `ECBC312C8BD145A15FCB123B3BC54CF8196D2C63C493763FBE7C7656E14B23D3` |
| E16 PSD sensitivity JSON | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| E16 Proposition-3 instantiation JSON (historical name) | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| E16 Proposition-3 deployment summary JSON (historical name) | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |
| E16 stage decomposition JSON (new) | `F91D4200D2375368E8E21553B00E81F63071C85288FEEB83A848AC82DB6826D5` |
| Proposition-3 margin stratification JSON (new) | `8C3A654B7B6C7C7B50CA13104F37A117D7F54F0C942799203D12CD7E96692043` |
| Weight-bound sensitivity JSON (new) | `8B72B4F9B9CC646473E1DAF707D68BA3BCF9516CA10F210E6B69674408C4ADB5` |
