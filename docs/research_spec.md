# Research Specification
## Conditional Validity of Quantum Event Classifiers under Collider Systematics

**Status:** Project blueprint / execution specification  
**Target quality:** Strong Q1-level paper  
**Primary domains:** Quantum Machine Learning, High-Energy Physics, Trustworthy ML, Distribution Shift, Scientific ML  
**Core philosophy:** Do not optimize for a positive quantum result. Optimize for a scientifically defensible result that remains valuable whether quantum models win, lose, or tie classical baselines.

---

# 1. Working Title

Preferred:

**When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics**

Alternative:

**Conditional Validity of Quantum Event Classifiers under Experimental Systematics**

Do not lock the final title until the main empirical contribution is clear.

---

# 2. Central Scientific Question

> Under what experimentally available information can the validity of a quantum event classifier be justified when collider systematics shift the deployment distribution away from the nominal simulation on which it was validated?

The paper must NOT be framed primarily as:

- quantum advantage;
- QSVC vs SVC benchmarking;
- generic robustness to artificial noise;
- another Higgs classification experiment.

The paper must study **what claims about a QML system remain scientifically justified under experimentally meaningful distribution shift**.

---

# 3. Scientific Positioning

The project sits at the intersection of:

- quantum kernels / QML;
- collider event classification;
- simulation-to-data shift;
- experimental systematic uncertainty;
- trustworthy / auditable ML;
- partial-label validation;
- scientific inference under uncertainty.

The scientific contribution must be methodological, not dataset-specific.

The paper should distinguish clearly between:

1. **true target performance**;
2. **observable evidence about target performance**;
3. **claims that can be justified from that evidence**.

This distinction is central.

---

# 4. Core Hypotheses

## H1 — Systematic sensitivity

Quantum kernels exhibit measurable and structured degradation patterns under physically meaningful collider systematics.

We do **not** assume they are more robust than classical models.

Test:

\[
\Delta_\theta(f)=M_0(f)-M_\theta(f)
\]

for quantum and classical models over controlled nuisance parameters.

---

## H2 — Geometry carries predictive information

Changes in quantum-kernel geometry contain information about future target-domain degradation.

Conceptually:

\[
G(K_0,K_\theta)\rightarrow \Delta_\theta(f)
\]

where \(G\) contains geometry-shift descriptors.

This is an empirical hypothesis, not an assumed fact.

---

## H3 — Partial target evidence enables useful certification

A small amount of target information can be sufficient to accept or refute performance claims without fully labeling the target domain.

For information set:

\[
I_n = \{D_S, X_T, Y_{T,L}, |Y_{T,L}|=n\}
\]

estimate or bound whether a claim such as:

\[
M_T(f)\ge \tau
\]

is supported.

---

## H4 — Validity is information-conditional

There exist target environments for which the available information is insufficient to justify a performance claim.

The correct system behavior is therefore:

- **SUPPORTED**
- **REFUTED**
- **NOT CERTIFIED / UNRESOLVED**

The framework must be fail-closed.

---

## H5 — Physics-level reliability can diverge from classifier-level reliability

Good predictive performance does not guarantee valid downstream physics inference.

The project must test whether collider systematics can preserve metrics such as AUC while damaging quantities such as:

- signal-strength estimation;
- confidence interval calibration;
- interval coverage.

---

## H6 — Quantum estimation noise interacts with collider systematics

Finite-shot estimation and hardware noise may amplify, attenuate, or qualitatively alter model degradation caused by experimental systematics.

This interaction should be measured explicitly.

---

# 5. Research Contributions to Aim For

The strongest version of the paper should support as many of the following as the evidence permits.

## C1. Physically grounded robustness map

A systematic evaluation of quantum kernels under collider nuisance parameters rather than generic Gaussian/noise perturbations.

## C2. Information-set conditional validity framework

A formal separation between:

- what is true;
- what is observed;
- what is certifiable.

