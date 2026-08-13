# Decision Log

Every material design decision is recorded here before or at the moment it takes
effect. Format: ID, date, decision, alternatives considered, rationale, status.

---

## D-001 — Package layout deviates cosmetically from spec §26

- **Date:** 2026-08-10
- **Decision:** Source code lives in `src/qevc/<module>/` (an installable package,
  `qevc` = Quantum Event Validity Certification) rather than bare `src/<module>/`
  directories as drawn in spec §26.
- **Alternatives:** bare `src/data`, `src/models`… as literal spec layout.
- **Rationale:** bare top-level modules named `data`, `statistics`, `inference`
  shadow stdlib/common package names and are not pip-installable; the spec's module
  set is preserved 1:1 under the package root. No scientific definition altered.
- **Status:** adopted.

## D-002 — Quantum stack: Qiskit

- **Date:** 2026-08-10
- **Decision:** Qiskit (+ qiskit-machine-learning FidelityQuantumKernel /
  FidelityStatevectorKernel, qiskit-aer for finite-shot simulation,
  qiskit-ibm-runtime for the E10 hardware phase).
- **Alternatives:** PennyLane (+ lightning simulators; hardware via plugins).
- **Rationale:** direct path from identical circuit definitions to statevector
  (exact), Aer shot-based (finite-shot), and IBM QPU execution — exactly the
  K_exact / K_shots / K_hw comparison required by spec §18–19 with one codebase.
  Kernel entries are also computable from raw counts, so no framework lock-in for
  the estimator. PennyLane remains a fallback if Qiskit's Python 3.13 support on
  Windows proves problematic (see D-003 risk).
- **Status:** adopted.

## D-003 — Local environment: Python 3.13 venv on Windows; heavy runs CPU-parallel

- **Date:** 2026-08-10
- **Decision:** Develop against the machine's Python 3.13 in a project venv
  (`.venv`). Kernel-matrix computation parallelized over the 20 CPU cores.
  No GPU assumed. If any dependency lacks 3.13 wheels on Windows, pin the affected
  component in a container or downgrade the venv to 3.12 and record it here.
- **Status:** adopted; risk logged.

## D-004 — License MIT; authorship

- **Date:** 2026-08-10
- **Decision:** Code under MIT, author Roberto Fernández Barrios. Dataset licenses
  tracked separately per dataset in `docs/dataset_audit.md` (CERN Open Data is
  CC0; FAIR Universe license recorded on audit).
- **Status:** adopted.

## D-005 — Statistical backbone of the auditor: anytime-valid confidence sequences

- **Date:** 2026-08-10
- **Decision:** Claim resolution in the conditional auditor (spec §13–14) will be
  built on time-uniform / anytime-valid confidence sequences for bounded means
  (betting-style CS, Waudby-Smith–Ramdas family) rather than fixed-n Hoeffding or
  naive repeated binomial tests.
- **Alternatives:** fixed-n Clopper–Pearson per budget point (invalid under
  optional stopping across the n-grid); Hoeffding bounds (valid but loose);
  post-hoc bootstrap (no finite-sample guarantee).
- **Rationale:** n* — the minimum label budget at which a claim resolves — is by
  construction a stopping time. Only anytime-valid inference keeps Type-I error
  control when labels are inspected sequentially, and it composes correctly with
  the active-acquisition arm (via importance-weighted supermartingales). This is
  also the technical answer to Gate 4: the auditor issues statistically valid
  claim resolutions with explicit error control, not an OOD score.
- **Status:** adopted, pending detail in `docs/statistical_analysis_plan.md`.

## D-006 — Fail-closed semantics fixed up front

- **Date:** 2026-08-10
- **Decision:** SUPPORTED requires the (1−α) lower confidence bound of the claim
  metric to clear the claim threshold; REFUTED requires the upper bound to fall
  below it; everything else is UNRESOLVED. Heuristic sensors (geometry, I0/I1
  scores) can *only* move a claim toward UNRESOLVED or trigger label acquisition —
  they can never move a claim to SUPPORTED. Guarantees only ever come from labeled
  target evidence (I2/I3).
- **Rationale:** spec §4-H4, §13, §34: heuristics must never be laundered into
  certificates.
- **Status:** adopted (frozen; changing this requires a new decision entry).

## D-007 — Finite-shot kernels sampled from the exact binomial law

- **Date:** 2026-08-10
- **Decision:** `kernel_shots` draws each Gram entry from
  Binomial(shots, K_exact)/shots instead of executing compute–uncompute circuits
  on a shot-based simulator.
- **Rationale:** for an ideal (noiseless) device, the all-zeros outcome of the
  compute–uncompute protocol is exactly Bernoulli(K_exact) per shot, so the two
  procedures are distributionally identical; direct sampling is orders of
  magnitude cheaper, enabling the full shots × θ grid of E09. Device *noise* is
  deliberately excluded here — that is E10's job with real hardware, keeping
  H6's decomposition (shot noise vs hardware noise) clean.
- **Consequence:** any statement about "hardware noise" must come from E10 runs,
  never from E09.
- **Status:** adopted.

## D-008 — Dataset selections (Gate 1 / Gate 6)

- **Date:** 2026-08-10
- **Decision:** Level I = FAIR Universe HiggsML Uncertainty (Zenodo
  10.5281/zenodo.15131565, systematics code pinned at commit `31816a0d`).
  Level II = CMS Open Data H→ττ 2012 μτ_h (records 12350–12359, dev on the
  root.cern 10% mirror), with Z→μμ (12365/12366 + 12353) as companion control
  channel. Fallbacks: ATLAS HiggsML 2014 (Level I), 2015 POET series (Level II).
- **Rationale:** full audit in `docs/dataset_audit.md`; decisive factor beyond
  the spec §7 criteria is cross-level coherence — both levels are the same
  physics process (H→ττ), removing the "different process" objection against
  the sim-to-real demonstration.
- **Known upstream defect handled:** norm-nuisance no-op bug in official
  `systematics()`; weight scalings applied by `qevc.systematics` directly, with
  an E00 regression test pinning semantics (audit §1.3).
- **Status:** adopted.

## D-009 — Claims discipline for novelty statements

- **Date:** 2026-08-10
- **Decision:** the paper claims exactly the four differentiators listed in
  `docs/novelty_matrix.md` ("Differentiators to claim") and no others; targeted
  literature re-searches are re-run before submission and the matrix updated
  (watch items listed there).
- **Status:** adopted.

## D-010 — Subset weights renormalized per process

- **Date:** 2026-08-10
- **Decision:** when a subset of the full parquet is used, event weights are
  rescaled per process: `w ← w · (Σw_process,full / Σw_process,subset)`, with
  the full-file sums measured by the loader (cached).
