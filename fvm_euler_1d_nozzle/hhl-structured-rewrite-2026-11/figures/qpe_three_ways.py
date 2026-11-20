"""Figure: the QPE of the step-0 HHL circuit built three ways.

Base HHL repeats controlled-U 2^j times on clock qubit j; LuGo makes one
controlled-U^(2^j) per clock qubit; the rewrite writes each as
L^dag c-R^(2^j) L, with only R controlled. Schematic notation and colours as
in block_rewrite.py, simplified: clock qubits c_0..c_2 (more implied) and the
five system qubits as one bundled wire. Grey parts are the same in all three.
CX counts are the measured nelem-5 values.

Drawn at the AIAA text width (6.5 in), so font sizes are print sizes; include
at width=\\textwidth.
CLI: qpe_three_ways.py <out stem>   (writes <stem>.pdf and <stem>.png)
"""

import sys

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

EXACT, LUGO, MID, SAME = "#2e7d32", "#546e7a", "#1565c0", "0.45"
FS_TITLE, FS_WIRE, FS_BOX, FS_SMALL, FS_LEGEND = 9, 8.5, 8.5, 7.5, 8
CLOCKS = [3.6, 3.0, 2.4]  # y of c_0, c_1, c_2
YS = 1.1  # bundled system register
X0, X1 = 0.0, 12.0  # wire extent
XH, XB = 0.4, 0.95  # clock H column, start of the controlled blocks
XL = -1.55  # left edge (wire labels, titles)
PAD = 0.3  # half height of a box on the system wire


def wires(ax) -> None:
    labels = [r"clock $c_0$", r"$c_1$", r"$c_2$"]
    for y, lab in zip(CLOCKS, labels):
        ax.plot([X0, X1], [y, y], color="0.25", lw=0.9, zorder=1)
        ax.text(X0 - 0.12, y, lab, ha="right", va="center", fontsize=FS_WIRE)
    ax.text(X0 - 0.4, 1.85, r"$\vdots$", ha="center", va="center",
            fontsize=FS_WIRE)
    ax.plot([X0, X1], [YS, YS], color="0.25", lw=0.9, zorder=1)
    ax.text(X0 - 0.12, YS, "system", ha="right", va="center",
            fontsize=FS_WIRE)
    ax.plot([X0 + 0.1, X0 + 0.26], [YS - 0.15, YS + 0.15], color="0.25",
            lw=0.9)
    ax.text(X0 + 0.27, YS - 0.4, "5", fontsize=FS_SMALL - 1, ha="center")


def box(ax, x, y0, y1, w, label, color, fs=FS_BOX, pad=PAD) -> None:
    ax.add_patch(FancyBboxPatch((x - w / 2, y0 - pad), w, y1 - y0 + 2 * pad,
                                boxstyle="round,pad=0.01,rounding_size=0.06",
                                fc="white", ec=color, lw=1.2, zorder=3))
    ax.text(x, (y0 + y1) / 2, label, ha="center", va="center",
            fontsize=fs, color=color, zorder=4)


def controlled(ax, x, j, w, label, color) -> None:
    """A box on the system wire controlled by clock qubit c_j."""
    ax.plot([x, x], [CLOCKS[j], YS + PAD], color=color, lw=1.1, zorder=2)
    ax.plot(x, CLOCKS[j], "o", ms=4.5, color=color, zorder=4)
    box(ax, x, YS, YS, w, label, color)


# one column per clock qubit j, shared by all three rows: the width of a
# rewrite block L^dag, R, L
WL, WR, GB, BGAP = 0.56, 0.62, 0.1, 0.3
BW = WL + GB + WR + GB + WL
XSTART = XB + 0.15
CENTERS = [XSTART + j * (BW + BGAP) + BW / 2 for j in range(3)]
XDOTS = XSTART + 3 * BW + 2 * BGAP + 0.45


def rewrite_block(ax, xc, j) -> None:
    """L^dag, c-R^(2^j), L on the system wire, centred on xc."""
    off = WR / 2 + GB + WL / 2
    box(ax, xc - off, YS, YS, WL, r"$L^\dagger$", EXACT)
    controlled(ax, xc, j, WR, ("$R$", "$R^2$", "$R^4$")[j], MID)
    box(ax, xc + off, YS, YS, WL, r"$L$", EXACT)


def frame(ax, title) -> None:
    ax.set_xlim(XL, X1 + 0.05)
    ax.set_ylim(0.55, 4.3)
    ax.axis("off")
    ax.text(XL, 4.15, title, fontsize=FS_TITLE, ha="left", va="center")
    wires(ax)
    for y in CLOCKS:
        box(ax, XH, y, y, 0.36, "H", SAME, fs=FS_SMALL, pad=0.17)
    box(ax, X1 - 0.5, CLOCKS[-1], CLOCKS[0], 0.9, r"QFT$^\dagger$", SAME,
        fs=FS_SMALL, pad=0.2)


def dots(ax, x) -> None:
    ax.text(x, YS + 0.22, r"$\cdots$", ha="center", va="center",
            fontsize=FS_BOX + 2)


def main(stem: str) -> None:
    fig, axs = plt.subplots(3, 1, figsize=(6.5, 4.25))
    frame(axs[0], r"$\bf{(i)\ Base\ HHL}$: $U^{2^j}$ from $2^j$ copies of "
                  r"$U$ on clock $c_j$ ($j = 0, \ldots, 7$ at "
                  r"$N_{\rm elem} = 5$), ~3,400 CX each")
    w, g = 0.42, 0.06
    for j, n in enumerate((1, 2, 4)):
        x = CENTERS[j] - (n * w + (n - 1) * g) / 2 + w / 2
        for _ in range(n):
            controlled(axs[0], x, j, w, "$U$", LUGO)
            x += w + g
    dots(axs[0], XDOTS)

    frame(axs[1], r"$\bf{(ii)\ LuGo}$: $U^{2^j}$ computed classically and "
                  r"synthesized once per clock qubit, ~3,400 CX each")
    for j, lab in enumerate(("$U$", "$U^2$", "$U^4$")):
        controlled(axs[1], CENTERS[j], j, 0.8, lab, LUGO)
    dots(axs[1], XDOTS)

    frame(axs[2], r"$\bf{(iii)\ Rewrite}$: $U^{2^j} = L\,R^{2^j}L^\dagger$, "
                  r"$L$ real and a byproduct of LuGo's factoring of $U$, "
                  r"$R^{2^j}$ differs, 276 CX each")
    for j in range(3):
        rewrite_block(axs[2], CENTERS[j], j)
    dots(axs[2], XDOTS)

    fig.tight_layout(h_pad=0.2)
    for ext in ("pdf", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=200, bbox_inches="tight",
                    pad_inches=0.02)
        print("wrote", f"{stem}.{ext}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qpe_three_ways")