## C3. Quantum-kernel geometry under physical shift

Characterization of how kernel geometry changes under experimental systematics and whether that change predicts failure.

## C4. Label-efficiency of scientific certification

Estimate:

\[
n^*(\theta,\mathcal C)
\]

the minimum target-label evidence required to resolve a scientific performance claim.

## C5. Physics-level validity

Connect classifier degradation to physical inference quality, not only ML metrics.

## C6. Quantum-specific uncertainty

Study ideal, finite-shot and hardware-estimated kernels under the same systematic environments.

## C7. Simulation-to-real fail-closed demonstration

Apply the developed auditor to real CMS collision data without pretending to possess event-level truth labels.

---

# 6. Experimental Architecture

Two distinct experimental levels are mandatory.

---

## LEVEL I — Controlled Collider World

Primary dataset:

**FAIR Universe / HiggsML Uncertainty-style benchmark**

Purpose:

- controlled ground truth;
- known nuisance parameters;
- reproducible systematic environments;
- classifier-level evaluation;
- physics-level inference;
- validation of the auditor.

Requirements:

- use the official dataset/protocol where possible;
- preserve official nuisance semantics;
- do not replace physical systematics with arbitrary feature noise;
- record exact data release/version/checksum.

Core nuisance dimensions should include, where available:

- Tau Energy Scale (TES);
- Jet Energy Scale (JES);
- soft / missing transverse momentum uncertainty;
- background normalization uncertainties;
- process-specific normalization uncertainties.

Create:

\[
D_\theta \sim P_\theta(X,Y)
\]

for controlled values of \(\theta\).

---

## LEVEL II — Real Collider World

Primary source:

**CMS Open Data**

Purpose:

- simulation-to-real demonstration;
- real detector data;
- stress-test scientific abstention;
- show that the framework does not invent target accuracy where truth is unavailable.

Ideal structure:

\[
\text{Monte Carlo} \rightarrow \text{trained model}
\rightarrow \text{auditor} \rightarrow \text{real CMS data}
\]

Requirements:

- use an analysis channel with corresponding MC and real data;
- prefer an analysis with reproducible CMS Open Data tooling and documentation;
- select a manageable reconstructed/high-level representation;
- do not require raw detector reconstruction unless scientifically necessary;
- document what can and cannot be known on real data.

Event-level truth on real collision data must never be fabricated or implied.

---

# 7. Dataset Selection Gate

Before implementing the full study, create:

`docs/dataset_audit.md`

It must evaluate candidate datasets on:

| Criterion | Requirement |
|---|---|
| Physics relevance | Real collider process |
| Ground truth | Available in controlled benchmark |
| Systematics | Physically defined |
| Real-data counterpart | Preferred |
| Features | Feasible for quantum kernel experiments |
| Reproducibility | Public + documented |
| Scale | Supports large classical experiments |
| Quantum subset | Can define representative reduced subsets |
| Physics inference | Preferably supports downstream quantity estimation |

GO only if at least one controlled benchmark and one real-data demonstration are scientifically coherent.

---

# 8. Data Representation

Do not immediately reduce everything to a tiny arbitrary feature vector.

Run a principled feature-selection study.

Candidate pathways:

1. expert high-level HEP variables;
2. statistically selected compact subsets;
3. PCA or other linear compression;
4. supervised feature-selection methods;
5. physically motivated compact representations.

Quantum dimensionality reduction must be fixed using source/training information only.

No target-label leakage.

Every transformation must be fitted only on allowed training information.

---

# 9. Model Suite

## Quantum primary model

Quantum-kernel SVC.

A general kernel:

\[
K_Q(x_i,x_j)
=
|\langle \phi(x_i)|\phi(x_j)\rangle|^2
\]

Feature maps must be justified rather than selected only because they perform well.

Study controlled variants of:

- number of qubits;
- circuit depth;
- entanglement topology;
- encoding repetition;
- feature scaling;
- exact vs finite-shot estimation.

