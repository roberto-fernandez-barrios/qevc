"""Classical baseline suite (spec §9) with comparable tuning budgets.

Registry of model builders + a seeded random-search tuner. Scale-sensitive
models (SVMs, MLP) get a StandardScaler inside their pipeline, fitted on the
training fold only. MLP trains on weight-proportional resampled data (D-012).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from lightgbm import LGBMClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC
from xgboost import XGBClassifier

from qevc.metrics.classifier import weighted_auc
from qevc.models.common import weighted_resample_indices


class SkModel:
    """Uniform wrapper: fit(X, y, w) + scores(X)."""

    def __init__(self, estimator, resample_fit: bool = False, seed: int = 0):
        self.est = estimator
        self.resample_fit = resample_fit
        self.seed = seed

    def fit(self, X, y, sample_weight=None):
        if self.resample_fit and sample_weight is not None:
            idx = weighted_resample_indices(sample_weight, len(y), self.seed)
            self.est.fit(np.asarray(X)[idx], np.asarray(y)[idx])
        elif sample_weight is not None:
            fit_kwargs = {}
            step = self.est.steps[-1][0] if isinstance(self.est, Pipeline) else None
            key = f"{step}__sample_weight" if step else "sample_weight"
            fit_kwargs[key] = sample_weight
            self.est.fit(X, y, **fit_kwargs)
        else:
            self.est.fit(X, y)
        return self

    def scores(self, X) -> np.ndarray:
        if hasattr(self.est, "predict_proba"):
            return self.est.predict_proba(X)[:, 1]
        return self.est.decision_function(X)


def _sample_params(rng: np.random.Generator, space: dict[str, list]) -> dict:
    return {k: v[rng.integers(len(v))] for k, v in space.items()}


# name -> (builder(params, seed) -> SkModel, search space)
REGISTRY: dict[str, tuple[Callable[[dict, int], SkModel], dict[str, list]]] = {
    "linear_svc": (
        lambda p, s: SkModel(Pipeline([
            ("sc", StandardScaler()),
            ("clf", LinearSVC(C=p["C"], max_iter=20_000)),
        ])),
        {"C": [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]},
    ),
    "rbf_svc": (
        lambda p, s: SkModel(Pipeline([
            ("sc", StandardScaler()),
            ("clf", SVC(kernel="rbf", C=p["C"], gamma=p["gamma"], cache_size=500)),
        ])),
        {"C": [0.1, 0.3, 1.0, 3.0, 10.0, 30.0],
         "gamma": ["scale", 0.01, 0.03, 0.1, 0.3]},
    ),
    "xgboost": (
        lambda p, s: SkModel(XGBClassifier(
            n_estimators=p["n_estimators"], max_depth=p["max_depth"],
            learning_rate=p["learning_rate"], subsample=p["subsample"],
            colsample_bytree=p["colsample_bytree"], reg_lambda=p["reg_lambda"],
            tree_method="hist", n_jobs=-1, random_state=s, eval_metric="logloss",
        )),
        {"n_estimators": [200, 400, 800], "max_depth": [4, 6, 8],
         "learning_rate": [0.03, 0.05, 0.1, 0.2], "subsample": [0.7, 0.9, 1.0],
         "colsample_bytree": [0.7, 0.9, 1.0], "reg_lambda": [0.5, 1.0, 3.0]},
    ),
    "lightgbm": (
        lambda p, s: SkModel(LGBMClassifier(
            n_estimators=p["n_estimators"], num_leaves=p["num_leaves"],
            learning_rate=p["learning_rate"], subsample=p["subsample"],
            colsample_bytree=p["colsample_bytree"], reg_lambda=p["reg_lambda"],
            n_jobs=-1, random_state=s, verbose=-1,
        )),
        {"n_estimators": [200, 400, 800], "num_leaves": [15, 31, 63],
         "learning_rate": [0.03, 0.05, 0.1, 0.2], "subsample": [0.7, 0.9, 1.0],
         "colsample_bytree": [0.7, 0.9, 1.0], "reg_lambda": [0.5, 1.0, 3.0]},
    ),
    "mlp": (
        lambda p, s: SkModel(Pipeline([
            ("sc", StandardScaler()),
            ("clf", MLPClassifier(
                hidden_layer_sizes=p["hidden"], alpha=p["alpha"],
                learning_rate_init=p["lr"], max_iter=300,
                early_stopping=True, n_iter_no_change=15, random_state=s,
            )),
        ]), resample_fit=True, seed=s),
        {"hidden": [(32,), (64, 32), (128, 64)],
         "alpha": [1e-5, 1e-4, 1e-3, 1e-2], "lr": [1e-3, 3e-3, 1e-2]},
    ),
}


@dataclass
class TuneResult:
    name: str
    best_params: dict[str, Any]
    best_cv_auc: float
    trials: list[dict]


def tune(
    name: str, X, y, w_train, w_eval,
    n_configs: int, cv_folds: int, seed: int,
    builder_override=None, space_override=None,
) -> TuneResult:
    """Seeded random search; selection metric = physics-weighted CV AUC.

    ``w_train``: class-balanced training weights (D-012); ``w_eval``: raw
    physical weights used for fold scoring. Identical budget semantics for
    every model family, quantum included (via the override hooks).
    """
    builder, space = REGISTRY[name] if builder_override is None else (
        builder_override, space_override)
    X, y = np.asarray(X), np.asarray(y)
    w_train, w_eval = np.asarray(w_train), np.asarray(w_eval)
    rng = np.random.default_rng(seed)
    configs, seen = [], set()
    while len(configs) < n_configs:
        p = _sample_params(rng, space)
        key = tuple(sorted((k, str(v)) for k, v in p.items()))
        if key not in seen or len(seen) >= np.prod([len(v) for v in space.values()]):
            seen.add(key)
            configs.append(p)

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    trials = []
    for p in configs:
        aucs = []
        for tr, va in skf.split(X, y):
            model = builder(p, seed)
            model.fit(X[tr], y[tr], sample_weight=w_train[tr])
            aucs.append(weighted_auc(y[va], model.scores(X[va]), w_eval[va]))
        trials.append({"params": p, "cv_auc": float(np.mean(aucs)),
                       "cv_auc_std": float(np.std(aucs))})
    best = max(trials, key=lambda t: t["cv_auc"])
    return TuneResult(name, best["params"], best["cv_auc"], trials)


def build(name: str, params: dict, seed: int) -> SkModel:
    return REGISTRY[name][0](params, seed)
