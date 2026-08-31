# Final submission and public-release audit — 2026-08-31

## Scope and outcome

This audit closes D-040 without generating new science. It compares the final
manuscript, Supplementary Information, cover letter, README, novelty matrix,
formal results, decisions, audit trail, submission metadata, release bundle
and public archive. The experimental program remains closed and E20 remains a
preregistered offline NO-GO before hardware.

No scientific blocker was found. All high-return editorial/reproducibility
findings were closed. The remaining imaginable requests are reviewer
preferences or new projects and are rejected for this version.

## Adversarial referee findings

| Class | Finding | Disposition |
|---|---|---|
| A | Mathematical error invalidating C1--C3 | None found after formal and executable audits. |
| A | Unsupported statistical population trend in E16 | None remains; the abstract makes deployment semantics primary and explicitly describes five deployments per budget, heterogeneity and no monotonic population inference. |
| A | False priority claim after new collider-QML shift work | None remains; Brown, Spannowsky and Williams are cited and priority language is removed. |
| B | Direct competitive literature missing | Closed with Brown et al. 2608.11330, Miroszewski et al. 2407.15776 and Casas et al. s41534-026-01330-y, each checked against the primary work. |
| B | Methods require internal YAML navigation to understand the design | Closed: exact features, role sizes, search spaces, inference construction, QK map/shot semantics, IBM provenance limits and CMS C1--C4 semantics are stated in main or supplement. |
| B | CMS heading can overstate the real-data claim | Closed: renamed “Real-data fail-closed case study”; event-level accuracy remains UNRESOLVED and QCD is only a plausible explanation of C4. |
| B | ORCID placeholder, page-size mismatch and supplemental overflows | Closed: no literal placeholder remains; all three PDFs are A4; overflows were removed. |
| B | Public repository/archive version mismatch | Closed with `0.3.0`, tag `npjqi-submission-v1`, version DOI `10.5281/zenodo.22206235` and matching checksums. |
| C | Re-expand or further compress the paper to a simulated referee’s preferred length | Rejected: current 26+11 pages maximize density and self-containment without an arbitrary page target. |
| C | Redesign Figures 3, 4, 7 or 8 despite legible publication-size rendering | Rejected after visual inspection; labels, axes, panels and captions are readable and faithful. |
| C | Further cosmetic rewording after all consistency gates pass | Rejected as diminishing returns before real peer review. |
| D | More seeds, QPU time, qubits, datasets, kernels, tuning, calibration or inference campaigns | Out of scope; these would be another paper, not a submission patch. |

## Executable and document gates

- Repository tests: 127/127 passed.
- High-risk scientific/number/semantic audit: 144/144 passed; bidirectional
  Markdown/LaTeX four-gram coverage 95.2078% and 97.2396%.
- npj submission gate: 53/53 passed; abstract 145 words, 59 bibliography
  entries, longest caption 118 words.
- Citation-key audit: 59 unique bibliography keys, 38 cited keys, no missing
  or duplicate keys; all three new references are cited.
- LaTeX logs: no undefined citation/reference and no overfull box in main,
  supplement or cover letter.
- `git diff --check`: clean apart from platform line-ending notices.
- Independent ZIP build: all three sources compile; page count, A4 size and
  extracted-text SHA-256 are identical to the frozen PDFs.
- Visual inspection: every page of all three PDFs inspected; Figures 3, 4, 7
  and 8 additionally inspected at 180 dpi.

## Frozen artifacts

| Artifact | Pages | TeXcount sum | SHA-256 |
|---|---:|---:|---|
| Manuscript | 26 | 8,301 | `30CB232B95119CB593DD927A909CD78269B40F8C44F9D69BF04E4E7411A42BD7` |
| Supplementary Information | 11 | 3,434 | `52904EB164AC6E24409F16911A98639968E726AE6F685023F87F71547513C8AC` |
| Cover letter | 1 | 566 | `895AF4A38561D70889863C7C81CBF0F9482455988C25ED9E754D6B2FCBF08E01` |
| Submission ZIP | source + three PDFs | — | `B8CF241218C8D472CAC8D7637D706E22120A9F26426CE019CD10D411429BDA96` |

## Public archive and related manuscript

Zenodo version `10.5281/zenodo.22206235` was published under concept DOI
`10.5281/zenodo.21894291`. Its eight files were downloaded after publication;
all eight SHA-256 values matched local files. The previous version DOI
`10.5281/zenodo.21894292` remains public and unchanged.

Immediately before freeze, the distinct manuscript *Sharp Target-Domain
Certificates for Quantum-Kernel Advantage under Distribution Shift* remains
public preprint/Zenodo material and has not been submitted to any journal. The
cover letter states exactly that status. No file in that other work was
changed.

## Stop decision

There is no class-A blocker and every reasonable class-B item is closed. No
further internal review is recommended before real peer review. Only a newly
discovered defect that invalidates a central contribution would reopen the
scientific scope.
