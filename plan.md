# Working plan — arXiv v1 endgame (reconstructed 2026-08-12)

> Reconstructed after a power loss destroyed the session-local copy, then
> cross-checked against Roberto's saved "Hoja de ruta v2" (kept in notes).
> This version lives in the repo so it survives. Source of truth for scope
> and rules remains D-028/D-029/D-030 and the experiment registry; this
> file only sequences the work. Roadmap-v2 phase numbers are cited as
> (F5.2) etc. where useful.

**Objective:** bring the paper to the highest level the current project
permits and submit arXiv v1 (three-contribution framing per D-028).

---

## 1. State ledger (verified against repo, 2026-08-12)

Done and committed:

- E12–E16 campaign + post-campaign audit; manuscript v0.3 baseline.
- Extension campaign registered before execution (D-028): E17, E19,
  E08v2, E11v3 mandatory; E07v2, E13v2 priority B.
- **E17 complete** — arm (b) falsifier TRIGGERED (degradation signs
  draw-dependent across worlds; kept per frozen falsifier); ±0.05 caveat
  quantified (between-world std 0.030–0.050).
- **E19 complete** — validity replicates in fresh world; archives
  certified byte-identical 12/12.
- **E11v3 complete** — all four CMS ledger verdicts stable v1→v2→v3;
  C3 refuted on calibrated grounds; both M8 limitations closed.
- Manuscript surgery: intro restructured around C1–C3, formal
  environments placed (Thm 1, Props 2–4 — Prop 4 IS the roadmap's F2.4
  stability-margin result, resolved in its assumption-explicit form —
  C_dep/C_ideal), §5 redesigned, E17/E19/E11v3 integrated, back matter
  finalized (reproducibility, availability, acknowledgements); falsifier
  tally harmonized to five firings. Archive-mining items F1.1–1.6 all
  landed (∂μ̂/∂θ, n* vs Wald floor, Figs 3/6/S16, E19).
- Number-verification pass (~178 exact matches); figures 3/6/S16 and
  4b/7b/8b validated.
- Release hygiene D-030: README/CITATION current, CI workflow, container
  recipe, root spec collapsed to pointer.
- Zenodo DOI reserved: 10.5281/zenodo.21894292 (deposition 21894292,
  draft; populated + published only at F8/submission).
- Pre-submission literature re-sweep: Gate 0 GO re-confirmed; four
  adjacent items queued for cite-and-differentiate (2512.07074,
  2602.22248, 2606.11949, 2606.14028).

Completed but **not yet dispositioned or committed** (survived the power
loss; both JSON files parse clean, manifest `finished_at` present,
git_commit e132602, dirty=False, wall 5409 s):

- **E08v2 run complete — BOTH frozen falsifiers FIRED. `all_pass: false`.**
  - `results/tables/E08v2_independent_mc.json`
  - `results/manifests/E08v2_4df40c2496d2_seed1812_1786484445.json`

## 2. E08v2 outcome and diagnosis (the immediate work item)

Measured:

- Arm (a) counting, accounting (iii) `independent_bb`, nominal env:
  coverage 1.000 / 1.000 / 0.9916 for the three gated models (band
  0.6827 ± 0.02) → falsifier (a) fired ("implementation invalid →
  blocked until fixed and re-registered").
- Arm (b) profile L2 with independent templates: flagship
  tes=0.98 × A:xgboost coverage **0.000** (threshold 0.633; E15 shared
  reference 0.7188) → falsifier (b) fired (downgrade "profiling restores
  validity" to shared-simulation-conditional; revise §6.7).
- Decisive extra fact: the three **nominal** calibration cells also
  collapse (coverage 0.000–0.0088, μ-bias +3 to +11, nuisances dragged:
  jes ≈ −1.8σ, diboson_scale ≈ 0.16) — the collapse is driven by
  belief-template MC noise alone, not by any environment shift.

Diagnosis (code audited — `run_e08v2.py` arithmetic is correct; no
scale/alignment bug found; row-alignment asserts passed):

- Belief-half MC-stat is huge in the SRs: s₀ relerr 0.23–0.32 (heavy
  tails, tiny signal ESS). The realized belief-vs-truth offsets are
  b₀-level several × Poisson σ.
- Accounting (iii) adds the (honest) delta-method term, which dominates
  the Poisson term ~8× → intervals ~8× wider. With a **single** realized
  belief draw, conditional coverage is degenerate (≈1 if the one draw's
  offset < z·σ_bb, ≈0 otherwise). The 0.6827 target is only observable
  **marginally over belief draws**. The falsifier's premise (single-draw
  coverage lands in the band) was a design oversight of the falsifier,
  not an arithmetic bug in the estimator.
- Same structure in arm (b): all six profile cells share the one belief
  draw, so the six collapses are one correlated realization. The
  magnitude (±25% signal-yield noise, worse per-bin) is intrinsic to the
  half size + weight tails, so most draws will carry comparable
  (random-sign) template distortions — but the single-draw design cannot
  distinguish "L2 invalid under independent MC at this size" from "this
  draw is pathological".

## 3. Decision point — D-031 — RESOLVED 2026-08-12 (Option A executed
under Roberto's delegation; E08v3 registered, run, both outcomes
integrated: falsifier (a) fired → D-015-closure claim withdrawn,
direction conservative; strength rule → generic → §6.7/§9/intro/tally
revised; E18 stays deferred with recorded reasoning). Also executed
same day: D-032 (E19 weighted-arm estimand corrected after
pre-submission-audit HIGH finding; re-run verified; 6/7,980 = 0.08%).
Original decision text kept below for the record.

