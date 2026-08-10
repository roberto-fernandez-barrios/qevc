# Experiment Registry

Rule (spec §27, §38): an experiment is registered here — question, hypothesis,
falsifier, planned outputs — **before** it is run. Status transitions:
`planned → specified → running → complete | failed | abandoned(reason)`.
Registered falsifiers are never edited after a run starts; corrections get a new
entry.

---

## E00 — Dataset validation

- **Question:** Does the ingested FAIR Universe data reproduce documented schemas,
  distributions, weights, and nuisance semantics?
- **Hypothesis:** none (validation gate).
- **Inputs:** raw benchmark release (version + checksum recorded in
  `docs/dataset_audit.md`).
- **Models:** none.
- **Metric:** schema checks; weighted yield tables vs documentation; distribution
  sanity plots; systematics round-trip checks (θ=0 shift is identity; ±1σ moves
  the documented observables in the documented direction).
- **Falsifier:** any unexplained mismatch with official documentation blocks Gate 1.
- **Outputs:** `experiments/E00_dataset_validation/run_e00.py` →
  `results/tables/E00_validation.json` + manifest.
- **Status:** **complete** (2026-08-10) — ALL PASS (11/11).
  `results/tables/E00_validation.json`, manifests for both runs kept (first run
  failed one check on a 4.6e-5 metadata precision artifact; tolerance set to
  1e-4 with the discrepancy documented in the check itself and audit §1.1).
  Findings: 220,099,101 rows and per-process counts exactly match the paper;
  stored-weight sums match the paper per process; nominal selection keeps 91.3%
  of raw rows; TES=1.02 raises mean `PRI_had_pt` by 1.15% with upward event
  migration (+3,805 events on 200k subsample). Parquet row-group head is
  process-blocked (group 0 is 100% ztautau) — subset loaders must sample by
  global index, never by row-group clusters.

## E01 — Nominal baselines

- **Question:** What is fair nominal performance for classical baselines and the
  quantum-kernel model on identical folds and comparable tuning budgets?
- **Hypothesis:** supports later contrasts (no directional claim).
- **Information set:** source-only (I0 for training discipline).
- **Models:** linear SVC, RBF-SVC, XGBoost, LightGBM, compact MLP, QK-SVC
  (statevector-exact kernel).
- **Metric:** SAP §1.1 suite, nominal test split.
- **Falsifier:** QK-SVC nominal AUC below linear SVC would question the quantum
  pipeline's basic competence (triggers feature-map review before proceeding).
- **Outputs:** `results/tables/E01_nominal.json` + manifest; splits under
  `data/processed/splits/`.
- **Status:** **complete** (2026-08-10, v2 under raw-row partitioning D-013;
  v1 manifest kept, superseded). 300k subset seed 101 → D₀ 274,004 rows;
  roles: train 109,699 / source_val 41,128 / nominal_test 41,116 /
  auditor_dev 41,001 (final_eval sealed). Tier A (matched 2000 events,
  physics-weighted test AUC [95% CI]): QK-SVC 0.8372 [0.782, 0.876] —
  reps 2, scale 0.5, linear entanglement, C=1; XGBoost 0.8597; LightGBM
  0.8535; RBF-SVC 0.7890; MLP 0.7796; linear SVC 0.7165. Paired ΔAUC
  (QK − other): beats linear (+0.121 [0.066, 0.170]), RBF (+0.048
  [0.000, 0.099]) and MLP (+0.058 [0.001, 0.114]); tied with XGBoost
  (−0.022 [−0.053, +0.004]) and LightGBM (−0.016 [−0.046, +0.011]).
  Tier B (train 109,699): XGBoost 0.9091, LightGBM 0.9083, MLP 0.8771,
  linear 0.8013 — scale gap ~5 AUC points over tier A, reported as context.
  **Falsifier check: passed** (QK-SVC ≫ linear SVC; quantum pipeline
  competent at nominal).

## E02 — Systematic landscape

