# Build 10: SQLS-aware fvm harvester

Work-plan item 10 (`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`).
Built 2026-10-15T02:51Z to 03:00Z (UTC) by builder C. Nothing committed.

Repos:

- experiments: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments`, `main` @ `6f646617` (unchanged).
- metautil: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`, `feature/solverfw-v2` @ `753b97e` (unchanged; only read).
- Python: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`.
- Solver repo `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` was only read.

## 1. What changed

One file:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
(640 lines before, 845 lines after; `git diff --stat`: 242 insertions, 36 deletions
across all experiments edits, 268 lines touched in this file). Line numbers below
are in the new file.

| Where | Change | Why |
|---|---|---|
| `:186-190` `_STDOUT_SOL_LAYOUTS` | Table of layouts: HHL `("HHL sol", column 2)`, SQLS `("SQLS sol", column 1)` | The SQLS stdout table has 3 columns, not 4 |
| `:192-244` `_parse_stdout_lu_solutions` | Accepts either header. Returns `{"solver", "lu", "qsol"}` per block | Before, it only matched `HHL sol` (finding 2) |
| `:247-249` `_stdout_declares_converged` | True if stdout contains `SOLUTION CONVERGED` | Lets the harvester use the solver's own banner (`nozzle_1d_solver.py:314-318`) |
| `:252-258` `_is_sqls` | SQLS if pickle `linear_solver == "SQLS"`, or if the qc_metadata CSV has a `solve_time` column | Picks the SQLS column mapping |
| `:261-267` `_int_or_none` | Integer, or None for a missing cell or the `-1` "not logged" flag | SQLS writes `cx_count`/`circuit_depth = -1` unless run with `-v 2` (`quantum_tools.py:829`) |
| `:270-282` `_sqls_params` | method, k, state_prep, repeats: from pickle `quantum_circuit`, else from the CSV | Fills `code.sqls_*` and `effective_shots` |
| `:384-397` `_build_backend` | SQLS `num_qubits = n_data_qubits + m_ancilla`. HHL still uses `nqubits` | Finding 11. HHL left alone so the regression stays clean (see section 6) |
| `:410-413` `_build_backend` | `effective_shots = nshots x repeats` when both are known (SQLS only) | Finding 6. Item 11c depends on it |
| `:419-420` `HHL_BASIS`, `SQLS_BASIS` | `"aer_simulator"` (HHL, all gates) and `"{u3,cx}"` (SQLS, CX count) | Finding 3. Records the basis so the two are never silently compared |
| `:423-495` `_build_artifacts_sqls` | SQLS branch, described below | Finding 2 |
| `:498-506` `_build_artifacts` | New `sqls` keyword that dispatches to the SQLS branch | |
| `:540-541`, `:563` | HHL `after.basis = "aer_simulator"`, `after.gate_count_scope = "all"`, `artifacts.circuit_basis` | Records the basis for both solvers |
| `:587-594` `_build_results` | Per-iteration key is now `<solver>_solution_vector`: `hhl_solution_vector` for HHL (unchanged), `sqls_solution_vector` for SQLS | The 3-column layout |
| `:609-636` `_last_dq_converged` | The solver's dq rule, described below | Finding 9 |
| `:639-711` `_build_analysis` | `residual_reduction` is no longer rounded (`:678`). The `converged` test was rewritten (`:681-702`). Adds a `converged_by` field. Removed the now-unused `cfd_residual` | Finding 9 |
| `:777-782` `generate_metadata` | For SQLS: `code.algorithm = "SQLS"`, plus `sqls_method`, `sqls_k`, `sqls_state_prep`, `sqls_repeats`. Passes `sqls=` to artifacts and `outdir` to analysis | |

### What the SQLS artifacts branch writes

Each `transpile_passes[i]` entry holds:

- `wall_time_execute_s` = `solve_time`.
- `wall_time_generate_s` and `wall_time_transpile_s` = null. SQLS logs no split.
- `before` = null. fvm never records the raw SQLS circuit.
- `after`:
  - `depth` = `circuit_depth`
  - `gate_count` = `cx_count`
  - `num_qubits` = `n_data_qubits + m_ancilla`
  - `basis` = `"{u3,cx}"`
  - `gate_count_scope` = `"cx"`
- `sqls`: method, k, state_prep, repeats, n_data_qubits, m_ancilla, cx_count,
  circuit_depth, aer_device, solve_time (raw, unrounded).

At the top level:

- `circuit_basis` = `"{u3,cx}"`.
- `circuit_timing_total_s`: `execute` and `total` = sum of `solve_time`;
  `generate` and `transpile` = null.
- `linear_system.matrix_size_hermitian` = null, because SQLS does no Hermitian
  doubling.

### The convergence rule

The solver stops when `resratio < conv_tol` or
`np.all(norm(q - qold, axis=1) <= 1e-10)` (`nozzle_1d_solver.py:313`). The
harvester checks four criteria in this order and stores the first that holds as
`converged_by`:

1. `residual_ratio`: last `residual_total` / first `residual_total` `<` conv_tol.
2. `dq_norm`: the last step's applied dq. That is the 2nd column of the dq CSV,
   reshaped `(nelem, 3)` as in `time_solvers.py:342`. Converged if all three
   per-equation L2 norms are `<= 1e-10`. This check is skipped for unsteady
   `_nsteps` file naming.
3. `solver_stdout`: the `SOLUTION CONVERGED` banner is in stdout.
4. `solver_early_stop`: pickle `final_iters < max_iters - 1`. The loop only
   breaks on convergence.

`converged` is true if any of them holds.

On the ratio criterion: the first row of the residual CSV is exactly the
solver's `res0`. The residual is lagged one step, and April stdout shows
`step: 0 ... res/res0:1.0` with `res` equal to CSV row 0, `12.375368413827264`.
So test 1 reproduces the solver's own `resratio`.

## 2. Commands run

All in the scratch dir `/tmp/order1-build-10-13/`, which was deleted at the end.
`P` = `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`.
`H` = the harvester path above.

| Step | Command | Wall time |
|---|---|---|
| copy inputs | `cp -Rp .../2026-08-17-qiskit25-local/trial_0 /tmp/order1-build-10-13/hhl0`; same for `2026-08-17-sqls-local-v2/trial_0` -> `sqls0` (`-p` keeps mtimes so `file_inventory.modified` matches) | < 1 s |
| baseline | ORIGINAL harvester on an HHL copy: `$P harvester_orig.py --outdir /tmp/order1-build-10-13/hhl_base`, then a recursive JSON diff against the committed `q8020_*_0.json` | < 1 s |
| SQLS on a /tmp copy | `$P $H --outdir /tmp/order1-build-10-13/sqls_new` | 0.19 s |
| HHL regression | `$P $H --outdir /tmp/order1-build-10-13/hhl_new`, then a recursive diff | 0.13 s |
| stdout tests | built synthetic `q8020_stdout_test.txt` files with the solver's own `math_tools.print_matrix_scientific` and the exact header strings from `time_solvers.py:577` (HHL) and `:667` (SQLS). Ran `$P $H --outdir` on copies `sqls_stdout` and `hhl_stdout` | < 1 s each |
| real write (2026-10-15T02:55:11Z) | `$P $H --outdir /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0` | 0.15 s |
| roll-up check | `q8020_cfd_metautil.harvest.harvest_metadata(<real SQLS trial_0>, read_only=True)` | < 1 s |

Baseline result: the unmodified harvester reproduces the committed HHL fragments
byte-for-byte as JSON (zero differences). So every difference in section 5 comes
from this change.

The re-run was repeated after the last edit (the `_nsteps` guard). The /tmp SQLS
output is byte-identical (`cmp`) to the six files written into the real trial
dir.

## 3. Fragment naming

The committed HHL `q8020_<section>_0.json` names come from running the harvester
in `--outdir` mode. That mode sets `experiment_id = None`, and
`meta_fragment.write_fragment` (`meta_fragment.py:354-357`) then writes
`q8020_<section>_<index>.json`. The HHL README
(`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/README.md:38`)
lists them as "repo harvester". The SQLS run used the same `--outdir` call, so
the names match:

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_case_0.json`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_code_0.json`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_backend_0.json`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_artifacts_0.json`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_results_0.json`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_analysis_0.json`

The trial dir now has 40 files: 34 originals plus these 6. The read-only roll-up
counts 1 each of `case`, `code`, `backend`, `artifacts`, `results` and
`analysis`, 0 `experiment` and 0 `exec_stats`, and no warnings. `git status`
shows only these six as untracked under `results/`; no tracked file under
`results/` is modified.

## 4. Key values in the SQLS fragments (2026-08-17-sqls-local-v2/trial_0)

| Field | Value |
|---|---|
| `code` | `algorithm "SQLS"`, `sqls_method "full_svd"`, `sqls_k 128`, `sqls_state_prep "initialize"`, `sqls_repeats 1` (from pickle `quantum_circuit`) |
| `backend` | `name "ideal_statevector"`, `type "simulator"`, `method "statevector"`, `noise false`, `num_qubits 4` (4 data + 0 ancilla qubits), `nshots 150000`, `effective_shots 150000` (150000 shots x 1 repeat) |
| `artifacts.transpile_passes[0..6].after` (depth, CX count, qubits) | (398, 200, 4), (397, 201, 4), (398, 201, 4), (398, 200, 4), (398, 201, 4), (398, 201, 4), (398, 201, 4); `basis "{u3,cx}"`, `gate_count_scope "cx"` |
| `transpile_passes[0].wall_time_execute_s` | 0.102901 s (step 0 `solve_time` 0.10290098190307617 s) |
| `transpile_passes[i].before`, `wall_time_generate_s`, `wall_time_transpile_s` | null |
| `transpile_passes[0].sqls` | method full_svd, k 128, state_prep initialize, repeats 1, n_data_qubits 4, m_ancilla 0, cx_count 200, circuit_depth 398, aer_device CPU, solve_time 0.10290098190307617 s |
| `circuit_timing_total_s` | generate null, transpile null, execute 0.575051 s, total 0.575051 s (raw sum 0.5750510692596436 s) |
| `circuit_basis` | `"{u3,cx}"` |
| `linear_system` | `matrix_size_original 15`, `matrix_size_padded 16`, `matrix_size_hermitian null`, `condition_number_range [59.9218, 95.9779]` (2-norm condition numbers, dimensionless) |
| `analysis` | `iterations_completed 7`, `converged true`, `converged_by "dq_norm"`, `residual_reduction 1.018457653098037e-10` (unrounded; last/first CFD `residual_total` = 1.2603788670970093e-09 / 12.375368413827264), `fidelity 0.4510250082577229` (last row, the known tail collapse), `l2_error_normalized 0.8104403398460795`, `residual 1.2276304729466986e-09` (last `linsys_residual`), `shots 150000` |
| `results` | `final_solution` 5 rows, `per_iteration` 7 entries (solution + dq), `residual_history` 7 rows; no stdout vectors (the trial has no stdout file) |

On the convergence criteria for this run: `residual_ratio` is false, since
1.0185e-10 is not `<` the conv_tol of 1e-10. `dq_norm` is true: the step-6
applied dq per-equation norms are 2.58e-11, 2.58e-11 and 5.77e-11 (rho, rhou, rhoE; nondimensional), all
`<= 1e-10`. `solver_early_stop` would also be true (final_iters 6 < 14). So the
harvester agrees with the solver's declaration at iteration 6.

## 5. HHL regression (2026-08-17-qiskit25-local/trial_0)

I harvested a /tmp copy and diffed it recursively against the committed
`q8020_*_0.json` (JSON, all keys). There are 39 diff lines. Every one is
intentional:

| Fragment | Field | Committed | New | Reason |
|---|---|---|---|---|
| analysis | `residual_reduction` | 0.000549 | 0.0005490977149420549 | stored unrounded (finding 9) |
| analysis | `converged_by` | absent | null | new field; no criterion met |
| analysis | `converged` | false | false (unchanged) | 15-iteration cap: final_iters 14 = max_iters - 1, ratio 5.49e-4, last dq not below 1e-10 |
| artifacts | `circuit_basis` | absent | `"aer_simulator"` | new field (basis record) |
| artifacts | `transpile_passes[0..14].after.basis` | absent | `"aer_simulator"` (15 entries) | new field |
| artifacts | `transpile_passes[0..14].after.gate_count_scope` | absent | `"all"` (15 entries) | new field |
| backend, case, code, results | all | -- | identical | -- |

`backend.effective_shots` is not added for HHL because HHL has no `repeats`.
`backend.num_qubits` stays 5 for HHL (see open doubts).

## 6. Stdout parsing (synthetic files)

| Copy | Header in file | Blocks | Extracted (first 4 entries of each vector, step 0) |
|---|---|---|---|
| `sqls_stdout` (SQLS trial copy) | `LU sol \t    SQLS sol    L1_diff(%)` (3 columns) | 2 (steps 0, 1) | `lu_reference_vector [-0.01705, -0.007527, -0.03946, -0.1283]`, `sqls_solution_vector [-0.009876, -0.006983, -0.04131, -0.131]`; `lu_reference_vector_final` has 15 entries (step 1 values `[-0.002857, 0.002252, 0.01206, 0.01588, ...]`) |
| `hhl_stdout` (HHL trial copy) | `LU sol \t    Herm LU sol    HHL sol    L1_diff(%)` (4 columns) | 2 (steps 0, 1) | `lu_reference_vector [-0.01705, -0.007527, -0.03946, -0.1283]`, `hhl_solution_vector [-0.0, -0.0, -0.05635, -0.138]`; `lu_reference_vector_final` has 15 entries |

In both copies, per_iteration entries 2 and later carry no vectors, as expected
for 2 blocks. The vector values are the dq CSV values printed at 3 significant
digits by `print_matrix_scientific`. Item 13 adds a real-data HHL check: the
April runs have real stdout, and all 45 and 67 per-iteration entries of the two
April cases got `hhl_solution_vector` (see `build-13.md`).

## 7. Open doubts

1. **Is `after.gate_count` for SQLS a CX count, not a total gate count?** Yes. It
   is tagged `gate_count_scope "cx"` and `basis "{u3,cx}"`. HHL's is the total
   in the Aer basis (`"all"`). A consumer that ignores these tags still compares
   unlike things. Finding 3, a shared basis helper in fvm, is the real fix.
2. **HHL `backend.num_qubits` is still 5 (log2 of the 32-row Hermitian
   system).** Its circuit is 13 to 14 qubits. Finding 11 suggests preferring
   `circ_qubits_transpile`. I did not do this, because it would change a
   committed HHL value and break the clean regression. It is a one-line change
   if the owner wants it.
3. **The `sqls_k` value of 128 is what the August pickle recorded.** With
   N = 16 that k is meaningless for full_svd. The concurrent solver edit now
   defaults k to N // 2.
4. **New per-iteration key.** The key is `sqls_solution_vector`, not
   `hhl_solution_vector`. The analysis list is still named `hhl_metrics` for
   SQLS (an existing misnomer, kept for compatibility). `results.per_iteration[].dq`
   keeps the CSV key `dq_sqls`.
5. **The `dq_norm` check reproduces the solver rule only for steady mode.** It
   assumes one inner iteration per step and the `(nelem, 3)` layout. For
   unsteady `_nsteps` naming it returns false and the other criteria decide.
6. **Null where there used to be 0.** `circuit_timing_total_s.generate/transpile`
   and `wall_time_generate_s/transpile_s` are null for SQLS. A downstream
   consumer that sums these without a null guard would fail. That is
   deliberate, so the unknowns don't read as measured zeros.
7. **Headline `analysis.fidelity` is still the last row** (0.451 for SQLS).
   Finding 10 is out of scope here.

## Fix-up round (code review findings), 2026-10-15T03:42Z

Builder C applied the code-review fix-ups to the same uncommitted harvester
(`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`).
Repo HEAD is still `6f646617`. Nothing was committed.

### What changed (line numbers in the edited file)

| Fix | Where | Change |
|---|---|---|
| style | `:30-32` | `HHL_BASIS` / `SQLS_BASIS` moved to the top of the module |
| C1 | `:642` `_last_dq_converged` | `if not norm <= 1e-10: return False`. A NaN dq norm now means not converged, as in the solver's `np.all(dqnorm <= 1e-10)` |
| C3 | `:458-467` `_build_artifacts_sqls` | SQLS `after` now has `cx_count` (int or null) and `gate_count` null. `depth`, `num_qubits` and `basis "{u3,cx}"` stay. `gate_count_scope` for SQLS is `"none; CX only, in cx_count"`. HHL is unchanged (`gate_count_scope "all"`). The CX count is also still in `sqls.cx_count` |
| C5 | `:716-720` | `solver_early_stop` now needs `max_iters > 1` and `0 < final_iters < max_iters - 1`. A resumed chunk with 0 iterations no longer counts as converged |
| C8 | `:681-689`, `:693-724`, `:730` `_build_analysis` | If the pickle has a bool `converged`, it is used directly. `converged_by` comes from the pickle (null when not converged). `resnorm_init`, when present, is the denominator of `residual_reduction`. Otherwise the old heuristics run. The new field `analysis.converged_source` is `"solver"` or `"heuristic"` |
| C7/C8b | `:61` `_iter_no`; `:323` `_extract_dq_by_step`; `:337` `_extract_per_iteration_results`; `:775-779`, `:813-818` `generate_metadata` | `generate_metadata` computes these once: stdout text, `is_sqls`, SQLS params, and dq-by-step (plus an unsteady flag). It passes them to `_build_backend`, `_build_results` and `_build_analysis`. The stdout parsers now take text instead of `outdir`. `_last_dq_converged` reuses the parsed last-step dq. One `_iter_no` helper replaces the three `iter(\d+)` lambdas and the nested helper |
| C10 | `:256-264` `_stdout_declares_converged` | Only the text after the LAST `step:` line is searched for `SOLUTION CONVERGED` (whole text if there is no `step:` line). This is still the third criterion of four |

### HHL regression (`2026-08-17-qiskit25-local/trial_0`)

I made a `/tmp` copy with mtimes kept and without `q8020_*_0.json`, harvested
it, and did a recursive JSON diff against the committed fragments. Every
difference is in the allowed set:

- `analysis.residual_reduction`: 0.000549 -> 0.0005490977149420549 (unitless ratio)
- `analysis.converged_by`: added, null
- `analysis.converged_source`: added, `"heuristic"`
- `artifacts.circuit_basis`: added, `"aer_simulator"`
- `artifacts.transpile_passes[0..14].after.basis`: added, `"aer_simulator"` (15 entries)
- `artifacts.transpile_passes[0..14].after.gate_count_scope`: added, `"all"` (15 entries)
- case, code, backend, results: identical

Compared with the pre-fix-up harvester, the only HHL change is
`converged_source`.

### SQLS fresh harvest (`2026-08-17-sqls-local-v2/trial_0` copy)

Step-0 `after`, verbatim:

```json
{
  "depth": 398,
  "num_qubits": 4,
  "gate_count": null,
  "cx_count": 200,
  "basis": "{u3,cx}",
  "gate_count_scope": "none; CX only, in cx_count"
}
```

`analysis`: `converged` true, `converged_by` `"dq_norm"`, `converged_source`
`"heuristic"`, `residual_reduction` 1.018457653098037e-10 (unitless ratio).

Compared with the previous fragments, these are the only changes:

- In each of the 7 passes, `after.gate_count` moved to `after.cx_count` and became null (values 200 or 201 CX gates).
- The scope tag changed.
- `converged_source` was added.

### Probes (edited `/tmp` copies of the SQLS trial)

| Probe | Setup | Result |
|---|---|---|
| (a) C1 | last dq CSV all `nan`; `final_iters` 14, `max_iters` 15, so early stop cannot fire | converged false, `converged_by` null. The pre-fix-up harvester on the same input gives true / `dq_norm` |
| (b) C5 | `final_iters` 0, `max_iters` 15, no stdout, ratio 1.018e-10 > tol 1e-10, dq CSVs removed | converged false. Control with `final_iters` 6: true / `solver_early_stop` |
| (c) C8 | pickle with `converged=True`, `converged_by='residual_ratio'`, `resnorm_init` 12.375368413827264 | converged true, `residual_ratio`, source `"solver"` |
| (c) C8 | pickle with `converged=False`, `converged_by=None` (the heuristic alone gives `dq_norm`) | converged false, null, source `"solver"` |
| (d) C10 | stdout: banner after `step: 0`, then later `step: 1` and `step: 2` with no banner; dq removed, `final_iters` 14 | converged false. Control with the banner after the last step: true / `solver_stdout` |

### Checks and re-harvest

- No added line is longer than 88 characters.
- No added line has trailing whitespace.
- `py_compile` passes (`cfile` written in `/tmp`, no `__pycache__` in the repo).
- I re-harvested the real trial dir in place with
  `.../q8020-cfd-metautil/.venv/bin/python -B <harvester> --outdir <trial_0>`.
  All six `q8020_{case,code,backend,artifacts,results,analysis}_0.json` match
  the scratch harvest by sha256.
- `git status --short results/` shows only those six untracked files.

## Follow-up: carry solver `code_versions` into the code fragment (2026-10-15T04:44Z)

**Change.** The edit is to
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`,
in `generate_metadata` (9 lines added after the `sqls_*` keys, now about lines
811-819). It was made on top of the harvester as found on disk. Someone else had
refactored the file in the meantime; it was 876 lines when this edit started.