Avoid a combinatorial feature-map zoo.

---

## Mandatory classical baselines

At minimum:

- linear SVC;
- RBF-SVC;
- gradient-boosted trees (XGBoost / LightGBM or equivalent);
- compact MLP.

Add a stronger HEP-specific baseline if feasible and scientifically justified.

Hyperparameter budgets must be comparable and documented.

Do not tune quantum models more aggressively than classical ones.

---

# 10. Data Splitting

Use strict, predeclared partitions:

- training;
- source validation;
- nominal test;
- target/systematic environments;
- auditor-development split if needed;
- final untouched evaluation environments.

No test-set-driven feature map design.

No selecting nuisance values after seeing which ones produce attractive results.

Use multiple random seeds.

Store exact indices or deterministic split seeds.

---

# 11. Systematic Landscape

For each nuisance parameter \(\theta_j\), evaluate a predeclared grid such as:

\[
-2\sigma,-1\sigma,0,+1\sigma,+2\sigma
\]

when physically supported by the benchmark.

Then evaluate selected combinations:

\[
(\theta_1,\theta_2,\dots,\theta_k)
\]

Do not attempt the full Cartesian product if computationally wasteful.

Use:

- one-dimensional sweeps;
- physically motivated multi-nuisance combinations;
- Latin hypercube / space-filling designs if useful;
- dedicated worst-case combinations.

Produce:

\[
M_f(\theta)
\]

for each model.

Primary outputs:

- BA;
- ROC-AUC;
- PR-AUC where class imbalance warrants;
- calibration metrics;
- expected calibration error if appropriate;
- task-specific physics quantities.

---

# 12. Quantum Kernel Geometry Observatory

For each quantum and kernel baseline, compute a fixed set of descriptors.

Candidate descriptors:

- centered kernel alignment;
- source-target kernel alignment;
- eigenspectrum;
- effective rank;
- spectral entropy;
- trace / norm statistics;
- condition number where meaningful;
- margin distribution;
- class-centroid separation in RKHS;
- within/between-class similarity;
- kernel-target alignment;
- nearest-neighbor consistency;
- pairwise similarity distribution shift.

Define:

\[
G_\theta =
[g_1(\theta),...,g_m(\theta)]
\]

and compare against:

\[
\Delta M_\theta.
\]

Use:

- correlation analysis;
- regression with cross-validation;
- rank consistency;
- out-of-environment generalization;
- calibration of any risk predictor.

Do not claim certification from correlation alone.

Geometry-based models are **risk sensors**, unless formal guarantees are later derived.

---

# 13. Information-Set Conditional Auditing

Formalize a claim:

\[
\mathcal C(M,\tau):
M_T(f) \ge \tau
\]

or a degradation claim:

\[
\mathcal C_\delta:
M_T(f) \ge M_S(f)-\delta.
\]

Define explicit information sets.

## I0

\[
I_0 =
\{D_S, f\}
\]

Source-only.

## I1

\[
I_1 =
\{D_S,f,X_T\}
\]

Target features, no labels.

## I2(n)

\[
I_2(n)=
\{D_S,f,X_T,Y_{T,L}\}
\]

with \(n\) target labels.

## I3

Add known/estimated nuisance information:

\[
I_3 =
I_2(n)\cup\hat\theta
\]

when available.

For each information set, determine what claims are:

- supported;
- refuted;
- unresolved.

The method must explicitly distinguish heuristic warnings from statistically guaranteed conclusions.

---

# 14. Partial-Label Certification

Evaluate:

\[
n \in \{0,5,10,20,50,100,200,\ldots\}
\]

with the final grid adapted to dataset size.

For each:

- nuisance environment;
- model;
- metric claim;
- seed;

estimate:

\[
n^*(\theta,\mathcal C)
\]

minimum labels needed to resolve the claim.

Key figure:

## Certification Landscape

Axes:

- systematic severity / nuisance coordinate;
- number of target labels.

Regions:

- SUPPORTED;
- REFUTED;
- UNRESOLVED.

Report uncertainty across seeds.

---

# 15. Active Auditing

Only add complexity if it provides evidence.

Compare:

- uniform random acquisition;
- classifier uncertainty;
- margin-based acquisition;
- geometry-aware acquisition;
- diversity / coverage acquisition;
- information-aware or worst-case acquisition.

Primary objective:

\[
\min n^*
\]

while preserving statistical validity.

Do not use the labels selected by an adaptive strategy as if they were an IID sample unless the inference method correctly accounts for acquisition.

If active acquisition does not beat random sampling, report that result.

---

# 16. Physics-Level Inference

The project must go beyond classifier metrics if the selected benchmark supports it.

Primary physics quantity:

\[
\mu
\]

signal strength or an equivalent benchmark-defined parameter.

Evaluate:

- bias of \(\hat\mu\);
- RMSE;
- interval width;
- empirical coverage;
- nuisance sensitivity.

Key question:

> Can a classifier remain apparently strong while producing invalid physics inference?

Test:

\[
P(\mu_{\text{true}}\in CI_{1-\alpha})
\]

against nominal coverage.

Compare quantum and classical pipelines.

---

# 17. Failure Propagation Study

Explicitly study the chain:

\[
\text{experimental systematic}
\rightarrow
\text{representation geometry}
\rightarrow
\text{classifier output}
\rightarrow
\text{physics inference}.
\]

Estimate which intermediate signals are predictive of downstream failure.

Do not assume monotonicity.

Look for counterexamples.

---

# 18. Finite-Shot Study

For representative quantum experiments compare:

\[
K_{\mathrm{exact}}
\]

and:

\[
\hat K_{N_{\mathrm{shots}}}
\]

using shot budgets such as:

\[
128,256,512,1024,2048,4096
\]

subject to feasibility.

Measure:

- kernel estimation error;
- PSD violations if any;
- spectral distortion;
- classifier degradation;
- certification instability;
- interaction with collider systematics.

Question:

> Does a certificate valid for the ideal quantum kernel survive realistic kernel-estimation noise?

---

# 19. Quantum Hardware Validation

Hardware is complementary evidence, not the statistical backbone.

Use a representative subset, e.g. order \(10^2\) events rather than pretending full-scale HEP inference on hardware is practical.

Compare:

\[
K_{\mathrm{ideal}},
K_{\mathrm{finite-shot}},
K_{\mathrm{hardware}}.
\]

Requirements:

- record provider/backend;
- device calibration metadata where available;
- transpilation settings;
- circuit depths;
- gate counts;
- shot counts;
- date/time of executions;
- raw results;
- mitigation method if used.

Never hide failed hardware runs.

---

# 20. CMS Real-Data Demonstration

Select one reproducible CMS Open Data analysis channel.

Ideal candidates should have:

- real collision samples;
- corresponding MC;
- documented event selection;
- manageable reconstructed variables;
- sufficiently mature open-data examples.

Pipeline:

\[
MC_{\mathrm{source}}
\rightarrow f
\rightarrow X_{\mathrm{CMS-real}}
\rightarrow Auditor
\]

The output is not "real-data accuracy."

Instead report:

- observable source-target shifts;
- geometry-risk indicators;
- information-set available;
- claims accepted;
- claims refused;
- failure-to-certify behavior.

Use control regions or aggregate physical observables when justified.

The final demonstration should show that the framework **fails closed** rather than creating false certainty.

---

# 21. Statistical Protocol

Predefine before final runs:

- primary metric;
- secondary metrics;
- primary hypotheses;
- significance level;
- confidence interval method;
- multiple-comparison strategy;
- number of seeds;
- effect-size reporting;
- bootstrap/permutation methods where appropriate.