- **Question:** How do all models degrade over the physical nuisance grid?
- **Hypothesis:** H1.
- **Environments:** per-nuisance {−2σ…+2σ} + predeclared LHC combinations.
- **Metric:** `M(θ)`, `Δ_θ` per SAP §1.1; paired quantum–classical contrasts.
- **Falsifier:** Δ_θ CIs include 0 everywhere → H1 unsupported; report as such.
- **Outputs:** `results/tables/E02_landscape.json` + per-env score arrays in
  `results/raw/E02_scores/` (reused by E03–E05).
- **Status:** **complete — first pass** (2026-08-10; single model-training
  seed; the multi-seed replication required by SAP §4 and paired-Δ CIs are the
  registered follow-up pass before any paper claim). 41 environments × 10
  frozen models. Observed patterns:
  1. **TES: clean monotone, sign-antisymmetric response of QK-SVC**
     (ΔAUC +0.0088/+0.0044/−0.0044/−0.0088 across 0.98→1.02) — ~4× the
     sensitivity of matched tier-A XGBoost (±0.003, non-monotone) on the same
     events; RBF shows the same shape at ~2/3 amplitude (kernel-geometry
     signature, feeds H2).
  2. QK-SVC has the largest tier-A worst-case degradation (+0.0345,
     all-worst combo3) — consistent with spec §37's "unusually sensitive
     despite competitive nominal performance" alternative story.
  3. soft_met: strong seed variance (stochastic smearing); consistent
     degradation at 5 GeV, largest for tier-B models (+0.028 XGBoost) —
     scale-trained models exploit MET fine structure and lose more.
  4. Norm nuisances ≈ AUC-invariant (bkg_scale exactly 0 — internal
     consistency check passed: uniform background weight scaling cannot move
     weighted AUC); their effect is deferred to physics-level E08 (H5 design
     confirmed).
  Caveat logged: tier-A per-env AUC CIs (~±0.04) exceed single-env deltas;
  the evidence for H1 currently rests on the monotone grid trend and
  shared-population contrasts, not on per-env significance.

## E02R — Multi-seed replication of E01/E02 (SAP §4)

- **Question:** Do the nominal contrasts and the landscape patterns survive
  partition + initialization variance?
- **Hypothesis:** replication requirement for H1 and the E01 contrasts.
- **Design:** 5 replication seeds; per seed a fresh five-role raw-row
  partition (final_eval sealed), fresh tier-A subsample, fresh model init;
  hyperparameters frozen from E01 (declared: tuning variance not covered);
  focus models A:qksvc, A:rbf_svc, A:xgboost, A:lightgbm, B:xgboost over the
  full E02 grid.
- **Falsifier:** TES sign pattern of A:qksvc fails to replicate (monotone in
  < 4/5 seeds) or nominal QK-vs-XGB contrast flips sign across seeds beyond
  its std.
- **Outputs:** `results/tables/E02R_multiseed.json`.
- **Status:** **complete (2026-08-10) — falsifier PARTIALLY TRIGGERED; the
  single-seed narrative is corrected as follows and these are the numbers
  that gate the manuscript:**
  1. **Nominal contrast:** QK-SVC 0.8478 ± 0.0223 vs A:XGBoost 0.8831 ±
     0.0159; per-seed paired difference **negative in 5/5 seeds**
     (−0.035 ± 0.013). The E01 "tie with XGBoost" was partition luck: with
     replication, the trees are consistently ahead at matched budget; QK-SVC
     remains above RBF (+0.02) and far above linear. Paper framing updates
     to "competitive but below tuned trees" — fully compatible with the
     spec's no-quantum-advantage philosophy.
  2. **TES pattern:** down-shifts replicate (tes=0.98: +0.0024 ± 0.0010;
     tes=0.99: +0.0010 ± 0.0004; sign-consistent 5/5) but are an order of
     magnitude smaller than the single-seed estimate; the up-shift
     "improvement" arm does NOT replicate (monotone ordering in only 2/5
     seeds). H1 language weakened to: *small but replicated QK degradation
     under TES down-shifts and adverse combinations* (combo3: +0.025 ±
     0.024, positive 5/5).
  3. **Partition variance (±0.015–0.022 AUC) dominates most single-nuisance
     deltas** — 13/40 environments sign-consistent for QK. Single-seed
     landscape values must never be quoted without E02R error bars.
  4. **Consequence for E04 (registered follow-up):** its degradation targets
     were single-seed; H2's ρ=0.761 must be re-estimated against E02R
     multi-seed mean deltas before any manuscript claim (E04 v2).

