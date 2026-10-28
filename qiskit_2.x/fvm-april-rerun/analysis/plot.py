"""Plots for the April fvm CFL sweep vs its AWS reruns (run collect.py first).

  residual_history.png  outer residual vs Newton iteration, one panel per CFL
  final_error.png       final-solution rel. L2 error vs the converged LU solution
  timing.png            median per-case time split into generate / transpile / run
"""
import csv
import glob
import os
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SETS = {"april": ("April Frontier (qiskit 2.3.1)", "#2a78d6", "o"),
        "old": ("AWS old stack (qiskit 2.3.1)", "#eb6834", "s"),
        "new": ("AWS new stack (qiskit 2.6.1)", "#1baf7a", "^")}
CFLS = ["1", "5", "10", "25", "1e10"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
    "legend.frameon": False,
})


def read_csv(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f, skipinitialspace=True))
    head = [h.strip() for h in rows[0]]
    return [dict(zip(head, r)) for r in rows[1:] if r]


CASES = read_csv(os.path.join(HERE, "cases.csv"))


def cases(s, c):
    return [r for r in CASES if r["set"] == s and r["cfl"] == c]


def residual_history(case_dir):
    res = read_csv(glob.glob(os.path.join(WORKSPACE, case_dir, "residual_*.csv"))[0])
    return [float(r["residual_total"]) for r in res]


def plot_residuals():
    fig, axes = plt.subplots(1, 5, figsize=(14, 3.6), sharey=True)
    for ax, c in zip(axes, CFLS):
        lu = read_csv(glob.glob(f"{HERE}/lu_ref/iters15_cfl{c}/residual_*.csv")[0])
        ax.plot([float(r["residual_total"]) for r in lu], color=INK2, lw=1.2, ls="--", label="classical LU")
        for s, (label, color, _) in SETS.items():
            # trials that converge stop early; each iteration uses the trials
            # still running, plotted while at least half of them are
            hist = [residual_history(r["case_dir"]) for r in cases(s, c)]
            cols = [[h[i] for h in hist if i < len(h)] for i in range(max(map(len, hist)))]
            cols = [v for v in cols if 2 * len(v) >= len(hist)]
            n = len(cols)
            ax.fill_between(range(n), [min(v) for v in cols], [max(v) for v in cols],
                            color=color, alpha=0.15, lw=0)
            ax.plot(range(n), [median(v) for v in cols], color=color, lw=2, label=label)
        ax.set_yscale("log")
        ax.set_title(f"CFL {c}", color=INK, fontsize=10)
        ax.set_xlabel("Newton iteration")
    axes[0].set_ylabel("outer residual (total)")
    axes[0].legend(loc="lower left", fontsize=7.5)
    fig.suptitle("Outer residual per Newton iteration — median of 10 trials, band = min to max "
                 "(lines end where trials converged)", x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "residual_history.png"), dpi=160)


def plot_final_error():
    fig, ax = plt.subplots(figsize=(8, 4))
    offsets = {"april": -0.22, "old": 0.0, "new": 0.22}
    for s, (label, color, marker) in SETS.items():
        for i, c in enumerate(CFLS):
            v = [float(r["relL2_vs_steady"]) for r in cases(s, c)]
            ax.scatter([i + offsets[s]] * len(v), v, s=36, marker=marker, color=color,
                       edgecolor=SURFACE, linewidth=1, label=label if i == 0 else None, zorder=3)
    ax.set_yscale("log")
    ax.set_xticks(range(len(CFLS)), [f"CFL {c}" for c in CFLS])
    ax.set_ylabel("rel. L2 error vs converged LU (ρ, u, p)")
    ax.set_title("Final solution error after 15 Newton iterations, 10 trials each",
                 loc="left", fontsize=11)
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "final_error.png"), dpi=160)


def plot_timing():
    parts = [("t_generate_s", "circuit generation", "#86b6ef"),
             ("t_transpile_s", "transpile", "#2a78d6"),
             ("t_run_s", "simulation run", "#104281")]
    groups = [("CFL 1–25", ["1", "5", "10", "25"]), ("CFL 1e10", ["1e10"])]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.2), sharex=True)
    for ax, (title, cfls) in zip(axes, groups):
        labels = []
        for y, s in enumerate(SETS):
            rows = [r for c in cfls for r in cases(s, c)]
            total = median(float(r["t_case_s"]) for r in rows) / 60
            left = 0.0
            for key, name, color in parts:
                w = median(float(r[key]) for r in rows) / 60
                ax.barh(y, w, left=left, color=color, height=0.6, edgecolor=SURFACE, linewidth=2,
                        label=name if y == 0 else None)
                left += w
            ax.barh(y, max(total - left, 0), left=left, color=GRID, height=0.6, edgecolor=SURFACE,
                    linewidth=2, label="everything else" if y == 0 else None)
            ax.text(total + 1.5, y, f"{total:.0f} min", va="center", color=INK2, fontsize=8)
            labels.append(SETS[s][0])
        ax.set_yticks(range(len(SETS)), labels)
        ax.invert_yaxis()
        ax.set_title(title, loc="left", color=INK, fontsize=10)
        ax.set_xlabel("median minutes per case (15 HHL solves)")
        ax.grid(axis="y", visible=False)
    handles, names = axes[0].get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=4, fontsize=8)
    fig.suptitle("Where each case's time goes (median case; bar end = case total)",
                 x=0.01, ha="left", fontsize=11)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(os.path.join(HERE, "timing.png"), dpi=160)


if __name__ == "__main__":
    plot_residuals()
    plot_final_error()
    plot_timing()
    print("wrote residual_history.png, final_error.png, timing.png")
