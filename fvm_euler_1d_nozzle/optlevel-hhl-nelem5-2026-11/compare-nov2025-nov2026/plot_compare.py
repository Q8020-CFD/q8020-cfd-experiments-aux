"""Plot the nov2025 vs nov2026 optimization-level comparison.

Reads only data/per_case.csv and data/per_step.csv (build_compare_data.py
writes them), so plots can be restyled without the raw results. Writes
plots/*.png next to this file. Edit the settings block to change what is shown.

Usage: ~/.venvs/tooling/bin/python plot_compare.py
"""
import os

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PLOTS = os.path.join(HERE, "plots")

# ---- settings -------------------------------------------------------------
CIRCUIT_SHOTS = 0          # which runs' circuits to plot (0 or 150000)
FIDELITY_SUMMARY = "fidelity_mean_excl_last"   # per_case column, or
# "fidelity_mean" / "fidelity_last"; excl_last drops the converged final
# statevector step, where the pad (pad_eps 1e-8) swamps the right-hand side
DPI = 150
# dataviz reference palette: categorical slots 1-2, ordinal blue ramp for level
CODEBASE_COLOR = {"nov2025": "#2a78d6", "nov2026": "#eb6834"}
LEVEL_COLOR = {0: "#86b6ef", 1: "#3987e5", 2: "#1c5cab", 3: "#0d366b"}
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
LINE_W, MARKER_PT = 1.4, 5
# small x offset per codebase so coinciding lines stay visible
DODGE = {"nov2025": -0.05, "nov2026": 0.05}
# ---------------------------------------------------------------------------


def style() -> None:
    matplotlib.use("Agg")
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.family": "sans-serif", "font.size": 9,
        "axes.titlesize": 10, "legend.frameon": False,
    })


def label(cb: str, cases: pd.DataFrame) -> str:
    q = cases.loc[cases.codebase == cb, "qiskit"].iloc[0]
    return f"{cb} (qiskit {q})"


def end_labels(ax, ends: dict, x: float = 3.05, size: float = 8) -> None:
    """Direct labels at the line ends: one shared label when the ends
    coincide on screen, pushed apart when they would overlap. Call after
    the axis scale is set."""
    ax.get_ylim()  # settle autoscaled limits before measuring
    px = {k: ax.transData.transform((x, v))[1] for k, v in ends.items()}
    lo, hi = min(px, key=px.get), max(px, key=px.get)
    gap, need = px[hi] - px[lo], 1.3 * size * ax.figure.dpi / 72
    kw = dict(textcoords="offset points", va="center", color=INK_2,
              fontsize=size)
    if gap < 1:
        ax.annotate("both", (x, ends[lo]), xytext=(6, 0), **kw)
        return
    shift = max(0.0, need - gap) / 2 * 72 / ax.figure.dpi
    for k, dy in ((lo, -shift), (hi, shift)):
        ax.annotate(k, (x, ends[k]), xytext=(6, dy), **kw)


def circuit_vs_level(cases: pd.DataFrame) -> None:
    sel = cases[cases.shots == CIRCUIT_SHOTS]
    panels = [("circ_qubits", "Width (qubits)", False),
              ("circ_depth_max", "Depth, max over Newton steps", False),
              ("circ_gates_max", "Gate count (all types), max over steps",
               False),
              ("circ_transpile_s_mean", "Transpile time per Newton step (s)",
               True)]
    fig, axs = plt.subplots(2, 2, figsize=(9.5, 6.4))
    for ax, (col, title, logy) in zip(axs.flat, panels):
        ends = {}
        for cb, g in sel.groupby("codebase"):
            g = g.sort_values("opt_level")
            ends[cb] = g[col].iloc[-1]
            ax.plot(g.opt_level + DODGE[cb], g[col], color=CODEBASE_COLOR[cb],
                    lw=LINE_W, marker="o", ms=MARKER_PT, mec=SURFACE,
                    mew=1.2, label=label(cb, cases))
        ax.set_title(title, loc="left")
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlim(-0.2, 3.6)
        if logy:
            ax.set_yscale("log")
        else:
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        end_labels(ax, ends)
    for ax in axs[1]:
        ax.set_xlabel("Transpiler optimization level")
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper left", ncol=2, bbox_to_anchor=(0.01, 1.0))
    fig.suptitle(f"HHL nelem 5 transpiled circuit, shots {CIRCUIT_SHOTS} runs"
                 " (times under 8 concurrent runs)", x=0.99, ha="right",
                 fontsize=9, color=INK_2)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(os.path.join(PLOTS, "circuit_vs_opt_level.png"), dpi=DPI)
    plt.close(fig)


