# Item 18 build: sqls smallest-k SVD as a second deflation backend

Builder report. Work ran 2026-10-18T23:50Z to 2026-10-19T00:20Z (UTC).
Nothing is committed. A separate verifier judges AC18-1 to AC18-9. This
report only says what was built and what was measured.

## Summary

- New fvm flag `-hhl_deflate_svd {numpy, sqls}`, default `numpy`.
- `numpy` is the old path. Its numbers are bit-identical to the
  pre-item-18 module on all 36 archived cases (9 systems, k = 1 to 4).
- `sqls` calls `sqls.core.truncated_svd.smallest_k_svd` from the
  installed sqls. It asks for k + 1 triplets.
- sigma_max comes from ARPACK Lanczos on A^T A (`eigsh`, k = 1). This is
  not a full SVD.
- ||x||^2 for `x_share_classical` comes from one sparse LU solve. That
  solve is timed on its own.
- New flag `-hhl_deflate_svd_tol` (default 1e-12). It sets the tolerance
  of both Lanczos runs and applies to `sqls` only.
- Nine new qc_metadata columns record the backend, the methods, the
  tolerances, the split times and a residual check. Two new pickle keys
  record the flags.
- Equivalence on the archived Jacobians is about 1e-14 or better. The
  tolerances asked for are 1e-8 and 1e-6 rad.
- With `sqls`, `-hhl_spectrum deflation` and `-hhl_spectral_diag off`,
  no dense full-spectrum routine runs on the solve path. This holds for
  every module, qiskit and scipy included.
- Cost: numpy wins below N = 255. sqls wins at N = 255 (1.4x) and
  N = 1023 (4.0x). numpy wins at N = 510 and N = 2046, because the fvm
  Jacobian at those sizes carries round-off fill (details below).
- Full fvm suite: 211 tests, 206 pass, 4 fail, 1 skipped, 227.9 s. The 4
  failures are the `test_code_versions` cases already reported for item
  19. They come from the editable fork override.

## Repos and state

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90`, uncommitted.
  - `git diff | shasum -a 256` before my work: `5bd4c7e5...a126c`. This is
    the post-item-19 state. The task text quotes `8b541216...`, which is
    the state before item 19 landed.
  - After my work: `ba85da22...0931`. The untracked file
    `tests/test_deflation_svd.py` is new.
  - `pyproject.toml` and `uv.lock` are untouched. Their pinned git
    sources are intact.
- HHL fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, HEAD
  `9d1d7bb`, not edited by me.
  - `git diff` sha256 is `67e9f74a...5e76`, equal to
    `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`.
    So that patch did not need regenerating.
  - The editable override is still installed in the fvm venv
    (`direct_url.json`: `file://...quantum_linear_solvers`, editable).
- sqls: `/Users/agallojr/proj/src/q8020/sqls` at `187a7a5`, clean, not
  edited. The fvm venv has the pinned git install.
- Harvester: not edited. The changes it needs are listed below.
- Stack: Python 3.12.10, numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2,
  qiskit-aer 0.17.2. Machine: Apple M3 Pro, 12 cores, 36 GiB RAM, macOS
  26.7.1 (arm64).

## What changed (fvm)

### `deflation.py`

- `:1-53` module docstring: the two backends, the sigma_max method, the
  x_share solve, the checks and the reproducibility note.
- `:56-58` imports: `scipy.sparse`; `ArpackError`, `LinearOperator`,
  `eigsh`, `splu` from `scipy.sparse.linalg`.
- `:66-82` constants: `DEFLATE_SVD_CHOICES`, `DEFLATE_SVD_DEFAULT`,
  `DEFLATE_SVD_TOL_DEFAULT` = 1e-12, `DEFLATE_SVD_TOL_MAX` = 1e-6,
  `SVD_CHECK_TOL` = 1e-6, `SIGMA_MAX_SEED` = 0, `SIGMA_MAX_METHODS`,
  `X_SHARE_METHODS`, `SVD_BACKEND_COLUMNS`.
- `:85-101` new frozen dataclass `SvdInfo`: the backend, tolerances,
  methods, split times and residual.
- `:104-169` `Deflation` gains three optional fields with defaults:
  - `sigma_max`: None means "use sigma[-1]", the full-spectrum case.
  - `x_norm2`: None means "use the full spectrum".
  - `svd`: the SvdInfo record.

  `shift`, `kappa`, `kappa_eff` and `x_share_classical` branch on these.
  On the numpy path they keep the old expressions exactly.
  `correction()` and `recombine()` are unchanged and work with k + 1
  columns.
- `:172-198` `check_deflate_svd(svd, tol, k, n)`. It holds the rules in
  one place, for the CLI and the class. It returns the effective
  tolerance.
- `:201-238` `deflate(a, b, k, svd='numpy', tol=None, maxiter=None)`. The
  numpy branch has the same arithmetic as before. It now also times the
  SVD alone (`t_smallest_k_s`) and attaches an `SvdInfo`.
- `:241-250` `_smallest_k_svd()` imports sqls lazily. Importing sqls pulls
  in qiskit (about 1 s), which LU runs never need.
- `:253-281` `sigma_max_estimate(a_sp, tol, maxiter)`. It runs ARPACK
  Lanczos on the operator A^T A (k = 1, which `LA`, seeded start vector).
  It then checks the result against the norm bounds max column or row
  2-norm <= ||A||_2 <= sqrt(||A||_1 ||A||_inf).
- `:284-324` `_deflate_sqls`, in order:
  1. Converts dense A to CSR.
  2. Calls `smallest_k_svd(a_sp, k + 1, tol=tol, maxiter=maxiter)`.
  3. Estimates sigma_max.
  4. Runs the checks.
  5. Applies the rank-k update.
  6. Does the x_share sparse LU solve, which is timed separately.
