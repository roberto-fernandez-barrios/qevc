# When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics and Quantum Estimation Uncertainty

**Draft v0.3 — 2026-08-11.** Rebuilt after the E12–E16 campaign per the
evidence; structure per research spec §33; language per the claims
discipline of §34. All numbers come from the audited result tables
(`docs/experiment_registry.md` campaign section; the ~172-value
number audit and the adversarial code audit are in
`docs/audits/post_campaign_audit_2026-08-11.md`; superseded first-run
tables are preserved under `*_v1_*.json` names). Remaining before submission: BibTeX bibliography and venue formatting at
LaTeX conversion (citation keys already in §2; sources in
`docs/novelty_matrix.md`).

---

## Abstract (draft)

Quantum machine-learning classifiers for collider physics face two
distinct validation gaps. Like their classical counterparts they are
validated on nominal simulation while deployment happens under
experimentally uncertain conditions — the collider's systematic
uncertainties. Unlike their classical counterparts, even *evaluating*
them is a statistical estimation problem: finite-shot and hardware-noisy
kernels make the deployed model itself uncertain. We ask when a
scientific claim made with a quantum event classifier is actually valid
when uncertainty enters simultaneously from collider deployment and from
quantum estimation, and we answer with an
information-set-conditional, fail-closed auditing framework whose
verdicts (SUPPORTED / REFUTED / UNRESOLVED) carry anytime-valid error
control. On the FAIR Universe HiggsML Uncertainty benchmark (H→ττ, six
parameterized nuisance sources) with a quantum-kernel classifier and
matched classical baselines we establish, and confirm on a provably
disjoint fresh holdout: (i) small but replicated degradations of the
quantum-kernel classifier under tau-energy-scale shifts and adverse
nuisance combinations — with a matched-kernel control showing nothing
quantum-specific in either classification or label-free shift sensing;
(ii) a label-free kernel-geometry sensor that generalizes out of the
development grid (48 unseen nuisance configurations, rank correlation up
to 0.65) while being *provably* blind to normalization nuisances — on
common random numbers the weight-only environments are byte-identical to
nominal; (iii) an exact extension of anytime-valid certification to
physics-weighted estimands via a one-sample reduction, whose measured
label cost is ×1.7 at matched margins and whose fail-closed behavior
hardens under the physical estimand; (iv) a formal identifiability
boundary — no I1/I2 evidence has any power against weight-only
nuisances — together with its resolution at information level I3
(control-region rates), whose practical resolving power we show is set by
the auxiliary evidence's template statistics (±10% on the ttbar scale at
our MC size); (v) propagation to signal-strength inference through three
inference levels, showing that a calibration-gate-validated profile
likelihood restores the coverage that a deployment-blind estimator loses
under scale and normalization shifts (0.63–0.67 from 0.00–0.59) at a
measured ×1.8–3.4 interval-width price — while stochastic soft-MET
smearing and multi-nuisance combinations defeat even the profiled
treatment (coverage 0.22 and 0.09), because their structure is not
representable by deterministic template morphing; (vi) a quantum-estimation-
uncertainty study showing that noise moves the deployed pipeline's own
reference points by up to 0.05 typically (0.14 in the worst
configuration), flipping fixed-reference verdicts at rates from 21%
(far-margin, 128 shots) to 0.4% (4096 shots) while false
certification stays below α in every accounting — noise changes what is
resolvable, never the validity of what is certified — including a
first end-to-end run of the full pipeline on 100%-QPU-estimated kernels;
and (vii) a fail-closed claims ledger on the complete public CMS Run2012
H→ττ collision dataset (126k selected events) that certifies
control-region claims, detects the simulation-to-data shift, and refuses
by construction to certify event-level accuracy without labels. Two of
our own headline patterns did not survive internal falsification — a
single-seed TES antisymmetry and the draw-fragility of
normalization-induced coverage damage — and are reported as corrections
with their mechanisms. None of our conclusions requires quantum
advantage; the framework treats quantum and classical models identically
and is fail-closed by design.

## 1. Introduction

Machine-learned event classifiers are standard components of collider
analyses, and quantum machine-learning (QML) classifiers are increasingly
proposed as successors. Both are validated the same way: on nominal
simulation, under the exact conditions the simulation happened to assume.
Deployment is different in two ways, one shared and one quantum-specific.

The shared gap is the collider's: the real experiment operates under
uncertain calibrations — tau and jet energy scales, soft missing-energy
activity, background normalizations — and the classifier validated at
θ = 0 is deployed at some unknown θ ≠ 0. The quantum-specific gap is
statistical: a quantum-kernel model's Gram matrix is not computed but
*estimated*, from finite shots on noisy hardware, so the deployed
pipeline — kernel, calibration, operating point — is itself a random
object. The QML-for-HEP literature addresses neither: robustness there
means hardware noise or adversarial perturbations on nominal data, never
physically parameterized deployment shift, and never the interaction of
the two (Sec. 2).

This paper asks a deliberately conditional question: *which claims about
a (quantum) event classifier remain justified when collider systematics
shift the deployment distribution and quantum estimation noise perturbs
the deployed pipeline — under what experimentally available
information?* We formalize the observable side as an information-set
hierarchy — source data only (I0); plus unlabeled target data (I1); plus
n target labels (I2(n)); plus experimentally available aggregates:
control-region rates, yields, and nuisance estimates (I3) — and require
of any verdict that it be *fail-closed*: SUPPORTED or REFUTED only when
the declared information suffices at a declared error rate, UNRESOLVED
otherwise. Heuristic signals may veto certification; they may never grant
it.

We instantiate this program end-to-end (Fig. 1) on the FAIR Universe
HiggsML Uncertainty benchmark with a quantum-kernel classifier alongside
matched classical baselines, propagate every question to physics-level
inference, and validate the resulting decision discipline from controlled
simulation through four provably disjoint data worlds to real CMS
collisions and QPU-estimated kernels. Three contributions organize the
paper.

**C1 — Information-conditional certification (I0→I3).** We prove an
exact extension of anytime-valid certification to physics-weighted
estimands (Theorem 1: a one-sample reduction maps every weighted ratio
claim onto the existing bounded-mean confidence sequence with zero added
slack; measured price ×1.7 median label-cost inflation, and a
fail-closed hardening — 536 of 7,054 certifications retreat to
abstention under the physical estimand). We prove where certification
must abstain: weight-only nuisances leave the feature distribution
*exactly* unchanged, so no I1 statistic and no I2 stream carrying
nominal weights has power beyond α (Proposition 2 — realized
computationally as byte-identical sensor values under common random
numbers); information level I3 restores identifiability with resolving
power set by the auxiliary evidence's template statistics (±10% on the
ttbar scale at our MC size — tighter claims stay UNRESOLVED,
fail-closed). The guarantees are measured, not asserted: false
certification ≤ α in every accounting across three independent worlds
and both estimand families (0.61%, 0.69%, 0.36% unweighted / 0.07%
weighted), and measured label costs sit within a factor 1.5–3.4 of the
Wald information floor — the near-boundary label explosion is
fundamentally statistical, not procedural slack. Supporting evidence: a
label-free sensor whose degradation-rank prediction generalizes out of
the development grid (rank, not magnitude, is the defensible claim) and
which serves as veto-only evidence; and a primary negative —
uncertainty-guided label acquisition loses to uniform sampling.

**C2 — Classifier metrics do not certify scientific inference.**
Classifier metrics and physics-level validity decouple: coverage
collapses at flat AUC, with the mechanism traced to signal-region
composition across worlds. A calibration-gate-validated profile
likelihood restores validity exactly where its nuisance model can
represent the shift — coverage 0.63–0.67 from 0.00–0.59, with fitted
nuisances tracking the true shifts at slope 0.99–1.00 and μ̂-sensitivity
∂μ̂/∂θ suppressed by one to two orders of magnitude — at a measured
×1.8–3.4 interval-width price; and it fails, predictably, where it
cannot (stochastic soft-MET smearing: tracking slope 0.25–0.50,
coverage 0.22; joint shifts under an additive morph: 0.09). The
fail-closed ledger runs end-to-end on the complete public CMS Run2012
H→ττ dataset (126k selected events): control-region claims certified
with MC-side statistics propagated, the simulation-to-data shift
detected at calibrated p = 0.005/0.001 in every observation draw, and
event-level accuracy refused by construction.

