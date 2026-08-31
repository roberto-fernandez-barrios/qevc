# Post-Campaign Falsification Audit — 2026-08-11

Scope: active attempt to falsify the E12–E16 / E04v3 / E11v2 campaign
results before the manuscript rebuild. Two independent passes: (A) a
number-by-number verification of every quantitative claim in the campaign
registry entries against the archived result tables (~172 values checked);
(B) an adversarial statistical/methodological review of all new campaign
code (weighted CS, rates/I3, profile likelihood, all runners) hunting for
leakage, guarantee violations, seed hygiene, silent protocol deviations,
and estimand mismatches. Everything found is dispositioned below —
findings are labeled by the audit's severity codes.

**Bottom line: two findings required re-runs (both completed, prior tables
preserved); one required a corrected scientific reading (in the direction
of a STRONGER claim); the statistical guarantees themselves survived the
audit intact.**

---

## 1. Findings that changed results (fixed + re-run; v1 tables preserved)

### C1 — E13 audited θ-scaled weights while declaring the nominal-weight
estimand. `build_environment_dataset` applies the normalization scalings
to the weights column, so on the 15 norm-affected environments Part B's
streams carried w(θ), not the declared w(0) (E14 always did this
correctly). **Fixed** (weights indexed from the raw subset by surviving
row_id), v1 preserved as `E13_weighted_cs_v1_theta_weights.json`, re-run.
v2 proves the estimand computationally: weight-only environments now give
byte-identical weighted target accuracies. Headline numbers essentially
unchanged (fc 2/8,580; n* ratio 1.66).

### E15 calibration gate, triggered twice — both causes found and fixed
(D-023 amendments 2–3): (i) conditional-ensemble error (constraint centers
not fluctuated per pseudo-experiment); (ii) a numerical-conditioning bug —
the raw Poisson nll's ~10⁷ magnitude made L-BFGS-B's relative ftol stop
~0.02 above the optimum, flattening profiles (q(μ) even negative, μ̂
frozen near its start, coverage → 1). Fixes: unconditional-ensemble
auxiliary draws; saturated-deviance nll; explicit tolerances; analytic
gradient (verified to 10⁻⁹ against central differences; 9 s → 38 ms per
fit); monotone global-minimum safeguard. The gate now actually HALTS the
grid on failure (audit M5). This sequence is the registered-falsifier
system working as designed: an invalid inference implementation was
blocked from producing shifted-environment numbers twice.

## 2. Findings that changed the scientific reading (no re-run needed)

### M2 (number audit) — E12's normalization-collapse "non-reproduction"
was overstated by my own registry text: per-model data show A:rbf_svc
collapsing in 10/12 norm environments (to 0.008) and B:xgboost degrading
to 0.51–0.59, while only the two registered flagship models
(A:qksvc/A:xgboost, whose E12 SRs hold little ttbar/diboson) stay
nominal-like. Corrected reading — **the norm-collapse mechanism reproduces
where the SR composition supports it** — is stronger than my original
wording and is now in the registry; the registered flagship-cell arm still
FAILS as registered (kept).

### H2 — E12's arm-(d) false-certification denominator included streams
where the (CRN-degenerate) I1 alarm makes SUPPORTED structurally
impossible (24/41 envs vetoed). The honest rate over non-vetoed
false-claim streams is 21/3,060 = 0.69% ≤ α (still passes). Registry
corrected; the degenerate-floor issue itself was independently found and
fixed in E04v3 (floor_v2, independent-nominal-draw null) — E12's frozen
protocol predates that amendment and is disclosed rather than rewritten.

### H1 — E16's flip rate mixed claim-definition changes (each noisy
deployment refreezes its own M_S, moving τ by up to 0.049) with
resolution changes. **Fixed by dual accounting**: every noisy deployment
is now audited under its own refrozen τ AND under the ideal deployment's
fixed τ; both flip rates and false-cert tallies are reported (re-run
produced the clean-manifest table). The far-margin stability conclusion
was robust to the confound and remains.

### H3 — E13's "BA_w conservatism" block measured the ratio-CS component
path, whose radius (~0.28 in BA units at n = 5,000) dwarfs the tested
margins — it demonstrates that path's vacuity at these scales, not mild
conservatism. Registry re-worded; per-component claims (the physics
quantities) remain the primary, sharp route.

### H4 — E16 hardware arm deviations now disclosed explicitly in the
registry: decision-function-sign micro-deployment (not the frozen
Platt+BA-threshold pipeline — uncalibratable at n=28), absolute τ grid
(not the frozen degradation grid), ladder sizes differing from the
config's aspirational n_train=48 (live-budget sizing), possible row
overlap between the nominal and tes test halves, and the at-chance
m_target=0.50 that makes "0 flips" a consistency statement, not a
stability proof. The kernel-level diagnostics (device excess 10.6% vs
2.1% shot-only) are unaffected.

## 3. Number corrections applied to the registry (audit pass A)