- `code.code_versions` is the pickle's `metadata['code_versions']`, carried
  verbatim. The solver writes this from fvm `4f44d5be`
  (`helper_tools.get_code_versions`). It is null when absent, which is the case
  for every archived run.
- `code.fvm_commit`, `code.sqls_commit` and `code.linear_solvers_commit` are the
  `commit` of each entry. They are null when the entry or `code_versions` is
  missing.

**Regression.** I harvested `cp -Rp` copies of both August `trial_0` dirs, with
all `q8020_*` files removed, using the harvester as it was just before this edit
and again after it. The recursive JSON diff is the same in both trials:

| Trial | Fragment | Differences |
|---|---|---|
| HHL `2026-08-17-qiskit25-local` | `code` | ADDED `code_versions = null`, `fvm_commit = null`, `sqls_commit = null`, `linear_solvers_commit = null` |
| HHL | case, backend, artifacts, results, analysis | none |
| SQLS `2026-08-17-sqls-local-v2` | `code` | the same four null fields added |
| SQLS | case, backend, artifacts, results, analysis | none |

The real SQLS fragments as they stood before this follow-up were also identical
to the pre-edit harvester's output.

**Test run.** This was one short solver run, reading the solver repo and its
venv without changing them:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow -outdir /tmp/order2-harv-codever/run
```

- It ran at 2026-10-15T04:43:41Z, returned rc 0, and took 2.58 s wall time.
- The solver's `git status --short` was the same before and after, and no
  `__pycache__` file there was touched.
- Harvesting that dir gave six fragments.

The `code` fragment, verbatim:

```json
{
  "_source": "solver",
  "algorithm": "SQLS",
  "sqls_method": "full_svd",
  "sqls_k": 4,
  "sqls_state_prep": "initialize",
  "sqls_repeats": 1,
  "code_versions": {
    "fvm": {
      "path": "/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver",
      "commit": "abf749413b98a0a9a99900c74361390807e40dc7",
      "dirty": false,
      "version": "0.1.0"
    },
    "sqls": {
      "path": "/Users/agallojr/proj/src/q8020/sqls/src/sqls",
      "commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
      "dirty": true,
      "commit_source": "git",
      "version": "0.1.0"
    },
    "linear_solvers": {
      "path": "/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/linear_solvers",
      "commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923",
      "dirty": null,
      "commit_source": "direct_url",
      "version": "0.1.0"
    },
    "qiskit": "2.5.2",
    "qiskit_aer": "0.17.2",
    "qiskit_ibm_runtime": "0.49.0",
    "numpy": "2.5.2",
    "scipy": "1.18.0",
    "python": "3.12.10"
  },
  "fvm_commit": "abf749413b98a0a9a99900c74361390807e40dc7",
  "sqls_commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
  "linear_solvers_commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923"
}
```

All three commits are 40-hex. `sqls` is `dirty: true` because its working tree
holds the uncommitted port. `linear_solvers` is a non-editable install, so its
commit comes from `direct_url.json` and `dirty` is null.

**In-place re-harvest.** I re-harvested
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0`
at 2026-10-15T04:43:57Z, which took 0.09 s.