- **Alternatives:** official loader's global rescale (preserves total Σw only);
  no rescale (subset yields unphysical).
- **Rationale:** per-process rescaling preserves each σ×L exactly, so weighted
  metrics and pseudo-experiment yields on subsets estimate the full-dataset
  quantities without distorting the background composition. The official
  global rescale distorts process fractions under stratified sampling.
- **Status:** adopted.

## D-011 — Quantum feature set v1 (8 features, predeclared)

- **Date:** 2026-08-10
- **Decision:** QK-SVC v1 encodes 8 features (one per qubit):
  `DER_mass_transverse_met_lep, DER_mass_vis, DER_pt_ratio_lep_had,
  DER_met_phi_centrality, DER_deltar_had_lep, DER_pt_h, DER_sum_pt, PRI_met`.
- **Rationale:** expert HiggsML pathway of spec §8 — the DER variables with
  highest documented discriminative power in HiggsML-style analyses, defined
  for every event (no jet-dependent sentinel features in v1, avoiding sentinel
  angles dominating the kernel). Fixed from source knowledge only; no target
  information involved. Alternative pathways (statistical selection, PCA,
  jet-inclusive sets) are the registered feature-selection ablation, not v1.
- **Status:** adopted for E01; revisit only via a new decision entry.

## D-012 — Training weights vs evaluation weights

- **Date:** 2026-08-10
- **Decision:** models train with **class-balanced physical weights**
  (`w · 0.5 / Σw_class`, preserving within-class importance structure while
  equalizing class mass), renormalized to mean 1 over the training set —
  boosting split criteria and SVM regularization are not weight-scale
  invariant, so O(1)-sum weights silently cripple them. All evaluation uses
  raw physical weights (SAP §1.1).
  MLP (no per-sample weight support in sklearn) trains on weight-proportional
  resampled data with the same balanced weights, seeded.
- **Alternatives:** raw physical weights in training (weighted signal fraction
  ≈0.1% → degenerate reject-all classifiers); unweighted training (discards
  within-class importance).
- **Rationale:** training objective is an analyst choice; what is *predeclared*
  is that evaluation is always physics-weighted and the training choice is
  identical across quantum and classical models (fair-comparison rule §9).
- **Status:** adopted.

## D-013 — Partitions are defined on RAW pre-selection rows

- **Date:** 2026-08-10
- **Decision:** the five-role partition (spec §10) is defined on raw
  pre-selection rows of the subset, carried through every environment via a
  `row_id` column that survives the official systematics pipeline. For any
  environment θ (nominal included), the role dataset is
  `apply_environment(raw[role_rows], θ)` — selection migration happens *inside*
  the role.
- **Alternatives:** partitioning the nominal post-selection dataset D₀ (E01
  v1 did this).
- **Rationale:** under upward shifts, events migrate INTO the selection; a
  D₀-based partition has no role assignment for them, so shifted test sets
  would either drop them (unphysical) or leak unassigned rows. Raw-row
  partitioning gives every environment a consistent, closed test population.
  E01 was re-run under this scheme (v2 supersedes v1; both manifests kept).
- **Status:** adopted.

## D-014 — E05 v1 audit estimand: unweighted event correctness

- **Date:** 2026-08-10
- **Decision:** the conditional auditor's v1 estimand is **per-event
  correctness at the frozen threshold under uniform sampling of the target
  population** (bounded {0,1} draws → the EB confidence sequence applies
  exactly; label draws are with replacement so each draw is IID
  Bernoulli(M_T)). Claims are the degradation form
  `M_T ≥ M_S − δ`, δ ∈ {0.02, 0.05, 0.10} predeclared, α = 0.05.
  A single CS per stream resolves all three δ-claims **simultaneously**
  (time-uniform coverage of M_T implies simultaneous validity over any set of
  thresholds derived from the same CS).
- **Deferred (registered extensions):** physics-weighted metrics need
  weighted/importance CS machinery (SAP §3.1) — E05 v2; information set I3
  (nuisance estimates) — E05 v2.
- **Rationale:** starts the auditor on ground where the guarantee is exact
  rather than approximate; weighted estimands change the martingale, not the
  framework.
- **Status:** adopted.

## D-015 — E08 v1 physics estimator: single-signal-region counting analysis

- **Date:** 2026-08-10
- **Decision:** E08 v1 measures μ with the simplest deployable estimator:
  a per-model signal region (calibrated score ≥ t_SR, t_SR chosen on
  source_val to maximize s/√b with a floor b ≥ 50 rescaled events), yields
  rescaled from the test role to 10 fb⁻¹ with per-process factors computed at
  nominal, pseudo-experiments N ~ Poisson(μ·s(θ) + b(θ)), and the
  deployment-blind estimator μ̂ = (N − b₀)/s₀, σ̂ = √N/s₀, 68.27% Gaussian
  interval — the deployment believes the NOMINAL expectations (s₀, b₀).
- **Known limitations (registered, not hidden):** one counting bin discards
  shape information (real analyses profile nuisances over score bins);
  s₀/b₀ derive from the same simulation subset as the θ-truth yields
  (independent-MC split deferred to v2); Gaussian interval adequate for the
  SR count scale here (checked in-run).
- **Rationale:** the H5 question — can classifier metrics survive while
  inference validity fails — needs the *cleanest possible* propagation chain
  first; refinements change power, not the logic of the demonstration.
- **Status:** adopted for E08 v1.

## D-016 — Clean-tree regeneration campaign; manifest semantics fixed

- **Date:** 2026-08-10 (Phase 10 review, finding 1 — BLOCKER)
- **Problem:** all prior manifests recorded `git_dirty: true` (development
  runs), so the recorded commit did not identify the code that produced any
  result table.
- **Decision:** (a) `git_is_dirty` now measures the CODE state only
  (`results/` excluded — a run writing its own outputs does not make the
  code ambiguous); (b) manifest filenames include the run start time, so
  clean re-runs of identical configs get their own immutable manifest;
  (c) all simulation experiments (E00–E09, E02R, E04v2, E11) are re-executed
  in one sequential campaign from a single clean commit; superseded dirty
  manifests are retained. E10's QPU job cannot be re-executed; its
  provenance is captured independently by the archived job id, raw counts,
  and submission metadata, and this is disclosed.
- **Status:** adopted; campaign scripted in `scripts/regenerate_all.ps1`.

## D-017 — SAP deviations, logged (Phase 10 findings 5, 11, 15)

