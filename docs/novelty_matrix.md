# Novelty Matrix

**Status:** v1.0 — 2026-08-10 (literature current through August 2026).
Gate 0 assessment per spec §30. Built from four parallel literature sweeps
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

1. **No paper evaluates quantum classifiers under physically meaningful collider
   systematics or MC-vs-data shift.** All QML "robustness" work concerns
   hardware/shot noise or adversarial perturbations; all collider-QML papers
   evaluate on fixed nominal simulation. Closest partial touches: Ait Haddou+
   (normalization uncertainty enters only a final limit, classifier unaudited);
   Mott+ (overtraining-robustness claim only); Alvi+ (critical validation of QML
   claims, no systematics).
2. **No QML paper uses the FAIR Universe HiggsML Uncertainty benchmark** (zero
   quantum entries in the competition; no follow-ups found).
3. **No work in any field combines** error-controlled claim certification under
   shift + explicit information-set conditioning + label-budget n* + a scientific
   downstream inference task. Nearest neighbors each miss ≥2 axes: CELEUS (no
   shift, no info-sets), Chugg+ (labeled stream assumed, no info-set hierarchy),
   Podkopaev–Ramdas (continuous labels, no claim framing), Dis² (upper bound
   only, uncheckable assumption), PPI/active-testing line (no shift semantics),
   weighted-conformal/PAC-sets line (set coverage, not claim verdicts),
   FAIR Universe itself (empirical scoring, no certified auditor, no QML).

### Differentiators to claim (and nothing more)

- First evaluation of quantum-kernel event classifiers under parameterized
  physical collider systematics as **nuisance-induced (shape-level)
  distribution shift** of the inputs. (Sharpened 2026-08-10: Ait Haddou+
  PTEP 2026 folds rate-only background-normalization uncertainty into final
  limits without evaluating the classifier under shift — cite and
  distinguish.)
- First information-set-conditional, fail-closed certification framework
  (SUPPORTED/REFUTED/UNRESOLVED with anytime-valid error control) applied to
  collider classifiers, quantum and classical.
- First propagation of quantum-classifier degradation to signal-strength
  inference validity (bias/width/coverage) under systematics.
- Kernel-geometry shift diagnostics as *risk sensors* with an explicit
  out-of-environment predictive test (H2) — never sold as certificates.

### Standing on (infrastructure/theory this work consumes)

FAIR Universe benchmark (data + nuisance semantics); betting-CS/e-process
statistics (Waudby-Smith–Ramdas; Howard+); active-testing estimators
(LURE); kernel-trust theory (Huang+, Thanasilp+, Canatar+) for feature-map
design discipline and expected failure modes (concentration under shift).

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

## Gate 0 verdict

**GO.** The combination remains materially underexplored on every pairing that
defines the contribution; the paper does not rely on quantum advantage and
survives all four alternative outcomes of spec §37.
