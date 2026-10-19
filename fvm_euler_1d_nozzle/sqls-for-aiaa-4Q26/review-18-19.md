# Code review: items 19 and 18 (supplied HHL spectrum; sqls deflation backend)

Reviewer report. Review ran 2026-10-19T00:25Z to 2026-10-19T00:55Z (UTC).
No code was edited. Nothing is committed. No scratch was left behind (the
test suite's own temp root under `$TMPDIR` removes itself at exit; I did
not create `/tmp/item18-19-reviewer/`).

## What was reviewed

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90`, uncommitted. `git diff |
  shasum -a 256` = `ba85da22...0931` (14 files, +1188 / -281) plus three
  untracked files: `hhl_spectrum.py`, `tests/test_deflation_svd.py`,
  `tests/test_hhl_spectrum.py`. The pre-existing git-source switch
  (`pyproject.toml`, `uv.lock`, the two docs, `tests/test_output_contract.py`,
  `tests/test_sqls.py`, install text in README) was ignored as out of scope.
  The pinned sources are intact (sqls `187a7a5...`, fork `9d1d7bb...`).
- HHL fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, HEAD
  `9d1d7bb`, uncommitted (6 files, +364 / -23). `git diff | shasum -a 256`
  = `67e9f74a...5e76`, equal to the patch
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`.
- sqls: read only, `smallest_k_svd` and `_smallest_k_svd_cpu` in the
  installed package (sparse LU of A and A^H, `eigsh` on (A^H A)^-1, U = A V / s,
  ascending sort). Not edited.
- Builder and verifier reports (`build-19.md`, `build-18.md`, `verify-19.md`,
  `verify-18.md`) were read after the diffs, to avoid repeating what they
  already list. Where a point below is also in those reports it is marked.

## Verdict

The code is correct on the points I hunted for. I found no numerical error
in the spectrum transformation, no index or sign mistake, no silent
fallback to a full SVD, no timing contamination of a recorded column, no
metadata that misreports what ran, and no vacuous test. The defaults are
the old behaviour.

Two should-fix items and a handful of nits. Neither should-fix blocks the
operator from committing; both are small.

1. Should-fix. At the CLI default verbosity (`-v 1`) two full dense SVDs
   still run on every HHL step on the `-hhl_spectrum deflation
   -hhl_spectral_diag off` path, in print-only diagnostics. One is on the
   same 2 N_pow2 Hermitian matrix item 19 removed from the library.
2. Should-fix. Under the sqls backend, a degenerate top singular value with
   sigma_K inside the cluster makes `encoded_spectrum` fail with a
   misleading message. Triggered 1 time in 60 random cases at K = N - 2.

## Findings, ranked

