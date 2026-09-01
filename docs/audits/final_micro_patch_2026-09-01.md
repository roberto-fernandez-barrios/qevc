# Final 0.3.3 micro-patch audit — 2026-09-01

This audit records the bounded bibliographic, statistical-presentation and
scope patch authorized by D-044. The release is `0.3.3 /
npjqi-submission-v1.3`, with reserved Zenodo DOI
`10.5281/zenodo.22227158` under concept DOI `10.5281/zenodo.21894291`.

## Authorized changes

- Add the primary references by Agliardi et al. on finite/noisy
  quantum-kernel PSD projection and by He, Krause and Wang on FAIR-HUC
  signal-strength inference.
- Remove 68.7% from the abstract while retaining the correlated cell-level
  counts in Results and Supplementary Information.
- Derive a descriptive aggregation across 30 noisy-kernel deployments from
  `results/tables/E16_proposition4_instantiation.json` only.
- State the frozen finite-population batch-deployment scope, narrow the
  independent-MC limitation to the evaluated archived fixed-template
  construction at the studied MC size, and replace probabilistically ambiguous
  world-independence wording with verified row-disjointness by construction.
- Synchronize version, DOI, package, GitHub and Zenodo metadata.

## Scientific integrity

No experiment, seed, sample, dataset, model, feature map, hyperparameter,
claim, threshold, alpha level, likelihood, CMS analysis, QPU job, PSD repair,
E16 primary result or E20 result is added or changed. The other manuscript is
untouched. The new deployment summary is a deterministic derivative and adds
no population inference.

## Final gates and artifact freeze

- `pytest`: 143 passed.
- npj submission gate: 77/77 passed.
- mathematical/scientific/semantic audit: 170/170 passed; high-risk numeric
  and semantic gates passed.
- Proposition 4 deployment-summary reproduction check: exact match to the
  frozen source JSON; 120 deployment/scope/repair rows, 60 condition cells per
  row, and zero truth-sign flips among HOLDS.
- Citation audit: 60 bibliography entries, 40 cited keys and zero missing
  citations. Both new DOI resolvers returned HTTP 200 and their primary-source
  metadata matched the bibliography.
- Clean build: 28-page manuscript, 13-page Supplementary Information and
  one-page cover letter, with no LaTeX/package warnings, undefined references,
  undefined citations, overfull boxes or build errors.
- Independent build from the source ZIP: all three PDFs were byte-identical to
  the packaged PDFs, with identical extracted text and page counts.
- Full visual inspection: all 42 pages inspected; no clipping, overlap, broken
  glyphs, missing pages or illegible final-size elements were found.
- `git diff --check`: passed.
- Protected scientific inputs: zero changed paths. Hashes for the E16 primary
  table, E16 Proposition 4 source, PSD source, QPU raw data, frozen configs,
  E20 results and CMS results are unchanged from the 0.3.2 baseline.

Final SHA-256 hashes:

| Artifact | SHA-256 |
|---|---|
| Manuscript PDF | `482364C9FC18803DE8159A5C6B15E1ED0EBAE8B13C8037E848400EDFA2BF161B` |
| Supplementary Information PDF | `3DD6FC8135250D6DFB6BABCE0308F14EEC9928A18EF15E27253330DB242695AF` |
| Cover letter PDF | `214B31ECA7F7F3ECF240094D1DA909A0FF8602CE19B550F1189F3C77670FABC6` |
| Submission ZIP | `3EDDE555413B358EDBA2D1DA859E526A7D5CAEDA5ED70E344F588C1E156FC940` |
| E16 PSD sensitivity JSON | `5EDE2CF71D69B4C50A9BC164A02248634B70FFAA47FBD35101B36A1CB3DAABF1` |
| E16 Proposition 4 source JSON | `E98FF380CF64F2042153A09709C04850B82BB5A797AF6F10A9E4DABCF587115B` |
| E16 Proposition 4 deployment summary JSON | `4E09E3B86A38F26EB7892F49FC55C146BECFC5C7DDF6BFF210CD3EEBB60CE31B` |

The Git commit/tag and the GitHub/Zenodo byte-for-byte public-asset
verification are reported in the final release handoff, because they occur
after this audit file is frozen into the release commit.
