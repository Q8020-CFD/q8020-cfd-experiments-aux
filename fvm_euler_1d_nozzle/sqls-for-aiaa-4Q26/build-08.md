# build-08: smoke/regression test suite for fvm_euler_1d_solver

Builder B, work-plan item 8. Written 2026-10-15T03:30Z.

Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26` (from main @ `ef7f0a8b`). Builder A's items 7 and 9
landed on the branch before the suite was run (`d7658f6a`, `3a88a37d`); all
tests below were executed against that state. New files only: `tests/**` and
`TESTING.md`; no existing module touched.

## Run command and result

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
.venv/bin/python -m unittest discover -s tests -v
```

Result (2026-10-15T03:20Z, laptop, macOS 26.7.1 arm64; stack python 3.12.10,
numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime
0.49.0, quantum_linear_solvers 0.1.0 = fork `66eadf0`, sqls 0.1.0 @ `9a4346a7`):

```
Ran 60 tests in 42.262s
OK (skipped=1)
```

Process wall 42.6 s (`/usr/bin/time`). 59 pass, 1 skipped by design (the
gate-only nelem-5 HHL fixture). A first run before two tolerance fixes
(below) took 43.7 s. No single test exceeds 60 s; the longest shared solver
run is the nelem-2 HHL CLI run at 16.3 s (run once per process, consumed by
`test_hhl` and `TestHHLOutputContract`).

Gate (opt-in):

```
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

```
Ran 7 tests in 94.728s
OK
```

`TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`: 86.6 s,
PASS (max-abs vs reference within 1e-10; reproducibility measured at 1.0e-14
between two independent solves).

`git status` after both runs: only the new `tests/` tree (untracked before the
commit); temp dirs (`fvm_tests_*` under `$TMPDIR`) removed at exit. No
network, no Frontier, no install; the venv was not modified.

## Test inventory

Wall times are the per-test `[wall]` prints from the 2026-10-15T03:20Z run.
Tests marked "shared run" assert on a CLI run performed once in `setUpClass`
(cached by argument list); that run's time is listed separately.

### `tests/test_classical.py` (a)

| Test | Pins | Wall |
|---|---|---|
| `TestLUNelem2.test_residual_strictly_decreasing` | LU nelem 2, 3 steps: `residual_total` strictly decreasing, per-equation residuals finite | 0.00 s (shared run 0.96 s) |
| `TestLUNelem2.test_initial_residual_is_solver_independent` | step-0 residual = 1.3141049901831434 +- 1e-11 | 0.00 s |
| `TestLUNelem2.test_solution_physical_and_finite` | final + per-step results finite, rho > 0, p > 0, Mach > 1 | 0.00 s |
| `TestGMRESNelem3.*` (3 tests) | same for GMRES nelem 3, 4 steps; step-0 residual 12.064020617099798 | 0.00 s (shared run 1.14 s) |
| `TestLUNelem5Converges.test_converges_before_max_iters` | nelem 5 LU converges in < 15 steps (6), final/initial < 1e-10 (1.7e-14), step-0 residual = August 12.375368413827264 | 0.00 s (shared run 0.92 s) |
| `TestLUNelem5Converges.test_steady_state_matches_august_archive` | `final_results` = August SQLS trial steady state to 1e-8 abs (observed 2e-11) | 0.02 s |

### `tests/test_sqls.py` (b), (c), item 9

| Test | Pins | Wall |
|---|---|---|
| `TestSQLSStatevectorNelem2.test_dq_matches_lu_per_step` | dq_sqls vs dq_lu <= 1e-12 abs, 3 steps (observed <= 5e-16) | 0.00 s (shared run 1.80 s) |
| `TestSQLSStatevectorNelem2.test_fidelity_and_linsys_residual` | fidelity >= 0.999999 (1.0), linsys_residual <= 1e-12 (1.5e-15), l2_error_abs <= 1e-12 | 0.00 s |
| `TestSQLSStatevectorNelem2.test_qc_metadata_values` | full_svd, k = N//2 = 4 (item 7), repeats 1, pow2 8, nqubits 3, m_ancilla 0 | 0.00 s |
| `TestSQLSStatevectorNelem2.test_newton_trajectory_matches_lu` | residual history vs LU rtol 1e-5 (6.2e-7), final state 1e-8 abs (3e-12) | 0.00 s (LU run cached) |
| `TestSQLSStatevectorNelem5.test_dq_matches_lu_per_step` | as above at nelem 5 (observed 4.8e-15) | 0.00 s (shared run 1.87 s, `-v 2`) |
| `TestSQLSStatevectorNelem5.test_fidelity_and_linsys_residual` | fidelity 1.0, linsys_residual 4.8e-14 <= 1e-12 | 0.00 s |
| `TestSQLSStatevectorNelem5.test_qc_metadata_values` | k = 8 (item 7), pow2 16, nqubits 4 | 0.00 s |
| `TestSQLSStatevectorNelem5.test_newton_trajectory_matches_lu` | rtol 1e-5 (1.3e-7), final 1e-8 abs (4.7e-10) | 0.94 s (runs LU nelem 5, 3 steps) |
| `TestSQLSStatevectorNelem5.test_step0_system_matches_august_archive` | solver's `system_Ab_nelem5_iter0.pkl` = archived August system to 1e-12 (observed 0.0) | 0.00 s |
| `TestSQLSStatevectorNelem5.test_cx_count_and_depth_reported_at_verbosity_2` | cx_count in [150, 260] (200-201), circuit_depth in [300, 500] (397-398), aer_device CPU | 0.01 s |
| `TestSQLSShotsNelem2.test_fidelity_per_step` | 10000 shots, repeats 1, 2 steps: fidelity >= 0.999 (0.99994, 0.99986) | 0.01 s (shared run 1.72 s) |
| `TestSQLSShotsNelem2.test_sign_and_norm_recovery` | dq_sqls*dq_lu >= 0, strict on dominant components, norm ratio within 5 % (1.000000) | 0.00 s |
| `TestSQLSShotsNelem2.test_shots_suffix_in_file_names` | `_nshots10000` / `_shots10000` names, metadata nshots and repeats | 0.00 s |
| `TestSQLSConvergedStepShots.test_fidelity_no_collapse_on_archived_iter6` | item 9: archived iter-6 system (||b|| 1.26e-9), 10000 shots in-process, fidelity >= 0.99 (0.9996; 0.451 before the fix) | 0.01 s |
| `TestSQLSConvergedStepShots.test_convert_to_pow2_padding` | default pad 1e-8 unchanged (HHL), `eps=0.0` pads exact zeros, A unchanged | 0.00 s |
| `TestSQLSConvergedStepShots.test_non_ideal_backend_raises_real_cause` | `QuantumSQLS(backend_type='fake')` raises ValueError naming `ideal` | 0.00 s |

### `tests/test_hhl.py` (d)

| Test | Pins | Wall |
|---|---|---|
| `TestHHLStatevectorNelem2.test_runs_and_writes_metrics` | 2 steps, fidelity >= 0.98 (0.9999986, 0.99996), linsys_residual finite and decreasing | 0.00 s (shared run 16.27 s) |
| `TestHHLStatevectorNelem2.test_dq_close_to_lu` | rel L2 <= 5 % (0.18 %), dominant signs agree | 0.00 s |
| `TestHHLStatevectorNelem2.test_circuit_metadata` | sizes 6/8/16, nqubits 4, circ_qubits_transpile 12, lambda_max_scaled 1, depth in (0, 200000) (68963), timings > 0 | 0.00 s |
| `TestHHLStatevectorNelem2.test_newton_residual_decreases` | residual_total decreasing from 1.3141049901831434; final physical | 0.00 s |

### `tests/test_cli.py` (e), item 7

| Test | Pins | Wall |
|---|---|---|
| `test_sqls_k_128_rejected_before_solve` | truncated_qr nelem 5: non-zero exit, no artifacts, message has `power of 2`, `k=128`, `N=16` | 0.39 s |
| `test_sqls_k_3_rejected_before_solve` | truncated_mps, `k=3`, `N=16` | 0.40 s |
| `test_sqls_k_equal_to_n_rejected` | `k=16` rejected (k < N) | 0.40 s |
| `test_default_sqls_k_resolves_for_truncated_methods` | truncated_qr and truncated_mps run with no `-sqls_k`; qc_metadata k 8, pow2 16, n_data_qubits 4 | 3.95 s |
| `test_explicit_valid_sqls_k_accepted` | `-sqls_k 4` recorded as 4 | 1.89 s |
| `test_sqls_non_ideal_backend_fails_fast_with_real_cause` | `fake fake_manila`, `real-ibm ibm_brisbane`: fail before solve, message names `ideal` + backend type, no `install`, no `not initialized` | 0.69 s |
| `test_invalid_linsolver_rejected` | `-linsolver FOO`: exit 2, `invalid choice` | 0.39 s |
| `test_help_lists_all_linear_solvers` | `-h` mentions LU, GMRES, HHL, SQLS, `-sqls_k` | 0.35 s |

### `tests/test_output_contract.py` (f)

| Test | Pins | Wall |
|---|---|---|
| `TestSQLSOutputContract.test_exact_file_set` | SQLS nelem 2 x 3 steps writes exactly the 18 files of `contract.expected_files` | 0.00 s (shared SQLS run) |
| `TestSQLSOutputContract.test_harvester_globs_unambiguous` | 5 singleton globs match 1 file each; 2 per-iteration globs match 3 files with iter 0..2 | 0.00 s |
| `TestSQLSOutputContract.test_common_csv_columns` | results/final_results/residual headers, `iters` = 0..2 | 0.00 s |
| `TestSQLSOutputContract.test_quantum_csv_columns` | hhl_metrics 7 columns, dq `dq_lu, dq_sqls`, per-step results header | 0.00 s |
| `TestSQLSOutputContract.test_qc_metadata_sqls_columns_and_values` | file `qc_metadata_sqls_nelem2_full_svd.csv`, 17 SQLS columns; metadata `quantum_circuit` method/k/state_prep/repeats = full_svd/4/initialize/1 | 0.00 s |
| `TestSQLSOutputContract.test_metadata_pickle` | 18 common keys + 4 quantum keys with values; `final_residual` = last residual_total; `quantum_circuit` keys exact | 0.00 s |
| `TestSQLSOutputContract.test_system_pickles` | `{A, b}` shapes (6, 6) / (6,) | 0.00 s |
| `TestHHLOutputContract.*` (7 tests) | same for HHL nelem 2 x 2 steps: 18 files incl. 2 x 2 `.qpy`, `qc_metadata_nelem2_statevector.csv` with the 21 HHL columns, dq `dq_lu, dq_hhl`, `quantum_circuit` keys backend_type/backend_method/use_gpu | 0.00-0.01 s (shared HHL run) |
| `TestLUOutputContract.*` (3 tests) | LU nelem 2 x 3: 7 files, headers, metadata without quantum keys | 0.00 s |

### `tests/test_gate_fixture.py` (item-15 gate)

| Test | Pins | Wall |
|---|---|---|
| `TestFixtureProvenance.test_fixture_files_match_recorded_sha256` | every `tests/data` file matches `provenance.json` | 0.00 s |
| `TestFixtureProvenance.test_archived_sources_unchanged` | archived source pickles unchanged (skips if the experiments tree is absent) | 0.00 s |
| `TestFixtureProvenance.test_systems_are_well_posed` | shapes (15, 15)/(15,), cond < 200; nelem-2 system (6, 6) | 0.00 s |
| `TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference` | `sqls_solve` on archived iter 0 = reference to 1e-10 max-abs; fidelity/residual to 1e-8; LU to 1e-12 | 0.01 s |
| `TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference` | same on the nelem-2 system | 0.01 s |
| `TestHHLFixture.test_nelem2_iter0_statevector_matches_reference` | `hhl_solve` on the nelem-2 system = reference to 1e-10 (default suite) | 8.02 s |
| `TestHHLFixture.test_nelem5_iter0_statevector_matches_reference` | `hhl_solve` on archived iter 0 = reference to 1e-10; **gate-only, `FVM_GATE_TESTS=1`** | 86.60 s (skipped in the default suite) |

## Tests that depend on items 7 and 9, and their state

Item 7 (`d7658f6a`): all 8 tests in `test_cli.py`; `test_qc_metadata_values`
(k = N//2) in both statevector classes of `test_sqls.py`;
`TestSQLSOutputContract.test_qc_metadata_sqls_columns_and_values` (k = 4);
`TestSQLSConvergedStepShots.test_non_ideal_backend_raises_real_cause`.
Item 9 (`3a88a37d`): `TestSQLSConvergedStepShots.test_fidelity_no_collapse_on_archived_iter6`
and `test_convert_to_pow2_padding`. State: all PASS on the branch as of
2026-10-15T03:20Z. Not weakened, not marked expected-failure. Verified
behaviour of builder A's messages: `-sqls_k must be a power of 2 with
2 <= k < N for -sqls_method truncated_qr; got k=128, N=16 (nelem=5, ...)`,
exit 2 via `parser.error`, output dir not even created; `-linsolver SQLS
supports only '-backend ideal' (Aer statevector/shots); got '-backend fake'`.

## Fixture provenance

| File | sha256 | Source |
|---|---|---|
| `tests/data/system_Ab_nelem5_iter0.pkl` | `7c2551de3f326b7aa493d8a8014f6ad880302cbcdcacb0f6c514c98f113b148f` | verbatim copy of `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter0.pkl` (2026-08-17; bit-identical to the HHL trial's `2026-08-17-qiskit25-local/trial_0/system_Ab_nelem5_iter0.pkl`) |
| `tests/data/system_Ab_nelem5_iter6.pkl` | `6457ae08ce595691bc226f115c68b24f9b8f9f94c196c634564b6fd76994e25f` | verbatim copy of `.../2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter6.pkl` (the converged step, ||b|| = 1.26e-9) |
| `tests/data/system_Ab_nelem2_iter0.pkl` | `b0354a9d8a3dcd832b051c8cf0b28043ea328ba4184ea95e246c39d5cb5ce631` | written by `nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 0 -iters 1 -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow` on 2026-10-15T03:09:07Z at fvm `3a88a37d` |
| `tests/data/ref_hhl_nelem5_iter0.npz` | in `provenance.json` | `LinearSystemSolver.hhl_solve` (ideal statevector, `hhl_scale_type='true_scale'` = least-squares branch as the CLI default) on iter 0; fidelity 0.999957137763, ||A dq - b|| 4.207e-2; 86.8 s; generated 2026-10-15T03:10:42Z |
| `tests/data/ref_hhl_nelem2_iter0.npz` | in `provenance.json` | same on the nelem-2 system; fidelity 0.999998635611, residual 3.352e-3; 6.8 s |
| `tests/data/ref_sqls_nelem5_iter0.npz` | in `provenance.json` | `LinearSystemSolver.sqls_solve` full_svd statevector; fidelity 1.0, residual 4.76e-14 |
| `tests/data/ref_sqls_nelem2_iter0.npz` | in `provenance.json` | same; fidelity 1.0, residual 1.47e-15 |

Stack at generation: python 3.12.10, numpy 2.5.2, scipy 1.18.0, qiskit 2.5.2,
qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0, quantum_linear_solvers 0.1.0
(fork `66eadf0` per `uv.lock`), sqls 0.1.0 @ `9a4346a7`
(`/Users/agallojr/proj/src/q8020/sqls`, editable), fvm `3a88a37d`. Recorded by
`tests/make_fixtures.py` in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/tests/data/provenance.json`.
The pickles are force-added (`git add -f`) because the repo `.gitignore`
ignores `*.pkl`; `.npz`/`.json` are not ignored.

## Findings along the way

- Report 03 sec. 5.3 rung 2 says the nelem-5 LU residual history should match
  the August SQLS run "to ~1e-14: 12.375 -> 0.761 -> 0.0710". That August run
  was in 150000-shot mode, so its trajectory is not LU's: LU today gives
  12.375368413827264 -> 0.5687 -> 0.0583 -> ... -> 2.1e-13 at step 5. The
  step-0 residual and the step-0 system do match August exactly (0.0
  difference), and the converged steady state matches to 2e-11. The suite pins
  those, not the shot-noise trajectory.
- Rung 3's "final residual_total matches LU to 1e-10" is also optimistic: with
  dq equal to 1e-15, the FD Jacobian roundoff (eps ~ 1.5e-8, cond 40-70) makes
  the next residual differ by ~1e-7 relative (measured 6.2e-7 at nelem 2,
  1.3e-7 at nelem 5). The suite uses rtol 1e-5 for the trajectory and keeps the
  per-step dq pin at 1e-12.
- HHL on the nelem-5 system is deterministic to 1.0e-14 across solves on this
  stack (no coupling map, so the transpiler is deterministic without a seed).
- Rung 4's wall estimate (30-80 s for 2 HHL steps at nelem 2) was high: 16.3 s
  (generate 1.9 s, transpile 1.7 s, statevector 3.2 s per step; 12 qubits,
  depth 68963, 74824 gates).
- `-hhl_scale` default `true_scale` is not in its argparse choices (report 04
  finding 12), so the CLI always takes the least-squares branch; the HHL
  fixtures select that branch explicitly, so they do not move if the default is
  later corrected.

## Open doubts

- Shots-mode assertions are statistical (no seed in the solver). The 0.999
  fidelity floor at 10000 shots is ~6x the expected infidelity 1.75e-4 (8
  amplitudes); estimated flake rate ~1e-4 per solve. The converged-step test
  uses 0.99 at 16 amplitudes (observed 0.9996). If a flake ever appears, the
  cure is a seed on `SamplerV2`/Aer in the solver, not a looser bound.
- The SQLS cx/depth pin ([150, 260] / [300, 500] at N = 16 with `-v 2`) is a
  qiskit-synthesis property; a qiskit (not runtime) bump could move it. It is
  intentionally loose and documented; item 3 bumps only the runtime.
- pytest collection was not exercised (no pytest in the venv; I did not run
  `uv run --with pytest` to keep the venv and the network untouched). The
  modules are plain `unittest.TestCase` subclasses in `test_*.py` with
  underscore-prefixed non-TestCase mixins, which pytest collects natively.
- Truncated SQLS runs at nelem 5 emit `RuntimeWarning: invalid value
  encountered in sqrt` from `space_solvers.py:113/175` (the rank-8 update is
  inexact, fidelity 0.9675, so a primitive goes negative for that step). The
  CLI tests assert only completion and `k` resolution; whether truncated
  methods should be allowed to drive the Newton loop at all is a design
  question for items 6/11, not pinned here.
- The 60 s per-test budget is measured on this laptop with a concurrent
  builder active at the start of the session; a slower node would see the
  16 s HHL run and the 8 s HHL fixture scale up but stay well inside 60 s.

## Commits

`git log --oneline main..feature/sqls-aiaa-4q26` at 2026-10-15T03:40Z:

```
5af4dd2f Add unittest regression suite and gate fixtures for LU GMRES HHL SQLS paths   (builder B, item 8)
3a88a37d SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse     (builder A, item 9)
d7658f6a SQLS: default sqls_k to N//2, validate k and ideal backend early, narrow import except   (builder A, item 7)
```

`5af4dd2f` adds 19 files, 1656 insertions, all under `tests/` plus
`TESTING.md`; no existing module changed. Not pushed. Working tree clean;
scratch under `/tmp/b8` and `$TMPDIR/fx_*` removed.


## Fix-up round (code review findings)

Builder B, fix-up round. Written 2026-10-15T04:12Z. One new commit `f16720b3`
on `feature/sqls-aiaa-4q26` (parent: the solver fix-up `71c02aed`); 9 files,
468 insertions, 53 deletions, all under `tests/**` plus `TESTING.md`. No solver
module touched; nothing pushed; no new binaries in `tests/data/`.

### What changed (file:line)

Review findings:

- R9 (interpreter mismatch): `tests/helpers.py:42` now sets `PYTHON =
  sys.executable`; the `.venv/bin/python` lookup (old `VENV_PY`) is gone. CLI
  subprocesses and in-process tests therefore share the interpreter that
  launched unittest by construction. Chosen over the import-time realpath
  assertion as the simpler option with no failure mode of its own; the rule
  "launch with the repo venv" is stated in `TESTING.md` (Run section and
  Notes). A launch under another Python fails loudly anyway: `tests/helpers.py`
  imports `time_solvers` at module top, so collection stops on the first
  missing package.
- R10 (function-local imports): all gone (`grep -n "^\s\+import \|^\s\+from
  .* import" tests/*.py` is empty). The `sys.path` insertion moved from
  `tests/helpers.py` into `tests/__init__.py:14` so it runs when the `tests` package
  is imported, before any solver import; `helpers.py` then imports
  `math_tools`, `case.SimCase`, `mesh.Mesh`, `space_solvers.SpaceSolver`,
  `time_solvers.LinearSystemSolver` at `tests/helpers.py:30` (local group,
  after numpy) and `make_space_solver` / `make_linsys_solver`
  (`tests/helpers.py:191`, `tests/helpers.py:218`) use them directly.
  `tests/test_sqls.py` imports `math_tools` and `quantum_tools` at
  `tests/test_sqls.py:21` (used by `tests/test_sqls.py:301` and `tests/test_sqls.py:315`);
  `tests/test_cli.py` imports `math_tools` at `tests/test_cli.py:22`. Local-group
  order is `from tests ...` first, then the solver modules, with a one-line
  comment saying why.

New behaviour pinned (fvm `71c02aed`):

- N1 backend method: `tests/test_cli.py:113` (`-backend ideal density_matrix` -> rc 2,
  stderr names `statevector` and `density_matrix`, stdout empty, no solve
  artifact); `tests/test_cli.py:126` (`-backend ideal statevector` spelled out runs,
  metadata `backend_method` statevector, one banner).
- N2 k rule: `tests/test_cli.py:168` `TestResolveSqlsK`, 5 unit tests on
  `math_tools.resolve_sqls_k` and `SQLS_TRUNCATED_METHODS`. Also
  `tests/test_cli.py:47` `_assert_k_message` now takes the method and asserts the CLI
  stderr embeds the canonical in-process message verbatim (the CLI wraps the
  shared rule); the three existing `-sqls_k` tests pass it.
- N3 `-v` banner: `tests/test_cli.py:149` `TestSQLSVerbosityBanner`: a new nelem-2
  `-iters 1 -v 0` run has no `SQLS: N=` line on stdout or stderr and still
  writes its outputs; the cached default `-v 1` nelem-2 run prints exactly one
  (`SQLS: N=8 (padded), k=4, method=full_svd`). `tests/test_sqls.py:153` adds that the
  `-v 2` nelem-5 run also prints it once.
- N4 zero RHS: `tests/test_sqls.py:323` `TestSQLSZeroRHS`: `LinearSystemSolver.sqls_solve
  (A, zeros(15))` at shots 0 and 10000 returns a (15,) all-zero update, metrics
  fidelity 1.0 and all four errors 0.0, no `qc_metadata*` file (no circuit),
  `dq_*.csv` with both columns zero and the `system_Ab_*.pkl` written;
  `QuantumSQLS.solve_one_step` directly returns zeros, leaves the dir empty and
  still resolves `k` to 8.
- N5 convergence metadata: `tests/contract.py:47` adds `converged`,
  `converged_by`, `resnorm_init` to `METADATA_KEYS_COMMON` (21 keys, in the
  solver's dict order) and `tests/contract.py:54` `CONVERGED_BY_VALUES`.
  Values: capped runs in `tests/test_output_contract.py:73` (all three contract runs: `converged`
  False, `converged_by` None, `resnorm_init` float equal to residual row 0 to
  1e-12) and `tests/test_sqls.py:153` (nelem-5 `-iters 3`); converging runs in
  `tests/test_classical.py:134` (existing LU nelem-5 `-iters 15`: True, `'residual_ratio'`,
  `resnorm_init` 12.375368413827264 to 1e-9) and the new SQLS nelem-5
  `-shots 0 -iters 15` run, `tests/test_sqls.py:168` `TestSQLSStatevectorNelem5Converges`
  (4 tests, below). The LU nelem-5 args moved to `tests/helpers.py:60` so both
  modules share one cached run; the SQLS converging args are
  `tests/helpers.py:62`.
- N6 messages: no existing test pinned the old `... solver not initialized`
  strings positively (only `assertNotIn`, still valid) or the old in-process k
  message; nothing to update. The new strings are pinned instead:
  `tests/test_sqls.py:366` (`SQLS back-end unavailable: <ImportError>` + `pip install
  -e ../sqls --no-deps`) and `tests/test_hhl.py:81` (`HHL back-end unavailable:` +
  `linear_solvers` + `uv sync`), both in-process by clearing the solver
  attribute and setting `qsolver_import_error` as the constructor does; the
  `no trailing period` property of the k message is asserted in `TestResolveSqlsK`.

### New tests (19; 60 -> 79)

| Test | Pins | Wall |
|---|---|---|
| `test_cli.TestCLIValidation.test_sqls_density_matrix_backend_rejected` | N1 reject, rc 2, no artifact | 0.39 s |
| `test_cli.TestCLIValidation.test_sqls_explicit_statevector_backend_accepted` | N1 accept, metadata backend_method | 1.77 s (own CLI run) |
| `test_cli.TestSQLSVerbosityBanner.test_v0_prints_no_banner` | N3, `-v 0` silent, outputs written | 1.72 s (own CLI run) |
| `test_cli.TestSQLSVerbosityBanner.test_default_v1_prints_banner_once` | N3, one banner, exact text | 1.92 s (first use of the cached nelem-2 SQLS run) |
| `test_cli.TestResolveSqlsK.test_truncated_methods_constant` | N2 constant | 0.00 s |
| `test_cli.TestResolveSqlsK.test_default_k_is_half_n_for_every_method` | N2 None -> n // 2, 3 methods x N 8/16/32 | 0.00 s |
| `test_cli.TestResolveSqlsK.test_valid_powers_of_two_accepted_for_truncated_methods` | N2 k 2/4/8 at N 16 | 0.00 s |
| `test_cli.TestResolveSqlsK.test_invalid_k_rejected_for_truncated_methods` | N2 k 128/3/16/1/0 -> ValueError text, no period | 0.00 s |
| `test_cli.TestResolveSqlsK.test_full_svd_never_validates_k` | N2 full_svd passthrough | 0.00 s |
| `test_sqls.TestSQLSStatevectorNelem5.test_capped_run_metadata_not_converged` | N5 capped values, N3 `-v 2` once | 0.00 s (cached run) |
| `test_sqls.TestSQLSStatevectorNelem5Converges.test_converges_before_max_iters` | SQLS nelem 5 converges (6 rows, 1.55e-14) | 0.00 s (1.84 s CLI run in setUpClass) |
| `test_sqls.TestSQLSStatevectorNelem5Converges.test_metadata_records_convergence` | N5 True / residual_ratio / resnorm_init / file set | 0.00 s |
| `test_sqls.TestSQLSStatevectorNelem5Converges.test_same_stopping_point_and_steady_state_as_lu` | same final_iters, converged_by, state 1e-8 | 0.00 s (LU run cached) |
| `test_sqls.TestSQLSStatevectorNelem5Converges.test_fidelity_holds_on_the_converged_tail` | fidelity >= 0.999999 down to b ~ 1e-13 | 0.00 s |
| `test_sqls.TestSQLSZeroRHS.test_sqls_solve_returns_zero_update` | N4 via `sqls_solve`, shots 0 and 10000 | 0.01 s |
| `test_sqls.TestSQLSZeroRHS.test_solve_one_step_returns_zeros_without_circuit` | N4 via `solve_one_step`, k resolved | 0.00 s |
| `test_sqls.TestSQLSBackendUnavailableMessage.test_sqls_solve_names_import_error_and_hint` | N6 SQLS message | 0.00 s |
| `test_hhl.TestHHLBackendUnavailableMessage.test_hhl_solve_names_import_error_and_hint` | N6 HHL message | 0.00 s |
| `test_classical.TestLUNelem5Converges.test_metadata_records_convergence` | N5 LU converging values | 0.00 s (cached run) |

Existing tests extended in place (no new test id): the three
`test_metadata_pickle` (contract mixin, capped values) and the three
`-sqls_k` rejection tests (canonical message embedded).

### Suite results (verbatim)

Default suite, started 2026-10-15T03:58:46Z (`.venv/bin/python -m unittest
discover -s tests -v`):

```
Ran 79 tests in 46.164s

OK (skipped=1)
```

Process wall 47.76 s (`/usr/bin/time -p`, real). 78 pass, 1 skipped (the
opt-in nelem-5 HHL fixture). Longest items: the shared nelem-2 HHL CLI run
16.04 s, `TestHHLFixture.test_nelem2_iter0_statevector_matches_reference`
6.86 s, `test_default_sqls_k_resolves_for_truncated_methods` 3.59 s.

Gate, started 2026-10-15T04:00:28Z (`FVM_GATE_TESTS=1 .venv/bin/python -m
unittest tests.test_gate_fixture -v`):

```
Ran 7 tests in 92.596s

OK
```

Process wall 93.29 s; `TestHHLFixture.test_nelem5_iter0_statevector_matches_
reference` 84.85 s, nelem-2 HHL fixture 7.71 s, both SQLS fixtures <= 0.03 s.

Checks after the runs: `git status --short` empty before the commit apart from
the 8 modified test files (now clean); `__pycache__` only at the repo root,
`src/` and `tests/` (all gitignored, the usual import caches); `output/`
untouched (29 entries, mtime 2026-09-01 15:11 -0400). `awk 'length > 88'`
over `tests/*.py`: none. Indented imports: none. Trailing whitespace: none.
Compile check of all `tests/*.py`: OK.

### Not pinned, and why

- `converged_by == 'dq_norm'`: no short case ends by the dq-norm test (the
  nelem-5 case hits `resratio < 1e-10` first, at 1.55e-14); the suite pins the
  accepted value set (`contract.CONVERGED_BY_VALUES`) and the
  `'residual_ratio'` branch only.
- The constructor's `except ImportError` branch itself (printing `SQLS
  back-end unavailable` at construction and storing `qsolver_import_error`)
  is not driven end to end: both back-ends are installed in the venv and
  uninstalling is out of scope. The tests set the two attributes the branch
  would set and pin the message `sqls_solve` / `hhl_solve` then raise.
- The zero-b path through the CLI is unreachable in a short run (the outer
  loop stops on the residual ratio before b is exactly 0), so N4 is pinned
  in-process only, which is the code path the task named.
- `-v 0` still lets the sqls package print its timing lines (`Time
  consumption for SVD`, 36 stdout lines at nelem 2); only the `SQLS: N=`
  banner is pinned, as specified.
- Only `density_matrix` is used for the non-statevector rejection; the other
  Aer methods share the same `parser.error` branch.

Scratch under `/tmp/order1-fixup-B/` (probe runs and the two suite logs)
deleted at the end of the round. Commit made with the git gate's literal
`git -C /abs/repo add|commit` form; not pushed.
