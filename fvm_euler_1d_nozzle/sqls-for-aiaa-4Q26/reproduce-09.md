# reproduce-09: independent recompute of the SQLS shots-mode fidelity collapse (b-pad eps)

Reproducer run 2026-10-15T03:00:55Z to 2026-10-15T03:12Z (UTC), independent
of any build/verify narrative (none read). Everything below was recomputed
from the archived artifacts and from four short solver runs with the code
shown inline.

## Environment

- Repo `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26` @ `3a88a37d` (2026-10-15T02:55:48Z); `main` @
  `ef7f0a8b` (2026-08-17T23:22:59Z) is the pre-fix state.
- Python 3.12.10 (`.venv`), numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2, `sqls`
  from `/Users/agallojr/proj/src/q8020/sqls/src/sqls`.
- Archive: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`
  (nelem 5, cfl 1e10, 150000 shots, full_svd). Pickles are
  `{'A': (15,15) float64, 'b': (15,) float64}`, i.e. the UNPADDED systems.
- Scratch `/tmp/order1-reproduce-9/` (deleted at the end). Nothing written
  under `results/`; no git operations.

## A. Padded systems: probability mass on the 15 true entries

For each archived `system_Ab_nelem5_iter{0..6}.pkl` the 15 x 15 system was
padded to 16 x 16 two ways: with the repo's own
`math_tools.convert_to_pow2(A, b, eps=...)` and with my own padding (unit
diagonal in row/col 15, constant `eps` in `b[15]`). The two paddings were
bit-identical (`np.array_equal`) for all 7 systems and both eps values.
Solved with `numpy.linalg.solve`. The leading 15 entries of the 16 x 16
solution agree with the direct 15 x 15 solve to at most 2.5e-15 (max
relative, roundoff). `mass` = sum of squares of the 15 true entries over the
total; `E[shots]` = 150000 x mass.

| iter | ‖b‖₂ | ‖dq_true‖₂ (15 entries) | eps | x[15] (pad entry) | mass on true 15 | E[shots on true 15] of 150000 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.24e+01 | 2.71e+00 | 1e-8 | 1.00e-08 | 1.000 | 1.50e+05 |
| 1 | 7.61e-01 | 1.68e-01 | 1e-8 | 1.00e-08 | 1.000 | 1.50e+05 |
| 2 | 7.10e-02 | 2.36e-02 | 1e-8 | 1.00e-08 | 1.000 | 1.50e+05 |
| 3 | 2.69e-03 | 4.23e-04 | 1e-8 | 1.00e-08 | 1.000 | 1.50e+05 |
| 4 | 4.55e-05 | 1.90e-06 | 1e-8 | 1.00e-08 | 1.000 (1 - 2.8e-5) | 1.50e+05 |
| 5 | 2.61e-07 | 1.07e-08 | 1e-8 | 1.00e-08 | 5.36e-01 | 8.03e+04 |
| 6 | 1.26e-09 | 7.35e-11 | 1e-8 | 1.00e-08 | 5.41e-05 | 8.11e+00 |
| 0..6 | (same) | (same) | 0.0 | 0.00e+00 | 1.000 | 1.50e+05 |

With eps = 1e-8 the mass is exactly ‖dq‖²/(‖dq‖² + 1e-16): it halves when
‖dq‖ crosses 1e-8 (iter 5) and collapses to 5.4e-5 at iter 6, where only
about 8 of 150000 shots are expected to land on the 15 real unknowns. With
eps = 0 the pad entry is identically 0 and the mass is 1.000 at every
iteration. Conditioning of the unpadded A (cond₂): 95.98, 59.92, 66.31,
67.37, 67.39, 67.39, 67.39 for iter 0..6; this matches the archived
`qc_metadata_sqls_*.csv` `condition_number` column, confirming the pickles
are the systems that run actually solved.

```python
# taskA.py  (run with .venv/bin/python -I from the repo root)
import pickle, sys
import numpy as np
sys.path.insert(0, '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver')
import math_tools
math_tools.set_verbosity(0)
ARCH = ('/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/'
        'fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0')
