# Build 06: hybrid SVD-deflated HHL (`-hhl_deflate_k`) in the 1D Euler nozzle solver

Builder 6, order-3 pod. Written 2026-10-15T09:55Z (UTC). Repo
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26`, base `484b24ed`, HEAD `9e8fc7fe`. Nothing pushed,
`main` untouched, no other branch, pyproject / venv / uv.lock unchanged.
Python `.venv/bin/python` (qiskit 2.5.2, qiskit-aer 0.17.2). Scratch
`/tmp/order3-build-6/` deleted at the end of this build.

## Commits (`git log --oneline 484b24ed..HEAD`)

```
9e8fc7fe TESTING: record item 6 suite and gate fixture timings
8c5bab3c README and TESTING: hybrid SVD-deflated HHL flag, columns, tests and item 11 follow-up wording
63bd1b07 Item 11 follow-ups: unseeded HHL fidelity floor 0.7, seed docstring, empty cells for circ_metrics none
279a14d1 Add tests for shifted SVD deflation: dry-check reproduction, identity, columns, CLI
8eb40832 Add hhl_deflate_k: shifted SVD deflation pre and post steps around the HHL path with metadata columns
f1c18965 Add August iter1-5 and April CFL1e10 iter14 Jacobians to tests/data with provenance
```

`git diff 484b24ed..HEAD --stat`: 20 files, +877 / -78 lines. New:
`deflation.py` (166 lines), `tests/test_deflation.py` (345 lines), six
`tests/data/system_Ab_nelem5_iter{1,2,3,4,5,14}.pkl` (2115 bytes each,
`git add -f`, `*.pkl` is gitignored). Modified: `time_solvers.py` (+66/-x),
`quantum_tools.py` (+40), `nozzle_1d_solver.py` (+27), `tests/contract.py`
(+30), `tests/helpers.py`, `tests/make_fixtures.py`,
`tests/data/provenance.json`, `tests/test_cli.py`, `tests/test_hhl.py`,
`tests/test_circuit_metrics.py`, `README.md` (+76), `TESTING.md` (+95).
One note on commit granularity: README.md and TESTING.md carry both the
item-6 documentation and the item-11 follow-up wording in interleaved hunks
of the same files, so they are one docs commit (`8c5bab3c`); the item-11
code and test changes are their own commit (`63bd1b07`) as asked.

## 1. Design as implemented

Equations (06a Refinement 1 and 2), with (sigma_i, u_i, v_i) the singular
triplets of the ORIGINAL unpadded, undoubled 3*nelem x 3*nelem Jacobian A in
ascending order of sigma, shift = sigma_max = sigma_N:

    A' = A + sum_{i<k} (sigma_max - sigma_i) u_i v_i^T              (pre-step)
    HHL solves A' y = b through the UNCHANGED path: scale by spectral
    radius, pad to 16, Hermitian-double to 32, build the circuit,
    statevector / shots readout, sign and -hhl_scale scaling -- every one
    of these now acts on (A', b)
    x = y + sum_{i<k} (u_i . b) (1/sigma_i - 1/sigma_max) v_i          (post-step)

    kappa      = sigma_max / sigma_1                (original A)
    kappa_eff  = sigma_max / sigma_{k+1} = kappa(A')   (exact; = kappa at k = 0)
    n_l        = max(n_b + 1, ceil(log2(kappa + 1))) + 1,  n_b = log2(2 * 2^ceil(log2 N))
    P_succ     = sum_i w_i (lambda_min / lambda_i)^2, w_i = (u_i.b)^2 / ||b||^2,
                 deflated lambda_i := shift, lambda_min := sigma_{k+1}
    x-share    = sum_{i<k} (u_i.b / sigma_i)^2 / sum_i (u_i.b / sigma_i)^2
    b-share    = sum_{i<k} (u_i.b)^2 / ||b||^2

All five definitions are copied from `kappa_eff_deflation_check.py`
(`analyse`, `clock_qubits`, `success_prob`; the SVD is reordered ascending
with `np.argsort(s)` exactly as there).

Where the code sits (HEAD `9e8fc7fe`):

| piece | location |
|---|---|
| new module, numpy only, no qiskit import | `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py`: `Deflation` dataclass L33 (`kappa` L57, `kappa_eff` L62, `x_share_classical` L67, `correction` L72, `recombine` L78), `deflate(A, b, k)` L83 (dense `np.linalg.svd`, rank-k update, timed as `t_svd_s`), `x_share` L109, `b_share` L117, `state_qubits` L125, `clock_qubits` L131 (the library rule), `success_prob` L138, `deflation_columns` L151, `DEFLATION_COLUMNS` L28 |
| rank plumbing | `time_solvers.py` L285-290: `LinearSystemSolver.__init__` reads `linsolv_args['hhl_deflate_k']` (default 0, rejects < 0) |
| classical Hermitian reference factored out | `time_solvers.py` L528 `herm_lu_solve(A, b)` (same four calls as before: `convert_to_pow2`, `convert_system_to_herm`, `lu_solve`, `extract_true_sol_from_herm`) |
| pre-step | `time_solvers.py` L567-578 in `hhl_solve`: `defl = deflate(A, b, k)`, `A_q = defl.a_shifted`, `dq_herm_q = herm_lu_solve(A_q, b)`; with k = 0 `A_q is A`, `dq_herm_q is dq_herm` |
| HHL call | `time_solvers.py` L583: `self.hhl_solver.solve_one_step(A_q, b, nelem, self.iter, step=step, deflation=defl)` |
| sign / scale on the solved system | `time_solvers.py` L588-609: `true_sol` norm and `choose_global_sign` use `dq_herm_q` and `A_q`; `leastsq` alpha uses `A_q @ dq_hhl`; shots-mode per-component signs use `dq_herm_q` |
| post-step | `time_solvers.py` L612-613: `dq_hhl = defl.recombine(dq_hhl)`; the metrics below it (fidelity vs `dq_herm` of the ORIGINAL A, `||A dq - b||` with the original A) are unchanged |
| metadata hook (no circuit change) | `quantum_tools.py` L626 `solve_one_step(..., deflation=None)`; L731 `qc_metadata['deflate_k']` (pickle); L775-776 `deflation_columns(deflation, A_o, circ.qregs[1].size)` inserted before the item-11 fairness columns; L784-786 the archived `system_Ab_*.pkl` gets `deflation.a_orig, deflation.b` (the ORIGINAL system) when deflating |
| CLI | `nozzle_1d_solver.py` L118 `-hhl_deflate_k` (int, default 0); L235-238 rejects K > 0 with a non-HHL `-linsolver`; L252-255 rejects K outside `0 <= K < 3*nelem`; L255 into `linsolv_args`; L470 pickle `metadata['hhl_deflate_k']` |
| contract | `tests/contract.py` L54 `QC_METADATA_DEFLATION_COLUMNS`, L65 inserted into `QC_METADATA_HHL_COLUMNS` after `circ_run_time` and before the eight fairness columns; L119 `METADATA_KEYS_HHL_ONLY += 'hhl_deflate_k'`; L122 `HHL_DEFLATE_K_DEFAULT = 0`; L125 `QUANTUM_CIRCUIT_KEYS['HHL'] += 'deflate_k'` |

`n_clock` is read off the circuit the library built: `construct_circuit`
allocates `QuantumRegister(nb)`, `QuantumRegister(nl)`, optional ancillas,
`QuantumRegister(nf)` in that order, so `circ.qregs[1].size` is the library's
own `nl`, sized from `NumPyMatrix(A_herm).condition_bounds()` =
`np.linalg.cond(A_herm)` (`linear_solvers/hhl.py` L424-433,
`matrices/numpy_matrix.py` L103-107). No kappa override anywhere.

Nothing inside `QuantumHHL.generate_circuit` / `HHL.construct_circuit`
changed. With K = 0 `deflate` is never called, `A_q is A`, and the
arithmetic is the one at `484b24ed`: the gate fixture passes 7/7 at 1e-10
max-abs (below) and the k = 0 nelem-5 CLI run reproduces the archived
reference fidelity 0.999957137763 and `||A dq - b||` 4.2067e-2 to every
printed digit.

## 2. Dry check reproduced by the new code path

`tests/test_deflation.py::TestDryCheckReproduction` loads the archived
Jacobians through `tests/helpers.load_system` and recomputes every column
with `deflation.deflate`, `clock_qubits`, `success_prob`, `b_share`,
`Deflation.x_share_classical`. Which pickle the script used: the acceptance
numbers (kappa 67.6, x-share 23 / 35 / 59 / 72 %) are the block
`[April Frontier HHL] CFL=1e+10 iter=14` of `kappa_eff_deflation_output.txt`,
i.e. `results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e/system_Ab_nelem5_iter14.pkl`
(sha256 `b0b16eda...7caf93`), NOT the August iter 6 that was already in
`tests/data/`. It is now `tests/data/system_Ab_nelem5_iter14.pkl` with
source, date and sha256 in `provenance.json` (the `test_archived_sources_
unchanged` check compares it with the archive). Iteration 0 of the April
trial is bit-identical to the August iter 0 already in `tests/data/`
(sha256 `7c2551de...148f`), so that fixture serves the iteration-0 row. The
August iterations 1 to 5 were copied as well so the identity check covers
the whole converged run (iter 0 to 6).

Script value (printed) vs module value (same digits in every cell; the
test asserts at the printed precision, i.e. 2 decimals on kappa_eff, 4 on
P_succ, 1 on the shot factor, 3 on the shares, exact on n_l):

| system | k | kappa_eff script / module | n_l | P_succ | shots x | b-share | x-share | identity rel err |
|---|---|---|---|---|---|---|---|---|
| CFL 1e10 iter 14 (kappa 67.63) | 0 | 67.63 / 67.63 | 8 / 8 | 0.0055 / 0.0055 | 1.0 | 0.000 | 0.000 | 0 |
| | 1 | 35.19 / 35.19 | 7 / 7 | 0.0157 / 0.0157 | 2.9 / 2.9 | 0.001 | 0.225 / 0.225 | 3.7e-15 |
| | 2 | 15.02 / 15.02 | 7 / 7 | 0.0722 / 0.0722 | 13.1 / 13.1 | 0.004 | 0.352 / 0.352 | 3.7e-15 |
| | 3 | 13.74 / 13.74 | 7 / 7 | 0.0531 / 0.0531 | 9.7 / 9.7 | 0.032 | 0.602 / 0.602 | 3.8e-15 |
| | 4 | 7.88 / 7.88 | 7 / 7 | 0.1113 / 0.1113 | 20.2 / 20.2 | 0.048 | 0.727 / 0.727 | 3.9e-15 |
| CFL 1e10 iter 0 (kappa 95.98) | 0 | 95.98 / 95.98 | 8 / 8 | 0.0143 / 0.0143 | 1.0 | 0.000 | 0.000 | 0 |
| | 1 | 43.31 / 43.31 | 7 / 7 | 0.0061 / 0.0061 | 0.4 / 0.4 | 0.013 | 0.913 / 0.913 | 2.8e-15 |
| | 2 | 16.32 / 16.32 | 7 / 7 | 0.0378 / 0.0378 | 2.7 / 2.7 | 0.014 | 0.923 / 0.923 | 3.0e-15 |
| | 3 | 15.66 / 15.66 | 7 / 7 | 0.0335 / 0.0335 | 2.3 / 2.3 | 0.021 | 0.938 / 0.938 | 3.1e-15 |
| | 4 | 7.87 / 7.87 | 7 / 7 | 0.0922 / 0.0922 | 6.5 / 6.5 | 0.031 | 0.957 / 0.957 | 3.0e-15 |

The acceptance list quotes "kappa 67.6, 35.2, 15.0, 13.7, 7.9; x-share 23,
35, 59, 72 %; iter 0 k = 2: 16.3, 92 %": the kappas and the first two
shares are the same numbers at 3 significant figures; "59 %" and "72 %" were
rounding slips in 06a (the output file's 0.602 and 0.727 round to 60 % and
73 %), corrected in 06a in the fix-up round below. The quoted ascending spectrum 0.861 ... 58.2 is also
asserted at 3 significant figures, and `kappa(A')` = kappa_eff to 1e-10
relative (`np.linalg.cond(A')`).

Identity `x = y + correction` vs `numpy.linalg.solve(A, b)`, with
`A' y = b` solved by numpy, `TestShiftedDeflationIdentity`: relative error
<= 1e-13 asserted; observed 4.5e-16 to 3.9e-15 on all nine archived systems
(August iter 0 to 6, April iter 14, nelem-2 step 0) for k = 1, 2, 3, 4
(36 subtests). The same test checks the singular values of A' are
sigma_{k+1..N} plus k copies of sigma_max (rtol 1e-10), that the record
keeps A and b untouched, and that k = 0, -1, N, N + 1 and a mismatched b
raise `ValueError` (k = 0 is the caller's branch, never a `Deflation`).

## 3. HHL statevector runs

All runs: `-linsolver HHL -shots 0 -iters 1 -time_scheme BDF1 -localdt
-cfl 1e10 -initers 1 -noshow`, laptop (Apple silicon), fvm working tree at
`279a14d1` (clean; `code_versions.fvm.dirty` False in both nelem-5
pickles), `/usr/bin/time -p` for the process wall. Because `-iters 1` runs
one Newton step, every number below is the FIRST Newton step (iteration 0,
kappa 95.98, the first-update regime where 06a predicts a 92 % classical
share), not the converged iteration-14 Jacobian of the 35 % row.

### nelem 5, k = 0 vs k = 2 (N = 15, padded 16, doubled 32, n_b = 5)

| quantity | k = 0 (`-hhl_deflate_k 0`) | k = 2 (`-hhl_deflate_k 2`) |
|---|---|---|
| `kappa` (original A) | 95.9779 | 95.9779 |
| `kappa_eff` = `condition_number` of the matrix handed to HHL | 95.9779 | 16.3158 |
| fvm print "Condition # of Hermitian matrix" (same number the library's `condition_bounds()` sees) | 95.9779 | 16.3158 |
| `n_clock` (library clock register, `circ.qregs[1].size`) | 8 | 7 |
| predicted n_l = max(6, ceil(log2(kappa_eff + 1))) + 1 | 8 | 7 |
| `circ_qubits` = `nqubits` 5 + `n_clock` + 1 flag | 14 | 13 |
| `fb_cx_count` ({u3, cx}, level 0) | 2,054,602 | 1,022,314 |
| `fb_depth` | 4,067,708 | 2,024,100 |
| `fb_total_gates` | 5,455,676 | 2,715,252 |
| `circ_depth_transpile` (Aer basis) | 596,687 | 297,295 |
| fidelity(dq_hhl, dq_herm of the original A) | 0.999957137763 | 0.999994897449 |
| `||A dq - b||_2` (original A) | 4.2067e-2 | 7.0909e-2 |
| relative L2 error vs `dq_lu` | 6.82e-3 | 2.26e-3 |
| max-abs error vs `dq_lu` | 1.02e-2 | 3.23e-3 |
| `||dq(k=2) - dq(k=0)|| / ||dq_lu||` | - | 6.64e-3 |
| `x_share_classical` | 0.0 | 0.9234 |
| `t_svd_s` | 0.0 s | 7.3e-5 s |
| `circ_generate_time` | 18.13 s | 9.07 s |
| `circ_transpile_time` | 14.12 s | 7.67 s |
| `circ_run_time` (statevector) | 51.10 s | 18.11 s |
| `t_count_s` (fixed-basis count, excluded from the above) | 9.35 s | 4.53 s |
| pickle `elapsed_time` | 96.57 s | 41.3 s |
| process wall | 98.45 s | 43.18 s |
| start (UTC) | 2026-10-15T09:37:33Z | 2026-10-15T09:36:50Z |

Reading. The clock register drops 8 -> 7 and the width 14 -> 13 exactly as
06a predicted, through the library's own `condition_bounds()` on the doubled
A' (no override). The fixed-basis CX count and depth halve (one fewer
controlled Hamiltonian-evolution power in the QPE), the statevector run
takes 2.8x less. Fidelity vs LU improves (infidelity 4.3e-5 -> 5.1e-6) and
the L2 error drops 3x, but `||A dq - b||` is 1.7x LARGER with k = 2. Both
runs are within the HHL path's own accuracy band (infidelity below 1e-4,
relative L2 below 1 %), and the two updates differ from each other by
6.6e-3 relative, the same order as either one's distance from LU. The
residual increase is consistent with the HHL error in y no longer sitting
mostly along the small-sigma directions (which A damps in `A e`) once those
are parked at sigma_max in A', and with the coarser 7-qubit QPE grid; I did
not isolate the cause (open doubt below). At iteration 0 the classical part
carries 92 % of `||x||^2`; the quantum solve delivered an 8 % remainder.

### nelem 2, k = 1 (N = 6, padded 8, doubled 16, n_b = 4)

| quantity | k = 0 | k = 1 |
|---|---|---|
| `kappa` / `kappa_eff` | 38.306 / 38.306 | 38.306 / 6.850 |
| `n_clock` / `circ_qubits` | 7 / 12 | 6 / 11 |
| `fb_cx_count` / `fb_depth` / `fb_total_gates` | 234,899 / 470,394 / 630,388 | 116,067 / 232,343 / 311,810 |
| fidelity | 0.999998635611 | 0.999994160356 |
| `||A dq - b||_2` | 3.352e-3 | 1.625e-2 |
| relative L2 vs `dq_lu` | 1.83e-3 | 2.42e-3 |
| `x_share_classical` / `t_svd_s` | 0.0 / 0.0 s | 0.951 / 3.1e-4 s |
| process wall | 10.44 s | 18.83 s (first invocation of the session, cold imports; the same run inside the suite took 5.94 s) |

The archived `system_Ab_nelem2_iter0.pkl` of the k = 1 run is bit-identical
(`np.array_equal`) to `tests/data/system_Ab_nelem2_iter0.pkl` and to the
k = 0 run's: the ORIGINAL A (cond 38.3), not A' (cond 6.85).

## 4. Metadata (for the harvester follow-up)

Six new columns in `qc_metadata_nelem*_<method>[_shots*].csv` (HHL only),
written on every HHL run including k = 0, placed after `circ_run_time` and
before the eight item-11 fairness columns (`circ_qubits` ... `seed`), so
`csv_columns[-8:]` is still the fairness block:

| column | type | units | meaning |
|---|---|---|---|
| `deflate_k` | int | - | the `-hhl_deflate_k` rank; 0 = plain HHL |
| `kappa` | float | - | sigma_max / sigma_min of the ORIGINAL Newton Jacobian A (2-norm condition number) |
| `kappa_eff` | float | - | sigma_max / sigma_{k+1} = kappa(A'), the matrix the circuit was built from; equals `kappa` when k = 0 |
| `n_clock` | int | qubits | the library's clock-register width for the solved system, read off the circuit registers (`circ_qubits` = `nqubits` + `n_clock` + 1 on this path) |
| `x_share_classical` | float | dimensionless, 0 to 1 | share of `||x||^2` carried by the k deflated right-singular directions, `sum_{i<k} (u_i.b/sigma_i)^2 / sum_i (u_i.b/sigma_i)^2`; the part of the answer that came from the classical rank-k solve; 0.0 at k = 0 |
| `t_svd_s` | float | s | wall time of the classical pre-step (dense `numpy.linalg.svd` of A plus the rank-k update), `time.perf_counter`; 0.0 at k = 0 |

Pickle: `metadata['hhl_deflate_k']` (int, HHL runs only, next to
`hhl_scale`) and `metadata['quantum_circuit']['deflate_k']` (int). Pinned in
`tests/contract.py` as `QC_METADATA_DEFLATION_COLUMNS`,
`METADATA_KEYS_HHL_ONLY`, `QUANTUM_CIRCUIT_KEYS['HHL']`,
`HHL_DEFLATE_K_DEFAULT`.

Harvester notes (read-only here, not changed): (a) the existing
`condition_number`, `lambda_*_orig`, `lambda_*_scaled` columns describe the
matrix the circuit was built from, i.e. A' when k > 0; a harvester that
wants the Jacobian's own kappa should read `kappa`, and `kappa_eff` for the
solved system. (b) `-circ_metrics none` now writes EMPTY cells for
`fb_depth`, `fb_total_gates`, `fb_cx_count`, `t_count_s` (basis `none`)
instead of -1 / 0.0; the harvester's `_int_or_none('')` and the
`t_count_s` guard on basis `none` already map these to null (verified by
reading `fvm_euler_1d_solver_harvester.py` L276-325; the module could not
be imported here because `q8020_cfd_metautil` is not in the fvm venv). (c)
File names do not encode k: two runs with different k into the same
`-outdir` would overwrite each other, as different `-hhl_scale` runs do
today; sweeps use one outdir per case.

## 5. Framing for the paper row

Hybrid SVD-deflated HHL: classical rank-k deflation plus HHL on the
remainder, with the classical share reported and no speedup claimed. For
each Newton solve the k smallest singular triplets of the 15 x 15 Jacobian
are computed classically by a dense SVD (`t_svd_s` 7e-5 s here; a
shift-invert Lanczos would be the sparse route), the matrix handed to HHL is
A' with those modes shifted to sigma_max, and the rank-k part of the answer
is added back classically. On the archived converged CFL-1e10 Jacobian
(iteration 14) k = 2 lowers kappa 67.6 -> 15.0, the clock register 8 -> 7
qubits, the post-selection proxy 13x, and leaves 65 % of `||x||^2` to the
quantum solve (`x_share_classical` 35 %); on the first Newton step (the
only one run here) the classical share is 92 %, the circuit goes 14 -> 13
qubits and 2,054,602 -> 1,022,314 CX, fidelity vs LU 0.99996 -> 0.999995,
`||A dq - b||` 4.2e-2 -> 7.1e-2. Caveats checked: (1) the library's kappa is
taken from A' itself, through its own `condition_bounds()` on the doubled
A', with no manual override (`n_clock` 7 observed, equal to
max(n_b + 1, ceil(log2(16.3 + 1))) + 1); (2) deflation is applied to the
original A, b before the path's spectral-radius scaling, power-of-2 padding
and Hermitian doubling, all of which then act on A'; (3) obtaining the k
smallest triplets costs a classical SVD or shift-invert Lanczos, which at
N = 15 (and at N = 255) is a full classical solve, so the row is a resource
reduction for the quantum kernel given a classical rank-k preconditioner;
(4) reusing the deflation space across Newton iterations, the route to
amortizing that cost, is not implemented and remains future work. At small
CFL (kappa <= 10) deflation buys nothing (06a), so the row applies to the
steady CFL-1e10 case only.

Added in the fix-up round (verifier-6 F2): the quantum kernel's own error
must be read next to the share. With `hhl_kernel_rel_err` = ||A_q y - b|| /
||b|| on the system the circuit actually solved, after scaling and before
the classical recombination (fvm `hhl_metrics_*.csv`, HEAD of this round),
the nelem-5 iteration-0 solves give 3.40e-3 at K = 0 (A x = b, 14 qubits,
8 clock qubits) and 5.73e-3 at K = 2 (A' y = b, 13 qubits, 7 clock qubits):
the quantum kernel is 1.7x LESS accurate with the smaller clock register,
and the fidelity gain vs LU at K = 2 (0.99996 -> 0.999995) is carried by
the exact 92 % classical share, not by a better quantum solve. (The
verifier's hand values 6.8e-3 / 8.2e-3 were not reproduced under this
definition; 6.8e-3 coincides with the K = 0 `l2_error_rel`, so a different
normalization was likely used; the ratio K = 2 / K = 0 is the same order,
1.2x there vs 1.7x here.) Any paper row therefore reports BOTH
`x_share_classical` and `hhl_kernel_rel_err`, and should be taken at the
iteration-14 steady Jacobian (35 % classical share, dry-checked) rather
than at iteration 0 (92 %), which is the only step run so far.

## 6. Item-11 follow-ups (commit `63bd1b07`, docs in `8c5bab3c`)

- `tests/test_hhl.py`: unseeded 1000-shot HHL fidelity floor 0.8 -> 0.7,
  comment now says ~35 post-selected shots and cites the Monte Carlo
  P(fail) 0.34 % at 0.8; the seeded-case docstring and comment say "unseeded
  floor 0.7". `TESTING.md` (d) and (i) updated the same way ("~100 of the
  1000 shots" -> "~35").
- `README.md`: SQLS nelem 5 fixed-basis range "depth 400-401 / 572-577" ->
  "depth 400-402 / 572-580 gates (the upper ends observed across the Newton
  steps of a converged run)".
- `quantum_tools.count_circuit_metrics` docstring: `seed_transpiler=0` pins
  determinism; a different seed shifts the HHL u3 count and depth slightly,
  CX unchanged (the old "no stochastic pass runs" sentence removed). README
  fb_* row says the same.
- `-circ_metrics none` writes empty cells (not -1 / 0.0) for `fb_depth`,
  `fb_total_gates`, `fb_cx_count`, `t_count_s`; `fb_basis` stays `none`.
  Cheap (one dict in `quantum_tools.circuit_metrics`), contract column set
  unchanged, two tests in `tests/test_circuit_metrics.py` updated to the new
  expectation (`read_csv` keeps an unparsable column as the raw strings
  `['']`), `-circ_metrics` help text, `contract.py` comment, README and
  TESTING (h) updated. The sentinels are therefore gone, not documented.

## 7. Commands and wall times (UTC)

| command (from the repo root, `.venv/bin/python`) | start | wall |
|---|---|---|
| `nozzle_1d_solver.py -nelem 2 -linsolver HHL -shots 0 -iters 1 -hhl_deflate_k 1 <base> -outdir /tmp/order3-build-6/n2k1` (smoke) | 09:28:32Z | 18.83 s |
| `-m unittest tests.test_deflation tests.test_gate_fixture -v` (24 tests, before the commits) | 09:32:55Z | 36.3 s |
| `nozzle_1d_solver.py -nelem 5 -hhl_deflate_k 2 -linsolver HHL -shots 0 -iters 1 <base> -outdir .../n5k2` | 09:36:50Z | 43.18 s |
| `nozzle_1d_solver.py -nelem 5 -hhl_deflate_k 0 -linsolver HHL -shots 0 -iters 1 <base> -outdir .../n5k0` | 09:37:33Z | 98.45 s |
| `nozzle_1d_solver.py -nelem 2 -hhl_deflate_k 0 -linsolver HHL -shots 0 -iters 1 <base> -outdir .../n2k0` | 09:39:12Z | 10.44 s |
| `-m unittest discover -s tests` | 09:45:54Z | 113.9 s (115.0 s process) |
| `-m pytest tests -q -p no:cacheprovider` | 09:47:49Z | 115.0 s (116.4 s process) |
| `FVM_GATE_TESTS=1 -m unittest tests.test_gate_fixture -v` | 09:49:46Z | 104.0 s (104.7 s process) |

`<base>` = `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`. Three
parse-time rejection runs (0.4 s each) and `-h` were also run by hand.
Budget: suite 2 of 3 runs used (unittest, pytest), gate fixture 1 of 2,
nelem-5 statevector solves 2 standalone (k = 2, k = 0) plus the one inside
the gate fixture (k = 0, in-process), nelem-2 runs several (all < 20 s). No
shots-mode nelem-5 run, no sweep, no background job, no network, no
Frontier.

## 8. Suite lines

```
unittest:  Ran 145 tests in 113.850s   OK (skipped=1)
pytest:    144 passed, 1 skipped, 1 warning, 96 subtests passed in 115.02s (0:01:55)
gate:      Ran 7 tests in 103.981s   OK   (nelem-5 HHL 95.04 s, nelem-2 HHL 8.88 s, 1e-10 max-abs)
```

The one pytest warning is runtime's own `fake_nighthawk` properties warning
(pre-existing). 145 = 128 (item 11) + 17 new tests in `tests/test_deflation.py`
(5 classes: `TestDryCheckReproduction` 3, `TestShiftedDeflationIdentity` 3,
`TestDeflationColumns` 3, `TestHHLDeflateNelem2CLI` 5,
`TestDeflateCLIValidation` 3); the skipped one is the opt-in nelem-5 gate.
Same count under unittest and pytest. Gate fixture 7/7 unchanged (no new
gate test was added, so the count stays 7; a k = 2 nelem-5 reference would
have needed a second ~100 s solve per gate run and was left out).

## 9. Open doubts

1. `||A dq - b||` grows with deflation (1.7x at nelem 5, 4.8x at nelem 2)
   while fidelity and the L2 error improve. "Within the HHL path's own
   accuracy" holds on fidelity and L2 (both better) and on the k-vs-k
   distance (6.6e-3 relative), but a reader who ranks by residual sees k = 2
   as worse. The planned Frontier runs (k in {0, 2, 4}, 10 trials, 150k
   shots) should report all three, and the residual history over the Newton
   loop will show whether the larger per-step residual slows convergence.
2. The only nelem-5 solve here is iteration 0 (x-share 92 %). The 35 %
   share, the headline of the paper row, is a dry-check number on the
   archived iteration-14 Jacobian, reproduced by the module but not yet by a
   circuit run. A `-iters 15` deflated run (about 15 x 43 s) was outside
   this build's budget.
3. `kappa_eff` equals `condition_number` only because the padding's unit
   diagonal (1.0) lies inside [sigma_{k+1}/rho, sigma_max/rho] after the
   spectral-radius scaling (rho 37.2 here, sigma_{k+1}/rho 0.09). For a
   system where sigma_{k+1}/rho > 1 the padded matrix's kappa would be set
   by the padding, not by A'; not the case at nelem 2 or 5 at any CFL in the
   archive, but worth an assertion if nelem grows.
4. Shots mode with deflation is wired (per-component signs from the
   Hermitian LU of A') but not exercised in this build (no shots nelem-5 run
   allowed; the nelem-2 shots tests run k = 0 only).
5. The harvester's `condition_numbers` series will read kappa(A') for
   deflated runs (item 4a above) until it is taught the `kappa` column.

