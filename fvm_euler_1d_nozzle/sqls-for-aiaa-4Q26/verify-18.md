# Item 18 verification, round 1: sqls smallest-k SVD as a second deflation backend

Independent verifier report. Written 2026-10-19T00:35Z (UTC). I did not
read the builder's narrative before checking; I read the diffs, ran the
tests and wrote my own checks. All my scratch lived under
`/tmp/item18-19-verifier/` and was removed at the end. Nothing was
committed. No code was edited.

Verdict: **PASS** on all nine criteria. Non-blocking observations are
listed at the end.

## State checked

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90` (committed
  2026-10-15T20:41:46-04:00, i.e. 2026-10-16T00:41:46Z). Working tree
  uncommitted. `git diff | shasum -a 256` =
  `ba85da2213c8285941ed8f5ed15732e5a1102281cce5f6864458fdea856a0931`,
  unchanged by my work. Modified: README.md, TESTING.md, deflation.py,
  docs/FRONTIER_CONDA_SETUP.md, docs/QUICKSTART_PARALLEL.md,
  math_tools.py, nozzle_1d_solver.py, pyproject.toml, quantum_tools.py,
  tests/contract.py, tests/test_output_contract.py, tests/test_sqls.py,
  time_solvers.py, uv.lock. Untracked: hhl_spectrum.py,
  tests/test_deflation_svd.py, tests/test_hhl_spectrum.py.
- The earlier-today pyproject.toml / uv.lock change is intact:
  `[tool.uv.sources]` has `sqls` as git
  `https://github.com/Q8020-CFD/sqls.git` rev `187a7a54...8f34` and
  `quantum_linear_solvers` as git rev `9d1d7bbb...5cdc`; uv.lock carries the
  same two git sources. The task's fingerprint `8b541216...` is of the diff
  before item 19 landed, so it cannot be re-checked as a hash; I checked the
  content instead.
- HHL fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, HEAD
  `9d1d7bb`, uncommitted item-19 diff. `git diff | shasum -a 256` =
  `67e9f74ab95956ab67e9c67f8d0a9ec569a0b7332464f22cf3b7f73b59c65e76`,
  byte-equal to
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`
  (`diff` reports no difference). Item 18 did not touch the fork.
- sqls: `/Users/agallojr/proj/src/q8020/sqls` at `187a7a5`, clean. The fvm
  venv has it as a pinned git install (`direct_url.json`: vcs git, commit
  `187a7a54...`), import path
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/sqls/`.
- fvm venv: `linear_solvers` is the editable dev override
  (`direct_url.json`: `file:///Users/agallojr/proj/src/q8020/quantum_linear_solvers`,
  editable true). Still in place at the end.
- Stack: Python 3.12.10, numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2. Machine:
  Apple M3 Pro, 36 GiB RAM, macOS 26.7.1 arm64.

## Commands I ran, with wall times

| Command (from the fvm repo, `.venv/bin/python`) | Wall | Result |
|---|---|---|
| `-m unittest tests.test_deflation_svd -v` | 38.8 s (39.7 s process) | 31 tests OK |
| `-m unittest tests.test_deflation -v` | 29.3 s (29.8 s process) | 17 tests OK (file unchanged in git) |
| `-m unittest tests.test_hhl_spectrum -v` | 77.5 s (78.5 s process) | 23 tests OK |
| own script `ac18_1_numpy_identical.py` (HEAD deflation.py vs working tree) | about 1 s | bitwise identical, 36 cases |
| own script `ac18_5_equivalence.py` (9 Jacobians, k = 1 to 4) | about 2 s | table below |
| own script `ac18_8_profile.py` (sys.setprofile log, 4 in-process `hhl_solve`) | 40.2 s | table below |
| CLI nelem 2, `-hhl_deflate_k 1 -hhl_deflate_svd numpy`, 2026-10-19T00:28:39Z | 6.0 s | outputs under /tmp, deleted |
| CLI nelem 2, `-hhl_deflate_k 1 -hhl_deflate_svd sqls` | 6.4 s | outputs under /tmp, deleted |
| own script `ac18_7_timing.py`, 2026-10-19T00:30:36Z to 00:31:21Z | 45.4 s | table below |
| `-m unittest discover -s tests` (full default suite, background) | see the last section | |

The full CLI argument lists were
`nozzle_1d_solver.py -nelem 2 -linsolver HHL -shots 0 -iters 1 -hhl_deflate_k 1 -hhl_deflate_svd {numpy|sqls} -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow -v 0 -outdir /tmp/item18-19-verifier/cli_{numpy|sqls}`.

