# Editorial focus / concision patch — 2026-09-01 (0.3.8 / npjqi-submission-v1.8)

Decision D-048. Editorial only; baseline `npjqi-submission-v1.7` (0.3.7,
Zenodo `10.5281/zenodo.22236115`). No number, JSON artifact, figure file,
seed, model, threshold, claim grid, alpha, likelihood, dataset or QPU record
changed; `configs/`, `data/`, `experiments/`, `src/` and `results/` are
byte-identical to `npjqi-submission-v1.7` (verified by `git diff` and by the
protected-baseline gates).

## Length accounting (before → after)

| Quantity | 0.3.7 | 0.3.8 |
|---|---:|---:|
| Abstract (gate tokenizer; limit 150) | 139 | 149 |
| Introduction | 1,603 | 1,496 |
| Results | 6,146 | 5,799 |
| Discussion | 684 | 697 |
| Introduction–Discussion total | 8,433 | 7,992 (−441, −5.2%) |
| Methods | 862 | 884 |
| Pages (main / SI / cover) | 31 / 18 / 1 | 31 / 18 / 1 |
| Figures / tables (main) | 8 / 3 | 8 / 3 |
| Longest figure caption (words) | 163 | 106 |

The soft 7,000–7,500-word target was **not** reached. After removing
repetition, audit-history narrative and internal identifiers, the remaining
prose consists of results, caveats now stated exactly once, and wording pinned
byte-exactly by the repository verification gates; a further ~500-word cut
would require relocating entire result subsections (the CMS ledger,
audit-label draw efficiency) out of the Article. Per the patch instruction's
quality rule ("stop before removing science, results or necessary context"),
the pruning stopped here.

**Removed as repetition or audit narrative (every number remains in the main
text or the cited Supplementary table):** the unweighted seed-variation
re-draw parenthetical and the E19 re-audit history (context: Table S4); the
veto-set degeneracy parenthetical duplicated from Sec. 2.5; the v1
balanced-accuracy bound radius parenthetical (Tables S14–S15); the raw
Proposition-3 stream counts 49,430 / 4,554 / 13,637 / 22,570 (percentages
kept in the main text; counts in Table S8); the development-era gate-firing
anecdote in Sec. 2.2.6; the duplicate "Acquisition" subsubsection (the result
and both numbers remain in Sec. 2.8 and the Introduction); repeated
statements of the with-replacement-budget, five-deployment-correlation and
Monte-Carlo-scope caveats (each kept once at its canonical location); the
Fig. 8 caption's duplication of in-text results. **Compacted without loss:**
the Introduction's guarantee-scope paragraph and related-work block (six
paragraphs to four; every citation retained), the E19 fresh-world sentence,
the weighted-balanced-accuracy oracle passage (also fixing the grammatical
error "For weighted balanced accuracy is diagnosed..."), the CMS narrative
and the Discussion bullets. No table or figure was removed; no numeric value
was dropped from the paper + SI pair.

## Content changes

1. **Proposition 3.** The formal statement no longer contains "deployment-
   relative claims are structurally the stabler class". The common-mode
   observation stays in the empirical text with the explicit sentence that it
   "is not claimed as a universal structural ordering between claim
   semantics". `docs/formal_results.md` (iii) updated in the same sense.
   Equations, proof, counterexamples, the 2α bound and the α/2 split are
   unchanged (environment order, labels and resolved counters verified).
2. **Abstract.** Classical controls scoped: "Matched classical controls
   remove apparent quantum-specific nominal-performance and sensing
   effects." A matched classical *stochastic* control for the finite-shot
   deployment study was not executed and is nowhere implied (also stated in
   the submission-metadata guardrails).
3. **Contribution 2 condition.** Every coverage-loss statement now carries
   the finite-template condition in the same sentence (abstract,
   Introduction, Sec. 2.9, Discussion bullet): coverage can be lost, even in
   shift-free controls, when templates are estimated independently at the
   studied finite-template statistics and template-statistical uncertainty is
   not modeled explicitly. This matches the executed pipeline: the
   independent-MC studies use the archived fixed-template likelihood with no
   template-statistical term, at signal-template effective sample size ≈ 46.
   "Profile likelihood generally loses coverage" is asserted nowhere.
