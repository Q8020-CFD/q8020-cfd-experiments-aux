"""Figure: one controlled-power block under LuGo, the rewrite, and AQC.

Schematic circuit notation (matplotlib only): wires are the clock qubit c,
the embedding qubit e (system MSB) and the four lower system qubits as one
bundled wire. CX counts are the measured nelem-5 values.
CLI: block_rewrite.py <out.png>
"""

import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

EXACT, APPROX, LUGO, MID = "#2e7d32", "#ef6c00", "#546e7a", "#1565c0"
WIRES = {"c": 2.0, "e": 1.0, "s": 0.0}  # y positions
LABELS = {"c": r"clock $c_k$", "e": r"embed. $e$", "s": r"system $s$"}


def wires(ax, x0, x1):
    for k, y in WIRES.items():
        ax.plot([x0, x1], [y, y], color="0.25", lw=1.2, zorder=1)
        ax.text(x0 - 0.15, y, LABELS[k], ha="right", va="center",
                fontsize=10)
    ys = WIRES["s"]
    ax.plot([x0 + 0.25, x0 + 0.45], [ys - 0.18, ys + 0.18], color="0.25",
            lw=1.2)
    ax.text(x0 + 0.42, ys - 0.38, "4", fontsize=8, ha="center")


def box(ax, x, y0, y1, w, label, color, fs=12):
    h = y1 - y0 + 0.6
    ax.add_patch(FancyBboxPatch((x - w / 2, y0 - 0.3), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc="white", ec=color, lw=1.8, zorder=3))
    ax.text(x, (y0 + y1) / 2, label, ha="center", va="center",
            fontsize=fs, color=color, zorder=4)


def control(ax, x, y_ctrl, y_target, color):
    ax.plot([x, x], [y_ctrl, y_target], color=color, lw=1.6, zorder=2)
    ax.plot(x, y_ctrl, "o", ms=7, color=color, zorder=4)


def mux_control(ax, x, y, color):
    """Multiplexer control: an open square on the bundled wire."""
    ax.plot(x, y, "s", ms=8, mfc="white", mec=color, mew=1.6, zorder=4)


def row(ax, title, note, kind):
    ax.set_xlim(-1.6, 10.6)
    ax.set_ylim(-0.75, 2.6)
    ax.axis("off")
    ax.text(-1.6, 2.5, title, fontsize=11, ha="left", va="center",
            weight="bold")
    wires(ax, 0.0, 7.2)
    if kind == "lugo":
        control(ax, 3.6, WIRES["c"], WIRES["e"] + 0.3, LUGO)
        box(ax, 3.6, WIRES["s"], WIRES["e"], 3.0,
            "$U^m$\n(QSD of $U^m$,\nevery gate controlled)", LUGO, fs=10)
    else:
        col = EXACT if kind == "rewrite" else APPROX
        lab = "L" if kind == "rewrite" else r"\tilde{L}"
        box(ax, 1.2, WIRES["s"], WIRES["e"], 1.1, f"${lab}^\\dagger$", col)
        box(ax, 2.55, WIRES["e"], WIRES["e"], 0.6, "H", "0.2", fs=11)
        control(ax, 3.6, WIRES["c"], WIRES["e"] + 0.3, MID)
        ax.plot([3.6, 3.6], [WIRES["s"], WIRES["e"] - 0.3], color=MID,
                lw=1.6, zorder=2)
        mux_control(ax, 3.6, WIRES["s"], MID)
        box(ax, 3.6, WIRES["e"], WIRES["e"], 1.1, r"$R_z(m\theta_i)$", MID,
            fs=10)
        box(ax, 4.65, WIRES["e"], WIRES["e"], 0.6, "H", "0.2", fs=11)
        box(ax, 6.0, WIRES["s"], WIRES["e"], 1.1, f"${lab}$", col)
    ax.text(7.5, 1.0, note, fontsize=9.5, ha="left", va="center",
            linespacing=1.4)


def main(out: str) -> None:
    fig, axs = plt.subplots(3, 1, figsize=(10.5, 6.6))
    row(axs[0], "(i) LuGo block",
        "every gate of the synthesized\n$U^m$ is controlled by $c_k$\n"
        "~3,400 CX per block", "lugo")
    row(axs[1], "(ii) Rewrite (exact)",
        "$U^m = L\\,R^m L^\\dagger$: only the middle\n"
        "rotation is controlled\n"
        "276 CX per block", "rewrite")
    row(axs[2], "(iii) + AQC (approximate)",
        "$\\tilde{L}$ refit with fewer CX,\n"
        "at a cost in fidelity", "aqc")
    fig.tight_layout(h_pad=0.6)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "block_rewrite.png")