## Fix-up round (2026-10-15T10:19Z to 10:53Z, builder 6)

Reviews of the item-11 and item-6 ranges plus verifier 6; every listed item
implemented. fvm `feature/sqls-aiaa-4q26` HEAD `1ec8abcf` (base of the
round `9e8fc7fe`); six commits, one per file group / concern; nothing pushed,
main untouched, no venv / pyproject change. Scratch `/tmp/order3-fixup-fvm`
deleted at 10:53Z.

### Commits (`git log --oneline 9e8fc7fe..HEAD`)

```
1ec8abcf TESTING: record fix-up round suite and gate fixture timings
27545386 README and TESTING: fix-up round docs for fb_cached, hhl_kernel_rel_err, CSV rotation, circ_qubits authority, deflation index convention, sqls probe
61ebdb21 nozzle: a non-ideal HHL backend without -shots records the 128 shots actually used in the case name and pickle
e3d2e7b8 Move the dry-check-only helpers out of deflation.py into tests/deflation_drycheck.py
1c54a0d0 time_solvers and deflation fix-ups: hhl_kernel_rel_err metric, Hermitian LU of A prime only when consumed, one system pickle writer, condition number passed into deflation_columns
e50f4800 quantum_tools fix-ups: sqls signature probe, fixed-basis count cache with fb_cached, seed only for Aer backends, CSV header rotation, SQLS circ_qubits from the circuit, deflate_k qpy key
```

