# Pre-submission adversarial audit — 2026-08-12

Scope (roadmap F8.1): every runner and script added by the extension
campaign (E17, E19, E08v2, E08v3, E11v3; `make_figures_extension.py`,
`summarize_e15_sensitivity.py`, `summarize_nstar_efficiency.py`) and an
adversarial line-by-line review of the formal results (Theorem 1,
Propositions 2–4, including the underlying spec §4b proof and the
D-024(ii) α budget). Method: three independent adversarial reviewers,
one per surface, instructed to hunt result-changing defects and to
verify every suspicion against the archived tables before reporting;
every actionable finding was then independently re-verified by the
consolidating author-side reviewer against the raw tables before any
fix was applied. The formal-proof review was done directly, not
delegated. E08v3 was audited by code reading before its run completed;
its executed outputs were subsequently checked against the registered
falsifiers (registry E08v3 status).

The E12–E16 campaign surface was audited previously
(`post_campaign_audit_2026-08-11.md`); nothing there was re-opened.

## Findings and dispositions

| # | Severity | Finding | Verification | Disposition |
|---|---|---|---|---|
| 1 | HIGH | Manuscript claimed nuisance tracking "slope 0.99–1.00 for TES/JES and norms"; the archived table has JES = 0.71 for the tree — a real single-cell fit pathology (jes = +2σ: fitted +0.5σ, μ̂ bias +3.1, coverage 0.012), plus 0.98-level values outside the stated range | Re-derived from `E15_inference.json` raw cells; other three tree JES cells cover 0.648–0.662 with correct pulls | **Fixed** — disclosed in intro C2 and §6.7; ranges corrected (0.98–1.00; L3 TES +4.8..+8.7; L1 scoped to gated models). Commit 3190308 |
| 2 | HIGH | E19 weighted arm audited environment-scaled weights w(θ), not the registered nominal w(0) (D-019 §4; E13 Part-B frozen convention) — the same defect E13's audit-C1 fix corrected; ~15/41 envs affected, 3 of 6 published weighted false-cert events in weight-only envs | Confirmed against tables: E19 m_t_w varied across weight-only envs where E13's is exactly constant; superseded E13 v1 shows the same varying pattern | **Fixed** — D-032: runner corrected (E13 idiom `w0_all[rid]`), re-run (75 s); frozen expectation held: unweighted + landscape blocks reproduced v1 EXACTLY; weighted headline 6/7,980 = 0.08% ≤ α; v1 table preserved (`*_v1_theta_weights`); registry + manuscript updated. Commit ef5b504 |
| 3 | LOW | E11v3 C4 verdict rule in code (z > 3 → SUPPORTED) is not coupled to the registered falsifier boundary (z < 5 → corrected verdict); a z in (3, 5) would have printed a self-contradictory table | Not triggered: z_with_mc_stat = 18.78, `c4_z_below_5 = false`, verdict consistent | **Documented** — archived run stands; any future E11 re-run must couple the verdict rule to the registered boundary |
| 4 | LOW | E08v3 `bb_predicted` diagnostic deviates from the exact marginal model (Jensen on the mean ratio; no μ² weighting; 2-dp-rounded inputs) | Background Σw² dominates signal terms by 2–5 orders; effect below reporting precision; not falsifier-gated | **Documented** — the exact prediction is computable from the stored per-draw variance components; measured bb (0.546–0.660) vs stored prediction (≈0.52) already shows the heavy-tail excess |
| 5 | LOW | E08v2 config declares `profile_spotcheck.seed: 1815`, never consumed (runner uses `stable_seed`, deterministic) | Confirmed in code + config | **Documented** — documentation mismatch only |
| 6 | LOW | E19 registered weighted salt "E19W" never consumed; registry simultaneously said "identical draws" (which is what ran) | Confirmed in code | **Fixed** — contradiction resolved in D-032; table now records the salts actually used (`audit_salts`) |
| 7 | LOW | Registry E19 status "false refutation 1/12,260" arithmetically impossible (true unweighted streams = 19,680 − 7,700 = 11,980) | Recomputed from E19/E12 tables | **Fixed** — corrected to 1/11,980 (D-032) |
| 8 | LOW | E17 registered estimand (i) partially delivered: no unweighted between-world summary | Confirmed against `E17_worlds.json` | **Completed** — derived from archived per-world tables (D-032.5): unweighted AUC ranges 0.002–0.004 (0.029 rbf_8f) vs weighted std 0.030–0.050; prior worlds archived weighted-only AUC (disclosed; four-world unweighted version dispositioned as not run) |
| 9 | LOW | E19 did not replicate E13 Part-B class-conditional claims (TPR_w/TNR_w) | Confirmed in code + table | **Disclosed** — scope reduction recorded in D-032 and the registry status |
| 10 | LOW | E08v3 table lacks in-table E08v2-vs-E08v3 counting comparison rows (acceptance criterion) | Confirmed | **Satisfied at report level** — comparison rows recorded in the registry status (point 3), where the acceptance is read |
| 11 | LOW | Prop 4(ii) stated deterministically but holds on the CS coverage event (prob ≥ 1 − α); radius/margin compared across scales (Z vs metric) without the E[u]/w_max bridge | Line-by-line proof review | **Fixed** — qualifiers added in `formal_results.md` and the placed manuscript statement. Commit 27d6983 |

## Formal-proof review (direct, not delegated)

Theorem 1 (a)–(c): verified line by line — boundedness and the exact
equivalence E[Z(τ)] ≥ τ ⟺ R ≥ τ hold as stated; the time-uniform
argument correctly reduces false certification to a coverage violation;
the u ≡ 1 reduction is exact. Proposition 2 and the spec §4b proof:
identical-law argument and the Poisson power argument sound; the
D-024(ii) α budget (2·α/4 + α/2 = α) checks. Proposition 3: tower
property with the stated measurability conditions (ω independent of the
label stream; threshold σ(ω)-measurable) — sound, honestly presented as
elementary. Proposition 4: (i)/(iii) verified; (ii) fixed per finding 11.

## Benign observations (recorded, no action)

Dead code `bucket_of()` in `summarize_nstar_efficiency.py` and
`TRACK_THETA` in `summarize_e15_sensitivity.py`; `np.std` ddof=0 over
n=3 draws in Fig 3's visual band; quantiles over 3-dp-pre-rounded
ratios (≤5e-4); E08v3 smoke default output path sits under
`results/tables/` (a real smoke run in this program wrote to the
scratchpad; no `*_DELETEME` file exists in the repo); `n*` efficiency
recompute reproduced the published table exactly (518 cells, median
2.07, IQR [1.56, 2.97], buckets 3.35/3.19/1.98/1.46); figure data
series spot-checked against tables (Fig 3 exact-zero weight-only
ΔMMD²; Fig 6 480 jointly resolved cells, nothing clipped; S16 all 30
configs); E17/E19 sealed-role handling machine-enforced (`final_eval`
popped unless explicitly touched); E17 disjointness genuinely asserted
with SHA-256 archived in-table; E19 integrity chain (subset indices,
row alignment, byte-identical score certification 12/12) verified.

## Residual scope (tracked in plan.md)

The ~220-number verification and the semantic diff run on the LaTeX at
F8.2 (after conversion); the priority-B experiments are undecided and
outside this audit; any code added after this date (LaTeX tooling,
figure regeneration) joins the F8.2 pass.
