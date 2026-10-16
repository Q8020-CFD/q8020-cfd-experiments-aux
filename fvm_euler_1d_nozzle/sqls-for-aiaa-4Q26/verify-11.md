VERDICT: PASS

# verify-11 — independent verification of work item 11 (benchmark-fairness fixes)

- Verifier session: 2026-10-15T08:49:23Z to 2026-10-15T09:11Z (UTC), Mac laptop, read-only.
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`,
  HEAD `484b24ed`, working tree clean (`git status --short` empty). Item range
  `e13cbb1e..484b24ed` = 6 commits: `005f05b2` (sign rule), `cca70256` (fixed-basis counter,
  `-circ_metrics`, 8 fairness columns), `68ef63f5` (`-seed`), `035018cc` (`effective_shots`),
  `545d6b03` (`-hhl_scale`), `484b24ed` (README/TESTING).
- Also in scope: uncommitted `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`
  (branch `local/sampler-port-2026-10`, HEAD `9a4346a7`) and the uncommitted edit to
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`
  (experiments HEAD `6f646617`).
- Python: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python` 3.12.10,
  qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0; `sqls` imported from
  `/Users/agallojr/proj/src/q8020/sqls/src/sqls/`.
- Scratch: `/tmp/order3-verify-11/` (all `-outdir` targets and probe scripts), deleted at the end.
  No file was created or modified anywhere else; this report is the only new file in this folder.

All ten acceptance criteria hold. Two literal deviations from the criterion text are recorded
(D1, D2 below) and judged not to be defects; four low-severity findings are listed, none of them
blocking. PASS is given on the reading that a `-1` / `none` / `0.0` sentinel row is an acceptable
realisation of "columns empty/None" for `-circ_metrics none` (D1); if the orchestrator wants
literally empty fields, that is a three-line change in `quantum_tools.circuit_metrics`.

## Summary table

| # | Criterion | Result | Key evidence |
|---|---|---|---|
| 1 | (a) reference-free SQLS sign; HHL classical dependencies; default HHL path byte-identical; rung 3; rung 5a | PASS | `math_tools.choose_global_sign`; garbage-LU probe gives bitwise-identical dq; gate 7/7; rung 3 max diff 2.0e-15; rung 5a min fidelity 0.99997 |
| 2 | (b) shared counter, columns independent of `-v`, `-circ_metrics`, independent counts | PASS (D1) | own transpile = helper = CSV on a 3-CX circuit, SQLS nelem 5 (200/400/574) and HHL nelem 2 (234,899/470,394/630,388); HHL nelem 5 2,054,602 CX, t_count_s 9.65 s |
| 3 | (c) `effective_shots` | PASS | 5000 x 2 -> 10000 in CSV and pickle; HHL 1000; statevector 0; pinned in `tests/contract.py` |
| 4 | (d) August README corrections | PASS | all four elements present; numbers re-derived from the archived CSVs (ratio 5.491e-4, 1.2276e-9 vs 3.7252e-3); only README.md changed in that folder |
| 5 | `circ_qubits` | PASS | HHL 12 / 14; SQLS 3 / 4 |
| 6 | (e) `-seed` | PASS | seeded pairs byte-identical (sha256), unseeded pairs differ; seed in CSV and pickle; sqls `quantum_solve(..., *, seed=None)` |
| 7 | (f) `-hhl_scale` | PASS | choices `{leastsq,true_sol}`, default leastsq; `true_scale` rc 2; pickle `hhl_scale`; true_sol finite; gate 7/7 |
| 8 | tests | PASS (F4) | unittest 128 tests OK, 1 skip, 107.13 s; gate 7/7 112.03 s; floors documented; unseeded HHL floor flake risk estimated at 0.34 % per run |
| 9 | hygiene | PASS | 0 added lines > 88 chars, 0 trailing whitespace, no non-top imports; README lines 337-339 say `AerSimulator.run` |
| 10 | nothing pushed, pins | PASS | no `origin/feature/sqls-aiaa-4q26`; main = origin/main = `ef7f0a8b` (2026-08-17); sqls `9a4346a7`; experiments `6f646617` |

## Criterion 1 — (a) reference-free global sign — PASS

Code path (read, not inferred). `time_solvers.LinearSystemSolver.sqls_solve` now does, in order:
`dq_sqls = self.sqls_solver.solve_one_step(A, b, ...)`, then
`dq_sqls = choose_global_sign(A, b, dq_sqls)` on the ORIGINAL unpadded `A`, `b`, and only then
`dq_lu = self.lu_solve(A, b)` "used ONLY for the metrics below and the dq_lu column". The rule is
`math_tools.choose_global_sign(A, b, x)`: one matvec `ax = A @ x`, keep `x` if
`||ax - b|| <= ||ax + b||` else `-x` (tie keeps `+x`). The old `if np.dot(dq_sqls, dq_lu) < 0`
flip is gone (`git diff e13cbb1e..484b24ed -- time_solvers.py`).

HHL classical dependencies after the diff (`hhl_solve`):
- `leastsq` (default): `alpha_ls = (b @ A_dq_hhl) / (A_dq_hhl @ A_dq_hhl + 1e-15)` from `A`, `b`
  only; `dq_lu` and `dq_herm` feed the metrics and `dq_lu` column only.
- `true_sol`: `dq_hhl *= np.linalg.norm(dq_herm)` (classical LU norm of the Hermitian system)
  then `choose_global_sign(A, b, dq_hhl)` (sign reference-free). New in this item.
- shots mode (either rule): `dq_hhl = np.abs(dq_hhl) * dq_herm / (|dq_herm| + 1e-15)` — the
  per-component signs come from the classical Hermitian LU solution; the comment documents it
  ("documented, kept as is"). This classical dependence remains and is correctly disclosed in
  README "What is classical in each quantum path".

Default HHL path untouched: in the diff the `else:` branch's three code lines
(`A_dq_hhl = A @ dq_hhl`, `alpha_ls = ...`, `dq_hhl *= alpha_ls`) appear only as context; only the
trailing comment on the `else:` line changed. The CLI default moved from the invalid string
`'true_scale'` (which fell through to this `else`) to `'leastsq'` (which selects it explicitly):
same branch, same arithmetic.

Gate fixture (`FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`,
2026-10-15T08:56:04Z to 08:57:59Z, 114.83 s process): 7/7 OK at `MAX_ABS_TOL = 1e-10`
(TestHHLFixture nelem2 8.94 s, nelem5 98.32 s; TestSQLSFixture nelem2 3.52 s, nelem5 1.25 s;
3 provenance tests). Log was at `/tmp/order3-verify-11/gate-fixture.log`.

Own in-process probes (`/tmp/order3-verify-11/probe_inprocess.py`, archived step-0 systems
`tests/data/system_Ab_nelem{2,5}_iter0.pkl`), beyond the suite's `TestSQLSReferenceFreeSign`:

| nelem | probe | dq bitwise-equal to intact-LU baseline | max abs dq - x_true | metrics fidelity vs corrupted ref | linsys residual |
|---|---|---|---|---|---|
| 2 | `lu_solve` returns a fixed random vector | True | 1.11e-16 | 0.2248 (metrics follow the garbage ref, dq does not) | 1.47e-15 |
| 2 | back-end returns -x AND `lu_solve` returns -x | True | 1.11e-16 | - | 1.47e-15 |
| 5 | `lu_solve` returns a fixed random vector | True | 2.22e-15 | 0.0054 | 4.76e-14 |
| 5 | back-end returns -x AND `lu_solve` returns -x | True | 2.22e-15 | - | 4.76e-14 |

Sign margins: nelem 2 `||A(+x)-b|| = 1.47e-15` vs `||A(-x)-b|| = 2.63`; nelem 5 `4.76e-14` vs
`24.75`. The suite's own test (`tests/test_sqls.py::TestSQLSReferenceFreeSign`, three tests)
covers the same two corruptions and the rule's tie cases; read and passing.

Rung 3 (`-nelem {2,5} -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 3
-initers 1 -noshow`, 2.4 s and 2.5 s wall): max |dq_lu - dq_sqls| per step
nelem 2: 3.05e-16, 2.78e-17, 5.08e-20 (worst 3.05e-16); nelem 5: 2.00e-15, 1.25e-16, 1.39e-17
(worst 2.00e-15). Both <= 1e-12. Fidelity 1.0 at every step.

Rung 5a (`-nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15
-initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow`, 2.5 s wall, converged at
iteration 6, 7 solves): fidelity 0.99997895, 0.99997895, 0.99997172, 0.99998998, 0.99998564,
0.99996986, 0.99998667 — min 0.999970 >= 0.9999 at every step including the last (item-9 padding
fix holds). `linsys_residual` last step 4.96e-12; `residual_total` 1.85e-9.

## Criterion 2 — (b) shared fixed-basis counter — PASS (deviation D1)

Counter: `quantum_tools.count_circuit_metrics(circ, basis=FB_BASIS)` with `FB_BASIS = ('u3','cx')`:
`transpile(circ.remove_final_measurements(inplace=False), basis_gates=['u3','cx'],
optimization_level=0, seed_transpiler=0)`, returns `fb_depth`, `fb_total_gates` (every
instruction incl. the `reset`s of an `Initialize`), `fb_cx_count`, `fb_num_qubits`, `fb_basis`
('u3cx'), `t_count_s`. Recipe documented in the docstring, `tests/contract.py` and README
"Circuit metrics and fairness columns". Applied to BOTH circuits: HHL on the generated `circ`
after step 4 (`circuit_metrics(circ, self.circ_metrics)`), SQLS on `sqls_out['qc']` after
`t_solve` is taken. Gate `circuit_metrics(circ, mode)`: `'none'` returns the placeholder row
without transpiling; CLI `-circ_metrics {none,u3cx}` default `u3cx`
(`math_tools.CIRC_METRICS_CHOICES/DEFAULT`); `-circ_metrics bogus` -> rc 2 "invalid choice".

Columns independent of `-v` (SQLS nelem 2 statevector, `-iters 2`, `-v 0` 2.6 s / `-v 1` 3.4 s /
`-v 2` 6.4 s): headers identical (25 columns, last eight
`circ_qubits, fb_depth, fb_total_gates, fb_cx_count, fb_basis, t_count_s, effective_shots, seed`);
`fb_depth 88, 88`, `fb_total_gates 130, 130`, `fb_cx_count 42, 42`, `fb_basis u3cx`,
`circ_qubits 3`, `effective_shots 0`, `seed ''` identical across the three; `t_count_s` > 0 in all
(0.64 s / 1.41 s / 0.0017 s at step 0 — at `-v 2` sqls's own `count_cx` transpile warms the
transpiler first, inside `solve_time`). The continuity columns behave as documented:
`cx_count`/`circuit_depth` are `-1` at `-v 0/1` and `42 / 86` at `-v 2`.

`-circ_metrics none` (SQLS nelem 2, 1.8 s): `fb_depth -1, fb_total_gates -1, fb_cx_count -1,
fb_basis none, t_count_s 0.0`; `circ_qubits 3`, `effective_shots 0`; pickle `circ_metrics 'none'`;
solve unchanged (max |dq_lu - dq_sqls| 3.05e-16); stdout contains no transpile message. The
transpile is skipped by construction (`circuit_metrics` returns before `count_circuit_metrics`).
D1: the criterion says "empty/None"; the implementation writes the sentinel `-1` (ints),
`'none'`, `0.0`, consistent with the pre-existing `cx_count = -1` convention and pinned by
`tests/test_circuit_metrics.py::TestCircMetricsCLI`. Not a defect; noted as a wording deviation.

Independent counts (`/tmp/order3-verify-11/probe_inprocess.py`, `probe_hhl_circ.py`):

| circuit | my transpile (u3/cx, level 0, seed 0) | helper | CSV | match |
|---|---|---|---|---|
| 2-qubit, exactly 3 CX + h, rx, ry, z, s, measure_all | cx 3, depth 7, total 8 (u3 5) | cx 3, depth 7, total 8 | - | yes; input not mutated (measure kept) |
| SQLS nelem 5 step-0 system (4 qubits: Initialize + 2 UnitaryGate) | cx 200, depth 400, total 574 (u3 370, reset 4) | 200 / 400 / 574 | 200 / 400 / 574 | yes |
| SQLS nelem 5 rung-5a step-1 system | cx 201, depth 402, total 580 | 201 / 402 / 580 | 201 / 402 / 580 | yes |
| HHL nelem 2 generated circuit (12 qubits, regenerated in-process from the run's `system_Ab_nelem2_iter0.pkl` via `QuantumHHL.generate_circuit`) | cx 234,899, depth 470,394, total 630,388 (u3 395,485, reset 4) | same | same | yes |

Rung 5a CSV (`qc_metadata_sqls_nelem5_full_svd_shots150000.csv`, 7 rows): `fb_cx_count`
200, 201, 200, 200, 201, 200, 200; `fb_depth` 400, 402, 400, 400, 400, 400, 400;
`fb_total_gates` 574, 580, 572, 572, 575, 572, 572; `fb_basis u3cx`; `t_count_s` 0.548 s then
0.0046 to 0.0050 s; `solve_time` 0.011 to 0.021 s. CX 200/201 as expected; depth 400 at six steps
and 402 at step 1 (expected "400 or 401": see F3 — the 402 is real, confirmed by my own transpile
of that step's system; shots runs are unseeded so the step-1 system differs run to run).

HHL nelem 2 statevector (`-iters 1`, 10.4 s wall): `fb_cx_count 234,899` (expected ~234,899),
`fb_depth 470,394`, `fb_total_gates 630,388`, `t_count_s 1.06 s`; Aer-basis continuity columns
`circ_depth_transpile 68,963`, `circ_gates_transpile 74,802`.

HHL nelem 5 statevector (the one allowed solve, `-iters 1`, 2026-10-15T09:03:44Z to 09:05:24Z,
99.84 s wall): `fb_cx_count 2,054,602` (expected ~2,054,602), `fb_depth 4,067,708`,
`fb_total_gates 5,455,676`, `t_count_s 9.65 s` (expected ~9 s), `circ_generate_time 18.55 s`,
`circ_transpile_time 14.28 s`, `circ_run_time 51.57 s`, Aer-basis `circ_depth_transpile 596,687`
/ `circ_gates_transpile 641,101`, fidelity 0.999957. These are the numbers the two READMEs quote.

`t_count_s` exclusion: SQLS `t_solve` is taken immediately after `quantum_solve` returns and before
`circuit_metrics` (code), and the data agree: step 0 `t_count_s` 0.55 to 1.41 s against
`solve_time` 0.002 to 0.021 s. HHL: the count runs after step 4; the three timings are measured
inside their own steps (code). Data: 18.55 + 14.28 + 51.57 = 84.40 s of timed steps + 9.65 s count
+ ~5.8 s of untimed work (imports, LU, pickles) = 99.84 s wall; had the count been inside
`circ_run_time` that column would read ~61 s, and the stdout "extracting exact hhl solution"
line equals `circ_run_time` (51.57 s).

## Criterion 3 — (c) effective_shots — PASS

- SQLS `-nelem 2 -shots 5000 -sqls_repeats 2 -iters 1` (2.4 s): CSV `repeats 2`,
  `effective_shots 10000`; pickle `nshots 5000`, `effective_shots 10000` (type `int`),
  `quantum_circuit.repeats 2`.
- SQLS 10000 shots x 1 repeat: `effective_shots 10000` in CSV and pickle (all four seed runs).
- SQLS statevector (rung 3, rung 5a at 150000 shots): `effective_shots 0` resp. `150000` in both.
- HHL 1000 shots: CSV and pickle `effective_shots 1000`; HHL statevector: `0`.
- Code: SQLS `self.nshots * self.repeats if self.nshots else 0`; HHL `self.nshots`; pickle
  `linsolv_args['shots'] * args.sqls_repeats` (SQLS) / `linsolv_args['shots']` (HHL).
- Pinned: `tests/contract.py` `QC_METADATA_FAIRNESS_COLUMNS` (in both column lists),
  `METADATA_KEYS_QUANTUM` includes `effective_shots`; `tests/test_sqls.py::TestSQLSEffectiveShots`,
  `tests/test_output_contract.py` (CSV column equals pickle value).

## Criterion 4 — (d) August README corrections — PASS

`git -C /Users/agallojr/proj/src/q8020/q8020-cfd-experiments diff -- aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`:
- Iterations row now `| Newton iters | 6 (converged) | 15 (cap reached, not converged; residual
  ratio 5.5e-4 vs tol 1e-10) |` (was `14`).
- Residual row relabelled `| final CFD \`residual_total\` | 1.26e-9 | 6.80e-3 |`; new row
  `| final linear-system residual ‖A dq - b‖ (last step) | 1.228e-9 | 3.725e-3 |`.