### F1 (should-fix) Default verbosity defeats the item-19 saving

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/math_tools.py:147`
  (`np.linalg.cond(A_padded)` in `convert_to_pow2`) and `:187`
  (`np.linalg.cond(A_herm)` in `convert_system_to_herm`). Both sit under
  `if verbosity:`. The CLI default is `-v 1`
  (`nozzle_1d_solver.py:232-233`).
- What happens: with `-hhl_deflate_svd sqls -hhl_spectrum deflation
  -hhl_spectral_diag off` and the default `-v 1`, every HHL step still runs
  `np.linalg.cond` (a full SVD) on the padded N_pow2 matrix and on the
  doubled 2 N_pow2 Hermitian matrix. The second is exactly the matrix the
  library's `condition_bounds()` used to decompose. So a default-verbosity
  deflation run pays the cost item 19 set out to remove, just from a print.
- Verified: in-process nelem-2 solve under the test module's global call
  log. Verbosity 0: no watched call. Verbosity 1: `cond` and nested `svd`
  on (8, 8) from `convert_to_pow2`, and on (16, 16) from
  `convert_system_to_herm`. 9.1 s for both solves.
- Compliance: AC19-5 allows "an existing verbosity gate", and the README
  (item-19 section) and both build reports say `-v 0` is needed. So this is
  compliant and documented. It is still the wrong default for the use the
  flag was built for, and the AC18-8 "no dense routine" test runs at
  verbosity 0 only, so it does not cover what the CLI does by default.
- Suggested fix (one of): move the two `det` / `cond` prints to
  `verbosity == 2` (they are "detailed" output by nature); or make
  `-hhl_spectral_diag off` also skip them (pass a flag down from
  `solve_one_step`); or at minimum add `-v 0` to the README example runs for
  the supplied-spectrum configuration and say why.

### F2 (should-fix) Tolerance gap between `_check_triplets` and `encoded_bounds`

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py:343`
  accepts `s[-1] <= sigma_max * (1 + 1e-6)` (sigma_K may exceed the Lanczos
  sigma_max estimate by up to 1e-6 relative).
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/hhl_spectrum.py:75`
  then requires `sigma_K <= sigma_max` exactly.
- What happens: when sigma_K lies in a degenerate top cluster (sigma_K =
  sigma_max up to round-off), the sqls estimate can land a few ulp below
  sigma_K. `_check_triplets` passes; `encoded_spectrum` raises `ValueError:
  need 0 < sigma_min <= scale <= sigma_max; got 7.000000000000002,
  7.000000000000001, 7.000000000000001`. The message does not say the cut
  is degenerate, and the failure is spurious: clamping would give
  kappa_eff = 1, which is the right answer.
- Verified: 60 random 10 x 10 matrices with three equal top singular values,
  K = N - 2 = 8, sqls backend, `-hhl_spectrum deflation` values: 1 of 60
  raised (seed 24). 1.0 s. Not reachable on the archived Jacobians (the top
  cluster is far from sigma_K for K <= 4) and not with the numpy backend
  (there sigma_max is the exact SVD value, sigma_K <= sigma_max always).
- Suggested fix: in `encoded_spectrum`, clamp `sigma_k = min(sigma_k,
  sigma_max)` when `sigma_k <= sigma_max * (1 + SVD_CHECK_TOL)`, or make the
  (k+1)-th check in `_check_triplets` strict and raise there with a message
  that names the degenerate cut. Add the 10 x 10 degenerate-top case to
  `TestSqlsBackendFailures` or `test_degenerate_cut`.

### F3 (nit) `test_sigma_max` one-sided bound is platform-tight

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/tests/test_deflation_svd.py:159`:
  `assertLessEqual(ds.shift, ref * (1 + 4 * eps))`.
- Why: "a Ritz value is a lower bound" holds in exact arithmetic. In floating
  point the matvec, the sqrt and LAPACK's own SVD each add O(N eps) noise.
  Observed on this machine: signed relative error of sigma_max_est in
  [-8.5e-16, +3.7e-16] over the 36 cases (my run; the builder saw +6.1e-16).
  The upper limit 4 eps = 8.9e-16 is within a factor 2 of the observed
  maximum. On another BLAS (Frontier, the Linux nodes) the last-bit rounding
  can go the other way and this assertion would fail for no reason.
- Suggested fix: `ref * (1 + 1e-14)` (or 32 eps), keeping the two-sided
  `abs(ds.shift - ref) / ref <= TOL` check as the real test.

### F4 (nit) `py-modules` omits `deflation` and `hhl_spectrum`

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/pyproject.toml:75`.
- `nozzle_1d_solver.py` and `time_solvers.py` import both at module top, so
  any non-editable install of the fvm project would fail at import on every
  path, LU included. No documented install path does that (`uv sync` is
  editable; the Frontier recipe uses `uv export --no-emit-project`, so the
  project itself is never installed), and the CLI runs from the repo root.
  Also listed by the item-18 builder and verifier. One-line fix. Out of the
  "never revert pyproject sources" rule since it touches `py-modules` only.

### F5 (nit) `-hhl_deflate_svd sqls` with `-hhl_deflate_k 0` is a silent no-op

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py:193`
  (`if int(k) and ...`).
- The pickle then records `hhl_deflate_svd = 'sqls'` and
  `hhl_deflate_svd_tol = 1e-12` while no Lanczos ran and the nine CSV cells
  are empty. Harmless and documented (builder's design choice, for sweeps
  that hold the backend fixed). Item 19 rejects the analogous
  `-hhl_spectrum deflation` at K = 0; a parse-time rejection here would be
  consistent. Also listed by the item-18 verifier.