- `:327-357` `_check_triplets` raises on any of these:
  - non-finite or unsorted output;
  - a numerically singular A (sigma_0 <= N eps sigma_max);
  - a sigma_max estimate below sigma_k;
  - a relative residual or an orthonormality defect above 1e-6.
- `:386-406` `svd_backend_columns(defl)`: the nine columns.

### Other fvm files

- `time_solvers.py:15` imports. `:323-329` reads `hhl_deflate_svd` and
  `hhl_deflate_svd_tol` and validates them with N = 3 * nelem. `:603-611`
  passes them to `deflate()`.
- `quantum_tools.py:18` import. `:969-972` puts the nine values into
  `qc_metadata`, the pickle's `quantum_circuit`. `:1024-1028` puts them
  into the CSV row, after the spectrum columns and before the fairness
  columns.
- `nozzle_1d_solver.py:9` `import deflation`. `:156-176` the two new
  flags with help text. `:298-303` HHL-only rejection. `:329-339`
  parse-time check (K + 1 < N for sqls, tol rules). The effective tol
  goes into `linsolv_args`. `:561-564` pickle keys `hhl_deflate_svd` and
  `hhl_deflate_svd_tol`.
- `hhl_spectrum.py:21-27, 35-41` docstring only. It says where both ends
  of the spectrum come from under sqls. It also notes that sigma_max is a
  Lanczos lower bound, which leaves lambda_max(H) a hair above the
  supplied 1. The QPE phase of lambda_max sits near 1/2, with a margin of
  about 2^-n_l, so this has no effect beyond round-off.
- `tests/contract.py:110-134` `QC_METADATA_SVD_BACKEND_COLUMNS`, with a
  comment for every column, and the choice and method constants. `:147`
  adds the columns to `QC_METADATA_HHL_COLUMNS`. `:198-206` adds the two
  `METADATA_KEYS_HHL_ONLY` keys. `:210-217` adds the nine
  `QUANTUM_CIRCUIT_KEYS['HHL']` keys.
- `tests/test_deflation_svd.py` (new, 554 lines, 31 tests). This is
  TESTING section (n).
- `README.md`:
  - `:190-191` two CLI table rows;
  - `:273-274` pickle sentence;
  - `:424-517` new section "Two backends for the deflation pre-step";
  - the "What is classical" bullet;
  - the code tree comment.
- `TESTING.md`: the item-18 run record, the layout row, the contract row
  and the new section (n).

## Design choices and why

- **k + 1 triplets.** kappa_eff = sigma_max / sigma_k (0-based) needs
  sigma_k. So the backend asks `smallest_k_svd` for k + 1 triplets. Only
  the first k are deflated. That is why the sqls backend needs
  k + 1 < N.
- **sigma_max by Lanczos on A^T A, not `svds`.** `scipy.sparse.linalg.svds`
  can call a dense SVD internally on its small projected matrix. That
  would show up in the AC18-8 call log. Calling `eigsh` directly is
  simpler and seedable.
  - The tolerance is the ARPACK relative eigenvalue tolerance on
    lambda_max(A^T A).
  - A Lanczos Ritz value is a lower bound (up to round-off). So
    sigma_max_est is low by at most about tol / 2 relative.
  - Measured: within 6.2e-16 relative of the numpy SVD on the archived
    systems, and within 3.7e-15 up to N = 2046.
- **The estimate is also the shift and the scale.** The deflation
  identity x = y + sum (u.b)(1/sigma_i - 1/shift) v_i is exact for any
  shift. Using the estimate keeps it exact.
- **x_share by one sparse LU solve.** The k + 1 triplets give the
  numerator of the share, sum_{i<k} (u_i.b / sigma_i)^2. They do not give
  ||x||^2. One `splu(A).solve(b)` gives it.
  - It is a metric only. Nothing on the solve path uses that x.
  - Its time is the `t_xshare_s` column. It is not in `t_svd_s`.
  - Another option would reuse `dq_lu`, which `hhl_solve` already
    computes for the error metrics. I kept the backend self-contained, so
    the in-process tests, the CLI and the cost table use the same code.
- **One tolerance flag for both Lanczos runs.** It is recorded twice, as
  `svd_tol` and `sigma_max_tol`, so a later split needs no format change.
  - Default 1e-12. The allowed range is 0 to 1e-6; 0 means machine
    precision. Looser values would make A' drift from the reference.
  - Giving the flag with numpy is rejected. No Lanczos runs there.
- **Checks.** `smallest_k_svd` builds U as A V / s, so U is only as
  orthonormal as V is accurate. The a-posteriori residual
  ||A^T u_i - sigma_i v_i|| / sigma_max and the orthonormality defect
  catch bad triplets. The 1e-6 limit is far above a converged result
  (measured at most 2.5e-12) and far below garbage.
  - The singular test uses the `numpy.linalg.matrix_rank` rule,
    sigma_0 <= N eps sigma_max.
  - An exactly singular A makes `splu` fail. That is mapped to
    `ValueError`.
  - Any ARPACK error becomes `RuntimeError` with N, tol and maxiter in
    the message.
- **`-hhl_deflate_svd sqls` with K = 0 is allowed.** It is a no-op. A sweep
  can then hold the backend fixed while it varies K. The CSV cells say ''
  (no pre-step ran). The pickle records the flag.
- **The qpy file names do not depend on the backend.** The two A' agree
  to 1e-14 relative. The verifier may prefer a key; it is easy to add.
- **The numpy path is not rewritten.** It keeps its arithmetic and
  ordering, so its outputs stay bit-identical.

## How the singular values map to the encoded matrix (the numerics)

This follows the item-19 derivation (`hhl_spectrum.py`) with sqls inputs.

1. A' keeps sigma_k .. sigma_{N-1} of A. It parks k values at the shift.
   Under sqls the shift is sigma_max_est, a hair at or below sigma_max(A).
   So sigma_min(A') = sigma_k and sigma_max(A') = sigma_max(A).
