# Final mathematical and editorial audit

**Date:** 2026-08-12
**Scope:** current main paper, supplement, formal specifications, immutable
result tables, manifests, experiment registry, decision log, figure sources,
compiled PDFs, and arXiv source package.
**Constraint obeyed:** no new experiment, model, dataset, expensive simulation,
or QPU execution was opened. Figure changes use only archived E06, E09, E10,
and E16 artifacts.
**Verdict:** **READY TO FREEZE**.

## Executive disposition

No critical error invalidating a central empirical conclusion was found. The
audit did find several HIGH formal/editorial overstatements. Every one was
corrected. The principal changes are restrictions of scope: Proposition 4 is
conditional rather than empirically instantiated; Theorem 1 is finite-
population-conditional and per fixed claim; E13v2 is an oracle diagnostic; C2
depends jointly on nuisance representability and auxiliary-information quality;
and the Wald comparison is a contextual yardstick, not an optimality bound.

## Findings and corrections

| Severity | Finding | Disposition |
|---|---|---|
| HIGH | Failure of Proposition 4's sufficient inequality had been read as forcing a verdict flip, although failure of a sufficient condition implies nothing. | Rewritten throughout: the inequalities preserve truth-sign when satisfied; failure means only that invariance is not guaranteed. E16 flip rates are independent empirical evidence. |
| HIGH | E16 archives only source-reference movements `m_s_shift_unw` and `m_s_shift_w`; it does not archive target movement or target-minus-source movement. Figure S16/Table S6 therefore could not instantiate either Proposition 4 condition. | Proposition 4 remains conditional. Figure S16/Table S6 explicitly say that they show only `|Delta M_S|` and are not Proposition 4 inputs. No missing quantity was imputed. |
| HIGH | Truth-sign preservation plus resolution of only the realized audit did not imply equality of two three-way verdicts. | Verdict equality now requires both audits to resolve and both CSs to cover. Without joint calibration the intersection is at least `1-2 alpha`; using `alpha/2` for each gives at least `1-alpha`. |
| HIGH | The weighted theorem had been readable as using an unconditional, ex-ante numerical weight bound, while operational E13/E19 compute a global bound from each already frozen finite population. E13v2 additionally used full-population labels to sharpen class bounds. | Theorem 1 is explicitly conditional on the frozen finite population and scalar bound fixed before random label order. Only that scalar is supplied by data curation. E13v2 is labeled an oracle/benchmark diagnostic, not an operational I2 guarantee. |
| HIGH | Time-uniform/per-claim error control could be mistaken for simultaneous or FWER control over the full claim grid. | Main and supplement now state that `alpha=0.05` is per fixed claim; time-uniformity covers its stopping times only. Post-label threshold/claim selection, arbitrary adaptive row selection, and family conclusions need separate constructions/adjustment. |
| HIGH | C2 sometimes asserted that representability alone restored validity. | C2 now states that inference validity is jointly limited by nuisance representability and auxiliary/template quality. The independent-MC result is central and scoped to the archived fixed-template construction and MC size. |
| HIGH | E17's withdrawn directional degradation claim survived in conclusion/supplement language. | Replaced by “small within-world replicated but cross-world unstable responses”; the signs are stated not to transfer across worlds. |
| MEDIUM | Proposition 2 said power exactly `alpha` and made UNRESOLVED sound deterministic. | Correct result: power equals actual size and is at most `alpha`; equality with `alpha` requires exact size. UNRESOLVED is the chosen fail-closed policy when distinguishing evidence is absent. |
| MEDIUM | The Wald quantity was called a universal information floor and was locally expanded as `2m^2` without fixing `tau=1/2`. | Renamed a Wald-style information yardstick/benchmark. Universal, minimax, and “no sequential procedure can beat it” claims were removed. Expansion is `m^2/[2 tau(1-tau)] + O(m^3) = Theta(m^2)`. The descriptive ratios 1.46--3.35 remain numerically unchanged. |
| MEDIUM | Classical randomness and quantum deployment randomness were contrasted too absolutely. | Reframed: classical pipelines may also be stochastic; quantum-kernel evaluation adds measurement-induced deployment uncertainty intrinsic to finite-shot/noisy execution. |
| MEDIUM | Independent-MC and hardware language could overgeneralize beyond the tested construction/scale. | E08v3 is scoped to the two registered XGBoost multi-draw cells (plus six one-draw spot checks) and does not claim that MC-statistics-aware profiling fails in general. QPU evidence is a micro-scale fail-closed consistency demonstration, not performance or certification at scale. |
| MEDIUM | HEP wording overstated Barlow--Beeston and some CMS control-region interpretations. | The implemented likelihood is described as Barlow--Beeston-inspired/BB-lite Gaussian aggregate template variance. CMS C2 is total-MC normalization in a W-enriched CR with fixed non-W and absent QCD; C4 is an SS excess over non-QCD MC, consistent with QCD rather than exclusively attributed to it. |
| MEDIUM | Figure 8 conflated an E09 `n=2000` simulated curve with an E10 `n=32` hardware point and its labels were difficult at final column width. | Redrawn from existing artifacts. It now shows the E10 matched local shot floor (~0.020), separates provenance/scales in the caption, enlarges panels/fonts, removes overlapping end labels, and states that the separate E16 `n=28` micro-arm is not plotted. |
| LOW | The text used inverse ESS as “effective sample size,” called `n=2000` hardware-feasible, and used an ambiguous hardware priority phrase. | Corrected to ESS `(sum w)^2/sum(w^2)`, “statevector-feasible matched scale,” and “the project's first.” |

