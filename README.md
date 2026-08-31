# Conditional validity of quantum event classifiers under collider systematics and quantum estimation uncertainty

Research codebase for the paper *"Conditional validity of quantum event
classifiers under collider systematics and quantum estimation uncertainty"*.

**npj Quantum Information submission release `0.3.2` (2026-08-31).** The
scientific program is closed: no new dataset, model, configuration, QPU run or
primary result was added. The manuscript, Supplementary Information and
Collection-specific cover letter incorporate the final adversarial review and
pass the mathematical, editorial, journal-format and cross-document gates.
The self-contained submission package is built and independently recompiles;
it has not yet been submitted. The exact release is tagged
[`npjqi-submission-v1.2`](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.2)
and archived as Zenodo version `0.3.2` at
[10.5281/zenodo.22214449](https://doi.org/10.5281/zenodo.22214449). The
historical `0.3.1 / npjqi-submission-v1.1` PSD-audited release is preserved in
its [GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.1)
and at [10.5281/zenodo.22209367](https://doi.org/10.5281/zenodo.22209367). The
historical `0.3.0 / npjqi-submission-v1` release remains unchanged in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1)
and at [10.5281/zenodo.22206235](https://doi.org/10.5281/zenodo.22206235).
Earlier
`arxiv-v1` artifacts remain public as
the historical pre-submission release in the
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/arxiv-v1)
and archived at [Zenodo DOI
10.5281/zenodo.21894292](https://doi.org/10.5281/zenodo.21894292). The final npj
presentation and its scientific scope are governed by D-036--D-043, the
[final patch snapshot](docs/audits/final_patch_release_snapshot_2026-08-31.md),
the [technical PSD audit](docs/audits/final_technical_psd_patch_2026-08-31.md),
and the [final logical-closure audit](docs/audits/final_logical_closure_2026-08-31.md).

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
contribution is methodological, organized as three contributions:

- **Contribution 1 — Information-conditional certification (I0→I3):** a fail-closed
  auditor (SUPPORTED / REFUTED / UNRESOLVED) with anytime-valid error
  control per fixed I2 label-stream claim, conditional on the frozen finite
  audit population under declared with-replacement sampling (not
  simultaneous/FWER control over the claim grid). I3 inference is separately
  coverage-gated, while CMS and other empirical ledgers use their own
  calibrated tests and information constraints rather than inheriting the I2 theorem,
  an exact fixed-threshold reduction for physics-weighted ratio estimands, a
  formal feature-only boundary for weight-only nuisances, and audit-label draw budgets
  contextualized against a Wald-style information yardstick (not an
  optimality bound or universal lower bound).
- **Contribution 2 — Scientific-inference validity:** classifier-metric stability does
  not imply valid signal-strength inference; under shared simulation a
  fixed-template profile recovers most representable cells at a measured
  interval-width price, while independent-MC studies show that validity is
  jointly limited by nuisance representability and auxiliary-template quality.
- **Contribution 3 — Quantum deployment uncertainty:** finite-shot and noisy quantum
  evaluation adds measurement-induced deployment uncertainty;
  deployment-relative vs ideal-anchored claim semantics preserve per-claim
  validity. The final deterministic replay reconstructs Proposition 4's
  `ΔM_S`, `ΔM_T` and `ΔM_T−ΔM_S` exactly for all 7,200 raw/PSD condition cells.
  Its sufficient condition holds in 68.7% and discriminates paired-stream
  verdict flips (9.2% when it holds versus 60.4% when it fails), while remaining
  sufficient rather than necessary. The classification is **INFORMATIVELY INSTANTIATED**.
  E16 has five independent
  noisy-kernel deployments per budget; claims within each are correlated, the
  intermediate rates are non-monotonic, and no population trend is claimed.
  A post-hoc final technical audit found all 30 raw training Grams indefinite.
  Every evaluated far-margin deployment-relative claim is true and remains
  supported across raw and PSD-repaired realizations; the grid contains no
  false far-margin claim with which to test refutation stability. Minimum
  diagonal loading changes several ideal-anchored magnitudes; the declared
  robustness verdict is **PSD-SENSITIVE-BUT-SCOPED**. The historical raw
  pipeline remains primary: it is an SVC fit to an indefinite realized
  similarity matrix, not interpreted as a standard convex RKHS SVM. The loaded
  training block gives a convex precomputed-SVM problem but is a post-hoc
  regularized similarity matrix—not a normalized fidelity Gram or a claimed
  global Mercer kernel. The complete derived analyses are archived in
  `results/tables/E16_psd_sensitivity.json` and
  `results/tables/E16_proposition4_instantiation.json`.

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
| `output/pdf/npjqi_manuscript.pdf` | 27 | `E860D76B2AF5A7E3804722EF845B57F7A916261DBEB655DF3293762E1226DCC5` |
| `output/pdf/npjqi_supplementary_information.pdf` | 12 | `619DDEFD3D697FD1E42F0CC91B6BD51365E27597FE6CE986833382CA17C2D542` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `A9589B2630BA908FE31F831F33BA9DF22566A15F45B5A15B08475FB95DBE3E19` |
| `dist/npjqi-submission.zip` | source + 3 PDFs | `EF85DC6811F9C9207DC072A34A570E873FB3C23887A8ECAC4C869700DE27699C` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |

The authoritative checksum file is
`docs/submission/npjqi_checksums.sha256`. The bundle includes the three PDFs,
the self-contained Springer Nature source, figure PDFs, submission metadata
and the complete derived PSD-sensitivity and Proposition 4 JSON artifacts.

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
The final technical patch additionally replays all 30 E16 realizations,
audits their spectra, and refits the declared minimum-diagonal-loading
sensitivity without new randomness or QPU work. The 0.3.2 closure replay also
instantiates Proposition 4 from those reconstructed frozen deployments; it
adds no experiment, seed, sample, model, likelihood or hardware job.

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
