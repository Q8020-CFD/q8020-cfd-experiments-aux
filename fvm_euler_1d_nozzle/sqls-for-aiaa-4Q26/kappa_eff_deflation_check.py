#!/usr/bin/env python3
"""Spectrum of the saved 1D-nozzle Jacobians and what SVD deflation would buy HHL.

Reads the system_Ab_nelem5_iter*.pkl files archived from the April 2026 CFL
sweep (trial_0 of each CFL group) and the August 2026 local trials, and for
each (CFL, iteration) reports: singular values, kappa, kappa_eff(k) after
deflating the k smallest singular triplets, the HHL clock-register width the
Vazquez library would pick, the HHL post-selection success probability with and
without deflation, the share of ||b||^2 in the deflated modes, and a numerical
check of the shifted-deflation identity. Pure post-processing of existing data;
no solver is run.
"""
from __future__ import annotations

import glob
import math
import os
import pickle
import sys

import numpy as np

ROOT = ("/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
        "fvm_euler_1d_solver")
APRIL = {
    1: "2026-04-05/_52d087d1/time_steps_0/trial_0_5066b4fb",
    5: "2026-04-05/_52d087d1/time_steps_1/trial_0_84dc6b0d",
    10: "2026-04-05/_52d087d1/time_steps_2/trial_0_bce93f35",
    25: "2026-04-05/_52d087d1/time_steps_3/trial_0_d18dd36e",
    1e10: "2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e",
}
KS = (0, 1, 2, 3, 4)
ITERS = (0, 3, 7, 14)


def load(path: str) -> tuple[np.ndarray, np.ndarray]:
    d = pickle.load(open(path, "rb"))
    return np.asarray(d["A"], float), np.asarray(d["b"], float).ravel()


def clock_qubits(kappa: float, n_b: int) -> int:
    """Clock-register width as sized by linear_solvers/hhl.py (doubled system
    has +/- sigma eigenvalues, so the negative-eigenvalue qubit is always on)."""
    return max(n_b + 1, math.ceil(math.log2(kappa + 1))) + 1


def success_prob(sig: np.ndarray, ub: np.ndarray, lam_min: float,
                 shift: float | None, k: int) -> float:
    """HHL post-selection probability proxy on the Hermitian-doubled system with
    reciprocal constant C = lam_min: sum_i |u_i.b|^2 (C / lambda_i)^2 / ||b||^2.
    Deflated modes (i < k) sit at eigenvalue `shift` after shifted deflation."""
    lam = sig.copy()
    if k:
        lam[:k] = shift
    w = ub ** 2 / np.sum(ub ** 2)
    return float(np.sum(w * (lam_min / lam) ** 2))


def analyse(A: np.ndarray, b: np.ndarray) -> dict:
    n = A.shape[0]
    n_pad = 1 << math.ceil(math.log2(n))
    n_b = int(math.log2(2 * n_pad))            # state register of the doubled system
    u, s, vt = np.linalg.svd(A)
    order = np.argsort(s)                      # ascending: s[order[0]] smallest
    s_asc, u_asc, v_asc = s[order], u[:, order], vt[order, :].T
    ub = u_asc.T @ b
    x_ref = np.linalg.solve(A, b)
    out = {"n": n, "n_b": n_b, "sigma": s_asc, "kappa": s_asc[-1] / s_asc[0],
           "rows": []}
    for k in KS:
        kap_eff = s_asc[-1] / s_asc[k]
        shift = s_asc[-1]                      # park deflated modes at sigma_max
        # shifted deflation: A' = A + sum_{i<k} (shift - sigma_i) u_i v_i^T
        A_p = A + sum((shift - s_asc[i]) * np.outer(u_asc[:, i], v_asc[:, i])
                      for i in range(k)) if k else A.copy()
        y = np.linalg.solve(A_p, b)
        corr = sum(ub[i] * (1.0 / s_asc[i] - 1.0 / shift) * v_asc[:, i]
                   for i in range(k)) if k else 0.0
        x = y + corr
        p_full = success_prob(s_asc, ub, s_asc[0], None, 0)
        p_defl = success_prob(s_asc, ub, s_asc[k], shift, k)
        out["rows"].append({
            "k": k, "kappa_eff": kap_eff,
            "kappa_Aprime": np.linalg.cond(A_p),
            "n_l": clock_qubits(kap_eff, n_b),
            "p_succ": p_defl, "shot_gain": p_defl / p_full,
            "b_share_deflated": float(np.sum(ub[:k] ** 2) / np.sum(ub ** 2)),
            "x_share_deflated": float(np.sum((ub[:k] / s_asc[:k]) ** 2)
                                      / np.sum((ub / s_asc) ** 2)),
            "identity_err": float(np.linalg.norm(x - x_ref)
                                  / max(np.linalg.norm(x_ref), 1e-300)),
        })
    return out


def report(label: str, path: str) -> None:
    A, b = load(path)
    r = analyse(A, b)
    sig = ", ".join(f"{v:.3g}" for v in r["sigma"])
    print(f"\n{label}  N={r['n']}  n_b(doubled)={r['n_b']}  "
          f"kappa={r['kappa']:.1f}")
    print(f"  sigma (asc): {sig}")
    print("   k  kappa_eff  kappa(A')   n_l  P_succ   shots x  b-share  x-share  identity")
    for row in r["rows"]:
        print(f"  {row['k']:>2}  {row['kappa_eff']:>9.2f}  {row['kappa_Aprime']:>9.2f}"
              f"  {row['n_l']:>4}  {row['p_succ']:.4f}  {row['shot_gain']:>7.1f}"
              f"  {row['b_share_deflated']:.3f}  {row['x_share_deflated']:.3f}"
              f"  {row['identity_err']:.1e}")


def main() -> None:
    print("HHL clock width n_l = max(n_b+1, ceil(log2(kappa_eff+1))) + 1 (neg. eigs)")
    print("P_succ = post-selection probability proxy with C = lambda_min; "
          "shots x = P_succ(k)/P_succ(0)")
    print("b-share / x-share = fraction of ||b||^2 / ||x||^2 carried by the k "
          "deflated modes (the part solved classically)")
    print("identity = ||x_shifted_deflation - A^-1 b|| / ||A^-1 b||")
    for cfl, rel in APRIL.items():
        for it in ITERS:
            p = os.path.join(ROOT, rel, f"system_Ab_nelem5_iter{it}.pkl")
            if os.path.exists(p):
                report(f"[April Frontier HHL]  CFL={cfl:g}  iter={it}", p)
    for tag, rel in (("Aug SQLS local", "2026-08-17-sqls-local-v2/trial_0"),
                     ("Aug HHL local", "2026-08-17-qiskit25-local/trial_0")):
        files = sorted(glob.glob(os.path.join(ROOT, rel, "system_Ab_nelem5_iter*.pkl")),
                       key=lambda f: int(f.rsplit("iter", 1)[1].split(".")[0]))
        for p in (files[0], files[-1]):
            it = p.rsplit("iter", 1)[1].split(".")[0]
            report(f"[{tag}]  CFL=1e10  iter={it}", p)


if __name__ == "__main__":
    sys.exit(main())