### F6 (nit) Attribution punctuation differs from the AC literal

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/README.md:435`,
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/TESTING.md:719`.
- Text reads "sqls smallest_k_svd, ORNL sqls package, refs 13 to 15 ..." while
  AC18-9 gives "sqls smallest_k_svd (ORNL sqls package, refs 13 to 15 ...)".
  Content is the same. Also listed by the item-18 verifier.

### F7 (nit, simplification) Three-way `None` branching in `Deflation`

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py:133,
  140, 148, 156`.
- `shift`, `kappa`, `kappa_eff` each branch on `self.sigma_max is None`, and
  `x_share_classical` on `self.x_norm2 is None`. Setting `sigma_max =
  float(s_asc[-1])` and `x_norm2 = float(np.sum(w))` on the numpy path keeps
  the numbers bit-identical (the same float operations in the same order)
  and collapses the four properties to one line each. The builder kept
  `None` to be safe on bit-identity; the identity holds either way.

### F8 (nit, simplification) Column keys spelled more than once

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py:386`
  (`svd_backend_columns`: two nine-key dict literals next to
  `SVD_BACKEND_COLUMNS`) and
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py:966`
  (five spectrum keys re-spelled for the pickle).
- `dataclasses.asdict(info)` zipped with `SVD_BACKEND_COLUMNS`, and
  `SPECTRUM_COLUMNS[:-1]`, would remove the duplication. The contract tests
  guard it today, so this is tidiness only.

### F9 (nit, efficiency) Third LU of A for the x_share solve

- Where: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/deflation.py:313`.
- `smallest_k_svd` has already factorized A and A^H; the backend factorizes
  A again for `||A^-1 b||^2`, and `hhl_solve` computes the same `dq_lu`
  one more time for the metrics. The cost is at most 3 % of the sqls
  pre-step in the builder's table and is timed apart (`t_xshare_s`), so the
  cost comparison is not distorted. Reusing `dq_lu` (pass `x_norm2` in)
  would remove one factorization; the builder chose self-containment.

### F10 (nit) Fork does not cross-check supplied kappa against supplied bounds

- Where: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/hhl.py:461`.
- `condition_bound = 1` with `eigenvalue_bounds = (1, 6000)` is accepted and
  sizes a too-small clock register. fvm derives both from the same numbers,
  so it is unreachable from the CLI. A `warnings.warn` when `kappa <
  lambda_max / lambda_min * (1 - 1e-8)` would catch a future caller. Also
  listed by the item-19 verifier.

### F11 (nit) `SpectralInfo.source` reads `internal` with no bounds at all

- Where: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/hhl.py:60-63`.
- When both `kappa_source` and `eigs_source` are `none`, `used` is empty and
  the property returns `internal`. Unreachable with `NumPyMatrix`. A fourth
  label (`none`) would be exact. Also listed by the item-19 verifier.

## Observations (not defects of items 18 or 19)

- The 4 failing `test_code_versions` cases (HHL, HHL shots, LU, SQLS) assert
  `commit_source == 'direct_url'` for `linear_solvers`; under the mandated
  editable fork override the entry is `git`, `dirty True`, commit `9d1d7bb`.
  So AC19-7 (i) "full default suite green" is not literally true right now.
  It should become true after the operator commits the fork, bumps the rev
  in `pyproject.toml` and runs `uv lock && uv sync`. The operator should
  re-run the suite then.
- `-loadcirc` of a generated qpy fails on qiskit 2.5.2 (`ExactReciprocalGate`
  reload `TypeError`), on the default path too. Pre-existing; the spectrum
  record's read-back is covered in-process and via the transpiled file only.
- The sqls backend is not bit-reproducible (`smallest_k_svd` passes no start
  vector to `eigsh`); runs agree to about 1e-14. Needs an sqls change, which
  is read-only here.