- Caveat 4 "Fidelity tail collapse (root cause found, fixed)" cites the `convert_to_pow2` 1e-8 pad
  as the cause and the post-fix last-step fidelity 0.99996 to 0.99999 (item 9 build 0.99997, item 11
  run 0.99996); my rung 5a last step gave 0.99998667, consistent.
- A "Corrections (2026-10-15 ...)" paragraph states the basis mismatch (SQLS CX-only {u3,cx} vs
  HHL all-gates Aer basis) and points to the `fb_*` columns; the key-results row also now says
  "CX only" / "all gates".

Re-derived from the archived source runs (not the README): HHL
`results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/residual_nelem5_HHL_statevector_nshots150000.csv`
has 15 rows (iters 0 to 14), first 12.3754, last 6.7953e-3, ratio 5.4910e-4; pickle
`max_iters 15`, `final_iters 14` -> the cap was reached. `hhl_metrics` last row
`linsys_residual 3.7252e-3`. SQLS
`.../2026-08-17-sqls-local-v2/trial_0`: 7 rows, final `residual_total 1.2604e-9`, `hhl_metrics`
last row `linsys_residual 1.2276e-9`, fidelity 0.4510 at iter 6 (the collapse). All README figures
check out. `git status --short -- aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/` lists only
` M .../README.md`.

