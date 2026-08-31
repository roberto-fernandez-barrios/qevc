# Final logical-closure audit — 2026-08-31

## Authorized scope

This 0.3.2 patch is a deterministic derived analysis of the 30 already
reconstructed and frozen E16 deployments. It adds no experiment, seed,
randomness, QPU job, dataset, model, feature map, hyperparameter, PSD repair,
likelihood, claim, CMS analysis or E20 arm. The related manuscript is outside
this repository and was not read, cited or modified.

## Proposition 4 derivation

For the exact ideal deployment `f*` and a realized raw-indefinite or
PSD-repaired deployment `f_tilde_omega`, the replay uses the metric family of
the claim itself:

- unweighted claims: mean correctness over the corresponding frozen source or
  target rows;
- weighted claims: raw-physical-weighted mean correctness over those rows.

It computes

`delta_M_S = M_S(f_tilde_omega) - M_S(f*)`,
`delta_M_T = M_T(f_tilde_omega) - M_T(f*)`, and
`delta_M_T - delta_M_S`.

For claim offset `delta`, the exact ideal margin is
`m* = M_T(f*) - (M_S(f*) - delta)`. The strict sufficient condition is
`abs(m*) > abs(delta_M_T - delta_M_S)` for a deployment-relative claim and
`abs(m*) > abs(delta_M_T)` for an ideal-anchored claim. All reconstructed
thresholds are interior, all exact margin identities have zero residual, and
all 7,200 deployment/cell cases are evaluable.

## Descriptive results

Condition cells and paired audit streams within a deployment are correlated;
the descriptive unit remains the 30 deployments. The following counts are
descriptive stream-level contingencies, not independent replications.

| Cut | Cells | HOLDS | FAILS | Holds (%) | H: flip/no flip | F: flip/no flip |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 7,200 | 4,943 | 2,257 | 68.7 | 4,554 / 44,876 | 13,637 / 8,933 |
| RAW-INDEFINITE | 3,600 | 2,532 | 1,068 | 70.3 | 2,260 / 23,060 | 6,247 / 4,433 |
| PSD-repaired | 3,600 | 2,411 | 1,189 | 67.0 | 2,294 / 21,816 | 7,390 / 4,500 |
| Deployment-relative | 3,600 | 3,341 | 259 | 92.8 | 2,127 / 31,283 | 62 / 2,528 |
| Ideal-anchored | 3,600 | 1,602 | 1,998 | 44.5 | 2,427 / 13,593 | 13,575 / 6,405 |
| Far | 2,400 | 2,288 | 112 | 95.3 | 683 / 22,197 | 967 / 153 |
| Moderate | 2,040 | 1,428 | 612 | 70.0 | 2,955 / 11,325 | 4,112 / 2,008 |
| Near | 2,760 | 1,227 | 1,533 | 44.5 | 916 / 11,354 | 8,558 / 6,772 |

The inequality preserves the truth sign in all 4,943 holding cells. Of the
2,257 failing cells, 1,069 change truth sign and 1,188 do not; this is the
cell-level `HOLDS/FAILS × sign-flip/no-sign-flip` diagnostic. Of the
49,430 condition-holding paired streams, 4,554 (9.2%) change verdict, almost
entirely through resolution/abstention changes; two yield opposite resolved
verdicts, as permitted by Proposition 4's coverage-conditioned `2 alpha`
bound. In contrast, 13,637/22,570 (60.4%) condition-failing streams change
verdict, but 8,933 remain stable. Thus failure is not treated as a predicted
flip, and holding is not empirical proof of a general law.

The bound is most often satisfied for deployment-relative and far-margin
cells, remains useful at moderate margins, and is conservative for near and
ideal-anchored cells. Its substantial separation of observed flip rates makes
the final classification **INFORMATIVELY INSTANTIATED**, while the many stable
failures document its sufficient-not-necessary character.

All far-margin deployment-relative claims in the evaluated grid are true and
remain supported in every raw and PSD-repaired realization. There is no false
far-margin deployment-relative claim with which to assess refutation
stability.

## Interpretation boundaries

The historical RAW-INDEFINITE pipeline remains primary. It fits an SVC to the
realized finite-shot quantum-similarity matrix, but the indefinite object is
not interpreted as the standard convex RKHS SVM associated with a PSD kernel.
The minimum-diagonal-loading analysis is a post-hoc robustness sensitivity: it
restores a PSD training block and hence a convex precomputed-SVM training
problem, while producing a regularized similarity matrix rather than a
normalized fidelity Gram or a claimed global Mercer kernel.

Theorem 1's anytime-valid error control applies to each fixed I2 label-stream
claim, conditional on the frozen finite audit population under the declared
with-replacement protocol. I3 profile-likelihood and auxiliary-information
procedures are separately coverage-gated. CMS and the other empirical ledgers
use their own calibrated tests or information constraints and do not inherit
Theorem 1 automatically. In the label-economics results, `n*` is only an
audit-label draw budget under with-replacement sampling; it is not a count of
unique labels/events, a universal physical labeling cost, or a sample-
complexity lower bound.

## Reproducible artifact

`results/tables/E16_proposition4_instantiation.json` contains the input hashes,
provenance guards, exact per-case movements and margins, condition statuses,
paired verdict outcomes, all requested aggregate cuts and a canonical-payload
SHA-256. The test suite reconstructs the aggregates exactly from the case
table, reevaluates every strict inequality and margin identity, verifies every
recorded protected input byte-for-byte, and rejects QPU submission imports or
calls in the analysis script.

## Local release freeze

- Version/tag: `0.3.2 / npjqi-submission-v1.2`.
- Reserved Zenodo DOI: `10.5281/zenodo.22214449` (concept DOI
  `10.5281/zenodo.21894291`).
- `pytest`: 142 passed.
- Scientific/mathematical/semantic gate: 170/170 passed.
- npj gate: 67/67 passed.
- Citation audit: 38 cited keys, zero missing bibliography entries and zero
  undefined citations/references.
- Clean PDFs: 27-page manuscript, 12-page Supplementary Information and
  one-page cover letter, all A4 with title/author/subject metadata and no
  overfull, undefined-reference or LaTeX-warning lines.
- Independent ZIP build: all three sources compile; page counts and extracted
  text match the packaged PDFs exactly.
- Visual audit: all 40 final pages inspected; no clipping, overlap, broken
  glyph, unreadable table or layout defect observed.
- Protected tracked paths changed: zero. Every E16 primary table, E16 hardware
  raw file, E20 result and CMS result hash recorded in the derived artifact
  remains byte-identical.

| Frozen artifact | SHA-256 |
|---|---|
| `output/pdf/npjqi_manuscript.pdf` | `E860D76B2AF5A7E3804722EF845B57F7A916261DBEB655DF3293762E1226DCC5` |
| `output/pdf/npjqi_supplementary_information.pdf` | `619DDEFD3D697FD1E42F0CC91B6BD51365E27597FE6CE986833382CA17C2D542` |
| `output/pdf/npjqi_cover_letter.pdf` | `A9589B2630BA908FE31F831F33BA9DF22566A15F45B5A15B08475FB95DBE3E19` |
| `dist/npjqi-submission.zip` | `EF85DC6811F9C9207DC072A34A570E873FB3C23887A8ECAC4C869700DE27699C` |
| `results/tables/E16_psd_sensitivity.json` | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
