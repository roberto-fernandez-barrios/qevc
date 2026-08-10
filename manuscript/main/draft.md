# When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics

**Draft v0.1 — 2026-08-10.** Structure per research spec §33; language per the
claims discipline of §34. All numbers come from the registered experiments
(`docs/experiment_registry.md`); nothing here exceeds what the evidence
supports. TODO markers indicate sections needing prose expansion.

---

## Abstract (draft)

Quantum machine-learning classifiers for collider physics are validated, like
their classical counterparts, on nominal simulation — yet deployment happens
under experimentally uncertain conditions. We ask a question that prior work
on quantum machine learning has not addressed: *which claims about a quantum
event classifier remain justified when collider systematics shift the
deployment distribution, and under what experimentally available information?*
Using the FAIR Universe HiggsML Uncertainty benchmark (H→ττ with six
parameterized nuisance sources), we (i) map the behavior of quantum-kernel
classifiers under physical systematics — to our knowledge the first
evaluation of quantum classifiers under nuisance-induced, shape-level
distribution shift of the inputs (prior work folds only rate-type
normalization uncertainty into final limits) — finding small but replicated
degradations under tau-energy-scale shifts and adverse nuisance
combinations; (ii) show that a label-free
quantum-kernel geometry sensor (MMD²) predicts degradation magnitude
out-of-environment (Spearman ρ = 0.56–0.68 against multi-seed targets) while
being *provably blind* to normalization nuisances that nevertheless destroy
physics-level inference; (iii) construct a fail-closed, information-set-
conditional auditor based on anytime-valid confidence sequences whose
empirical false-certification rate is 0.61% at a nominal α = 5% over 19,680
claim-streams, and measure the label budget n*(θ, C) at which claims resolve;
(iv) demonstrate that classifier metrics and inference validity decouple:
89 environment–model cells combine |ΔAUC| < 0.005 with μ-interval coverage
below 0.63 — including coverage 0.000 at ΔAUC = +0.0002; and (v) deploy the
framework end-to-end on real CMS Open Data collisions, where it certifies
control-region claims, detects the simulation-to-data shift, and — by
construction — refuses to certify event-level accuracy without labels.
Finite-shot and superconducting-hardware experiments bound where quantum
estimation noise perturbs certificates: only near claim boundaries, with
device noise exceeding shot noise ~8× at practical budgets. None of our
conclusions requires quantum advantage; the framework treats quantum and
classical models identically and is fail-closed by design.

## 1. Introduction

- Validation-deployment gap in collider ML; systematics as distribution shift.
- QML-for-HEP literature evaluates on nominal simulation only (novelty matrix);
  robustness in QML means hardware/adversarial noise, never physical
  systematics.
- Contributions C1–C7 (spec §5), mapped to experiments E01–E11.
- Explicitly NOT a quantum-advantage paper (spec §2); all four outcome
  scenarios of §37 are scientifically reportable; we report which one the
  evidence selected.

**TODO:** full prose; framework figure (Fig. 1).

## 2. Related Work

Condensed from `docs/novelty_matrix.md` (five clusters, 40+ works; all
flagged arXiv IDs verified 2026-08-10): QML-for-HEP; quantum-kernel theory
and trust; QML validity/monitoring; systematics-aware classical HEP ML;
certification and label-efficient evaluation. Gap statement: no work
combines quantum models + physical collider systematics +
information-conditional certification + physics-level inference. Nearest
neighbors to cite and distinguish explicitly: Ait Haddou et al. (PTEP 2026,
arXiv:2511.15672 — rate-only normalization uncertainty entering final
limits, classifier itself unaudited under shift) and Chen & Weng
(arXiv:2606.24038 — betting e-process certification of sim-to-real transfer
in robotics; no information-set hierarchy, no physics inference).

## 3. Problem Formulation

- Collider event classification with event weights; nuisance-parameterized
  environments D_θ (official FAIR Universe semantics; selection migration is
  physics, D-013).
- Quantum fidelity kernels; frozen-deployment discipline (nothing retunes
  per environment).
- Claims C(M, τ) and degradation form; information sets I0 ⊂ I1 ⊂ I2(n) ⊂ I3;
- Conditional validity: SUPPORTED / REFUTED / UNRESOLVED with fail-closed
  semantics (D-006): heuristics can veto, never certify.