## Criterion 5 — circ_qubits — PASS

HHL: `circ_qubits 12` (nelem 2) and `14` (nelem 5) = `circ.num_qubits` of the generated circuit =
`circ_qubits_orig` = `circ_qubits_transpile`. SQLS: `circ_qubits 3` (nelem 2) and `4` (nelem 5) =
`n_data_qubits + m_ancilla` (3+0, 4+0); the older `nqubits` column stays the data register (HHL 4
at nelem 2 / 5 at nelem 5 is the Hermitian register, kept as before).

## Criterion 6 — (e) -seed — PASS

SQLS (nelem 2, 10000 shots, `-sqls_repeats 1 -iters 2`, 2.4 s each):

| pair | `dq_nelem2_iter0_statevector_shots10000.csv` sha256 (first 16) | iter1 | identical |
|---|---|---|---|
| `-seed 7` run a / run b | 68d7e37dc271a767 / 68d7e37dc271a767 | 20c846d09e8ddf8a / 20c846d09e8ddf8a | yes, both files; `hhl_metrics` identical too (fidelity 0.99997801, 0.99989803) |
| unseeded run a / run b | ff682120be215703 / d8c55992671a85e3 | d8fe9ce3be62134b / 6f5cb0daa10164e8 | no |

Seeded vs unseeded differ. CSV `seed` = `7` (seeded) / empty (unseeded); pickle `seed` 7 / None;
`effective_shots 10000` everywhere.