- **Date:** 2026-08-10
- **Deviations from the predeclared SAP, now recorded:**
  1. Bootstrap resamples: 10³ (E01) / 5×10² (E02) instead of SAP §5's 10⁴ —
     compute trade-off; descriptive CIs only, effect sizes dwarf CI-of-CI
     precision. Kept as-is; SAP note added.
  2. Multi-nuisance design: 4 physics-motivated corners instead of a Latin
     hypercube (SAP §4) — LHC design deferred to a follow-up pass.
  3. Replication depth: 5 seeds for all replicated pipelines (SAP §4 said 10
     for cheap classical) — E02R covers classical and quantum identically.
  4. H1 primary analysis: across-seed sign-consistency and mean ± std
     replaced the per-environment paired bootstrap of Δ_θ (stronger against
     partition variance, which proved dominant); recorded as an amendment.
  5. ∂μ̂/∂θ nuisance-sensitivity (SAP §1.2) not implemented in E08 v1;
     deferred to E08 v2 (multi-bin/profiled).
  6. Tuning budgets are *comparable*, not identical (MLP: 5 configs vs 10,
     predeclared in E01.yaml) — manuscript language corrected accordingly.
- **Status:** adopted; manuscript §5 rewritten to match reality.

## D-018 — Global holdout after E02R (Phase 10 finding 6)

- **Date:** 2026-08-10
- **Problem:** E02R's fresh per-seed partitions overlap the primary
  partition's `final_eval` rows, so no globally-untouched holdout survived
  replication.
- **Decision:** the seed-101 `final_eval` raw-row set is declared the global
  holdout going forward: no future run (including E02R extensions) may
  train, calibrate, tune, or evaluate on those rows without a new decision
  entry. Manuscript and registry language corrected to: "each partition
  seals its own final_eval; single-partition results never touched the
  primary final_eval; E02R's replication partitions overlap it, so no
  globally-untouched holdout remains for the results reported here."
  `auditor_dev` (unused to date) is likewise reserved for future
  auditor-development choices, documented as such (finding 12).
- **Status:** adopted.

## D-019 — Weighted certification estimands and guarantees (E13)

- **Date:** 2026-08-11
- **Decision:** the weighted auditor implements exactly the estimands and
  machinery predeclared in `docs/weighted_certification_spec.md`: weighted
  accuracy A_w and weighted class-conditional rates TPR_w/TNR_w as primary
  claims via the one-sample reduction Z_i(τ) = (u_i(c_i − τ) + τ·w_max)/w_max
  on the existing empirical-Bernstein CS (exact, time-uniform); BA_w only as
  the conservative α/2-per-component bound; weighted AUC stays on fixed-n
  checkpoints (never CS). Per-event weights are revealed only at labeling
  time (they are process- and label-informative — granting them on
  unlabeled events would add label-adjacent information to I1). Conditional
  on each frozen finite population, the scalar bound
  w_max = (max per-event D-010-rescaled weight at nominal) × 2.05 is fixed
  before the random audit order. The multiplier covers the largest compound
  official scale, diboson × background = 2.0 × 1.01 = 2.02.
- **Alternatives considered:** weight-proportional label sampling (exact
  Bernoulli reduction, rejected: requires pre-labeling weights = label
  leakage); direct ratio-CS as primary (rejected as primary: strictly more
  conservative per claim; kept as the simultaneous-in-τ secondary);
  betting-CS re-derivation (unnecessary: the reduction reuses the tested
  EB-CS unchanged).
- **Status:** adopted; falsifiers frozen in the E13 registry entry. Wording
  and multiplier corrected by the final mathematical audit on 2026-08-12;
  no experiment consumed the earlier 2.0 value.

## D-020 — Campaign freeze artifact and row-index archival (E12)

- **Date:** 2026-08-11
- **Decision:** (a) all frozen analysis quantities (E01 hyperparameters,
  feature sets, feature-map config, scaler recipe, calibration/threshold
  procedure, claim grid, sensor definition, environment grid, E08
  estimator, statistical protocol references) are snapshotted into
  `configs/frozen/frozen_deployment_v1.yaml`, committed BEFORE any E12 row
  is drawn; downstream campaign code reads the snapshot, not
  `results/tables/E01_nominal.json` (which remains as the historical
  record — pre-campaign audit F6). (b) Every parquet row draw archives its
  global indices under `data/processed/used_rows/` (seed-101 subset and
  E00's validation row groups 34/65/146/184 reconstructed and archived
  retroactively; E12 and all future draws archived at draw time), so
  disjointness is a stored, checkable artifact (audit F1). (c) The E12
  subset (seed 121) is drawn from the verified complement of all archived
  indices and its rows are quarantined from E13–E16 development.
- **Status:** adopted.

## D-021 — auditor_dev becomes the sensor role for all new experiments

- **Date:** 2026-08-11
- **Problem (audit F2):** E03/E05 computed I1 sensor draws on the same
  `nominal_test` events that feed I2 label streams; the veto-only design
  keeps Type-I honest, but sensor operating characteristics were measured
  on dependent data, while `auditor_dev` (45,000 rows) sat reserved.
- **Decision:** from E13 on, every sensor calibration/evaluation draw
  (geometry floors, CR boundary definitions, noise-floor bootstraps) uses
  the `auditor_dev` role; `nominal_test` remains the claim population.
  Existing results stand with the dependence disclosed in the manuscript's
  limitations.
- **Status:** adopted.

## D-022 — Independent per-call shot noise in QKSVC (before E16)

- **Date:** 2026-08-11
- **Problem (audit F5):** `QKSVC._gram` seeds an identical RNG on every
  call, so train/test Grams receive correlated noise and re-scoring
  reproduces the identical realization — unphysical for a device.
- **Decision:** `QKSVC(shots=...)` draws per-call independent substreams
  via `numpy.random.SeedSequence(seed).spawn(...)` with a call counter;
  regression test added. E09's published numbers are unaffected (its
  resampling was performed externally per configuration with distinct
  seeds); the difference is documented rather than retrofitted.
- **Status:** adopted.

## D-023 — E15 inference levels and likelihood definition

- **Date:** 2026-08-11
- **Decision:** three predeclared inference levels per environment/model:
  L1 = D-015 deployment-blind counting (unchanged baseline); L2 = binned
  Poisson profile likelihood over the frozen classifier score,
  L(μ,θ) = Π_b Pois(n_b | μ s_b(θ) + b_b(θ)) · Π_j N(θ̃_j; θ_j, σ_j), with
  per-nuisance template morphing anchored at the official ±1σ/±2σ points
  (piecewise linear-quadratic vertical morphing), all six benchmark
  nuisances profiled, intervals from the profile likelihood ratio;
  L3 = L2 with a predeclared leave-one-family-out nuisance model
  (realistic misspecification). L2 must pass a nominal-environment
  coverage calibration gate (0.6827 ± 0.02, 2000 pseudo-experiments)
  before any shifted-environment number is reported. Neither direction of
  the coverage outcome is privileged; both are findings.