## 4. Method

- 4.1 Geometry observatory (E03/E04): descriptors; the univariate MMD²
  sensor; the structural blind spot to weight-only nuisances (measured, and a
  *feature* of the argument: label-free sensors cannot protect physics).
- 4.2 Conditional auditor: empirical-Bernstein confidence sequences
  (anytime-valid ⇒ n* is a legitimate stopping time); one CS resolves all
  thresholds simultaneously; decision rule frozen (D-006); estimand D-014.
- 4.3 Partial-label certification: n*(θ, C) as survival curves over budgets.
- 4.4 Acquisition: uniform vs bounded-importance uncertainty mixture (validity
  preserved by construction).
- 4.5 Physics-level inference: deployment-blind single-SR counting estimator
  (D-015; limitations stated — profiled analyses degrade more gracefully; the
  demonstrated claim is about information, not about H→ττ being hopeless).

## 5. Experimental Design

FAIR Universe (Zenodo 15131565, 220,099,101 events verified; norm-nuisance
no-op defect in the official code found, worked around, and reported upstream
as FAIR-Universe/HEP-Challenge#184); 300k-event subset; raw-row five-role
partitions with sealed final_eval; 41 environments (±1σ/±2σ grids ×
{TES, JES, soft-MET, 3 normalizations} + 4 combos); model suite with
identical tuning budgets (10 configs × 3-fold, physics-weighted CV AUC);
statistical protocol per the predeclared SAP (10⁴-resample bootstrap CIs;
5-seed replication gates every reported number; predeclared relevance
thresholds).

## 6. Results

### 6.1 Nominal performance (E01 + E02R)
Matched 2000-event budget, 5-seed replication: QK-SVC 0.848 ± 0.022 —
consistently above RBF-SVC and linear SVC, consistently below tuned trees
(QK − XGB = −0.035 ± 0.013, negative in 5/5 seeds). The single-seed "tie"
with XGBoost did not survive replication and is reported as such.

### 6.2 Behavior under systematics (E02 + E02R; Fig. 2)
TES down-shifts degrade the QK-SVC in 5/5 seeds (+0.0024 ± 0.0010 at −2σ);
the up-shift arm does not replicate (partition variance dominates); the
adverse combination degrades the QK-SVC in 5/5 seeds (+0.025 ± 0.024).
Weight-only nuisances leave AUC invariant (exactly, for uniform background
scaling — an internal consistency check).

### 6.3 Kernel geometry (E03 + E04v2; Fig. 4)
The label-free quantum-kernel MMD² predicts replicated degradation
out-of-environment: ρ_S = 0.56 (own model, p = 0.002), 0.68 (transfer to
XGBoost, p = 10⁻⁴). The RBF-28 sensor does not (ρ_S = −0.21, n.s.).
Multivariate descriptor regressions overfit at this environment count and
underperform the single sensor. Geometry is categorically blind to
normalization nuisances (weight-only shifts move no feature) — measured via
the noise-floor construction.

### 6.4 Conditional certification (E05; Fig. 5 data)
19,680 claim-streams: empirical false certification 0.61% ≤ α = 5%; false
refutation 0.03%; 98% of near-boundary false claims end UNRESOLVED at
n = 3,000 (fail-closed). Threshold-level accuracy proves far more
shift-robust than ranking (worst accuracy drop 0.008 vs AUC drops up to
0.035): *the metric named in the claim changes which claims are at risk*.

### 6.5 Label efficiency (E06 + E07; Figs. 5–6)
n* is sharply margin-driven: ~180 labels at |margin| ≥ 0.08; ~870 at
0.04–0.08; ~13,000 at 0.01–0.02; fail-closed UNRESOLVED below 0.01 even at
20,000. Uncertainty-guided acquisition **loses** to uniform sampling
(median n* ratio 1.55; better in 10% of cells) — the ×2 importance-weight
range halves effective margins and errors are not concentrated at the frozen
threshold. Random labeling is near-optimal here; reported as a primary
(and practically simplifying) negative result.

### 6.6 Physics-level validity (E08; Fig. 7)
With a deployment-blind counting estimator (nominal coverage verified at
0.68), 89 environment–model cells combine |ΔAUC| < 0.005 with coverage
< 0.633 — flagship: ΔAUC = +0.0002 with coverage = 0.000 (background shift
23× the statistical uncertainty, invisible to ranking metrics). The
geometry-blind normalization nuisances also break coverage (diboson down to
0.003). Neither classifier metrics nor label-free geometry carry the
information that protects inference.

## 7. Quantum Realism

### 7.1 Finite shots (E09; Fig. 8)
Kernel error ∝ 1/√shots (13.7% → 2.4%); effective rank inflates under shot
noise (353 → 489 at 128 shots); the classifier is shot-tolerant at n = 2000
(±0.01 AUC at 128 shots); certificates flip only near claim boundaries
(8/360 cells); at low budgets shot noise swamps the small replicated TES
response — measuring small systematic effects requires ≳2–4k shots.

### 7.2 Hardware (E10; Fig. 8)
ibm_marrakesh (Heron r2), 496 compute–uncompute circuits × 2048 shots, raw
counts, no mitigation, 276 s QPU: K_hw deviates 17.0% (Frobenius) vs 1.9%
for pure shot noise — device-noise excess 15.1% (~8×); fidelities biased
down (−0.010); K_hw remained PSD. Classifier-level comparisons at n = 32 are
reported as qualitative only. [E10 v2 under BasQ access — proposal in
`docs/basq_e10v2_proposal.md` — would run the full certification pipeline on
hardware kernels and quantify the mitigation-recoverable fraction.]

## 8. Simulation-to-Real Demonstration (E11; Fig. 9 = claims ledger table)

CMS Open Data H→ττ 2012 (μτ_h; same physics process as Level I). MC-trained
models with Level-I-frozen hyperparameters; no target tuning. The ledger:
event-level accuracy on collision data — UNRESOLVED *by construction* (no
labels exist; the framework refuses to invent real-data accuracy);
W-normalization within 30% in the high-mT control region — SUPPORTED
(data/MC = 0.922 [0.885, 0.961]); no-shift-at-sensor-floor — REFUTED
(MMD² at 2.6× the MC-vs-MC floor: the sim-to-real shift is detected and
vetoes performance claims); SS-region QCD excess — SUPPORTED (+1,007 events,
z = 18.6). Aggregate physics claims are certifiable from control-region
evidence; event-level performance claims are not — and the framework says so
rather than guessing.

## 9. Failure Cases and Limitations

- The elegant single-seed TES antisymmetry did not replicate (up-shift arm);
  partition variance dominates most single-nuisance deltas — all reported
  numbers carry 5-seed error bars.
- Active acquisition lost to uniform (§6.5); smarter estimators (LURE-style
  control variates) remain open.
- The H5 magnitudes are estimator-specific (deployment-blind single-SR
  counting with low-purity SRs); profiled analyses degrade more gracefully.
- E05 v1 audits an unweighted estimand (D-014); weighted-metric confidence
  sequences and information set I3 are future work.
- Hardware evidence is kernel-level at n = 32; certification-on-hardware
  requires the E10 v2 workload.
- Level II uses a 10% data mirror and a simplified reference selection; a
  ×10 luminosity-normalization error on first ingestion was caught by the
  control regions themselves and is documented.

## 10. Discussion

The narrative the evidence selected is spec §37's composite: the quantum
model is competitive but not superior; its kernel geometry is a genuinely
better label-free shift sensor than the classical comparator; and the
validity question is dominated not by the model family but by *what
information the deployment possesses* — with certification cheap when claims
have margin, impossible when they don't, and physics inference at risk
precisely where every label-free signal is blind. This is an argument for
information-set-conditional auditing as standard practice for ML-based
physics analyses, quantum or classical.

## 11. Conclusion

**TODO:** prose.

---

### Reproducibility statement (draft)

All experiments are configuration-driven with immutable run manifests (git
commit, config hash, dataset SHA-256, seeds, package versions, backend
metadata); the five-role partition seals a final-evaluation split untouched
by every result reported here; raw QPU counts and full provenance are
archived. Code, configs, and result tables will be released with a DOI.
