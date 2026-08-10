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
kernel-geometry sensor (MMD² of a bandwidth-limited kernel over compact
physics features — quantum and matched classical alike, Spearman ρ =
0.56–0.73 against multi-seed targets; a full-feature RBF sensor fails,
identifying feature conditioning rather than quantumness as the active
ingredient) predicts degradation magnitude out-of-environment, while being
blind — by the rate-free nature of feature-distribution evidence — to the
benchmark's weight-only normalization nuisances, which nevertheless destroy
physics-level inference; (iii) construct a fail-closed,
information-set-conditional auditor based on anytime-valid confidence
sequences whose empirical false-certification rate is 0.61% of 7,820
genuinely-false claim-streams at a nominal α = 5% (per-cell maximum 2/20,
within binomial fluctuation), and measure the label budget n*(θ, C) at which
claims resolve; (iv) demonstrate that classifier metrics and inference
validity decouple: replication-gated cells combine ΔAUC consistent with zero
at the ±0.01 partition-variance precision with μ-interval coverage collapse
(to 0.000 in the flagship tau-energy-scale cell); and (v) deploy the
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
partitions (each partition seals its own final_eval; the primary partition's
final_eval was untouched by all single-partition results, while the
replication partitions overlap it — no globally-untouched holdout remains,
and the primary final_eval rows are frozen as the global holdout going
forward, D-018); 28 unique nuisance points θ (±1σ/±2σ grids ×
{TES, JES, soft-MET, 3 normalizations} + 4 combos), evaluated as 41
environment datasets including seed replicates of the stochastic soft-MET
shift and nominal; model suite with comparable, predeclared tuning budgets
(10 random-search configs × 3-fold physics-weighted CV AUC; MLP 5 configs);
statistical protocol per the predeclared SAP with logged deviations (D-017:
10³/5×10²-resample descriptive bootstrap CIs; 5-seed replication gates the
nominal contrasts and the TES/combination degradation claims — descriptor,
auditor-error and coverage numbers are single-partition with audit-seed
replication only).

## 6. Results

### 6.1 Nominal performance (E01 + E02R)
Matched 2000-event budget, 5-seed replication: QK-SVC 0.848 ± 0.022 —
consistently above RBF-SVC and linear SVC, consistently below tuned trees
(QK − XGB = −0.035 ± 0.013, negative in 5/5 seeds). The single-seed "tie"
with XGBoost did not survive replication and is reported as such. Feature
asymmetry stated plainly and resolved by the matched-kernel control
(spec §23): the QK-SVC encodes 8 predeclared sentinel-free features (one per
qubit, D-011) while most classical baselines consume all 28; the RBF-SVC on
the identical 8 features reaches 0.859 ± 0.016 — statistically
indistinguishable from the QK-SVC (per-seed difference sign-unstable) and at
the tuned-tree level. The earlier "QK above RBF" contrast was a feature-set
effect (sentinel dilution of the 28-feature RBF), not quantumness.

### 6.2 Behavior under systematics (E02 + E02R; Fig. 2)
TES down-shifts degrade the QK-SVC in 5/5 seeds (+0.0024 ± 0.0010 at −2σ);
the up-shift arm does not replicate (partition variance dominates); the
adverse combination degrades the QK-SVC in 5/5 seeds (+0.025 ± 0.024).
Weight-only nuisances leave AUC invariant (exactly, for uniform background
scaling — an internal consistency check).

### 6.3 Kernel geometry (E03 + E04v2 + matched control; Fig. 4)
The label-free quantum-kernel MMD² predicts replicated degradation
out-of-environment: ρ_S = 0.56 (own model), 0.68 (transfer to XGBoost). The
RBF sensor on the full 28-feature set does not (ρ_S = −0.21, n.s.) — but the
matched RBF sensor on the identical 8 features does, and best of all
(ρ_S = 0.73 own model, 0.60 transfer). The active ingredient is therefore
*feature conditioning and kernel bandwidth*, not quantumness: a
bandwidth-limited kernel over compact, sentinel-free physics features is an
effective label-free shift sensor whether quantum or classical — a
practically useful, model-agnostic recipe, and an honest negative for
quantum-specific sensing. The 28 grid environments are family-correlated,
so we lean on the predeclared falsifier (out-of-environment ρ ≤ 0,
comfortably cleared), not on the nominal p-values. Multivariate descriptor regressions overfit at this
environment count and underperform the single sensor. Feature-distribution
geometry is rate-free by construction and therefore blind to the benchmark's
weight-only implementation of normalization nuisances — measured via the
noise-floor construction; rate/control-region monitoring is the label-free
channel that does carry that information (§8), which is precisely the
information-set point.

