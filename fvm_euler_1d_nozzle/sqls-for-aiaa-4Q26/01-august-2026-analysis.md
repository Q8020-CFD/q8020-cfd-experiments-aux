# What was done in August 2026 (SQLS into fvm_euler_1d_solver)

Written 2026-10-14 (UTC) for work item 1 of `WORKPLAN.md` in this folder.
Read-only analysis of the local git history, result trees, analysis folders,
mesh library records, and GitHub issues. Nothing was run or modified.

Summary. All of the August SQLS work happened on one day, 2026-08-17, on the
laptop `MH-DT9TLJQR2V`, in one interactive session (co-author tag
"Claude Opus 4.8"). The day had three phases: (1) deliver and reconcile the
HHL line onto `main` and repin it from qiskit 1.2.4 to 2.3.1 (commits
`60d973c5`, `fbe6ef10`, `3c20cff8`), validated by one 150000-shot HHL run;
(2) bump to qiskit 2.5.2 (`a885ef47`), validated by a second identical HHL
run; (3) wire ORNL's `sqls` in as an opt-in `-linsolver SQLS` (`ef7f0a8b`),
validated by one `full_svd` run at nelem 5. The SQLS result is one laptop trial
with no sweep, no Frontier run, no metadata fragments, no README, and no
truncated-method test. Everything that follows is evidence for those
statements.

## Timeline (UTC)

Local timestamps in the sources are `-04:00` (laptop) and are converted here.
Commit times are author dates from `git log --date=iso-strict`.

| UTC | Event | Source |
|---|---|---|
| 2026-06-30T14:40:52Z | `sqls` upstream HEAD `9a4346a7` "Merge branch 'to_be_released' into 'main'" (Chao Lu) | `git log` in `/Users/agallojr/proj/src/q8020/sqls` |
| 2026-07-26T14:03:43Z | `sqls` cloned locally (directory mtime); this checkout is what the August integration coded against; still at `9a4346a7` == `origin/main`, clean | `stat` of `/Users/agallojr/proj/src/q8020/sqls` |
| 2026-08-10T18:18:08Z | qtsuite #8 "Code: SQLS" created, with sub-issues #9 to #12 at 18:18:09Z to 18:18:13Z | `gh issue view 8`, `sub_issues` API |
| 2026-08-17T18:32:12Z | fvm `60d973c5` "Deliver feature/qiskit-hhl to main" | fvm git log |
| 2026-08-17T20:11:00Z to 20:25:12Z | HHL run, qiskit 2.3.1, 817.74 s; tree = `60d973c5` + uncommitted port | `2026-08-17-qiskit23-local/trial_0/q8020_exec_stats_local.json`, `q8020_code_provenance_local.json` |
| 2026-08-17T20:44:14Z | fvm `fbe6ef10` "Reconcile solver code with archive/qiskit-hhl-2" | fvm git log |
| 2026-08-17T20:44:30Z | fvm `3c20cff8` "Repin to qiskit 2.3 + Q8020-CFD fork; go uv-native" | fvm git log |
| 2026-08-17T20:45Z | session notes (`PORT-PLAN.md`, `STEPS-q8020-main-to-2.3.md`, `two-way-nov-vs-apr.md`, `gather.py`, `summary.json`) moved into the qiskit_2.x analysis folder | file mtimes |
| 2026-08-17T20:56:07Z to 21:09:25Z | HHL run, qiskit 2.5.2, 859.34 s; tree = `3c20cff8` + uncommitted bump | `2026-08-17-qiskit25-local/trial_0/q8020_exec_stats_local.json` |
| 2026-08-17T21:13Z | four-way qiskit README written | mtime of `aux/qiskit_2.x/fvm-euler-1d-1x-vs-2x-vs-local-2026-08/README.md` |
| 2026-08-17T21:16:25Z | fvm `a885ef47` "Bump quantum stack to latest qiskit 2.5 line" | fvm git log |
| 2026-08-17T21:47:20Z | qtsuite #53 "Basic FVM Euler integration & test" created | `gh issue view 53` |
| about 2026-08-17T22:21Z | `2026-08-17-sqls-local-v2/trial_0/` directory created (dir mtime); consistent with a first SQLS run without `-v 2` into the same outdir (the compare script says that run logged `cx_count = -1`) | dir mtime; `compare_sqls_hhl.py` comment |
| 2026-08-17T22:28:07Z | SQLS `full_svd` run finished (solver `timestamp` 2026-08-17T18:28:07.82 local, `elapsed_time` 0.619 s); tree = `a885ef47` + uncommitted SQLS code | `metadata_nelem5_SQLS_statevector_nshots150000.pkl`; file mtimes 18:28:07 local |
| 2026-08-17T22:29:54Z | `hhl_metrics_*.csv` and `qc_metadata_sqls_*.csv` in the SQLS trial last modified (107 s after the run; see caveat in Validation) | file mtimes |
| 2026-08-17T22:30Z | `compare_sqls_hhl.py` last modified | file mtime |
| 2026-08-17T22:48:52Z | qtsuite #54 "Test: truncated_mps" created | `gh issue view 54` |
| 2026-08-17T23:22Z | `sqls-vs-hhl-2026-08-17/README.md` and the two PNGs written | file mtimes |
| 2026-08-17T23:22:59Z | fvm `ef7f0a8b` "Add optional SQLS linear solver alongside HHL"; `main` tip, local == `origin/main` | fvm git log, `git rev-parse` |
| 2026-08-17 | mesh note `note-20260817-0001` filed (`discovered_on` = `verified_on` = 2026-08-17) | note front-matter |
| 2026-08-24T22:04:47Z | qtsuite #53 closed | `gh issue view 53` |
| 2026-08-29T15:29:40Z | qtsuite #68 "Understand algorithm" added under #8 | `sub_issues` API |

Ordering check: each validation run preceded the commit it validated (the
`_local` provenance JSON for both HHL runs records `solver_working_tree_dirty:
true` with the uncommitted change named), and the SQLS run (22:28Z) sits
between `a885ef47` (21:16Z) and `ef7f0a8b` (23:22Z).

## State of fvm main before 2026-08-17

Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, remote
`Q8020-CFD/fvm_euler_1d_solver`, branch `main`.

- Before the day started, `main`'s tip was `a5317f2b` (2025-11-12T01:00:44Z,
  "Adding the detailed guide", Mohammad Alhawwary's HHL line). Its declared
  environment was 1.x: `requirements-quantum.txt` pinned
  `quantum_linear_solvers @ git+https://github.com/jw676/quantum_linear_solvers`,
  `qiskit==1.2.4`, `qiskit-aer==0.15.1`, `qiskit-algorithms==0.3.1`,
  `qiskit-ibm-runtime==0.35.0`, `qiskit-qasm3-import==0.5.1`, `qiskit-iqm==18.0`.
  The code, however, was already 2.x-idiomatic (`SamplerV2`, `qc.initialize`,
  no `opflow`/`qiskit_algorithms` imports), per the symbol sweep recorded in
  `STEPS-q8020-main-to-2.3.md`. There was no `pyproject.toml` on `main`.
