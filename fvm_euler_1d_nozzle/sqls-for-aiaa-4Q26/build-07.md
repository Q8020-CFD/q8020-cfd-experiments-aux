# Build 07 -- `-sqls_k` default and early validation, fail fast on non-ideal backend

- Builder: builder A, 2026-10-15T02:54:26Z (commit time; `-0400` local = 2026-10-14 22:54:26 -0400)
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26` (base `main` @ `ef7f0a8b`)
- Commit: `d7658f6a` "SQLS: default sqls_k to N//2, validate k and ideal backend early, narrow import except"
- Work-plan item: 7 in `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`; findings 7 and 8 of `04-sqls-wiring-validation.md`

## What changed

| file:line (after commit) | change |
|---|---|
| `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py:112-116` | `-sqls_k` default `128` -> `None`; help states the rule (power of 2, 2 <= k < N, N = 3*nelem padded to the next power of 2, N=16 at nelem 5 so k in {2,4,8}, ignored by full_svd, default N//2). |
| `nozzle_1d_solver.py:213-233` (SQLS branch of `linsolv_args`) | (a) `backend_type != 'ideal'` -> `parser.error(...)` before the solver is built. (b) `sqls_n = math_tools.next_power_of_2(3 * Nelem)`; default k resolved to `sqls_n // 2`; an explicit k is validated only for `truncated_qr`/`truncated_mps` and rejected with `parser.error` (exit status 2) quoting k, N and nelem. (c) prints `SQLS: N=<N> (padded), k=<k>, method=<m>`. |
| `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py:757` | `QuantumSQLS.__init__` default `k=128` -> `k=None`. |
| `quantum_tools.py:758-761` | probe `import sqls.runtime.quantum` in `__init__` so a missing sqls package raises `ImportError` at construction (before this, the sqls import was only inside `solve_one_step`, so construction succeeded without sqls). Inline import kept deliberately: sqls is an optional extra. |
| `quantum_tools.py:832-840` (`solve_one_step`, after padding) | defensive: `k=None` -> `N // 2`; for the truncated methods raise `ValueError` if k is not a power of 2 with 2 <= k < N, before calling `quantum_solve`. |
| `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/time_solvers.py:292-296` | SQLS construction `except Exception` -> `except ImportError` (prints `SQLS back-end unavailable: ...`; `sqls_solver` stays None so the existing install-hint `RuntimeError` fires at the first solve). Any other error (e.g. the non-ideal `ValueError`) now propagates with its real message. The HHL `except Exception` above it is untouched. |

N computation: the Euler system has 3 conserved variables per element, so nsys = 3*nelem (15 at nelem 5); `convert_to_pow2` pads bottom/right to `next_power_of_2(nsys)` (16). 3*nelem is never a power of two, so padding always happens on this path.

`full_svd` with an explicit `-sqls_k` (e.g. 128) is passed through unvalidated, as before; sqls ignores k for full_svd. With the default, full_svd now records `k = N//2` (8 at nelem 5, 4 at nelem 2) in the `k` column of `qc_metadata_sqls_*.csv` instead of 128; numerics unchanged (see below).

## Commands and results

