# Formal results (extension campaign, D-028/D-029)

Status: working formalization document, 2026-08-11. The manuscript's three
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

## Theorem 1 — Exact weighted anytime-valid certification

**Setting.** Labeled draws (c_i, u_i), i = 1, 2, …, IID from the audited
population: c_i ∈ {0, 1} a correctness indicator, u_i ∈ [0, w_max] a
nonnegative mask-weight (u_i = w_i for A_w; u_i = w_i·1[y_i = 1] for TPR_w;
u_i = w_i·1[y_i = 0] for TNR_w), with w_max a *predeclared, nonrandom* bound
(spec §3.4) and E[u] > 0. The weighted estimand is the ratio
R = E[u·c] / E[u]. For a claim R ≥ τ, τ ∈ [0, 1], define

    Z_i(τ) = ( u_i (c_i − τ) + τ·w_max ) / w_max .

**Theorem.** (a) Z_i(τ) ∈ [0, 1] almost surely, and

    R ≥ τ   ⟺   E[Z(τ)] ≥ τ ,

an equivalence, not an approximation. (b) Let (L_n, U_n) be any confidence
sequence for a bounded mean with time-uniform coverage 1 − α (here: the
empirical-Bernstein predictable plug-in CS), applied to the stream Z_1(τ),
Z_2(τ), …, and let the D-006 rule issue SUPPORTED at the first n with
L_n ≥ τ. Then

    P( ∃ n : SUPPORTED issued  ∧  R < τ ) ≤ α ,

so the false-certification guarantee holds *simultaneously over all stopping
rules*; n* is a legitimate stopping time. (c) The unweighted D-014 system is
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
hence R ≥ τ by (a); so a false certification requires a coverage violation
at some n. (c) Substitution. ∎

*Why exactness matters.* Z is a fixed measurable transform per claim of an
IID draw; no clipping, truncation or asymptotic argument enters, so the
guarantee is inherited *unchanged* from the CS — the reduction adds zero
slack of its own. The label price of weighting is paid in the variance of Z
(effective sample size Σw²/(Σw)²), not in validity.

**Empirical instances.** Validation battery: time-uniform miscoverage within
α + 3σ in every profile × level cell; adversarial optional stopping breaks
the naive fixed-n Wald rule (27.8% false certification) while the CS holds
at 0.0% (`E13_weighted_cs.json`, Part A). Deployment-scale: weighted false
certification 2/8,580; the estimand-equivalence check gives byte-identical
A_w on weight-only environments (E13 v2). Label price: n*_w/n*_unw median
1.66, IQR [1.11, 3.00].

---

## Proposition 2 — Weight-only unidentifiability at I0–I2; I3 restores it

Statement and proof as registered in `docs/weighted_certification_spec.md`
§4b (frozen before any E14 run): for a weight-only nuisance θ (P_θ(X) =
P_0(X), correctness process unchanged), (i) every I1 statistic has identical
law under θ and 0, so any size-α label-free test has power exactly α;
(ii) the same holds at I2 with nominal weights; (iii) hence every claim
whose truth differs between θ and 0 is unresolvable at I0–I2 and a
fail-closed auditor must return UNRESOLVED; (iv) a control-region count
N ~ Poisson(λ(θ)), λ(θ) ≠ λ(0), has non-trivial power — I3 restores
identifiability precisely because rate evidence enters the information set.

**Corollary (quantitative I3 restoration is auxiliary-evidence-bounded).**
The power restored by (iv) is limited by the statistical quality of the
auxiliary evidence: with template-statistics variance σ²_c = Σ_g
(relerr·λ)² (Barlow–Beeston-lite, D-024), the identifiable resolution on a
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
ω, since conditionally on ω the claim threshold is a constant and the
stream is IID. Then the marginal false-certification rate over deployment
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

**Remark (why this needs quantum).** For a deterministic classical pipeline
the map data → deployment is fixed: pseudo-randomness in training is
seed-controllable and reproducible. Estimated kernels make the deployed
object *physically* random — irreducibly so on hardware — and Proposition 3
is the statement that the certification layer is indifferent to that
randomness while the claim semantics must not be.