Options, either is publishable under D-028 rules:

- **Option A (recommended): re-register a bounded multi-draw follow-up
  (E08v3)** — K independent half-split draws (new salts), counting arm
  over {nominal + a small registered env subset} with the same three
  accountings, and the profile arm over {flagship + one nominal cell};
  report the distribution over draws (marginal coverage of accounting
  (iii); distribution of L2 coverage/bias). Environments/scores are
  already cached; per-draw cost is dominated by the L2 fits — bound it
  (e.g. K = 10, 200 PEs/cell) to stay under a few hours. Then write
  §6.7/§9 from the marginal answer. Falsifier for E08v3 frozen before
  running (e.g. accounting-(iii) marginal nominal coverage outside
  0.6827 ± 0.03 → the BB-lite delta-method correction itself is
  invalidated and the counting arm is published as such).
- **Option B: accept the single-draw result as-is** — record both
  firings, downgrade §6.7 to shared-simulation-conditional with the
  single-draw structure disclosed as a limitation, rewrite the §9
  sentence that currently says the caveat "is addressed by" E08v2
  (it is *measured*, adversely, not resolved), tally 5→7 falsifier
  firings. Cheapest; leaves the marginal question open in print.

In both options the arm-(b) downgrade of §6.7 stands (the frozen
falsifier consequence was pre-accepted); Option A determines *how
strongly* it is stated and whether the counting-BB correction survives
as a valid marginal procedure.

D-031 must ALSO disposition two clauses the roadmap ties to E08v2:

- **E18 Latin-hypercube trigger (D-028):** E18 stays deferred "unless
  E08v2 raises a concrete question it can answer". E08v2 DID raise a
  concrete question — but it is about belief-side template statistics /
  single-draw degeneracy, not about the additive-morphing cross-terms
  E18 targets. Expected disposition: E18 remains deferred, with that
  reasoning recorded explicitly in D-031 (not silently).
- **Abstract dependency:** abstract item (v) currently claims the
  profile likelihood "restores the coverage ... at a measured ×1.8–3.4
  price". E08v2 arm (b) qualifies exactly that sentence
  (shared-simulation-conditional). The abstract rewrite (F5.2, step 4.5
  below) must therefore WAIT for the D-031 outcome — it cannot be
  drafted before the E08v2 wording is settled.

## 4. After D-031 — integration (order matters) — steps 1–3 DONE
2026-08-12; step 4 (targeted number re-verification) pending alongside
the audit-doc consolidation; step 5 (abstract) next.

1. Registry: E08v2 status block (outcome + diagnosis + disposition —
   status recorded 2026-08-12, disposition pending); decisions.md:
   D-031 entry incl. E18 disposition. Commit E08v2 artifacts +
   registry + decision + this plan together. pytest green before the
   commit (roadmap end-to-end rule: suite green, manifest
   git_dirty:false, falsifier dispositioned).
