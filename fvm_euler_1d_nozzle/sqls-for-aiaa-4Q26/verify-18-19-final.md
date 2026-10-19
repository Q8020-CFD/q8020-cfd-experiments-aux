# Final verification: items 19 and 18 (after code review and fix-up)

Independent verifier report, round final. Ran 2026-10-19T01:09:48Z to
2026-10-19T01:26Z (UTC). I read the diffs myself, ran the tests myself,
and wrote my own probe scripts. I did not use the builders' narrative
to decide any criterion. No code was edited. Nothing was committed.
Scratch was under `/tmp/item18-19-verifier/` and is removed.

## Verdict: PASS

Every criterion of items 19 and 18 passes. Both should-fix findings of
the code review (F1, F2) are fixed and I reproduced the fixes. Four
non-blocking nits remain and are listed at the end. One of them is a
one-line style slip introduced by the fix-up.

Two caveats the operator should know, neither caused by the change:

1. The full default fvm suite has 4 failures. All four are
   `test_output_contract.*.test_code_versions`. They assert
   `commit_source == 'direct_url'` for `linear_solvers`. Under the
   editable fork override the task mandates, the value is `'git'`. The
   same assertion passes for `sqls` in the same test (sqls is the pinned
   git install). So the four failures are the install mode, not the
   code. Re-run the suite after the fork is committed, the rev bumped,
   and `uv lock && uv sync` done.
2. The harvester in the experiments-aux working tree is modified. That
   edit is the orchestrator's item-19 harvester update, logged in
   `STATUS.md` at 2026-10-18T23:50Z at the operator's request. It is
   not a builder edit. Item-18 columns are still to be added (the list
   is in `build-18.md`).

## State verified

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90` (unchanged), uncommitted.
  14 modified files plus 3 untracked (`hhl_spectrum.py`,
  `tests/test_deflation_svd.py`, `tests/test_hhl_spectrum.py`).
- Fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, branch
  `feature/sqls-aiaa-4q26`, HEAD `9d1d7bb` (unchanged), 6 modified files.
  `git diff | shasum -a 256` =
  `67e9f74ab95956ab67e9c67f8d0a9ec569a0b7332464f22cf3b7f73b59c65e76`,
  equal to the patch
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`.
- sqls: `/Users/agallojr/proj/src/q8020/sqls` at `187a7a5`, clean. Not
  edited.
- fvm venv: `linear_solvers` imports from the fork working tree
  (editable override, `direct_url.json` says `file://.../quantum_linear_solvers`,
  editable true). `sqls` is the pinned git install at `187a7a5`.
- Earlier uncommitted fvm changes intact: `pyproject.toml`
  `[tool.uv.sources]` has git sources at `187a7a5…` (sqls) and
  `9d1d7bb…` (fork); `uv.lock` has the same two git sources and no
  path source. The `docs/`, `tests/test_output_contract.py`,
  `tests/test_sqls.py` hunks are the pin switch and are untouched by
  items 18 and 19.
- Stack: Python 3.12.10, numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2, macOS
  26.7.1 arm64.

## Item 19

### AC19-1 Inventory: PASS

`build-19.md` has the table. Every dense call on the HHL path is
listed with file:line, class (a) to (d), when it runs, and what happens
under `-hhl_spectrum deflation`. I grepped both trees for
`np.linalg.{svd,cond,eig,eigvals,eigh,eigvalsh}` and `scipy.linalg`.
Every hit in fvm (`deflation.py:227`, `math_tools.py:152, 198, 234,
255, 259, 269, 279, 363, 372`) and in the fork (`numpy_matrix.py:102,
111`, `tridiagonal_toeplitz.py:220`) is in the table. Nit: the "now"
line numbers of `math_tools.py` in the table are 5 to 11 lines low
after the item-18 fix-up added docstring lines (e.g. V7 `147` is now
`152`, V8 `187` is now `198`). The file and function names are right.

### AC19-2 Fork API: PASS