HHL (nelem 2, 1000 shots, `-iters 1`, ~9 s each): seeded pair `dq_*.csv` sha256 a1b9048cfc38 =
a1b9048cfc38 and `hhl_metrics` identical (fidelity 0.99011868 both); unseeded pair d31bb108ffca vs
e421e1ad645c, fidelities 0.8674 and 0.8776; CSV `seed 7` / empty, pickle 7 / None,
`effective_shots 1000`. Plumbing: `QuantumHHL._run_on_backend` does
`run_kwargs.setdefault('seed_simulator', self.seed)`; `QuantumSQLS` passes `seed=` to
`quantum_solve` only when set.

sqls clone: `git -C /Users/agallojr/proj/src/q8020/sqls diff` (working tree vs HEAD `9a4346a7`,
and HEAD == main, 0 commits ahead) touches only `src/sqls/runtime/quantum.py` (+31/-15) and
consists of (i) the `_run_shots` port from `qiskit_ibm_runtime.SamplerV2` to
`simulator.run([qc_meas]*repeats, shots=..., **run_kw).result()` with `result.get_counts(i)`,
(ii) the keyword-only `seed=None` on `quantum_solve` (validated via `operator.index`, forwarded
as `seed_simulator`, docstring), and (iii) the single line `sqls_out["qc"] = qc` after
`sqls_build`. `inspect.signature(quantum_solve)` ends `..., gpu=False, restore_sign=True, *,
seed=None`. Because the earlier port is itself uncommitted, git cannot separate (i)+(ii) from
(iii); by content, (iii) is the only line that is not part of the sampler/seed port, and the fvm
README's description of the port ("runs `simulator.run(..., seed_simulator=seed)` directly")
places (ii) in the port. `sqls-patches/` was not read (forbidden).