Not run (over the 60 s single-run limit; for the operator):
`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture`
(about 90 s).

## AC18-1: flag, default, numpy unchanged. PASS

- `-hhl_deflate_svd {numpy,sqls}` exists, default `numpy`
  (`nozzle_1d_solver.py -h` lists it with `[numpy]`; `deflation.DEFLATE_SVD_DEFAULT = 'numpy'`).
- The numpy path is the old code. I loaded `git show HEAD:deflation.py` as a
  separate module and compared it with the working-tree `deflate()` on all
  nine archived Jacobians, k = 1 to 4 (36 cases): `sigma`, `u`, `v`, `ub`,
  `a_shifted`, `correction()`, `recombine()`, `kappa`, `kappa_eff`,
  `x_share_classical` and the six `deflation_columns` (except the wall time)
  are bitwise equal (`np.array_equal`, `==`).
- `tests/test_deflation.py` is unchanged in git and passes (17 tests,
  29.3 s).
- CLI numpy run: 51-column `qc_metadata` header equal to
  `contract.QC_METADATA_HHL_COLUMNS`; `deflate_k` 1, `kappa` 38.306,
  `kappa_eff` 6.8498, `n_clock` 6, `circ_qubits` 11, `x_share_classical`
  0.95113, the same values TESTING.md section (l) records for this run.
- Note on "outputs identical": the deflation record is bitwise identical.
  HHL outputs of the same code differ between processes anyway
  (`circ_gates_transpile` 37117 vs 36930 between my two runs; transpiler
  non-determinism, pre-existing), so bitwise identity of a whole run is not
  a meaningful bar.

## AC18-2: installed smallest_k_svd, k + 1, cheap sigma_max, tolerances recorded. PASS

- `deflation._deflate_sqls` imports `smallest_k_svd` from
  `sqls.core.truncated_svd` (lazy import, `_smallest_k_svd()`); there is no
  copy of its code in fvm. The installed module is the pinned git install
  under `.venv/.../site-packages/sqls/`.
- It is called as `smallest_k_svd(a_sp, k + 1, tol=tol, maxiter=maxiter)`
  with a CSR matrix. `tests/test_deflation_svd.py::TestSqlsBackendRecord::test_sqls_routine_is_the_installed_one`
  spies the call (k = 3 gives `args[1] == 4`, `tol == 1e-11`). My own run
  of `deflate(a, b, k, svd='sqls')` returns `sigma.shape == (k + 1,)` in all
  36 cases.
- sigma_max: `deflation.sigma_max_estimate` runs
  `scipy.sparse.linalg.eigsh(op, k=1, which='LA', tol=tol, v0=seeded)` on
  the `LinearOperator` x -> A^T (A x), then `sqrt`. Not a full SVD. The
  estimate is checked against the norm bounds
  max column / row 2-norm <= ||A||_2 <= sqrt(||A||_1 ||A||_inf).
- Tolerances: `-hhl_deflate_svd_tol` (default 1e-12, range [0, 1e-6]) is
  passed to both Lanczos runs and recorded as `svd_tol` and `sigma_max_tol`
  in the CSV (my sqls CLI run: both `1e-12`), as `hhl_deflate_svd_tol` in
  the pickle (`1e-12`; `None` for numpy), and the method as
  `sigma_max_method = eigsh_ata` (`numpy_svd` for numpy).
- Documented in the `deflation.py` module docstring and in README
  "Two backends for the deflation pre-step".

## AC18-3: Deflation with a partial spectrum. PASS

- `Deflation` carries `sigma_max` and `x_norm2` for the sqls backend;
  `shift`, `kappa` (= sigma_max_est / sigma_0), `kappa_eff`
  (= sigma_max_est / sigma_k, 0-based) and `x_share_classical`
  (= sum_{i<k} (u_i . b / sigma_i)^2 / ||x||^2) branch on them.
  `correction()` and `recombine()` use `sigma[:k]`, `v[:, :k]`, `shift`,
  so they work with k + 1 triplets.
- My check on all 36 cases: `recombine(A'^-1 b)` vs `np.linalg.solve(A, b)`
  worst 1.5e-13 relative (limit 1e-8); the singular values of the sqls A'
  equal {sigma_k .. sigma_{N-1}} plus k copies of sigma_max to 6.2e-15
  relative; `kappa` and `kappa_eff` agree with numpy to 4.9e-15 and
  2.0e-15 relative.
