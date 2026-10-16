# Build 09 -- zero RHS pad on the SQLS path

- Builder: builder A, 2026-10-15T02:55:48Z (commit time; local 2026-10-14 22:55:48 -0400)
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`
- Commit: `3a88a37d` "SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse" (on top of item 7, `d7658f6a`)
- Work-plan item: 9 in `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`; section 5d and finding 1 of `04-sqls-wiring-validation.md`

## What changed

`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py:825-830` (`QuantumSQLS.solve_one_step`): `convert_to_pow2(A_o, b_o, verbosity=self.verbosity)` -> `convert_to_pow2(A_o, b_o, verbosity=self.verbosity, eps=0.0)`, plus a 4-line comment. The padded RHS entries are now exactly 0.0. The padded A block keeps its unit diagonal, so the padded system stays nonsingular. The padded unknown solves to exactly 0.

Unchanged: `convert_to_pow2`'s default `eps=1e-8` (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/math_tools.py:28`). The HHL path calls it at `quantum_tools.py:562` and `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/time_solvers.py:520`, so HHL keeps eps = 1e-8.

Why this is safe for sqls:
- `SQLS` only rejects a b that is zero overall: `float(np.linalg.norm(b)) == 0` at `/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py:179-181`. Zero entries are fine.
- In `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`, `psi_norm=b_pow2` is only a norm fallback, and its norm changes by at most 1e-8.
- Sign restoration uses `np.where(final_b < 0, -1, 1)`, which handles a zero entry.
- The statevector phase fix divides by `sv[j]` at the largest-magnitude entry, not at the pad.
- The caller slices `x_pow2[:nsys]`, so the pad entry is dropped.

## Commands and results