2. The scale s divides every singular value by s. `-hhl_spectrum
   deflation` uses s = sigma_max_est.
3. Padding adds unit singular values. They lie inside [sigma_k / s, 1],
   so they change no bound.
4. Hermitian doubling turns singular values into the |eigenvalues| of H.

So H has lambda_min = sigma_k / s and lambda_max = sigma_max(A) / s. The
latter is 1 plus the estimate's relative error, measured at most 6.2e-16.
Its kappa is kappa_eff (supplied).

The fork's clock width nl = max(nb + 1, ceil(log2(kappa + 1))) + 1 and
its QPE delta integer floor(lambda_min (2^(nl-1) - 1) / lambda_max) were
compared for both backends. They are identical under both the internal
and the supplied spectrum, on all 36 cases.

Margins: in all 36 cases nl is set by the nb + 1 floor, not by kappa_eff.
The delta argument is at least 3.9e-3 from an integer. Backend
differences of about 1e-14 cannot flip either.

## Commands and wall times

All with `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`,
from the fvm root unless noted. Scratch lived in `/tmp/item18-19-builder/`
and was removed at the end (see below). Solver output went to that
scratch only.

| What | When (UTC) | Wall | Result |
|---|---|---|---|
| one-off: sqls `smallest_k_svd` vs numpy on the 9 archived systems, k = 1 to 4, tol 0 and 1e-12 | 23:50Z | under 5 s (not timed) | about 1e-14 everywhere; smallest gap 0.075 at that point |
| one-off: new `deflate(..., svd='sqls')` vs numpy, same 36 cases | 23:54Z | under 5 s (not timed) | all metrics 1e-13 or better |
| CLI smoke, nelem 2, `-iters 1 -hhl_deflate_k 1 -hhl_deflate_svd sqls -hhl_spectrum deflation -hhl_spectral_diag off` | 23:56:54Z | 8.3 s | ran; n_clock 6; all nine columns filled |
| one-off: global spectral call log, one in-process nelem-2 solve per config | 23:57Z | 11.9 s | sqls + deflation + diag off: 0 calls; numpy: 1 svd |
| reference tree (pre-item-18 solver modules in `/tmp/item18-19-builder/ref`) vs new, nelem 2, `-iters 2`, k = 1 / k = 1 + spectrum deflation / k = 0, six CLI runs in parallel | 23:58:56Z | 35 s total, each run 10.9 s to 18.9 s | iteration-0 deterministic columns identical; see AC18-1 notes |
| reference repeat, k = 1 | 00:00:27Z | 13.5 s | sets the run-to-run noise floor |
| one-off: old vs new numpy `deflate`, bitwise, 36 cases | 00:01Z | under 5 s (not timed) | 0 mismatches over all arrays, properties and columns |
| `python -m unittest tests.test_deflation_svd` | 00:03:57Z | 59.7 s (63.2 s process) | 31 tests OK |
| four CLI runs, nelem 2, `-iters 1 -hhl_deflate_k 1`, numpy / sqls, with and without the supplied spectrum, in parallel | 00:05:40Z | 11 s total | see AC18-5 CLI |
| cost pilot `cost.py 5,11,21 5`, then `cost.py 42,85,170,341 5` | 00:06:30Z, 00:06:43Z | 1.1 s, 5.8 s | pilot numbers |
| sigma_max tolerance probe and Lanczos ncv probe (nelem 85, 341) | 00:07Z | under 10 s each (not timed) | see the cost notes |
| cost table `cost.py 5,11,21,42,85,170,341,682 7` (classical only, many sub-second timings) | 00:07:46Z | 62.4 s total; the largest single SVD about 1.1 s | the table below |
| band-truncated Jacobians, nelem 170 and 682, 7 repeats | 00:09:20Z | 23 s | the context table below |
| full suite `python -W default::DeprecationWarning -m unittest discover -s tests` | 00:11:44Z to 00:15:34Z | 227.9 s (229.7 s process) | 211 tests: 206 pass, 4 fail, 1 skipped |

Not run (over the 60 s limit, for the operator):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

Example sqls-backend run (nelem 2, about 8 s):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
.venv/bin/python nozzle_1d_solver.py -nelem 2 -linsolver HHL -shots 0 \
  -iters 1 -hhl_deflate_k 1 -hhl_deflate_svd sqls -hhl_spectrum deflation \
  -hhl_spectral_diag off -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 \
  -noshow -outdir /tmp/x
