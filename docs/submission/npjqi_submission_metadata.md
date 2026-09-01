# npj Quantum Information submission metadata

Status: final micro-patch release on 2026-09-01; not yet submitted.

- Release version: `0.3.4` / `npjqi-submission-v1.4`
- Version DOI: `10.5281/zenodo.22229290`
- Historical `0.3.3` / `npjqi-submission-v1.3` DOI:
  `10.5281/zenodo.22227158`
- Historical `0.3.2` / `npjqi-submission-v1.2` DOI:
  `10.5281/zenodo.22214449`
- Historical `0.3.1` / `npjqi-submission-v1.1` DOI:
  `10.5281/zenodo.22209367`
- Historical `0.3.0` / `npjqi-submission-v1` DOI:
  `10.5281/zenodo.22206235`
- Historical `0.2.0` / `arxiv-v1` DOI: `10.5281/zenodo.21894292`

## Destination

- Journal: *npj Quantum Information*
- Content type: Article
- Collection: *Quantum machine learning: understanding capabilities,
  limitations, and perspectives for quantum advantage*
- Collection deadline verified on the official page: 31 December 2026
- Corresponding author: Roberto Fernández-Barrios
- Corresponding email: roberto.fernandez.b@deusto.es

## Title

Conditional validity of quantum event classifiers under collider systematics
and quantum estimation uncertainty

Compliance: 13 words; no punctuation, idiom, or pun.

## Abstract

Claims made by deployed quantum machine-learning classifiers can fail under
target shift or when finite-shot quantum evaluation randomizes the model. We
develop an information-conditional, fail-closed framework returning supported,
refuted or unresolved verdicts. Anytime-valid error control applies to each
fixed I2 label-stream claim, conditional on the frozen finite audit population
under declared with-replacement sampling; I3 and CMS procedures are separately
coverage-gated or calibrated. On a Higgs-to-tau-tau benchmark, we give an exact
fixed-threshold reduction for physics-weighted ratio claims and a feature-only
identifiability boundary. Stable classifier metrics do not ensure
signal-strength coverage. Finite-shot deployments propagate each realized Gram
through refitting, calibration and thresholding. Deterministic replay
instantiates the sufficient sign-stability bound and shows that it discriminates
observed instability while remaining sufficient rather than necessary. All evaluated far-margin
deployment-relative claims were true and remained supported across raw and
PSD-repaired realizations. Matched classical controls remove apparent
quantum-specific performance and sensing effects. We claim no quantum
advantage.

Compliance: at most 150 words by the repository verifier; no citations,
equations, or subheadings.

## Keywords

1. quantum machine learning
2. quantum kernels
3. conditional certification
4. collider systematics
5. distribution shift
6. scientific inference

## Editorial significance statement

The manuscript establishes when claims made by deployable quantum event
classifiers are identifiable and certifiable from the information available at
deployment. It integrates the scientific uncertainty shared by classical and
quantum pipelines with the additional measurement-induced uncertainty of
finite-shot quantum-kernel evaluation, then tests the distinction through
physics-level inference, matched classical controls, CMS open data, and a
micro-scale IBM QPU deployment. It explicitly does not claim quantum advantage.

## Three contributions for portal fields

1. An exact fixed-threshold reduction for the physics-weighted ratio estimands
   and a feature-only identifiability boundary make certification conditional on the information actually
   observable, with per-claim rather than family-wise error control.
2. Signal-strength validity is shown to depend jointly on nuisance
   representability and auxiliary-template quality, even when classifier
   metrics remain stable.
3. Deployment-relative and ideal-anchored QML claims separate scientific shift
   from measurement-induced deployment uncertainty; archived shot and hardware
   studies quantify the latter without asserting quantum advantage.

## Scientific guardrails

- Historical alpha-plus-three-sigma implementation gates used binomial
  heuristics over stream/cell counts. Because pooled streams share audit draws,
  deployments, claims and thresholds, those quantities are not interpreted as
  IID sampling standard errors or confidence boundaries. Formal validity is
  per fixed claim from the confidence sequence; pooled rates are descriptive.
- Proposition 4 is informatively instantiated by deterministic replay: all
  7,200 condition cells are evaluable, 68.7% satisfy the sufficient inequality,
  and paired-stream flips are 9.2% when it holds versus 60.4% when it fails.
  Failure remains non-predictive because the condition is sufficient, not
  necessary; cell/stream counts are correlated within deployment.
- The E16 instantiation is retrospective: target movements are reconstructed
  from frozen target rows after deployment. It diagnoses observed deployment
  stability and is not a prospective operational pre-audit certificate.
- Same-verdict stability additionally requires the corresponding sign-stability
  condition, both audits to cover and both to resolve; two level-alpha audits
  give a 2-alpha union bound, or alpha jointly when each uses alpha/2.
- Observed verdict flips are descriptive comparisons, not deterministic theorem
  predictions or independent replications.
- The deployment-level derivative aggregates only the frozen Proposition 4
  JSON. It reports median, IQR, range, mean and sample SD across 30 noisy-kernel
  deployments; no population inference or new independence assumption is
  introduced.
