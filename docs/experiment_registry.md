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
- **Outputs:** `results/tables/E04_geom_failure.*`, Fig. 4 data.
- **Status:** planned.

## E05 — Conditional auditor

- **Question:** Which claims are resolvable under I0/I1/I2(n)/I3, with what error
  rates?
- **Hypothesis:** H3, H4.
- **Metric:** auditor-level metrics SAP §1.3; empirical false-certification vs α.
- **Falsifier:** empirical false certification > α (beyond binomial fluctuation)
  invalidates the implementation; auditor that never abstains under I0/I1
  invalidates fail-closed design.
- **Outputs:** `results/tables/E05_auditor.*`.
- **Status:** planned.

## E06 — Partial-label certification landscape

- **Question:** What is `n*(θ, C)` across severity × claims?
- **Hypothesis:** H3.
- **Metric:** n* distributions over seeds; certification landscape regions.
- **Falsifier:** n* ≳ full labeling everywhere (certification adds nothing).
- **Outputs:** `results/tables/E06_nstar.*`, Fig. 5 data.
- **Status:** planned.

## E07 — Active auditing

- **Question:** Do acquisition strategies reduce n* below random sampling while
  preserving validity?
- **Hypothesis:** exploratory (spec §15).
- **Metric:** n* ratio active/random with CIs; empirical Type-I under active
  acquisition (must stay ≤ α).
- **Falsifier:** no strategy beats random → reported as a primary negative result.
- **Outputs:** `results/tables/E07_active.*`, Fig. 6 data.
- **Status:** planned.

## E08 — Physics-level inference

- **Question:** Does classifier degradation propagate to μ bias / interval
  coverage, and can AUC and coverage decouple?
- **Hypothesis:** H5.
- **Metric:** SAP §1.2 across environments; decoupling search per SAP §6.
- **Falsifier:** no decoupling found on the full grid (negative result for H5).
- **Outputs:** `results/tables/E08_physics.*`, Fig. 7 data.
- **Status:** planned.

## E09 — Finite-shot kernels

- **Question:** How does shot noise interact with systematics and certificate
  stability?
- **Hypothesis:** H6.
- **Environments:** shots ∈ {128…4096} × selected θ from E02.
- **Metric:** kernel estimation error, spectral distortion, PSD violations,
  classifier degradation, certificate flip rate vs K_exact.
- **Falsifier:** no shots×θ interaction and zero certificate flips (negative H6).
- **Outputs:** `results/tables/E09_shots.*`, Fig. 8 data.
- **Status:** planned.

## E10 — Hardware validation

- **Question:** Do representative conclusions survive on a real QPU subset
  (~10² events)?
- **Hypothesis:** complementary evidence for H6 (never statistical backbone).
- **Metric:** K_ideal vs K_shots vs K_hw comparison suite; full provenance per
  spec §19.
- **Falsifier:** n/a — all outcomes (including failed runs) are reported.
- **Outputs:** `results/raw/E10_hw/*` + provenance manifests.
- **Status:** planned (last; depends on QPU access).

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
