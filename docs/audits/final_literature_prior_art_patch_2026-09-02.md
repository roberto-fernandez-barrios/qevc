# Final literature / prior-art patch (0.3.9) — 2026-09-02

Release 0.3.9 / `npjqi-submission-v1.9` combines two bounded, non-scientific
patches on the published 0.3.8 baseline (`a4c622f`): the figure-legibility
patch and the final literature / prior-art patch driven by a deep
bibliographic audit to 2026-09-02.

## Bibliographic audit outcome

- **A novelty blockers: 0.** The audit found no external work that combines
  finite-shot/noisy quantum Grams, refit/recalibration/threshold reselection,
  deployment-relative vs ideal-anchored claim semantics,
  information-conditional fail-closed certification and collider scientific
  inference under systematics. The manuscript's combined-object framing
  ("the combined scientific object rather than priority over its
  ingredients") is preserved verbatim and no priority claim is added.
- **Five class-B actions, all applied and verified against primary
  sources** (arXiv pages, dblp, proceedings.com DOI resolution,
  proceedings.neurips.cc, Project Euclid via search):
  1. **Added** Alexe, Bendavid, Bianchini, Bruschini, *Under-coverage in
     high-statistics counting experiments with finite MC samples*, Nucl.
     Instrum. Methods A **1086**, 171360 (2026), DOI
     10.1016/j.nima.2026.171360, arXiv:2401.10542 (key
     `arxiv2401.10542`).
  2. **Added** Miroszewski, *Adaptive Measurement Allocation for Learning
     Kernelized SVMs Under Noisy Observations*, arXiv:2605.22275 (2026;
     v2 of 28 July 2026; no journal version exists, none invented) (key
     `arxiv2605.22275`).
  3. **Added** Howard, Ramdas, McAuliffe, Sekhon, *Time-uniform,
     nonparametric, nonasymptotic confidence sequences*, Ann. Statist.
     **49**(2), 1055–1080 (2021), DOI 10.1214/20-AOS1991, arXiv:1810.08240
     (key `arxiv1810.08240`).
  4. **Updated** FAIR Universe (`arxiv2410.02867`) to the NeurIPS 2025
     Datasets and Benchmarks version of record: Advances in Neural
     Information Processing Systems 38, pp. 92065–92101, DOI
     10.52202/085713-2767. The VoR author list (25 authors, led by Bhimji
     and Chakkappai; verified via dblp and the proceedings.com DOI landing
     page, which agree) differs from the arXiv v5 list and replaces it.
  5. **Updated** `waudbysmith2020wor` to the NeurIPS 2020 version of
     record (Advances in Neural Information Processing Systems 33), with
     arXiv:2006.04347 retained as a complementary identifier; no page range
     or proceedings DOI invented.
- Casas et al. deliberately keeps its austere `npj Quantum Information
  (2026)` metadata: the publisher record still exposes no volume/article
  number. Brown, Ait Haddou, He, Shastry, Gentinetta, Miroszewski 2024,
  Hubregtsen, Agliardi, Karampatziakis and Barlow–Beeston were re-verified
  unchanged. The sibling preprint remains uncited by design (not under
  consideration elsewhere; this paper does not depend on it).

## Positioning sentences (exact insertions)

1. Related work (C1): "The general time-uniform confidence-sequence
   framework is developed by Howard et al.; our bounded-mean implementation
   follows the betting and predictable-plug-in constructions [Waudby-Smith
   & Ramdas 2024] that provide our statistical backbone."
2. Related work (C3): "Recent work also studies the non-uniform sensitivity
   of kernelized-SVM solutions to noisy Gram observations, including margin
   and support-vector active-set instability under adaptive measurement
   allocation [Miroszewski 2026]; we instead propagate each realized kernel
   through refitting, recalibration, operating-point selection and
   scientific-claim evaluation."
3. Sec. 2.9 (C2, replacing the former "does not test, and therefore does
   not reject" sentence): "Finite-simulation fluctuations are already known
   to induce under-coverage in profile-likelihood inference, including in
   apparently high-statistics regimes [Alexe et al. 2026]; the result is
   therefore not a priority claim for that general effect and does not test
   MC-statistics-aware profiling --- it establishes the failure mode for
   the archived classifier-to-inference construction and template
   statistics evaluated here, at this auxiliary-template quality."

Word count (texcount, words in text, `-inc`): 9,129 → 9,214 (+85, +0.9%).
Bibliography: 62 → 65 entries; rendered citations [1]–[48] (+3), no
undefined references or citations, no BibTeX errors. A duplicated arXiv
identifier in the rendered [45] (note + eprint) was removed.

## Figure-legibility component (commit `92d5241`)

Seven figures re-rendered (fig1 info-set box; fig2 marks/dodge/label
anchor; fig4b legend placement; fig5 staggered labels; fig7 desaturation;
fig7b clipping/annotation/legend; fig8 annotation backing); panel-label
skips fixed and `\raggedbottom` added in `main.tex`; Supplementary Table
S2 converted to a page-breaking longtable. The release-consistency gate's
audit-trail isolation regex was updated for the longtable form (same
semantics), and the three protected-baseline allowlists (hygiene test,
micro-patch test, npj gate) gained exactly the fourteen re-rendered figure
files.

## Validation record (pre-tag)

- pytest: 171 passed, 0 failed (includes the new
  `tests/test_literature_patch.py`).
- npj submission gate: 108/108.
- Release consistency: 113/115 pre-tag; the two open checks are "release
  tag exists" and "release tag targets HEAD", which close at tagging.
- F8.2: 213/213; semantic 4-gram coverage draft→LaTeX 95.4%, LaTeX→draft
  97.4%.
- Clean build: main 31 pp, SI 18 pp, cover 1 p (page counts unchanged); no
  undefined references/citations; `git diff --check` clean; the submission
  ZIP's sources are byte-compared against the working tree by the npj gate.
- `git diff npjqi-submission-v1.8 -- configs data experiments src`: EMPTY.
- `git diff npjqi-submission-v1.8 -- results`: exactly the fourteen
  re-rendered figure files; all six frozen scientific JSON SHA-256 values
  are byte-identical to 0.3.8.

## Release rule

Publish as `0.3.9 / npjqi-submission-v1.9` under the reserved Zenodo
version DOI `10.5281/zenodo.22254835` (deposition 22254835, concept
`10.5281/zenodo.21894291`), release date 2026-09-02, preserving all prior
tags and DOIs (see D-049).
