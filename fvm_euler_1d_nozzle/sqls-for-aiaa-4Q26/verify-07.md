VERDICT: PASS

# verify-07: independent verification of work item 7 (`-sqls_k` default/validation, SQLS backend fail-fast)

- Verifier session: 2026-10-15T03:00:56Z to 2026-10-15T03:12Z (UTC)
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`, HEAD `3a88a37d`
- Base: `main` @ `ef7f0a8b` (== `origin/main`)
- Commits on the branch (`git log main..feature/sqls-aiaa-4q26`):
  - `d7658f6a` "SQLS: default sqls_k to N//2, validate k and ideal backend early, narrow import except" -- item 7 (`nozzle_1d_solver.py` +25/-4, `quantum_tools.py` +12/-1, `time_solvers.py` +5/-2)
  - `3a88a37d` "SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse" -- NOT item 7 (`quantum_tools.py`, `eps=0.0` in the `convert_to_pow2` call). Present on the branch, so every "branch" run below includes it; where it matters I isolated item 7 (see criterion 4 and finding F8).
- Python: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python` (3.12); nothing installed; venv untouched.
- `main` comparison: detached worktree `git worktree add --detach /tmp/order1-verify-7/main-wt main`, removed afterwards with `git worktree remove --force`. Repo left read-only (`git status --porcelain` shows only the other agent's untracked `tests/`).
- All runs: `cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && .venv/bin/python nozzle_1d_solver.py <flags> -noshow -outdir /tmp/order1-verify-7/<name>`; wall time from `date +%s.%N` around the process. Scratch `/tmp/order1-verify-7` (19 MB) deleted at the end.
- Common flag set used below, `BASE` = `-nelem 5 -shots 0 -time_scheme BDF1 -iters 1 -initers 1 -localdt -cfl 1e10`.

## Criterion 1 -- default `-sqls_k` works with the truncated methods: PASS

Run window 2026-10-15T03:03:30Z to 03:03:37Z.

| name | command (after `nozzle_1d_solver.py`) | rc | wall |
|---|---|---|---|
| c1_tqr_i1 | `BASE -linsolver SQLS -sqls_method truncated_qr` | 0 | 2.21 s |
| c1_tmps_i1 | `BASE -linsolver SQLS -sqls_method truncated_mps` | 0 | 1.80 s |

Observed (both runs):
- stdout line 1: `SQLS: N=16 (padded), k=8, method=truncated_qr` (resp. `truncated_mps`)
- stdout line 8: `SQLS linear solver: method=truncated_qr, k=8, state_prep=initialize, mode=statevector`
- `qc_metadata_sqls_nelem5_truncated_qr.csv` row: `0, 0, 15, 16, 95.9778901432456, 9, 4, truncated_qr, 8, initialize, 1, 4, 0, -1, -1, CPU, 0.0021979808807373047` -- `matrix_size_orig`=15, `matrix_size_pow2`=16, `k`=8. The `truncated_mps` CSV records `k`=8 with `m_ancilla`=6.
- `[SQLS info]: Fidelity(true_sol, sqls_sol): 0.967513632695678` (tqr) / `0.9675136326956778` (tmps) -- rank-8 pseudo-inverse at N=16, as expected for a truncated method.
- No `ValueError`, no traceback; 10 output files each, including `residual_nelem5_SQLS_statevector.csv` with the single row `0.0,12.375368413827264,...`.
- k=8 is a power of two with 2 <= 8 < 16. PASS.

`-iters 2` with the truncated methods (reported per the brief; not a failure of the item):

| name | command | rc | wall |
|---|---|---|---|
| c1_tqr_i2 | `-nelem 5 -shots 0 -time_scheme BDF1 -iters 2 -initers 1 -localdt -cfl 1e10 -linsolver SQLS -sqls_method truncated_qr` | 1 | 1.35 s |
| c1_tmps_i2 | same with `truncated_mps` | 1 | 1.35 s |

Failure mode (identical for both): the rank-8 update at step 0 leaves the state unphysical, `space_solvers.py:113/175/269: RuntimeWarning: invalid value encountered in sqrt`, then at step 1 the Jacobian contains NaN and the crash is `numpy.linalg.LinAlgError: SVD did not converge` raised from `math_tools.py:248 get_matrix_properties -> np.linalg.cond(A)` (called from `quantum_tools.py:822 QuantumSQLS.solve_one_step`). Step 0 completed and recorded `k=8` in the CSV first. This is the known numerical limitation, not a k-validation problem.

## Criterion 2 -- invalid explicit `-sqls_k` rejected before any solve: PASS

Run window 2026-10-15T03:04:55Z to 03:05:13Z. All with `BASE -linsolver SQLS -sqls_method truncated_qr -sqls_k <k>` unless noted.

| name | k | rc | wall | outdir created | files |
|---|---|---|---|---|---|
| c2_tqr_k128 | 128 | 2 | 0.34 s | no | 0 |
| c2_tqr_k3 | 3 | 2 | 0.35 s | no | 0 |
| c2_tqr_k16 | 16 | 2 | 0.39 s | no | 0 |
| c2_tqr_k1 | 1 | 2 | 0.40 s | no | 0 |
| c2_tqr_k0 | 0 | 2 | 0.36 s | no | 0 |
| c2_tqr_k-4 | -4 | 2 | 0.39 s | no | 0 |
| c2_tqr_k5 | 5 | 2 | 0.38 s | no | 0 |
| c2_tqr_k32 | 32 | 2 | 0.43 s | no | 0 |
| c2_tmps_k128 | 128 (`truncated_mps`) | 2 | 0.42 s | no | 0 |
| c2_tmps_k3 | 3 (`truncated_mps`) | 2 | 0.45 s | no | 0 |
| c2_tmps_k1 | 1 (`truncated_mps`) | 2 | 0.33 s | no | 0 |

Verbatim message (k=128, truncated_qr; the others differ only in the k and method values), printed to stderr after the argparse usage block:

```
FVM Solver - Euler 1D Solver: error: -sqls_k must be a power of 2 with 2 <= k < N for -sqls_method truncated_qr; got k=128, N=16 (nelem=5, 3*nelem padded to a power of 2)
```

- States the constraint (power of 2, 2 <= k < N), the actual k, the actual N, and how N derives from nelem. Exit status 2 (argparse `parser.error`). The `-outdir` directory is never created (the check sits before `os.makedirs(args.output_dir)` at `nozzle_1d_solver.py`), so no solve output exists. The `SQLS: N=...` line is not printed on the rejection path (grep over the rejected logs: none). 0.3 to 0.45 s wall = import + parse only.

Valid explicit values, same window, all rc=0 with 10 files each: `-sqls_k 2` (tqr, 1.90 s, CSV `k`=2), `-sqls_k 4` (tqr, 1.84 s, `k`=4), `-sqls_k 2` (tmps, 1.99 s), `-sqls_k 8` (tmps, 1.79 s). Stdout line 1 and the CSV `k` column agree in every case.

Other mesh sizes (tests the N derivation at the edges): `-nelem 2 ... -sqls_k 4` rc=0 (N=8, `matrix_size_orig`=6); `-nelem 2 ... -sqls_k 8` rc=2 with `got k=8, N=8 (nelem=2, ...)`; `-nelem 1` default k rc=0, stdout `SQLS: N=4 (padded), k=2`, CSV `3, 4, ..., 2`; `-nelem 6` default k rc=0, `SQLS: N=32 (padded), k=16`, CSV `18, 32, ..., 16`.

## Criterion 3 -- non-ideal backend fails at startup with the real cause: PASS

Run window 2026-10-15T03:05:14Z to 03:05:24Z. All `BASE -linsolver SQLS <backend flags>`.

| name | backend flags | rc | wall | outdir |
|---|---|---|---|---|
| c3_fake | `-backend fake fake_manila` | 2 | 0.34 s | no |
| c3_realibm | `-backend real-ibm ibm_brisbane` | 2 | 0.40 s | no |
| c3_realiqm | `-backend real-iqm iqm_deneb` | 2 | 0.36 s | no |
| c3_fakequoted | `-backend "fake fake_manila"` (single quoted token) | 2 | 0.35 s | no |
| c3_fake_tqr | `-backend fake fake_manila -sqls_method truncated_qr -sqls_k 128` | 2 | 0.38 s | no |
| c3_bogus | `-backend bogus` | 2 | 0.37 s | no |
| c3_ideal_dm | `-backend ideal density_matrix` | 0 | 1.89 s | yes (10 files; runs as ideal, method string ignored as before) |

Verbatim (fake; others substitute the type):

```
FVM Solver - Euler 1D Solver: error: -linsolver SQLS supports only '-backend ideal' (Aer statevector/shots); got '-backend fake'
```

Note `c3_fake_tqr`: the backend check fires before the k check, so the backend message wins when both are wrong -- fine.

For contrast, the same `-backend fake fake_manila` on `main` (c3_fake_MAIN, rc=1, 1.65 s) printed `An unexpected error occurred: ValueError - QuantumSQLS supports backend_type='ideal' only (simulator statevector/shots); got 'fake'.` and then died at the first solve with `RuntimeError: SQLS solver not initialized. Install the optional sqls back-end: ...` -- the misleading path the item was meant to remove -- and it had already created the (empty) output dir. On the branch neither happens.

Missing-sqls path, verified two ways:
- Code: `quantum_tools.py` `QuantumSQLS.__init__` now begins with `import sqls.runtime.quantum  # noqa: F401`, so a missing package raises `ImportError` (or its subclass `ModuleNotFoundError`) at construction; `time_solvers.py` `LinearSystemSolver.__init__` catches exactly `ImportError`, prints `SQLS back-end unavailable: ...`, leaves `sqls_solver = None`, and `sqls_solve()` (`time_solvers.py:615-618`) raises the `RuntimeError` install hint at the first solve. Any non-ImportError (e.g. the `ValueError` from `get_backend()`) now propagates.
- In-process simulation (no venv change), run from the repo root with `-c` + `runpy`, `sys.modules['sqls'] = None`, args `BASE -linsolver SQLS -noshow -outdir /tmp/order1-verify-7/c3_nosqls`: rc=1, 1.40 s. Output contains `SQLS back-end unavailable: ModuleNotFoundError - No module named 'sqls.runtime'; 'sqls' is not a package` and then `RuntimeError: SQLS solver not initialized. Install the optional sqls back-end: pip install -e ".[sqls]" (or `pip install -e ../sqls --no-deps`).` -- the install hint survives. (A real absence would read `No module named 'sqls'`; same `ImportError` family, same handler.) The same simulation on `main` also ends in the install hint (rc=1), so that path is unchanged.

## Criterion 4 -- LU and HHL unchanged; full_svd unchanged and not blocked by k validation: PASS

Run window 2026-10-15T03:05:24Z to 03:05:51Z (plus determinism re-runs about 03:07Z and the item-7-only build at 03:09:06Z).

LU, branch vs `main`, command `-nelem 5 -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -linsolver LU` (c4_LU_branch 0.98 s rc=0; c4_LU_main 0.96 s rc=0). `residual_nelem5_LU.csv` is byte-identical:

```
iters, residual_total, residual_rho, residual_rhou, residual_rhoE
0.0,12.375368413827264,3.056753228741153,4.585129843111731,11.080730454186686
1.0,0.5686791352317027,0.06349331497032062,0.40978589237959717,0.3891530292938936
2.0,0.05832886414347176,0.00044965619536545883,0.04400539680842916,0.038282884600121865
```

i.e. 12.375 -> 0.5687 -> 0.0583 (3 s.f.) as required. `diff -r` of the two output dirs: only `metadata_nelem5_LU.pkl` differs, and unpickling shows the only differing keys are `timestamp` and `elapsed_time` (0.132 s vs 0.134 s). `-v 0` LU stdout differs only in the elapsed-time string and the outdir path.

HHL smoke run on the branch, `-nelem 2 -shots 0 -time_scheme BDF1 -localdt -cfl 1e10 -iters 1 -initers 1 -linsolver HHL` (c4_HHL_branch): rc=0, 9.06 s wall, 12 files; `Using ideal local simulator with 'statevector' method`; `[HHL info]: linear system residual (e=||Ax-b||_2): 0.003351932640843925`; `Fidelity(true_sol, hhl_sol): 0.9999986356113311`; `residual_nelem2_HHL_statevector.csv` row `0.0,1.3141049901831434,0.3245878859783296,0.48688182896749443,1.1766310866714451`. Code: `git diff main..feature/sqls-aiaa-4q26 -- time_solvers.py` touches only the SQLS `except` block (lines 292-296); the HHL `except Exception` at line 275 and the HHL branch of `nozzle_1d_solver.py` are untouched. A CLI-only probe (patched `BDFTimeSolver.__init__` to stop after parse) confirms `-linsolver HHL -backend fake fake_manila` still reaches construction with `backend_type='fake'` (the new SQLS-only backend check does not leak into HHL), and `-linsolver HHL -sqls_k 128 -sqls_method truncated_qr` is still silently ignored (no `sqls_*` keys in `linsolv_args`), as on `main`. No HHL run on `main` was made (not needed: path untouched, and the brief limits HHL runs).

SQLS full_svd, `-nelem 5 -shots 0 -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -linsolver SQLS -sqls_method full_svd`: c4_fsvd_branch 1.87 s rc=0; c4_fsvd_main 1.96 s rc=0; stdout line 1 on branch `SQLS: N=16 (padded), k=8, method=full_svd`. `residual_nelem5_SQLS_statevector.csv` byte-identical between branch and main:

```
0.0,12.375368413827264,3.056753228741153,4.585129843111731,11.080730454186686
1.0,0.568679135231724,0.06349331497030834,0.40978589237960644,0.38915302929391704
2.0,0.05832885640886122,0.00044965720794885324,0.044005392973146436,0.038282877212140735
```

Three branch-vs-main CSVs differ at rounding level: `dq_nelem5_iter1_statevector.csv` max |diff| 4.163e-17, `dq_nelem5_iter2_statevector.csv` 5.204e-18, `hhl_metrics_nelem5_statevector.csv` 1.313e-16 (dimensionless solver-update and metric values). Repeat runs on each side are bit-identical in every solution CSV (only `solve_time` in `qc_metadata` changes), so this is a real, deterministic difference. To attribute it I built `/tmp/order1-verify-7/item7-only/` from the `main` worktree's `*.py` with `nozzle_1d_solver.py`, `quantum_tools.py`, `time_solvers.py` replaced by `git show d7658f6a:<file>` (read-only git), and ran the same command (c4_fsvd_item7only, 1.80 s, rc=0): every solution/residual CSV is byte-identical to `main` (only `qc_metadata` differs, `k` 8 vs 128). The 1e-17-level differences therefore come from the later commit `3a88a37d` (`eps=0.0` RHS padding), not item 7.

full_svd must not be blocked by k validation: `-sqls_k 3` (c4_fsvd_k3, 1.89 s, rc=0, 3 iters, CSV `k`=3), `-sqls_k 128` (c4_fsvd_k128, 1.90 s, rc=0, CSV `k`=128), `-sqls_k 1` (c4_fsvd_k1, 1.77 s, rc=0, CSV `k`=1) all run; residual CSVs identical to c4_fsvd_branch. The CLI check is gated on `args.sqls_method in ('truncated_qr', 'truncated_mps')` and the solve-time check on `self.method in (...)`; `sqls.py:174-178` likewise only checks k for the truncated methods, so an odd k is never seen by a validator for `full_svd`.

## Criterion 5 -- help text and commit placement: PASS

`.venv/bin/python nozzle_1d_solver.py --help` (rc=0), verbatim block:

```
  -sqls_k SQLS_K        SQLS truncation rank for truncated_qr/truncated_mps:
                        must be a power of 2 with 2 <= k < N, N = 3*nelem
                        padded to the next power of 2 (N=16 at nelem 5, so k
                        in {2,4,8}). Ignored by full_svd. [N//2]
```

- `git branch --contains d7658f6a` -> `* feature/sqls-aiaa-4q26` only; `git merge-base --is-ancestor d7658f6a main` -> false; `git rev-parse main origin/main` both `ef7f0a8b2247615b56e4391fa1804b59825de217`.
- `git rev-parse --verify origin/feature/sqls-aiaa-4q26` -> `fatal: Needed a single revision`; `git branch -r` lists no such ref. Nothing pushed.
- Working tree clean apart from the other agent's untracked `tests/`.

## Additional findings

- F1 (PASS, no action). N derivation agrees with the solver: CLI uses `math_tools.next_power_of_2(3 * Nelem)`; `convert_to_pow2` uses `next_power_of_2(A.shape[0])` with `A.shape[0] == 3*nelem` (CSV `matrix_size_orig` 3/6/15/18 at nelem 1/2/5/6; `time_solvers.sqls_solve` also assumes `nsys/3`). Same function, so the CLI N and the runtime N cannot disagree. `3*nelem` is never itself a power of two (3 is odd; checked exhaustively for nelem <= 100000), so padding always occurs and there is no "already a power of two" edge. Table for nelem 1..12: N = 4, 8, 16, 16, 16, 32, 32, 32, 32, 32, 64, 64 with default k = N//2 = 2, 4, 8, 8, 8, 16, 16, 16, 16, 16, 32, 32.
- F2 (info). The solve-time defensive check in `QuantumSQLS.solve_one_step` uses the identical predicate `(k < 2 or k >= N or (k & (k-1)) != 0)` as the CLI and as `sqls.py:175`. The CLI validates only an EXPLICIT k; the derived default `N//2` is always valid for N >= 4, which holds for every nelem >= 1 (only the degenerate `-nelem 0`, N=1, k=0 would slip past the CLI check, and the mesh fails before any solve there). I found no CLI combination that reaches the sqls k `ValueError`: `-sqls_method` and `-sqls_state_prep` are argparse `choices`, k is validated, and sqls's `iso_chi`/`mps_chi` are not exposed. The remaining sqls `ValueError`s (zero b, zero alpha) are data-dependent, not configuration.
- F3 (PASS). Exception narrowing is confined to the SQLS branch; the HHL `except Exception` (`time_solvers.py:275`) is untouched. Side effect of narrowing: non-ImportError failures inside `QuantumSQLS.__init__` (e.g. `AerSimulator` construction errors, `os.makedirs` `OSError`) now propagate with their real traceback instead of being swallowed into the misleading install hint -- an improvement. Simulated missing `qiskit_aer` with sqls present (`sys.modules['qiskit_aer']=None`, rc=1) still takes the ImportError path: `SQLS back-end unavailable: ModuleNotFoundError - import of qiskit_aer halted; None in sys.modules` then the sqls install hint. The hint text names only sqls, not qiskit-aer (pre-existing wording; low).
- F4 (low). `-v 0` behavior change: one new unconditional stdout line `SQLS: N=16 (padded), k=8, method=full_svd` for SQLS runs (c4_v0_fsvd_branch vs c4_v0_fsvd_main differ by exactly that line). LU and HHL `-v 0` output is unchanged. SQLS at `-v 0` was already far from silent on `main` (the sqls package prints its timing lines and the `[SQLS info]` block is unconditional), and the line is the k report criterion 1 asks for, so I rate this cosmetic. If `-v 0` is meant to be quiet, guard the print with `args.verbosity`.
- F5 (PASS). No new import-time output: `python -c "import time_solvers, quantum_tools, math_tools"` prints nothing on branch or main. `py_compile` of the three files OK.
- F6 (PASS). Style over the whole `main..branch` diff of the three files: longest added line 77 chars (<= 88), no trailing whitespace, no tabs. The new `import sqls.runtime.quantum` is inside `__init__` rather than at module top, deliberately as an optional-dependency probe, matching the pre-existing in-function `from sqls.runtime.quantum import quantum_solve`. pyflakes/pycodestyle are not in the venv; checks were manual.
- F7 (low). `qc_metadata_sqls_*.csv` `k` column for `full_svd`: now records 8 (= N//2) where `main` recorded 128; an explicit `-sqls_k 3/128/1` with `full_svd` is recorded verbatim (3/128/1). Sensible in that the column shows what was passed and the default now satisfies the documented rule, but k has no meaning for `full_svd` and a CSV reader could misread `k=8` as a truncation rank. Optional improvement, not required by the item: record `k=N` (full rank) or empty for `full_svd`.
- F8 (info, not item 7). Commit `3a88a37d` (`eps=0.0` RHS pad) is on the same branch and changes `full_svd` solution CSVs at the 1e-17 level while leaving the residual CSV byte-identical (details under criterion 4). Flagging it so whoever verifies that item does not attribute the drift to item 7, and vice versa.
- F9 (PASS). On `main`, `-linsolver SQLS -backend fake` created the empty `-outdir` before failing; on the branch the rejection happens before `os.makedirs`, so no directory is created (verified: `outdir_exists=no` for every rc=2 case).
- F10 (info). Extra paths exercised on the branch, all rc=0: `truncated_mps -sqls_state_prep mps` (sqls `UserWarning` about state_prep being ignored, run completes, 1.80 s); `truncated_qr -shots 256` default k (CSV `qc_metadata_sqls_nelem5_truncated_qr_shots256.csv`, fidelity 0.9588, 1.89 s); `-linsolver GMRES` 3 iters (residual 12.375 -> 0.6452 -> 0.07377, 1.00 s).

## Not checked, and why

- HHL on fake/real backends and any HHL run longer than the one 9 s statevector case: out of scope per the run limits; the diff shows the HHL code paths untouched.
- A genuinely uninstalled `sqls` package: only simulated in-process (`sys.modules['sqls'] = None`), since the venv must not change. The real message would be `No module named 'sqls'`; same `ImportError` handler.
- GPU (`-qc_gpu`) and `-sqls_repeats > 1` paths: not touched by the item.
- pycodestyle/pyflakes: not installed; line-length, whitespace, tab and compile checks were done manually over the diff.
- Any `build-*.md`, `verify-*.md`, `STATUS.md`: not read, per instructions.