## Criterion 7 — (f) -hhl_scale — PASS

`-h` shows `-hhl_scale {leastsq,true_sol}`; `time_solvers.HHL_SCALE_TYPES = ('leastsq',
'true_sol')`, `HHL_SCALE_DEFAULT = 'leastsq'`, used by the CLI default and by the LU/GMRES
`linsolv_args` default; `LinearSystemSolver.__init__` raises `ValueError` on anything else.
`-hhl_scale true_scale` -> rc 2, stderr `argument -hhl_scale: invalid choice: 'true_scale'
(choose from leastsq, true_sol)`, output dir left empty. Pickle `hhl_scale` = `leastsq` (default
run) / `true_sol`; absent from SQLS pickles (checked on all SQLS runs).

`true_sol` at nelem 2 statevector (`-iters 1`, 10.2 s): finite `dq_hhl`, `residual_total 1.3141`,
fidelity 0.9999986, `linsys_residual 3.82e-3`; `||dq_hhl|| = 0.5440470 = ||dq_herm||` to 7.0e-14;
component ratio true_sol/leastsq constant 0.99859811 (spread 1.5e-14, same direction and sign);
sign rule holds (`||A dq - b|| 3.8e-3` vs `||A(-dq) - b|| 2.63`); `dq_lu` identical to the
leastsq run. Default path numerics unchanged: gate fixture 7/7 at 1e-10 (above).

