# Novelty Matrix

**Status:** v1.1 — 2026-08-31 (literature checked through 31 August 2026).
Gate 0 assessment per spec §30. Built from targeted literature sweeps
(QML-in-HEP; quantum-kernel theory; trustworthy-ML certification/shift;
HEP systematics-aware ML). arXiv IDs were verified during the sweep unless
marked ⏳ (re-verify before citing in the manuscript).

Column key — **QML**: quantum model studied · **HEP**: collider data/task ·
**PhSys**: *physical* collider systematics (not generic noise) · **Shift**:
distribution / sim-to-real shift of the *data* · **KGeo**: kernel/representation
geometry analysis · **PartLab**: partial-label / label-budget evaluation ·
**Cert**: certification or error-controlled validation of claims · **PhysInf**:
physics-level inference (μ, intervals, coverage) · **Real**: real collision data.
✓ = central, ~ = partial, · = absent.

## Cluster A — QML for collider physics

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| Mott+ 2017, Nature 550 (annealing H→γγ) | ✓ | ✓ | · | · | · | · | · | · | · |
| Terashi+ 2021, CSBS (VQC/QSVM) arXiv:2002.09935 | ✓ | ✓ | · | · | · | · | · | · | · |
| Wu+ 2021, PRR 3 (QSVM-kernel ttH) arXiv:2104.05059 | ✓ | ✓ | · | · | ~ | · | · | · | · |
| Fadol+ 2024, IJMPA (CEPC QSVM) arXiv:2209.12788 | ✓ | ✓ | · | · | · | · | · | · | · |
| Woźniak, Belis+ 2024, Commun. Phys. (QK anomaly) arXiv:2301.10780 | ✓ | ✓ | · | · | ~ | · | · | · | · |
| Alvi, Bauer, Nachman 2023, JHEP arXiv:2206.08391 | ✓ | ✓ | · | · | · | · | ~ | · | · |
| Ait Haddou+ 2026, PTEP arXiv:2511.15672 | ✓ | ✓ | ~ | · | · | · | · | ~ | · |
| Maier+ 2026, EPJ QT (QELM, Kaggle HiggsML) arXiv:2510.13994 | ✓ | ✓ | · | · | ~ | · | · | · | · |
| Brown, Spannowsky & Williams 2026 (detector-inspired smearing) arXiv:2608.11330 | ✓ | ✓ | ~ | ✓ | · | · | · | · | · |

## Cluster B — Quantum-kernel theory and trust

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| Havlíček+ 2019, Nature 567 arXiv:1804.11326 | ✓ | · | · | · | ✓ | · | · | · | · |
| Huang+ 2021, Nat. Commun. (power of data) arXiv:2011.01938 | ✓ | · | · | · | ✓ | · | ~ | · | · |
| Kübler+ 2021, NeurIPS (inductive bias) arXiv:2106.03747 | ✓ | · | · | · | ✓ | · | · | · | · |
| Thanasilp+ 2024, Nat. Commun. (concentration) arXiv:2208.11060 | ✓ | · | · | · | ✓ | · | ~ | · | · |
| Canatar+ 2023, TMLR (bandwidth) arXiv:2206.06686 | ✓ | · | · | · | ✓ | · | · | · | · |
| Wang+ 2021, Quantum (NISQ kernels) arXiv:2103.16774 | ✓ | · | · | · | ✓ | · | · | · | · |
| Schnabel & Roth 2025, QMI (benchmark scrutiny) arXiv:2409.04406 | ✓ | · | · | · | ✓ | · | ~ | · | · |
| Miroszewski+ 2024 (shot-cost rules for fidelity/projected kernels) arXiv:2407.15776 | ✓ | · | · | · | ✓ | · | ~ | · | · |
| Casas, Bonet-Monroig & Pérez-Salinas 2026, npj QI (embedding class margin) DOI:10.1038/s41534-026-01330-y | ✓ | · | · | · | ✓ | · | ~ | · | · |

