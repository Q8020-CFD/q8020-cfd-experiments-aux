# Build 11 -- benchmark-fairness fixes (reference-free sign, shared circuit counter, effective shots, seed, hhl_scale, README corrections)

- Builder: BUILDER 11 (Fable), 2026-10-15T08:00Z to 08:45Z (laptop, macOS 26.6, Apple silicon; qiskit 2.5.2 / qiskit-aer 0.17.2 / qiskit-ibm-runtime 0.50.0 / numpy 2.5.2 / scipy 1.18.0, python 3.12.10, `.venv` untouched, `pyproject.toml` / `uv.lock` untouched)
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`, base `e13cbb1e` (main @ `ef7f0a8b`), HEAD `484b24ed`. Nothing pushed, `main` untouched, working tree clean after the last commit.
- Work-plan item 11 in `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`; findings 3, 4, 5, 6, 11, 12, 13 of `04-sqls-wiring-validation.md` sec. 6.
- Scratch `/tmp/order3-build-11/` (all solver outputs), deleted at the end of this build.

## Commits (`git log --oneline e13cbb1e..HEAD`)

```
484b24ed README and TESTING: item 11 flags, fairness columns, classical dependencies, AerSimulator.run wording
545d6b03 Make -hhl_scale default leastsq explicit, validate the choice and record hhl_scale in the pickle
035018cc Record effective_shots (nshots x repeats) in the metadata pickle
68ef63f5 Add -seed for reproducible HHL and SQLS shots, recorded in the CSVs and the pickle
cca70256 Add shared fixed-basis circuit counter, -circ_metrics and the eight fairness columns to both qc_metadata CSVs
005f05b2 SQLS: choose the statevector global sign from A and b, not the LU reference
```

`git diff e13cbb1e..HEAD --stat`: 13 files changed, 1145 insertions(+), 66 deletions(-) -- `README.md` (+65), `TESTING.md` (+150), `math_tools.py` (+18), `nozzle_1d_solver.py` (+55), `quantum_tools.py` (+147), `time_solvers.py` (+65), `tests/contract.py` (+30), `tests/helpers.py` (+22), `tests/test_circuit_metrics.py` (new, 210), `tests/test_cli.py` (+15), `tests/test_hhl.py` (+192), `tests/test_output_contract.py` (+38), `tests/test_sqls.py` (+204).

Outside the fvm repo (both uncommitted, by design):
- `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py` line 123: one added line `sqls_out["qc"] = qc` (right after the `SQLS(...)` call; ORNL style, no other change). Branch `local/sampler-port-2026-10`, tip still equal to `main` @ `9a4346a7`; the working tree carries the item-3 sampler port plus this line.
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff` regenerated from `git -C /Users/agallojr/proj/src/q8020/sqls diff main`: **6099 bytes, sha256 `c8425988ddc64d72385dcf026eb5125c665fdbe3d0c1a7b85a9e4b6250090752`** (was 5712 bytes, `2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9`). `git diff main | shasum -a 256` reproduces it exactly.
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md` corrected (item d, below). No other file in that folder touched; the harvester is untouched.

## What changed, per sub-item (file:line at HEAD `484b24ed`)

### (a) Reference-free global sign (commit `005f05b2`)

- `math_tools.py:50-59` new `choose_global_sign(A, b, x)`: returns `x` if `||A x - b|| <= ||A(-x) - b||`, else `-x`; one matvec (`A @ x`) and two norms, so `A(-x) = -(A x)` is not recomputed; tie (x = 0 or b = 0) keeps `+x`. Pure numpy, no qiskit.
- `time_solvers.py:672-683` (`sqls_solve`): the SQLS result is signed by `choose_global_sign(A, b, dq_sqls)` on the ORIGINAL unpadded A, b (line 679); the classical `dq_lu = self.lu_solve(A, b)` moved AFTER it (line 683) and is used only for the fidelity / L2 metrics and the `dq_lu` column. The old `if np.dot(dq_sqls, dq_lu) < 0: dq_sqls = -dq_sqls` is gone. Docstring (`:652-660`) rewritten accordingly.
- `time_solvers.py:561-574` (`hhl_solve`): the `true_sol` branch now applies `choose_global_sign(A, b, dq_hhl)` after scaling by `||dq_herm||` (line 567). The `leastsq` branch (the default) is UNCHANGED in code (comments only): alpha_ls = <b, A x>/<A x, A x> already fixes sign and magnitude from A and b alone, so the current default never used the LU answer for the sign. The shots-mode re-signing (`:576-581`) is unchanged and now carries a comment that it is a classical dependence.

What classical information each path still consumes for the RETURNED update (the LU solve of the same system always runs, for the metrics):
- SQLS statevector: none from fvm. Sign from A, b (this change); magnitude from `||final_b||`, which sqls computes from its own SVD (`sqls.py:398-407`, `final_b = V S^+ U^H b` is itself the classical answer in `full_svd`).
- SQLS shots: per-component signs from `sign(final_b)` inside sqls (classical, unchanged); magnitude as above; the global-sign rule is a no-op there (verified: every shots run had `dq_sqls * dq_lu >= 0` on all components).
- HHL statevector `leastsq` (default): alpha from A and b only; LU (`dq_lu`, `dq_herm`) metrics only. Bit-identical to before (gate fixture 7/7 at 1e-10, max-abs 3.0e-14 on the nelem-5 fixture).
- HHL statevector `true_sol`: magnitude `||dq_herm||` from the classical LU of the Hermitian system (as before); sign now reference-free (new).
- HHL shots (either scale): per-component signs from `dq_herm` (classical LU) -- left as is, documented in code, README ("What is classical in each quantum path") and here.

### (b) Shared fixed-basis circuit counter (commit `cca70256`)

- `quantum_tools.py:159-220`: `FB_BASIS = ('u3', 'cx')`; `count_circuit_metrics(circ, basis=FB_BASIS)` -> `{fb_depth, fb_total_gates, fb_cx_count, fb_num_qubits, fb_basis, t_count_s}`; `circuit_metrics(circ, mode)` gates it on `-circ_metrics` (`'none'` -> placeholder `-1, -1, -1, -1, 'none', 0.0`); `fairness_columns(...)` builds the eight shared CSV columns.
- Recipe: `transpile(circ.remove_final_measurements(inplace=False), basis_gates=['u3', 'cx'], optimization_level=0, seed_transpiler=0)`. Final measurements and their barrier are removed first so a measured (HHL, `measure_all` in `generate_circuit`) and an unmeasured (SQLS) circuit count the same. **optimization_level 0** because it counts the circuit as built, with no optimization passes whose heuristics change between qiskit versions; probes showed level 1 gives the SAME CX count (42 / 200 / 234899) and 7 to 15 % fewer `u3` (SQLS nelem 2: 121 vs 130 gates; nelem 5: 540 vs 574; HHL nelem 2: 530916 vs 630388). **seed_transpiler 0** only pins determinism: with `basis_gates` and no coupling map no stochastic pass runs at any level (two calls gave identical numbers in every probe). `fb_total_gates` counts every instruction of the transpiled circuit, including the `reset`s that `Initialize` expands to (3 to 5 here), the same for both solvers.
- HHL: `quantum_tools.py:706-712` the count runs on the generated circuit `circ` as step (5), AFTER the timed generate / transpile / run steps, so `circ_generate_time`, `circ_transpile_time`, `circ_run_time` keep their meaning (the one-time transpiler warm-up stays in `circ_transpile_time` as before); its own wall goes to `t_count_s`. Columns appended at `:759-762`.
- SQLS: `quantum_tools.py:966-975` the count runs on `sqls_out['qc']` (the circuit sqls built, exposed by the one-line sqls change) after `quantum_solve` returned, OUTSIDE the `solve_time` region. If the patch is missing and `-circ_metrics` is not `none`, a `RuntimeError` names the patch path (`:969-974`). sqls's own `count_cx_depth` ({u3,cx}, level 1, inside `solve_time`, `-v 2` only) is kept for the continuity columns `cx_count` / `circuit_depth` (`:944-947`), unchanged.
- CLI `-circ_metrics {none,u3cx}` default `u3cx`, `nozzle_1d_solver.py:124-133`; choices live in `math_tools.py:32-33` so the LU path imports no qiskit; passed through `linsolv_args['circ_metrics']` (`:231`, `:245`) and `time_solvers.py:292-293`, `:315`; recorded in the pickle as `circ_metrics` (`:434`). Both constructors validate the mode (`quantum_tools.py:262-265`, `:859-862`).

### (c) Effective shots (commits `cca70256` CSV, `035018cc` pickle)

- CSV column `effective_shots` in both files: SQLS `nshots * repeats` (0 in statevector mode), `quantum_tools.py:1014-1017`; HHL `nshots`, `:761-762`.
- Pickle `effective_shots`, `nozzle_1d_solver.py:436-443`: SQLS `linsolv_args['shots'] * args.sqls_repeats`, HHL `linsolv_args['shots']` (so a non-ideal HHL backend with `-shots 0`, which the CLI turns into 128, records 128). Pinned in `tests/contract.py:97-99` (`METADATA_KEYS_QUANTUM`) and `:35-38` (`QC_METADATA_FAIRNESS_COLUMNS`).
- Matched paper case arithmetic: `-shots 150000 -sqls_repeats 1` -> `effective_shots = 150000 x 1 = 150000` on every step of rung 5a (CSV and pickle); HHL at `-shots 150000` records 150000 (one run per solve). A `-shots 5000 -sqls_repeats 2` run records `nshots` 5000, `repeats` 2, `effective_shots` 10000 (test `TestSQLSEffectiveShots`). The sqls default `repeats=10` (fvm passes 1) can no longer go unrecorded.

### (d) README corrections (uncommitted, experiments repo)

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`:
- Key-results table: "Newton iters to converge | 6 | 14" -> "Newton iters | 6 (converged) | 15 (cap reached, not converged; residual ratio 5.5e-4 vs tol 1e-10)"; the "final residual (‖Ax-b‖)" row relabelled "final CFD `residual_total`" (1.26e-9 / 6.80e-3) and a new row "final linear-system residual ‖A dq - b‖ (last step) | 1.228e-9 | 3.725e-3"; the CX / gates row now says "CX only" vs "all gates".
- New "Corrections (2026-10-15, work-plan item 11 ...)" paragraph after the table stating all of the above, the basis mismatch (SQLS {u3,cx} CX-only vs HHL Aer-basis all gates, not comparable until the `fb_*` columns are used) and the fixed-basis numbers of this build.
- Caveat 4 rewritten to the padding root cause (constant 1e-8 RHS pad, ~8 of 150000 shots on the true entries at the last step; item 9 pads with zeros; last-step fidelity 0.99996 to 0.99999 after the fix: 0.99997 in the item-9 build, 0.99996 in this build's rung 5a).

### (5) `circ_qubits` for both solvers (commit `cca70256`)

CSV column `circ_qubits`: HHL `circ.num_qubits` of the generated circuit (`quantum_tools.py:761`; equals `circ_qubits_transpile` on Aer, 12 at nelem 2, 14 at nelem 5); SQLS `n_data_qubits + m_ancilla` (`:1014-1016`; 3 at nelem 2, 4 at nelem 5; `nqubits` stays the data-register width). `hhl_metrics_*.csv` keeps its name; README "Output Files" now says it holds the metrics for whichever quantum solver ran.

### (e) Seedable shots (commit `68ef63f5`)

- CLI `-seed INT` default None, `nozzle_1d_solver.py:98-104`; `linsolv_args['seed']` (`:232`, `:246`); pickle `seed` (`:435`).
- HHL: `QuantumHHL(seed=...)` (`quantum_tools.py:261`); `_run_on_backend` adds `seed_simulator=self.seed` to `run_kwargs` via `setdefault` when set (`:554-555`), so every `backend.run` for ideal and fake goes through it (`run_circuit_ibm` -> `_run_on_backend`; `run_circuit_iqm` too). The real-ibm SamplerV2 branch is unreachable (get_backend raises) and untouched.
- SQLS: `QuantumSQLS(seed=...)` (`:858`); passed as `quantum_solve(..., seed=self.seed)` only when not None (`:950`, `:961`), so an unseeded run still works against an unpatched sqls; with `-seed` an unpatched sqls raises `TypeError` from `quantum_solve` (not caught; the patch is part of the stack of record).
- CSV column `seed` in both files: the int, or `''` when unseeded (`fairness_columns`, `:218`).

### (f) `-hhl_scale` (commit `545d6b03`)

- `time_solvers.py:12-22`: `HHL_SCALE_TYPES = ('leastsq', 'true_sol')`, `HHL_SCALE_DEFAULT = 'leastsq'`, with the history (the old CLI default `'true_scale'` was not a valid choice and fell through to the least-squares branch in every April, August and current run). `LinearSystemSolver.__init__` validates the value (`:281-283`, `ValueError`, propagates: only `ImportError` is caught there).
- `nozzle_1d_solver.py:106-116`: `choices=list(HHL_SCALE_TYPES), default=HHL_SCALE_DEFAULT`, help text describes both rules; `linsolv_args` default `HHL_SCALE_DEFAULT` (`:217`); pickle `hhl_scale` for HHL runs only (`:444-445`). `-hhl_scale true_scale` is now rejected by argparse (rc 2).
- Default path numerics bit-identical: gate fixture 7/7 at 1e-10; my separate nelem-5 solve max|dq - ref| = 3.0e-14; HHL nelem-2 fixture 8.6 s OK. `tests/helpers.py:212-219` spells `'leastsq'` explicitly (was `'true_scale'`); `tests/data/provenance.json` still records the old spelling in `linsolv_args` (data, left as is, explained in TESTING.md).
- `true_sol` vs `leastsq` at nelem 2 statevector, step 0 (same system, same `dq_lu`): component-wise ratio `dq_true_sol / dq_leastsq` = 0.99859811 on all six components (spread 6.3e-15), so same direction and sign, different magnitude because the HHL direction is inexact (fidelity 0.9999986356); `||dq_true_sol|| - ||dq_herm||` = -7.0e-14; `||dq_leastsq||` = 0.5448108 vs `||dq_herm||` = 0.5440470. Whether the paper's HHL control switches to `true_sol` stays Andy's open question 10; both are now explicit, testable and recorded.

### (8) Docs (commit `484b24ed`)

- `README.md`: "ideal shots runs use Aer's own `SamplerV2`" -> "call `AerSimulator.run` directly, with `seed_simulator` when `-seed` is given" (Dependencies); SQLS in the solver lists; `-seed`, `-hhl_scale`, `-circ_metrics`, `-sqls_*` rows in the arguments table; "Output Files" extended (hhl_metrics note, qc_metadata, dq, system pickles); new sections "Circuit metrics and fairness columns" (column table, recipe, continuity columns, measured counts) and "What is classical in each quantum path".
- `TESTING.md`: item-11 suite counts and timings, layout rows, new sections (g) to (k), gate note, hhl_scale spelling note, seed note.

## Measured fixed-basis counts and counting cost ({u3, cx}, optimization_level 0; this build, qiskit 2.5.2)

| circuit | circ_qubits | fb_cx_count | fb_depth | fb_total_gates | t_count_s | continuity columns (same step) |
|---|---|---|---|---|---|---|
| SQLS full_svd nelem 2, steps 0/1/2 (statevector, rung 3) | 3 | 42 / 42 / 42 | 88 / 88 / 88 | 130 / 130 / 130 | 0.592 s (step 0, incl. warm-up) / 0.0023 s / 0.0022 s | `cx_count` -1 (`-v 1`); `solve_time` 1.3 / 0.8 / 0.45 ms |
| SQLS full_svd nelem 5, steps 0/1/2 (statevector, `-v 2`, rung 3) | 4 | 200 / 201 / 200 | 400 / 401 / 400 | 574 / 577 / 572 | 0.523 s / 0.0044 s / 0.0046 s | sqls level-1 `cx_count` 200 / 201 / 200, `circuit_depth` 398 / 399 / 398 |
| SQLS full_svd nelem 5, 150000 shots, steps 0..6 (rung 5a) | 4 | 200, 201 x 6 | 400 | 574, 574, 574, 575, 575, 575, 575 | 0.559 s then 0.0048 to 0.0050 s | `solve_time` 0.017 s then 0.010 to 0.013 s |
| HHL nelem 2, steps 0/1 (statevector; 12 qubits) | 12 | 234899 / 234899 | 470394 | 630388 | 1.098 s / 1.017 s (in-process repeats 1.66, 1.09, 1.03 s) | Aer basis: depth 68963 / 69203, gates 74796 / 75215; generate 1.75 / 1.85 s, transpile 2.20 / 1.63 s, run 3.18 / 3.18 s |
| HHL nelem 5, step 0 (ONE statevector solve of the archived system; 14 qubits) | 14 | 2054602 | 4067708 | 5455676 | **9.23 s** | Aer basis: depth 596687, gates 641072 (August: 596688 / 641145); generate 18.67 s, transpile 14.21 s, run 51.26 s; `hhl_solve` wall 95.0 s |

Counting cost verdict: 9.2 s per iteration at nelem 5 is well under the ~60 s threshold (and under the Aer transpile of the same circuit, 14.2 s), so the default stays `u3cx`; no size gating is needed at paper sizes. The cost is roughly linear in the {u3,cx} gate count (~1.7 us per emitted gate here), so `-circ_metrics none` is the switch for anything much bigger. Step 0 of an SQLS run also pays the one-time transpiler warm-up in `t_count_s` (0.52 to 0.59 s in the rung runs, 6.05 s once in the very first run of the session); for HHL the warm-up lands in `circ_transpile_time` as before because the Aer transpile runs first. The harvester should take the median (or steps >= 1) of `t_count_s`.

Fixed-basis gate ratio HHL / SQLS at nelem 5 (same step-0 system): CX 2054602 / 200 = 1.03e4, total gates 5455676 / 574 = 9.5e3, depth 4067708 / 400 = 1.0e4 -- an order of magnitude larger than the mixed-basis ratio quoted in August (641145 / 201 = 3.2e3), because the Aer basis keeps ccx / cu / crz whole.

## Commands run (from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, `MPLBACKEND=Agg`, `-outdir /tmp/order3-build-11/...`; wall = `/usr/bin/time -p` real)

`B = -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`, `PY = .venv/bin/python nozzle_1d_solver.py`.

| rung | command | wall | result |
|---|---|---|---|
| 3 nelem 2 | `PY -nelem 2 -linsolver SQLS -shots 0 -iters 3 -sqls_method full_svd B` | 2.45 s | rc 0; max abs(dq_lu - dq_sqls) 3.05e-16 / 2.78e-17 / 5.08e-20 (<= 1e-12); fidelity 1 - 2e-16, 1.0, 1 - 2e-16; linsys_residual 1.47e-15 / 6.23e-17 / 3.33e-19; residual_total 1.3141049901831434 -> 0.013898239383409517 -> 1.3263305324237676e-4 (identical to build 09) |
| 3 nelem 5 | same with `-nelem 5` | 2.31 s | rc 0; dq diffs 2.00e-15 / 1.25e-16 / 1.39e-17; fidelity 1.0 / 1 + 4e-16 / 1 + 4e-16; linsys 4.76e-14 / 2.84e-15 / 2.13e-16; residual_total 12.375368413827264 -> 0.568679135231724 -> 0.05832885640886122 (identical to build 09) |
| 3b | `PY -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 B` | 2.21 s | rc 0; fidelity 0.99992398 / 0.99994886; linsys 4.08e-2 / 5.71e-4; all `dq_sqls * dq_lu >= 0`; `effective_shots` 10000, `seed` empty |
| 4b | `PY -nelem 2 -linsolver HHL -shots 1000 -iters 1 B` | 9.00 s | rc 0; fidelity 0.93927 (unseeded); linsys 0.850; `circ_qubits` 12, fb 234899 CX / 470394 / 630388, `t_count_s` 1.11 s; `effective_shots` 1000; pickle `hhl_scale` leastsq, `seed` None, `circ_metrics` u3cx |
| 5a matched | `PY -nelem 5 -linsolver SQLS -shots 150000 -iters 15 -sqls_method full_svd -sqls_repeats 1 B` | 2.33 s | rc 0; converged (`dq_norm`) at step 6, 7 solves; fidelity 0.99998018, 0.99998004, 0.99997383, 0.99996350, 0.99998027, 0.99998978, 0.99996288 (every step >= 0.9999, last step 0.99996); residual_total 12.3754 -> 1.3524e-9; last linsys_residual 1.16e-11; `effective_shots` 150000 on every row; solver elapsed 0.743 s |
| HHL sv nelem 2 | `PY -nelem 2 -linsolver HHL -shots 0 -iters 2 B` | 18.35 s | rc 0; the HHL fb row above |
| seeded SQLS x 2 | `PY -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 -seed 7 B` | 2.17 s, 2.23 s | identical `dq_*.csv` (md5 a65547220a472bf179a323a813d242ba, 5ad1ddb15a4f58675613954beb4c862e in both), fidelity 0.9999780104544436 / 0.9998980289752558 in both; CSV `seed` 7, `effective_shots` 10000 |
| seeded HHL x 2 | `PY -nelem 2 -linsolver HHL -shots 1000 -iters 1 -seed 7 B` | 8.87 s, 8.71 s | identical `dq_*.csv` (md5 22004dd46d6ac272204c31bee25c6152), fidelity 0.9901186807697129 in both; unseeded run of the same case: fidelity 0.813898967131267, different dq (md5 e76a36b281f4a96a7628de57582a5802) |
| hhl_scale | `PY -nelem 2 -linsolver HHL -shots 0 -iters 1 -hhl_scale true_sol B` | 22.50 s (ran concurrently with the gate fixture) | rc 0; numbers in (f) above; pickle `hhl_scale` true_sol. `-hhl_scale true_scale`: rc 2, `invalid choice: 'true_scale' (choose from leastsq, true_sol)`, no file written |
| gate fixture | `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` (2026-10-15T08:28:37Z) | 103.9 s | **7/7 OK** at 1e-10 (nelem-5 HHL 94.37 s, nelem-2 HHL 8.63 s, SQLS 0.09 s and 0.01 s, provenance 3 tests) |
| nelem-5 HHL solve | `/tmp/order3-build-11/hhl_n5_count.py` (in-process `LinearSystemSolver.hhl_solve` on `tests/data/system_Ab_nelem5_iter0.pkl`, the second and last nelem-5 solve) | 96.2 s | fidelity 0.999957137763, linsys 4.2067e-2, max abs(dq - ref_hhl_nelem5_iter0) 3.0e-14; the fb row above. The follow-up qpy reload of the saved generated circuit failed (`ExactReciprocalGate.__init__() missing ... 'num_state_qubits' and 'scaling'`), so no in-process re-count; one measurement |
| suite, unittest | `.venv/bin/python -m unittest discover -s tests -v` (2026-10-15T08:35:48Z) | 108.2 s | `Ran 128 tests in 107.246s` / `OK (skipped=1)` |
| suite, pytest | `.venv/bin/python -m pytest tests -q -p no:cacheprovider` (ended 2026-10-15T08:39:27Z) | 109.9 s | `127 passed, 1 skipped, 1 warning, 40 subtests passed in 108.97s`; the warning is runtime's own `fake_nighthawk` properties warning (pre-existing) |

No sweeps, no Frontier, no network, no background jobs. Exactly two nelem-5 HHL statevector solves were run (the gate fixture's and the counting one) plus no 15-minute matched HHL run.

## New tests (32; 96 -> 128)

- `tests/test_sqls.py`: `TestSQLSReferenceFreeSign` (3: the rule on a 2 x 2 system incl. ties and an inexact direction; `sqls_solve` with `lu_solve` corrupted to `-solve(A, b)` on the archived nelem-2 and nelem-5 systems returns +x to 1e-12 while `l2_error_abs` = 2||x|| and the `dq_lu` column is negated; back-end output negated AND LU corrupted still gives +x), `TestSQLSSeededShots` (3), `TestSQLSEffectiveShots` (3).
- `tests/test_hhl.py`: `TestHHLSeededShots` (3; seeded floor 0.98), `TestRunOnBackendSeed` (2; `backend.run` kwargs captured with `mock.patch.object(..., wraps=...)`), `TestHHLScale` (3).
- `tests/test_circuit_metrics.py` (new): `TestCountCircuitMetrics` (5: Bell = 1 CX / 2 gates / depth 2; measurements excluded; cx, cx, ccx = 8 CX; modes; constructors reject an unknown mode), `TestFixedBasisColumnsSQLS` (2), `TestFixedBasisColumnsHHL` (1), `TestCircMetricsCLI` (3).
- `tests/test_cli.py`: `test_hhl_scale_invalid_choice_rejected` (1); `-h` test extended to `-seed`, `-circ_metrics`.
- `tests/test_output_contract.py`: `test_fairness_columns` on the three quantum contract runs (3); `test_metadata_pickle` extended (`circ_metrics`, `seed`, `effective_shots`, `hhl_scale` HHL-only).
- `tests/contract.py`: `QC_METADATA_FAIRNESS_COLUMNS` appended to both column lists, `FB_BASIS_TAG`, `CIRC_METRICS_*`, `METADATA_KEYS_QUANTUM` + `circ_metrics`, `seed`, `effective_shots`; `METADATA_KEYS_HHL_ONLY = ['hhl_scale']`, `HHL_SCALE_TYPES`, `HHL_SCALE_DEFAULT`.

## New columns and keys for the harvester follow-up

Both `qc_metadata_nelem*_*.csv` (HHL) and `qc_metadata_sqls_nelem*_*.csv` (SQLS) end with these eight columns, in this order, after the unchanged existing columns (21 HHL, 17 SQLS):

| column | type | units | meaning |
|---|---|---|---|
| `circ_qubits` | int | qubits | actual circuit width. HHL: generated circuit (= `circ_qubits_transpile` on Aer). SQLS: `n_data_qubits + m_ancilla`. Prefer over `nqubits` |
| `fb_depth` | int | layers | depth of the circuit transpiled to {u3, cx} at optimization_level 0 (final measurements removed first); -1 when `-circ_metrics none` |
| `fb_total_gates` | int | instructions | all instructions of that transpiled circuit (u3 + cx + the resets of `Initialize`); -1 when none |
| `fb_cx_count` | int | CX gates | CX count of that transpiled circuit; -1 when none |
| `fb_basis` | str | - | `u3cx`, or `none` when the counter was skipped |
| `t_count_s` | float | s | wall time of the counting transpile; excluded from `solve_time` and from `circ_generate_time` / `circ_transpile_time` / `circ_run_time`; step 0 of an SQLS run includes the one-time transpiler warm-up (0.5 to 6 s); 0.0 when none |
| `effective_shots` | int | measurements per solve | SQLS `nshots x repeats`, HHL `nshots`; 0 in statevector mode |
| `seed` | int or empty | - | the `-seed` value; EMPTY string when unseeded (parse as nullable int) |

`metadata_*.pkl` (quantum runs) new top-level keys: `circ_metrics` (str, `none` | `u3cx`), `seed` (int or None), `effective_shots` (int, same rule as the column), and for HHL only `hhl_scale` (str, `leastsq` | `true_sol`). Unchanged: `backend_type`, `backend_method`, `nshots`, `quantum_circuit` (its key set is unchanged: `backend_type, backend_method, use_gpu` for HHL, plus `method, k, state_prep, repeats` for SQLS). `hhl_metrics_*.csv`, `dq_*.csv`, `results_*`, `residual_*`, `final_results_*`, file names and globs: unchanged.

## Open doubts

1. `-loadcirc` is broken on this stack independently of item 11: `qpy.load` of a saved generated HHL circuit raises `TypeError: ExactReciprocalGate.__init__() missing 2 required positional arguments` (the fork's ported gate is not qpy-round-trippable). Observed while trying to re-count the nelem-5 circuit; not fixed (fork repo, item 15 territory). It also means no second timing sample exists for the nelem-5 count (9.23 s, one measurement).
2. `fb_total_gates` includes the `reset`s that `Initialize` expands to (both solvers' state preparation uses `Initialize`): 3 to 5 instructions, negligible, but it is why `fb_total_gates - fb_cx_count` is not exactly the u3 count.
3. The SQLS continuity columns `cx_count` / `circuit_depth` (sqls's level-1 count) remain `-v 2`-only and INSIDE `solve_time` (finding 4 of report 04, not in this item's scope). For paper timings run at `-v 1` (default) and quote `fb_*`; `solve_time` is then free of any transpile.
4. HHL shots mode still takes per-component signs from the classical `dq_herm` (left as instructed, documented). The HHL `leastsq` scaling is reference-free but still a classical post-processing of the quantum direction; `true_sol` uses the classical norm.
5. The one unseeded HHL shots draw during this build had fidelity 0.814, close to the unseeded floor 0.8 in `TestHHLShotsNelem2` (previous observations 0.937 to 0.97). Left at 0.8 as instructed; the seeded class pins 0.98. A rare unseeded failure of that test is possible.
6. The fvm SQLS path now requires the patched sqls (`sqls_out['qc']`) unless `-circ_metrics none`; `-seed` with an unpatched sqls raises `TypeError` inside `quantum_solve`. Both are consistent with the stack of record (patched clone), but a node that forgets to apply the patch fails loudly on the first SQLS solve.
7. The warm-up share of step-0 `t_count_s` varies (0.52 s typical, 6.05 s once in the first run of the session, probably page-cache / plugin discovery); the harvester should not read step 0 as the counting cost.
8. `fb_basis` and `seed` are string-typed columns (the SQLS CSV already had `method`, `state_prep`, `aer_device`); `seed` is empty when unseeded, so a numeric parser needs a nullable int.
9. The experiments README correction quotes this build's fixed-basis numbers (not August artifacts: the August HHL `.qpy` circuits were never archived, so the August circuits themselves cannot be re-counted); the step-0 system is bit-identical to August's, the circuit is the ported fork's.

## Fix-up round note (2026-10-15T10:55Z, builder 6, fvm commit `e50f4800` plus docs `27545386`)

Item-11 review findings implemented in the fvm fix-up round that also closed item 6 (details and verification in `build-06.md`, section "Fix-up round"):

- Q1: `QuantumSQLS.__init__` probes `inspect.signature(quantum_solve)` for the keyword-only `seed` and raises `RuntimeError` with the `sqls-patches/` hint before any solve; a stock sqls now fails at construction (test `TestSQLSUnpatchedProbe`).
- Q2: the HHL fixed-basis count is cached per `QuantumHHL` instance on the generated circuit's structure (width plus the instruction sequence, qiskit's auto-generated `circuit-<n>` names normalized; the first key attempt on `count_ops()` missed because of those names); reused rows carry `t_count_s` 0.0 and the new bool column `fb_cached` (ninth fairness column, after `t_count_s`; SQLS always False; empty under `-circ_metrics none`). Two-step nelem-2 HHL: step 0 1.10 s / False, step 1 0.0 s / True, identical 470394 / 630388 / 234899.
- Q3: `_run_on_backend` passes `seed_simulator` only for `backend_type in ('ideal', 'fake')`.
- Q4: `helper_tools.append_csv_row` writes the three per-step CSVs; a stale header rotates the old file to `<outdir>/rotated/<name>.pre-<UTC>.csv` (subdirectory, not a sibling, so the harvester's singleton globs keep matching one file) and logs one `[csv]` line.
- Q5: SQLS `circ_qubits` = `qc.num_qubits` of the circuit sqls built (fallback `n_data_qubits + m_ancilla`); the unused `fb_num_qubits` key was dropped.
- Q6: `circ_qubits` documented as the authoritative width, `circ_qubits_orig` / `circ_qubits_transpile` as legacy (README, `tests/contract.py`).
- Q7: `QuantumSQLS` docstring now states the reference-free sign rule.
- N1: a non-ideal HHL backend without `-shots` sets `args.nshots` to the 128 actually used, so the case name, pickle `nshots` / `effective_shots` and file names agree (not exercised by the suite: no fake backend wide enough for the 12-qubit circuit runs in test time).
- Doubt 5 above is closed: the unseeded HHL floor is 0.7 since `63bd1b07`.

## Final fix-up round note (2026-10-15T11:50Z, builder 6; details in `build-06.md`, "Final fix-up round")

- Z2 (`a87bb510`): `QuantumSQLS.__init__` now runs a 2 x 2 `full_svd` statevector probe solve on its Aer backend after the signature check: `seed=` must be accepted, `sqls_out['qc']` must be exposed, and the answer must equal A^-1 b; any failure raises `RuntimeError` with the `sqls-patches/` hint before the first real solve. Measured 1.2 to 1.4 ms on the first instance of a process, 0.3 to 0.4 ms on later ones (`probe_time_s`, asserted < 50 ms in `TestSQLSUnpatchedProbe`); `quantum_solve`'s own timing prints are swallowed. Negative test: a stub that accepts `seed` but exposes no `qc` is refused at construction.
- Z3 (`651fc276`): `helper_tools.append_csv_row` treats a zero-byte or truncated existing file (empty first line) as new (header written, no rotation, no log line); the rotation stamp has microsecond precision (`%Y%m%dT%H%M%S.%fZ`) and a `-1`, `-2`, ... suffix on a name collision. Exercised on a scratch dir (empty `qc_metadata_sqls_*.csv` plus a stale `hhl_metrics_*.csv`: only the stale one rotated) and with two back-to-back rotations (`twice.pre-20261015T114840.495316Z.csv`, `...498295Z.csv`).
- Z6 (`cdf7103b`): `hhl_kernel_rel_err` reuses the least-squares matvec (`alpha_ls * A_dq_hhl - b`); the `true_sol` and shots branches form their one matvec after the sign step.
- Z7 (`95782e61`): the `_deflate<k>` qpy suffix lives once in `math_tools.deflate_suffix`, used by `QuantumHHL.qpy_path` (one builder for the generated and transpiled circuit names) and by `tests/contract.py expected_files`.
- Z1 (`d8a071ba`, item 6 / item 11 shared): the fixed-basis count cache key is now `quantum_tools.circuit_key`, a sha256 of the full circuit data including parameters; the item-11 `fb_cached` column keeps its meaning (True = count reused). Default `-circ_metrics u3cx` is exact per step again; `-circ_metrics u3cx-once` is the opt-in that declares later rows cached. Cost of the exact key: ~0.36 s for the 12-qubit nelem-2 circuit, 2.98 s for the 14-qubit nelem-5 circuit, included in `t_count_s` of a fresh row.
