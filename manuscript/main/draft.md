# When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics

**Draft v0.2 — 2026-08-11.** Structure per research spec §33; language per
the claims discipline of §34. All numbers come from the clean-tree
regenerated experiments (`docs/experiment_registry.md`, commit 627796d);
nothing here exceeds what the evidence supports. Remaining before
submission: Related Work expanded to full cited prose at LaTeX conversion
(bibliography from `docs/novelty_matrix.md`), venue formatting, and final
number-by-number verification against the result tables.

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

Machine-learned event classifiers are now standard components of collider
analyses, and quantum machine-learning (QML) classifiers are increasingly
proposed as their successors. Both are validated the same way: on nominal
simulation, under the exact conditions the simulation happened to assume.
Deployment is different. The real experiment operates under uncertain
calibrations — tau and jet energy scales, soft missing-energy activity,
background normalizations — collectively the *systematic uncertainties* of
the measurement. Each nuisance configuration θ defines a slightly different
data distribution D_θ, and the classifier that was validated at θ = 0 is
deployed, unavoidably, at some unknown θ ≠ 0. For classical models this
validation–deployment gap is studied under headings like decorrelation,
systematics-aware training, and uncertainty-aware inference. For quantum
models it has, to our knowledge, never been studied at all: the QML-for-HEP
literature evaluates on fixed nominal simulation, and "robustness" in QML
means hardware noise, shot noise, or adversarial perturbations — never the
physically parameterized distribution shifts that collider deployment
actually presents (Sec. 2).

This paper asks a deliberately conditional question: *which claims about a
(quantum) event classifier remain justified when collider systematics shift
the deployment distribution — and under what experimentally available
information?* The framing separates three things that benchmarking
conflates: what is true about deployment performance, what is observable
about it, and what is certifiable from those observations. We formalize the
observable side as an information-set hierarchy — source data only (I0),
plus unlabeled target data (I1), plus n target labels (I2(n)) — and require
of any verdict that it be *fail-closed*: a claim is SUPPORTED or REFUTED
only when the declared information suffices at a declared error rate, and
UNRESOLVED otherwise. Heuristic signals may veto certification; they may
never grant it.

We instantiate this program end-to-end (Fig. 1) on the FAIR Universe
HiggsML Uncertainty benchmark — H→ττ classification with six physically
parameterized nuisance sources and official systematics tooling — with a
quantum-kernel classifier alongside matched classical baselines, and we
propagate every question to physics-level inference (signal-strength
intervals and their coverage). Five findings organize the paper. First,
quantum-kernel classifiers exhibit small but replicated degradations under
tau-energy-scale shifts and adverse nuisance combinations — the first
measurement of QML behavior under shape-level physical systematics —
though partition variance dominates most single-nuisance effects, a
caution we quantify rather than hide. Second, a label-free kernel-geometry
sensor predicts degradation magnitude out of environment; a matched-kernel
control shows the active ingredient is bandwidth and feature conditioning,
not quantumness — an honest negative for quantum-specific sensing that
yields a model-agnostic recipe. Third, an anytime-valid conditional auditor
certifies claims with empirically verified error control and measures the
label budget n* at which claims resolve — sharply margin-driven, from
hundreds of labels to fail-closed abstention. Fourth, classifier metrics
and inference validity decouple: dozens of replication-gated environments
combine a classifier indistinguishable from nominal with destroyed interval
coverage, including under normalization nuisances that no
feature-distribution signal can see. Fifth, deployed on real CMS Open Data
collisions, the framework certifies control-region claims, detects the
simulation-to-data shift, and refuses — by construction — to certify
event-level accuracy without labels.

None of this requires, assumes, or concludes quantum advantage. The study
was predeclared to be reportable under every outcome (registered
falsifiers, five-seed replication gates, logged protocol deviations), and
two of its own headline single-seed patterns did not survive replication —
we report both the corrected numbers and the correction process, because a
framework about trustworthy validation should itself be validated
trustworthily.

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

**Events and environments.** An event is a feature vector x ∈ R^d with label
y ∈ {0, 1} (signal = 1) and physical weight w (cross-section × luminosity /
N_generated). A nuisance vector θ indexes environments P_θ(x, y): feature-
level nuisances (energy scales, soft missing energy) transform x and
re-apply the event selection — so environments gain and lose events, which
we treat as physics, not as a nuisance of bookkeeping (partitions are
defined on pre-selection rows and carried through every environment) —
while normalization nuisances rescale weights only. Validation happens at
θ = 0; deployment at unknown θ.

**Frozen deployment.** A deployment is the tuple (features, model f,
calibration, decision threshold), fitted and frozen using θ = 0 training
and validation data only. Nothing is retuned per environment: every
evaluation below asks what happens to *this* deployment, not to a
hypothetical re-optimized one.

