# verify-gate1-fvm — independent re-verification of the review fix-ups

VERDICT: PASS

Re-verifier session 2026-10-15T04:10:10Z to 2026-10-15T04:22Z (UTC), on the
laptop (macOS 26.6 / Darwin 25.6.0, Apple silicon). Repo
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26` at `f16720b3`, `main` and `origin/main` both at
`ef7f0a8b`. Interpreter
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
(Python 3.12.10, qiskit 2.5.2, qiskit-aer 0.17.2, numpy 2.5.2, scipy 1.18.0).
Read-only: no edits, adds, commits, stashes, checkouts, resets or pushes; one
detached worktree created and removed for the byte comparison. No
`build-*.md`, `verify-*.md`, `reproduce-*.md` or `STATUS.md` was read.
Scratch tree `/tmp/order1-reverify-fvm/` deleted at the end.

Commits under test (all five present, `git log --oneline main..feature/sqls-aiaa-4q26`):

```
f16720b3 Tests: use sys.executable, top-level imports, pin 71c02aed SQLS fixups and convergence metadata
71c02aed SQLS review fixups: backend method check, shared k rule, zero b, import hints, -v 0, convergence metadata
5af4dd2f Add unittest regression suite and gate fixtures for LU GMRES HHL SQLS paths
3a88a37d SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse
d7658f6a SQLS: default sqls_k to N//2, validate k and ideal backend early, narrow import except
```

`git show 71c02aed --stat`: `math_tools.py` +16, `nozzle_1d_solver.py` +24/-12,
`quantum_tools.py` +9/-9, `time_solvers.py` +25/-10 (4 files, 74 insertions,
31 deletions). `git show f16720b3 --stat`: `TESTING.md` and 8 files under
`tests/` (9 files, 468 insertions, 53 deletions); no solver module touched.

Timing note: the gate suite (93 s) was run concurrently with the short CLI and
in-process probes to save wall time. The probe wall times below are therefore
upper bounds under CPU contention; the one probe that exceeded 10 s under
contention (F1b, 12.75 s) was re-run alone and took 1.78 s. The default suite
ran alone.

All CLI probes used `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`
plus `-outdir /tmp/order1-reverify-fvm/<name>`, cwd the repo root.

## Findings resolved by 71c02aed (solver modules)

### F1 — `-linsolver SQLS` rejects `backend_method != 'statevector'` at parse time: RESOLVED

Code (`nozzle_1d_solver.py` lines 220-223, added by 71c02aed): after the existing
`backend_type != 'ideal'` check, `if backend_method != 'statevector':
parser.error(...)`. `backend_method` defaults to `'statevector'` when only one
`-backend` token is given (lines 180, 182; argparse default
`['ideal', 'statevector']`, line 82).

F1a, two-token form (0 bytes on stdout, no outdir created, 3.07 s under contention):

```
.venv/bin/python nozzle_1d_solver.py -nelem 2 -linsolver SQLS -backend ideal density_matrix -shots 0 -iters 1 ... -outdir /tmp/order1-reverify-fvm/f1-dm
rc=2
FVM Solver - Euler 1D Solver: error: -linsolver SQLS supports only '-backend ideal statevector'; got '-backend ideal density_matrix'
```

F1a', quoted single-token form (the split branch at lines 171-178), 0.42 s:

```
-backend "ideal density_matrix"
rc=2
FVM Solver - Euler 1D Solver: error: -linsolver SQLS supports only '-backend ideal statevector'; got '-backend ideal density_matrix'
```

F1b, explicit `-backend ideal statevector` still runs (rc 0; 12.75 s contended,
1.78 s uncontended re-run), banner printed once, metadata pickle
`backend_type`/`backend_method` = `ideal statevector`, 10 output files written
(`dq_nelem2_iter0_statevector.csv`, `final_results_nelem2_SQLS_statevector.csv`,
`hhl_metrics_nelem2_statevector.csv`, `metadata_nelem2_SQLS_statevector.pkl`,
`qc_metadata_sqls_nelem2_full_svd.csv`, `residual_nelem2_SQLS_statevector.csv`,
`results_nelem2_iter0_statevector.csv`, `results_nelem2_SQLS_statevector_iter0.csv`,
`solution_plot_nelem2_SQLS_statevector.png`, `system_Ab_nelem2_iter0.pkl`).
The default (no `-backend`) runs in every SQLS probe below (F7b, F8a, F8b).

### F2 — HHL constructor catches only `ImportError`, hint corrected, numerics unchanged: RESOLVED

Diff of `time_solvers.py` in `main..HEAD` touches exactly two `except` lines, both
`except Exception as e:` to `except ImportError as e:` (HHL and SQLS constructor
blocks). `grep -n "qiskit-algorithms\|qiskit_algorithms" time_solvers.py` is
empty. New HHL hint (lines 504-508): `HHL back-end unavailable:
{self.qsolver_import_error}. HHL needs qiskit and the quantum_linear_solvers
fork (module linear_solvers); install the project dependencies with 'uv sync'.`

Narrowing demonstrated in-process (F2c): `helpers.make_linsys_solver(2, 'HHL',
backend_type='bogus', backend_method='nothing')` now propagates
`ValueError: Unknown backend_type: bogus. Must be one of: 'ideal', 'fake',
'real-ibm', 'real-iqm'` instead of being swallowed. (A probe with
`backend_type='fake', backend_method='fake_manila', shots=100` constructed
without error, so it was not informative either way.)

Numerics: in-process HHL statevector solve of the archived nelem-2 iter-0 system
(`tests/data/system_Ab_nelem2_iter0.pkl`) via `LinearSystemSolver.hhl_solve`:

```
F2 HHL nelem2 iter0 fidelity = 0.9999986356113313  (7.75 s)
```

matching the expected 0.9999986356 to all quoted digits. The gate suite (below)
pins the nelem-2 and nelem-5 HHL and SQLS solutions to 1e-10 max-abs against
references stored before 71c02aed and is green.

Out of scope, pre-existing: two bare `except:` at `time_solvers.py` lines 487 and
498 (GMRES fallback and `lu_solve`) exist on `main` (lines 477, 488 there) and
are untouched by the branch.

### F3 — all-zero RHS on the SQLS path returns zero without reaching sqls; no division by zero: RESOLVED

Code: `quantum_tools.py` `QuantumSQLS.solve_one_step` lines 836-840, `if not
np.any(b_o): return np.zeros(nsys)` placed after `resolve_sqls_k` and before
`quantum_solve`; `time_solvers.py` `sqls_solve` lines 662-667 sets
`fidelity_val = 1.0` when both `dq_lu` and `dq_sqls` are all zero; the remaining
metric divisions already carry `+ 1e-15` guards (lines 671-674, 684).

Premise confirmed: `sqls/src/sqls/sqls.py` line 179-181 raises
`ValueError("b is the zero vector; the SQLS target state is undefined.")`, and
calling `sqls.runtime.quantum.quantum_solve` directly with the zero-padded
`b = 0` (bypassing the guard) raised exactly
`ValueError: b is the zero vector; the SQLS target state is undefined.`

In-process on the archived nelem-5 Jacobian (`system_Ab_nelem5_iter0.pkl`),
`LinearSystemSolver.sqls_solve(A, zeros(15), step=0)`:

```
F3 shots=0:     dq.shape=(15,) all_zero=True (0.001 s)
   metrics: {'fidelity': 1.0, 'l2_error_abs': 0.0, 'l2_error_rel': 0.0, 'l2_error_normalized': 0.0, 'linsys_residual': 0.0}   finite: True
   files written: ['dq_nelem5_iter0_statevector.csv', 'system_Ab_nelem5_iter0.pkl']
