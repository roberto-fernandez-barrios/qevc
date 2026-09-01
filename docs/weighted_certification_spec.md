# Weighted Anytime-Valid Certification — Mathematical Specification (E13)

**Status:** v1.1 synchronized clarification — 2026-08-13. SAP §3 extension, predeclared before any
E13 implementation or run (registered as D-019). Nothing in this document was
derived from looking at E13 data: it fixes estimands, guarantees, and
falsifiers first. The 2026-08-13 amendment narrows the observable-experiment
scope and terminology without changing an experiment or result.

**Retrospective statistical interpretation (2026-09-01; D-045).** The
`alpha + 3 sigma` / `alpha + 3 sigma MC` thresholds below are retained as the
historically frozen implementation-falsifier gates. They are not interpreted
as IID sampling standard errors or confidence boundaries across the correlated
cell/stream grid. Formal validity is per fixed claim from the confidence
sequence; pooled Monte-Carlo rates are descriptive implementation diagnostics.

Notation: the target environment's audited population is the post-selection
environment dataset restricted to the audit role, with events indexed
i = 1..N, per-event physical weight w_i > 0, correctness indicator
c_i = 1[f(x_i) decided correctly at the frozen threshold] ∈ {0,1}, and class
label y_i ∈ {0,1}.

---

## 1. Estimands

### 1.1 Weighted accuracy (primary)

    A_w = Σ_i w_i c_i / Σ_i w_i

This is the physics-weighted analogue of D-014's unweighted correctness: the
probability that a *weight-proportionally sampled* event is classified
correctly; equivalently the weighted fraction of the physical yield that is
correctly classified.

### 1.2 Weighted class-conditional rates (primary; the physics quantities)

    TPR_w = Σ_{i: y_i=1} w_i c_i / Σ_{i: y_i=1} w_i     (weighted signal efficiency)
    TNR_w = Σ_{i: y_i=0} w_i c_i / Σ_{i: y_i=0} w_i     (weighted background rejection)

### 1.3 Weighted balanced accuracy (derived, not a primary estimand)

    BA_w = (TPR_w + TNR_w) / 2

**Decision (registered):** BA_w is a *ratio-of-ratios* combination and admits
no single bounded-increment stream whose mean is BA_w under any sampling
design we can implement (the two denominators are distinct random subsets).
Rather than force an ugly estimator, we audit the physically meaningful
components TPR_w and TNR_w as first-class claims and certify BA_w only via
the conservative component bound of §3.3. This is the "reformulate the
estimand or build per-component bounds" branch anticipated in the campaign
directive; it is a feature, not a concession — signal efficiency and
background rejection are what a physicist actually needs bounded.

### 1.4 Weighted AUC — explicitly out of scope for CS machinery

AUC is a two-sample U-statistic, not a bounded mean of IID increments; per
SAP §3.1 it stays on fixed-n checkpoints with alpha-spending. E13 does not
change this.

## 2. Sampling design and what labeling reveals

Label draws are **uniform with replacement** from the audited population
(identical to D-014 — the acquisition mechanism does not change). Labeling
event i reveals the pair (y_i, hence c_i; and w_i).

Why w_i is revealed *at labeling time and not before*: in this benchmark the
per-event weight is process- and label-informative. The archived per-process
ranges overlap and are not constant, so a weight does not identify a process
exactly; nevertheless, granting event-wise weights on *unlabeled* events would
add label-adjacent information to I1. The scalar design bound is a separate
input fixed for each frozen finite audit population before its random label
order (see w_max below).

## 3. Confidence machinery

### 3.1 One-sample reduction for ratio claims (primary)

Every fixed claim of the form R ≥ τ, with τ ∈ [0,1] chosen before the audit
label stream and R = E[u·c]/E[u], for a nonnegative
bounded "mask-weight" u (u_i = w_i for A_w; u_i = w_i·1[y_i=1] for TPR_w;
u_i = w_i·1[y_i=0] for TNR_w) is equivalent, since E[u] > 0, to

    E[ u·(c − τ) ] ≥ 0.