## Cluster C — QML validity, robustness, monitoring

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| Weber+ 2021, npj QI (hypothesis-test certificates) arXiv:2009.10064 | ✓ | · | · | · | · | · | ✓ | · | · |
| Guan+ 2021, CAV (formal verification) arXiv:2008.07230 | ✓ | · | · | · | · | · | ✓ | · | · |
| Caro+ 2023, Nat. Commun. (OOD quantum dynamics) arXiv:2204.10268 | ✓ | · | · | ~ | · | · | ~ | · | · |
| Park & Simeone 2024, IEEE TQE (quantum conformal) arXiv:2304.03398 | ✓ | · | · | · | · | · | ✓ | · | · |
| Spencer+ 2026 (adaptive QCP, HW drift) arXiv:2511.18225 | ✓ | · | · | ~ | · | · | ✓ | · | · |
| Kempkes+ 2026, MLST (underdetermination in PQCs) arXiv:2504.03315 | ✓ | · | · | ~ | · | · | ✓ | · | · |
| Q-SafeML 2026 (drift monitoring) arXiv:2509.04536 | ✓ | · | · | ✓ | · | · | ~ | · | · |

## Cluster D — Systematics-aware classical ML in HEP

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| Louppe+ 2017, NeurIPS (pivot) arXiv:1611.01046 | · | ✓ | ✓ | ~ | · | · | · | ~ | · |
| de Castro & Dorigo 2019, CPC (INFERNO) arXiv:1806.04743 | · | ✓ | ✓ | · | · | · | · | ✓ | · |
| Ghosh, Nachman, Whiteson 2021, PRD arXiv:2105.08742 | · | ✓ | ✓ | ~ | · | · | · | ✓ | · |
| Ghosh & Nachman 2022, EPJC (cautionary decorrelation) arXiv:2109.08159 | · | ✓ | ✓ | ~ | · | · | ~ | ✓ | · |
| ATLAS NSBI 2024/25, Rep. Prog. Phys. arXiv:2412.01600 | · | ✓ | ✓ | ~ | · | · | ~ | ✓ | ✓ |
| Flek+ 2026 (hidden systematics in NNs) arXiv:2605.07470 | · | ✓ | ✓ | ✓ | · | · | ~ | ~ | ~ |
| **FAIR Universe** 2024/25 arXiv:2410.02867, 2509.22247 | · | ✓ | ✓ | ✓ | · | · | ~ | ✓ | · |

## Cluster E — Certification, shift, label-efficient evaluation (general ML)

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| Garg+ 2022, ICLR (ATC + impossibility) arXiv:2201.04234 | · | · | · | ✓ | · | · | ~ | · | · |
| Rosenfeld & Garg 2023, NeurIPS (Dis²) arXiv:2306.00312 | · | · | · | ✓ | · | · | ✓ | · | · |
| Kossen+ 2021, ICML (active testing) arXiv:2103.05331 | · | · | · | · | · | ✓ | ~ | · | · |
| Farquhar+ 2021, ICLR (LURE) arXiv:2101.11665 | · | · | · | · | · | ✓ | ~ | · | · |
| Waudby-Smith & Ramdas 2024, JRSS-B (betting CS) arXiv:2010.09686 | · | · | · | · | · | ~ | ✓ | · | · |
| Karampatziakis, Mineiro & Ramdas 2021, ICML (off-policy CS) arXiv:2102.09540 | · | · | · | ~ | · | ✓ | ✓ | · | · |
| Waudby-Smith+ 2022/25 (anytime-valid adaptive off-policy inference) arXiv:2210.10768 | · | · | · | ~ | · | ✓ | ✓ | · | · |
| Podkopaev & Ramdas 2022, ICLR (risk monitoring) arXiv:2110.06177 | · | · | · | ✓ | · | · | ✓ | · | · |
| Chugg+ 2023, NeurIPS (auditing fairness by betting) arXiv:2305.17570 | · | · | · | ~ | · | ~ | ✓ | · | · |
| Angelopoulos+ 2023, Science (PPI) arXiv:2301.09633 | · | · | · | · | · | ✓ | ✓ | · | · |
| Zrnic & Candès 2024, ICML (active inference) arXiv:2403.03208 | · | · | · | · | · | ✓ | ✓ | · | · |
| Park+ 2022, ICLR (PAC sets, covariate shift) arXiv:2106.09848 | · | · | · | ✓ | · | · | ✓ | · | · |
| Tibshirani+ 2019, NeurIPS (weighted conformal) arXiv:1904.06019 | · | · | · | ✓ | · | · | ✓ | · | · |
| CELEUS 2026 (e-process LLM eval) arXiv:2606.20820 | · | · | · | · | · | ✓ | ✓ | · | · |
| Kim 2026 (fail-closed deployment gating) arXiv:2606.24996 | · | · | · | ~ | · | · | ✓ | · | · |
| Chen & Weng 2026 (sim-to-real betting e-process, robotics) arXiv:2606.24038 | · | · | · | ✓ | · | · | ✓ | · | ~ |
| Rabanser+ 2019, NeurIPS (failing loudly) arXiv:1810.11953 | · | · | · | ✓ | ~ | · | ~ | · | · |
| Kornblith+ 2019, ICML (CKA) arXiv:1905.00414 | · | · | · | · | ✓ | · | · | · | · |