From `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, `.venv/bin/python nozzle_1d_solver.py ... -noshow -outdir /tmp/order1-build-7-9/<run>` (deleted afterwards). Wall = `/usr/bin/time -p` real. The CSV numbers were checked with `~/.venvs/tooling/bin/python` (pandas; read-only analysis, because the repo venv has no pandas).

### Rung 3 statevector, full_svd (criterion 2)

Command: `-nelem N -linsolver SQLS -shots 0 -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -sqls_method full_svd`

| nelem | exit | wall | fidelity per step | linsys_residual per step | max abs(dq_lu - dq_sqls) | final residual_total SQLS / LU | abs diff |
|---|---|---|---|---|---|---|---|
| 2 | 0 | 1.80 s | 1.0000000000000, 1.0, 1.0000000000000 (min 0.9999999999999998) | 1.47e-15, 6.23e-17, 3.33e-19 | 3.05e-16 | 1.326330532e-4 / 1.326331354e-4 | 8.22e-11 |
| 5 | 0 | 1.85 s | 1.0, 1.0000000000000004, 1.0000000000000004 | 4.76e-14, 2.84e-15, 2.13e-16 | 2.00e-15 | 5.83288564e-2 / 5.83288641e-2 | **7.73e-9** |

LU baselines (same args with `-linsolver LU`): nelem 2 took 3.07 s wall (first, cold run), nelem 5 took 0.92 s. nelem 5 residual_total: 12.375368 -> 0.568679 -> 0.058329. nelem 2: 1.314105 -> 0.013898 -> 1.32633e-4. Note: the order quoted 0.761 -> 0.0710 for nelem 5. I measured 0.5687 -> 0.0583, both on `main` code (before any change) and after.

The rung-3 residual histories are bit-identical (max abs diff 0.0) to the same runs made after item 7 but before item 9. This is expected: in statevector mode the extracted slice is exact either way.

### Shots sanity, nelem 2

`-nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -time_scheme BDF1 -localdt -cfl 1e10 -iters 2 -initers 1 -sqls_method full_svd`: exit 0, 1.75 s wall. Fidelity 0.99996273 at step 0 and 0.99996575 at step 1; linsys_residual 4.22e-2 and 7.21e-4 (shot noise at 10000 shots).

### Matched case, 150000 shots (criteria 3 and 4)

`-nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1`

| step | fidelity BEFORE (eps 1e-8, this session) | fidelity AFTER (eps 0) | residual_total AFTER |
|---|---|---|---|
| 0 | 0.99997891 | 0.99996095 | 12.375368 |
| 1 | 0.99997991 | 0.99996442 | 0.73293 |
| 2 | 0.99997317 | 0.99995501 | 0.067965 |
| 3 | 0.99997593 | 0.99998080 | 3.1853e-3 |
| 4 | 0.99998360 | 0.99998587 | 5.7593e-5 |
| 5 | 0.99991734 | 0.99998316 | 1.8855e-7 |
| 6 | **0.66845990** | **0.99997184** | 9.7885e-10 |

- BEFORE: wall 11.33 s (first SQLS run, cold imports). The 0.668 is this session's draw; the August value was 0.451. Shots are unseeded, so the collapsed value varies between runs.
- AFTER: exit 0, wall 2.36 s, SQLS solve time summed over 7 solves about 0.51 s (about 0.07 s each).
- Newton stopped at 7 iterations (steps 0-6), below the 15-iteration cap.
- Final residual_total is 9.79e-10, within the 5e-9 limit. Every iteration, the final one included, has fidelity >= 0.99995. Step-6 linsys_residual 4.35e-12 and l2_error_abs 2.18e-13.
- `final_results_nelem5_SQLS_statevector_nshots150000.csv` against the August file `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/final_results_nelem5_SQLS_statevector_nshots150000.csv` (5 rows), max abs diff: xp 0.0, rho 1.89e-11, u 6.96e-11, p 2.46e-11, Mach 1.67e-10. All are within 1e-6.

## Open doubts

1. **Criterion 2 "final residual_total matches LU to 1e-10" fails at nelem 5: 7.73e-9.** This does not come from item 9. The value is identical before and after the change, and the per-step dq agree to 2.0e-15. My hypothesis: the finite-difference Jacobian (`compute_Jacobian_matrix_FD`, `time_solvers.py:397-425`, perturbation `eps_machine * norm(q)`) magnifies about 1e-15 differences in q into about 1e-7 relative differences in the next step's A. That would make 1e-10 agreement unreachable for any non-LU solver at nelem 5. I did not test this hypothesis. It holds at nelem 2 (8.2e-11). A tolerance of about 1e-8, or a relative tolerance, is more realistic for that criterion.
2. The expected LU residuals in the order (0.761 -> 0.0710) do not match what I measured (0.5687 -> 0.0583), even on the unmodified `main` code. They may come from a different configuration.
3. Shots are unseeded, so the matched-case numbers vary from run to run. One AFTER run is a single sample. With the pad at 0, the step-6 state has no dummy component left to soak up probability, so the collapse mechanism is gone structurally rather than by chance.
4. HHL was not run (forbidden by the order). Its eps is untouched by construction: only the SQLS call site changed.

## Fix-up round (code review findings)

Date: 2026-10-15T03:43:43Z. Commit `71c02aed` on `feature/sqls-aiaa-4q26` in `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`. Only F3 belongs to item 9. The other fix-ups (F1, F2, F4, F6, F7, F8) are recorded in `build-07.md`.

### F3: zero right-hand side

- `quantum_tools.py:836-840`, `QuantumSQLS.solve_one_step`. k is resolved first, so a bad k is still a config error. Then, if `not np.any(b_o)`, it returns `np.zeros(nsys)` without building a circuit. With the `eps=0.0` pad, an all-zero b would otherwise reach `sqls`, which raises `ValueError("b is the zero vector; ...")` (`/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py:180-182`). A x = 0 has the unique solution x = 0 because A is nonsingular. No `qc_metadata_sqls_*.csv` row is written for that step (no circuit ran), and `self.qc_metadata` keeps its previous value.
- `time_solvers.py:662-667`, `sqls_solve`. When both `dq_lu` and `dq_sqls` are exactly zero, fidelity is set to `1.0`: the solutions are identical, and `quantum_tools.fidelity` would divide by a zero norm. The L2 errors already have `+ 1e-15` guards and come out 0.0. `hhl_metrics_*.csv` therefore still gets a row: fidelity 1.0, l2_error_abs / rel / normalized 0.0, linsys_residual 0.0.

### Verification

- In-process, nelem-5 iter-0 A with b = zeros(15). Each check took under 2 s.
  - `QuantumSQLS(verbosity=0).solve_one_step(A, 0, 5)` returns shape (15,), all zero, with no exception. `k` resolves to 8.
  - `LinearSystemSolver.sqls_solve(A, 0)` returns a zero dq. Metrics: `{'fidelity': 1.0, 'l2_error_abs': 0.0, 'l2_error_rel': 0.0, 'l2_error_normalized': 0.0, 'linsys_residual': 0.0}`. No RuntimeWarning. Only `dq_nelem5_iter0_statevector.csv` and `system_Ab_nelem5_iter0.pkl` were written; there was no qc_metadata CSV.
- Rung 3, nelem 5, statevector, `-iters 3`, 1.87 s: `residual_nelem5_SQLS_statevector.csv` is byte-identical to the pre-edit run. The nonzero-b path is untouched.
- Test suite: 60 tests OK, 1 skipped, 42.12 s. No test fails.