F3 shots=10000: dq.shape=(15,) all_zero=True (0.001 s)
   metrics: identical to the above, finite: True
   files written: ['dq_nelem5_iter0_statevector_shots10000.csv', 'system_Ab_nelem5_iter0.pkl']
F3 direct: QuantumSQLS.solve_one_step(A, zeros(15), 5, 0, step=0) -> x.shape=(15,) all_zero=True k=8 files=[]
```

No `qc_metadata*` file is written for the zero step; `k` is still resolved to
N // 2 = 8 before the early return.

### F4 — ImportError hints carry the original exception text: RESOLVED

Code: `self.qsolver_import_error = str(e)` stored in both constructor `except
ImportError` blocks (`time_solvers.py` lines 258, 280, 302) and interpolated into
both `RuntimeError` messages (lines 504-508 HHL, 624-628 SQLS). Simulated
missing packages in fresh interpreters by setting `sys.modules[name] = None`
after importing `tests.helpers` (so the real import paths are exercised, not a
cleared attribute):

```
missing qiskit_aer (SQLS):   sqls_solver None: True | qsolver_import_error: 'import of qiskit_aer halted; None in sys.modules'
  RuntimeError: SQLS back-end unavailable: import of qiskit_aer halted; None in sys.modules. If sqls itself is missing: pip install -e ../sqls --no-deps (or pip install -e ".[sqls]").