- All six `q8020_*_0.json` files are sha256-equal to the fresh scratch harvest.
  For example, `q8020_code_0.json` is
  `75d552a9b350f2121f612afeca4879936ec82a02a6a3d1bc3e9e89718b9bd1e3`.
- The dir still holds 40 files.
- The committed HHL fragments were not re-harvested, so they do not carry the
  four null fields.
- The scratch dir `/tmp/order2-harv-codever` was deleted, and no `__pycache__`
  was left under `aux/fvm_euler_1d_nozzle/`.

## Follow-up: item 11 fairness columns (2026-10-15T08:51Z)

**Change.** The edit is to
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.
It was applied to the file as found on disk; others had edited it since the last
section.

It adds:

- `import statistics`.
- Three helpers after `_sqls_params`: `_float_or_none`, `_fixed_basis` and
  `_fixed_basis_summary`.
- A rewrite of the num_qubits, effective_shots and seed logic in
  `_build_backend`, including the -1 guard for SQLS width.
- A `fixed_basis` entry in each step of both artifacts builders, plus a
  `fixed_basis_summary` per fragment.
- `circ_metrics` and `hhl_scale` in `code`.

The source is fvm `feature/sqls-aiaa-4q26` @ `484b24ed`. Commit `cca70256` adds
eight columns to both `qc_metadata_*.csv` writers: `circ_qubits, fb_depth,
fb_total_gates, fb_cx_count, fb_basis, t_count_s, effective_shots, seed`. The
pickle gains `circ_metrics`, `seed`, `effective_shots` and, for HHL,
`hhl_scale`.