def my_pad(A, b, eps):
    n = A.shape[0]; N = 1 << (n - 1).bit_length()
    Ap = np.eye(N); Ap[:n, :n] = A
    bp = np.full(N, eps, dtype=float); bp[:n] = b
    return Ap, bp
for it in range(7):
    d = pickle.load(open(f'{ARCH}/system_Ab_nelem5_iter{it}.pkl', 'rb'))
    A, b = d['A'], d['b']
    for eps in (1e-8, 0.0):
        Ap, bp = math_tools.convert_to_pow2(A, b, eps=eps)
        Ap2, bp2 = my_pad(A, b, eps)
        assert np.array_equal(Ap, Ap2) and np.array_equal(bp, bp2)
        x = np.linalg.solve(Ap, bp); x_true = np.linalg.solve(A, b)
        reldiff = np.max(np.abs(x[:15] - x_true)) / np.max(np.abs(x_true))
        mass = np.sum(x[:15]**2) / np.sum(x**2)
        print(it, eps, np.linalg.norm(b), np.linalg.norm(x[:15]), x[15],
              mass, 150000 * mass, reldiff, np.linalg.cond(A))
```

## B. Archived August final iteration

`hhl_metrics_nelem5_statevector_shots150000.csv`, `fidelity` column:
0.999981, 0.999965, 0.999966, 0.999979, 0.999968, 0.999954 for iter 0..5,
then **0.451025** at iter 6 (`l2_error_rel` 0.784). The repo's `fidelity()`
(`quantum_tools.py:123`) normalizes both vectors and returns qiskit
`state_fidelity`, i.e. the squared overlap; my cosine between the archived
`dq_lu` and `dq_sqls` at iter 6 is 0.6716 and 0.6716² = 0.4510, consistent.

`dq_nelem5_iter6_statevector_shots150000.csv`: `dq_sqls` has **4 nonzero
entries of 15** (0-based indices 1, 5, 12, 14; the other 11 are exactly 0)
with only **two distinct magnitudes**: 2.5820587141701135e-11 (indices 1,
12, 14) and 5.164117428340227e-11 (index 5), the second exactly 2x the
first. The shots reconstruction (`sqls/runtime/quantum.py::_run_shots`) is
`x_i = sqrt(n_i / 150000) x ‖x_pow2‖` with the sign restored classically.
With ‖x_pow2‖ = sqrt(1e-16 + 7.354e-11²) = 1.000027e-8 the single-shot
amplitude is 1.000027e-8 / sqrt(150000) = 2.58206e-11, matching the smaller
value to 7 digits; 2x that is sqrt(4/150000). So the pattern is **1, 1, 1
and 4 shots: 7 shots total landed on the 15 real unknowns** (Task A
predicts 8.1), and the remaining 149993 landed on the pad index 15, whose
reconstructed amplitude (about 1e-8) is then discarded by `x[:nsys]`. Three
of the four surviving entries are forced to the same magnitude regardless
of their true values (dq_lu there: 1.64e-11, 1.91e-11, 1.55e-11) and 11
entries are zeroed, which is why the direction (fidelity) collapses while
the norm (6.83e-11 vs 7.35e-11, set classically) stays plausible. ‖dq_lu‖
at iter 5 was 1.07e-8 and iter 6 7.35e-11, bracketing the 1e-8 pad exactly
as Task A predicts.

## C. Current branch, matched case (two runs) and the eps = 0 pad

Commands (from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, each
timed with `/usr/bin/time -p`, stdout to a log):

```
.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow -outdir /tmp/order1-reproduce-9/branch_run1
.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow -outdir /tmp/order1-reproduce-9/branch_run2
```

Wall: run1 2.41 s (2026-10-15T03:02:46Z to 03:02:48Z), run2 2.33 s
(03:02:48Z to 03:02:51Z); solver-reported "6 steps in 0.58 s", each SQLS
solve 0.07 s to 0.09 s. Both runs: **7 Newton iterations (iter 0..6)**,
stopped by `SOLUTION CONVERGED at iteration 6` on res/res0 (4.09e-11 and
7.97e-11 against tolerance 1e-10).

| iter | run1 fidelity | run1 residual_total | run2 fidelity | run2 residual_total | August residual_total |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.999958 | 1.238e+01 | 0.999987 | 1.238e+01 | 1.238e+01 |
| 1 | 0.999988 | 6.939e-01 | 0.999950 | 6.493e-01 | 7.612e-01 |
| 2 | 0.999980 | 5.779e-02 | 0.999954 | 7.371e-02 | 7.096e-02 |
| 3 | 0.999987 | 1.821e-03 | 0.999977 | 4.630e-03 | 2.690e-03 |
| 4 | 0.999978 | 1.552e-05 | 0.999992 | 7.106e-05 | 4.545e-05 |
| 5 | 0.999974 | 1.538e-07 | 0.999985 | 1.595e-07 | 2.608e-07 |
| 6 | **0.999974** | **5.057e-10** | **0.999978** | **9.859e-10** | 1.260e-09 (fid 0.451) |

Final-iteration fidelity is >= 0.99 in both runs (0.999974, 0.999978; the
August value at the same iteration was 0.451). Shot-to-shot spread across
all 14 solves: fidelity 0.99995 to 0.99999; final residual_total 5.06e-10
vs 9.86e-10 (factor 1.95), same iteration count. ‖dq_true‖ at iter 6 was
2.1e-11 (run1), well below the old 1e-8 pad, so the old failure would have
fired here too.

The branch run writes `system_Ab_nelem5_iter{0..6}.pkl` into the outdir;
`b` is still saved unpadded (shape (15,)), so the pad is applied inside the
solver. Code: `quantum_tools.py:829-830` in `QuantumSQLS.solve_one_step`
calls `convert_to_pow2(A_o, b_o, verbosity=self.verbosity, eps=0.0)`;
`math_tools.py:28` has the default `eps=1e-8`, `:63` pads `B` with
`constant_values=eps`, `:66` puts the unit diagonal in A's pad block.
`git diff main..HEAD` shows `main` called
`convert_to_pow2(A_o, b_o, verbosity=self.verbosity)` with no `eps`, i.e.
1e-8. In-process confirmation (the solver's own path, `convert_to_pow2`
wrapped to record its arguments; statevector mode, no save): for both the
branch iter-6 system and the August iter-6 system the captured `eps` was
`0.0`, `len(b_pow2) == 16`, `b_pow2[15] == 0.0`, and the statevector SQLS
solution matched LU to 2.3e-15 and 3.8e-15 relative.

```python
# taskC_eps.py
import pickle, sys
import numpy as np
sys.path.insert(0, '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver')
import math_tools, quantum_tools
math_tools.set_verbosity(0)
cap = {}; _orig = quantum_tools.convert_to_pow2
def spy(A, B, verbosity=None, eps=1e-8):
    Ap, bp = _orig(A, B, verbosity=verbosity, eps=eps)
    cap['eps'] = eps; cap['b_pow2'] = bp.copy(); return Ap, bp