## Formal audit

### Proposition 4

For the ideal-anchored margin, the exact movement is `Delta M_T`; for the
deployment-relative margin it is `Delta M_T-Delta M_S`. Hence

```
|m*| > |Delta M_T|
|m*| > |Delta M_T-Delta M_S|
```

are sufficient for preservation of the respective truth-signs. Their failure
does not imply a sign or verdict flip. On coverage, any decisive verdict points
to the preserved sign. Equality of two ternary verdicts additionally needs both
audits to resolve and the intersection of their coverage events.

The immutable E16 JSON contains `m_s_shift_unw`, `m_s_shift_w`, and empirical
flip rates, but neither `Delta M_T` nor `Delta M_T-Delta M_S`. Accordingly:

- Proposition 4 is retained as a conditional mathematical result;
- Figure S16/Table S6 show only source movement and cannot instantiate it;
- the archived far fixed-reference flip rates (20.8% at 128 shots and 0.4% at
  4096) remain empirical observations, not theory predictions.

Final locations: `manuscript/latex/main.tex` Proposition 4 and its proof;
`manuscript/supplementary/supplement.tex` Section 1.3 and Figure S16/Table S6;
`docs/formal_results.md` Proposition 4.

### Proposition 2

When the observable law is identical under `H0` and `H1`, any test event has
the same probability under both. Therefore

```
power = actual size <= alpha,
```

with equality to `alpha` only for a test of exact size `alpha`. No deterministic
UNRESOLVED outcome follows from indistinguishability; that verdict is the
framework's explicit fail-closed reporting policy.

Final locations: `manuscript/latex/main.tex` Proposition 2;
`manuscript/supplementary/supplement.tex` Section 1.2;
`docs/formal_results.md` Proposition 2.

### Theorem 1

The final theorem and proof were checked line by line:

1. **Conditioning and bound.** Inference is conditional on an already frozen
   finite audit population and one scalar `w_max` fixed before the random audit
   order. The predeclared nuisance multiplier is 2.05, covering the largest
   compound official factor `2.0 x 1.01 = 2.02`. The base maximum is population-
   dependent; no unconditional claim that its number was known before population
   construction remains.
2. **Positive denominator.** Both classes have positive archived weight mass,
   so `E[u] > 0` for accuracy, weighted TPR, and weighted TNR reductions.
3. **Exact equivalence.** Since
   `E[Z]-tau = E[u](R-tau)/w_max`, positivity of `E[u]` gives
   `R >= tau iff E[Z] >= tau` exactly.
