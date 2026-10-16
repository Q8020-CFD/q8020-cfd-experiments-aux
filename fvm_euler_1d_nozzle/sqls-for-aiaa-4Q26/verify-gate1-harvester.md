# Gate 1 re-verification: SQLS-aware FVM harvester after code-review amendments

VERDICT: PASS

- Re-verifier: independent agent (did not build or amend the code). Read-only in
  both repos; all probes ran on `cp -Rp` copies under `/tmp/order1-reverify-harv/`
  (deleted at the end). No solver runs, no sweeps, no installs, no network.
- Session window: 2026-10-15T04:10:10Z (first command) to 2026-10-15T04:21:48Z
  (scratch deleted, final state check).
- Target: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
  (876 lines, uncommitted working-tree change on main @ 6f646617; `git diff --stat`
  = 300 insertions, 64 deletions).
- Python: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`
  (3.12.10). Every invocation used
  `PYTHONPYCACHEPREFIX=/tmp/order1-reverify-harv/pyc`; no `__pycache__` appeared
  next to the harvester (checked after every run).
- Did not read any `build-*.md`, `verify-*.md`, `reproduce-*.md` or `STATUS.md`.

## Summary

| Item | Result | One-line evidence |
|---|---|---|
| C1 NaN dq -> not converged | PASS | all-NaN iter6 dq, `final_iters=14`, no stdout -> `converged false, converged_by null`; control with original dq -> `true / dq_norm` |
| C3 SQLS CX under `after.cx_count`, `gate_count` null, basis tags | PASS | SQLS step 0: depth 398, cx_count 200, num_qubits 4, gate_count null, basis `{u3,cx}`; HHL step 0: gate_count 641145, basis `aer_simulator`, scope `all` |
| C5 early-stop guards | PASS | `final_iters=0,max_iters=15` -> false; `final_iters=6` -> `true / solver_early_stop`; `max_iters=1` -> false |
| C7/C8b single computation, passed down | PASS | `_read_stdout(` called once (line 775); `glob("dq_` once (line 327); one `_iter_no` (line 61); `_is_sqls`/`_sqls_params` once each (lines 778-779) |
| C8 pickle `converged` used directly | PASS | `converged=True, converged_by='residual_ratio'` -> `true / residual_ratio / solver`; `converged=False` -> `false / null / solver` despite dq_norm heuristic; `resnorm_init` halves `residual_reduction` to 5.09e-11; keys absent -> `heuristic` |
| C10 banner anchored after last `step:` | PASS | banner then two later `step:` lines -> false; banner last -> `true / solver_stdout` |
| Style | PASS | `HHL_BASIS`/`SQLS_BASIS` at lines 31-32; 0 added lines over 88 chars; 0 added lines with trailing whitespace; `py_compile` OK |
| HHL regression | PASS | 34 differences, all in the allowed set (listed in full below); `converged` stays false |
| SQLS six-fragment sha256 | PASS | all six byte-identical to the files in the real trial dir |
| Git state (both repos) | PASS | exactly as specified |

## Producer-side facts checked against the solver source

The harvester's heuristics are only meaningful if they match what the solver
actually prints and pickles, so I checked the producer (read-only):

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py`,
  repo HEAD f16720b3 (2026-10-15 00:05:08 -0400 = 2026-10-15T04:05:08Z).
  - line 322: `print(f'\nstep: {n}/{nmax} res:{resnorm}, ' ...` -> the harvester
    regex `^\s*step:` (line 262) matches the real step line.
  - line 345: `print(f'SOLUTION CONVERGED at iteration {n}')` -> substring match.
  - lines 382-384 write `'converged'`, `'converged_by'`, `'resnorm_init'` into the
    metadata pickle -> same key names the harvester reads (lines 686, 700-702).
  - lines 321, 341: `dqnorm = np.linalg.norm(q-qold, axis=1)`;
    `if resratio < conv_tol or np.all(dqnorm <= 1e-10)` -> mirrored by
    `_last_dq_converged` (threshold 1e-10, all three equations).
- dq CSV layout (load-bearing for C1, not itself a review finding): using the
  real archived run
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/exact_09899a29/`,
  whose `run.log` line 596 prints
  `dq_norm: [5.36345031e-12 3.74233471e-12 1.03722543e-11]` at step 7, the
  harvester's grouping (row = e*3 + eq, 2nd column `dq_hhl`) of
  `dq_nelem5_iter7_statevector.csv` gives
  `[5.363460e-12, 3.742244e-12, 1.037232e-11]` (5 significant digits match); the
  alternative grouping (row = eq*nelem + e) gives
  `[5.63e-12, 7.50e-12, 7.90e-12]` and does not. Layout assumption confirmed.
- Real FVM logs in scope (40 `run.log` / `q8020_stdout_*.txt` under
  `results/fvm_euler_1d_solver/`): none has a banner before a later `step:` line,
  so C10's anchoring changes no archived verdict.
- Neither the SQLS nor the HHL trial dir has a `q8020_stdout_*.txt` or `run.log`,
  so `stdout_text` is empty for both real harvests; the stdout heuristic never
  fires on them.

## Data used

- SQLS trial (read-only):
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`
  pickle: `nelem 5`, `cfl 1e10`, `max_iters 15`, `final_iters 6`, `conv_tol 1e-10`,
  `nshots 150000`, `linear_solver SQLS`, `quantum_circuit.method full_svd`, `k 128`,
  `state_prep initialize`, `repeats 1`; no `converged` / `converged_by` /
  `resnorm_init` keys. Residual CSV row 0 `residual_total` 12.375368413827264,
  row 6 1.2603788670970093e-09 -> ratio 1.018457653098037e-10 (above
  `conv_tol` 1e-10, so the residual-ratio heuristic is false and dq_norm decides
  the real run). dq iter6 CSV header `dq_lu, dq_sqls,` with 15 rows.
- HHL trial (regression reference, committed fragments):
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/`
  pickle: `max_iters 15`, `final_iters 14`, `conv_tol 1e-10`, `linear_solver HHL`.
- Copies: `cp -Rp <trial> /tmp/order1-reverify-harv/<name>`; then
  `rm -f <copy>/q8020_{case,code,backend,artifacts,results,analysis}_0.json`
  (the HHL `q8020_*_local.json` sweeper files were left in place; the harvester
  skips every `q8020_*` file in `_inventory_files`). Sub-second mtimes were
  verified preserved: `stat -f '%Fm %N'` listings of all non-`q8020_` files in
  original vs copy were `diff`-identical for both trials (e.g.
  `1787005687.201973662 system_Ab_nelem5_iter0.pkl`).

## Per-finding evidence

Probe harness (all probes): fresh `cp -Rp` of the cleaned SQLS copy; pickle edits
via a scratch `edit_pkl.py` (pickle load, assign, dump) with the metautil python;
then
`PYTHONPYCACHEPREFIX=/tmp/order1-reverify-harv/pyc <venv>/python <harvester> --outdir /tmp/order1-reverify-harv/<probe>`
and a json read of `q8020_analysis_0.json`. All runs exited 0 with no stderr
beyond the harvester's "Metadata fragments written" line.

### C1: NaN dq must yield not-converged

Code (lines 639-644): `if not norm <= 1e-10: return False` with comment
"NaN-safe, as np.all(dqnorm <= 1e-10)". `float("nan") <= 1e-10` is False, so
`not False` returns not-converged.

| Probe | Setup | Observed `analysis` |
|---|---|---|
| `c1_nan` | `dq_nelem5_iter6_statevector_shots150000.csv` rewritten to header `dq_lu, dq_sqls,` + 15 rows `nan,nan`; pickle `final_iters=14` (so early stop cannot fire); 0 stdout files | `converged False, converged_by None, converged_source heuristic, residual_reduction 1.018457653098037e-10` |
| `c1_ctl` (control) | same pickle edit, original iter6 dq | `converged True, converged_by dq_norm, converged_source heuristic` |
| `c1_one` | single cell: row 7 of the CSV changed to `-3.9866779977871345e-11,nan`; `final_iters=14` | `converged False, converged_by None` |

Informational (not gating): `c1_nan_fi6` = all-NaN dq with the REAL
`final_iters=6` -> `converged True, converged_by solver_early_stop`. That is the
early-stop heuristic by design (the solver loop breaks only on convergence), and
is exactly why the finding's probe pins `final_iters` high.

### C3: SQLS CX count placement and basis tags

From the regression harvest of the SQLS copy (byte-identical to the real
`q8020_artifacts_0.json`, see sha256 below):

```
SQLS circuit_basis {u3,cx}
SQLS step0 {"step": 0, "wall_time_generate_s": null, "wall_time_transpile_s": null,
  "wall_time_execute_s": 0.102901, "before": null,
  "after": {"depth": 398, "num_qubits": 4, "gate_count": null, "cx_count": 200,
            "basis": "{u3,cx}", "gate_count_scope": "none; CX only, in cx_count"},
  "sqls": {"method": "full_svd", "k": 128, "state_prep": "initialize", "repeats": 1,
           "n_data_qubits": 4, "m_ancilla": 0, "cx_count": 200, "circuit_depth": 398,
           "aer_device": "CPU", "solve_time": 0.10290098190307617}}
SQLS all cx: [200, 201, 201, 200, 201, 201, 201]  gate_count: [None x7]
SQLS circuit_timing_total_s {generate None, transpile None, execute 0.575051 s, total 0.575051 s}
SQLS linear_system {matrix_size_original 15, matrix_size_padded 16, matrix_size_hermitian None,
  condition_number_range [59.9218, 95.9779]}
HHL circuit_basis aer_simulator
HHL step0 after {'depth': 596688, 'num_qubits': 14, 'gate_count': 641145,
  'basis': 'aer_simulator', 'gate_count_scope': 'all'}
HHL step0 before {'depth': 5, 'num_qubits': 14, 'gate_count': 19}
HHL has cx_count key in any after? False
```

Matches the expected step-0 values (depth 398, cx_count 200, num_qubits 4,
gate_count null); HHL keeps the all-gates `gate_count` in the Aer basis; `basis`
and `gate_count_scope` are present on both. Source: lines 460-467 (SQLS),
547-553 (HHL), constants at lines 31-32.

### C5: `solver_early_stop` guards

Code (lines 716-720): `final_iters is not None and max_iters is not None and
int(max_iters) > 1 and 0 < int(final_iters) < int(max_iters) - 1`.

All probes: dq files removed, no stdout, residual ratio 1.018e-10 > `conv_tol`
1e-10, so only early stop can decide.

| Probe | Pickle | Observed |
|---|---|---|
| `c5_zero` | `final_iters=0, max_iters=15` | `converged False, converged_by None, converged_source heuristic` |
| `c5_ctl` (control) | `final_iters=6, max_iters=15` | `converged True, converged_by solver_early_stop` |
| `c5_max1` | `final_iters=0, max_iters=1` | `converged False, converged_by None` |
| `c5_13` (boundary) | `final_iters=13, max_iters=15` | `converged True, converged_by solver_early_stop` |
| `c5_14` (boundary, hit cap) | `final_iters=14, max_iters=15` | `converged False, converged_by None` |

### C7/C8b: computed once in `generate_metadata`, passed down

grep over the harvester (line numbers verbatim):

```
_read_stdout      183:def _read_stdout(outdir: Path) -> str:
                  775:    stdout_text = _read_stdout(outdir)           <- the only call
glob("dq_         327:    dq_files = sorted(outdir.glob("dq_nelem*_iter*_*.csv"), key=_iter_no)   <- the only dq glob
_iter_no          61:def _iter_no(path: Path) -> int:                   <- single definition; used at 327, 330, 344, 349
_is_sqls          267:def ...  778:    sqls = _is_sqls(run_params, qc_metadata)             <- once
_sqls_params      285:def ...  779:    sqls_params = _sqls_params(run_params, qc_metadata) if sqls else None   <- once
```

Other `glob(` calls (lines 128, 153, 161, 169, 177, 185, 344) are the
one-per-artifact extractors and the results-CSV glob; none re-globs dq files or
re-reads stdout. `stdout_text` is passed to `_build_backend` (813),
`_build_results` (815-816) and `_build_analysis` (817-818); `dq_by_step`/`unsteady`
from line 776 are passed to `_extract_per_iteration_results` (777) and
`_build_analysis` (818); `sqls_params` to `_build_backend` and the `code`
fragment; `sqls` to `_build_artifacts` (814).

### C8: pickle `converged` / `converged_by` / `resnorm_init`

Code: lines 686-688 (`first_res = run_params.get("resnorm_init") or
residuals[0]["residual_total"]`), lines 700-703 (`isinstance(run_params.get(
"converged"), bool)` -> use pickle, `converged_by` only when converged,
`converged_source = "solver"`), lines 704-724 (else: heuristics, `"heuristic"`).

| Probe | Pickle injection | Observed |
|---|---|---|
| `c8_true` | `converged=True, converged_by='residual_ratio'` | `converged True, converged_by residual_ratio, converged_source solver` |
| `c8_false` | `converged=False, converged_by='dq_norm'`, dq files intact (heuristics would say dq_norm, cf. `c1_ctl`) | `converged False, converged_by None, converged_source solver` |
| `c8_init` | `converged=True, converged_by='dq_norm', resnorm_init=24.750736827654528` (= 2 x row-0 residual) | `residual_reduction 5.092288265490185e-11` (exactly half of 1.018457653098037e-10); `converged True / dq_norm / solver` |
| real trial (keys absent) | untouched pickle | `converged True, converged_by dq_norm, converged_source heuristic` |

Informational (not gating): `c8_npbool` with `converged=np.bool_(False)` ->
`False / None / solver` (numpy scalars are unwrapped by `.item()` in
`_extract_run_params`, so a numpy bool is accepted as the solver verdict);
`c8_none` with `converged=None` -> falls to heuristics (`True / dq_norm /
heuristic`); `c8_init_only` with only `resnorm_init=24.75...` and no `converged`
key -> `heuristic`, and because the denominator doubles, the ratio 5.09e-11 is
now below `conv_tol` so `converged_by residual_ratio` (consistent with the
documented rule that `resnorm_init` is the denominator when present).

### C10: banner counts only after the LAST `step:` line

Code (lines 256-264): `steps = list(re.finditer(r"^\s*step:", text,
re.MULTILINE)); tail = text[steps[-1].end():] if steps else text; return
"SOLUTION CONVERGED" in tail`.

All C10 probes: dq files removed, `final_iters=14` (cap), pickle `conv_tol=1e-12`
so the ratio 1.018e-10 is above tolerance with margin; only the stdout heuristic
can decide. Synthetic `q8020_stdout_x.txt` written with real-format lines
(`step: 0/15 res:... res/res0:... dq_norm: [...]`, banner block copied from the
solver's format).

| Probe | stdout content | Observed |
|---|---|---|
| `c10_early` | `step: 0/15 ...`, banner block (`SOLUTION CONVERGED at iteration 0`), then `step: 1/15 ...`, `step: 2/15 ...`, no further banner | `converged False, converged_by None, converged_source heuristic` |
| `c10_last` (control) | `step: 0/15`, `step: 1/15`, `step: 2/15`, then banner block last | `converged True, converged_by solver_stdout, converged_source heuristic` |
| `c10_none` | no stdout file | `converged False, converged_by None` |

Informational: `c10_nostep` (banner present, zero `step:` lines) ->
`True / solver_stdout` because `tail = text` when no step line exists; that is the
documented fallback (line 263) and cannot occur in a real solver log, which always
prints a step line before the banner (solver lines 322 vs 345).

### Style

- `HHL_BASIS = "aer_simulator"` (line 31) and `SQLS_BASIS = "{u3,cx}"` (line 32)
  at module top, directly after the imports.
- `git diff -- <harvester> | grep '^+' | grep -v '^+++' | awk 'length > 89'` ->
  no output (0 added lines over 88 chars).
- `git diff -- <harvester> | grep '^+' | grep -v '^+++' | grep -E '[[:space:]]+$'`
  -> no output (0 added lines with trailing whitespace).
- Pre-existing, unchanged, not introduced by this change: whole-file lines 394
  (97 chars), 514 (90 chars), 802 (89 chars) are HEAD lines 323, 354, 572
  verbatim; the one trailing-whitespace line (77, inside the `_inventory_files`
  docstring) is HEAD line 67. None appears in the diff.
- `PYTHONPYCACHEPREFIX=/tmp/order1-reverify-harv/pyc <venv>/python -m py_compile
  <harvester>` -> exit 0.

## HHL regression: full difference list

Command: harvest `/tmp/order1-reverify-harv/hhl_regress` (a `cp -Rp` of the HHL
trial with the six fragments removed), then a recursive JSON walk comparing each
of the six committed fragments to the new ones (dict keys, list indices and
lengths, leaf values; NaN==NaN). Result:

```
--- case:      0 difference(s)
--- code:      0 difference(s)
--- backend:   0 difference(s)
--- results:   0 difference(s)
--- artifacts: 31 difference(s)
  artifacts.circuit_basis: committed=<ABSENT> -> new='aer_simulator'
  artifacts.transpile_passes[i].after.basis:            committed=<ABSENT> -> new='aer_simulator'   for i = 0..14 (15 entries)
  artifacts.transpile_passes[i].after.gate_count_scope: committed=<ABSENT> -> new='all'             for i = 0..14 (15 entries)
--- analysis:  3 difference(s)
  analysis.converged_by:       committed=<ABSENT> -> new=None
  analysis.converged_source:   committed=<ABSENT> -> new='heuristic'
  analysis.residual_reduction: committed=0.000549 -> new=0.0005490977149420549
```

Total 34 differences, every one inside the allowed set (`residual_reduction`
precision, `converged_by` null, `converged_source` "heuristic",
`circuit_basis`, per-step `after.basis` / `after.gate_count_scope`). Nothing
else changed: in particular `file_inventory` (mtimes), `backend.num_qubits` 5,
`code.algorithm` "HHL", all `before`/`after` depth/qubit/gate counts, timings,
`linear_system`, `results.*`, and `analysis.hhl_metrics` are identical. New HHL
analysis header verbatim:
`{'iterations_completed': 15, 'converged': False, 'converged_by': None,
'converged_source': 'heuristic', '_source': 'solver', 'fidelity':
0.9933403261305034, 'l2_error_normalized': 0.08167495796430485, 'residual':
0.0037252461048310325, 'shots': 150000, 'residual_reduction':
0.0005490977149420549}` -> HHL `converged` stays false.

## SQLS six-fragment sha256 comparison

Harvested `/tmp/order1-reverify-harv/sqls_regress` (a `cp -Rp` of the SQLS trial
with the six fragments removed) and compared with the six untracked files in the
real trial dir. `shasum -a 256` listings were `diff`-identical and `cmp` passed
on every pair (byte-identical). No fragment carries a timestamp (`grep -l
timestamp` over the six real files matches nothing; the only timestamp writer in
`meta_fragment.py` is `make_experiment_meta`, line 175, which the harvester does
not use).

```
711cf6a4b38da13b64cd1eecb35dc330fba7286edb2d7bdfc44e98e54bd8b606  q8020_analysis_0.json
1addd1016efce9227c3edd8b081cc999676b0dd1e70c4f6ee6a2aabc2064e7c3  q8020_artifacts_0.json
5b74731160f951e3306d67bd56e5deff4098bf60e95f52692af56bbd073ebaac  q8020_backend_0.json
3dd93d5f230ad3a75a81f3182edd45a01176aac9e924e09d5b9d31df71c8d36a  q8020_case_0.json
ca03accf849a65a1d53d28ce19bd350aee97dad77566e09c3f85ba04653f7be5  q8020_code_0.json
6e4a2356a7d947814125178b7db4faa0d1cd8a37c6d7682fddc8b9a03c82b0bf  q8020_results_0.json
```

(identical for `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`
and `/tmp/order1-reverify-harv/sqls_regress/`). Real SQLS `analysis` header:
`iterations_completed 7, converged true, converged_by "dq_norm",
converged_source "heuristic", residual 1.2276304729466986e-09,
residual_reduction 1.018457653098037e-10`; `code`: `algorithm "SQLS",
sqls_method "full_svd", sqls_k 128, sqls_state_prep "initialize",
sqls_repeats 1`; `backend`: `num_qubits 4, nshots 150000, effective_shots
150000`.

## Git state

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments` (checked before and after
all harvests; 12 status lines both times):

```
git log -1 -> 6f6466172b1509f3484f88db0455ca792defdc81 (2026-09-20 21:37:41 -0400)
 M aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml
 M aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml
 M aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py
 M aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py
 M aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/harvest_lugo_all.sh
?? aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_analysis_0.json
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_artifacts_0.json
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_backend_0.json
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_case_0.json
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_code_0.json
?? results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_results_0.json
```

Exactly the 5 expected modified files, the untracked `sqls-for-aiaa-4Q26/`
folder (this report lands inside it, so the status line set is unchanged) and
the six SQLS fragments.

`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`: HEAD
753b97eb8b2ff1235ac2a59baa94ebab7709251c (2026-07-26 19:28:56 -0400);
`git status --short` = 4 ` M` lines, `git status --porcelain
--untracked-files=all | grep '^??'` -> nothing untracked; `git diff --stat`:

```
 tests/examples/base_case.toml            | 2 +-
 tests/examples/base_case_hhl.toml        | 2 +-
 tests/examples/fvm_1d_smoke_test.toml    | 2 +-
 tests/examples/hhl_time_step_impact.toml | 2 +-
 4 files changed, 4 insertions(+), 4 deletions(-)
```

`git diff` confirms each is a one-line `_case_postproc` path change
`codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` ->
`aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`;
nothing else.

## Not checked, and why

- Downstream consumers (sweeper aggregation / make_meta schema validation of the
  fragments) were not exercised; only fragment content was compared. Out of the
  gate's scope.
- The unsteady (`_nsteps`) dq naming path (`_last_dq_converged` returns False by
  design) and the `run.log` stdout fallback were not probed; neither trial in
  scope exercises them and the fallback code is unchanged apart from the banner
  anchoring (which was probed via `q8020_stdout_x.txt`).
- The resumed-chunk (`final_iters == 0`) and solver-written `converged` cases were
  synthesized by editing pickle copies; no archived run carries those keys
  (confirmed: both trial pickles lack them) and no solver run was performed.
- The two gate fixtures (`c5_*`, `c8_*`) assume the solver writes `converged` as a
  Python bool; a numpy bool was also shown to work (informational probe).
- Non-gating observation for a future pass: `_build_backend` (lines 405-408)
  computes SQLS `num_qubits` as `int(n_data_qubits) + int(m_ancilla)` without the
  `-1`-means-not-logged guard that `_int_or_none` applies in
  `_build_artifacts_sqls` (lines 451-453). No effect on this trial
  (`m_ancilla = 0`); it would under-count width by one if a future CSV logged
  `m_ancilla = -1`. Not among the review findings; recorded only.

## Scratch cleanup

`/tmp/order1-reverify-harv/` (all copies, probe dirs, `edit_pkl.py`, `jdiff.py`,
pyc prefix) removed at the end of the session. No `__pycache__` was created next
to the harvester. Nothing under `results/` was written; no file other than this
one was created or modified in `sqls-for-aiaa-4Q26/`.