`HHL.construct_circuit` and `HHL.solve` take `condition_bound` and
`eigenvalue_bounds`. When supplied, `condition_bounds()` and
`eigs_bounds()` are not called. Proof: fork test
`TestSuppliedSpectrum.test_supplied_skips_internal_calls` patches both
methods to raise and builds four circuits (8 tests, 0.83 s, OK).

Identical to 9d1d7bb when not supplied. My own check: I exported the
9d1d7bb tree with `git archive` into scratch, built circuits with no
arguments from that tree and from the working tree, and compared.
Five systems: 2 x 2, 4 x 4, synthetic doubled 8 x 8, and the real fvm
nelem-2 encoded H (16 x 16) at k = 0 and k = 1. Statevector
(`np.array_equal`), register sizes, instruction count and `scaling`
are bit-identical in all five. 7.5 s and 7.3 s.

Invalid supplied bounds raise `ValueError` (kappa 0.5, nan; bounds
(2, 1), (0, 0)). Checked by hand.

### AC19-3 Fork provenance: PASS

`HHL.spectral_info` and `LinearSolverResult.spectral_info` are a
`SpectralInfo` with `kappa`, `lambda_min`, `lambda_max`,
`kappa_source`, `eigs_source`, `source`, `wall_s`. fvm reads it, stores
`library_source`, and raises `RuntimeError` if the library reports a
source other than the one fvm asked for (`quantum_tools.py`,
`generate_circuit`).

### AC19-4 fvm wiring: PASS

- Flag `-hhl_spectrum {internal, deflation}`, default `internal`.
  Default path numbers unchanged (see AC19-7 and the 9d1d7bb check).
- Transformation documented in `hhl_spectrum.py` (module docstring) and
  `build-19.md`: with s = sigma_max, kappa = sigma_max / sigma_k,
  lambda_min = sigma_k / sigma_max, lambda_max = 1, and the p padding
  ones lie inside [lambda_min, lambda_max].
- I verified the transformation against `np.linalg.cond(H)` and
  `np.linalg.eigvals(H)` of the real encoded H built through
  `math_tools.scale_Ab` / `convert_to_pow2` / `convert_system_to_herm`,
  on all 9 archived Jacobians, k = 1 to 4, for both backends (72 cases):
  kappa relative error <= 7.1e-15, lambda_min <= 3.6e-15,
  |lambda_max(H) - 1| <= 6.4e-15. Clock width from the supplied kappa
  equals the one from cond(H) in 72 of 72.
- Edge: numpy backend at K = N - 1 = 5 (nelem 2) gives kappa_eff = 1,
  supplied (1, 1, 1); cond(H) = 1 + 9e-16; recombine error 5.3e-16.
- Parse-time rejections, each exit 2 with 0 files written and a clear
  message (11 probes, about 1 s each): `-hhl_spectrum deflation` with
  k absent or 0; `-hhl_spectral_diag off` without deflation;
  `-hhl_spectrum` / `-hhl_spectral_diag` with LU or SQLS; unknown
  choice.

### AC19-5 fvm-side spectral calls: PASS

- (b) scale: `scale_Ab(rho=sigma_max)` returns before any eig.
  Verified by call log (below): zero watched calls.
- (a) library calls: skipped when supplied (AC19-2).
- (c)/(d) calls carry `diagnostic (c)` / `diagnostic (d)` comments in
  `math_tools.py` and `quantum_tools.py`. None sits inside `t_svd_s`,
  `t_spectrum_s`, `circ_generate_time`, `circ_transpile_time` or
  `circ_run_time`: `get_matrix_properties` runs before the `scale_Ab`
  timer; the det / cond prints are inside untimed `convert_*` calls;
  `t_rho_s` wraps only the eig.