`git diff 9e8fc7fe..HEAD --stat`: 16 files, +684 / -277 (new
`tests/deflation_drycheck.py`, 48 lines). Whole item-6 range
`484b24ed..HEAD`: 25 files, +1436 / -230.

### What changed, per item

quantum_tools.py (commit `e50f4800`):
- Q1: `QuantumSQLS.__init__` imports `quantum_solve` and probes
  `inspect.signature(...).parameters` for `seed`; a stock sqls raises
  `RuntimeError` naming `patched sqls`, `'seed'` and the `sqls-patches/` path
  at construction, before any solve. Test `TestSQLSUnpatchedProbe` (stub
  without `seed` refused; installed sqls passes).
- Q2: `QuantumHHL.fixed_basis_metrics(circ)` wraps `circuit_metrics` behind
  a one-entry cache keyed on `structure_key(circ)` = (num_qubits, sequence
  of (instruction name, qubits, clbits)) with qiskit's auto-generated
  `circuit-<n>` names normalized. The first attempt keyed on
  `count_ops()` MISSED on step 1 (`circuit-46` vs `circuit-924`, the
  Initialize sub-circuit's auto name differs per build; found with an
  in-process comparison of the two steps' generated circuits, which are
  otherwise identical instruction for instruction). Reused rows carry
  `t_count_s` 0.0 and the new bool column `fb_cached` (ninth fairness
  column, after `t_count_s`; SQLS always False; empty under `-circ_metrics
  none`). Assumption stated in the docstring / README: the {u3, cx}
  level-0 count depends on the structure, not the matrix entries
  (evidence: identical 470394 / 630388 / 234899 on both nelem-2 steps).
