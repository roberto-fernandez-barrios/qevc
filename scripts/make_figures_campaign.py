"""Campaign figures from the E04v3/E15/E16 tables (Figs. 4b, 7b, 8b).

Same design method and validated palette as make_figures.py: form first,
entity-stable categorical colors in fixed theme order, sequential ramp for
ordered magnitude buckets, one axis, thin marks, recessive grid, direct
labels (the aqua slot's contrast WARN is relieved by direct labels).
Outputs: results/figures/*.pdf + *.png (300 dpi).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/figures"
OUT.mkdir(parents=True, exist_ok=True)

THEME = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # fixed order (validated)
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e8e7e4"
SEQ_BLUE = ["#9ec5f4", "#3987e5", "#1c5cab"]           # near -> far (|margin|)

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


# ---- Fig. 4b — Out-of-grid sensor generalization (E04v3) -------------------
def fig4b() -> None:
    d = load("E04v3_out_of_grid")["worlds"]
    fams = ["tes", "jes", "soft_met", "prior"]
    fam_labels = {"tes": "TES (7)", "jes": "JES (7)", "soft_met": "soft-MET (10)",
                  "prior": "prior draws (24)", "pooled": "POOLED (48)"}
    sensors = [("quantum->A:qksvc", THEME[0], "quantum MMD²"),
               ("rbf8->A:rbf_svc_8f", THEME[2], "matched-rbf8 MMD²")]
    worlds = [("s101", "primary world (seed-101 deployment)"),
              ("e12", "confirmatory world (E12 deployment)")]
    rows = fams + ["pooled"]
    y = np.arange(len(rows))[::-1]

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0), sharey=True, sharex=True)
    for ax, (w, wtitle) in zip(axes, worlds):
        a = d[w]["analysis"]
        for si, (key, color, label) in enumerate(sensors):
            off = 0.16 if si == 0 else -0.16
            vals = [a["per_family"][key][f]["rho"] for f in fams]
            vals.append(a["pooled"][key]["rho"])
            ax.scatter(vals, y + off, s=42, color=color, zorder=3,
                       label=label if w == "s101" else None)
            for v, yy in zip(vals, y + off):
                ax.plot([0, v], [yy, yy], color=color, lw=1.2, alpha=0.45,
                        zorder=2)
        ax.axvline(0, color=MUTED, lw=0.9)
        ax.set_yticks(y)
        ax.set_yticklabels([fam_labels[r] for r in rows])
        ax.set_xlabel(r"out-of-grid Spearman $\rho$ (sensor vs |$\Delta$AUC|)")
        ax.set_title(wtitle, fontsize=9)
        ax.set_xlim(-0.35, 1.05)
    axes[0].legend(loc="lower right", frameon=False, fontsize=8)
    fig.suptitle("Frozen label-free sensors on 48 never-seen nuisance "
                 "configurations per world (own-model targets)", y=1.04,
                 fontsize=10)
    save(fig, "fig4b_out_of_grid_sensor")


# ---- Fig. 7b — What restores physics validity, and what defeats it (E15) ---
def fig7b() -> None:
    cells = load("E15_inference")["coverage_summary"]

    def fam(e):
        for f in ("tes", "jes", "soft_met", "ttbar_scale", "diboson_scale",
                  "bkg_scale", "combo"):
            if e.startswith(f):
                return f
        return "nominal"

    agg = defaultdict(lambda: {"L1": [], "L2": [], "L3": []})
    for c in cells:
        f = fam(c["env"])
        for lv in ("L1", "L2", "L3"):
            if c[lv] is not None:
                agg[f][lv].append(c[lv])
    rows = ["nominal", "tes", "jes", "ttbar_scale", "diboson_scale",
            "bkg_scale", "soft_met", "combo"]
    labels = {"nominal": "nominal", "tes": "TES", "jes": "JES",
              "ttbar_scale": "ttbar norm", "diboson_scale": "diboson norm",
              "bkg_scale": "bkg norm", "soft_met": "soft-MET (stochastic)",
              "combo": "combinations"}
    levels = [("L1", THEME[0], "L1 deployment-blind counting"),
              ("L2", THEME[1], "L2 full profile likelihood"),
              ("L3", THEME[2], "L3 profile minus shifted family")]
    y = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.axvline(0.6827, color=MUTED, lw=1.0, ls="--", zorder=1)
    ax.annotate("nominal 0.683", (0.6827, len(rows) - 0.45), color=MUTED,
                fontsize=7.5, ha="center", va="bottom")
    for li, (lv, color, label) in enumerate(levels):
        off = (1 - li) * 0.22
        vals = [float(np.mean(agg[r][lv])) if agg[r][lv] else np.nan
                for r in rows]
        ax.scatter(vals, y + off, s=40, color=color, zorder=3, label=label)
        for v, yy in zip(vals, y + off):
            ax.plot([0, v], [yy, yy], color=color, lw=1.2, alpha=0.4, zorder=2)
    ax.set_yticks(y)
    ax.set_yticklabels([labels[r] for r in rows])
    ax.set_xlabel("mean empirical coverage of the 68.27% interval")
    ax.set_xlim(0, 0.82)
    ax.set_title("Coverage by nuisance family and inference level\n"
                 "(3 calibration-gated models; B:xgboost gate-excluded)",
                 fontsize=9.5)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    save(fig, "fig7b_inference_levels")


# ---- Fig. 8b — When does estimation noise change a verdict? (E16) ----------
def fig8b() -> None:
    agg = load("E16_quantum_uncertainty")["aggregate_by_shots"]
    shots = [128, 256, 512, 1024, 2048, 4096]
    strata = [("near", SEQ_BLUE[0], "near (|m| < 0.01)"),
              ("moderate", SEQ_BLUE[1], "moderate (0.01–0.04)"),
              ("far", SEQ_BLUE[2], "far (|m| ≥ 0.04)")]
    panels = [("flip_rate_fixed_tau_mean",
               "fixed-reference claims (ideal deployment's τ)"),
              ("flip_rate_own_tau_mean",
               "deployment-relative claims (own refrozen τ)")]

    dodge = {"near": -9, "moderate": 7, "far": 0}   # end-label collision fix
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0), sharey=True)
    for ax, (key, title) in zip(axes, panels):
        for st, color, label in strata:
            vals = [agg[str(s)].get(st, {}).get(key, np.nan) for s in shots]
            ax.plot(shots, vals, color=color, lw=2, marker="o", ms=4.5)
            ax.annotate(label.split(" (")[0], (shots[-1], vals[-1]),
                        xytext=(6, dodge[st]), textcoords="offset points",
                        color=INK, fontsize=8, va="center")
        ax.set_xscale("log", base=2)
        ax.set_xticks(shots)
        ax.set_xticklabels([str(s) for s in shots], fontsize=8)
        ax.set_xlabel("shots per kernel entry")
        ax.set_title(title, fontsize=9)
        ax.set_xlim(110, 9000)
    axes[0].set_ylabel("verdict flip rate vs C_ideal")
    axes[0].set_ylim(-0.03, 0.9)
    handles = [plt.Line2D([], [], color=c, lw=2, marker="o", ms=4.5)
               for _, c, _ in strata]
    axes[0].legend(handles, [lbl for _, _, lbl in strata], loc="upper right",
                   frameon=False, fontsize=8)
    fig.suptitle("Quantum estimation noise and claim verdicts, by ideal-margin "
                 "stratum (5 kernel seeds/point; false certification ≤ α "
                 "in every cell)", y=1.05, fontsize=10)
    save(fig, "fig8b_estimation_noise_verdicts")


if __name__ == "__main__":
    fig4b()
    fig7b()
    fig8b()
    print("campaign figures complete")