Always report:

- point estimate;
- confidence interval;
- effect size.

Avoid "statistically significant" without practical magnitude.

For large datasets, emphasize effect sizes and calibration over tiny p-values.

---

# 22. Robustness and Negative Experiments

The paper must actively try to falsify itself.

Required negative tests:

1. geometry changes but performance does not;
2. performance changes without a strong geometry warning;
3. interacting nuisance parameters;
4. quantum and classical models fail similarly;
5. active acquisition does not outperform random;
6. finite shots invalidate ideal-kernel conclusions;
7. auditor abstains when target performance was actually adequate;
8. auditor certifies under mild shift but fails under unseen shift;
9. nuisance family misspecification;
10. feature-selection instability.

Report false certification and false abstention separately.

---

# 23. Ablations

Mandatory candidate ablations:

- remove geometry sensors;
- remove target unlabeled information;
- remove nuisance estimates;
- vary label budgets;
- vary qubits;
- vary feature-map depth;
- vary shot count;
- exact vs estimated kernel;
- quantum vs matched classical kernel;
- alternate feature subsets;
- alternate claim thresholds;
- single vs combined nuisances.

Ablations must answer scientific questions, not merely inflate the supplement.

---

# 24. Leakage and Validity Rules

Absolutely forbidden:

- fitting preprocessing on full source+target data;
- selecting features using target labels outside permitted auditor information;
- choosing nuisance settings after inspecting final test results;
- hyperparameter tuning on final target environments;
- reporting target metrics unavailable in real data;
- calling heuristic scores "certificates";
- claiming quantum advantage from a narrow comparator;
- using artificial noise as a substitute for collider systematics;
- omitting negative results that challenge the method.

Implement automated leakage tests where possible.

---

# 25. Reproducibility Requirements

Every result must be reproducible from configuration.

Use configuration-driven experiments.

Each run records:

- git commit;
- config hash;
- dataset version/hash;
- random seed;
- package versions;
- hardware/backend metadata;
- wall-clock time;
- CPU/GPU/QPU resources;
- output artifacts.

Use immutable result manifests.

No manually edited result CSVs.

---

# 26. Repository Architecture

Recommended:

```text
project/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── environment/
│   ├── requirements-lock.txt
│   └── containers/
├── configs/
│   ├── datasets/
│   ├── models/
│   ├── systematics/
│   ├── auditors/
│   └── experiments/
├── data/
│   ├── README.md
│   ├── raw/              # ignored
│   ├── interim/          # ignored
│   └── processed/        # ignored
├── docs/
│   ├── research_spec.md
│   ├── dataset_audit.md
│   ├── novelty_matrix.md
│   ├── statistical_analysis_plan.md
│   ├── experiment_registry.md
│   └── decisions.md
├── src/
│   ├── data/
│   ├── preprocessing/
│   ├── physics/
│   ├── models/
│   │   ├── classical/
│   │   └── quantum/
│   ├── kernels/
│   ├── geometry/
│   ├── systematics/
│   ├── auditing/
│   ├── acquisition/
│   ├── inference/
│   ├── hardware/
│   ├── metrics/
│   ├── statistics/
│   └── utils/
├── experiments/
│   ├── E00_dataset_validation/
│   ├── E01_nominal_baselines/
│   ├── E02_systematic_landscape/
│   ├── E03_kernel_geometry/
│   ├── E04_geometry_failure/
│   ├── E05_conditional_auditing/
│   ├── E06_partial_labels/
│   ├── E07_active_auditing/
│   ├── E08_physics_inference/
│   ├── E09_finite_shots/
│   ├── E10_hardware/
│   └── E11_cms_real_data/
├── results/
│   ├── manifests/
│   ├── tables/
│   ├── figures/
│   └── raw/
├── tests/
├── scripts/
└── manuscript/
    ├── main/
    ├── supplementary/
    └── bibliography/
```

---

# 27. Experiment Registry