quantum_tools.convert_to_pow2 = spy
for src in ('/tmp/order1-reproduce-9/branch_run1', ARCH):   # ARCH as in A
    d = pickle.load(open(f'{src}/system_Ab_nelem5_iter6.pkl', 'rb'))
    s = quantum_tools.QuantumSQLS(nshots=0, verbosity=0,
                                  output_dir='/tmp/order1-reproduce-9/spy')
    s.savedata = False
    x = s.solve_one_step(d['A'], d['b'], nelem=5, iter=6)
    x_lu = np.linalg.solve(d['A'], d['b']); x = x if x @ x_lu > 0 else -x
    print(cap['eps'], len(cap['b_pow2']), cap['b_pow2'][15],
          np.linalg.norm(x - x_lu) / np.linalg.norm(x_lu))
```

Provenance check: the iter-0 `A` and `b` in the August pickle are
bit-identical (`np.array_equal`) to those from both new runs (same initial
state, same Jacobian code), so the archived systems are directly comparable.

## D. Why LU and statevector SQLS diverge in residual_total

Pair (two short runs, from the repo root):

```
.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver LU   -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir /tmp/order1-reproduce-9/lu3
.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -cfl 1e10 -iters 3 -initers 1 -shots 0 -sqls_method full_svd -sqls_repeats 1 -noshow -outdir /tmp/order1-reproduce-9/sqls_sv3
```

Wall 0.93 s (LU, 03:02:51Z) and 1.94 s (SQLS statevector, 03:02:52Z to
03:02:54Z). Per-step linear-solve agreement in the SQLS run
(`dq_nelem5_iter*_statevector.csv`): ‖dq_sqls - dq_lu‖/‖dq_lu‖ = 1.8e-15,
1.5e-15, 1.5e-15; fidelity 1.0. Residual file row n is ‖r(q_n)‖, the
residual before the n-th update, so with `-iters 3` the last row is after
two Newton updates.

| row | LU residual_total | SQLS (shots 0) residual_total | abs diff | rel diff |
|---:|---:|---:|---:|---:|
| 0 | 12.375368413827264 | 12.375368413827264 | 0 | 0 |
| 1 | 0.5686791352317027 | 0.568679135231724 | 2.13e-14 | 3.75e-14 |
| 2 | 0.05832886414347176 | 0.05832885640886122 | **7.74e-09** | **1.33e-07** |

Mechanism (`time_solvers.py:395` `eps_v = sqrt(2.22e-16)·‖q_v‖₂`, `:419`
`J[:, j] = -(r1 - r0)/eps_v`). At q_1, eps_v = [2.35e-8, 3.98e-8, 7.07e-8]
for (rho, rhou, rhoE). The forward-difference entries carry a roundoff term
u·(residual scale)/eps_v, i.e. a relative noise floor of order
sqrt(u) = 1.5e-8 on J, whose bit pattern is re-rolled by ANY change of q at
or above the ulp level. Row 0 to 1: both runs use the bit-identical J(q_0)
and differ only through dq (1.8e-15), so ‖r(q_1)‖ differs by
≲ ‖J‖·‖δq‖ ≈ 60 x 5e-15 ≈ 3e-13 (observed 2e-14). Row 1 to 2: J(q_1) is
re-evaluated at two q_1's that differ by 1e-15, so δJ/J jumps to the
sqrt(u) floor; δ(dq)/dq ≲ cond₂(A)·δJ/J = 60 x 1.3e-8 ≈ 8e-7 (bound), and
δ‖r(q_2)‖/‖r(q_2)‖ ≈ ‖J‖·‖δdq‖/‖r(q_2)‖ ≲ 60 x 3e-8 x 0.167 / 0.0583 ≈ 5e-6
(bound). Amplification from the 1e-15 dq agreement to the Jacobian
difference is ≈ 1.3e-8 / 1e-15 ≈ 1.3e7.

Direct measurement, in-process (solver built as in `nozzle_1d_solver.py`,
one LU step to q_1, then the Newton pieces at q_1 and at q_1(1 + 1e-15·N(0,1))
for six seeds; the unperturbed baseline repeats bit-identically and its
‖r(q_2)‖ = 0.05832886414346909 reproduces the LU run's row 2 to 4.6e-14):

| seed | ‖δq‖/‖q‖ | ‖δJ‖_F/‖J‖_F | ‖δb‖/‖b‖ | ‖δdq‖/‖dq‖ | δ‖r(q_2)‖/‖r(q_2)‖ |
|---:|---:|---:|---:|---:|---:|
| 0 | 9.8e-16 | 1.16e-08 | 2.3e-13 | 2.05e-08 | 1.55e-07 |
| 1 | 6.5e-16 | 1.12e-08 | 1.4e-13 | 3.11e-08 | 2.64e-07 |
| 2 | 1.1e-15 | 1.51e-08 | 1.8e-13 | 3.97e-08 | 2.16e-07 |
| 3 | 7.3e-16 | 1.29e-08 | 1.6e-13 | 3.55e-08 | 2.54e-08 |
| 4 | 9.3e-16 | 1.08e-08 | 1.7e-13 | 2.25e-08 | 4.59e-08 |
| 5 | 8.7e-16 | 1.38e-08 | 1.7e-13 | 2.50e-08 | 1.25e-07 |

So a 1e-15 perturbation of q produces a 1.1e-8 to 1.5e-8 relative change in
the FD Jacobian, 2e-8 to 4e-8 in the Newton update, and 2.5e-8 to 2.6e-7 in
the next residual_total; the observed LU-vs-SQLS gap of 1.33e-7 at row 2
sits inside that range. Expected relative difference after the third
solve's residual is of the same order (each step re-rolls δJ at the sqrt(u)
floor; cond ≈ 60), i.e. ~1e-7, seven orders above the per-step dq
agreement. This is a property of the finite-difference Jacobian, not of
the quantum solver.

```python
# taskD_sens.py (core)
import os, sys; import numpy as np
ROOT = '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver'
sys.path.insert(0, ROOT); os.chdir(ROOT)
import math_tools; from case import SimCase; from mesh import Mesh
from space_solvers import SpaceSolver; from time_solvers import BDFTimeSolver
math_tools.set_verbosity(0)
ss = SpaceSolver(SimCase(scaling_mode='compressible_cinf'), Mesh(5, 0, 10, nondim=True))
ts = BDFTimeSolver(ss, 1e10, True, 1e-2, 1, 'BDF1', 'LU', {'output_dir': '/tmp/order1-reproduce-9/so'})
ss.init_sol(); q = ss.get_num_sol(); ts.init_from_q(q)
ts.solve_one_step(q); ts.update_after_one_step(q)
ls = ts.linsys_solver; q1 = q.copy()   # get_num_sol() aliases solver state
def pieces(qin):
    qq = qin.copy(); resid = np.zeros_like(qq)
    ts.nrestart = ts.curr_restart_levels(); ts.update_phystime_coeffs(ts.nrestart)
    tsrc = ts.compute_temporal_source(qq); eps = ls.compute_sol_epsilon(qq)
    ls.update_sol_and_residual(qq, resid)
    b = ls.compute_unsteady_residual(qq, resid, tsrc).swapaxes(0, 1).reshape(-1)
    A = ls.compute_Jacobian_matrix_FD(qq, resid, ls.dt, eps)
    dq = np.linalg.solve(A, b).reshape(ss.nelem, 3).T
    r2 = np.zeros_like(qq); ls.update_sol_and_residual(qq + dq, r2)
    return A, b, dq, np.linalg.norm(r2)
