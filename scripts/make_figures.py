"""Generate the paper's data figures from results JSONs (Figs. 2, 4, 5, 7, 8).

Design per the dataviz method: form first, entity-stable categorical colors
(validated palette), sequential ramp for magnitude buckets, one axis, thin
marks, recessive grid, direct labels. Fig. 1 (framework diagram) and Fig. 9
(claims-ledger table) are not charts and are produced in the manuscript.
Outputs: results/figures/*.pdf + *.png (300 dpi).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/figures"
OUT.mkdir(parents=True, exist_ok=True)

# Entity-stable categorical assignment (validated, light surface)
C = {"qksvc": "#2a78d6", "xgboost": "#eb6834", "rbf_svc": "#1baf7a",
     "fourth": "#eda100"}
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e8e7e4"
SEQ_BLUE = ["#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9, "axes.titlesize": 10, "figure.dpi": 120,
})


def save(fig, name: str) -> None:
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"saved {name}")


def load(name: str) -> dict:
    return json.loads((REPO / f"results/tables/{name}.json").read_text())


# ---- Fig. 2 — Replicated TES response (E02R) -------------------------------
def fig2() -> None:
    d = load("E02R_multiseed")["summary"]
    tes_x = [0.98, 0.99, 1.01, 1.02]
    fig, ax = plt.subplots(figsize=(4.4, 3.2))
    for key, color, label in (
        ("A:qksvc", C["qksvc"], "QK-SVC"),
        ("A:xgboost", C["xgboost"], "XGBoost"),
        ("A:rbf_svc", C["rbf_svc"], "RBF-SVC"),
    ):
        mu = [d[key]["delta_auc"][f"tes={t}"]["mean"] for t in tes_x]
        sd = [d[key]["delta_auc"][f"tes={t}"]["std"] for t in tes_x]
        ax.errorbar(tes_x, mu, yerr=sd, color=color, lw=2, marker="o",
                    ms=5, capsize=3, label=label)
        ax.annotate(label, (tes_x[-1], mu[-1]), xytext=(6, 0),
                    textcoords="offset points", color=INK, fontsize=8,
                    va="center")
    ax.axhline(0, color=MUTED, lw=0.8, ls="--")
    ax.axvline(1.0, color=GRID, lw=0.8)
    ax.set_xlabel("Tau energy scale (TES)")
    ax.set_ylabel(r"$\Delta$AUC vs nominal (mean $\pm$ s.d., 5 seeds)")
    ax.set_xlim(0.975, 1.033)
    ax.set_title("Replicated TES response (matched 2000-event models)")
    save(fig, "fig2_tes_replicated")


# ---- Fig. 4 — Geometry sensor vs multi-seed degradation (E04 v2) ----------
def fig4() -> None:
    e04 = load("E04_geom_failure")
    e02r = load("E02R_multiseed")["summary"]
    v2 = load("E04v2_geom_failure_multiseed")["analysis"]
    records = e04["records"]
    envs = sorted({r["env"] for r in records}
                  - {"nominal"})
    shift = [e for e in envs if not any(
        e.startswith(p) for p in ("ttbar_scale", "diboson_scale", "bkg_scale"))]

    def mmd(e):
        rows = [r["mmd2"] for r in records
                if r["env"] == e and r["kernel"] == "quantum"]
        return float(np.mean(rows))

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.1), sharex=True)
    for ax, target, color, label in (
        (axes[0], "A:qksvc", C["qksvc"], "QK-SVC"),
        (axes[1], "A:xgboost", C["xgboost"], "XGBoost"),
    ):
        x = np.array([mmd(e) for e in shift]) * 1e3
        y = np.array([abs(e02r[target]["delta_auc"][e]["mean"]) for e in shift])
        ax.scatter(x, y, s=26, color=color, alpha=0.85,
                   edgecolors="white", linewidths=1.2)
        rho = v2[f"quantum->{target}"]["mmd2_only_rho"]
        p = v2[f"quantum->{target}"]["mmd2_only_p"]
        ax.set_title(f"target: {label}   "
                     rf"$\rho_S$ = {rho:.2f} (p = {p:.4g})", fontsize=9)
        ax.set_xlabel(r"quantum-kernel MMD$^2$ ($\times 10^{-3}$, label-free)")
    axes[0].set_ylabel(r"|$\Delta$AUC| (5-seed mean)")
    fig.suptitle("Label-free geometry sensor vs replicated degradation "
                 "(28 feature-shift environments)", fontsize=10, y=1.02)
    save(fig, "fig4_geometry_sensor")


# ---- Fig. 5 — Certification landscape (E06) --------------------------------
def fig5() -> None:
    d = load("E06_nstar")
    buckets = [(0.0, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, 0.04),
               (0.04, 0.08), (0.08, 0.2)]
    budgets = [10, 20, 50, 100, 200, 500, 1000, 2000, 3000, 5000, 10000, 20000]
    cells: dict[int, list] = {i: [] for i in range(len(buckets))}
    for env in d["environments"].values():
        for m in env["models"].values():
            for c in m["claims"].values():
                mg = abs(c["margin"])
                for i, (lo, hi) in enumerate(buckets):
                    if lo <= mg < hi:
                        cells[i].append([c["resolved_frac_at_budget"][str(b)]
                                         for b in budgets])
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    for i, (lo, hi) in enumerate(buckets):
        if not cells[i]:
            continue
        mean = np.mean(cells[i], axis=0)
        ax.plot(budgets, mean, color=SEQ_BLUE[i], lw=2, marker="o", ms=4)
        ax.annotate(f"[{lo:g}, {hi:g})", (budgets[-1], mean[-1]),
                    xytext=(6, 0), textcoords="offset points",
                    color=INK, fontsize=7.5, va="center")
    ax.set_xscale("log")
    ax.set_xlabel("label budget n")
    ax.set_ylabel("fraction of claims resolved")
    ax.set_ylim(-0.03, 1.06)
    ax.set_title("Certification landscape by claim margin |M$_T$ − τ|")
    ax.text(0.02, 0.95, "darker = larger margin", transform=ax.transAxes,
            color=INK2, fontsize=7.5)
    save(fig, "fig5_certification_landscape")


# ---- Fig. 7 — Classifier metrics vs physics validity (E08, H5) ------------
def fig7() -> None:
    d = load("E08_physics")
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    order = [("A:qksvc", "qksvc", "QK-SVC"), ("A:xgboost", "xgboost", "XGBoost"),
             ("A:rbf_svc", "rbf_svc", "RBF-SVC"), ("B:xgboost", "fourth",
                                                   "XGBoost (110k)")]
    for key, ck, label in order:
        xs, ys = [], []
        for env, v in d["environments"].items():
            if env == "nominal":
                continue
            m = v["models"][key]
            xs.append(max(abs(m["delta_auc"]), 2e-5))
            ys.append(m["coverage_mean"])
        ax.scatter(xs, ys, s=22, color=C[ck], alpha=0.85, label=label,
                   edgecolors="white", linewidths=1.0)
    ax.axhline(0.6827, color=MUTED, lw=1.0, ls="--")
    ax.text(1.3e-5, 0.695, "nominal coverage", color=INK2, fontsize=7.5)
    ax.axvspan(1e-5, 5e-3, ymin=0, ymax=0.633 / 1.05, color="#f4e8e7",
               zorder=0)
    ax.text(2.4e-5, 0.06, "classifier looks fine,\nphysics broken (H5)",
            color="#a03432", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel(r"|$\Delta$AUC| vs nominal (log)")
    ax.set_ylabel(r"mean coverage of the 68.27% $\mu$ interval")
    ax.set_ylim(-0.05, 1.0)
    ax.legend(loc="center right", fontsize=7.5, frameon=False)
    ax.set_title("Classifier health does not protect inference validity")
    save(fig, "fig7_h5_decoupling")


# ---- Fig. 8 — Finite shots and hardware (E09 + E10) ------------------------
def fig8() -> None:
    e09 = load("E09_shots")
    e10 = load("E10_hardware")
    shots = sorted({int(k.split("_")[0][5:]) for k in e09["configs"]})
    frob = {s: [v["kernel"]["frob_rel_err"]
                for k, v in e09["configs"].items()
                if k.startswith(f"shots{s}_")] for s in shots}
    auc = {s: [v["envs"]["nominal"]["auc"]
               for k, v in e09["configs"].items()
               if k.startswith(f"shots{s}_")] for s in shots}
    hw_frob = e10["kernels"]["hardware"]["stats_vs_ideal"]["frob_rel_err"]
    local_frob = [v["frob_rel_err"] for v in
                  e10["kernels"]["shots_local"]["stats_vs_ideal"]]
    local_mean = float(np.mean(local_frob))
    exact_auc = e09["exact"]["envs"]["nominal"]["auc"]

    fig, axes = plt.subplots(2, 1, figsize=(4.0, 5.2), sharex=True,
                             height_ratios=[1.15, 1.0])
    ax = axes[0]
    m = [np.mean(frob[s]) for s in shots]
    ax.plot(shots, m, color=C["qksvc"], lw=2, marker="o", ms=5,
            label="E09 shot-only ($n=2000$)")
    ax.plot(shots, m[0] * np.sqrt(shots[0] / np.array(shots)), color=MUTED,
            lw=1, ls=":", label=r"$1/\sqrt{\mathrm{shots}}$")
    ax.scatter([2048], [local_mean], color=C["rbf_svc"], marker="D", s=42,
               zorder=4, label=f"E10 local shots ($n=32$): {local_mean:.3f}")
    ax.scatter([2048], [hw_frob], color=C["xgboost"], marker="s", s=46,
               zorder=4, label=f"E10 hardware ($n=32$): {hw_frob:.3f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.minorticks_off()
    ax.set_ylabel("kernel error (rel. Frobenius)")
    ax.set_title("Kernel error (E09 and local E10 scales differ)", fontsize=9.5)
    ax.legend(frameon=False, fontsize=7.2, loc="lower left")

    ax = axes[1]
    mu = [np.mean(auc[s]) for s in shots]
    lo = [np.min(auc[s]) for s in shots]
    hi = [np.max(auc[s]) for s in shots]
    ax.fill_between(shots, lo, hi, color=C["qksvc"], alpha=0.18, lw=0)
    ax.plot(shots, mu, color=C["qksvc"], lw=2, marker="o", ms=5)
    ax.axhline(exact_auc, color=MUTED, lw=1.0, ls="--")
    ax.text(shots[0], exact_auc + 0.002, f"exact kernel: {exact_auc:.3f}",
            color=INK2, fontsize=7.5)
    ax.set_xscale("log")
    ax.minorticks_off()
    ax.set_xlabel("shots per kernel entry")
    ax.set_ylabel("nominal test AUC")
    ax.set_title("E09 downstream AUC ($n=2000$)", fontsize=9.5)
    ax.set_xticks(shots)
    ax.set_xticklabels(["128", "256", "512", "1k", "2k", "4k"],
                       rotation=28, ha="right")
    fig.suptitle("Finite-shot estimation and the E10 hardware diagnostic",
                 fontsize=10.5, y=0.995)
    fig.subplots_adjust(hspace=0.28)
    save(fig, "fig8_shots_hardware")


if __name__ == "__main__":
    fig2()
    fig4()
    fig5()
    fig7()
    fig8()
    print("all figures done ->", OUT)