def fidelity_vs_level(cases: pd.DataFrame) -> None:
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6))
    for ax, shots in zip(axs, (0, 150000)):
        ends = {}
        for cb, g in cases[cases.shots == shots].groupby("codebase"):
            g = g.sort_values("opt_level")
            x, y = g.opt_level + DODGE[cb], g[FIDELITY_SUMMARY]
            ends[cb] = y.iloc[-1]
            if FIDELITY_SUMMARY == "fidelity_mean_excl_last":
                err = [y - g.fidelity_min_excl_last,
                       g.fidelity_max_excl_last - y]
                ax.errorbar(x, y, yerr=err, fmt="none",
                            ecolor=CODEBASE_COLOR[cb], elinewidth=1,
                            capsize=3)
            ax.plot(x, y, color=CODEBASE_COLOR[cb], lw=LINE_W, marker="o",
                    ms=MARKER_PT, mec=SURFACE, mew=1.2,
                    label=label(cb, cases))
        ax.set_title(f"shots {shots}" + (" (statevector)" if not shots
                                         else ""), loc="left")
        ax.set_xticks([0, 1, 2, 3])
        ax.set_xlim(-0.2, 3.6)
        ax.set_xlabel("Transpiler optimization level")
        ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        end_labels(ax, ends)
    axs[0].set_ylabel("Fidelity vs classical solve")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper left", ncol=2, bbox_to_anchor=(0.01, 1.0))
    note = {"fidelity_mean_excl_last": "dot: mean over Newton steps except "
            "the last; bar: min to max over the same steps",
            "fidelity_mean": "mean over all Newton steps",
            "fidelity_last": "final Newton step"}[FIDELITY_SUMMARY]
    fig.text(0.99, 0.01, note, ha="right", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(os.path.join(PLOTS, "fidelity_vs_opt_level.png"), dpi=DPI)
    plt.close(fig)


def per_step(steps: pd.DataFrame, cases: pd.DataFrame, infidelity: bool) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(9.5, 6.4), sharex="row",
                            sharey="row")
    for r, shots in enumerate((0, 150000)):
        for c, cb in enumerate(("nov2025", "nov2026")):
            ax = axs[r, c]
            sel = steps[(steps.shots == shots) & (steps.codebase == cb)]
            wide = sel.pivot(index="step", columns="opt_level",
                             values="fidelity")
            for lvl in sorted(wide.columns):
                y = 1 - wide[lvl] if infidelity else wide[lvl]
                ax.plot(wide.index, y, color=LEVEL_COLOR[lvl], lw=LINE_W,
                        marker="o", ms=MARKER_PT - 1, mec=SURFACE, mew=0.8,
                        label=f"opt level {lvl}")
            spread = (wide.max(axis=1) - wide.min(axis=1)).max()
            ax.text(0.02, 0.04, f"max spread across levels: {spread:.1e}",
                    transform=ax.transAxes, fontsize=8, color=INK_2)
            ax.set_title(f"{label(cb, cases)}, shots {shots}", loc="left")
            if infidelity:
                ax.set_yscale("log")
            if r == 1:
                ax.set_xlabel("Newton step")
        axs[r, 0].set_ylabel("1 - fidelity" if infidelity else "Fidelity")
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper left", ncol=4, bbox_to_anchor=(0.01, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    name = "infidelity_per_step.png" if infidelity else "fidelity_per_step.png"
    fig.savefig(os.path.join(PLOTS, name), dpi=DPI)
    plt.close(fig)


def main() -> None:
    style()
    os.makedirs(PLOTS, exist_ok=True)
    cases = pd.read_csv(os.path.join(DATA, "per_case.csv"))
    steps = pd.read_csv(os.path.join(DATA, "per_step.csv"))
    circuit_vs_level(cases)
    fidelity_vs_level(cases)
    per_step(steps, cases, infidelity=False)
    per_step(steps, cases, infidelity=True)
    print(f"plots -> {PLOTS}")


if __name__ == "__main__":
    main()
