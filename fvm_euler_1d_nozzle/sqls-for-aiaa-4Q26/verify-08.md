VERDICT: PASS

# Verification of work item 8 (fvm Euler solver smoke tests)

- Verifier session: 2026-10-15T03:26:41Z to 2026-10-15T03:39Z (UTC), Apple silicon laptop.
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`, HEAD `5af4dd2f` (item-8 commit), parent `3a88a37d` (item 9), `d7658f6a` (item 7), base `main` @ `ef7f0a8b`.
- Stack confirmed from the venv: python 3.12.10, qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0, numpy 2.5.2, scipy 1.18.0. No pytest in the venv (`ModuleNotFoundError`); nothing installed; `uv` not run.
- Interpreter used throughout: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.
- Repo was never modified (no edit/add/commit/stash/checkout). Scratch under `/tmp/order1-verify-8/` (deleted at the end).
- Independent-by-design: I did not read any `build-*.md`, `verify-*.md`, `reproduce-*.md` or `STATUS.md`. I read `TESTING.md` (part of the deliverable), all of `tests/**`, and the solver code the tests claim to exercise.

Suite runs performed (3 of 3 allowed): Run 1 = full default discover under my own timing runner; Run 2 = opt-in gate module with `FVM_GATE_TESTS=1` under a runner that also prints the fixture max-abs errors; Run 3 = the exact TESTING.md default command. Plus short probes: 6 x 1.8 s CLI shots-mode runs, 5 x 0.01 s in-process item-9 solves, 1 x 6.8 s in-process HHL nelem-2 fixture solve.

## Criterion 1: tests/ exists, unittest-style, all green, per-test < 60 s, total reported -- PASS

Layout: `tests/__init__.py` present; 6 test modules `tests/test_{classical,sqls,hhl,cli,output_contract,gate_fixture}.py`; every test class subclasses `unittest.TestCase` via `tests.helpers.TimedTestCase`; mixins are underscore-prefixed non-TestCase classes (not collected on their own); all test methods `test_*`. pytest would collect these natively, but pytest was NOT executed (not in venv, install forbidden); collectability is reasoned from naming only.

Run 1 (2026-10-15T03:30:40Z to 03:31:24Z), my timing runner (`unittest.defaultTestLoader.discover('tests')`, `TextTestRunner(verbosity=2)` with a result class recording start/stop per test and the gap before each test, which captures `setUpClass` cost):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
/usr/bin/time -p .venv/bin/python /tmp/order1-verify-8/run_timed.py
-> n_tests=60 failures=0 errors=0 skipped=1 total_wall=43.2 s  (real 43.55 s, user 83.33 s, sys 5.20 s)
   max single test 8.13 s; max setUpClass gap 15.99 s (shared HHL nelem-2 CLI run)
   SKIPPED: test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference: gate-only (~90 s): set FVM_GATE_TESTS=1
```

Per-test wall (s), Run 1, all 60 (test-body time only; fixture cost listed separately below):

| s | test |
|---|---|
| 8.13 | test_gate_fixture.TestHHLFixture.test_nelem2_iter0_statevector_matches_reference |
| 3.82 | test_cli.TestCLIValidation.test_default_sqls_k_resolves_for_truncated_methods |
| 1.80 | test_cli.TestCLIValidation.test_explicit_valid_sqls_k_accepted |
| 1.02 | test_sqls.TestSQLSStatevectorNelem5.test_newton_trajectory_matches_lu |
| 0.79 | test_cli.TestCLIValidation.test_sqls_non_ideal_backend_fails_fast_with_real_cause |
| 0.39 | test_cli.TestCLIValidation.test_sqls_k_3_rejected_before_solve |
| 0.39 | test_cli.TestCLIValidation.test_sqls_k_equal_to_n_rejected |
| 0.34 | test_cli.TestCLIValidation.test_help_lists_all_linear_solvers |
| 0.34 | test_cli.TestCLIValidation.test_invalid_linsolver_rejected |
| 0.34 | test_cli.TestCLIValidation.test_sqls_k_128_rejected_before_solve |
| 0.02 | test_classical.TestLUNelem5Converges.test_steady_state_matches_august_archive |
| 0.01 | test_sqls.TestSQLSConvergedStepShots.test_fidelity_no_collapse_on_archived_iter6 |
| 0.01 | test_gate_fixture.TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference |
| 0.01 | test_gate_fixture.TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference |
| 0.01 | test_sqls.TestSQLSStatevectorNelem5.test_cx_count_and_depth_reported_at_verbosity_2 |
| 0.01 | test_sqls.TestSQLSStatevectorNelem5.test_fidelity_and_linsys_residual |
| 0.01 | test_sqls.TestSQLSShotsNelem2.test_fidelity_per_step |
| 0.01 | test_output_contract.TestSQLSOutputContract.test_common_csv_columns |
| 0.01 | test_output_contract.TestSQLSOutputContract.test_quantum_csv_columns |
| <= 0.005 each | the remaining 41 tests (classical x 6, sqls x 10, hhl x 4, output_contract x 14, gate_fixture x 3 provenance, cli x 0); every one of them reported 0.00 s |
| 0.00 (skipped) | test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference |

Fixture (`setUpClass`) gaps > 0.5 s, Run 1: 0.97 s before TestLUNelem2 (LU nelem 2 CLI run); 0.95 s before TestLUNelem5Converges; 15.99 s before TestHHLStatevectorNelem2 (HHL nelem-2 CLI run, cached and reused by TestHHLOutputContract); 1.90 s before TestSQLSOutputContract (SQLS statevector nelem-2 CLI run); 1.76 s before TestSQLSShotsNelem2; 1.91 s before TestSQLSStatevectorNelem5. GMRES nelem-3 run 1.16 s. Worst case attributable to any single test including its fixture: 8.13 s (default run) or 16 s + 0.00 s for the HHL class; both far under 60 s.

Run 3 (2026-10-15T03:37:38Z to 03:38:21Z), the exact TESTING.md command:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
/usr/bin/time -p .venv/bin/python -m unittest discover -s tests -v
-> Ran 60 tests in 42.670s / OK (skipped=1)   (real 42.98 s, user 82.70 s, sys 5.08 s)
```

The one skip is explicit (`@unittest.skipUnless(GATE, 'gate-only (~90 s): set FVM_GATE_TESTS=1')`), opt-in via `FVM_GATE_TESTS=1`, and documented in TESTING.md. A second, environment-conditional skip exists in code (`TestFixtureProvenance.test_archived_sources_unchanged` calls `self.skipTest` only when the experiments archive is absent); on this host the archive is present and the test ran (see Findings F1).

## Criterion 2: coverage with real assertions -- PASS

Read every test body. None is tautological; each item below is backed by an assertion that fails on a wrong value.

- (a) LU nelem 2 (3 steps) and GMRES nelem 3 (4 steps), `tests/test_classical.py` `_ClassicalMixin`: `assertGreaterEqual(n_steps, 3)`, `assertEqual(len(total), n_steps)`, `np.all(np.diff(residual_total) < 0)` (strict); sanity `assert_physical`: finite xp/rho/u/p/Mach, `rho > 0`, `p > 0`, `Mach > 1` on `final_results` and every per-step `results_*`; step-0 residual pinned to 1e-11 abs (1.3141049901831434 / 12.064020617099798). Also LU nelem 5 to convergence vs embedded August steady state at 1e-8 abs.
- (b) SQLS `-shots 0` nelem 2 and 5, `tests/test_sqls.py` `_StatevectorMixin`: per step `max|dq_sqls - dq_lu| <= 1e-12` with `len(dq_lu) == 3*nelem` guard; `fidelity >= 0.999999` with `len == n_steps` guard; `linsys_residual <= 1e-12`; qc_metadata `k == N//2` (item 7); nelem-5 step-0 system equals the archived August pickle to 1e-12 abs.
- (c) SQLS shots nelem 2, 10000 shots, `-sqls_repeats 1`, `TestSQLSShotsNelem2`: `fidelity >= 0.999` per step; `np.all(dq_sqls*dq_lu >= 0)` and strict `> 0` on dominant components (`|dq_lu| >= 0.1 ||dq_lu||`); `| ||dq_sqls||/||dq_lu|| - 1 | <= 0.05`; metadata `nshots == 10000`, `repeats == 1`.
- (d) HHL statevector nelem 2, 2 Newton steps, `tests/test_hhl.py`: `fidelity >= 0.98` both steps, `linsys_residual` finite and step 1 < step 0, `dq_hhl` vs `dq_lu` rel-L2 <= 5 %, circuit metadata (`matrix_size_herm == 16`, `nqubits == 4`, `circ_qubits_transpile == 12`, depth bounded).
- (e) CLI, `tests/test_cli.py`: `-sqls_k` 128 / 3 / 16 with truncated methods at nelem 5 -> non-zero exit, no solve artifact in outdir (7 globs), no `Traceback`, stderr matches `power of 2`, `k=<k>`, `N=16`. Verified in `nozzle_1d_solver.py` lines 215-227 that both `parser.error` calls (non-ideal backend; bad k) precede `os.makedirs(args.output_dir)` (line 238) and any solver construction, so "before any solve" is structural, and the `real-ibm` case never reaches runtime/network code. Default k resolves to 8 for `truncated_qr` and `truncated_mps` at nelem 5 (asserted from `qc_metadata_sqls_*.csv`); `-linsolver FOO` -> argparse exit 2 with `invalid choice`.
- (f) Output contract, `tests/test_output_contract.py` + `tests/contract.py`: exact file-set equality for SQLS nelem 2 (18 files incl. `metadata_*.pkl`, `hhl_metrics_*`, `qc_metadata_sqls_*`, `final_results_*`, `residual_*`, `results_*_iter{0,1,2}`, `dq_*_iter{0,1,2}`, `system_Ab_*`), HHL nelem 2 (18 files incl. `qc_metadata_nelem2_statevector.csv` and two `.qpy` per step) and LU; harvester singleton globs match exactly one file; exact column lists: SQLS `qc_metadata` 17 columns including `method, k, state_prep, repeats, n_data_qubits, m_ancilla, cx_count, circuit_depth, aer_device, solve_time`; HHL `qc_metadata` 21 columns including all `circ_*` and `matrix_size_herm`; `hhl_metrics` `fidelity, l2_error_abs, l2_error_rel, l2_error_normalized, linsys_residual`; metadata pkl 18 common keys + 4 quantum keys with value checks. The contract is exact-equality (not superset), which is stricter than required.

## Criterion 3: item-15 gate fixture -- PASS

Provenance: `tests/data/provenance.json` records source path, sha256 and date for the archived systems. I recomputed sha256 read-only:

```
7c2551de3f326b7aa493d8a8014f6ad880302cbcdcacb0f6c514c98f113b148f  .../2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter0.pkl  == tests/data/system_Ab_nelem5_iter0.pkl
6457ae08ce595691bc226f115c68b24f9b8f9f94c196c634564b6fd76994e25f  .../2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter6.pkl  == tests/data/system_Ab_nelem5_iter6.pkl
```
Both match provenance.json and the archive at `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`. The four `ref_*.npz` sha256 also match provenance.json. The three `*.pkl` are tracked despite `.gitignore`'s `*.pkl` (confirmed with `git ls-files tests/data`).

Same code as the solver: `tests/helpers.make_linsys_solver` constructs `time_solvers.LinearSystemSolver(space_solver, 1e-2, 1, scheme, linsolv_args)`; the CLI path is `BDFTimeSolver(space_solver, cfl, localdt, res_tol=1e-2, max_inner_iters=1, ...)` -> `ImplicitTimeSolver.__init__` -> `LinearSystemSolver(space_solver, convtol, maxiter, linsys_solver_type, linsolv_args)` with identical arguments (`-restol` default 1e-2, `-initers 1`). The test then calls `solver.hhl_solve(A, b, step=0)` / `sqls_solve` via `getattr`, i.e. the solver's own method, not a reimplementation. `hhl_scale_type='true_scale'` matches the CLI default, which is outside the argparse `choices=['true_sol','leastsq']` and therefore takes the least-squares branch in `hhl_solve` (time_solvers.py line 534 `else`), exactly as the CLI does. My in-process probe confirmed the object: `time_solvers.LinearSystemSolver`, `hhl_solver` = `QuantumHHL`, `hhl_scale_type` = `true_scale`, `steady_mode` = True.

Run 2 (2026-10-15T03:33:56Z to 03:35:42Z): `FVM_GATE_TESTS=1 /usr/bin/time -p .venv/bin/python /tmp/order1-verify-8/run_gate.py`, which loads `tests.test_gate_fixture` through `unittest.defaultTestLoader.loadTestsFromName` (equivalent to the TESTING.md command `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`) and additionally hooks `assertLessEqual`/`assertAlmostEqual` to print the compared values:

| test | wall | observed vs reference |
|---|---|---|
| TestHHLFixture.test_nelem5_iter0_statevector_matches_reference (gate) | 85.24 s | max-abs 4.441e-14 (tol 1e-10); fidelity diff 2.2e-16; residual diff 6.8e-14 (delta 1e-8) |
| TestHHLFixture.test_nelem2_iter0_statevector_matches_reference | 20.04 s | max-abs 8.882e-16; fidelity diff 2.2e-16; residual diff 3.6e-16 |
| TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference | 0.10 s | max-abs 0.0 |
| TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference | 0.01 s | max-abs 0.0 |
| TestFixtureProvenance x 3 | 0.00 to 0.03 s | sha256 all equal; archive present and unchanged |
| total | 105.4 s (real 106.41 s, user 242.47 s) | 7 run, 0 failed, 0 skipped |

Result: PASS, 85.24 s for the gate test (TESTING.md: 86.6 s). It is correctly gate-only (> 60 s) and TESTING.md says so, with the env var and the measured time.

Independent in-process probe (2026-10-15T03:36:32Z, 6.81 s): HHL nelem-2 solve on `system_Ab_nelem2_iter0.pkl` vs `ref_hhl_nelem2_iter0.npz` gives max-abs 9.437e-16, fidelity 0.9999986356113311 vs 0.9999986356113308.

Is the reference independent evidence? No, and it does not claim to be: `tests/make_fixtures.py` generates `ref_*.npz` by calling the same `helpers.make_linsys_solver(...).hhl_solve` at fvm commit `3a88a37d` on the recorded stack (provenance.json `fvm_commit`, `stack`, `sqls_commit 9a4346a7`, `wall_s 86.8`). It is a regression baseline of the code under test, which is what the item-15 gate needs (reproduce the pre-port HHL solution after the port); it cannot detect a pre-existing HHL bug. The only correctness cross-checks are the classical `dq_lu` stored alongside (checked to 1e-12 against `np.linalg.solve`) and HHL fidelity 0.99996 vs LU. `|dq|max` is 1.53 (nelem 5) and 0.44 (nelem 2), so 1e-10 abs is ~1e-10 relative.

Would it detect a 1e-9 change? Yes. Measured run-to-run reproducibility across processes is 4.4e-14 (nelem 5, one re-run) and 8.9e-16 / 9.4e-16 (nelem 2, two re-runs); the tolerance 1e-10 sits 2.3e3x above the noise and a 1e-9 change is 10x the tolerance, so it fails deterministically with no false-positive risk at the measured noise. The HHL transpile is seeded (`seed_transpiler=42`, quantum_tools.py line 440) and the statevector run is deterministic, consistent with the 1e-14 noise.

## Criterion 4: temp dirs only, clean git status, no network / Frontier / install -- PASS

Mechanism: `helpers.tmp_root()` = `tempfile.mkdtemp(prefix='fvm_tests_')` under `$TMPDIR` with `atexit.register(shutil.rmtree, ...)`; every CLI run gets `-outdir <mkdtemp under that root>`; in-process solvers get `output_dir` under the same root; `MPLBACKEND=Agg`. `QuantumSQLS.__init__` does `os.makedirs(output_dir)` only on that temp dir.

Checks after Run 1 and again after Run 3 (both at 2026-10-15T03:3xZ):
- `git status --short` -> empty.
- `git status --short --ignored` before vs after -> identical (`.venv/`, `__pycache__/`, `fvm_euler_1d_solver.egg-info/`, `output/`, `src/`, `tests/__pycache__/`; all pre-existing).
- `find output -type f -exec stat -f '%m %z %N'` before vs after -> identical (27 files, mtimes Sep 1); the repo `output/` directory was not touched.
- `find . -newer <pre-run snapshot>` excluding `.venv .git src` -> nothing.
- `ls -d $TMPDIR/fvm_tests_* $TMPDIR/run_* $TMPDIR/rejected_* /tmp/fvm_tests_*` -> none left.
- `__pycache__` dirs pre-existed (builder's runs); none new.
- Network: `grep -i 'requests|urllib|http|socket|QiskitRuntimeService' tests/*.py` -> none. The `-backend real-ibm` CLI case is rejected by `parser.error` before any runtime import; the in-process `QuantumSQLS(backend_type='fake')` raises in `get_backend` before `from qiskit_aer import AerSimulator`. Nothing installed; no `uv`.

All of the above was measured on a clean tree (`git status --short` empty at 2026-10-15T03:31:24Z after Run 1 and at 03:38:21Z after Run 3). At 03:41:30Z, after all runs were complete, four solver files appeared modified by a concurrent editor, not by the suite or by me; see F9.

## Criterion 5: diff scope, branch, TESTING.md -- PASS

- `git diff --name-only 3a88a37d 5af4dd2f | grep -v -E '^tests/|^TESTING.md$'` -> empty. 19 files, 1656 insertions, 0 deletions, all under `tests/**` plus `TESTING.md`.
- Commit `5af4dd2f` is HEAD of `feature/sqls-aiaa-4q26` (2026-10-14T23:23:59-04:00 = 2026-10-15T03:23:59Z). `git branch -r` lists no `origin/feature/sqls-aiaa-4q26`; not pushed.
- `TESTING.md`: gives the exact default and gate commands (both run as written / equivalently, above), expected wall times, per-module purpose table, and a "What each test pins" section with thresholds and observed values per test. Times vs mine: default 42.3 s documented vs 43.2 s and 42.98 s measured; gate module 94.7 s vs 105.4 s; nelem-5 gate test 86.6 s vs 85.24 s; HHL nelem-2 CLI run 16.3 s vs 16.0 s / 16.57 s; HHL nelem-2 fixture 8.0 s vs 8.13 s (Run 1) and 20.04 s (Run 2, see F6). All within a factor ~2 (the single 2.5x outlier is load-dependent and still < 60 s).

## Findings

Severity scale: High = would flip the verdict; Medium = should be fixed before relying on the suite; Low = cosmetic or hardening; Info = note for the record.

- F1 (Low) Environment-conditional skip and run-time read of the experiments tree. `tests/test_gate_fixture.py` lines 46-57 `test_archived_sources_unchanged` reads `prov['systems'][*]['source']` (absolute paths under `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/...`) and skips with `self.skipTest(...)` when none exists. It is explicit and TESTING.md documents it ("when the experiments tree is present on the host"), and on this host it ran and passed, but it is not an opt-in gate skip, and it is the only test with a hidden external dependency (a soft one: absence -> skip, not pass). Everything the suite asserts on otherwise comes from `tests/data/` or embedded constants (`AUGUST_FINAL_NELEM5`, `INITIAL_RESIDUAL`).
- F2 (Low) Shots-mode sign and norm checks are structural, not statistical. In `sqls_solve` the magnitude is restored classically from `||final_b||` and the signs from the classical reference, so `||dq_sqls||/||dq_lu||` is identically 1.000000000 (12/12 probe samples) and `dq_sqls*dq_lu >= 0` cannot be violated by sampling. They still pin that the restoration code is present, so they count as real assertions, but the 5 % tolerance is not exercising sampling noise. The only truly sampled quantity is fidelity.
- F3 (Low) Flakiness margin of the unseeded shots tests. Six extra CLI runs of the (c) case: step-0 fidelity 0.999809 to 0.999953, step-1 0.999893 to 0.999958 (12 samples; infidelity 4.2e-5 to 1.9e-4; threshold infidelity 1e-3, i.e. >= 5x margin on the worst sample, ~9x on the mean). Five in-process item-9 solves on archived iter 6: fidelity 0.999611 to 0.999846 vs floor 0.99 (>= 25x margin). With ~7 effective degrees of freedom the chance of a sample exceeding 9x the mean is far below 1e-6 per solve; the TESTING.md estimate of ~1e-4 per solve is conservative. No test depends on test ordering: the CLI run cache is populated lazily in `setUpClass`, so each module also runs standalone; the only wall-time-dependent assertions are `solve_time > 0` and `circ_*_time > 0` (quantum_tools.py measures with `time.time()` differences; observed values ms or larger, so a 0.0 would require a coarse clock).
- F4 (Low) PEP 8 deviations: function-local imports in `tests/helpers.py` lines 181-183, 212-213 and `tests/test_sqls.py` lines 209, 222 (repo modules imported after the `sys.path.insert` at helpers import, and to keep qiskit out of CLI-only test processes). Defensible, but not top-of-module. All `tests/*.py` lines are <= 88 chars (max exactly 88), no trailing whitespace, no tabs. `TESTING.md` has 13 lines > 88 chars (table rows and absolute paths; Markdown, not code).
- F5 (Low) Per-test guards. `TestSQLSStatevectorNelem5.test_cx_count_and_depth_reported_at_verbosity_2` uses `np.all(...)` on `cx_count`/`circuit_depth` without asserting the array length in the same test; an empty `qc_metadata_sqls_*.csv` would pass this one test alone (`np.all([])` is True), though the sibling `test_qc_metadata_values` in the same class asserts `qc['method'] == ['full_svd']*3` and would fail. Similarly `TestFixtureProvenance.test_fixture_files_match_recorded_sha256` checks every provenance entry against disk but not that every file in `tests/data/` has a provenance entry.
- F6 (Info) Timing variance. In Run 2 the nelem-2 HHL fixture took 20.04 s vs 8.13 s in Run 1 and 8.0 s documented, while the 85 s gate test matched to 2 %; another agent was active on this machine during the session, so this reads as load, not a code issue. Worst case remains well under 60 s.
- F7 (Info) The stored references are a self-generated regression baseline (same code, same stack, fvm `3a88a37d`), appropriate for the item-15 before/after gate but not independent evidence of HHL correctness (see Criterion 3). The `make_fixtures.py` regenerator hard-codes the archive path and the local `sqls` checkout path; it is not run by the suite.
- F8 (Info) TESTING.md states "pytest collects them natively" and gives `pytest tests -q`; this was not executed by the builder or by me (no pytest in the venv). Collection is plausible from the naming (`test_*.py`, `Test*` classes subclassing `TestCase`, `test_*` methods, `tests/__init__.py`), but unverified.
- F9 (Info, outside item 8) Concurrent working-tree edits during verification. At 2026-10-15T03:41:30Z `git status --short` showed ` M math_tools.py`, ` M nozzle_1d_solver.py`, ` M quantum_tools.py`, ` M time_solvers.py` (all mtime 2026-10-15T03:40:28Z; `git diff --stat` 4 files, 74 insertions, 31 deletions). The tree was clean after each of my three suite runs (last at 03:38:21Z), the suite writes only to `$TMPDIR/fvm_tests_*`, and I made no edits, so this is another agent working in the same checkout (a `code-review` agent is active in this session). Content: the item-7 `-sqls_k` rule moved into a new `math_tools.resolve_sqls_k(k, n, method)` and reused by `QuantumSQLS`; a new `parser.error` when SQLS is given a non-`statevector` backend method; the `SQLS: N=... k=...` print gated on `-v >= 1`; new metadata keys `converged`, `converged_by`, `resnorm_init`; `QuantumSQLS.solve_one_step` returns zeros without a circuit when `b == 0`; a comment in `LinearSystemSolver`. Verdict scope: this report verifies commit `5af4dd2f` as committed; the suite was NOT re-run against the modified tree (3-run budget spent, and the edits are not part of item 8). Reasoned impact if these edits are committed: the `test_cli` regexes (`power of 2`, `\bk\s*[=:]?\s*128\b`, `\bN\s*[=:]?\s*16\b`) still match the new message `-sqls_k: SQLS method='truncated_qr' requires k to be a power of 2 with 2 <= k < N; got k=128, N=16 (...)`; the metadata contract uses `assertIn` for the common keys, so three extra keys pass; no test uses an SQLS backend method other than `statevector` or a zero RHS through the CLI. Likely green, but unverified; re-run `.venv/bin/python -m unittest discover -s tests -v` after those edits land.

## Not checked, and why

- pytest collection/run: pytest is not in the venv and installing is out of scope. Reasoned from naming only.
- The skip path of `test_archived_sources_unchanged` on a host without the experiments archive: not exercised (archive present here; I did not move files).
- nelem-5 HHL reproducibility beyond one re-run (4.44e-14): a second re-run would cost another ~85 s solver run, outside the 3-run budget and the < 10 s probe allowance. The nelem-2 fixture was re-run twice (8.9e-16, 9.4e-16).
- The fidelity-collapse "before" value for item 9 (0.451 claimed in TESTING.md) was not reproduced; that is item-9 territory, not item 8. The "after" value was (0.9996 to 0.9998).
- Behavior on other mesh nodes (Linux, different CPU) and on qiskit 3.x: not applicable to this verification.

## Scratch

`/tmp/order1-verify-8/` (runner scripts, raw run logs, probe outputs, snapshots) deleted at 2026-10-15T03:39Z after this file was written. No other file in this folder was created or modified.
