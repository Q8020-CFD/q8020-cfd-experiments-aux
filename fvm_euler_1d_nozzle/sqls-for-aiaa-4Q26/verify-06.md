# verify-06: independent verification of work item 6 (hybrid SVD-deflated HHL, `-hhl_deflate_k`)

VERDICT: PASS

Verifier session 2026-10-15T09:59:25Z to 2026-10-15T10:16Z (UTC). Repo
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26`, HEAD `9e8fc7fe0519b5f44445356fc630a38c7737fe7c`,
range `484b24ed..9e8fc7fe` (six commits: f1c18965, 8eb40832, 279a14d1,
63bd1b07, 8c5bab3c, 9e8fc7fe). Python
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
(qiskit 2.5.2 stack as recorded in `tests/data/provenance.json`); HHL library
is the editable fork at
`/Users/agallojr/proj/src/q8020/quantum_linear_solvers` (commit 66eadf0).
Read-only everywhere; scratch `/tmp/order3-verify-6/` (deleted at the end).
Not read: `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`.

All seven acceptance criteria hold. Three low-severity findings, none of
them a defect of the branch (one rounding slip in the 06a note, one
interpretation caveat for the paper row, one pre-existing qpy limitation).

## Runs performed (all wall times measured here, this laptop)

| # | command (from the repo root) | start (UTC) | wall | result |
|---|---|---|---|---|
| R1 | `.venv/bin/python -m unittest tests.test_deflation -v` | 10:02:58Z | 31.0 s (31.5 s process) | 17 tests OK |
| R2 | `.venv/bin/python -m unittest discover -s tests -t .` | 10:03:42Z | 117.5 s (118.7 s process) | 145 tests OK, 1 skipped |
| R3 | `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` | 10:06:19Z | 105.3 s (106.1 s process) | 7/7 OK at 1e-10 max-abs (nelem-5 HHL 96.3 s, nelem-2 HHL 8.9 s) |
| R4 | `nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 0 -iters 1 -circ_metrics none <BASE>` | 10:08:06Z | ~2 s | exit 0 |
| R5 | 6 parse-time rejections (SQLS / LU / GMRES with K = 1; HHL with K = 6, -1, 100 at nelem 2) | 10:08:07Z | <1 s each | all exit 2, nothing written |
| R6 | `nozzle_1d_solver.py -nelem 2 -hhl_deflate_k 1 <HHL-BASE>` | 10:08:57Z | 6.16 s | exit 0 |
| R7 | `nozzle_1d_solver.py -nelem 2 -hhl_deflate_k 0 <HHL-BASE>` | 10:09:03Z | 10.40 s | exit 0 |
| R8 | `nozzle_1d_solver.py -nelem 5 -hhl_deflate_k 2 <HHL-BASE>` | 10:09:14Z | 43.76 s | exit 0 (first nelem-5 solve) |
| R9 | `nozzle_1d_solver.py -nelem 5 -hhl_deflate_k 0 <HHL-BASE>` | 10:09:58Z | 100.81 s | exit 0 (second nelem-5 solve) |
| R10 | `nozzle_1d_solver.py -nelem 2 -hhl_deflate_k 1 -hhl_scale true_sol <HHL-BASE>` | 10:13:09Z | 11.76 s | exit 0 |

`<BASE>` = `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`;
`<HHL-BASE>` = `<BASE> -linsolver HHL -shots 0 -iters 1`; every run had
`MPLBACKEND=Agg -outdir /tmp/order3-verify-6/<run>`. No shots-mode nelem-5
run, no sweep, no background job, no network.

## Criterion 1: flag, mechanics, unchanged HHL path, clock sizing -- PASS

Code read: `deflation.py` (new, 166 lines), `time_solvers.py`
`LinearSystemSolver.hhl_solve` and `herm_lu_solve`, `quantum_tools.py`
`QuantumHHL.solve_one_step`, `nozzle_1d_solver.py` argument block, fork
`linear_solvers/hhl.py` `construct_circuit`, `linear_solvers/matrices/numpy_matrix.py`.

- Flag `-hhl_deflate_k K`, `type=int`, default 0 (`nozzle_1d_solver.py:118`).
  Non-HHL solvers with K > 0 are REJECTED at parse time, before any solve and
  before any file is written: `parser.error("-hhl_deflate_k applies to
  -linsolver HHL only; got -linsolver SQLS")`, exit 2 (R5: SQLS, LU, GMRES
  all exit 2, output dir empty). K = 0 with a non-HHL solver is accepted
  silently (it is the default). Out-of-range K on HHL (6, -1, 100 at nelem 2)
  rejected with `must satisfy 0 <= K < 3*nelem = 6`, exit 2, nothing written.
  `LinearSystemSolver.__init__` also rejects K < 0 with `ValueError`.