- Q3: `_run_on_backend` adds `seed_simulator` only for `backend_type in
  ('ideal', 'fake')`; test `test_seed_not_sent_to_hardware_backends`.
- Q4: new `helper_tools.append_csv_row(path, row, verbosity)` used by the
  HHL and SQLS `save_metadata` and by `save_hhl_metrics`; on a header
  mismatch the old file is moved to `<outdir>/rotated/<name>.pre-<UTC>.csv`
  and a new file started, one `[csv] ...` log line. DEVIATION from the
  requested sibling name `<name>.pre-<utc>.csv`: a sibling would match the
  harvester's non-recursive singleton globs (`qc_metadata_*.csv`,
  `hhl_metrics_*.csv`, read with `[0]`, `tests/contract.py`
  `HARVESTER_SINGLETON_GLOBS`), so the rotated copy goes into a
  subdirectory; the `.csv` extension and the `.pre-<stamp>` infix are kept.
  Tests `TestCsvHeaderRotation` (helper and CLI).
- Q5: SQLS `circ_qubits` = `qc.num_qubits` of the circuit sqls built,
  fallback `n_data_qubits + m_ancilla`; the unused `fb_num_qubits` key is
  dropped (not kept).
- Q6: `circ_qubits` documented as authoritative, `circ_qubits_orig` /
  `circ_qubits_transpile` as legacy (README table, contract comment,
  `fairness_columns` docstring).
