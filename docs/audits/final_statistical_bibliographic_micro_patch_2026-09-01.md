# Final 0.3.4 statistical/bibliographic micro-patch audit — 2026-09-01

This audit records only D-045. Version 0.3.3 is the frozen scientific baseline;
no experiment, seed, sample, dataset, model, quantum kernel, feature map,
hyperparameter, claim, threshold, alpha level, likelihood, PSD repair, CMS
result, E16 result, E20 result or QPU job was changed or added.
The release is `0.3.4 / npjqi-submission-v1.4`, with reserved Zenodo DOI
`10.5281/zenodo.22229290` under concept DOI `10.5281/zenodo.21894291`.

## Historical alpha-plus-three-sigma inventory

The literal/name search covered `alpha + 3 sigma`, `alpha + 3 sigma MC`,
`threshold_alpha_plus_3sigma`, `slack_alpha_plus_3sigma`, `3-sigma boundary`
and `binomial slack`. It found:

- E12: the formula and `threshold_alpha_plus_3sigma` field in
  `experiments/E12_confirmatory/run_e12.py`, plus the frozen value 0.05745 in
  `results/tables/E12_confirmatory.json`. The pooled false-claim streams reuse
  each audit draw across the six claim thresholds, so the denominator is not
  an IID sample size. It was historical confirmatory acceptance arm (d).
- E13: the formula and `slack_alpha_plus_3sigma` field in
  `experiments/E13_weighted_certification/run_e13.py`, with 0.08269 in both
  frozen E13 JSON variants. The registered gate compared per-cell Monte-Carlo
  rates at 400 replications and fed `implementation_valid`; it was not
  simultaneous inference across the cell grid.
- E13v2: the frozen falsifier text and formula in `run_e13v2.py`, the two
  occurrences in `docs/weighted_certification_spec.md`, the registry entry,
  and the generic `slack` value 0.09623 in
  `results/tables/E13v2_baw_allocation.json`. It was an implementation gate
  across cells, not the Proposition 3 proof.
- E19: both `threshold_alpha_plus_3sigma` source fields and the frozen
  unweighted/weighted values 0.06182 and 0.05732 in the corrected E19 JSON;
  the superseded nominal-weight variant contains 0.06182 and 0.05728. The
  gate determined the registered E19 falsifier pass, but its pooled streams
  share deployments, audit draws, claims and thresholds.
- Narrative/audit records: Table S4; `docs/experiment_registry.md` (seven
  historical gate references), `docs/weighted_certification_spec.md` (two),
  `docs/formal_results.md` (one), `docs/decisions.md` D-029 (one), and
  `docs/audits/post_campaign_audit_2026-08-11.md` (one binomial-slack note).

All source and JSON values are retained. Table S4 now labels the last column
`Historical heuristic gate` and explicitly states that the binomial expression
over correlated streams is neither an IID sampling standard error nor a
confidence boundary. Formal validity comes from the per-fixed-claim confidence
sequence; pooled rates are descriptive implementation diagnostics. Historical
gate decisions are preserved, but no current scientific conclusion relies on
the pooled gate as a proof of validity.

## Finite-shot quantum-kernel literature and novelty boundary

Primary-source verification gives:

- Abhay Shastry, Abhijith Jayakumar, Apoorva D. Patel and Chiranjib
  Bhattacharyya, “Shot-frugal and Robust quantum kernel classifiers,”
  arXiv:2210.06971v3 (revised 31 December 2023; first submitted 13 October
  2022), DOI 10.48550/arXiv.2210.06971. No separate journal publication DOI
  was identified. The paper relates unbiased finite-shot kernel uncertainty to
  ideal-classifier margins, reliability, margin errors and shot bounds, and
  develops chance-constrained robust SVM formulations.
- Gian Gentinetta, Arne Thomsen, David Sutter and Stefan Woerner, “The
  complexity of quantum support vector machines,” Quantum 8, 1225 (published
  11 January 2024), DOI 10.22331/q-2024-01-11-1225. It analyzes how shot noise
  affects QSVM solution complexity, proving dual and conditional primal
  circuit-evaluation scalings and empirically examining their tightness.

The manuscript now credits prior work for propagation from finite-shot kernel
uncertainty to entries, margins, classifier reliability, accuracy/solution
precision and complexity. The contribution claimed here is the integration:
realized Gram -> refit -> recalibration -> refrozen threshold ->
deployment-relative versus ideal-anchored semantics -> fail-closed claim
resolution -> downstream scientific-inference context.

## Proposition 4 and Tier-A resource accounting

Proposition 4 remains the same formal sufficient sign-stability condition.
Every equation, threshold, cell count and verdict count is unchanged. Its E16
instantiation is now called a retrospective diagnostic: the required target
movements are reconstructed from frozen target rows after deployment. `HOLDS`
is sufficient for truth-sign stability; `FAILS` does not predict a flip, and
resolved-verdict outcomes remain coverage-conditioned.

E16 uses the Tier-A n=2,000 training subset and an analytic unit diagonal. The
symmetric training block therefore contains 2,000 x 1,999 / 2 = 1,999,000
distinct off-diagonal evaluations. Multiplication gives 255,872,000 shots at
128 shots per entry and 8,187,904,000 at 4,096. These training-only counts
exclude calibration/source-validation and target cross-Grams and do not imply
linear wall-clock time, scalable hardware deployment or quantum advantage.

## I3 and visual disposition

The suggested “straw man” characterization is rejected as factually
incomplete. The current manuscript already reports the failed pure-Poisson
model, the attempted and audited Barlow--Beeston-inspired Gaussian aggregate
template-variance/BB-lite correction, and the independent-template limitation
conditional on the archived fixed-template construction and MC size. It makes
no universal claim about all MC-statistical likelihoods, so no I3 text changed.

The final Supplement artifact map was objectively awkward because full paths
could split filename extensions and `decisions.md`. The common
`results/tables/` prefix is now stated once and the filenames are listed
separately; content is unchanged.