- **Alternatives:** unbinned likelihoods (unnecessary power, higher
  misspecification surface), pyhf/HistFactory dependency (declined:
  scipy-based implementation keeps the morphing explicit and testable).
- **Status:** adopted.
- **Amendment (2026-08-11, before any E15 run):** (i) pseudo-experiment
  counts: L1 keeps E08's 2000 (its table is reused as the baseline, not
  re-run); L2/L3 use 500 PEs per (env, model, μ) — coverage precision
  ±2.2% amply resolves the effects of interest (0.68 vs collapse) at 4×
  less compute; the L2 nominal calibration gate stays at 2000 PEs with its
  0.6827 ± 0.02 criterion widened by the MC term in quadrature.
  (ii) soft_met's official LogNormal(0,1) prior has no density at the
  nominal soft_met = 0 (support s > 0): soft_met is profiled as a bounded
  free parameter in [0, 5] with NO constraint term (flat prior) —
  conservative (wider intervals), pathology-free, documented.
  (iii) L3's omitted family per environment is predeclared in E15.yaml:
  the actually-shifted family for single-nuisance environments; soft_met
  for the combo environments; the shifted norm scale for weight-only
  environments.
- **Amendment 2 (2026-08-11, after the registered calibration gate
  TRIGGERED on the first E15 run — coverage 0.93–0.98 vs 0.6827, all four
  models):** cause identified as the conditional-ensemble error: pseudo-
  experiments fluctuated only the Poisson counts while the Gaussian
  constraint centers stayed fixed at nominal, anchoring the profiled
  nuisances more strongly than the likelihood's constraint widths assume
  and over-widening the PLR intervals. Fix (standard unconditional
  ensemble): each pseudo-experiment also draws the auxiliary constraint
  centers θ̃_j ~ N(θ_j^true, σ_j) (tes/jes in σ units, norm scales in
  scale units; soft_met has no constraint term and thus no auxiliary).
  The gate is re-run after the fix; shifted environments are interpreted
  only if it passes. First-run output not retained as a results table
  (the run was aborted mid-grid at the gate failure, by design).
- **Amendment 3 (2026-08-11, second gate failure — numerical, found by
  q-scan diagnosis):** the raw Poisson nll has magnitude ~10⁷, so
  L-BFGS-B's *relative* ftol (2.2·10⁻⁹) terminated ~0.02 above the true
  minimum: profiles came out artificially flat (q(μ) even negative), μ̂
  frozen near its starting point, intervals ~×40 too wide, coverage → 1.
  Fixes: (i) saturated-model deviance form of the nll (identical q(μ),
  O(10) magnitude); (ii) explicit ftol=10⁻¹², gtol=10⁻⁹; (iii) monotone
  global-minimum safeguard during endpoint scans (q clamped ≥ 0, endpoints
  recomputed once if the reference improves). Post-fix diagnosis on real
  templates: q(μ) smooth and non-negative, σ(μ̂) ≈ 1.06 consistent with
  interval half-widths — the profiled-systematics inflation of μ (vs
  σ_stat ≈ 0.45) is genuine physics at s/b ≤ 0.7% per bin, and is itself
  an E15 finding (the price of validity).

## D-024 — Information set I3: definition and evidence channels (E14)

- **Date:** 2026-08-11
- **Decision:** I3 = I2(n) ∪ {control-region counts/yields computed from
  unlabeled target data in predeclared, frozen regions; nuisance estimates
  θ̂ derived from them with declared uncertainties}. Two guarantee-bearing
  channels: (i) rate claims |s_p − 1| ≤ x resolved from CR counts with
  exact Poisson-based bounds (anytime-valid e-process if sequential,
  fixed-n exact otherwise — declared per run config); (ii) true-weighted
  metric claims A_w^{(θ)} via reweighted label streams bounded worst-case
  over the θ̂ confidence set (fail-closed: insufficient θ̂ precision →
  UNRESOLVED). The weight-only unidentifiability at I1/I2-nominal is
  stated as a formal proposition (P_θ(X) = P_0(X) ⇒ no label-free test
  has power beyond α) — proved, not asserted.
- **Status:** adopted.
- **Amendment (2026-08-11, after the E14 v1 run TRIGGERED the registered
  CI-coverage falsifier — v1 table preserved as
  `E14_i3_v1_template_naive.json`):** the pure-Poisson CR fit ignores
  template MC statistics: analyst templates (auditor_dev role) differ from
  the target population (nominal_test role) by ~5% relative in the ttbar
  CR tail, which the fit misreads as a scale shift (ŝ_tt bias +0.07,
  CI coverage 0.0). Amended model (Barlow–Beeston-lite, Gaussian regime —
  counts are 10³–10⁶): per-CR expected-count variance gains the
  template-statistical term σ²_c = Σ_g (relerr_{g,c}·λ_{g,c})² with
  relerr from the template role's √(Σw²)/Σw; PLR CIs on the Gaussianized
  likelihood. Predicted consequence, embraced as a finding: s_tt is
  identified only to roughly ± the template noise (~±10% at 300k-subset
  statistics), so claims tighter than that remain UNRESOLVED — I3
  resolvability is real but quantitatively limited by auxiliary-evidence
  (template) quality; s_bkg (dominated by the high-statistics ztautau
  template) stays sharply resolvable.

## D-025 — Sensor family frozen; out-of-grid validation protocol (E04v3)

- **Date:** 2026-08-11
- **Problem (audit F3/F4):** the sensor identity (MMD²) was selected after
  E03's descriptor tables existed, and its veto floor is an
  uncertainty-free max over 12 weight-only environments.
- **Decision:** the sensor family is frozen as {quantum-kernel MMD²,
  matched-rbf8 MMD²}; no other descriptor may be promoted to veto duty in
  this paper. E04v3 validates the frozen sensors on 60 out-of-grid
  environments (36 off-grid single-nuisance + 24 official-prior draws,
  config committed before execution) with leave-one-family-out
  calibration, sensor values archived BEFORE degradation targets are
  computed, and the veto floor re-estimated on `auditor_dev` draws with
  bootstrap uncertainty and a predeclared quantile rule.
- **Status:** adopted.

## D-026 — E11v2 luminosity and sample policy

