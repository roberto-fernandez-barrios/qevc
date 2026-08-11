# Weighted Anytime-Valid Certification — Mathematical Specification (E13)

**Status:** v1.0 draft — 2026-08-11. SAP §3 extension, predeclared before any
E13 implementation or run (registered as D-019). Nothing in this document was
derived from looking at E13 data: it fixes estimands, guarantees, and
falsifiers first.

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
per-event weight is a deterministic function of the generating process
(w = σ·L/N_gen per process, D-010-rescaled), and the process identity is
label-equivalent (htautau = signal). Granting the auditor per-event weights
on *unlabeled* events would therefore leak labels into I1. Weights are
label-adjacent information and live strictly on the labeled side of the
information boundary. (Population-level weight *constants* — the per-process
weight values and their official clip ranges — are prior physics knowledge
and are available at all information levels; see w_max below.)

## 3. Confidence machinery

### 3.1 One-sample reduction for ratio claims (primary)

Every claim of the form  R ≥ τ  with  R = E[u·c]/E[u]  for a nonnegative
bounded "mask-weight" u (u_i = w_i for A_w; u_i = w_i·1[y_i=1] for TPR_w;
u_i = w_i·1[y_i=0] for TNR_w) is equivalent, since E[u] > 0, to

    E[ u·(c − τ) ] ≥ 0.

Define the per-draw increment

    Z_i(τ) = ( u_i (c_i − τ) + τ·w_max ) / w_max  ∈ [0, 1],

where w_max is a predeclared a priori bound on u_i (§3.4). Then

    R ≥ τ  ⟺  E[Z(τ)] ≥ τ.

The existing empirical-Bernstein predictable-plug-in confidence sequence
(`empirical_bernstein_cs`, WSR Thm 2 variant; observations required in
[0,1]) applied to the stream Z_1(τ), Z_2(τ), … is therefore **exactly valid
and time-uniform** for the transformed mean, and the frozen decision rule
(D-006) applies verbatim with threshold τ on the Z-scale:

    SUPPORTED  ⟺  lower CS bound on E[Z(τ)] ≥ τ
    REFUTED    ⟺  upper CS bound on E[Z(τ)] < τ
    UNRESOLVED otherwise.

Because the draws are IID and Z is a fixed measurable transform per claim,
optional stopping is licensed by time-uniformity exactly as in D-014; n* is
a stopping time and inherits the guarantee.

Properties to note (and to verify empirically in §5):
- Each claim (each τ) carries its own CS over the *same* underlying draws.
  Per-claim α = 0.05 is the unit of inference (SAP §3.3); family-wise counts
  and a Holm sensitivity check are reported as before.
- The D-014 unweighted estimand is the special case u ≡ 1, w_max = 1 — the
  weighted machinery strictly generalizes the running system, giving a clean
  weighted-vs-unweighted comparison on identical draws.

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

CS validity for bounded means requires a *nonrandom, predeclared* upper
bound on the increments. We set

    w_max = (max over processes of the D-010-rescaled per-event weight
             in the audited subset at nominal)  ×  κ_norm,

with κ_norm = 2.05 — covering the largest *compound* per-event scale under
the official clip ranges: a diboson event receives diboson_scale × bkg_scale
≤ 2.0 × 1.01 = 2.02 (ttbar events at most 1.2 × 1.01 = 1.212) — so w_max
remains a valid bound under every admissible weight-only nuisance
configuration, including combined scalings. *(Amended 2026-08-11, before any
E13 implementation or run: v1.0 said κ_norm = 2.0 citing the diboson clip
alone, which misses the compound diboson × bkg worst case by 1%. No
experiment had consumed the old value.)* w_max is process metadata (σ·L/N_gen and official clip
ranges), not event-level information: declaring it does not leak labels.
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
   verdict-flip table across the E05 claim grid; quantify the label cost of
   physics-weighted certification and its driver (effective-sample-size
   ratio Σw²/(Σw)² and the w_max bound).
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