## This work

| Work | QML | HEP | PhSys | Shift | KGeo | PartLab | Cert | PhysInf | Real |
|---|---|---|---|---|---|---|---|---|---|
| **This paper** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Gap analysis

Sweep conclusion (searches enumerated in the survey logs, August 2026):

1. **Collider-QML robustness under detector variability is no longer an open
   category.** Brown, Spannowsky & Williams train on a reference distribution
   and evaluate frozen quantum autoencoders and supervised data-reuploading
   classifiers under controlled feature-level smearing. The work uses exact
   simulation and a simplified detector-inspired variability model, and calls
   realistic detector systematics, finite shots and device noise future work.
   It does not include official nuisance parameterizations, rate-only effects,
   information-conditional claim certification, signal-strength inference, or
   a realized noisy Gram deployment.
2. **No QML paper uses the FAIR Universe HiggsML Uncertainty benchmark** (zero
   quantum entries in the competition; no follow-ups found).
3. **The specific combination remains underexplored:** error-controlled claim certification under
   shift + explicit information-set conditioning + label-budget n* + a scientific
   downstream inference task. Nearest neighbors each miss ≥2 axes: CELEUS (no
   shift, no info-sets), Chugg+ (labeled stream assumed, no info-set hierarchy),
   Podkopaev–Ramdas (continuous labels, no claim framing), Dis² (upper bound
   only, uncheckable assumption), PPI/active-testing line (no shift semantics),
   weighted-conformal/PAC-sets line (set coverage, not claim verdicts),
   FAIR Universe itself (empirical scoring, no certified auditor, no QML).

### Differentiators to claim (and nothing more)

- Evaluation under official, physically parameterized collider nuisances,
  including both shape and rate-only effects, while separating feature-only
  from aggregate/control-region evidence. This is a scope distinction, not a
  priority claim over all collider-QML shift studies.
- Information-set-conditional, fail-closed certification framework
  (SUPPORTED/REFUTED/UNRESOLVED with anytime-valid error control) applied to
  collider classifiers, quantum and classical.
- Propagation of quantum-classifier degradation to signal-strength
  inference validity (bias/width/coverage) under systematics.
- Kernel-geometry shift diagnostics as *risk sensors* with an explicit
  out-of-environment predictive test (H2) — never sold as certificates.

### Standing on (infrastructure/theory this work consumes)

FAIR Universe benchmark (data + nuisance semantics); betting-CS/e-process
statistics (Waudby-Smith–Ramdas; Howard+); active-testing estimators
(LURE); kernel-trust theory (Huang+, Thanasilp+, Canatar+, Miroszewski+,
Casas+) for feature-map design discipline, finite-shot resource costs and
expected embedding/concentration failure modes.
Weighted anytime-valid inference is established by the off-policy confidence
sequence literature. Theorem 1 claims only the exact fixed-threshold algebraic
reduction for this physics-weighted ratio estimand and its integration with the
fail-closed information hierarchy.

### Watch items (fast-moving threats)

- Yang/Zhang/Yue muon-collider group (quantum methods drifting toward
  physics-level statistics). [2026-08-10: JHEP 01 (2026) 023 published —
  cite published form; no systematics-aware follow-up found.]
- Ait Haddou group PTEP follow-ups. [2026-08-10: none beyond PTEP 2026(6)
  063C02.]