- `60d973c5` (2026-08-17T18:32:12Z) "Deliver feature/qiskit-hhl to main".
  41 files, +3797/-586 lines. Merged the mature HHL line wholesale: steady
  mode, counts sign correction, +1e-15 norm guards, circuit save/load, timing
  metadata, SLURM/Frontier parallel-shot scripts (`scripts/run_shots.py`,
  `scripts/run_shots_parallel.py`, `scripts/submit_parallel_shots.sbatch`),
  `docs/DETAILED_GUIDE.md`, `docs/FRONTIER_CONDA_SETUP.md`,
  `docs/QUICKSTART_PARALLEL.md`, `post_process/plot_comparison.py`, LU
  reference solutions under `post_process/ref_sol/nelem{3,4,5,10,200}/`,
  `utils/list_fake_backends.py`, and a fix of a `np.zero` typo in
  `time_solvers.py`. Commit message: "feature/qiskit-hhl is a strict content
  superset of main."
- `fbe6ef10` (2026-08-17T20:44:14Z) "Reconcile solver code with
  archive/qiskit-hhl-2 (verbosity, checkpointing)". 5 files, +202/-17.
  Global verbosity in `math_tools.py` (`_GLOBAL_VERBOSITY`, `set_verbosity`,
  `get_verbosity`; `convert_to_pow2` / `convert_system_to_herm` /
  `scale_Ab_by_spectral_radius` default `verbosity=None`); `QuantumHHL`
  honors `verbosity=None`; `space_solvers.py` plot save guarded by
  `self.savedata`; `nozzle_1d_solver.py` gains `-savedata`, `-checkpoint`,
  `-resume`, `-original_max_iters`, `-v/-verb/-verbosity`, per-outer-iteration
  checkpoint save and resume, converged banner; new `checkpoint_tools.py`
  (80 lines). Main's general `FakeProviderForBackendV2` was kept over the
  branch's FakeBrisbane/FakeTorino rework (operator decision recorded in
  `STEPS-q8020-main-to-2.3.md`).

So immediately before the three commits analysed below, `main` was an
HHL-only solver (`-linsolver` choices `LU`, `GMRES`, `HHL`), with 2.x code
but a contradictory 1.x dependency declaration and no packaging file.

## The three commits of 2026-08-17 (what each changed, file by file)

### `3c20cff8` 2026-08-17T20:44:30Z "Repin to qiskit 2.3 + Q8020-CFD fork; go uv-native, drop requirements*.txt"

Commit message (body, verbatim):

> Make the declared environment consistent with the (already 2.x) code, and
> pin it to the Apr 2026 Frontier run's exact stack for reproducibility.
>
> - pyproject.toml: single source of truth (with uv.lock). Quantum stack is a
>   CORE dependency (not an optional extra): quantum_linear_solvers @ the
>   Q8020-CFD fork, qiskit==2.3.1, qiskit-aer==0.17.2, qiskit-ibm-runtime==0.46.1,
>   qiskit-qasm3-import>=0.6.0. qiskit-algorithms omitted (the fork ships its own
>   AlgorithmResult); qiskit-iqm dropped.
> - uv.lock: fresh lock; pins the git lib by commit SHA (66eadf0).
> - .python-version: 3.12.
> - requirements.txt / requirements-quantum.txt: DELETED (deprecated; pyproject
>   is authoritative).
> - README + docs: install via `uv sync` / `pip install .` instead of
>   `pip install -r requirements*.txt`.
>
> Old main pinned qiskit==1.2.4 + the jw676 fork, contradicting the 2.x code.

8 files, +1101/-67 (1039 of the additions are `uv.lock`). No `.py` touched.

- `pyproject.toml` (new, 40 lines): `name = "fvm-euler-1d-solver"`, version
  0.1.0, `requires-python = ">=3.12,<3.14"`, authors Alhawwary and Gallo.
  `dependencies`: numpy>=1.20.0, scipy>=1.7.0, matplotlib>=3.3.0, PyYAML,
  python-dotenv, `quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers`,
  qiskit==2.3.1, qiskit-aer==0.17.2, qiskit-ibm-runtime==0.46.1,
  qiskit-qasm3-import>=0.6.0. `[tool.setuptools] py-modules` lists the flat
  modules: case, mesh, math_tools, helper_tools, checkpoint_tools,
  space_solvers, time_solvers, quantum_tools, nozzle_1d_solver.
- `uv.lock` (new): resolved set recorded in the 2.3 run's provenance JSON:
  python 3.12.10, qiskit 2.3.1, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.46.1,
  qiskit-qasm3-import 0.6.0, quantum-linear-solvers 0.1.0 at `66eadf0`,
  numpy 2.5.2, scipy 1.18.0, matplotlib 3.11.1.
- `.python-version` (new): `3.12`.
- `requirements.txt` (16 lines) and `requirements-quantum.txt` (26 lines):
  deleted.
- `README.md` (+8/-10), `docs/FRONTIER_CONDA_SETUP.md` (+11/-12),
  `docs/QUICKSTART_PARALLEL.md` (+2/-3): install text changed from the two
  `pip install -r` steps to `uv sync` / `pip install .`; "quantum stack
  (qiskit 2.3.x + the Q8020-CFD fork) is a core dependency".

Note the design decision: the quantum stack became a core dependency, not an
extra. The `STEPS` plan had proposed an optional `quantum` extra and thin
`requirements*.txt` mirrors for the Frontier conda-pack flow; the operator
chose core deps and deleted the requirements files instead (recorded in
`two-way-nov-vs-apr.md`, RESULTS section). `docs/FRONTIER_CONDA_SETUP.md`
therefore now says `pip install .` inside the conda env.

### `a885ef47` 2026-08-17T21:16:25Z "Bump quantum stack to latest qiskit 2.5 line"

Commit message (body, verbatim):

> qiskit 2.3.1 -> 2.5.2, qiskit-ibm-runtime 0.46.1 -> 0.49.0 (qiskit-aer stays
> 0.17.2, already latest; qiskit-qasm3-import >=0.6.0 unchanged). Verified against
> the Q8020-CFD linear-solver fork (66eadf0) with no fork change needed: the fork
> declares only qiskit>=2.0 and its imports + a full HHL solve run clean under
> 2.5.2.
>
> Solver .py code is unchanged. uv.lock re-resolved; docs bumped 2.3.x -> 2.5.x.
>
> Comparison of a matched 150k-shot nelem5 run under 2.3 vs 2.5 (same laptop, same
> fork, same case): qiskit 2.5's transpiler builds a ~6.5% shallower circuit
> (596,688 vs 638,237 depth, same 14 qubits) but takes ~3.7x longer to transpile
> (14.3 vs 3.9 s/iter). End-to-end wall time and solution quality unchanged within
> shot noise.

4 files, +22/-22. `pyproject.toml`: `qiskit==2.5.2`,
`qiskit-ibm-runtime==0.49.0`, comment changed from "pinned to the Apr 2026
Frontier run's exact versions" to "pinned to the latest qiskit 2.5 line".
`uv.lock` re-resolved (30 lines changed). `README.md` and
`docs/FRONTIER_CONDA_SETUP.md`: "2.3.x" to "2.5.x". No `.py` touched.

