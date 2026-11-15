"""Paper figure: HHL circuit depth and transpile time vs optimization level.

Two panels from data/per_step.csv (shots 0 runs): the transpiled depth at
Newton step 0, and the transpile time per Newton step as the mean with a
min-to-max bar over the run's steps. A ring marks each qiskit version's
default level (in the legend). Writes plots/depth_transpile_vs_level.{pdf,png}.

Usage: ~/.venvs/tooling/bin/python plot_paper_figure.py
"""
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "per_step.csv")
OUT = os.path.join(HERE, "plots", "depth_transpile_vs_level")

# dataviz reference palette slots 1-2, validated on a white surface
SERIES = {
    "nov2025": {"color": "#2a78d6", "marker": "o", "default": 1},
    "nov2026": {"color": "#eb6834", "marker": "s", "default": 2},
}
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
DODGE = {"nov2025": -0.08, "nov2026": 0.08}


def style() -> None:
    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.family": "sans-serif", "font.size": 8.5,
        "axes.titlesize": 9.5, "axes.titlelocation": "left",
        "legend.frameon": False, "pdf.fonttype": 42,
    })


def ring_default(ax, x: float, y: float, color: str) -> None:
    """Open ring around the default-level point."""
    ax.plot(x, y, marker="o", ms=13, mfc="none", mec=color, mew=1.2,
            zorder=4)


def main() -> None:
    style()
    df = pd.read_csv(DATA)
    df = df[df.shots == 0]
    fig, (ax_d, ax_t) = plt.subplots(1, 2, figsize=(6.5, 2.7))

    for cb, spec in SERIES.items():
        g = df[df.codebase == cb]
        name = f"qiskit {g.qiskit.iloc[0]}"
        c, m = spec["color"], spec["marker"]

        depth = g[g.step == 0].set_index("opt_level").circ_depth.sort_index()
        x = depth.index.to_numpy() + DODGE[cb]
        ax_d.plot(x, depth.to_numpy() / 1e3, color=c, lw=2, marker=m, ms=6,
                  mec="white", mew=1, label=name, zorder=3)
        lvl = spec["default"]
        ring_default(ax_d, lvl + DODGE[cb], depth[lvl] / 1e3, c)

        t = g.groupby("opt_level").circ_transpile_s
        mean, lo, hi = t.mean(), t.min(), t.max()
        x = mean.index.to_numpy() + DODGE[cb]
        ax_t.errorbar(x, mean, yerr=[mean - lo, hi - mean], color=c, lw=2,
                      marker=m, ms=6, mec="white", mew=1, elinewidth=1.2,
                      capsize=0, zorder=3)
        ring_default(ax_t, lvl + DODGE[cb], mean[lvl], c)

        # direct labels at the right end of the depth lines
        ax_d.annotate(name, (3 + DODGE[cb], depth[3] / 1e3),
                      xytext=(8, 0), textcoords="offset points", va="center",
                      fontsize=8, color=INK_2)

    ax_d.set_title("Circuit depth at Newton step 0")
    ax_d.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}k"))
    ax_d.set_ylim(570, 725)
    ax_t.set_title("Transpile time per Newton step (s)")
    ax_t.set_yscale("log")
    ax_t.set_ylim(0.1, 150)
    ax_t.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    for ax in (ax_d, ax_t):
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlim(-0.4, 3.9 if ax is ax_d else 3.4)
        ax.set_xlabel("Transpiler optimization level")
    handles, labels = ax_d.get_legend_handles_labels()
    handles.append(Line2D([], [], ls="none", marker="o", ms=11, mfc="none",
                          mec=INK_2, mew=1.2))
    labels.append("default level")
    fig.legend(handles, labels, loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.03), fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=2.5)
    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT}.{ext}", dpi=200, bbox_inches="tight")
    print(f"{OUT}.pdf")


if __name__ == "__main__":
    main()
