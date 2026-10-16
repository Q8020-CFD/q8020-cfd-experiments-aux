# Reproduce item 6: shifted SVD deflation around HHL

Independent reproduction, 2026-10-15T09:59Z to 2026-10-15T10:09Z (UTC). Own numpy
code only; the dry-check script, the `deflation` module and the solver CSVs were
read AFTER my code was written and are compared against it, not used by it.
Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26` @ `9e8fc7fe`, Python
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
(numpy 2.5.2, qiskit 2.5.2, qiskit-aer 0.17.2 per `tests/data/provenance.json`).
Inputs: the nine archived systems in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/tests/data/system_Ab_*.pkl`
(each a dict `{A, b}`, A 15 x 15 or 6 x 6 float64). Not read: `build-*.md`,
`verify-*.md`, `reproduce-*.md`, `STATUS.md`. Scratch `/tmp/order3-reproduce-6/`
(deleted at the end). Compute spent: one nelem-5 HHL statevector solve
(43.80 s), two nelem-2 solves (5.99 s and 10.85 s), and one circuit-only
build-and-count at nelem 5 for k = 0 and k = 2 (48.56 s total, no simulation).

## Verdict

All four claims reproduce. Every number in the prompt matches my own code to the
printed precision; the solver module and the solver CSVs match my code to 6+
digits (CX counts exactly). Two cosmetic slips in
`06a-deflation-numbers-and-recommendation.md` (x-share rounded 0.602 -> "59 %",
0.727 -> "72 %"; should read 60 % and 73 %). One observation on pre-existing CSV
columns (`lambda_max_orig` / `lambda_min_orig` are |eig|, not singular values).

## My code

```python
# my_deflation.py (own code; no solver imports)
import math, pickle
import numpy as np

def spectrum(A):                      # SVD ascending, cross-checked vs |eig| of the doubling
    U, s, Vt = np.linalg.svd(A); idx = np.argsort(s)
    U, s, V = U[:, idx], s[idx], Vt[idx, :].T
    n = A.shape[0]
    H = np.block([[np.zeros((n, n)), A], [A.T, np.zeros((n, n))]])
    lam = np.sort(np.abs(np.linalg.eigvalsh(H)))
    assert np.allclose(lam[::2], s, rtol=1e-12) and np.allclose(lam[1::2], s, rtol=1e-12)
    return U, s, V

def n_clock(kappa, n_b):
    return max(n_b + 1, math.ceil(math.log2(kappa + 1))) + 1

def p_succ(s_eff, w, C):             # sum_i w_i (C/lambda_i)^2, w_i = |u_i.b|^2/||b||^2
    return float(np.sum(w * (C / s_eff) ** 2))

def analyse(A, b, ks=(0, 1, 2, 3, 4)):
    n = A.shape[0]; n_pad = 1 << math.ceil(math.log2(n)); n_b = int(math.log2(2 * n_pad))
    U, s, V = spectrum(A); x = np.linalg.solve(A, b)
    ub = U.T @ b; w = ub ** 2 / (b @ b); xv = V.T @ x        # x-share by projecting x on V
    p0 = p_succ(s, w, s[0]); rows = []
    for k in ks:
        s_eff = s.copy(); s_eff[:k] = s[-1]; pk = p_succ(s_eff, w, s[k])
        rows.append(dict(k=k, kappa_eff=s[-1] / s[k], n_l=n_clock(s[-1] / s[k], n_b),
                         x_share=float(np.sum(xv[:k] ** 2) / (x @ x)),
                         b_share=float(np.sum(w[:k])), p_succ=pk, shots=pk / p0))
    return dict(n_b=n_b, sigma=s, kappa=s[-1] / s[0], rows=rows)

def shifted_identity(A, b, k):
    U, s, V = spectrum(A); smax = s[-1]; Ap = A.copy()
    for i in range(k):
        Ap += (smax - s[i]) * np.outer(U[:, i], V[:, i])
    y = np.linalg.solve(Ap, b); corr = np.zeros_like(b)
    for i in range(k):
        corr += (U[:, i] @ b) * (1.0 / s[i] - 1.0 / smax) * V[:, i]
    x_ref = np.linalg.solve(A, b); sp = np.linalg.svd(Ap, compute_uv=False)
    top = np.sort(sp)[::-1][:k + 1]
    return dict(rel_err=np.linalg.norm(y + corr - x_ref) / np.linalg.norm(x_ref),
                kappa_Ap=sp.max() / sp.min(), kappa_pred=smax / s[k],
                deflated_spread=top.max() - top.min())
```