- Mechanics (`deflation.deflate`): dense `numpy.linalg.svd` of the ORIGINAL
  unpadded, undoubled A (the `A` argument of `hhl_solve`, before
  `scale_Ab_by_spectral_radius` / `convert_to_pow2` / `convert_system_to_herm`,
  which all run inside `solve_one_step` on whatever matrix it receives);
  ascending sort; `a_shifted = A + (U_k * (sigma_max - sigma_k)) @ V_k^T`;
  `recombine(y) = y + V_k @ (ub_k * (1/sigma_k - 1/sigma_max))`. This is 06a
  Refinement 1 to the letter.
- Pre/post steps live in `time_solvers.hhl_solve`, outside `QuantumHHL`'s
  circuit construction: pre-step `defl = deflate(A, b, K); A_q =
  defl.a_shifted` before `solve_one_step(A_q, b, ..., deflation=defl)`;
  post-step `dq_hhl = defl.recombine(dq_hhl)` after the sign / `-hhl_scale`
  step. The scale step (`leastsq` alpha from `A_q`, `b`; `true_sol` norm and
  `choose_global_sign` on `A_q`) and the shots-mode sign reference
  (`dq_herm_q` = LU of the Hermitian form of A') all act on (A', b); the
  metrics (fidelity, L2, `||A dq - b||`) use the ORIGINAL A, b. The only
  change inside `solve_one_step` is the `deflation=None` kwarg used for the
  six metadata columns, `quantum_circuit['deflate_k']`, and archiving the
  ORIGINAL system; `generate_circuit`, `transpile_circuit`, `run_*`,
  `get_sol_*` are untouched by the diff.
- K = 0: `defl` stays `None`, `A_q = A`, `dq_herm_q = dq_herm`;
  `solve_one_step(A, b, ..., deflation=None)`; `deflation_columns(None, A,
  n_clock)` writes kappa = kappa_eff = `np.linalg.cond(A)`, 0, 0.0, 0.0.
  Bit-identity of the K = 0 path: gate fixture 7/7 at 1e-10 (R3) with the
  flag absent, AND my own CLI K = 0 runs with `-hhl_deflate_k 0` spelled
  explicitly reproduce the stored references: nelem 2 max|dq_hhl - ref| =
  7.8e-16, nelem 5 max|dq_hhl - ref| = 4.8e-14 (reference tolerance 1e-10).