### `ef7f0a8b` 2026-08-17T23:22:59Z "Add optional SQLS linear solver alongside HHL"

Commit message (body, verbatim):

> Wire the ORNL SVD-based quantum linear solver (SQLS) into the FVM 1D Euler
> nozzle as an opt-in -linsolver SQLS scheme. Additive: the existing HHL path
> is untouched (QuantumHHL class and hhl_solve are byte-identical; the four
> shared 'HHL' gates are widened to ('HHL','SQLS') and still fire for HHL; the
> one shared metadata-harvest block was rewritten to pick up either solver and
> verified to still capture HHL).
>
> - pyproject.toml: sqls as an optional [sqls] extra (ORNL repo is
>   access-gated, so not a base dependency). No base deps changed.
> - quantum_tools.py: QuantumSQLS, mirroring QuantumHHL.solve_one_step but
>   SVD-native -- feeds the general non-Hermitian Jacobian directly (no
>   Hermitian doubling, no spectral pre-scale), calls sqls.runtime.quantum.
>   quantum_solve, aligns the free global sign to the classical reference.
> - time_solvers.py: sqls_solver init branch + sqls_solve + SQLS dispatch.
> - nozzle_1d_solver.py: -linsolver SQLS and -sqls_method/-sqls_k/
>   -sqls_state_prep/-sqls_repeats (repeats default 1 to match HHL's single
>   shot-budget run).
>
> Simulator-only (Aer statevector/shots); backend must be 'ideal'. Validated
> end-to-end at nelem 5 (full_svd: residual ~1e-9, converges in 6 Newton
> iters). Tracked in qtsuite #53; truncated_mps follow-up is #54.

4 files, +346/-12: `quantum_tools.py` +181/-1, `time_solvers.py` +115/-1,
`nozzle_1d_solver.py` +51/-10 (net +41), `pyproject.toml` +11.
`README.md` and `docs/` were NOT touched: as of `main` today `README.md:138`
and `docs/DETAILED_GUIDE.md:212` still read "Linear solver: LU, GMRES, HHL",
and no `-sqls_*` flag is documented anywhere outside `--help`.

`pyproject.toml` (+11): adds

```toml
[project.optional-dependencies]
sqls = ["sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git"]
```

with a comment block stating the ORNL repo is access-gated, that
`pip install -e ../sqls --no-deps` against a sibling checkout is the
intended install, and that `sqls` pins qiskit==2.1.2 but "only touches
stable core APIs (QuantumCircuit / Initialize / UnitaryGate / AerSimulator /
SamplerV2), so --no-deps against this repo's qiskit 2.5.2 stack is intended
and verified." The fvm `.venv` today indeed holds
`__editable__.sqls-0.1.0.pth` pointing at `/Users/agallojr/proj/src/q8020/sqls/src`,
alongside qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0,
quantum_linear_solvers 0.1.0.

`quantum_tools.py` (+181): one new class `QuantumSQLS` appended after
`QuantumHHL`, with `__init__`, `get_backend`, `solve_one_step`,
`save_metadata`. Details in the design section. `QuantumHHL` is unchanged.

`time_solvers.py` (+115): in `LinearSystemSolver.__init__`, `self.sqls_solver
= None` and a new `elif scheme_type == 'SQLS'` branch that imports
`QuantumSQLS` and constructs it from `linsolv_args` (wrapped in the same
broad `try/except Exception` that prints and continues, exactly as the HHL
branch does). In `solve_one_step`, the per-inner-iteration metrics-save gate
`if self.scheme_type == 'HHL'` became `in ('HHL', 'SQLS')`. In the dispatcher,
a new `elif self.scheme_type == "SQLS"` calls `self.sqls_solve(A, b,
step=step)` and stores the returned metrics in `self.hhl_metrics` ("reuse
the HHL metrics CSV path"). New method `sqls_solve(A, b, step=0)` (about
90 lines), described below.