```

## Results by criterion (for the verifier to judge)

### AC18-1: the numpy default is unchanged

- In-process, the old module (a copy of `deflation.py` taken before my
  edit) was compared with the new `deflate(A, b, k)`. On the 9 archived
  systems for k = 1 to 4 they are bitwise equal. That covers sigma, u, v,
  ub, a_orig, b, a_shifted, shift, kappa, kappa_eff, x_share_classical,
  correction(), recombine() and the six item-6 columns, `t_svd_s` aside:
  0 mismatches in 36 cases.
- The existing `tests/test_deflation.py` and `tests/test_hhl_spectrum.py`
  are unchanged and pass in the full suite.
- CLI, reference tree versus new code, nelem 2:
  - Same file set.
  - Iteration 0: `kappa`, `kappa_eff`, `n_clock`, `x_share_classical`,
    the five spectrum values, `circ_qubits`, `nqubits`, `circ_gates_orig`,
    `circ_depth_orig` and `fb_cx_count` are bit-identical. `dq_hhl`
    differs by 2.1e-16 max-abs (k = 1).
  - Iteration 1 differs by about 1e-8 relative. So does reference versus
    reference (1.2e-8 relative). The finite-difference Jacobian
    (perturbation about 1.5e-8) amplifies round-off in the step-0 state.
  - `circ_gates_transpile` and `circ_depth_transpile` also differ between
    two runs of the same code, by 0.2 % to 0.6 %. This is pre-existing,
    seen at k = 0 too.
  - So between processes, "identical" holds for the deterministic
    quantities, not for every HHL output.

### AC18-2: the sqls call, sigma_max, tolerances

- The test spies on the installed `sqls.core.truncated_svd.smallest_k_svd`.
  It is called once, with k + 1, a sparse matrix and the explicit `tol`.
  No sqls code is copied.
- sigma_max method: `eigsh_ata`, ARPACK Lanczos on A^T A (k = 1, which
  `LA`, seed 0 start vector). Tolerance: relative on the eigenvalue,
  default 1e-12. It is recorded in `sigma_max_tol`; the smallest_k_svd
  tolerance is recorded in `svd_tol`.

### AC18-3: Deflation with a partial spectrum

- `sigma`, `u` and `v` hold k + 1 triplets. `sigma_max` holds the
  estimate. `shift`, `kappa` (sigma_max_est / sigma_0) and `kappa_eff`
  (sigma_max_est / sigma_k) use it.
- `a_shifted`, `correction()` and `recombine()` use only the first k
  triplets.
- `x_share_classical` = sum_{i<k} (u_i.b / sigma_i)^2 / ||A^-1 b||^2.
  The denominator comes from one classical sparse LU solve, labeled
  `x_share_method = splu_solve` and timed as `t_xshare_s`.
- No full SVD runs in this backend.

### AC18-4: metadata

New HHL qc_metadata columns, after `t_spectrum_s`:

| column | numpy | sqls | k = 0 |
|---|---|---|---|
| `hhl_deflate_svd` | `numpy` | `sqls` | '' |
| `svd_tol` | '' | 1e-12 (the flag) | '' |
| `sigma_max_method` | `numpy_svd` | `eigsh_ata` | '' |
| `sigma_max_tol` | '' | 1e-12 | '' |
| `t_smallest_k_s` | full SVD time | smallest_k_svd time | 0.0 |
| `t_sigma_max_s` | 0.0 | Lanczos time | 0.0 |
| `x_share_method` | `svd` | `splu_solve` | '' |
| `t_xshare_s` | 0.0 | LU solve time | 0.0 |
| `svd_residual` | '' | max_i ||A^T u_i - sigma_i v_i|| / sigma_max | '' |

- `t_svd_s` keeps its meaning: the whole pre-step. Under sqls that is
  the CSR conversion, smallest-k, sigma_max, the checks and the update.
- Pickle: `hhl_deflate_svd` (string), and `hhl_deflate_svd_tol` (float
  for sqls, None for numpy). `quantum_circuit` carries the nine values of
  the last step.
- Every existing column and key keeps its name, order and value.
  `tests/contract.py` and `TESTING.md` are updated.

### AC18-5: equivalence

36 cases: 9 archived systems (nelem 5 iterations 0 to 6 and 14, nelem 2
iteration 0), k = 1 to 4, tol 1e-12. One run of the backend (its start
vector is random, see the open doubts):

| quantity | worst over the 36 cases | asked |
|---|---|---|
| smallest k + 1 singular values, relative | 5.0e-15 | 1e-8 |
| principal angle, left k-subspace | 2.4e-14 rad | 1e-6 rad |
| principal angle, right k-subspace | 8.6e-15 rad | 1e-6 rad |
| sigma_max_est, relative | 6.1e-16 (signed range -2.7e-16 to +6.1e-16) | tol 1e-12 |
| A', relative Frobenius | 9.3e-15 | 1e-8 |
| kappa_eff, relative | 2.4e-15 | "identical" |
| n_clock and QPE delta integer | identical, internal and supplied | identical |
| x_share_classical, absolute | 1.4e-13 | (not set) |
| recombine(A'^-1 b) vs A^-1 b, relative | 2.5e-13 | 1e-8 |
| svd_residual | 2.2e-14 | (check limit 1e-6) |

Near-degeneracy:

- The smallest relative gap (sigma_k - sigma_{k-1}) / sigma_k over the
  36 cuts is 0.040. So every k-subspace is well defined, and the test
  asserts the gap is above 1e-3.
- A synthetic 9 x 9 case with sigma_1 = sigma_2 exactly and k = 2 cuts
  through a degenerate pair. There the subspace is not unique and A'
  may differ between backends. kappa_eff, the singular values of A'
  (1e-10) and the recombined solution (1e-10) still agree.

CLI, nelem 2, one Newton step, `-hhl_deflate_k 1`:

| spectrum | circ_qubits | n_clock | dq_hhl max-abs | dq_hhl relative |
|---|---|---|---|---|
| default (internal) | 11 / 11 | 6 / 6 | 3.8e-15 | 7.8e-15 |
| `-hhl_spectrum deflation -hhl_spectral_diag off` | 11 / 11 | 6 / 6 | 1.0e-14 | 2.7e-14 |

For contrast, numpy internal versus numpy supplied spectrum is 1.9e-12
max-abs, the item-19 figure.

### AC18-6: validation

- At parse time (exit 2, nothing written):
  - `-hhl_deflate_svd sqls` with K >= 3*nelem - 1 is rejected. The
    message is "needs K + 1 < N = 6, i.e. K <= 4" at nelem 2.
  - `-hhl_deflate_svd_tol` with numpy is rejected.
  - A tolerance outside [0, 1e-6] is rejected.
  - Either flag with LU or SQLS is rejected, as is an unknown backend.
- In the module:
  - Lanczos non-convergence raises `RuntimeError` with ARPACK's "No
    convergence" message. It was provoked for both runs on a 400 x 400
    spectrum clustered within 0.1 %, with one restart.
  - An exactly singular A raises `ValueError` ("A is singular"). A
    numerically singular one (sigma 1e-17) raises `ValueError`
    ("numerically singular").
  - A wrong sigma_max raises `RuntimeError` (patched `eigsh`, "outside
    the norm bounds").
  - Perturbed triplets raise `RuntimeError` (patched `smallest_k_svd`,
    "inaccurate").

### AC18-7: cost (classical only, no HHL)

Setup:

- Jacobians are assembled in-process with the fvm space solver, exactly
  as the CLI builds them (CFL 1e10, BDF1, local dt, nondim). This is the
  first Newton step, iteration 0. No solver files were written.
- `t_svd_s` is the whole pre-step:
  - numpy: the full SVD plus the rank-k update;
  - sqls: the CSR conversion, smallest-k, sigma_max, the checks and the
    update.
- The x_share solve is listed apart.
- Median of 7 repeats, wall seconds, tol 1e-12, default multi-threaded
  numpy and scipy, laptop as above.

| nelem | N | k | nnz | kappa | numpy t_svd_s | sqls t_svd_s | sqls smallest-k | sqls sigma_max | sqls x_share solve | faster |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 15 | 2 | 149 | 96 | 0.036 ms | 0.633 ms | 0.283 ms | 0.290 ms | 0.032 ms | numpy 17.6x |
| 5 | 15 | 4 | 149 | 96 | 0.033 ms | 0.623 ms | 0.277 ms | 0.281 ms | 0.031 ms | numpy 19.1x |
| 11 | 33 | 2 | 383 | 219 | 0.102 ms | 0.800 ms | 0.376 ms | 0.348 ms | 0.041 ms | numpy 7.9x |
| 11 | 33 | 4 | 383 | 219 | 0.099 ms | 0.781 ms | 0.378 ms | 0.338 ms | 0.050 ms | numpy 7.9x |
| 21 | 63 | 2 | 773 | 422 | 0.337 ms | 1.198 ms | 0.467 ms | 0.645 ms | 0.060 ms | numpy 3.6x |
| 21 | 63 | 4 | 773 | 422 | 0.333 ms | 1.195 ms | 0.467 ms | 0.649 ms | 0.060 ms | numpy 3.6x |
| 42 | 126 | 2 | 3634 | 851 | 1.288 ms | 2.522 ms | 0.833 ms | 1.539 ms | 0.137 ms | numpy 2.0x |
| 42 | 126 | 4 | 3634 | 851 | 1.281 ms | 2.511 ms | 0.829 ms | 1.532 ms | 0.137 ms | numpy 2.0x |
| 85 | 255 | 2 | 3269 | 1731 | 5.914 ms | 4.314 ms | 0.919 ms | 3.098 ms | 0.123 ms | sqls 1.4x |
| 85 | 255 | 4 | 3269 | 1731 | 5.880 ms | 4.302 ms | 0.920 ms | 3.095 ms | 0.122 ms | sqls 1.4x |
| 170 | 510 | 2 | 44369 | 3469 | 26.179 ms | 35.915 ms | 6.857 ms | 27.818 ms | 1.730 ms | numpy 1.4x |
| 170 | 510 | 4 | 44369 | 3469 | 26.254 ms | 35.881 ms | 6.748 ms | 27.853 ms | 1.711 ms | numpy 1.4x |
| 341 | 1023 | 2 | 13253 | 6967 | 0.150 s | 37.338 ms | 2.644 ms | 31.411 ms | 0.412 ms | sqls 4.0x |
| 341 | 1023 | 4 | 13253 | 6967 | 0.150 s | 37.492 ms | 2.736 ms | 31.448 ms | 0.413 ms | sqls 4.0x |
| 682 | 2046 | 2 | 629626 | 13940 | 1.133 s | 2.667 s | 0.162 s | 2.486 s | 28.155 ms | numpy 2.4x |
| 682 | 2046 | 4 | 629626 | 13940 | 1.127 s | 2.666 s | 0.163 s | 2.483 s | 27.556 ms | numpy 2.4x |

Accuracy of sqls against numpy on the same matrices:

| nelem | N | k | sigma rel | A' rel | sigma_max rel | x_share abs | svd_residual | assembly |
|---|---|---|---|---|---|---|---|---|
| 5 | 15 | 2 | 1.3e-15 | 6.8e-15 | 2.7e-16 | 5.8e-14 | 7.9e-15 | 0.00 s |
| 5 | 15 | 4 | 1.4e-15 | 9.5e-15 | 2.7e-16 | 1.1e-13 | 1.8e-14 | 0.00 s |
| 11 | 33 | 2 | 1.7e-15 | 1.4e-14 | 1.2e-16 | 7.3e-14 | 2.6e-14 | 0.00 s |
| 11 | 33 | 4 | 2.1e-15 | 1.9e-14 | 1.2e-16 | 4.1e-14 | 4.9e-14 | 0.00 s |
| 21 | 63 | 2 | 9.6e-15 | 2.1e-14 | 6.4e-16 | 6.9e-14 | 5.9e-14 | 0.01 s |
| 21 | 63 | 4 | 1.0e-14 | 1.9e-14 | 6.4e-16 | 8.7e-14 | 5.7e-14 | 0.01 s |
| 42 | 126 | 2 | 2.1e-14 | 3.1e-14 | 7.6e-16 | 6.7e-16 | 1.1e-13 | 0.02 s |
| 42 | 126 | 4 | 2.1e-14 | 3.9e-14 | 7.6e-16 | 7.8e-16 | 2.7e-13 | 0.02 s |
| 85 | 255 | 2 | 3.7e-14 | 4.4e-14 | 5.0e-16 | 1.6e-13 | 2.5e-13 | 0.05 s |
| 85 | 255 | 4 | 3.4e-14 | 4.6e-14 | 5.0e-16 | 1.3e-13 | 2.5e-12 | 0.05 s |
| 170 | 510 | 2 | 4.2e-14 | 6.8e-14 | 3.8e-16 | 3.7e-15 | 4.3e-13 | 0.18 s |
| 170 | 510 | 4 | 4.4e-14 | 8.1e-14 | 3.8e-16 | 3.1e-13 | 1.2e-12 | 0.18 s |
| 341 | 1023 | 2 | 1.2e-13 | 8.8e-14 | 1.5e-15 | 5.8e-13 | 8.4e-13 | 0.68 s |
| 341 | 1023 | 4 | 1.1e-13 | 1.1e-13 | 1.5e-15 | 5.8e-13 | 9.3e-13 | 0.68 s |
| 682 | 2046 | 2 | 3.2e-13 | 1.3e-13 | 3.7e-15 | 8.9e-14 | 1.6e-12 | 2.57 s |
| 682 | 2046 | 4 | 3.1e-13 | 1.6e-13 | 3.7e-15 | 5.9e-13 | 1.9e-12 | 2.57 s |

Where each wins, plainly:

- **numpy wins at small N.** Below N = 255 the dense SVD costs well under
  2 ms. The sqls path pays Python and ARPACK overhead (about 0.3 ms per
  Lanczos run) plus the CSR conversion.
- **sqls wins when A is truly sparse and large.** That is N = 255 (1.4x)
  and N = 1023 (4.0x). These are the sizes where the Jacobian is
  block-banded: every nonzero lies within 2 elements of the diagonal.
- **The fvm Jacobian is not always sparse.** At nelem 42, 170 and 682 the
  finite-difference Jacobian carries tiny off-band entries: up to 5.5e-10
  (nelem 170) and 2.7e-10 (nelem 682) of the largest entry. At nelem 682
  it is 15 % dense (629,626 nonzeros versus 28,498 in the band). The
  sparse LU and the matvecs then lose their advantage, and numpy wins
  (1.4x at N = 510, 2.4x at N = 2046). The entries look like round-off in
  the finite-difference residual. That is a property of the fvm assembly,
  out of scope here.
- **For context only**, the same matrices with every entry outside the
  5-element band set to 0 (a change of 3.7e-10 and 1.9e-10 relative,
  Frobenius). These are not what fvm passes:

  | nelem | N | k | numpy | sqls | sqls smallest-k | sqls sigma_max | sqls x_share | faster |
  |---|---|---|---|---|---|---|---|---|
  | 170 | 510 | 2 | 26.19 ms | 11.38 ms | 1.58 ms | 8.88 ms | 0.21 ms | sqls 2.3x |
  | 682 | 2046 | 2 | 1.133 s | 0.170 s | 4.72 ms | 0.153 s | 0.79 ms | sqls 6.7x |

  k = 4 gives the same numbers to 1 %.
- **sigma_max is the expensive part of sqls, not smallest-k.** The top
  singular values are tightly clustered (relative gap 9.4e-5 at nelem 85,
  4.1e-7 at nelem 341). The Lanczos residual test therefore converges
  slowly, although the value is right to 1e-15 early.
  - Loosening the tolerance from 1e-12 to 1e-8 saves only about 25 %
    (31 ms to 24 ms at nelem 341).
  - A larger Lanczos subspace (ncv 40 instead of scipy's 20) saves about
    1.5x (31 ms to 21 ms).
  - I kept scipy's defaults and record this as an option.
- **k barely matters.** k = 2 and k = 4 cost the same to 1 % in every row.
- **The x_share solve is cheap.** It is at most 3 % of the sqls pre-step.

### AC18-8: no dense full-spectrum routine on the solve path

The log (`tests/test_deflation_svd.py: GlobalSpectralCallLog`) patches
every module attribute in `sys.modules` that is bound to one of these:

- `numpy.linalg` svd, cond, eig, eigvals, eigh, eigvalsh;
- `scipy.linalg` svd, svdvals, eig, eigvals, eigh, eigvalsh, schur.

That is 43 bindings. So `from ... import` copies, numpy's own nested
calls and calls from sqls, scipy and qiskit are all seen. One in-process
`hhl_solve` on the archived nelem-2 system, `-hhl_deflate_k 1`, `-v 0`:

| configuration | calls |
|---|---|
| `-hhl_deflate_svd sqls -hhl_spectrum deflation -hhl_spectral_diag off` | none |
| the same with `-hhl_spectral_diag on` | only calls whose fvm origin is `math_tools.get_matrix_properties` (the labeled diagnostic columns, switched off by `-hhl_spectral_diag off`) |
| `-hhl_deflate_svd numpy -hhl_spectrum deflation -hhl_spectral_diag off` | exactly one `numpy.linalg.svd` of the 6 x 6 A, from `deflation.deflate` |

Remaining dense work that the log cannot see, listed for honesty:

- ARPACK's internal LAPACK work on its small projected matrix (at most
  ncv = 20 square, not A). This happens inside `eigsh`, in both Lanczos
  runs.
- `scipy.linalg.expm` of the encoded matrix in the fork. That is the
  Hamiltonian simulation, not a spectral decomposition (item-19 row F4).
- Compiled qiskit and Aer code (Rust and C++), which does not call numpy.
- At `-v >= 1` the condition-number prints of `math_tools` (item-19 rows
  V7, V8) still run. They are print-only.

### AC18-9: hygiene

- PEP 8, lines <= 88, imports at the module top. The exception is the
  lazy sqls import, explained in the code. There is no trailing
  whitespace, and the new functions have type hints.
- The tests are unittest-based; the longest new test is under 10 s.
- README and TESTING explain both backends and that both are classical.
  They carry the attribution "sqls smallest_k_svd (ORNL sqls package,
  refs 13 to 15 of the AIAA abstract; source attribution to be
  confirmed)".
- Nothing is committed. The earlier uncommitted fvm changes are intact:
  - `pyproject.toml`, `uv.lock`, both docs files,
    `tests/test_output_contract.py`, `tests/test_sqls.py`, `math_tools.py`
    and `tests/test_hhl_spectrum.py` are untouched by me.
  - In `README.md`, `TESTING.md`, `time_solvers.py`, `quantum_tools.py`,
    `nozzle_1d_solver.py`, `hhl_spectrum.py` and `tests/contract.py` my
    edits sit on top. I made them with exact string replacement only.

### Full suite

- 211 tests: 206 pass, 4 fail, 1 skipped. 227.9 s (229.7 s process),
  from 2026-10-19T00:11:44Z to 00:15:34Z.
- No DeprecationWarning. The longest single test is 23.4 s
  (`TestSuppliedExactValuesSameCircuit.test_nelem5_iter0_k1`).
- The 4 failures are `test_output_contract.*.test_code_versions` (HHL,
  HHL shots, LU, SQLS). Each reports `'git' != 'direct_url'` for
  `linear_solvers`. This is the editable fork override, exactly as in
  build-19.md. They should pass once the fork is committed and pushed,
  the rev is bumped and the lock is refreshed.

## Harvester changes needed (not made)

File: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.

1. Add a `_deflation_svd(row)` reader next to `_deflation` (near line
   383). It returns None when `hhl_deflate_svd` is absent, and the nine
   values otherwise:
   - strings stripped, '' as None;
   - floats via the existing `_float_or_none`, which already maps '' to
     None.
2. Attach it per step where `"deflation": _deflation(row)` is built
   (lines 701 and 779), e.g. as `"deflation_svd"`.
3. `_deflation_summary` (lines 420 to 441): add the backend, the
   `sigma_max_method`, the tolerances, the medians of `t_smallest_k_s`,
   `t_sigma_max_s`, `t_xshare_s` and `t_svd_s`, and the maximum
   `svd_residual`.
4. `_spectrum_summary` (lines 469 to 499): add `t_xshare_total_s` next to
   `t_svd_total_s`. Note that it is not part of `t_svd_s`.
5. Run parameters (line 1079): add `hhl_deflate_svd` and
   `hhl_deflate_svd_tol` to the key loop next to `hhl_spectrum` and
   `hhl_spectral_diag` (None for SQLS).

## Scratch removal

`/tmp/item18-19-builder/` held the probes, the reference tree, the smoke
and comparison outputs and the cost scripts. It was removed after this
report was written. The test suite's own temp root removes itself at
exit.

## Open doubts

- **The sqls backend is not bit-reproducible.** `smallest_k_svd` passes no
  start vector to `eigsh`. scipy 1.18 then draws one from OS entropy. Two
  runs agree to about 1e-14, not bit for bit. A small sqls patch (pass
  `v0` or `rng` through) would fix it. That is a change to sqls, so I did
  not make it. The sigma_max start vector is seeded.
- **"Identical outputs" for numpy.** HHL outputs of the same code are not
  bit-identical between processes: transpiled gate counts vary by 0.2 %
  to 0.6 %, and step 1 differs by about 1e-8 relative through the
  finite-difference Jacobian. I showed bitwise identity for the
  deflation record and the deterministic columns. The verifier should
  judge whether that meets AC18-1.
- **"kappa_eff identical".** The backends agree to 2.4e-15 relative, not
  bitwise. n_clock and the QPE delta integer are identical, with margin.
- **x_share by a separate sparse LU solve.** It duplicates `dq_lu`, which
  `hhl_solve` already computes. Reusing `dq_lu` would save the solve
  inside the runs (at most 3 % of the pre-step).
- **The check thresholds are judgment calls.** They are 1e-6 for the
  residual and orthonormality, N eps for numerical singularity, and
  1e-10 + 10 tol slack on the norm bounds.
- **Finite-difference fill in the fvm Jacobian** at some nelem (42, 170,
  682) decides the sparse-versus-dense cost. Dropping entries below a
  relative threshold in `compute_Jacobian_matrix_FD`, or assembling the
  band only, would change A. That is a separate decision.
- **`pyproject.toml` lists the flat modules in `py-modules`.**
  `deflation` (since item 6) and `hhl_spectrum` (item 19) are missing
  there. A non-editable install of fvm would miss them. I did not touch
  `pyproject.toml`.
- **`-hhl_deflate_svd sqls` with K = 0 is accepted as a no-op**, to keep
  sweeps simple. The verifier may prefer a rejection like item 19's.
- **Attribution.** The README wording is as specified. Whether
  `smallest_k_svd` follows KU refs 13 to 14, ORNL ref 15 or standard
  shift-invert Lanczos is still to be confirmed against the papers.

## Fix-up (2026-10-19T01:08:20Z)

Two should-fix findings from the verifier. I fixed both. Nothing is
committed. The fork is unchanged by this fix-up, so
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`
still matches `git diff` of the fork byte for byte (checked with `cmp`).
The pinned git sources in `pyproject.toml` and `uv.lock` are untouched
(sqls rev 187a7a5, fork rev 9d1d7bb).