## E03 — Kernel geometry observatory

- **Question:** How does quantum-kernel geometry move under physical systematics?
- **Hypothesis:** H2 (descriptive half).
- **Metric:** geometry descriptor vector `G_θ` (CKA, spectrum, effective rank,
  alignment, margin stats, RKHS class separation…) across the E02 grid.
- **Falsifier:** descriptors statistically flat across θ while E02 shows material
  degradation (records a *negative* geometry result).
- **Outputs:** `results/tables/E03_geometry.json`, Fig. 3 data.
- **Status:** **complete — first pass** (2026-08-10). Findings:
  1. Kernel MMD² rank-correlates positively but weakly with degradation
     magnitude across the 40 environments (quantum kernel ρ≈0.28–0.36; RBF
     ρ≈0.29–0.42; only some nominally significant, uncorrected).
  2. **Noise floor identified:** at n_target=2000, sampling noise on MMD²
     (~±0.0002, measured via the weight-only environments whose feature
     distribution is exactly nominal) is comparable to the signal range;
     only the strongest shifts (soft_met=5, combo3) clear it. E04 must use
     larger/repeated target draws.
  3. **Structural blind spot (important for the paper):** normalization
     nuisances change only event weights, so feature-space geometry is
     *categorically blind* to them — I1-level sensors cannot flag shifts
     that still damage physics inference (E08/H5). This is a designed-in
     limitation of label-free OOD detection in HEP and a direct argument for
     information-set-conditional auditing (Gate 4).
  Follow-up registered for E04: variance-reduced geometry (repeated draws),
  weight-only environments analyzed separately, out-of-environment
  leave-one-nuisance-out protocol.

## E04 — Geometry → failure prediction

- **Question:** Do label-free geometry shifts predict degradation
  out-of-environment?
- **Hypothesis:** H2 (predictive half).
- **Information set:** I1 (unlabeled target only).
- **Metric:** leave-one-nuisance-out regression/rank metrics per SAP §2.
- **Falsifier:** out-of-env rank correlation ≤ 0 or sign-unstable across seeds.
- **Outputs:** `results/tables/E04_geom_failure.json`, Fig. 4 data.
- **Status:** **complete — first pass** (2026-08-10). **H2 falsifier NOT
  triggered for the quantum kernel.** Out-of-environment (LONO) results on
  the 28 feature-shift environments:
  1. Quantum geometry → QK-SVC degradation: pooled ρ = 0.563 (p = 0.002);
     **MMD² alone: ρ = 0.761 (p < 10⁻³)** — the simple sensor beats the
     5-descriptor ridge (overfitting at n≈24 training envs; honest finding).
     Folds: tes +0.8, soft_met +0.48, combos +0.74; jes −0.8 (n=4, JES ΔAUC
     ~0.001–0.003 ≈ noise floor of the single-seed E02 targets).
  2. Transfer: quantum geometry predicts XGBoost degradation too (ρ = 0.589)
     — the sensor tracks the shift itself, not one model's quirks.
  3. RBF-28-feature geometry is much weaker for its own model (pooled
     ρ = 0.082; mmd2-only 0.471) — the bandwidth-limited fidelity kernel on
     the 8 physics features is the better shift sensor in this setup.
  4. CRN worked: quantum MMD² noise floor 7.6e-5 (vs ~2e-4 in E03's
     independent-draw design).
  Caveats carried: degradation targets from single-seed E02; small per-fold n;
  conclusions restricted to feature-shift nuisances (weight-only = structural
  blind spot, E03).
  **v2 (2026-08-10, targets = E02R multi-seed mean |ΔAUC|;
  `results/tables/E04v2_geom_failure_multiseed.json`): H2 survives in
  simple-sensor form.** Quantum MMD² → QK degradation ρ = 0.557 (p = 0.002);
  → XGBoost degradation ρ = 0.682 (p = 10⁻⁴) — the transfer result
  *strengthens* with cleaner targets. The multi-descriptor LONO ridge
  collapses (pooled ρ ≈ 0) — definitively overfit; the manuscript presents
  the univariate MMD² sensor only. RBF-28 geometry fails as a sensor with
  clean targets (own-model ρ = −0.21 n.s.) — the quantum-kernel-as-better-
  shift-sensor asymmetry replicates.