Maintain:

`docs/experiment_registry.md`

Each experiment must contain:

- ID;
- scientific question;
- hypothesis;
- inputs;
- information set;
- models;
- nuisance environment;
- metric;
- expected falsifier;
- output files;
- status.

Example:

```text
E03
Question: Does kernel geometry change before target performance collapses?
Hypothesis: H2
Falsifier: geometry descriptors have no reproducible out-of-environment relationship with degradation.
```

---

# 28. Minimum Experiment Set

## E00 — Dataset validation

Validate schemas, distributions, labels, weights, nuisances and benchmark reproduction.

## E01 — Nominal baselines

Establish fully tuned but fair classical and quantum nominal results.

## E02 — Systematic landscape

Map model degradation over nuisance space.

## E03 — Kernel geometry

Measure geometry changes across nuisance space.

## E04 — Geometry → failure

Test predictive relationship without target labels.

## E05 — Conditional auditor

Implement explicit information-set claim resolution.

## E06 — Partial labels

Estimate \(n^*\) for representative claims.

## E07 — Active auditing

Compare label-acquisition strategies.

## E08 — Physics inference

Propagate model behavior to \(\mu\), intervals and coverage.

## E09 — Finite shots

Add quantum kernel estimation uncertainty.

## E10 — Hardware validation

Validate representative conclusions on QPU hardware.

## E11 — CMS real-data demonstration

Apply fail-closed auditing to real collider data.

---

# 29. GO / NO-GO Gates

## Gate 0 — Novelty

GO if literature review supports that the combination of:

- QML;
- collider systematics;
- information-conditional certification;
- physics-level validity;

is materially underexplored.

If not, reformulate before large computation.

---

## Gate 1 — Dataset

GO if controlled systematics are reproducible and scientifically meaningful.

---

## Gate 2 — QML feasibility

GO if quantum kernels can be evaluated on representative subsets without reducing the problem to a scientifically meaningless toy dataset.

---

## Gate 3 — Systematic signal

GO if at least one relevant model exhibits nontrivial, reproducible behavior across physical systematics.

No requirement that quantum outperform classical.

---

## Gate 4 — Methodological value

GO to full paper only if conditional auditing provides information beyond ordinary OOD detection or descriptive robustness plots.

This is critical.

---

## Gate 5 — Physics relevance

Strong-paper gate: classification findings must connect to a physics-level quantity or inference validity.

---

## Gate 6 — Real-data demonstration

Preferred for the strongest version.

If impossible, document why and strengthen controlled validation instead.

---

# 30. Novelty Matrix

Before experiments, create:

`docs/novelty_matrix.md`

Columns:

| Work | QML | HEP | Physical systematics | Domain shift | Kernel geometry | Partial labels | Certification | Physics inference | Real data |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

Include:

- foundational QML-for-HEP works;
- quantum kernel HEP papers;
- sim-to-real/domain adaptation HEP;
- uncertainty-aware HEP;
- FAIR Universe benchmark papers;
- trustworthy/verifiable ML for physics;
- relevant conditional-validation/certification literature.

The paper's novelty must remain visible after this matrix is filled.

---

# 31. Literature Review Requirements

Search continuously until submission.

Prioritize:

- peer-reviewed literature;
- official CERN/CMS documentation;
- INSPIRE-HEP;
- arXiv for very recent QML work;
- primary methodological sources.

Literature categories:

1. quantum kernels;
2. QML in HEP;
3. collider systematics;
4. simulation-to-data discrepancy;
5. domain adaptation in HEP;
6. uncertainty quantification;
7. selective prediction / abstention;
8. risk certification;
9. partial-label validation;
10. active testing;
11. kernel geometry;
12. physics inference under ML selection;
13. finite-shot quantum kernels;
14. QPU noise and kernel estimation.

Keep an annotated bibliography.

---

# 32. Figures the Final Paper Should Aim to Earn