### Finding 1: two full SVDs still ran at the default `-v 1`

What was wrong. `convert_to_pow2` and `convert_system_to_herm` print
`np.linalg.det` and `np.linalg.cond` at verbosity 1 and above. Each cond
is a full SVD. One is of the padded matrix. One is of the 2 N_pow2
Hermitian matrix, the same matrix item 19 removed from the library's
`condition_bounds()`. The CLI default is `-v 1`. So a default-verbosity
`-hhl_spectrum deflation -hhl_spectral_diag off` run still paid for them.
The AC18-8 test ran at verbosity 0 only, so it missed this.

What I did. I took the second suggested option: `-hhl_spectral_diag off`
now also skips these two prints.

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/math_tools.py`:
  `convert_to_pow2` and `convert_system_to_herm` take a new keyword
  `spectral_diag=True`. When it is False, the det / cond line is not
  printed and not computed. The shape lines still print.
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py`:
  `QuantumHHL` passes `spectral_diag=self.spectral_diag` to both.
- The default (`on`) prints exactly what it printed before. Other
  callers (the SQLS path, `time_solvers.py`, the tests) keep the default.
- I chose this over moving the prints to `-v 2`. Moving them would change
  the default `-v 1` output of every run, including the internal path.
  This way only the opted-in `off` configuration changes.