**Empirical instances.** E16's dual accounting (forced by audit H1) is
exactly the C_dep/C_ideal split: own-τ false certifications 0.5–1.3% ≤ α at
every budget; fixed-τ accounting 0 false certifications out of 80
genuinely-false far-margin claims at 128 shots; hardware arm fail-closed
with 0 false certifications (`E16_quantum_uncertainty.json`, `E16_hw.json`).

---

## Proposition 4 — Verdict stability under bounded deployment movement

**Setting.** Fix a claim family and let m⋆ = M_T(f⋆) − τ⋆ be the ideal
margin. For a realization ω define the movements

    ε_T(ω) = | M_T(f̃_ω) − M_T(f⋆) | ,      ε_S(ω) = | M_S(f̃_ω) − M_S(f⋆) | .

**Proposition.** (i) *Margin transport.* The realized margin m(ω) satisfies

    C_ideal :  | m(ω) − m⋆ | ≤ ε_T(ω)
    C_dep   :  | m(ω) − m⋆ | ≤ | ΔM_T(ω) − ΔM_S(ω) | ≤ ε_T(ω) + ε_S(ω) ,

where ΔM_T, ΔM_S are the signed movements. In particular, if
m⋆ > ε_Q(ω) — with ε_Q = ε_T for C_ideal and ε_Q = |ΔM_T − ΔM_S| for
C_dep — the realized claim remains true; symmetrically for m⋆ < −ε_Q.
(ii) *Verdict stability.* If additionally the realized audit resolves, i.e.
the running-intersection CS radius at the stopping time is below the
realized margin, then the realized verdict equals the ideal verdict: same
sign of margin + resolution ⇒ same D-006 output. (iii) *Common-mode
cancellation.* When the deployment movement is common-mode — ΔM_T(ω) ≈
ΔM_S(ω), as when refitting and recalibration shift source and target
performance together — C_dep margins difference it away (|ΔM_T − ΔM_S|
small) while C_ideal margins absorb ΔM_T in full: deployment-relative
claims are structurally the more stable class.

**Proof.** (i) Triangle inequality on m(ω) − m⋆ written in terms of the
signed movements; for C_dep, m(ω) − m⋆ = ΔM_T − ΔM_S. (ii) The D-006 rule
is a deterministic function of the CS bounds; if the margin sign is
unchanged and its magnitude exceeds the realized radius, the same bound
crosses the same side of τ. (iii) Immediate from the C_dep bound. ∎

**Honesty note (assumption status).** ε_T, ε_S are *realized random
quantities*; Proposition 4 is conditional on them. Their per-shot-budget
distributions are **measured, not derived**: the chain shots → kernel
Frobenius error → movement is calibrated empirically from the 30 archived
noisy deployments (`E16_quantum_uncertainty.json` per_config; Fig. S16).
No first-principles bound from Frobenius error to metric movement is
claimed — a loose one exists but would be vacuous at these scales.

**Predicted-then-measured pattern.** The measured movements at 128 shots
reach ε_S = 0.058 (typ.) and 0.139 (worst) — larger than the far-margin
band |m⋆| ≥ 0.04 — so Proposition 4 *predicts* fixed-τ far-margin verdict
flips at 128 shots and their disappearance once ε falls below the margin at
high budgets; and it predicts own-τ far-margin stability at every budget by
common-mode cancellation. Both patterns are what E16 measured: fixed-τ far
flips 20.8% (128) → 0.4% (4096); own-τ far flips 0.000 at every budget.
The 21% → 0.4% curve is not a curiosity; it is the theory's prediction
traced by the data.

---

## Placement map (for the manuscript surgery)

| Result | Manuscript location | Proof location |
|---|---|---|
| Theorem 1 | §4 (Method, C1) — statement; short proof inline | inline (8 lines) |
| Proposition 2 + corollary | §3 (Formulation, C1) — already present as prose; elevate to numbered environment | inline (already short) |
| Proposition 3 | §7 opening (C3) + conceptual front matter | inline (3 lines) |
| Proposition 4 | §7 (C3), before the E16 results it predicts | inline (6 lines) |
