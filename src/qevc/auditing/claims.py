"""Claim objects and the fail-closed decision rule (spec §13, D-006).

A claim is a statement about a target-domain metric, e.g.

    C(M, tau):      M_T(f) >= tau          (absolute form)
    C_delta:        M_T(f) >= M_S(f) - delta   (degradation form, tau = M_S - delta)

Resolution semantics (frozen in docs/decisions.md D-006):

    SUPPORTED  <=>  lower confidence bound >= tau
    REFUTED    <=>  upper confidence bound <  tau
    otherwise      UNRESOLVED

Heuristic sensors may veto SUPPORTED into UNRESOLVED; nothing can promote a
claim to SUPPORTED except labeled target evidence through a valid confidence
bound. Guarantees are inherited from the confidence machinery used (anytime-
valid CS => valid at data-dependent stopping times).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import numpy as np

from qevc.statistics.confidence_sequences import ConfidenceSequence


class Verdict(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Claim:
    """A performance claim about a bounded metric in [0, 1]."""

    metric_name: str
    threshold: float
    description: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1] (rescale the metric)")


@dataclass(frozen=True)
class Resolution:
    """Outcome of auditing one claim on one evidence stream."""

    claim: Claim
    verdict: Verdict
    n_used: int
    lower: float
    upper: float
    n_star: int | None  # first t at which the verdict left UNRESOLVED; None if never
    vetoed: bool = False  # True when a heuristic alarm demoted SUPPORTED


def resolve_claim(
    claim: Claim,
    cs: ConfidenceSequence,
    heuristic_alarm: bool = False,
) -> Resolution:
    """Resolve a claim against a confidence sequence, fail-closed.

    Uses the running intersection of the CS (valid, monotone) and scans for the
    first time the claim resolves; the final verdict is the verdict at the last
    observation. ``heuristic_alarm=True`` demotes SUPPORTED to UNRESOLVED and
    is recorded — it can never flip REFUTED or promote anything.
    """
    inter = cs.running_intersection()
    tau = claim.threshold

    supported_at = inter.lower >= tau
    refuted_at = inter.upper < tau
    resolved_at = supported_at | refuted_at

    n_star: int | None = None
    if resolved_at.any():
        n_star = int(np.argmax(resolved_at)) + 1  # 1-indexed observation count

    if supported_at[-1]:
        verdict = Verdict.SUPPORTED
    elif refuted_at[-1]:
        verdict = Verdict.REFUTED
    else:
        verdict = Verdict.UNRESOLVED

    vetoed = False
    if heuristic_alarm and verdict is Verdict.SUPPORTED:
        verdict = Verdict.UNRESOLVED
        vetoed = True

    return Resolution(
        claim=claim,
        verdict=verdict,
        n_used=inter.n,
        lower=float(inter.lower[-1]),
        upper=float(inter.upper[-1]),
        n_star=n_star,
        vetoed=vetoed,
    )
