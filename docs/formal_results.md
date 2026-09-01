# Formal results (extension campaign, D-028/D-029)

Status: synchronized pre-submission formalization, 2026-08-13. The manuscript's three
contributions each carry formal statements: **C1** gets Theorem 1 and
Proposition 2; **C3** gets Propositions 3 and 4. Notation follows
`docs/weighted_certification_spec.md` (D-019) and the frozen decision rule
D-006. Every statement lists its empirical instance in the archived tables —
the theory and the measurements are cross-referenced deliberately.

Presentation rule (D-029): Proposition 3's mathematics is deliberately
elementary; its content is the claim *semantics* and the fact that the E16
campaign instantiates it measurably. It is presented as a clarification, not
sold as a deep theorem.

---

## Theorem 1 — Exact fixed-threshold weighted reduction

**Setting.** Condition on a frozen finite audit population and a scalar
w_max fixed before the random audit order. Labeled draws (c_i, u_i), i = 1,
2, …, are IID with replacement from that population: c_i ∈ {0, 1} is a
correctness indicator and u_i ∈ [0, w_max] is a nonnegative mask-weight
(u_i = w_i for A_w; u_i = w_i·1[y_i = 1] for TPR_w; u_i =
w_i·1[y_i = 0] for TNR_w), with E[u] > 0. The weighted estimand is the ratio
R = E[u·c] / E[u]. For a fixed claim R ≥ τ, τ ∈ [0, 1] chosen before the
audit label stream, define

    Z_i(τ) = ( u_i (c_i − τ) + τ·w_max ) / w_max .

**Theorem.** (a) Z_i(τ) ∈ [0, 1] almost surely, and

    E[Z(τ)] − τ = E[u] / w_max · (R − τ),

and therefore

    R ≥ τ   ⟺   E[Z(τ)] ≥ τ ,

an equivalence, not an approximation. (b) Let (L_n, U_n) be any confidence
sequence for a bounded mean with time-uniform coverage 1 − α (here: the
empirical-Bernstein predictable plug-in CS), applied to the stream Z_1(τ),
Z_2(τ), …, and let the D-006 rule issue SUPPORTED at the first n with
L_n ≥ τ. Then

    P( ∃ n : SUPPORTED issued  ∧  R < τ ) ≤ α,
    P( ∃ n : REFUTED issued    ∧  R ≥ τ ) ≤ α,

so each directional error is controlled simultaneously over all stopping
times for this fixed claim; the union of incorrect decisive verdicts is also
contained in the single two-sided-CS coverage failure. n* is a legitimate
stopping time and, under with-replacement sampling, an audit-label draw budget
rather than a unique-event label count. (c) The unweighted D-014 system is
the special case u ≡ 1, w_max = 1: the weighted machinery strictly
generalizes it, licensing weighted-vs-unweighted comparisons on identical
draws.

**Proof.** (a) Boundedness: u_i(c_i − τ) ∈ [−τ·w_max, (1 − τ)·w_max] since
u_i ∈ [0, w_max] and (c_i − τ) ∈ [−τ, 1 − τ] with u_i(c_i − τ) minimized at
c_i = 0, u_i = w_max and maximized at c_i = 1, u_i = w_max; adding τ·w_max
and dividing by w_max lands in [0, 1]. Equivalence: E[Z(τ)] ≥ τ ⟺
E[u(c − τ)] + τ·w_max ≥ τ·w_max ⟺ E[u·c] ≥ τ·E[u] ⟺ R ≥ τ, using
E[u] > 0. (b) On the event that the CS covers E[Z(τ)] at every n — an event
of probability ≥ 1 − α by time-uniformity — L_n ≥ τ implies E[Z(τ)] ≥ τ,
hence R ≥ τ by (a); the symmetric statement holds for refutation. Thus any
incorrect decisive verdict requires a coverage violation at some n. (c)
Substitution. ∎

*Why exactness matters.* Z is a fixed measurable transform per claim of an
IID draw; no clipping, truncation or asymptotic argument enters, so the
guarantee is inherited *unchanged* from the CS — the reduction adds zero
slack of its own. The label price of weighting is paid in the variance of Z
(effective sample size (Σw)²/Σw²), not in validity. Labeling reveals y_i and
w_i and hence u_i; event-wise weights are withheld from I1 because they are
process- and label-informative, not because they identify a process exactly.
The data-curation layer supplies only the single global scalar bound before
sampling, not row weights or class labels; this does not enlarge I1 with
event-level information.
The multiplier 2.05 covers the largest compound official scaling 2.02, and
both classes have positive archived weight mass, so E[u] > 0.

**Scope.** The guarantee is per fixed claim and simultaneous only over its
stopping times. It is not FWER control over thresholds, models, or
environments. Selecting τ or a claim after labels requires a separate
multiplicity construction. Time-uniformity likewise does not validate
arbitrary adaptive row selection; E07 uses a proposal fixed from unlabeled
scores with bounded importance weights.

