"""Deterministic helpers for instantiating the Proposition 4 sign bound."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from typing import Any, Iterable


HOLDS = "HOLDS"
FAILS = "FAILS"
NOT_EVALUABLE = "NOT-EVALUABLE"
RESOLVED_VERDICTS = {"SUPPORTED", "REFUTED"}


def sufficient_condition_status(
    ideal_margin: float,
    movement: float,
    *,
    evaluable: bool = True,
) -> str:
    """Evaluate the strict sufficient inequality |m*| > |movement|.

    A failed inequality is deliberately returned as ``FAILS`` rather than as a
    predicted sign change: Proposition 4 is sufficient, not necessary.
    """

    if not evaluable or not (math.isfinite(ideal_margin) and math.isfinite(movement)):
        return NOT_EVALUABLE
    return HOLDS if abs(ideal_margin) > abs(movement) else FAILS


def opposite_resolved_verdict(left: str, right: str) -> bool:
    """Return whether two verdicts are opposite and both are resolved."""

    return (
        left in RESOLVED_VERDICTS
        and right in RESOLVED_VERDICTS
        and left != right
    )


def canonical_json_sha256(payload: Any) -> str:
    """Hash a JSON value using a platform-independent canonical encoding."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _contingency(cases: list[dict[str, Any]], outcome: str) -> dict[str, dict[str, int]]:
    matrix = {
        HOLDS: {"flip": 0, "no_flip": 0},
        FAILS: {"flip": 0, "no_flip": 0},
        NOT_EVALUABLE: {"flip": 0, "no_flip": 0},
    }
    for case in cases:
        status = case["sufficient_condition_status"]
        for stream in case["audit_streams"]:
            key = "flip" if stream[outcome] else "no_flip"
            matrix[status][key] += 1
    return matrix


def summarize_proposition4_cases(cases: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Summarize condition cells without treating them as independent trials."""

    rows = list(cases)
    statuses = Counter(row["sufficient_condition_status"] for row in rows)
    evaluable = statuses[HOLDS] + statuses[FAILS]
    n_streams = sum(len(row["audit_streams"]) for row in rows)
    verdict_matrix = _contingency(rows, "verdict_flip")
    opposite_matrix = _contingency(rows, "opposite_resolved_verdict")

    per_deployment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        per_deployment[row["deployment_id"]].append(row)

    deployment_summaries = {}
    for deployment_id, deployment_rows in sorted(per_deployment.items()):
        dep_statuses = Counter(
            row["sufficient_condition_status"] for row in deployment_rows
        )
        dep_evaluable = dep_statuses[HOLDS] + dep_statuses[FAILS]
        dep_streams = [
            (row["sufficient_condition_status"], stream)
            for row in deployment_rows
            for stream in row["audit_streams"]
        ]
        deployment_summaries[deployment_id] = {
            "n_condition_cells": len(deployment_rows),
            "n_audit_stream_cases": len(dep_streams),
            "fraction_evaluable": dep_evaluable / len(deployment_rows)
            if deployment_rows
            else None,
            "fraction_holds_among_evaluable": dep_statuses[HOLDS] / dep_evaluable
            if dep_evaluable
            else None,
            "verdict_flip_rate_when_holds": (
                sum(stream["verdict_flip"] for status, stream in dep_streams if status == HOLDS)
                / sum(status == HOLDS for status, _ in dep_streams)
                if any(status == HOLDS for status, _ in dep_streams)
                else None
            ),
            "verdict_flip_rate_when_fails": (
                sum(stream["verdict_flip"] for status, stream in dep_streams if status == FAILS)
                / sum(status == FAILS for status, _ in dep_streams)
                if any(status == FAILS for status, _ in dep_streams)
                else None
            ),
        }

    return {
        "descriptive_unit": (
            "deployment; condition cells and paired audit streams within a deployment "
            "are correlated and are not independent replications"
        ),
        "n_deployments": len(per_deployment),
        "n_condition_cells": len(rows),
        "n_audit_stream_cases": n_streams,
        "n_evaluable_condition_cells": evaluable,
        "fraction_evaluable": evaluable / len(rows) if rows else None,
        "fraction_holds_among_evaluable": statuses[HOLDS] / evaluable if evaluable else None,
        "condition_cell_counts": {
            HOLDS: statuses[HOLDS],
            FAILS: statuses[FAILS],
            NOT_EVALUABLE: statuses[NOT_EVALUABLE],
        },
        "verdict_flip_contingency": verdict_matrix,
        "opposite_resolved_verdict_contingency": opposite_matrix,
        "per_deployment": deployment_summaries,
    }
