"""Stratify the frozen Proposition-3 instantiation by ideal-margin magnitude.

DERIVED / NO NEW RANDOMNESS.  Reads only
``results/tables/E16_proposition4_instantiation.json`` (the archived artifact
name retains the pre-v0.3.5 identifier ``proposition4``; the current formal
result is Proposition 3) and reports, for each claim-semantics class and
regime, how the HOLDS/FAILS split of the strict sufficient inequality and the
paired-stream verdict-flip rates distribute across |m*| bins.  The bins refine
the registered far/moderate/near strata; they are descriptive.  Cells and
paired audit streams within a deployment are correlated and are not
independent replications; no IID test is performed.

Usage:
  python scripts/summarize_e16_prop3_margin_stratification.py          # write
  python scripts/summarize_e16_prop3_margin_stratification.py --check  # verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qevc.auditing.stability import FAILS, HOLDS, canonical_json_sha256  # noqa: E402

SOURCE = ROOT / "results" / "tables" / "E16_proposition4_instantiation.json"
OUTPUT = ROOT / "results" / "tables" / "E16_prop3_margin_stratification.json"
BIN_EDGES = (0.0, 0.005, 0.01, 0.02, 0.04, 0.08, float("inf"))
BIN_LABELS = ("[0,0.005)", "[0.005,0.01)", "[0.01,0.02)", "[0.02,0.04)", "[0.04,0.08)", ">=0.08")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def bin_of(value: float) -> str:
    for label, lower, upper in zip(BIN_LABELS, BIN_EDGES[:-1], BIN_EDGES[1:]):
        if lower <= value < upper:
            return label
    raise ValueError(value)


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def stratify(cases: list[dict]) -> dict:
    table = {}
    for label in BIN_LABELS:
        table[label] = {
            status: {
                "cells": 0,
                "streams": 0,
                "verdict_flips": 0,
                "opposite_resolved_verdicts": 0,
                "truth_sign_flip_cells": 0,
            }
            for status in (HOLDS, FAILS)
        }
    for case in cases:
        label = bin_of(abs(float(case["ideal_margin"])))
        status = case["sufficient_condition_status"]
        if status not in (HOLDS, FAILS):
            raise ValueError(f"unexpected status {status}")
        slot = table[label][status]
        slot["cells"] += 1
        slot["truth_sign_flip_cells"] += int(bool(case["ideal_truth"]) != bool(case["realized_truth"]))
        for stream in case["audit_streams"]:
            slot["streams"] += 1
            slot["verdict_flips"] += int(stream["verdict_flip"])
            slot["opposite_resolved_verdicts"] += int(stream["opposite_resolved_verdict"])
    for label in BIN_LABELS:
        for status in (HOLDS, FAILS):
            slot = table[label][status]
            slot["verdict_flip_rate"] = rate(slot["verdict_flips"], slot["streams"])
            slot["truth_sign_flip_cell_rate"] = rate(slot["truth_sign_flip_cells"], slot["cells"])
    return table


def build() -> dict:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    cases = payload["cases"]
    semantics = ("deployment_relative", "ideal_anchored")
    regimes = ("raw", "psd_repaired")
    by_semantics = {
        claim: stratify([c for c in cases if c["claim_semantics"] == claim]) for claim in semantics
    }
    by_regime_and_semantics = {
        regime: {
            claim: stratify([c for c in cases if c["claim_semantics"] == claim and c["regime"] == regime])
            for claim in semantics
        }
        for regime in regimes
    }
    # deployment-relative FAILS cells occur only where |m*| is tiny: record the
    # largest |m*| among FAILS cells for each class.
    largest_fail_margin = {}
    fail_margins = defaultdict(list)
    for case in cases:
        if case["sufficient_condition_status"] == FAILS:
            fail_margins[case["claim_semantics"]].append(abs(float(case["ideal_margin"])))
    for claim in semantics:
        values = fail_margins.get(claim, [])
        largest_fail_margin[claim] = round(max(values), 8) if values else None
    totals = {
        "condition_cells": len(cases),
        "audit_streams": sum(len(c["audit_streams"]) for c in cases),
        "holds_cells": sum(c["sufficient_condition_status"] == HOLDS for c in cases),
        "fails_cells": sum(c["sufficient_condition_status"] == FAILS for c in cases),
    }
    output = {
        "analysis": "Proposition 3 instantiation stratified by ideal-margin magnitude |m*|",
        "status": "DERIVED / NO NEW RANDOMNESS",
        "numbering_note": (
            "The source artifact name retains the pre-v0.3.5 identifier 'proposition4'; after "
            "natural renumbering the corresponding formal result is Proposition 3."
        ),
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": sha256(SOURCE),
        "source_canonical_payload_sha256": payload["reproducibility"]["canonical_payload_sha256"],
        "method": (
            "each of the 7,200 condition cells is assigned to a bin by |ideal_margin|; within "
            "each bin and claim-semantics class the HOLDS/FAILS cells, paired audit streams, "
            "ternary verdict flips, opposite resolved verdicts and truth-sign flips are counted"
        ),
        "bins": {"edges": [e if e != float("inf") else "inf" for e in BIN_EDGES], "labels": list(BIN_LABELS)},
        "unit_of_analysis": (
            "condition cell / paired audit stream; cells and streams within a deployment are "
            "correlated and are not independent replications; no IID test is performed"
        ),
        "dependencies": ["results/tables/E16_proposition4_instantiation.json"],
        "limitations": [
            "descriptive stratification of correlated cells",
            "bins are post-hoc refinements of the registered far/moderate/near strata",
            "HOLDS is a sufficient truth-sign condition; FAILS does not predict a flip",
        ],
        "totals": totals,
        "largest_abs_ideal_margin_among_FAILS_cells": largest_fail_margin,
        "by_claim_semantics": by_semantics,
        "by_regime_and_claim_semantics": by_regime_and_semantics,
    }
    output["canonical_payload_sha256"] = canonical_json_sha256(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify the committed artifact")
    args = parser.parse_args()
    output = build()
    if args.check:
        committed = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if committed != output:
            print("MISMATCH: committed stratification differs from a fresh derivation")
            return 1
        print(f"OK: {OUTPUT.relative_to(ROOT)} reproduces exactly")
        return 0
    OUTPUT.write_text(json.dumps(output, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
