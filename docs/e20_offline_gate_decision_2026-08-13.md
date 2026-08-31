# E20 offline gate decision — no QPU expenditure

**Decision:** `NO-GO — current paper is already at its useful ceiling`

This decision was reached without connecting to IBM Quantum or submitting a
job (`qpu_jobs_submitted = 0`). The gate configuration was frozen before the
offline run (SHA-256
`2b237305ad5eb0a49ed964d38738899b130dc6e44702bd5533a10bd54e857914`).
The current npj Quantum Information manuscript and submission package are not
changed by E20.

## A. Current hardware limitation

| Study | Evidence size | Circuits / shots | QPU time | Kernel diagnostics | Predictive diagnostic |
|---|---|---:|---:|---|---|
| E09/E16 simulation | 2,000 train; 40,248–41,946 selected target events per environment | no QPU circuits; 128–4,096 simulated shots, three seeds in E09 and five independent Gram deployments per budget in E16 | 0 | exact effective rank 353.36; 128-shot error about 13.7% and rank about 489; 4,096-shot error about 2.4% | exact nominal AUC 0.837; finite-shot AUC remained close, while claim flips were concentrated near boundaries |
| E10 hardware diagnostic | one 32-event Gram; leave-one-out, not a train/test deployment | 496 / 2,048 | 276 s | hardware Frobenius error 17.019% versus a 1.95% mean local shot floor; PSD violation 0; effective rank 29.42 exact to 30.87 hardware | archived LOO accuracy 0.594 exact and 0.531 hardware; derived from the archived Grams, LOO AUC/BA are 0.570/0.594 exact and 0.488/0.531 hardware |
| E16 hardware micro-arm | 28 train, 12 test: six nominal and six TES=0.98 | 378 train + 336 cross = 714 / 1,024 | 200 s | train/cross Frobenius error 12.715%/48.078%; shot-only train error 2.119%; PSD violation 0; effective rank 26.37 exact to 27.22 hardware | target accuracy and BA 0.50 in both exact and hardware deployments. A post-hoc ranking diagnostic gives global AUC 0.806 exact and 0.917 hardware, but both deployments predict only background at the frozen operating point; n=12 makes the AUC unsuitable as performance evidence |

E16 evaluates six claim cells with ten paired audit streams each. Both its
ideal and hardware deployments give 0 SUPPORTED, 55 REFUTED and 5 UNRESOLVED
audit verdicts; all six majority verdicts are REFUTED and there are zero
majority flips. This is the relevant floor effect: the absence of flips is
compatible with fail-closed behavior but has little power to distinguish
deployment-relative from ideal-anchored stability.

For context, E09's exact 20-cell grid contains 10 SUPPORTED and 10 UNRESOLVED
verdicts. Across its 18 shot/seed configurations the descriptive internal-cell
counts are 178 SUPPORTED, 176 UNRESOLVED and 6 REFUTED, with 8/360 flips; those
360 cells are not independent repetitions. The fuller E16 simulation uses 30
independent Gram deployments (five per shot budget). Its far-margin
deployment-relative flip rate is zero in all 30 deployments. Ideal-anchored
far-margin means are non-monotone across intermediate budgets, with endpoint
means 20.8% at 128 shots and 0.4% at 4,096 shots. That simulation evidence is
substantially stronger than the single physical realization.

The hardware therefore supports exactly the current statement:

> micro-scale integration / fail-closed consistency demonstration, not
> hardware performance or certification at scale.

It does not support replicated physical-deployment stability, a population
claim about QPU variability, an empirical direction between
deployment-relative and ideal-anchored stability, or an empirical
instantiation of Proposition 4. E10 is not a full deployment and E16 is one
physical Gram realization at an uninformative operating point.

## B. Candidate E20 design

All candidates preserve the existing eight-qubit feature map, scale 0.5,
two repetitions, linear entanglement, preprocessing, C=1 QK-SVC,
class-balanced training, weighted Platt calibration, BA threshold, claims,
audit streams and C3 semantics. Events are fixed. There is no tuning.

The budget-feasible candidate uses 48 train events, 24 fixed source-validation
events and the same 24 target row IDs evaluated at nominal and TES=0.98. Thus
each physical deployment would estimate one 48×48 train Gram and one 48×72
cross block at 1,024 shots.

| Candidate | Train / calibration / target per environment | Train circuits | Cross circuits | Total | Classical runtime | QPU minutes per deployment | Three deployments |
|---|---:|---:|---:|---:|---:|---:|---:|
| A48 | 48 / 24 / 24 | 1,128 | 3,456 | 4,584 | 7.8 s including full audits | 21.4 [16.8, 29.0] | 64.2 [50.4, 87.1] |
| B64 | 64 / 24 / 24 | 2,016 | 4,608 | 6,624 | 0.3 s, performance gate only | 30.9 [24.3, 42.0] | 92.7 [72.9, 125.9] |
| C80 | 80 / 24 / 24 | 3,160 | 5,760 | 8,920 | 0.3 s, performance gate only | 41.6 [32.7, 56.5] | 124.9 [98.1, 169.5] |

Dense matrix memory is negligible (0.046–0.097 MB), as is the eight-qubit
statevector workspace used offline (0.49–0.62 MB); estimated archived raw
counts are 13.7, 19.8 and 26.6 MB per deployment. QPU intervals use the two
real jobs as anchors and 0.22–0.38 s/circuit at 1,024 shots. They are planning
ranges, not a linear-runtime assertion or a guarantee against backend drift.

