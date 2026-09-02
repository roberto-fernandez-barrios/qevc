"""Fig. 1 — framework diagram (boxes + arrows; not a data chart).

Verdict colors use the status palette (good/critical) — reserved semantics —
and neutral ink for UNRESOLVED (abstention is not an error state).
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results/figures"

BLUE, INK, INK2, MUTED = "#2a78d6", "#0b0b0b", "#52514e", "#898781"
GOOD, CRIT = "#0ca30c", "#d03b3b"
FILL, FILL_Q = "#f3f2ef", "#e4eefb"


def box(ax, x, y, w, h, text, fc=FILL, ec=MUTED, tc=INK, fs=7.8, lw=1.1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, linespacing=1.35)


def arrow(ax, x1, y1, x2, y2, color=MUTED, lw=1.4, style="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 color=color, lw=lw, mutation_scale=11,
                                 shrinkA=2, shrinkB=2))


fig, ax = plt.subplots(figsize=(10.2, 4.6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 46)
ax.axis("off")

# ---- top row: the deployment chain ----------------------------------------
box(ax, 1, 30, 15, 11, "collider\nsystematics\n$\\theta$ (TES, JES, …)")
box(ax, 21, 30, 15, 11, "shifted data\n$D_\\theta$\n(selection migration)")
box(ax, 41, 30, 16, 11, "representation\nquantum kernel\n$K_Q(x,x')$", fc=FILL_Q, ec=BLUE)
box(ax, 62, 30, 15, 11, "frozen classifier\n$f$ + threshold\n(no retuning)")
box(ax, 82, 30, 17, 11, "physics inference\n$\\hat\\mu$, intervals,\ncoverage")
for x1, x2 in ((16, 21), (36, 41), (57, 62), (77, 82)):
    arrow(ax, x1, 35.5, x2, 35.5)

# ---- geometry sensor (label-free, veto-only) ------------------------------
box(ax, 41, 15, 16, 8, "geometry sensor\nMMD$^2$ shift alarm\n(label-free, I1)",
    fc=FILL_Q, ec=BLUE, fs=7.2)
arrow(ax, 49, 30, 49, 23, color=BLUE)

# ---- auditor ---------------------------------------------------------------
box(ax, 62, 12, 15, 13,
    "conditional auditor\nclaim $M_T \\geq \\tau$\nanytime-valid CS\n(fail-closed)",
    fs=7.2)
arrow(ax, 69.5, 30, 69.5, 25)
arrow(ax, 57, 19, 62, 19, color=BLUE)  # sensor veto path
ax.text(59.4, 20.2, "veto\nonly", ha="center", color=BLUE, fontsize=6.6)

# information sets feeding the auditor
box(ax, 59.5, 1.0, 20, 7.5,
    "information set\nI0: source; I1: $X\\mid N=n$\nI2: + queried labels; I3: + rates", fs=6.6)
arrow(ax, 69.5, 8.5, 69.5, 12)

# ---- verdicts --------------------------------------------------------------
box(ax, 82, 19, 17, 5.4, "SUPPORTED  (LCB $\\geq \\tau$)", fc="#e7f4e7",
    ec=GOOD, tc=GOOD, fs=7.2)
box(ax, 82, 12.6, 17, 5.4, "REFUTED  (UCB $< \\tau$)", fc="#fbe9e9",
    ec=CRIT, tc=CRIT, fs=7.2)
box(ax, 82, 6.2, 17, 5.4, "UNRESOLVED  (abstain)", fc=FILL, ec=MUTED,
    tc=INK2, fs=7.2)
for y in (21.7, 15.3, 8.9):
    arrow(ax, 77, 18.5, 82, y)

ax.text(1, 44.2, "Deployment happens under $\\theta \\neq 0$; "
                 "validation happened at $\\theta = 0$.",
        color=INK2, fontsize=8.2)
ax.text(1, 2.5, "Heuristics (geometry) can only veto; labeled target\n"
                "evidence (I2) can certify in the simulated audit — guarantees are per-claim,\n"
                "time-uniform, and fail closed.",
        color=INK2, fontsize=7.6, va="bottom")

fig.savefig(OUT / "fig1_framework.pdf", bbox_inches="tight")
fig.savefig(OUT / "fig1_framework.png", bbox_inches="tight", dpi=300)
print("saved fig1_framework")
