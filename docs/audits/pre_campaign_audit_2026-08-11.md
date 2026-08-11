# Pre-Campaign Falsification Audit — 2026-08-11

Scope: active attempt to falsify the E00–E11 results and manuscript v0.2
before designing and running the final campaign (E12–E16, E04v3, E11v2).
Method: full re-read of `src/qevc` (all 34 modules), all experiment runners
and configs, all result tables, manifests, split artifacts, campaign log,
and the governing docs. This complements (does not repeat) the Phase 10
adversarial review whose findings were already dispositioned in D-016–D-018.

Verdict up front: **no finding invalidates a reported result.** The findings
below are (a) statistical-dependence and provenance weaknesses that the new
campaign must not inherit, and (b) design constraints that E12–E16 are
explicitly built to address. All dispositions are registered as decisions
(D-019 ff.) before any new run.

---

## 1. Findings that shape the campaign design

### F1 — Subset-index provenance is reconstructive, not archival
The only parquet draw ever made (300k rows, `stratified_indices(n=300000,
seed=101)`) is reproducible from `label_codes.npy` + the seed, but the
**global indices were never persisted**; E02R's five replication partitions
(seeds 201–205) exist only as code+seed. Disjointness proofs for a fresh
holdout therefore depend on exact re-execution of NumPy PCG64 code paths.
*Disposition:* D-020 — reconstruct and archive the seed-101 global indices
(and E00's four validation row groups 34/65/146/184); archive every future
draw's indices; E12 samples from the verified complement. Falsifiable
disjointness becomes a stored artifact, not a claim.

### F2 — I1 sensor and I2 label streams share events
E03/E05 compute the geometry sensor on `nominal_test`-role draws and audit
claims with label streams from the same role. The veto can only demote
SUPPORTED→UNRESOLVED, so the empirical Type-I guarantee is not inflated by
this dependence (certification never *increases*), but abstention behavior
and the veto's operating characteristics are measured on statistically
dependent data, and the `auditor_dev` role (45,000 rows, reserved for
exactly this) sits unused.
*Disposition:* D-021 — all new sensor calibration/evaluation draws (E13,
E14, E04v3 floors) move to `auditor_dev`; `nominal_test` remains the claim
population. Existing results stand with the dependence disclosed.

### F3 — Sensor identity was selected after seeing E03 output
`E05.yaml`'s `kernel: quantum, descriptor: mmd2` was fixed after E03's
descriptor tables existed — an analyst-in-the-loop selection over ~36
descriptors. The matched-kernel control already demoted any quantum-specific
sensor claim; what remains unvalidated is generalization of the *selected*
sensor beyond the development grid.
*Disposition:* the sensor family is now frozen (MMD² of the quantum kernel
and of the matched rbf8 kernel; nothing else may be promoted), and E04v3
tests it on 60 out-of-grid environments with leave-one-family-out
calibration — new data the selection never saw. This is the correct
post-selection validation and is registered before any new environment is
generated.

### F4 — The I1 noise floor is a point estimate with no uncertainty
The veto threshold is `max(MMD²)` over the 12 weight-only environments —
one realization, no CI, and the resulting alarm set is non-monotone in
shift magnitude (`soft_met=1.0/seed11` alarms while 2.0/3.0 do not).
*Disposition:* E04v3 re-estimates the floor from repeated `auditor_dev`
draws with a bootstrap distribution and a predeclared quantile rule;
non-monotonicity of the current alarm set is disclosed in the manuscript's
limitations (it is an honest property of a max-rule at the noise floor).

### F5 — `kernel_shots` reuses one fixed seed per call
Every Gram evaluation inside a `QKSVC(shots=...)` re-seeds an identical RNG
(`qksvc.py:42`): train and test Grams get correlated noise realizations, and
re-scoring the same matrix reproduces the identical draw — unlike any
physical device. E09's conclusions (error scaling, rank inflation,
near-boundary flips) are computed on explicitly re-sampled Grams in the
runner and are unaffected; the flag matters for E16, where certificate
stability under *independent* estimation noise is the measurand.
*Disposition:* D-022 — per-call independent substreams (seed sequence
spawning) before E16; E09 numbers stand (their resampling was external to
QKSVC), difference documented.