## Criterion 8 — tests — PASS (finding F4)

- `.venv/bin/python -m unittest discover -s tests -v`, 2026-10-15T08:53:31Z to 08:55:19Z:
  `Ran 128 tests in 107.129s`, `OK (skipped=1)` (the skip is
  `test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`, opt-in via
  `FVM_GATE_TESTS=1`); 108.03 s process. pytest runner not run (the default suite was allowed
  once; TESTING.md reports pytest 127 passed / 1 skipped / 40 subtests, 109.0 s).
- Contract pins: `QC_METADATA_FAIRNESS_COLUMNS` (8 names, appended to both
  `QC_METADATA_HHL_COLUMNS` and `QC_METADATA_SQLS_COLUMNS`, compared as full lists in
  `tests/test_output_contract.py` lines 297/321/341 and `tests/test_circuit_metrics.py` line 182),
  `FB_BASIS_TAG`, `CIRC_METRICS_CHOICES/DEFAULT`, `METADATA_KEYS_QUANTUM` += `circ_metrics, seed,
  effective_shots`, `METADATA_KEYS_HHL_ONLY = ['hhl_scale']`, `HHL_SCALE_TYPES/DEFAULT`.
- Floors documented: TESTING.md lines 213-219 (unseeded HHL floor 0.8, "observed 0.81 to 0.97",
  "~100 of the 1000 shots" kept) and 378-382 (seeded floor 0.98, observed 0.99012 with seed 7);
  `tests/test_hhl.py` carries the same numbers.