missing sqls (SQLS):         sqls_solver None: True | qsolver_import_error: 'import of sqls.runtime.quantum halted; None in sys.modules'
  RuntimeError: SQLS back-end unavailable: import of sqls.runtime.quantum halted; None in sys.modules. If sqls itself is missing: pip install -e ../sqls --no-deps (or pip install -e ".[sqls]").
missing linear_solvers (HHL): hhl_solver None: True | qsolver_import_error: 'import of linear_solvers halted; None in sys.modules'
  RuntimeError: HHL back-end unavailable: import of linear_solvers halted; None in sys.modules. HHL needs qiskit and the quantum_linear_solvers fork (module linear_solvers); install the project dependencies with `uv sync`.
```

A missing qiskit-aer is reported as qiskit_aer, not as "install sqls" (the sqls
hint is conditional, "If sqls itself is missing").

### F6 — single k rule in `math_tools.resolve_sqls_k`: RESOLVED

`math_tools.py` lines 27-41 define `SQLS_TRUNCATED_METHODS = ('truncated_qr',
'truncated_mps')` and `resolve_sqls_k(k, n, method)` (default `n // 2`; validation
only for the truncated methods; `full_svd` never validated). Callers:
`nozzle_1d_solver.py` line 228 (`math_tools.resolve_sqls_k(args.sqls_k, sqls_n,
args.sqls_method)` inside `try/except ValueError -> parser.error`) and
`quantum_tools.py` line 835 (`self.k = resolve_sqls_k(self.k, N, self.method)`;
`resolve_sqls_k` imported at line 15).

Duplicate grep over `nozzle_1d_solver.py quantum_tools.py math_tools.py
time_solvers.py` for `k & (k - 1)`, `sqls_k &`, `self.k &`, `2 <= k < N`,
`'truncated_qr', 'truncated_mps'`: the only code hit is `math_tools.py` line 37.
Remaining hits are argparse help text (`nozzle_1d_solver.py` lines 109, 114-115)
and comments (`quantum_tools.py` lines 833-834). No second copy remains.

CLI message (0.35 s, rc 2, 0 bytes on stdout):

```
-nelem 5 -linsolver SQLS -sqls_method truncated_qr -sqls_k 3 -iters 1
FVM Solver - Euler 1D Solver: error: -sqls_k: SQLS method='truncated_qr' requires k to be a power of 2 with 2 <= k < N; got k=3, N=16 (nelem=5, 3*nelem padded to a power of 2)
```

contains `power of 2`, `k=3`, `N=16`. `full_svd` not validated: `-nelem 2
-sqls_method full_svd -sqls_k 128` ran (rc 0, 1.79 s) and printed
`SQLS: N=8 (padded), k=128, method=full_svd`.

### F7 — `SQLS: N=.., k=.., method=..` line only at `-v >= 1`: RESOLVED

Code: `nozzle_1d_solver.py` lines 233-235, `if args.verbosity >= 1: print(...)`;
`-v` default 1, choices {0, 1, 2} (lines 136-137).