A, b, dq, r2 = pieces(q1); rng = np.random.default_rng(0)
for seed in range(6):
    Ap, bp, dqp, r2p = pieces(q1 + 1e-15 * q1 * rng.standard_normal(q1.shape))
    print(np.linalg.norm(Ap - A) / np.linalg.norm(A), np.linalg.norm(bp - b) / np.linalg.norm(b),
          np.linalg.norm(dqp - dq) / np.linalg.norm(dq), abs(r2p - r2) / r2)
```

## Conclusion

The archived evidence supports the root cause. Recomputed from the August
pickles, the eps = 1e-8 pad puts a 16th unknown of exactly 1e-8 into the
sampled state; the mass on the 15 real unknowns is ‖dq‖²/(‖dq‖² + 1e-16),
which is 1.000 while ‖dq‖ >> 1e-8, 0.536 at iter 5 (‖dq‖ = 1.07e-8) and
5.4e-5 at iter 6 (‖dq‖ = 7.35e-11), predicting about 8 of 150000 shots on
the real entries; the archived iter-6 `dq_sqls` is exactly the signature of
7 shots (three 1-shot entries at 2.582e-11 = 1e-8/sqrt(150000), one 4-shot
entry at twice that, eleven zeros), giving the archived fidelity 0.451.
With eps = 0 the mass is 1.000 at every iteration. The current branch
(`quantum_tools.py:829-830`, `eps=0.0`, verified in-process on the
solver's own path) removes it: two matched 150000-shot runs converged in
7 Newton iterations each with every per-iteration fidelity between 0.99995
and 0.99999, final-iteration fidelity 0.999974 and 0.999978 (>= 0.99), and
final residual_total 5.06e-10 and 9.86e-10. The separate LU-vs-statevector
residual divergence (1.33e-7 relative after two updates despite 1.5e-15
per-step dq agreement) is fully explained by the sqrt(u) ≈ 1.5e-8 roundoff
floor of the finite-difference Jacobian (measured 1.1e-8 to 1.5e-8 relative
δJ from a 1e-15 δq, propagating to 2.5e-8 to 2.6e-7 in the next residual)
and is unrelated to the pad or to SQLS.

Scratch `/tmp/order1-reproduce-9/` removed after writing this file.