**Novelty boundary.** Importance-weighted, self-normalized and adaptive-data
confidence sequences already exist, including *Off-Policy Confidence
Sequences* (Karampatziakis, Mineiro and Ramdas, 2021) and *Anytime-valid
off-policy inference for contextual bandits* (Waudby-Smith et al., 2022/2025).
We claim only the exact algebraic reduction for the fixed-threshold physics
ratio estimand used here, the equivalence of its claim, and integration with
the information hierarchy and fail-closed auditor.

**Empirical instances.** These correlated Monte-Carlo rates are implementation
stress tests, not proofs of the theorem or FWER. Validation battery: time-uniform miscoverage within
α + 3σ in every profile × level cell; adversarial optional stopping breaks
the naive fixed-n Wald rule (27.8% false certification) while the CS holds
at 0.0% (`E13_weighted_cs.json`, Part A). Deployment-scale: weighted false
certification 2/8,580; the estimand-equivalence check gives byte-identical
A_w on weight-only environments (E13 v2). Label price: n*_w/n*_unw median
1.66, IQR [1.11, 3.00].

---

## Proposition 2 — Feature-only unidentifiability for weight-only nuisances

I1 is the fixed-size or count-conditioned feature experiment

    O_1^(n) = (X_1, …, X_n) | N = n,

which explicitly excludes N, exposure, yields and event weights. If a
weight-only nuisance satisfies

    P_θ(X_1, …, X_n | N=n) = P_0(X_1, …, X_n | N=n),

every I1 statistic has the same law. I2 adds queried binary signal/background
labels and nominal weights in the simulated audit protocol. A binary label
reveals class, not background process category. If the joint law of
(X,Y,w^(0)) is unchanged while the nuisance-dependent category or true weight
w^(θ) remains hidden, the same conclusion holds at I2. A level-α test has
power equal to its actual size and hence at most α; affected rate or
true-weighted claims are reported UNRESOLVED under the fail-closed policy.

This is not an impossibility for every collider observable. If the full
experiment observes N and N ~ Poisson(λ(θ)) with λ(θ) ≠ λ(0), then

    P_θ(N, X_1, …, X_N) ≠ P_0(N, X_1, …, X_N),

and count-based I3 tests can have nontrivial power.

**Corollary (quantitative I3 restoration is auxiliary-evidence-bounded).**
The power restored by (iv) is limited by the statistical quality of the
auxiliary evidence: with template-statistics variance σ²_c = Σ_g
(relerr_g·λ_g)² (Barlow–Beeston-lite, D-024), the identifiable resolution on a
rate scale s_p is of order the template noise, and claims tighter than that
remain UNRESOLVED — fail-closed degradation, not failure.

**Empirical instances.** *Exact* form of (i): under common random numbers,
weight-only environments produce MMD² *byte-identical* to nominal — every
environment, every draw (`E04_geom_failure.json` records; E04v3's CRN
identity; Fig. 3). The corollary, measured: s_ttbar CI width 0.19 (±10%,
set by 2.4% template rel-err), tight claims UNRESOLVED, s_diboson
unidentified by construction; 12/400 REFUTED with 0 false certifications on
the adversarial rate claim (`E14_i3.json`).

---

## Proposition 3 — Error control under estimated (random) deployments

**Setting (D-029).** With finite-shot or hardware kernels the deployed
pipeline is itself estimated: the realized kernel noise ω (shot outcomes,
device noise) determines the trained model, the calibrator, and the
operating threshold — write f̃_ω for the realized deployment and f⋆ for the
ideal (exact-kernel) one. ω is independent of the audit label stream. Two
registered claim classes:

    C_dep(ω)  :  M_T(f̃_ω) ≥ M_S(f̃_ω) − δ     (deployment-relative; E16 "own-τ")
    C_ideal(ω):  M_T(f̃_ω) ≥ M_S(f⋆) − δ       (ideal-anchored;      E16 "fixed-τ")

Both are claims about the *realized* deployment's target metric; they differ
in the reference the deployment is held to.

**Proposition.** Suppose the certification procedure, applied to the
realized pipeline's own label stream, controls false certification at level
α conditionally on every realization:

    P( false certification | ω ) ≤ α    for P_ω-almost every ω

— which is Theorem 1(b) (or its unweighted special case) applied at fixed
ω, since conditionally on ω the claim threshold is a constant and the audit
stream remains IID and disjoint from training, calibration, and threshold
selection. Then the marginal false-certification rate over deployment
randomness obeys

    P( false certification ) = E_ω [ P( false certification | ω ) ] ≤ α ,

for **both** claim classes. ∎ (Tower property.)

**Remark (what randomness does and does not do).** Deployment randomness
moves the claim's *truth value* and *margin* — for C_dep through τ(ω) =
M_S(f̃_ω) − δ, for C_ideal through M_T(f̃_ω) — so it changes *which* claims
are true and which are resolvable at a given label budget. It never touches
the validity of what is certified. This is the formal counterpart of the
campaign's measured sentence: "noise changes what is resolvable, never the
validity of what is certified."

