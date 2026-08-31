# Senior-author adversarial revision — 2026-08-13

## Scope and invariants

This pre-submission revision responds to the final adversarial npj Quantum
Information review using the existing scientific material. No dataset, primary
result, model, experimental configuration or QPU raw record was changed, and
no experiment or QPU job was run. The only new numerical artifact,
`results/tables/E16_deployment_level.json`, is a deterministic reanalysis of
`E16_quantum_uncertainty.json`.

This document is the npj Quantum Information editorial adaptation and
scientific consistency audit that supersedes the earlier submission freeze.
The Wald comparison remains only a contextual information yardstick, never a
lower bound or optimality claim.

## Material dispositions

1. **Proposition 4 — CLOSED.** Equal decisive verdicts now require the
   corresponding sign-stability condition, both CS coverage events and both
   audits resolving. Two level-α audits give a 2α union bound; α/2 each gives
   joint α. Counterexamples show both that coverage plus resolution is
   insufficient and that failure of the sufficient inequality does not force a
   flip. E16 flip rates remain separate empirical evidence.
2. **Proposition 2 / observable experiment — CLOSED.** I1 is
   `(X_1,…,X_n)|N=n`, excluding count, exposure, yields and weights. The full
   marked-count experiment is explicitly distinguished. I2 reveals binary
   class and nominal weights only in the simulated audit; process category and
   nuisance-dependent true weights remain hidden. I3 adds rate/count evidence.
3. **Weighted sequential related work — CLOSED.** The manuscript now cites
   *Off-Policy Confidence Sequences* and *Anytime-valid off-policy inference
   for contextual bandits*. Theorem 1 claims only the exact fixed-threshold
   physics-ratio reduction and its integration with the auditor.
4. **E16 evidential unit — CLOSED for the scoped descriptive claim.** All five
   independently sampled kernel seeds at each of six shot budgets are tabulated.
   Means, sample SD, ranges and leave-one-deployment-out sensitivity are
   reported at the deployment level. Claims within a deployment are correlated,
   and paired audit streams induce common-random-number dependence across
   deployment comparisons. No
   population CI or monotonic trend is claimed. Five deployments suffice only
   for the final descriptive C3, so no additional seed is recommended.
5. **Audit-label budget — CLOSED.** `n*` is a with-replacement audit-label draw
   or labeled-observation budget, not unique-event labeling cost. Real CMS data
   have no queryable event truth; accuracy remains UNRESOLVED.
6. **C2 narrative — CLOSED.** The result now leads with joint limitation by
   nuisance representability and template quality. Shared-simulation recovery
   is a conditional positive case; independent-template failure includes the
   nominal control. No general MC-statistics-aware framework is claimed.
7. **QML centrality — CLOSED as a scope statement; editorial risk remains.**
   The exact QML chain is finite-shot/noisy kernel → random Gram → refit,
   calibration and threshold → claim semantics/resolvability. The eight-qubit
   study is classically simulable; matched RBF removes performance/sensing
   advantage; the QPU arm is micro-scale integration/fail-closed consistency
   with a floor effect.
8. **Dependence, wording and concision — CLOSED.** Structured-environment IID
   Spearman p-values were removed from the manuscript and Figure 4. Figure 2's
   caption describes only TES. The variance formula is indexed consistently.
   Defensive phrases and much audit-history narrative were removed from the
   main paper. Experiment identifiers remain mainly for traceability.

## E16 number audit

- Independent deployments: 5 per budget, 30 total.
- Far own-reference flips: 0 in every deployment.
- Far fixed-reference means by shots 128/256/512/1024/2048/4096:
  20.8/17.7/0.9/11.9/5.8/0.4%.
- Endpoint sample SD and ranges: 19.9%, 0–44%; 0.65%, 0–1.5%.
- Leave-one-deployment-out endpoint mean ranges: 15–26%; 0.13–0.50%.
- High-leverage intermediate seeds: 256 shots 0–88.5%; 1024 shots 0–59%.

These values are recomputed by `scripts/summarize_e16_deployments.py`; the
immutable source hash is stored in the derived JSON.

## Related-manuscript disclosure

The cover letter now states exactly that *Sharp Target-Domain Certificates for
Quantum-Kernel Advantage under Distribution Shift* is public preprint/Zenodo
material and has not been submitted to any journal. It distinguishes that
paper's target-domain advantage-identification question from this paper's
scientific-claim validity question and states the complete non-overlap. The
other repository was not modified.

## Final validation record

- Full test suite: **127 passed** (`pytest`, cache disabled and isolated temp).
- Scientific audit: **146/146 passed**; LaTeX/Markdown semantic four-gram
  coverage is 94.9965% draft→LaTeX and 97.1415% LaTeX→draft.
- npj submission gate: **53/53 passed**, including exact frozen hashes.
- Independent build from the extracted ZIP: **clean**, producing a 25-page
  main paper, 9-page supplement and 1-page cover letter without missing source
  files, undefined citations/references, multiply defined labels or overfull
  boxes.