### New fragment fields

All counts are dimensionless integers. Times are wall-clock seconds.

| Field | Type | Units | Source |
|---|---|---|---|
| `artifacts.transpile_passes[i].fixed_basis` | object or null | -- | null when the CSV has no `fb_depth` column (all archived runs) |
| `...fixed_basis.basis` | string or null | -- | CSV `fb_basis`; `u3cx` is mapped to `"{u3,cx}"`, `none` (from `-circ_metrics none`) to null |
| `...fixed_basis.depth` | int or null | gate layers | `fb_depth`; -1 becomes null |
| `...fixed_basis.total_gates` | int or null | gates (every instruction, resets included) | `fb_total_gates`; -1 becomes null |
| `...fixed_basis.cx_count` | int or null | CX gates | `fb_cx_count`; -1 becomes null |
| `...fixed_basis.t_count_s` | float or null | s | `t_count_s`, the counting-transpile time, which is excluded from `solve_time`; null when basis is null |
| `artifacts.fixed_basis_summary` | object or null | -- | null when no step has fixed-basis data |
| `...fixed_basis_summary.basis` | string, list or null | -- | the one basis over all steps; a sorted list if they differ |
| `...median_depth`, `median_total_gates`, `median_cx_count` | number or null | as above | median over all steps; a float such as 87.0 when the step count is even |
| `...median_t_count_s_steps_ge1` | float or null | s | median `t_count_s` over steps >= 1, because step 0 carries the transpiler warm-up; null for a 1-step run |
| `...n_steps` | int | steps | number of steps with fixed-basis data |
| `backend.num_qubits` | int | qubits | CSV `circ_qubits`, the circuit width, when logged. Otherwise the legacy rule: SQLS `n_data_qubits + m_ancilla` with -1 treated as missing, HHL `nqubits` |
| `backend.num_qubits_source` | string | -- | `"circ_qubits"` or `"legacy"`; present whenever `num_qubits` is |
| `backend.effective_shots` | int or null | shots per linear solve | pickle `effective_shots`, else CSV `effective_shots`, else legacy SQLS `nshots x repeats`; 0 means statevector; null when unknown. Now for HHL too |
| `backend.seed` | int or null | -- | pickle `seed`, else CSV `seed` (`''` = unseeded); null when unseeded or not recorded |
| `code.circ_metrics` | string or null | -- | pickle `circ_metrics` (`u3cx` or `none`) |
| `code.hhl_scale` | string or null | -- | pickle `hhl_scale` (`leastsq` or `true_sol`) for HHL; always null for SQLS |