**C3 — Quantum estimation uncertainty is a claim-semantics problem.**
Finite-shot and hardware kernels make the deployed pipeline a random
object — refit, recalibration and threshold all functions of the
realized noise. We register two claim classes (deployment-relative vs
ideal-anchored), show that conditional-on-realization certification
keeps the marginal false-certification rate ≤ α for both (Proposition
3), and derive when verdicts are stable across realizations
(Proposition 4: margins beyond the measured reference movement;
deployment-relative margins cancel common-mode movement). The theory's
predictions are what the data trace: measured reference movement up to
~0.05 typically (0.14 worst) exceeds far margins at 128 shots and falls
below them at 4096, so ideal-anchored verdicts flip at 21% → 0.4% while
deployment-relative far-margin verdicts never flip at any budget — and
false certification stays below α in every accounting. A full-pipeline
run on 100%-hardware kernels (28-event train Gram plus cross-Gram on
ibm_marrakesh) behaves identically to its shot-only counterparts, with
device noise dominating the kernel error budget ~6×.

Throughout, the honest negatives stay central: no quantum advantage
appears anywhere — a matched classical kernel on identical features is
statistically indistinguishable as a classifier and at least as good as
a sensor — and the small within-world degradation patterns that
motivated early drafts did not survive the cross-world falsifier (two
further independent worlds flip their signs; §6.2). The framework's
value is exactly that such statements come out labeled as what they
are.

The study was predeclared to be reportable under every outcome
(registered falsifiers, five-seed replication gates, a frozen deployment
snapshot committed before the confirmatory draw, pre- and post-campaign
falsification audits with logged dispositions), and its registered
falsifiers fired five times (the confirmatory holdout's flagship-cell
arm, the rate-fit coverage check, the inference calibration gate twice,
and the cross-world degradation arm) while the falsification audits
forced two further corrections (an estimand label; an over-generalized
reading of the normalization-collapse result). One registered
re-analysis carried a bidirectional falsifier that was free to
*downgrade* a published verdict on real data; the verdict survived on
calibrated grounds instead (§8). We report the corrections and the
correction process — as methods, not as a contribution — because a
framework about trustworthy validation should itself be validated
trustworthily.

## 2. Related Work

*(Full prose; bibliography keys resolve against `docs/novelty_matrix.md`,
whose arXiv IDs were re-verified 2026-08-10. BibTeX at LaTeX
conversion.)*

**2.1 Quantum machine learning in collider physics.** Since the quantum
annealing Higgs classification of Mott et al. (Nature 550, 2017), the
QML-for-HEP program has produced variational and kernel classifiers for
ttH (Wu et al., PRR 3, 2021, arXiv:2104.05059), CEPC Higgs analyses
(Fadol et al., IJMPA 2024, arXiv:2209.12788), continuum benchmarks
(Terashi et al., CSBS 2021, arXiv:2002.09935; Maier et al., EPJ QT 2026,
arXiv:2510.13994) and unsupervised anomaly detection (Woźniak, Belis et
al., Commun. Phys. 2024, arXiv:2301.10780). All of these evaluate on
fixed nominal simulation; Alvi, Bauer and Nachman (JHEP 2023,
arXiv:2206.08391) provide the critical-validation counterpoint but do not
touch systematics. The closest work to ours, Ait Haddou et al. (PTEP
2026, arXiv:2511.15672), folds background-normalization uncertainty into
a final quantum-classifier limit — rate-type uncertainty entering
downstream only, with the classifier itself never audited under
distribution shift. To our knowledge no QML paper evaluates classifiers
under parameterized, shape-level collider systematics, and none uses the
FAIR Universe HiggsML Uncertainty benchmark.

**2.2 Quantum-kernel theory and trust.** Fidelity-kernel classification
(Havlíček et al., Nature 567, 2019, arXiv:1804.11326) comes with a
maturing trust literature: potential and limits of quantum kernels from
data (Huang et al., Nat. Commun. 2021, arXiv:2011.01938), inductive-bias
analyses (Kübler et al., NeurIPS 2021, arXiv:2106.03747), exponential
concentration as a failure mode (Thanasilp et al., Nat. Commun. 2024,
arXiv:2208.11060), bandwidth as the controlling hyperparameter (Canatar
et al., TMLR 2023, arXiv:2206.06686), noise-aware NISQ kernels (Wang et
al., Quantum 2021, arXiv:2103.16774), and benchmark scrutiny (Schnabel &
Roth, QMI 2025, arXiv:2409.04406). We consume this theory as design
discipline — our bandwidth-limited map and the matched-kernel control
descend from it — and add what it lacks: the deployment-shift and
certification questions.

**2.3 QML validity, robustness, and monitoring.** Certification in the
quantum literature means hypothesis-test certificates for devices (Weber
et al., npj QI 2021, arXiv:2009.10064), formal verification of circuits
(Guan et al., CAV 2021, arXiv:2008.07230), out-of-distribution guarantees
for learning dynamics (Caro et al., Nat. Commun. 2023, arXiv:2204.10268),
and conformal prediction for quantum models (Park & Simeone, IEEE TQE
2024, arXiv:2304.03398; Spencer et al. 2026, arXiv:2511.18225, which
adapts to hardware drift). Q-SafeML (2026, arXiv:2509.04536) monitors
distributional drift of quantum classifiers, and Kempkes et al. (MLST
2026, arXiv:2504.03315) study underdetermination in parameterized
circuits. None of these connects to physically parameterized deployment
shift, information-set conditioning, or a downstream scientific
estimand; none treats the estimated kernel as part of the *claim* being
certified, as our Sec. 7 does.

**2.4 Systematics-aware machine learning in HEP.** The classical
community has long confronted nuisance-dependent deployment: adversarial
decorrelation (Louppe et al., NeurIPS 2017, arXiv:1611.01046),
inference-aware learning (INFERNO — de Castro & Dorigo, CPC 2019,
arXiv:1806.04743), uncertainty-aware networks (Ghosh, Nachman &
Whiteson, PRD 2021, arXiv:2105.08742), cautionary analyses of
decorrelation itself (Ghosh & Nachman, EPJC 2022, arXiv:2109.08159),
neural simulation-based inference at experiment scale (ATLAS NSBI, Rep.
Prog. Phys. 2024/25, arXiv:2412.01600), and searches for hidden
systematics sensitivity in networks (Flek et al. 2026, arXiv:2605.07470).
The FAIR Universe program (arXiv:2410.02867; results overview
arXiv:2509.22247) supplies the benchmark infrastructure we build on —
parameterized nuisances with official semantics and a μ-inference
protocol — but scores empirically, without certified auditing, and drew
no quantum entries. Our E15 sits deliberately downstream of this line:
we do not propose a better systematics-aware learner; we quantify which
*inference* treatments restore claim validity for a *frozen* learner.

