# Conversion notes: draft.md -> main.tex

Source: `manuscript/main/draft.md` (1,163 lines, v0.3 of 2026-08-11).
Target: `manuscript/latex/main.tex`. Strictly faithful conversion; no content
changes. Not compiled (per instructions).

## Counts

- **Sections:** 11 numbered (`\section`) + 3 unnumbered back-matter
  (`\section*`: Reproducibility statement, Data and code availability,
  Acknowledgements).
- **Subsections:** 26 (`\subsection`): 2.1-2.6, 4.1-4.7, 5.1-5.4, 6.1-6.7,
  7.1-7.2.
- **Paragraph pseudo-headings:** 8 (`\paragraph`): C1-C3 in Sec. 1; Events and
  environments / Frozen deployment / Quantum kernels / Claims, estimands, and
  information sets / Conditional validity in Sec. 3.
- **Formal environments:** Theorem 1 (Sec. 4.3), Propositions 2 (Sec. 3),
  3 and 4 (Sec. 7). Shared counter, explicitly seeded (see below).
- **Figures:** 8 floats; Figs. 4, 7, 8 are subfigure pairs (a)/(b), so 11
  graphics files total. Fig. S16 excluded (supplement).
- **Tables:** 3 (D-030 numbering: Table 1 = claim x information set, Sec. 6.5;
  Table 2 = CMS ledger, Sec. 8; Table 3 = frozen deployment, Sec. 5.2).
- **Citations:** 45 `\cite*` commands, 45 unique keys (43 arXiv +
  mott2017nature + barlow1993fitting). Verified: every arXiv ID appearing in
  the draft is cited exactly once, and every cited key exists in
  `manuscript/bibliography/references.bib`.

## Non-obvious mapping decisions

1. **Draft-status header dropped.** Lines 3-11 ("Draft v0.3 ... LaTeX
   conversion.") plus the following `---` rule are working notes, removed per
   spec.
2. **Bold numbered pseudo-headings -> `\subsection`.** The source formats
   2.1-2.6 and 4.1-4.7 as bold run-in headings (`**2.1 ...**`), not `###`.
   They were converted to `\subsection{}` so that (a) LaTeX auto-numbering
   reproduces the source numbers exactly, and (b) the prose cross-references
   "Sec. 4.3" and "Sec. 4.4" (in Sec. 2.5) get real `\ref` anchors
   (`sec:weighted-cert`, `sec:i3-method`). Trailing periods of those headings
   dropped (heading style). Unnumbered bold lead-ins (C1-C3, the Sec. 3
   blocks) stayed `\paragraph{}` as in source.
3. **Theorem-counter seeding.** `\newtheorem{theorem}{Theorem}` +
   `\newtheorem{proposition}[theorem]{Proposition}` share one counter, but
   Proposition 2 appears in Sec. 3, *before* Theorem 1 in Sec. 4.3. Seeding:
   `\setcounter{theorem}{1}` before Prop 2 (prints "Proposition 2"),
   `\setcounter{theorem}{0}` before Theorem 1 (prints "Theorem 1"),
   `\setcounter{theorem}{2}` immediately after Theorem 1 so Sec. 7 prints
   Propositions 3 and 4. Printed numbers match every prose reference
   (all prose references use `\ref`, so they track automatically).
4. **Table-counter seeding (D-030).** Table 3 (Sec. 5.2) precedes Table 1
   (Sec. 6.5) in document order: `\setcounter{table}{2}` before the Sec. 5.2
   float, `\setcounter{table}{0}` before the Sec. 6.5 float; the Sec. 8 ledger
   then naturally prints Table 2.
5. **Proposition 2's Corollary** kept as a bold run-in (`\textbf{Corollary.}`)
   inside the proof paragraph, exactly as in source; no corollary environment
   introduced.
6. **Proofs are plain text.** "Proof: ..." paragraphs kept as ordinary prose
   (as in source); the amsthm `proof` environment (with QED box) was NOT used.
7. **Table lead-in sentences.** Floats cannot sit inline, so the three
   sentences that introduced tables with a colon now carry explicit
   `(Table~\ref{...})` references: Sec. 5.2 "... deployment snapshot) are
   given in Table 3." (colon -> period); Sec. 6.5 "The claim x
   information-set table (Table 1) is the campaign's conceptual center:";
   Sec. 8 "The ledger (Table 2) is stable across all three analyses, ...:".
   No other wording changed.
8. **Sec. 8 heading** "(E11, E11v2, E11v3; Fig. 9 = ledger)" -> "(E11, E11v2,
   E11v3; Table~2 = ledger)" per the draft's own D-030 numbering plan (former
   Fig. 9 is Table 2).