## E05 — Conditional auditor

- **Question:** Which claims are resolvable under I0/I1/I2(n)/I3, with what error
  rates?
- **Hypothesis:** H3, H4.
- **Metric:** auditor-level metrics SAP §1.3; empirical false-certification vs α.
- **Falsifier:** empirical false certification > α (beyond binomial fluctuation)
  invalidates the implementation; auditor that never abstains under I0/I1
  invalidates fail-closed design.
- **Outputs:** `results/tables/E05_auditor.json`.
- **Status:** specified (2026-08-10) — config `configs/experiments/E05.yaml`:
  estimand per D-014 (unweighted correctness at frozen thresholds; exact IID
  Bernoulli streams); claims M_T ≥ M_S − δ, δ ∈ {0.02, 0.05, 0.10}, α=0.05,
  n_max=3000, 20 audit-seed replications; models A:qksvc, A:rbf_svc,
  A:xgboost, B:xgboost over the 41 E02 environments (archived scores).
  I0 = UNRESOLVED by construction; I1 = E03 quantum-MMD² alarm above the
  weight-only noise floor, veto-only; I2 = EB confidence sequence. Truth used
  only to score decisions. I3 and weighted estimands deferred to v2 (D-014).
  **v1.1 amendment (2026-08-10, registered before run 2):** run 1 found ALL
  δ∈{0.02,0.05,0.10} claims true (worst unweighted-accuracy drop 0.0084 —
  far below the AUC drops; threshold-level accuracy is shift-robust here), so
  false certification had no stress cases. Added adversarial claims
  δ ∈ {0, −0.005, −0.01} (τ at/above M_S), several genuinely false by
  simulation truth. Falsifier unchanged.
  **Complete (2026-08-10, run 2; 19,680 claim-streams).** Results:
  1. **Empirical false certification 0.61% ≤ α=5%** (48/7820 streams on
     genuinely false claims; misses concentrated at margins ≥ −0.003) —
     falsifier NOT triggered; implementation validated end-to-end.
  2. False refutation 0.03% (3/11,860).
  3. Fail-closed dominates near the boundary: 98% of false-claim streams end
     UNRESOLVED at n_max=3000 (margins −0.0001…−0.018 need more labels to
     refute); refutation achieved in 108 streams at the larger margins.
  4. Certification landscape (run 1, δ=0.02, margins ≈ +0.02): n* medians
     250–2400 when resolved; majority abstain at 3000 — the E06 landscape's
     first contour, measured.
  5. I0 resolves nothing by construction; I1 alarm (8 envs) veto-only.
  Finding for the paper: at frozen thresholds, unweighted accuracy is far
  more shift-robust than ranking (AUC) — metric choice changes which claims
  are at risk, reinforcing claim-explicit auditing.

## E06 — Partial-label certification landscape

- **Question:** What is `n*(θ, C)` across severity × claims?
- **Hypothesis:** H3.
- **Metric:** n* distributions over seeds; certification landscape regions.
- **Falsifier:** n* ≳ full labeling everywhere (certification adds nothing).
- **Outputs:** `results/tables/E06_nstar.json`, Fig. 5 data.
- **Status:** **complete** (2026-08-10; config `configs/experiments/E06.yaml`:
  E05 claim grid, n_max=20,000, salt "E06", 20 replications). The
  certification landscape is sharply margin-driven (984 claim-cells):
  | \|margin\| | resolved@20k | median n* |
  |---|---|---|
  | <0.005 | 2% | — (UNRESOLVED region) |
  | 0.005–0.01 | 9% | — |
  | 0.01–0.02 | 58% | ~12,700 |
  | 0.02–0.04 | 92% | ~7,100 |
  | 0.04–0.08 | 100% | ~870 |
  | ≥0.08 | 100% | ~180 |
  Validity holds at 20k: false certification 0.72% ≤ α=5%; false refutation
  0.025%. **H3 supported, falsifier not triggered**: claims with ≥0.04
  margins certify with a few hundred labels — far below full labeling; the
  fail-closed UNRESOLVED region is confined to |margin| ≲ 0.01. Environment
  severity enters through the margin (e.g. A:qksvc δ=0.02: nominal n*₅₀=6.4k
  → soft_met=5 n*₅₀=18.8k), giving Fig. 5 its severity axis.

