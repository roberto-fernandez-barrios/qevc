"""Extension figures: Fig. 3, Fig. 6, and the E16 supplementary diagnostic.

Same design method and validated palette as make_figures.py /
make_figures_campaign.py (palette re-validated this session: PASS; the
aqua/amber contrast WARN is relieved by direct labels). Form first, one axis,
thin marks, recessive grid, entity-stable colors.

Fig. 3  — sensor response by nuisance family + categorical weight-only
          blindness (E04 CRN records; the empirical face of the
          unidentifiability proposition).
Fig. 6  — label economics: (A) active-vs-uniform paired n* ratio ECDF (E07,
          primary negative); (B) n* efficiency vs the Wald information floor
          by margin bucket (E06_nstar_efficiency).
Fig. S16 — kernel estimation diagnostics per shot budget (E16 per-config):
          Frobenius error vs 1/sqrt(shots), effective-rank inflation,
          reference movement |Delta M_S|.

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

THEME = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # fixed order (validated)
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e8e7e4"

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


# ---- Fig. 3 — Sensor response by family; weight-only blindness -------------
FAMILIES = [
    ("tes",     "TES (4)",            lambda e: e.startswith("tes=")),
    ("jes",     "JES (4)",            lambda e: e.startswith("jes=")),
    ("soft_met", "soft-MET (12)",     lambda e: e.startswith("soft_met=")),
    ("combo",   "combos (8)",         lambda e: e.startswith("combo")),
    ("ttbar",   "ttbar-scale (4)",    lambda e: e.startswith("ttbar_scale=")),
    ("diboson", "diboson-scale (4)",  lambda e: e.startswith("diboson_scale=")),
    ("bkg",     "bkg-scale (4)",      lambda e: e.startswith("bkg_scale=")),
]
WEIGHT_ONLY = {"ttbar", "diboson", "bkg"}


def fig3() -> None:
    """x = ΔMMD² relative to the SAME CRN draw's nominal value — the quantity
    with meaning under common random numbers. Weight-only environments are
    byte-identical to nominal per draw (verified in the table), so their
    ΔMMD² is exactly zero: the empirical face of the unidentifiability
    proposition."""
    d = load("E04_geom_failure")
    records = d["records"]
    envs = sorted({r["env"] for r in records} - {"nominal"})
    draws = sorted({r["draw"] for r in records})

    idx = {(r["env"], r["kernel"], r["draw"]): r["mmd2"] for r in records}

    def delta_mean(env: str, kernel: str) -> float:
        ds = [idx[(env, kernel, dr)] - idx[("nominal", kernel, dr)]
              for dr in draws]
        return float(np.mean(ds)) * 1e4

    def floor_std(kernel: str) -> float:
        """Across-draw std of ΔMMD² pooled over shape-level envs."""
        stds = []
        for e in envs:
            if any(e.startswith(p) for p in
                   ("ttbar_scale", "diboson_scale", "bkg_scale")):
                continue
            ds = [idx[(e, kernel, dr)] - idx[("nominal", kernel, dr)]
                  for dr in draws]
            stds.append(np.std(ds))
        return float(np.mean(stds)) * 1e4

    sensors = [("quantum", THEME[0], "quantum MMD$^2$", +0.16),
               ("rbf8", THEME[2], "matched-rbf8 MMD$^2$", -0.16)]
    floor = max(floor_std("quantum"), floor_std("rbf8"))

    y = np.arange(len(FAMILIES))[::-1]
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    ax.axvspan(-floor, floor, color=GRID, alpha=0.75, zorder=1)
    for kernel, color, label, off in sensors:
        for (fam, _lab, pred), yy in zip(FAMILIES, y):
            xs = [delta_mean(e, kernel) for e in envs if pred(e)]
            ax.scatter(xs, np.full(len(xs), yy + off), s=30, color=color,
                       alpha=0.9, edgecolors="white", linewidths=0.8,
                       zorder=3, label=label if yy == y[0] else None)
    ax.set_yticks(y)
    ax.set_yticklabels([lab for _f, lab, _p in FAMILIES])
    for (fam, _lab, _p), yy in zip(FAMILIES, y):
        if fam in WEIGHT_ONLY:
            ax.axhspan(yy - 0.44, yy + 0.44, color="#f6f5f2", zorder=0)
    xmax = ax.get_xlim()[1]
    ax.text(xmax * 0.97, y[5],
            "weight-only: $\\Delta$MMD$^2$ = 0 exactly,\n"
            "every environment, every draw\n(unidentifiability proposition)",
            ha="right", va="center", fontsize=8, color=INK2, style="italic")
    ax.annotate("CRN draw noise ($\\pm 1\\sigma$)",
                (floor, y[0] + 0.55), fontsize=7.5, color=MUTED,
                ha="left", va="center", xytext=(6, 0),
                textcoords="offset points")
    ax.set_xlabel(r"$\Delta$MMD$^2$ vs same-draw nominal "
                  r"($\times 10^{-4}$, label-free, mean of 3 CRN draws)")
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.set_ylim(-0.7, len(FAMILIES) - 0.3 + 0.6)
    ax.set_title("Label-free sensor response by nuisance family: weight-only "
                 "shifts are exactly invisible; shape-level response grows "
                 "with severity", fontsize=10)
    save(fig, "fig3_family_blindness")


# ---- Fig. 6 — Label economics: active acquisition + information floor ------
def fig6() -> None:
    e07 = load("E07_active")
    eff = load("E06_nstar_efficiency")

    ratios = []
    for env in e07["environments"].values():
        for cell in env["models"].values():
            st = cell["strategies"]
            for delta in st["uniform"]:
                nu = st["uniform"][delta]["n_star_q50"]
                na = st["uncertainty_mix"][delta]["n_star_q50"]
                if nu and na:
                    ratios.append(na / nu)
    ratios = np.sort(np.array(ratios))
    med = float(np.median(ratios))
    frac_better = float(np.mean(ratios < 1.0))

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.0))

    ax = axes[0]
    ecdf = np.arange(1, len(ratios) + 1) / len(ratios)
    ax.step(ratios, ecdf, where="post", color=THEME[0], lw=2.0, zorder=3)
    ax.axvline(1.0, color=MUTED, lw=1.0, ls="--", zorder=2)
    ax.axhline(0.5, color=GRID, lw=0.8, zorder=1)
    ax.plot([med], [0.5], "o", ms=7, color=THEME[0], zorder=4)
    ax.annotate(f"median {med:.2f}", (med, 0.5), textcoords="offset points",
                xytext=(8, -12), fontsize=8, color=INK2)
    ax.annotate(f"active better in {frac_better:.0%}", (1.0, 0.06),
                textcoords="offset points", xytext=(-6, 0), fontsize=8,
                color=INK2, ha="right")
    ax.set_xlabel(r"paired $n^*$ ratio active / uniform "
                  f"({len(ratios)} jointly resolved cells)")
    ax.set_ylabel("ECDF")
    ax.set_xlim(0.3, 4.0)
    ax.set_title("Active acquisition loses to uniform (E07)", fontsize=9)

    ax = axes[1]
    buckets = [("[0.01, 0.02)", "0.01–0.02"), ("[0.02, 0.04)", "0.02–0.04"),
               ("[0.04, 0.08)", "0.04–0.08"), (">=0.08", "$\\geq$0.08")]
    x = np.arange(len(buckets))
    q50 = [eff["by_margin_bucket"][k]["ratio_q50"] for k, _ in buckets]
    q25 = [eff["by_margin_bucket"][k]["ratio_q25"] for k, _ in buckets]
    q75 = [eff["by_margin_bucket"][k]["ratio_q75"] for k, _ in buckets]
    ax.errorbar(x, q50, yerr=[np.subtract(q50, q25), np.subtract(q75, q50)],
                fmt="o", ms=7, color=THEME[0], ecolor=THEME[0], elinewidth=1.6,
                capsize=3, zorder=3)
    ax.axhline(1.0, color=MUTED, lw=1.0, ls="--", zorder=2)
    ax.text(len(buckets) - 0.55, 1.06, "Wald information floor", fontsize=8,
            color=INK2, ha="right")
    for xi, v in zip(x, q50):
        ax.annotate(f"{v:.2f}", (xi, v), textcoords="offset points",
                    xytext=(8, 2), fontsize=8, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _k, lab in buckets])
    ax.set_xlabel("|claim margin| bucket")
    ax.set_ylabel(r"$n^*_{q50}\ /\ [\log(1/\alpha)/\mathrm{KL}]$")
    ax.set_ylim(0.8, 4.3)
    ax.set_title("Measured label cost vs information bound (E06)", fontsize=9)

    fig.suptitle("Label economics of certification: uniform sampling is "
                 "near-optimal; costs sit a small factor above the "
                 "information floor", fontsize=10, y=1.04)
    save(fig, "fig6_label_economics")


# ---- Fig. S16 — kernel estimation diagnostics (E16 per-config) -------------
def fig_s16() -> None:
    d = load("E16_quantum_uncertainty")
    pc = d["per_config"]
    shots_list = sorted({int(k.split("|")[0][5:]) for k in pc})

    def vals(shots: int, field) -> list[float]:
        out = []
        for k, v in pc.items():
            if int(k.split("|")[0][5:]) == shots:
                out.append(field(v))
        return out

    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.0))

    ax = axes[0]
    for s in shots_list:
        ys = vals(s, lambda v: v["kernel"]["frob_rel_err"] * 100)
        ax.scatter(np.full(len(ys), s), ys, s=22, color=THEME[0], alpha=0.85,
                   edgecolors="white", linewidths=0.7, zorder=3)
    anchor = float(np.mean(vals(128, lambda v: v["kernel"]["frob_rel_err"])))
    guide = [anchor * np.sqrt(128 / s) * 100 for s in shots_list]
    ax.plot(shots_list, guide, color=MUTED, lw=1.2, ls="--", zorder=2)
    ax.text(shots_list[1], guide[1] * 0.62, r"$1/\sqrt{\rm shots}$",
            fontsize=8, color=INK2, ha="left", va="top")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(shots_list)
    ax.set_xticklabels(shots_list)
    ax.minorticks_off()
    ax.set_xlabel("shots per circuit")
    ax.set_ylabel("Gram Frobenius rel. error (%)")
    ax.set_title("Estimation error", fontsize=9)

    ax = axes[1]
    exact = float(np.mean(vals(shots_list[0],
                               lambda v: v["kernel"]["eff_rank_exact"])))
    for s in shots_list:
        ys = vals(s, lambda v: v["kernel"]["eff_rank"])
        ax.scatter(np.full(len(ys), s), ys, s=22, color=THEME[0], alpha=0.85,
                   edgecolors="white", linewidths=0.7, zorder=3)
    ax.axhline(exact, color=MUTED, lw=1.2, ls="--", zorder=2)
    ax.text(shots_list[0], exact * 1.01, "exact-kernel rank", fontsize=8,
            color=INK2, va="bottom")
    ax.set_xscale("log", base=2)
    ax.set_xticks(shots_list)
    ax.set_xticklabels(shots_list)
    ax.minorticks_off()
    ax.set_xlabel("shots per circuit")
    ax.set_ylabel("effective rank")
    ax.set_title("Shot noise inflates rank", fontsize=9)

    ax = axes[2]
    series = [("m_s_shift_unw", THEME[0], "unweighted $M_S$"),
              ("m_s_shift_w", THEME[1], "weighted $M_S$")]
    for field, color, label in series:
        for i, s in enumerate(shots_list):
            ys = np.abs(vals(s, lambda v, f=field: v[f]))
            ax.scatter(np.full(len(ys), s) * (1.06 if color == THEME[1] else 1),
                       ys, s=22, color=color, alpha=0.85, edgecolors="white",
                       linewidths=0.7, zorder=3,
                       label=label if i == 0 else None)
    ax.set_xscale("log", base=2)
    ax.set_xticks(shots_list)
    ax.set_xticklabels(shots_list)
    ax.minorticks_off()
    ax.set_xlabel("shots per circuit")
    ax.set_ylabel(r"reference movement $|\Delta M_S|$")
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    ax.set_title("Recalibration moves the reference", fontsize=9)

    fig.suptitle("Quantum estimation diagnostics per noisy deployment "
                 "(30 configurations: 6 budgets × 5 kernel seeds)",
                 fontsize=10, y=1.04)
    save(fig, "figS16_estimation_diagnostics")


if __name__ == "__main__":
    fig3()
    fig6()
    fig_s16()