- Q7: `QuantumSQLS` docstring states the reference-free sign rule.
- Q8: qpy file names carry `_deflate<K>` when K > 0 (`deflate_suffix`,
  both the generated and the transpiled circuit; `expected_files(...,
  deflate_k=)` in the contract); `-loadcirc` with K > 0 and no matching file
  raises `FileNotFoundError` with a clear message (test
  `test_loadcirc_without_deflated_circuit_refused`).

time_solvers.py / deflation.py (commit `1c54a0d0`):
- Q9: `hhl_kernel_rel_err` = ||A_q y - b|| / ||b|| computed in `hhl_solve`
  after the sign / `-hhl_scale` scaling and before `recombine` (A_q = A' at
  K > 0, A at K = 0); SQLS rows carry `linsys_residual / ||b||`; 0.0 for
  b = 0. New last column of `hhl_metrics_*.csv`, pinned in
  `HHL_METRICS_COLUMNS`; the gate fixtures print their metrics on stderr.
- T1: `herm_lu_solve(A', b)` only when `-hhl_scale true_sol` or shots mode.
- T2: the system pickle has one writer (`hhl_solve`, original A, b); the
  pickle dump in `QuantumHHL.save_metadata_and_matrices` is gone (method is
  now `save_metadata(row, nelem)`).
- T3: `deflation_columns(defl, cond_a, n_clock)` takes
  `matrix_props_orig['condition_number']`; no second `np.linalg.cond`.

deflation.py / tests (commit `e3d2e7b8`): D1 `clock_qubits`, `state_qubits`,
`success_prob`, `b_share` moved to `tests/deflation_drycheck.py`;
`deflation.py` keeps `Deflation`, `deflate`, `x_share`, `deflation_columns`
(a test asserts the four names are gone). D2 the duplicate `-h` subprocess
test was folded into `test_cli`'s help test (`x_share_classical` added
there). D3: nothing added; the suite is green.

nozzle_1d_solver.py (commit `61ebdb21`): N1 `args.nshots` set to the 128
default after `linsolv_args['shots'] = 128`, so the case name, pickle
`nshots` / `effective_shots` and file names agree. Not covered by a test
(no fake backend wide enough for the 12-qubit circuit runs in test time).

Docs (commits `27545386`, `1ec8abcf`): R1 README uses one 0-based index
convention (`sum_{i<K}`, sigma_K the (K+1)-th smallest), documents
`fb_cached`, `hhl_kernel_rel_err`, the CSV rotation, the `circ_qubits`
authority, the `_deflate<K>` qpy key and `-loadcirc` refusal, the sqls probe;
TESTING (b), (d), (f), (h), (i), (l) and the layout table updated, timings
recorded. R2: `06a-deflation-numbers-and-recommendation.md` iteration-14
table k = 3 "59 %" -> "60 %", k = 4 "72 %" -> "73 %" (0.602 / 0.727 from
the output file) and the "hands 72 %" sentence -> 73 %, with a correction
note; section 2 and section 5 of this report amended (see above).

### Verification (UTC, laptop, same stack; `B` = `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`)

