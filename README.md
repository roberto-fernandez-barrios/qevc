# Conditional validity of quantum event classifiers under collider systematics and quantum estimation uncertainty

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21894291.svg)](https://doi.org/10.5281/zenodo.21894291)
[![Tests](https://github.com/roberto-fernandez-barrios/qevc/actions/workflows/tests.yml/badge.svg)](https://github.com/roberto-fernandez-barrios/qevc/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Research codebase for the paper *"Conditional validity of quantum event
classifiers under collider systematics and quantum estimation uncertainty"*.

**npj Quantum Information submission release `0.3.9` (2026-09-02).** The
scientific program is closed: no new dataset, model, configuration, seed, QPU
run or primary result was added. Version 0.3.9 is a figure-legibility and
final literature / prior-art patch on 0.3.8: seven figures are re-rendered to
fix label overlap and clipping (no data change), the panel labels and
Supplementary Table S2 layout are repaired, and a bounded citation patch adds
Alexe et al. (Nucl. Instrum. Methods A 1086, 171360, 2026), Miroszewski
(arXiv:2605.22275) and Howard et al. (Ann. Statist. 49, 1055--1080, 2021),
updates the FAIR Universe reference to its NeurIPS 2025 Datasets and
Benchmarks version of record and the without-replacement
confidence-sequence reference to its NeurIPS 2020 version of record, with
three compact positioning sentences and no new priority claim. No number,
table value, result JSON or scientific claim changed. The manuscript, Supplementary
Information and Collection-specific cover letter pass the mathematical,
editorial, journal-format and cross-document gates. The self-contained
submission package is built and independently recompiles; it has not yet been submitted. The exact release is tagged
[`npjqi-submission-v1.9`](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.9)
and archived as Zenodo version `0.3.9` at
[10.5281/zenodo.22254835](https://doi.org/10.5281/zenodo.22254835). The
historical `0.3.8 / npjqi-submission-v1.8` editorial focus / concision patch
is preserved in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.8)
and at [10.5281/zenodo.22250951](https://doi.org/10.5281/zenodo.22250951). The
historical `0.3.7 / npjqi-submission-v1.7` wording micro-patch is preserved in
its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.7)
and at [10.5281/zenodo.22236115](https://doi.org/10.5281/zenodo.22236115). The
historical `0.3.6 / npjqi-submission-v1.6` mechanistic-clarity release is
preserved in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.6)
and at [10.5281/zenodo.22235287](https://doi.org/10.5281/zenodo.22235287). The
historical `0.3.5 / npjqi-submission-v1.5` submission-hygiene release is
preserved in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.5)
and at [10.5281/zenodo.22231469](https://doi.org/10.5281/zenodo.22231469). The
historical `0.3.4 / npjqi-submission-v1.4` release is preserved in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.4)
and at [10.5281/zenodo.22229290](https://doi.org/10.5281/zenodo.22229290). The
historical `0.3.3 / npjqi-submission-v1.3` release is preserved in its
[GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.3)
and at [10.5281/zenodo.22227158](https://doi.org/10.5281/zenodo.22227158). The
historical `0.3.2 / npjqi-submission-v1.2` logical-closure release is preserved
in its [GitHub release](https://github.com/roberto-fernandez-barrios/qevc/releases/tag/npjqi-submission-v1.2)
and at [10.5281/zenodo.22214449](https://doi.org/10.5281/zenodo.22214449). The
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
  Here deployment means a frozen finite-population batch deployment evaluated
  against a finite, frozen audit population, not a continually re-estimated
  online kernel service or an unspecified future superpopulation.
- **Contribution 2 — Scientific-inference validity:** classifier-metric stability does
  not imply valid signal-strength inference. At the studied MC size, the
  evaluated archived fixed-template construction can lose coverage, including
  in shift-free nominal controls, when templates are estimated independently;
  under shared simulation the same construction can appear to recover
  representable cells, a conditional diagnostic that does not establish
  validity. Validity is jointly limited by nuisance representability and
  auxiliary-template quality.
- **Contribution 3 — Quantum deployment uncertainty:** finite-shot and noisy quantum
  evaluation adds measurement-induced deployment uncertainty;
  deployment-relative vs ideal-anchored claim semantics preserve per-claim
  validity. The final deterministic replay reconstructs Proposition 3's
  `ΔM_S`, `ΔM_T` and `ΔM_T−ΔM_S` exactly for all 7,200 raw/PSD condition cells.
  The pooled, correlated cell-level condition holds in 68.7% and discriminates
  paired-stream verdict flips (9.2% when it holds versus 60.4% when it fails),
  while remaining sufficient rather than necessary. A deployment-level summary
  now reports median, IQR and range across the 30 noisy-kernel deployments,
  which are the descriptive units. The classification is
  **INFORMATIVELY INSTANTIATED**. E16 has five noisy-kernel deployments per
  budget; claims within each are correlated, the intermediate rates are
  dominated by single deployments (heterogeneity and outlier sensitivity), and
  no population trend is claimed. A deterministic stage decomposition of the
  same 30 deployments and their loaded counterparts gives a mixed picture: in
  the primary raw pipeline the realized decision function keeps the ideal
  ranking moderately well (median Spearman 0.92) and AUC barely moves,
  recalibration at a fixed probability threshold generates almost all
  far-margin ideal-anchored flips, and threshold refreezing partly compensates
  them (raw regime MIXED), whereas the loaded sensitivity is
  MODEL/RANKING-dominated through a decision-function scale change; the
  overall classification is MIXED and no universal downstream mechanism is
  claimed across kernel treatments. The weighted balanced accuracy that
  selects the operating point is more stable than the audited accuracies. The
  measurement-induced origin is the upstream finite-shot perturbation; the
  downstream mechanism need not be quantum-specific.
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
  `results/tables/E16_proposition4_instantiation.json`; the deployment-level
  derivative is `results/tables/E16_proposition4_deployment_summary.json`. The
  version-0.3.6 derived analyses are `results/tables/E16_stage_decomposition.json`,
  `results/tables/E16_prop3_margin_stratification.json` and
  `results/tables/E13_wmax_nominal_bound_sensitivity.json` (no new randomness).

The closest new collider-QML study, Brown, Spannowsky and Williams
([arXiv:2608.11330](https://arxiv.org/abs/2608.11330)), evaluates frozen
quantum models under controlled detector-inspired feature smearing. This work
does not claim priority for studying collider shift. Its differential scope is
official physically parameterized nuisances including rate-only effects, the
I0--I3 information hierarchy, fail-closed anytime-valid certification,
signal-strength inference, and finite-shot/noisy Gram estimation carried
through the realized deployment.

Two additional adjacent references delimit rather than expand the claims.
Agliardi et al. ([npj Quantum Information 12, 12
(2026)](https://doi.org/10.1038/s41534-025-01154-2)) treat loss of PSD in
finite/noisy quantum-kernel matrices and use negative-eigenvalue clipping for
a PSD projection; this repository retains its historical RAW-INDEFINITE
pipeline and declares minimum diagonal loading only as a post-hoc sensitivity,
not a repair benchmark. He, Krause and Wang
([arXiv:2509.00672v1](https://arxiv.org/abs/2509.00672v1)) train a
systematics-aware learner on FAIR-HUC for profile-likelihood signal-strength
inference. This paper instead freezes the learner, audits I0--I3 claim validity
and adds finite-shot/noisy quantum deployment uncertainty.

## npj submission artifacts

| Artifact | Pages | SHA-256 |
|---|---:|---|
| `output/pdf/npjqi_manuscript.pdf` | 31 | `8A044E206176F966062666D40A17C6F7FC1F007E4AA0B9618A727EA7B5E745CA` |
| `output/pdf/npjqi_supplementary_information.pdf` | 18 | `F442F1F5A6FF54590B3FEA94929B84DC5ED6E7F4ACBDC436458215D1F788A977` |
| `output/pdf/npjqi_cover_letter.pdf` | 1 | `CBE6FA5ACC444C149082E795A44628866E2C4E22FC40373E38AB85994AF73FA4` |
| `dist/npjqi-submission.zip` | source + 3 PDFs | `CB53CBC6320EE4E6838DD8BC06611622D40C1C2DAB4A1995E2895219033A0A0E` |
| `results/tables/E16_psd_sensitivity.json` | 30 deployments | `5EDE2C056327DFB5768933C7BEE78A662C9E257011EF39984151E163170AABF1` |
| `results/tables/E16_proposition4_instantiation.json` | 7,200 condition cells | `E98FF0E9E160E172DFC4DA69D8B5645D5E5A98C7BF8654CEF3BFD16ADF07115B` |
| `results/tables/E16_proposition4_deployment_summary.json` | 30 noisy-kernel deployments | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |
| `results/tables/E16_stage_decomposition.json` | 30 RAW + 30 PSD deployments, 4 stages | `F91D4200D2375368E8E21553B00E81F63071C85288FEEB83A848AC82DB6826D5` |
| `results/tables/E16_prop3_margin_stratification.json` | 7,200 condition cells | `8C3A654B7B6C7C7B50CA13104F37A117D7F54F0C942799203D12CD7E96692043` |
| `results/tables/E13_wmax_nominal_bound_sensitivity.json` | E13 Part B + E19 weighted arm | `8B72B4F9B9CC646473E1DAF707D68BA3BCF9516CA10F210E6B69674408C4ADB5` |

The authoritative checksum file is
`docs/submission/npjqi_checksums.sha256`. The bundle includes the three PDFs,
the self-contained Springer Nature source, figure PDFs, submission metadata
and the complete derived PSD-sensitivity, Proposition 3, deployment-summary,
stage-decomposition, margin-stratification and weight-bound-sensitivity JSON
artifacts.

## Governing documents

| Document | Purpose |
|---|---|
| `docs/research_spec.md` | Full execution specification (frozen blueprint) |
| `docs/novelty_matrix.md` | Literature positioning; Gate 0 |
| `docs/dataset_audit.md` | Dataset selection audit; Gate 1 |
| `docs/statistical_analysis_plan.md` | Predeclared statistical protocol |
| `docs/weighted_certification_spec.md` | Weighted anytime-valid certification (D-019) |
| `docs/formal_results.md` | Formal statements + proofs (Proposition 1, Theorem 1, Props. 2–3) |
| `docs/experiment_registry.md` | Registry of all experiments (E00–E19; falsifiers frozen before execution) |
| `docs/decisions.md` | Log of every material design decision (D-001…) |
| `docs/audits/` | Pre-campaign, post-campaign and pre-submission falsification audits |
| `docs/submission/npjqi_submission_metadata.md` | Portal metadata, claim guardrails and final author checklist |
| `scripts/verify_npjqi_submission.py` | Executable npj format and disclosure gate |
| `scripts/verify_release_consistency.py` | Release gate for version/DOI/tag, real PDF page counts, hashes, ZIP and manifest |
| `scripts/analyze_e16_stage_decomposition.py` | Deterministic E16 stage decomposition (derived, no new randomness; 0.3.6) |
| `scripts/summarize_e16_prop3_margin_stratification.py` | Proposition-3 margin stratification of the frozen instantiation (0.3.6) |
| `scripts/analyze_wmax_nominal_bound_sensitivity.py` | Sharp-nominal-bound sensitivity of the weighted certification on frozen streams (0.3.6) |

## Experimental levels

- **Level I — Controlled collider world:** FAIR Universe HiggsML Uncertainty
  benchmark (H→ττ with parameterized systematics: TES, JES, soft MET,
  background normalizations). 220M events; four 300k worlds verified
  row-disjoint by construction (seeds 101, 121, 131, 141), with archived index
  proofs; no probabilistic independence claim is made from row disjointness.
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
Version 0.3.3 adds only the two adjacent references, scope wording and a
deterministic deployment-level aggregation of the frozen Proposition 4 JSON.
Version 0.3.4 adds only the historical-gate interpretation correction, two
finite-shot quantum-kernel references, retrospective wording for the frozen
Proposition 4 replay, Tier-A Gram shot accounting and objective Supplement
filename wrapping. Scientific artifacts remain byte-identical to 0.3.3.
Version 0.3.5 changes submission hygiene only: natural formal-result numbering,
the cover-letter date, release-document synchronization and a 0.5 pt
bibliography-spacing microadjustment. The scientific baseline remains
byte-identical to 0.3.4.
Version 0.3.6 is the mechanistic-clarity / derived-analysis patch: it replays
the 30 frozen E16 deployments through diagnostic counterfactual stages (fit,
evaluation, calibration, threshold) and classifies the amplification under a
predeclared rule (MIXED overall: recalibration generates almost all far-margin
ideal-anchored flips in the raw pipeline and threshold refreezing partly
compensates them; diagonal loading acts through a decision-function scale
change), stratifies the Proposition-3 instantiation by margin, measures the
price of the deliberate 2.05 weight-bound conservatism on identical frozen
streams, and applies the corresponding framing and editorial corrections. No
experiment, seed, sample, model, threshold rule, PSD repair, likelihood, CMS
analysis or QPU job was added; the primary scientific artifacts remain
byte-identical to 0.3.5.
Version 0.3.7 changes wording only: the Contribution-3 mechanism statement is
made regime-specific in the abstract, Introduction, Results, Discussion, cover
letter and Supplement, so that it cannot be read as one downstream mechanism
dominating both the raw pipeline and the diagonal-loading sensitivity. No
number, JSON artifact, seed, result or gate expectation changed.
Version 0.3.8 is an editorial focus / concision patch: main-text shortening
and de-jargonization with no change to any number, figure file or artifact.
Version 0.3.9 re-renders seven figures for label legibility and applies the
audited final literature / prior-art citation patch (Alexe 2026, Miroszewski
2026 and Howard 2021 added; FAIR Universe and the without-replacement
confidence-sequence reference updated to their versions of record; three
compact positioning sentences, no new priority claim). The scientific JSON
artifacts remain byte-identical; only the re-rendered figure files changed.

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

## How to cite

If you use this code or its derived results, cite the Zenodo archive: the
concept DOI [10.5281/zenodo.21894291](https://doi.org/10.5281/zenodo.21894291)
always resolves to the latest version, and the version DOI
[10.5281/zenodo.22254835](https://doi.org/10.5281/zenodo.22254835) pins
release 0.3.9. GitHub's "Cite this repository" button uses `CITATION.cff`.

```bibtex
@software{qevc,
  author  = {Fern{\'a}ndez-Barrios, Roberto and Pastor-L{\'o}pez, Iker and
             Gonz{\'a}lez-Santocildes, Asier and Garc{\'i}a Bringas, Pablo},
  title   = {qevc: Quantum Event Validity Certification},
  year    = {2026},
  version = {0.3.9},
  doi     = {10.5281/zenodo.22254835},
  url     = {https://doi.org/10.5281/zenodo.21894291}
}
```

The associated manuscript is under submission to *npj Quantum Information*;
this section will link the version of record upon publication.

## License

The code is released under the [MIT License](LICENSE). The FAIR Universe
HiggsML Uncertainty dataset (CC-BY-4.0) and the CMS Open Data records (CC0)
retain their own licenses and terms; see `data/README.md`.