2. (If Option A) register + run E08v3; record outcome.
3. Manuscript: §6.7 revision (downgrade wording per outcome), §9
   limitations block rewrite (the sentence saying the shared-simulation
   caveat "is addressed by" E08v2), §10 discussion touch if needed;
   falsifier tally update everywhere it appears (currently "five
   firings" → seven, or per E08v3 outcome).
4. Re-run the number-verification pass on the touched sections only.
5. **Abstract rewrite (F5.2 — NOT yet done):** currently 509 words /
   3,780 chars, still headed "Abstract (draft)". Target 200–250 words,
   ≤ 1,920 chars (arXiv limit), structured C1/C2/C3 + one hardware
   sentence + honest-negative framing; no branches on priority-B
   experiments; item (v) reworded per D-031 outcome. Also remove the
   draft-status header block at the top of draft.md (lines 3–11) at
   LaTeX conversion.

## 5. Priority B disposition (D-028) — CLOSED 2026-08-12 (D-033):
E13v2 RUN to the impossibility branch (validity PASS; falsifier (b)
fired; TNR_w certifiable, TPR_w information-limited ~2×10⁷ labels;
spec §4c + resolve_ba_presplit + 4 tests; manuscript §6.6/§9
integrated; tally now NINE firings). E07v2 DECLINED with recorded
disposition. Experimental program for arXiv v1 is CLOSED. Original
text below for the record.

E07v2 / E13v2 run only if the mandatory set completed "on schedule".
E08v2's firing consumed schedule; decide explicitly and record in
D-028's disposition list rather than dropping silently:

- E07v2 (active acquisition): substantial implementation (new module +
  tests + WoR-CS). Recommend: **defer, disposition recorded** unless
  Roberto wants it.
- E13v2 (BA_w allocation): smaller (spec derivation + one MC battery).
  Recommend: decide after D-031 compute is known.
- E16 priority (b) DD-on/off micro-split: only if the IBM 28-day window
  resets (~2026-09-07) before the freeze AND F8 has not started; never
  critical path (D-027/D-028). At the current pace the freeze lands
  first → most likely outcome: not run, no text debt.

## 6. Submission endgame (after §4 closes)

1. Final figure/table numbering per D-030 amendment (4/4b → 4(a)(b),
   ledger → Table 2, claim×info table → Table 1); captions pass;
   renumbering map recorded.
2. **LaTeX conversion and front matter DONE 2026-08-12.** The final four-author
   list, ORCIDs, common University of Deusto affiliation and corresponding
   email are present; funding/back matter is done. Bibliography from
   `manuscript/bibliography` (citation keys already in §2; sources in
   novelty matrix); cite-and-differentiate the four adjacent arXiv
   items from the re-sweep. Figures as PDFs with embedded fonts.
3. **Supplementary DONE 2026-08-12** in `manuscript/supplementary/` (7-page
   compiled PDF); final arXiv `anc/` packaging remains a submission mechanic.
   Contents: long proofs, audit-trail summary, registry extract
   (falsifiers + corrections incl. E08v2), extended tables (E15
   sensitivity, E19, n* efficiency, E16 diagnostics, E08v2/E08v3,
   priority-B if run).
4. **Pre-submission adversarial audit F8.1 DONE 2026-08-12:**
   `docs/audits/pre_submission_audit_<date>.md` — adversarial pass over
   ALL extension code (E17/E19/E08v2[/E08v3]/E11v3 runners + figure
   scripts) and adversarial math review of every step of the Thm 1 /
   Props 2–4 proofs; findings dispositioned.
5. **Number verification F8.2 DONE 2026-08-12:** prior manuscript-wide trace
   plus 73/73 reproducible final-LaTeX checks and bidirectional semantic diff;
   see `docs/audits/f8_2_latex_audit_2026-08-12.md`.
6. **Fresh-eyes PDF read-through DONE 2026-08-12:** all 26 main and 7
   supplementary pages inspected; both compile clean with every citation,
   reference, figure and table resolved. Final arXiv source-package build
   remains part of submission mechanics.
7. **Sealed-role endgame disposition DONE 2026-08-12 (D-035):**
   seed-101/seed-121 `final_eval` KEPT SEALED for journal review. The E16
   DD-on/off micro-split is not run because F8 began before the IBM window
   reset.
8. **arXiv package DONE 2026-08-12:** primary quant-ph, cross-list hep-ph +
   stat.ME, license CC BY 4.0, `.bbl` included; abstract ≤ 1,920 chars;
   source archive independently compiled clean (26 + 7 pages).
9. **CI green gate** before tagging: then F8: populate + publish Zenodo
   deposition 21894292 (record deposit SHA-256s), submit to arXiv, tag
   `arxiv-v1`, add `preferred-citation` to CITATION.cff when the arXiv
   record exists, update README status line.

## Session hygiene (lesson from the power cut)

- This file stays in the repo and is updated at each state change.
- Commit completed experiment artifacts + registry/decision updates in
  the same sitting they are produced — never leave finished results
  uncommitted overnight.
