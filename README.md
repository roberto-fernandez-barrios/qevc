# Conditional Validity of Quantum Event Classifiers under Collider Systematics

Research codebase for the paper *"When Can Quantum Event Classifiers Be Trusted? Conditional Validity under Collider Systematics"*.

**Scientific question.** Under what experimentally available information can the validity of a
quantum event classifier be justified when collider systematics shift the deployment
distribution away from the nominal simulation on which it was validated?

The project does **not** optimize for a positive quantum result. It builds an
information-set conditional auditing framework that decides, fail-closed, whether a
performance claim about a (quantum or classical) event classifier is
**SUPPORTED / REFUTED / UNRESOLVED** under a declared information set, and propagates
classifier behavior to physics-level inference (signal strength, interval coverage).

## Governing documents

| Document | Purpose |
|---|---|
| `docs/research_spec.md` | Full execution specification (frozen blueprint) |
| `docs/novelty_matrix.md` | Literature positioning; Gate 0 |
| `docs/dataset_audit.md` | Dataset selection audit; Gate 1 |
| `docs/statistical_analysis_plan.md` | Predeclared statistical protocol |
| `docs/experiment_registry.md` | Registry of all experiments (E00–E11) |
| `docs/decisions.md` | Log of every material design decision |

## Experimental levels

- **Level I — Controlled collider world:** FAIR Universe HiggsML Uncertainty benchmark
  (H→ττ with parameterized systematics: TES, JES, soft MET, background normalizations).
- **Level II — Real collider world:** CMS Open Data simulation-to-real, fail-closed
  demonstration (no event-level truth labels are ever fabricated).

## Repository layout

See `docs/research_spec.md` §26. Code lives in `src/qevc/` (Quantum Event Validity
Certification); experiments are config-driven from `configs/` and registered in
`docs/experiment_registry.md` before execution. Results are written to `results/`
with immutable manifests.

## Reproducibility

Every run records git commit, config hash, dataset version/hash, seeds, package
versions, and backend metadata. No manually edited result files. See
`docs/statistical_analysis_plan.md` for the predeclared protocol.