New tests in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/tests/test_deflation_svd.py`,
class `TestNoFullSpectrumOnSolvePath` (now five solves in setUpClass):

- `test_default_verbosity_diag_off_has_none`: sqls backend, supplied
  spectrum, diagnostics off, verbosity 1. The global call log is empty.
- `test_default_verbosity_diag_on_only_labeled_prints`: the same at
  verbosity 1 with diagnostics on. The calls come only from
  `get_matrix_properties`, `convert_to_pow2` and `convert_system_to_herm`.
  This is the negative control: it shows the verbosity-1 prints do run
  when the flag is on, so the empty log above is meaningful.

Docs updated: the flag help text in `nozzle_1d_solver.py`, the comment on
`HHL_SPECTRAL_DIAG_CHOICES` in `math_tools.py`, the flag table and the
"Diagnostics" and AC18-8 paragraphs of `README.md`, and the
no-full-spectrum bullet of `TESTING.md`.

Remaining dense spectral calls, `-hhl_deflate_svd sqls -hhl_spectrum
deflation -hhl_spectral_diag off`: none at `-v 0` or `-v 1` (tested). I
did not test `-v 2`; it adds matrix prints only.

### Finding 2: spurious failure when sigma_K sits in a degenerate top cluster

What was wrong. `_check_triplets` accepts sigma_K up to sigma_max_est (1 +
1e-6). `encoded_bounds` needs sigma_K <= sigma_max exactly. With a
degenerate top cluster, the Lanczos sigma_max can land a few ulp below
sigma_K. Then `encoded_spectrum` raised a ValueError that did not name the
cause. I reproduced it: 10 x 10 random systems with singular values
0.5, 1, 2, 3, 4, 5, 6, 7, 7, 7 and K = N - 2 = 8. Seed 41 of 60 failed
(sigma_K = 7.0000000000000036, estimate 7.000000000000003).

What I did. I fixed it at the source, in the sqls pre-step, not in
`encoded_spectrum`.

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py`,
  sqls branch of `deflate`, right after `_check_triplets`:
  `sigma_max = max(sigma_max, float(s[-1]))`.
