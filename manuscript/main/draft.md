# When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics and Quantum Estimation Uncertainty

**Draft v0.3 — 2026-08-11.** Rebuilt after the E12–E16 campaign per the
evidence; structure per research spec §33; language per the claims
discipline of §34. All numbers come from the audited result tables
(`docs/experiment_registry.md` campaign section; the ~172-value
number audit and the adversarial code audit are in
`docs/audits/post_campaign_audit_2026-08-11.md`; superseded first-run
tables are preserved under `*_v1_*.json` names). Remaining before
submission: Related Work expanded to full cited prose at LaTeX conversion
(bibliography from `docs/novelty_matrix.md`), figure regeneration for the
new tables, venue formatting, and a final number-by-number verification
pass.

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
reference points by up to 0.05, flipping fixed-reference verdicts at
rates from 21% (far-margin, 128 shots) to 0.4% (4096 shots) while false
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
simulation through a provably disjoint confirmatory holdout to real CMS
collisions and QPU-estimated kernels. Seven findings organize the paper.

**First**, quantum-kernel classifiers exhibit small but replicated
degradations under tau-energy-scale shifts and adverse combinations; a
matched classical kernel on the identical features matches both the
classifier and the sensor, so nothing in our sensing or certification
results is quantum-specific — an honest negative we keep central.
**Second**, a label-free kernel-geometry sensor (MMD² of a
bandwidth-limited kernel over compact physics features) predicts
degradation rank out-of-environment and — new here — out of the
development grid entirely: on 48 continuous nuisance configurations never
seen during development, including draws from the official priors, rank
correlations reach 0.65, while leave-one-family-out magnitude calibration
remains rough — rank, not magnitude, is the defensible claim. **Third**,
the sensor's blindness to normalization nuisances is not an empirical
noise-floor statement but an exact one: weight-only environments produce
feature distributions *identical* to nominal, which we state as a formal
unidentifiability proposition — no I1 statistic, and no I2 stream carrying
nominal weights, has power beyond α against them. **Fourth**, anytime-valid
certification extends *exactly* to physics-weighted estimands through a
one-sample reduction that maps every weighted ratio claim onto the
existing bounded-mean confidence sequence; its measured price is a ×1.7
median label-cost inflation and a fail-closed hardening (543 of ~7,300
certifications retreat to abstention under the physical estimand).
**Fifth**, information level I3 restores identifiability of what I1/I2
cannot see — but its practical resolving power is set by the quality of
the auxiliary evidence: with control-region templates from our MC sample
size, the ttbar normalization is identified only to ±10%, so tighter rate
claims remain UNRESOLVED, fail-closed. **Sixth**, classifier metrics and
physics-level validity decouple, and the confirmatory holdout sharpened
the mechanism: selection-migration-induced coverage collapse reproduces
robustly (all four models, coverage → 0 at flat AUC), while
normalization-induced collapse reproduces exactly where the signal
region's process composition supports it and vanishes where it does not —
validity depends on information the classifier metrics do not carry, with
a mechanism now traced to SR composition — and a profiled likelihood
restores validity exactly where its nuisance model matches the physics,
fails where it cannot (stochastic smearing, joint shifts), and pays a
measured factor 2–3 in interval width for the coverage it recovers.
**Seventh**, quantum estimation
uncertainty acts on certification exactly where the framework predicts:
noise perturbs the deployed pipeline's reference points by up to 0.05, so
fixed-reference verdicts flip at 21% → 0.4% (far-margin, 128 → 4096
shots) while deployment-relative verdicts flip only near boundaries — and
in *every* accounting, empirical false certification stays below α: noise
changes what is resolvable, never the validity of what is certified. A
full-pipeline run on 100%-hardware kernels (28-event train Gram plus
cross-Gram on ibm_marrakesh) behaves identically to its shot-only
counterparts, with device noise dominating the kernel error budget ~6×.