```
-nelem 2 -linsolver SQLS -shots 0 -iters 1 -v 0   rc=0 1.78 s  'SQLS: N=' count stdout 0, stderr 0; 1435 bytes of other stdout; all 10 output files written
-nelem 2 -linsolver SQLS -shots 0 -iters 1        rc=0 1.80 s  'SQLS: N=' count 1: "SQLS: N=8 (padded), k=4, method=full_svd"
```

The suite also checks the `-v 2` run prints it exactly once.

### F8 — metadata pickle carries `converged`, `converged_by`, `resnorm_init`: RESOLVED

Code: `nozzle_1d_solver.py` lines 302-303 initialize `converged = False`,
`converged_by = None`; lines 342-343 set them inside the existing `if resratio <
conv_tol or np.all(dqnorm <= 1e-10):` block (`'residual_ratio' if resratio <
conv_tol else 'dq_norm'`); lines 382-384 add the three keys to the metadata dict.
The loop condition, loop body order and banners are unchanged (diff adds only
these lines in that region).

F8a converging run (1.89 s, rc 0), exact command
`.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 15 -initers 1 -noshow -outdir /tmp/order1-reverify-fvm/f8-conv`:

```
stdout: SOLUTION CONVERGED at iteration 5 / Final residual ratio: 1.55e-14 / Completed: 5 steps in 0.06s
metadata: converged True (bool) | converged_by 'residual_ratio' | resnorm_init 12.375368413827264 (float) | final_iters 5 | max_iters 15 | final_residual 1.9141592490752604e-13
keys: area_equation backend_method backend_type cfl conv_tol converged converged_by elapsed_time final_iters final_residual linear_solver localdt max_inner_iters max_iters nelem nondim nshots p_ref quantum_circuit res_tol resnorm_init rho_ref time_scheme timestamp u_ref
```

F8b capped run, same with `-iters 2` (1.73 s, rc 0, no `SOLUTION CONVERGED`):

```
metadata: converged False (bool) | converged_by None | resnorm_init 12.375368413827264 | final_iters 1 | max_iters 2
```

F8c, LU `-nelem 2 -iters 2` (0.93 s): `converged False | converged_by None |
resnorm_init 1.3141049901831434` (keys present on the classical path too).

## Findings resolved by f16720b3 (tests)

### R9 — `tests/helpers.py` uses `sys.executable`; `TESTING.md` states the rule: RESOLVED