4. **Contribution 3 visibility.** Abstract, Introduction, Results and
   Discussion now state the frozen mechanistic finding with its numbers,
   verified against `E16_stage_decomposition.json` and
   `E16_prop3_margin_stratification.json` before use: ranking relatively
   stable (median Spearman 0.92 realized-vs-ideal; median nominal-AUC change
   +0.001 at the archived stage over the 30 raw deployments) while
   thresholded target metrics move by a median of about 0.02 (|ΔM_T| median
   0.019 over the 1,800 raw condition cells; stage-D medians 0.014 unweighted
   / 0.024 weighted accuracy), flipping ideal-anchored claims. Journal-fit
   sentence added to the contributions framing: "This makes the study a QML
   limitations result: finite quantum measurement changes the realized
   deployed object even when conventional predictive ranking metrics remain
   nearly unchanged." AUC remains a ranking/discrimination diagnostic, not
   "kernel quality"; the downstream mechanism is still not claimed to be
   quantum-specific, and the two regime-specific D-047 sentences are retained
   verbatim.
5. **Acronyms and readability.** TES/JES/soft-MET defined in Sec. 2.1; CRN in
   Sec. 2.2.1; HEP and the signal-strength parameter μ in the Introduction;
   same-sign and control region expanded in Table 2; leave-one-nuisance-out
   expanded in the Fig. 4 caption; BB-lite now cites Barlow–Beeston (1993).
   The ΔAUC sign convention (nominal minus shifted; positive = degradation)
   is defined in Sec. 2.4 and the Fig. 2 caption. The five-seed 0.848 ± 0.022
   versus single-seed Table S18 distinction is stated; Methods 4.3 clarifies
   20 audit-stream replications (certification studies) versus ten paired
   streams per condition cell (finite-shot deployment study). Internal
   experiment/decision identifiers (D-0xx, E-numbers) no longer appear in the
   main text; they remain in the Supplement, Methods-adjacent artifacts and
   the repository.
6. **Citations.** Hubregtsen et al., Phys. Rev. A 106, 042431 (2022) added
   (metadata verified against the primary arXiv record 2105.02276: author
   list, journal reference and DOI), cited in the related-work paragraph and
   Sec. 2.10.1 with conceptual wording only (finite-sampling/device-noise
   analysis and mitigation tailored to quantum embedding kernels); no claim
   about specific projection strategies is attributed. Barlow–Beeston (1993)
   cited at the BB-lite definition.
7. **Supplement Table S1 provenance.** New "Freeze / provenance" column with
   the short Git SHA and date at which each frozen condition entered the
   repository, cross-checked against `docs/experiment_registry.md`, the git
   history and the immutable run manifests: E02R `ce6734d` 2026-08-10
   (registration and launch share one commit; the archived run began 25
   minutes later — marked "at launch", not strictly predeclared); E12(e),
   E14 v1 and the E15 gate `f6d99cb` 2026-08-11; E17(b), E08v2(a) and
   E08v2(b) `1d6d93d` 2026-08-11; E08v3(a) `1faecfc` 2026-08-12; E13v2(b)
   `1d6d93d` plus spec addendum `309025f` 2026-08-12 (the run manifest
   records `git_commit = 309025f`). The deployment-snapshot freeze before the
   confirmatory world is `47fabe9` 2026-08-11 09:59, before the seed-121 run
   at 10:09 (D-020). No provenance was fabricated; the one ambiguous case
   (E02R) is disclosed in the table caption.
8. **Objective micro-corrections.** "Section 2.10 proves" → "shows";
   "monotone (Möbius)" → "linear-fractional, and therefore monotone"; an
   unbalanced parenthesis in Sec. 2.5 removed; the Fig. 5 caption no longer
   promises a median-stopping-time panel that the figure does not show.