**2.5 Certification, shift, and label-efficient evaluation.** Outside
physics, unsupervised accuracy estimation under shift is known to be
impossible without assumptions (Garg et al., ICLR 2022, arXiv:2201.04234)
and bounded only under uncheckable conditions (Rosenfeld & Garg, NeurIPS
2023, arXiv:2306.00312) — the impossibility our I0/I1 levels encode by
construction. Label-efficient evaluation (active testing — Kossen et al.,
ICML 2021, arXiv:2103.05331; LURE — Farquhar et al., ICLR 2021,
arXiv:2101.11665; prediction-powered inference — Angelopoulos et al.,
Science 2023, arXiv:2301.09633; Zrnic & Candès, ICML 2024,
arXiv:2403.03208) optimizes estimator variance but carries no shift
semantics or claim verdicts. Anytime-valid inference (Waudby-Smith &
Ramdas, JRSS-B 2024, arXiv:2010.09686) supplies our statistical backbone,
as it does for sequential risk monitoring (Podkopaev & Ramdas, ICLR 2022,
arXiv:2110.06177), fairness auditing by betting (Chugg et al., NeurIPS
2023, arXiv:2305.17570), and e-process LLM evaluation (CELEUS 2026,
arXiv:2606.20820). Weighted-conformal and PAC prediction sets under
covariate shift (Tibshirani et al., NeurIPS 2019, arXiv:1904.06019; Park
et al., ICLR 2022, arXiv:2106.09848) target set coverage rather than
claim verdicts; fail-closed deployment gating (Kim 2026,
arXiv:2606.24996) shares our semantics without the information-set
hierarchy or a scientific downstream task. The nearest methodological
neighbor, Chen & Weng (2026, arXiv:2606.24038), certifies sim-to-real
transfer in robotics with betting e-processes — no information-set
conditioning, no physics inference, no estimation-noise axis. Our
statistical additions to this line are the exact one-sample reduction for
weighted ratio claims (Sec. 4.3) and the worst-case-over-nuisance-box
composition with rate evidence (Sec. 4.4); our template-statistics
treatment follows Barlow & Beeston, and our toy conventions the standard
unconditional-ensemble practice of profile-likelihood analyses.

**2.6 The gap.** No prior work combines quantum models, physically
parameterized collider systematics, information-conditional
error-controlled certification, and physics-level inference — and none
poses quantum estimation noise as a certification problem in which the
deployed pipeline is itself the random object. That combination, each
axis of which is individually grounded in the literatures above, is this
paper's contribution.

## 3. Problem Formulation

**Events and environments.** An event is a feature vector x ∈ R^d with
label y ∈ {0, 1} (signal = 1) and physical weight w. A nuisance vector θ
indexes environments P_θ: feature-level nuisances (energy scales, soft
missing energy) transform x and re-apply the event selection — so
environments gain and lose events, which we treat as physics (partitions
are defined on pre-selection rows) — while normalization nuisances
rescale weights only, leaving P_θ(X) = P_0(X) *exactly*. Validation
happens at θ = 0; deployment at unknown θ.

