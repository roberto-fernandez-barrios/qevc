# Decision Log

Every material design decision is recorded here before or at the moment it takes
effect. Format: ID, date, decision, alternatives considered, rationale, status.

---

## D-001 — Package layout deviates cosmetically from spec §26

- **Date:** 2026-08-10
- **Decision:** Source code lives in `src/qevc/<module>/` (an installable package,
  `qevc` = Quantum Event Validity Certification) rather than bare `src/<module>/`
  directories as drawn in spec §26.
- **Alternatives:** bare `src/data`, `src/models`… as literal spec layout.
- **Rationale:** bare top-level modules named `data`, `statistics`, `inference`
  shadow stdlib/common package names and are not pip-installable; the spec's module
  set is preserved 1:1 under the package root. No scientific definition altered.
- **Status:** adopted.

## D-002 — Quantum stack: Qiskit

- **Date:** 2026-08-10
- **Decision:** Qiskit (+ qiskit-machine-learning FidelityQuantumKernel /
  FidelityStatevectorKernel, qiskit-aer for finite-shot simulation,
  qiskit-ibm-runtime for the E10 hardware phase).
- **Alternatives:** PennyLane (+ lightning simulators; hardware via plugins).
- **Rationale:** direct path from identical circuit definitions to statevector
  (exact), Aer shot-based (finite-shot), and IBM QPU execution — exactly the
  K_exact / K_shots / K_hw comparison required by spec §18–19 with one codebase.
  Kernel entries are also computable from raw counts, so no framework lock-in for
  the estimator. PennyLane remains a fallback if Qiskit's Python 3.13 support on
  Windows proves problematic (see D-003 risk).
- **Status:** adopted.

## D-003 — Local environment: Python 3.13 venv on Windows; heavy runs CPU-parallel

- **Date:** 2026-08-10
- **Decision:** Develop against the machine's Python 3.13 in a project venv
  (`.venv`). Kernel-matrix computation parallelized over the 20 CPU cores.
  No GPU assumed. If any dependency lacks 3.13 wheels on Windows, pin the affected
  component in a container or downgrade the venv to 3.12 and record it here.
- **Status:** adopted; risk logged.

## D-004 — License MIT; authorship

- **Date:** 2026-08-10
- **Decision:** Code under MIT, author Roberto Fernández Barrios. Dataset licenses
  tracked separately per dataset in `docs/dataset_audit.md` (CERN Open Data is
  CC0; FAIR Universe license recorded on audit).
- **Status:** adopted.

## D-005 — Statistical backbone of the auditor: anytime-valid confidence sequences

- **Date:** 2026-08-10
- **Decision:** Claim resolution in the conditional auditor (spec §13–14) will be
  built on time-uniform / anytime-valid confidence sequences for bounded means
  (betting-style CS, Waudby-Smith–Ramdas family) rather than fixed-n Hoeffding or
  naive repeated binomial tests.
- **Alternatives:** fixed-n Clopper–Pearson per budget point (invalid under
  optional stopping across the n-grid); Hoeffding bounds (valid but loose);
  post-hoc bootstrap (no finite-sample guarantee).
- **Rationale:** n* — the minimum label budget at which a claim resolves — is by
  construction a stopping time. Only anytime-valid inference keeps Type-I error
  control when labels are inspected sequentially, and it composes correctly with
  the active-acquisition arm (via importance-weighted supermartingales). This is
  also the technical answer to Gate 4: the auditor issues statistically valid
  claim resolutions with explicit error control, not an OOD score.
- **Status:** adopted, pending detail in `docs/statistical_analysis_plan.md`.

## D-006 — Fail-closed semantics fixed up front

- **Date:** 2026-08-10
- **Decision:** SUPPORTED requires the (1−α) lower confidence bound of the claim
  metric to clear the claim threshold; REFUTED requires the upper bound to fall
  below it; everything else is UNRESOLVED. Heuristic sensors (geometry, I0/I1
  scores) can *only* move a claim toward UNRESOLVED or trigger label acquisition —
  they can never move a claim to SUPPORTED. Guarantees only ever come from labeled
  target evidence (I2/I3).
- **Rationale:** spec §4-H4, §13, §34: heuristics must never be laundered into
  certificates.
- **Status:** adopted (frozen; changing this requires a new decision entry).
