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