- Clock register: fork `hhl.py:424-433`:
  `kappa = matrix_circuit.condition_bounds()[1]` (NumPyMatrix:
  `np.linalg.cond(matrix)` of the matrix handed to `construct_circuit`, i.e.
  the scaled, padded, doubled A') and
  `nl = max(nb + 1, int(np.ceil(np.log2(kappa + 1)))) + neg_vals`,
  `neg_vals=True`. No override anywhere in the diff (grep `condition_bounds`,
  `nl`, `neg_vals` in the fvm diff: none). My own computation through the
  real `scale_Ab_by_spectral_radius -> convert_to_pow2 ->
  convert_system_to_herm` chain gives cond(A_herm) = cond(A') exactly in every
  case (the identity pad and the +/- sigma doubling do not change kappa), so
  the reduced kappa does reach the library:

  | system | k | cond(A_herm) seen by the library | n_b | n_l | width n_b + n_l + 1 |
  |---|---|---|---|---|---|
  | nelem-5 iter 0 | 0 | 95.978 | 5 | 8 | 14 |
  | nelem-5 iter 0 | 2 | 16.316 | 5 | 7 | 13 |
  | nelem-5 iter 0 | 4 | 7.867 | 5 | 7 | 13 |
  | nelem-5 iter 14 | 0 | 67.633 | 5 | 8 | 14 |
  | nelem-5 iter 14 | 2 | 15.018 | 5 | 7 | 13 |
  | nelem-2 iter 0 | 0 | 38.306 | 4 | 7 | 12 |
  | nelem-2 iter 0 | 1 | 6.850 | 4 | 6 | 11 |

- `n_clock` is `circ.qregs[1].size` of the generated circuit
  (`quantum_tools.py`, `deflation_columns(deflation, A_o,
  circ.qregs[1].size)`); the fork builds `QuantumCircuit(qb, ql, [qa], qf)`
  so `qregs[1]` is the clock register `ql` by construction. Confirmed on the
  saved transpiled circuits: registers `[(q0, 5), (q1, 7), (q2, 1)]` at nelem
  5 K = 2 (13 qubits) and `[(q0, 5), (q1, 8), (q2, 1)]` at K = 0 (14 qubits);
  `[(q0, 4), (q1, 6), (q2, 1)]` / `[(q0, 4), (q1, 7), (q2, 1)]` at nelem 2.

## Criterion 2: dry-check reproduction -- PASS

- R1: `tests/test_deflation.py` 17 tests OK, 31.0 s (the nelem-2 K = 1 run
  6.5 s, the cached K = 0 `-iters 2` run 20.1 s).
- Fixture integrity (sha256, all six new pickles): local file == provenance
  entry == source file, read-only:

  | file in `tests/data/` | sha256 | source |
  |---|---|---|
  | `system_Ab_nelem5_iter14.pkl` | `b0b16eda…caf93` | `.../results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e/system_Ab_nelem5_iter14.pkl` |
  | `system_Ab_nelem5_iter1.pkl` | `3e848f9a…fbc70` | `.../2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter1.pkl` |
  | `system_Ab_nelem5_iter2.pkl` | `c99a5104…61836` | same trial, iter2 |
  | `system_Ab_nelem5_iter3.pkl` | `5efae34b…6a5915` | same trial, iter3 |
  | `system_Ab_nelem5_iter4.pkl` | `ab5d14ff…827e1` | same trial, iter4 |
  | `system_Ab_nelem5_iter5.pkl` | `b80e58fd…a4988` | same trial, iter5 |

  All six are git-tracked (`git ls-files tests/data`), 2115 bytes each, and
  `provenance.json` carries a `systems_added_utc` entry
  (2026-10-15T09:25:00Z).
- My own numpy (no module code) on `system_Ab_nelem5_iter14.pkl`
  (N = 15, padded 16, doubled 32, n_b = 5; kappa 67.63; spectrum 0.861, 1.65,
  3.88, 4.24, 7.39, 8.21, 13.5, 15.4, 18.4, 20.2, 27.3, 28.8, 39.6, 51.2,
  58.2) with `n_l = max(n_b + 1, ceil(log2(kappa_eff + 1))) + 1` (the +1 for
  the negative eigenvalues, as in `kappa_eff_deflation_check.py`):

  | k | kappa_eff (mine) | n_l | x-share | P_succ | shots x | module (`deflate`, `clock_qubits`, `x_share_classical`, `success_prob`) | `kappa_eff_deflation_output.txt` | 06a table |
  |---|---|---|---|---|---|---|---|---|
  | 0 | 67.63 | 8 | 0.000 | 0.0055 | 1.0 | identical to 1e-12 | 67.63 / 8 / 0.000 | 67.6 / 8 / 0 % |
  | 1 | 35.19 | 7 | 0.225 | 0.0157 | 2.9 | identical | 35.19 / 7 / 0.225 | 35.2 / 7 / 23 % |
  | 2 | 15.02 | 7 | 0.352 | 0.0722 | 13.1 | identical | 15.02 / 7 / 0.352 | 15.0 / 7 / 35 % |
  | 3 | 13.74 | 7 | 0.602 | 0.0531 | 9.7 | identical | 13.74 / 7 / 0.602 | 13.7 / 7 / **59 %** (see F1) |
  | 4 | 7.88 | 7 | 0.727 | 0.1113 | 20.2 | identical | 7.88 / 7 / 0.727 | 7.9 / 7 / **72 %** (see F1) |

  Iteration 0 (`system_Ab_nelem5_iter0.pkl`, kappa 95.98), k = 2: 16.32 / 7 /
  0.923 (expected 16.3 / 7 / 92 %), identical to the module; k = 0, 1, 3, 4
  also equal the output file (95.98/8, 43.31/7/0.913, 15.66/7/0.938,
  7.87/7/0.957).
- Identity `x = y + sum (u_i.b)(1/sigma_i - 1/sigma_max) v_i`, `A' y = b`,
  vs `numpy.linalg.solve(A, b)`, k = 1..4, computed both with my own numpy
  and through `deflate(...).recombine(...)`, on all NINE archived systems
  (August iter 0-6, April iter 14, nelem-2 iter 0): worst relative error
  3.9e-15 (requirement 1e-13); cond(A') equals sigma_max / sigma_{k+1} in
  every case (e.g. iter 14: 35.19, 15.02, 13.74, 7.88; iter 0: 43.31, 16.32,
  15.66, 7.87; nelem 2: 6.85, 5.20, 2.39, 1.78).

## Criterion 3: runs -- PASS

(a) nelem 2, statevector, one step (R6, R7):

| | K = 1 | K = 0 |
|---|---|---|
| wall | 6.16 s | 10.40 s |
| `circ_qubits` | 11 | 12 |
| `n_clock` | 6 | 7 |
| `kappa` / `kappa_eff` | 38.306 / 6.850 | 38.306 / 38.306 |
| `condition_number` (matrix the circuit was built from) | 6.850 | 38.306 |
| `x_share_classical` | 0.9511 | 0.0 |
| `t_svd_s` | 5.2e-5 s | 0.0 s |
| `fb_cx_count` / `fb_depth` | 116,067 / 232,343 | 234,899 / 470,394 |
| fidelity vs LU (CSV; my recomputation agrees to 1e-7) | 0.9999942 | 0.9999986 |
| rel L2 `||dq_hhl - dq_lu|| / ||dq_lu||` | 2.42e-3 | 1.83e-3 |
| `||A dq - b||` (CSV; mine from the archived A, b agrees to 1e-6) | 1.625e-2 (||b|| = 1.314, rel 1.24e-2) | 3.352e-3 (rel 2.55e-3) |

R10 (`-hhl_scale true_sol`, K = 1): fidelity 0.9999960, rel L2 2.08e-3,
`||A dq - b||` 1.743e-2, n_clock 6, 11 qubits, pickle `hhl_scale true_sol`,
`hhl_deflate_k 1` -- the `dq_herm_q` branch works.

(b) nelem 5, statevector, one step (R8, R9); step-0 Jacobian is bit-identical
to the gate fixture `system_Ab_nelem5_iter0.pkl` (max|dA| = 0):

| | K = 2 (R8) | K = 0 (R9) | gate-fixture reference / README |
|---|---|---|---|
| wall | 43.76 s | 100.81 s | README 43 s / 98 s |
| `circ_qubits` | 13 | 14 | 13 / 14 |
| `n_clock` | 7 | 8 | 7 / 8 |
| `kappa` | 95.978 | 95.978 | 96.0 |
| `kappa_eff` | 16.316 | 95.978 | 16.3 |
| `x_share_classical` | 0.9234 | 0.0 | 0.92 |
| `t_svd_s` | 7.8e-5 s | 0.0 s | |
| `fb_cx_count` | 1,022,314 | 2,054,602 | 1,022,314 / 2,054,602 |
| `fb_depth` | 2,024,100 | 4,067,708 | 2,024,100 / 4,067,708 |
| fidelity vs LU | 0.9999949 | 0.9999571 | ref 0.9999571; README 0.9999949 / 0.9999571 |
| 1 - fidelity | 5.1e-6 | 4.29e-5 | |
| rel L2 vs LU | 2.26e-3 | 6.82e-3 | |
| `||A dq - b||` | 7.091e-2 (rel to ||b|| = 12.375: 5.73e-3) | 4.207e-2 (rel 3.40e-3) | ref 4.2067e-2; README 7.09e-2 / 4.21e-2 |
| `||e||`, e = dq_hhl - dq_lu | 6.11e-3 | 1.84e-2 | |

Judgement on the residual (`||A dq - b||` 1.69x larger at K = 2 while
fidelity and rel L2 improve 3x): NOT a contradiction. I decomposed the error
e = dq_hhl - dq_lu in the right-singular basis of the ORIGINAL A. At K = 0,
73.6 % of ||e||^2 sits in the two smallest modes (sigma 0.55 and 1.21), and A
damps those components in the residual (sigma |e.v_i| = 1.9e-3 and 1.9e-2);
at K = 2 the share of ||e||^2 in those two modes is 0.000 (they are exact,
classical) and the whole quantum error sits in the sigma 3.35 to 18 band,
where A amplifies it 3x to 18x into the residual (largest contributions
4.4e-2, 3.9e-2, 2.8e-2 from the sigma 17.4, 17.9, 6.9 modes). Under a
kappa-96 operator, `||A e||` and `||e||` are different norms that can disagree
by up to 96x; the error got 3x smaller and merely moved to directions the
residual weights more. The item's claims (kappa_eff, clock width, shots
proxy, classical share) do not depend on the residual, and the paper's
Table-4 metric (error vs LU) improves. Both relative residuals (5.7e-3 and
3.4e-3) are within the HHL path's own accuracy band (nelem-2 K = 0 gives
2.6e-3, K = 1 1.2e-2). See F2 for the caveat about WHY fidelity improves.

## Criterion 4: metadata -- PASS

- HHL `qc_metadata_nelem{2,5}_statevector.csv` carry `deflate_k, kappa,
  kappa_eff, n_clock, x_share_classical, t_svd_s` between `circ_run_time` and
  the eight fairness columns; K = 0 rows: `deflate_k 0`, `kappa == kappa_eff`
  (95.9778901432456 both), `x_share_classical 0.0`, `t_svd_s 0.0`. K > 0
  rows: `condition_number` == `kappa_eff` (cond of A'), `kappa` == cond of the
  archived ORIGINAL A.
- Pickle `metadata_*.pkl`: `hhl_deflate_k` 2 / 0 / 1 and
  `quantum_circuit = {'backend_type': 'ideal', 'backend_method':
  'statevector', 'use_gpu': False, 'deflate_k': K}` in every run.
- `tests/contract.py` pins `QC_METADATA_DEFLATION_COLUMNS` (inside
  `QC_METADATA_HHL_COLUMNS`), `METADATA_KEYS_HHL_ONLY = ['hhl_scale',
  'hhl_deflate_k']`, `HHL_DEFLATE_K_DEFAULT = 0`,
  `QUANTUM_CIRCUIT_KEYS['HHL']` includes `deflate_k`;
  `QC_METADATA_SQLS_COLUMNS` unchanged.
- Archived `system_Ab_*_iter0.pkl` of the K > 0 runs equals the K = 0 run's
  (max|dA| = max|db| = 0): the ORIGINAL system, cond 95.98 / 38.31, not A'.
- SQLS CSV header (R4 and an SQLS K = 0 run) is unchanged: 25 columns, no
  deflation columns.

## Criterion 5: item-11 follow-ups in 63bd1b07 -- PASS

- `tests/test_hhl.py`: unseeded floor `assertGreaterEqual(met['fidelity'][0],
  0.7)` with the Monte-Carlo rationale (P(fidelity < 0.8) 0.34 %); the seeded
  class text updated to "0.7".
- `quantum_tools.count_circuit_metrics` docstring: "seed_transpiler=0, which
  pins determinism: a different seed shifts the HHL u3 count and depth
  slightly (the CX count is unchanged), so the seed is part of the recipe".
- README SQLS nelem-5 range: "200-201 CX / depth 400-402 / 572-580 gates";
  TESTING: "post-selection on the ancilla keeps ~35 of the 1000 shots".
- `-circ_metrics none` (R4, SQLS nelem 2): CSV row
  `..., 3, , , , none, , 0, ` -- `fb_depth`, `fb_total_gates`, `fb_cx_count`,
  `t_count_s` are empty cells, `fb_basis` `none`, `circ_qubits` 3. (The
  SQLS-native `cx_count` / `circuit_depth` columns are -1 in BOTH modes; that
  is pre-existing `-v 2`-only behaviour documented in the README, not this
  item.)

## Criterion 6: suite, gate, hygiene, git -- PASS

- R2: 145 tests, OK, 1 skipped (the opt-in gate), 117.5 s under one runner
  (TESTING records 113.9 s). R3: gate 7/7 OK at `MAX_ABS_TOL = 1e-10`,
  105.3 s (TESTING 104.0 s).
- Hygiene: `git diff 484b24ed..9e8fc7fe -- '*.py' | grep '^+' | awk 'length
  > 89'` -> 0 lines; added lines with trailing whitespace (all files) -> 0;
  `deflation.py` and `tests/test_deflation.py` have all imports at the top
  (stdlib, third-party, local) and compile; the two new `from deflation
  import ...` lines in `quantum_tools.py` / `time_solvers.py` sit in the
  module import blocks.
- Git: working tree clean before and after my runs (nothing written inside
  the repo; all output went to `/tmp`); `feature/sqls-aiaa-4q26` has NO
  remote tracking branch (nothing pushed); `main` = `ef7f0a8b` =
  `origin/main` (untouched). New binaries: exactly the six pickles above,
  each with a provenance entry whose sha256 matches the source (table in
  criterion 2).

## Criterion 7: claims hygiene -- PASS (no speedup claimed)

| claim (where) | status |
|---|---|
| "kappa(A') = sigma_max / sigma_(K+1) exactly" (README, help) | measured-in-this-branch (tests + my cond(A') checks on nine systems) |
| "the library's own `condition_bounds()` on the doubled A' sizes the clock register", "8 -> 7 clock qubits" (README) | measured-in-this-branch (n_clock 8 -> 7 at nelem 5, 7 -> 6 at nelem 2; registers read from the saved circuits) |
| "with K = 0 ... the path is the one the gate fixtures pin" (README) | measured-in-this-branch (gate 7/7; CLI K = 0 dq equals the references to 4.8e-14) |
| "K = 0: n_clock 8, 14 qubits, 2,054,602 CX / depth 4,067,708, fidelity 0.9999571, residual 4.21e-2, 98 s" (README) | measured-in-this-branch; reproduced here exactly except wall 100.8 s |
| "K = 2: kappa_eff 16.3, n_clock 7, 13 qubits, 1,022,314 CX / depth 2,024,100, fidelity 0.9999949, residual 7.09e-2, 43 s, 92 % of ||x||^2 classical" (README) | measured-in-this-branch; reproduced here exactly (43.8 s) |
| "iteration-14 Jacobian: kappa 67.6 -> 15.0, 8 -> 7 clock qubits, 35 % classical share at K = 2" (README) | dry-check-only, and labelled so in the README ("classical dry check"); reproduced by `tests/test_deflation.py` and by my numpy |
| "about 13x fewer post-selected shots" (06a and the work-item text; NOT in README or help) | dry-check-only (P_succ proxy with C = lambda_min); no shots-mode run with deflation exists in this branch, so unsupported by measurement; the branch correctly does not quote it |
| "the first update is almost entirely the two slowest modes" (README) | measured-in-this-branch (x_share 0.9234) |
| "resource reduction for the quantum kernel given a classical rank-K preconditioner ... no speedup is claimed" (README, help) | explicit disclaimer; the branch makes no speedup claim anywhere (grep `speedup` in the diff: only the disclaimers) |
| "the dense SVD is a full classical solve at this size" (README, help) | statement of method, correct |
| TESTING (l): "fidelity 0.9999942 vs 0.9999986 at k = 0", "fb_cx_count 116067 < 234899", "0.24 %" rel L2, "0.3 ms" t_svd | measured-in-this-branch; mine 0.9999942 / 0.9999986, 116,067 / 234,899, 0.242 %, 0.05 ms |
| README line 38 "Potential speedup: Theoretically O(log N) vs O(N)" | pre-existing general HHL text, not about deflation, outside the item |

## Findings

- F1 (low, documentation, outside the commit range): the 06a table rounds the
  iteration-14 x-share to "59 %" at k = 3 and "72 %" at k = 4, but
  `kappa_eff_deflation_output.txt` (and the module, and my numpy) give 0.602
  and 0.727, i.e. 60 % and 73 %. The module reproduces the output file; the
  README quotes only the k = 2 value (35 %), which is right. Fix the two
  cells in `06a-deflation-numbers-and-recommendation.md` when it is next
  edited (the acceptance-criteria text inherited the 59 %).
- F2 (low, interpretation for the paper row): at iteration 0 the K = 2
  fidelity / rel-L2 improvement vs LU is dominated by the exact classical
  92 % share, not by a more accurate quantum kernel. Isolating the quantum
  part y = x - correction of R8: `||y_hhl - y_exact|| / ||y_exact||` =
  8.2e-3 and `||A' y_hhl - b||` = 7.10e-2, versus the K = 0 full solve's
  6.8e-3 relative error. So with one clock qubit fewer the kernel's own
  relative accuracy on A' y = b is about the same (slightly worse), and the
  headline fidelity gain is the classical part. The README does print the
  92 % next to the fidelity, which is the disclosure the item demands; a
  paper row should additionally quote the quantum-part error (or compare at
  iteration 14, where the share is 35 %). Not a defect; a caveat.
- F3 (info, pre-existing, out of scope): `circuit_generated_*.qpy` of the HHL
  circuit does not load back through `qiskit.qpy.load`
  (`ExactReciprocalGate.__init__() missing 2 required positional arguments`);
  the transpiled `.qpy` loads fine. This affects `-loadcirc`, not this item;
  `n_clock` is read from the in-memory circuit, so it is unaffected.
- Note (no action): `-hhl_deflate_k 0` with `-linsolver SQLS` / `LU` is
  accepted (it is the default); only K > 0 is rejected. Sensible.

## Not checked, and why

- Shots mode with deflation (the `dq_herm_q` per-component sign path): no
  shots-mode nelem-5 run is allowed and nelem-2 shots runs were not in the
  allowed list; verified by code reading only (`time_solvers.py`, the
  `if self.linsolv_args['shots']` block uses `dq_herm_q`).
- The "13x fewer shots" dry-check proxy against real post-selected counts.
- Multi-step Newton convergence with deflation (only `-iters 1` runs); the
  15-minute run; Frontier; fake / GPU backends; `-loadcirc` with deflation.
- `-hhl_scale true_sol` at nelem 5 (only nelem 2, R10).