**Frozen deployment.** A deployment is the tuple (features, model f,
calibration, decision threshold), fitted and frozen on θ = 0 training and
validation data. Nothing is retuned per environment. Under finite-shot or
hardware kernel estimation the deployment is additionally a *random*
tuple: each estimation realization ω owns its own refit, recalibration,
and refrozen threshold — write f̃_ω for the realized deployment and f⋆
for its ideal exact-kernel counterpart. For such estimated deployments
two claim classes must be distinguished (they are conflated at the
community's peril): **deployment-relative**, C_dep(ω):
M_T(f̃_ω) ≥ M_S(f̃_ω) − δ, holding the realized pipeline to its own
recalibrated reference; and **ideal-anchored**, C_ideal(ω):
M_T(f̃_ω) ≥ M_S(f⋆) − δ, holding it to the ideal deployment's. Section 7
proves that certification validity survives deployment randomness for
both classes and shows which class is stable.

**Quantum kernels.** The quantum model is a support-vector classifier
over the fidelity kernel K_Q(x, x′) = |⟨φ(x)|φ(x′)⟩|², with |φ(x)⟩
prepared by a ZZ feature map (one qubit per feature, entangling
repetitions, a global bandwidth scale) on standardized inputs. Exact
(statevector), finite-shot (the compute–uncompute sampling law, sampled
independently per Gram evaluation as a device would), and hardware
estimates of the same kernel are compared in Sec. 7.

**Claims, estimands, and information sets.** A claim C(M, τ): M_T(f) ≥ τ
concerns a bounded target-environment metric, used in the degradation
form τ = M_S − δ. Unweighted per-event correctness (D-014) and
physics-weighted estimands (D-019) are both audited: weighted accuracy
A_w = Σ w_i c_i / Σ w_i and the class-conditional physics quantities
TPR_w (weighted signal efficiency) and TNR_w (weighted background
rejection). Weights are label-adjacent in this benchmark (the per-event
weight identifies the generating process), so they are revealed only at
labeling time — granting them earlier would leak labels into I1. The
information sets are I0 = {source data, f}; I1 = I0 ∪ {unlabeled target
features}; I2(n) = I1 ∪ {n target labels (with their weights)}; I3 =
I2(n) ∪ {control-region counts and yields from unlabeled target data,
nuisance estimates θ̂ derived from them, with declared uncertainties}.

**Proposition 2 (weight-only unidentifiability at I0–I2; I3
restoration).** *For weight-only θ (P_θ(X) = P_0(X), correctness process
unchanged): (i) any I1 statistic has identical law under θ and 0, so any
size-α test has power exactly α; (ii) the same holds at I2 with nominal
weights; (iii) hence any claim whose truth value differs between θ and
0 — rate claims, the true-weighted metric A_w^{(θ)} — is unresolvable at
I0–I2, and a fail-closed auditor must return UNRESOLVED; (iv) a
control-region count N ~ Poisson(λ(θ)) with λ(θ) ≠ λ(0) has non-trivial
power — I3 restores identifiability precisely because rate evidence
enters the information set.* Proof: equality of sampling laws applied to
the SUPPORTED event; the error-control requirement; standard Poisson
testing (registered before any I3 run;
`docs/weighted_certification_spec.md` §4b). **Corollary.** The power
that (iv) restores is bounded by the auxiliary evidence's own
statistics: with template-variance σ²_c = Σ_g (relerr·λ)², rate scales
are identified only to the order of the template noise, and tighter
claims remain UNRESOLVED — fail-closed degradation, measured in §6.5.
The campaign realizes (i) computationally: under common random numbers
the weight-only environments' sensor values are byte-identical to
nominal's (Fig. 3).

**Conditional validity.** For confidence bounds [L_t, U_t] on the claim
metric valid uniformly over labeling time t, the verdict is SUPPORTED iff
L_t ≥ τ, REFUTED iff U_t < τ, UNRESOLVED otherwise; heuristic sensors may
demote SUPPORTED to UNRESOLVED and may prioritize labeling, but cannot
create certification. The first budget at which a claim leaves UNRESOLVED
defines n*(θ, C), a legitimate stopping time under time-uniform validity.

## 4. Method

**4.1 Geometry observatory (I1).** For each kernel and environment we
compute the label-free MMD² between a source anchor Gram and unlabeled
target draws (common random numbers across environments). The sensor
family is frozen — MMD² of the quantum kernel and of the matched
classical RBF kernel on the identical 8 features — and its only powers
are to flag shift and to veto certification. Its veto floor is the null
distribution of MMD² over independent nominal draws from a dedicated
auditor-development role (the max-over-weight-only rule of the
development phase degenerates under common random numbers, where
weight-only environments are identical to nominal — measured, disclosed,
and re-based).

**4.2 Conditional auditor, unweighted (I2).** Labeled target draws are
uniform with replacement, so per-event correctness is an exact
Bernoulli(M_T) stream tracked by a predictable plug-in
empirical-Bernstein confidence sequence; the decision rule inherits
per-claim Type-I control at level α by construction and is verified
empirically against simulation truth.

**4.3 Weighted certification (I2).**

**Theorem 1 (exact weighted anytime-valid certification).** *Let
(c_i, u_i) be IID with c_i ∈ {0,1}, u_i ∈ [0, w_max] for a predeclared
nonrandom bound w_max, and E[u] > 0; let R = E[u·c]/E[u] and, for a
claim R ≥ τ, define Z_i(τ) = (u_i(c_i − τ) + τ·w_max)/w_max. Then
(a) Z_i(τ) ∈ [0,1] and R ≥ τ ⟺ E[Z(τ)] ≥ τ — an equivalence, not an
approximation; (b) any time-uniform level-(1−α) confidence sequence for
a bounded mean, applied to the Z-stream with the fail-closed rule,
satisfies P(∃n: SUPPORTED issued ∧ R < τ) ≤ α simultaneously over all
stopping rules; (c) the unweighted system is the special case u ≡ 1,
w_max = 1.* Proof: boundedness and the equivalence are four lines of
algebra using E[u] > 0; a false certification then requires a coverage
violation of the CS at some n, an event of probability ≤ α by
time-uniformity; substitution gives (c)
(`docs/formal_results.md`). The reduction adds *zero slack of its own*:
the label price of weighting is paid in the variance of Z (effective
sample size Σw²/(Σw)²), never in validity. Here u = w for A_w;
u = w·1[y=1] for TPR_w; u = w·1[y=0] for TNR_w; w_max comes from process
metadata and the official nuisance clip ranges. Balanced accuracy, a
ratio-of-ratios, gets only a conservative component bound; we audit the
components (the physics quantities) directly instead.

**4.4 I3: rates and worst-case reweighting.** Normalization scales are
estimated by a joint fit to disjoint control-region counts
(ttbar-enriched tail of the scalar-sum-p_T spectrum, and its complement),
with template-statistics variance included Barlow–Beeston-style — a
pure-Poisson fit failed its registered Monte-Carlo coverage falsifier by
mistaking template noise for scale shifts, and the amended likelihood is
coverage-validated at both the reporting and the chain's α levels. Rate
claims |s_p − 1| ≤ x resolve fail-closed against profile-likelihood-ratio
intervals; the diboson scale, with no viable control region in this
feature space, stays UNRESOLVED by construction. True-weighted claims
A_w^{(θ)} ≥ τ are audited by reweighting the labeled stream at every
corner of the (s_ttbar, s_diboson, s_bkg) confidence box and taking the
worst case; the α budget splits between the box and the corner-wise
confidence sequences, and the corner reduction is exact because the
estimand is monotone (Möbius) in each scale.

**4.5 Certification landscapes.** Sweeping claims (δ grid, including
adversarially false claims) across environments and replicated label
streams yields the survival curves of n* — the certification landscape
whose controlling variable is claim margin, not model family.

**4.6 Physics-level inference.** Three levels per environment and model:
L1, the deployment-blind counting estimator (single signal region,
nominal beliefs) — deliberately naive, kept as the baseline; L2, a
score-binned Poisson profile likelihood with per-process template
morphing anchored at the official ±1σ/±2σ systematics grid, all six
nuisances profiled, intervals from the profile likelihood ratio, and
pseudo-experiments drawn as an unconditional ensemble (auxiliary
constraint centers fluctuated around truth); L3, the same machinery with
the actually-shifted nuisance family omitted from the profile — realistic
misspecification. L2 must pass a nominal-environment coverage calibration
gate *per model* before any shifted-environment number is interpreted;
the gate fired twice during development (an ensemble error and a
numerical-conditioning failure), blocked the grid both times, and one
model (the scale-trained tree) remains gate-excluded and is reported as
such.

**4.7 Acquisition.** Uncertainty-guided label acquisition with bounded
importance weights loses to uniform sampling (median n* ratio 1.55); the
negative result stands and simplifies practice.

## 5. Experimental Design

### 5.1 Data and worlds

FAIR Universe HiggsML Uncertainty (Zenodo 15131565; 220,099,101 events
verified at ingestion; the official normalization no-op defect found,
worked around, and reported upstream). Four provably disjoint 300k-event
worlds drawn from the benchmark: the development world (seed 101 — the
only parquet draw of the development era), the confirmatory world
(seed 121, drawn after the deployment freeze), and two additional
variance-characterization worlds (seeds 131, 141; E17). Disjointness is
an artifact, not a claim: every draw archives its global row indices with
SHA-256s, and each new draw records overlap zero against every prior
archive. Each world carries a raw-row five-role partition (train 40%,
source_val / nominal_test / auditor_dev / final_eval 15% each); both
`final_eval` roles of the development and confirmatory worlds remain
sealed and have never been read. Level II uses the complete public CMS
Run2012B+C TauPlusX H→ττ samples (126,164 selected collision events at
11,467 pb⁻¹) with mirror MC re-weighted to full luminosity.

### 5.2 Models and budgets

Tier A trains on a matched, stratified 2000-event budget (the
quantum-feasible scale); tier B on the full 110k train role. Frozen
hyperparameters (E01 random-search under comparable budgets, revived
verbatim from the deployment snapshot):

| Model | Features | Frozen hyperparameters |
|---|---|---|
| QK-SVC | 8 (D-011) | C=1.0; ZZ map, reps 2, scale 0.5, linear entanglement |
| RBF-SVC (matched control) | same 8 | C=30.0, γ=0.3 |
| RBF-SVC | all 28 | C=1.0, γ=0.3 |
| XGBoost (A) | all 28 | 400 trees, depth 8, lr 0.03 |
| LightGBM (A) | all 28 | 400 trees, 63 leaves, lr 0.03 |
| XGBoost (B, 110k) | all 28 | 800 trees, depth 4, lr 0.1 |

Every model shares one training protocol: class-balanced mean-one
weights, Platt calibration on `source_val`, balanced-accuracy-optimal
frozen threshold. Quantum kernels are exact statevector unless the
experiment studies estimation (E09/E10/E16: binomial finite-shot law,
D-007, and IBM Open-plan hardware).

### 5.3 Environments, claims, and information sets

Six nuisance families (TES, JES, soft-MET smearing, ttbar/diboson/bkg
normalizations) over the frozen grid: 28 unique nuisance points evaluated
as 41 environment datasets (stochastic soft-MET carries three seeds;
seed is part of environment identity). Claims are degradation-form
M_T ≥ M_S − δ with the frozen grid δ ∈ {−0.01, −0.005, 0, 0.02, 0.05,
0.10} — the negative deltas are adversarially false by construction —
audited at α = 0.05 per claim, n_max = 3,000 (20,000 for landscape
studies), 20 audit-seed replications per cell, under the information-set
discipline of §3 (I1 sensors veto-only). Physics inference uses the
D-015 counting estimator and the D-023 profile likelihood over the frozen
score with μ ∈ {0.5, 1, 1.5, 2, 3}.

### 5.4 Protocol discipline and compute

A frozen deployment snapshot (hyperparameters, features, feature map,
calibration and threshold procedures, claim grid, sensor family,
environment grid, physics estimator, statistical protocol) was committed
*before* the confirmatory subset was drawn; campaign rules quarantine
confirmatory rows from all development; falsification audits ran before
and after the campaign and before submission, with every finding
dispositioned in the open (`docs/audits/`). Statistical protocol per the
predeclared SAP and its logged amendments; superseded run tables are
preserved, never overwritten. Every experiment is registered with a
frozen falsifier before execution; registered falsifiers fired five times
in this program (E02R, E12 arm (e), E14 v1, E15 gate, E17 arm (b)) and
were obeyed each time. Compute is a single workstation: the full
simulation program re-executes from one clean commit in under a day
(largest single run: profiled inference, 5.4 h; confirmatory holdout
627 s; both variance worlds 549 s; weighted-certification battery 59 s),
plus two IBM Open-plan QPU jobs (276 s and 200 s charged) with raw counts
archived.

## 6. Results

### 6.1 Nominal performance, the matched control, and what "absolute"
numbers mean (E01, E02R, E12)

Matched 2000-event budget, five-seed replication: QK-SVC 0.848 ± 0.022 —
above full-feature RBF in 4/5 seeds and above linear SVC in 5/5,
consistently below tuned trees (QK − XGB = −0.035 ± 0.013, negative in 5/5 seeds). The
matched-kernel control — RBF on the identical 8 features — reaches
0.859 ± 0.016, statistically indistinguishable from the QK-SVC: the
earlier "QK above RBF" contrast was a feature-set effect, not
quantumness. The fresh holdout confirms the *paired* structure exactly
(QK − XGB = −0.039; QK − RBF8 = −0.008, both within the replication
bands) while exposing a finding about absolute numbers: every model's
absolute weighted AUC sits 0.067–0.098 lower on the fresh draw, with
unweighted AUCs essentially unchanged (0.839–0.845 / 0.875–0.877 for the
trees across both worlds and both model sets). The mechanism is the
benchmark's heavy-tailed signal weights (max/mean ≈ 420–440 across
draws; effective sample
size ratio 0.005, i.e. ≈ 46 effective signal events per 41k-event test
role): *absolute physics-weighted metrics carry subset-draw variance of
order ±0.05 (bootstrap CI half-widths 0.04–0.09) that partition-level
replication structurally understates.*

