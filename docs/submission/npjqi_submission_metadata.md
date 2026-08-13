# npj Quantum Information submission metadata

Status: prepared for author verification and portal upload on 2026-08-12.

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

Claims made by deployed quantum machine-learning classifiers can fail because
the target environment differs from validation and finite-shot quantum
evaluation randomizes the model itself. We develop an information-conditional,
fail-closed framework that returns supported, refuted or unresolved verdicts
with anytime-valid per-claim error control. Across a Higgs-to-tau-tau
benchmark, four disjoint simulated worlds, CMS open data and a micro-scale IBM
hardware demonstration, we prove an exact weighted extension and an
indistinguishability boundary for weight-only nuisances. Stable classifier
metrics do not ensure signal-strength coverage: inference is jointly limited by
nuisance representability and auxiliary-template quality. For quantum kernels,
deployment-relative and ideal-anchored claims separate measurement-induced
uncertainty from scientific shift; empirical fixed-reference far-margin verdict
flips decrease from 20.8% to 0.4% across tested shot budgets. A matched classical
kernel reproduces all apparent quantum-specific performance and sensing
effects. The result is a framework for deciding which QML claims are
supportable, not a claim of quantum advantage.

Compliance: 147 words by the repository verifier; no citations, equations, or
subheadings.

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

1. An exact weighted anytime-valid reduction and an indistinguishability
   boundary make certification conditional on the information actually
   observable, with per-claim rather than family-wise error control.
2. Signal-strength validity is shown to depend jointly on nuisance
   representability and auxiliary-template quality, even when classifier
   metrics remain stable.
3. Deployment-relative and ideal-anchored QML claims separate scientific shift
   from measurement-induced deployment uncertainty; archived shot and hardware
   studies quantify the latter without asserting quantum advantage.

## Scientific guardrails

- Proposition 4 is conditional: E16 archives neither target movement nor the
  target-minus-source movement required to instantiate its sufficient bounds.
- Observed verdict flips are independent empirical evidence, not a theorem
  prediction.
- The anytime-valid guarantee is per fixed claim and stopping time; it is not
  simultaneous or FWER control across models, thresholds, or environments.
- The IBM run is a micro-scale fail-closed consistency demonstration, not a
  performance result or certification at scale.
- The fixed-template profiling result is conditional on nuisance
  representability and auxiliary/template quality.
- The matched classical control removes apparent quantum-specific performance
  and sensing effects; no quantum advantage is claimed.

## Related-manuscript disclosure

The same authors have released *Sharp Target-Domain Certificates for
Quantum-Kernel Advantage under Distribution Shift*, Zenodo DOI
10.5281/zenodo.21776862. It uses unrelated cybersecurity and tabular datasets
and studies partial identification of predictive advantage against a fixed
classical-kernel family. It shares no datasets, experiments, theorems,
estimands, codebase, or results with the present collider-inference paper.
Upload the manuscript as related material if it is under consideration or in
press at the time of submission; retaining the voluntary disclosure in the
cover letter is the conservative option in either case.

## Upload set

- Main manuscript PDF with figures embedded and line numbers.
- Single Supplementary Information PDF.
- Cover letter PDF.
- Source bundle containing the main TeX, bibliography, Springer Nature class
  and style, and all figure PDFs.
- Editorial Policy Checklist if requested by the portal.
- Reporting Summary if generated or requested by the portal.
- Copy of the related manuscript described above.

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