**Remark (quantum-specific role).** Classical pipelines may also contain
training and inference randomness. Quantum-kernel evaluation adds an
additional measurement-induced deployment uncertainty intrinsic to
finite-shot and noisy quantum execution. Proposition 3 says the
certification layer is indifferent to the source of randomness while claim
semantics must not be.

**Empirical instances.** E16's dual accounting (forced by audit H1) is
exactly the C_dep/C_ideal split: own-τ false certifications 0.5–1.3% ≤ α at
every budget; fixed-τ accounting 0 false certifications out of 80
genuinely-false far-margin claims at 128 shots; hardware arm fail-closed
with 0 false certifications (`E16_quantum_uncertainty.json`, `E16_hw.json`).

---

## Proposition 4 — Truth-sign and resolved-verdict stability

**Setting.** Fix a claim family and let m⋆ be its ideal signed margin. Define
the signed target and source movements

    ΔM_T(ω) = M_T(f̃_ω) − M_T(f⋆),
    ΔM_S(ω) = M_S(f̃_ω) − M_S(f⋆).

**Proposition.** (i) *Exact margin transport:*

    C_ideal :  m(ω) − m⋆ = ΔM_T(ω),
    C_dep   :  m(ω) − m⋆ = ΔM_T(ω) − ΔM_S(ω).

Consequently |m⋆| > |ΔM_T| for C_ideal, or
|m⋆| > |ΔM_T − ΔM_S| for C_dep, is sufficient to preserve the truth-sign.
Failure of either sufficient condition gives no conclusion about a flip.
(ii) *Resolved verdicts.* For either claim class, the corresponding
sign-stability condition plus coverage of both CSs plus resolution of both
audits implies the same decisive verdict. Conditional on a realization that
satisfies stability, two level-α audits obey

    P(V⋆ ≠ V(ω), R⋆ ∩ R(ω) | ω) ≤ 2α

by a union bound, with no independence assumption. Running each audit at α/2
gives joint level-α control; no sharper dependence-based bound is claimed.
For weighted claims,
the metric-scale margin maps to the Z scale by E[u]/w_max. (iii)
*Common-mode cancellation.* If ΔM_T ≈ ΔM_S, the deployment-relative movement
is small while the ideal-anchored movement retains ΔM_T, so C_dep is
structurally the stabler claim class.

**Proof and counterexamples.** Substitute the signed movements into each
margin. If a perturbation has magnitude below |m⋆|, it cannot cross zero. Under
the relevant stability condition, coverage makes each decisive verdict point
to the same truth sign; two resolutions and the union bound yield the result.
Coverage and resolution alone do not suffice: m⋆=0.05 and ΔM_T=−0.10 produce
opposite ideal and realized truth signs, so perfectly covering audits resolve
SUPPORTED and REFUTED. Failure of sufficiency does not force a flip either:
ΔM_T=+0.10 violates |m⋆|>|ΔM_T| but preserves the positive sign. ∎

**Artifact status (0.3.3 presentation closure).** The deterministic raw/PSD replay
reconstructs the exact source and target accuracy estimands for every frozen
E16 realization. It therefore evaluates ΔM_S, ΔM_T and ΔM_T − ΔM_S for 7,200
deployment/regime/claim-semantics/environment-family-delta condition cells;
all are evaluable, with no threshold clipping and zero margin-identity
residual. The strict sufficient condition holds in 4,943/7,200 (68.7%). It
preserves the truth sign in every holding cell. Across the ten paired audit
streams per cell, verdict flips occur in 4,554/49,430 (9.2%) holding cases and
13,637/22,570 (60.4%) failing cases. Two holding streams have opposite resolved
verdicts, as permitted by the proposition's coverage-conditioned 2α bound;
8,933 stable verdicts occur despite failure, confirming that the condition is
sufficient rather than necessary. The result is **INFORMATIVELY INSTANTIATED**
and conservative, not a theory prediction for each verdict or a population
law. The independent descriptive unit remains one deployment (five per shot
budget), not correlated cells or streams. All evaluated far-margin
deployment-relative claims are true and supported in raw and PSD-repaired
realizations; no false far-margin deployment-relative claim tests refutation
stability. Source:
`results/tables/E16_proposition4_instantiation.json`. The 0.3.3 derivative
`results/tables/E16_proposition4_deployment_summary.json` reports median, IQR,
range, mean and sample SD across the same 30 noisy-kernel deployments without
changing the replay or adding population inference.

---

## Manuscript locations

| Result | Manuscript location | Proof location |
|---|---|---|
| Theorem 1 | §4 (Method, C1) — statement; short proof inline | inline (8 lines) |
| Proposition 2 + corollary | §3 (Formulation, C1) — already present as prose; elevate to numbered environment | inline (already short) |
| Proposition 3 | §7 opening (C3) + conceptual front matter | inline (3 lines) |
| Proposition 4 | §7 (C3), before the independent E16 empirical results | inline |
