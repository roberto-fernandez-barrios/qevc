"""Reproducible checks for the final LaTeX/supplement audit (F8.2).

This is not a result generator. It verifies the high-risk quantitative
summaries directly against the immutable JSON tables, checks the author and
falsifier metadata, and performs a bidirectional prose n-gram comparison of
the Markdown source and the LaTeX conversion. It writes nothing.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "latex" / "main.tex"
DRAFT = ROOT / "manuscript" / "main" / "draft.md"
SUPPLEMENT = ROOT / "manuscript" / "supplementary" / "supplement.tex"
FORMAL = ROOT / "docs" / "formal_results.md"
WEIGHTED_SPEC = ROOT / "docs" / "weighted_certification_spec.md"
REGISTRY = ROOT / "docs" / "experiment_registry.md"
TABLES = ROOT / "results" / "tables"


class Audit:
    def __init__(self) -> None:
        self.checks = 0
        self.failures: list[str] = []

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        self.checks += 1
        if not condition:
            suffix = f": {detail}" if detail else ""
            self.failures.append(f"{name}{suffix}")


def load(name: str) -> dict:
    with (TABLES / name).open(encoding="utf-8") as stream:
        return json.load(stream)


def has_all(text: str, values: list[str]) -> bool:
    return all(value in text for value in values)


def prose_words(text: str, kind: str) -> list[str]:
    if kind == "draft":
        # The Markdown file is now an explicitly historical prose snapshot;
        # compare the scientific body, not the journal-specific front matter.
        text = text[
            text.index("## 3. Problem Formulation") : text.index(
                "### Reproducibility statement"
            )
        ]
        text = re.sub(r"`[^`]+`", " ", text)
        text = re.sub(r"\([^\n()]*arXiv:[^\n()]*\)", " ", text)
        text = re.sub(r"^#+ .*$", " ", text, flags=re.MULTILINE)
        text = re.sub(r"[*_#`|]", " ", text)
    else:
        # The npj/Springer Nature version uses \abstract{...} and moves Methods
        # after Discussion. Four-gram sets are insensitive to that reordering.
        text = text[
            text.index(r"\section{Results}") : text.index(
                r"\subsection{Reproducibility and computational environment}"
            )
        ]
        text = re.sub(r"(?m)%.*$", " ", text)
        text = re.sub(
            r"\\(?:citep|citet|citealp)(?:\[[^]]*\])?\{[^{}]*\}", " ", text
        )
        text = re.sub(
            r"\\(?:label|ref|includegraphics|setcounter)(?:\[[^]]*\])?\{[^{}]*\}",
            " ",
            text,
        )
        text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", " ", text)
        text = re.sub(
            r"\\(?:section\*?|subsection|subsubsection|paragraph)(?:\[[^]]*\])?\{[^{}]*\}",
            " ",
            text,
        )
        text = re.sub(r"\\caption(?:\[[^]]*\])?\{([^{}]*)\}", r" \1 ", text)
        text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
        text = text.replace(r"\&", " and ").replace(r"\_", "_")
        text = re.sub(r"[{}$\\&~^]", " ", text)

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower().replace("---", " ").replace("--", " ")
    return re.findall(r"[a-z]{4,}", text)


def ngram_coverage(left: list[str], right: list[str], n: int = 4) -> float:
    left_grams = {tuple(left[i : i + n]) for i in range(len(left) - n + 1)}
    right_grams = {tuple(right[i : i + n]) for i in range(len(right) - n + 1)}
    return len(left_grams & right_grams) / len(left_grams)


def round_half_up(value: float, digits: int) -> float:
    quantum = Decimal(1).scaleb(-digits)
    return float(Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP))


def main() -> int:
    audit = Audit()
    main_tex = MAIN.read_text(encoding="utf-8")
    draft_md = DRAFT.read_text(encoding="utf-8")
    supplement = SUPPLEMENT.read_text(encoding="utf-8")
    formal = FORMAL.read_text(encoding="utf-8")
    weighted_spec = WEIGHTED_SPEC.read_text(encoding="utf-8")
    registry = REGISTRY.read_text(encoding="utf-8")

    # Front matter and the two F8.2 corrections must be synchronized.
    for author, orcid in {
        "Roberto": "0009-0003-5312-2634",
        "Iker": "0000-0002-3068-6248",
        "Asier": "0009-0002-8888-8560",
        "Pablo": "0000-0003-3594-9534",
    }.items():
        audit.check(f"{author} ORCID in main", orcid in main_tex)
        audit.check(f"{author} ORCID in supplement", orcid in supplement)
    audit.check(
        "institutional corresponding email in main",
        "roberto.fernandez.b@deusto.es" in main_tex,
    )
    audit.check(
        "affiliation in main and supplement",
        all(
            "Faculty of Engineering" in text and "University of Deusto" in text
            for text in (main_tex, supplement)
        ),
    )
    audit.check("no front-matter TODO remains", "TODO: affiliation" not in main_tex)
    for text, label in [(main_tex, "LaTeX"), (draft_md, "Markdown")]:
        audit.check(f"E08v3 corrected bias endpoint in {label}", "+7.5" in text)
        audit.check(f"stale E08v3 endpoint absent in {label}", "to $+6.1$" not in text and "to +6.1" not in text)
        if label == "LaTeX":
            audit.check(
                "nine-arm convention in LaTeX",
                "registered falsifiers fired nine" in text
                and all(
                    arm in text
                    for arm in (
                        "E02R",
                        "E12 arm (e)",
                        "E14 v1",
                        "E15 gate",
                        "E17 arm (b)",
                        "E08v2 arms (a) and (b)",
                        "E08v3 arm (a)",
                        "E13v2 arm (b)",
                    )
                ),
            )
        else:
            audit.check(
                "nine-arm convention in Markdown",
                "multi-seed TES replication arm" in text
                and "one registered arm that blocked two implementations" in text,
            )

    # Final mathematical/editorial audit: formal scope and stale-claim guards.
    audit.check(
        "Proposition 2 size/power correction synchronized",
        "power equal to its actual size and hence at" in main_tex
        and "power equal\nto its actual size and hence at most $\\alpha$" in supplement
        and re.search(r"power equal to its actual\s+size", formal) is not None
        and "power equal to its actual size" in weighted_spec,
    )
    audit.check(
        "Proposition 2 fail-closed policy is not a theorem",
        "absence of distinguishing evidence is reported" in main_tex
        and "absence of distinguishing evidence is reported" in supplement
        and "absence of distinguishing evidence is\nreported" in formal
        and "absence of distinguishing evidence is reported" in weighted_spec,
    )
    audit.check(
        "Theorem 1 fixed-claim and multiplicity scope",
        "fixed $\\tau\\in[0,1]$ chosen before observing the audit label stream" in main_tex
        and "The guarantee is \\emph{per fixed claim}" in main_tex
        and "It is not FWER" in supplement,
    )
    audit.check(
        "conditional finite-population weight bound",
        "Condition on a frozen finite audit population" in main_tex
        and "2.0\\times1.01=2.02" in main_tex
        and "conditional on that population and scalar bound" in weighted_spec,
    )
    audit.check(
        "E13v2 oracle qualification",
        "E13v2 is not an operational" in main_tex
        and "oracle/benchmark diagnostic" in supplement
        and "oracle/benchmark diagnostic" in weighted_spec
        and "oracle/benchmark diagnostic" in registry,
    )
    audit.check(
        "C2 joint validity condition",
        "jointly limited by nuisance representability and" in main_tex
        and "auxiliary/template quality" in main_tex,
    )
    audit.check(
        "E17 cross-world instability in conclusion",
        "small within-world replicated but" in main_tex
        and "cross-world unstable responses" in main_tex,
    )
    audit.check(
        "measurement-induced quantum framing",
        "additional measurement-induced deployment uncertainty" in main_tex
        and "classical training randomness is" not in main_tex,
    )

    audit.check(
        "weights are informative, not exact process identifiers",
        "identifies the generating process" not in main_tex
        and "process- and label-informative" in main_tex,
    )
    audit.check(
        "Wald comparison is only a yardstick",
        "no universal lower bound, expected-stopping-time comparison" in main_tex,
    )

    # E08v3: recompute all ranges quoted in the main text and supplement.
    e08 = load("E08v3_multidraw.json")
    count = e08["counting_marginal"]
    shared = [row["shared_truth_half"] for row in count.values()]
    naive = [row["independent_naive"] for row in count.values()]
    sym = [row["independent_bb_sym"] for row in count.values()]
    audit.check("E08v3 draw counts", e08["n_draws"] == {"counting": 400, "profile": 10})
    audit.check("E08v3 shared range", min(shared) == 0.6823 and max(shared) == 0.683)
    audit.check("E08v3 naive range", min(naive) == 0.0645 and max(naive) == 0.086)
    audit.check("E08v3 symmetric range", min(sym) == 0.7033 and max(sym) == 0.8284)
    flagship = [row["tes=0.98|A:xgboost"] for row in e08["profile_draws"]]
    nominal = [row["nominal|A:xgboost"] for row in e08["profile_draws"]]
    f_cov = [row["coverage_mean"] for row in flagship]
    n_cov = [row["coverage_mean"] for row in nominal]
    f_bias = [row["bias_mean"] for row in flagship]
    n_bias = [row["bias_mean"] for row in nominal]
    audit.check("E08v3 flagship coverage range", min(f_cov) == 0 and max(f_cov) == 0.238)
    audit.check("E08v3 nominal coverage range", min(n_cov) == 0 and max(n_cov) == 0.359)
    audit.check("E08v3 flagship bias range", min(f_bias) == -6.6 and max(f_bias) == 4.0499)
    audit.check("E08v3 nominal bias range", min(n_bias) == -6.5567 and max(n_bias) == 7.496)
    audit.check(
        "E08v3 supplement transcription",
        has_all(
            supplement,
            [
                "0.6828 & 0.0691 & 0.6501 & 0.8113 & 0.5220",
                "0.6827 & 0.0860 & 0.6605 & 0.8284 & 0.5220",
                "0.6830 & 0.0673 & 0.5650 & 0.7513 & 0.5216",
                "0.6823 & 0.0645 & 0.5458 & 0.7033 & 0.5164",
                r"$-6.557$--$+7.496$",
            ],
        ),
    )

    # E13v2: validate the mechanism and resolution tables.
    e13 = load("E13v2_baw_allocation.json")
    syn = e13["populations"]["synthetic_v1"]
    bench = e13["populations"]["benchmark_class"]
    audit.check("E13v2 validity", e13["acceptance"]["a_validity"]["pass"])
    audit.check("E13v2 impossibility branch", e13["acceptance"]["b_physics_resolution"]["impossibility_branch"])
    audit.check("E13v2 weighted signal fraction", bench["class_structure"]["weighted_signal_fraction"] == 0.000966)
    audit.check("E13v2 TPR Z margin", bench["z_margin_diagnostics"]["0.05"]["tpr_z_margin"] == 2.827e-05)
    audit.check("E13v2 TPR radius", bench["radius_at_nmax"]["tpr"] == 0.001806)
    audit.check("E13v2 v1 radius", bench["radius_at_nmax"]["v1_ba_radius_ba_units"] == 0.288855)
    audit.check(
        "E13v2 benchmark TNR resolves",
        bench["cells"]["m+0.05|true"]["component_verdicts"]["tnr"]["SUPPORTED"] == 200
        and bench["cells"]["m+0.05|false"]["component_verdicts"]["tnr"]["REFUTED"] == 200,
    )
    audit.check(
        "E13v2 synthetic control resolves",
        syn["cells"]["m+0.05|true"]["presplit_verdicts"]["SUPPORTED"] == 83
        and syn["cells"]["m+0.05|false"]["presplit_verdicts"]["REFUTED"] == 87,
    )
    audit.check(
        "E13v2 supplement diagnostics",
        has_all(
            supplement,
            ["0.301459 & 0.000966", "0.011776 & 0.001806", "0.168819 & 0.288855"],
        ),
    )

    # E19: error accounting and fresh-world integrity.
    e19 = load("E19_fresh_world_validity.json")
    unw = e19["error_rates"]["unweighted"]
    weighted = e19["error_rates"]["weighted"]
    audit.check("E19 archive certification", len(e19["archive_certification"]) == 12 and all(e19["archive_certification"].values()))
    audit.check("E19 unweighted counts", unw["counts_nonvetoed"] == [11, 3060] and unw["counts_all"] == [11, 7700])
    audit.check("E19 weighted counts", weighted["counts"] == [6, 7980])
    audit.check("E19 weight bound", e19["w_max"]["w_max"] == 14.80963)
    audit.check(
        "E19 supplement transcription",
        has_all(
            supplement,
            [
                "11/3,060 = 0.359",
                "11/7,700 = 0.143",
                "6/7,980 = 0.075",
                r"7.22421\times2.05=14.80963",
            ],
        ),
    )

    # E06 n* efficiency table.
    e06 = load("E06_nstar_efficiency.json")
    audit.check("E06 overall", e06["overall"] == {"n_cells": 518, "ratio_q25": 1.56, "ratio_q50": 2.07, "ratio_q75": 2.97})
    expected_buckets = {
        "[0.01, 0.02)": (95, 2.82, 3.35, 3.85),
        "[0.02, 0.04)": (95, 2.62, 3.19, 3.66),
        "[0.04, 0.08)": (164, 1.63, 1.98, 2.38),
        ">=0.08": (164, 1.25, 1.46, 1.72),
    }
    for bucket, expected in expected_buckets.items():
        row = e06["by_margin_bucket"][bucket]
        observed = (row["n_cells"], row["ratio_q25"], row["ratio_q50"], row["ratio_q75"])
        audit.check(f"E06 bucket {bucket}", observed == expected)

    # E16: recompute the six displayed rows from the 30 per-config records.
    e16 = load("E16_quantum_uncertainty.json")
    e16_fields = {field for item in e16["per_config"].values() for field in item}
    audit.check(
        "E16 target movements not archived",
        "m_s_shift_unw" in e16_fields and "m_s_shift_w" in e16_fields
        and not ({"delta_m_t", "m_t_shift", "delta_m_t_minus_delta_m_s"} & e16_fields),
    )
    audit.check(
        "Proposition 4 remains conditional",
        "$\\Delta M_T-\\Delta M_S$; therefore Fig.~S16 and Table~S6 do not instantiate" in main_tex
        and "do not instantiate either condition" in supplement,
    )
    audit.check(
        "no stale Proposition 4 flip inference",
        all(phrase not in main_tex for phrase in
            ["must flip", "must not", "theory's prediction traced", "they predict what follows"]),
    )
    expected_e16 = {
        "128": (13.66, 488.6, 0.058, 20.8, 15.8, 71.4, 94.0),
        "256": (9.66, 455.2, 0.139, 17.7, 16.1, 49.4, 92.9),
        "512": (6.84, 428.3, 0.023, 0.9, 11.5, 47.7, 92.5),
        "1024": (4.83, 407.6, 0.080, 11.9, 13.2, 54.6, 92.0),
        "2048": (3.42, 392.1, 0.038, 5.8, 11.1, 58.4, 93.9),
        "4096": (2.42, 380.7, 0.034, 0.4, 6.7, 40.4, 93.0),
    }
    audit.check("E16 config count", len(e16["per_config"]) == 30)
    for shots, expected in expected_e16.items():
        configs = [value for key, value in e16["per_config"].items() if key.startswith(f"shots{shots}|")]
        aggregate = e16["aggregate_by_shots"][shots]
        observed = (
            round(100 * mean(item["kernel"]["frob_rel_err"] for item in configs), 2),
            round(mean(item["kernel"]["eff_rank"] for item in configs), 1),
            round(max(abs(item["m_s_shift_w"]) for item in configs), 3),
            round_half_up(100 * aggregate["far"]["flip_rate_fixed_tau_mean"], 1),
            round_half_up(100 * aggregate["moderate"]["flip_rate_own_tau_mean"], 1),
            round_half_up(100 * aggregate["moderate"]["flip_rate_fixed_tau_mean"], 1),
            round_half_up(100 * aggregate["near"]["abstention_mean"], 1),
        )
        audit.check(f"E16 row {shots}", observed == expected, f"observed {observed}")

    # Existing artifact values newly surfaced by the editorial corrections.
    e10 = load("E10_hardware.json")
    local_floor = mean(row["frob_rel_err"] for row in
                       e10["kernels"]["shots_local"]["stats_vs_ideal"])
    audit.check("E10 local shot floor", round(local_floor, 3) == 0.019)
    e11 = load("E11v3_cms_stats.json")
    audit.check(
        "CMS hardened C2 interval",
        e11["claims_ledger"]["C2_w_norm"]["evidence"]["ratio_ci95_with_mc_stat"]
        == [0.9042, 0.9972],
    )
    audit.check(
        "CMS hardened C4 significance",
        e11["claims_ledger"]["C4_ss_qcd"]["evidence"]["z_with_mc_stat"] == 18.78,
    )

    # E15: all 18 displayed model/family rows are direct four-decimal transcriptions.
    e15 = load("E15_sensitivity.json")
    model_labels = {"A:qksvc": "QK-SVC", "A:rbf_svc": "RBF-SVC", "A:xgboost": "XGBoost"}
    family_labels = {
        "tes": "TES",
        "jes": "JES",
        "soft_met": "soft-MET",
        "ttbar_scale": "ttbar scale",
        "diboson_scale": "diboson scale",
        "bkg_scale": "background scale",
    }
    for family, family_label in family_labels.items():
        data = e15["families"][family]
        for model, model_label in model_labels.items():
            values = [data["levels"][level][model]["slope_at_nominal_mu_avg"] for level in ["L1", "L2", "L3"]]
            tracking = data["tracking"]["L2"][model]
            row = (
                f"{family_label} & {model_label} & {values[0]:.4f} & {values[1]:.4f} & "
                f"{values[2]:.4f} & {tracking:.4f}"
            )
            audit.check(f"E15 row {family}/{model}", row in supplement, row)

    # Unique-arm ledger and source map.
    for arm in ["E02R", "E12(e)", "E14 v1", "E15 gate", "E17(b)", "E08v2(a)", "E08v2(b)", "E08v3(a)", "E13v2(b)"]:
        audit.check(f"falsifier ledger {arm}", supplement.count(arm + " &") == 1)

    # Bidirectional scientific-body check. The title, abstract, Introduction,
    # declarations and section ordering are deliberately journal-adapted;
    # citations, math syntax, headings, and table layout are stripped here.
    draft_words = prose_words(draft_md, "draft")
    tex_words = prose_words(main_tex, "tex")
    draft_to_tex = ngram_coverage(draft_words, tex_words)
    tex_to_draft = ngram_coverage(tex_words, draft_words)
    audit.check("semantic draft-to-LaTeX coverage", draft_to_tex >= 0.90, f"{draft_to_tex:.4f}")
    audit.check("semantic LaTeX-to-draft coverage", tex_to_draft >= 0.92, f"{tex_to_draft:.4f}")

    print(f"F8.2 checks: {audit.checks - len(audit.failures)}/{audit.checks} passed")
    print(f"Semantic 4-gram coverage: draft->LaTeX {draft_to_tex:.4%}; LaTeX->draft {tex_to_draft:.4%}")
    if audit.failures:
        print("FAILURES:")
        for failure in audit.failures:
            print(f"- {failure}")
        return 1
    print("All high-risk numerical transcriptions and semantic gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
