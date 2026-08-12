# F8.2 final LaTeX, number, and semantic audit — 2026-08-12

## Scope and method

This closes roadmap item F8.2 for the arXiv-v1 manuscript and its
supplement. It combines the earlier manuscript-wide source audit
(`post_campaign_audit_2026-08-11.md`, approximately 178 exact quantitative
matches with every mismatch dispositioned) with a reproducible final-LaTeX
gate in `scripts/verify_f8_2.py`. The final gate reads the immutable JSON
tables directly, writes nothing, and checks the highest-risk derived ranges,
all extended-table rows, front matter, the falsifier ledger, and bidirectional
semantic equivalence between `draft.md` and `main.tex`.

Final execution result:

- 81/81 executable assertions passed.
- Four-word prose coverage was 90.5473% from Markdown to LaTeX and 92.4084%
  from LaTeX to Markdown (thresholds 90% and 92%).
- The residual is explained by TeX math syntax, citations moved to BibTeX,
  automatic numbering, float/table markup, and the deliberately omitted
  working-caption section; spot inspection found no lost scientific claim.

## Source trace by manuscript block

| Manuscript block | Primary archived sources |
|---|---|
| Abstract and C1 | E05, E06/E06-efficiency, E13/E13v2, E14, E19 |
| Abstract and C2 | E08, E12, E15/E15-sensitivity, E08v2, E08v3, E11v3 |
| Abstract and C3 | E09, E10, E16, E16 hardware arm |
| Section 5 | E00/configuration snapshot, E11 deployment inputs |
| Section 6.1 | E01, E02R, E12 diagnostics, E17 |
| Section 6.2 | E02/E02R, E12, E17 |
| Section 6.3 | E03, E04v2, E04v3 |
| Section 6.4 | E05, E12, E13, E19, E13v2 |
| Section 6.5 | E14 |
| Section 6.6 | E06, E07, E06-efficiency |
| Section 6.7 | E08, E12, E15/E15-sensitivity, E08v2, E08v3 |
| Section 7 | E09, E10, E16 and hardware arm |
| Section 8 | E11, E11v2, E11v3 |
| Supplement | E15-sensitivity, E19, E06-efficiency, E16, E08v2/v3, E13v2 |

## Final findings and dispositions

1. **E08v3 nominal profile-bias endpoint:** the archived ten-draw range ends
   at +7.496, while the prose still said +6.1. Corrected to the rounded +7.5
   in `draft.md`, `main.tex`, and the experiment registry; the supplement
   retains the exact +7.496 value.
2. **Nine-falsifier tally:** the introduction's prose omitted E02R and could
   be read as counting the two E15 implementation blocks separately. It now
   counts unique registered arms, explicitly states that the one E15 arm
   blocked two implementations, and matches the nine-row supplementary
   ledger.
3. **Author front matter:** a `% TODO` inside `\thanks{}` initially commented
   out the visible metadata and left a blank asterisk. The final four-author
   list, four linked ORCIDs, common University of Deusto affiliation and
   institutional corresponding-author email now render correctly.
4. **Table 1 layout:** column proportions and type size were adjusted after
   rendering to remove the only overfull line without changing content.

## Recomputed high-risk quantities

- E08v3: all four counting rows, 400-draw coverage ranges, ten-draw profile
  coverage/bias ranges, and the stored-prediction column were checked against
  `E08v3_multidraw.json`.
- E13v2: the weighted signal fraction, component radii, resolution counts,
  zero false certifications, and the diagnostic extrapolation
  `5,000 × 64² ≈ 2 × 10^7` labels were checked against
  `E13v2_baw_allocation.json`.
- E19: archive identity for all 12 score comparisons, 11/3,060,
  11/7,700, 6/7,980, and the weight bound 7.22421 × 2.05 = 14.80963 were
  checked against `E19_fresh_world_validity.json` and its registered status.
- E16: all six supplement rows were recomputed from the 30 per-configuration
  records; decimal half-up formatting was applied where the displayed tenth
  is exactly on a half boundary.
- E15: all 18 family/model rows were compared at four-decimal precision to
  `E15_sensitivity.json`.
- E06: the overall and four margin-bucket stopping-time quartiles were checked
  against `E06_nstar_efficiency.json`.

## Build and visual gate

- `main.tex`: MiKTeX/pdfLaTeX, 26 pages, 850,886 bytes; zero overfull boxes,
  unresolved citations, or unresolved references.
- `supplement.tex`: MiKTeX/pdfLaTeX, 7 pages, 411,805 bytes; zero overfull
  boxes or unresolved references.
- Repository regression suite: 127/127 tests passed in the project virtual
  environment.
- All 33 rendered pages were inspected after the final compilation. No
  clipping, overlap, missing graphics, illegible table, or float-order defect
  remains. Figure S16 and Tables S1--S10 are present in the supplement.

F8.2 is complete and the front matter is complete. Submission-only actions
(sealed-role disposition, Zenodo publication, arXiv submission, CI/tagging)
remain separately governed by the release decision log.