9. **Figure references in headings** are literal numbers ("Fig.~2",
   "Figs.~4(a) and 4(b)", "Figs.~5--6", "Figs.~7(a) and 7(b)", "Figs.~8(a)
   and 8(b)", "Fig.~8") -- no `\ref` inside sectioning arguments (hyperref
   bookmark safety). Figure numbering is deterministic (floats appear in
   order 1-8), so the literals are correct. All *body* references use
   `\ref`. Companion-figure references mapped 4b -> 4(b), 7b -> 7(b),
   8b -> 8(b).
10. **Fig. S16**: not included (supplement). The prose reference in
    Proposition 4 kept literally as "Fig.~S16" (points to the supplement);
    its caption block was dropped with the working section.
11. **Captions working section deleted.** The "Figure and table captions
    (working section...)" block near the end of the draft was consumed into
    the float captions verbatim (with the "Figure N (name)." headers turned
    into caption lead-ins, since LaTeX supplies "Figure N:") and the section
    itself deleted. Its "Numbering plan (D-030 amendment)" paragraph was
    implemented (subfigures, Table 1/2/3, S16 supplementary) rather than
    reproduced.
12. **Citations.** Key scheme `arxiv<ID>` (dot kept), non-arXiv
    `mott2017nature`. Pure parentheticals "(Author, Venue Year, arXiv:ID)"
    -> `\citep{...}`; the human-readable author/venue/volume strings
    (e.g. "Havlicek et al., Nature 567, 2019"; "Wu et al., PRR 3") now live
    only in the future bib entries -- this is the one place source-visible
    text moves into the bibliography. Subject-position names ("Mott et al.",
    "Alvi, Bauer and Nachman", "Ait Haddou et al.", "Kempkes et al.",
    "Chen & Weng") -> `\citet{...}`. Parentheticals containing extra prose
    keep manual parens with `\citealp`: the Park&Simeone/Spencer pair ("which
    adapts to hardware drift"), "INFERNO --- ", "ATLAS NSBI, ", the FAIR
    Universe pair ("results overview"), and the active-testing/LURE/PPI list.
13. **Barlow & Beeston** (Sec. 2.5) has no arXiv ID in the draft; the
    pre-existing `manuscript/bibliography/references.bib` carries
    `barlow1993fitting`, so the prose was kept verbatim with
    `\citep{barlow1993fitting}` appended (45th citation).
14. **Symbol conventions.** `R^d` -> `\mathbb{R}^d`; the draft's middle-dot
    products kept as `\cdot`; unicode super/subscripts -> math (`10^{-4}`,
    `s_0`, `pb^{-1}`); `MMD²` -> `MMD$^2$`; information sets I0/I1/I2(n)/I3
    kept as upright text tokens exactly as the draft writes them; state kets
    `\phi` used for the feature map phi; `f*` (star) -> `f^\star`, `m^\star`;
    identifiers with underscores (`source_val`, `ibm_marrakesh`,
    `ttbar_scale`, `A:rbf_svc`) kept with escaped underscores, `\texttt{}`
    only where the source uses backticks.
15. **Figure file mapping** (via `\graphicspath{{../../results/figures/}}`):
    fig1_framework, fig2_tes_replicated, fig3_family_blindness,
    fig4_geometry_sensor + fig4b_out_of_grid_sensor (subfig a/b),
    fig5_certification_landscape, fig6_label_economics,
    fig7_h5_decoupling + fig7b_inference_levels (subfig a/b),
    fig8_shots_hardware + fig8b_estimation_noise_verdicts (subfig a/b).
16. **Float placement.** Fig. 1 in Sec. 1; Figs. 2-8 in the sections whose
    headings/captions tie to them (6.2, 6.3, 6.3, 6.4, 6.6, 6.7, 7.1).
    Fig. 3's first prose reference is in Sec. 3 (Proposition 2 corollary) --
    a forward reference to the Sec. 6.3 float.
17. **Wide tables** (Tables 1 and 2) set in `\footnotesize` with
    ragged-right `p{}` columns (`array` package added for the `>{}`
    specifiers); Table 3 in `\small` plain `lll`. Nothing exceeds
    `\textwidth`; no `table*`/`resizebox` needed in one-column article.
18. **Subfigure tags** (a)/(b) produced by empty subcaptions; the working
    section's caption text (which already narrates "(a) ... (b) ...") is the
    main caption.
19. **Fig. 6** is a single PDF whose caption narrates (a)/(b) panels -- kept
    as one non-subfigure float (only 4/4b, 7/7b, 8/8b are file pairs).

## %%TODO markers left (1)

1. `\thanks{%%TODO: affiliation, ORCID, email --- author to supply}` on the
   author (closing brace on the next line so the file compiles with an empty
   thanks).

Note: `manuscript/bibliography/references.bib` already exists in the repo
(created in parallel) and contains all 45 cited keys, plus extra entries
(datasets, the four adjacent cite-and-differentiate items) that are simply
not cited from main.tex -- verified by key-set comparison.

## Citation keys (44 from the draft's citation scheme + 1)

arXiv (43): arxiv1611.01046, arxiv1804.11326, arxiv1806.04743,
arxiv1904.06019, arxiv2002.09935, arxiv2008.07230, arxiv2009.10064,
arxiv2010.09686, arxiv2011.01938, arxiv2101.11665, arxiv2103.05331,
arxiv2103.16774, arxiv2104.05059, arxiv2105.08742, arxiv2106.03747,
arxiv2106.09848, arxiv2109.08159, arxiv2110.06177, arxiv2201.04234,
arxiv2204.10268, arxiv2206.06686, arxiv2206.08391, arxiv2208.11060,
arxiv2209.12788, arxiv2301.09633, arxiv2301.10780, arxiv2304.03398,
arxiv2305.17570, arxiv2306.00312, arxiv2403.03208, arxiv2409.04406,
arxiv2410.02867, arxiv2412.01600, arxiv2504.03315, arxiv2509.04536,
arxiv2509.22247, arxiv2510.13994, arxiv2511.15672, arxiv2511.18225,
arxiv2605.07470, arxiv2606.20820, arxiv2606.24038, arxiv2606.24996.
Non-arXiv (2): mott2017nature (Mott et al., Nature 550, 2017);
barlow1993fitting (Barlow & Beeston -- key taken from the pre-existing
references.bib; no arXiv ID in the draft).

## Verification performed

- Number-multiset diff (all numeric tokens, draft minus dropped header vs
  main.tex): every discrepancy accounted for (unicode superscripts becoming
  ASCII digits, venue years/volumes moved to bib keys, auto-numbered
  headings, dropped S16/working-section blocks, added layout constants and
  counter seeds).
- All 43 draft arXiv IDs present as cite keys (exact set match), each cited
  once; 44 total with mott2017nature.
- Structure counts as listed above; no non-ASCII bytes; no leftover markdown
  (`**`, backticks, `#` headings).
- Rare-word presence sweep (38 distinctive terms) -- all present.
- NOT compiled, per instructions.