Define the per-draw increment

    Z_i(τ) = ( u_i (c_i − τ) + τ·w_max ) / w_max  ∈ [0, 1],

where w_max is a predeclared a priori bound on u_i (§3.4). Then

    E[Z(τ)] − τ = E[u] / w_max · (R − τ),
    R ≥ τ  ⟺  E[Z(τ)] ≥ τ.

The existing empirical-Bernstein predictable-plug-in confidence sequence
(`empirical_bernstein_cs`, WSR Thm 2 variant; observations required in
[0,1]) applied to the stream Z_1(τ), Z_2(τ), … is therefore **exactly valid
and time-uniform** for the transformed mean, and the frozen decision rule
(D-006) applies verbatim with threshold τ on the Z-scale:

    SUPPORTED  ⟺  lower CS bound on E[Z(τ)] ≥ τ
    REFUTED    ⟺  upper CS bound on E[Z(τ)] < τ
    UNRESOLVED otherwise.

Because the draws are IID with replacement and Z is a fixed measurable transform per claim,
optional stopping is licensed by time-uniformity exactly as in D-014; n* is
a stopping time and inherits the guarantee. Because sampling is with
replacement, n* is an audit-label draw (labeled-observation) budget, not the
number of unique events that would need new experimental labels.

Properties to note (and to verify empirically in §5):
- Each claim (each τ) carries its own CS over the *same* underlying draws.
  Per-claim α = 0.05 is the unit of inference (SAP §3.3). Time-uniformity is
  simultaneous over stopping times for that claim, not over τ, models, or
  environments. No family-wise manuscript claim is made without a separately
  implemented multiplicity adjustment; a post-label choice of τ is not covered.
- The D-014 unweighted estimand is the special case u ≡ 1, w_max = 1 — the
  weighted machinery strictly generalizes the running system, giving a clean
  weighted-vs-unweighted comparison on identical draws.
- Weighted and adaptive-data anytime-valid inference predates this work; the
  claimed contribution is the exact fixed-threshold ratio reduction used here
  and its integration with the information-set/fail-closed framework.

### 3.2 Simultaneous ratio CS (secondary, for landscape plots)

For plots that need one interval valid for all τ simultaneously (the E06
landscape analogue), we form CSs for numerator mean μ_N = E[u·c]/w_max and
denominator mean μ_D = E[u]/w_max at level α/2 each and report

    [ L_N / U_D , U_N / L_D ]  (clipped to [0,1])

by union bound: time-uniform, simultaneous in τ, strictly more conservative
than §3.1 per claim. Used descriptively; verdicts always come from §3.1.

### 3.3 BA_w component bound (derived)

With per-component claims run at α/2 each (Bonferroni),

    BA_w ≥ ( L_TPR + L_TNR ) / 2   with probability ≥ 1 − α, uniformly in t.

SUPPORTED for a BA_w claim requires the component lower bounds' average to
clear τ; REFUTED requires the component upper bounds' average to fall below
τ. Conservatism is quantified in the Monte Carlo study (§5).

### 3.4 The a priori bound w_max

CS validity for bounded means requires an upper bound fixed relative to the
audit filtration. Conditional on each frozen finite population, before its
random audit order, we set

    w_max = (max over processes of the D-010-rescaled per-event weight
             in the audited subset at nominal)  ×  κ_norm,

with κ_norm = 2.05 — covering the largest *compound* per-event scale under
the official clip ranges: a diboson event receives diboson_scale × bkg_scale
≤ 2.0 × 1.01 = 2.02 (ttbar events at most 1.2 × 1.01 = 1.212) — so w_max
remains a valid bound under every admissible weight-only nuisance
configuration, including combined scalings. *(Amended 2026-08-11, before any
E13 implementation or run: v1.0 said κ_norm = 2.0 citing the diboson clip
alone, which misses the compound diboson × bkg worst case by 1%. No
experiment had consumed the old value.)* The base maximum is computed from
the already materialized finite audit population; thus the stated guarantee
is conditional on that population and scalar bound, not an unconditional
claim that its numerical value was known before population construction.
Only the scalar is exposed before the random audit order, not event-wise weights.
Looseness in w_max costs only statistical efficiency (wider CS), never
validity; the measured cost appears in the §5 comparison.