4. **Boundedness.** With `c in {0,1}`, `u in [0,w_max]`, and fixed
   `tau in [0,1]`, `u(c-tau)` lies in
   `[-tau w_max,(1-tau)w_max]`, hence `Z in [0,1]`.
5. **Optional stopping.** A time-uniform two-sided bounded-mean CS controls both
   false certification and false refutation over all stopping times for one
   fixed claim. Both are subsets of the same CS coverage failure.
6. **Observability.** Labeling reveals `(y_i,w_i)` and therefore `c_i` and the
   relevant `u_i`: `w_i`, `w_i 1[y_i=1]`, or `w_i 1[y_i=0]`. Event-wise weights
   remain outside I1 because they are process- and label-informative. The data-
   curation layer exposes only the one global scalar bound before sampling, not
   row weights or class labels.
7. **Information set.** Weighted TPR/TNR therefore live at I2. E13v2's
   class-specific maxima used full-population labels and are disclosed as oracle
   diagnostics; operational E13/E19 use the global scalar bound.
8. **Multiplicity/adaptivity.** `alpha=0.05` is per fixed claim, not FWER over
   thresholds, models, or environments. Time-uniformity does not license choosing
   `tau`/the claim after labels or arbitrary adaptive row selection. E07 uses a
   proposal fixed from unlabeled scores with bounded importance weights.

Final locations: `manuscript/latex/main.tex` Theorem 1 and proof;
`manuscript/supplementary/supplement.tex` Section 1.1;
`docs/formal_results.md` Theorem 1;
`docs/weighted_certification_spec.md` Sections 2--3 and final E13v2
qualification.

## Reviewer triad

| Reviewer | Objection / strongest version | Exact final answer location | Sufficient after correction? |
|---|---|---|---|
| QML | “Quantum is decorative; why is this not classical validation?” Strongest: C1/C2 and the matched sensor are generic, so the quantum component must have a non-decorative, non-advantage role. | Main Discussion: C1/C2 are generic; E09/E10/E16 specifically propagate finite-shot/hardware measurement uncertainty through Gram estimation, refit, calibration and threshold. Main Section 7 and Figure 8 instantiate it. | Yes. No quantum advantage or exclusivity is claimed. |
| QML | The paper implied only quantum deployments are random. | Abstract, Introduction, Proposition 3 proof, Discussion. | Yes: quantum evaluation adds an additional measurement-induced uncertainty; classical stochasticity is acknowledged. |
| QML | Hardware language could be read as scaled performance/certification validation. | Abstract; Section 7.2; Figure 8 caption; Limitations; Conclusion. | Yes: consistently “micro-scale fail-closed consistency”; the chance-level arm and absence of scale/performance claim are explicit. |
| QML | Figure 8 compared different Gram scales without identifying provenance. | Figure 8 panels and caption. | Yes: E09 `n=2000`, E10 `n=32` local floor/hardware, E16 simulated verdicts, and the unplotted E16 `n=28` arm are separated. |
| HEP | Profiling cannot be called valid merely where the nuisance model represents the shift. Strongest: independent template noise invalidates the frozen construction even nominally, while one representable JES cell already fails under shared simulation. | Abstract C2; Results Section 6.7; Figure 7 caption; Limitations; Discussion/Conclusion; supplement Section 3.4. | Yes: representability and auxiliary/template quality are joint conditions; scope and exceptions are explicit. |
| HEP | “Barlow--Beeston” overstated the implemented Gaussian aggregate variance treatment. | Method Section 4.4; Results Section 6.5; registry/decision log. | Yes: consistently Barlow--Beeston-inspired/BB-lite. |
| HEP | CMS C2/C4 assigned more process physics than the computed observables support. | Main Table 2 and Section 8; experiment registry E11v3. | Yes: total-MC in W-enriched CR and SS excess over non-QCD MC, merely consistent with QCD. |
| HEP | Low initial optimizer-success fractions might be hidden evidence of unreliable global fits. | Limitations and supplement Section 3.1. | Yes: minimum 0.382 is disclosed; safeguards/gate support the fits but are not claimed as a proof of global optimization. |
| Statistics | Proposition 4 overreached from truth-sign to equality of ternary verdicts and from failed sufficiency to forced flips. | Main Proposition 4/proof; supplement Section 1.3; formal results. | Yes: both-resolution/joint-coverage conditions and the one-way nature of sufficiency are explicit. |
| Statistics | Theorem 1 might not cover fixed threshold, weighting, observability, optional stopping, adaptivity, or multiplicity as actually described. | Main Theorem 1/proof and adjacent conditional-validity text; supplement Section 1.1; weighted spec. | Yes, after finite-population, fixed-`tau`, information-set, adaptivity, and per-claim qualifications. |
| Statistics | Proposition 2's exact-`alpha` power and deterministic UNRESOLVED conclusion were false. | Main Proposition 2; supplement Section 1.2; formal results. | Yes. |
| Statistics | Wald was presented as a universal floor despite no matching lower-bound theorem and a median-versus-expectation comparison. | Main Section 6.6/Figure 6; supplement Table S5; E06 summary artifact. | Yes: now only a contextual benchmark; the numerical ratio is descriptive. |