## E07 — Active auditing

- **Question:** Do acquisition strategies reduce n* below random sampling while
  preserving validity?
- **Hypothesis:** exploratory (spec §15).
- **Metric:** n* ratio active/random with CIs; empirical Type-I under active
  acquisition (must stay ≤ α).
- **Falsifier:** no strategy beats random → reported as a primary negative result.
- **Outputs:** `results/tables/E07_active.json`, Fig. 6 data.
- **Status:** **complete — negative result, reported as primary** (2026-08-10).
  Uncertainty-mixture importance sampling LOSES to uniform: median n* ratio
  active/uniform = 1.55 (IQR 1.22–1.92) over 480 jointly-resolved cells;
  active strictly better in only 10%; resolves fewer cells at 20k (0.49 vs
  0.53). Type-I controlled under both (0.45% / 0.10% ≤ α). Interpretation:
  the ×2 importance-weight range halves the effective claim margin on the
  rescaled scale, and misclassification is not concentrated near the frozen
  threshold enough for the variance reduction to compensate. Matches the
  spec §37 alternative story: *simple random target labeling is already
  near-optimal under the tested conditions* — a practically useful, simpler
  protocol. Smarter estimators (LURE-style control variates, stratified
  WoR) registered as candidate v2 before declaring the question closed.

## E08 — Physics-level inference

- **Question:** Does classifier degradation propagate to μ bias / interval
  coverage, and can AUC and coverage decouple?
- **Hypothesis:** H5.
- **Metric:** SAP §1.2 across environments; decoupling search per SAP §6.
- **Falsifier:** no decoupling found on the full grid (negative result for H5).
- **Outputs:** `results/tables/E08_physics.json`, Fig. 7 data.
- **Status:** **complete** (2026-08-10; estimator per D-015). Results:
  1. Internal validity: nominal coverage 0.679–0.687 ≈ 0.6827 for all four
     models (the PE machinery is calibrated where beliefs are correct).
  2. **H5 confirmed, decisively: 89 decoupled cells** (|ΔAUC| < 0.005 with
     mean coverage < 0.6327), across EVERY nuisance family. Flagship:
     A:xgboost at tes=0.98 has ΔAUC = +0.0002 (perfectly healthy classifier)
     and coverage = 0.000 (bias −10 in μ units) — the background yield shift
     (−5.8% of b₀ ≈ 23× σ_stat) is invisible to ranking metrics.
  3. **The geometry-blind normalization nuisances break coverage too**
     (ttbar_scale 12 cells, diboson_scale 11 down to cov 0.003, bkg_scale 6
     down to 0.44): neither classifier metrics NOR label-free geometry
     sensors carry the information that protects the physics — completing
     the paper's central argument for information-set-conditional auditing.
  4. Honest framing (carried into the manuscript): effect sizes are those of
     the deployment-blind single-SR counting estimator with low-purity SRs
     (s/b ≈ 0.2–7%); real profiled analyses degrade far more gracefully. The
     demonstrated claim is that *validity depends on information the
     classifier metrics do not carry*, not that H→ττ physics is hopeless.
     Multi-bin/profiled estimator registered as E08 v2.

## E09 — Finite-shot kernels

- **Question:** How does shot noise interact with systematics and certificate
  stability?
- **Hypothesis:** H6.
- **Environments:** shots ∈ {128…4096} × selected θ from E02.
- **Metric:** kernel estimation error, spectral distortion, PSD violations,
  classifier degradation, certificate flip rate vs K_exact.