`nozzle_1d_solver.py` (+51/-10): `-linsolver` choices gain `'SQLS'`. Four
new flags: `-sqls_method` (choices `full_svd`, `truncated_qr`,
`truncated_mps`; default `full_svd`), `-sqls_k` (int, default 128,
"power of 2, 2<=k<N; ignored by full_svd"), `-sqls_state_prep` (choices
`initialize`, `mps`; default `initialize`), `-sqls_repeats` (int, default 1,
"Default 1 matches the HHL single-run shot budget; >1 multiplies the
effective shots by this factor"). A new `elif linear_solver == 'SQLS'` block
builds `linsolv_args` with `backend_type`, `backend_method`, `shots`
(= `args.nshots`), `load_qcirc`, `use_gpu`, `output_dir`, `hhl_verbosity`
(= `args.verbosity`, name reused), and the four `sqls_*` values. Three
HHL-only gates were widened to `in ('HHL', 'SQLS')`: the `case_name` suffix
(`_{backend_method}` and `_nshots{N}`), the metadata-pkl block that records
`backend_type`/`backend_method`/`nshots`, and the plot `case_label`. The
metadata harvest of `qc_metadata` was rewritten from a hard-coded
`time_solver.linsys_solver.hhl_solver` to
`getattr(..., 'hhl_solver', None) or getattr(..., 'sqls_solver', None)`.
Unlike the HHL block, the SQLS block does not apply the "128 shots default
for real backends" rule (moot, since SQLS only accepts `ideal`).

## The SQLS integration design (as implemented)

### Class and function map

| Layer | HHL path (pre-existing) | SQLS path (added in `ef7f0a8b`) |
|---|---|---|
| CLI | `-linsolver HHL`, `-backend`, `-shots`, `-qc_gpu`, `-load_qcirc` | `-linsolver SQLS` plus `-sqls_method`, `-sqls_k`, `-sqls_state_prep`, `-sqls_repeats`; same `-shots`, `-qc_gpu`, `-backend` |
| Driver | `nozzle_1d_solver.py` builds `linsolv_args` | same, separate `elif` block |
| Time solver | `time_solvers.LinearSystemSolver.__init__` -> `self.hhl_solver = QuantumHHL(...)`; dispatcher -> `hhl_solve` | `self.sqls_solver = QuantumSQLS(...)`; dispatcher -> `sqls_solve` |
| Quantum wrapper | `quantum_tools.QuantumHHL.solve_one_step` -> `generate_circuit` (library `HHL` class from `linear_solvers`) -> `transpile_circuit` -> `run_circuit_ibm` / `get_sol_ideal_backend` | `quantum_tools.QuantumSQLS.solve_one_step` -> `sqls.runtime.quantum.quantum_solve` |
| Library | `Q8020-CFD/quantum_linear_solvers` at `66eadf0` | `sqls` at `9a4346a7` (`src/sqls/runtime/quantum.py`, `src/sqls/sqls.py`) |
| Per-solve metadata | `qc_metadata_nelem{n}_{backend}_shots{s}.csv`, 21 columns | `qc_metadata_sqls_nelem{n}_{method}_shots{s}.csv`, 17 columns |
| Per-solve metrics | `hhl_metrics_nelem{n}_{backend}_shots{s}.csv` | same file name and same 7 columns (reused on purpose) |
| Per-solve vectors | `dq_nelem{n}_iter{i}_{backend}_shots{s}.csv` with header `dq_lu, dq_hhl,` | same name pattern, header `dq_lu, dq_sqls,` |
| Saved systems | `system_Ab_nelem{n}_iter{i}.pkl` | same |
| Circuits | `.qpy` per iteration (about 1.5 GB per run, not archived) | none saved |

### Data flow from the CLI flag to the sqls call

1. `nozzle_1d_solver.py` parses `-linsolver SQLS`, fills `linsolv_args`, and
   passes it to the time scheme, which builds `LinearSystemSolver(scheme_type
   ='SQLS', ...)`.
2. `LinearSystemSolver.__init__` constructs `QuantumSQLS(backend_type,
   backend_method, nshots=linsolv_args['shots'], use_gpu, output_dir,
   verbosity=linsolv_args['hhl_verbosity'], steady_mode, method, k,
   state_prep, repeats)`. `QuantumSQLS.__init__` sets `self.mode = 'shots' if
   nshots else 'statevector'`, builds an `AerSimulator(method='statevector')`
   (GPU device if `use_gpu`, with CPU fallback), and prints the config.
3. Each Newton iteration, the Jacobian system `A dQ = b` (size
   `nsys = 3 * nelem`; 15 by 15 at nelem 5) reaches the dispatcher, which
   calls `sqls_solve(A, b, step)`.
4. `sqls_solve` pickles `{A, b}` to `system_Ab_nelem{n}_iter{step}.pkl`,
   computes the classical reference `dq_lu = self.lu_solve(A, b)` on the
   ORIGINAL system, then calls `self.sqls_solver.solve_one_step(A, b,
   nelem_q, self.iter, step=step)`.
5. `QuantumSQLS.solve_one_step` computes `get_matrix_properties(A_o)`
   (condition number, nnz per row), pads with `convert_to_pow2` (15 -> 16,
   `num_q = 4`), and calls

   ```python
   quantum_solve(csr_matrix(A_pow2), b_pow2, num_q, self.backend,
                 psi_norm=b_pow2, mode=self.mode, k=self.k, method=self.method,
                 state_prep=self.state_prep, shots=(self.nshots or int(1e6)),
                 repeats=self.repeats, sqls_out=sqls_out, timings=timings,
                 count_cx=(self.verbosity == 2), gpu=self.use_gpu)
   ```

   Inside `sqls`, `quantum_solve` builds the circuit with `SQLS(A_csr, b,
   k, method, state_prep, ...)`. For `full_svd` that is a dense SVD
   `A = W S V^H`, `alpha = S^{-1} W^H b`, `new_b = W alpha`, and a circuit
   `Initialize(new_b)` + `UnitaryGate(W^H)` + `UnitaryGate(V)` whose output
   state is proportional to `final_b = V alpha = A^{-1} b`. `final_b` and
   its norm are therefore known classically before the circuit runs. In
   statevector mode `_run_statevector` appends `save_statevector`, runs on
   Aer UNTRANSPILED, strips a global phase, casts to real when the imaginary
   residue is below 1e-10 relative, and returns `sv / ||sv|| * ||final_b||`.
   In shots mode `_run_shots` uses `qiskit_ibm_runtime.SamplerV2` on the
   Aer backend with `[qc_meas] * repeats` at `shots` each, reconstructs
   `sqrt(prob)` per repeat, averages the `repeats` reconstructions, and
   `quantum_solve` restores per-component signs from `sign(final_b)`.
6. Back in `solve_one_step`, `x = x_pow2[:nsys].real` (padding is bottom /
   right), `self.qc_metadata` (backend, method, k, state_prep, repeats) is set
   for the run-level pkl, and a 17-column numerical row is appended to
   `qc_metadata_sqls_nelem{n}_{method}[_shots{s}].csv`: step, iter,
   matrix_size_orig, matrix_size_pow2, condition_number, nnz_per_row,
   nqubits, method, k, state_prep, repeats, n_data_qubits, m_ancilla,
   cx_count, circuit_depth, aer_device, solve_time.
7. `sqls_solve` aligns the global sign (`if np.dot(dq_sqls, dq_lu) < 0:
   dq_sqls = -dq_sqls`), computes `linsys_residual = ||A dq_sqls - b||_2`,
   `fidelity(dq_sqls, dq_lu)`, absolute / relative / normalized L2 errors
   versus `dq_lu`, prints a comparison table, writes the `dq_*.csv`, and
   returns `(dq_sqls, metrics)`. The caller stores the metrics in
   `self.hhl_metrics` and `save_hhl_metrics` appends them to
   `hhl_metrics_nelem{n}_{backend}_shots{s}.csv`.

### What is HHL-specific and SQLS skips

The HHL path (`QuantumHHL.solve_one_step`, `time_solvers.hhl_solve`,
unchanged by the commit) does, per solve:

- `scale_Ab_by_spectral_radius(A_o, b_o)`: spectral pre-scale so
  `lambda_max_scaled = 1` (visible in the HHL `qc_metadata` columns
  `lambda_max_scaled` about 1.0, `lambda_min_scaled` about 0.17).
- `convert_to_pow2` (15 -> 16) then `convert_system_to_herm` (16 -> 32):
  Hermitian doubling `[[0, A],[A^H, 0]]`. Data register 5 qubits
  (`nqubits = 5`); with QPE and ancilla registers the circuit is 14 qubits
  (13 on iteration 1 in both HHL runs).
- Library `HHL` circuit generation (QPE, `ExactReciprocal`, inverse QPE),
  then a MANDATORY `transpile(circ, AerSimulator)` because Aer cannot
  execute the composite QPE / 1/x blocks (`AerError: unknown instruction`
  when fed raw; verified in the session per the README and the note).
  Transpiled depth about 5.97e5 to 6.38e5 layers, 6.4e5 to 6.5e5 gates.
- Post-processing in `hhl_solve`: extract the true solution from the
  doubled vector, rescale magnitude by `||dq_herm||` (`hhl_scale_type ==
  'true_sol'`) or a least-squares alpha, and in shots mode take `|dq|` and
  copy the per-component signs from the classical Hermitian LU solution.
  Fidelity is computed against `dq_herm` (LU of the doubled system).

The SQLS path skips all of this: the general non-Hermitian `A` goes in
directly (4 data qubits, `m_ancilla = 0` for `full_svd`); `(A/rho)^+ (b/rho)
== A^+ b` so the spectral scale is a no-op and is dropped; `Initialize` and
`UnitaryGate` are Aer-native so nothing is transpiled for execution (the
`{u3, cx}` transpile at `-v 2` is a diagnostic only: `count_cx_depth`
transpiles to `basis_gates=["u3","cx"]`, optimization level 1 then 0, and
returns `(-1, -1)` on failure); magnitude is exact from `||final_b||`, so no
classical rescale; and per-component signs in shots mode come from
`sign(final_b)` inside `sqls`, not from the fvm LU solve. Fidelity is
against `dq_lu` of the original system.

### Sign alignment

Statevector fidelity is phase-blind, so the state returned by
`_run_statevector` has an arbitrary global sign (and `quantum_solve` only
fixes a global phase to make the vector real). `sqls_solve` resolves it by
`np.dot(dq_sqls, dq_lu) < 0`, i.e. against the classical LU solution of the
same system. This is the one place the SQLS path still depends on a
classical reference solve for the returned `dQ`; the HHL path depends on it
for magnitude as well. In shots mode `quantum_solve` already restores all
signs from `final_b`, so the dot-product flip is a no-op there.

### Repeats semantics

`sqls.runtime.quantum.quantum_solve` defaults `repeats=10`: it submits
`[qc_meas] * repeats` to the Sampler at `shots` each and averages the
`repeats` amplitude reconstructions, so a "150000-shot" run draws 1.5e6
measurements by default. The fvm wrapper exposes this as `-sqls_repeats` and
defaults it to 1 "so the effective shot budget is exactly nshots, matching
the HHL path's single run." The `repeats` value is recorded per solve in
the `qc_metadata_sqls_*.csv` and in the run pkl. The session also found that
at 150000 shots on a 16-amplitude state, pre-tail fidelity was the same at
repeats 1 and 10 (about 0.99997): sampling was already saturated. In
statevector mode (`-shots 0`) `repeats` and `shots` are unused.

### Backend restrictions

`QuantumSQLS.get_backend` raises `ValueError` for any `backend_type` other
than `'ideal'` ("quantum_solve runs circuits on Aer untranspiled, so this
path is simulator-only"). `backend_method` is recorded but the simulator is
always `AerSimulator(method='statevector')`; the `-backend` string still
flows into file names (`_statevector_`). `-qc_gpu` requests
`AerSimulator(device='GPU')` and also sets `gpu=True` for `sqls`'s classical
torch paths; the August run recorded `aer_device = CPU`. There is no fake-
backend, noisy, IBM, or IQM path for SQLS, and no transpile-to-device step,
so hardware execution is not reachable from the fvm wrapper today. HHL, by
contrast, accepts `ideal`, `fake`, `real-ibm`, `real-iqm`.

### Smaller implementation facts worth knowing

- `-sqls_k` defaults to 128. `sqls.SQLS` enforces `2 <= k < N`, power of 2,
  for the two truncated methods (`ValueError` otherwise). At nelem 5,
  `N = 16`, so any `truncated_qr` / `truncated_mps` run must pass
  `-sqls_k` in {2, 4, 8}; the default would raise at the first solve. The
  construction-time `try/except` in `LinearSystemSolver.__init__` does not
  cover this because the check happens inside `quantum_solve`.
- `linsolv_args['load_qcirc']` is populated for SQLS but `QuantumSQLS` has
  no circuit save/load; no `.qpy` is written.
- The `-v 2` verbosity is what populates `cx_count` / `circuit_depth`; at
  lower verbosity they are `-1`. That is why the archived trial is "v2".
- SQLS metrics go to a file literally named `hhl_metrics_*.csv`, and the run
  pkl's `linear_solver` field is `SQLS`. Any downstream tool keyed on the
  file name will treat the rows as HHL metrics; any tool keyed on HHL's
  21-column `qc_metadata_nelem*` schema (as the harvester's
  `transpile_passes` output suggests) will not find SQLS's 17-column
  `qc_metadata_sqls_*` file. This is the likely reason the SQLS trial has no
  `q8020_*.json` fragments (to be confirmed under WORKPLAN item 4).
- `psi_norm=b_pow2` is passed only as `quantum_solve`'s legacy fallback for
  the output scale; `final_b` is always present for the three methods.
- The fvm convergence banner fires on `resratio < conv_tol or
  np.all(dqnorm <= 1e-10)` (`nozzle_1d_solver.py:313`). For the SQLS run the
  final residual ratio was 1.2604e-9 / 12.3754 = 1.02e-10, just above
  `conv_tol = 1e-10`; the stop at iteration 6 came from the `dqnorm` branch
  (all `|dq|` at iteration 6 are at or below 5.2e-11).

## Validation that was done

Three single-trial runs on the laptop, all the same physics case: nozzle
`A(x) = 1.398 + 0.347 tanh(0.8 x - 4)`, nelem 5, BDF1, `-localdt`, nondim,
`cfl = 1e10`, 15 outer / 1 inner iterations, `conv_tol 1e-10`, `res_tol
0.01`, ideal statevector backend, 150000 shots. Iteration-0 outer residual
is `12.375368413827264` (dimensionless nondimensional residual norm) in all
three, identical to the Nov 2025 and Apr 2026 Frontier groups: same
discretization and same assembled system.

### Run inventory

| | HHL, qiskit 2.3.1 | HHL, qiskit 2.5.2 | SQLS full_svd, qiskit 2.5.2 |
|---|---|---|---|
| Results dir | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit23-local/trial_0/` | `.../2026-08-17-qiskit25-local/trial_0/` | `.../2026-08-17-sqls-local-v2/trial_0/` |
| Files in trial_0 | 78 (15 dq, 15 results_iter x2 naming, 15 system pkl, 12 q8020 JSON, qc_metadata, hhl_metrics, residual, final_results, pkl, PNG) | 78 (same layout) | 34 (7 dq, 7 x2 results_iter, 7 system pkl, qc_metadata_sqls, hhl_metrics, residual, final_results, pkl, PNG); no JSON |
| README.md in results dir | yes (2120 bytes) | yes (2237 bytes) | NO |
| `q8020_*.json` fragments | 12: harvester `q8020_{case,code,backend,artifacts,results,analysis}_0.json` + hand-authored `q8020_{params,experiment,exec_stats}_local.json`, `q8020_env_{before,after}_local.json`, `q8020_code_provenance_local.json` | same 12 | none |
| Solver tree at run time | `60d973c5` + uncommitted 2.3 port | `3c20cff8` + uncommitted 2.5 bump | `a885ef47` + uncommitted SQLS code (inferred from timestamps; no provenance file) |
| Linear-solver lib | Q8020-CFD `66eadf0` | Q8020-CFD `66eadf0` | `sqls` `9a4346a7` (editable, `--no-deps`) |
| Command | `./.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 10000000000.0 -outdir .../agent-tmp/fvm-euler-1d-qiskit-1x-vs-2x/local-run-2026` | same with `-outdir .../local-run-2.5` | per the comparison README: `-nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -v 2` (not recorded in a provenance file) |
| Start to end (UTC) | 20:11:00Z to 20:25:12Z | 20:56:07Z to 21:09:25Z | ended 22:28:07Z |
| Solver `elapsed_time` | 817.74 s | 859.34 s | 0.619 s |
| Outer iterations run | 15 (0..14), `converged: false` | 15 (0..14), `converged: false` | 7 (0..6), stopped by `dqnorm <= 1e-10` |
| Final outer residual | 4.6875e-3 | 6.7953e-3 | 1.2604e-9 |
| Residual reduction from iter 0 | 3.79e-4 | 5.49e-4 | 1.02e-10 |

### Circuit and timing numbers (per linear solve)

| metric | HHL 2.3.1 | HHL 2.5.2 | SQLS full_svd |
|---|---|---|---|
| system size: original / pow2 / Hermitian | 15 / 16 / 32 | 15 / 16 / 32 | 15 / 16 / (none) |
| condition number range over solves | 59.9 to 96.0 | 58.2 to 96.0 | 59.9 to 96.0 |
| data-register qubits | 5 | 5 | 4 |
| circuit width (qubits) | 14 (13 at iter 1) | 14 (13 at iter 1) | 4 |
| pre-transpile depth / gates | 5 / 19 | 5 / 19 | n/a (no execution transpile) |
| transpiled depth (iter 0) | 638237 layers (Aer basis) | 596688 layers (Aer basis) | 398 layers ({u3,cx} diagnostic; 397 at iter 1) |
| transpiled gate count (iter 0) | 649089 gates (Aer basis) | 641145 gates (Aer basis) | 200 to 201 CX ({u3,cx} diagnostic) |
| circuit generate time | 20.9 s/iter (10.5 s at iter 1) | 20.4 s/iter | included in solve_time |
| transpile time | 3.9 to 4.3 s/iter | 14.4 to 15.8 s/iter | 0 s for execution (diagnostic transpile not timed in CSV) |
| execute time | 18.2 to 19.0 s/iter | 18.2 to 18.6 s/iter | included in solve_time |
| mean total time per solve | 42.0 s (mean of generate+transpile+run over 15 solves; 43.1 to 44.7 s excluding the 19.8 s iter 1) | 51.70 s (mean of generate+transpile+run over 15 solves; 53.1 to 54.8 s excluding the 24.8 s iter 1) | 0.082 s (mean `solve_time` over 7 solves; 0.103 s at iter 0, 0.075 to 0.085 s after) |

HHL 2.3 versus 2.5 (the qiskit isolation, same machine): depth -6.5 %,
gates -1.2 %, transpile time about 3.7x longer (3.9 +/- 0.5 s to
14.3 +/- 1.9 s per iteration), generate and execute flat, end-to-end 817.7 s
to 859.3 s. The 2.3 local run reproduces the April 2026 Frontier transpiled
circuit exactly (638237 / 649089 / 14), which was the port-validation
criterion.

### Solution quality

| metric | HHL 2.3.1 | HHL 2.5.2 | SQLS full_svd |
|---|---|---|---|
| per-solve fidelity, range | 0.9801 to 0.9975 | 0.9880 to 0.9990 | 0.999954 to 0.999981 for iters 0..5; 0.4510 at iter 6 |
| per-solve fidelity, mean | 0.990 | 0.993 | 0.9999 (iters 0..5) |
| mean `l2_error_normalized` | 0.095 | 0.082 | 0.0043 to 0.0068 (iters 0..5); 0.81 at iter 6 |
| linear-system residual `||A dq - b||_2`, iter 0 -> last | 1.885 -> 2.69e-3 | 2.122 -> 3.73e-3 | 0.269 -> 1.23e-9 |
| final primitive solution vs LU reference (`post_process/ref_sol/nelem5/final_results_nelem5_LU.csv`), max abs difference | about 5e-4 in rho (e.g. rho(x=0.5) 0.61973 vs 0.61971) | about 5e-5 in rho (0.48372 vs 0.48377 at x=0.9) | at or below 1e-11 in every cell (rho(x=0.9) 0.4837714414765217 vs 0.48377144146979123) |

SQLS outer residual history: 12.3754, 0.7612, 0.07096, 2.690e-3,
4.545e-5, 2.608e-7, 1.260e-9 (quadratic Newton convergence, as with an exact
LU solve; the LU reference run in `ref_sol/nelem5/residual_nelem5_LU.csv`
reaches 8.3e-13 in 3 iterations from a different start). HHL 2.5 history:
12.3754, 2.4929, 0.6306, 0.3820, 0.1587, 0.0739, 0.0651, 0.0457, 0.0357,
0.0311, 0.0201, 0.0123, 0.0116, 0.0108, 0.0068 (linear, shot-noise-limited).

### Caveats the authors recorded (all load-bearing for any paper use)

From `sqls-vs-hhl-2026-08-17/README.md` and `note-20260817-0001` section D:

1. Circuit basis mismatch. SQLS CX / depth are a `{u3,cx}` synthesis from
   `sqls`'s `count_cx_depth` diagnostic (`-v 2`); HHL depth / gates are
   `transpile(circ, AerSimulator)` in Aer's own basis. The "about 3 orders
   of magnitude" gap is order-of-magnitude only. A like-for-like comparison
   needs both circuits re-synthesized to one basis; HHL's about 1.5 GB of
   per-iteration `.qpy` files were not copied into the results tree (the
   raw run dir under `bus/agent-tmp/fvm-euler-1d-qiskit-1x-vs-2x/` no longer
   exists either), so it cannot be done from the archived artifacts.
2. Why HHL cannot skip transpilation (verified empirically in the session):
   the raw HHL circuit is four opaque composite blocks (state-prep, QPE,
   1/x, QPE-dagger) and Aer raises `AerError: unknown instruction` on it.
   SQLS's `Initialize` / `UnitaryGate` are Aer-native. The asymmetry is
   intrinsic to the circuit constructions, not a wrapper choice. The flip
   side (note section E): `full_svd`'s two N x N `UnitaryGate`s decompose
   via Quantum Shannon Decomposition to O(4^n) CX on real hardware, the same
   asymptotic failure mode as HHL; at n = 4 the about 201-CX circuit is
   hardware-sized, but the blow-up arrives as the grid grows.
3. Shots / repeats. `sqls` defaults `repeats=10`, so a naive 150000-shot run
   draws 1.5e6 measurements, 10x HHL. The comparison used `-sqls_repeats 1`.
   Pre-tail fidelity was identical at repeats 1 and 10 (about 0.99997), so
   the extra sampling was wasted at this size.
4. Fidelity tail collapse. SQLS per-solve fidelity is about 1.0 through the
   penultimate Newton step and drops to 0.45 to 0.69 (run-dependent; 0.4510
   in the archived trial) at the converged final step. The archived
   `dq_nelem5_iter6_statevector_shots150000.csv` shows why: `dq_lu` entries
   are 2e-13 to 4e-11 and the shots reconstruction returns exactly 0.0 for
   11 of 15 components and 2.58e-11 or 5.16e-11 for the rest, i.e. the
   update is below shot resolution. The linear-system residual at that step
   is still 1.23e-9, so it is a sampling artifact on a near-zero update, not
   a solver error. Statevector mode (`-shots 0`) removes it (asserted; no
   `-shots 0` run is archived).
5. Laptop versus Frontier timing. All three August runs are laptop
   wall-clock. The April 2026 Frontier matched HHL trial took 1653.6 +/- 86 s
   solver-only (2354.9 s including postproc) for 15 iterations; the laptop
   took 817.7 s and 859.3 s. Hardware differs, so only the 2.3-vs-2.5 laptop
   pair is a valid timing comparison; compare circuit size and quality
   across hosts, not seconds. The 0.62 s SQLS total is likewise laptop-only.
6. n = 1 everywhere. The 2.3 and 2.5 final residuals (4.69e-3 vs 6.80e-3)
   differ by shot RNG, not by version; the four-way README is explicit that
   single-trial comparisons measure shot noise (a trap the earlier Nov-vs-Apr
   study hit and documented).

### Additional provenance observations (mine, 2026-10-14)

- In the SQLS trial, every file carries mtime 2026-08-17T22:28:07Z (the
  solver's own end timestamp) except `hhl_metrics_nelem5_statevector_shots150000.csv`
  and `qc_metadata_sqls_nelem5_full_svd_shots150000.csv`, which are
  2026-08-17T22:29:54Z. Both files are append-mode in the code; the
  directory's own mtime is about 22:21Z. The consistent reading is that a
  first SQLS run (without `-v 2`, `cx_count = -1`) wrote into the same
  outdir at about 22:21Z, the `-v 2` run overwrote the per-iteration files
  at 22:28Z, and the two append-mode CSVs were then hand-trimmed to the
  second run's 7 rows at 22:29:54Z. The rows present are self-consistent
  (7 rows, `cx_count` populated, `repeats = 1`), but the trial has no
  provenance file saying so.
- The SQLS trial has no `README.md`, no command record, no environment
  snapshot, and no git SHA record; the two HHL trials have all of these
  (`q8020_params_local.json`, `q8020_env_{before,after}_local.json`,
  `q8020_code_provenance_local.json`). The SQLS command line above is
  reconstructed from the comparison README.
- The `.venv` the runs used still exists in the fvm repo and is the
  qiskit 2.5.2 / sqls-editable environment; it is the only record of the
  resolved SQLS-side stack (sqls 0.1.0 at the local checkout, no sqls deps
  installed by it).

## What was NOT done

Gaps relative to producing paper-grade SQLS results under the HHL / LuGo
protocol (10 trials, shot sweep, CFL sweep, mesh scaling, sweeper-driven,
metautil metadata):

1. No Frontier run. Everything SQLS-related ran on `MH-DT9TLJQR2V`. No
   sbatch, no `q8020-sweep` invocation, no `run_shots_parallel.py` use.
2. One trial. The paper's HHL shot study has 10 trials per shot count
   (`results/fvm_euler_1d_solver/2025-11-11/shots_*`); the CFL sweep has 3
   matched trials at 150000 shots. SQLS has n = 1 at one operating point.
3. No shot sweep. Only 150000 shots. No statevector-only (`-shots 0`) run is
   archived even though the README relies on it to explain the tail collapse.
4. No CFL sweep (the April protocol is `time_steps_0..4`), no nelem scaling
   (only nelem 5; the LU reference set covers nelem 3, 4, 5, 10, 200).
5. No `q8020_*.json` metadata fragments for the SQLS trial, versus 12 per HHL
   trial. The trial was not run through the sweeper or the harvester; the
   SQLS metadata CSV has a different name and schema from HHL's, so the
   existing harvester most likely cannot read it (WORKPLAN items 4 and 5).
6. No results-dir README for `2026-08-17-sqls-local-v2`; the write-up lives
   only in `aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`.
7. `truncated_mps` and `truncated_qr` untested in the fvm context (qtsuite
   #54, open, board status Todo). The default `-sqls_k 128` is invalid for
   them at nelem 5 (`N = 16` requires `k` in {2, 4, 8}); nothing in the fvm
   wrapper guards this.
8. No non-ideal backend. `QuantumSQLS` raises on anything but `ideal`; no
   fake / noisy / IBM / IQM path, no device transpile, no GPU run
   (`aer_device = CPU`). Hardware readiness is "stub" per the note (section E).
9. No like-for-like circuit-cost comparison. HHL `.qpy` circuits were not
   kept and the HHL path does not emit `{u3,cx}` counts; SQLS counts are
   `{u3,cx}` only.
10. Documentation not updated. `README.md` and `docs/DETAILED_GUIDE.md` still
    list `LU, GMRES, HHL` and document no `-sqls_*` flags; `pyproject.toml`'s
    `description` still says "quantum HHL linear solver support".
11. No tests. The fvm repo contains no `test_*.py` or `tests/` directory
    (checked 2026-10-14), so the #53 scope line "Validate by re-running the
    existing FVM tests" could only have meant the manual nelem-5 run.
12. The `repeats` 1-versus-10 equivalence (about 0.99997 pre-tail fidelity
    both ways) is recorded in prose only; the repeats = 10 run's artifacts
    are not in the results tree.
13. Dependency posture is informal. The `[sqls]` extra points at
    `https://code.ornl.gov/olcf-qcfd/sqls.git`, which is access-gated and
    which this network has seen refuse with HTTP 403 after a burst of
    requests (2026-10-13) and answer HTTP 504 once on `git pull`
    (2026-10-14) (lore-20261013-0001; WORKPLAN item 2). The actual install
    was `pip install -e ../sqls --no-deps` from a checkout that pins
    qiskit==2.1.2 / qiskit-aer==0.17.1 / numpy==2.3.3 / scipy==1.16.2 but
    runs under qiskit 2.5.2 / aer 0.17.2 / numpy 2.5.2 / scipy 1.18.0; the
    commit calls this "verified" but no `sqls` test run is recorded. The
    local `sqls` checkout has not been refreshed since the 2026-07-26 clone
    (HEAD `9a4346a7`, 2026-06-30; 22 commits total).
14. No flow-field or convergence-history figures were produced for SQLS
    beyond the two comparison PNGs (4-panel bars and the fidelity-collapse
    line); the solver's own `solution_plot_*.png` exists in the trial.
15. Of #8's sub-issues, #10 "Test plan (SQLS)", #11 "Run cases (SQLS)" and
    #12 "Analysis (SQLS)" (all created 2026-08-10) show no activity; #68
    "Understand algorithm" was added 2026-08-29. Only #53 moved.
16. The harness-level `nozzle_1d_solver.py` still writes SQLS metrics into
    `hhl_metrics_*.csv`; if the paper pipeline keys on that name, SQLS rows
    will be mislabeled as HHL unless the harvester is taught the difference.

## Tracking — qtsuite issues 8/53/54 state

Checked 2026-10-14 via `gh` (repo `agallojr/qtsuite`, GitHub Project #3
"Q8020-CFD"; see lore-20260812-0002 for the board layout).

- #8 "Code: SQLS". OPEN. Created 2026-08-10T18:18:08Z, updated
  2026-08-11T18:52:15Z. Body: "Exercise the SQLS solvers." Board status:
  On-deck. Sub-issues: #9 (open) "solverfw port & basic operation, FV case";
  #10 (open) "Test plan (SQLS)"; #11 (open) "Run cases (SQLS)"; #12 (open)
  "Analysis (SQLS)"; #53 (closed); #54 (open); #68 (open) "Understand
  algorithm" (2026-08-29T15:29:40Z).
  https://github.com/agallojr/qtsuite/issues/8
- #53 "Basic FVM Euler integration & test". CLOSED 2026-08-24T22:04:47Z
  (created 2026-08-17T21:47:20Z; no comments). Board status: Done. Body:
  wire SQLS in as an optional back-end for `q8020/fvm_euler_1d_solver`
  alongside HHL; scope = optional `[sqls]` extra; `QuantumSQLS` mirroring
  the `QuantumHHL.solve_one_step(A, b, ...)` contract and calling
  `sqls.runtime.quantum.quantum_solve`; new `SQLS` branch in
  `time_solvers.py` plus `-linsolver SQLS` with `method` / `k` /
  `state_prep` knobs; exploit the SVD-native path (drop Hermitian doubling
  and spectral pre-scale, exact magnitude from `final_b`); "Validate by
  re-running the existing FVM tests." Sub-issue of #8. Every scope line
  except the test line maps to `ef7f0a8b`; `-sqls_repeats` was added beyond
  scope. https://github.com/agallojr/qtsuite/issues/53
- #54 "Test: truncated_mps". OPEN. Created 2026-08-17T22:48:52Z, no updates
  since, no comments. Board status: Todo. Body: exercise `truncated_mps` in
  the FVM integration (the hardware-scaling path): `full_svd` is validated
  and default but its N x N `UnitaryGate`s blow up via QSD (O(4^n) CX);
  `truncated_mps` costs O((n+m) chi^2) CX. Scope: run with `-linsolver SQLS
  -sqls_method truncated_mps -sqls_k <pow2>` across k; characterize the
  rank-k truncation ceiling on fidelity and on Newton convergence; report CX
  / depth / width including bond ancillas versus `full_svd` at matched
  cases; note when truncation stalls outer convergence. Sub-issue of #8.
  https://github.com/agallojr/qtsuite/issues/54

## Sources

Git (fvm), `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`main`, remote `https://github.com/Q8020-CFD/fvm_euler_1d_solver.git`,
HEAD == origin/main == `ef7f0a8b`:
- `a5317f2b` 2025-11-12T01:00:44Z (pre-August tip)
- `60d973c5` 2026-08-17T18:32:12Z, `fbe6ef10` 2026-08-17T20:44:14Z,
  `3c20cff8` 2026-08-17T20:44:30Z, `a885ef47` 2026-08-17T21:16:25Z,
  `ef7f0a8b` 2026-08-17T23:22:59Z (`git show --stat` and full diffs)
- Working tree files read: `pyproject.toml`, `quantum_tools.py`
  (`QuantumHHL.__init__`, `QuantumHHL.solve_one_step`, `QuantumSQLS`),
  `time_solvers.py` (`LinearSystemSolver.__init__`, `save_hhl_metrics`,
  `hhl_solve`, `sqls_solve`), `nozzle_1d_solver.py` (lines 59 to 110,
  198 to 215, 296 to 320), `README.md:138`, `docs/DETAILED_GUIDE.md:212`,
  `post_process/ref_sol/nelem5/final_results_nelem5_LU.csv`,
  `post_process/ref_sol/nelem5/residual_nelem5_LU.csv`,
  `.venv/lib/python3.12/site-packages/` listing and `__editable__.sqls-0.1.0.pth`

Git (sqls), `/Users/agallojr/proj/src/q8020/sqls`, remote
`https://code.ornl.gov/olcf-qcfd/sqls.git`, HEAD == origin/main ==
`9a4346a7` (2026-06-30T14:40:52Z), 22 commits, clean tree, directory mtime
2026-07-26T14:03:43Z:
- `README.md`, `pyproject.toml`, `requirements.txt`
- `src/sqls/runtime/quantum.py` (`count_cx_depth`, `quantum_solve`,
  `_run_statevector`, `_run_shots`), `src/sqls/sqls.py` (`SQLS` signature,
  `full_svd` block, k validation)

Results, `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/`:
- `2026-08-17-qiskit23-local/README.md` and `trial_0/` (`qc_metadata_nelem5_statevector_shots150000.csv`,
  `hhl_metrics_nelem5_statevector_shots150000.csv`,
  `residual_nelem5_HHL_statevector_nshots150000.csv`,
  `final_results_nelem5_HHL_statevector_nshots150000.csv`,
  `metadata_nelem5_HHL_statevector_nshots150000.pkl`, all 12 `q8020_*.json`)
- `2026-08-17-qiskit25-local/README.md` and `trial_0/` (same set)
- `2026-08-17-sqls-local-v2/trial_0/` (`qc_metadata_sqls_nelem5_full_svd_shots150000.csv`,
  `hhl_metrics_nelem5_statevector_shots150000.csv`,
  `residual_nelem5_SQLS_statevector_nshots150000.csv`,
  `final_results_nelem5_SQLS_statevector_nshots150000.csv`,
  `metadata_nelem5_SQLS_statevector_nshots150000.pkl`,
  `dq_nelem5_iter5_statevector_shots150000.csv`,
  `dq_nelem5_iter6_statevector_shots150000.csv`; file mtimes via `ls -lT`)

Analysis folders:
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`,
  `compare_sqls_hhl.py`, `sqls_vs_hhl_compare.png` (95413 bytes),
  `sqls_fidelity_collapse.png` (42116 bytes)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/qiskit_2.x/fvm-euler-1d-1x-vs-2x-vs-local-2026-08/README.md`
  and `session-notes/PORT-PLAN.md`, `session-notes/STEPS-q8020-main-to-2.3.md`,
  `session-notes/two-way-nov-vs-apr.md` (`gather.py`, `summary.json` listed, not read)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`

Mesh library, `/Users/agallojr/proj/src/research-notes/bus/memory/`:
- `notes/note-20260817-0001-sqls-fvm-quantum-timestep-frozen-jacobian.md` (primary)
- `lore/lore-20261013-0001-code-ornl-gov-blocks-ip-after-burst-of-fetches.md`
- `lore/lore-20260812-0002-q8020-issue-list-location.md`
- `refs/ref-20261013-0001-ornl-vqls-cfd-hybrid-quantum-hpc-qce2026.md` (header only; related ORNL work, not August)
- grep hits in `notes/note-20260924-0002-solverfw-v2-vocabulary-catalog-and-component-tree.md`
  and `notes/note-20260924-0001-helloquantum-as-framework-gaps-vs-solverfw.md`
  (September framing of SQLS as an encode plugin; not August work, not used)
- auto-memory index line `sqls-fvm-integration` in `~/.claude/projects/-Users-agallojr-proj-src/memory/MEMORY.md`

GitHub (read-only, 2026-10-14): `gh issue view 8|53|54 --repo agallojr/qtsuite`,
`gh api repos/agallojr/qtsuite/issues/8/sub_issues`,
`gh project item-list 3 --owner agallojr -L 200`.
