"""I3 rate/control-region evidence (E14; D-024).

Weight-only (normalization) nuisances leave P_theta(X) = P_0(X) exactly, so
no I1 statistic — and no I2 stream carrying nominal weights — has any power
to detect them (formal proposition in the E14 registry entry /
weighted_certification_spec addendum). The evidence that DOES carry the
information is rates: control-region counts are Poisson with means that
scale with the normalization factors. This module supplies:

- ``garwood_poisson_ci`` — exact fixed-n Poisson CI (no optional stopping
  is involved in a single lumi-fixed count, so fixed-n exactness is the
  right guarantee; declared per D-024).
- ``fit_norm_scales`` — joint Poisson MLE for (s_ttbar, s_bkg) over
  disjoint control regions, diboson profiled over its official clip range
  (a dedicated diboson CR does not exist in this feature space — its scale
  is expected UNRESOLVED at I3 and that is a finding, not a failure).
  Confidence intervals from the profile likelihood ratio, validated by
  Monte Carlo in the E14 run.
- ``resolve_rate_claim`` — fail-closed verdict for |s_p - 1| <= x:
  SUPPORTED iff the CI lies inside the band, REFUTED iff it is disjoint
  from the band, UNRESOLVED otherwise.
- ``worst_case_weighted_verdict`` — D-019 §4 / D-024(ii): the true-weighted
  claim A_w^theta >= tau audited by reweighting the labeled stream with
  every corner of the s-confidence box and taking the worst case; the alpha
  budget is split between the rate estimate and the confidence sequence.
"""

from __future__ import annotations

from itertools import product

import numpy as np
from scipy import optimize, stats

from qevc.auditing.claims import Resolution, Verdict
from qevc.statistics.weighted import resolve_weighted_claim

DIBOSON_CLIP = (0.0, 2.0)