The existing `after` blocks are unchanged.

### Test runs

These are fvm `484b24ed`, run with `PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg`
from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`. The solver's
`git status` was unchanged afterwards. Both were harvested in /tmp.

**SQLS run** (2026-10-15T08:50:52Z, rc 0, 2.23 s wall time). Flags: `-nelem 2
-time_scheme BDF1 -linsolver SQLS -shots 5000 -sqls_repeats 2 -seed 7 -localdt
-cfl 1e10 -iters 2 -initers 1 -noshow`.

- `backend`: `num_qubits 3`, `num_qubits_source "circ_qubits"`, `nshots 5000`,
  `effective_shots 10000`, `seed 7`.
- `transpile_passes[0].fixed_basis`: `{basis "{u3,cx}", depth 88, total_gates
  130, cx_count 42, t_count_s 0.5574729442596436}`.
- `fixed_basis_summary`: median_depth 87.0, median_total_gates 128.5,
  median_cx_count 41.5, median_t_count_s_steps_ge1 0.0023941993713378906 s,
  n_steps 2.
- `code`: `circ_metrics "u3cx"`, `hhl_scale null`.
- This run is at the default `-v`, so the legacy `after.depth` and
  `after.cx_count` are null: the solver wrote -1. The fixed-basis block covers
  them.

**HHL run** (2026-10-15T08:50:54Z, rc 0, 8.97 s wall time). Same flags with
`-linsolver HHL -shots 1000 -iters 1` and no `-sqls_*` flags; `-seed 7` was
kept.

- `backend`: `num_qubits 12`, `num_qubits_source "circ_qubits"`,
  `effective_shots 1000`, `seed 7`.
- `transpile_passes[0].fixed_basis`: `{basis "{u3,cx}", depth 470394,
  total_gates 630388, cx_count 234899, t_count_s 1.0618338584899902}`.
- The `after` block, in the Aer basis, is unchanged: depth 68964, gate_count
  74846, 12 qubits.
- `code`: `circ_metrics "u3cx"`, `hhl_scale "leastsq"`.

### Regression

I harvested `cp -Rp` copies of both August trials, with `q8020_*` removed,
using the harvester before and after this edit.

| Trial | Differences |
|---|---|
| HHL | artifacts: ADDED `fixed_basis_summary = null` and 15 x `transpile_passes[i].fixed_basis = null`; backend: ADDED `effective_shots = null`, `num_qubits_source = "legacy"`, `seed = null`; code: ADDED `circ_metrics = null`, `hhl_scale = null` |
| SQLS | artifacts: ADDED `fixed_basis_summary = null` and 7 x `transpile_passes[i].fixed_basis = null`; backend: ADDED `num_qubits_source = "legacy"`, `seed = null`. `effective_shots` stays 150000 via the legacy rule. code: ADDED `circ_metrics = null`, `hhl_scale = null` |

No existing field changed. The only non-null addition is the requested
`num_qubits_source` tag. The real SQLS fragments before this edit were
identical to the pre-edit harvest.

### In-place re-harvest

The real SQLS trial was re-harvested at 2026-10-15T08:51:21Z (0.09 s). All six
fragments are sha256-equal to the scratch harvest:

| File | sha256 |
|---|---|
| artifacts | `4342f618ee377b0cb6cd96856aec37ad98d04d0c25c3eeb41bf7b0e5af6a825c` |
| backend | `116f5fe2fb4dad4aeb17ce522b46c75040cc3dcd3e9b07c294289ca0e91c2e8f` |
| code | `2b375b424f3391c26be19011cfcab21206c43def4648297dba42c666bd2ac961` |
| analysis | unchanged |
| case | unchanged |
| results | unchanged |

The scratch dir `/tmp/order3-harv-11` was deleted, and no `__pycache__` was left
under `aux/fvm_euler_1d_nozzle/`.

## Follow-up: item 6 HHL deflation columns (2026-10-15T10:01Z)

**Change.** The edit is to
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.
It adds three helpers after `_fixed_basis_summary`: `_deflation`,
`_linear_system_deflation` and `_deflation_summary`. It also adds a `deflation`
entry to each step in both artifacts builders, a `linear_system.update(...)` in
both builders, `code.hhl_deflate_k`, and `analysis.deflation_summary`, which is
set in `generate_metadata`.

The source is fvm `feature/sqls-aiaa-4q26` @ `9e8fc7fe`. Commit `8eb40832` adds
six columns to the HHL `qc_metadata_*.csv`, placed after `circ_run_time`:
`deflate_k, kappa, kappa_eff, n_clock, x_share_classical, t_svd_s`. The pickle
gains a top-level `hhl_deflate_k`.

When deflate_k > 0, the solver's `condition_number` column, which is harvested
into `linear_system.condition_number_range`, describes the shifted A', not A.
The new `condition_number_refers_to` field says which.

### New fragment fields

| Field | Type | Units | Source |
|---|---|---|---|
| `artifacts.transpile_passes[i].deflation` | object or null | -- | null when the CSV has no `deflate_k` column (SQLS, all archived runs) |
| `...deflation.deflate_k` | int | directions | `deflate_k`; 0 is plain HHL |
| `...deflation.kappa` | float | dimensionless (sigma_max / sigma_min of the original unpadded A) | `kappa` |
| `...deflation.kappa_eff` | float | dimensionless (sigma_max / sigma_{k+1} of the shifted A' given to HHL; equals kappa when k = 0) | `kappa_eff` |
| `...deflation.n_clock` | int | qubits (clock register) | `n_clock` |
| `...deflation.x_share_classical` | float | fraction 0 to 1 of the squared norm of x carried by the k deflated directions | `x_share_classical` |
| `...deflation.t_svd_s` | float | s (wall time of the SVD pre-step) | `t_svd_s` |
| `artifacts.linear_system.condition_number_refers_to` | string or null | -- | `"A_shifted"` if any step has deflate_k > 0, `"A"` if all are 0, null when the column is absent (archived and SQLS runs) |
| `artifacts.linear_system.kappa_original_range` | [float, float] or null | dimensionless | [min, max] over steps of `kappa`, rounded to 4 decimal places like `condition_number_range`; null when absent |
| `analysis.deflation_summary` | object or null | -- | only for HHL runs with deflate_k > 0, else null |
| `...deflation_summary` contents | -- | -- | `deflate_k` and `n_clock_first` / `n_clock_last` (ints), `median_kappa`, `median_kappa_eff` and `median_x_share_classical` (floats; medians over steps), `n_steps` (int) |
| `code.hhl_deflate_k` | int or null | directions | pickle `hhl_deflate_k`; null when absent |

### Test run

The run was fvm `9e8fc7fe`, from cwd `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`:

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver HHL -hhl_deflate_k 1 -shots 0 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow -outdir /tmp/order3-harv-6/run
```