- ||x||^2: one `scipy.sparse.linalg.splu(A).solve(b)`, labeled
  `x_share_method = splu_solve`, timed as `t_xshare_s` outside `t_svd_s`
  (my sqls CLI run: 4.1e-5 s against `t_svd_s` 1.09e-3 s). The code
  comment and README say it is a metric only; nothing on the solve path
  uses that x (I confirmed `x_ref` is used only for `x_norm2`).
- No full SVD anywhere in the sqls backend: see AC18-8 (zero dense
  spectral calls in the whole solve, including the backend).
- Boundary: k = N - 2 = 13 on the 15 x 15 iteration-14 Jacobian works
  (`sigma.shape (14,)`, `kappa_eff` 1.13718 vs numpy to 2.5e-15 relative).

## AC18-4: metadata. PASS

- Nine new CSV columns after `t_spectrum_s` and before the fairness
  columns: `hhl_deflate_svd, svd_tol, sigma_max_method, sigma_max_tol,
  t_smallest_k_s, t_sigma_max_s, x_share_method, t_xshare_s, svd_residual`
  (`contract.QC_METADATA_SVD_BACKEND_COLUMNS`, equal to
  `deflation.SVD_BACKEND_COLUMNS`; the test asserts the constants match).
  My two CLI runs: header equal to `contract.QC_METADATA_HHL_COLUMNS`
  (51 columns). Values as expected (numpy: `numpy`, '', `numpy_svd`, '',
  3.5e-5 s, 0.0, `svd`, 0.0, ''; sqls: `sqls`, 1e-12, `eigsh_ata`, 1e-12,
  5.0e-4 s, 3.9e-4 s, `splu_solve`, 4.1e-5 s, 3.9e-15).
- Pickle: `hhl_deflate_svd` and `hhl_deflate_svd_tol` keys
  (`contract.METADATA_KEYS_HHL_ONLY`); `quantum_circuit` carries the nine
  values of the last step (key set equal to
  `contract.QUANTUM_CIRCUIT_KEYS['HHL']`, values equal to the CSV row).
- Existing column names are unchanged. The fairness columns move nine
  places right, as they did for item 19; the harvester reads by name
  (`csv.DictReader`, line 41), so order does not matter.
- Sentinel convention: empty cells for not-applicable strings and
  tolerances, `0.0` for times that were not spent, the convention of the
  fb_* columns and of the item-6 columns at k = 0 (TESTING.md section (h):
  "empty rather than -1 / 0.0 sentinels"). Followed.
- `tests/contract.py` and TESTING.md (new section (n), the summary table
  row, the column list) are updated.
- Harvester: not edited (its mtime is 2026-10-18 19:43 local, before item
  18). The needed changes are listed in build-18.md, section "Harvester
  changes needed (not made)": a `_deflation_svd(row)` reader, its
  attachment per step, additions to `_deflation_summary` and
  `_spectrum_summary` (`t_xshare_total_s`), and the two run-parameter
  keys.

## AC18-5: equivalence on every archived Jacobian. PASS