### 6.4 Conditional certification (E05; Fig. 5 data)
Across 19,680 claim-streams, of which 7,820 carry genuinely false claims:
empirical false certification 48/7,820 = 0.61% ≤ α = 5% (per-cell maximum
2/20, three near-boundary cells, within binomial fluctuation of α); false
refutation 3/11,860; 98% of near-boundary false claims end UNRESOLVED at
n = 3,000 (fail-closed). Threshold-level accuracy proves far more
shift-robust than ranking (worst accuracy drop 0.008 vs replicated AUC drops
up to +0.025 ± 0.024 at the adverse combination): *the metric named in the
claim changes which claims are at risk*.

### 6.5 Label efficiency (E06 + E07; Figs. 5–6)
n* is sharply margin-driven (medians over resolved streams; 100% resolve at
|margin| ≥ 0.04): ~180 labels at |margin| ≥ 0.08; ~870 at 0.04–0.08;
~13,000 at 0.01–0.02 where 58% resolve by 20,000; below 0.01 only 2–9%
resolve and the fail-closed UNRESOLVED verdict dominates. Streams draw
labels with replacement (the CS is then exactly valid); for budgets
approaching the target-population size a without-replacement CS would
tighten these numbers — the quoted large-budget n* are conservative as
distinct-label counts. Uncertainty-guided acquisition **loses** to uniform sampling
(median n* ratio 1.55; better in 10% of cells) — the ×2 importance-weight
range halves effective margins and errors are not concentrated at the frozen
threshold. Random labeling is near-optimal here; reported as a primary
(and practically simplifying) negative result.

### 6.6 Physics-level validity (E08; Fig. 7)
With a deployment-blind counting estimator (nominal coverage verified at
0.68), 73 decoupled cells — replication-gated (E02R |mean ΔAUC| + s.d.
< 0.005), spanning 65 unique (θ, model) pairs over 23 distinct nuisance
points — combine a classifier indistinguishable from nominal at
partition-variance precision with coverage < 0.633; flagship: the TES −2σ cell where XGBoost's
replicated ΔAUC is consistent with zero while coverage = 0.000 (background
shift 23× the statistical uncertainty, invisible to ranking metrics). The
normalization nuisances — invisible to rate-free feature-space geometry —
also break coverage (diboson down to 0.003). Within the I0/I1
(feature-distribution) information sets, neither classifier metrics nor
geometry carry the information that protects inference; rate monitoring
(§8) and labeled evidence (I2) do.

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
for pure shot noise at the same budget — a ~9× ratio (defining the excess by
linear subtraction gives 15.1%; under an independent-sources quadrature
decomposition, 16.9% — the device term dominates either way); fidelities
biased down (−0.010); K_hw remained PSD. Classifier-level comparisons at n = 32 are
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

The narrative the evidence selected is spec §37's composite, sharpened by
the matched control: the quantum model is competitive but not superior, and
nothing in our sensing or certification results is quantum-specific — the
matched classical kernel matches both the classifier and the sensor. What
remains is arguably more useful: the validity question is dominated not by
the model family but by *what information the deployment possesses* — certification is
cheap when claims have margin, impossible when they don't, and physics
inference is at risk precisely where feature-distribution evidence is blind
and only rate monitoring or labels can see. This is an argument for
information-set-conditional auditing as standard practice for ML-based
physics analyses, quantum or classical.

## 11. Conclusion

**TODO:** prose.

---

### Reproducibility statement (draft)

All experiments are configuration-driven with immutable run manifests (git
commit, config hash, dataset SHA-256, seeds, package versions, backend
metadata). All simulation results were regenerated in a single clean-tree
campaign so every manifest's commit identifies the exact code state (D-016);
development-era manifests are retained alongside. Each partition seals its
own final-evaluation split; single-partition results never touched the
primary final_eval, replication partitions overlap it, and the primary
final_eval rows are frozen as the global holdout for all future work
(D-018). Raw QPU counts and full hardware provenance are archived (the QPU
job itself is not re-executable; its job id, calibration snapshot, and raw
counts stand as its record). Code, configs, and result tables will be
released with a DOI.