All from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` with `.venv/bin/python nozzle_1d_solver.py`, output under `/tmp/order1-build-7-9/<run>` (deleted afterwards). Wall times from `/usr/bin/time -p` (real).
Common args `C = -nelem 5 -shots 0 -time_scheme BDF1 -initers 1 -localdt -cfl 1e10 -noshow`.

| run | args | exit | wall | observed |
|---|---|---|---|---|
| truncated_qr default k, 2 iters | `-linsolver SQLS -sqls_method truncated_qr $C -iters 2` | 1 | 1.55 s | `SQLS: N=16 (padded), k=8, method=truncated_qr`; step 0 solve completes (fidelity 0.96751, linsys_residual 11.81, k column 8); step 1 dies in `get_matrix_properties` -> `numpy.linalg.LinAlgError: SVD did not converge` after `RuntimeWarning: invalid value encountered in sqrt` in `space_solvers.py:269` (state went non-physical). See doubt 1. |
| truncated_mps default k, 2 iters | same, `truncated_mps` | 1 | 1.41 s | same pattern: k=8, step 0 fidelity 0.96751, linsys_residual 11.81, then LinAlgError at step 1 |
| truncated_qr default k, 1 iter | `... -iters 1` | 0 | 1.82 s | completes, `final_results_nelem5_SQLS_statevector.csv` written |
| truncated_mps default k, 1 iter | `... -iters 1` | 0 | 1.78 s | completes |
| truncated_qr k=4, 1 iter | `-sqls_k 4 ... -iters 1` | 0 | 1.78 s | `k=4`, fidelity 0.93768, linsys_residual 12.25 |
| invalid k=128 | `-sqls_method truncated_qr -sqls_k 128` | 2 | 0.33 s | `FVM Solver - Euler 1D Solver: error: -sqls_k must be a power of 2 with 2 <= k < N for -sqls_method truncated_qr; got k=128, N=16 (nelem=5, 3*nelem padded to a power of 2)` |
| invalid k=3 | `-sqls_method truncated_qr -sqls_k 3` | 2 | 0.35 s | same message, `got k=3, N=16` |
| invalid k=16 | `-sqls_method truncated_mps -sqls_k 16` | 2 | 0.32 s | same message, `got k=16, N=16` |
| invalid k=1 | `-sqls_method truncated_mps -sqls_k 1` | 2 | 0.35 s | same message, `got k=1, N=16` |
| fake backend | `-backend fake fake_manila` | 2 | 0.36 s | `FVM Solver - Euler 1D Solver: error: -linsolver SQLS supports only '-backend ideal' (Aer statevector/shots); got '-backend fake'` |
| real-ibm backend | `-backend real-ibm ibm_brisbane` | 2 | 0.34 s | same, `got '-backend real-ibm'` |
| full_svd explicit k=128 | `-sqls_method full_svd -sqls_k 128 ... -iters 1` | 0 | not recorded (about 1.8 s like the others) | runs; L2 error (absolute) 4.80e-15 |
| missing sqls (simulated) | `runpy` wrapper setting `sys.modules['sqls'] = None`, `-linsolver SQLS $C -iters 2` | 1 | not recorded | `SQLS back-end unavailable: ModuleNotFoundError - No module named 'sqls.runtime'; 'sqls' is not a package`, then `RuntimeError: SQLS solver not initialized. Install the optional sqls back-end: pip install -e ".[sqls]" (or \`pip install -e ../sqls --no-deps\`).` |
| direct API checks | `QuantumSQLS(backend_type='fake')`; `QuantumSQLS(method='truncated_qr', k=128).solve_one_step(A15, b15)`; default k on a 15x15 system | n/a | under 2 s | `QuantumSQLS supports backend_type='ideal' only (simulator statevector/shots); got 'fake'.`; `SQLS method='truncated_qr' requires k to be a power of 2 with 2 <= k < N; got k=128, N=16.`; default resolves to `k = 8` |
| LU regression | `-nelem 5 -time_scheme BDF1 -linsolver LU -localdt -cfl 1e10 -iters 3 -initers 1 -noshow` | 0 | 0.98 s | `residual_nelem5_LU.csv` byte-identical to the pre-change baseline (12.3754 -> 0.56868 -> 0.058329) |
| full_svd rung 3, nelem 2 / 5 | item 9 rung-3 command, before the item 9 change | 0 / 0 | 1.93 s / 1.88 s | `SQLS: N=8 (padded), k=4` / `N=16, k=8`; residual history identical (max abs diff 0.0) to the post-item-9 runs in `build-09.md` |
| `--help` | `--help` | 0 | under 1 s | shows the k rule text above |

HHL was not run (out of scope); no line of the HHL path changed (`git show d7658f6a` touches only the SQLS branch in `nozzle_1d_solver.py`, `QuantumSQLS`, and the SQLS `try/except` in `time_solvers.py`).

## Open doubts

1. **Criterion 1 is met for k, not for "run completes" at `-iters 2`.** The default k no longer raises inside sqls, and the first truncated solve runs. But at N=16 the largest legal k is 8, which keeps only 8 of 16 singular values. The step-0 update is then far from the Newton step (fidelity 0.968, ||A dq - b|| = 11.8 against ||b|| about 12.4). That update drives the nelem-5 state non-physical (negative p/rho -> NaN), and step 1 dies in `np.linalg.cond` with `LinAlgError: SVD did not converge`. Both truncated methods fail the same way, and no legal k can avoid it. This is a numerics limit of rank-k truncation at this size, not a k-validation bug. `-iters 1` completes. If the verifier needs `-iters 2` to complete, that needs a separate decision: for example a smaller CFL, or a guard that rejects non-physical updates. I did not change solver numerics for it.
2. The CLI's N formula (`next_power_of_2(3 * nelem)`) duplicates what `convert_to_pow2` does at solve time. The solve-time check in `QuantumSQLS.solve_one_step` is the backstop if the two ever diverge.
3. The default k for full_svd is now N//2 rather than 128 in `qc_metadata_sqls_*.csv`. That changes the CSV, not the numerics; a harvester comparing k across runs would see the change.
4. The CLI prints `SQLS: N=..., k=...` unconditionally, even at `-v 0`.

## Fix-up round (code review findings)

Date: 2026-10-15T03:43:43Z. Commit `71c02aed` on `feature/sqls-aiaa-4q26` in `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, on top of `5af4dd2f`. Files: `math_tools.py`, `nozzle_1d_solver.py`, `quantum_tools.py`, `time_solvers.py` (74 insertions, 31 deletions). No test file changed. Line numbers below refer to the new tree.

### What changed

- **F1, backend method** (`nozzle_1d_solver.py:218-223`). `-linsolver SQLS` now rejects any `-backend` method other than `statevector`. `QuantumSQLS.get_backend` always uses `AerSimulator(method='statevector')`, so another value would only mislabel the case name and file names. New message, verbatim:
  `-linsolver SQLS supports only '-backend ideal statevector'; got '-backend ideal density_matrix'`
- **F6, one k rule** (`math_tools.py:27-42`). New `resolve_sqls_k(k: int | None, n: int, method: str) -> int` and the constant `SQLS_TRUNCATED_METHODS`. If k is None it returns n//2. For the truncated methods it raises `ValueError` unless k is a power of 2 with 2 <= k < n. Otherwise it returns k. full_svd is not validated: an explicit k passes through and is recorded as given; the default is N//2. This matches the previous behavior.
  - The CLI calls it at `nozzle_1d_solver.py:227-232` and turns the error into `parser.error`. New CLI message, verbatim:
    `-sqls_k: SQLS method='truncated_qr' requires k to be a power of 2 with 2 <= k < N; got k=128, N=16 (nelem=5, 3*nelem padded to a power of 2)`
  - `QuantumSQLS.solve_one_step` calls it at `quantum_tools.py:833-835` and lets it raise. In-process message, verbatim:
    `SQLS method='truncated_qr' requires k to be a power of 2 with 2 <= k < N; got k=3, N=16`
    The trailing period of the old in-process message is gone.
  - Help text for `-sqls_k` (`nozzle_1d_solver.py:116`) now ends `Ignored (not validated) by full_svd. [N//2]`.
- **F7, `-v 0`** (`nozzle_1d_solver.py:233-235`). The `SQLS: N=.. (padded), k=.., method=..` line now prints only when `-v` >= 1.
- **F2 and F4, import errors** (`time_solvers.py`).
  - The new attribute `self.qsolver_import_error` (line 259) holds `str(e)` of the ImportError.
  - The HHL constructor handler is narrowed from `except Exception` to `except ImportError` (lines 277-281), exactly like SQLS. Other HHL constructor errors, such as a real-ibm or fake backend failure, now propagate with their real message. Before, they were swallowed and surfaced later as "not initialized". HHL numerics did not change.
  - The SQLS handler also stores the message (lines 300-303). It notes that the error may come from a missing `qiskit_aer`.
  - New HHL RuntimeError (`hhl_solve`, lines 504-508), verbatim:
    ``HHL back-end unavailable: <original ImportError message>. HHL needs qiskit and the quantum_linear_solvers fork (module linear_solvers); install the project dependencies with `uv sync`.``
  - New SQLS RuntimeError (`sqls_solve`, lines 625-628), verbatim:
    `SQLS back-end unavailable: <original ImportError message>. If sqls itself is missing: pip install -e ../sqls --no-deps (or pip install -e ".[sqls]").`
  - The constructor-time prints are `HHL back-end unavailable: <Type> - <msg>` (new for HHL) and `SQLS back-end unavailable: <Type> - <msg>` (unchanged).
- **F8, metadata** (`nozzle_1d_solver.py:301-303, 342-343, 382-384`). `converged = False` and `converged_by = None` are set before the Newton loop. They are set inside the existing convergence `if`, before the banner. Loop logic and banners are unchanged. New keys in `metadata_<case>.pkl`:
  - `converged`: `bool`. True iff the loop exited through `resratio < conv_tol` or `np.all(dqnorm <= 1e-10)`.
  - `converged_by`: `str` or `None`. `'residual_ratio'` if `resratio < conv_tol` fired; this takes precedence when both fire. Otherwise `'dq_norm'`. `None` when the iteration cap was reached.
  - `resnorm_init`: `float`. The reference residual the ratio test divides by. On `-resume` it is the value restored from the checkpoint.
  - `max_iters` and `final_iters` were already present (`final_iters` = index of the last step, i.e. `imax`). They were not duplicated.

### Verification (laptop, short runs; `-noshow -outdir /tmp/order1-fixup-A/<name>`)

| case | command (after `.venv/bin/python nozzle_1d_solver.py`) | rc | wall | observed |
|---|---|---|---|---|
| F1 reject | `-nelem 5 -linsolver SQLS -shots 0 -iters 1 -backend ideal density_matrix` | 2 | 0.37 s | message above (names `statevector`) |
| F1 explicit ok | same, `-backend ideal statevector` | 0 | 2.00 s | `SQLS: N=16 (padded), k=8, method=full_svd` |
| F1 default ok | same, no `-backend` | 0 | 1.81 s | same line |
| F7 `-v 0` | `-nelem 2 -linsolver SQLS -shots 0 -iters 1 -v 0` | 0 | 1.79 s | `grep -c "SQLS: N="` = 0 |
| F7 `-v 1` | same, `-v 1` | 0 | 1.81 s | `grep -c "SQLS: N="` = 1 |
| F6 k=128 | `-nelem 5 -linsolver SQLS -shots 0 -iters 1 -sqls_k 128 -sqls_method truncated_qr` | 2 | 0.33 s | message above (`power of 2`, `k=128`, `N=16`) |
| F6 k=3 | same, `-sqls_k 3` | 2 | 0.38 s | same text with `k=3` |
| F6 default k, truncated_qr | `-nelem 5 -linsolver SQLS -shots 0 -iters 1 -initers 1 -cfl 1e10 -localdt -sqls_method truncated_qr` | 0 | 1.94 s | `SQLS: N=16 (padded), k=8, method=truncated_qr`; fidelity 0.96751 |
| F6 in-process | `QuantumSQLS(method='truncated_qr', k=3).solve_one_step(A, b, 5)` with the nelem-5 iter-0 system | n/a | under 2 s | `ValueError` raised from frame `resolve_sqls_k`, message above |
| F2/F4 hints | `LinearSystemSolver` with `sqls_solver` / `hhl_solver` = None and `qsolver_import_error` set | n/a | under 2 s | both RuntimeError texts above, original message embedded verbatim |
| HHL regression | `-nelem 2 -shots 0 -iters 1 -linsolver HHL` (3 inner iterations) | 0 | 23.30 s | fidelities 0.9999986356113315 / 0.9999320074278994 / 0.9999987809883504. Before the edit: ...113313 / ...4757788 / ...0128117. A second after-run gave ...113313 / ...4924254 / ...0185293. The run-to-run spread is about 5e-11 (Aer, unrelated to this change); first-iteration value 0.9999986 as in the item-7 verifier |
| rung 3 regression | `-nelem 5 -linsolver SQLS -shots 0 -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -sqls_method full_svd` | 0 | 1.87 s (before: 2.14 s) | `residual_nelem5_SQLS_statevector.csv` byte-identical (`cmp`) to the pre-edit run |
| F8 converged | `-nelem 5 -linsolver SQLS -shots 0 -iters 15 -initers 1 -cfl 1e10 -localdt` | 0 | 1.87 s | `converged=True (bool)`, `converged_by='residual_ratio' (str)`, `resnorm_init=12.375368413827264 (float)`, `max_iters=15`, `final_iters=5`; banner at iteration 5 |
| F8 capped | same, `-iters 2` | 0 | 1.80 s | `converged=False`, `converged_by=None`, `resnorm_init=12.375368413827264`, `max_iters=2`, `final_iters=1` |
| test suite | `.venv/bin/python -m unittest discover -s tests -v` | 0 | 42.44 s | `Ran 60 tests ... OK (skipped=1)`; the skip is the gate-only `TestHHLFixture.test_nelem5_iter0_statevector_matches_reference` (needs `FVM_GATE_TESTS=1`) |

### Existing tests

None fail. The suite as committed in `5af4dd2f` passes unchanged against the new behavior: 60 tests in 42.12 s, 1 skipped. Tests that pin exact strings could break if they are tightened later. Two strings changed: the in-process k message lost its trailing period, and the RuntimeError hints are new.

### Notes

- The `truncated_qr` run with the default `-iters 1` (3 inner iterations at default CFL, nelem 5) still exits rc 1 with `LinAlgError: SVD did not converge`. I reproduced the same failure on the pre-fix-up tree (`git stash`). This is open doubt 1 above (rank-k truncation numerics), not a fix-up regression. The table therefore uses `-initers 1`.
- Open doubt 4 above (unconditional print) is resolved by F7.
