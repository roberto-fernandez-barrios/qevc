"""Binned profile-likelihood inference (E15; D-023).

Model, per environment and classifier: score-binned Poisson likelihood

    L(mu, theta) = prod_b Pois( n_b | mu * S_b(theta_shape)
                                + sum_p f_p(theta_norm) * B_{p,b}(theta_shape) )
                   * prod_j constraint_j(theta_j)

- Score bins are frozen on source_val (quantile edges with a background
  floor), never re-derived per environment.
- Shape nuisances (tes, jes, soft_met) enter through per-process template
  morphing anchored at the official grid points: piecewise
  linear-quadratic in sigma units for tes/jes (quadratic for |alpha| <= 1
  matching the +-1 sigma anchors, linear continuation from the 1->2 sigma
  slope beyond), piecewise-linear in GeV for soft_met (anchors 0,1,2,3,5).
- Normalization nuisances act EXACTLY (multiplicative per process):
  ttbar_scale on ttbar, diboson_scale on diboson, bkg_scale on all
  background — no interpolation error.
- Constraints: unit Gaussians in sigma units for tes/jes; Gaussian with
  official sigma for the norm scales (bounds at the official clips);
  soft_met is profiled flat on [0, 5] (D-023 amendment ii — the official
  LogNormal prior has no density at the nominal 0).

Intervals come from the profile likelihood ratio (Wilks, 1 dof):
q(mu) = -2 [ ln L(mu, theta_hat_hat) - ln L(mu_hat, theta_hat) ] <= z^2.
The Wilks approximation is gate-checked at nominal before any shifted
environment is interpreted (registry E15 falsifier).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import optimize

SHAPE_NUISANCES = ("tes", "jes", "soft_met")
NORM_NUISANCES = ("ttbar_scale", "diboson_scale", "bkg_scale")
# official priors / clips (docs/dataset_audit.md §1.2)
NORM_SIGMA = {"ttbar_scale": 0.02, "diboson_scale": 0.25, "bkg_scale": 0.001}
NORM_CLIP = {"ttbar_scale": (0.8, 1.2), "diboson_scale": (0.0, 2.0),
             "bkg_scale": (0.99, 1.01)}
SHAPE_SIGMA = {"tes": 0.01, "jes": 0.01}          # sigma units for tes/jes
TESJES_ALPHA_BOUND = 10.0                          # clip range [0.9,1.1] = 10 sigma
SOFTMET_BOUND = (0.0, 5.0)


def score_bin_edges(p_sv: np.ndarray, w_sv: np.ndarray, y_sv: np.ndarray,
                    n_bins: int, b_floor: float) -> np.ndarray:
    """Frozen score binning: weighted-quantile edges on source_val with
    low-score bins merged until every bin's background yield >= b_floor."""
    qs = np.linspace(0.0, 1.0, n_bins + 1)
    order = np.argsort(p_sv)
    cw = np.cumsum(w_sv[order])
    cw /= cw[-1]
    edges = np.interp(qs, cw, p_sv[order])
    edges[0], edges[-1] = 0.0, 1.0
    edges = np.unique(edges)
    # merge from the left until every bin clears the background floor
    while len(edges) > 2:
        b_yield, _ = np.histogram(p_sv[y_sv == 0], bins=edges,
                                  weights=w_sv[y_sv == 0])
        bad = np.flatnonzero(b_yield < b_floor)
        if len(bad) == 0:
            break
        i = bad[0]
        edges = np.delete(edges, i + 1 if i + 1 < len(edges) - 1 else i)
    return edges