- Why this is right. The Lanczos Ritz value is a lower bound of
  sigma_max(A). sigma_K is a singular value of A, so it is a lower bound
  too. Taking the larger is a better estimate. It keeps the whole
  Deflation consistent: the shift, kappa, kappa_eff and the supplied
  kappa all use the same value. kappa_eff is then exactly 1 in this case,
  which is the right answer.
- Why not clamp in `encoded_spectrum`. The supplied kappa must equal the
  `kappa_eff` column exactly. A clamp there would leave kappa_eff
  slightly below 1 and break that identity.
- Effect on the archived Jacobians: none. There sigma_K is far below
  sigma_max for K <= 4, so `max` returns the Lanczos estimate unchanged.
  The equivalence tests are unchanged and pass.
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/hhl_spectrum.py`:
  `encoded_spectrum` now re-raises any bound violation with a message that
  names k, sigma_k and sigma_max. After the fix it can only be reached by
  a Deflation built by hand.

New test `TestSqlsBackendEquivalence.test_degenerate_top_cut` (0.01 s):
the 10 x 10 triple-top-cluster system, K = 8, 20 seeds unpatched, plus one
run where `sigma_max_estimate` is patched to return a value 1e-10
relative low (smallest_k_svd draws its own random start vector, so the
patch makes the case deterministic). It checks sigma_K <= sigma_max,
kappa_eff = 1 (exactly 1 in the patched run), a valid supplied spectrum
and the exact recombined solution. Negative control: with the `max` line
removed, the test fails (`6.999999999300002 != 7.0`).

Docs updated: the sigma_max bullet in `README.md`, the sqls docstring in
`deflation.py`, and the equivalence bullet of `TESTING.md`.

### Commands and wall times (fix-up)

All from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`.