- The anytime-valid guarantee applies per fixed I2 label-stream claim and
  stopping time, conditional on the frozen finite audit population under
  declared with-replacement sampling; it is not simultaneous/FWER control.
  I3 inference is separately coverage-gated, and CMS/other ledgers use their
  own calibrated tests and information constraints.
- The IBM run is a micro-scale fail-closed consistency demonstration, not a
  performance result or certification at scale.
- E16 has five noisy-kernel deployments per shot budget. Claims
  within each deployment are correlated; reported rates/ranges are descriptive
  and no monotonic trend or population interval is claimed.
- At n=2,000, the analytic-diagonal symmetric training block has 1,999,000
  distinct off-diagonal evaluations: 255,872,000 shots at 128 per entry and
  8,187,904,000 at 4,096. These training-only counts exclude cross-Grams and
  are not a wall-clock, scalable-deployment or quantum-advantage estimate.
- All 30 historical finite-shot training Grams are indefinite. A post-hoc
  minimum-diagonal-loading sensitivity preserves support for every evaluated
  far-margin deployment-relative claim but changes several ideal-anchored magnitudes;
  the result is PSD-SENSITIVE-BUT-SCOPED, not repair-invariant.
- Alternative PSD projections, including negative-eigenvalue clipping used in
  prior noisy quantum-kernel work, may yield different quantitative
  deployments. The diagonal-loading analysis is a declared robustness
  sensitivity, not an optimization or comparison of repair strategies.
- Every evaluated far-margin deployment-relative claim is true; the grid has no
  false far-margin claim with which to assess refutation stability.
- n* is a with-replacement audit-label draw budget, not a unique-event labeling
  cost. Real CMS event truth cannot be queried.
- At the studied MC size, the evaluated archived fixed-template construction
  can lose coverage under independent-MC template noise. MC/template-
  uncertainty-aware likelihood constructions are outside scope.
- Deployment denotes a frozen finite-population batch deployment evaluated
  against a finite, frozen audit population, not a continually re-estimated
  online kernel service or an unspecified future superpopulation.
- The matched classical control removes apparent quantum-specific performance
  and sensing effects; no quantum advantage is claimed.
- Brown, Spannowsky and Williams (arXiv:2608.11330) now provide directly
  adjacent collider-QML evidence under controlled detector-inspired feature
  smearing. This manuscript therefore makes no priority claim for studying
  collider deployment shift; its differential scope is the official
  shape/rate nuisance family, I0--I3 hierarchy, fail-closed anytime-valid
  certification, signal-strength propagation, and realized noisy-Gram
  deployment semantics.
- Agliardi et al., *npj Quantum Information* 12, 12 (2026), DOI
  `10.1038/s41534-025-01154-2`, provide the adjacent finite/noisy quantum-kernel
  PSD projection work; the present RAW/diagonal-loading analyses are not
  represented as equivalent to their clipping construction.
- Shastry et al., arXiv:2210.06971v3, connect finite-shot kernel uncertainty
  to margins, reliability and shot complexity; Gentinetta et al., *Quantum* 8,
  1225 (2024), DOI `10.22331/q-2024-01-11-1225`, analyze shot-noise-driven
  QSVM solution complexity. The present novelty claim is integration through
  refit, recalibration, threshold freezing, scientific claim semantics,
  fail-closed resolution and downstream inference, not first propagation of
  kernel-estimation noise into a classifier.
- He, Krause and Wang, arXiv:2509.00672v1, study a systematics-aware FAIR-HUC
  learner for profile-likelihood signal-strength inference. The present paper
  freezes the learner and audits I0--I3 claim and scientific-inference validity,
  including finite-shot/noisy quantum deployment uncertainty.

## Related-manuscript disclosure

The same authors have released *Sharp Target-Domain Certificates for
Quantum-Kernel Advantage under Distribution Shift*, Zenodo DOI
10.5281/zenodo.21776862. It is currently public preprint/Zenodo material and
has not been submitted to any journal. It studies partial identification and
certification of predictive advantage under target-domain shift. The present
paper studies scientific claim validity under collider systematics, incomplete
information, downstream physics inference and measurement-induced quantum
deployment uncertainty. The works share no datasets, experiments, theorems,
estimands, codebase, or results and are not simultaneously under consideration.

## Upload set

- Main manuscript PDF with figures embedded and line numbers.
- Single Supplementary Information PDF.
- Cover letter PDF.
- Source bundle containing the main TeX, bibliography, Springer Nature class
  and style, and all figure PDFs.
- Editorial Policy Checklist if requested by the portal.
- Reporting Summary if generated or requested by the portal.
- Related preprint copy only if requested by the portal/editor.

## Author checks immediately before upload

- Confirm author order, contribution statement, and approval by all authors.
- Confirm the competing-interests declaration.
- Add any study funding to Acknowledgements; do not create a separate Funding
  section. APC funding alone need not be represented as scientific funding.
- Confirm the related manuscript's current status and upload a copy when the
  policy requires it.
- Select the Collection in the submission portal and repeat the Collection
  interest in the cover letter.
- Link the corresponding author's ORCID to the Springer Nature account before
  acceptance.