```python
# check_runs.py (excerpt): recompute the run metrics from the archived A, b and dq_hhl
r = A @ dq_hhl - b                                   # ||A dq - b||_2
cos = dq_hhl @ dq_lu / (np.linalg.norm(dq_hhl) * np.linalg.norm(dq_lu))   # fidelity = cos^2
rel_l2 = np.linalg.norm(dq_hhl - dq_lu) / np.linalg.norm(dq_lu)
```

```python
# count_k0.py (excerpt): build the nelem-5 circuit as QuantumHHL.solve_one_step does, count only
from math_tools import scale_Ab_by_spectral_radius, convert_to_pow2, convert_system_to_herm
As, bs, rho = scale_Ab_by_spectral_radius(A_q, b, verbosity=0)
Ap, bp = convert_to_pow2(As, bs, verbosity=0); Ah, bh = convert_system_to_herm(Ap, bp, verbosity=0)
circ = H.hhl.construct_circuit(Ah, bh); circ.measure_all()   # H = LinearSystemSolver(...).hhl_solver
fb = quantum_tools.count_circuit_metrics(circ)               # u3+cx, optimization_level 0, seed 0
```

## Commands and wall times (UTC)

| what | command (from the repo root) | start | real |
|---|---|---|---|
| own analysis, 4 key systems | `.venv/bin/python -I /tmp/order3-reproduce-6/my_deflation.py system_Ab_nelem5_iter14.pkl system_Ab_nelem5_iter0.pkl system_Ab_nelem5_iter6.pkl system_Ab_nelem2_iter0.pkl` | 10:01:27Z | < 1 s |
| HHL nelem 5, k = 2 | `.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -hhl_deflate_k 2 -shots 0 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow -outdir /tmp/order3-reproduce-6/k2` | 10:01:27Z | 43.80 s (user 108.61 s) |
| HHL nelem 2, k = 1 | same flags with `-nelem 2 -hhl_deflate_k 1 -outdir /tmp/order3-reproduce-6/n2k1` | 10:02:50Z | 5.99 s |
| HHL nelem 2, k = 0 (baseline) | same flags with `-nelem 2 -hhl_deflate_k 0 -outdir /tmp/order3-reproduce-6/n2k0` | 10:02:57Z | 10.85 s |
| module vs mine | `.venv/bin/python /tmp/order3-reproduce-6/compare_module.py` | 10:04Z | < 1 s |
| circuit-only count, nelem 5, k = 2 then k = 0 | `.venv/bin/python /tmp/order3-reproduce-6/count_k0.py` | 10:07:30Z | 48.56 s (k = 2: build 11.1 s + count 6.2 s; k = 0: build 20.8 s + count 9.5 s) |
| own analysis, remaining 5 systems | `my_deflation.py system_Ab_nelem5_iter{1,2,3,4,5}.pkl` | 10:08Z | < 1 s |

Archived systems written by the three runs are bit-identical (`cmp`) to
`tests/data/system_Ab_nelem5_iter0.pkl` (sha256
`7c2551de3f326b7aa493d8a8014f6ad880302cbcdcacb0f6c514c98f113b148f`) and
`tests/data/system_Ab_nelem2_iter0.pkl`.

## Claim A: dry-check numbers

Columns: mine / `kappa_eff_deflation_check.py` output / `deflation` module
(`deflate().kappa_eff`, `.x_share_classical`, `clock_qubits`, `success_prob`,
`b_share`) / `06a` note where it tabulates the value. n_b = 5 for N = 15
(padded 16, doubled 32); n_b = 4 for N = 6.

### April CFL 1e10, iteration 14 (`system_Ab_nelem5_iter14.pkl`), kappa = 67.6334 (script 67.63, module 67.633389)

Singular values ascending, mine: 0.8607, 1.654, 3.876, 4.236, 7.389, 8.214,
13.55, 15.38, 18.37, 20.22, 27.29, 28.77, 39.57, 51.19, 58.21 (script, 3 s.f.:
0.861, 1.65, 3.88, 4.24, 7.39, 8.21, 13.5, 15.4, 18.4, 20.2, 27.3, 28.8, 39.6,
51.2, 58.2; module `sigma` equals mine to rtol 1e-14). Also equal to the
|eigenvalues| of the Hermitian doubling, in pairs (assert in `spectrum`).