- Flakiness of the unseeded HHL 0.8 floor (`/tmp/order3-verify-11/mc_floor.py`): exact output
  distribution of the Aer-transpiled nelem-2 step-0 circuit (12 qubits, `Statevector`, 3.1 s),
  20,000 numpy multinomial draws of 1000 shots pushed through the solver's own chain
  (`get_sol_real_backend` -> `extract_true_sol_from_herm` -> leastsq -> abs/sign from `dq_herm`
  -> `fidelity`); the infinite-shot limit of the chain reproduces the statevector fidelity
  0.9999986, validating it. Post-selection probability 0.0347, i.e. ~35 of 1000 shots survive
  (not ~100 as TESTING.md says). Fidelity: mean 0.9464, median 0.9543, std 0.0337, min 0.7021,
  quantiles 0.1 % 0.773 / 1 % 0.835 / 5 % 0.875; `P(fidelity < 0.8) = 0.0034` (68 of 20,000),
  `P(< 0.75) = 0.0006`, `P(< 0.7) = 0` in 20,000. The observed draws (0.814, 0.867, 0.878, 0.81 to
  0.97) sit where the distribution says. The suite evaluates this floor once per run (one cached
  unseeded run), so about 1 in 300 suite runs will fail on it. See F4.

## Criterion 9 — hygiene — PASS

`git diff e13cbb1e..484b24ed -- '*.py' | grep '^+' | grep -v '^+++' | awk 'length > 89'` -> 0
lines; trailing-whitespace grep on added `.py` and `.md` lines -> 0; no indented `import`/`from`
added (the only in-function imports in the touched files, `from quantum_tools import fidelity` and
`from scipy.sparse import csr_matrix`, predate the item). README.md lines 337-339 (the former
277-278, hunk `@@ -275,7 +335,8 @@`): "ideal shots runs call `AerSimulator.run` directly, with
`seed_simulator` when `-seed` is given". TESTING.md line 41 still mentions the "Aer SamplerV2
port" only as the historical name of item 3 (fine).

## Criterion 10 — nothing pushed, pins — PASS

`git branch -r` has no `origin/feature/sqls-aiaa-4q26`; `main` = `origin/main` = `ef7f0a8b`
(2026-08-17T19:22:59-04:00 = 2026-08-17T23:22:59Z), reflog of `main` unchanged since; branch is 30
commits ahead of main with the six item-11 commits at the tip; `git stash list` empty; single
worktree. sqls HEAD `9a4346a7` (2026-06-30T14:40:52Z), only `src/sqls/runtime/quantum.py`
modified. experiments HEAD `6f646617`, branch main; the experiments working tree has other
pre-existing modifications outside the August folder (`fvm_*.toml`, harvesters, untracked
`sqls-for-aiaa-4Q26/`, untracked `q8020_*_0.json` in the SQLS trial dir), none of them in
`sqls-vs-hhl-2026-08-17/`.

## Findings