It ran at 2026-10-15T10:00:59Z, returned rc 0 and took 12.17 s wall time. The
solver's `git status` was unchanged.

| Field | Value |
|---|---|
| `transpile_passes[0].deflation` | `{deflate_k 1, kappa 38.306161601199506, kappa_eff 6.8498325090581, n_clock 6, x_share_classical 0.9511345924972174, t_svd_s 0.00012037495616823435}` |
| `linear_system.condition_number_range` | `[6.8498, 6.8498]`, the shifted A' |
| `linear_system.condition_number_refers_to` | `"A_shifted"` |
| `linear_system.kappa_original_range` | `[38.3062, 38.3062]` |
| `analysis.deflation_summary` | `{deflate_k 1, median_kappa 38.306161601199506, median_kappa_eff 6.8498325090581, median_x_share_classical 0.9511345924972174, n_clock_first 6, n_clock_last 6, n_steps 1}` |
| `code.hhl_deflate_k` | 1 |

**k = 0 check.** I copied the run dir and set its CSV `deflate_k` cell to 0 by
hand. The harvest then gave `condition_number_refers_to "A"`,
`deflation_summary null` and `deflation.deflate_k 0`. This was a synthetic edit
on a scratch copy only; there was no real k = 0 run with the new columns.

### Regression