| k | kappa_eff mine / script / module | n_l mine / script / module | x-share mine / script / module / 06a | P_succ mine / script / module | shots x mine / script / module / 06a |
|---|---|---|---|---|---|
| 0 | 67.633 / 67.63 / 67.633389 | 8 / 8 / 8 | 0 / 0 / 0 / 0 % | 0.00550 / 0.0055 / 0.005498 | 1.00 / 1.0 / 1.0000 / 1.0 |
| 1 | 35.187 / 35.19 / 35.187308 | 7 / 7 / 7 | 0.2255 / 0.225 / 0.225492 / 23 % | 0.01573 / 0.0157 / 0.015732 | 2.86 / 2.9 / 2.8616 / 2.9 |
| 2 | 15.018 / 15.02 / 15.017565 | 7 / 7 / 7 | 0.3524 / 0.352 / 0.352414 / 35 % | 0.07223 / 0.0722 / 0.072229 | 13.14 / 13.1 / 13.1378 / 13.1 |
| 3 | 13.743 / 13.74 / 13.742973 | 7 / 7 / 7 | 0.6024 / 0.602 / 0.602408 / "59 %" | 0.05311 / 0.0531 / 0.053108 | 9.66 / 9.7 / 9.6599 / 9.7 |
| 4 | 7.879 / 7.88 / 7.878801 | 7 / 7 / 7 | 0.7273 / 0.727 / 0.727274 / "72 %" | 0.11127 / 0.1113 / 0.111267 | 20.24 / 20.2 / 20.2385 / 20.2 |

### August CFL 1e10, iteration 0 (`system_Ab_nelem5_iter0.pkl`), kappa = 95.9779 (script 95.98, module 95.977890)

| k | kappa_eff mine / script / module | n_l | x-share mine / script / module / 06a | P_succ mine / script / module | shots x mine / script / module / 06a |
|---|---|---|---|---|---|
| 0 | 95.978 / 95.98 / 95.977890 | 8 / 8 / 8 | 0 / 0 / 0 / 0 % | 0.01426 / 0.0143 / 0.014259 | 1.00 / 1.0 / 1.0000 / 1.0 |
| 1 | 43.307 / 43.31 / 43.306592 | 7 / 7 / 7 | 0.9128 / 0.913 / 0.912786 / 91 % | 0.00611 / 0.0061 / 0.006115 | 0.43 / 0.4 / 0.4289 / 0.4 |
| 2 | 16.316 / 16.32 / 16.315810 | 7 / 7 / 7 | 0.9234 / 0.923 / 0.923435 / 92 % | 0.03783 / 0.0378 / 0.037829 | 2.65 / 2.7 / 2.6531 / 2.7 |
| 3 | 15.658 / 15.66 / 15.658284 | 7 / 7 / 7 | 0.9377 / 0.938 / 0.937681 / - | 0.03347 / 0.0335 / 0.033470 | 2.35 / 2.3 / 2.3473 / - |
| 4 | 7.867 / 7.87 / 7.866509 | 7 / 7 / 7 | 0.9568 / 0.957 / 0.956794 / 96 % | 0.09221 / 0.0922 / 0.092208 | 6.47 / 6.5 / 6.4668 / 6.5 |

### August CFL 1e10, iteration 6 (`system_Ab_nelem5_iter6.pkl`), kappa = 67.3850 (script 67.39, module 67.385047)

| k | kappa_eff mine / script / module | n_l | x-share mine / script / module | P_succ mine / script / module | shots x mine / script / module |
|---|---|---|---|---|---|
| 0 | 67.385 / 67.39 / 67.385047 | 8 / 8 / 8 | 0 / 0 / 0 | 0.00253 / 0.0025 / 0.002525 | 1.00 / 1.0 / 1.0000 |
| 1 | 34.956 / 34.96 / 34.955730 | 7 / 7 / 7 | 0.000008 / 0.000 / 0.000008 | 0.00938 / 0.0094 / 0.009385 | 3.72 / 3.7 / 3.7161 |
| 2 | 14.919 / 14.92 / 14.919223 | 7 / 7 / 7 | 0.6393 / 0.639 / 0.639341 | 0.01861 / 0.0186 / 0.018608 | 7.37 / 7.4 / 7.3682 |
| 3 | 13.802 / 13.80 / 13.801816 | 7 / 7 / 7 | 0.6422 / 0.642 / 0.642230 | 0.02157 / 0.0216 / 0.021569 | 8.54 / 8.5 / 8.5410 |
| 4 | 7.859 / 7.86 / 7.858943 | 7 / 7 / 7 | 0.6423 / 0.642 / 0.642314 | 0.06651 / 0.0665 / 0.066509 | 26.34 / 26.3 / 26.3362 |