My own script (own reference: `np.linalg.svd` of A and `np.linalg.solve`,
not the builder's helpers), nine systems
(`system_Ab_nelem5_iter0..6.pkl`, `_iter14.pkl`, `system_Ab_nelem2_iter0.pkl`),
k = 1 to 4, tol 1e-12. Worst values over the 36 cases:

| Quantity | Worst | Limit |
|---|---|---|
| singular values sigma_0..sigma_k, relative | 4.9e-15 | 1e-8 |
| principal angles, left k-dim subspace | 2.1e-14 rad | 1e-6 rad |
| principal angles, right k-dim subspace | 1.1e-14 rad | 1e-6 rad |
| smallest relative gap (sigma_k - sigma_{k-1}) / sigma_k at any cut | 0.040 (nelem 5 iter 0, k = 3) | subspaces well defined; no near-degenerate cut |
| sigma_max estimate, relative, absolute value | 6.1e-16 | about tol / 2 = 5e-13 |
| sigma_max estimate, signed maximum | +6.1e-16 | never above sigma_max beyond 4 eps = 8.9e-16 |
| A' Frobenius, relative | 9.6e-15 | 1e-8 |
| singular values of A' vs {sigma_k..} + k x sigma_max, relative | 6.2e-15 | |
| kappa_eff, relative | 2.0e-15 | identical n_clock |
| n_clock = max(n_b + 1, ceil(log2(kappa_eff + 1))) + 1 | 6/6 (nelem 2), 7/7 (nelem 5), both backends | identical |
| recombine(A'^-1 b) vs A^-1 b, relative | 1.5e-13 | 1e-8 |
| x_share_classical, absolute | 1.0e-13 | |
| sqls residual max_i ||A^T u_i - sigma_i v_i|| / sigma_max | 1.8e-14 | |

Near-degenerate values: none in the archived set (smallest gap 0.040).
The builder's test asserts the gap above 1e-3 before comparing angles and
adds a synthetic exactly degenerate cut where only kappa_eff, the A'
spectrum and the recombined solution are compared. That is the honest
handling.

nelem-2 CLI HHL runs, `-hhl_deflate_k 1`, one Newton step, each backend:
`circ_qubits` 11 and `n_clock` 6 in both; `dq_hhl` differs by 1.14e-14
max-abs, 2.7e-14 relative (limit 1e-8); `fidelity` 0.99999416 in both;
`kappa_eff` 6.8498325090581 vs 6.849832509058088.

## AC18-6: validation and failure modes. PASS

- Parse time: `check_deflate_svd` is called in `nozzle_1d_solver.py` with
  N = 3 * nelem before any solve; `-hhl_deflate_k 5 -hhl_deflate_svd sqls`
  at nelem 2 exits 2 with "K + 1 < N = 6 ... K <= 4" and writes nothing
  (`TestDeflateSvdCLIValidation`, passed). Also rejected: a tolerance with
  numpy, a tolerance above 1e-6 or below 0, the flags with `-linsolver`
  LU / SQLS, an unknown choice. `LinearSystemSolver.__init__` repeats the
  check for in-process use.
- Lanczos non-convergence: `ArpackError` (which includes
  `ArpackNoConvergence`) from either run is re-raised as `RuntimeError`
  with the routine, N, tol and maxiter in the message (test: clustered
  400 x 400 spectrum, `maxiter=1`, both runs raise).
- Singular A: `splu` "exactly singular" becomes `ValueError('... A is
  singular ...')`; sigma_0 <= N eps sigma_max becomes `ValueError('A is
  numerically singular ...')` (tests pass).
- A-posteriori guards: sigma_max outside the norm bounds, unsorted or
  non-finite triplets, residual or orthonormality defect above 1e-6 all
  raise `RuntimeError` (tests with patched `eigsh` / `smallest_k_svd`
  pass). No silent fallback path exists in `_deflate_sqls`.
- Loose tolerance probe (tol 1e-6, nelem 5 iter 14, k = 2): sigma still
  within 3.0e-15 relative, sigma_max within 2.4e-16, residual 5.9e-15.

## AC18-7: cost comparison. PASS

build-18.md has the table (median of 7 repeats, N = 15 to 2046, k = 2 and
4, machine and versions stated). I reproduced it with my own script:
Jacobians assembled in-process with `SpaceSolver` + `BDFTimeSolver`
(CFL 1e10, BDF1, local dt, iteration 0), median of 5 repeats, tol 1e-12,
no solver files written. Wall times in milliseconds unless marked;
`sqls` = whole pre-step (`t_svd_s`), split times from the record.

| nelem | N | k | nnz | band nnz | max off-band / max entry | kappa | numpy | sqls | sqls smallest-k | sqls sigma_max | sqls x_share solve | faster |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 15 | 2 | 149 | 149 | 0 | 96 | 0.045 | 0.730 | 0.311 | 0.312 | 0.034 | numpy 16x |
| 5 | 15 | 4 | 149 | 149 | 0 | 96 | 0.048 | 0.716 | 0.302 | 0.309 | 0.034 | numpy 15x |
| 11 | 33 | 2 | 383 | 383 | 0 | 219 | 0.119 | 0.910 | 0.416 | 0.373 | 0.043 | numpy 7.7x |
| 11 | 33 | 4 | 383 | 383 | 0 | 219 | 0.108 | 0.931 | 0.416 | 0.378 | 0.052 | numpy 8.7x |
| 21 | 63 | 2 | 773 | 773 | 0 | 422 | 0.311 | 1.313 | 0.483 | 0.639 | 0.057 | numpy 4.2x |
| 21 | 63 | 4 | 773 | 773 | 0 | 422 | 0.308 | 1.320 | 0.503 | 0.685 | 0.063 | numpy 4.3x |
| 42 | 126 | 2 | 3634 | 1739 | 1.1e-9 | 851 | 1.376 | 2.596 | 0.821 | 1.387 | 0.143 | numpy 1.9x |
| 42 | 126 | 4 | 3634 | 1739 | 1.1e-9 | 851 | 1.203 | 2.556 | 0.865 | 1.368 | 0.145 | numpy 2.1x |
| 85 | 255 | 2 | 3269 | 3269 | 0 | 1731 | 6.040 | 4.142 | 0.983 | 2.644 | 0.148 | sqls 1.5x |
| 85 | 255 | 4 | 3269 | 3269 | 0 | 1731 | 6.158 | 4.125 | 0.928 | 2.673 | 0.141 | sqls 1.5x |
| 170 | 510 | 2 | 44369 | 7216 | 5.5e-10 | 3469 | 28.09 | 38.01 | 6.64 | 27.90 | 1.71 | numpy 1.4x |
| 170 | 510 | 4 | 44369 | 7216 | 5.5e-10 | 3469 | 25.96 | 39.38 | 6.97 | 28.33 | 1.85 | numpy 1.5x |
| 341 | 1023 | 2 | 13253 | 13253 | 0 | 6967 | 159.4 | 40.24 | 2.99 | 32.30 | 0.45 | sqls 4.0x |
| 341 | 1023 | 4 | 13253 | 13253 | 0 | 6967 | 150.5 | 38.12 | 2.53 | 32.02 | 0.40 | sqls 3.9x |
| 682 | 2046 | 2 | 629626 | 29079 | 2.7e-10 | 13940 | 1118.8 | 2685.0 | 162.1 | 2486.8 | 27.3 | numpy 2.4x |
| 682 | 2046 | 4 | 629626 | 29079 | 2.7e-10 | 13940 | 1114.0 | 2684.9 | 161.7 | 2496.1 | 27.3 | numpy 2.4x |

Accuracy on the same matrices: sigma relative 1.2e-15 to 3.0e-13, A'
relative (Frobenius) 6.5e-15 to 1.5e-13 (worst at N = 2046).

My numbers agree with the builder's table to about 10 % in every row and
give the same winner in every row. The report's reading is honest: numpy
wins below N = 255; sqls wins at N = 255 (1.5x) and N = 1023 (4x); numpy
wins again at N = 510 and 2046 because the finite-difference Jacobian at
nelem 42, 170 and 682 carries round-off fill outside the band (up to
1.1e-9 of the largest entry; 15 % dense at nelem 682), which defeats the
sparse LU. The sigma_max Lanczos is the dominant sqls cost (clustered top
of the spectrum). The x_share solve is at most 3 % of the sqls pre-step.
Note N = 126 at nelem 42 (3 x 42), not 127 as in the criterion text.

## AC18-8: no dense full-spectrum routine on the solve path. PASS

Independent method: `sys.setprofile` hook recording every Python-level
call whose code object lives in `numpy/linalg` or `scipy/linalg` and is
named svd, cond, eig, eigvals, eigh, eigvalsh, svdvals, schur,
eigh_tridiagonal, matrix_rank, pinv, or norm with ord in {2, -2, 'nuc'}.
This catches aliased imports and nested calls (e.g. cond -> svd) without
patching anything. One in-process `hhl_solve` on the archived nelem-2
system, `hhl_deflate_k=1`, verbosity 0:

| Configuration | Dense spectral calls |
|---|---|
| sqls, `-hhl_spectrum deflation`, `-hhl_spectral_diag off` | **0** |
| numpy, `-hhl_spectrum deflation`, `-hhl_spectral_diag off` | 1: `svd` of the 6 x 6 A from `deflation.deflate` (the backend itself) |
| sqls, `-hhl_spectrum deflation`, diag on (default) | 6: cond (-> svd) and eigvals of A' and of the scaled A', all from `math_tools.get_matrix_properties` (the diagnostic columns; switched off by `-hhl_spectral_diag off`) |
| sqls, `-hhl_spectrum internal` (default), diag on | 10: the 6 diagnostics above, plus `eig` of A' in `math_tools.scale_Ab` (spectral-radius scale) and the library's cond + eigvals of the 16 x 16 encoded H in `quantum_tools.generate_circuit` |

The builder's `GlobalSpectralCallLog` (mock-based, 43 bindings) gives the
same result and the test passes. Remaining dense calls, all outside the
AC18-8 configuration: `get_matrix_properties` (diagnostic, flag
`-hhl_spectral_diag off`), `scale_Ab` spectral-radius `eig` and the
library's internal bounds (both skipped by `-hhl_spectrum deflation`), and
the `math_tools` verbosity prints (`det`, `cond`) at `-v 1` and above.
The classical `np.linalg.solve` / LU calls for `dq_lu`, `dq_herm` and the
x_share `splu` are solves, not spectrum routines, and are labeled classical.

## AC18-9: hygiene. PASS

- Style: no line over 88 characters and no trailing whitespace in
  deflation.py, hhl_spectrum.py, tests/test_deflation_svd.py,
  tests/test_hhl_spectrum.py, nor in any added line of the modified files
  (own scan). Imports grouped at the top; type hints on the new functions;
  `unittest.TestCase`-based tests; longest new test about 8 s (the cached
  CLI runs).
- Tests: 31 new tests in `tests/test_deflation_svd.py`, all pass.
- README: section "Two backends for the deflation pre-step
  (`-hhl_deflate_svd`, work-plan item 18)" explains both backends, states
  "Both are classical. Neither is part of the quantum solve.", the
  sigma_max and x_share methods, the checks, reproducibility, the
  equivalence numbers and a cost summary; the flag table has both new
  flags; "What is classical in each quantum path" is updated. TESTING.md
  has section (n) and the measured suite line.
- Attribution: README line 435 and TESTING.md line 719 read "(sqls
  smallest_k_svd, ORNL sqls package, refs 13 to 15 of the AIAA abstract;
  source attribution to be confirmed)". Same substance as the required
  wording; the only difference is a comma where the criterion has an
  opening parenthesis after `smallest_k_svd` (see observations).
- Nothing committed: the last commits in fvm, the fork and sqls are dated
  2026-10-15 (local); all item-18 and item-19 work is in uncommitted
  working trees; the fork patch file is current.
- Today's pyproject.toml / uv.lock git-source change is intact (see State
  checked).