| id | severity | finding | where | suggested action |
|---|---|---|---|---|
| D1 | deviation (low) | `-circ_metrics none` writes `-1 / -1 / -1 / none / 0.0`, not empty/None as the criterion reads. Self-consistent with the `cx_count -1` convention, documented in README, contract and tests. | `quantum_tools.circuit_metrics` | accept, or switch the sentinels to `''` if literally empty fields are wanted |
| D2 | deviation (budget) | two HHL nelem-2 statevector CLI runs were made (leastsq 10.4 s, true_sol 10.2 s) instead of one, because criterion 7 requires a `true_sol` run with finite output. | this report | none |
| F1 | low (doc) | README ranges "SQLS nelem 5: 200-201 CX / depth 400-401 / 572-577 gates" (fvm README and the August README corrections paragraph) understate: rung 5a step 1 gives depth 402 / 580 gates (confirmed by independent transpile). Unseeded shots runs produce different Newton systems, so the range is run-dependent. | both READMEs | say "about 200 CX, depth about 400, about 575 gates" or widen to 400-402 / 572-580 |
| F2 | low (doc) | `count_circuit_metrics` docstring: "no stochastic pass runs without a coupling map; the seed only pins determinism". With `seed_transpiler=4242` the HHL nelem-2 circuit gives depth 470,395 / 630,401 gates vs 470,394 / 630,388 at seed 0 (CX identical at 234,899); the SQLS circuit is seed-independent. The pinned seed 0 keeps the published numbers deterministic, but the claim is inaccurate at the 1e-5 level for u3 count/depth. | `quantum_tools.py` | reword: "seed_transpiler=0 pins the result; some synthesis steps are seed-dependent at the u3 level" |
| F3 | low (doc) | TESTING.md says post-selection keeps "~100 of the 1000 shots" for the HHL nelem-2 shots test; the exact post-selection probability is 0.0347 (about 35 shots). | TESTING.md lines 215, `tests/test_hhl.py` comment | correct the number |
| F4 | medium-low (test flakiness) | Unseeded HHL floor `fidelity >= 0.8` at 1000 shots fails with estimated probability 0.34 % per draw (68/20,000 MC; 0.1 % quantile 0.773, min 0.702). The suite evaluates it once per run, so roughly 1 in 300 suite runs is red for no code reason. The seeded test already pins 0.98. | `tests/test_hhl.py::TestHHLShotsNelem2` | lower the unseeded floor to 0.7 (0 of 20,000 below) or drop the fidelity assertion from the unseeded test and keep it in the seeded one |
| F5 | low (pre-existing, out of item scope) | `circuit_generated_*.qpy` written by the HHL path cannot be reloaded on this stack: `qpy.load` raises `TypeError: ExactReciprocalGate.__init__() missing 2 required positional arguments` (the fork's custom gate does not round-trip qpy). `-loadcirc` of a generated circuit would fail. Not introduced by item 11; I regenerated the circuit in-process instead. | `quantum_tools.generate_circuit` / fork | track separately |

## Not checked, and why

- pytest runner: the default suite was allowed once; run under unittest only.
- The 15-minute matched HHL nelem-5 shots run, sweeps, Frontier, network: out of budget by rule.
- `fake` / `real-*` backend paths of `-seed` and `effective_shots` (code read only: `_run_on_backend`
  covers fake; for a fake backend with `-shots 0` the solver substitutes 128 shots, and pickle
  `effective_shots` = 128 while pickle `nshots` stays 0 — a correct record, noted for awareness).
- `sqls-patches/`, `build-*.md`, `reproduce-*.md`, `STATUS.md`: forbidden to read; the sqls diff was
  assessed from the clone's working tree only.
- Whether the "earlier shots port" in the sqls clone already contained the `seed=` kwarg could not be
  established by git (nothing is committed); assessed by content as described under criterion 6.

## Commands and wall times (UTC)

| when | command | wall |
|---|---|---|
| 08:53:31Z | `.venv/bin/python -m unittest discover -s tests -v` | 107.13 s (128 tests, OK, 1 skip) |
| 08:56:04Z | `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` | 112.03 s (7/7 OK) |
| 08:58Z | rung 3 nelem 2 / nelem 5; rung 5a; `-v 0/1/2`; `-circ_metrics none`; `-shots 5000 -sqls_repeats 2`; SQLS seeded x2, unseeded x2 | 2.4, 2.5, 2.5, 2.6, 3.4, 6.4, 1.8, 2.4, 2.4, 2.4, 2.5, 2.4 s |
| 08:59Z | `-hhl_scale true_scale`, `-circ_metrics bogus` | rc 2 each, < 1 s |
| 09:00:31Z | HHL nelem 2: statevector leastsq, statevector true_sol, `-seed 7` x2, unseeded x2 | 10.4, 10.2, 8.9, 8.9, 9.0, 9.1 s |
| 09:03:44Z | HHL nelem 5 statevector `-iters 1` | 99.84 s |
| 09:06Z | in-process probes (LU corruption, counter checks, HHL regeneration, Monte Carlo 20,000 draws) | ~30 s total |