- (c) calls that still run with `-hhl_spectral_diag on`:
  `get_matrix_properties` cond + eigvals on A_q and on A_q / s (V9 to
  V11), and at `-v 1` the print-only cond in `convert_to_pow2` /
  `convert_system_to_herm` (V7, V8). All are switched off by
  `-hhl_spectral_diag off` and listed in `build-19.md`.

### AC19-6 Recording: PASS

My own CLI runs (nelem 2, one step), CSV read by column name:

| run | hhl_spectrum | hhl_a_scale | hhl_kappa | hhl_lambda_min | hhl_lambda_max | t_spectrum_s | condition_number |
|---|---|---|---|---|---|---|---|
| k 1, sqls, deflation, diag off | deflation | 17.232977768079294 | 6.849832509058093 | 0.14598897107011277 | 1.0 | 0.0 | '' |
| k 1, numpy, internal | internal | 11.836773857840834 | 6.849832509058099 | 0.21254310701978207 | 1.4558846840403186 | 7.9e-05 s | 6.8498325090580945 |
| k 0, default | internal | 6.0291613707809875 | 38.306161601199456 | 0.07461648443127339 | 2.858271110737748 | 9.5e-05 s | 38.30616160119951 |

`hhl_kappa` equals `kappa_eff` exactly under deflation. Internal row:
`hhl_a_scale * hhl_lambda_max` = 17.2330 = sigma_max(A'), consistent.
Pickle has `hhl_spectrum`, `hhl_spectral_diag`, and `quantum_circuit`
carries the five spectrum values of the last step. The 6 new columns
sit after `t_svd_s`; the 27 earlier columns keep their names and
values; empty cells for unknown values, 0.0 for a time that did not
run. `TESTING.md` section (m) and `tests/contract.py`
(`QC_METADATA_SPECTRUM_COLUMNS`, `METADATA_KEYS_HHL_ONLY`,
`QUANTUM_CIRCUIT_KEYS`, `expected_files(hhl_spectrum=)`) are updated.

### AC19-7 Equivalence gates: PASS (caveat on "green")

(i) Default path:
- nelem-2 HHL gate fixture at 1e-10:
  `test_gate_fixture.TestHHLFixture.test_nelem2_iter0_statevector_matches_reference`
  ok, 7.97 s, in the full suite.
- Fork tests: `test.test_linear_solvers`, 33 tests OK, 7.1 s, run with
  `-W error::DeprecationWarning`.
- Full default fvm suite: 214 tests, 236.5 s, 209 ok, 4 FAIL, 0 ERROR,
  1 skipped (the opt-in nelem-5 gate). The 4 FAIL are the override
  artifact described at the top. No test in `test_deflation`,
  `test_deflation_svd`, `test_hhl_spectrum` or `test_gate_fixture`
  failed.
- DeprecationWarnings: suite run with
  `PYTHONWARNINGS=default::DeprecationWarning` (inherited by the solver
  subprocesses) and `-W default::DeprecationWarning`: 0 lines contain
  `DeprecationWarning`. My six CLI runs: 0 lines on stderr.

(ii) Supplying the exact internal values gives the identical circuit
(`circuit_key` equality, library bounds forbidden): nelem 2 k = 0 and
k = 1, and the archived nelem-5 iteration-0 system at k = 1,
construction only, 25.63 s (under 60 s). All ok in the suite.

(iii) nelem 2, k = 1, supplied from deflation: `n_clock` 6 equals the
internal computation on the same encoded matrix and the default path;
solution within 1e-10 of both (in-process test ok). My CLI runs:
`dq_hhl` differs from the internal numpy k = 1 run by 1.90e-12 max-abs
(|dq| scale 0.44) and from the numpy supplied-spectrum run by 2.25e-14;
`dq_lu` identical; `circ_qubits` 11 in all.

### AC19-8 Hygiene: PASS (one nit, see AC18-9)

Added lines in both diffs: none over 88 chars, no trailing whitespace.
New-file scan: one 97-char line, `tests/test_deflation_svd.py:13`, a
module-docstring line added by the item-18 fix-up (reported under
AC18-9). Imports grouped at module top; type hints on new functions.
README and TESTING updated in fvm; README updated in the fork
("Supplied spectral bounds" section). Nothing committed (HEADs
unchanged). Fork patch written and byte-equal to the diff. Earlier
uncommitted changes intact.

## Item 18

### AC18-1 Default unchanged: PASS

`-hhl_deflate_svd {numpy, sqls}`, default `numpy`.
`tests/test_deflation.py` (item 6) is unmodified vs HEAD and passes in
the suite. My bit-identity check: `deflate()` of the working tree vs
HEAD's `deflation.py` (loaded from `git show HEAD:deflation.py`) on all
9 archived systems, k = 1 to 4: `a_shifted`, `sigma`, `u`, `v`,
`kappa`, `kappa_eff`, `x_share_classical`, `shift`, `correction()` all
`array_equal` / `==`. 0 mismatches of 36.

### AC18-2 sqls backend call: PASS

A `mock.patch.object(..., wraps=...)` spy on
`sqls.core.truncated_svd.smallest_k_svd`: called once, second argument
k + 1 (3 for k = 2), `tol=1e-11` passed through, input is a scipy
sparse matrix. No copy of its code (the only `np.linalg.svd` in
`deflation.py` is in the numpy branch, line 227). sigma_max: ARPACK
`eigsh(k=1, which='LA')` on a `LinearOperator` for A^T A, seeded start
vector, tolerance = the Lanczos tolerance; recorded as
`sigma_max_method = eigsh_ata`, `sigma_max_tol`, `svd_tol`. The result
is checked against max column / row 2-norm <= ||A||_2 <= sqrt(||A||_1
||A||_inf).

### AC18-3 Partial spectrum: PASS

`kappa = sigma_max_est / sigma[0]`, `kappa_eff = sigma_max_est /
sigma[k]`, `correction()` uses `sigma[:k]`, `ub[:k]`, `v[:, :k]` and
`shift`. Verified: recombine of the exact A'^-1 b reproduces A^-1 b to
1.4e-13 relative (worst of 36). ||x||^2 by one `splu` solve, labeled
`x_share_method = splu_solve`, timed as `t_xshare_s` outside `t_svd_s`
(`t_svd_s` 7.1e-4 s >= smallest-k + sigma_max 6.4e-4 s; `t_xshare_s`
3.5e-5 s). `x_norm2` equals ||A^-1 b||^2 to 1.9e-15 relative. No full
SVD in the backend (call log below).

### AC18-4 Metadata: PASS

Nine columns after `t_spectrum_s`: `hhl_deflate_svd, svd_tol,
sigma_max_method, sigma_max_tol, t_smallest_k_s, t_sigma_max_s,
x_share_method, t_xshare_s, svd_residual`. My CLI runs:

| run | hhl_deflate_svd | svd_tol | sigma_max_method | sigma_max_tol | t_smallest_k_s | t_sigma_max_s | x_share_method | t_xshare_s | svd_residual |
|---|---|---|---|---|---|---|---|---|---|
| sqls k 1 | sqls | 1e-12 | eigsh_ata | 1e-12 | 4.5e-4 s | 3.7e-4 s | splu_solve | 4.0e-5 s | 6.3e-15 |
| numpy k 1 | numpy | '' | numpy_svd | '' | 3.4e-5 s | 0.0 | svd | 0.0 | '' |
| k 0 | '' | '' | '' | '' | 0.0 | 0.0 | '' | 0.0 | '' |

Pickle: `hhl_deflate_svd`, `hhl_deflate_svd_tol` (1e-12 for sqls,
None for numpy); `quantum_circuit` carries the nine values of the last
step. `tests/contract.py` and `TESTING.md` section (n) updated.
Harvester changes listed in `build-18.md` (5 items), not made.
Observation: the 15 new columns (items 19 and 18) are inserted before
the 9 fairness columns rather than appended; the harvester reads by
name and `append_csv_row` rotates stale headers, so this is safe.

### AC18-5 Equivalence: PASS

My own script, all 9 archived Jacobians x k = 1 to 4 (36 cases), tol
1e-12, 1.5 s:

| quantity | worst | limit |
|---|---|---|
| smallest k + 1 singular values, relative | 5.0e-15 | 1e-8 |
| principal angles, left subspace | 1.8e-14 rad | 1e-6 rad |
| principal angles, right subspace | 1.2e-14 rad | 1e-6 rad |
| relative gap at the cut (sigma_k - sigma_{k-1}) / sigma_k, smallest | 0.040 | well separated |
| sigma_max estimate, relative | 6.1e-16 (sign +6.1e-16 max) | 1e-12 |
| A' Frobenius, relative | 9.3e-15 | 1e-8 |
| kappa_eff, relative | 3.0e-15 | identical in spirit |
| clock width n_clock (supplied kappa, both backends; cond(H), both backends) | 1 distinct value in all 36 | identical |
| recombine(A'^-1 b) vs A^-1 b, relative | 1.4e-13 | 1e-8 |
| x_share_classical, absolute | 1.0e-13 | |

Near-degenerate cuts: none on the archived systems (min gap 0.040).
The test module checks the gap before the angles and has a synthetic
exactly-degenerate case (`test_degenerate_cut`). sqls repeat runs agree
to 4e-15 (own random start vector in `smallest_k_svd`).

nelem-2 CLI, k = 1, one step, each backend: `circ_qubits` 11,
`n_clock` 6, `nqubits` 4 in both; `dq_hhl` differs 1.77e-14 max-abs
(internal spectrum) and 2.25e-14 (supplied spectrum); `dq_lu`
identical. Limit 1e-8.

### AC18-6 Validation: PASS

- `-hhl_deflate_k 5 -hhl_deflate_svd sqls` at nelem 2: exit 2, message
  "needs K + 1 < N = 6, i.e. K <= 4; got K = 5", 0 files.
- `-hhl_deflate_svd_tol` with numpy, above 1e-6, negative: exit 2.
- Lanczos non-convergence (400 x 400 clustered, `maxiter=1`):
  `RuntimeError` naming `smallest_k_svd: Lanczos` and `No convergence`.
- Exactly singular A: `ValueError` "the sparse LU of A failed, A is
  singular". Numerically singular (sigma 1e-17): `ValueError`
  "numerically singular ... 1.000e-17 <= N eps sigma_max = 6.661e-15".
- Wrong sigma_max and perturbed triplets: `RuntimeError` (suite tests
  ok).
- scipy 1.18 `eigsh` falls back to dense `eigh` only at `k >= n`
  (source checked), so K + 1 = N - 1 is safe; the parse rule K + 1 < N
  matches.

### AC18-7 Cost comparison: PASS

`build-18.md` has the table: N = 15, 33, 63, 126, 255, 510, 1023,
2046 (nelem 5, 11, 21, 42, 85, 170, 341, 682), k = 2 and 4, median of
7, wall times in ms / s, split into smallest-k, sigma_max, x_share
solve; Jacobians assembled in-process (kappa 96 at nelem 5 iteration 0
matches `06a`); machine Apple M3 Pro, 12 cores, 36 GiB, macOS 26.7.1,
numpy 2.5.2, scipy 1.18.0. Honest reading: numpy wins below N = 255
(17.6x at N = 15) and on the round-off-dense Jacobians at nelem 170 and
682; sqls wins at N = 255 (1.4x) and N = 1023 (4.0x); sigma_max is the
costly sqls step. My spot check on the archived N = 15 (iteration 14),
median of 7: numpy 0.031 ms / 0.039 ms (k 2 / 4), sqls 0.664 ms /
0.670 ms (smallest-k 0.31 ms, sigma_max 0.30 ms, x_share 0.034 ms).
The table's first rows read 0.036 / 0.033 ms and 0.633 / 0.623 ms.
Same picture.

### AC18-8 No dense routine end to end: PASS

`tests/test_deflation_svd.TestNoFullSpectrumOnSolvePath` (5 solves,
ok in the suite) uses a log that patches every module attribute bound
to `numpy.linalg` svd / cond / eig / eigvals / eigh / eigvalsh and
`scipy.linalg` svd / svdvals / eig / eigvals / eigh / eigvalsh / schur,
so nested `cond -> svd` and `from ... import` aliases are caught. My
own in-process run of the same log, `-hhl_deflate_svd sqls
-hhl_spectrum deflation -hhl_spectral_diag off`, nelem 2, k = 1:
verbosity 1 (the CLI default): `[]`; verbosity 2: `[]`. My CLI run at
default `-v 1`: 0 "Condition #" prints on stdout (the k = 0 control run
prints 2). Remaining dense calls in this configuration: none. With
`-hhl_spectral_diag on` the only calls are the labeled diagnostics
(`get_matrix_properties`, and at `-v 1` the `convert_*` prints), all
switched off by the documented flag.

### AC18-9 Hygiene: PASS (one nit)

- Style: one line over 88 chars, `tests/test_deflation_svd.py:13` (97
  chars, module docstring, added by the fix-up). No other long line and
  no trailing whitespace in the added lines of either diff or the new
  files. `py_compile` clean.
- Tests: 57 tests in the two new modules, all ok.
- README (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/README.md`,
  "Two backends for the deflation pre-step") and TESTING (section (n))
  explain both backends, state "Both are classical. Neither is part of
  the quantum solve", and carry the attribution "sqls smallest_k_svd,
  ORNL sqls package, refs 13 to 15 of the AIAA abstract; source
  attribution to be confirmed" (same words as the AC, commas instead
  of the AC's parentheses).
- Nothing committed; earlier uncommitted changes intact (above).

## Review findings (review-18-19.md)

| finding | class | status | my evidence |
|---|---|---|---|
| F1 default `-v 1` still ran two full SVDs | should-fix | fixed | call log empty at `-v 1` and `-v 2` with diag off; CLI stdout 0 "Condition #" prints; k = 0 control prints 2 |
| F2 degenerate top cluster spurious failure | should-fix | fixed | 60 random 10 x 10 seeds, K = 8, sqls: 0 failures; sigma_max clamped to sigma_K in 7 of 60; `test_degenerate_top_cut` ok |
| F3 one-sided 4 eps bound platform-tight | nit | open | observed max +6.1e-16 vs limit 8.9e-16 on this machine; passes here |
| F4 `py-modules` omits `deflation`, `hhl_spectrum` | nit | open | `pyproject.toml:75-78` unchanged; no documented install path is affected |
| F5 `-hhl_deflate_svd sqls` with k = 0 silent no-op | nit | open | pickle records `hhl_deflate_svd 'sqls'`, `tol 1e-12`; CSV cells '' and 0.0; run 10.8 s |
| F6 attribution punctuation | nit | open | content identical, commas not parentheses |
| F7 to F11 | nit | open | unchanged; none affects a number |

No must-fix findings existed.

## Non-blocking findings (mine)

1. `tests/test_deflation_svd.py:13` is 97 chars (limit 88). One-line
   wrap.
2. `build-19.md` inventory "now" line numbers for `math_tools.py` are
   stale by 5 to 11 lines after the fix-up.
3. F5: with `-hhl_deflate_k 0 -hhl_deflate_svd sqls` the pickle
   records the backend option and tolerance while the CSV correctly
   shows no pre-step. A parse-time rejection would be consistent with
   `-hhl_spectrum deflation` at k = 0.
4. The 15 new qc_metadata columns are inserted before the fairness
   block, not appended. Safe for the by-name harvester and the header
   rotation; worth knowing when diffing old CSVs.

## Commands run (fvm venv `.venv/bin/python`, cwd fvm root unless noted)

| UTC | command | wall | result |
|---|---|---|---|
| 01:09:48 | `git status`, `git diff --stat`, `git diff \| shasum -a 256` (fork) vs patch file | < 1 s | fork hash = patch; HEADs 1b4abd90 / 9d1d7bb; sqls clean 187a7a5 |
| 01:12 | venv provenance (`direct_url.json`), pyproject / uv.lock sources, grep of dense calls in fvm and fork | < 1 s | fork editable override in place; sqls pinned git; sources intact |
| 01:13:14 | fork: `PYTHONPATH=. python -W error::DeprecationWarning -m unittest test.test_linear_solvers.TestSuppliedSpectrum -v` | 2.6 s | 8 OK |
| 01:13:52 | fork: same, whole module `test.test_linear_solvers` | 8.0 s | 33 OK |
| 01:14 | style scan of added lines (both diffs, 3 new files); `py_compile` | < 1 s | one 97-char line |
| 01:15:27 to 01:19:25 | `PYTHONWARNINGS=default::DeprecationWarning python -W default::DeprecationWarning -m unittest discover -s tests -v` | 236.5 s | 214 tests, 209 ok, 4 FAIL (test_code_versions), 0 ERROR, 1 skipped, 0 DeprecationWarning lines |
| 01:16 | 11 CLI parse-time probes (nelem 2, `-iters 1`) | about 1 s each | all exit 2, 0 files, clear messages |
| 01:17:14 | `/tmp/item18-19-verifier/indep_check.py` (bit-identity vs HEAD, sqls vs numpy, H bounds, spy, x_norm2, N = 15 timing, repeatability) | 1.5 s | all within limits (tables above) |
| 01:18 | CLI nelem 2: sqls + deflation + diag off (`-v 1`); k 0 sqls; shots 300 sqls + deflation + diag off | 6.19 s, 10.78 s, 5.60 s | exit 0; 0 / 2 / 0 "Condition #" prints; 0 DeprecationWarning |
| 01:19:05 | `/tmp/item18-19-verifier/calllog_probe.py` (call log at `-v 1`, `-v 2`; F2 60-seed scan; failure modes; invalid fork bounds) | 9.4 s | `[]`, `[]`; 0 of 60 failed; clear errors; ValueErrors |
| 01:20 | CLI nelem 2: numpy + deflation + diag off; numpy internal k 1; sqls internal k 1 | 6.18 s, 5.95 s, 6.00 s | exit 0 |
| 01:21 | harvester provenance (`stat`, `git log`, `git diff`, STATUS.md) | < 1 s | orchestrator edit 2026-10-18T23:50Z |
| 01:22 | CSV / pickle parse of the six runs, `dq_hhl` comparisons | < 1 s | tables above; 2.25e-14, 1.90e-12, 1.77e-14 |
| 01:23 | K = N - 1 numpy edge; `test_deflation.py` unchanged check | < 1 s | kappa_eff 1, cond(H) 1 + 9e-16; unchanged |
| 01:23:55 | `git archive 9d1d7bb linear_solvers` to scratch; `build_circ.py` under 9d1d7bb and under the working tree; compare | 7.5 s + 7.3 s | 15 of 15 arrays bit-identical |

Not run (over the 60 s single-run limit; for the operator):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

(STATUS.md records the orchestrator ran it with the item-19 fork at
2026-10-18T23:50Z: 7 OK, nelem-5 HHL 124.3 s, 1e-10 matched. Item 18
did not change the fork.)

After the fork is committed, the rev bumped and `uv lock && uv sync`
run, re-run the default suite; the 4 `test_code_versions` cases should
then pass:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
.venv/bin/python -m unittest discover -s tests
```

## Scratch

`/tmp/item18-19-verifier/` (scripts, six nelem-2 run dirs, suite log,
9d1d7bb export) removed at the end of this verification. No other
`/tmp/item18*` or `/tmp/item19*` directories were present.