- **Date:** 2026-08-11
- **Decision:** the real-data side moves to the full opendata.cern.ch
  Run2012B+C TauPlusX files (sequential download → skim → delete raw,
  disk budget ~60 GB free); MC remains on the verified mirror files —
  statistically valid because MC weights normalize by the ingested file's
  own N_generated (w = σ·L/N_ingested), so a 10% MC sample yields unbiased
  expectations with larger MC-stat uncertainty, which is reported. With
  full data, DATA_LUMI_FRACTION = 1.0 and L = 11,467 pb⁻¹ for both data
  and MC weights. E11 v1 (mirror) results are retained; the ledger gets a
  mirror-vs-full comparison row per claim. `data/README.md` gains the
  missing Level II registration (audit note).
- **Status:** adopted.

## D-027 — E16 hardware arm scoped to the IBM Open plan

- **Date:** 2026-08-11
- **Context:** the BasQ allocation (`ibm_basquecountry`, E10v2 proposal)
  has not been granted; the account's only instance is the free Open plan
  (verified 2026-08-11: backends ibm_fez / ibm_marrakesh / ibm_kingston,
  ~10 min QPU per 28-day window; E10 v1 consumed 276 s for 496 circuits ×
  2048 shots).
- **Decision:** E16's hardware arm is sized to the measured Open-plan
  budget with priorities frozen in the registry entry: (a) full-pipeline
  micro-demonstration (fresh train Gram n≈48–64 + cross-Gram, auditor
  end-to-end on 100%-hardware kernels), (b) DD on/off mitigation split if
  budget allows, (c) drift sessions only if (a)+(b) fit. The E10v2 BasQ
  workload remains registered as the scaled version contingent on access;
  the paper claims only what the achievable scale supports (spec §34: no
  "hardware-validated" inflation).
- **Status:** adopted.

## D-028 — Post-campaign extension: scope, rules, and dispositions

- **Date:** 2026-08-11
- **Context:** the E12–E16 campaign and the post-campaign audit are closed
  (manuscript v0.3, commit fa95e8a). An extension prepares arXiv v1. Scope
  decided *against* maximal experiment accumulation: the remaining ceiling
  lies in (i) elevating existing results to formal statements, (ii) a small
  set of targeted hardening experiments, and (iii) restructuring the
  manuscript around three contributions — not in new grids.
- **Decision (rules, binding for every extension experiment):**
  1. Registration before execution with frozen falsifiers (spec §27/§38),
     no exceptions — including re-analyses of archived artifacts (E19,
     E11v3) and re-analyses that could *weaken* published verdicts.
  2. Fresh subsets draw only from the verified complement of ALL archived
     index sets (`data/processed/used_rows/`); index archives + SHA-256 +
     overlap-zero checks recorded in the result table itself (E12 pattern,
     D-020).
  3. The sealed `final_eval` roles (seed-101 global holdout per D-018;
     seed-121) remain sealed through arXiv v1; any spend requires its own
     decision entry. The endgame disposition is recorded at submission.
  4. Superseded tables preserved (`*_v1_*`); manifests append-only.
  5. E19 reuses `results/raw/E12_scores/*.npz`: the scores are archived
     *outputs* of the frozen deployment (config comment: "post-hoc checks
     only; not dev data"), not development inputs; labels and weights are
     reconstructed deterministically from the archived E12 subset indices
     + the frozen environment grid, with row_id alignment asserted against
     each archive. This reuse is declared here, before execution.
- **Dispositions (registered deferrals NOT run in this extension):**
  - Latin-hypercube multi-nuisance design (SAP §4; D-017 deviation 3):
    remains deferred. It would refine the disclosed additive-morphing /
    cross-term limitation (E15) without changing any verdict; revisited
    only if E08v2 raises a concrete question it can answer.
  - Classical-only seed top-up 5→10 (SAP §4; D-017 deviation 2): declined.
    The headline contrasts are per-seed *paired*; topping up only the
    cheap classical arms cannot tighten them and would introduce an
    asymmetric replication depth across the comparison.
  - Bootstrap 10⁴ (D-017 deviation 1): unchanged; stands as a documented
    deviation.
  - E10v2/BasQ scaled hardware: unchanged (D-027; allocation not
    granted). The DD-on/off Open-plan micro-split (E16 priority (b)) may
    run only if the 28-day window resets before the submission freeze;
    it is never on the critical path.
- **Manuscript direction (recorded, not a run):** restructure around three
  contributions — information-conditional certification; scientific-
  inference validity; quantum deployment uncertainty. The §3
  unidentifiability result and the §4.3 weighted reduction are elevated to
  formal Proposition/Theorem with proofs; the deployment-relative vs
  ideal-anchored claim taxonomy is registered as D-029. Governance/audit
  discipline is presented as methods/reproducibility evidence, not as a
  headline contribution.
- **Status:** adopted.

## D-029 — Claim semantics under estimated (random) deployments

- **Date:** 2026-08-11
- **Context:** with finite-shot or hardware kernels the deployed pipeline
  is itself estimated: the trained model, Platt calibrator, and operating
  threshold are functions of the realized kernel noise ω (E16 refits,
  recalibrates and re-freezes per realization). E16's dual accounting
  (post-audit H1) already measures two distinct claim families; this entry
  fixes their semantics for the manuscript's formal treatment.
- **Decision:** two registered claim classes for estimated deployments:
  - **Deployment-relative** C_dep(ω): M_T(f̃_ω) ≥ M_S(f̃_ω) − δ — both
    sides refer to the realized deployment; the reference is recalibrated
    per realization (E16 "own-τ" accounting).
  - **Ideal-anchored** C_ideal(ω): M_T(f̃_ω) ≥ M_S(f⋆) − δ — the
    reference is the ideal exact-kernel deployment (E16 "fixed-τ"
    accounting).
  Formal consequence to be stated in the manuscript with proof: if the
  certification procedure controls false certification at level α
  conditionally on every realized ω — which the confidence sequence
  guarantees, being applied to the realized pipeline's own label stream —
  then the marginal false-certification rate over deployment randomness is
  ≤ α by the tower property, for BOTH classes. Deployment randomness
  changes *which* claims are true and resolvable (reference movement,
  margin erosion), never the validity of what is certified. The result is
  presented as a claim-semantics clarification whose mathematics is
  deliberately elementary; it is the formal counterpart of E16's measured
  "noise changes what is resolvable, never the validity of what is
  certified". Any stability-margin bound (|margin| > ε_Q + ε_stat ⇒
  verdict stability across realizations) enters the manuscript only if
  its assumptions can be stated cleanly; otherwise it appears as an
  assumption-explicit proposition calibrated against the archived
  per-configuration E16 kernel diagnostics. No experiment consumes new
  randomness under this entry.