`tests/helpers.py` line 42: `PYTHON = sys.executable`; the former
`VENV_PY = REPO / '.venv' / 'bin' / 'python'` and the `sys.path.insert` are
removed (moved to `tests/__init__.py`). `grep -rn "\.venv" tests/*.py` finds
only comments / usage strings (`tests/helpers.py` line 41,
`tests/make_fixtures.py` line 4). `TESTING.md` lines 9-12 ("Launch the suite
with the repo venv interpreter (`.venv/bin/python`). The CLI subprocesses run
under `sys.executable` ...") and lines 270-275 state the one-interpreter rule.

### R10 — no function-local imports; grouped at module top: RESOLVED

`grep -n "^\s\+import \|^\s\+from .* import" tests/*.py` -> empty (rc 1);
cross-checked with `grep -nE "^[[:space:]]+(import |from [^ ]+ import)"
tests/*.py` -> empty. Import blocks (listed for all 10 files) are
`__future__` / stdlib / `numpy` / local (`tests`, then `math_tools`,
`quantum_tools`, `case`, `mesh`, `space_solvers`, `time_solvers`), each group
separated by a blank line. `tests/__init__.py` inserts the repo root into
`sys.path` so the solver modules import at module top.

### New behaviour pinned with real assertions: YES

Read in full from `git show f16720b3`; each has concrete expected values that the
pre-fix code would fail:

- F1: `test_cli.TestCLIValidation.test_sqls_density_matrix_backend_rejected`
  (rc == 2, `'statevector'` and `'density_matrix'` in stderr, stdout == '',
  no banner) and `test_sqls_explicit_statevector_backend_accepted`
  (metadata `ideal`/`statevector`, banner count == 1).
- F3: `test_sqls.TestSQLSZeroRHS.test_sqls_solve_returns_zero_update` (shots 0
  and 10000: shape (15,), all zero, fidelity == 1.0, four metrics == 0.0, no
  `qc_metadata*`, dq csv both columns zero, system pickle present) and
  `test_solve_one_step_returns_zeros_without_circuit` (zeros, k == 8, empty outdir).
- F4: `test_sqls.TestSQLSBackendUnavailableMessage` and
  `test_hhl.TestHHLBackendUnavailableMessage` (message starts with
  `... back-end unavailable: `, contains the ImportError text and the hint,
  not `not initialized`). These clear the solver attribute and set
  `qsolver_import_error` by hand rather than forcing a real ImportError; my
  `sys.modules` probes above cover the real path.
- F6: `test_cli.TestResolveSqlsK` (5 tests: constant equality, default `n // 2`
  for 3 methods x N in {8,16,32}, k in {2,4,8} accepted, k in {128,3,16,1,0}
  rejected with `power of 2`/`k=`/`N=16`/`repr(method)`/no trailing period,
  `full_svd` never validates) plus `_assert_k_message` now asserts the CLI
  stderr embeds the canonical `resolve_sqls_k` message verbatim.
- F7: `test_cli.TestSQLSVerbosityBanner` (`-v 0`: banner absent from stdout
  and stderr, outputs still written; default: count == 1 and exact text) and
  `TestSQLSStatevectorNelem5.test_capped_run_metadata_not_converged` (`-v 2`
  count == 1).
- F8: `test_classical.TestLUNelem5Converges.test_metadata_records_convergence`
  and `test_sqls.TestSQLSStatevectorNelem5Converges.test_metadata_records_convergence`
  (`assertIs(converged, True)`, `== 'residual_ratio'`, in
  `contract.CONVERGED_BY_VALUES`, `final_iters == rows - 1 < max_iters - 1`,
  `resnorm_init` float == 12.375368413827264 to 1e-9, ratio < conv_tol);
  `test_output_contract._ContractMixin` and
  `TestSQLSStatevectorNelem5.test_capped_run_metadata_not_converged`
  (`assertIs(converged, False)`, `assertIsNone(converged_by)`, `resnorm_init`
  equals the first residual row); `contract.METADATA_KEYS_COMMON` extended
  with the three keys so the exact-key-set check would fail without them.

All 19 new tests appear in the default-suite log followed by `ok` (per-test
walls 0.00 s to 1.85 s).

### Diff scope of f16720b3: RESTRICTED

`git show f16720b3 --name-only`: `TESTING.md`, `tests/__init__.py`,
`tests/contract.py`, `tests/helpers.py`, `tests/test_classical.py`,
`tests/test_cli.py`, `tests/test_hhl.py`, `tests/test_output_contract.py`,
`tests/test_sqls.py`. Nothing else.

## Regression and hygiene

- Default suite, run alone, start 2026-10-15T04:13:11Z:
  `.venv/bin/python -m unittest discover -s tests -v` -> `Ran 79 tests in
  45.984s`, `OK (skipped=1)`, rc 0, 47.61 s process wall. The one skip is the
  opt-in `test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`
  ('gate-only (~90 s): set FVM_GATE_TESTS=1'). 78 `ok` lines, 0 `FAIL`/`ERROR`.
  Longest item: shared `solver -nelem 2 -linsolver HHL -shots 0 -iters 2 ...`
  15.94 s; longest test 6.81 s (gate nelem-2 HHL fixture). No test over 60 s.
- Gate suite, start 2026-10-15T04:16:58Z:
  `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`
  -> `Ran 7 tests in 92.531s`, `OK`, rc 0, 93.27 s process wall. Per test:
  provenance x3 0.00 s, HHL nelem2 7.79 s, HHL nelem5 84.64 s, SQLS nelem2
  0.09 s, SQLS nelem5 0.01 s. The 84.64 s item exceeds 60 s by design (the
  approved opt-in gate; it is skipped in the default suite).
- `git status --short` clean before and after everything (only ignored
  `output/` and `tests/__pycache__/` show under `--ignored`).
- `output/` untouched: `ls -laR output | md5` = `4c9d397c8106be34d2f25e9399dc59aa`
  before and after; `find output -newer <snapshot>` empty.
- Temp hygiene: `$TMPDIR` (`/var/folders/p9/m5qdpl0j5_385464fbcj2jkc0000gn/T/`,
  261 entries) and `/tmp` (41 entries) listed before the suites and after;
  `comm -13` shows no new entries; no `fvm_tests_*` directories remain.
- `git diff main..feature/sqls-aiaa-4q26 --stat`: 23 files, 2172 insertions,
  19 deletions. Solver-module changes confined to `math_tools.py` (+16),
  `nozzle_1d_solver.py` (+41 incl. -12), `quantum_tools.py` (+23 incl. -9),
  `time_solvers.py` (+40 incl. -10); everything else is `TESTING.md` and
  `tests/**` (incl. 7 binary fixtures under `tests/data/`).
- Nothing pushed: `git branch -r` lists `origin/HEAD`, `origin/main`, 9 archive /
  feature branches, no `origin/feature/sqls-aiaa-4q26`; `main` and `origin/main`
  both `ef7f0a8b`.
- Style: `git diff main..HEAD -- '*.py' | grep '^+' | awk 'length > 89'` empty
  (also empty restricted to the four solver modules); no added line in `*.py` or
  `*.md` has trailing whitespace. Added solver code follows the file's 2-space
  indent convention, typed signature on `resolve_sqls_k`.
- Byte comparison against `main` (detached worktree
  `/tmp/order1-reverify-fvm/main-wt` at `ef7f0a8b`, same venv python, cwd in
  each tree, `-nelem 5 -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1
  -noshow`; SQLS with `-sqls_method full_svd -shots 0`):
  - `residual_nelem5_LU.csv`: sha256
    `26d5929a0d0c789fd399e6c583dbb05d69ec8c70b50a63d76ad0aa47ff97841f` on both,
    `cmp` identical (branch 1.04 s, main 0.98 s).
  - `residual_nelem5_SQLS_statevector.csv`: sha256
    `82248cb7dbba4e7c822e806dca3b2bed2cae93f62b14ae0da89e97a915216fc4` on both,
    `cmp` identical (branch 1.86 s, main 1.88 s). Rows: 12.375368413827264,
    0.568679135231724, 0.05832885640886122 (residual_total).
  - Informational: `final_results_*.csv` identical for both solvers;
    `dq_nelem5_iter0_statevector.csv` identical; `dq_*_iter1` and `iter2`
    differ in `dq_sqls` by max-abs 4.163e-17 and 5.204e-18 (||dq_lu|| 1.67e-1
    and 2.41e-2), i.e. floating-point noise consistent with 3a88a37d's zero RHS
    pad; `dq_lu` columns identical.
  - Worktree removed (`git worktree remove --force`, `git worktree prune`);
    `git worktree list` shows only the main checkout.

## Not checked, and why

- Real package removal: a missing `qiskit-aer` / `sqls` / `linear_solvers` was
  simulated with `sys.modules[name] = None` in fresh interpreters (which makes
  the real `import` statements raise ImportError), not by uninstalling
  (install/uninstall forbidden).
- Mutation testing of the new tests (deliberately breaking the solver to watch
  them fail): forbidden (read-only). Assertion strength judged by reading.
- The `converged_by == 'dq_norm'` branch: no probe case ends by the dq-norm test
  on this problem (the residual-ratio test fires first); only the code path
  was read.
- `-sqls_k` behaviour on the `main` worktree was not compared (main predates
  d7658f6a); only the full_svd and LU residual CSVs were compared as asked.
- The nelem-5 HHL fixture is the only item over 60 s and is the approved
  opt-in gate; it was run once as approved.