### nelem 2, iteration 0 (`system_Ab_nelem2_iter0.pkl`), kappa = 38.3062 (not in the script; module 38.306162)

| k | kappa_eff mine / module | n_l mine / module | x-share mine / module | P_succ mine / module | shots x mine / module |
|---|---|---|---|---|---|
| 0 | 38.306 / 38.306162 | 7 / 7 | 0 / 0 | 0.03469 / 0.034689 | 1.00 / 1.0000 |
| 1 | 6.850 / 6.849833 | 6 / 6 | 0.9511 / 0.951135 | 0.05372 / 0.053715 | 1.55 / 1.5485 |
| 2 | 5.199 / 5.198860 | 6 / 6 | 0.9525 / 0.952482 | 0.09076 / 0.090765 | 2.62 / 2.6165 |

Conclusion A. Every value in the prompt and in `06a` reproduces from my own SVD:
the singular values, kappa 67.63 / 95.98 / 67.39, kappa_eff per k, the clock
widths (8 at k = 0, 7 for k >= 1, the n_b + 1 = 6 floor plus one binding from
k = 1 on), the x-shares, P_succ and the shot factors; iteration 0 at k = 2
gives 96.0 -> 16.3 and 92.3 %. My x-share uses a different formulation
(projection of the LU solution onto the k smallest right-singular vectors)
from the script's and module's sum of (u_i.b/sigma_i)^2, and the two agree to
1e-6. The module's functions equal my code to every printed digit. The only
discrepancies are rounding slips in the `06a` iteration-14 table: 0.602 is
written "59 %" (should be 60 %) and 0.727 is written "72 %" (should be 73 %);
the prompt repeats both. Note also that the iteration-6 x-share jumps from
0.0008 % at k = 1 to 63.9 % at k = 2: the first mode carries nothing of that
update, so "deflating the k worst-conditioned modes" is not monotone in payoff
per mode.

## Claim B: the shifted identity, kappa(A') and the deflated values