I harvested `cp -Rp` copies of both August trials, with `q8020_*` removed,
before and after this edit. The differences are the same for both trials and
all null:

- analysis: ADDED `deflation_summary = null`.
- artifacts: ADDED `linear_system.condition_number_refers_to = null`,
  `linear_system.kappa_original_range = null`, and
  `transpile_passes[i].deflation = null` (15 for HHL, 7 for SQLS).
- code: ADDED `hhl_deflate_k = null`.
- backend, case and results: no differences.

The real SQLS fragments before this edit were identical to the pre-edit
harvest.

### In-place re-harvest

The real SQLS trial was re-harvested at 2026-10-15T10:01:28Z (0.15 s). All six
fragments are sha256-equal to the scratch harvest:

| File | sha256 |
|---|---|
| analysis | `593265fe3033f24cb71d43accaba5609de3bb3e870912449a3a1e0861f8a2f4f` |
| artifacts | `44da58c7c45f8ac3a474ea73d3bf3c8e55a705ca148cfb4ff8b6541d912a6af2` |
| code | `054164df6d74075845010c0baba43dc1df278d690756c97e5a07556093faa58b` |
| backend | unchanged |
| case | unchanged |
| results | unchanged |

**Cleanup.** The scratch dir `/tmp/order3-harv-6` was deleted.

There was a gitignored
`aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/__pycache__/fvm_euler_1d_solver_harvester.cpython-312.pyc`
dated 2026-10-15T09:44Z. That is before this follow-up started, and every
harvester call here used `-B`, so it was not created by this follow-up. I
removed it so that no `__pycache__` is left.

## Follow-up: fb_cached, hhl_kernel_rel_err, rotated CSVs (2026-10-15T10:58Z)

**Change.** The edit is to
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.
The source is fvm `feature/sqls-aiaa-4q26` @ `1ec8abcf`, which includes
`e50f4800` and `1c54a0d0`.

It adds:

- A `_bool_or_none` helper.
- `fixed_basis.cached`.
- A cached-row exclusion and an `n_cached_steps` count in
  `_fixed_basis_summary`.
