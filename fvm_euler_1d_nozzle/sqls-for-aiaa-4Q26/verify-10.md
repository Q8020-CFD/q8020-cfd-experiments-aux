# Verify 10 — SQLS-aware harvester

VERDICT: PASS

Independent verification of work item 10 (make `fvm_euler_1d_solver_harvester.py`
SQLS-aware; fix `converged` / `residual_reduction`; re-harvest the SQLS trial).
Verified against the UNCOMMITTED working tree of
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments` at main 6f646617.
All runs 2026-10-15T03:10:33Z to 2026-10-15T03:19:00Z (UTC) on macOS (Darwin
25.6.0), Python 3.12.10 from
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`
(`q8020_cfd_metautil` resolves to
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/`).
No build-*/verify-*/reproduce-*/STATUS.md files were read. No solver runs.
Both repos were left read-only; all work was on copies under
`/tmp/order1-verify-10/` (8.4 MB at peak, 20 scratch dirs), deleted at the end.

Harvester under test:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
(`git diff --stat`: 268 insertions, 36 deletions; 215 added lines by `git diff -U0`).

## Setup

```
mkdir -p /tmp/order1-verify-10/{sqls_clean,hhl_clean,april_078e27ce}
SRC=/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver
find $SRC/2026-08-17-sqls-local-v2/trial_0 -maxdepth 1 -type f ! -name 'q8020_*' -exec cp -p {} /tmp/order1-verify-10/sqls_clean/ \;
find $SRC/2026-08-17-qiskit25-local/trial_0 -maxdepth 1 -type f ! -name 'q8020_*' -exec cp -p {} /tmp/order1-verify-10/hhl_clean/ \;
cp -p $SRC/2026-04-08/_85fd6d17/more_iters_0/trial_1_078e27ce/* /tmp/order1-verify-10/april_078e27ce/
```

Copies: sqls_clean 34 files (0 q8020), hhl_clean 66 files (0 q8020),
april_078e27ce 261 files (full copy incl. real `q8020_stdout_078e27ce.txt`).
`cp -p` preserves mtimes, which matters for criterion 4 (file_inventory
records `modified`).

## Criterion 1 — SQLS copy produces six correct fragments: PASS

```
/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python \
  /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py \
  --outdir /tmp/order1-verify-10/sqls_clean
```

Run 2026-10-15T03:11:02Z, wall 0.15 s (`/usr/bin/time -p` real), exit 0.
Produced exactly `q8020_{case,code,backend,artifacts,results,analysis}_0.json`.

Observed, field by field (from the scratch output):

| Field | Observed | Expected | OK |
|---|---|---|---|
| `code.algorithm` | `"SQLS"` | SQLS | yes |
| `code.sqls_method` | `"full_svd"` | full_svd | yes |
| `code.sqls_k` | 128 | 128 | yes |
| `code.sqls_state_prep` | `"initialize"` | initialize | yes |
| `code.sqls_repeats` | 1 | 1 | yes |
| `artifacts.transpile_passes` length | 7 (steps 0..6) | 7 | yes |
| `transpile_passes[i].after.depth` | 398, 397, 398, 398, 398, 398, 398 | 397 to 398 | yes |
| `transpile_passes[i].after.gate_count` | 200, 201, 201, 200, 201, 201, 201 | 200 to 201 | yes |
| `transpile_passes[i].after.num_qubits` | 4 (all steps) | 4 | yes |
| `transpile_passes[i].after.basis` | `"{u3,cx}"` (all) | {u3, cx} | yes |
| `transpile_passes[i].after.gate_count_scope` | `"cx"` (all) | — (new tag) | yes |
| `artifacts.circuit_basis` | `"{u3,cx}"` | — (new tag) | yes |
| `transpile_passes[i].wall_time_execute_s` | 0.102901, 0.078859, 0.075332, 0.077435, 0.077961, 0.077801, 0.084762 s | nonzero, from solve_time | yes |
| `transpile_passes[i].wall_time_generate_s` / `wall_time_transpile_s` / `before` | null / null / null (all steps) | null, not 0 | yes |
| `artifacts.circuit_timing_total_s` | `{generate: null, transpile: null, execute: 0.575051, total: 0.575051}` s | about 0.575 s total | yes (sum of CSV solve_time = 0.5750510692596436 s) |
| `artifacts.linear_system.matrix_size_hermitian` | null | null, not 0 | yes |
| `artifacts.linear_system` (rest) | `matrix_size_original 15, matrix_size_padded 16, condition_number_range [59.9218, 95.9779]` | — | yes |
| `transpile_passes[i].sqls` | present every step with exactly `method, k, state_prep, repeats, n_data_qubits, m_ancilla, cx_count, circuit_depth, aer_device, solve_time` (e.g. step 0: full_svd, 128, initialize, 1, 4, 0, 200, 398, CPU, 0.10290098190307617 s) | 10 fields | yes |
| `backend.num_qubits` | 4 | n_data_qubits + m_ancilla = 4 + 0 | yes |
| `backend.nshots` | 150000 | — | yes |
| `backend.effective_shots` | 150000 | nshots x repeats = 150000 x 1 | yes |
| `analysis.converged` | true | true | yes |
| `analysis.converged_by` | `"dq_norm"` | — (new) | yes |
| `analysis.residual_reduction` | 1.018457653098037e-10 | about 1.0185e-10, unrounded | yes (bit-exact `1.2603788670970093e-09 / 12.375368413827264`) |
| `analysis.iterations_completed` | 7 | — | yes |
| Any 0 in HHL-only fields | none | none | yes |

`results` carries 7 `per_iteration` entries (step, solution, dq) and 7
`residual_history` rows; no stdout exists in this trial so no solution vectors
(correct: nothing to parse). `file_inventory`: 25 csv, 8 pkl, 1 png, 0 qpy.

Metautil roll-up (`harvest_metadata(Path(...), read_only=True)`) over the
scratch dir: counts `{case 1, code 1, backend 1, artifacts 1, results 1,
analysis 1, experiment 0, exec_stats 0}`, zero warnings.

## Criterion 2 — stdout parsing, SQLS 3-column and HHL 4-column: PASS

Formats taken from the solver source, not from the harvester:
`time_solvers.py` line 670 prints `LU sol \t    SQLS sol    L1_diff(%)`,
line 580 prints `LU sol \t    Herm LU sol    HHL sol    L1_diff(%)`; rows come
from `math_tools.print_matrix_scientific` (3-decimal `%.3e`, right-justified,
joined by two spaces); fences are `"=" * 88`. I generated the synthetic rows
from each copy's own `dq_*.csv` so the extracted vectors could be checked.

### 2a. Synthetic SQLS stdout

```
cp -rp /tmp/order1-verify-10/sqls_clean /tmp/order1-verify-10/sqls_stdout   # then removed q8020_*
# wrote /tmp/order1-verify-10/sqls_stdout/q8020_stdout_test.txt: 7 blocks, header
#   "LU sol \t    SQLS sol    L1_diff(%)" (tab verified with cat -vet), plus a
#   SOLUTION CONVERGED banner
<venv python> <harvester> --outdir /tmp/order1-verify-10/sqls_stdout
```

Run 2026-10-15T03:15:57Z, wall 0.12 s. Result: all 7 `per_iteration` entries
carry `lu_reference_vector` (15 values) and `sqls_solution_vector` (15 values);
no `hhl_solution_vector` anywhere. Step 6 `sqls_solution_vector` equals the CSV
`dq_sqls` column rounded to 3 significant figures (exact list match:
`[-0.0, 2.582e-11, -0.0, -0.0, -0.0, -5.164e-11, -0.0, -0.0, -0.0, 0.0, -0.0,
0.0, 2.582e-11, 0.0, 2.582e-11]`). `results.lu_reference_vector_final` present
(15 values). `analysis.converged_by` stayed `dq_norm` (it precedes
`solver_stdout` in the criteria order).

### 2b. Synthetic HHL stdout

```
cp -rp /tmp/order1-verify-10/hhl_clean /tmp/order1-verify-10/hhl_stdout   # then removed q8020_*
# wrote q8020_stdout_test.txt: 15 blocks, 4-column header with "Herm LU sol" and "HHL sol"
<venv python> <harvester> --outdir /tmp/order1-verify-10/hhl_stdout
```

Run 2026-10-15T03:15:58Z, wall 0.12 s. Result: 15/15 entries carry
`hhl_solution_vector` and `lu_reference_vector`, 0 carry
`sqls_solution_vector`. Step 14 `hhl_solution_vector` and
`lu_reference_vector` match the CSV `dq_hhl` / `dq_lu` columns at 3 s.f.
(exact list match). `analysis.converged` false, `converged_by` null.

### 2c. Real April HHL stdout

```
<venv python> <harvester> --outdir /tmp/order1-verify-10/april_078e27ce
```

Run 2026-10-15T03:11:02Z, wall 0.60 s. Source
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-08/_85fd6d17/more_iters_0/trial_1_078e27ce/`
(HHL, cfl 1.0, max_iters 60, 60 iterations, 120 lines containing "LU sol" =
60 banner lines + 60 headers). Result: 60/60 `per_iteration` entries have
`lu_reference_vector` and `hhl_solution_vector`, each 15 long, none missing;
step 0 `lu[:4] = [-0.001238, -0.0002227, -0.002418, -0.03105]`,
`hhl[:4] = [-0.0, -0.0, -0.0, -0.03308]`, matching the stdout table rows 1-4.
`analysis.converged` false (hit the 60-iteration cap; residual_reduction
1.5793341615080853e-06, conv_tol 1e-10; no banner in stdout; final_iters 59 =
max_iters - 1). `code.algorithm` HHL, `backend.num_qubits` 5,
`circuit_basis aer_simulator`, `matrix_size_hermitian` 32.

## Criterion 3 — HHL regression vs committed fragments: PASS

```
<venv python> <harvester> --outdir /tmp/order1-verify-10/hhl_clean       # 2026-10-15T03:11:02Z, wall 0.15 s
# then a recursive json diff (sorted keys) against
# /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/q8020_*_0.json
```

Complete list of differences (committed -> new):

- `case`: json-equal, 0 differences.
- `code`: json-equal, 0 differences.
- `backend`: json-equal, 0 differences (no `effective_shots` added for HHL;
  see finding F6).
- `results`: json-equal, 0 differences.
- `artifacts`: 31 differences, all ADDED keys:
  - `artifacts/circuit_basis = "aer_simulator"` (1)
  - `artifacts/transpile_passes[i]/after/basis = "aer_simulator"` for i = 0..14 (15)
  - `artifacts/transpile_passes[i]/after/gate_count_scope = "all"` for i = 0..14 (15)
- `analysis`: 2 differences:
  - ADDED `analysis/converged_by = null`
  - CHANGED `analysis/residual_reduction: 0.000549 -> 0.0005490977149420549`
    (precision only; 0.0067952865175986326 / 12.375368413827264)

`analysis.converged` is unchanged at false. Every difference is in the
acceptable set (basis/scope tags, converged_by, residual_reduction precision).

## Criterion 4 — real SQLS trial fragments match the fresh harvest: PASS

```
for s in case code backend artifacts results analysis; do cmp -s $REAL/q8020_${s}_0.json /tmp/order1-verify-10/sqls_clean/q8020_${s}_0.json; done
shasum -a 256 ...
cd /Users/agallojr/proj/src/q8020/q8020-cfd-experiments && git status --short results/
```

All six files in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`
are BYTE-IDENTICAL to the scratch output (sha256 equal for each; no timestamp
field differs because the only timestamps are file_inventory mtimes, preserved
by `cp -p`). Names are `q8020_<section>_0.json`. `git status --short results/`
lists exactly the six `??` lines for those files and nothing `M` under
`results/`. No other `q8020_*` files exist in that trial dir.

| file | sha256 |
|---|---|
| q8020_analysis_0.json | 341958d9c309b8a730f84c7e1080a5c319e6ee05600a3ddf7b8fbf25f55dd419 |
| q8020_artifacts_0.json | e799ed03ef228c0636028679b112a7c82f1edf8af3a3f03f6e1467f518661124 |
| q8020_backend_0.json | 5b74731160f951e3306d67bd56e5deff4098bf60e95f52692af56bbd073ebaac |
| q8020_case_0.json | 3dd93d5f230ad3a75a81f3182edd45a01176aac9e924e09d5b9d31df71c8d36a |
| q8020_code_0.json | ca03accf849a65a1d53d28ce19bd350aee97dad77566e09c3f85ba04653f7be5 |
| q8020_results_0.json | 6e4a2356a7d947814125178b7db4faa0d1cd8a37c6d7682fddc8b9a03c82b0bf |

## Criterion 5 — nothing committed: PASS

`git -C /Users/agallojr/proj/src/q8020/q8020-cfd-experiments log -1 --oneline`
-> `6f646617 plots for ieee`. Working tree `M` entries are the five
pre-existing ones (the harvester plus the two `.toml` path fixes,
`backend_meta_harvester.py` docstring path, `harvest_lugo_all.sh` path), all
unstaged. Nothing was staged, committed, stashed or checked out by this
verification.

## Findings

Severity scale: HIGH = would make a criterion fail or corrupt data; MEDIUM =
wrong or misleading in a realistic case; LOW = edge case, cosmetic, or
pre-existing.

### Convergence rule (as now implemented, vs the solver)

Solver (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py`
lines 262, 305-313, 334-344): `resnorm_init = residual_norm()` before the loop;
each step appends `resnorm` to `res_hist`, `resratio = resnorm / resnorm_init`,
`dqnorm = np.linalg.norm(q - qold, axis=1)` with `q` shaped (3, nelem) so
`dqnorm` is 3 per-equation norms; breaks only on
`resratio < conv_tol or np.all(dqnorm <= 1e-10)` and prints
`SOLUTION CONVERGED at iteration n`. `final_iters = imax = n` of the last step.
In steady mode `q[...] += dQ` (`time_solvers.py` line 346) and the dq CSV's
second column is that `dQ` flattened element-major (`reshape(nelem, 3)`, index
`e*3 + eq`), so the harvester's `dq[e*3 + eq]` per-equation grouping is the
solver's grouping.

Harvester: `converged_by` = first true of `residual_ratio`
(`last/first < conv_tol`, strict like the solver), `dq_norm` (per-equation norm
of the last steady-mode dq CSV's quantum column, all <= 1e-10), `solver_stdout`
(`"SOLUTION CONVERGED"` in stdout), `solver_early_stop`
(`final_iters < max_iters - 1`). This is a faithful mirror plus two
declaration proxies. Probes on edited copies (all ran, exit 0):

| Probe | Edit | Result | Matches solver? |
|---|---|---|---|
| C1 | pickle final_iters=14, max_iters=15 (cap hit), real iter6 dq (max 5.2e-11) | converged true by dq_norm | yes: the solver would also have declared on that dq (the input is self-inconsistent, not a misclassification) |
| C2 | as C1 plus iter6 dq set to 1e-3 everywhere; ratio 1.0185e-10 vs tol 1e-10 | converged false | yes |
| C3 | as C2 with conv_tol 2e-10 | converged true by residual_ratio | yes |
| C4 | as C2 with residual row 0 set to 1e6 | converged true by residual_ratio (rr 1.26e-15) | n/a: tampered input; see F1 |
| C5 | one iteration, max_iters 1, iter0 dq large | converged false, residual_reduction absent | yes |
| C6 | one iteration, max_iters 15 | converged true by solver_early_stop | yes (loop only breaks on convergence) |
| C7 | as C2 plus a stdout containing only the banner | converged true by solver_stdout | yes |
| C8 | as C2 with last residual_total set to 0.0 | converged false, residual_reduction ABSENT | no, see F2 |
| C9 | iter6 dq: eq0 = 0.9e-10 on all 5 elements, others 0 (per-eq norm 2.01e-10, per-element norm 0.9e-10) | converged false | yes: confirms per-equation grouping (per-element grouping would have said true) |
| C10 | dq files renamed to unsteady `_nsteps<n>_iter0_` form | converged false, no crash | guard works as documented |

- F1 (LOW, comment accuracy): the code comment says "res0 is not recorded, so
  the ratio uses the first logged residual". Row 0 of `residual_*.csv` IS
  `resnorm_init`: the April stdout prints `step: 0/60 res:12.375368413827264,
  res/res0:1.0` and the CSV row 0 is 12.375368413827264; `residual_norm()`
  returns the residual of the state entering the step, so `res_hist[0] ==
  resnorm_init`. `checkpoint_tools.restore_from_checkpoint` restores the full
  `res_hist`, so resumed runs keep row 0 = res0 as well. The computed ratio is
  therefore exactly the solver's `resratio` at the final step. Only a tampered
  CSV (C4) produces a wrong ratio. Fix the comment; no code change needed.
- F2 (LOW): `if first_res and last_res and first_res != 0` drops the ratio
  when the last residual is exactly 0.0 (falsy), so `residual_reduction` is
  omitted and `residual_ratio` cannot fire (C8). In practice an exactly-zero
  residual would come with a zero dq and `dq_norm` would fire, but the field
  should be 0.0, not absent. Use `last_res is not None`.
- F3 (LOW, solver-side degenerate case, not reproduced): with `-resume` where
  `start_iter >= max_iters` the solver loop body never runs, `imax` stays 0,
  and `final_iters = 0 < max_iters - 1` would make `solver_early_stop` fire on
  a run that did nothing. Not reachable from the sweep tooling as far as I can
  see; noting it because the early-stop proxy trusts `final_iters` alone.
- The HHL trial (`2026-08-17-qiskit25-local/trial_0`, final_iters 14 =
  max_iters - 1, ratio 5.49e-4, iter14 dq ~1e-5) correctly stays
  `converged: false`.

### Robustness

| Probe | Edit | Result |
|---|---|---|
| R1 | `qc_metadata_sqls_*.csv` removed | exit 0. code: SQLS + sqls_* from pickle. backend: no num_qubits (correctly omitted), effective_shots 150000. artifacts: 0 passes, linear_system `{}`, but `circuit_timing_total_s.execute = 0.0` and `.total = 0.0` (see F4). analysis unchanged (dq_norm). |
| R2 | empty `q8020_stdout_test.txt` | exit 0. No vectors, no `lu_reference_vector_final`, no banner match; converged by dq_norm. |
| R3 | `cx_count = -1`, `circuit_depth = -1` on every CSV row (the `-v 1` "not counted" flag) | exit 0. `after.depth` null, `after.gate_count` null, `sqls.cx_count` null, `sqls.circuit_depth` null on every step; `after.num_qubits` 4; backend.num_qubits 4. No 0 or -1 leaked. |
| R4 | `metadata_*.pkl` removed | exit 0. code: SQLS detected from the CSV's `solve_time` column, sqls_* from CSV (k 128 as int). backend: name `unknown` (no stdout to fall back on), num_qubits 4, no nshots. case: nelem/conv_tol/max_iters null. analysis: converged false, converged_by null (no conv_tol, nelem, final_iters available). |
| R5 | `solve_time` column deleted from the CSV (pickle still says SQLS) | exit 0 but `wall_time_execute_s` 0.0, `sqls.solve_time` 0.0, timing execute/total 0.0 (see F4). |

- F4 (MEDIUM-LOW, silent zeros): two paths still emit 0.0 where null is
  meant. (a) With no qc_metadata rows, `_build_artifacts_sqls` writes
  `circuit_timing_total_s.execute = 0.0, total = 0.0` (the HHL path has the
  same pre-existing behaviour with its three totals). (b)
  `float(row.get("solve_time", 0.0))` defaults a missing `solve_time` to 0.0
  per step and in the totals. The solver always writes `solve_time`
  (`quantum_tools.py` line 891; `tests/contract.py` lists it), so (b) is
  unlikely in real data; (a) happens whenever the CSV is missing. Neither
  affects the acceptance criteria. Suggest `None` when there are no rows and
  `_float_or_none` for solve_time.
- `_int_or_none` correctly maps the solver's `-1` sentinel
  (`timings.get('cx_count', -1)`) to null.

### HHL-only vs SQLS-only fields, and shared keys with different meaning

- SQLS output: HHL-only fields are null, not 0, everywhere checked
  (`wall_time_generate_s`, `wall_time_transpile_s`, `before`,
  `circuit_timing_total_s.generate/transpile`, `matrix_size_hermitian`).
- HHL output: SQLS-only fields are ABSENT rather than null (`sqls` sub-dict,
  `code.sqls_*`, `backend.effective_shots`). Acceptable, but asymmetric with
  the SQLS side (F6).
- Tagged shared keys: `after.depth` and `after.gate_count` differ in meaning
  (HHL: all gates in the Aer basis; SQLS: CX count in {u3,cx}) and are tagged
  by `after.basis`, `after.gate_count_scope` and `artifacts.circuit_basis`.
  Good. `results.per_iteration[i].dq` rows are self-tagging (`dq_hhl` vs
  `dq_sqls`), and `code.algorithm` tags the whole record.
- F5 (MEDIUM-LOW, untagged shared key): `backend.num_qubits`. For HHL it is the
  CSV `nqubits = log2(dim(A_herm))` = 5, the data register of the
  Hermitian-doubled system (the circuit is 13 to 14 qubits wide,
  `circ_qubits_transpile`). For SQLS it is `n_data_qubits + m_ancilla` = 4,
  the circuit width. The code comment ("nqubits there is the data register
  only") is true of the SQLS CSV but equally true of the HHL CSV, so the
  change makes the two algorithms report different quantities under one key.
  For this trial (full_svd, m_ancilla 0) 4 is both the data register and the
  width, so the number is right either way, and the acceptance criterion
  asked for exactly this; flagging it so a future truncated-SVD run with
  m_ancilla > 0 is not compared qubit-for-qubit against HHL's 5.
- F6 (LOW): `wall_time_execute_s` and `circuit_timing_total_s.total`. HHL
  `execute` is `circ_run_time` (circuit execution only; generate and transpile
  are separate). SQLS `execute` is `solve_time` = the whole `quantum_solve`
  wall (SVD, circuit build, transpile, run, reconstruction). `total` is
  comparable across the two; `execute` is not, and nothing tags that except
  the null generate/transpile. Also `backend.effective_shots` is absent for
  HHL, so a consumer must fall back to `nshots` for HHL but not for SQLS.
- F7 (LOW, cosmetic, pre-existing): `analysis.hhl_metrics` holds SQLS metrics
  for an SQLS run (the solver itself writes them to `hhl_metrics_*.csv`). The
  metrics themselves mean the same thing for both (fidelity and L2 errors vs
  the LU solution of the same system, `linsys_residual = ||A x - b||` on the
  original A), so no silent semantic clash, just a misleading key.

### PEP 8 / line length / whitespace (added lines only)

```
git diff -U0 -- <harvester> | grep '^+' | grep -v '^+++' | sed 's/^+//' | awk 'length($0) > 88'   # -> none
... | grep -nE '[[:space:]]+$'                                                               # -> none
... | grep -P '\t'                                                                           # -> none
```

215 added lines; 0 over 88 characters; 0 with trailing whitespace; 0 tabs.
`python -m py_compile` succeeds. No linter (pyflakes, pycodestyle, flake8,
ruff, pylint) is installed in the metautil venv or on PATH and I installed
nothing, so this is a mechanical check only. Style nits (LOW): the module
constants `HHL_BASIS` / `SQLS_BASIS` and `_STDOUT_SOL_LAYOUTS` are defined
mid-file between functions rather than near the top; `HHL_BASIS` and
`SQLS_BASIS` lack the leading underscore the other module-private names use.

### Other observations

- The working tree also contains unrelated path fixes (`codes/` ->
  `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/`) in `fvm_cfl_sweeps.toml`,
  `fvm_euler_1d_nozzle.toml`, `backend_meta_harvester.py` (docstring) and
  `harvest_lugo_all.sh`. Not part of item 10; not verified beyond noting they
  are path-only edits.
- Running the harvester did not create a `__pycache__` next to it. My
  `py_compile` check did; I removed
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/__pycache__`
  and confirmed `git status` is unchanged.

## Not checked, and why

- Unsteady-mode (`max_inner_iters > 1`, `_nsteps` filenames) harvesting beyond
  confirming the dq_norm guard skips it: no unsteady output exists in
  `results/` and I may not run the solver.
- A real SQLS run with `m_ancilla > 0` (truncated methods) or `repeats > 1`:
  none exists in `results/`; `effective_shots` and `num_qubits` arithmetic were
  checked only on the repeats = 1, m_ancilla = 0 trial and by reading the code.
- A real SQLS stdout (the trial has none): the 3-column path was exercised
  only with the synthetic file built from the solver's print code.
- Linting with pyflakes/pycodestyle: not installed, and installing was out of
  scope.

## Cleanup

`/tmp/order1-verify-10/` deleted after writing this file. No file other than
this one was created or modified in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`.