The study was predeclared to be reportable under every outcome
(registered falsifiers, five-seed replication gates, a frozen deployment
snapshot committed before the confirmatory draw, pre- and post-campaign
falsification audits with logged dispositions), and its registered
falsifiers fired five times during the campaign — twice blocking an
invalid inference implementation, once correcting an estimand label, and
twice correcting our own over-generalized readings. We report the
corrections and the correction process, because a framework about
trustworthy validation should itself be validated trustworthily.

## 2. Related Work

Condensed from `docs/novelty_matrix.md` (five clusters, 40+ works; all
flagged arXiv IDs verified 2026-08-10): QML-for-HEP; quantum-kernel
theory and trust; QML validity/monitoring; systematics-aware classical
HEP ML; certification and label-efficient evaluation. Gap statement: no
work combines quantum models + physical collider systematics +
information-conditional certification + physics-level inference; none
treats quantum estimation noise as a certification problem. Nearest
neighbors to cite and distinguish explicitly: Ait Haddou et al. (PTEP
2026 — rate-only normalization uncertainty entering final limits,
classifier unaudited under shift) and Chen & Weng (arXiv:2606.24038 —
betting e-process certification of sim-to-real transfer in robotics; no
information-set hierarchy, no physics inference). Statistical
infrastructure consumed: Waudby-Smith–Ramdas confidence sequences;
Barlow–Beeston template-statistics treatment; standard profile-likelihood
toy conventions (unconditional ensembles).

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
tuple: each estimation realization owns its own refit, recalibration, and
refrozen threshold.

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

**Unidentifiability at I0–I2 (formal).** For weight-only θ:
(i) any I1 statistic has identical law under θ and 0, so any size-α test
has power exactly α; (ii) the same holds at I2 with nominal weights;
(iii) hence any claim whose truth value differs between θ and 0 — rate
claims, the true-weighted metric A_w^{(θ)} — is unresolvable at I0–I2,
and a fail-closed auditor must return UNRESOLVED; (iv) a control-region
count N ~ Poisson(λ(θ)) with λ(θ) ≠ λ(0) has non-trivial power — I3
restores identifiability precisely because rate evidence enters. (Proof:
equality of sampling laws applied to the SUPPORTED event; standard
Poisson testing. Full statement:
`docs/weighted_certification_spec.md` §4b.) The campaign realizes (i)
computationally: under common random numbers the weight-only
environments' sensor values are byte-identical to nominal's.

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

**4.3 Weighted certification (I2).** Every physics-weighted ratio claim
R ≥ τ with R = E[u·c]/E[u] (u = w for A_w; u = w·1[y=1] for TPR_w;
u = w·1[y=0] for TNR_w) reduces to a bounded-mean claim through the
one-sample transform Z_i(τ) = (u_i(c_i − τ) + τ·w_max)/w_max ∈ [0, 1]
with R ≥ τ ⟺ E[Z(τ)] ≥ τ, where w_max is a predeclared bound from
process metadata and the official nuisance clip ranges. The existing
confidence sequence applies *verbatim* — with u ≡ 1 the stream is
byte-identical to the unweighted one — so time-uniform validity and
optional stopping carry over exactly. Balanced accuracy, a
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

FAIR Universe HiggsML Uncertainty (Zenodo 15131565; 220,099,101 events
verified; the official normalization no-op defect found, worked around,
and reported upstream). Development world: one 300k-event subset (the
only parquet draw of the development era), raw-row five-role partitions,
five-seed replication (E02R), 28 unique nuisance points evaluated as 41
environment datasets. Campaign discipline: a frozen deployment snapshot
(hyperparameters, features, feature map, calibration and threshold
procedures, claim grid, sensor family, environment grid, physics
estimator, statistical protocol) committed *before* a fresh confirmatory
subset was drawn from the verified complement of every previously touched
row (index archives with SHA-256s; overlap zero by construction and by
check); campaign rules quarantining the confirmatory rows from all
development; and falsification audits before and after the campaign, with
every finding dispositioned in the open (`docs/audits/`). Statistical
protocol per the predeclared SAP and its logged amendments; superseded
run tables are preserved, never overwritten.