| check | start | wall | result |
|---|---|---|---|
| `-m unittest discover -s tests` | 10:43:08Z | 115.6 s (116.6 s process) | `Ran 150 tests` OK (skipped=1) |
| `-m pytest tests -q -p no:cacheprovider` | 10:45:05Z | 116.2 s (117.5 s process) | 149 passed, 1 skipped, 96 subtests, 1 warning (runtime `fake_nighthawk`, pre-existing); the same 150 tests |
| `FVM_GATE_TESTS=1 -m unittest tests.test_gate_fixture -v` | 10:47:38Z | 104.5 s (105.3 s process) | 7/7 OK at 1e-10; nelem-5 HHL 95.7 s; `[metrics]` nelem-5 HHL fidelity 0.999957137763, linsys 4.206694e-2, `hhl_kernel_rel_err` 3.399247e-3; nelem-2 HHL 0.999998635611 / 3.351933e-3 / 2.550734e-3; SQLS nelem 5 1.0 / 4.763e-14 / 3.849e-15, nelem 2 1.0 / 1.472e-15 / 1.120e-15 |
| rung 3b `python -W error nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 B` | 10:49:23Z | 2.15 s | rc 0; fidelity 0.99993 / 0.99977; `hhl_kernel_rel_err` 3.02e-2 / 5.44e-2 (shots) |
| rung 4b `python -W error nozzle_1d_solver.py -nelem 2 -linsolver HHL -shots 1000 -iters 1 B` | 10:49:25Z | 8.98 s | rc 0; fidelity 0.8656 (unseeded, above the 0.7 floor); `hhl_kernel_rel_err` 1.17 (linsys 1.54, the known unseeded stall case); `fb_cached` False, `t_count_s` 1.09 s, `effective_shots` 1000 |
| nelem-5 K = 2: `-nelem 5 -hhl_deflate_k 2 -linsolver HHL -shots 0 -iters 1 B` (the one allowed nelem-5 solve) | 10:49:34Z | 43.64 s | rc 0; 36 columns incl. `deflate_k` 2, `kappa` 95.98, `kappa_eff` 16.32, `n_clock` 7, `x_share_classical` 0.9234, `t_svd_s` 6.9e-5 s, `circ_qubits` 13, fb 2024100 / 2715252 / 1022314, `t_count_s` 4.55 s, `fb_cached` False; fidelity 0.999994897, `||A dq - b||` 7.0909e-2, **`hhl_kernel_rel_err` 5.734739e-3**; qpy files `circuit_{generated,transpile}_statevector_nelem5_iter0_deflate2.qpy` |
| K = 0 kernel error | from the gate fixture's in-process nelem-5 solve (no extra run) | - | **`hhl_kernel_rel_err` 3.399247e-3** (= 4.206694e-2 / ||b|| 12.3754) |
| `-loadcirc -hhl_deflate_k 2` in an empty dir (nelem 2) | 10:50:18Z | ~1 s | rc 1, `FileNotFoundError: -loadcirc with -hhl_deflate_k 2: no saved circuit for this deflation rank at .../circuit_generated_statevector_nelem2_iter0_deflate2.qpy. Run the case once without -loadcirc ...`; only the system pickle written |
| CSV rotation, scratch dir seeded with stale `qc_metadata_sqls_nelem2_full_svd.csv` (`step, iter, old_column`) and stale `hhl_metrics_nelem2_statevector.csv` (`step, iter, fidelity`), one SQLS nelem-2 step | 10:50:19Z | ~2 s | both rotated to `rotated/<name>.pre-20261015T105020Z.csv` with their rows, two `[csv]` log lines, new files with the current headers, singleton globs still unique |
| cache: `-nelem 2 -linsolver HHL -shots 0 -iters 2 B` | 10:50:21Z | 17.82 s | step 0 `t_count_s` 1.097 s / `fb_cached` False, step 1 `t_count_s` 0.0 / True, counts identical (470394 / 630388 / 234899); `hhl_kernel_rel_err` 2.55e-3 / 1.40e-2 |

Suite count 145 -> 150 (five new tests: `TestSQLSUnpatchedProbe` x2,
`TestCsvHeaderRotation` x2, `test_loadcirc_without_deflated_circuit_refused`,
`test_seed_not_sent_to_hardware_backends`; minus the folded `-h` test).

### Kernel-error reading (verifier-6 F2)

nelem 5, iteration 0: `hhl_kernel_rel_err` 3.40e-3 at K = 0 vs 5.73e-3 at
K = 2 (ratio 1.69, the same ratio as `||A dq - b||` 4.21e-2 -> 7.09e-2).
The quantum kernel is less accurate on A' with the 7-qubit clock register;
the fidelity gain vs LU (0.99996 -> 0.999995) comes from the exact 92 %
classical share. The verifier's hand values 6.8e-3 / 8.2e-3 were not
reproduced under the stated definition (6.8e-3 equals the K = 0
`l2_error_rel`, which suggests a different normalization); the direction
of the comparison is the same. nelem 2: 2.55e-3 (K = 0) vs the K = 1 run's
value asserted within 10x of it in the suite.

### Findings rejected or deviated from, with evidence

- Rotated-file location (Q4): subdirectory `rotated/` instead of a sibling,
  because `HARVESTER_SINGLETON_GLOBS` are read with `[0]` and a sibling
  `.csv` would make `qc_metadata_*.csv` match two files; verified by the
  contract test `test_harvester_globs_unambiguous` still passing and by the
  rotation tests asserting one match per glob.
- `fb_num_qubits` (Q5): dropped rather than kept consistently; it was
  written to no CSV and read by no consumer (grep over the repo and the
  harvester).
- The verifier's kernel-error values (Q9): reported as measured (3.40e-3 /
  5.73e-3), not the hand values, see above.