- The run-level `elapsed_time` in the metadata pickle
  (`nozzle_1d_solver.py:529`) is the whole process wall time and so includes
  the diagnostics of F1 at `-v 1`. No per-step recorded column does.

## What I checked and found correct

Spectrum transformation (AC19-4). H = double(pad(A_q / s)) has |eig| =
sigma(A_q) / s plus p ones; with s = sigma_max the ones lie in
[sigma_K / sigma_max, 1], so kappa(H) = sigma_max / sigma_K, lambda_min =
sigma_K / sigma_max, lambda_max = 1. Checked by my own script under the
sqls backend (the builder's test uses numpy only): on all 9 archived systems
times K = 1 to 4, built through `math_tools.scale_Ab` / `convert_to_pow2` /
`convert_system_to_herm`, versus `np.linalg.cond` / `eigvals` of H: kappa
relative error <= 9.1e-15, lambda_min relative error <= 4.4e-15,
lambda_max(H) - 1 <= 1.0e-14, and the clock width `nl` from the supplied
kappa equals the one from `cond(H)` in all 36 cases. 7.2 s.

Index conventions. `sigma_k = defl.sigma[defl.k]` is the (K+1)-th smallest,
0-based, for both backends (numpy: index K of N; sqls: the last of K + 1).
`correction()` uses `ub[:k]`, `sigma[:k]`, `v[:, :k]` and `self.shift`, not
`sigma[-1]`, so it is right when `sigma` holds only K + 1 values.
`kappa_eff = sigma_max / sigma[k]`, `kappa = sigma_max / sigma[0]`.

Sign and scaling. `u_i v_i^T` and `(u_i . b) v_i` are invariant to a common
sign flip; sqls builds U = A V / s, so the pair is consistent. The HHL
output is a normalized statevector rescaled by the leastsq alpha from A and b,
so the change of scale s (spectral radius to sigma_max) cannot change the
result beyond the fixed b offsets; fvm never reads `hhl.scaling`.

Boundary K + 1 < N. I suspected an off-by-one against scipy's dense
fallback in `eigsh`. scipy 1.18 falls back only at `k >= n`
(`arpack.py:1690`), so K + 1 = N - 1 is fine; confirmed by running the sqls
backend at K = 4 on the N = 6 system (no error, no warning). Not a bug.

Silent fallback. `smallest_k_svd(..., gpu=False)` never densifies the CPU
path; `_deflate_sqls` has no `except` that returns a numpy result; the only
`except RuntimeError` re-raises unless the message says `singular`.

Timing. `t_svd_s` (sqls) = CSR conversion + smallest-k + sigma_max + checks
+ update, without the x_share solve, as documented; `t_smallest_k_s` and
`t_sigma_max_s` are disjoint sub-intervals of it; `t_xshare_s` is outside.
`t_spectrum_s` = fvm spectral-radius eig + the library's bound calls, 0.0
under deflation. The diagnostics (`get_matrix_properties`, V7, V8) are in
no recorded per-step timing. No per-iteration timer exists in
`time_solvers.py`.

Metadata. `hhl_spectrum`, `hhl_a_scale`, `hhl_kappa`, `hhl_lambda_*` are
the values passed to (or returned by) the library for the circuit of that
step; `library_source` is the fork's own report and `generate_circuit`
raises if it disagrees with what fvm asked for. The nine backend columns
come from the `SvdInfo` of the pre-step that ran. '' means not applicable,
0.0 means a time that did not happen, following the fb_* and `t_svd_s`
conventions. `_matrix_properties` under diag off keeps `nnz_per_row` by the
same formula as `get_matrix_properties`.

Defaults. `-hhl_spectrum internal`, `-hhl_spectral_diag on`,
`-hhl_deflate_svd numpy`, tol None: `deflate()` runs the old arithmetic in
the old order; the fork with no arguments calls each bound method once
instead of twice (same deterministic values). `tests/test_deflation.py`
(item 6, unchanged) passes: 17 tests, 30.5 s.

Tests are not vacuous. The global call log is proven live by the numpy
contrast case (exactly one `svd` from `deflation.py:deflate`, shape (6, 6))
and the diag-on case (only `get_matrix_properties` origins). The fork's
"skips internal calls" tests patch `condition_bounds` / `eigs_bounds` to
raise and compute the reference values before patching. Statevector
equality in the fork is exact (`assert_array_equal`), not approximate.
`|dq|` at nelem 2 is O(0.1 to 1), so the 1e-10 absolute solution checks
are meaningful.

Style. No added line in either diff exceeds 88 characters and none carries
trailing whitespace (the long lines and trailing spaces the scan shows in
`math_tools.py`, `quantum_tools.py`, `time_solvers.py`,
`nozzle_1d_solver.py` and `hhl.py:233-256` are pre-existing, outside the
diff hunks). Imports are grouped at module top except the lazy sqls import
in `deflation._smallest_k_svd`, which is explained in code. New functions
carry type hints.

## Commands run (fvm venv `.venv/bin/python`, from the fvm root)

| When (UTC) | Command | Wall | Result |
|---|---|---|---|
| 00:27 | `git diff --stat`, `git diff \| shasum -a 256` (both repos) | < 1 s | fvm `ba85da22...`, fork `67e9f74a...` = patch file |
| 00:38 | probe: sqls backend at K = 3, 4 on the N = 6 archived system | 0.5 s | both OK, no warning (K + 1 < N rule is right) |
| 00:38 | `-m unittest tests.test_deflation_svd.TestSqlsBackendEquivalence TestSqlsBackendFailures TestSqlsBackendRecord tests.test_hhl_spectrum.TestEncodedSpectrumDerivation` with `-W error::DeprecationWarning` | 1.0 s | 20 tests OK |
| 00:38 | fork: `PYTHONPATH=. python -W error::DeprecationWarning -m unittest test.test_linear_solvers.TestSuppliedSpectrum` | 2.1 s | 8 tests OK |
| 00:38 | style scan of added lines (length > 88, trailing whitespace), both diffs and the 3 new files | < 1 s | none |
| 00:38 | probe: degenerate top (sigma_5 = sigma_6 = sigma_7), K = 5, 6, both backends | < 1 s | no error in that instance |
| 00:41 | probe: supplied bounds vs `cond` / `eigvals` of the real encoded H, sqls backend, 9 systems x K = 1..4 | 7.2 s | worst 9.1e-15 (kappa), 4.4e-15 (lambda_min), 1.0e-14 (lambda_max - 1); `nl` identical |
| 00:44 | `-m unittest tests.test_deflation_svd.TestNoFullSpectrumOnSolvePath` | 21.0 s | 3 tests OK |
| 00:44 | `-m unittest tests.test_hhl_spectrum.TestDeflationSpectrumSolveNelem2` | 12.7 s | 5 tests OK |
| 00:47 | `-m unittest tests.test_deflation` (pre-existing item-6 module) | 30.5 s | 17 tests OK |
| 00:52 | probe: global call log at verbosity 0 and 1, sqls + deflation + diag off, nelem 2 | 9.1 s | v0: none; v1: `cond`+`svd` on (8, 8) and (16, 16) from `math_tools` (F1) |
| 00:52 | probe: 60 random degenerate-top 10 x 10 cases, K = 8, sqls, `encoded_spectrum` | 1.0 s | 1 of 60 raised the `encoded_bounds` ValueError (F2) |

Not run (over the 60 s limit, for the operator):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

and the full default suite (about 230 s), which the builders and verifiers
ran (211 tests, 206 pass, 4 `test_code_versions` fail under the override,
1 skipped).

## Not reviewed

- Harvester changes (listed by both builders; not made, as required).
- The pre-existing git-source switch in `pyproject.toml`, `uv.lock`,
  `docs/`, `tests/test_output_contract.py`, `tests/test_sqls.py` and the
  README install text.
- The AC18-7 cost numbers were not re-measured (classical only, but the
  table took the builder 62 s; the method and honesty of the table read
  correctly: in-process Jacobians, median of 7, split timings, the fill-in
  caveat at nelem 42 / 170 / 682 stated plainly).
