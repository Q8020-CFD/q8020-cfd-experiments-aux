# Item 19 verification (round 1): optional, recorded HHL spectral computations

Independent verifier report. Work ran 2026-10-18T23:33Z to 2026-10-18T23:45Z
(UTC). I did not read the builder's narrative before checking; I read the diffs,
ran the tests, and ran my own one-off checks. I did not edit code. Scratch lived
in `/tmp/item18-19-verifier/` and was removed at the end.

## Verdict: PASS

Every criterion passes. One criterion (AC19-7 i, "full default fvm suite
green") passes with an environment caveat: 4 of 180 tests fail, all four are
`test_code_versions`, and the cause is the editable fork override the task
requires me to leave in place. Details under AC19-7 and in the findings list.

## State checked

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90`, uncommitted. `git diff | shasum
  -a 256` = `5bd4c7e5bb901815...` before and after my work (I changed nothing).
- fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, branch
  `feature/sqls-aiaa-4q26`, HEAD `9d1d7bb`, uncommitted. Installed in the fvm
  venv as the editable override (`direct_url.json`: `file://...`, `editable:
  true`).
- sqls: `/Users/agallojr/proj/src/q8020/sqls` at `187a7a5`, clean, installed
  non-editable from GitHub at that rev. Not touched.
- Stack: qiskit 2.5.2, numpy 2.5.2, scipy 1.18.0, Python 3.12 in `.venv`.

## Criteria

### AC19-1 Inventory: PASS

I grepped both working trees for `np.linalg.{svd,cond,eig,eigvals,eigh,
eigvalsh}` and the `scipy.linalg` equivalents, then compared against the table
in `build-19.md`.

fvm hits (file:line, working tree): `deflation.py:104` svd; `math_tools.py:147`
cond, `:187` cond, `:223` eig, `:244` cond, `:248` cond, `:258` eig, `:268`
cond, `:352` cond, `:361` eigvals. No hits in `quantum_tools.py`,
`time_solvers.py`, `nozzle_1d_solver.py`, `helper_tools.py`, `hhl_spectrum.py`.

fork hits: `numpy_matrix.py:102` eigvals, `:111` cond;
`tridiagonal_toeplitz.py:220` cond (not on the fvm path). Called from
`hhl.py:520` and `:538`.

Every hit is in the builder's table (V1 to V10 and F1 to F3) with the right
line and a class (a), (b), (c) or (d). Nothing reachable on the HHL path is
missing. The table is in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/build-19.md`.

### AC19-2 Fork API: PASS

- `HHL.construct_circuit(..., condition_bound=None, eigenvalue_bounds=None)`
  and `HHL.solve(...)` take the same two keywords (`hhl.py:424-429`,
  `:644-647`).
- Not called when supplied: the fork test `TestSuppliedSpectrum.
  test_supplied_skips_internal_calls` patches `NumPyMatrix.condition_bounds`
  and `eigs_bounds` to raise and builds on four matrices;
  `test_supplied_toeplitz_skips_internal_calls` does the same for
  `TridiagonalToeplitz`. Both pass (fork suite below). My probe P3 (kappa
  supplied, `condition_bounds` patched to raise) also built fine and reported
  `source = mixed`.
- Identical to 9d1d7bb when not supplied. I exported 9d1d7bb with `git
  archive` into scratch and built the default-path circuit with the old and
  the new fork in separate processes (`PYTHONPATH` plus `python -P`; the
  loaded `linear_solvers.__file__` was printed and differed as intended).
  `quantum_tools.circuit_key` (sha256 of the full instruction data) was equal
  on all 7 systems:

| system | nl | key prefix | old | new |
|---|---|---|---|---|
| 2 x 2 symmetric | 3 | `4f2923144e911a8d` | same | same |
| 4 x 4 tridiagonal | 4 | `bf5e2517c431cf2d` | same | same |
| 4 x 4 with negative eigenvalues | 4 | `95595868798d1e13` | same | same |
| 8 x 8 doubled non-symmetric | 5 | `20a073d8591fbee3` | same | same |
| archived nelem 2 iter 0, k = 0 | 7 | `af09503fa9db61af` | same | same |
| archived nelem 2 iter 0, k = 1 | 6 | `aa2d204c388f5a15` | same | same |
| archived nelem 5 iter 0, k = 1 | 7 | `c43ee0d1e55f7ac9` | same | same |

  `HHL.scaling` was equal too (e.g. nelem 5 k = 1: 0.043971695696357053 both).
  Wall: old 6.8 s and 16.9 s, new 5.9 s and 18.1 s (two processes each).
- Call counts on the internal path (probe P5, P6): `condition_bounds` once,
  `eigs_bounds` once, `np.linalg.eigvals` once inside `eigs_bounds`. At 9d1d7bb
  each method was called twice and `eigs_bounds` ran eigvals twice. Same
  values, so the same circuit; the fork now does one SVD and one eigvals per
  build instead of two and four.

### AC19-3 Fork provenance: PASS

`HHL.spectral_info` is a frozen dataclass `SpectralInfo(kappa, lambda_min,
lambda_max, kappa_source, eigs_source, wall_s)` with a `source` property
(`internal`, `supplied`, `mixed`). `LinearSolverResult.spectral_info` carries it
from `solve()` (probe P8: `supplied`, kappa 10.0). `lambda_min` is recorded
after the near-zero substitution (probe P1: supplied 0.0 with lambda_max 6.0 is
recorded as 0.006, and the warning printed). Exported from
`linear_solvers.__init__`.

### AC19-4 fvm wiring: PASS

- Flag `-hhl_spectrum {internal, deflation}`, default `internal`. Second flag
  `-hhl_spectral_diag {on, off}`, default `on`.
- Default path numbers unchanged: see AC19-7 (i) and the default CLI run
  below (`hhl_spectrum = internal`, circuit files keep their old names).
- `deflation` supplies kappa = sigma_max / sigma_k, lambda_min = sigma_k /
  sigma_max, lambda_max = 1 and scales A' by sigma_max
  (`hhl_spectrum.encoded_spectrum`, `time_solvers.py:600-609`).
- Derivation documented in the `hhl_spectrum.py` module docstring, the fvm
  README section "Supplied spectrum", and `build-19.md`. I checked it
  independently (`/tmp/item18-19-verifier/check_transform.py`, 1.0 s): for all
  9 archived systems, k = 0 (default rho scale) and k = 1 to 4 (sigma_max
  scale), I built H through the solver's own `scale_Ab`, `convert_to_pow2`,
  `convert_system_to_herm` and compared the supplied triple against
  `NumPyMatrix.condition_bounds()` / `eigs_bounds()` of H. Worst relative
  error over the 45 rows: 5.25e-15. The clock-register size `nl` and the
  fork's `_get_delta` value agreed in all 45 rows. The margin of log2(kappa+1)
  to the next integer was at least 0.0016 (nelem 5 iter 14, k = 2), so no row
  sits on a rounding edge.
- Why the identity holds: H = [[0, P], [P^H, 0]] has eigenvalues +- the
  singular values of P; P = [[A_q / s, 0], [0, I_p]] adds p unit singular
  values; with sigma_min(A_q) <= s <= sigma_max(A_q) those ones never set a
  bound. For A', sigma_min = sigma_k and sigma_max is kept, s = sigma_max.
- Parse-time rejections (exit 2, empty outdir, wall about 1 s each):

| extra arguments | message |
|---|---|
| `-hhl_spectrum deflation` | `-hhl_spectrum deflation takes the spectrum from the deflation pre-step and needs -hhl_deflate_k >= 1; got -hhl_deflate_k 0` |
| `-hhl_spectrum deflation -hhl_deflate_k 0` | same |
| `-hhl_spectral_diag off -hhl_deflate_k 1` | `-hhl_spectral_diag off needs -hhl_spectrum deflation; got -hhl_spectrum internal` |
| `-hhl_spectrum deflation -hhl_deflate_k 1 -linsolver LU` | `-hhl_deflate_k applies to -linsolver HHL only; got -linsolver LU` |
| `-hhl_spectrum sqls -hhl_deflate_k 1` | `argument -hhl_spectrum: invalid choice: 'sqls'` |

### AC19-5 fvm-side spectral calls: PASS

- (b) the spectral-radius eig (`math_tools.py:223`) is skipped when a scale is
  supplied (`scale_Ab(rho=...)` returns before any spectral call,
  `t_rho_s = 0.0`; probe: N = 6, rho = 4.0 at verbosity 0, 1, 2 gives
  `t_rho_s = 0.0` and prints 0, 3, 3 lines).
- (a) the library's cond and eigvals are skipped when supplied (AC19-2).
- (c) `get_matrix_properties` (cond + eigvals of A_q and of A_q / s) is labeled
  "diagnostic (c)" in `math_tools.py:343-346` and `quantum_tools.py:854-858`.
  It runs before the timed generate / transpile / run steps and outside
  `t_svd_s`, so no solve or pre-step timing contains it. It is skippable with
  `-hhl_spectral_diag off` (empty cells), and listed in the report (V9 to V11).
- (d) the print-only cond / det / eig calls are labeled "diagnostic (d)" in
  `math_tools.py` (lines 139, 179, 227, 241, 255) and gated on `-v >= 1`. The
  `eig(A_scaled)` that used to run and be discarded at `-v 0` is now gated
  too (`math_tools.py:257`).
- The suite test `test_no_dense_spectral_call_besides_prestep_svd` logs every
  `numpy.linalg` / `scipy.linalg` dense call from fvm or fork code during an
  `hhl_solve`: with `-hhl_spectrum deflation -hhl_spectral_diag off` at `-v 0`
  the list is exactly `[('svd', 'deflation.py')]`. It passed in the full suite
  and in my direct run.
- `t_spectrum_s` = spectral-radius eig time + the library's bound-call time.
  Internal nelem-2 run: 1.4e-4 s; deflation run: 0.0 s. The library part is
  inside `circ_generate_time` (documented), which is unavoidable since the
  library does the work inside `construct_circuit`.

### AC19-6 Recording: PASS

CLI run `-nelem 2 -linsolver HHL -shots 0 -iters 1 -hhl_deflate_k 1
-hhl_spectrum deflation -hhl_spectral_diag off -v 0` (7.9 s wall) wrote
`qc_metadata_nelem2_statevector.csv` with header (verbatim order):

`step, iter, matrix_size_orig, matrix_size_pow2, matrix_size_herm,
condition_number, nnz_per_row, lambda_max_orig, lambda_min_orig,
lambda_max_scaled, lambda_min_scaled, nqubits, circ_depth_orig,
circ_gates_orig, circ_qubits_orig, circ_depth_transpile,
circ_gates_transpile, circ_qubits_transpile, circ_generate_time,
circ_transpile_time, circ_run_time, deflate_k, kappa, kappa_eff, n_clock,
x_share_classical, t_svd_s, hhl_spectrum, hhl_a_scale, hhl_kappa,
hhl_lambda_min, hhl_lambda_max, t_spectrum_s, circ_qubits, fb_depth,
fb_total_gates, fb_cx_count, fb_basis, t_count_s, fb_cached,
effective_shots, seed`

Row values: `hhl_spectrum = deflation`, `hhl_a_scale = 17.23297776807929`,
`hhl_kappa = 6.8498325090581` (equal to `kappa_eff` to the last digit),
`hhl_lambda_min = 0.14598897107011263`, `hhl_lambda_max = 1.0`,
`t_spectrum_s = 0.0`, `n_clock = 6`; `condition_number` and the four
`lambda_*` cells empty. Every pre-existing column keeps its name and order;
the six new columns sit between `t_svd_s` and `circ_qubits`, the same place
the item-6 columns were inserted. Empty cells for unknown values and 0.0 for
times that did not happen follow the deflation / fb_* convention.

Pickle: `hhl_spectrum = 'deflation'`, `hhl_spectral_diag = 'off'` next to
`hhl_deflate_k = 1`; `quantum_circuit` has `hhl_spectrum, hhl_a_scale,
hhl_kappa, hhl_lambda_min, hhl_lambda_max` with the CSV's last-step values.

A 2-iteration run with diagnostics on (12.9 s) wrote two rows with per-step
values (step 1: `hhl_a_scale 17.7518`, `hhl_kappa 6.5260 = kappa_eff`,
`condition_number 6.5260`), so the record is rebuilt each step. Both qpy files
per step are keyed `_deflate1_specdeflation.qpy`.

`tests/contract.py` has `QC_METADATA_SPECTRUM_COLUMNS`,
`QC_METADATA_DIAGNOSTIC_COLUMNS`, the choice constants, the HHL column list,
`METADATA_KEYS_HHL_ONLY`, `QUANTUM_CIRCUIT_KEYS['HHL']` and
`expected_files(..., hhl_spectrum=)`. TESTING.md documents the change (run
record, layout row, contract row, section (m), column order in (l)).

### AC19-7 Equivalence gates: PASS (with an environment caveat on i)

(i) Default path.
- nelem-2 HHL gate fixture: `test_gate_fixture.TestHHLFixture.
  test_nelem2_iter0_statevector_matches_reference` passed in the full suite,
  10.47 s, tolerance 1e-10 max-abs (`MAX_ABS_TOL` in the module).
- Fork tests: `PYTHONPATH=. .venv/bin/python -W error::DeprecationWarning -m
  unittest test.test_linear_solvers` at 2026-10-18T23:33:12Z: 33 tests OK,
  9.4 s. Only the three pre-existing scipy `FutureWarning`s.
- Full suite: `.venv/bin/python -W default::DeprecationWarning -m unittest
  discover -s tests`, 2026-10-18T23:34:31Z to 23:39:08Z, 277.5 s wall
  (274.9 s unittest). **Ran 180 tests: 175 pass, 4 fail, 1 skipped.** The
  skip is the opt-in nelem-5 gate. The 4 failures are
  `test_output_contract.{TestHHLOutputContract, TestHHLShotsOutputContract,
  TestLUOutputContract, TestSQLSOutputContract}.test_code_versions`, each with
  `AssertionError: 'git' != 'direct_url'`.
- Cause of the 4 failures, checked directly: `helper_tools.get_code_versions()
  ['linear_solvers']` = `{commit: 9d1d7bbb..., dirty: true, commit_source:
  git}`; the rev pinned in `pyproject.toml` is the same `9d1d7bbb...`. The
  test (written in today's earlier, pre-item-19 change) asserts
  `commit_source == 'direct_url'` and `dirty is None`, which only a
  non-editable git install satisfies. The editable override that the task
  requires me to leave in place cannot satisfy it. Item 19 does not touch
  `tests/test_output_contract.py` (its diff is the git-source migration
  only). The failing assertion will hold again after the operator commits the
  fork, bumps the rev, and runs `uv lock && uv sync`. I count (i) as passing
  for item 19 and list this as a non-blocking finding.
- DeprecationWarnings: 0 lines matching `DeprecationWarning` in the 277 s log.
  The only non-Future warning is the pre-existing `fake_nighthawk` UserWarning.
- Longest single test: 32.8 s (`test_nelem5_iter0_k1`). Everything is under
  60 s.

(ii) Supplied exact internal values give the identical circuit.
- `tests.test_hhl_spectrum.TestSuppliedExactValuesSameCircuit` (nelem 2 k = 0
  and k = 1; archived nelem 5 iter 0 k = 1, construction only) asserts
  `circuit_key` equality with the library's bound methods patched to raise.
  Passed in the full suite and in my direct run (6.3 s, 3.1 s, 31.6 s).
- Fork tests do the same with exact statevector equality on 4 matrices
  including a synthetic 8 x 8.

(iii) nelem 2, `-hhl_deflate_k 1`, supplied from deflation.
- My CLI comparison, deflation-spectrum run vs internal k = 1 run (13.4 s):
  `n_clock` 6 vs 6, `circ_qubits` 11 vs 11, `hhl_kappa` 6.8498325090581 vs
  6.849832509058099. `dq_hhl` max-abs difference 1.894e-12 on entries up to
  0.435 (tolerance 1e-10). `dq_lu` identical.
- The suite's `TestDeflationSpectrumSolveNelem2` compares in-process against
  both the default rho-scaled deflated path and the internal library bounds of
  the same encoded matrix (A' / sigma_max): clock register equal (6), solution
  within 1e-10 for both. Passed in the full suite and in my direct run.
- Note the encoded matrix differs between the two readings (A' / rho vs
  A' / sigma_max), which is why the qpy files carry `_specdeflation`. The
  circuit depends on A only through A / lambda_min and lambda_min /
  lambda_max, so the solutions agree to round-off; the builder documents this.

### AC19-8 Hygiene: PASS

- Style: no added line in the fvm or fork diffs exceeds 88 characters; no
  trailing whitespace on added lines (awk scan of `git diff -U0` plus the two
  new files). Imports grouped at the top in `hhl_spectrum.py`,
  `tests/test_hhl_spectrum.py`, `hhl.py`. Type hints on the new functions.
  `hhl_spectrum.py` uses 4-space indentation like `deflation.py`; the older
  fvm modules keep their 2-space style (pre-existing).
- Tests: 23 new `unittest.TestCase` tests in `tests/test_hhl_spectrum.py`, 8
  new in the fork's `test/test_linear_solvers.py`. All pass.
- Docs: fvm README (CLI rows, pickle sentence, "Supplied spectrum" section,
  code tree) and TESTING.md updated; fork README has "Supplied spectral
  bounds".
- Nothing committed: HEADs unchanged (fvm `1b4abd90`, fork `9d1d7bb`), no new
  branches, all changes in working trees.
- Fork patch: `git -C quantum_linear_solvers diff | shasum -a 256` =
  `67e9f74ab95956ab...` = sha256 of
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`;
  `diff` of the two is empty.
- Today's earlier fvm changes intact: `pyproject.toml` `[tool.uv.sources]` has
  the two GitHub git sources at `187a7a54...` and `9d1d7bbb...`; `uv.lock`
  has the same two git sources; `docs/FRONTIER_CONDA_SETUP.md`,
  `docs/QUICKSTART_PARALLEL.md`, `tests/test_output_contract.py`,
  `tests/test_sqls.py` still carry the git-source wording. The builder's
  item-19-only diff touches none of those files. I could not reproduce the
  task's fingerprint `8b541216...` because, per the builder, the baseline
  diff changed at 2026-10-18T22:49Z before building started; I verified the
  content instead.
- Scratch: `/tmp/item18-19-builder/` is gone; no solver output left under
  `/tmp` apart from my own scratch, removed at the end.

## Attempts to break it

- Transformation on every archived Jacobian, k = 0 to 4, both scales: holds to
  5e-15 (above).
- Rounding edges: no archived row has log2(kappa+1) within 0.0016 of an
  integer; `_get_delta` equal in all 45 rows.
- Supplied lambda_min = 0: accepted, substituted to lambda_max / 1000,
  recorded as substituted (P1).
- Inconsistent kappa vs eigenvalue bounds (kappa 1 with bounds ratio 6000):
  accepted silently by the fork, `nl = 4` (P2). No cross-check; fvm never
  passes inconsistent values. Listed as a finding.
- numpy scalar inputs (`np.float32`, `np.int64`): accepted, stored as float
  (P4).
- `scale_Ab` at verbosity 0, 1, 2 with and without a supplied rho, and the
  N > 200 power-iteration branch: no crash; `scale_Ab_by_spectral_radius`
  wrapper returns identical arrays and rho.
- Loaded-circuit record: the transpiled qpy from my run reloads and carries
  `metadata['hhl_spectrum'] = {source: deflation, kappa 6.8498..., lambda_min
  0.14598..., lambda_max 1.0, library_source: supplied}`. The generated qpy
  fails to reload with `TypeError: ExactReciprocalGate.__init__() missing 2
  required positional arguments` on qiskit 2.5.2. That is pre-existing (the
  builder reports it on the default path too) and not item 19.
- Harvester: `fvm_euler_1d_solver_harvester.py:610-612` and `:699-701` do
  `if cond is not None: float(cond)`. An empty `condition_number` cell is
  `''`, not None, so `float('')` raises. The builder's listed harvester change
  is needed before any `-hhl_spectral_diag off` run is harvested.

## Findings

1. Non-blocking (AC19-7 i): 4 `test_code_versions` failures under the
   mandated editable fork override (`'git' != 'direct_url'`); not caused by
   item 19; clears after the fork commit, rev bump and relock.
2. Non-blocking (AC19-2 / spirit): the fork does not cross-check a supplied
   `condition_bound` against supplied `eigenvalue_bounds`. A caller can pass
   kappa = 1 with a 6000:1 eigenvalue ratio and get a too-small clock
   register. fvm always derives both from the same SVD, so it is not reachable
   from the CLI.
3. Non-blocking (cosmetic): `SpectralInfo.source` reads `internal` when both
   `kappa_source` and `eigs_source` are `none` (a matrix circuit without the
   bound methods). Unreachable with `NumPyMatrix`.
4. Non-blocking (outside scope): the harvester will raise on empty
   `condition_number` cells (above). Listed by the builder; not fixed.
5. Non-blocking (pre-existing): the N > 200 spectral-radius estimate is an
   unseeded power iteration (`matrix_spectral_radius_estimate`); two calls on
   the same 256 x 256 matrix gave rho 6.5017 and 6.5335. Not item 19, but it
   means "numbers unchanged" at N > 200 was never deterministic on the default
   path.
6. Non-blocking (pre-existing): generated qpy files cannot be reloaded on
   qiskit 2.5.2 (`ExactReciprocalGate`), so the `-loadcirc` round trip of the
   spectrum record is covered only in-process and via the transpiled file.

## Commands run (fvm venv `.venv/bin/python` unless stated)

| When (UTC) | Command | Wall | Result |
|---|---|---|---|
| 23:33:12 | fork: `PYTHONPATH=. python -W error::DeprecationWarning -m unittest test.test_linear_solvers` | 9.4 s | 33 OK |
| 23:34:31 | `python -W default::DeprecationWarning -m unittest discover -s tests` (background, log in scratch) | 277.5 s | 180 tests, 4 fail (`test_code_versions`), 1 skip, 0 DeprecationWarning |
| 23:35 | `check_transform.py` (45 system/k rows vs fork bounds) | 1.0 s | worst rel err 5.25e-15, nl and delta agree |
| 23:35:50 | CLI nelem 2, k = 1, `-hhl_spectrum deflation -hhl_spectral_diag off -v 0` | 7.9 s | columns and pickle as reported |
| 23:37:51 | `fork_identity.py old small n2k0 n2k1` (9d1d7bb export) | 6.8 s | 6 keys |
| 23:38 | `fork_identity.py new small n2k0 n2k1` (working tree) | 5.9 s | same 6 keys |
| 23:38 | 5 parse-time rejection runs | about 1 s each | exit 2, empty outdir |
| 23:38 | fork edge probes P1 to P8 | 3 s | above |
| 23:38:09 | CLI nelem 2, k = 0, default, `-v 0` | 13.3 s | `hhl_spectrum internal`, `hhl_kappa` = `condition_number` to 1.5e-15 |
| 23:39:56 | `fork_identity.py old n5k1` | 16.9 s | key `c43ee0d1e55f7ac9` |
| 23:40 | `fork_identity.py new n5k1` | 18.1 s | same key |
| 23:40:33 | CLI nelem 2, k = 1, internal, `-v 0`; compare with deflation run | 13.4 s | n_clock 6 = 6, dq_hhl max-abs diff 1.894e-12 |
| 23:41 | `scale_Ab` verbosity / branch probes | 1 s | no crash, wrapper identical |
| 23:42:10 | CLI nelem 2, k = 1, deflation, diag on, `-iters 2` | 12.9 s | per-step records |
| 23:43:16 | `python -W error::DeprecationWarning -m unittest tests.test_hhl_spectrum.TestSuppliedExactValuesSameCircuit tests.test_hhl_spectrum.TestDeflationSpectrumSolveNelem2` | 58.5 s | 8 OK |

Not run (over the 60 s single-run limit), for the operator:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

After the fork commit, rev bump and `uv lock && uv sync`, re-run the four
code-versions tests to confirm finding 1 clears:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
.venv/bin/python -m unittest tests.test_output_contract -k test_code_versions -v
```
