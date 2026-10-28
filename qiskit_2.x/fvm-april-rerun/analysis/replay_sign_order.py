"""Isolate the 38a41e52 sign-order fix: replay old vs new HHL shot post-processing
on the linear systems the old-stack AWS runs actually solved.

For each saved system (A, b) (system_Ab_nelem5_iter<k>.pkl, every CFL, every
trial) the exact Newton update x = A^-1 b is the target. A shot readout is
simulated from the normalized x: 150000 multinomial shots give |x_i| only,
optionally after a random shape error of the size the real HHL circuit shows
(normalized L2 error ~0.035, see hhl_metrics). The same sample then goes
through both post-processing orders:

  old (9e76e398): alpha fit to the UNSIGNED magnitudes m, then signs restored
                  dq = |alpha m| * sign(x)
  new (38a41e52): signs restored first, then alpha fit
                  s = m * sign(x);  dq = alpha(s) s

Signs come from the exact solution in both, as both codes take them from the
classical Hermitian LU. Output: median rel. error ||dq - x|| / ||x|| per
Newton step, and the share of negative components of x.
"""
import glob
import os
import pickle
import re
from collections import defaultdict
from statistics import median

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_RUNS = os.path.join(os.path.dirname(HERE), "old", "apr05")
SHOTS = 150_000
SHAPE_ERR = 0.035


def alpha_ls(A, b, v):
    Av = A @ v
    return (b @ Av) / (Av @ Av + 1e-15)


def readout(x, rng, shape_err):
    state = x / np.linalg.norm(x)
    if shape_err:
        noise = rng.standard_normal(x.size)
        state = state + shape_err * noise / np.linalg.norm(noise)
        state /= np.linalg.norm(state)
    counts = rng.multinomial(SHOTS, state ** 2)
    return np.sqrt(counts / SHOTS)


def replay(A, b, rng, shape_err):
    x = np.linalg.solve(A, b)
    sign = x / (np.abs(x) + 1e-15)
    m = readout(x, rng, shape_err)
    dq_old = np.abs(alpha_ls(A, b, m) * m) * sign
    s = m * sign
    dq_new = alpha_ls(A, b, s) * s
    err = lambda dq: np.linalg.norm(dq - x) / np.linalg.norm(x)
    return err(dq_old), err(dq_new), float(np.mean(x < 0))


def main():
    rng = np.random.default_rng(20261028)
    for shape_err in (0.0, SHAPE_ERR):
        by_step = defaultdict(lambda: ([], [], []))
        for path in glob.glob(f"{OLD_RUNS}/**/system_Ab_nelem5_iter*.pkl", recursive=True):
            step = int(re.search(r"iter(\d+)\.pkl$", path)[1])
            sysd = pickle.load(open(path, "rb"))
            e_old, e_new, neg = replay(np.asarray(sysd["A"]), np.asarray(sysd["b"]), rng, shape_err)
            for lst, v in zip(by_step[step], (e_old, e_new, neg)):
                lst.append(v)
        print(f"\nshape error {shape_err:.3f} + {SHOTS} shots; median over all CFLs and trials")
        print("step   n   old-order err   new-order err   share of x<0")
        for step in sorted(by_step):
            o, n, g = by_step[step]
            print(f"{step:4d} {len(o):3d}   {median(o):13.4f}   {median(n):13.4f}   {median(g):12.2f}")


if __name__ == "__main__":
    main()