No reviewer objection was dismissed solely rhetorically. Objections already
answered by the frozen design (disjoint CRs, unconditional pseudo-experiment
ensembles, explicit weight-only benchmark scope, and disclosed shared-
simulation construction) required no new result and were left unchanged except
where a clarity edit was warranted.

## Numerical and artifact trace

| Item checked | Source of truth | Result |
|---|---|---|
| E16 available movements and flip rates | `results/tables/E16_quantum_uncertainty.json` | Only `m_s_shift_unw/w` plus empirical flip/abstention rates; no target or difference movement. Main/S6 transcriptions pass. |
| E10 local shot floor and hardware error | `results/tables/E10_hardware.json` | Local shot Frobenius values 0.01828, 0.02158, 0.01860 (mean 0.01949); hardware 0.17019. Figure 8 uses these archived values. |
| Wald-style ratios | `results/tables/E06_nstar_efficiency.json` and E06 `n*` table | 518 cells; overall median 2.07; bucket endpoints 1.46--3.35. Numeric payload unchanged; only definition/caveats corrected. |
| Independent-MC coverage/bias | `results/tables/E08v2_independent_mc.json`, `E08v3_multidraw.json` | Multi-draw scope, coverage ranges 0--0.238 and 0--0.359, and bias range through +7.496 verified. |
| Weighted fresh-world bound/rates | `results/tables/E19_fresh_world_validity.json` | `7.22421 x 2.05 = 14.80963`; reported false-certification/refutation transcriptions verified. |
| E13 bound and E13v2 mechanism | `results/tables/E13_weighted.json`, `E13v2_baw_allocation.json` | Global bound and oracle class-bound qualification verified; no operational claim attached to class-label maxima. |
| Inference sensitivity/optimizer flags | `results/tables/E15_sensitivity.json` | JES exception and minimum archived success fraction 0.382 verified. |
| E17 cross-world signs | `results/tables/E17_worlds.json` and registry disposition | Opposite/improving signs preserved; general directional degradation withdrawn. |
| CMS hardened claims | `results/tables/E11v3_cms_stats.json` and registry | C2 interval `[0.9042,0.9972]`; C4 `z=18.78`; wording matches computed estimands. |

The expanded executable audit performs 97 high-risk manuscript-to-artifact and
formal-wording checks. All 97 pass. Bidirectional semantic four-gram coverage is
90.4294% Markdown-to-LaTeX and 92.1970% LaTeX-to-Markdown.

## Semantic diff and experimental-scope proof

`git diff --name-only -- src experiments configs data` is empty. No runner,
model, dataset, frozen configuration, raw result, QPU record, or experimental
manifest changed. The only changed result JSON is
`E06_nstar_efficiency.json`; its numerical fields are unchanged and its two
edited strings now call the quantity a contextual yardstick and record the
missing lower-bound conditions. Changed figures are deterministic redraws of
existing artifacts for labels, scale provenance, and readability.

The manuscript diff introduces no new experimental finding. Every substantive
claim change belongs to one of four classes:

1. mathematical correction (Propositions 2/4, Theorem 1, KL expansion, ESS);
2. explicit conditioning or multiplicity scope;
3. evidential weakening/qualification (C2, E17, E13v2, QPU scale, CMS
   attribution);