## 6. Results

### 6.1 Nominal performance, the matched control, and what "absolute"
numbers mean (E01, E02R, E12)

Matched 2000-event budget, five-seed replication: QK-SVC 0.848 ± 0.022 —
consistently above full-feature RBF and linear SVC, consistently below
tuned trees (QK − XGB = −0.035 ± 0.013, negative in 5/5 seeds). The
matched-kernel control — RBF on the identical 8 features — reaches
0.859 ± 0.016, statistically indistinguishable from the QK-SVC: the
earlier "QK above RBF" contrast was a feature-set effect, not
quantumness. The fresh holdout confirms the *paired* structure exactly
(QK − XGB = −0.039; QK − RBF8 = −0.008, both within the replication
bands) while exposing a finding about absolute numbers: every model's
absolute weighted AUC sits 0.067–0.098 lower on the fresh draw, with
unweighted AUCs essentially unchanged (0.839–0.845 / 0.875–0.877 for the
trees across both worlds and both model sets). The mechanism is the
benchmark's heavy-tailed signal weights (max/mean ≈ 420; effective sample
size ratio 0.005, i.e. ≈ 46 effective signal events per 41k-event test
role): *absolute physics-weighted metrics carry subset-draw variance of
order ±0.05 that partition-level replication structurally understates.*
Paired contrasts, degradation signs, rank structure, and error control —
everything our claims rest on — replicate. We flag this as a caution for
matched-budget benchmark practice generally.

### 6.2 Behavior under systematics (E02, E02R, E12; Fig. 2)

TES down-shifts degrade the QK-SVC in 5/5 seeds (+0.0024 ± 0.0010 at
−2σ); the up-shift arm does not replicate; the adverse combination
degrades the QK-SVC in 5/5 seeds (+0.025 ± 0.024). Both signs reproduce
on the fresh holdout (+0.0011; +0.0081). Weight-only nuisances leave AUC
invariant exactly.

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
p < 10⁻⁴; secondary world 0.39–0.62 with world-dependent detail; JES
folds sit at the noise floor, as their degradations do). Magnitude
calibration (leave-one-family-out isotonic) is rough — MAE 0.0005–0.012
against target means 0.0003–0.012, at the high end exceeding the target
mean itself: *rank prediction generalizes; magnitude prediction does
not*, and we claim only the former. Blindness to normalization nuisances
is exact under common random numbers (weight-only environments are
byte-identical to nominal — the proposition of Sec. 3 realized
computationally), which also degenerates the development-era veto floor;
the operative floor is re-based on independent nominal draws
(null σ ≈ 7·10⁻⁵), under which 4–8 of 48 out-of-grid environments alarm —
only the soft-MET family and the strongest prior draws, consistently
across worlds and kernels.

### 6.4 Conditional certification: unweighted and physics-weighted
(E05, E13; Fig. 5 data)