- Any second-round FAIR Universe competition attracting a quantum entry.
  [2026-08-10: none for HiggsML; the new track is Weak Lensing Phase 2
  (NeurIPS 2026, arXiv:2604.14451) — cosmology, evidence the paradigm is
  expanding, not a threat.]
- Nearest methodological neighbor found 2026-08-10: Chen & Weng
  arXiv:2606.24038 (betting e-process certification of sim-to-real transfer,
  robotics) — cite and differentiate: no information-set hierarchy, no
  collider physics, no physics-level inference.
- Re-run targeted searches before submission (spec §31: continuous review).
- **Verification status (2026-08-10): all 12 previously-flagged arXiv IDs
  verified correct; venue data recorded in the sweep log.**
- **Resolved 2026-08-31:** Brown, Spannowsky & Williams arXiv:2608.11330 is
  now the nearest collider-QML robustness neighbor and is cited explicitly.

## Pre-submission re-sweep (2026-08-11; spec §31)

Four targeted searches (QML×HEP×shift; anytime-valid certification under
deployment shift; FAIR Universe quantum entries; nuisance-aware classifier
validity in HEP). **No new work combines the paper's axes; the four
differentiators stand.** Adjacent items to cite-and-differentiate at the
bibliography stage:

- arXiv:2512.07074 (Profile OmniFold — ML unfolding with nuisance
  parameters, CMS case studies): cluster D; nuisance-aware *measurement*,
  no claim certification, no information-set conditioning, no QML.
- arXiv:2602.22248 (ML-HEQUPP review — ML on heterogeneous/edge/quantum
  hardware for particle physics): cluster A context; survey, no validity
  framework.
- arXiv:2606.11949 (online shift detection + conformal adaptation):
  cluster E; monitoring/adaptation, not fail-closed claim certification,
  no physics inference, no label-budget n*.
- arXiv:2606.14028 (anytime-valid confirmation of label-shift
  corrections): cluster E; nearest in statistical machinery, but
  label-shift-specific, no information-set hierarchy, no collider
  systematics, no downstream inference validity.
- FAIR Universe challenge results paper (arXiv:2509.22247) confirms the
  leaderboard remains free of quantum entries — gap statement #2
  unchanged.

## Gate 0 verdict

## Final novelty audit (2026-08-31)

Primary sources checked: Brown, Spannowsky & Williams (arXiv:2608.11330v1,
submitted 11 August 2026); Miroszewski et al. (arXiv:2407.15776v1); and Casas,
Bonet-Monroig & Pérez-Salinas (npj Quantum Information,
DOI:10.1038/s41534-026-01330-y). Targeted searches also screened recent work on
covariant-kernel concentration, finite-size shot-resource scaling, adversarial
quantum robustness and quantum-data distribution shift. Those papers do not
directly overlap C1--C3 beyond limitations already represented by the cited
kernel and certification literature, so they were not added merely to enlarge
Related Work.

| Old claim | New competitive literature | Final defensible claim |
|---|---|---|
| Collider-QML studies have not evaluated deployment shift. | Brown et al. evaluate frozen collider QML models under controlled detector-inspired feature smearing. | Existing work has begun evaluating collider QML robustness under detector variability. This paper instead integrates official shape and rate-only nuisances, I0--I3 evidence, fail-closed anytime-valid claim certification, signal-strength inference and finite-shot/noisy Gram deployment. |
| Finite-shot kernels are an unstructured implementation caveat. | Miroszewski et al. give spread/concentration rules for shot precision and resource estimation. | This paper consumes shot-cost limitations as prior art and contributes downstream propagation of each realized Gram through refitting, calibration, thresholding and claim resolution. |
| Kernel limitations are adequately represented by concentration and bandwidth alone. | Casas et al. connect data-induced randomness and embedding quality to classification through class margin. | Embedding choice is acknowledged as a classification limitation; the paper claims neither an optimal embedding nor quantum advantage and uses a frozen bandwidth-limited map plus matched RBF control. |
| The combination is categorically first. | The component literatures now overlap more strongly. | No first-ever/first-study claim is made. Novelty is the specific integration and the resulting information-conditional claim semantics. |

## Gate 0 verdict

**GO.** The updated claim is narrower but remains materially distinct. The
paper does not rely on priority for collider shift or on quantum advantage.