@dataclass
class TemplateSet:
    """Per-process binned templates with shape anchors, for one classifier."""

    edges: np.ndarray
    processes: list[str]
    signal_processes: tuple[str, ...] = ("htautau",)
    nominal: dict[str, np.ndarray] = field(default_factory=dict)
    # shape_anchors[nuisance][alpha_key][process] -> per-bin yields;
    # alpha_key in sigma units for tes/jes (-2,-1,1,2), GeV for soft_met.
    shape_anchors: dict[str, dict[float, dict[str, np.ndarray]]] = field(
        default_factory=dict)

    @property
    def n_bins(self) -> int:
        return len(self.edges) - 1

    def hist(self, p: np.ndarray, w: np.ndarray) -> np.ndarray:
        h, _ = np.histogram(np.clip(p, 0.0, 1.0), bins=self.edges, weights=w)
        return h

    # -- morphing -----------------------------------------------------------

    def _shape_delta(self, nuisance: str, alpha: float,
                     proc: str) -> np.ndarray:
        """Yield shift vs nominal for one nuisance at strength alpha."""
        anchors = self.shape_anchors.get(nuisance, {})
        if not anchors or alpha == 0.0:
            return np.zeros(self.n_bins)
        nom = self.nominal[proc]
        if nuisance == "soft_met":  # piecewise linear on the GeV grid incl. 0
            xs = np.array(sorted(anchors))
            grid = np.concatenate(([0.0], xs))
            a = min(max(float(alpha), SOFTMET_BOUND[0]), SOFTMET_BOUND[1])
            deltas = np.vstack([np.zeros(self.n_bins)]
                               + [anchors[x][proc] - nom for x in xs])
            out = np.empty(self.n_bins)
            for b in range(self.n_bins):
                out[b] = np.interp(a, grid, deltas[:, b])
            return out
        # tes/jes: quadratic inside +-1 sigma, linear continuation outside
        d_p1 = anchors[1.0][proc] - nom
        d_m1 = anchors[-1.0][proc] - nom
        d_p2 = anchors.get(2.0, {}).get(proc, 2.0 * d_p1) - (
            nom if 2.0 in anchors else np.zeros(self.n_bins))
        d_m2 = anchors.get(-2.0, {}).get(proc, 2.0 * d_m1) - (
            nom if -2.0 in anchors else np.zeros(self.n_bins))
        a = min(max(float(alpha), -TESJES_ALPHA_BOUND), TESJES_ALPHA_BOUND)
        if abs(a) <= 1.0:
            return a * (d_p1 - d_m1) / 2.0 + a * a * (d_p1 + d_m1) / 2.0
        if a > 1.0:
            slope = d_p2 - d_p1
            return d_p1 + (a - 1.0) * slope
        slope = d_m2 - d_m1
        return d_m1 + (-a - 1.0) * slope

    def expected(self, mu: float, shape_alphas: dict[str, float],
                 norm_scales: dict[str, float]) -> np.ndarray:
        """lambda_b(mu, theta): morphed, norm-scaled expected yields."""
        lam = np.zeros(self.n_bins)
        for proc in self.processes:
            y = self.nominal[proc].copy()
            for nui, a in shape_alphas.items():
                y = y + self._shape_delta(nui, a, proc)
            y = np.clip(y, 1e-9, None)
            f = 1.0
            if proc not in self.signal_processes:
                if proc == "ttbar":
                    f *= norm_scales.get("ttbar_scale", 1.0)
                if proc == "diboson":
                    f *= norm_scales.get("diboson_scale", 1.0)
                f *= norm_scales.get("bkg_scale", 1.0)
                lam = lam + f * y
            else:
                lam = lam + mu * y
        return np.clip(lam, 1e-9, None)


@dataclass(frozen=True)
class FitResult:
    mu_hat: float
    nll_hat: float
    interval: tuple[float, float]
    nuisance_hat: dict[str, float]
    converged: bool


