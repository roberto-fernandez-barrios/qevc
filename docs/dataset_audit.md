# Dataset Audit

**Status:** v1.0 — 2026-08-10. Gate 1 and Gate 6 assessment per spec §7.
Sources: direct inspection of Zenodo/CERN Open Data records, the official
FAIR Universe repositories (execution-verified on this machine's platform), and
the competition papers. Exact URLs and identifiers throughout; anything not yet
verified locally is marked ⏳ and blocks the affected item, not the gate.

---

## 1. LEVEL I — Controlled collider world

### 1.1 Selected: FAIR Universe HiggsML Uncertainty benchmark

| Item | Value |
|---|---|
| Canonical release | Zenodo record 15131565, DOI `10.5281/zenodo.15131565` (concept `10.5281/zenodo.15131564`), published 2025-04-03 |
| File | `FAIR_Universe_HiggsML_data.zip`, 15.14 GB → one parquet (~16 GB) + metadata JSON |
| License / access | CC-BY-4.0, open, no registration |
| Local copy | `data/raw/fair_universe/FAIR_Universe_HiggsML_data.parquet` (16.80 GB, 220,099,101 rows × 31 cols verified; bundled metadata JSON declares sum_weights 1,051,433 @ 10 fb⁻¹). Zip SHA-256 `adaa3dd81a02663051aa93f960bc1c5ee67a78d25c091015bb020b1f9cd7dcb5`, deleted after verified extraction (disk budget, §4) |
| Systematics code | github.com/FAIR-Universe/HEP-Challenge, vendored at `external/HEP-Challenge`, commit `31816a0d8c8dda03d4b28d9e824674821756962b`, `systematics.py __version__ = 4.0` |
| Physics | H→ττ (τ had-lep) vs Z→ττ, ttbar, diboson; Pythia 8.2 + Delphes 3.5.0; luminosity convention 10 fb⁻¹ |
| Size | ~220M generated events in the public parquet (paper abstract says 280M; discrepancy noted, does not affect us — we subsample); 120M private hold-out (not needed) |
| Schema | 16 PRI + 12 DER features + `weights`, `labels` (1=signal), `detailed_labels` ∈ {htautau, ztautau, ttbar, diboson} |
| Class balance | unweighted: ztautau 63.4%, htautau 33.6%, ttbar 2.6%, diboson 0.4%; **weighted signal fraction ≈ 0.1%** (Σw ≈ 1.05M expected events: 1,015 signal) |
| Weights | `w = σ × L / N_gen`; subset loaders renormalize to preserve Σw |
| Benchmark papers | arXiv:2410.02867 (dataset + competition, NeurIPS D&B), arXiv:2509.22247 (results overview) |

### 1.2 Nuisance parameters (official semantics, spec §6 requirement)

| Nuisance | Nominal | Official prior | Clip | Application |
|---|---|---|---|---|
| `tes` | 1.0 | N(1.0, 0.01) | [0.9, 1.1] | scales `PRI_had_pt`; MET corrected by the recoil of the tau shift; DER recomputed |
| `jes` | 1.0 | N(1.0, 0.01) | [0.9, 1.1] | scales jet pts + `PRI_jet_all_pt`; MET corrected per jet; DER recomputed |
| `soft_met` | 0.0 GeV | LogNormal(0, 1) | [0, 5] | adds N(0, soft_met) to MET px/py — **stochastic given θ** (seed-controlled) |
| `ttbar_scale` | 1.0 | N(1.0, 0.02) | [0.8, 1.2] | weight scale on ttbar events |
| `diboson_scale` | 1.0 | N(1.0, 0.25) | [0, 2] | weight scale on diboson events |
| `bkg_scale` | 1.0 | N(1.0, 0.001) | [0.99, 1.01] | weight scale on all background |

After TES/JES/soft-MET the official `postprocess()` re-applies event selection
(`PRI_had_pt` ≥ 26 GeV; jets < 26 GeV deleted with `PRI_n_jets` decrement):
**shifted environments lose events — selection migration is part of the physics
and must not be "fixed".**

**Finding (pinned by tests):** the raw parquet carries a *looser* preselection
than the analysis selection — `postprocess()` drops ~7.5% of raw events even at
nominal θ (verified on the bundled official sample: 1000 → 925). Therefore the
nominal analysis dataset D₀ is `apply_environment(raw, NOMINAL)`, never the raw
file; all splits and models operate downstream of nominal post-selection, and
sub-threshold raw events exist precisely so upward shifts can migrate events
*into* the selection.

### 1.3 Verified defect in official code (must work around)

`systematics()` guards the normalization block with
`if "detailedlabel" in data_syst.columns` while the real column is
`detailed_labels` → passing `ttbar_scale` / `diboson_scale` / `bkg_scale` to
`systematics()` is a **silent no-op** (confirmed by execution: ttbar weight sum
unchanged with `ttbar_scale=2.0`; both repos, master @ 2026-08). The official
competition pipeline is unaffected because it applies normalizations inside
`get_bootstrapped_dataset()`.

**Mitigation (adopted):** `qevc.systematics` applies weight scalings directly
(three multiplications on `weights` keyed by `detailed_labels`) and calls
`systematics()` only for feature-level shifts (TES/JES/soft-MET). E00 includes a
regression test that reproduces both the bug and our workaround, so an upstream
fix cannot silently change semantics. Reported upstream as good citizenship. ⏳

### 1.4 D_θ regeneration API (execution-verified on Windows / Python 3.13)

```python
from systematics import systematics                      # external/HEP-Challenge/ingestion_program
out = systematics(dset, tes=1.02, jes=0.99, soft_met=2.0, seed=31415, dopostprocess=True)
# dset = {"data": df_PRI, "weights": w, "labels": y, "detailed_labels": dl}
# norm nuisances: applied by qevc.systematics on weights (see 1.3)
```

Cost: ~tens of seconds per million events including DER recompute, parallel per
chunk over 20 cores. The official pseudo-experiment generator
(`get_bootstrapped_dataset`: μ scaling + norm scaling + Poisson fluctuation +
row repetition) is reused for E08 physics inference.

### 1.5 Official evaluation protocol (adopted for E08)

Participants output per pseudo-experiment `{mu_hat, delta_mu_hat, p16, p84}`
(68.27% interval for μ); μ_true ~ U(0.1, 3); nuisances drawn from the priors;
score combines mean interval width with an empirical-coverage penalty. We reuse
the interval/coverage estimands (SAP §1.2) but report them raw (bias, RMSE,
width, coverage) instead of the composite competition score.

### 1.6 Spec §7 criteria — Level I verdict

| Criterion | Assessment |
|---|---|
| Physics relevance | ✅ H→ττ with realistic detector simulation |
| Ground truth | ✅ labels + `detailed_labels` on all public events |
| Systematics | ✅ six physically defined nuisances with official code |
| Real-data counterpart | ✅ CMS H→ττ 2012 (§2 — same process) |
| Features | ✅ 28 tabular features; compact subsets feasible for QK |
| Reproducibility | ✅ DOI'd data, versioned code, deterministic seeds (except soft_met, by design stochastic given θ — seeds recorded) |
| Scale | ✅ 220M events ≫ any classical baseline need |
| Quantum subset | ✅ stratified weighted subsets; procedure fixed in configs |
| Physics inference | ✅ native μ / interval / coverage protocol |

**GO** — pending only E00 validation of the local copy (schema, yields,
systematics round-trip) before any model training.

### 1.7 Rejected / fallback Level I candidates

- **ATLAS HiggsML 2014 (Kaggle)** — opendata.cern.ch record 328, 818k events,
  CC0. Real ATLAS full-sim but no built-in systematics (only third-party TES
  skewing scripts). **Fallback** if FAIR Universe fails E00; would weaken C1.
- **FAIR Universe single-TES variant** (Codabench 4346) — same data, TES only;
  useful cross-check of our 1-D sweeps, not a primary.
- **FAIR Universe Weak Lensing** (arXiv:2604.14451) — sibling OoD design but
  image-based cosmology; out of scope.
- **IRIS-HEP AGC ttbar 2015** — excellent systematics machinery but MC-only
  (no real data) and 1.8 TB; not suitable here.

---

## 2. LEVEL II — Real collider world

### 2.1 Selected: CMS Open Data H→ττ 2012 (μ + τ_h, 8 TeV)

Reference analysis: record 12350 (DOI `10.7483/OPENDATA.CMS.GV20.PR5T`),
following CMS HIG-13-004; code
github.com/cms-opendata-analyses/HiggsTauTauNanoAODOutreachAnalysis (GPLv3).

| recid | Sample | Role | Events | Size |
|---|---|---|---|---|
| 12351 | GluGluToHToTauTau | signal MC | 477k | 197 MB |
| 12352 | VBF_HToTauTau | signal MC | 492k | 232 MB |
| 12353 | DYJetsToLL M-50 | Z→ττ/ll MC | 30.5M | 9.3 GB |
| 12354 | TTbar | MC | 6.4M | 3.5 GB |
| 12355–12357 | W1/W2/W3JetsToLNu | MC | 75.7M | 29.4 GB |
| 12358 | Run2012B TauPlusX | **real data** | 35.6M | 10.9 GB |
| 12359 | Run2012C TauPlusX | **real data** | 51.3M | 15.9 GB |

All CC0-1.0, no authentication; QCD is data-driven from the same-sign control
region (documented in 12350) — no QCD MC exists, which our framework handles
naturally (background-normalization nuisance + CR evidence).

**Working set:** verified 10% mirror with identical 69-branch schema at
`https://root.cern/files/HiggsTauTauReduced/` (≈ 6.9 GB total, HTTP range
requests OK) for development; final paper numbers from the full opendata.cern.ch
files of the samples actually used (portal ignores Range headers → full-file
downloads, ~18 MB/s verified).

### 2.2 Feature parity with Level I

The 69-branch reduced-NanoAOD schema supports all HiggsML-style DER analogues:
m_vis, mT(μ,MET), pt ratios, ΔR/Δη(μτ), pt_H, pt_tot, jet multiplicity, mjj,
Δη_jj, MET (+covariance, significance), centralities. No MMC di-tau mass; the
collinear-approximation mass is computable. The `qevc.preprocessing` layer maps
both worlds into one feature dictionary so classifiers and auditors are
representation-identical across levels.

### 2.3 Sim-to-real information structure (spec §20 discipline)

- Real data: **no event-level truth, ever.** Information set is I1 (unlabeled
  features) + control-region aggregates:
  - same-sign μτ region (QCD-dominated) — yield + m_vis shape;
  - Z→μμ companion channel (records 12365/12366 + DY MC 12353, identical
    schema) — peak position/width/yield validates lepton scale, efficiency,
    pileup;
  - high-mT(μ,MET) sideband — W+jets normalization;
  - b-tag-enriched region — ttbar normalization;
  - data/MC yield ratios, npvs and MET distributions.
- These aggregates enter the auditor as *evidence about p(x) and background
  normalizations*, never as proxy labels. Claims certified on real data are
  restricted to what this information can support; everything else must return
  UNRESOLVED (fail-closed by construction, spec §20).
- MC truth on Level II MC (gen-matching branches) is used for training and for
  simulation-side validation only.

### 2.4 Practicality (verified)

uproot 5.7.5 + awkward 2.12.0 install and read these files on this exact
platform (Windows 11, Python 3.13) with no ROOT/CMSSW. XRootD has no Windows
wheels → HTTPS downloads. Working set after skim + feature engineering: < 1 GB
parquet.

### 2.5 Spec §7 criteria — Level II verdict

| Criterion | Assessment |
|---|---|
| Real collision data | ✅ Run2012B+C TauPlusX (~11.5 fb⁻¹, 8 TeV) |
| Matching MC | ✅ signal + Z/tt/W; QCD via documented data-driven CR |
| Documented selection | ✅ HIG-13-004-derived reference analysis with code |
| Manageable format | ✅ flat trees, laptop-scale mirror, CC0 |
| Truth discipline | ✅ no event labels on data — matches fail-closed design |

**GO for Gate 6 feasibility** — E11 stays last in the execution order; its
absence would not invalidate Level I results (spec Gate 6 fallback).

### 2.6 Level II fallback

2015 POET series (records 31000–31057; SingleMuon Run2015D + TT samples with
scale/PS variations) if a 13 TeV channel were required — at ~50–100 GB/sample
cost, via per-file subsetting. Not planned.

---

## 3. Cross-level coherence

Both levels study **the same physics process** (H→ττ against Z→ττ/tt/EW
backgrounds) with compatible high-level features: Level I supplies controlled
nuisance-parameterized ground truth; Level II supplies a genuine deployment
distribution with only partial, aggregate evidence. This is the strongest
available public instantiation of the paper's central question and removes the
"different process, different conclusions" reviewer objection.

## 4. Risks and predeclared handling

| Risk | Handling |
|---|---|
| 280M vs 220M event-count discrepancy in benchmark paper | does not affect subsampled use; noted; question sent upstream ⏳ |
| `soft_met` stochastic given θ | seeds recorded; environments defined as (θ, seed); replication across ≥3 seeds in affected experiments |
| Norm-scale no-op bug resurfacing via upstream fix | regression test in E00 pins semantics |
| Selection migration changes environment sample sizes | never "corrected"; metrics use weights; auditors see realistic post-selection data |
| 8 TeV (Level II) vs 13-TeV-like Delphes (Level I) | no cross-level transfer of trained models is claimed; levels are linked by methodology, not by pooled training |
| Disk (~42 GB free) | zip deleted post-extraction; working parquets in float32 |

## 5. Gate decisions

- **Gate 1 (controlled systematics reproducible & meaningful): GO**, conditional
  on E00 completing without unexplained mismatches.
- **Gate 6 (real-data demonstration feasible): GO** (H→ττ 2012 selected).