| Command | Result | Wall |
|---|---|---|
| `.venv/bin/python /tmp/item18-19-fixup/scan.py` (60 seeds, before fix) | 1 failure (seed 41) | 0.6 s |
| same, after fix | 0 failures | 0.6 s |
| `.venv/bin/python -m unittest tests.test_deflation_svd.TestNoFullSpectrumOnSolvePath` | 5 tests OK | 20.0 s |
| `.venv/bin/python -m unittest tests.test_deflation_svd.TestSqlsBackendEquivalence.test_degenerate_top_cut` | OK; fails without the fix | 1.0 s |
| `.venv/bin/python -m unittest tests.test_deflation_svd tests.test_hhl_spectrum` | 57 tests OK | 127.8 s |
| `.venv/bin/python -m unittest discover -s tests` | 214 tests, 4 failures, 1 skipped | 237 s |

The 4 failures in the full suite are the known
`test_output_contract.*.test_code_versions` cases (HHL, HHL shots, LU,
SQLS). They assert `commit_source == 'direct_url'` for `linear_solvers`;
the editable fork override gives `git`. This is the expected effect of the
dev override, as reported for items 18 and 19. They pass once the operator
pushes the fork, bumps the rev and relocks. Zero DeprecationWarnings in
the full-suite log. The slowest single test or class setup took 23.4 s.

Not run (over the 60 s limit; for the operator):
`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` (nelem-5 HHL gate, about 90 s).

Harvester: no new columns in this fix-up, so no new harvester changes.

Scratch `/tmp/item18-19-fixup/` removed.