## 4. Weights under unknown normalization nuisances — the identifiability
boundary (bridge to E14)

Under a weight-only nuisance θ_norm, the environment's true weights are
w_i(θ_norm) = s(θ_norm, proc_i)·w_i(0), while the labeling oracle reveals the
*nominal* MC weight w_i(0) (no experiment knows the true θ_norm at labeling
time). Consequently:

- I2(n) with nominal weights identifies A_w^{(0)} — the nominal-weighted
  correctness — **not** the true deployed estimand A_w^{(θ)}. Since
  P_θ(X) = P_0(X) for weight-only nuisances, no I1 or I2 evidence
  distinguishes θ_norm from 0 at all (E14 states and proves this formally).
- Under I3 ⊇ I2 ∪ {θ̂_norm from rates/control regions}, the reweighted
  increments u_i(θ̂) = s(θ̂, proc_i)·w_i(0) restore identifiability of
  A_w^{(θ)}, with the θ̂ uncertainty propagated by auditing at the
  worst-case s over the θ̂ confidence set (fail-closed: if the worst-case
  bound cannot clear τ, the claim stays UNRESOLVED).

E13 implements and validates the fixed-weight machinery (this document);
E14 owns the θ̂-uncertain extension and its experiments.

## 4b. E14 addendum — formal unidentifiability proposition (added
2026-08-11, before any E14 run)

**Proposition (feature-only unidentifiability for a weight-only nuisance;
observable-experiment clarification, 2026-08-13).** I1 is the fixed-size or
count-conditioned feature experiment O_1^(n)=(X_1,…,X_n)|N=n and excludes N,
exposure, yields and event weights. Suppose

    P_θ(X_1,…,X_n | N=n) = P_0(X_1,…,X_n | N=n).

(i) Every I1 statistic has identical law under θ and 0; a level-α test has
power equal to its actual size and hence at most α.

(ii) I2 adds queried binary signal/background labels and nominal event weights
in the simulated benchmark. The binary label reveals class but not the
background process category. If the joint law of (X,Y,w⁰) is invariant while
the nuisance-dependent category or true weight w^(θ) remains hidden, the same
indistinguishability result holds. A binary target label alone cannot
reconstruct the hidden physical rate weights.

(iii) Claims whose truth changes only through the unobserved rate or
true-weighted estimand have no nontrivial distinguishing power in these
declared experiments and are reported UNRESOLVED by policy.

(iv) This is not a statement about every collider observable. If the full
experiment includes N ~ Poisson(λ(θ)) with λ(θ) ≠ λ(0), then
P_θ(N,X_1,…,X_N) differs from P_0(N,X_1,…,X_N), and count-based I3 tests can
have nontrivial power.

*Proof.* (i)–(iii) follow from equality of the declared sampling laws; every
rejection event has the same probability under null and alternative. Part
(iv) is the explicit count-observable counterexample. ∎

Alpha budget for I3-conditional weighted verdicts (D-024(ii)): the
(s_ttbar, s_bkg) confidence box is built from per-parameter
profile-likelihood CIs at α/4 each; diboson is bounded by its official
clip range (prior knowledge, no data term); the corner-wise confidence
sequences run at α/2; the union bound gives total level α. Diboson's
unidentifiability from these control regions is expected and reported —
its clip range enters the worst case.

## 4c. E13v2 addendum — pre-split component allocation for BA_w
(added 2026-08-12, before any E13v2 implementation or run; registry
E13v2, falsifiers frozen at D-028)

