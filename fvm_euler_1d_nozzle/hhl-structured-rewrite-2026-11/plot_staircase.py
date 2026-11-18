"""Paper figure: IBM staircases, survival and system fidelity against
two-qubit gate count, one row per backend.

Reads captured staircase results folders (ibm_capture.py): analysis.json for
the per-step scores and prep.json for the backend and the full circuit's
two-qubit gate count. Left: readout-corrected survival on a log scale; steps
whose system distribution is at the maximally mixed value are grey (their
survival is a floor set by relaxation toward 0, not signal), and the dotted
line fits the steps with signal and is extended to the full circuit; with
fewer than two such steps no fit is drawn. Right: the fidelity to |b|^2 of the system's
distribution given clock and ancilla 0, against the maximally mixed value;
the leftmost point is the state preparation alone.

Usage: plot_staircase.py <results folder> [<folder> ...] -o <out> [<out> ...]
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

BLUE = "#2a78d6"                            # categorical slot 1
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
GREY = "#a3a29d"                            # de-emphasized: no signal
MARK = {"marker": "o", "ms": 5.5, "mec": "white", "mew": 0.8}


def load(folder: Path) -> dict:
    ana = json.loads((folder / "analysis.json").read_text())
    prep = json.loads((folder / "prep.json").read_text())
    proc = prep.get("processor") or {}
    fam = f", {proc.get('family', '')} r{proc.get('revision', '')}" if proc else ""
    return {"steps": ana["steps"], "full": prep["full_circuit_two_qubit_gates"],
            "null": ana["steps"][0]["readout"]["system_fidelity_null"],
            "name": prep["backend"] + fam}


def sci(v: float) -> str:
    m, e = f"{v:.0e}".split("e")
    return rf"{m}$\times10^{{{int(e)}}}$"


def draw_row(ax1, ax2, d: dict, letters: tuple[str, str]) -> None:
    steps, full, null = d["steps"], d["full"], d["null"]
    walked = [s for s in steps if s["blocks"] > 0]
    x = np.array([s["two_qubit_gates"] for s in walked])
    surv = np.array([s["readout"]["survival"] for s in walked])
    sig = np.array([s["readout"]["system_fidelity"] > null + 0.02
                    for s in walked])
    k = int(np.argmin(sig)) if not sig.all() else len(walked)

    # left: survival
    ax1.plot(x[max(k - 1, 0):], surv[max(k - 1, 0):], color=GREY, lw=1.4,
             zorder=2)
    ax1.plot(x[k:], surv[k:], color=GREY, lw=0, zorder=3, **MARK)
    ax1.plot(x[:k], surv[:k], color=BLUE, lw=1.4, zorder=4, **MARK)
    if k >= 2:  # fit only steps that still carry system signal
        fx, fy = x[:k], np.log(surv[:k])
        slope, icept = np.polyfit(fx, fy, 1)
        xx = np.linspace(fx.min(), full, 50)
        pred = math.exp(icept + slope * full)
        print(f"{d['name']}: fit over steps "
              f"{[s['blocks'] for s in walked[:k]]}, "
              f"{1 - math.exp(slope):.2e} per 2q gate, {pred:.1e} at {full}")
        ax1.plot(xx, np.exp(icept + slope * xx), color=BLUE, lw=1.0, ls=":",
                 zorder=2)
        ax1.plot([full], [pred], marker="D", ms=5, mfc="white", mec=BLUE,
                 mew=1.2, ls="none", zorder=4)
        ax1.annotate(sci(pred), (full, pred), xytext=(-6, -2),
                     textcoords="offset points", ha="right", va="top",
                     fontsize=8, color=INK2)
    else:
        print(f"{d['name']}: {k} step(s) with system signal; no fit drawn")
    ax1.set_yscale("log")
    ax1.set_ylim(1e-6, 1.0)
    ax1.set_ylabel("survival")
    ax1.set_title(f"({letters[0]}) {d['name']}", loc="left")

    # right: system fidelity
    allx = np.array([s["two_qubit_gates"] for s in steps])
    fid = np.array([s["readout"]["system_fidelity"] for s in steps])
    ax2.axhline(null, color=INK2, lw=0.9, ls="--", zorder=1)
    ax2.text(full * 0.97, null + 0.05, f"maximally mixed, {null:.2f}",
             ha="right", va="bottom", fontsize=8, color=INK2)
    ax2.plot(allx, fid, color=BLUE, lw=1.4, zorder=3, **MARK)
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel(r"system fidelity to $|b|^2$")
    ax2.set_title(f"({letters[1]}) {d['name']}", loc="left")

    for ax in (ax1, ax2):
        ax.axvline(full, color=INK2, lw=0.9, ls="-.", zorder=1)
        ax.text(full - 60, 0.98, "full circuit", ha="right", va="top",
                fontsize=8, color=INK2, transform=ax.get_xaxis_transform())


SERIES = (("#2a78d6", "o"), ("#eb6834", "s"))   # categorical slots 1, 2
FADE = 0.35                                     # alpha: no system signal


def draw_overlay(ax1, ax2, rows: list[dict]) -> None:
    """All backends in one row, one color and marker each. Steps without
    system signal are faded in (a); every step is drawn in full in (b)."""
    null = rows[0]["null"]
    for d, (col, mk) in zip(rows, SERIES):
        steps, full = d["steps"], d["full"]
        walked = [s for s in steps if s["blocks"] > 0]
        x = np.array([s["two_qubit_gates"] for s in walked])
        surv = np.array([s["readout"]["survival"] for s in walked])
        sig = np.array([s["readout"]["system_fidelity"] > null + 0.02
                        for s in walked])
        k = int(np.argmin(sig)) if not sig.all() else len(walked)
        mark = {"marker": mk, "ms": 5.5, "mec": "white", "mew": 0.8}
        ax1.plot(x[max(k - 1, 0):], surv[max(k - 1, 0):], color=col, lw=1.4,
                 alpha=FADE, zorder=2)
        ax1.plot(x[k:], surv[k:], color=col, lw=0, alpha=FADE, zorder=3,
                 **mark)
        ax1.plot(x[:k], surv[:k], color=col, lw=1.4, zorder=4, **mark)
        if k >= 2:
            slope, icept = np.polyfit(x[:k], np.log(surv[:k]), 1)
            xx = np.linspace(x[0], full, 50)
            pred = math.exp(icept + slope * full)
            print(f"{d['name']}: fit over steps "
                  f"{[s['blocks'] for s in walked[:k]]}, "
                  f"{1 - math.exp(slope):.2e} per 2q gate, {pred:.1e} at {full}")
            ax1.plot(xx, np.exp(icept + slope * xx), color=col, lw=1.0,
                     ls=":", zorder=2)
            ax1.plot([full], [pred], marker="D", ms=5, mfc="white", mec=col,
                     mew=1.2, ls="none", zorder=4)
            ax1.annotate(sci(pred), (full, pred), xytext=(-6, -2),
                         textcoords="offset points", ha="right", va="top",
                         fontsize=8, color=INK2)
        else:
            print(f"{d['name']}: {k} step(s) with system signal; no fit")
        allx = np.array([s["two_qubit_gates"] for s in steps])
        fid = np.array([s["readout"]["system_fidelity"] for s in steps])
        ax2.plot(allx, fid, color=col, lw=1.4, zorder=3, **mark)
        for ax in (ax1, ax2):
            ax.axvline(full, color=col, lw=0.9, ls="-.", alpha=0.8, zorder=1)
    # a terse legend in (a): one entry per backend, drawn at full color
    handles = [Line2D([], [], color=col, lw=1.4, marker=mk, ms=5.5,
                      mec="white", mew=0.8)
               for (col, mk), _ in zip(SERIES, rows)]
    ax1.legend(handles, [d["name"].split(",")[0] for d in rows],
               loc="lower left", fontsize=8, handlelength=1.8, frameon=False)
    lo = min(d["full"] for d in rows)
    for ax in (ax1, ax2):
        ax.text(lo - 60, 0.98, "full circuit", ha="right", va="top",
                fontsize=8, color=INK2, transform=ax.get_xaxis_transform())
    ax1.set_yscale("log")
    ax1.set_ylim(1e-6, 1.0)
    ax1.set_ylabel("survival")
    ax1.set_title("(a) clock and ancilla return to 0", loc="left")
    ax2.axhline(null, color=INK2, lw=0.9, ls="--", zorder=1)
    ax2.text(lo * 0.97, null + 0.05, f"maximally mixed, {null:.2f}",
             ha="right", va="bottom", fontsize=8, color=INK2)
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel(r"system fidelity to $|b|^2$")
    ax2.set_title("(b) system, given clock and ancilla 0", loc="left")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folders", type=Path, nargs="+")
    ap.add_argument("-o", "--out", type=Path, nargs="+", required=True)
    ap.add_argument("--overlay", action="store_true",
                    help="all folders in one row, one color each (max 2)")
    a = ap.parse_args()
    rows = [load(f) for f in a.folders]
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix", "font.size": 9, "axes.titlesize": 9,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
        "ytick.color": INK2, "axes.linewidth": 0.6, "legend.frameon": False,
    })
    if a.overlay:
        if len(rows) > len(SERIES):
            raise SystemExit(f"--overlay takes at most {len(SERIES)} folders")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.9))
        draw_overlay(ax1, ax2, rows)
        for ax in (ax1, ax2):
            ax.set_xlim(0, max(r["full"] for r in rows) * 1.04)
            ax.set_xlabel("two-qubit gates")
            ax.grid(True, color=GRID, lw=0.5, zorder=0)
            ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout(w_pad=2.0)
        for out in a.out:
            out.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(out, dpi=300, bbox_inches="tight")
            print("wrote", out)
        return
    n = len(rows)
    fig, axes = plt.subplots(n, 2, figsize=(6.6, 2.7 * n), sharex=True,
                             squeeze=False)
    letters = "abcdefgh"
    xmax = max(r["full"] for r in rows) * 1.04
    for i, d in enumerate(rows):
        draw_row(axes[i, 0], axes[i, 1], d, (letters[2 * i], letters[2 * i + 1]))
    for i in range(n):
        for j in range(2):
            ax = axes[i, j]
            ax.set_xlim(0, xmax)
            ax.grid(True, color=GRID, lw=0.5, zorder=0)
            ax.spines[["top", "right"]].set_visible(False)
            if i == n - 1:
                ax.set_xlabel("two-qubit gates")
    fig.tight_layout(w_pad=2.0, h_pad=1.2)
    for out in a.out:
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print("wrote", out)


if __name__ == "__main__":
    main()