Two further worlds (seeds 131, 141; E17) turn that inference into a
measured cross-world fact: over four independent worlds the between-world
standard deviation of absolute weighted AUC is 0.030–0.050 per model
(ranges up to 0.121), while QK − XGB stays negative in all four worlds
(−0.022 to −0.076) and QK − RBF8 changes sign across worlds — the
"statistically indistinguishable" reading is world-robust. What
replicates everywhere is the *paired ordering* against tuned trees and
the error control; what does not is anything absolute. This is no longer
a caution but a quantified warning for matched-budget benchmark practice:
the development world's re-partition variance understates the total
by about a factor of two (contrast std 0.023 across worlds vs 0.013
across partitions).

### 6.2 Behavior under systematics (E02, E02R, E12, E17; Fig. 2)

Within the development world, TES down-shifts degrade the QK-SVC in 5/5
seeds (+0.0024 ± 0.0010 at −2σ; the up-shift arm does not replicate) and
the adverse combination degrades it in 5/5 seeds (+0.025 ± 0.024); both
signs reproduce on the confirmatory holdout (+0.0011; +0.0081). The two
additional worlds then **triggered the registered cross-world
falsifier**: in one the adverse combination *improves* the QK-SVC
(−0.0090) and in the other the TES down-shift does (−0.0050). The
corrected claim is therefore scoped honestly: the small degradations are
*within-world replicable but draw-dependent across worlds* — at their
|ΔAUC| ≈ 0.001–0.01 scale they sit below the between-world variability
of the paired contrasts themselves (±0.02), and no world-robust
directional degradation claim survives at this magnitude. This
correction sharpens the paper's thesis rather than weakening it:
benchmark deltas of this size, however internally replicated, do not
transfer across data draws — deployment claims need certification, not
extrapolation. Weight-only nuisances leave the feature distribution
unchanged exactly; their weighted-AUC effect is at the 4·10⁻⁴ level
(uniform background scaling exactly zero).

### 6.3 The label-free sensor: out-of-grid generalization and exact
blindness (E03, E04v2, E04v3; Figs. 4 and 4b)

On the development grid, the frozen MMD² sensors predict replicated
degradation out-of-environment (quantum ρ_S = 0.56 own-model, 0.68
transfer; matched rbf8 0.73/0.60 — the matched classical sensor is at
least as good, so sensing is not quantum-specific). The campaign's
generalization test evaluates the frozen sensors on 48 out-of-grid
environments per world — off-grid single-nuisance values and 24
multi-nuisance draws from the official priors — with the sensor archived
before any target existed. Pooled out-of-grid rank correlation is
positive in both worlds and for both sensors (best: quantum→own 0.65,
p < 10⁻⁴; secondary world 0.22–0.62 with world-dependent detail (the rbf8→own
fold at 0.22, n.s.); JES
folds sit at the noise floor, as their degradations do). Magnitude
calibration (leave-one-family-out isotonic) is rough — MAE 0.0005–0.012
against target means 0.0003–0.012, at the high end exceeding the target
mean itself: *rank prediction generalizes; magnitude prediction does
not*, and we claim only the former. Blindness to normalization nuisances
is exact under common random numbers (weight-only environments are
byte-identical to nominal — the proposition of Sec. 3 realized
computationally), which also degenerates the development-era veto floor;
the operative floor is re-based on independent nominal draws
(null σ ≈ 7·10⁻⁵ for the quantum sensor, 1.6·10⁻⁴ for rbf8), under which 4–8 of 48 out-of-grid environments alarm —
only the soft-MET family and the strongest prior draws, consistently
across worlds and kernels.

### 6.4 Conditional certification: unweighted and physics-weighted
(E05, E13; Fig. 5 data)

Unweighted (development world): across 19,680 claim-streams, empirical
false certification 0.61% ≤ α = 5% on genuinely-false claims (an
independent stream re-draw of the same arm in the weighted study gives
0.56% — seed variation, both ≤ α), false refutation 0.03%, with 98% of
near-boundary false claims ending UNRESOLVED at n = 3,000. On the confirmatory holdout the corresponding
rate over non-vetoed false-claim streams is 0.69% ≤ α (the fresh
partition's veto set is disclosed as degenerate under CRN; streams are
shared across the δ grid, so pooled denominators are correlated ≈6:1 —
per-claim α is unaffected). A dedicated fresh-world replication (E19)
closes the "one-world validity" question: the confirmatory world's
archived deployment scores — certified byte-identical against a full
re-derivation of the frozen deployment before any audit ran — give false
certification 0.36% unweighted and 0.07% weighted on fresh audit
streams. Across three independent accountings and both estimand
families, every measured false-certification rate is below α.