- No stray files in the repos (`git status` shows only the intended
  files). The fork dev override remains installed.

## Non-blocking observations

1. Attribution punctuation differs from the criterion's literal string
   (comma instead of a parenthesis after `smallest_k_svd`). One-word edit
   if the exact string matters for the paper.
2. `pyproject.toml` `py-modules` lists neither `deflation` nor
   `hhl_spectrum` (nor was `deflation` added at item 6). The CLI and tests
   run from the repo root, so nothing breaks today; a non-editable install
   of fvm would miss both modules. The builder flagged it too.
3. `-hhl_deflate_svd sqls` with `-hhl_deflate_k 0` is accepted: no pre-step
   runs, the CSV cell `hhl_deflate_svd` is '' (documented) while the pickle
   records `sqls` and `hhl_deflate_svd_tol` 1e-12. Harmless but
   inconsistent; a parse-time warning or an error would be cleaner.
4. The sqls backend is not bit-reproducible: `smallest_k_svd` passes no
   start vector to `eigsh`, so two runs differ (sigma by 1.1e-15, A' by
   4.0e-13 absolute in my probe). Documented in README; a seed would need a
   change to sqls (read-only here).
5. A zero right-hand side gives `x_share_classical = nan` with a
   `RuntimeWarning` in both backends (0 / 0). Pre-existing for numpy; not
   reachable from the Newton loop with a non-converged residual.
6. The four `test_code_versions` failures in the full suite are the
   documented effect of the editable fork override (`commit_source git`,
   `dirty True` for `linear_solvers`), the same as under item 19. They clear
   once the fork is committed, the rev bumped and the lock refreshed.
7. `/tmp/item18-19-reproducer/` (another role's scratch) existed at
   2026-10-19T00:29Z and was gone by 00:37Z. I did not touch it.

## Full default suite

`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && .venv/bin/python -m unittest discover -s tests`,
2026-10-19T00:32:28Z to 00:36:26Z: **211 tests in 235.3 s (238.1 s
process), 206 pass, 4 fail, 1 skipped.** The 4 failures are
`test_output_contract.{TestHHL,TestHHLShots,TestLU,TestSQLS}OutputContract.test_code_versions`,
each `AssertionError: 'git' != 'direct_url'` for `linear_solvers`: the
editable fork dev override that the task asks to leave in place
(observation 6). No other failure. Same count and the same four failures
as TESTING.md records for item 18.

## Cleanup

`/tmp/item18-19-verifier/` (my scripts, the two nelem-2 CLI output trees
and the logs) was removed after this report was written. The fvm working
tree fingerprint is unchanged (`ba85da22...0931`); the fork and sqls trees
are as found.