9. **Figures and Table 1.** No figure file changed (all byte-identical and
   protected). LaTeX-layout-only legibility fixes: Figs. 4 and 7 stacked at
   (near-)full width with bold lower-case panel labels **a**/**b** (npj
   style, also applied to Fig. 8); Fig. 8 caption deduplicated; Table 1 font
   raised from 6.5 pt to 7.5 pt. Known residual defect, deferred: the
   in-plot margin-bucket end labels of Fig. 5 overlap at the top right;
   fixing them requires regenerating
   `results/figures/fig5_certification_landscape.*`, which this patch's
   zero-diff rule for `results/` forbids.
10. **Final page.** Page 31 carries the last three reference entries — more
    than a 1–2-line overhang — so no typographic squeeze was applied and the
    page counts remain 31 / 18 / 1.

## Gate updates (wording-only, no gate weakened)

`scripts/verify_npjqi_submission.py`: three literals re-pointed to the new
wording (Proposition-3 retrospective diagnostic; PSD-repair scoping;
measurement-induced scoping), release literals bumped to 0.3.8 /
v1.8, a "historical 0.3.7 release retained" check added, Zenodo metadata path
moved to `zenodo_npjqi_submission_v1_8_metadata.json`.
`scripts/verify_f8_2.py`: one literal ("E13v2 is not an operational" → "not
an operational I2 guarantee"). `tests/test_submission_micro_patch.py`: the
same Proposition-3 literal. `scripts/verify_release_consistency.py`:
VERSION/TAG/metadata-path bump; `VERSION_DOI` temporarily equals the pending
sentinel (below). `scripts/sync_markdown_draft.py`: generated lines are
stripped of trailing whitespace. The protected-baseline path lists and hash
mechanisms are untouched.

## Validation record

- pytest: 165 passed, 1 failure —
  `test_submission_hygiene.py::test_release_consistency_gate_passes_before_tagging`,
  caused solely by the pending-DOI sentinel; it passes once the reserved DOI
  is substituted.
- npj submission gate: 105/106 (same single cause). Release consistency:
  112/113 (same single cause: "version DOI synchronized" refuses the
  sentinel by design). F8.2: 213/213; semantic 4-gram coverage draft→LaTeX
  95.4%, LaTeX→draft 97.3%.
- Clean build: main 31 pp, SI 18 pp, cover 1 p; no undefined references or
  citations, no overfull boxes, no unresolved markers; `git diff --check`
  clean.
- `git diff npjqi-submission-v1.7 -- configs data experiments src results`:
  empty. Full visual inspection of the rendered main PDF and the SI Table
  S1 / audit-trail pages performed across build iterations.

## Release closure (2026-09-02)

The Zenodo network action, blocked on 2026-09-01, succeeded on 2026-09-02:
the version DOI `10.5281/zenodo.22250951` (deposition 22250951, concept
`10.5281/zenodo.21894291`) was reserved with
`python scripts/zenodo_release.py reserve --from-deposition 22236115`, and
the pending-DOI sentinel was replaced by the reserved DOI in README.md,
CITATION.cff, `docs/submission/npjqi_release_manifest.md`,
`docs/submission/npjqi_submission_metadata.md`,
`docs/submission/zenodo_npjqi_submission_v1_8_metadata.json`,
`manuscript/bibliography/references.bib`, `manuscript/latex/main.tex`
(Data and Code availability), `scripts/verify_npjqi_submission.py` and
`scripts/verify_release_consistency.py` (`VERSION_DOI`; the `PENDING_DOI`
sentinel constant is retained by design). Because the calendar advanced
during the closure, the release date moved mechanically from 2026-09-01 to
2026-09-02 on the release surfaces the consistency gate synchronizes (cover
letter visible date and PDF creation date, CITATION `date-released`,
manifest release date, Zenodo `publication_date`, README header) together
with the corresponding gate literals; the patch content is unchanged. The
final rebuild, gate results, tag `npjqi-submission-v1.8`, GitHub release and
Zenodo publication are recorded in the release manifest and in D-048.