Unweighted (development world): across 19,680 claim-streams, empirical
false certification 0.61% ≤ α = 5% on genuinely-false claims, false
refutation 0.03%, with 98% of near-boundary false claims ending
UNRESOLVED at n = 3,000. On the confirmatory holdout the corresponding
rate over non-vetoed false-claim streams is 0.69% ≤ α (the fresh
partition's veto set is disclosed as degenerate under CRN; streams are
shared across the δ grid, so pooled denominators are correlated ≈6:1 —
per-claim α is unaffected).

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
region dominates even at 20,000. Uncertainty-guided acquisition loses to
uniform (median n* ratio 1.55; better in 10% of cells) — a primary
negative result that simplifies practice.

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
ttbar/diboson content (matched-kernel RBF: 10/12 normalization
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
seven-times-narrower interval, the confident-and-wrong failure mode —
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

## 7. Quantum Realism: estimation uncertainty as a certification problem

### 7.1 Finite shots (E09, E16; Figs. 8 and 8b)

Kernel error scales as 1/√shots (13.7% → 2.4% Frobenius); effective rank
inflates under shot noise; the classifier is shot-tolerant at n = 2000
(±0.01 AUC at 128 shots). The campaign's certification study rebuilds the
*entire deployment* — refit, recalibration, threshold refreeze — under
independently sampled kernels (30 noisy deployments) and audits the
frozen claim grid with paired label streams under two accountings.
Deployment-relative (each noisy pipeline's own refrozen references):
far-margin claims (|m| ≥ 0.04) never flip at any budget; moderate margins
flip 16% → 7% (128 → 4096 shots); near-boundary abstention is 92–94%.
Fixed-reference (the ideal deployment's claims): estimation noise moves
the deployed pipeline's source reference by up to +0.049, so the same
claim resolves differently — far-margin flips 21% at 128 shots, 12% at
1024, 0.4% at 4096 (monotone in budget); moderate 71% → 40%. The
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
budget. Device excess is 10.6% over 2.1% shot-only (~6×, consistent with
the deeper-shot v1 ratio); the hardware Gram stays PSD. Run end-to-end,
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

## 8. Simulation-to-Real Demonstration (E11, E11v2; Fig. 9 = ledger)

CMS Open Data H→ττ 2012 (μτ_h, same physics process as Level I),
MC-trained models with Level-I-frozen hyperparameters, no target tuning —
first on a verified 10% mirror, then on the complete public Run2012B+C
collision files (126,164 selected events, ×10). The ledger is stable
across the two data scales, which is itself the demonstration:

| Claim | mirror | full data |
|---|---|---|
| C1 event accuracy on data | UNRESOLVED | UNRESOLVED — by construction; more data cannot change this, which is the point |
| C2 W normalization ≤ 30% (high-mT CR) | SUPPORTED, 0.922 [0.885, 0.961] | SUPPORTED, 0.9495 [0.937, 0.962] — 3× tighter, √N-consistent |
| C3 no MC→data shift at sensor floor | REFUTED (2.6× floor) | REFUTED (2.5× floor) — the sim-to-real shift is not a mirror artifact |
| C4 SS-region QCD excess | SUPPORTED, z = 18.6 | SUPPORTED, z = 59.4 |

Aggregate physics claims are certifiable from control-region evidence;
event-level performance claims are not — and the framework says so
rather than guessing. Known limitations (disclosed): control-region
intervals treat the MC yield as exact; the sensor verdict rests on a
single MC-vs-data draw against a 20-draw floor.

## 9. Failure Cases, Corrections, and Limitations

- **Corrected by replication:** the single-seed TES antisymmetry
  (up-shift arm) did not replicate; partition variance dominates most
  single-nuisance deltas.
- **Corrected by the confirmatory draw:** absolute weighted-AUC levels
  are draw-fragile (±0.05 at this benchmark's signal-weight tails);
  normalization-induced coverage collapse is SR-composition-dependent —
  the two registered flagship cells failed while the mechanism reproduced
  in other models; both corrections are reported with mechanisms.
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
  real cross-terms) and single-family L2 coverage is partially trivial by
  shared-simulation construction; one model (scale-trained tree) is
  L2-gate-excluded (0.717 vs 0.6827, conservative direction); the E16
  hardware arm is a micro-scale consistency demonstration, not
  certification at scale; CMS CR intervals ignore MC-side statistics;
  E12 computes its landscape before its geometry phase (no label flow —
  verified — but the stronger archive-before-targets discipline of E04v3
  is not claimed for E12).
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
kernels, or to quantum models. Its registered falsifiers fired five times
during this campaign and were obeyed every time — which is, we believe,
the property a validation framework should be most eager to demonstrate.

---

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