4. editorial provenance/readability for existing numbers and figures.

Decision D-036 records these corrections and supersedes D-035's hashes/page
counts. The supplement audit trail includes this audit.

## npj Quantum Information editorial adaptation

After the mathematical freeze, the target journal was fixed as *npj Quantum
Information*, specifically the Collection *Quantum machine learning:
understanding capabilities, limitations, and perspectives for quantum
advantage*. The decision was rechecked against the journal's current official
aims, author guide, submission instructions, and the Collection page on
2026-08-12. The Springer Nature `sn-jnl` class and `sn-nature` bibliography
style were recovered from the related local project and copied into this
repository so the submission source is self-contained. The local `guidelines/`
folder is deliberately ignored by Git.

The adaptation changes presentation, not evidence:

- the title is 13 words with no punctuation, and the abstract is 147 words;
- the opening now makes the QML validity question and the additional
  measurement-induced deployment uncertainty visible before the collider case;
- the journal structure is Introduction, Results, Discussion, Methods, followed
  by Data availability, Code availability, Acknowledgements, individual Author
  contributions, Competing interests, and References;
- the Introduction and Discussion have no subheadings, the Methods section does,
  and there is no separate Conclusion or Limitations section;
- the use of generative AI is disclosed in Methods with author verification and
  responsibility stated explicitly;
- the cover letter is specific to the Collection, makes no quantum-advantage
  claim, and voluntarily discloses the distinct related manuscript and its lack
  of overlap;
- a portal-ready metadata sheet records keywords, significance, three
  contributions, scientific guardrails, upload contents, and the remaining
  author confirmations;
- no experiment, model, dataset, result table, QPU execution, or scientific
  conclusion was added.

## Final verification

- `pytest -q`: **127 passed** in 21.29 s.
- `python scripts/verify_f8_2.py`: **97/97 passed**; semantic four-gram
  coverage **90.8032%** Markdown-to-LaTeX and **93.9100%**
  LaTeX-to-Markdown.
- `python scripts/verify_npjqi_submission.py`: **49/49 passed**, including
  title, abstract, section order, declarations, Collection cover letter,
  README/manuscript/supplement/cover-letter/decision/audit consistency, frozen
  artifact hashes, cross-document title, and scientific guardrails.
- Main PDF: **29 pages**, SHA-256
  `A2DC23A938D9A044EC9FB4C52C6C409EBE17486FEF6E2A89E0E109F7615E1E68`.
- Supplementary Information PDF: **8 pages**, SHA-256
  `CDAF97F09A2DDCB2614421E909FAD334834A49DA9AFAF9BDFDF4684FC023DE1F`.
- Cover letter PDF: **1 page**, SHA-256
  `3D4F6F3DF84CEF8DDED32F3A9A0F6F3F5D75BC42B870D8CD76D5EB69741A7A8A`.
- Submission source/PDF bundle: SHA-256
  `D122C53F729242513B1A3218473E5FD511C00F7A1EC86FCFAB5F48F57A9A4FE3`.
- The three source documents compile independently from a fresh extraction of
  the bundle to 29, 8, and 1 pages with no unresolved citations/references,
  overfull boxes, or final LaTeX/package warnings. The Springer Nature class
  emits cosmetic underfull-box diagnostics in the main build; complete visual
  review confirms no corresponding layout defect.
- All **38** final PDF pages were rendered and visually inspected. No clipping,
  overlap, broken glyph, unreadable equation, figure/table overflow, orphaned
  legend, or numbering inconsistency remains. Figure 8's two accounting panels,
  provenance, labels, fonts, and legend are legible at page scale.
- `git check-ignore -v guidelines/npj.txt` confirms the local journal-guideline
  folder is excluded by `.gitignore`.

There is no remaining mathematical, evidential, journal-format, build, or
layout blocker. The only outstanding items are author-side portal confirmations
(approval, competing interests, study-funding text if any, related-manuscript
status, and ORCID linkage); they do not change the frozen scientific record.

## Final verdict

**READY TO FREEZE**
