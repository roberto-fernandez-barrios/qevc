# Statistical Analysis Plan (SAP)

**Status:** v1.0 — predeclared before any final experimental run.
Amendments require a dated entry in `docs/decisions.md` and must state whether any
affected experiment had already been run at amendment time.

This SAP implements spec §21 (statistical protocol), §13–14 (conditional auditing),
§15 (active auditing) and §16 (physics-level inference).

---

## 1. Estimands and metrics

### 1.1 Classifier-level

For a classifier `f` and environment `P_θ` (nuisance vector θ; θ=0 is nominal):

- **Primary metric:** ROC-AUC under `P_θ`, event-weight aware.
- **Secondary metrics:** balanced accuracy at the source-frozen operating point;
  PR-AUC (signal is rare after weighting); expected calibration error (ECE, 15
  equal-mass bins, weight-aware); Brier score.
- **Degradation:** `Δ_θ(f) = M_0(f) − M_θ(f)` per metric M.

The operating point (decision threshold) is frozen on source validation data and
never re-tuned per environment — deployment cannot re-tune on the target.

### 1.2 Physics-level

Signal-strength estimand μ (benchmark-defined). Per environment and model:

- bias `E[μ̂] − μ_true`;
- RMSE of μ̂;
- mean interval width at 1−α = 0.68 (benchmark convention);
- **empirical coverage** `P(μ_true ∈ CI)` vs nominal — the primary physics-level
  quantity;
- nuisance sensitivity `∂μ̂/∂θ_j` (finite differences on the predeclared grid).

### 1.3 Auditor-level

For a claim `C(M, τ): M_T(f) ≥ τ` (or degradation form `M_T ≥ M_S − δ`) under
information set `I`:

- decision ∈ {SUPPORTED, REFUTED, UNRESOLVED};
- **false certification rate** `P(SUPPORTED | claim false)` — must be ≤ α by
  construction; verified empirically across environments and seeds;
- **false refutation rate** `P(REFUTED | claim true)`;
- abstention rate and its complement (decisiveness) as a function of label budget n;
- `n*(θ, C)`: first label count at which the decision leaves UNRESOLVED (a stopping
  time; see §3).

## 2. Hypothesis → test mapping

| Hyp. | Primary analysis | Falsifier reported when |
|---|---|---|
| H1 | Per-model degradation curves `M(θ)` with bootstrap CIs; quantum-vs-classical contrast of Δ_θ with paired bootstrap over test events | CIs of Δ_θ include 0 across the grid |
| H2 | Out-of-environment R² / Spearman ρ of geometry→degradation regressions (leave-one-nuisance-out CV) | out-of-env rank correlation ≤ 0 or unstable sign across seeds |
| H3 | Empirical `n*` distributions vs the label budget grid | n* exceeds the largest feasible budget in most environments |
| H4 | Existence of environments with UNRESOLVED at all tested n while truth is estimable in-simulation | auditor resolves everything (never abstains) or abstains everywhere |
| H5 | Environments where AUC drop < ε_AUC but coverage drop > ε_cov (thresholds §6) | no decoupling observed anywhere on the grid |
| H6 | Two-factor design shots × θ: interaction term in degradation ANOVA-style decomposition + certificate flip rate between K_exact and K_shots | interaction ≈ 0 and no certificate flips |

## 3. Auditor statistics (the core guarantee)

### 3.1 Confidence machinery

- **Bounded per-event metrics** (accuracy-type, weighted means): anytime-valid
  confidence sequences for bounded means — betting/plug-in empirical-Bernstein CS
  (Waudby-Smith–Ramdas family). These are time-uniform: valid at every n
  simultaneously, hence valid at the stopping time n*.
- **AUC-type claims:** AUC is a two-sample U-statistic, not a bounded mean of IID
  terms; use (a) fixed-n DeLong or bootstrap CIs evaluated only at predeclared
  budget checkpoints with alpha-spending across checkpoints, or (b) a
  sub-sampled one-sample reduction with CS machinery. Method (a) is primary;
  (b) is exploratory.
- **Active acquisition:** unbiased risk estimates via importance weighting
  (LURE-style); CS built on the weighted supermartingale so adaptive selection
  preserves Type-I control. If weights become extreme (ESS < 30% of n), the
  auditor reports UNRESOLVED rather than trusting the estimate (fail-closed).

### 3.2 Decision rule (frozen; mirrors D-006)

At significance α = 0.05 per claim:

- SUPPORTED ⇔ lower CS bound ≥ τ;
- REFUTED ⇔ upper CS bound < τ;
- otherwise UNRESOLVED.

Heuristic sensors (I0/I1 geometry scores) may only (i) flag risk, (ii) prioritize
label acquisition, (iii) veto SUPPORTED into UNRESOLVED under predeclared alarm
conditions. They can never produce SUPPORTED.

### 3.3 Multiplicity

- The per-claim guarantee is the unit of inference (a deployment audits one claim).
- When the paper reports families of claims (across environments/models), we
  additionally report family-wise false-certification counts and, where a family
  conclusion is drawn, Holm–Bonferroni-adjusted decisions as a sensitivity check.
- Alpha-spending across the label-budget grid is unnecessary for CS-based claims
  (time-uniform by construction); it applies only to the fixed-n AUC checkpoints
  (Pocock-style equal spending unless revised here).

## 4. Sampling design

- **Seeds:** 10 seeds for all cheap classical pipelines; ≥ 5 seeds for quantum
  simulation pipelines; ≥ 3 for finite-shot grids (variance dominated by shot
  noise, which is itself replicated); hardware runs as feasibility allows and are
  never used for statistical claims (spec §19).
- Seeds control: train/validation/test splits, model initialization, label-order
  permutations in auditing, shot-noise RNG.
- **Environment grid:** per nuisance, predeclared {−2σ, −1σ, 0, +1σ, +2σ} where the
  benchmark supports it; multi-nuisance combinations via a predeclared Latin
  hypercube (size recorded in the experiment registry before running) plus
  physics-motivated worst-case corners.
- **Splits:** disjoint train / source-val / nominal-test / auditor-dev /
  final-eval partitions with stored indices. The final-eval environments are
  never touched until the analysis code is frozen.

## 5. Interval and effect-size conventions

- Default CI: 95% percentile bootstrap (10⁴ resamples, event-weight aware) for
  descriptive metrics; BCa where skew is material and cost permits.
- Paired model comparisons: paired bootstrap over shared test events; report the
  full CI of the difference, never a bare p-value.
- Effect sizes: absolute metric differences in native units (AUC points, coverage
  points); standardized effects only as supplements.
- Language rule: "significant" is never written without the accompanying
  magnitude and CI (spec §21, §34).

## 6. Practical-relevance thresholds (predeclared)

- Classifier degradation is *material* when |ΔAUC| ≥ 0.01 (1 AUC point).
- Coverage is *damaged* when empirical coverage deviates from nominal 68% by ≥ 5
  points with CI excluding the nominal value.
- H5 decoupling requires: ΔAUC < 0.005 while coverage damage per the above.
- These thresholds calibrate *language* ("material", "damaged"), not the auditor's
  guarantees, which use claim-specific τ/δ.

## 7. What is never done

- No metric on real CMS collision events that requires event-level truth.
- No environment or nuisance value selected post hoc after seeing final metrics.
- No per-environment hyperparameter retuning.
- No reporting of a heuristic score as a bound or certificate.
- No exclusion of failed runs without a logged decision entry.