Do not force figures if the result does not justify them.

### Fig. 1 — Framework

Collider systematics → representation → classifier → auditor → physics inference.

### Fig. 2 — Systematic landscape

Quantum and classical performance over nuisance space.

### Fig. 3 — Kernel geometry landscape

How the representation changes under systematics.

### Fig. 4 — Geometry vs degradation

Out-of-environment predictive relationship.

### Fig. 5 — Certification landscape

Systematic severity × label budget → supported / unresolved / refuted.

### Fig. 6 — Label efficiency

Random vs active auditing.

### Fig. 7 — Physics inference

Bias, interval width and coverage.

### Fig. 8 — Exact vs finite-shot vs hardware

Quantum-specific validity.

### Fig. 9 — CMS real-data case study

Claims accepted and rejected under real deployment information.

---

# 33. Manuscript Structure

```text
1. Introduction

2. Related Work
   2.1 Quantum machine learning in collider physics
   2.2 Experimental systematics and simulation-to-data shift
   2.3 Trustworthy scientific machine learning
   2.4 Gap addressed by this work

3. Problem Formulation
   3.1 Collider event classification
   3.2 Nuisance-parameter environments
   3.3 Quantum kernels
   3.4 Claims and information sets
   3.5 Conditional validity

4. Method
   4.1 Geometry observatory
   4.2 Conditional auditor
   4.3 Partial-label certification
   4.4 Acquisition strategies
   4.5 Physics-level inference

5. Experimental Design
   5.1 FAIR Universe
   5.2 Models and baselines
   5.3 Systematic environments
   5.4 Statistical protocol

6. Results
   6.1 Nominal performance
   6.2 Behavior under systematics
   6.3 Kernel geometry
   6.4 Conditional certification
   6.5 Label efficiency
   6.6 Physics-level validity

7. Quantum Realism
   7.1 Finite-shot kernels
   7.2 Hardware validation

8. Simulation-to-Real Demonstration
   8.1 CMS Open Data setup
   8.2 Available information
   8.3 Supported and unsupported claims

9. Failure Cases and Limitations

10. Discussion

11. Conclusion
```

---

# 34. Claims Discipline

Never write:

- "quantum advantage" unless formally and empirically justified;
- "robust" without defining the threat/systematic model;
- "certificate" for an empirical heuristic;
- "real-data accuracy" without ground truth;
- "generalizable" from one HEP process;
- "hardware validated" from a decorative tiny run.

Prefer:

- conditional;
- under stated information;
- under specified nuisance family;
- statistically supported;
- empirically observed;
- fail-closed;
- unresolved under available evidence.

---

# 35. Success Criteria

A strong Q1-level outcome should satisfy most of:

- meaningful physical systematics;
- strong classical baselines;
- nontrivial quantum analysis;
- methodological contribution beyond benchmarking;
- rigorous statistical protocol;
- clear information-set formalization;
- negative-result robustness;
- physics-level consequences;
- finite-shot analysis;
- reproducible code/data workflow;
- real-data demonstration if feasible;
- no dependence on quantum advantage.

---

# 36. Best-Case Scientific Story

The strongest possible narrative is:

> Collider classifiers are usually validated under nominal simulation, while real deployment occurs under uncertain experimental conditions. Quantum event classifiers inherit this validity problem and add a second layer of uncertainty through quantum kernel estimation. We develop an information-set conditional auditing framework that determines which performance claims are justified under specified collider systematics, characterize how quantum-kernel geometry changes before downstream degradation, quantify the target-label evidence required to resolve claims, propagate failures to physics-level inference, and demonstrate fail-closed behavior when moving from Monte Carlo to real CMS collision data.

If the results support that narrative, it is the preferred paper.

---

# 37. Acceptable Alternative Scientific Stories

If H2 fails:

> Kernel geometry alone is insufficient to certify QML under collider systematics, but information-conditional validation quantifies exactly when labels become necessary.

