"""Reproducible checks for the final LaTeX/supplement audit (F8.2).

This is not a result generator. It verifies the high-risk quantitative
summaries directly against the immutable JSON tables, checks the author and
falsifier metadata, and performs a bidirectional prose n-gram comparison of
the Markdown source and the LaTeX conversion. It writes nothing.
"""

from __future__ import annotations

import json
import hashlib
import re
import sys
import unicodedata
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from statistics import mean, stdev


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "manuscript" / "latex" / "main.tex"
DRAFT = ROOT / "manuscript" / "main" / "draft.md"
SUPPLEMENT = ROOT / "manuscript" / "supplementary" / "supplement.tex"
FORMAL = ROOT / "docs" / "formal_results.md"
WEIGHTED_SPEC = ROOT / "docs" / "weighted_certification_spec.md"
REGISTRY = ROOT / "docs" / "experiment_registry.md"
CITATION = ROOT / "CITATION.cff"
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
        # The Markdown file is a mechanically synchronized prose mirror.
        text = text[
            text.index("## Results") : text.index(
                "### Reproducibility and computational environment"
            )
        ]
        text = text.replace("`", " ")
        text = re.sub(r"\([^\n()]*arXiv:[^\n()]*\)", " ", text)
        text = re.sub(r"^#+ .*$", " ", text, flags=re.MULTILINE)
        text = re.sub(r"[*_#`|]", " ", text)
        text = re.sub(r"(?m)%.*$", " ", text)
        text = re.sub(
            r"\\(?:citep|citet|citealp)(?:\[[^]]*\])?\{[^{}]*\}", " ", text
        )
        text = re.sub(
            r"\\(?:label|ref|includegraphics|setcounter)(?:\[[^]]*\])?\{[^{}]*\}",
            " ", text,
        )
        text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", " ", text)
        text = re.sub(r"\\[A-Za-z@]+\*?", " ", text)
        text = text.replace(r"\&", " and ").replace(r"\_", "_")
        text = re.sub(r"[{}$\\&~^]", " ", text)
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
    citation = CITATION.read_text(encoding="utf-8")

    # Front matter and the two F8.2 corrections must be synchronized.
    for author, orcid in {
        "Roberto": "0009-0003-5312-2634",
        "Iker": "0000-0002-3068-6248",
        "Asier": "0009-0002-8888-8560",
        "Pablo": "0000-0003-3594-9534",
    }.items():
        audit.check(f"{author} ORCID in citation metadata", orcid in citation)
    audit.check("no visual ORCID placeholder in main", "[ORCID]" not in main_tex)
    audit.check("no visual ORCID placeholder in supplement", "[ORCID]" not in supplement)
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
                "registered falsifiers and" in text
                and "public audit" in text,
            )
        else:
            audit.check(
                "Markdown mirror is synchronized",
                "Auto-generated by scripts/sync_markdown_draft.py" in text,
            )

    # Final mathematical/editorial audit: formal scope and stale-claim guards.
    audit.check(
        "Proposition 1 size/power correction synchronized",
        "power equal to its actual size and\nhence at most $\\alpha$" in main_tex
        and "power equal to its actual size and hence\nat most $\\alpha$" in supplement
        and re.search(r"power equal to its actual\s+size", formal) is not None
        and "power equal to its actual size" in weighted_spec,
    )
    audit.check(
        "Proposition 1 fail-closed policy is not a theorem",
        "Under our\nfail-closed policy they remain UNRESOLVED" in main_tex
        and "fail-closed policy, affected rate and true-weighted\nclaims remain UNRESOLVED" in supplement
        and "reported UNRESOLVED under the fail-closed policy" in formal
        and "reported UNRESOLVED by policy" in weighted_spec,
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
        re.search(
            r"jointly limited\s+by nuisance representability and\s+auxiliary-template quality",
            main_tex,
        ) is not None,
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
    e16_deployment = load("E16_deployment_level.json")
    e16_fields = {field for item in e16["per_config"].values() for field in item}
    audit.check(
        "E16 target movements not archived",
        "m_s_shift_unw" in e16_fields and "m_s_shift_w" in e16_fields
        and not ({"delta_m_t", "m_t_shift", "delta_m_t_minus_delta_m_s"} & e16_fields),
    )
    e16_proposition4 = load("E16_proposition4_instantiation.json")
    proposition4_overall = e16_proposition4["aggregate_summaries"]["overall"]
    audit.check(
        "Proposition 3 informatively instantiated",
        e16_proposition4["interpretation"] == "INFORMATIVELY INSTANTIATED"
        and proposition4_overall["n_condition_cells"] == 7200
        and proposition4_overall["n_evaluable_condition_cells"] == 7200
        and proposition4_overall["condition_cell_counts"]["HOLDS"] == 4943
        and "informatively instantiated" in main_tex.lower()
        and "informatively instantiated" in supplement.lower(),
    )
    audit.check(
        "Proposition 3 sufficient-not-necessary semantics",
        proposition4_overall["verdict_flip_contingency"]["FAILS"]
        == {"flip": 13637, "no_flip": 8933}
        and re.search(r"sufficient\s+rather than\s+necessary", main_tex) is not None
        and re.search(r"sufficient\s+rather than\s+necessary", supplement) is not None,
    )
    audit.check(
        "no stale Proposition 3 flip inference",
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
    source_bytes = (TABLES / "E16_quantum_uncertainty.json").read_bytes()
    audit.check(
        "E16 derived source hash",
        e16_deployment["source_sha256"] == hashlib.sha256(source_bytes).hexdigest().upper(),
    )
    audit.check("E16 independent deployment count", e16_deployment["n_independent_deployments_total"] == 30)
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
        derived = e16_deployment["by_shots"][shots]
        audit.check(f"E16 deployment count {shots}", derived["n_independent_deployments"] == 5)
        for seed, item in enumerate(derived["per_seed"], start=1):
            source_item = e16["per_config"][f"shots{shots}|k{seed}"]
            audit.check(
                f"E16 per-seed far rates {shots}/k{seed}",
                item["far_flip_rate_fixed_tau"] == source_item["strata"]["far"]["flip_rate_fixed_tau"]
                and item["far_flip_rate_own_tau"] == source_item["strata"]["far"]["flip_rate_own_tau"],
            )

    far_expected = {
        "128": (0.208, 0.1986, [0.0, 0.44], [0.15, 0.26]),
        "256": (0.177, 0.3958, [0.0, 0.885], [0.0, 0.2213]),
        "512": (0.009, 0.0089, [0.0, 0.02], [0.0063, 0.0112]),
        "1024": (0.119, 0.2633, [0.0, 0.59], [0.0013, 0.1487]),
        "2048": (0.058, 0.0672, [0.0, 0.14], [0.0375, 0.0725]),
        "4096": (0.004, 0.0065, [0.0, 0.015], [0.0013, 0.005]),
    }
    for shots, expected in far_expected.items():
        summary = e16_deployment["by_shots"][shots]["deployment_level_summary"]["far_flip_rate_fixed_tau"]
        observed = (summary["mean"], summary["sample_sd"], summary["range"], summary["leave_one_deployment_out_mean_range"])
        audit.check(f"E16 deployment summary {shots}", observed == expected, str(observed))

    # Post-hoc PSD sensitivity: all numbers are derived from the same 30
    # deterministic E16 realizations; the historical primary JSON is immutable.
    e16_psd = load("E16_psd_sensitivity.json")
    audit.check("E16 PSD deployment count", e16_psd["n_independent_deployments"] == 30)
    audit.check(
        "E16 PSD raw replay",
        e16_psd["raw_replay_validation"]["all_30_primary_rows_match"]
        and not e16_psd["raw_replay_validation"]["mismatches"],
    )
    audit.check(
        "E16 PSD primary hash",
        e16_psd["provenance"]["primary_e16_sha256"]
        == hashlib.sha256(source_bytes).hexdigest().upper(),
    )
    expected_psd_rows = {
        "128": (-1.930, -1.939, 580, 580, 0.0, 0.0, 20.8, 31.5),
        "256": (-1.325, -1.333, 531, 532, 0.0, 0.0, 17.7, 40.7),
        "512": (-0.936, -0.966, 489, 490, 0.0, 0.0, 0.9, 25.1),
        "1024": (-0.655, -0.657, 449, 450, 0.0, 0.0, 11.9, 3.0),
        "2048": (-0.448, -0.457, 412, 413, 0.0, 0.0, 5.8, 6.9),
        "4096": (-0.313, -0.319, 379, 380, 0.0, 0.0, 0.4, 0.3),
    }
    for shots, expected in expected_psd_rows.items():
        summary = e16_psd["aggregate_by_shots"][shots]
        observed = (
            round(summary["spectrum_raw"]["lambda_min"]["median"], 3),
            round(summary["spectrum_raw"]["lambda_min"]["worst_case"], 3),
            round(summary["spectrum_raw"]["negative_modes"]["median"]),
            round(summary["spectrum_raw"]["negative_modes"]["worst_case"]),
            round_half_up(100 * summary["raw_far_c_dep_flip_rate"]["mean"], 1),
            round_half_up(100 * summary["psd_far_c_dep_flip_rate"]["mean"], 1),
            round_half_up(100 * summary["raw_far_c_ideal_flip_rate"]["mean"], 1),
            round_half_up(100 * summary["psd_far_c_ideal_flip_rate"]["mean"], 1),
        )
        audit.check(f"E16 PSD row {shots}", observed == expected, str(observed))
        rendered = " & ".join(
            [
                shots,
                "5",
                f"${expected[0]:.3f}$",
                f"${expected[1]:.3f}$",
                str(expected[2]),
                str(expected[3]),
            ]
        )
        normalized_supplement = re.sub(r"\s+", " ", supplement)
        audit.check(
            f"E16 PSD supplement row {shots}",
            rendered in normalized_supplement,
            rendered,
        )
    audit.check(
        "E16 PSD all raw Grams indefinite",
        all(row["spectrum_raw"]["negative_modes"] > 0
            and row["spectrum_raw"]["lambda_min"] < 0
            for row in e16_psd["per_deployment"].values()),
    )
    audit.check(
        "E16 PSD scoped verdict",
        "PSD-sensitive-but-scoped" in main_tex
        and "PSD-sensitive-but-scoped" in supplement,
    )
    audit.check(
        "E16 raw LIBSVM semantics",
        "RAW-INDEFINITE fitted object is not interpreted as the\nstandard convex RKHS SVM" in main_tex
        and "RAW-INDEFINITE\nfitted object is not interpreted as the standard convex RKHS SVM" in supplement,
    )
    audit.check(
        "E16 PSD regularization semantics",
        "not a normalized fidelity Gram" in main_tex
        and "no global Mercer\nextension is claimed" in main_tex
        and "not a normalized fidelity Gram" in supplement
        and "no global\nMercer extension is claimed" in supplement,
    )
    audit.check(
        "E16 far-margin support-only scope",
        "no\nfalse far-margin deployment-relative claim" in main_tex
        and "no false far-margin deployment-relative claim" in supplement,
    )
    audit.check(
        "E16 heterogeneity wording (non-monotonicity demoted)",
        "are each dominated by one or two\ndeployments" in main_tex
        and "non-monotonic" not in main_tex
        and "non-monotonic" not in supplement
        and "outlier sensitivity" in supplement
        and "decrease from 20.8" not in main_tex,
    )

    # 0.3.6 derived analyses: every displayed number is recomputed from its JSON.
    strat = load("E16_prop3_margin_stratification.json")
    audit.check(
        "stratification totals",
        strat["totals"] == {"condition_cells": 7200, "audit_streams": 72000,
                            "holds_cells": 4943, "fails_cells": 2257},
    )
    strat_source = hashlib.sha256((TABLES / "E16_proposition4_instantiation.json").read_bytes()).hexdigest().upper()
    audit.check("stratification source hash", strat["source_sha256"] == strat_source)
    audit.check(
        "stratification largest failing deployment-relative margin",
        strat["largest_abs_ideal_margin_among_FAILS_cells"]["deployment_relative"] < 0.005
        and "largest failing margin 0.0040" in main_tex,
    )
    labels = {"[0,0.005)": "$[0,0.005)$", "[0.005,0.01)": "$[0.005,0.01)$", "[0.01,0.02)": "$[0.01,0.02)$",
              "[0.02,0.04)": "$[0.02,0.04)$", "[0.04,0.08)": "$[0.04,0.08)$", ">=0.08": "$\\geq0.08$"}
    for claim, name in (("deployment_relative", "deployment-relative"), ("ideal_anchored", "ideal-anchored")):
        for key, tex_label in labels.items():
            row = strat["by_claim_semantics"][claim][key]
            h, f = row["HOLDS"], row["FAILS"]
            flip_h = f"{round_half_up(100 * h['verdict_flip_rate'], 1):.1f}" if h["verdict_flip_rate"] is not None else "--"
            flip_f = f"{round_half_up(100 * f['verdict_flip_rate'], 1):.1f}" if f["verdict_flip_rate"] is not None else "--"
            rendered = f"{name} & {tex_label} & {h['cells']} & {f['cells']} & {flip_h} & {flip_f} \\\\"
            audit.check(f"stratification row {claim}/{key}", rendered in supplement, rendered)
    ia = strat["by_claim_semantics"]["ideal_anchored"]
    ia_h = [100 * ia[k]["HOLDS"]["verdict_flip_rate"] for k in labels]
    ia_f = [100 * ia[k]["FAILS"]["verdict_flip_rate"] for k in labels]
    audit.check(
        "stratification ranges quoted in main text",
        round_half_up(min(ia_h), 1) == 2.7 and round_half_up(max(ia_h), 1) == 38.7
        and round_half_up(min(ia_f), 1) == 63.8 and round_half_up(max(ia_f), 1) == 100.0
        and "2.7--38.7\\%" in main_tex and "63.8--100\\%" in main_tex,
    )

    stage = load("E16_stage_decomposition.json")
    rep = stage["reproduction"]
    audit.check(
        "stage decomposition exact reproduction",
        rep["all_raw_stage_D_match_primary"] and rep["all_raw_stage_D_match_psd_archive"]
        and rep["all_psd_stage_D_match_psd_archive"] and rep["platt_slopes_positive"]
        and rep["prop3_movement_max_abs_residual"] == {"raw": 0.0, "psd_repaired": 0.0}
        and rep["prop3_movement_cells_compared"] == {"raw": 1800, "psd_repaired": 1800},
    )
    audit.check(
        "stage decomposition source hash",
        stage["provenance"]["input_sha256"]["primary_e16"] == hashlib.sha256(source_bytes).hexdigest().upper(),
    )
    audit.check(
        "stage decomposition classification",
        stage["classification"]["overall"] == "MIXED"
        and stage["classification"]["by_regime"]["raw"]["label"] == "MIXED"
        and stage["classification"]["by_regime"]["psd_repaired"]["label"] == "MODEL/RANKING-DOMINATED",
    )

    def signed(value: float, digits: int = 4) -> str:
        return f"${round_half_up(value, digits):+.{digits}f}$"

    for regime, label in (("raw", "RAW"), ("psd_repaired", "PSD")):
        agg = stage["aggregate_by_regime"][regime]
        for st in ("B0", "B", "C", "D"):
            b = agg["by_stage"][st]
            dms, dba, dauc = b["delta_M_S_unweighted"], b["delta_source_weighted_balanced_accuracy"], b["delta_nominal_auc"]
            rho = agg["ranking_stability"]["B0_vs_ideal" if st == "B0" else "B_vs_ideal"]["source_val"]["spearman"]["median"]
            row = (
                f"{label} & {st} & {signed(dms['median'])} [{signed(dms['min'])}, {signed(dms['max'])}] & "
                f"{signed(dba['median'])} & {signed(dauc['median'])} & {round_half_up(rho, 3):.3f} & "
                f"{round_half_up(100 * b['far_ideal_anchored_flip_rate']['mean'], 1):.1f} & "
                f"{round_half_up(100 * b['moderate_ideal_anchored_flip_rate']['mean'], 1):.1f} & "
                f"{round_half_up(100 * b['near_ideal_anchored_flip_rate']['mean'], 1):.1f} & "
                f"{round_half_up(100 * b['moderate_deployment_relative_flip_rate']['mean'], 1):.1f} \\\\"
            )
            audit.check(f"stage row {label}/{st}", row in supplement, row)
    raw_agg = stage["aggregate_by_regime"]["raw"]
    raw_inc = raw_agg["source_metric_increments"]["m_s_unw"]
    raw_far = raw_agg["ideal_anchored_flip_path"]["far"]
    audit.check(
        "stage decomposition headline numbers",
        round_half_up(100 * raw_far["cumulative_mean_flip_rate_by_stage"]["C"], 1) == 14.3
        and round_half_up(100 * raw_far["cumulative_mean_flip_rate_by_stage"]["D"], 1) == 9.6
        and round_half_up(100 * raw_far["cumulative_mean_flip_rate_by_stage"]["B"], 1) == 0.2
        and round_half_up(100 * raw_far["positive_share"]["CALIBRATION"], 0) == 99
        and round_half_up(raw_inc["thr"]["share_of_mean_absolute_increment"], 2) == 0.50
        and round_half_up(raw_inc["thr"]["absolute"]["mean"], 3) == 0.020
        and round_half_up(raw_agg["ranking_stability"]["B_vs_ideal"]["source_val"]["spearman"]["median"], 2) == 0.92
        and round_half_up(raw_agg["ranking_stability"]["B_vs_ideal"]["source_val"]["kendall_tau_b"]["median"], 2) == 0.78
        and raw_agg["balanced_accuracy_vs_accuracy"]["deployments_with_abs_delta_BA_w_below_abs_delta_unweighted_accuracy"] == 25
        and stage["aggregate_by_regime"]["psd_repaired"]["balanced_accuracy_vs_accuracy"]["deployments_with_abs_delta_BA_w_below_abs_delta_unweighted_accuracy"] == 28
        and round_half_up(stage["aggregate_by_regime"]["psd_repaired"]["by_stage"]["B0"]["delta_M_S_unweighted"]["median"], 3) == -0.053
        and round_half_up(stage["aggregate_by_regime"]["psd_repaired"]["by_stage"]["B0"]["delta_nominal_auc"]["median"], 3) == 0.017
        and "far flips rise to 14.3" in main_tex and "back to 9.6" in main_tex
        and "25 of 30 raw and 28 of 30 loaded" in main_tex,
    )
    for regime in ("raw", "psd_repaired"):
        cm = stage["aggregate_by_regime"][regime]["common_mode"]["D|unweighted"]
        audit.check(
            f"stage decomposition common mode {regime}",
            cm["abs_delta_M_T_minus_delta_M_S"]["median"] < 0.002
            and cm["abs_delta_M_T"]["median"] > 0.01,
        )

    wmax = load("E13_wmax_nominal_bound_sensitivity.json")
    e13w = wmax["E13_part_b"]
    cmp = e13w["comparison"]
    audit.check("w_max historical replay exact", e13w["historical_replay_exact"] is True and wmax["E19_weighted_arm"]["historical_replay_exact"] is True)
    audit.check(
        "w_max sensitivity numbers",
        cmp["error_rates"]["historical"]["w"]["false_cert"] == 2
        and cmp["error_rates"]["sharp"]["w"]["false_cert"] == 12
        and cmp["error_rates"]["sharp"]["w"]["n_false"] == 8580
        and cmp["n_star_ratio_w_over_unw"]["historical_archived"]["median"] == 1.664
        and cmp["n_star_ratio_w_over_unw"]["sharp_archived_style"]["median"] == 1.336
        and round_half_up(cmp["weighted_accuracy_claims"]["per_claim_n_star_ratio_sharp_over_historical"]["median"], 2) == 0.85
        and cmp["weighted_accuracy_claims"]["stream_verdicts_historical"] == {"SUPPORTED": 6743, "REFUTED": 336, "UNRESOLVED": 12601}
        and cmp["weighted_accuracy_claims"]["stream_verdicts_sharp"] == {"SUPPORTED": 6572, "REFUTED": 310, "UNRESOLVED": 12798}
        and wmax["E19_weighted_arm"]["historical_false_cert_counts"] == [6, 7980]
        and wmax["E19_weighted_arm"]["sharp_false_cert_counts"] == [12, 7980]
        and cmp["cell_transitions"]["near_margin_cells_abs_margin_below_0_01"] == {"cells": 323, "resolved_streams_historical": 46, "resolved_streams_sharp": 72}
        and cmp["cell_transitions"]["far_margin_cells_abs_margin_at_least_0_04"] == {"cells": 312, "resolved_streams_historical": 6082, "resolved_streams_sharp": 5945}
        and "1.66 [1.11, 3.00] & 1.34 [1.00, 2.10]" in supplement
        and "2/8,580 & 12/8,580 & 6/7,980 & 12/7,980" in supplement
        and "median ratio 1.34, IQR 1.00--2.10" in main_tex,
    )

    e01 = load("E01_nominal.json")
    e01_rows = (
        ("A", "linear_svc", "linear SVC"), ("A", "rbf_svc", "RBF-SVC"),
        ("A", "rbf_svc_8f", "RBF-SVC (matched, 8 features)"), ("A", "xgboost", "XGBoost"),
        ("A", "lightgbm", "LightGBM"), ("A", "mlp", "MLP"), ("A", "qksvc", "QK-SVC"),
        ("B", "linear_svc", "linear SVC"), ("B", "xgboost", "XGBoost"),
        ("B", "lightgbm", "LightGBM"), ("B", "mlp", "MLP"),
    )
    for tier, key, label in e01_rows:
        entry = e01["tiers"][tier][key]
        row = (
            f"{tier} & {label} & {entry['features']} & {round_half_up(entry['test']['auc'], 3):.3f} "
            f"[{round_half_up(entry['auc_ci95'][0], 3):.3f}, {round_half_up(entry['auc_ci95'][1], 3):.3f}] & "
            f"{round_half_up(entry['test']['balanced_accuracy'], 3):.3f} \\\\"
        )
        audit.check(f"E01 model row {tier}/{key}", row in supplement, row)
    audit.check(
        "E16 no pseudo-replication wording",
        "not IID replicates" in main_tex
        and "not an IID sample size" in supplement,
    )
    audit.check(
        "Proposition 3 counterexample",
        "$\\Delta M_T=-0.10$" in main_tex
        and "$m^\\star=0.05$, $\\Delta M_T=-0.10$" in supplement,
    )
    audit.check(
        "I1 count-conditioned experiment",
        "$P_\\theta(N,X_1,\\ldots,X_N)$" in main_tex
        and "$P_\\theta(N,X_1,\\ldots,X_N)$" in supplement,
    )
    audit.check(
        "structured Spearman p-values retired",
        "$p < 10^{-4}$" not in main_tex and "IID rank-test $p$-value is not reported" in main_tex,
    )
    audit.check(
        "unsupported equivalence wording retired",
        "statistically indistinguishable" not in main_tex.lower()
        and "statistically equivalent" not in main_tex.lower()
        and "no additional seeds are required" not in main_tex.lower()
        and "no additional seeds are required" not in supplement.lower(),
    )
    audit.check(
        "main article has no internal docs references",
        "docs/" not in main_tex,
    )
    audit.check(
        "hardware measured-entry wording",
        "378 off-diagonal training-kernel" in main_tex
        and "336 cross-kernel entries" in main_tex
        and "fixed analytically to unity" in main_tex
        and "unit-diagonal convention" in supplement,
    )
    audit.check(
        "sealed-role wording is scientifically exact",
        "sealing begins immediately after that construction" in main_tex
        and "scientific-use guarantee" in supplement
        and "never been read" not in main_tex
        and "remain unread" not in supplement,
    )
    audit.check(
        "contribution and CMS claim names do not collide",
        "Contributions 1 and 2" in main_tex
        and "coupled to Contribution 3" in main_tex
        and "C1 and C2 are model-agnostic" not in main_tex,
    )

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
