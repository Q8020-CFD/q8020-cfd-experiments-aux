# SQLS wiring validation (fvm_euler_1d_solver main @ ef7f0a8b vs sqls @ 9a4346a7)

Read-only validation that the ORNL SVD-based quantum linear solver (`sqls`) is
correctly woven into the 1D Euler nozzle FVM solver as `-linsolver SQLS`.
Written 2026-10-15T01:48Z (UTC) for work item 4 of `WORKPLAN.md`. No solver
was run; the only executions were `import` checks, `--help`, read-only loads of
saved CSV/pickle data, and one harvester pass over a `/tmp` copy of the August
SQLS trial.

Code under review:

- fvm solver: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `main` @ `ef7f0a8b2247615b56e4391fa1804b59825de217`
  (2026-08-17T23:22:59Z, "Add optional SQLS linear solver alongside HHL"),
  venv `.venv` (Python 3.12.10, qiskit 2.5.2, qiskit-aer 0.17.2,
  qiskit-ibm-runtime 0.49.0, numpy 2.5.2, scipy 1.18.0, torch not installed).
- sqls: `/Users/agallojr/proj/src/q8020/sqls`, HEAD
  `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` (2026-06-30T14:40:52Z, "Merge
  branch 'to_be_released' into 'main'"), installed editable into the fvm venv
  (`.venv/lib/python3.12/site-packages/sqls-0.1.0.dist-info/direct_url.json`
  = `file:///Users/agallojr/proj/src/q8020/sqls`, editable; `.pth` ->
  `/Users/agallojr/proj/src/q8020/sqls/src`). `uv.lock` carries no `sqls`
  entry; the `[sqls]` extra in `pyproject.toml` points at the ORNL URL.

Verdict in one line: the wiring is complete and type-correct (every keyword
fvm passes exists on the sqls side, every field fvm reads is populated, imports
succeed, the August trial numbers reproduce), but there are two should-fix
items that affect paper-grade results: (a) the power-of-2 padding constant
`eps=1e-8` in `convert_to_pow2` is what causes the shots-mode fidelity
collapse at Newton convergence, and (b) the metadata harvester reads the SQLS
files but silently zeroes every circuit/timing field because it only knows the
HHL column names. Details in section 6.

## 1. Code path trace (CLI -> time_solvers -> quantum_tools -> sqls)

Sequence for one Newton step with `-linsolver SQLS`:

1. `nozzle_1d_solver.py:61-63` parses `-linsolver {LU,GMRES,HHL,SQLS}`.
2. `nozzle_1d_solver.py:201-214` fills `linsolv_args` for SQLS.
3. `nozzle_1d_solver.py:228-231` builds `BDFTimeSolver(..., linear_solver, linsolv_args)`.
4. `time_solvers.py:136-137` -> `LinearSystemSolver.__init__`; SQLS branch
   `time_solvers.py:277-293` constructs `QuantumSQLS(...)` (quantum_tools.py).
5. `quantum_tools.py:780` -> `QuantumSQLS.get_backend()` (`:787-808`) builds
   `AerSimulator(method='statevector')`; raises `ValueError` unless
   `backend_type == 'ideal'`.
6. Outer loop `nozzle_1d_solver.py:284-323` -> `BDFTimeSolver.solve_one_step`
   (`time_solvers.py:197-201`) -> `LinearSystemSolver.solve_one_step`
   (`:314-389`): FD Jacobian `A` (`:335`, `compute_Jacobian_matrix_FD`
   `:394-422`, dense, N = 3*nelem), RHS `b = unsres` (`:336`).
7. `linear_sys_solve` dispatch `time_solvers.py:433-436` -> `sqls_solve`
   (`:605-692`), stores metrics in `self.hhl_metrics` (name reused).
8. `sqls_solve`: pickles `system_Ab_*.pkl` (`:617-627`); classical reference
   `dq_lu = lu_solve(A, b)` (`:630`); `dq_sqls =
   self.sqls_solver.solve_one_step(A, b, nelem_q, self.iter, step=step)`
   (`:635-636`); global-sign alignment `if np.dot(dq_sqls, dq_lu) < 0:
   dq_sqls = -dq_sqls` (`:640-641`); metrics (`:644-656`); `dq_*.csv`
   (`:671-680`); returns `(dq_sqls, metrics)` (`:682-692`).
9. `QuantumSQLS.solve_one_step` (`quantum_tools.py:810-881`):
   `convert_to_pow2(A_o, b_o)` (`:823`, math_tools.py:28-90), `num_q =
   log2(N)` (`:825`), `count_cx = (verbosity == 2)` (`:829`), call
   `sqls.runtime.quantum.quantum_solve(...)` (`:833-839`), slice
   `x = x_pow2[:nsys].real` (`:847`), write `qc_metadata_sqls_*.csv`
   (`:878-879`, `save_metadata` `:883-895`).
10. `sqls/runtime/quantum.py:quantum_solve` (`:36-141`) -> `sqls.sqls.SQLS`
    (`sqls.py:105-426`) builds the circuit; `_run_statevector` (`:144-184`)
    or `_run_shots` (`:187-237`); returns a length-`2**n_data` vector scaled
    to `||final_b||`.
11. Back in `time_solvers.py:363-383`: per-iteration solution CSV and
    `save_hhl_metrics` (`:438-471`) -> `hhl_metrics_*.csv`.
12. End of run `nozzle_1d_solver.py:339-372`: `metadata_*.pkl` (gated
    `linear_solver in ('HHL','SQLS')` at `:359-367`, pulls
    `sqls_solver.qc_metadata`), `final_results_*.csv` (`:379-381`),
    `residual_*.csv` (`:384-391`), plot (`:404-409`).

### 1a. `nozzle_1d_solver.py` (CLI)

Argparse entries (line, dest, default, choices):

| flag | lines | dest / default | notes |
|---|---|---|---|
| `-nelem` | 53-54 | `nelem` = 200 | |
| `-x` | 55-56 | `x_vec` = [0, 10] | |
| `-time_scheme` | 57-60 | `BDF1`; choices BDF1, BDF2, BDF2OPT, RK1, RK2, RK3 | only BDF* use a linear solver (`:228-233`) |
| `-linsolver` | 61-63 | `LU`; choices LU, GMRES, HHL, SQLS | |
| `-cfl` | 64-65 | 1e10 | help text says `[1000.]`; code default is 1e10 |
| `-iters` | 66-67 | `max_iters` = 2000 | |
| `-initers` | 68-70 | `max_inner_iters` = 10 | `== 1` selects steady-mode file names (`time_solvers.py:253`, `nozzle:300-303`) |
| `-restol` | 71-72 | 1e-2 | inner-loop tolerance |
| `-tol` | 73-74 | `conv_tol` = 1e-10 | help text says `[1e-12]`; code default is 1e-10; it is a residual RATIO tolerance (`:292`, `:313`) |
| `-localdt` | 75-76 | store_true | |
| `-use_dim_form` | 77-78 | store_false -> `nondim = True` by default (`:164`, `:221-223`) | the nondimensionalization flag; both August runs had `nondim = True` |
| `-backend` | 81-90 | nargs+, default `['ideal','statevector']` | split logic `:167-180` |
| `-shots` | 92-94 | `nshots` = 0 | help says "only significant for non-ideal backends"; in practice ideal+shots is the paper protocol |
| `-hhl_scale` | 96-98 | default `'true_scale'`, choices `true_sol`, `leastsq` | default is NOT in choices (argparse does not validate defaults), so HHL falls to the `else` (least-squares) branch at `time_solvers.py:534-539`; HHL-only, see finding 12 |
| `-loadcirc` | 100-101 | `load_qcirc` | HHL only (SQLS never reads it) |
| `-qc_gpu` | 103-104 | `use_qc_gpu` | |
| `-sqls_method` | 107-111 | `full_svd`; choices full_svd, truncated_qr, truncated_mps | |
| `-sqls_k` | 112-114 | 128 | "ignored by full_svd"; invalid for truncated methods unless `2 <= k < N`, see finding 8 |
| `-sqls_state_prep` | 115-118 | `initialize`; choices initialize, mps | |
| `-sqls_repeats` | 119-123 | 1 | fvm default 1 vs sqls default 10, see finding 6 |
| `-noshow` | 126-127 | | |
| `-outdir` | 129-132 | `output_dir` = `output` | |
| `-v`/`-verb`/`-verbosity` | 134-137 | 1; choices 0, 1, 2 | `-v 2` is REQUIRED to get SQLS cx/depth (`quantum_tools.py:829`) |
| `-savedata` | 139-140 | | sets `space_solver.savedata` only (`:374-375`); quantum metadata is saved regardless (`QuantumSQLS.savedata = True`, `quantum_tools.py:765`) |
| `-checkpoint`, `-resume`, `-original_max_iters` | 141-147 | | solver-agnostic; checkpoints pickle `time_solver` (`checkpoint_tools.py`), which holds the `QuantumSQLS` object incl. an `AerSimulator`; not exercised in August |

`linsolv_args` (lines 182-214). Defaults `:182-188`: `backend_type='ideal'`,
`backend_method='statevector'`, `shots=0`, `hhl_scale_type='true_sol'`,
`load_qcirc=False`, `use_gpu=False`, `output_dir='output'`.

- HHL branch `:190-200` sets `backend_type`, `backend_method`, `shots`,
  `load_qcirc`, `use_gpu`, `output_dir`, `hhl_scale_type`, `hhl_verbosity`;
  forces `shots = 128` for a non-ideal backend with `-shots 0`.
- SQLS branch `:201-214` sets `backend_type`, `backend_method`, `shots`,
  `load_qcirc` (unused downstream), `use_gpu`, `output_dir`, `hhl_verbosity`,
  `sqls_method`, `sqls_k`, `sqls_state_prep`, `sqls_repeats`. No
  `hhl_scale_type` override (stays `'true_sol'`, unused by SQLS). No
  non-ideal shots default (moot: SQLS is ideal-only).

Every `linear_solver in ('HHL', 'SQLS')` gate:

- `:279-282` `case_name = f'nelem{N}_{linsolver}'` + `_{backend_method}` +
  `_nshots{n}` -> drives `results_{case_name}_iter{n}.csv` (`:300-305`),
  `metadata_{case_name}.pkl` (`:369`), `final_results_{case_name}.csv`
  (`:379`), `residual_{case_name}.csv` (`:384`), and the plot file name.
- `:359-367` metadata extras `backend_type`, `backend_method`, `nshots`, and
  `quantum_circuit = sqls_solver.qc_metadata` (via `getattr(...,'hhl_solver')
  or getattr(...,'sqls_solver')`).
- `:397-400` plot label suffix.
- Checkpointing (`:308-312`, `:319-322`) is NOT gated on the solver.

### 1b. `time_solvers.py`

- Init branch `:277-293`: `from quantum_tools import QuantumSQLS`;
  `QuantumSQLS(backend_type=, backend_method=, nshots=linsolv_args['shots'],
  use_gpu=, output_dir=, verbosity=linsolv_args['hhl_verbosity'],
  steady_mode=self.steady_mode, method=linsolv_args['sqls_method'],
  k=linsolv_args['sqls_k'], state_prep=linsolv_args['sqls_state_prep'],
  repeats=linsolv_args.get('sqls_repeats', 1))`. Any exception (ImportError,
  the `ValueError` from a non-ideal backend, ...) is caught and only printed
  (`:292-293`); `self.sqls_solver` stays `None` and the run proceeds until the
  first linear solve raises `RuntimeError('SQLS solver not initialized.
  Install the optional sqls back-end ...')` at `:612-615` (misleading message
  when the real cause was the backend type; finding 7).
- Dispatch `:433-436`: `dQ, metrics = self.sqls_solve(A, b, step=step);
  self.hhl_metrics = metrics`.
- Formation of A and b: `A` is the dense FD Jacobian plus `diag(1/dt)*aq`
  (`:394-422`), `b = unsres` flattened element-major (`:336`). For SQLS there
  is NO `convert_system_to_herm` and NO `scale_Ab_by_spectral_radius` (both
  HHL-only; compare `hhl_solve` `:517-518` and `quantum_tools.py:553,
  :566-567`). The only transformation is `convert_to_pow2` inside
  `QuantumSQLS.solve_one_step` (`quantum_tools.py:823`): pads A
  bottom/right with an identity block and pads b with the constant
  `eps = 1e-8` (`math_tools.py:28`, `:62-66`). N = 15 -> 16 for nelem = 5.
- Reconstruction: `QuantumSQLS.solve_one_step` returns the leading `nsys`
  real entries of the length-`2**num_q` vector already scaled to
  `||final_b||` (`quantum_tools.py:847`); `sqls_solve` applies no further
  scaling, only the global sign flip against `dq_lu` (`:640-641`).
- Metrics `:644-656`: `linsys_residual = ||A dq_sqls - b||_2`; `fidelity =
  quantum_tools.fidelity(dq_sqls, dq_lu)` (`quantum_tools.py:123-134`,
  qiskit `state_fidelity` of the two unit vectors, i.e. |<a|b>|^2);
  `l2_error_abs = ||dq_lu - dq_sqls||`; `l2_error_rel = abs / ||dq_lu||`;
  `l2_error_normalized = ||dq_lu/||dq_lu|| - dq_sqls/||dq_sqls||||`. Note the
  reference is `dq_lu` of the ORIGINAL system (HHL uses `dq_herm` from the
  Hermitian-doubled system, `:521`, `:553`).
- Written files for SQLS: `system_Ab_nelem{n}_iter{step}.pkl` (`:617-627`),
  `dq_nelem{n}_iter{step}_{backend_method}[_shots{s}].csv` with header
  `dq_lu, dq_sqls,` (`:671-680`), `results_nelem{n}_iter{step}_{backend_method}[_shots{s}].csv`
  (`:370-379`), `hhl_metrics_nelem{n}_{backend_method}[_shots{s}].csv`
  with columns `step, iter, fidelity, l2_error_abs, l2_error_rel,
  l2_error_normalized, linsys_residual` (`:438-471`). The `hhl_metrics_`
  prefix is deliberately reused for SQLS (`:435` comment).

### 1c. `quantum_tools.py` class `QuantumSQLS` (lines 720-895)

- Constructor `:755-758`: `(backend_type='ideal', backend_method='statevector',
  nshots=0, verbosity=2, use_gpu=False, output_dir='.', steady_mode=False,
  method='full_svd', k=128, state_prep='initialize', repeats=1, *args,
  **kwargs)`. `self.mode = 'shots' if nshots else 'statevector'` (`:774`).
  `self.savedata = True` unconditionally (`:765`).
- `get_backend` `:787-808`: `if self.backend_type != 'ideal': raise
  ValueError(...)` (`:790-793`); always `AerSimulator(method='statevector')`
  (`:795`); `backend_method` is ignored for the simulator but still used in
  file names. GPU attempt `:796-801`.
- `solve_one_step` `:810-881`: lazy `from sqls.runtime.quantum import
  quantum_solve` (`:816`); `convert_to_pow2(A_o, b_o, verbosity=...)`
  (`:823`); `count_cx = (self.verbosity == 2)` (`:829`); the call
  (`:833-839`):

  ```
  x_pow2 = quantum_solve(
      csr_matrix(A_pow2), b_pow2, num_q, self.backend,
      psi_norm=b_pow2, mode=self.mode, k=self.k, method=self.method,
      state_prep=self.state_prep, shots=(self.nshots or int(1e6)),
      repeats=self.repeats,
      sqls_out=sqls_out, timings=timings, count_cx=count_cx,
      gpu=self.use_gpu)
  ```

  Reads back: the returned vector (`x_pow2`), `sqls_out['n_data_qubits']`,
  `sqls_out['m_ancilla']`, `timings['cx_count']`, `timings['circuit_depth']`,
  `timings['aer_device']` (`:871-875`). Does NOT read `final_b`, the circuit,
  counts, `timings['t_sim']`, `sqls_out['t_svd']`, or
  `sqls_out['t_circuit_assembly']`. `solve_time` (`:830`, `:840`) wraps the
  whole `quantum_solve` call, so with `-v 2` it includes the diagnostic
  `{u3,cx}` transpile (`quantum.py:118-124`).
- Sign alignment: not in this class; done by the caller (`time_solvers.py:640`)
  with the classical `dq_lu` solved at `time_solvers.py:630` on EVERY step.
  That LU solve is also what feeds fidelity / L2 metrics (HHL does the same
  plus a second LU on the Hermitian system, `:514-521`). So yes: a classical
  LU solve is performed every step and, in statevector mode, the quantum
  result's sign is taken from it. Benchmark-fairness item, finding 5. Also
  note that in `full_svd` mode `final_b = V S^+ U^H b` (`sqls.py:398-407`) is
  itself the full classical solution; the circuit loads a classically
  computed answer, and the "exact magnitude from `||final_b||`" is a classical
  norm of that answer.
- shots = 0 vs > 0: `mode` chosen at `:774`; `shots=(self.nshots or
  int(1e6))` (`:836`) only matters in shots mode (`quantum.py:129-134`).
  Shots mode uses `qiskit_ibm_runtime.SamplerV2` on the Aer backend
  (`quantum.py:202, :211-214`) with `[qc_meas] * repeats` circuits of `shots`
  each, averages the `repeats` reconstructions (`:218-234`), then restores
  per-component signs from `final_b` (`:135-139`, `restore_sign=True`
  default). Statevector mode runs one `save_statevector` job (`:154-161`),
  fixes global phase so the largest-magnitude entry is positive real
  (`:174-176`), casts to real if the imaginary part is noise (`:182-183`),
  rescales to `||final_b||` (`:184`).
- `repeats`: passed through verbatim (`:837`). fvm default 1; recorded in
  `qc_metadata_sqls_*.csv` and the metadata pickle `quantum_circuit` dict.
- `backend_type` restriction: `'ideal'` only (`:790-793`). No fake or real
  backend path; `quantum_solve` hands circuits to Aer untranspiled
  (`quantum.py:154, :207-209`), which is why.
- Metadata CSV `qc_metadata_sqls_nelem{n}_{method}[_shots{s}].csv`
  (`:883-895`) columns: `step, iter, matrix_size_orig, matrix_size_pow2,
  condition_number, nnz_per_row, nqubits, method, k, state_prep, repeats,
  n_data_qubits, m_ancilla, cx_count, circuit_depth, aer_device, solve_time`.
  `nqubits = num_q` = data-register width only (for `truncated_mps` the real
  circuit is `n_data + m_ancilla` qubits).

### 1d. sqls side

`/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`:

- `count_cx_depth(qc)` `:22-33`: `transpile(qc, basis_gates=["u3","cx"],
  optimization_level=1)` falling back to level 0; returns `(cx_count, depth)`
  or `(-1, -1)`.
- `quantum_solve(A_csr, b, num_q, simulator, psi_norm, mode="statevector",
  k=128, method="truncated_mps", state_prep="initialize", mps_chi=None,
  iso_chi=None, mps_chi_max=None, repeats=10, shots=int(1e6), sqls_out=None,
  timings=None, count_cx=False, gpu=False, restore_sign=True)` `:36-43`.
  Confirmed: `repeats` default is 10, `method` default is `truncated_mps`,
  `shots` default 1e6. Returns a numpy vector of length `2**n_data`. Side
  channels: `timings` gets `aer_device` (`:99/:101`), `cx_count`,
  `circuit_depth` (`:121-122` or `-1` at `:126-127`), `t_transpile` (`:156`
  / `:209`, always 0.0), `t_sim` (`:161` / `:235`); `sqls_out` is populated by
  `SQLS`.

`/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py`:

- `SQLS(matrix, b, gpu=None, k=128, method="truncated_mps", out=None,
  state_prep="initialize", mps_chi=None, iso_chi=None, mps_chi_max=None,
  GPU=None) -> QuantumCircuit` `:105-107`. Validation: method/state_prep
  (`:152-158`), N power of 2 (`:166-170`), for truncated methods `k` a power
  of 2 with `2 <= k < N` (`:171-178`), `b != 0` (`:179-181`).
- `full_svd` branch `:355-426`: densifies csr (`:358`), `scipy.linalg.svd`
  (`:383`), tolerance-gated `S^+` (`:392-396`), `alpha_full = S^+ U^H b`,
  `new_b = W alpha`, `final_b = V alpha` (`:398-407`), circuit =
  `Initialize(new_b)` + `UnitaryGate(W^H)` + `UnitaryGate(V)` (`:410-414`).
  `out` keys: `gpu` (`:185`), from `_prepare_state` (`:71-76`): `state_prep`,
  `mps_chi`, `m_ancilla = 0`, `F_mps = 1.0`, `t_mps_decomp`; then `method`,
  `final_b`, `n_data_qubits`, `t_svd`, `t_smallest_k_svd`,
  `t_circuit_assembly` (`:418-425`).
- `truncated_qr` `:190-242` and `truncated_mps` `:248-353` also set
  `n_data_qubits`, `m_ancilla`, `final_b` (`:235-236`, `:330-334`).
- `fidelity(qfunc, true)` `:429-433` exists but fvm uses its own.

Package state: `sqls/__init__.py` exports `SQLS` only; `sqls/runtime/__init__.py`
is a docstring; `pyproject.toml` pins `qiskit==2.1.2`, `qiskit-aer==0.17.1`
(installed with `--no-deps` against qiskit 2.5.2 / aer 0.17.2, per the fvm
`pyproject.toml` comment; import check below confirms it loads).

## 2. Interface check (fvm kwargs vs sqls signatures)

Every keyword fvm passes to `quantum_solve` and every field it reads back:

| fvm passes (quantum_tools.py:833-839) | sqls parameter (quantum.py:36-43) | exists | default on sqls side | note |
|---|---|---|---|---|
| positional `csr_matrix(A_pow2)` | `A_csr` | yes | required | `full_svd` densifies at `sqls.py:358` |
| positional `b_pow2` | `b` | yes | required | length 2**num_q after padding |
| positional `num_q` | `num_q` | yes | required | fallback for `n_data_qubits` |
| positional `self.backend` | `simulator` | yes | required | `AerSimulator(method='statevector')` |
| `psi_norm=b_pow2` | `psi_norm` | yes | required | legacy fallback only; `||final_b||` is used (`:115-116`) |
| `mode=self.mode` | `mode` | yes | `"statevector"` | fvm sends `"statevector"` or `"shots"`; both branches exist (`:129-141`) |
| `k=self.k` | `k` | yes | 128 | same default |
| `method=self.method` | `method` | yes | `"truncated_mps"` | fvm default `full_svd`; override is explicit |
| `state_prep=self.state_prep` | `state_prep` | yes | `"initialize"` | |
| `shots=(self.nshots or int(1e6))` | `shots` | yes | `int(1e6)` | |
| `repeats=self.repeats` | `repeats` | yes | 10 | fvm default 1; passed explicitly, so no silent 10x |
| `sqls_out=sqls_out` | `sqls_out` | yes | `None` | |
| `timings=timings` | `timings` | yes | `None` | |
| `count_cx=count_cx` | `count_cx` | yes | `False` | fvm sets True only for `-v 2` |
| `gpu=self.use_gpu` | `gpu` | yes | `False` | |
| (not passed) | `mps_chi`, `iso_chi`, `mps_chi_max`, `restore_sign` | n/a | `None`, `None`, `None`, `True` | fvm has no flags for these; `restore_sign=True` is what makes shots-mode signs come from `final_b` |

| fvm reads (quantum_tools.py:847, :871-875) | produced by | exists | note |
|---|---|---|---|
| return value `x_pow2` | `quantum_solve` return (`quantum.py:130, :140`) | yes | ndarray, length 2**n_data, real in both August modes |
| `sqls_out['n_data_qubits']` | `sqls.py:421` (full_svd), `:236`, `:331` | yes | |
| `sqls_out['m_ancilla']` | `sqls.py:74` (initialize), `:95` (mps), `:334` (truncated_mps) | yes | |
| `timings['cx_count']`, `timings['circuit_depth']` | `quantum.py:121-122` or `-1` (`:126-127`) | yes | -1 unless `-v 2` |
| `timings['aer_device']` | `quantum.py:99/:101` | yes | |

Result: no signature or field mismatch. The only semantic divergence is the
`repeats` default (1 in fvm, 10 in sqls), which fvm neutralizes by always
passing it. Fields available but NOT harvested by fvm: `sqls_out['final_b']`
(would allow a reference-free sign fix), `sqls_out['t_svd']`,
`sqls_out['t_circuit_assembly']`, `timings['t_sim']`, `sqls_out['F_mps']`.

## 3. Import / --help check (verbatim output)

Run 2026-10-15 (UTC) from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`.

```
$ .venv/bin/python -c "import sqls, sqls.runtime.quantum as q, inspect; print(sqls.__file__); print('quantum_solve', inspect.signature(q.quantum_solve)); import sqls.sqls as s; print('SQLS', inspect.signature(s.SQLS)); print('count_cx_depth', inspect.signature(q.count_cx_depth))"
/Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py
quantum_solve (A_csr, b, num_q, simulator, psi_norm, mode='statevector', k=128, method='truncated_mps', state_prep='initialize', mps_chi=None, iso_chi=None, mps_chi_max=None, repeats=10, shots=1000000, sqls_out=None, timings=None, count_cx=False, gpu=False, restore_sign=True)
SQLS (matrix, b, gpu=None, k=128, method='truncated_mps', out=None, state_prep='initialize', mps_chi=None, iso_chi=None, mps_chi_max=None, GPU=None)
count_cx_depth (qc)

$ .venv/bin/python -c "import quantum_tools, inspect; print(quantum_tools.QuantumSQLS); print(inspect.signature(quantum_tools.QuantumSQLS.__init__)); print(inspect.signature(quantum_tools.QuantumSQLS.solve_one_step))"
<class 'quantum_tools.QuantumSQLS'>
(self, backend_type='ideal', backend_method='statevector', nshots=0, verbosity=2, use_gpu=False, output_dir='.', steady_mode=False, method='full_svd', k=128, state_prep='initialize', repeats=1, *args, **kwargs)
(self, A_o, b_o, nelem=1, iter=0, true_sol_norm=1.0, step=0)

$ .venv/bin/python -c "import qiskit, qiskit_aer, numpy, scipy, sys; ..."
python 3.12.10
qiskit 2.5.2
qiskit_aer 0.17.2
numpy 2.5.2
scipy 1.18.0
qiskit_ibm_runtime 0.49.0
torch: not installed
```

Both imports succeed with no traceback and no warnings. `quantum_tools`
importing also pulls `linear_solvers.HHL` (Q8020-CFD fork) and
`qiskit_ibm_runtime.SamplerV2` at module top (`quantum_tools.py:7-11`), so
the SQLS path still requires the full HHL stack to be importable.

`--help` (`.venv/bin/python nozzle_1d_solver.py --help`), usage block and
the SQLS-relevant options; full text was identical to the argparse table in
section 1a:

```
usage: FVM Solver - Euler 1D Solver [-h] [-nelem NELEM] [-x X_VEC [X_VEC ...]]
                                    [-time_scheme {BDF1,BDF2,BDF2OPT,RK1,RK2,RK3}]
                                    [-linsolver {LU,GMRES,HHL,SQLS}]
                                    [-cfl CFL] [-iters MAX_ITERS]
                                    [-initers MAX_INNER_ITERS]
                                    [-restol RES_TOL] [-tol CONV_TOL]
                                    [-localdt] [-use_dim_form]
                                    [-backend BACKEND [BACKEND ...]]
                                    [-shots NSHOTS]
                                    [-hhl_scale {true_sol,leastsq}]
                                    [-loadcirc] [-qc_gpu]
                                    [-sqls_method {full_svd,truncated_qr,truncated_mps}]
                                    [-sqls_k SQLS_K]
                                    [-sqls_state_prep {initialize,mps}]
                                    [-sqls_repeats SQLS_REPEATS] [-noshow]
                                    [-outdir OUTPUT_DIR] [-v {0,1,2}]
                                    [-savedata] [-checkpoint] [-resume]
                                    [-original_max_iters ORIGINAL_MAX_ITERS]
...
  -linsolver {LU,GMRES,HHL,SQLS}
                        Linear system solver for implicit algorithms [LU]
  -shots NSHOTS         number of shots for shot based studies, default no
                        shots [0], only significant for non-ideal backends
  -hhl_scale {true_sol,leastsq}
                        choose type of scaling for the hhl sol [true_scale]
  -sqls_method {full_svd,truncated_qr,truncated_mps}
                        SQLS assembly method; full_svd is exact (default), the
                        truncated methods impose a rank-k pseudo-inverse
                        ceiling
  -sqls_k SQLS_K        SQLS truncation rank (power of 2, 2<=k<N); ignored by
                        full_svd [128]
  -sqls_state_prep {initialize,mps}
                        SQLS state-prep loader for full_svd/truncated_qr;
                        initialize is exact (default)
  -sqls_repeats SQLS_REPEATS
                        SQLS shot-mode: number of independent nshots-
                        reconstructions to average [1]. Default 1 matches the
                        HHL single-run shot budget; >1 multiplies the
                        effective shots by this factor
```

The epilog usage examples (`nozzle_1d_solver.py:23-36`) show only HHL
invocations; there is no SQLS example.

## 4. Metadata and harvester compatibility

Harvester: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
(640 lines, imports `q8020_cfd_metautil.meta_fragment`). Companion
`backend_meta_harvester.py` (69 lines) only acts when the sweep params carry
`-backend fake ...`; for an ideal SQLS run it prints "No -backend param,
skipping" and exits (`:36-39`), so it is a no-op for SQLS.

### 4a. File-name level: the harvester is NOT blind to SQLS

Its globs are prefix-only and all match the SQLS names:

| harvester glob (line) | HHL file (2026-08-17-qiskit25-local/trial_0) | SQLS file (2026-08-17-sqls-local-v2/trial_0) | matches |
|---|---|---|---|
| `metadata_*.pkl` (`:118`) | `metadata_nelem5_HHL_statevector_nshots150000.pkl` | `metadata_nelem5_SQLS_statevector_nshots150000.pkl` | yes |
| `hhl_metrics_*.csv` (`:143`) | `hhl_metrics_nelem5_statevector_shots150000.csv` | `hhl_metrics_nelem5_statevector_shots150000.csv` (same name) | yes |
| `qc_metadata_*.csv` (`:151`) | `qc_metadata_nelem5_statevector_shots150000.csv` | `qc_metadata_sqls_nelem5_full_svd_shots150000.csv` | yes |
| `final_results_*.csv` (`:159`) | `final_results_nelem5_HHL_statevector_nshots150000.csv` | `final_results_nelem5_SQLS_statevector_nshots150000.csv` | yes |
| `residual_*.csv` (`:165`) | `residual_nelem5_HHL_...csv` | `residual_nelem5_SQLS_...csv` | yes |
| `results_nelem*_iter*_*.csv` (`:259`) | `results_nelem5_iter{0..14}_statevector_shots150000.csv` (15) | `results_nelem5_iter{0..6}_statevector_shots150000.csv` (7) | yes |
| `dq_nelem*_iter*_*.csv` (`:264`) | `dq_nelem5_iter{0..14}_...csv` | `dq_nelem5_iter{0..6}_...csv` | yes |

### 4b. Column level: the harvester IS blind to SQLS content

`_build_artifacts` (`:350-421`) reads only HHL column names:
`circ_generate_time`, `circ_transpile_time`, `circ_run_time`,
`circ_depth_orig`, `circ_qubits_orig`, `circ_gates_orig`,
`circ_depth_transpile`, `circ_gates_transpile`, `circ_qubits_transpile`,
`matrix_size_herm` (`:364-366`, `:381-389`, `:401`), each with a default of
0. None exist in `qc_metadata_sqls_*.csv`, so every `transpile_passes[]`
entry and `circuit_timing_total_s` come out as zeros, and
`matrix_size_hermitian` is written as 0 (should be null for SQLS). The SQLS
columns `method, k, state_prep, repeats, n_data_qubits, m_ancilla, cx_count,
circuit_depth, aer_device, solve_time` are dropped entirely.
`_parse_stdout_lu_solutions` (`:185-226`) requires the literal header `LU
sol ... HHL sol` (`:206`); SQLS prints `LU sol \t SQLS sol L1_diff(%)`
(`time_solvers.py:667`) and has 3 columns instead of 4, so
`lu_reference_vector` / `hhl_solution_vector` are never extracted for SQLS
(moot for the August dirs, which have no stdout capture; relevant for
sweeper runs that write `q8020_stdout_*.txt`).

### 4c. Harvester run on a /tmp copy (read-only with respect to the results tree)

Copied `2026-08-17-sqls-local-v2/trial_0` (34 files) to
`/tmp/sqls-harvest-check/trial_0`, ran `generate_metadata(src,
write_dir=/tmp/sqls-harvest-check/fragments2)` with
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`
(the only local venv with `q8020_cfd_metautil`; the fvm venv lacks it), then
`q8020_cfd_metautil.harvest.harvest_metadata(..., read_only=True)`.

Produced, no exceptions, no warnings:
`q8020_{analysis,artifacts,backend,case,code,results}_0.json`. Roll-up
counts `{'results': 1, 'backend': 1, 'artifacts': 1, 'code': 1, 'analysis':
1, 'case': 1, 'exec_stats': 0, 'experiment': 0}`, warnings `[]`. (With an
explicit `experiment_id='sqlscheck'` the files were named
`q8020_<sec>_sqlscheck_0.json` and the roll-up found 0 of them; the sweeper
supplies its own id format, so this is an observation about my synthetic id,
not a defect.) The same roll-up on the real HHL trial dir found 1 of each as
well.

Fragment contents for SQLS vs the committed HHL fragments:

| fragment / field | HHL value (committed `q8020_*_0.json`) | SQLS value (my /tmp run) | can SQLS populate from its outputs |
|---|---|---|---|
| `case.*` (nelem, time_scheme, cfl, max_iters, max_inner_iters, conv_tol, res_tol, localdt, nondim, area_equation, reference_values) | populated | populated, identical | yes (from pickle) |
| `code.algorithm` | `"HHL"` | `"SQLS"` | yes |
| `backend.name/type/method/noise` | `ideal_statevector / simulator / statevector / false` | same | yes |
| `backend.num_qubits` | 5 (= log2 of the 32-row Hermitian system, NOT the 13-14 qubit circuit) | 4 (= data register; equals circuit width only for full_svd/initialize) | yes, but semantics differ between the two solvers (finding 11) |
| `backend.nshots` | 150000 | 150000 | yes; does not reflect `repeats` |
| `artifacts.transpile_passes[i].wall_time_{generate,transpile,execute}_s` | 20.41 s / 15.85 s / 18.50 s (step 0) | 0.0 / 0.0 / 0.0 | partially: `solve_time` (total), and `t_svd`, `t_circuit_assembly`, `t_sim` exist in sqls but fvm does not log them |
| `artifacts.transpile_passes[i].before.{depth,num_qubits,gate_count}` | 5 / 14 / 19 | 0 / 0 / 0 | no (fvm never records the raw circuit; `quantum_solve` does not return it) |
| `artifacts.transpile_passes[i].after.{depth,num_qubits,gate_count}` | 596688 / 14 / 641145 (Aer basis) | 0 / 0 / 0 | partially: `circuit_depth` 398 and `cx_count` 201 in `{u3,cx}` basis, `n_data_qubits + m_ancilla` = 4; no total gate count |
| `artifacts.circuit_timing_total_s` | generate 295.9 s, transpile 214.5 s, execute 265.1 s, total 775.5 s | all 0.0 | partially (sum of `solve_time` = 0.575 s) |
| `artifacts.linear_system` | `{15, 16, 32, cond [58.17, 95.98]}` | `{15, 16, 0, cond [59.92, 95.98]}` | `matrix_size_hermitian` not applicable; should be null |
| `artifacts.file_inventory` | csv 50, pkl 16, png 1 | csv 25, pkl 8, png 1, qpy 0 | yes |
| `results.final_solution` (5 rows) | populated | populated | yes |
| `results.per_iteration[].solution` | 15 entries | 7 entries | yes |
| `results.per_iteration[].dq` keys | `dq_lu, dq_hhl` | `dq_lu, dq_sqls` | yes (key name differs; downstream consumers keyed on `dq_hhl` will miss it) |
| `results.lu_reference_vector_final`, `per_iteration[].hhl_solution_vector` | absent here (no stdout in dir) | absent | no, header mismatch in `_parse_stdout_lu_solutions` |
| `results.residual_history` | 15 rows | 7 rows | yes |
| `analysis.iterations_completed` | 15 | 7 | yes |
| `analysis.converged` | false (correct: hit max_iters) | false (WRONG: solver declared convergence at iteration 6) | harvester compares absolute `residual_total` 1.26e-9 against `conv_tol` 1e-10, but `conv_tol` is a RATIO tolerance in the solver (`nozzle_1d_solver.py:292, :313`); the solver converged via the `dqnorm <= 1e-10` branch |
| `analysis.fidelity` (last row) | 0.9933 | 0.4510 | populated but misleading: last-step tail collapse (section 5) |
| `analysis.l2_error_normalized` (last row) | 0.0817 | 0.8104 | same caveat |
| `analysis.residual` (last `linsys_residual`) | 3.725e-3 | 1.228e-9 | yes |
| `analysis.residual_reduction` | 0.000549 | 0.0 (true value 1.0185e-10, rounded to 6 d.p. at `:493`) | lossy for a converged run |
| `analysis.hhl_metrics[]` | 15 rows | 7 rows | yes |
| hand-authored `q8020_{params,experiment,exec_stats,env_before,env_after,code_provenance}_local.json` | present | absent from the SQLS trial dir | not produced by this harvester for either solver; the sweeper writes them |

Why the August SQLS trial has no `q8020_*.json`: it was a manual run and the
harvester was simply never invoked on it (the HHL sibling's fragments were
produced by hand per its README). Running the harvester now would produce the
six fragments above with the column-level gaps listed.

## 5. August trial data cross-check

Sources: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`
(SQLS; metadata pickle timestamp `2026-08-17T18:28:07` local, laptop at
UTC-4, i.e. `2026-08-17T22:28:07Z`) and
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/`
(HHL; `2026-08-17T17:09:25` local = `2026-08-17T21:09:25Z`, matches
`q8020_exec_stats_local.json` end_time). Both: nelem = 5 (N = 15 -> 16
padded), BDF1, CFL 1e10, localdt, nondim, `-initers 1`, `-iters 15`,
`-shots 150000`, ideal statevector simulator, same host `MH-DT9TLJQR2V`.
Both runs share the iteration-0 residual 12.375368413827264 and condition
number 95.9778901432456, so the starting system is identical.

### 5a. SQLS per iteration (full_svd, repeats = 1, 150000 shots)

| step | CFD residual_total | fidelity | l2_error_normalized | linsys residual ‖A dq - b‖ | solve_time (s) | cond(A) | data qubits | CX ({u3,cx}) | depth ({u3,cx}) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.2375e+1 | 0.999981 | 4.319e-3 | 2.693e-1 | 0.1029 | 95.98 | 4 | 200 | 398 |
| 1 | 7.6116e-1 | 0.999965 | 5.949e-3 | 3.179e-2 | 0.0789 | 59.92 | 4 | 201 | 397 |
| 2 | 7.0965e-2 | 0.999966 | 5.790e-3 | 2.751e-3 | 0.0753 | 66.31 | 4 | 201 | 398 |
| 3 | 2.6904e-3 | 0.999979 | 4.542e-3 | 4.573e-5 | 0.0774 | 67.37 | 4 | 200 | 398 |
| 4 | 4.5451e-5 | 0.999968 | 5.655e-3 | 2.608e-7 | 0.0780 | 67.39 | 4 | 201 | 398 |
| 5 | 2.6079e-7 | 0.999954 | 6.778e-3 | 1.260e-9 | 0.0778 | 67.39 | 4 | 201 | 398 |
| 6 | 1.2604e-9 | 0.451025 | 8.104e-1 | 1.228e-9 | 0.0848 | 67.39 | 4 | 201 | 398 |

Summary: 7 linear solves; mean solve_time 0.0822 s (min 0.0753 s, max
0.1029 s, sum 0.575 s); solver `elapsed_time` 0.619 s; `final_iters` = 6;
final residual ratio 1.0185e-10 (just above `conv_tol` 1e-10; the run exited
on the `dqnorm <= 1e-10` criterion, `nozzle_1d_solver.py:313`). Pre-tail
fidelity 0.999954 to 0.999981.

### 5b. HHL per iteration (ideal statevector, 150000 shots)

| step | CFD residual_total | fidelity | l2_error_normalized | linsys residual | gen + transpile + run (s) | cond(A) | circuit qubits | gates (Aer basis) | depth (Aer basis) |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.2375e+1 | 0.99902 | 3.126e-2 | 2.122e+0 | 54.76 | 95.98 | 14 | 641145 | 596688 |
| 1 | 2.4929e+0 | 0.99341 | 8.126e-2 | 6.074e-1 | 24.80 | 58.17 | 13 | 319447 | 297178 |
| 2 | 6.3060e-1 | 0.99022 | 9.901e-2 | 3.813e-1 | 54.58 | 64.38 | 14 | 641325 | 596959 |
| 3 | 3.8198e-1 | 0.99267 | 8.571e-2 | 1.583e-1 | 53.83 | 65.36 | 14 | 641662 | 597198 |
| 4 | 1.5874e-1 | 0.98803 | 1.096e-1 | 7.378e-2 | 53.18 | 66.57 | 14 | 641662 | 597198 |
| 5 | 7.3884e-2 | 0.99535 | 6.824e-2 | 6.511e-2 | 53.24 | 67.02 | 14 | 642435 | 597971 |
| 6 | 6.5113e-2 | 0.99345 | 8.098e-2 | 4.568e-2 | 53.12 | 67.07 | 14 | 640898 | 596441 |
| 7 | 4.5685e-2 | 0.99728 | 5.218e-2 | 3.571e-2 | 53.18 | 67.15 | 14 | 640658 | 595947 |
| 8 | 3.5709e-2 | 0.99122 | 9.382e-2 | 3.108e-2 | 53.90 | 67.20 | 14 | 640824 | 596457 |
| 9 | 3.1084e-2 | 0.99109 | 9.448e-2 | 2.005e-2 | 53.79 | 67.23 | 14 | 642819 | 598473 |
| 10 | 2.0053e-2 | 0.99322 | 8.244e-2 | 1.235e-2 | 53.29 | 67.28 | 14 | 641670 | 597206 |
| 11 | 1.2348e-2 | 0.99524 | 6.903e-2 | 1.162e-2 | 53.09 | 67.32 | 14 | 641098 | 596680 |
| 12 | 1.1624e-2 | 0.98829 | 1.084e-1 | 1.077e-2 | 53.53 | 67.33 | 14 | 643423 | 598712 |
| 13 | 1.0771e-2 | 0.99088 | 9.559e-2 | 6.795e-3 | 53.59 | 67.33 | 14 | 642417 | 597963 |
| 14 | 6.7953e-3 | 0.99334 | 8.167e-2 | 3.725e-3 | 53.61 | 67.35 | 14 | 641370 | 596951 |

Summary: 15 linear solves; mean per-solve 51.70 s (generate 19.73 s +
transpile 14.30 s + run 17.67 s; min 24.80 s at step 1 where the circuit was
13 qubits, max 54.76 s), sum 775.5 s; solver `elapsed_time` 859.34 s
(includes the dense FD Jacobian builds and I/O); `final_iters` = 14 because
`max_iters` = 15 was exhausted, final residual ratio 5.49e-4, NOT converged
to `conv_tol` 1e-10. Fidelity 0.9880 to 0.9990.

### 5c. Comparison against `sqls-vs-hhl-2026-08-17/README.md`

| README claim | recomputed from the CSVs | status |
|---|---|---|
| circuit qubits 4 vs 14 | SQLS `nqubits` 4 (n_data 4, m_ancilla 0); HHL `circ_qubits_transpile` 14 (13 at step 1) | confirmed |
| ~201 CX / depth ~398 ({u3,cx}) vs 641,145 gates / 596,688 depth (Aer basis) | SQLS cx 200-201, depth 397-398; HHL step-0 values 641145 / 596688 (range 319447-643423 / 297178-598712) | confirmed; bases differ as the README says (finding 3) |
| mean time / solve 0.082 s vs 51.70 s | 0.0822 s vs 51.698 s (sum of gen+transpile+run) | confirmed |
| total solver elapsed 0.62 s vs 859.34 s | 0.619 s vs 859.34 s | confirmed |
| "Newton iters to converge 6 vs 14" | SQLS converged at iteration index 6 (7 solves); HHL did NOT converge: it stopped at index 14 because `-iters 15` was exhausted (residual ratio 5.5e-4 vs tol 1e-10) | discrepancy in wording: 14 is a cap, not a convergence count |
| "final residual (‖Ax-b‖) 1.26e-9 vs 6.80e-3" | the quoted numbers are the CFD `residual_total` (1.2604e-9, 6.7953e-3); the linear-system residuals at the last step are 1.228e-9 and 3.725e-3 | numbers right, row label wrong (CFD residual, not ‖Ax-b‖) |
| pre-tail fidelity 0.99995-0.99998 vs 0.988-0.999 | 0.999954-0.999981 vs 0.9880-0.9990 | confirmed |
| fidelity tail collapse 0.45-0.69 at the last step | 0.4510 in this trial | confirmed (within the quoted run-to-run range) |

### 5d. Root cause of the tail collapse (new, verified from the saved systems)

The README attributes the last-step collapse to "a shots-sampling artifact on
a near-zero solution update". The saved `system_Ab_nelem5_iter{0..6}.pkl`
files pin it to a specific line: `convert_to_pow2` pads `b` with the constant
`eps = 1e-8` and `A` with a unit diagonal (`math_tools.py:62-66`), so the
padded 16th unknown is exactly 1e-8 regardless of how small the true update
is. Recomputed with `numpy.linalg.solve` on the padded systems:

| step | ‖b‖ | ‖dq_true‖ (15 entries) | padded x[15] | probability mass on the 15 true entries | expected shots of 150000 landing on them |
|---|---|---|---|---|---|
| 0 | 1.238e+1 | 2.705e+0 | 1.0e-8 | 1.000 | 150000 |
| 4 | 4.545e-5 | 1.899e-6 | 1.0e-8 | 1.000 | 149996 |
| 5 | 2.608e-7 | 1.074e-8 | 1.0e-8 | 0.536 | 80336 |
| 6 | 1.260e-9 | 7.354e-11 | 1.0e-8 | 5.41e-5 | 8.1 |

At step 6 only about 8 of the 150000 shots carry information about the
solution; the saved `dq_nelem5_iter6_*.csv` shows exactly that signature: 4
nonzero entries out of 15, taking only the values 2.582e-11 and 5.164e-11
(a 1:2 ratio, i.e. sqrt of counts 1 and 4). Statevector mode is immune (the
slice is exact), and HHL at 1e-4-scale updates never reaches the regime, but
any shots-mode SQLS sweep that converges will hit it. Fix is one argument:
`convert_to_pow2(A_o, b_o, eps=0.0)` for the SQLS path (A's unit diagonal
keeps the padded system nonsingular and `b` stays nonzero overall, which is
all `SQLS` requires at `sqls.py:179-181`). See finding 1.

## 6. Findings

Severity: blocker = wrong or unusable result for the paper protocol;
should-fix = degrades or misrepresents results; note = clarity, robustness,
or framing.

1. **should-fix** -- Fixed padding constant corrupts shots-mode results at
   convergence. `quantum_tools.py:823` calls `convert_to_pow2(A_o, b_o)` with
   the default `eps=1e-8` (`math_tools.py:28`, `:62-66`); once
   `‖dq‖ < ~1e-8` the padded entry takes essentially all measurement
   probability and fidelity collapses (0.451 at step 6, section 5d). Fix:
   pass `eps=0.0` for the SQLS path (or scale eps to a small fraction of
   `‖b‖`) and re-run the shots case to confirm the tail is gone.

2. **should-fix** -- Harvester zeroes every SQLS circuit/timing field.
   `fvm_euler_1d_solver_harvester.py:361-391, :401` reads only HHL column
   names, so `artifacts.transpile_passes[]`, `circuit_timing_total_s` and
   `matrix_size_hermitian` are 0 for SQLS and `method, k, state_prep,
   repeats, n_data_qubits, m_ancilla, cx_count, circuit_depth, aer_device,
   solve_time` are dropped; `:206` only recognizes the `HHL sol` stdout
   header. Fix: branch on `code.algorithm`, map `solve_time` ->
   `wall_time_execute_s`, `cx_count`/`circuit_depth` -> `after`,
   `n_data_qubits + m_ancilla` -> `num_qubits`, emit null (not 0) for
   `matrix_size_hermitian`, add an `sqls` sub-dict with the dropped columns,
   and accept the `SQLS sol` header with its 3-column layout.

3. **should-fix** -- Circuit-metric basis mismatch. SQLS cx/depth come from
   `count_cx_depth` in `{u3, cx}` (`sqls/runtime/quantum.py:22-33`), HHL
   depth/gates from `transpile(circ, AerSimulator)` in Aer's own basis
   (`quantum_tools.py:160`, logged at `:657-664`) and count ALL gates, not CX.
   Fix: add one shared helper in fvm that transpiles any circuit to a fixed
   basis (`{u3, cx}` or IBM's `{rz, sx, x, cx}`) and records `cx_count`,
   `total_gates`, `depth`, `num_qubits` for both solvers; `QuantumHHL` already
   has the circuit in hand at `:578`, and `quantum_solve` would need to
   return or expose `qc` (or fvm calls `SQLS(...)` + `count_cx_depth` itself).

4. **should-fix** -- cx/depth only logged at `-v 2`. `quantum_tools.py:829`
   ties `count_cx` to verbosity, so a sweep run at the default `-v 1` records
   `-1` for both and `solve_time` differs between verbosity levels (the
   transpile is inside the timed region, `:830-840`). Fix: add a
   `-sqls_count_cx` flag (default on for N <= 2**8) independent of verbosity,
   and record `timings['t_sim']`, `sqls_out['t_svd']`,
   `sqls_out['t_circuit_assembly']` as separate columns so `solve_time` can be
   decomposed like HHL's generate/transpile/run.

5. **note** (benchmark fairness) -- Classical LU every step for the sign.
   `time_solvers.py:630` solves `A dq = b` with LU on every Newton step and
   `:640-641` uses it to fix the free global sign of the statevector result
   (HHL does the same plus a second LU on the doubled system, `:514-521`, and
   in shots mode takes per-component signs from `dq_herm`, `:542-544`). The
   LU is also needed for the fidelity/L2 metrics, so it is not extra cost,
   but the solver output depends on it. Fix: choose the sign by the
   reference-free test `‖A(+x) - b‖ <= ‖A(-x) - b‖` (two matvecs) and keep
   LU strictly for metrics; also state in the paper that `full_svd` computes
   `final_b = V S^+ U^H b` classically (`sqls.py:398-407`), so the circuit
   loads a classically known answer and the quantum step is state
   preparation plus two unitaries.

6. **note** -- `repeats` semantics. fvm default 1 (`nozzle_1d_solver.py:119-123`)
   vs sqls default 10 (`quantum.py:41`); fvm always passes it
   (`quantum_tools.py:837`) so there is no silent 10x, but the effective shot
   budget `nshots * repeats` is not reflected in file names, the pickle
   `nshots`, or `backend.nshots` (only the `repeats` column of
   `qc_metadata_sqls_*.csv`). Fix: log `total_shots = nshots * repeats` in
   the CSV and pickle, and have the harvester carry it into `backend`.

7. **note** -- Ideal-only backend, with a misleading failure. `QuantumSQLS.get_backend`
   raises for any `backend_type != 'ideal'` (`quantum_tools.py:790-793`), but
   `LinearSystemSolver.__init__` swallows it (`time_solvers.py:292-293`) and
   the run dies later with "Install the optional sqls back-end"
   (`:612-615`). `backend_method` is also ignored (`:795`) while still used in
   file names. Fix: validate `-backend ideal` for SQLS in
   `nozzle_1d_solver.py` before constructing the solver, and let config
   errors propagate instead of catching `Exception`; a fake/real path would
   need `quantum_solve` to accept a pass manager (sqls's `potential_flow.py`
   `hardware` subcommand shows the pattern).

8. **note** -- `-sqls_k` default 128 is invalid for the truncated methods at
   paper sizes. `sqls.py:171-178` requires `2 <= k < N` for `truncated_qr`
   / `truncated_mps`; with nelem = 5 (N = 16) the default raises
   `ValueError` at the first solve. Fix: default `k = None` and resolve to
   `N // 2` (or validate and clamp) in `QuantumSQLS.solve_one_step`.

9. **note** -- `analysis.converged` wrong for SQLS and `residual_reduction`
   lost. Harvester `:499-501` compares the absolute CFD residual to
   `conv_tol`, which the solver treats as a ratio (`nozzle_1d_solver.py:292,
   :313`), so the converged SQLS run reports `converged: false`; `:493` rounds
   `residual_reduction` to 6 decimals, turning 1.0185e-10 into 0.0. Fix:
   compare `last/first <= conv_tol` or `dqnorm` criterion, and store the
   ratio unrounded.

10. **note** -- Headline `analysis.fidelity` is the last row. Harvester
    `:479-483` takes the final `hhl_metrics` row, which for SQLS is the
    tail-collapsed 0.451. Fix: after finding 1 this largely resolves itself;
    additionally report min/median/pre-final fidelity, or skip rows whose
    `‖dq_lu‖` is below the convergence threshold.

11. **note** -- `nqubits` means different things. SQLS logs the data-register
    width (4; `quantum_tools.py:866`), HHL logs `log2(N_herm)` = 5
    (`:654`) while its circuit is 13-14 qubits; the harvester puts either into
    `backend.num_qubits` (`:329-333`). Fix: log `circ_qubits =
    n_data_qubits + m_ancilla` for SQLS and have the harvester prefer
    `circ_qubits_transpile` / `circ_qubits` over `nqubits`.

12. **note** -- HHL baseline uses least-squares magnitude scaling by accident.
    `-hhl_scale` default `'true_scale'` is not among its choices
    (`nozzle_1d_solver.py:96-98`); argparse does not validate defaults, so
    `hhl_scale_type != 'true_sol'` and `time_solvers.py:534-539` applies the
    least-squares alpha instead of `‖dq_herm‖`. Not an SQLS wiring issue but
    it is the baseline SQLS is compared against. Fix: set `default='true_sol'`
    (or `'leastsq'` deliberately) and say which in the paper.

13. **note** -- README wording. "Newton iters to converge 6 vs 14" should
    read "6 (converged) vs 15 (cap reached, not converged)"; the "final
    residual (‖Ax-b‖)" row reports the CFD `residual_total`, the linear-system
    residuals are 1.228e-9 and 3.725e-3. Fix: relabel in
    `sqls-vs-hhl-2026-08-17/README.md` and in any paper table derived from it.

14. **note** -- Dependency reproducibility. `sqls` is installed editable from
    a local path (`direct_url.json`), is absent from `uv.lock`, and the
    `[sqls]` extra points at `https://code.ornl.gov/olcf-qcfd/sqls.git`
    (HTTP 504 on 2026-10-14 per `WORKPLAN.md`). A fresh `uv sync` on Frontier
    will not install it. Fix: belongs to items 2 and 5; vendor a pinned
    tarball or mirror the repo under `Q8020-CFD` and reference the mirror.

15. **note** -- Minor CLI hygiene. `-shots` help says "only significant for
    non-ideal backends" (`:92-94`) though ideal+shots is the protocol; `-cfl`
    and `-tol` help defaults (`[1000.]`, `[1e-12]`) disagree with the code
    (1e10, 1e-10); the epilog has no SQLS example (`:23-36`); `load_qcirc`
    is set for SQLS (`:207`) but never consumed. Fix: one pass over the help
    strings and add `-linsolver SQLS -sqls_method full_svd -sqls_repeats 1`
    to the examples.

Nothing rose to blocker: a paper sweep with `-linsolver SQLS -sqls_method
full_svd -sqls_repeats 1 -v 2` would run and produce the same file set as the
August trial. Findings 1 to 4 should land before the shot sweep so the
fidelity tail and the metadata are right the first time.

## Sources

Code (fvm_euler_1d_solver, main @ ef7f0a8b):

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py` (410 lines)
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/time_solvers.py` (691 lines)
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py` (895 lines)
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/math_tools.py` (`convert_to_pow2` :28-90, `get_matrix_properties` :243-271)
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/helper_tools.py` (`write_csv` :6)
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/pyproject.toml`, `uv.lock`
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/sqls-0.1.0.dist-info/direct_url.json`
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/__editable__.sqls-0.1.0.pth`

Code (sqls, HEAD 9a4346a7):

- `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py` (237 lines)
- `/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py` (433 lines)
- `/Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py`, `src/sqls/runtime/__init__.py`, `src/sqls/gpu.py`
- `/Users/agallojr/proj/src/q8020/sqls/pyproject.toml`, `README.md`, `examples/potential_flow.py`

Harvesters and sweep config:

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/harvest_lugo_all.sh`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/harvest.py` (roll-up), venv `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv`

Data:

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/` (34 files: `residual_*`, `hhl_metrics_*`, `qc_metadata_sqls_*`, `final_results_*`, `dq_*`, `results_*`, `system_Ab_*.pkl`, `metadata_*.pkl`, one PNG)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/` (79 files incl. `q8020_{case,code,backend,artifacts,results,analysis}_0.json` and the hand-authored `*_local.json`) and its `README.md`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md` and `compare_sqls_hhl.py` (`:121-123` defines the per-solve time columns)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`

Scratch (safe to delete): `/tmp/sqls-harvest-check/` (copy of the SQLS trial
plus `fragments/` and `fragments2/` produced by the harvester).