- `hhl_kernel_rel_err` in the `hhl_metrics[]` entries, plus a series, final
  value, median and doc string in `analysis`. The doc text lives in a new
  module constant, `KERNEL_REL_ERR_DOC`.
- A `file_inventory.rotated_csv` list.

The metric globs are all `Path.glob` patterns with no `**` and no `rglob`, so
they match top-level files only. I checked this by grepping every `glob(` call
in the file. The one glob into `rotated/` is used only for the inventory
listing.

### New fragment fields

| Field | Type | Units | Source |
|---|---|---|---|
| `artifacts.transpile_passes[i].fixed_basis.cached` | bool or null | -- | CSV `fb_cached` (`True`/`False`); null when empty (as under `-circ_metrics none`) or absent |
| `artifacts.fixed_basis_summary.median_t_count_s_steps_ge1` | float or null | s | now excludes cached rows, whose `t_count_s` is 0.0; null when every step >= 1 is cached |
| `artifacts.fixed_basis_summary.n_cached_steps` | int | steps | number of steps with `cached` true |
| `analysis.hhl_metrics[i].hhl_kernel_rel_err` | float | dimensionless | `hhl_metrics_*.csv` `hhl_kernel_rel_err`; only present when the column is |
| `analysis.hhl_kernel_rel_err` | list of float, or null | dimensionless | per-step series in `hhl_metrics` row order; null when the column is absent |
| `analysis.hhl_kernel_rel_err_final` | float or null | dimensionless | last step |
| `analysis.hhl_kernel_rel_err_median` | float or null | dimensionless | median over steps |
| `analysis.hhl_kernel_rel_err_doc` | string or null | -- | definition (`KERNEL_REL_ERR_DOC`); null when there is no series |
| `artifacts.file_inventory.rotated_csv` | list of `{name, size_bytes, modified}` | bytes, UTC ISO 8601 | `<outdir>/rotated/*.csv`; listed only, never parsed. Its length is the count |

### Test run

The run was fvm `1ec8abcf`, from cwd `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`:

```
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver HHL -hhl_deflate_k 1 -shots 0 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow -outdir /tmp/order3-harv-fix/run
```

It ran at 2026-10-15T10:58:02Z, returned rc 0 and took 9.49 s wall time. The
solver's `git status` was unchanged.

| Field | Value |
|---|---|
| `fixed_basis` step 0 | depth 232343, total_gates 311810, cx_count 116067, `t_count_s` 0.5060548782348633 s, `cached` false |
| `fixed_basis` step 1 | same counts, `t_count_s` 0.0 s, `cached` true |
| `fixed_basis_summary` | medians 232343.0 / 311810.0 / 116067.0; `median_t_count_s_steps_ge1` null, because the only step >= 1 is cached; `n_steps` 2; `n_cached_steps` 1 |
| `analysis.hhl_kernel_rel_err` | [0.012737673250511191, 0.007675764241892524] |
| `hhl_kernel_rel_err_final` | 0.007675764241892524 |
| `hhl_kernel_rel_err_median` | 0.010206718746201857 |
| `file_inventory.rotated_csv` | `[]`; the counts of the other categories are qpy_generated 2, qpy_transpiled 2, csv 10, pkl 3, png 1 |

**Rotation check.** I copied the run dir and put two stale-header CSVs into its
`rotated/`. They were the August HHL trial's `hhl_metrics` and `qc_metadata`
files, renamed to
`rotated/hhl_metrics_nelem2_statevector.pre-20261015T105800Z.csv` (1732 bytes)
and `rotated/qc_metadata_nelem2_statevector.pre-20261015T105800Z.csv` (3538
bytes). Harvesting the copy and diffing it against the original run's harvest
gave exactly one difference: `file_inventory.rotated_csv` grew from `[]` to the
two entries. Every metric field, and the top-level `csv` count of 10, were
identical.

### Regression

I harvested `cp -Rp` copies of both August trials, with `q8020_*` removed,
before and after this edit. The differences are the same for both trials:

- analysis: ADDED `hhl_kernel_rel_err`, `hhl_kernel_rel_err_doc`,
  `hhl_kernel_rel_err_final` and `hhl_kernel_rel_err_median`, all null.
- artifacts: ADDED `file_inventory.rotated_csv = []`.
- backend, case, code and results: no differences.

`fixed_basis.cached` and `n_cached_steps` do not appear, because `fixed_basis`
and `fixed_basis_summary` are null in archived runs. The real SQLS fragments
before this edit were identical to the pre-edit harvest.

### In-place re-harvest

The real SQLS trial was re-harvested at 2026-10-15T10:58:36Z (0.19 s). All six
fragments are sha256-equal to the scratch harvest:

| File | sha256 |
|---|---|
| analysis | `b5751858d16a960cba3a015430d2deb751050e5251a969a547a81fadcceee678` |
| artifacts | `7f0aab0f83029a61950452ea8cceb22250d8893530c8dcabcbaa872d979fa8df` |
| backend | unchanged |
| case | unchanged |
| code | unchanged |
| results | unchanged |

The scratch dir `/tmp/order3-harv-fix` was deleted, and no `__pycache__` was
left.

### Departures from the request

1. **The kernel series is carried for SQLS too.** The request said null for
   SQLS. But the fvm SQLS path also writes `hhl_kernel_rel_err` into the shared
   metrics CSV, as `linsys_residual / ||b||` on the original system
   (`time_solvers.py:722-731`, `:775`). So the harvester carries it for SQLS
   runs that have the column, and the doc string says what it means there. It
   is null for every archived run, including the August SQLS trial. This has not
   been checked on a real new SQLS run.
2. **`rotated_csv` is a list, not an integer.** It has the same shape as the
   other inventory categories, so its count is `len`.
