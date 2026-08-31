# Conditional validity of quantum event classifiers under collider systematics and quantum estimation uncertainty

Research codebase for the paper *"Conditional validity of quantum event
classifiers under collider systematics and quantum estimation uncertainty"*.

**npj Quantum Information submission release `0.3.0` (2026-08-31).** The
scientific program is closed: no new dataset, model, configuration, QPU run or
primary result was added. The manuscript, Supplementary Information and
Collection-specific cover letter incorporate the final adversarial review and
pass the mathematical, editorial, journal-format and cross-document gates.
The self-contained submission package is built and independently recompiles;
it has not yet been submitted. The exact release is tagged
[`npjqi-submission-v1`](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1)
and archived as Zenodo version `0.3.0` at
[10.5281/zenodo.22206235](https://doi.org/10.5281/zenodo.22206235). Earlier
`arxiv-v1` artifacts remain public as
the historical pre-submission release in the
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/arxiv-v1)
and archived at [Zenodo DOI
10.5281/zenodo.21894292](https://doi.org/10.5281/zenodo.21894292). The final npj
presentation and its scientific scope are governed by D-036--D-040 and the
[final patch snapshot](docs/audits/final_patch_release_snapshot_2026-08-31.md).

Authors: Roberto Fernández-Barrios, Iker Pastor-López, Asier
González-Santocildes and Pablo García Bringas; Faculty of Engineering,
University of Deusto, Bilbao, Spain. ORCID records are included in
`CITATION.cff` and should be linked through the submission portal; no visual
placeholder is printed in the publication PDFs.

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
  control per fixed claim (not simultaneous/FWER control over the claim grid),
  an exact fixed-threshold reduction for physics-weighted ratio estimands, a
  formal feature-only boundary for weight-only nuisances, and audit-label draw budgets
  contextualized against a Wald-style information yardstick (not an
  optimality bound or universal lower bound).
- **C2 — Scientific-inference validity:** classifier-metric stability does
  not imply valid signal-strength inference; under shared simulation a
  fixed-template profile recovers most representable cells at a measured
  interval-width price, while independent-MC studies show that validity is
  jointly limited by nuisance representability and auxiliary-template quality.
- **C3 — Quantum deployment uncertainty:** finite-shot and noisy quantum
  evaluation adds measurement-induced deployment uncertainty;
  deployment-relative vs ideal-anchored claim semantics preserve per-claim
  validity. Proposition 4 is conditional because E16 did not archive its
  required target movement `ΔM_T` or difference `ΔM_T−ΔM_S`; verdict flips are
  separate empirical evidence, not theory predictions. E16 has five independent
  noisy-kernel deployments per budget; claims within each are correlated, the
  intermediate rates are non-monotonic, and no population trend is claimed.

The closest new collider-QML study, Brown, Spannowsky and Williams
([arXiv:2608.11330](https://arxiv.org/abs/2608.11330)), evaluates frozen
quantum models under controlled detector-inspired feature smearing. This work
does not claim priority for studying collider shift. Its differential scope is
official physically parameterized nuisances including rate-only effects, the
I0--I3 information hierarchy, fail-closed anytime-valid certification,
signal-strength inference, and finite-shot/noisy Gram estimation carried
through the realized deployment.

## npj submission artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 26 | `30CB232B95119CB593DD927A909CD78269B40F8C44F9D69BF04E4E7411A42BD7` |
| `output/pdf/npjqi_supplementary_information.pdf` | 11 | `52904EB164AC6E24409F16911A98639968E726AE6F685023F87F71547513C8AC` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `895AF4A38561D70889863C7C81CBF0F9482455988C25ED9E754D6B2FCBF08E01` |
| `dist/npjqi-submission.zip` | source + 3 PDFs | `B8CF241218C8D472CAC8D7637D706E22120A9F26426CE019CD10D411429BDA96` |

The authoritative checksum file is
`docs/submission/npjqi_checksums.sha256`. The bundle includes the three PDFs,
the self-contained Springer Nature source, figure PDFs and submission metadata.

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
| `docs/submission/npjqi_submission_metadata.md` | Portal metadata, claim guardrails and final author checklist |
| `scripts/verify_npjqi_submission.py` | Executable npj format and disclosure gate |

## Experimental levels

- **Level I — Controlled collider world:** FAIR Universe HiggsML Uncertainty
  benchmark (H→ττ with parameterized systematics: TES, JES, soft MET,
  background normalizations). 220M events; multiple provably disjoint
  300k worlds (seeds 101, 121, 131, 141) with archived index proofs.
- **Level II — Real collider world:** CMS Open Data Run2012B+C H→ττ
  real-data fail-closed case study (no event-level truth labels are
  ever fabricated), with calibrated sensor evidence (E11v3).
- **Hardware:** IBM Quantum Open-plan micro-scale fail-closed consistency
  demonstrations (`ibm_marrakesh`), disclosed at their achievable scale. They
  are not hardware-performance results or certification at scale; the chance-
  performance REFUTED/UNRESOLVED composition creates an explicit floor effect.

## Self-correction record

Registered falsifiers fired and were obeyed throughout: E02R (single-seed
narrative corrected), E12 arm (e) (flagship cells failed; mechanism
re-scoped), E14 v1 (template statistics), E15 gate (twice), E17 arm (b)
(degradation signs draw-dependent across fresh worlds) — plus audit-forced
corrections (E13 estimand, E16 dual accounting). All preserved, none
hidden; superseded tables are kept as `*_v1_*.json`. The 2026-08-13 revision
also corrects Proposition 4's missing stability premise, formalizes I1 as a
count-conditioned feature experiment, retires IID environment p-values, and
reports E16 by deployment in `E16_deployment_level.json`.

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
