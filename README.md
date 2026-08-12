# When Can Quantum Event Classifiers Be Trusted?

Research codebase for the paper *"When Can Quantum Event Classifiers Be
Trusted? Conditional Validity under Collider Systematics and Quantum
Estimation Uncertainty"*.

**Audited arXiv v1 release (2026-08-12).** The scientific program is closed;
the 26-page manuscript, 7-page supplement and self-contained source package
pass the final audit. The tagged artifacts are public in the
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/arxiv-v1)
and archived at [Zenodo DOI
10.5281/zenodo.21894292](https://doi.org/10.5281/zenodo.21894292). The arXiv
submission package is frozen but has not been submitted; arXiv publication
is deliberately deferred by author decision.

Authors: Roberto Fernández-Barrios, Iker Pastor-López, Asier
González-Santocildes and Pablo García Bringas; Faculty of Engineering,
University of Deusto, Bilbao, Spain. ORCID records are included in
`CITATION.cff` and in both publication PDFs.

**Scientific question.** Under what experimentally available information can
the validity of a quantum event classifier be justified when (i) collider
systematics shift the deployment distribution away from the nominal
simulation on which it was validated, and (ii) the deployed pipeline is
itself estimated (finite-shot / hardware kernels)?

The project does **not** optimize for a positive quantum result — and did
not find one: the matched classical controls retire every quantum-specific
performance and sensing claim, and that negative is kept central. The
contribution is methodological, organized as three claims:

- **C1 — Information-conditional certification (I0→I3):** a fail-closed
  auditor (SUPPORTED / REFUTED / UNRESOLVED) with anytime-valid error
  control, an exact weighted extension for physics-weighted estimands, a
  formal unidentifiability proposition for weight-only nuisances, and label
  costs measured against the Wald information floor.
- **C2 — Scientific-inference validity:** classifier-metric stability does
  not imply valid signal-strength inference; profiled inference restores
  validity exactly where its nuisance model can represent the shift, at a
  measured interval-width price — and fails where it cannot.
- **C3 — Quantum deployment uncertainty:** shot noise and hardware make the
  deployed pipeline a random object; deployment-relative vs ideal-anchored
  claim semantics keep certification valid under that randomness, and the
  measured verdict-flip patterns trace the theory's predictions.

## Governing documents

| Document | Purpose |
|---|---|
| `docs/research_spec.md` | Full execution specification (frozen blueprint) |
| `docs/novelty_matrix.md` | Literature positioning; Gate 0 |
| `docs/dataset_audit.md` | Dataset selection audit; Gate 1 |
| `docs/statistical_analysis_plan.md` | Predeclared statistical protocol |
| `docs/weighted_certification_spec.md` | Weighted anytime-valid certification (D-019) |
| `docs/formal_results.md` | Formal statements + proofs (Theorem 1, Props. 2–4) |
| `docs/experiment_registry.md` | Registry of all experiments (E00–E19; falsifiers frozen before execution) |
| `docs/decisions.md` | Log of every material design decision (D-001…) |
| `docs/audits/` | Pre-campaign, post-campaign and pre-submission falsification audits |

## Experimental levels

- **Level I — Controlled collider world:** FAIR Universe HiggsML Uncertainty
  benchmark (H→ττ with parameterized systematics: TES, JES, soft MET,
  background normalizations). 220M events; multiple provably disjoint
  300k worlds (seeds 101, 121, 131, 141) with archived index proofs.
- **Level II — Real collider world:** CMS Open Data Run2012B+C H→ττ
  simulation-to-real, fail-closed ledger (no event-level truth labels are
  ever fabricated), with calibrated sensor evidence (E11v3).
- **Hardware:** IBM Quantum Open-plan micro-demonstrations (ibm_marrakesh),
  disclosed at their achievable scale — never inflated to "hardware
  validated".

## Self-correction record

Registered falsifiers fired and were obeyed throughout: E02R (single-seed
narrative corrected), E12 arm (e) (flagship cells failed; mechanism
re-scoped), E14 v1 (template statistics), E15 gate (twice), E17 arm (b)
(degradation signs draw-dependent across fresh worlds) — plus audit-forced
corrections (E13 estimand, E16 dual accounting). All preserved, none
hidden; superseded tables are kept as `*_v1_*.json`.

## Repository layout

Code lives in `src/qevc/` (Quantum Event Validity Certification);
experiments are config-driven from `configs/` and registered in
`docs/experiment_registry.md` **before** execution. Results are written to
`results/` with immutable manifests (git commit, config hash, dataset
SHA-256, seeds, package versions). The frozen deployment is
`configs/frozen/frozen_deployment_v1.yaml`.

## Reproducibility

- `environment/requirements-lock.txt` — fully pinned environment
  (Python 3.13, Windows-developed; a best-effort Linux container recipe is
  in `environment/containers/`).
- `scripts/regenerate_all.ps1` — re-executes every simulation experiment
  from one clean commit.
- `pytest` — the guarantee test suite (statistical validity, leakage
  discipline, manifest immutability); data-dependent modules skip
  automatically when the benchmark parquet is absent.
- Data provenance, licenses and archive hashes: `data/README.md`.
  QPU jobs are archived with raw counts and usage records under
  `results/raw/E10_hw/` and `results/raw/E16_hw/`.
