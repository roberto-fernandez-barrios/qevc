"""Verify the repository's npj Quantum Information submission constraints.

This is an editorial-format gate. Scientific claims remain covered by
``verify_f8_2.py`` and the repository test suite.
"""

from __future__ import annotations

import hashlib
import json
import re
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
FINAL_AUDIT = ROOT / "docs" / "audits" / "final_logical_closure_2026-08-31.md"
CHECKSUMS = ROOT / "docs" / "submission" / "npjqi_checksums.sha256"
CITATION = ROOT / "CITATION.cff"
RELEASE_MANIFEST = ROOT / "docs" / "submission" / "npjqi_release_manifest.md"
PSD_ANALYSIS = ROOT / "results" / "tables" / "E16_psd_sensitivity.json"
PROPOSITION4_ANALYSIS = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"


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
    checksum_text = CHECKSUMS.read_text(encoding="utf-8")
    citation = CITATION.read_text(encoding="utf-8")
    release_manifest = RELEASE_MANIFEST.read_text(encoding="utf-8")
    proposition4 = json.loads(PROPOSITION4_ANALYSIS.read_text(encoding="utf-8"))

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
    check("abstract length", len(abstract_words) <= 150, f"{len(abstract_words)} words")
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

    reference_count = len(re.findall(r"^@", bib, flags=re.MULTILINE))
    check("reference guide", reference_count <= 60, f"{reference_count} entries")

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
        "Proposition 4 instantiated",
        proposition4["interpretation"] == "INFORMATIVELY INSTANTIATED"
        and proposition4["aggregate_summaries"]["overall"]["condition_cell_counts"]["HOLDS"] == 4943
        and "informatively instantiated" in main_tex.lower(),
    )
    check(
        "Proposition 4 logical structure",
        "sign-stability condition, coverage" in main_tex
        and "resolution of both audits" in main_tex
        and "2\\alpha" in main_tex
        and "each audit at $\\alpha/2$" in main_tex,
    )
    check("no quantum advantage guardrail", "We claim no\nquantum advantage" in main_tex)
    check("micro-scale hardware guardrail", "micro-scale full-pipeline IBM QPU run" in main_tex)
    check("public data DOI", "https://doi.org/10.5281/zenodo.15131565" in main_tex)
    check("public code DOI", "https://doi.org/10.5281/zenodo.22214449" in main_tex)
    check(
        "patch release synchronized",
        all("0.3.2" in text and "npjqi-submission-v1.2" in text
            for text in (readme, metadata, release_manifest)),
    )
    check(
        "patch DOI synchronized",
        all("10.5281/zenodo.22214449" in text
            for text in (main_tex, readme, metadata, citation, release_manifest)),
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
        "Proposition 4 artifact archived",
        PROPOSITION4_ANALYSIS.is_file()
        and "E16_proposition4_instantiation.json" in readme,
    )
    check(
        "I2 I3 CMS guarantee separation",
        "fixed I2 label-stream claim" in abstract
        and "I3 and CMS procedures are separately" in abstract
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
    check("decision log contains npj revision", "D-038" in decisions and "npj Quantum Information" in decisions)
    check("audit contains npj adaptation", "npj Quantum Information editorial adaptation" in audit)
    check(
        "final logical-closure audit",
        "INFORMATIVELY INSTANTIATED" in final_audit
        and "4,943" in final_audit
        and "7,200" in final_audit
        and "no experiment, seed" in final_audit,
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
        "Proposition 4 evidence synchronized",
        all("informatively instantiated" in text.lower()
            for text in (readme, main_tex, supp_tex, metadata)),
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

    frozen_outputs = (
        ROOT / "output" / "pdf" / "npjqi_manuscript.pdf",
        ROOT / "output" / "pdf" / "npjqi_supplementary_information.pdf",
        ROOT / "output" / "pdf" / "npjqi_cover_letter.pdf",
        ROOT / "dist" / "npjqi-submission.zip",
        PSD_ANALYSIS,
        PROPOSITION4_ANALYSIS,
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