- **Falsifier:** no shots×θ interaction and zero certificate flips (negative H6).
- **Outputs:** `results/tables/E09_shots.json`, Fig. 8 data.
- **Status:** **complete** (2026-08-10; config `configs/experiments/E09.yaml`;
  18 configs = shots {128…4096} × 3 kernel seeds; falsifier NOT triggered —
  H6 supported in a specific, bounded form). Results:
  1. Kernel error scales as 1/√shots (Frobenius 13.7% → 2.4%, ratio 5.6 ≈
     √32 — internal consistency ✓); PSD violations at every finite budget
     (0.9% → 0.16%, measured, never repaired); **effective rank inflates
     under shot noise** (353 exact → 489 at 128 shots): spurious spectral
     mass is a measurable estimation artifact.
  2. The classifier is shot-tolerant at n=2000: nominal AUC within ±0.01 of
     exact even at 128 shots.
  3. **Certificate stability: 8 verdict flips / 360 cells (2.2%),
     concentrated at near-boundary claims** (mostly δ=−0.01 UNRESOLVED cells
     and two δ=0.02 cells at the strongest shifts); comfortable-margin
     certificates (δ=0.05) never flip; no shots-monotone flip pattern (flips
     depend on where the noisy deployment's own M_S lands).
  4. **Shots × systematics interaction:** the measured TES response deviates
     from the exact kernel's by up to ±0.031 AUC at 128 shots, shrinking to
     ±0.009 at 4096 — at low budgets shot noise SWAMPS the replicated TES
     effect (+0.0024, E02R): measuring small systematic responses with
     finite-shot kernels requires ≳2–4k shots. Direct E10 design input.

## E10 — Hardware validation

- **Question:** Do representative conclusions survive on a real QPU subset
  (~10² events)?
- **Hypothesis:** complementary evidence for H6 (never statistical backbone).
- **Metric:** K_ideal vs K_shots vs K_hw comparison suite; full provenance per
  spec §19.
- **Falsifier:** n/a — all outcomes (including failed runs) are reported.
- **Outputs:** `results/raw/E10_hw/*` + provenance manifests.
- **Status:** **complete** (2026-08-10; job `d9t2jrvtfhrs73dtd8dg` on
  `ibm_marrakesh`, 496 compute–uncompute circuits × 2048 shots, 32 stratified
  events, median transpiled depth 182 / ~54 2q gates, raw counts archived, no
  mitigation). Results:
  1. **Device noise dominates the estimation budget ~8×:** K_hw deviates
     from K_ideal by 17.0% (Frobenius) vs 1.9% for pure shot noise at the
     same budget → device-noise excess 15.1%. At this circuit depth, going
     beyond ~2k shots buys almost nothing — mitigation or shallower maps are
     the lever, not shots (connects to E09's shots-only curve).
  2. Fidelities are biased DOWN (mean −0.010; worst entry −0.356) — noise
     decays the all-zeros return; the deformation is diagonally-dominant-
     preserving, so K_hw stayed PSD (violation 0.0) with mildly inflated
     effective rank (29.4 → 30.9).
  3. LOO-CV on 32 events: ideal 0.594 / shots ~0.56–0.59 / hardware 0.531 —
     qualitative only (declared); no "hardware-validated" performance claims
     are made from this scale (spec §34 discipline).
  Full provenance in `results/raw/E10_hw/job_provenance.json`; K_ideal,
  K_hw, and raw counts archived.

## E11 — CMS real-data fail-closed demonstration

- **Question:** On real collision data (no truth labels), which claims does the
  auditor accept, refuse, and abstain on — and does it fail closed?
- **Hypothesis:** H4 in deployment conditions.
- **Information set:** I1 (+ control-region aggregates if justified in the audit).
- **Metric:** claims ledger (accepted/refused/unresolved) + observable shift
  diagnostics; never "real-data accuracy".
- **Falsifier:** auditor certifying event-level accuracy claims on real data =
  design failure (must be impossible by construction).
- **Outputs:** `experiments/E11_cms_real_data/` case study + Fig. 9 data.
- **Status:** planned (channel selection pending `docs/dataset_audit.md`).