**Final-audit qualification (2026-08-12).** The mathematical allocation is
valid when its class bounds are fixed without using unrevealed labels. The
executed battery computed its class maxima using y over the complete frozen
population (`run_e13v2.py`, lines 114–121). It is therefore an
**oracle/benchmark diagnostic**, not an operational I2 guarantee. This does
not weaken the negative TPR/BA conclusion: failure even under the favorable
oracle bound is an information-limit diagnostic. Successful TNR resolutions
are reported only as oracle-bound results. The operational E13/E19 guarantees
use the global scalar bound described in §3.4.

**Motivation.** The §3.3 BA_w path was measured vacuous (post-audit H3:
radius ≈ 0.28 in BA units at n_max = 5,000). Two sources of slack are
removable without touching validity; a third limit is structural and, if
binding, is the honest result.

**The allocation rule (predeclared).** For a claim BA_w ≥ τ_BA:

1. *Component thresholds:* predeclare (τ₁, τ₂) with (τ₁ + τ₂)/2 = τ_BA.
   The registered decomposition is source-referenced: a claim at margin
   δ against a reference (T̂PR, T̂NR) uses τ₁ = T̂PR − δ, τ₂ = T̂NR − δ.
   In the Monte-Carlo battery the population's exact component values
   play the reference role, mirroring how §5's A_w claims are placed.
2. *α allocation:* α₁ + α₂ = α, predeclared; default α/2 each.
3. *Sharp per-component machinery:* each component claim R_k ≥ τ_k runs
   the §3.1 one-sample reduction — NOT the §3.2 ratio CS that §3.3 v1
   built on (§3.2 is registered as "never preferred for verdicts"; v1's
   use of it inside resolve_ba_claim is the first removable slack).
4. *Per-class oracle bounds in the executed battery (second removable-slack
   diagnostic):* the §3.1 reduction only needs an a.s. bound on u. For
   u⁽¹⁾ = w·1[y=1], the battery uses
   w_max⁽¹⁾ = (max signal-row weight in the audited subset at nominal)
   × κ_sig with **κ_sig = 1.0**: no admissible weight-only nuisance
   touches signal weights (`_norm_weight_scale` applies ttbar_scale and
   diboson_scale to those processes and bkg_scale to y = 0 rows only —
   verified in code before this addendum was frozen). For
   u⁽⁰⁾ = w·1[y=0], w_max⁽⁰⁾ = (max background-row weight) × κ_norm
   (2.05, §3.4). These subset maxima were derived using
   complete-population labels and do not follow the operational I2
   information boundary; see the qualification above.
5. *Streams and budget:* draws remain uniform-with-replacement (§2 —
   class-conditional sampling is impossible pre-label, since labeling
   is what reveals y). Every labeled draw feeds both component streams;
   masked draws contribute the neutral increment τ_k. The "label
   budget allocation" of the registry hypothesis is therefore realized
   through (α_k, w_max⁽ᵏ⁾), not through physical routing.

**Verdict rule.** SUPPORTED for BA_w ≥ τ_BA iff BOTH component audits
certify (L_k ≥ τ_k at level α_k, running intersection); REFUTED iff
BOTH component audits refute (U_k < τ_k); UNRESOLVED otherwise.

**Validity of the mathematical construction, conditional on admissible
pre-label bounds.** (i) False
certification: if BA_w < τ_BA then R_k < τ_k for at least one k (else
(R₁+R₂)/2 ≥ (τ₁+τ₂)/2 = τ_BA); certifying that component requires its
CS to violate coverage (Theorem 1 applied with the class bound
w_max⁽ᵏ⁾), so P ≤ α₁ + α₂ = α by the union bound. (ii) False
refutation: if BA_w ≥ τ_BA then R_k ≥ τ_k for at least one k; refuting
that component requires a coverage violation, so P ≤ α. (iii) The rule
is fail-closed: components disagreeing in direction yield UNRESOLVED. ∎

