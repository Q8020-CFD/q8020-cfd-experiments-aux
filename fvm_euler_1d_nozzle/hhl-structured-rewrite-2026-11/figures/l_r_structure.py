"""Figure: |U|, |L| and |R = L^T U L| for the nelem-5 step-0 HHL circuit.

U = exp(i A^H t0) is recovered from LuGo's first QPE block (cached block
unitaries of tmp/lugo-qpy-depth-ideas), A^H = [[0, A], [A^T, 0]] from its matrix
log. L = P (+) Q from the SVD A = P S Q^T. In L's basis U falls apart into 16
independent 2 x 2 rotations, one per singular pair (p_i, q_i); R is shown with
rows and columns grouped by pair (embedding qubit as the fastest index) so the
blocks sit on the diagonal. Checks each block against
[[cos t0 s_i, i sin t0 s_i], [i sin t0 s_i, cos t0 s_i]].
Drawn at the AIAA text width (6.5 in); include at width=\\textwidth.
CLI: l_r_structure.py <out stem>   (writes <stem>.pdf and <stem>.png)
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg as sla
from matplotlib.colors import LinearSegmentedColormap

BLOCKS = Path("/Users/agallojr/proj/src/research-notes/bus/spaces/tmp/"
              "lugo-qpy-depth-ideas/blocks_nelem5.npz")
BLUE = "#1565c0"  # the R colour of qpe_three_ways.py
FS_TITLE, FS_LABEL = 8.5, 7.5


def strip_control(m: np.ndarray, nb: int) -> np.ndarray:
    n = nb + 1
    for c in range(n):
        i0 = [i for i in range(2 ** n) if not (i >> c) & 1]
        i1 = [i for i in range(2 ** n) if (i >> c) & 1]
        if np.allclose(m[np.ix_(i0, i0)], np.eye(2 ** nb), atol=1e-9):
            return m[np.ix_(i1, i1)]
    raise ValueError("no control qubit")


def matrices():
    z = np.load(BLOCKS, allow_pickle=True)
    u = strip_control(z["mats"][0], int(z["nb"]))
    h = -1j * sla.logm(u)
    h = ((h + h.conj().T) / 2).real  # A^H t0, real symmetric
    n = h.shape[0] // 2
    p, s, qt = np.linalg.svd(h[:n, n:])
    lm = sla.block_diag(p, qt.T)
    r = lm.T @ u @ lm
    perm = [k // 2 + (k % 2) * n for k in range(2 * n)]  # 2 s + e <- s + n e
    rp = r[np.ix_(perm, perm)]
    # checks: R has only pair couplings, each block is exp(i s_i X)
    mask = np.zeros_like(rp, dtype=bool)
    for i in range(n):
        mask[2 * i:2 * i + 2, 2 * i:2 * i + 2] = True
    off = np.abs(rp[~mask]).max()
    blk = max(np.abs(rp[2 * i:2 * i + 2, 2 * i:2 * i + 2]
                     - np.array([[np.cos(s[i]), 1j * np.sin(s[i])],
                                 [1j * np.sin(s[i]), np.cos(s[i])]])).max()
              for i in range(n))
    print(f"|U - L R L^T| max {np.abs(u - lm @ r @ lm.T).max():.1e}; "
          f"R off-block max {off:.1e}; block vs rotation max {blk:.1e}")
    return u, lm, rp


def panel(ax, m, title, blocks) -> None:
    cmap = LinearSegmentedColormap.from_list("w2b", ["white", BLUE])
    ax.imshow(np.abs(m), cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    d = m.shape[0]
    for b in blocks:  # outline the nonzero blocks
        r0, size = b
        ax.add_patch(plt.Rectangle((r0 - 0.5, r0 - 0.5), size, size,
                                   fill=False, ec="0.35", lw=0.6))
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("0.35")
        sp.set_linewidth(0.6)
    ax.set_xlim(-0.5, d - 0.5)
    ax.set_ylim(d - 0.5, -0.5)
    ax.set_title(title, fontsize=FS_TITLE, pad=4)


def main(stem: str) -> None:
    u, lm, rp = matrices()
    fig, axs = plt.subplots(1, 3, figsize=(6.5, 2.55))
    panel(axs[0], u, "$U$: dense $32\\times32$", [])
    panel(axs[1], lm, "$L = P \\oplus Q$: two $16\\times16$ blocks",
          [(0, 16), (16, 16)])
    panel(axs[2], rp, "$R = L^{\\dagger}UL$: sixteen $2\\times2$ rotations",
          [(2 * i, 2) for i in range(16)])
    axs[1].text(0.5, -0.07, "$P$: left singular vectors of $A$\n"
                "$Q$: right singular vectors of $A$",
                transform=axs[1].transAxes, ha="center", va="top",
                fontsize=FS_LABEL)
    axs[2].text(0.5, -0.07, "block $i$: $e^{\\,i t_0 \\sigma_i X}$, a rotation "
                "of the\nembedding qubit by $2 t_0 \\sigma_i$, one per "
                "singular value",
                transform=axs[2].transAxes, ha="center", va="top",
                fontsize=FS_LABEL)
    fig.tight_layout(w_pad=1.0)
    for ext in ("pdf", "png"):
        fig.savefig(f"{stem}.{ext}", dpi=250, bbox_inches="tight",
                    pad_inches=0.02)
        print("wrote", f"{stem}.{ext}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "l_r_structure")