- Visual inspection: all **35 final PDF pages** inspected. A stranded final
  bibliography entry found during inspection was corrected by compacting the
  reference spacing; the final 25-page manuscript has no clipped figures,
  tables, text, overlaps or blank pages. All PDF fonts are embedded.
- E16 number audit: the immutable input SHA-256 is
  `3208814B4A66609A6C9436D2E232A8BD93204F36F6E2E5431D9FECA5DED981FE`;
  the deterministic deployment-level summary SHA-256 is
  `1E593F7BFBC8D1C974A0391042851D8F4E962DD90B7C997BD486D4A42D2FEDAC`.
- Diff audit: no dataset, primary-result table, QPU raw record, model,
  experimental configuration or source-analysis implementation changed. The
  only result-table addition is the derived E16 deployment summary; changed
  figures are regenerated presentations of existing artifacts.
- Editorial density: `texcount` falls from 9,191 to 7,945 words in the main
  source (−13.6%) while retaining adverse results and formal qualifications.

## Second adversarial review from the revised paper

| Original major issue | Disposition | Evidence | Status |
|---|---|---|---|
| Proposition 4 omitted sign stability from the resolved-verdict conclusion | The proposition now requires sign stability, both coverage events and both audits resolving; it gives the 2α union bound, the α/2 construction and both directions of counterexample. | Main §2.10; Supplement §1.3; `docs/formal_results.md` | **CLOSED** |
| Proposition 2 overclaimed beyond the observable feature-only experiment | I1 is now the fixed-size/count-conditioned feature experiment; the marked-count experiment is separated, and I2/I3 contents are explicit. | Main §2.1; Fig. 1; Supplement §1.2 | **CLOSED** |
| Theorem 1 was insufficiently positioned against weighted/off-policy sequential inference | The exact identity is retained, prior off-policy and adaptive-policy confidence sequences are cited, and novelty is restricted to the fixed-threshold physics-ratio reduction and auditor integration. | Main Introduction and §2.2.3; bibliography refs. 31–32 | **CLOSED** |
| E16 used correlated claims as apparent replication | The deployment is the unit; all five seeds per budget, SD/range and leave-one-deployment-out sensitivity are reported; no population CI or monotonic trend is claimed. | Main §2.10.1; Supplement Table S6; `E16_deployment_level.json` | **CLOSED for descriptive C3** |
| `n*` was described as experimental label cost | It is now a with-replacement audit-label draw/labeled-observation budget and is explicitly not a count of unique experimental labels; CMS accuracy remains UNRESOLVED. | Main §§2.1, 2.8 and 2.11; Fig. 6 | **CLOSED** |
| C2 foregrounded shared-template recovery and demoted independent-template failure | C2 now leads with the joint representability/template-quality limitation; shared-simulation recovery is conditional and the independent-MC nominal failure is central. | Main §2.9 and Discussion; Supplement §3.4 | **CLOSED** |
| The quantum component risked being decorative or overstated | The complete random-Gram→refit/calibration/threshold→claim chain is explicit; matched RBF, no advantage, classical simulability and micro-scale hardware scope are central. | Abstract; Introduction; §§2.3 and 2.10; cover letter | **CLOSED as scientific scope; editorial selectivity remains** |
| Dependence, related-paper status and development-log prose created statistical/editorial risk | IID environment p-values are retired; CMS p-values use calibrated/permutation constructions; the related paper's exact public/unsubmitted status is stated; main prose is reduced by 13.6%. | §§2.5, 2.11 and Discussion; cover letter; README; D-038 | **CLOSED** |

### Scores (1–5)

| Criterion | Score | Adversarial assessment |
|---|---:|---|
| Originality | 4.1 | The integrated information-set/physics-inference/random-deployment object is distinctive; individual ingredients are not all new. |
| Quantum-specific novelty | 3.2 | Real but deliberately narrow: measurement-induced deployment uncertainty and claim semantics, not an advantage or scaling result. |
| Mathematical rigor | 4.5 | The former blocker and identifiability boundary are now correctly scoped; guarantees are per fixed claim. |
| Empirical evidence | 4.0 | Broad and falsifier-driven overall; C3 is descriptive at five deployments per budget and hardware is micro-scale. |
| Reproducibility | 4.9 | Immutable artifacts, deterministic summaries, executable gates and an independently compiling bundle. |
| Clarity/conciseness | 4.3 | The main is substantially denser and adverse results remain visible; the breadth still demands attention. |
| Collection fit | 4.0 | Strong fit to capabilities/limitations; editorial risk remains because the quantum-specific empirical scale is intentionally modest. |

**Adversarial verdict: READY TO SUBMIT.** No mathematical or statistical flaw
that invalidates C1–C3 remains open. This is a submission-readiness judgment,
not a prediction of editorial acceptance; the principal residual risk is the
editor's threshold for quantum-specific centrality, not an unsupported claim
that can be repaired from the current material.