- **Status:** adopted.

## D-030 — Release hygiene for arXiv v1

- **Date:** 2026-08-11
- **Decision:** (i) the root-level `collider_qml_q1_research_spec.md`
  (verified byte-identical duplicate of `docs/research_spec.md`) is
  collapsed to a pointer stub; the canonical copy is the one under
  `docs/`, which every governing document already references. (ii)
  `README.md` and `CITATION.cff` are brought current with the extended
  registry (E00–E19), the three-contribution framing, and the
  self-correction record; `CITATION.cff` stays `type: software` with a
  `preferred-citation` to be added when the arXiv record exists. (iii) A
  GitHub Actions workflow runs the test suite on `windows-latest`
  (Python 3.13, pinned lockfile — the development platform) and
  best-effort on `ubuntu-latest` (`continue-on-error`); data-dependent
  test modules already skip when the benchmark parquet is absent, so CI
  exercises the guarantee suite. (iv) A best-effort Linux container
  recipe is added under `environment/containers/` with an honest header:
  the pinned Windows lockfile is the reproducibility instrument of
  record; the manifests (commit + config hash + dataset SHA-256 + seeds)
  are the scientific one. (v) The Zenodo deposit (code + configs +
  result tables + governing docs) is reserved by the author before the
  manuscript's data-availability text freezes, and published at
  submission; deposit hashes recorded.
- **Status:** adopted. (v) executed 2026-08-11 with an author-provided
  API token: Zenodo deposition **21894292** created as an unsubmitted
  draft with prereserved DOI **10.5281/zenodo.21894292**; the deposit is
  populated and published at arXiv submission time (F8), never before.
  The token lives in the gitignored `.env` only.
- **Amendment (2026-08-11, figure/table numbering):** at LaTeX
  conversion the companion figures Xb become subfigure (b) of Figure X
  (4/4b, 7/7b, 8/8b — prose references keep their identity as
  "Fig. 4b" → "Fig. 4(b)"); the former "Fig. 9" ledger is typeset as
  Table 2; the claim × information-set table is Table 1; the
  frozen-deployment table (§5.2) is Table 3; the estimation-diagnostics
  figure is supplementary (S16). The registry's historical "Fig. N
  data" output labels are unaffected (they name data products, not
  float numbers). New figures: Fig. 3 (family response / exact
  blindness — the registry's E03 "Fig. 3 data" promise, finally drawn)
  and Fig. 6 (label economics — closes the dangling §6.6 reference).


## D-031 — E08v2 falsifier disposition: bounded multi-draw re-registration (E08v3)

- **Date:** 2026-08-12
- **Context:** E08v2 completed 2026-08-11 (manifest
  `E08v2_4df40c2496d2_seed1812_1786484445`) and BOTH frozen falsifiers
  fired: (a) accounting-(iii) nominal coverage 1.000/1.000/0.9916 for
  the three gated models (band 0.6827 ± 0.02); (b) flagship
  tes=0.98 × A:xgboost L2 coverage 0.000 with independent templates —
  and the three nominal calibration cells collapse as well
  (0.000–0.0088, μ-bias +3..+11), showing the collapse is
  template-MC-noise-driven, not shift-driven. Post-run code audit found
  no arithmetic, scale, or alignment defect in `run_e08v2.py`.
- **Diagnosis (recorded as the basis of this decision):** belief-half
  MC-stat in the signal regions is large (s₀ relerr 0.23–0.32;
  heavy-tailed weights, small signal ESS), so the delta-method term
  dominates the Poisson term and, with a SINGLE realized belief draw,
  the conditional coverage of the corrected interval is degenerate
  (≈ 0 or ≈ 1 per draw). The 0.6827 target is observable only
  MARGINALLY over belief draws. Both E08v2 arms share the one draw, so
  the two firings are one correlated realization. The defect is the
  falsifier's single-draw premise, not the estimator's arithmetic.
  A second structural fact follows from the emulation itself: E08v2's
  "truth" is a finite half-sample, so the offset between belief and
  truth carries BOTH halves' MC variance while the field-correct
  belief-only BB term models only one — a belief-only interval cannot
  reach 0.6827 marginally in this emulation even in principle
  (predicted ≈ 2Φ(σ_bb/σ_tot) − 1 ≈ 0.52 when the variance terms
  dominate and the halves are symmetric).
- **Decision:**
  1. Per the frozen E08v2 falsifier-(a) text, the counting-BB arm is
     blocked and re-registered as **E08v3** (registry entry frozen
     before execution): K = 400 independent half-split draws for the
     counting arm (nominal env, four accountings — the three of E08v2
     plus `independent_bb_sym`, which adds the truth-half Σw² term and
     is the emulation-honest interval; in the field, where nature is
     exact, bb_sym ≡ bb) and K = 10 draws for the profile arm
     (flagship + shift-free nominal control cell, 200 PEs). The
     marginal falsifier applies to bb_sym; bb is reported against its
     model-predicted marginal coverage from the stored per-draw
     variance components.
  2. The E08v2 arm-(b) manuscript consequence STANDS as pre-accepted
     (§6.7 "profiling restores validity" downgraded to
     shared-simulation-conditional). E08v3's registered draw-fraction
     statistic fixes only the STRENGTH of the wording (generic vs
     draw-dependent), decided by frozen thresholds, not post hoc.
  3. **E18 trigger clause evaluated (D-028):** E08v2 did raise a
     concrete question — belief-side template statistics and
     single-draw degeneracy — but it is not one the Latin-hypercube
     multi-nuisance design answers (E18 targets additive-morphing
     cross-terms). E18 therefore REMAINS DEFERRED, with this reasoning
     recorded rather than silently.
  4. The abstract rewrite (roadmap F5.2) is blocked on E08v3: abstract
     item (v) asserts exactly the claim arm (b) qualifies.
  5. All E08v2 outputs stand published as-is (superseded-table rule
     not triggered; E08v3 is a follow-up, not a replacement).
- **Alternatives:** publish the single-draw result alone (Option B) —
  rejected: it leaves the marginal validity of the corrected estimator
  undetermined in print and the §6.7 wording strength unquantified,
  when a bounded (~2 h) registered follow-up resolves both. Author
  delegated the disposition 2026-08-12 ("best possible material").
- **Status:** adopted; E08v3 registered 2026-08-12 before execution.

## D-032 — Pre-submission audit finding: E19 weighted arm re-run under the registered nominal-weight convention

- **Date:** 2026-08-12
- **Context:** the pre-submission adversarial audit (F8.1) found, and the
  author-side verification confirmed against the tables, that
  `run_e19.py` audited the weighted claims with environment-scaled
  weights w(θ) (`te["weights"]` after `build_environment_dataset`
  applies normalization scalings) for both the truth `m_t_w` and the
  audit streams. The registered protocol — "the E13 Part-B
  weighted-vs-unweighted benchmark" — fixes NOMINAL per-event weights
  w(0) for every environment (D-019 spec §4; `configs/experiments/
  E13.yaml` estimand note; `run_e13.py` audit-C1 fix of 2026-08-11,
  whose superseded θ-weight table is preserved as
  `E13_weighted_cs_v1_theta_weights.json`). Diagnostic signature:
  E19's m_t_w varies across weight-only environments (0.76236 nominal
  → 0.76117 diboson_scale=1.5, A:qksvc) where the registered estimand
  is exactly invariant (E13 frozen table: 0.76382 everywhere). Blast
  radius: ~15/41 environments (12 weight-only + 3 combo3) × 4 models ×
  6 deltas × 20 seeds of weighted streams; 3 of the 6 published
  weighted false-certification events sit in weight-only environments;
  the headline "6/8,060 = 0.07%" is an estimate of a different,
  unregistered estimand. Internal coherence was preserved (truth and
  stream shared the same weights), so the ≤ α guarantee itself was
  never at risk; the estimand was wrong, not the statistics.