Weighted (the campaign's extension): the one-sample reduction passes its
predeclared Monte-Carlo battery — time-uniform coverage on uniform,
benchmark-derived, and heavy-tailed weight profiles; worst
false-certification cell 1.5% against an 8.3% slack; and an adversarial
optional-stopping stress in which a naive Wald rule falsely certifies
27.8% of the time while the confidence sequence holds at 0.0%. On the
benchmark, with weights revealed only at labeling time and the estimand
verified computationally (weight-only environments give byte-identical
weighted accuracies), weighted false certification is 2/8,580 = 0.02%
and class-conditional (TPR_w/TNR_w) false certification 0/4,700. The
measured price of the physical estimand: median n*_w/n*_unw = 1.66
(IQR 1.11–3.00) on identical draws, and a fail-closed hardening — 536
streams retreat from SUPPORTED to UNRESOLVED, while 1 stream flips
SUPPORTED→REFUTED: the weighted and unweighted estimands genuinely
disagree about deployment health, sharpening the finding that *the metric
named in the claim changes which claims are at risk*. The balanced-
accuracy component bound is vacuous at these scales (its ratio-CS radius
dwarfs the tested margins); we audit the components — the physics
quantities — directly.

### 6.5 Information level I3: what restores identifiability, and what it
costs (E14)

The claim × information-set table is the campaign's conceptual center:

| Claim | I0 | I1 | I2(n) | I3 |
|---|---|---|---|---|
| classifier performance (unweighted) | UNRESOLVED | veto only | resolvable (fc 0.61%) | resolvable |
| classifier performance (weighted, nominal estimand) | UNRESOLVED | veto only | resolvable (fc 0.02%) | resolvable |
| true weighted performance under θ_norm | UNRESOLVED | UNRESOLVED (proposition) | wrong estimand | resolvable, worst-case over θ̂ box |
| normalization / rate claims | UNRESOLVED | UNRESOLVED (proposition) | UNRESOLVED (θ-invariant stream) | resolvable in principle; resolution set by template quality; s_diboson unidentified |
| physics-level validity | UNRESOLVED | UNRESOLVED | insufficient (decoupling, §6.7) | requires inference consuming θ̂ (§6.7) |

Three measured refinements. (1) *Auxiliary evidence quality bounds I3.*
A pure-Poisson control-region fit failed its registered coverage
falsifier (ŝ_ttbar biased +0.07 with zero coverage): analyst templates
carry Monte-Carlo statistics (2.4% in the ttbar-enriched region at our
sample size) that a pure-Poisson likelihood misreads as scale shifts. The
Barlow–Beeston-amended fit is coverage-valid — and honest about its
resolution: s_ttbar ±10%, s_bkg's interval saturating the official clip
range in 99% of replications ("no information beyond the prior clip").
Predeclared tight bands therefore stay UNRESOLVED, fail-closed; only
clear violations refute (12/400 refutations of the genuinely false
|s_tt − 1| ≤ 0.02 claim at ttbar_scale = 1.04, zero false
certifications). (2) *The wrong-estimand risk at I2 is structural but
unrealized at official magnitudes:* the gap between the true-weighted and
nominal-weighted estimands is ≤ 0.003 at official normalization shifts —
below certification resolution at n = 3,000 — so the I2-nominal auditor,
audited against the true estimand, false-certifies 0/360 while the I3
worst-case auditor is strictly more abstinent. (3) *Feature shifts
contaminate rate evidence:* under the adverse combination, selection
migration biases the control-region fit (ŝ_bkg −0.012, outside its clip
coverage) — the principled joint treatment is profiling (§6.7), and we
say so rather than overclaiming CR evidence.

### 6.6 Label efficiency (E06, E07; Figs. 5–6)

n* is sharply margin-driven: ~180 labels at |margin| ≥ 0.08; ~870 at
0.04–0.08; ~13,000 at 0.01–0.02; below 0.01 the fail-closed UNRESOLVED
region dominates even at 20,000. Those costs are close to fundamental:
against the Wald information yardstick log(1/α)/KL(Ber(p) ‖ Ber(τ)) —
a floor for *any* sequential procedure with type-I error ≤ α — the
measured median stopping times sit a factor 2.07 above the bound overall
(IQR 1.56–2.97), from ×1.46 at large margins to ×3.35 near the boundary
(518 resolved cells; Fig. 6). The near-boundary label explosion is
fundamentally statistical — the information floor itself diverges as
KL ≈ 2·margin² — and the confidence sequence's own overhead is a bounded
small factor; no minimax optimality is claimed. Uncertainty-guided
acquisition loses to uniform (median n* ratio 1.55; better in 10% of
cells; Fig. 6) — a primary negative result that simplifies practice.
Principled variance-reduction estimators (LURE-style control variates,
stratified without-replacement sampling) remain registered as the
candidate second round before the question is declared closed.

### 6.7 Physics-level validity: decoupling, its mechanism, and the price
of restoring it (E08, E12, E15; Figs. 7 and 7b)

With the deployment-blind counting estimator (nominal coverage verified
at 0.68 in both worlds), classifier metrics and inference validity
decouple: on the development world, 73 replication-gated cells combine
ΔAUC consistent with zero with coverage < 0.633; on the confirmatory
holdout, 74 point-estimate cells reproduce the phenomenon, with 18/32
tes/jes cells collapsing to coverage exactly 0.0 at flat AUC. The
confirmatory draw also *corrected our reading* of the
normalization-driven cells: their collapse is signal-region-composition-
dependent — it reproduces decisively for the models whose SRs retain
ttbar/diboson content (the full-feature RBF-SVC: 10/12 normalization
environments below 0.633, down to 0.008; scale-trained tree: 0.51–0.59)
and vanishes for the models whose fresh-draw SRs hold little of either.
The mechanism — coverage is destroyed by yield shifts invisible to
ranking metrics, when and only when the SR composition exposes them — is
thereby sharper than the development-world summary, and precisely
documents that classifier-level evidence does not carry the information
that protects inference.

The three-level inference study then asks the reviewer-proof version of
the question: does the decoupling survive a physically defensible
inference chain? L2 — a score-binned profile likelihood with all six
nuisances profiled, validated by a per-model nominal calibration gate
(A:qksvc 0.682, A:rbf_svc 0.680, A:xgboost 0.658 pass; the scale-trained
tree overcovers marginally at 0.717 and is gate-excluded from every
shifted-environment claim) — cleanly splits the answer by nuisance type.
Where the nuisance model matches the physics, profiling restores
validity: mean coverage rises from 0.000/0.002 (counting) to 0.653/0.629
for TES/JES and from 0.27–0.59 to 0.67 for the three normalization
scales; in the flagship cell (TES −2σ, A:xgboost) coverage goes
0.000 → 0.719 with the fitted TES pull −2.007 — the profile *finds* the
true shift — and μ̂ bias 0.004. The restoration is bought with
statistical power: L2 intervals are ×1.8–3.4 wider than the counting
estimator's (1.74–4.76 vs 0.99–1.38 in μ units at these
signal-to-background ratios). Omitting the actually-shifted family from
the profile (L3, the realistic misspecification) re-collapses TES/JES
coverage to 0.000/0.073 — in the flagship cell μ̂ biases to −5.9 with a
3.5-times-narrower interval, the confident-and-wrong failure mode —
while small normalization shifts remain absorbable by the remaining
freedom. And two nuisance families defeat even the correctly-configured
profile: stochastic soft-MET smearing (L2 coverage 0.217; the fit leaves
the soft-MET parameter near 0.1 when truth is 5 GeV, because a
deterministic, seed-averaged template morph cannot represent a specific
smearing realization, and μ̂ absorbs the difference: bias −6.0 at width
0.066) and the multi-nuisance combinations (L2 coverage 0.089; the
additive morph misses real cross-terms — both failure modes predeclared
in the run's interpretation notes). The answer to the registered
question is therefore affirmative without having been forced: *a
classifier can look stable while physics inference remains invalid even
after a reasonable profiled treatment — precisely for nuisances whose
structure the inference model cannot represent* — and, symmetrically,
the information that restores validity (a correctly-specified constraint
on the shifted nuisance) is now identified and priced.

The mechanism is quantified by the nuisance sensitivities ∂μ̂/∂θ,
computed by finite differences over the archived grid (SAP §1.2). The
counting estimator's μ̂ moves by +5 to +10 μ-units per σ of TES shift
(model-dependent); full profiling suppresses this to +0.1 to +0.4 — one
to two orders of magnitude — while the fitted nuisance tracks the true
shift with slope 0.99–1.00 for TES/JES and the normalization scales.
For stochastic soft-MET the tracking slope is only 0.25–0.50: the fit
structurally under-recovers the shift, which is *why* profiling fails
there. And with the shifted family omitted (L3), sensitivities revert to
the counting estimator's scale (+5 to +9 μ/σ for TES) — the profile's
protection is exactly as good as its nuisance model.

## 7. Quantum Realism: estimation uncertainty as a certification problem

The claim semantics of Section 3 (C_dep vs C_ideal) carry two formal
consequences, both deliberately elementary — their content is the
semantics, and the fact that this section's measurements instantiate
them.

**Proposition 3 (validity under estimated deployments).** *If the
certification procedure, applied to the realized pipeline's own label
stream, controls false certification at level α conditionally on every
realization ω — which is Theorem 1 at fixed ω, the claim threshold being
a constant given ω — then the marginal false-certification rate over
deployment randomness satisfies P(false certification) =
E_ω[P(false certification | ω)] ≤ α, for both claim classes.* Proof:
tower property. Deployment randomness moves which claims are *true* and
*resolvable* (through τ(ω) and M_T(f̃_ω)); it never touches the validity
of what is certified. This is where the quantum setting genuinely
differs from the classical one: classical training randomness is
seed-controllable, while estimated kernels make the deployed object
physically random — irreducibly so on hardware — and the certification
layer must be, and is, indifferent to that.

**Proposition 4 (verdict stability under bounded movement).** *With
signed movements ΔM_T(ω), ΔM_S(ω) of the realized deployment's target
and source metrics, the realized margin obeys |m(ω) − m⋆| ≤ |ΔM_T| for
C_ideal and |m(ω) − m⋆| ≤ |ΔM_T − ΔM_S| for C_dep; if the ideal margin
exceeds the relevant movement bound and the audit resolves, the realized
verdict equals the ideal one. When movement is common-mode (refit and
recalibration shift source and target together), C_dep margins cancel it
while C_ideal margins absorb ΔM_T in full — deployment-relative claims
are structurally the stabler class.* Proof: triangle inequality plus the
determinism of the fail-closed rule given the CS bounds
(`docs/formal_results.md`). The movement magnitudes are *measured, not
derived* — per-budget distributions from the 30 archived noisy
deployments (Fig. S16) — and they predict what follows: at 128 shots the
measured reference movement (typically up to ~0.05; worst 0.139) exceeds
the far-margin band |m| ≥ 0.04, so C_ideal far verdicts must flip and
C_dep far verdicts must not; at 4096 shots the movement falls below the
band and both stabilize.

### 7.1 Finite shots (E09, E16; Figs. 8 and 8b)

Kernel error scales as 1/√shots (13.7% → 2.4% Frobenius); effective rank
inflates under shot noise; the classifier is shot-tolerant at n = 2000
(within ±0.015 AUC at 128 shots). The campaign's certification study rebuilds the
*entire deployment* — refit, recalibration, threshold refreeze — under
independently sampled kernels (30 noisy deployments) and audits the
frozen claim grid with paired label streams under two accountings.
Deployment-relative (each noisy pipeline's own refrozen references):
far-margin claims (|m| ≥ 0.04) never flip at any budget; moderate margins
flip 16% → 7% (128 → 4096 shots); near-boundary abstention is 92–94%.
Fixed-reference (the ideal deployment's claims): estimation noise moves
the deployed pipeline's source reference by up to 0.053 upward and 0.139
in worst-case magnitude, so the same claim resolves differently — far-margin flips 21% at 128 shots, 12% at
1024, 0.4% at 4096 (declining on trend; the per-budget series is
non-monotone); moderate 71% → 40%. The
quantitative answer to the title question of this section: *whether
quantum estimation uncertainty changes a scientific validity verdict
depends on the claim's margin and its anchoring, with ≳4k shots needed
before fixed-reference verdicts stabilize* — and in both accountings,
empirical false certification stays below α (own-τ 0.5–1.3%;
fixed-τ 0 false certifications on 80 genuinely-false far-margin claims at
128 shots). Estimation noise changes what is resolvable; it never breaks
the validity of what is certified.

### 7.2 Hardware (E10, E16 hardware arm; Fig. 8)

ibm_marrakesh (Heron r2). The development-era kernel study (496
compute–uncompute circuits × 2048 shots, 32 events, raw counts, no
mitigation) found device noise dominating the estimation budget ~8× over
shot noise, fidelities biased down, and the Gram still PSD. The campaign
adds the first 100%-hardware *deployment* Grams: a 28-event train Gram
plus a 28×12 cross-Gram (714 circuits × 1024 shots, 200 s QPU, test
events half nominal / half TES-shifted), auto-sized to the free-tier
budget. The hardware kernel error is 12.7% against 2.1% shot-only at the
same budget (6.0×; device excess 10.6%, i.e. 5.0× the shot floor —
consistent with the deeper-shot v1 ratios); the hardware Gram stays PSD. Run end-to-end,
the auditor returns identical verdicts across the hardware and three
same-budget shot-only deployments (0 flips, 0 false certifications) —
stated precisely: the n = 28 micro-deployment is at chance (M_T = 0.50,
as the development run's LOO 0.53–0.59 anticipated at this scale), so the
demonstrated property is *verdict stability and fail-closed behavior of
the full pipeline on a real device* — REFUTED and UNRESOLVED where they
should be, never certified — not a hardware performance claim. Protocol
deviations forced by scale (decision-function deployment without Platt
calibration; absolute τ grid; budget-ladder sizing) are disclosed in the
registry. The proposed BasQ-scale campaign
(`docs/basq_e10v2_proposal.md`) remains the registered path to
hardware-kernel certification at statistically meaningful scale.

## 8. Simulation-to-Real Demonstration (E11, E11v2, E11v3; Fig. 9 = ledger)

CMS Open Data H→ττ 2012 (μτ_h, same physics process as Level I),
MC-trained models with Level-I-frozen hyperparameters, no target tuning —
first on a verified 10% mirror, then on the complete public Run2012B+C
collision files (126,164 selected events, ×10), and finally under a
statistical hardening pass (E11v3) that propagates MC-side statistics
into the control-region claims and replaces the sensor's max-floor rule
with calibrated tests. The ledger is stable across all three analyses,
which is itself the demonstration:

| Claim | mirror | full data | hardened (v3) |
|---|---|---|---|
| C1 event accuracy on data | UNRESOLVED | UNRESOLVED | UNRESOLVED — by construction; more data cannot change this, which is the point |
| C2 W normalization ≤ 30% (high-mT CR) | SUPPORTED, 0.922 [0.885, 0.961] | SUPPORTED, 0.9495 [0.937, 0.962] — 3× tighter, √N-consistent | SUPPORTED with MC-stat propagated into the interval (the margin dwarfs it) |
| C3 no MC→data shift at sensor floor | REFUTED (2.6× floor) | REFUTED (2.5× floor) | REFUTED, calibrated: p = 0.005 against a 200-draw null and p = 0.001 by permutation, in *every one* of 20 observation draws |
| C4 SS-region QCD excess | SUPPORTED, z = 18.6 | SUPPORTED, z = 59.4 | SUPPORTED with MC-stat in the denominator (z still ≫ 5) |

Aggregate physics claims are certifiable from control-region evidence;
event-level performance claims are not — and the framework says so
rather than guessing. The hardening pass was registered with a
bidirectional falsifier — the calibrated test was free to *downgrade*
C3's verdict to UNRESOLVED, and that outcome was accepted in writing
before the run; instead every verdict survived on stronger statistical
ground. The remaining sensor caveat is estimand-level: it compares
unweighted MC row samples with data, matching v1/v2 for comparability.

## 9. Failure Cases, Corrections, and Limitations

- **Corrected by replication:** the single-seed TES antisymmetry
  (up-shift arm) did not replicate; partition variance dominates most
  single-nuisance deltas.
- **Corrected by the confirmatory draw:** absolute weighted-AUC levels
  are draw-fragile — later *measured* across four worlds at
  between-world std 0.030–0.050 (E17);
  normalization-induced coverage collapse is SR-composition-dependent —
  the two registered flagship cells failed while the mechanism reproduced
  in other models; both corrections are reported with mechanisms.
- **Corrected by the cross-world falsifier (E17 arm (b)):** the small
  TES/combination degradation signs, replicated 5/5 within the
  development world and confirmed on the first fresh holdout, do **not**
  replicate across two further independent worlds (one world's adverse
  combination *improves* the QK-SVC by 0.009; another's TES down-shift
  by 0.005). The cross-world degradation claim is withdrawn; what
  remains is within-world replicability plus the lesson that
  |ΔAUC| ≲ 0.01 benchmark effects do not transfer across draws.
- **Corrected by registered falsifiers during the campaign:** a
  pure-Poisson rate fit (template statistics), an estimand-label error in
  the weighted benchmark (θ-scaled vs nominal weights; first-run table
  preserved), and two invalid profile-likelihood implementations
  (conditional ensemble; numerical conditioning) — each blocked, fixed,
  registered, and re-run.
- **Structural limitations:** the I1 veto floor of the development-era
  experiments degenerates under common random numbers (E12's arm-(d)
  accounting is reported both ways); E12/E13 share label streams across
  the δ grid (pooled denominators correlated ≈6:1; per-claim α
  unaffected); the balanced-accuracy component bound is vacuous at tested
  scales; L2/L3 morphing is additive across nuisances (combo cells carry
  real cross-terms); one model (scale-trained tree) is
  L2-gate-excluded (0.717 vs 0.6827, conservative direction); the E16
  hardware arm is a micro-scale consistency demonstration, not
  certification at scale;
  E12 computes its landscape before its geometry phase (no label flow —
  verified — but the stronger archive-before-targets discipline of E04v3
  is not claimed for E12). Two previously disclosed limitations were
  closed by registered re-analyses rather than argued away: CMS CR
  intervals now propagate MC-side statistics and the sensor verdict is
  calibrated (E11v3, §8), and the shared-simulation construction of the
  physics beliefs is addressed by the independent-MC split study
  (E08v2, §6.7).
- **Scope:** conclusions are conditional on the declared information
  sets, the H→ττ process, and the benchmark's weight-only implementation
  of normalization nuisances; no quantum advantage is claimed anywhere,
  and the matched-kernel control retires quantum-specific sensing claims.

## 10. Discussion

The evidence selected the composite narrative and sharpened it twice
over. The quantum model is competitive but not superior, and nothing in
sensing or certification is quantum-specific — the matched classical
kernel matches both. What the campaign adds is that the validity question
is governed by *information*, now measured along three axes: the
information the deployment possesses (certification is cheap at margin,
impossible without labels, and physics inference is at risk exactly where
feature-distribution evidence is provably blind); the information's
*quality* (I3 restores identifiability in principle, with resolving power
set by template statistics; profiling restores coverage exactly where its
nuisance model matches the physics, at a ×1.8–3.4 interval-width price,
and fails against the stochastic and joint shifts it cannot represent);
and the information's *stability
under estimation noise* (quantum uncertainty moves the deployed
pipeline's reference points, flipping fixed-reference verdicts until shot
budgets reach thousands — while never breaking error control). This is an
argument for information-set-conditional auditing as standard practice
for ML-based physics analyses, quantum or classical — with the quantum
case adding one genuinely new ingredient: the deployment itself is a
random object whose certification must be anchored explicitly.

## 11. Conclusion

We asked when a scientific claim made with a quantum event classifier is
actually valid when uncertainty arrives simultaneously from collider
deployment and from quantum estimation, and we answered conditionally,
which is the only honest way to answer it. Under nuisance-induced
distribution shift the quantum-kernel classifier behaves like a
competitive member of its model family — small replicated degradations,
no special fragility, no special robustness, and after a matched-kernel
control, no quantum-specific sensing advantage either. What the study
establishes is a validation discipline with measured properties: an
information-set-conditional, fail-closed auditor with anytime-valid error
control, extended exactly to the physics-weighted estimands analysts
actually care about; a formal identifiability boundary at feature-
distribution evidence, resolved by rate evidence whose power we bound by
its template quality; a decoupling of classifier metrics from physics
validity whose mechanism — signal-region composition under invisible
yield shifts — survived and was sharpened by a provably disjoint
confirmatory holdout; and a quantum-estimation-uncertainty study showing
that noise relocates what is resolvable without ever breaking the
validity of what is certified, on simulated kernels and on a real QPU.
The framework's components are generic; nothing is specific to H→ττ, to
kernels, or to quantum models. Its registered falsifiers and audits forced six corrections during this
campaign and were obeyed every time — which is, we believe,
the property a validation framework should be most eager to demonstrate.

---

## Figure and table captions (working section; becomes floats at LaTeX conversion)

Numbering plan (D-030 amendment): companion figures Xb become subfigure
(b) of Figure X at conversion (4/4b, 7/7b, 8/8b); the former "Fig. 9"
ledger is Table 2; the claim × information-set table is Table 1; the
frozen-model table in §5.2 is Table 3; Fig. S16 is supplementary.

**Figure 1 (framework).** The information-set hierarchy I0→I3 and the
fail-closed decision rule. Claims about a frozen deployment are audited
under declared information; heuristic sensors may veto certification but
never grant it; SUPPORTED/REFUTED verdicts carry anytime-valid per-claim
error control; everything else remains UNRESOLVED.

**Figure 2 (systematics response).** Replicated tier-A degradation
ΔAUC under the frozen environment grid (five training seeds,
development world). Within-world sign replication at the 10⁻³ level for
TES down-shifts and adverse combinations; the cross-world falsifier
(E17) later shows these signs are draw-dependent across worlds (§6.2).

**Figure 3 (family response and exact blindness).** Label-free sensor
response by nuisance family: ΔMMD² relative to the same CRN draw's
nominal value, mean over three draws, quantum and matched-rbf8 sensors.
Weight-only families sit at exactly zero — every environment, every
draw (Proposition 2 realized computationally) — while shape-level
response grows with severity; the gray band is the CRN draw-noise ±1σ.

**Figure 4 (sensor generalization; (a) development grid, (b)
out-of-grid).** (a) MMD² vs replicated |ΔAUC| over 28 shift
environments (LONO). (b) The frozen sensors on 48 never-seen
environments per world (off-grid values and official-prior draws),
sensor values archived before targets existed: pooled rank correlation
positive in both worlds and for both sensors; rank, not magnitude, is
the claim.

**Figure 5 (certification landscape).** n*(θ, C) across the claim grid:
resolution fraction and median stopping time by claim margin, with the
severity axis entering through the margin. The fail-closed UNRESOLVED
region is confined to |margin| ≲ 0.01.

**Figure 6 (label economics).** (a) Paired n* ratio of
uncertainty-guided acquisition vs uniform sampling over 480 jointly
resolved cells (ECDF): the median ratio 1.55 is a primary negative
result. (b) Measured median stopping times against the Wald information
floor log(1/α)/KL by margin bucket: certification costs sit a small
factor (1.46–3.35) above a bound no sequential procedure can beat.

**Figure 7 (physics decoupling; (a) counting, (b) inference levels).**
(a) Coverage vs |ΔAUC| for the deployment-blind counting estimator:
validity collapses at flat AUC. (b) Coverage by nuisance family at
L1/L2/L3: profiling restores validity where the nuisance model can
represent the shift and fails where it cannot (soft-MET, combinations);
omitting the shifted family (L3) re-collapses it.

**Figure 8 (estimation uncertainty; (a) kernels and hardware, (b)
verdict stability).** (a) Kernel estimation error vs shot budget with
the hardware point (device excess over the shot floor). (b) Verdict
flips under the two claim anchorings per shot budget: deployment-
relative far-margin verdicts never flip; ideal-anchored far-margin flips
disappear once the measured reference movement falls below the margin
(Proposition 4's prediction traced by the data).

**Figure S16 (supplementary; estimation diagnostics).** Per-configuration
kernel diagnostics for the 30 noisy deployments: Frobenius error
following 1/√shots, effective-rank inflation, and the reference
movement |ΔM_S| whose per-budget distribution calibrates Proposition 4.

**Table 1 (claim × information set).** What each information level can
resolve, with measured error rates (§6.5).

**Table 2 (CMS fail-closed ledger).** Claims C1–C4 across the mirror,
full-data, and statistically hardened analyses (§8).

**Table 3 (frozen deployment).** Models, features, and frozen
hyperparameters (§5.2).

### Reproducibility statement (draft)

All experiments are configuration-driven with immutable run manifests
(git commit, config hash, dataset SHA-256, seeds, package versions,
backend metadata). The campaign adds: a frozen deployment snapshot
committed before the confirmatory draw; archived global row-index sets
with SHA-256s making subset disjointness a checkable artifact; preserved
first-run tables wherever a registered falsifier forced a re-run
(`*_v1_*.json`); pre- and post-campaign falsification audits with every
finding dispositioned in `docs/audits/`; and raw QPU counts with full
provenance and post-job usage for both hardware jobs. Code, configs, and
result tables will be released with a DOI.