### F6 — Frozen hyperparameters live in a results artifact
`results/tables/E01_nominal.json` is load-bearing configuration for E02–E11,
revived with `eval(v, {"__builtins__": {}})`; regenerating E01 would
silently redefine every downstream "frozen" model. The clean-tree campaign
made this reproducible in practice, but the freeze is not an artifact.
*Disposition:* D-020 — the campaign freeze snapshots all frozen quantities
(hyperparameters, feature sets, feature-map config, claim grid, sensor
definition, statistical protocol) into `configs/frozen/` as typed YAML/JSON
committed *before* E12 data is drawn. `E01_nominal.json` stays untouched as
the historical record.

### F7 — Weighted estimands are absent from the entire guarantee stack
`empirical_bernstein_cs` hard-requires observations in [0,1] with no
weighting anywhere; the MMD² sensor is unweighted; D-014 scoped the auditor
to unweighted correctness. Nothing wrong — but every physics-facing metric
in the paper is weighted, so the auditor and the metrics speak different
estimands, and weight-only nuisances sit exactly in the gap.
*Disposition:* E13 (spec in `docs/weighted_certification_spec.md`, D-019)
builds the weighted machinery; E14 formalizes what no feature-distribution
evidence can identify and what rate/CR evidence (I3) restores.

## 2. Checks that came back clean

- **Split hygiene (verified on disk):** the five roles of
  `E01_raw_row_v2_seed101_n300000.json` are pairwise disjoint;
  `load_splits` pops `final_eval` unless explicitly touched, and no code
  under `experiments/` or `scripts/` touches it; E02 score archives'
  `row_id` ⊂ nominal_test with zero intersection with `final_eval`; the E10
  hardware subset ⊂ train role.
- **Label leakage into I1:** none found at code level. `describe_environment`
  accepts source labels only; scalers fit on source only; E05 computes
  alarms before labels are indexed; `AngleScaler.transform` has an unfitted
  guard. (Design-level exposures F2/F3 dispositioned above.)
- **CS validity:** implementation matches WSR predictable plug-in EB;
  time-uniform coverage, fail-closed semantics, veto-only-demotes, and
  Type-I control all covered by passing tests (95/95 green today);
  empirical false certification 0.61% ≤ α on 7,820 false-claim streams.
- **Optional stopping:** n* defined via running intersection of an
  anytime-valid CS — legitimate stopping time; no alpha-spending needed.
- **Event weights:** D-010 per-process renormalization verified in loader;
  D-012 training/eval weight separation consistent across models; E08's
  per-process luminosity rescale uses full-file weight sums (correct under
  D-010); bkg_scale AUC-invariance consistency check passed in E02.
- **Multiple comparisons:** per-claim α as the declared unit of inference
  with family-wise counts reported (SAP §3.3); H5 cells are E02R-gated and
  deduplicated; E04 leans on the predeclared out-of-environment falsifier,
  not on per-correlation p-values from correlated environments.
- **Seed robustness:** the five-seed E02R replication corrected two
  single-seed headline patterns, and the corrections are in the manuscript;
  partition variance is quantified and quoted with every small effect.
- **No result deletion:** superseded manifests, failed first runs (E00
  tolerance, E11 lumi bug) and negative results (E07, matched-kernel
  control) are all retained and written up.

## 3. Minor issues logged (no disposition required beyond notes)

- E07's importance-weight rescaling makes the active-vs-uniform comparison
  conservative by construction; the manuscript already reports the negative
  result without over-generalizing it.
- `campaign.log` keeps only each step's last 3 stdout lines; full logs exist
  only for the ad-hoc development runs. Cosmetic.
- `wall_seconds` in manifests is meaningless (manifest constructed after the
  work); real timings live in the result tables. Cosmetic.
- E10's manifest is `git_dirty: true` with no clean counterpart — disclosed
  in D-016 (QPU job not re-executable; provenance archived).
- CMS Level II data is present (~7 GB) but unregistered in `data/README.md`
  — to be fixed alongside E11v2.
- `run_e02.py` acts as a de-facto shared library for nine other runners via
  `sys.path` injection; refactoring is deliberately out of scope during the
  campaign (behavior-preserving only).