- No new gate test for K = 2 (would double the gate's cost); the K = 2
  evidence is the CLI run above.

## Final fix-up round (2026-10-15T11:24Z to 11:50Z, builder 6)

Eight review points Z1 to Z8 plus the docstring index convention, all
implemented. fvm `feature/sqls-aiaa-4q26` HEAD `643cba0c` (base of this
round `1ec8abcf`); seven commits, one per concern; nothing pushed, main
untouched, no venv / pyproject change, tree clean. No nelem-5 statevector
solve beyond the gate fixture's own (the one allowed was not needed).
Scratch `/tmp/order3-fixup-fvm2` deleted at 11:50Z.

### Commits (`git log --oneline 1ec8abcf..HEAD`)

```
643cba0c TESTING: record final fix-up round suite and gate fixture timings
eb131de8 README, TESTING and deflation docstring: exact fixed-basis cache key, u3cx-once, probe solve, CSV rotation edge cases, nshots128 naming, 0-based index convention
a87bb510 QuantumSQLS: millisecond 2x2 probe solve at construction requiring seed= and sqls_out qc
651fc276 append_csv_row: empty or truncated file counts as new, microsecond rotation stamp with a collision suffix
d8a071ba Exact fixed-basis cache key: sha256 of the circuit data with parameters, opt-in circ_metrics u3cx-once, structure key removed
cdf7103b hhl_solve: lazy Hermitian LU of the solved system and kernel error from the existing least-squares matvec
95782e61 Share the deflate qpy suffix through math_tools.deflate_suffix and build qpy paths in one QuantumHHL.qpy_path
```

`git diff 1ec8abcf..HEAD --stat`: 12 files, +531 / -139. Whole item-6
range `484b24ed..HEAD`: 26 files, +1858 / -260.

### Z1 (correctness): exact cache key, `u3cx-once` opt-in (commit `d8a071ba`)

Accepted as a real bug: the level-0 {u3, cx} count depends on the circuit
entries, so the structure-only key could have served a stale row to a later
Newton step with the same widths. Fix: `quantum_tools.circuit_key(circ)` =
sha256 over the full instruction data, fed by `_hash_circuit`: circuit
width; per instruction its CLASS (`op.base_class.__name__`, not the name --
qiskit's auto-generated `circuit-<n>` names differ between two builds of
the same circuit), arity, control count and state, qubit / clbit indices,
and `params` via `_hash_params` (numpy arrays as dtype + shape + raw bytes:
UnitaryGate matrices, permutation patterns; scalars as complex128 bytes at
full precision: rotation angles, Initialize amplitudes; a QuantumCircuit
parameter by recursion; else `repr`). An instruction WITHOUT parameters is
recursed through its `definition` when it is a sub-circuit wrapper or a
non-standard library gate (Instruction / Gate / ControlledGate built from a
circuit, ExactReciprocal, QFT); standard gates and measure / barrier /
reset are leaves. Inspection of the generated nelem-2 circuit showed where
the entries live: Initialize (16 complex params), the QPE's controlled
powers (ControlledGate wrapping a Gate with no params whose definition is
cu / crz / ccx / s / h with float params), ExactReciprocal (ucry with 64
angles), QFT and a PermutationGate (ndarray param) in the inverse QPE.
`fixed_basis_metrics`: 'u3cx' (default) hashes every step and reuses the
count only on an identical key (exact); 'u3cx-once' (new opt-in,
`math_tools.CIRC_METRICS_CHOICES = ('none', 'u3cx', 'u3cx-once')`) counts
step 0 and declares later rows `fb_cached` True / `t_count_s` 0.0 by
assumption; 'none' unchanged. `structure_key` and the `re` import are gone
(Z8). The hash time is added to `t_count_s` of a fresh row.

Evidence:
- (a) Different Newton steps, different keys: in-process build of the HHL
  circuits of the iter-0 and iter-1 systems of a 2-step nelem-2 run (same
  12-qubit width, same instruction arities): keys `8c8dff6f...` vs
  `11e19b72...`, different, although the counts agree (234899 CX / depth
  470394 / 630388 gates on both). Pinned in
  `TestFixedBasisCache.test_newton_steps_differ_and_rebuild_hits`.
- (b) Same circuit built twice, same key and a hit: the iter-0 system built
  twice gives identical 64-hex keys; `fixed_basis_metrics` returns
  `fb_cached` False / `t_count_s` 2.06 s on the first, True / 0.0 on the
  rebuild, and False / 1.40 s (a re-count) on the iter-1 circuit. Tiny
  circuits (same test module): the key changes with the Initialize
  amplitudes, with the unitary entries (identity vs swap) and with a
  wrapped rotation angle (0.3 vs 0.31), and ignores the auto-generated
  `circuit-<n>` name of a wrapped sub-circuit.
- (c) `-circ_metrics u3cx-once` on a 2-step nelem-2 HHL run (17.6 s): row 0
  `fb_cached` False / `t_count_s` 1.38 s, row 1 True / 0.0, step-0 counts
  repeated, pickle `circ_metrics` `u3cx-once` (CLI test
  `TestCircMetricsOnceCLI`). The default `u3cx` 2-step run (19.2 s) now
  shows False / False with `t_count_s` 1.36 s / 1.42 s.
- (d) `TestFixedBasisColumnsHHL` expects two fresh counts under the default;
  `TestFixedBasisCache` (2 tests) and `TestCircMetricsOnceCLI` are new;
  `test_circuit_metrics_modes` covers `u3cx-once`.
- Cost of the exact key: 0.36 s for the 12-qubit nelem-2 circuit, 2.98 s
  for the 14-qubit nelem-5 circuit (measured by circuit construction only,
  19.0 s to build, no solve; stable across two hashes). So under the default
  the nelem-5 `t_count_s` per step becomes about 12.3 s (9.3 s count + 3 s
  hash) and nothing is saved across Newton steps; `u3cx-once` saves both
  the count and the hash from step 1 on. Trade-off documented in README,
  `-h`, `TESTING.md` and the `fixed_basis_metrics` docstring.

### Z2: SQLS probe solve (commit `a87bb510`)

`QuantumSQLS.__init__` keeps the signature check and then runs
`_probe_patched_sqls`: a 2 x 2 `full_svd` statevector `quantum_solve` on
the instance's Aer backend with `seed=0`, requiring `sqls_out['qc']` and
x = A^-1 b (`[[2, 1], [0, 1]] x = [1, 1]`, x = [0, 1]); `quantum_solve`'s
timing prints are redirected away. Measured: 1.2 to 1.4 ms on the first
instance of a process, 0.3 to 0.4 ms on later ones (`probe_time_s`;
`TestSQLSUnpatchedProbe.test_installed_sqls_passes_probe` asserts < 50 ms).
Negative probe: `sqls.runtime.quantum.quantum_solve` monkeypatched to a
stub that accepts `seed` and returns the right x but sets no `qc` ->
`RuntimeError` at construction naming `sqls_out['qc']` and `sqls-patches`
(`test_sqls_without_qc_refused_by_probe_solve`); the stub without `seed`
is still refused by the signature check. One shared `SQLS_PATCH_HINT`.

### Z3: `append_csv_row` edge cases (commit `651fc276`)

Empty first line (zero-byte or truncated file) -> treated as new: header
written with mode 'w', no `rotated/`, no log line. Rotation stamp
`%Y%m%dT%H%M%S.%fZ` (microseconds) plus a `-1`, `-2`, ... suffix while the
target exists. Tests: `test_empty_or_truncated_file_is_treated_as_new`
(zero bytes, and a lone newline; `print` asserted not called),
`test_two_rotations_in_one_second_do_not_collide` (two back-to-back
rotations -> two files; with `_rotation_stamp` pinned the second takes
`-1`). Scratch exercise: an empty `qc_metadata_sqls_nelem2_full_svd.csv`
next to a stale `hhl_metrics_nelem2_statevector.csv`, one SQLS step: only
the stale file rotated (`hhl_metrics_nelem2_statevector.pre-20261015T114839.093056Z.csv`),
the empty one got the header; two helper rotations 3 ms apart produced
`twice.pre-20261015T114840.495316Z.csv` and `...498295Z.csv`.

### Z4 to Z8 and the docstring

- Z4 (`eb131de8`): README "Output Files" documents the N1 naming change
  (`_nshots128` / `_shots128`, pickle `nshots` 128 for a non-ideal HHL
  backend without `-shots`) and that the suite does not exercise it.
- Z5 (`cdf7103b`): `hhl_solve` holds `A_q` and a memoized closure
  `dq_herm_q()` (at K = 0 it returns the already computed `dq_herm`; at
  K > 0 it runs `herm_lu_solve(A_q, b)` on first use); the `true_sol`
  norm and the shots-mode signs call it, the default leastsq statevector
  path never does, and nothing is ever `None`.
- Z6 (`cdf7103b`): the kernel residual reuses the least-squares matvec,
  `A_dq_q = alpha_ls * A_dq_hhl`; the `true_sol` branch forms `A_q @
  dq_hhl` once after the sign step, the shots branch after the re-signing.
  Gate metrics unchanged to every printed digit (kernel error 3.399247e-3
  at nelem 5, 2.550734e-3 at nelem 2).
- Z7 (`95782e61`): `math_tools.deflate_suffix(k)` is the single spelling of
  `'_deflate<k>'`; `QuantumHHL.qpy_path(kind, nelem, step, iter,
  deflate_k)` builds both qpy names (the transpiled one with the shots
  tag); `tests/contract.py` imports the helper.
- Z8 (`d8a071ba`): `structure_key` and the name regex removed.
- Index convention (`eb131de8`): `deflation.py` states the 0-based ascending
  convention once (sigma_0 smallest, kappa_eff = sigma_max / sigma_k, "the
  (k+1)-th smallest, sigma_{k+1} in 1-based counting"), matching the README;
  the `kappa_eff` and `deflation_columns` docstrings follow it.

### Verification (UTC, laptop, same stack, fvm tree clean at `eb131de8` for the runs)

| check | start | wall | result |
|---|---|---|---|
| `-m unittest discover -s tests` | 11:41:05Z | 146.5 s (147.6 s process) | `Ran 156 tests` OK (skipped=1) |
| `-m pytest tests -q -p no:cacheprovider` | 11:43:32Z | 147.8 s (149.2 s process) | 155 passed, 1 skipped, 96 subtests, 1 warning (runtime `fake_nighthawk`, pre-existing); the same 156 tests (150 + 6 new) |
| `FVM_GATE_TESTS=1 -m unittest tests.test_gate_fixture -v` | 11:46:37Z | 107.8 s (108.6 s process) | 7/7 OK at 1e-10; nelem-5 HHL 98.6 s (includes the ~3 s hash); `[metrics]` identical to the previous round (fidelity 0.999957137763, linsys 4.206694e-2, kernel 3.399247e-3; nelem 2 0.999998635611 / 3.351933e-3 / 2.550734e-3) |
| rung 3b `python -W error ... -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2` | 11:48:26Z | 2.21 s | rc 0; fidelity 0.99988 / 0.99988; kernel 6.3e-2 / 2.1e-2 (shots) |
| rung 4b `python -W error ... -nelem 2 -linsolver HHL -shots 1000 -iters 1` | 11:48:28Z | 9.26 s | rc 0; fidelity 0.9791 (unseeded); `fb_cached` False, `t_count_s` 1.48 s (count + hash), `effective_shots` 1000 |
| Z1 (a)(b) in-process proof, nelem 2 | 11:35:11Z | builds 1.9 s each, hash 0.36 s | keys differ across steps, equal on rebuild, hit / miss as described |
| Z1 (c) `-circ_metrics u3cx-once` 2-step nelem 2 | 11:34:53Z | 17.6 s | `fb_cached` False / True, `t_count_s` 1.38 s / 0.0 |
| Z2 probe timing | in-process | 1.2 to 1.4 ms first instance, 0.3 to 0.4 ms later | negative probe (no `qc`) refused at init |
| Z3 scratch (empty file; two rotations) | 11:48:37Z | ~3 s | as described above |
| nelem-5 hash cost (construction only, no solve) | 11:48:40Z | build 19.0 s, `circuit_key` 2.98 s / 2.96 s | stable key |

### Findings rejected or deviated from

None rejected. One deviation already stated in Z1: under the exact key the
default mode no longer saves anything across Newton steps (as the reviewer
predicted) and costs ~3 s more per nelem-5 step for the hash; the saving
is only available through the opt-in `u3cx-once`, whose assumption is
spelled out everywhere it is mentioned.

## Last mini-round (2026-10-15T12:05Z to 12:33Z, builder 6)

Nine review points on `1ec8abcf..643cba0c`, all implemented. fvm
`feature/sqls-aiaa-4q26` HEAD `d2e5c6a5` (base of the round `643cba0c`);
two commits (code + tests, then docs + counts + one test fix); nothing
pushed, main untouched, no venv / pyproject change, tree clean; no nelem-5
solve beyond the gate fixture's own. Scratch `/tmp/order3-fixup-fvm3`
deleted at 12:33Z.

```
d2e5c6a5 Mini-round docs and counts: u3cx counts every step, u3cx-once shape guard, probe needs qc only when counting, collision test with annotated False
6f96d9fa Mini-round: circuit_key hashes controlled base gates and Pauli operators, u3cx counts every step, u3cx-once reuses on a shape guard, probe needs qc only when counting, whitespace-only CSV counts as new, functools.cache for the Hermitian LU, csr_matrix import at module top
```

`git diff 643cba0c..HEAD --stat`: 9 files, +265 / -155. Whole item-6 range
`484b24ed..HEAD`: 26 files, +1977 / -269.

### Points

1. `circuit_key` (`_hash_operation`): a ControlledGate's `base_gate` is
   hashed recursively (class and parameters; its definition is covered by
   the controlled operation's own definition recursion), and a
   `PauliEvolutionGate`'s operator is hashed as Pauli labels plus complex128
   coefficient bytes (its `params` hold only the time). Collision test
   `test_key_separates_controlled_base_gates_and_pauli_operators`:
   `RY(0.3).control(2)` vs `RZ(0.3).control(2)` (built with
   `annotated=False`, the ControlledGate form the HHL circuits use) give
   DIFFERENT keys and the RY pair repeats its key; `PauliEvolutionGate`
   XX vs ZZ, coefficient 1 vs 2 and time 0.5 vs 0.7 all differ. Result:
   PASS (3 key tests clean under `-W error::DeprecationWarning` after the
   `annotated=False` fix in `d2e5c6a5`).
2. `u3cx-once`: the cached row is stored with `(num_qubits, len(circ.data))`;
   a later step with a different shape re-counts and logs one line
   `[fb] circuit (qubits, instructions) changed (a) -> (b): re-counting`.
   In-process check (`TestFixedBasisCache`): the iter-1 circuit (same
   shape) reuses the iter-0 count, a copy with one gate prepended
   re-counts (`fb_total_gates` + 1).
3. Probe: `sqls_out['qc']` required only when `circ_metrics != 'none'`
   (`seed=` always); `SQLS_PATCH_HINT`, the probe docstring and the
   `solve_one_step` comment / error now say the same thing; a stub without
   `qc` is accepted with `circ_metrics='none'` (new assertion) and refused
   otherwise.
4. Default `u3cx`: no hashing, count every step, `t_count_s` = count time
   only, `fb_cached` always False. `u3cx-once`: no hashing either, the
   shape guard of point 2. `circuit_key` stays as a tested utility; its
   docstring now states the measured cost (0.36 s at 12 qubits, 3.0 s at
   14) and that the solver path does not use it; the "a few ms" and "fresh
   row includes hashing" claims are gone.
5. `append_csv_row`: a file is new only when its whole content is
   empty / whitespace (`read().strip() == ''`); an empty first line above
   data rows rotates (new assertion in
   `test_empty_or_truncated_file_is_treated_as_new`: `'\n0, 0, 1\n'` is
   moved to `rotated/`).
6. `test_installed_sqls_passes_probe`: `0.0 < probe_time_s < 5.0`.
7. `hhl_solve`: `dq_herm_q = functools.cache(lambda: dq_herm if defl is
   None else self.herm_lu_solve(A_q, b))` replaces the memo dict (two lines,
   `import functools` at the top).
8. `from scipy.sparse import csr_matrix` once at the module top of
   `quantum_tools.py`; the two function-level imports removed.

### Verification (UTC, laptop; the machine was LOADED by other agents during this round: nelem-2 HHL runs 23 to 25 s against 18 to 19 s earlier, the nelem-5 gate solve 122.5 s against 95 to 99 s; no code path got slower, the default count path got cheaper by the removed hash)

| check | start | wall | result |
|---|---|---|---|
| `-m unittest discover -s tests` (tree at `6f96d9fa` + uncommitted docs) | 12:20:26Z | 199.8 s (201.3 s process) | `Ran 157 tests` OK (skipped=1) |
| `-m pytest tests -q -p no:cacheprovider` | 12:23:47Z | 203.0 s (204.4 s process) | 156 passed, 1 skipped, 96 subtests; 4 warnings = the pre-existing runtime `fake_nighthawk` one + 3 `Gate.control() annotated` deprecations from the new collision test, fixed in `d2e5c6a5` (`annotated=False`; module re-run under `-W error::DeprecationWarning`: 3 passed) |
| `FVM_GATE_TESTS=1 -m unittest tests.test_gate_fixture -v` | 12:27:51Z | 134.3 s (135.5 s process) | 7/7 OK at 1e-10; nelem-5 HHL 122.5 s; `[metrics]` identical to every printed digit (fidelity 0.999957137763, linsys 4.206694e-2, kernel 3.399247e-3; nelem 2 0.999998635611 / 3.351933e-3 / 2.550734e-3) |
| rung 3b `python -W error ... -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2` | 12:30:06Z | 14.6 s (loaded) | rc 0; fidelity 0.99981 / 0.99988 |
| rung 4b `python -W error ... -nelem 2 -linsolver HHL -shots 1000 -iters 1` | 12:30:21Z | 12.2 s | rc 0; fidelity 0.7945 (unseeded, above the 0.7 floor); `fb_cached` False, `t_count_s` 1.47 s |
| `u3cx` 2-step nelem-2 HHL | 12:30:33Z | 24.6 s | rows: `t_count_s` 1.431 s / 1.457 s (count only), `fb_cached` False / False |
| `u3cx-once` 2-step nelem-2 HHL | 12:30:58Z | 23.1 s | rows: `t_count_s` 1.471 s / 0.0, `fb_cached` False / True, no `[fb]` re-count line (shape unchanged), counts 234899 / 470394 / 630388 repeated |

Suite count 156 -> 157 (the collision test). Note on provenance: the two
suite runs and the CLI runs above executed with README.md / TESTING.md
modified in the working tree (docs only, committed as `d2e5c6a5`); the
code tree was `6f96d9fa`.

### Rejected

Nothing. One nuance recorded: under point 4 the default `u3cx` path now
differs from the structure-cached version of the previous round only in
that it never reuses, so `fb_cached` is informative under `u3cx-once` only.