Per system, worst case over k = 1..4 (mine; script `identity` column and the
module's `recombine` for the systems it covers in parentheses):

| system | max rel err of y + corr vs A^-1 b | max rel diff kappa(A') vs sigma_max/sigma_{k+1} | max spread of the k+1 values at sigma_max (abs; rel to sigma_max) |
|---|---|---|---|
| nelem5 iter14 | 3.66e-15 (script 3.7e-15 to 3.9e-15; module 3.72e-15 to 3.93e-15) | 5.0e-15 | 7.11e-14; 1.2e-15 |
| nelem5 iter0 | 2.93e-15 (script 2.8e-15 to 3.0e-15; module 2.76e-15 to 3.06e-15) | 4.6e-15 | 4.97e-14; 9.5e-16 |
| nelem5 iter1 | 1.39e-15 | 1.7e-15 | 3.55e-14; 5.9e-16 |
| nelem5 iter2 | 2.18e-15 | 1.5e-15 | 4.97e-14; 8.5e-16 |
| nelem5 iter3 | 1.82e-15 | 1.9e-15 | 4.97e-14; 8.6e-16 |
| nelem5 iter4 | 1.73e-15 | 7.7e-16 | 2.84e-14; 4.9e-16 |
| nelem5 iter5 | 2.45e-15 | 1.6e-15 | 3.55e-14; 6.1e-16 |
| nelem5 iter6 | 1.96e-15 (script 1.1e-15 to 1.8e-15; module 8.5e-16 to 1.78e-15) | 2.0e-15 | 3.55e-14; 6.1e-16 |
| nelem2 iter0 | 6.56e-16 (module 4.48e-16 to 5.53e-16) | 5.1e-16 | 1.42e-14; 8.2e-16 |

Conclusion B. On all nine archived systems and k = 1..4 the recombined
x = A'^-1 b + sum_{i<=k} (u_i.b)(1/sigma_i - 1/sigma_max) v_i equals A^-1 b to
at most 3.7e-15 relative (nelem 5) and 6.6e-16 (nelem 2), i.e. double-precision
roundoff; kappa(A') computed from the singular values of A' equals
sigma_max/sigma_{k+1} to at most 5e-15 relative; the k deflated singular values
land on sigma_max with a spread of at most 7.1e-14 absolute (1.2e-15 relative to
sigma_max 58.2). The identity is exact in exact arithmetic (A' has the same
singular vectors as A with sigma_i replaced by sigma_max for i <= k, so
A'^-1 b differs from A^-1 b by exactly the correction term) and the numerics
confirm it.

## Claim C: the HHL runs

### nelem 5, `-hhl_deflate_k 2` (`/tmp/order3-reproduce-6/k2`, 43.80 s wall)

| quantity | solver CSV | mine from the archived A, b, dq columns |
|---|---|---|
| kappa (original A) | 95.9778901432456 | 95.977890 (sigma 0.546382 to 52.440580) |
| kappa_eff | 16.315810025631496 | 16.315810 (= sigma_max/sigma_3 = 52.4406/3.2141) |
| `condition_number` (of the matrix the circuit was built from) | 16.315810025631507 | 16.3158 (= kappa(A')) |
| x_share_classical | 0.9234345559463597 | 0.923435 |
| n_clock / circ_qubits | 7 / 13 | 7 / 13 (= n_b 5 + n_clock 7 + 1 flag) |
| fb_cx_count / fb_total_gates / fb_depth | 1,022,314 / 2,715,252 / 2,024,100 | 1,022,314 / 2,715,252 / 2,024,100 (circuit-only rebuild, exact) |
| t_svd_s | 8.49e-5 s | - |
| fidelity | 0.9999948974490167 | cos^2(dq_hhl, dq_lu) = 0.9999948974490163 |
| linsys_residual ||A dq_hhl - b||_2 | 0.07090860660426168 | 7.090861e-2 (5.73e-3 relative to ||b||) |
| l2_error_rel | 0.002259393035923076 | 2.259393e-3 |
| l2_error_abs | 0.006110718102547998 | 6.110718e-3 |
| dq_lu vs my solve(A, b) | - | max abs 7.1e-16 |

### nelem 2, `-hhl_deflate_k 1` (`/tmp/order3-reproduce-6/n2k1`, 5.99 s wall)

| quantity | solver CSV | mine |
|---|---|---|
| kappa -> kappa_eff | 38.306161601199506 -> 6.8498325090581 | 38.306162 -> 6.849833 (sigma 0.449875, 2.516, ..., 17.232978) |
| x_share_classical | 0.9511345924972174 | 0.951135 |
| n_clock / circ_qubits | 6 / 11 | 6 / 11 (n_b 4 + 6 + 1) |
| fb_cx_count | 116,067 | 116,067 (fb_total_gates 311,810; fb_depth 232,343) |
| fidelity | 0.9999941603559575 | cos^2 = 0.9999941603559568 |
| linsys_residual | 0.01624775250704347 | 1.624775e-2 |
| l2_error_rel | 0.0024201253250294348 | 2.420125e-3 |

### nelem 2, `-hhl_deflate_k 0` baseline (`/tmp/order3-reproduce-6/n2k0`, 10.85 s wall)

kappa = kappa_eff = 38.30616160119951, x_share 0.0, n_clock 7, circ_qubits 12,
fb_cx_count 234,899 (= `HHL_NELEM2_FB_CX` in `tests/test_circuit_metrics.py`),
fidelity 0.9999986356113313 (mine cos^2 0.9999986356113295; the gate fixture
`ref_hhl_nelem2_iter0.npz` records 0.9999986356113308), linsys_residual
0.0033519326408426777 (mine 3.351933e-3; fixture 0.0033519326408439454). The
dq_hhl column equals the fixture `dq` to the 8 printed digits.

Conclusion C. The k = 2 run's kappa, kappa_eff and x_share are the values my
own SVD gives for the archived iteration-0 Jacobian (which is byte-identical
to the fixture), n_clock 7 and 13 qubits follow from the clock formula with
kappa_eff, the CX count 1,022,314 is reproduced exactly by rebuilding the
circuit from A' through the same scale / pad / double / construct path and
counting in the u3+cx basis, and the solver's fidelity, residual and relative
L2 are the cosine-squared, ||A dq - b||_2 and ||dq - dq_lu||/||dq_lu|| I
compute from its own dq columns, to 15 digits. Same for nelem 2 at k = 1
(38.31 -> 6.85, 6 clock qubits, 11 qubits, 116,067 CX, x-share 0.951) and the
k = 0 baseline, which also reproduces the committed gate fixture. The metrics
are measured against the ORIGINAL system after the classical recombination,
which is the right reference for a hybrid; they say nothing about the quality
of the quantum part alone (see D).

## Claim D: resource accounting

From my numbers (iteration 0 is the only nelem-5 system actually run; iteration
14 is the dry check):

| case | k | kappa -> kappa_eff | classical share of ||x||^2 | quantum share of ||x||^2 | qubits | fb CX | CX saving |
|---|---|---|---|---|---|---|---|
| nelem 5, iter 0 (run) | 2 | 95.98 -> 16.32 | 92.34 % | 7.66 % | 14 -> 13 | 2,054,602 -> 1,022,314 | 50.24 % (factor 2.010) |
| nelem 5, iter 14 (dry check) | 2 | 67.63 -> 15.02 | 35.24 % | 64.76 % | 14 -> 13 (predicted) | not run | - |
| nelem 2, iter 0 (run) | 1 | 38.31 -> 6.85 | 95.11 % | 4.89 % | 12 -> 11 | 234,899 -> 116,067 | 50.59 % (factor 2.024) |

The nelem-5 k = 0 CX count 2,054,602 is not stored in any CSV, fixture or JSON on
this machine (searched the repo, `q8020-cfd-experiments/results`, `~/q8020` and
`/tmp`); I obtained it by building the k = 0 circuit (14 qubits, n_clock 8) the
way `solve_one_step` does and running the solver's own `count_circuit_metrics`,
without simulating it (20.8 s build + 9.5 s count). The same rebuild at k = 2
returned 1,022,314, identical to the run's CSV, which validates the method.
The saving is one clock qubit (8 -> 7), which halves the QPE and so the CX
count (factor 2.010 at nelem 5, 2.024 at nelem 2).

Conclusion D. For the nelem-5 iteration-0 case the quantum solve delivered
7.66 % of ||x||^2; 92.34 % of the update came from the classical rank-2
correction, and the circuit was 50.24 % cheaper in CX (2,054,602 -> 1,022,314)
and one qubit narrower (14 -> 13). For the iteration-14 steady-state Jacobian
the dry check predicts 35.24 % classical (64.76 % quantum) at k = 2 with the
same one-qubit, ~2x CX saving, but that case was not run. The classical
pre-step is `numpy.linalg.svd` of the full dense 15 x 15 Jacobian (8.5e-5 s in
the CSV, against 35.3 s of circuit generate + transpile + run); that SVD is a
complete classical solve at this size: x = V Sigma^-1 U^T b from the same
factorization equals A^-1 b to 2.9e-15 relative (checked on all three cases).
So the hybrid's quantum kernel solves a problem whose full answer the pre-step
already holds, and the fidelity 0.999995 / residual 7.09e-2 figures are for the
recombined x, 92 % of which is classical in the iteration-0 run. Any claim
should be stated as resource reduction for the HHL kernel given a classical
rank-k preconditioner, with the x-share next to it, and no speedup.

## Observations outside the claims

- `qc_metadata` columns `lambda_max_orig` / `lambda_min_orig` (37.2149 / 7.4643
  at nelem 5 k = 2; 6.0292 / 1.1818 at nelem 2 k = 0) are the max / min
  |eigenvalue| of the (deflated) non-symmetric matrix, not singular values;
  their ratio (4.99, 5.10) is not kappa. `condition_number` (16.3158, 38.3062)
  is the true 2-norm condition number. Pre-existing column semantics, present
  at k = 0 too; not an item-6 defect, but a reader of the CSV should know.
- `06a` iteration-14 table rounding: k = 3 "59 %" should be 60 % (0.602), k = 4
  "72 %" should be 73 % (0.727).
- The iteration-6 Jacobian's first singular mode carries 8e-6 of ||x||^2, so
  k = 1 there buys the kappa reduction (67.4 -> 35.0) with no classical share;
  the x-share is strongly case-dependent and must be reported per run, as the
  module does.

Scratch `/tmp/order3-reproduce-6/` deleted after this file was written.