- **Decision:** following the E13 audit-C1 precedent — same experiment
  ID, no new registration scope:
  1. `run_e19.py` is corrected to audit the weighted arm with nominal
     weights w(0) aligned by row_id (one semantic change; the
     unweighted and landscape arms are untouched).
  2. The published table is superseded and preserved as
     `E19_fresh_world_validity_v1_theta_weights.json`; the corrected
     run writes the canonical path; manifests append-only.
  3. Frozen expectation, declared before the re-run: the unweighted
     block must reproduce the v1 table EXACTLY (identical draws, no
     weight dependence) — any deviation is a defect and blocks
     publication of the re-run; the weighted block changes in the
     weight-only/combo environments. The original E19 falsifier
     (validity replicates: weighted false certification ≤ α + 3σ on
     fresh streams) applies unchanged to the corrected numbers; both
     outcomes publishable.
  4. Registry/manuscript corrections riding along, from the same audit:
     the E19 status line "false refutation 1/12,260" is arithmetically
     impossible (true unweighted streams = 19,680 − 7,700 = 11,980;
     table rate 8e-05 ⇒ 1/11,980) and is corrected; the registered
     weighted seed salt "E19W" was never consumed (identical draws to
     the unweighted arm were used, matching the registry's "identical
     draws" clause) — the dead parameter is recorded here and the
     table now records the salt actually used; the E13 Part-B
     class-conditional claims (TPR_w/TNR_w) were not replicated in E19
     — disclosed as a scope reduction, not silently.
  5. E17 estimand (i) completion: the registered between-world table
     covers weighted AUC only; the unweighted between-world summary is
     computed as a derived analysis from the archived per-world tables
     (no new randomness) and recorded in the E17 status.
- **Status:** adopted; executed 2026-08-12.

## D-033 — Priority-B closure: E13v2 run to the impossibility branch; E07v2 declined with disposition

- **Date:** 2026-08-12
- **Context:** the mandatory extension set is closed (E17, E19+D-032,
  E11v3, E08v2+E08v3/D-031). The author directed the program to its
  absolute ceiling before the release freeze. Of the two priority-B
  items frozen at D-028, E13v2 was executed (spec §4c rule derived and
  frozen before implementation; battery complete 2026-08-12): validity
  PASS, falsifier (b) fired → the BA_w path is published as measured
  impossibility at physics weight dispersion, with the mechanism
  decomposed (TNR_w fully certifiable; TPR_w information-limited by the
  9.7×10⁻⁴ weighted signal fraction, implied n* ≈ 2×10⁷ at margin
  0.05; the sharpened rule resolves the class-independent control that
  the v1 bound could not touch).
- **Decision (E07v2 declined):** E07v2 (LURE-style control variates;
  stratified without-replacement acquisition) is NOT run for arXiv v1.
  Rationale: (i) its registered placement is supplement-only with no
  abstract branch — it cannot move the headline; (ii) E07's mechanism
  analysis already explains the active-acquisition negative (the ×2
  importance-weight range halves effective margins), and the E13v2
  result now demonstrates the deeper point on the weighted side —
  near-boundary label costs are information-limited, not
  procedure-limited (n* vs Wald-style yardstick; TPR_w impossibility); (iii) it
  is the costliest remaining item (new `src/qevc/acquisition/` module,
  WoR-valid finite-population CS, tests, 2–3 days) against the release
  freeze. The E07 negative therefore keeps its registered scope
  ("under the tested conditions", naive uncertainty-mixture importance
  sampling); the registry entry stays `specified` with its frozen
  falsifier, available to a future revision. This is a disposition of
  the D-028 priority-B clause, not a silent drop.
- **E16 priority (b) DD-on/off micro-split:** unchanged (D-027/D-028) —
  runs only if the IBM Open window resets (~2026-09-07) before the
  submission freeze AND F8 has not started; the final state will be
  recorded in the sealed-holdout/endgame decision entry at submission.
- **Status:** adopted. The experimental program for arXiv v1 is CLOSED:
  every registered mandatory experiment complete, every priority-B item
  executed or dispositioned, nine falsifier firings obeyed and
  published (E02R, E12(e), E14 v1, E15 gate, E17(b), E08v2(a)(b),
  E08v3(a), E13v2(b)).

## D-034 — Final authorship and institutional front matter

- **Date:** 2026-08-12
- **Context:** the author supplied a previously published team article solely
  as the authoritative source for the shared author list, ORCIDs and
  institutional affiliation. Page 1 and its embedded ORCID links were
  independently inspected; all four ORCID check digits validate under ISO
  7064 MOD 11-2. The source file was `sn-article.pdf`, SHA-256
  `D9679C24D2227D73E00A21839D8A1DE206A05C8FF53DEDD54461BC1FACDCB039`.
- **Decision:** the paper, supplement, package metadata and citation metadata
  use Roberto Fernández-Barrios (0009-0003-5312-2634), Iker Pastor-López
  (0000-0002-3068-6248), Asier González-Santocildes
  (0009-0002-8888-8560), and Pablo García Bringas
  (0000-0003-3594-9534), all affiliated with the Faculty of Engineering,
  University of Deusto, Avda. de las Universidades 24, 48007 Bilbao, Spain.
  Roberto is the corresponding author at roberto.fernandez.b@deusto.es.
  The reference article is not a research input or release artifact and is
  deleted from the working tree after verification, as explicitly requested
  by the author.
- **Status:** adopted and verified in the final 26-page manuscript and
  7-page supplement.

## D-035 — arXiv-v1 sealed holdouts and release freeze

- **Date:** 2026-08-12
- **Context:** all mandatory experiments, registered dispositions, F8.1/F8.2
  audits, bibliography checks, final compilation and visual inspection are
  complete. The author explicitly authorized publication on 2026-08-12.
- **Decision:** (i) seed-101 and seed-121 `final_eval` remain sealed for a
  journal revision; arXiv v1 spends no sealed-role data. (ii) The E16
  priority-(b) DD-on/off micro-split is not run: its gate required the IBM
  Open window to reset before F8 began, and F8 is already complete. (iii)
  The release uses arXiv primary category `quant-ph`, cross-lists `hep-ph`
  and `stat.ME`, and CC BY 4.0 for the preprint. (iv) Publication is gated
  on a green Windows CI run; the release tag is `arxiv-v1`; Zenodo deposition
  21894292 is populated with the audited release artifacts and published at
  submission time.
- **Frozen artifacts:** `manuscript/latex/main.pdf` — 26 pages, SHA-256
  `9F798522ED240BD7F76915877068291EBBC5FDC9ECEDBDC18EF6115D8DEA4D2F`;
  `manuscript/supplementary/supplement.pdf` — 7 pages, SHA-256
  `83C4279415295313903E1D052FA856C880809740B708DD88AB2A02F3074B1C22`;
  `dist/arxiv-v1-source.zip` — SHA-256
  `9C439AF7628567F490ABD60AA36A38A2EEC3FC5D85B846AC79DD223235FF8646`.
- **Status:** adopted. The mandatory Windows CI and auxiliary Linux CI passed
  on PR #1 and again on merge commit
  `a7387ec0b25e44c588fa3fa6b638e555d8e537e4`. Git tag `arxiv-v1`, the public
  GitHub release, and Zenodo record 10.5281/zenodo.21894292 were published on
  2026-08-12. The four Zenodo file MD5s matched the frozen local artifacts
  before publication. The arXiv source/metadata are ready but were not
  submitted: the author explicitly deferred arXiv publication on 2026-08-12.

## D-036 — Final mathematical/editorial audit and superseding freeze

- **Date:** 2026-08-12
- **Context:** the author requested one last mathematical and editorial audit
  of the complete release without new experiments. Independent QML, HEP and
  statistics reviews found formal overstatements in Proposition 4, the
  weight-bound information set, Proposition 2, multiplicity, the Wald
  comparison, C2, E17, and the interpretation of the micro-QPU arm.
- **Decision:** (i) Proposition 4 remains conditional because E16 archives
  only ΔM_S, not ΔM_T or ΔM_T−ΔM_S; flip rates are independent empirical
  evidence. Equality of two ternary verdicts requires both audits to resolve
  and joint coverage (at least 1−2α without joint calibration). (ii) Theorem 1
  is stated conditionally on a frozen finite population and scalar bound fixed
  before audit order, for fixed τ and per-claim error control; no FWER or
  arbitrary adaptive-sampling guarantee is implied. (iii) E13v2 class bounds,
  computed with complete-population labels, are an oracle diagnostic rather
  than an operational I2 guarantee. (iv) C2 is jointly conditioned on nuisance
  representability and auxiliary/template quality. (v) Wald is a contextual
  yardstick, E17 signs are cross-world unstable, and quantum execution adds
  measurement-induced uncertainty without exclusive claims about randomness.
- **Experimental scope:** no experiments, models, datasets, or QPU executions
  were added. Figure 8 was redrawn only from archived E09/E10/E16 artifacts.
- **Status:** adopted; the hashes and page counts in D-035 are superseded by
  the final audit manifest and `docs/audits/final_math_editorial_audit.md`.

## D-037 — npj Quantum Information target and submission ceiling

- **Date:** 2026-08-12
- **Context:** after the scientific freeze, the author supplied a comparative
  venue analysis, current scope extracts, a local guidelines folder, and the
  location of an earlier Springer Nature LaTeX template. APC funding is
  available, so cost does not constrain journal choice. Current official
  sources were rechecked independently: *npj Quantum Information* explicitly
  covers quantum machine learning, and its open Collection *Quantum machine
  learning: understanding capabilities, limitations, and perspectives for
  quantum advantage* accepts submissions through 2026-12-31. The main
  editorial risk is quantum centrality, not formal scope or evidence quality.
- **Decision:** target *npj Quantum Information* first through that Collection.
  The manuscript is positioned as a QML claim-validity paper: C1/C2 provide the
  model-agnostic scientific validity layer, while E09/E10/E16 instantiate the
  QML-specific additional measurement-induced deployment uncertainty through
  Gram estimation, refitting, calibration, and thresholding. HEP is retained
  as the stringent scientific deployment environment. No quantum advantage is
  claimed. The repository now uses the self-contained Springer Nature
  `sn-jnl`/`sn-nature` source, a 13-word title, 147-word abstract, journal-order
  sectioning, mandatory availability/declaration statements, generative-AI
  disclosure, a Collection-specific cover letter, metadata sheet, verifier,
  and reproducible source/PDF bundle. Hardware evidence remains explicitly a
  micro-scale fail-closed consistency demonstration, not performance or
  certification at scale. The distinct same-author manuscript DOI
  10.5281/zenodo.21776862 is disclosed voluntarily with its non-overlap stated.
  `guidelines/` is ignored by Git.
- **Scientific scope:** presentation only. No experiment, model, dataset,
  artifact value, QPU run, or conclusion was added. All formal and evidential
  weakenings of D-036 remain unchanged.
- **Frozen submission artifacts:** main PDF, 29 pages, SHA-256
  `A2DC23A938D9A044EC9FB4C52C6C409EBE17486FEF6E2A89E0E109F7615E1E68`;
  Supplementary Information, 8 pages, SHA-256
  `CDAF97F09A2DDCB2614421E909FAD334834A49DA9AFAF9BDFDF4684FC023DE1F`;
  cover letter, 1 page, SHA-256
  `3D4F6F3DF84CEF8DDED32F3A9A0F6F3F5D75BC42B870D8CD76D5EB69741A7A8A`;
  `dist/npjqi-submission.zip`, SHA-256
  `D122C53F729242513B1A3218473E5FD511C00F7A1EC86FCFAB5F48F57A9A4FE3`.
- **Status:** adopted. All 127 tests, 97 scientific audit gates, 49 npj
  submission gates, independent archive builds, and the 38-page visual review
  pass. The manuscript is ready for author confirmation and portal upload.