If quantum is less robust:

> Quantum kernels can be unusually sensitive to physically plausible systematics despite competitive nominal performance, motivating explicit validity auditing.

If quantum and classical are similar:

> Nominal model family is less important than the information available for validating deployment claims; both require conditional scientific auditing.

If active acquisition fails:

> Simple random target labeling is already near-optimal under the tested conditions, providing an important negative result and a simpler practical protocol.

Do not manipulate the study to preserve the preferred story.

---

# 38. Codex Execution Rules

Codex should:

1. inspect and understand the entire repository before major changes;
2. implement modularly;
3. keep experiments config-driven;
4. write tests for data leakage and reproducibility;
5. never alter scientific definitions silently;
6. update `docs/decisions.md` for every material design decision;
7. update `docs/experiment_registry.md` before running a new experiment;
8. preserve raw outputs;
9. regenerate tables/figures automatically;
10. stop and flag scientific contradictions rather than inventing convenient assumptions.

Codex must NOT:

- simplify the project into a QSVC benchmark;
- replace real systematics with arbitrary noise;
- silently remove failed experiments;
- choose a favorable subset after inspecting results;
- label heuristic scores as guarantees;
- use target information beyond the declared information set;
- claim real-data ground truth where none exists;
- overfit the paper around a positive quantum result.

---

# 39. Initial Execution Order

## Phase 0 — Scientific audit

Create:

- `docs/novelty_matrix.md`
- `docs/dataset_audit.md`
- `docs/statistical_analysis_plan.md`
- `docs/decisions.md`

No major experiment before these exist.

## Phase 1 — Controlled benchmark

Implement FAIR Universe ingestion and reproduce benchmark sanity checks.

## Phase 2 — Nominal models

Build strong classical baselines and quantum-kernel baseline.

## Phase 3 — Physical systematics

Generate the systematic landscape.

## Phase 4 — Geometry

Implement geometry observatory and H2 tests.

## Phase 5 — Conditional auditing

Implement information sets and claim-resolution framework.

## Phase 6 — Partial labels

Estimate certification/sample-efficiency curves.

## Phase 7 — Physics inference

Propagate classifier behavior to physics quantities.

## Phase 8 — Quantum realism

Finite-shot experiments followed by limited QPU validation.

## Phase 9 — Real CMS

Implement the simulation-to-real fail-closed case study.

## Phase 10 — Adversarial review

Run a final internal reviewer pass explicitly seeking:

- leakage;
- unsupported claims;
- weak baselines;
- hidden selection bias;
- missing related work;
- statistical weaknesses;
- conclusions stronger than evidence.

---

# 40. Final Quality Bar

Do not submit merely because all experiments ran.

The paper is ready only when a skeptical reviewer can answer **yes** to:

1. Is the scientific question important without requiring quantum advantage?
2. Are the collider shifts physically meaningful?
3. Is the method genuinely more than OOD detection?
4. Are all claims conditional on the information actually available?
5. Are classical baselines strong?
6. Does the paper reveal something new about QML under experimental uncertainty?
7. Is there a connection to physics inference?
8. Are negative results and failure cases reported?
9. Is the experimental protocol reproducible?
10. Would the main contribution still matter if the quantum model is not the best classifier?

If the answer to any of 1–6 is no, improve the science before writing around the weakness.

---

# 41. First Task for Codex

Start by performing a repository-independent scientific setup.

Produce only these four documents first:

1. `docs/novelty_matrix.md`
2. `docs/dataset_audit.md`
3. `docs/statistical_analysis_plan.md`
4. `docs/experiment_registry.md`

For each unresolved scientific choice, provide:

- options;
- evidence;
- trade-offs;
- recommended decision.

Do **not** begin full implementation until the dataset and novelty gates are passed.

The objective is not to build quickly.

The objective is to construct the strongest scientifically defensible paper that can emerge from this research question.
