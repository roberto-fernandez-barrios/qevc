# E20 preregistration — offline gate before any QPU expenditure

## Status and scope

This registration is frozen before running the E20 offline gate. It does not
authorize access to `Generic_project`, the 100-minute instance, or any other
QPU resource. The current npj Quantum Information submission remains the
baseline and is not modified by E20 planning.

E20 does not test quantum advantage. Its only possible added value is to turn
the existing single micro-scale hardware integration demonstration into either
(i) replicated physical-deployment evidence for C3, or (ii) an equally clear
physical limitation showing that device noise drives the pipeline into chance
or fail-closed floor.

## Current evidential gap used to set the gate

- E10: one 32-event symmetric Gram, 496 circuits at 2,048 shots, 276 s QPU;
  hardware Frobenius error 17.0% versus 1.9% shot-only; no train/cross
  deployment experiment.
- E16 hardware: one 28-event train Gram plus a 28×12 cross-Gram, 714 circuits
  at 1,024 shots, 200 s QPU. It is a full pipeline, but each environment has
  only six target events and BA/accuracy is 0.50. Of 60 audit-seed verdicts,
  0 are SUPPORTED, 55 REFUTED and 5 UNRESOLVED; all six majority cells are
  REFUTED. Zero flips therefore has little power to establish stability.

The wording “micro-scale integration / fail-closed consistency demonstration,
not hardware performance or certification at scale” remains correct.

## Frozen offline candidates

All candidates use the current eight-qubit, two-repetition, linearly entangled
feature map at scale 0.5; the existing angle scaler; C=1 QK-SVC; mean-one
class-balanced training weights; weighted Platt calibration; weighted
BA-optimal threshold; the same degradation claims, paired audit streams and
deployment-relative/ideal-anchored semantics as E16. No parameter is tuned.

The fixed evidence roles are nested train subsets of 48/64/80 events, 24 fixed
source-validation events for calibration/reference, and the same 24 fixed
nominal-test row IDs evaluated under nominal and TES=0.98 (48 target columns).

| Candidate | Train Gram circuits | Cross block | Cross circuits | Total circuits | Dense matrices | Approx. raw counts |
|---|---:|---:|---:|---:|---:|---:|
| A48 | 1,128 | 48×72 | 3,456 | 4,584 | 0.046 MB | 13.7 MB |
| B64 | 2,016 | 64×72 | 4,608 | 6,624 | 0.069 MB | 19.8 MB |
| C80 | 3,160 | 80×72 | 5,760 | 8,920 | 0.097 MB | 26.6 MB |

At 1,024 shots the two archived hardware jobs imply approximately 0.28 QPU
seconds per circuit. The preregistered prudent interval is 0.22–0.38 s/circuit,
which includes backend/session variation but not a failed-job rerun. Estimated
cost per physical deployment is therefore 21.4 min [16.8, 29.0] for A48,
30.9 min [24.3, 42.0] for B64 and 41.6 min [32.7, 56.5] for C80. Three A48
deployments cost 64.2 min centrally [50.4, 87.1]; four cost 85.6 min centrally
and can exceed the full allocation. B64/C80 are offline scaling diagnostics,
not post-result fallbacks.

## Frozen GO / NO-GO rule

The machine-readable thresholds are in
`configs/experiments/E20_offline_gate.yaml`. A48 must pass every gate:

1. Exact: nominal AUC ≥0.65, AUC ≥0.60 and BA ≥0.58 in each target
   environment.
2. Twenty 1,024-shot deployments: median nominal AUC ≥0.62, its 10th
   percentile ≥0.55, median worst-environment BA ≥0.54, and at most 25% of
   deployments at the preregistered chance definition.
3. Claims: exact deployment has ≥4 SUPPORTED unique claims, ≤50% UNRESOLVED
   and ≥4 far-margin claims; shot deployments have median ≥4 SUPPORTED,
   median ≤60% UNRESOLVED and median ≥6 informative C_dep/C_ideal pairs.
4. Cost: three A48 deployments are ≤70 min centrally and ≤90 min at the high
   estimate.
5. Every physical deployment must be capable of archiving ΔM_S, ΔM_T and
   ΔM_T−ΔM_S on fixed evidence populations. Failure to do so is NO-GO for a
   Proposition-4 instantiation claim.

Any failed hard gate means **ABORT E20**. A missing or corrupt offline artifact
may yield BORDERLINE; a failed threshold may not.

## Frozen physical falsifiers if GO is later authorized

- A physical deployment at the chance/floor definition rejects replicated
  physical stability for that realization; a campaign dominated by that state
  rejects the campaign-level claim.
- Physical variability materially exceeding the shot-only distribution is
  evidence that finite-shot simulation understates physical deployment
  instability.
- If C_dep is not descriptively more stable than C_ideal, no empirical
  direction claim is made.
- Three physical deployments remain descriptive replication, not a population
  law; claims inside a deployment are correlated and never count as replicates.
- Proposition 4 is instantiated only realization by realization where its
  archived sufficient condition is actually evaluable. Condition failure is
  not called a necessary flip, and a few successes are not generalized.
- Failed jobs and calibration drift are archived. There is no replacement run
  unless failure occurred before usable counts existed and the authors approve
  the opportunity cost without inspecting scientific outcomes.
