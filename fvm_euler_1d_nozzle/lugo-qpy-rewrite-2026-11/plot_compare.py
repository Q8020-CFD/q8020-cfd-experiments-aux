"""Plot the LuGo comparison: feb26, nov26 and the step-0 qpy rewrite.

Reads only data/per_set.csv and data/step0_trials.csv (build_compare_data.py
writes them). Writes plots/*.png next to this file.

Usage: ~/.venvs/tooling/bin/python plot_compare.py
"""

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA, PLOTS = HERE / "data", HERE / "plots"

# ---- settings -------------------------------------------------------------
DPI = 150
# dataviz reference palette, categorical slots 1-3; controls in muted ink
SETS = ["feb26", "nov26", "rewrite"]
CONTROLS = ["control_stored", "control_qiskit26"]
COLOR = {"feb26": "#2a78d6", "nov26": "#eb6834", "rewrite": "#1baf7a",
         "control_stored": "#898781", "control_qiskit26": "#898781"}
LABEL = {"feb26": "LuGo feb26\nqiskit 1.4.5", "nov26": "LuGo nov26\nqiskit 2.6",
         "rewrite": "feb26 step-0 qpy\nrewritten, qiskit 2.6",
         "control_stored": "control: feb26\nqpy as stored",
         "control_qiskit26": "control: feb26 qpy\nre-transpiled 2.6"}
SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
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


def fmt(v: float) -> str:
    return f"{v / 1e3:.1f}k" if v < 1e5 else f"{v / 1e3:.0f}k"


def circuit_cost(ps: pd.DataFrame) -> None:
    """Step-0 circuit size in hardware gates: original feb26 against rewrite.

    Rows: all-to-all cx/rz/sx/x basis, IBM Heron r2. Columns: two-qubit gate
    count, total depth. Every panel counts the same native gates, so the
    original and the rewrite are compared in one unit. nov26 kept no qpy and
    is not shown. The Aer-target depth stays in data/per_set.csv (aer_depth).
    """
    sets = ["feb26", "rewrite"]
    name = {"feb26": "LuGo feb26 circuit as stored (qiskit 1.4.5)",
            "rewrite": "feb26 step-0 qpy rewritten (qiskit 2.6)"}
    panels = [[("a2a_cx", "Two-qubit gates (CX), all-to-all"),
               ("a2a_depth", "Total depth, all-to-all")],
              [("heron_cz", "Two-qubit gates (CZ), IBM Heron r2"),
               ("heron_depth", "Total depth, IBM Heron r2")]]
    nel = sorted(ps.nelem.unique())
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.6))
    w = 0.34
    for row, prow in zip(axes, panels):
        for ax, (col, title) in zip(row, prow):
            for j, s in enumerate(sets):
                for i, n in enumerate(nel):
                    r = ps[(ps.set == s) & (ps.nelem == n)]
                    if not len(r) or pd.isna(r[col].iloc[0]):
                        continue
                    v = float(r[col].iloc[0])
                    x = i + (j - 0.5) * w
                    ax.bar(x, v, w * 0.92, color=COLOR[s], edgecolor=SURFACE,
                           linewidth=1)
                    txt = fmt(v)
                    if s == "rewrite":
                        base = ps[(ps.set == "feb26") & (ps.nelem == n)][col]
                        txt += f"\n{float(base.iloc[0]) / v:.1f}x less"
                    ax.text(x, v * 1.1, txt, ha="center", va="bottom",
                            fontsize=7.5, color=INK_2)
            ax.set_yscale("log")
            ax.set_ylim(5e3, 5e6)
            ax.set_xticks(range(len(nel)),
                          [f"nelem {n}\n({int(ps[ps.nelem == n].qubits.iloc[0])}"
                           " qubits)" for n in nel])
            ax.set_title(title, loc="left")
            ax.grid(axis="x", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[s]) for s in sets]
    fig.legend(handles, [name[s] for s in sets], loc="upper left", ncol=2,
               bbox_to_anchor=(0.01, 1.0))
    fig.text(0.01, 0.01, "first Newton step; both circuits transpiled with "
             "qiskit 2.6.0, level 2, to the same native gates (cx/rz/sx/x "
             "all-to-all; FakeMarrakesh heavy-hex cz)\ntwo-qubit depth is "
             "within 9 % of the two-qubit count in every case (the circuits "
             "are serial); nov26 kept no qpy, so it has no hardware counts",
             fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94))
    fig.savefig(PLOTS / "circuit_cost_step0.png", dpi=DPI)
    plt.close(fig)


def fidelity_step0(ps: pd.DataFrame, tr: pd.DataFrame) -> None:
    """Step-0 infidelity at 150000 shots per trial, with the exact value."""
    order = SETS + CONTROLS
    nel = sorted(ps.nelem.unique())
    fig, axes = plt.subplots(1, len(nel), figsize=(8.0 * len(nel), 4.4),
                             sharey=True)
    axes = np.atleast_1d(axes)
    rng = np.random.default_rng(0)
    for ax, n in zip(axes, nel):
        for x, s in enumerate(order):
            t = tr[(tr.set == s) & (tr.nelem == n)]
            r = ps[(ps.set == s) & (ps.nelem == n)]
            if not len(t):
                continue
            y = 1 - t.fidelity.to_numpy()
            jit = rng.uniform(-0.12, 0.12, len(y))
            hollow = s in CONTROLS
            ax.scatter(x + jit, y, s=26, zorder=3,
                       facecolor="none" if hollow else COLOR[s],
                       edgecolor=COLOR[s] if hollow else SURFACE,
                       linewidth=1.2 if hollow else 0.8)
            ax.hlines(np.median(y), x - 0.25, x + 0.25, color=INK_2, lw=1.4,
                      zorder=4)
            ex = 1 - float(r.sv_fidelity.iloc[0])
            ax.hlines(ex, x - 0.3, x + 0.3, color=COLOR[s], lw=1.6,
                      linestyle=(0, (2, 1.5)), zorder=2)
        ax.set_yscale("log")
        ax.set_xticks(range(len(order)), [LABEL[s] for s in order],
                      fontsize=7.5)
        ax.set_title(f"nelem {n}, first Newton step", loc="left")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("1 - fidelity vs classical solve")
    exact = "; ".join(
        f"{1 - ps[ps.nelem == n].sv_fidelity.median():.1e} at nelem {n}"
        for n in nel)
    fig.text(0.01, 0.01, "dots: 150000-shot trials (feb26, nov26: 10 recorded "
             "trials on Frontier; rewrite and controls: Aer seeds 1-10 on a "
             "laptop)\nsolid tick: median; dashed: exact statevector, the "
             f"same for every set ({exact})", fontsize=7.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(PLOTS / "fidelity_step0.png", dpi=DPI)
    plt.close(fig)


def main() -> None:
    style()
    PLOTS.mkdir(exist_ok=True)
    ps = pd.read_csv(DATA / "per_set.csv")
    tr = pd.read_csv(DATA / "step0_trials.csv")
    circuit_cost(ps)
    fidelity_step0(ps, tr)
    print(f"wrote {PLOTS}")


if __name__ == "__main__":
    main()