class ProfileLikelihood:
    """Profile fit of (mu, theta) for one TemplateSet and observed counts."""

    def __init__(self, templates: TemplateSet, profile_shapes: list[str],
                 profile_norms: list[str]):
        self.t = templates
        self.shapes = [s for s in SHAPE_NUISANCES if s in profile_shapes]
        self.norms = [n for n in NORM_NUISANCES if n in profile_norms]

    # parameter vector: [mu, alphas..., norms...]
    def _unpack(self, x: np.ndarray):
        mu = x[0]
        k = 1
        shape_alphas = {}
        for s in self.shapes:
            shape_alphas[s] = x[k]; k += 1
        norm_scales = {}
        for nrm in self.norms:
            norm_scales[nrm] = x[k]; k += 1
        return mu, shape_alphas, norm_scales

    def nll(self, x: np.ndarray, n_obs: np.ndarray,
            aux: dict | None = None) -> float:
        """-log L. ``aux`` holds the auxiliary constraint centers θ̃ (D-023
        amendment 2, unconditional ensemble): tes/jes in sigma units
        (default 0), norm scales in scale units (default 1). soft_met has
        no constraint term (flat on [0,5])."""
        mu, shape_alphas, norm_scales = self._unpack(x)
        lam = self.t.expected(mu, shape_alphas, norm_scales)
        val = float(np.sum(lam - n_obs * np.log(lam)))
        for s in self.shapes:
            if s in ("tes", "jes"):
                a0 = 0.0 if aux is None else float(aux.get(s, 0.0))
                val += 0.5 * (shape_alphas[s] - a0) ** 2
        for nrm in self.norms:
            a0 = 1.0 if aux is None else float(aux.get(nrm, 1.0))
            val += 0.5 * ((norm_scales[nrm] - a0) / NORM_SIGMA[nrm]) ** 2
        return val

    def _bounds(self, mu_bounds):
        bounds = [mu_bounds]
        for s in self.shapes:
            bounds.append(SOFTMET_BOUND if s == "soft_met"
                          else (-TESJES_ALPHA_BOUND, TESJES_ALPHA_BOUND))
        for nrm in self.norms:
            bounds.append(NORM_CLIP[nrm])
        return bounds

    def _x0(self, mu0=1.0):
        x0 = [mu0]
        for s in self.shapes:
            x0.append(0.0 if s != "soft_met" else 1e-3)
        for _ in self.norms:
            x0.append(1.0)
        return np.array(x0)

    def _minimize(self, n_obs, mu_bounds, fix_mu=None, x0=None, aux=None):
        bounds = self._bounds(mu_bounds)
        x0 = self._x0() if x0 is None else np.asarray(x0, dtype=float).copy()
        if fix_mu is not None:
            x0[0] = fix_mu
            bounds = [(fix_mu, fix_mu)] + bounds[1:]
        res = optimize.minimize(self.nll, x0, args=(n_obs, aux),
                                method="L-BFGS-B", bounds=bounds)
        return res

    def fit(self, n_obs: np.ndarray, z: float = 1.0,
            mu_bounds: tuple[float, float] = (-5.0, 15.0),
            aux: dict | None = None) -> FitResult:
        """Global fit + profile-likelihood-ratio interval at +-z (q = z^2)."""
        n_obs = np.asarray(n_obs, dtype=float)
        best = self._minimize(n_obs, mu_bounds, aux=aux)
        # one refinement from a second start (robustness against local minima)
        alt = self._minimize(n_obs, mu_bounds,
                             x0=self._x0(mu0=float(np.clip(best.x[0] * 0.5 + 0.5,
                                                           *mu_bounds))),
                             aux=aux)
        if alt.fun < best.fun:
            best = alt
        mu_hat, nll_hat = float(best.x[0]), float(best.fun)
        q_target = z * z

        def q(mu_val, x_warm):
            r = self._minimize(n_obs, mu_bounds, fix_mu=mu_val, x0=x_warm,
                               aux=aux)
            return 2.0 * (float(r.fun) - nll_hat), r.x

        def endpoint(direction: int) -> float:
            step = 0.25
            mu_a, x_warm = mu_hat, best.x
            q_a = 0.0
            for _ in range(60):
                mu_b = mu_a + direction * step
                if mu_b <= mu_bounds[0]:
                    return mu_bounds[0]
                if mu_b >= mu_bounds[1]:
                    return mu_bounds[1]
                q_b, x_warm = q(mu_b, x_warm)
                if q_b >= q_target:
                    # bisect in [mu_a, mu_b]
                    lo, hi, q_hi_x = mu_a, mu_b, x_warm
                    for _ in range(30):
                        mid = 0.5 * (lo + hi)
                        q_m, q_hi_x = q(mid, q_hi_x)
                        if q_m >= q_target:
                            hi = mid
                        else:
                            lo = mid
                        if hi - lo < 1e-4:
                            break
                    return 0.5 * (lo + hi)
                mu_a, q_a = mu_b, q_b
                step *= 1.6
            return mu_bounds[0] if direction < 0 else mu_bounds[1]

        lo = endpoint(-1)
        hi = endpoint(+1)
        _mu, shape_alphas, norm_scales = self._unpack(best.x)
        return FitResult(mu_hat=mu_hat, nll_hat=nll_hat, interval=(lo, hi),
                         nuisance_hat={**shape_alphas, **norm_scales},
                         converged=bool(best.success))
