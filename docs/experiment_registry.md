# Experiment Registry

> **Phase 10 adversarial review (2026-08-10):** findings and dispositions in
> `docs/decisions.md` D-016–D-018 and the annotations below. A clean-tree
> regeneration campaign re-executes E00–E09, E02R, E04v2 and E11 from one
> commit (D-016); numbers quoted below are superseded by the regenerated
> tables where they differ (they should not, runs are seeded — the campaign
> exists to make manifests honest, and to add the matched-kernel control).
> **Regeneration campaign complete (2026-08-11, commit 627796d):** all 13
> simulation experiments re-executed clean (`git_dirty: false`); seed-101
> numbers reproduced exactly (determinism verified). **Matched-kernel control
> verdicts (finding 3, decisive):** RBF-SVC on the identical 8 features =
> 0.8598 nominal / 0.8588 ± 0.0160 replicated — indistinguishable from
> QK-SVC (per-seed difference sign-unstable) and at tuned-tree level; the
> rbf8 MMD² sensor achieves ρ_S = 0.730 own-model / 0.601 transfer —
> *better* than the quantum sensor. "QK above RBF" and
> "quantum-kernel-as-better-sensor" were feature-set effects; both claims
> retired from the manuscript, replaced by the model-agnostic recipe
> (bandwidth-limited kernel on compact sentinel-free physics features).
> **E08 gated decoupling:** 73 cells / 65 unique (θ, model) pairs / 23
> distinct θ survive the E02R gate (was 89 raw single-seed cells).
> Scoping corrections adopted: (i) I1 geometry evidence is *rate-free*
> feature-distribution evidence — its blindness to normalization nuisances is
> a statement about the benchmark's weight-only implementation and this
> information set, NOT an impossibility claim for all label-free monitoring
> (rate/CR monitoring does carry that information, as E11's C2 shows —
> finding 2); (ii) "quantum kernel is the better sensor" is suspended until
> the rbf8 matched-kernel control (finding 3) reports; (iii) H5 cell counts
> are E02R-gated and deduplicated to unique θ (finding 4); (iv) E05's
> pooled false-certification rate is over false-claim streams (48/7,820),
> with per-cell max 2/20 (three near-boundary cells, within binomial
> fluctuation of α); (v) E06 n* medians are conditional on resolution and
> with-replacement draws (a WoR caveat applies at large budgets);
> (vi) environment counts: 28 unique θ + seed replicates + nominal = 41
> evaluations.

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
- **Outputs:** `results/tables/E11_cms_case_study.json` + Fig. 9 data.
- **Status:** **complete** (2026-08-10; H→ττ 2012 μτ_h, root.cern 10%
  mirror; MC 12,445 / data 12,557 selected; QKSVC + XGBoost with E01-frozen
  hyperparameters, no target tuning — MC-val AUC 0.736 / 0.851). The ledger:
  | Claim | Requires | Verdict | Evidence |
  |---|---|---|---|
  | C1 event accuracy on data | I2 labels | **UNRESOLVED** | labels do not exist — fail-closed by construction (the falsifier: certifying this would be design failure — did NOT happen) |
  | C2 W norm within 30% (high-mT CR) | I1+CR | **SUPPORTED** | data/MC = 0.922 [0.885, 0.961] |
  | C3 no MC→data shift at sensor floor | I1 | **REFUTED** | QK-MMD² 0.0030 vs floor 0.0011 (2.6×) — sim-to-real shift detected; alarm vetoes performance claims |
  | C4 SS QCD excess | I1+CR | **SUPPORTED** | +1,007 events over MC, z = 18.6 (the data-driven QCD method's premise) |
  The demonstration lands the paper's thesis on real collision data: aggregate
  physics claims ARE certifiable from control-region evidence; event-level
  performance claims are NOT, and the geometry sensor detects the sim-to-real
  shift that justifies the abstention.
  **Methods note (kept honest):** the first run's control regions caught a
  ×10 MC normalization bug (full-lumi weights vs the mirror's ~10% data
  luminosity) — fixed in `qevc.data.cms_htautau` (EFFECTIVE_LUMI_PB), both
  manifests kept.

---

# Final campaign — E12–E16, E04v3, E11v2 (registered 2026-08-11)

> Directive: deepen where the evidence says the real contribution is —
> information-conditional validity + sequential guarantees + physical
> systematics + physics inference + quantum estimation uncertainty + real
> CMS/QPU evidence. No quantum-advantage hunting; the matched-kernel
> negative result is retained. Pre-campaign falsification audit:
> `docs/audits/pre_campaign_audit_2026-08-11.md`; its dispositions are
> D-019–D-027. **Campaign-wide rules:** (i) the E12 confirmatory rows are
> quarantined — no E13–E16 development touches them; (ii) all new sensor
> calibration/evaluation draws use the `auditor_dev` role (D-021), the
> claim population stays `nominal_test`; (iii) every new row draw archives
> its global indices (D-020); (iv) frozen quantities live in
> `configs/frozen/` (D-020), committed before E12 data is drawn.
> **Execution order:** freeze → E12 → E13 → E14 → E15 → E04v3 → E16 →
> E11v2 → post-campaign audit → manuscript rebuild.

## E12 — Fresh confirmatory holdout

- **Question:** Do the paper's headline results reproduce on a completely
  virgin subset of the benchmark, with every analysis choice frozen in
  advance?
- **Hypothesis:** confirmatory replication of: (a) nominal ordering
  QK ≈ matched-RBF8 < tuned trees at matched budget; (b) TES −2σ
  degradation sign for QK-SVC; (c) adverse-combination (combo3)
  degradation; (d) MMD²(quantum, rbf8) → degradation rank prediction;
  (e) auditor error control (false certification ≤ α on adversarial
  claims); (f) classifier/physics decoupling in the flagship cells.
- **Estimand(s):** identical to E01/E02/E04v2/E05/E08 definitions — no new
  estimand is introduced by this experiment.
- **Information set:** as in the source experiments (I0/I1/I2 as
  applicable); E12 grants nothing new.
- **Status of this evidence (declared):** *post-development confirmatory
  evidence*, not preregistration — every protocol choice predates the data
  draw, but the choices themselves were developed on the seed-101 world.
- **Protocol:**
  1. Freeze artifact `configs/frozen/frozen_deployment_v1.yaml` (D-020):
     hyperparameters (from E01), feature sets, feature-map config,
     AngleScaler recipe, tier-A budget (2000, matched), calibration +
     threshold procedure, claim grid (E05 v1.1), α=0.05, EB-CS, sensor
     definition (quantum-MMD² and rbf8-MMD², weight-only max floor),
     environment grid (the 41 E02 evaluations), E08 estimator (D-015),
     statistical protocol (SAP + D-017 amendments). Committed before any
     E12 row is read.
  2. Reconstruct and archive seed-101 global indices + E00 validation row
     groups; draw a fresh 300k stratified subset (seed 121) from the
     verified complement; archive its indices; verify and record
     `intersection = 0` in the E12 table itself.
  3. Fresh five-role partition (seed 121) on the new subset, persisted to
     `data/processed/splits/`; `final_eval` sealed and never read.
  4. Re-run, with frozen settings only: E01-nominal (tier A: qksvc,
     rbf_svc_8f, rbf_svc, xgboost, lightgbm; tier B xgboost), the 41-env
     landscape for those models, geometry MMD² per env (CRN draws from the
     E12 auditor_dev role), E05 auditor protocol (all claims, 20 audit
     seeds), E08 physics inference (all envs, frozen SR procedure).
  5. No quantity is tuned, selected, or thresholded on E12 data. Anything
     that fails is reported as failed.
- **Falsifier (frozen):** any of — (a) nominal per-seed-style contrast
  QK−XGB positive or QK−RBF8 outside ±3× the E02R across-seed std;
  (b) tes=0.98 ΔAUC(QK) < 0 (improvement) or combo3 mean ΔAUC(QK) < 0;
  (c) pooled Spearman ρ(MMD² → |ΔAUC|) ≤ 0 for both frozen sensors over
  the 28 shift environments; (d) empirical false certification > α + 3σ
  binomial on the adversarial claim family; (e) the two flagship
  decoupling cells (A:xgboost @ tes=0.98; diboson_scale=0.5 family) fail
  to reproduce (|ΔAUC| ≥ 0.01 or coverage ≥ 0.633).
- **Acceptance criterion:** all five falsifier arms clear. Partial failure
  does not get hidden: each arm's outcome enters the manuscript as-is.
- **Expected outputs:** `results/tables/E12_confirmatory.json` (+ index
  archives under `data/processed/used_rows/`, split file, manifest).
- **Status:** **complete (2026-08-11) — 4/5 acceptance arms pass; arm (e)
  partially triggered; all outcomes reported.** Details:
  1. Disjointness proof clean: seed-101 draw reconstructed and verified
     against the cached subset; 4,488,506 excluded rows; E12∩(prior rows)
     = 0; SHA-256 of all index archives recorded in the table.
  2. **Arm (a) PASS:** QK−XGB = −0.0389 (E02R: −0.0353 ± 0.0119);
     QK−RBF8 = −0.0080 (E02R: −0.0110 ± 0.0174).
  3. **Arm (b) PASS:** tes=0.98 ΔAUC(QK) = +0.0011; combo3 mean +0.0081.
  4. **Arm (c) PASS:** sensor ρ_S out-of-partition: quantum→own 0.39
     (p=0.04), rbf8→own 0.54 (p=0.003) — weaker than seed-101 (0.56/0.73)
     but sign-correct and significant.
  5. **Arm (d) PASS:** false certification 21/7,700 = 0.27% ≤ α; false
     refutation 4/11,980; nominal physics coverage 0.678–0.685 ≈ 0.6827.
  6. **Arm (e) PARTIAL FAIL (kept):** the tes=0.98 flagship decoupling
     reproduces exactly (|ΔAUC| = 0.0036, coverage 0.027) and E12 shows 74
     decoupled-like cells with every tes/jes environment collapsing to
     coverage 0.0 at flat AUC — **but the normalization-nuisance coverage
     damage does NOT reproduce** (diboson/ttbar/bkg coverages 0.65–0.68 ≈
     nominal). E08's norm-nuisance collapse was driven by the accidental
     ttbar/diboson content of that draw's signal regions (E12's SRs sit at
     different thresholds with b₀ 3.9k vs 37.9k) — the *mechanism* is real
     but its magnitude is SR-composition- and draw-fragile. Manuscript
     framing must demote the norm-collapse cells from "decisive" to
     "possible, composition-dependent" and lean on the robust
     selection-migration decoupling.
  7. **Level-shift diagnostic (`run_e12_diagnostic.py`,
     `results/tables/E12_diagnostic.json`):** absolute weighted AUCs sit
     0.06–0.09 below the seed-101 world for every model, but the models ×
     data cross-grid shows unweighted AUC identical everywhere
     (0.839/0.875 both worlds, both model sets) while weighted AUC follows
     the data only. Cause: signal weights are extremely heavy-tailed
     (htautau max/mean ≈ 420, ESS ratio 0.0047 → ≈46 effective signal
     events in a 41k test role), so *absolute* physics-weighted metrics
     carry ±0.05 subset-draw variance that partition-level replication
     (E02R) structurally understates. Paired contrasts, degradation signs,
     rank structure and error control — everything the paper's claims rest
     on — replicate. New quantified caution for the manuscript (and for
     the field's matched-budget benchmark practice); feeds E13's expected
     n* inflation for weighted claims (signal-side ESS ≈ 0.5%).

## E13 — Weighted anytime-valid certification

- **Question:** Can the fail-closed auditor certify *physics-weighted*
  claims with the same anytime-valid guarantees, and at what label cost
  relative to unweighted claims?
- **Hypothesis:** the one-sample reduction (D-019) preserves time-uniform
  Type-I control exactly under weighted estimands; weighted n* exceeds
  unweighted n* by a factor driven by the weight dispersion (effective
  sample size Σw²/(Σw)² and the a priori bound w_max).
- **Estimand(s):** exactly as predeclared in
  `docs/weighted_certification_spec.md` (D-019): weighted accuracy A_w,
  weighted TPR_w/TNR_w as primary claims; BA_w only via the conservative
  component bound; weighted AUC explicitly out of CS scope. Claims are the
  degradation form M_T ≥ M_S − δ on the weighted scale, δ grid as E05
  v1.1 (including adversarially false claims).
- **Information set:** I2(n) — uniform-with-replacement label draws
  revealing (y_i, w_i) at labeling time; per-event weights are *never*
  available pre-labeling (they are label-equivalent in this benchmark —
  spec §2 of D-019). Sensor draws (if any) from `auditor_dev` (D-021).
- **Protocol:** implement `weighted` module in `qevc.statistics` (Z-stream
  transform + ratio-CS secondary); Monte Carlo validation battery per
  D-019 §5 (time-uniform coverage, false cert/refutation at margins,
  adversarial optional stopping, BA_w conservatism); then benchmark study
  on the seed-101 archives (E02 scores + weights): weighted vs unweighted
  verdicts and n* on identical draws over the 41 envs × 4 audit models ×
  δ grid; report weight-only environments separately — under nominal
  weights they now carry *different weighted estimands* only when the true
  weights are known, which I2 alone does not grant (the E14 bridge,
  measured here as the nominal-weight limitation).
- **Falsifier (frozen):** any Monte Carlo configuration with time-uniform
  miscoverage or false certification > α beyond 3σ MC slack falsifies the
  implementation and blocks downstream use until fixed and re-registered.
  If weighted n* > 20k for every claim with |margin| ≥ 0.04 on benchmark
  populations, weighted certification is reported as impractical at
  physics weights (negative result, published).
- **Acceptance criterion:** validation battery passes; weighted/unweighted
  comparison table complete with n* ratios and verdict-flip counts.
- **Expected outputs:** `results/tables/E13_weighted_cs.json`; new module
  + tests under `tests/`; SAP amendment note.
- **Status:** **complete (2026-08-11) — falsifier NOT triggered;
  implementation valid.** Results:
  1. **Validation battery:** time-uniform miscoverage within α + 3σ slack
     in every profile × level cell; worst MC false-certification cell 1.5%
     (slack threshold 8.3% at n_rep 400); adversarial optional stopping
     breaks the naive Wald rule (27.8% false certification) while the CS
     holds at 0.0% — the guarantee, demonstrated.
  2. **Benchmark (identical draws, 41 envs × 4 models × claim grid):**
     weighted false certification 2/8,900 = 0.02% ≤ α; weighted false
     refutation 0; class-conditional (TPR_w/TNR_w) false certification
     0/4,700.
  3. **Label cost of physics-weighted certification:** n*_w / n*_unw
     median 1.67 (IQR 1.11–3.01, 6,575 resolved pairs); verdict-flip
     table: 543 SUPPORTED→UNRESOLVED (fail-closed hardens under the
     physical estimand), 218 UNRESOLVED→SUPPORTED, 272
     UNRESOLVED→REFUTED, and 1 SUPPORTED→REFUTED — the weighted and
     unweighted estimands genuinely disagree about deployment health,
     sharpening the "metric named in the claim" finding.
  4. Per-process weights are NOT constant (htautau spans ×1000; matches
     the E12 diagnostic): the weighted machinery is necessary, not
     decorative. w_max = 7.264 × 2.05 = 14.89 (predeclared rule).
  5. **BA_w component bound is severely conservative at n_max = 3,000**
     (all BA claims UNRESOLVED, true and false alike): reported as the
     honest cost of the α/4-per-component union bound; BA claims should be
     stated per component (the physics quantities) — manuscript
     limitation.

## E14 — Information set I3

- **Question:** Which claims that are unidentifiable from
  feature-distribution evidence (I0/I1) or labels-with-nominal-weights
  (I2) become certifiable when the information set contains the
  experimentally available aggregate physics — nuisance estimates, rates,
  yields, control regions?
- **Hypothesis:** (a) weight-only (normalization) nuisances are *formally*
  unidentifiable from any I1 statistic — P_θ(X) = P_0(X) exactly, so no
  label-free test has power beyond α (stated and proved as a proposition);
  (b) they are also invisible to I2 with nominal weights (the labeled
  stream's distribution is θ-invariant); (c) control-region rate evidence
  (I3) identifies the normalization scales and turns rate claims and
  true-weighted-metric claims certifiable, with anytime-valid error
  control; (d) the physics-validity claim (interval coverage) requires I3
  *plus* an inference procedure that consumes it (E15).
- **Estimand(s):** (i) normalization scale s_p per process family
  (ttbar_scale, diboson_scale, bkg_scale) — claims of the form
  |s_p − 1| ≤ x; (ii) true-weighted accuracy A_w^{(θ)} under the
  environment's actual weights (D-019 §4: reweighted stream with
  worst-case-over-θ̂-confidence-set bounding, fail-closed); (iii) the
  claim × information-set resolvability table over
  {classifier performance, normalization/rate, physics-level validity} ×
  {I0, I1, I2(n), I3}.
- **Information set:** I3 = I2(n) ∪ {control-region counts and yields from
  the *unlabeled* target environment, nuisance estimates θ̂ derived from
  them, and their declared uncertainties}. CRs are predeclared, label-free
  score/feature regions (defined on `auditor_dev`-frozen boundaries):
  background-dominated low-score region per model + per-process-enriched
  regions where the benchmark's features support them; CR definitions are
  frozen before any E14 evaluation run.
- **Protocol:** (1) write the formal proposition + proof sketch
  (manuscript-ready); (2) implement CR yield extraction and normalization
  estimation with Poisson/Gaussian uncertainty; anytime-valid e-process or
  conservative fixed-n bounds for rate claims (method predeclared in the
  run config before execution); (3) evaluate over the 12 weight-only
  environments + combo3 family + nominal: verdict tables under I1, I2,
  I3; empirical false-certification against simulation truth; (4) the
  A_w^{(θ)} chain: θ̂ from CRs → reweighted worst-case stream → verdict;
  compare against the I2-nominal-weight verdict to exhibit the
  identifiability boundary experimentally.
- **Falsifier (frozen):** if I3 verdicts on genuinely false rate claims
  exceed α false certification (beyond binomial slack), the I3 machinery
  is invalid. If CR-based θ̂ cannot identify the normalization scales the
  benchmark actually varies (coverage of the θ̂ intervals < nominal on
  simulation truth), hypothesis (c) fails and is reported as a negative
  result — the table then documents *unresolvable-even-at-I3* cells.
- **Acceptance criterion:** proposition stated; table complete with
  measured error rates per cell; every I3-certified claim carries an
  explicit statistical guarantee (nothing heuristic is called a
  certificate).
- **Expected outputs:** `results/tables/E14_i3.json` + the claim ×
  information-set table (paper table); formal statement in
  `docs/weighted_certification_spec.md` addendum or manuscript directly.
- **Status:** specified (2026-08-11).

## E15 — Realistic physics inference

- **Question:** Does the classifier-vs-physics decoupling survive a
  physically defensible inference chain — and exactly which information or
  procedure restores validity where it does not?
- **Hypothesis:** H5 refined: (a) the deployment-blind counting estimator
  (E08, kept as baseline) overstates the practical damage; (b) a
  profile-likelihood fit that models the *right* nuisances restores
  coverage — quantifying the information that protects inference; (c) a
  profiled fit that omits the actually-shifted nuisance family (realistic
  misspecification) still loses coverage while classifier metrics stay
  healthy — the decoupling claim in its reviewer-proof form. (b) and (c)
  are both acceptable outcomes wherever the data lands; nothing is forced.
- **Estimand(s):** signal strength μ; bias of μ̂, interval width, empirical
  68.27% coverage, nuisance pulls (θ̂ − θ_true)/σ_θ; all per (environment,
  model, inference level).
- **Information set:** the inference levels *are* information sets over
  nuisances: L1 = frozen nominal beliefs (D-015 counting, unchanged
  baseline); L2 = binned profile likelihood over the frozen classifier
  score, Poisson per bin, L(μ, θ) = Π_b Pois(n_b | μ·s_b(θ) + b_b(θ)) ·
  Π_j N(θ̃_j; θ_j, σ_j), with template morphing in θ from the official
  systematics code at predeclared anchor points, profiling all six
  benchmark nuisances; L3 = same machinery with a predeclared *incomplete*
  nuisance model (leave-one-family-out of the profile, e.g. fit models
  TES/JES/norms but truth shifts soft_met) — "systematics-aware but
  misspecified", the realistic failure mode.
- **Protocol:** score-binned templates (bins frozen from source_val;
  b ≥ floor per bin); anchors at ±1σ, ±2σ per nuisance from the official
  systematics pipeline; piecewise-linear/quadratic vertical morphing;
  profile via numerical minimization; intervals from the profile
  likelihood ratio (Wilks; validated at nominal against pseudo-experiment
  coverage before use — internal calibration gate); 2000
  pseudo-experiments per (env, model, μ_true ∈ {0.5, 1, 1.5, 2, 3});
  models: A:qksvc, A:rbf_svc_8f, A:xgboost, B:xgboost; environments: the
  E08 grid (all 41), attention on the E02R-gated decoupled cells.
- **Falsifier (frozen):** if L2 fails its *nominal-environment* coverage
  calibration gate (coverage outside 0.6827 ± 0.02 with 2000 PEs at θ=0),
  the implementation is invalid — fix before any shifted-environment
  claim. Hypotheses (b)/(c) have no falsifier because both directions are
  reportable findings; what is falsifiable is the decoupling claim itself:
  if under L2-complete *and* L3-misspecified the previously decoupled
  cells all regain coverage, H5 in its strong form is retired and the
  manuscript says so.
- **Acceptance criterion:** calibration gate passed; bias/width/coverage/
  pull tables for L1/L2/L3 across the grid; explicit
  "what-restores-validity" summary quantified (coverage recovered per
  nuisance family when modeled vs omitted).
- **Expected outputs:** `results/tables/E15_inference.json`, Fig. 7
  replacement data; `qevc.inference` module + tests.
- **Status:** specified (2026-08-11).

## E04v3 — Out-of-grid generalization of the geometry sensor

- **Question:** Does the frozen label-free sensor (MMD² of the quantum and
  matched-rbf8 kernels) predict degradation on *continuous, out-of-grid*
  nuisance configurations and across nuisance families it never saw — or
  does it merely interpolate the development grid?
- **Hypothesis:** H2 in generalization form: rank prediction transfers to
  off-grid single-nuisance values and to prior-sampled multi-nuisance
  configurations; leave-one-family-out calibration predicts the held-out
  family with ρ > 0.
- **Estimand:** Spearman ρ (and sign-consistency) between sensor value and
  frozen-model |ΔAUC| over (a) 36 off-grid single-nuisance environments
  (six per family where physical: TES/JES 6 new values each inside the
  official clip range, soft_met 4 new values × 2 seeds, norm families for
  floor/blindness checks only), and (b) 24 multi-nuisance draws from the
  official priors (seeded, predeclared in the config before execution) —
  60 new environments total, none coinciding with any E02 grid point.
- **Information set:** I1 strictly — sensor sees unlabeled target draws
  only (from `auditor_dev`, D-021); degradation targets are computed once,
  after sensor values are archived, from the frozen seed-101 deployment
  (single-partition targets declared; E02R told us their precision, and
  the E12 deployment provides a cross-partition secondary check).
- **Protocol:** (1) commit the 60-environment config; (2) compute sensor
  values (CRN draws, floor re-estimated on auditor_dev with bootstrap
  uncertainty per F4); (3) only then score frozen models and compute
  |ΔAUC|; (4) leave-one-nuisance-family-out: any calibration map
  (monotone/isotonic) fit on the other families, evaluated on the held-out
  family — repeated for TES, JES, soft_met, combos; (5) out-of-grid
  pooled ρ with family-blocked bootstrap CIs.
- **Falsifier (frozen):** pooled out-of-grid ρ ≤ 0 for both frozen
  sensors, or any leave-one-family-out fold with ρ sign-unstable across
  the CRN draws for both sensors — reported as "the sensor interpolates,
  it does not generalize", which retires the sensor claim from the
  manuscript (the information-set thesis survives without it).
- **Acceptance criterion:** table of per-fold and pooled ρ with CIs;
  floor distribution with uncertainty; explicit no-labels attestation in
  the run script (sensor archived before targets exist).
- **Expected outputs:** `results/tables/E04v3_out_of_grid.json`, Fig. 4
  upgrade data.
- **Status:** **complete (2026-08-11) — falsifier NOT triggered; the
  sensor generalizes out-of-grid in rank terms, with world- and
  family-dependent detail reported honestly.** Results (48 out-of-grid
  shift environments per world; sensor archived before targets, SHA-256 in
  table):
  1. **Pooled out-of-grid ρ_S, primary (seed-101) world:** quantum→own
     0.654 (p < 10⁻⁴), rbf8→own 0.559 (p = 4·10⁻⁵); transfers to XGBoost
     0.302 / 0.220. **Secondary (E12) world:** quantum→own 0.389
     (p = 0.006), rbf8→own 0.219 (n.s.), transfers 0.567 / 0.615 —
     positive everywhere, but which target a sensor predicts best is
     world-dependent (E12's tiny tes/jes target magnitudes ≈ 0.0005 sit at
     partition noise).
  2. **Per-family:** TES generalizes best (ρ up to 0.96); soft_met strong
     (0.67–0.72); official-prior multi-nuisance draws 0.50–0.66 in the
     primary world; JES weak/unstable (its |ΔAUC| targets are at the noise
     floor) — matches the E04-era caveat.
  3. **Magnitude calibration (LOFO isotonic):** MAE 0.002–0.009 on targets
     whose means are 0.0005–0.012 — magnitude prediction is rough;
     *rank* prediction is the defensible claim, stated as such.
  4. **CRN identity finding (registered amendment + floor addendum):**
     under common random numbers the weight-only environments produce
     MMD² *identical* to nominal — the blindness proposition in its exact
     computational form (stronger than "below noise floor") — but the
     frozen max-over-weight-only floor rule degenerates (it equals the
     nominal point). The operative veto floor is re-based on 20
     independent auditor_dev nominal draws (`run_e04_v3_floor2.py`):
     null std ≈ 7·10⁻⁵ (quantum), floor_max alarming 4–8/48 out-of-grid
     envs — only soft_met-family and strong prior draws, consistently
     across worlds and kernels; TES/JES at official ±2σ stay below alarm
     (coherent: their degradations are also below material size).

## E16 — Quantum estimation uncertainty → certification

- **Question:** When does quantum-kernel estimation uncertainty —
  finite shots and hardware noise — change a scientific validity verdict?
- **Hypothesis:** H6 sharpened: verdict changes concentrate at claim
  margins comparable to the estimation-induced metric perturbation;
  far-margin certificates are stable at practical budgets; near-boundary
  claims flip or abstain, and abstention (not false certification) is the
  dominant failure mode — fail-closed under quantum noise.
- **Estimand(s):** per (kernel regime, environment, claim): verdict in
  {SUPPORTED, REFUTED, UNRESOLVED}; flip rate vs C_ideal; abstention
  inflation; empirical false-certification against simulation truth;
  n* inflation; supporting diagnostics: kernel Frobenius error, spectral
  distortion (eff-rank), PSD violation, ΔAUC vs exact, M_S shift, margin
  shift. Claim strata predeclared by ideal-kernel margin: far (|m| ≥
  0.04), moderate (0.01–0.04), near (< 0.01).
- **Information set:** I2(n) as E05/E13 (both unweighted and weighted
  claim families — E16 consumes E13's machinery); the kernel regime is
  part of the *deployment*, not the information set.
- **Protocol:** (1) D-022 fix (independent per-call shot noise) with
  regression test; (2) simulation arm: shots ∈ {128, 256, 512, 1024,
  2048, 4096} × 5 kernel seeds × environments {nominal, tes=0.98,
  tes=1.02, soft_met=5.0/seed11, combo3/seed11} × full E05 claim grid;
  each noisy deployment owns its pipeline (refit, recalibrate, re-freeze
  threshold — as E09); C_shots vs C_ideal tables by margin stratum;
  (3) hardware arm (Open-plan budget, D-027): scope decided by measured
  quota — priority order (a) full-pipeline micro-demonstration: fresh
  QPU train Gram (n ≈ 48–64 events) + cross-Gram to a held-out test set,
  auditor run end-to-end on 100%-hardware kernels (C_hw), raw counts
  archived; (b) if budget allows, a dynamical-decoupling on/off split at
  identical shots for a mitigation-recoverable-fraction estimate;
  (c) drift/session replication only if (a)+(b) fit comfortably. Archived
  E10 v1 Gram is reused for cross-checks, never silently mixed with new
  sessions. All jobs, calibration snapshots, transpiled depths, and raw
  counts archived; failed jobs reported.
- **Falsifier (frozen):** if verdict flips are *not* margin-concentrated
  (far-margin flip rate ≥ moderate-margin flip rate at any budget ≥ 1024
  shots), the "estimation noise only bites near boundaries" claim is
  false and the manuscript's Quantum Realism section is rewritten
  accordingly. If empirical false certification under noisy kernels
  exceeds α beyond binomial slack, the fail-closed claim under quantum
  uncertainty is falsified — a central negative result if it occurs.
- **Acceptance criterion:** complete C_ideal/C_shots (and C_hw at
  achievable scale) comparison tables with per-stratum flip/abstention/
  false-cert rates and n* inflation; hardware provenance complete.
- **Expected outputs:** `results/tables/E16_quantum_uncertainty.json`;
  `results/raw/E16_hw/*` if the hardware arm runs; Fig. 8 upgrade data.
- **Status:** specified (2026-08-11).

## E11v2 — Strengthened CMS real-data demonstration

- **Question:** Does the fail-closed ledger hold, with tighter aggregate
  evidence, when the real-data side uses the full public Run2012B+C
  samples instead of the 10% development mirror?
- **Hypothesis:** H4 in deployment conditions, unchanged; CR-based claims
  gain precision (narrower intervals), the sim-to-real sensor alarm
  persists, and event-level accuracy remains UNRESOLVED by construction.
- **Estimand(s):** the E11 ledger claims C1–C4 with identical definitions;
  CR data/MC ratios with their intervals; sensor MMD² vs re-estimated
  floor.
- **Information set:** I1 + control-region aggregates (unchanged); MC
  hyperparameters remain E01-frozen; no target tuning.
- **Protocol:** download full opendata.cern.ch files for the two real-data
  samples (Run2012B/C TauPlusX, ~27 GB; sequential download → skim →
  delete raw per file under the disk budget); MC stays on the verified
  mirror files (statistically valid: MC weights normalize by ingested
  N_generated; D-026 sets DATA_LUMI_FRACTION → 1.0 with the full-data
  path); re-run the E11 pipeline frozen; register `data/README.md`
  Level II provenance (audit gap); ledger + diagnostics regenerated; the
  mirror-based E11 v1 results are retained for comparison.
- **Falsifier (frozen):** unchanged from E11 — certifying C1 would be a
  design failure. Additionally: if the full-data CR ratios move outside
  the mirror-based intervals by more than their combined uncertainties,
  the mirror-based conclusions were sample-fragile — reported either way.
- **Acceptance criterion:** ledger reproduced on full data; explicit
  mirror-vs-full comparison row per claim.
- **Expected outputs:** `results/tables/E11v2_cms_full.json` + manifest;
  updated `data/README.md`.
- **Status:** specified (2026-08-11).