**Quantum kernels.** The quantum model is a support-vector classifier over
the fidelity kernel K_Q(x, x′) = |⟨φ(x)|φ(x′)⟩|², with |φ(x)⟩ prepared by a
ZZ feature map (one qubit per feature, entangling repetitions, a global
bandwidth scale on the encoded angles) acting on standardized inputs. Exact
(statevector), finite-shot (the compute–uncompute sampling law), and
hardware estimates of the same kernel are compared in Sec. 7.

**Claims and information sets.** A claim is a statement C(M, τ): M_T(f) ≥ τ
about a bounded target-environment metric, used here in the degradation
form τ = M_S − δ with M_S measured on labeled source validation data. The
auditor operates under a declared information set: I0 = {source data, f};
I1 = I0 ∪ {unlabeled target features}; I2(n) = I1 ∪ {n target labels};
I3 adds nuisance estimates (deferred here). Unsupervised accuracy
estimation is unidentifiable without shift assumptions, so I0/I1 can never
certify; this impossibility is a design input, not an inconvenience.

**Conditional validity.** For confidence bounds [L_t, U_t] on M_T valid
uniformly over the labeling time t, the verdict is SUPPORTED iff L_t ≥ τ,
REFUTED iff U_t < τ, and UNRESOLVED otherwise; heuristic sensors may demote
SUPPORTED to UNRESOLVED and may prioritize labeling, but cannot create
certification (fail-closed semantics, frozen before any experiment ran).
The first budget at which a claim leaves UNRESOLVED defines n*(θ, C).

## 4. Method

**4.1 Geometry observatory (I1).** For each kernel and environment we
compute label-free descriptors of the source Gram, an unlabeled target
Gram, and their cross Gram — spectra, effective rank, alignment, and the
squared maximum mean discrepancy MMD² in the kernel's RKHS. Descriptors are
*risk sensors*: their only powers are to flag shift and to veto
certification. Two structural facts are measured, not assumed: (i) at
finite target-sample size the sensor has a noise floor, which we estimate
from environments whose feature distribution is exactly nominal; (ii)
feature-distribution evidence is rate-free, hence blind to weight-only
normalization nuisances — the label-free channel that does carry that
information is rate/control-region monitoring, which the real-data case
study uses (Sec. 8).

**4.2 Conditional auditor (I2).** Labeled target draws are uniform with
replacement, so each per-event correctness indicator is an exact
Bernoulli(M_T) observation, and we track it with an empirical-Bernstein
confidence sequence (predictable plug-in construction). Time-uniform
validity makes n* a legitimate stopping time and makes one sequence
simultaneously valid for every threshold derived from it; the decision rule
of Sec. 3 then inherits per-claim Type-I control at level α by
construction, which we additionally verify empirically against simulation
truth (Sec. 6.4).

**4.3 Certification landscapes.** Sweeping claims (δ grid, including
adversarially false claims with τ at or above M_S) across environments and
replicated label streams yields the survival curves of n* over budgets —
the certification landscape whose axes the framework predicts: claim
margin, not model family, is the controlling variable.

**4.4 Acquisition.** Against the uniform baseline we test an
uncertainty-guided mixture proposal with bounded importance weights; the
rescaled stream stays in [0, 1], so validity is preserved by construction
and the comparison isolates pure variance effects. The result is negative
(uniform wins) and is reported as such.

**4.5 Physics-level inference.** A deployment-blind counting estimator —
per-model signal region chosen on source validation, nominal expectations
(s₀, b₀), pseudo-experiments drawn under shifted truth, μ̂ = (N − b₀)/s₀
with Gaussian 68.27% intervals — propagates classifier behavior to bias,
width, and empirical coverage. Its known limitations (single bin, no
profiling, shared-simulation expectations) are declared; profiled analyses
degrade more gracefully, and the demonstrated claim concerns *information*,
not the health of H→ττ physics.

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

We asked when a quantum event classifier can be trusted under the
experimental conditions that collider deployment actually presents, and we
answered conditionally, which is the only honest way to answer it. Under
nuisance-induced distribution shift, the quantum-kernel classifier behaves
like a competitive member of the model family it belongs to — small,
replicated degradations; no special fragility; no special robustness; and,
after a matched-kernel control, no quantum-specific advantage in label-free
shift sensing either. What the study establishes instead is a validation
discipline: an information-set-conditional, fail-closed auditor with
anytime-valid error control that certifies what the available evidence can
support, quantifies the label budget at which claims resolve, and abstains
— loudly and by construction — where evidence cannot reach, including on
real collision data where event-level truth does not exist. The
demonstration that healthy classifier metrics coexist with destroyed
physics-level coverage, precisely where feature-distribution evidence is
blind, is our strongest argument that such auditing should accompany any
learned classifier — quantum or classical — placed inside a physics
measurement. The framework's components are deliberately generic; nothing
in them is specific to H→ττ, to kernels, or to quantum models. Hardware
experiments bound where quantum estimation noise perturbs certificates
(only near claim boundaries, with device noise dominating shot noise ~9×
at practical depths), and a proposed hardware campaign would close the loop
by running the full certification pipeline on QPU-estimated kernels.

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