**Structural limit (stated as the falsifiable hypothesis).** The §3.1
margin on the Z scale is E[u⁽ᵏ⁾]·m / w_max⁽ᵏ⁾. At the benchmark's
physics weights the signal carries E[u⁽¹⁾]/E[w] ≈ 1.0 × 10⁻³ of the
weight mass, so the TPR_w Z-margin at m = 0.05 is ~10⁻⁵ against a CS
radius floor of order 10⁻³ at n = 5,000 — a gap of ~10² that the
per-class bound (factor w_max·κ_norm / w_max⁽¹⁾ ≈ 2.5) cannot close.
If the battery confirms this, falsifier (b) fires and the honest
publication is: the BA_w path at physics weight dispersion is
information-limited by the weighted signal fraction, not by estimator
slack — the sharpest exact reduction moves the feasibility boundary by
×2.5 and the remaining gap is structural. A population with the same
weight *values* but class-independent weights (the v1 battery design)
is predicted to RESOLVE under this allocation, attributing the
impossibility to the class–weight correlation.

**Battery (frozen).** Salt "E13V2"; α = 0.05; n_max = 5,000;
n_rep = 200 per cell. Populations: (P1) the v1 §5-style synthetic BA
population (y ~ Bern(0.3), weights drawn class-independently from the
benchmark per-process constants, component rates 0.75/0.85 — the v1
construction, for comparability and for the attribution control);
(P2) benchmark-faithful: the seed-101 subset's actual (y, w) rows as
the finite population, correctness synthesized class-conditionally at
the same target rates. Claims: τ_BA = BA_w ± m, m ∈ {0.02, 0.05}
(the registered margin range endpoints); component claims also audited
individually for diagnosis. Comparison arm: v1 `resolve_ba_claim` on
identical draws. Diagnostics recorded: per-class w_max values and
factors, weighted class fractions, mean CS radius at n_max in BA units
(v1 vs v2), per-component resolution. Falsifiers as registered (D-028;
registry E13v2): (a) any cell false-cert > α + 3σ → allocation invalid
and blocked; (b) ALL true BA_w claims at margins 0.02–0.05 UNRESOLVED
at n_max = 5,000 on the physics population → measured impossibility,
published as such.

## 5. Validation protocol (Monte Carlo, predeclared)

All checks use synthetic populations with known truth plus benchmark-derived
populations (E02 archived scores with row-level weights):

1. **Time-uniform coverage:** for weight profiles {uniform, benchmark
   per-process, adversarial heavy-tail (w_max/w̄ ≥ 20)} × true A_w ∈
   {0.55, 0.72, 0.85, 0.95}: P(∃t ≤ n_max: CS excludes truth) ≤ α + 3σ_MC.
2. **False certification / false refutation** on genuinely false/true claims
   at margins ±{0.002, 0.005, 0.01, 0.02, 0.05}: rates ≤ α (+ binomial
   slack); fail-closed dominance near zero margin.
3. **Optional-stopping stress:** adversarial stopping rule (stop the first
   time the naive fixed-n Wald interval would certify) must show inflated
   error for the naive interval and controlled error for the CS.
4. **Weighted vs unweighted on identical draws:** n*-ratio distributions and
   verdict-flip table across the E05 claim grid; quantify the audit-label draw budget of
   physics-weighted certification and its driver (effective-sample-size
  ratio (Σw)²/Σw² and the w_max bound).
5. **BA_w conservatism:** empirical coverage of the §3.3 bound vs its
   nominal level (expected strictly conservative; measure how much).

## 6. Falsifiers (frozen)

- Any MC configuration in §5.1–5.2 with time-uniform miscoverage or false
  certification exceeding α beyond 3σ Monte Carlo slack falsifies the
  implementation (not the theory) and blocks E13's use downstream until
  fixed and re-registered.
- If weighted n* exceeds the feasible budget (20k) for *every* claim with
  |margin| ≥ 0.04 on benchmark populations, weighted certification is
  reported as impractical at physics weights — a negative result to publish,
  not to hide.