A less fragile 48-train design with 48 calibration and 48 target events per
environment would require 8,040 circuits, about 37.5 [29.5, 50.9] min per
deployment and 112.6 [88.4, 152.8] min for three. It therefore cannot provide
the desired replication inside the allocation. The 24-event evidence blocks
in A48 are the largest plausible compromise under the preferred 50–70 minute
campaign budget, and the offline gate tests whether that compromise is
informative enough.

Had A48 passed, the preregistered physical campaign would have used three—not
four—independent deployments. Four A48 deployments have a central estimate of
85.6 min and a high estimate of 116.1 min, leaving inadequate failure margin.

## C. Offline gate results

The fixed gate was run with the exact statevector fidelity kernel and 20
independent 1,024-shot binomial compute–uncompute Gram realizations. The full
C3 audit was applied only to preregistered candidate A48; B64/C80 were cost and
performance scaling diagnostics and cannot replace A48 after seeing results.

| Candidate | Exact AUC nominal / TES | Exact BA nominal / TES | Shot nominal AUC median (range) | Shot worst-environment BA median (range) |
|---|---:|---:|---:|---:|
| A48 | 0.674 / 0.688 | 0.542 / 0.542 | 0.660 (0.639–0.681) | 0.625 (0.500–0.667) |
| B64 | 0.646 / 0.688 | 0.667 / 0.625 | 0.632 (0.604–0.660) | 0.625 (0.500–0.667) |
| C80 | 0.646 / 0.667 | 0.625 / 0.583 | 0.642 (0.618–0.667) | 0.542 (0.500–0.625) |

A48's exact ranking is above chance, but its frozen operating point predicts
positive for only 20.8% of target events (TPR 0.25, TNR 0.833), giving BA
0.542. Its exact audit has 24/24 unique claims REFUTED, 0 SUPPORTED and
0 UNRESOLVED, although 22 are far from their boundaries. Across the 20
shot-only deployments, the median number of SUPPORTED claims remains 0
(range 0–16), the median unresolved fraction is 0.125, and 25% meet the frozen
chance/floor definition. The occasional simulated realization with many
SUPPORTED claims is instability, not a seed to select for hardware.

At the independent-deployment level, A48 has median train-Gram error 3.20%
(range 3.03–3.47%), median effective rank 39.01 versus 39.07 exact, median
deployment-relative flips 3 (range 0–20), and median ideal-anchored flips 2
(range 0–8). These are descriptive distributions over 20 independent noisy
Gram realizations; the 24 claims inside each realization are not replicates.

The fixed calibration subset also has weight effective sample size 11.3 and a
weighted signal fraction of 0.00143. Consequently the exact weighted source
reference is 0.999 while the target weighted accuracy is 0.869. A physical
campaign at this scale would therefore conflate QPU realization variability
with a severe small-calibration/weight-concentration bottleneck.

The mechanical gate fails three hard criteria:

1. exact BA in every environment: 0.542 < 0.58;
2. exact SUPPORTED claims: 0 < 4;
3. median shot-only SUPPORTED claims: 0 < 4.

Cost, AUC, abstention, far-claim, informative-pair and archiveability checks
pass. In particular, ΔM_S, ΔM_T and ΔM_T−ΔM_S can be archived and the
Proposition-4 sufficient conditions can be evaluated realization by
realization. This technical success does not rescue the failed information
gate. Condition failure would not imply a flip, and condition success in a few
deployments would not establish a law.

## D. Scientific value

If the offline gate had passed and three physical deployments reproduced the
shot-only pattern, E20 could have added *replicated descriptive physical-
deployment evidence for C3*, including the previously missing target movement
terms. If hardware were more variable, it could instead show that shot-only
simulation understates physical deployment instability. Either would raise
the quantum-specific evidential ceiling.

The feasible frozen design does not support that upgrade. Because its ideal
deployment is already claim-floor dominated, physical REFUTED stability would
largely repeat E16, while sporadic SUPPORT would be inseparable from threshold
and calibration instability at this evidence size. The experiment could
still produce hardware data, but not a substantially stronger paper claim.

## E. Opportunity cost

The only budget-feasible replicated option consumes about 64% of the new
allocation centrally and could consume 87%. Designs with a larger training
Gram do not materially improve exact AUC and leave the small evidence blocks
unchanged; designs that enlarge calibration/test enough to address that
bottleneck exceed the budget for three deployments. A small `Generic_project`
smoke test cannot change a gate that failed under the exact kernel.

The expected value is therefore lower than reserving the minutes for a paper
whose central claim genuinely requires real-hardware replication. There is no
scientific reason to spend even a pilot QPU job on E20 after the exact gate
failure.

## F. Decision

`NO-GO — current paper is already at its useful ceiling`

**ABORT E20. Submit the current paper without changing its hardware claims.**
No IBM job, `Generic_project` test or main-instance execution is authorized by
this study. Reconsideration would require a new scientific protocol and new
pre-registration, not threshold relaxation, seed selection or a hardware run
performed merely because time is available.

## Reproducibility pointers

- Frozen registration: `docs/e20_preregistration_2026-08-13.md`
- Machine-readable gate: `configs/experiments/E20_offline_gate.yaml`
- Offline runner: `experiments/E20_confirmatory_hardware/run_e20_offline_gate.py`
- Complete deployment-level result: `results/tables/E20_offline_gate.json`
- Immutable current hardware evidence: `results/tables/E10_hardware.json`,
  `results/tables/E16_hw.json`, `results/raw/E10_hw/`, `results/raw/E16_hw/`