def garwood_poisson_ci(n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact (Garwood) central CI for a Poisson mean from one count."""
    if n < 0:
        raise ValueError("count must be >= 0")
    lo = 0.0 if n == 0 else 0.5 * stats.chi2.ppf(alpha / 2, 2 * n)
    hi = 0.5 * stats.chi2.ppf(1 - alpha / 2, 2 * n + 2)
    return float(lo), float(hi)


def _neg_loglike(params, counts, lam_sig, lam_ttbar, lam_diboson, lam_other,
                 s_db, template_var=None):
    """-log L over CRs for (s_tt, s_bkg) at fixed diboson scale s_db.

    lam_* are per-CR expected nominal yields; model per CR:
        lam = lam_sig + s_bkg * (s_tt*lam_ttbar + s_db*lam_diboson + lam_other)

    ``template_var`` (D-024 amendment, Barlow–Beeston-lite): per-CR variance
    of the expected count from template MC statistics. When given, the
    Gaussian-regime likelihood (counts here are 10^3–10^6) uses variance
    lam + template_var, so template noise cannot masquerade as a scale
    shift. When None, pure Poisson (the v1 model whose CI-coverage
    falsifier triggered).
    """
    s_tt, s_bkg = params
    lam = lam_sig + s_bkg * (s_tt * lam_ttbar + s_db * lam_diboson + lam_other)
    lam = np.clip(lam, 1e-9, None)
    if template_var is None:
        return float(np.sum(lam - counts * np.log(lam)))
    var = lam + np.asarray(template_var, dtype=float)
    return float(np.sum((counts - lam) ** 2 / (2.0 * var)
                        + 0.5 * np.log(var)))


def fit_norm_scales(counts: np.ndarray, lam_sig: np.ndarray,
                    lam_ttbar: np.ndarray, lam_diboson: np.ndarray,
                    lam_other: np.ndarray, alpha: float = 0.05,
                    clip_tt=(0.8, 1.2), clip_bkg=(0.99, 1.01),
                    template_var: np.ndarray | None = None) -> dict:
    """Joint MLE for (s_ttbar, s_bkg); diboson profiled over its clip range.

    Returns point estimates and profile-likelihood-ratio CIs (1 dof, level
    1-alpha per parameter). Coverage is Monte-Carlo-validated in the E14 run
    before any verdict is issued (registry falsifier). ``template_var``
    activates the D-024-amended template-statistics-aware likelihood.
    """
    counts = np.asarray(counts, dtype=float)
    db_grid = np.linspace(*DIBOSON_CLIP, 9)

    def nll_min(s_tt_fix: float | None = None,
                s_bkg_fix: float | None = None) -> tuple[float, tuple]:
        """Min nll over the free parameters (diboson profiled on a grid)."""
        best_val, best_par = np.inf, (1.0, 1.0)
        for s_db in db_grid:
            if s_tt_fix is not None and s_bkg_fix is not None:
                val = _neg_loglike((s_tt_fix, s_bkg_fix), counts, lam_sig,
                                   lam_ttbar, lam_diboson, lam_other, s_db,
                                   template_var)
                par = (s_tt_fix, s_bkg_fix)
            elif s_tt_fix is not None:
                r = optimize.minimize_scalar(
                    lambda b: _neg_loglike((s_tt_fix, b), counts, lam_sig,
                                           lam_ttbar, lam_diboson, lam_other,
                                           s_db, template_var),
                    bounds=clip_bkg, method="bounded")
                val, par = float(r.fun), (s_tt_fix, float(r.x))
            elif s_bkg_fix is not None:
                r = optimize.minimize_scalar(
                    lambda t: _neg_loglike((t, s_bkg_fix), counts, lam_sig,
                                           lam_ttbar, lam_diboson, lam_other,
                                           s_db, template_var),
                    bounds=clip_tt, method="bounded")
                val, par = float(r.fun), (float(r.x), s_bkg_fix)
            else:
                r = optimize.minimize(
                    lambda p: _neg_loglike(p, counts, lam_sig, lam_ttbar,
                                           lam_diboson, lam_other, s_db,
                                           template_var),
                    [1.0, 1.0], method="L-BFGS-B",
                    bounds=[clip_tt, clip_bkg])
                val, par = float(r.fun), (float(r.x[0]), float(r.x[1]))
            if val < best_val:
                best_val, best_par = val, par
        return best_val, best_par

    nll_hat, (s_tt_hat, s_bkg_hat) = nll_min()
    q_crit = 0.5 * stats.chi2.ppf(1 - alpha, 1)   # on the nll scale

    def plr_ci(name: str, clip) -> tuple[float, float]:
        grid = np.linspace(clip[0], clip[1], 41)
        inside = []
        for v in grid:
            f, _ = (nll_min(s_tt_fix=v) if name == "s_tt"
                    else nll_min(s_bkg_fix=v))
            if f - nll_hat <= q_crit:
                inside.append(v)
        if not inside:
            hat = s_tt_hat if name == "s_tt" else s_bkg_hat
            return (hat, hat)
        return (float(min(inside)), float(max(inside)))

    return {"s_tt_hat": s_tt_hat, "s_bkg_hat": s_bkg_hat,
            "ci_tt": plr_ci("s_tt", clip_tt),
            "ci_bkg": plr_ci("s_bkg", clip_bkg),
            "s_db_unidentified": True, "alpha": alpha}


def resolve_rate_claim(ci: tuple[float, float], band: tuple[float, float]
                       ) -> Verdict:
    """Fail-closed verdict for 's in band': SUPPORTED iff CI inside band,
    REFUTED iff CI disjoint from band, else UNRESOLVED."""
    lo, hi = ci
    b_lo, b_hi = band
    if b_lo <= lo and hi <= b_hi:
        return Verdict.SUPPORTED
    if hi < b_lo or lo > b_hi:
        return Verdict.REFUTED
    return Verdict.UNRESOLVED


def worst_case_weighted_verdict(correct: np.ndarray, w0: np.ndarray,
                                is_ttbar: np.ndarray, is_diboson: np.ndarray,
                                is_bkg: np.ndarray, tau: float, w_max: float,
                                s_boxes: dict[str, tuple[float, float]],
                                alpha_cs: float = 0.025,
                                heuristic_alarm: bool = False) -> dict:
    """True-weighted claim A_w^theta >= tau under an uncertain s-box.

    Evaluates the D-019 one-sample verdict at every corner of the
    (s_tt, s_db, s_bkg) confidence box and combines fail-closed:
    SUPPORTED only if supported at EVERY corner; REFUTED only if refuted at
    every corner; else UNRESOLVED. The caller splits alpha between the box
    (rate evidence) and alpha_cs (the CS at each corner); the union bound
    gives the total level.
    """
    verdicts = []
    for s_tt, s_db, s_bkg in product(s_boxes["ttbar"], s_boxes["diboson"],
                                     s_boxes["bkg"]):
        scale = np.ones_like(w0)
        scale[is_ttbar] *= s_tt
        scale[is_diboson] *= s_db
        scale[is_bkg] *= s_bkg
        u = w0 * scale
        res: Resolution = resolve_weighted_claim(
            correct, u, tau, w_max, alpha=alpha_cs,
            heuristic_alarm=heuristic_alarm)
        verdicts.append(res.verdict)
    if all(v is Verdict.SUPPORTED for v in verdicts):
        final = Verdict.SUPPORTED
    elif all(v is Verdict.REFUTED for v in verdicts):
        final = Verdict.REFUTED
    else:
        final = Verdict.UNRESOLVED
    return {"verdict": final,
            "corner_verdicts": [v.value for v in verdicts]}