M1 ddof convention stated explicitly (E02R sample vs E12 population std);
M3 "every tes/jes env at 0.0" → 18/32 cells, decoupling gate recorded;
M4 level-shift range 0.067–0.098 and scoped unweighted-invariance claim;
M5 BA_w n_max 5,000 (not 3,000); M6 LOFO MAE range 0.0005–0.012 with the
MAE>target-mean high end; M7 per-family off-grid counts corrected to the
committed config (7/7/5×2); M8 E11v2 C2 interval "overlaps" (upper bound
0.0006 outside v1's), MC-stat and single-draw-C3 limitations disclosed.
NF1: post-job QPU usage now archived (`E16_hw/job_usage_post.json`);
NF2: template rel-errs archived in the E14 table (2.4% CR_tt, 0.6%
CR_rest).

## 4. Latent risks disclosed (no numbers invalidated)

- **M1 (code audit):** E12/E13 share one label stream across the 6-δ
  claim grid (E14/E16 do not): per-claim α unaffected; pooled error-rate
  denominators are ≈6:1 correlated, so binomial slacks are ~√6 tighter
  than nominal — conservative for every pass verdict reported.
- **M2 (code audit):** E04v3's floor_v2 null uses single draws against
  mean-of-3 observations — under-alarms by ~7% in threshold units;
  conservative direction; disclosed.
- **M4/M3 (E15):** single-family L2 coverage partially trivial
  (shared-simulation anchors); combos are the real morphing test and
  carry the additive-approximation misspecification; combo0/1's L3 now
  omits tes (the shifted family), not the inactive soft_met. Both notes
  are embedded in the E15 output.
- **M6:** E12 arm (a) threshold calibrated on re-partition variance only
  (between-subset component absent) — disclosed in the registry.
- **M7:** the three false-certification rates in the E14 claim table are
  computed under different regimes (veto/no-veto, weighted/unweighted) —
  table strings now qualify each.
- **M8/C2:** E14's s_bkg CI saturates the official clip in 99.25% of
  reps (recorded in-table) — its coverage check is vacuous-by-saturation
  and says "no information beyond the clip", which is itself the honest
  statement; the α/4 CIs the I3 chain consumes are now also
  coverage-validated (1.0, conservative).
- **L1:** a partial-anchor fallback branch in the morphing would be
  dimensionally wrong if ever reached (currently unreachable); left with
  this note.
- **L3:** E12 computes its landscape before its geometry phase (no label
  flow into the sensor — verified — but E04v3's archive-before-targets
  discipline is stronger; E12 cannot make that claim).

## 5. Verified clean (challenged and confirmed)

- One-sample reduction algebra (Z ∈ [0,1] exactly; claim equivalence),
  ratio-CS α/2+α/2, BA α accounting, and the WSR EB-CS implementation.
- `worst_case_weighted_verdict`'s α budget — valid via a Möbius-monotonicity
  argument (box extrema at corners; deterministic corner given the box; CR
  counts independent of the audit stream → no corner union bound needed).
  Now documented in the module docstring reference here.
- E12 disjointness end-to-end (exclusion before sampling; archived indices
  are the used indices; stale-cache defeats impossible — overlap assert).
- Seed hygiene: no `hash()`; distinct salts; disambiguated key strings.
- No label leakage into I1 sensors or frozen decisions anywhere in the
  campaign code (the only information-set violation found was C1's
  θ-in-weights, fixed).
- ~172 registry numbers match their tables (all mismatches listed in §3
  were corrected registry-side; no table was edited post hoc — superseded
  tables are preserved under `*_v1_*.json` names).

## 6. Addendum — manuscript number-verification pass (same day)

A third independent pass verified every quantitative claim in manuscript
v0.3 against the tables: **≈178 exact matches**, 13 mismatches, 5
unsourced figures — all wording-level, all corrected in the manuscript
(and the two affected E16 registry lines): the intro's stale 543/~7,300
(v1-table value; live table 536/7,054); "monotone in budget" for a
non-monotone fixed-τ far series (endpoints correct); the reference-shift
maximum (+0.053 upward / 0.139 worst-case, not +0.049); the L3 flagship
width ratio (3.5×, not 7×); weight-only "AUC invariant exactly" scoped to
the feature distribution (weighted-AUC effects at 4·10⁻⁴); QK-above-RBF28
4/5 seeds (not implied 5/5); shot tolerance ±0.015 (not ±0.01); the
secondary-world sensor range including the descriptive 0.22 fold; the intro's
"factor 2–3" harmonized to ×1.8–3.4; the hardware ratio re-attached
(12.7/2.1 = 6.0×; excess 10.6% = 5.0×); "matched-kernel RBF" → the
full-feature RBF-SVC in the E12 norm-collapse sentence; the floor null σ
scoped per sensor; the falsifier tally made consistent (4 registered
firings + 2 audit corrections); ±0.05 and max/mean figures tied to their
artifacts; and a cross-artifact note added (E05's 0.61% vs the weighted
study's independent re-draw 0.56% of the same arm — seed variation).
