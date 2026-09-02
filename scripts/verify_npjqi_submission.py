"""Verify the repository's npj Quantum Information submission constraints.

This is an editorial-format gate. Scientific claims remain covered by
``verify_f8_2.py`` and the repository test suite.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "latex" / "main.tex"
SUPP = ROOT / "manuscript" / "supplementary" / "supplement.tex"
BIB = ROOT / "manuscript" / "bibliography" / "references.bib"
COVER = ROOT / "manuscript" / "npjqi" / "cover_letter.tex"
METADATA = ROOT / "docs" / "submission" / "npjqi_submission_metadata.md"
README = ROOT / "README.md"
DECISIONS = ROOT / "docs" / "decisions.md"
AUDIT = ROOT / "docs" / "audits" / "senior_author_revision_2026-08-13.md"
FINAL_AUDIT = ROOT / "docs" / "audits" / "final_micro_patch_2026-09-01.md"
PRECISION_AUDIT = (
    ROOT / "docs" / "audits" /
    "final_statistical_bibliographic_micro_patch_2026-09-01.md"
)
CHECKSUMS = ROOT / "docs" / "submission" / "npjqi_checksums.sha256"
CITATION = ROOT / "CITATION.cff"
RELEASE_MANIFEST = ROOT / "docs" / "submission" / "npjqi_release_manifest.md"
ZENODO_METADATA = (
    ROOT / "docs" / "submission" / "zenodo_npjqi_submission_v1_9_metadata.json"
)
MECHANISM_AUDIT = ROOT / "docs" / "audits" / "mechanistic_clarity_patch_2026-09-01.md"
STAGE_DECOMPOSITION = ROOT / "results" / "tables" / "E16_stage_decomposition.json"
MARGIN_STRATIFICATION = ROOT / "results" / "tables" / "E16_prop3_margin_stratification.json"
WMAX_SENSITIVITY = ROOT / "results" / "tables" / "E13_wmax_nominal_bound_sensitivity.json"
PSD_ANALYSIS = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
PROPOSITION4_ANALYSIS = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
PROPOSITION4_DEPLOYMENT_SUMMARY = (
    ROOT / "results" / "tables" / "E16_proposition4_deployment_summary.json"
)
RELEASE_CONSISTENCY_GATE = ROOT / "scripts" / "verify_release_consistency.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def words(text: str) -> list[str]:
    text = text.replace(r"\%", "%")
    text = re.sub(r"\\[A-Za-z*]+(?:\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$~]", " ", text)
    return re.findall(r"\b[\w.-]+\b", text, flags=re.UNICODE)


def balanced_arguments(text: str, command: str) -> list[str]:
    """Return braced arguments for a command, tolerating nested braces."""
    out: list[str] = []
    start = 0
    while True:
        idx = text.find(command, start)
        if idx < 0:
            return out
        pos = idx + len(command)
        if pos < len(text) and text[pos] == "[":
            depth = 1
            pos += 1
            while pos < len(text) and depth:
                depth += (text[pos] == "[") - (text[pos] == "]")
                pos += 1
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text) or text[pos] != "{":
            start = pos
            continue
        depth = 1
        begin = pos + 1
        pos += 1
        while pos < len(text) and depth:
            if text[pos] == "{" and (pos == 0 or text[pos - 1] != "\\"):
                depth += 1
            elif text[pos] == "}" and (pos == 0 or text[pos - 1] != "\\"):
                depth -= 1
            pos += 1
        if depth:
            raise ValueError(f"Unbalanced argument for {command} at offset {idx}")
        out.append(text[begin : pos - 1])
        start = pos


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    main_tex = MAIN.read_text(encoding="utf-8")
    supp_tex = SUPP.read_text(encoding="utf-8")
    bib = BIB.read_text(encoding="utf-8")
    cover = COVER.read_text(encoding="utf-8")
    metadata = METADATA.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    decisions = DECISIONS.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")
    final_audit = FINAL_AUDIT.read_text(encoding="utf-8")
    precision_audit = PRECISION_AUDIT.read_text(encoding="utf-8")
    checksum_text = CHECKSUMS.read_text(encoding="utf-8")
    citation = CITATION.read_text(encoding="utf-8")
    release_manifest = RELEASE_MANIFEST.read_text(encoding="utf-8")
    zenodo_metadata = ZENODO_METADATA.read_text(encoding="utf-8")
    proposition4 = json.loads(PROPOSITION4_ANALYSIS.read_text(encoding="utf-8"))
    proposition4_deployment = json.loads(
        PROPOSITION4_DEPLOYMENT_SUMMARY.read_text(encoding="utf-8")
    )
    mechanism_audit = MECHANISM_AUDIT.read_text(encoding="utf-8")
    stage = json.loads(STAGE_DECOMPOSITION.read_text(encoding="utf-8"))
    stratification = json.loads(MARGIN_STRATIFICATION.read_text(encoding="utf-8"))
    wmax = json.loads(WMAX_SENSITIVITY.read_text(encoding="utf-8"))
    flat_main = re.sub(r"\s+", " ", main_tex)

    titles = balanced_arguments(main_tex, r"\title")
    # The optional short title is skipped by balanced_arguments.
    title = titles[0]
    title_words = words(title)
    check("title length", len(title_words) <= 15, f"{len(title_words)} words")
    check(
        "title punctuation",
        not re.search(r"[,:;!?]", title),
        title,
    )

    abstracts = balanced_arguments(main_tex, r"\abstract")
    check("single abstract", len(abstracts) == 1, f"found {len(abstracts)}")
    abstract = abstracts[0]
    abstract_words = words(abstract)
    check("abstract length", 130 <= len(abstract_words) <= 150, f"{len(abstract_words)} words")
    check(
        "abstract avoids undefined internal labels",
        not re.search(r"\b(I2|I3|CMS|PSD|far-margin)\b", abstract),
    )
    check("abstract has no citations", r"\cite" not in abstract)
    check("abstract has no displayed equations", r"\[" not in abstract and "$$" not in abstract)

    intro = main_tex.index(r"\section{Introduction}")
    results = main_tex.index(r"\section{Results}")
    discussion = main_tex.index(r"\section{Discussion}")
    methods = main_tex.index(r"\section{Methods}")
    backmatter = main_tex.index(r"\backmatter")
    check("required section order", intro < results < discussion < methods < backmatter)
    check("introduction has no subheadings", r"\subsection" not in main_tex[intro:results])
    check("discussion has no subheadings", r"\subsection" not in main_tex[discussion:methods])
    check("no separate conclusion section", r"\section{Conclusion}" not in main_tex)
    check("no separate limitations section", "Failure Cases, Corrections, and Limitations" not in main_tex)
    check("methods uses subheadings", r"\subsection" in main_tex[methods:backmatter])
    check("AI use disclosed in Methods", "Use of generative AI" in main_tex[methods:backmatter])

    for heading in (
        "Data availability",
        "Code availability",
        "Acknowledgements",
        "Author contributions",
        "Competing interests",
    ):
        check(f"required heading: {heading}", rf"\section*{{{heading}}}" in main_tex)

    cited_keys = {
        key.strip()
        for group in re.findall(r"\\cite[pt]?(?:alp)?\{([^}]*)\}", main_tex)
        for key in group.split(",")
    }
    bib_keys = set(re.findall(r"^@\w+\{([^,]+),", bib, flags=re.MULTILINE))
    check("reference guide", len(cited_keys) <= 60, f"{len(cited_keys)} cited entries")
    check("all cited keys defined", cited_keys <= bib_keys, str(sorted(cited_keys - bib_keys)))

    captions = balanced_arguments(main_tex, r"\caption")
    caption_lengths = [len(words(caption)) for caption in captions]
    check(
        "figure and table legends",
        bool(caption_lengths) and max(caption_lengths) <= 350,
        f"maximum {max(caption_lengths, default=0)} words",
    )

    expected_title = (
        "Conditional validity of quantum event classifiers under collider "
        "systematics and quantum estimation uncertainty"
    )
    check("canonical title", " ".join(title.split()) == expected_title)
    check("supplement title synchronized", expected_title in " ".join(supp_tex.split()))
    check("Springer Nature template", "sn-nature" in main_tex and "sn-jnl" in main_tex)
    check("single Supplementary Information source", "Supplementary Information for" in supp_tex)

    check("Collection named in cover letter", "Quantum machine learning:" in cover)
    check("journal named in cover letter", "npj Quantum Information" in cover)
    check("related manuscript disclosed", "Sharp Target-Domain Certificates" in cover)
    check("related manuscript distinction recorded", "share no datasets" in cover.lower())
    check("related manuscript exact status", "has not been submitted to any" in cover and "journal" in cover)
    check("submission metadata present", "## Scientific guardrails" in metadata)

    check(
        "per-claim multiplicity guardrail",
        re.search(r"not simultaneous(?:ly)?\s+across a grid", main_tex) is not None,
    )
    check(
        "Proposition 3 instantiated",
        proposition4["interpretation"] == "INFORMATIVELY INSTANTIATED"
        and proposition4["aggregate_summaries"]["overall"]["condition_cell_counts"]["HOLDS"] == 4943
        and "informatively instantiated" in main_tex.lower(),
    )
    check(
        "Proposition 3 deployment summary",
        proposition4_deployment["independent_descriptive_unit"]
        == "noisy-kernel deployment"
        and proposition4_deployment["accounting"]["noisy_kernel_deployments"] == 30
        and proposition4_deployment["accounting"][
            "condition_cells_per_deployment_regime_semantics_slice"
        ]
        == 60
        and "E16\\_proposition4\\_deployment\\_summary.json" in supp_tex,
    )
    check(
        "Proposition 3 logical structure",
        "sign-stability condition, coverage" in main_tex
        and "resolution of both audits" in main_tex
        and "2\\alpha" in main_tex
        and "each audit at $\\alpha/2$" in main_tex,
    )
    check("no quantum advantage guardrail", "We claim no\nquantum advantage" in main_tex)
    check("micro-scale hardware guardrail", "micro-scale full-pipeline IBM QPU run" in main_tex)
    check("public data DOI", "https://doi.org/10.5281/zenodo.15131565" in main_tex)
    check("public code DOI", "https://doi.org/10.5281/zenodo.22254835" in main_tex)
    check(
        "patch release synchronized",
        all("0.3.9" in text and "npjqi-submission-v1.9" in text
            for text in (readme, metadata, release_manifest, zenodo_metadata)),
    )
    check(
        "patch DOI synchronized",
        all("10.5281/zenodo.22254835" in text
            for text in (main_tex, readme, metadata, citation, release_manifest,
                         zenodo_metadata)),
    )
    check(
        "historical 0.3.8 release retained",
        "10.5281/zenodo.22250951" in readme
        and "10.5281/zenodo.22250951" in release_manifest,
    )
    check(
        "historical 0.3.7 release retained",
        "10.5281/zenodo.22236115" in readme
        and "10.5281/zenodo.22236115" in release_manifest,
    )
    check(
        "historical 0.3.6 release retained",
        "10.5281/zenodo.22235287" in readme
        and "10.5281/zenodo.22235287" in release_manifest,
    )
    check(
        "historical 0.3.5 release retained",
        "10.5281/zenodo.22231469" in readme
        and "10.5281/zenodo.22231469" in release_manifest,
    )
    check(
        "historical 0.3.3 release retained",
        "10.5281/zenodo.22227158" in readme
        and "10.5281/zenodo.22227158" in release_manifest,
    )
    check(
        "historical 0.3.2 release retained",
        "10.5281/zenodo.22214449" in readme
        and "10.5281/zenodo.22214449" in release_manifest,
    )
    check(
        "historical 0.3.0 release retained",
        "10.5281/zenodo.22206235" in readme
        and "10.5281/zenodo.22206235" in release_manifest,
    )

    # Public-repository closeout: the README, paper, supplement, cover letter,
    # decision log, and final audit must describe the same frozen submission.
    check("README title synchronized", expected_title in " ".join(readme.split()))
    check("cover title synchronized", expected_title in " ".join(cover.split()))
    check("README artifact set", all(token in readme for token in ("npjqi_manuscript.pdf", "npjqi_supplementary_information.pdf", "npjqi_cover_letter.pdf")))
    check("README submission state", "has not yet been submitted" in readme)
    check("PSD sensitivity archived", "PSD-SENSITIVE-BUT-SCOPED" in readme and PSD_ANALYSIS.is_file())
    check(
        "Proposition 3 artifact archived",
        PROPOSITION4_ANALYSIS.is_file()
        and "E16_proposition4_instantiation.json" in readme,
    )
    check(
        "Proposition 3 deployment artifact archived",
        PROPOSITION4_DEPLOYMENT_SUMMARY.is_file()
        and "E16_proposition4_deployment_summary.json" in readme,
    )
    check(
        "abstract omits correlated-cell percentage",
        "68.7" not in abstract
        and "9.2" not in abstract
        and "sufficient rather than necessary" in flat_main,
    )
    check(
        "frozen batch deployment scope",
        "frozen\nfinite-population batch deployment" in main_tex
        and "continually\nre-estimated online kernel service" in main_tex
        and "unspecified future\nsuperpopulation" in main_tex,
    )
    check(
        "independent-template limitation scoped",
        "evaluated archived fixed-template construction\n  can lose coverage" in main_tex
        and "hierarchical/template-statistical constructions" in main_tex,
    )
    check(
        "row-disjoint wording scoped",
        "provably disjoint" not in main_tex.lower()
        and "four independent worlds" not in main_tex.lower()
        and "provably disjoint" not in readme.lower(),
    )
    check(
        "adjacent literature added",
        all(
            token in bib and token in main_tex
            for token in ("agliardi2026covariant", "arxiv2509.00672")
        )
        and "10.1038/s41534-025-01154-2" in bib
        and "10.48550/arXiv.2509.00672" in bib,
    )
    check(
        "finite-shot classifier literature added",
        all(
            token in bib and token in main_tex
            for token in ("shastry2023shotfrugal", "gentinetta2024complexity")
        )
        and "10.48550/arXiv.2210.06971" in bib
        and "10.22331/q-2024-01-11-1225" in bib,
    )
    check(
        "finite-shot novelty boundary",
        "Prior work therefore already connects finite-shot kernel" in main_tex
        and "Our distinction is the integration of a" in main_tex
        and "refrozen threshold" in main_tex
        and "downstream scientific-inference context" in main_tex,
    )
    check(
        "historical alpha-plus-three-sigma scope",
        r"$\alpha+3\sigma$ boundary" not in supp_tex
        and "Historical heuristic gate" in supp_tex
        and "not interpreted as an IID sampling standard" in supp_tex
        and re.search(r"historical\s+implementation-falsifier threshold", supp_tex)
        and "per-claim confidence-sequence result" in supp_tex,
    )
    check(
        "Proposition 3 retrospective diagnostic",
        "its instantiation on the frozen deployments is" in main_tex
        and "diagnostic of observed" in main_tex
        and "not as an operational pre-audit certificate" in main_tex
        and "retrospective diagnostic" in supp_tex
        and "does not predict a flip" in supp_tex,
    )
    check(
        "Tier-A Gram resource arithmetic",
        all(
            token in main_tex
            for token in (
                "n(n-1)/2=1{,}999{,}000",
                "255{,}872{,}000\\simeq2.56\\times10^8",
                "8{,}187{,}904{,}000\\simeq8.19\\times10^9",
                "not a linear wall-clock estimate",
                "not a claim of practical quantum advantage",
            )
        )
        and 2000 * 1999 // 2 == 1_999_000
        and 1_999_000 * 128 == 255_872_000
        and 1_999_000 * 4096 == 8_187_904_000,
    )
    check(
        "PSD repair benchmark excluded",
        "neither optimizing nor benchmarking PSD-repair" in main_tex
        and "rather than an optimized mitigation pipeline" in flat_main,
    )
    check(
        "I2 I3 CMS guarantee separation",
        "anytime-valid guarantee applies to each fixed label-stream claim" in flat_main
        and "auxiliary-information procedures are separately coverage-gated" in flat_main
        and "does not inherit the\nI2 confidence-sequence theorem" in main_tex,
    )
    check(
        "far-margin support-only scope",
        "no\nfalse far-margin deployment-relative claim" in main_tex
        and "no false far-margin deployment-relative claim" in supp_tex,
    )
    check(
        "raw and PSD formal semantics",
        "RAW-INDEFINITE fitted object is not interpreted" in main_tex
        and "not a normalized fidelity Gram" in main_tex
        and "no global Mercer" in main_tex,
    )
    check(
        "PDF metadata declared",
        "pdftitle=" in supp_tex and "pdfauthor=" in supp_tex and "pdfsubject=" in supp_tex
        and "pdftitle=" in cover and "pdfauthor=" in cover and "pdfsubject=" in cover,
    )
    check("no internal proof paths in main", "docs/" not in main_tex)
    check(
        "unsupported equivalence wording absent",
        "statistically indistinguishable" not in main_tex.lower()
        and "no additional seeds are required" not in main_tex.lower(),
    )
    check("decision log contains npj revision", "D-044" in decisions and "D-046" in decisions and "npj Quantum Information" in decisions)
    check(
        "mechanistic-clarity audit",
        "0.3.6" in mechanism_audit
        and "10.5281/zenodo.22235287" in mechanism_audit
        and "F1" in mechanism_audit and "F6" in mechanism_audit
        and "no experiment, gram realization, seed" in mechanism_audit.lower(),
    )
    check(
        "stage decomposition reproduces archived endpoints",
        stage["reproduction"]["all_raw_stage_D_match_primary"]
        and stage["reproduction"]["all_raw_stage_D_match_psd_archive"]
        and stage["reproduction"]["all_psd_stage_D_match_psd_archive"]
        and stage["reproduction"]["platt_slopes_positive"]
        and stage["provenance"]["no_new_randomness"] is True
        and stage["provenance"]["no_new_qpu_jobs"] is True,
    )
    check(
        "stage decomposition classification synchronized",
        stage["classification"]["overall"] == "MIXED"
        and stage["classification"]["by_regime"]["raw"]["label"] == "MIXED"
        and stage["classification"]["by_regime"]["psd_repaired"]["label"] == "MODEL/RANKING-DOMINATED"
        and "\\textsc{mixed}" in main_tex and "\\textsc{mixed}" in supp_tex
        and "amplified downstream" in flat_main
        and "through recalibration and operating-threshold selection" in flat_main
        and "need not itself be quantum-specific" in flat_main
        and "do not claim a universal downstream mechanism across kernel treatments" in flat_main
        and "partly compensates rather than generates the far ideal-anchored flips in the RAW replay" in flat_main
        and "decomposes differently" in abstract
        and "threshold-dominated" not in main_tex.lower(),
    )
    check(
        "non-monotonicity demoted",
        "non-monotonic" not in main_tex and "non-monotonic" not in supp_tex
        and "deployment heterogeneity" in flat_main
        and "outlier sensitivity" in flat_main,
    )
    check(
        "common-mode cancellation stated",
        "common-mode cancellation" in flat_main and "common-mode" in supp_tex,
    )
    check(
        "margin stratification artifact",
        stratification["totals"] == {
            "condition_cells": 7200, "audit_streams": 72000,
            "holds_cells": 4943, "fails_cells": 2257,
        }
        and "Supplementary Table S10" in flat_main
        and "tab:prop3-stratification" in supp_tex,
    )
    check(
        "weight-bound sensitivity is post hoc and exact",
        wmax["E13_part_b"]["historical_replay_exact"] is True
        and wmax["E19_weighted_arm"]["historical_replay_exact"] is True
        and "POST-HOC" in wmax["status"]
        and wmax["mathematical_necessity_audit"]["kappa_2_05_required_for_executed_nominal_claims"] is False
        and "post-hoc sensitivity" in flat_main
        and "deliberate conservatism rather than a validity requirement" in flat_main
        and "Supplementary Table S16" in flat_main,
    )
    check(
        "without-replacement future work only",
        "waudbysmith2020wor" in main_tex and "waudbysmith2020wor" in bib
        and "theorem and protocol here are unchanged" in flat_main,
    )
    check(
        "final literature patch citations",
        all(key in main_tex and f"{{{key}," in bib
            for key in ("arxiv2401.10542", "arxiv2605.22275",
                        "arxiv1810.08240"))
        and "10.52202/085713-2767" in bib
        and "Advances in Neural Information Processing Systems 33" in bib
        and "not a priority claim" in flat_main,
    )
    check(
        "measurement-induced semantics scoped",
        "names the source of the perturbation controlled here" in flat_main
        and "classical pipelines can exhibit analogous downstream sensitivity" in flat_main,
    )
    check(
        "C2 adverse result leads",
        "1.8--3.4" not in main_tex[intro:results]
        and "this conditional diagnostic does not establish validity" in flat_main,
    )
    check(
        "editorial corrections applied",
        "\\ref{sec:related}" not in main_tex and "\\label{sec:related}" not in main_tex
        and "\\label{sec:results}" not in main_tex
        and "\\label{sec:limitations}" not in main_tex
        and "\\label{sec:conclusion}" not in main_tex
        and "INFERNO \\citep{arxiv1806.04743}" in main_tex
        and "\\citealp{arxiv1806.04743}" not in main_tex
        and "historical identifier `proposition4'" in main_tex
        and "historical identifier `proposition4'" in supp_tex
        and "Supplementary Table~S18" in main_tex
        and "tab:e01models" in supp_tex
        and "A verdict flip is any change among SUPPORTED, REFUTED and UNRESOLVED" in flat_main
        and "Elharrauss, Salah Eddine" in bib
        and "frozen on 10 August 2026" not in main_tex,
    )
    check(
        "historical artifact names unchanged",
        PROPOSITION4_ANALYSIS.is_file() and PROPOSITION4_DEPLOYMENT_SUMMARY.is_file()
        and "E16_proposition4_instantiation.json" in readme
        and "E16_proposition4_deployment_summary.json" in readme,
    )
    check("audit contains npj adaptation", "npj Quantum Information editorial adaptation" in audit)
    check(
        "final micro-patch audit",
        "0.3.3" in final_audit
        and "10.5281/zenodo.22227158" in final_audit
        and "no experiment, seed" in final_audit.lower(),
    )
    check(
        "final precision micro-patch audit",
        "0.3.4" in precision_audit
        and "historical heuristic gate" in precision_audit.lower()
        and "retrospective diagnostic" in precision_audit.lower()
        and "8,187,904,000" in precision_audit
        and "no experiment, seed" in precision_audit.lower(),
    )

    framing_docs = {
        "README": readme,
        "manuscript": main_tex,
        "supplement": supp_tex,
        "decisions": decisions,
        "audit": audit,
    }
    check(
        "Wald yardstick synchronized",
        all("Wald" in text and "yardstick" in text for text in framing_docs.values()),
    )
    check(
        "C2 joint limitation synchronized",
        all("representability" in text and "template" in text for text in framing_docs.values()),
    )
    check(
        "Proposition 3 evidence synchronized",
        all("informatively instantiated" in text.lower()
            for text in (readme, main_tex, supp_tex, metadata)),
    )
    release_consistency = subprocess.run(
        [sys.executable, str(RELEASE_CONSISTENCY_GATE), "--allow-unreleased"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    check(
        "release consistency gate",
        release_consistency.returncode == 0,
        release_consistency.stdout.strip() if release_consistency.returncode else "",
    )
    check(
        "E16 deployment unit synchronized",
        all("five" in text.lower() and "deployment" in text.lower() and "correlated" in text.lower()
            for text in (readme, main_tex, supp_tex, decisions, audit)),
    )
    check(
        "audit-label draw terminology synchronized",
        all("audit-label draw" in text.lower() for text in (readme, main_tex, supp_tex, decisions, audit)),
    )
    hardware_docs = {
        "README": readme,
        "manuscript": main_tex,
        "cover": cover,
        "decisions": decisions,
        "audit": audit,
    }
    check(
        "micro-scale fail-closed framing synchronized",
        all("micro-scale" in text and "fail-closed" in text for text in hardware_docs.values()),
    )

    protected_paths = (
        "configs", "data", "experiments", "results", "src",
        "scripts/analyze_e16_psd_sensitivity.py",
        "scripts/summarize_e16_proposition4_deployments.py",
    )
    protected_diff = subprocess.run(
        ["git", "diff", "--name-only", "npjqi-submission-v1.5", "--", *protected_paths],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    derived_additions = {
        "results/tables/E16_stage_decomposition.json",
        "results/tables/E16_prop3_margin_stratification.json",
        "results/tables/E13_wmax_nominal_bound_sensitivity.json",
    } | {
        # 0.3.9 figure-legibility patch: re-rendered figure files only.
        f"results/figures/{stem}.{ext}"
        for stem in (
            "fig1_framework",
            "fig2_tes_replicated",
            "fig4b_out_of_grid_sensor",
            "fig5_certification_landscape",
            "fig7_h5_decoupling",
            "fig7b_inference_levels",
            "fig8_shots_hardware",
        )
        for ext in ("pdf", "png")
    }
    unexpected = [
        line for line in protected_diff.stdout.split()
        if line.replace("\\", "/") not in derived_additions
    ]
    check(
        "protected scientific artifacts unchanged from 0.3.5",
        protected_diff.returncode == 0 and not unexpected,
        " ".join(unexpected),
    )

    frozen_outputs = (
        ROOT / "output" / "pdf" / "npjqi_manuscript.pdf",
        ROOT / "output" / "pdf" / "npjqi_supplementary_information.pdf",
        ROOT / "output" / "pdf" / "npjqi_cover_letter.pdf",
        ROOT / "dist" / "npjqi-submission.zip",
        PSD_ANALYSIS,
        PROPOSITION4_ANALYSIS,
        PROPOSITION4_DEPLOYMENT_SUMMARY,
        STAGE_DECOMPOSITION,
        MARGIN_STRATIFICATION,
        WMAX_SENSITIVITY,
    )
    for path in frozen_outputs:
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        check(f"frozen hash: {rel}", f"{digest}  {rel}" in checksum_text, digest)

    failed = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        suffix = f" ({detail})" if detail else ""
        print(f"[{status}] {name}{suffix}")
        failed += not ok
    print(f"\n{len(checks) - failed}/{len(checks)} npj submission checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
