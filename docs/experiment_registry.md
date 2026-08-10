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
- **Outputs:** `experiments/E00_dataset_validation/` report + `results/tables/E00_*`.
- **Status:** planned.

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
- **Outputs:** `results/tables/E01_nominal.*`, tuned configs under `configs/models/`.
- **Status:** planned.

## E02 — Systematic landscape

- **Question:** How do all models degrade over the physical nuisance grid?
- **Hypothesis:** H1.
- **Environments:** per-nuisance {−2σ…+2σ} + predeclared LHC combinations.
- **Metric:** `M(θ)`, `Δ_θ` per SAP §1.1; paired quantum–classical contrasts.
- **Falsifier:** Δ_θ CIs include 0 everywhere → H1 unsupported; report as such.
- **Outputs:** `results/tables/E02_landscape.*`, Fig. 2 data.
- **Status:** planned.

## E03 — Kernel geometry observatory

- **Question:** How does quantum-kernel geometry move under physical systematics?
- **Hypothesis:** H2 (descriptive half).
- **Metric:** geometry descriptor vector `G_θ` (CKA, spectrum, effective rank,
  alignment, margin stats, RKHS class separation…) across the E02 grid.
- **Falsifier:** descriptors statistically flat across θ while E02 shows material
  degradation (records a *negative* geometry result).
- **Outputs:** `results/tables/E03_geometry.*`, Fig. 3 data.
- **Status:** planned.

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
