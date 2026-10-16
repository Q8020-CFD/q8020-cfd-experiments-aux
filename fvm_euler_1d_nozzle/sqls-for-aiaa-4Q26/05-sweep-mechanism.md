# Sweep mechanism — how fvm was run, how SQLS will be run

Item 5 of `WORKPLAN.md`. Written 2026-10-15T01:51Z on the laptop
(`MH-DT9TLJQR2V`), read-only against every repo, venv and results tree. The
only things executed were `q8020-sweep --dry-run` (after confirming from
`sweep.py` that it never launches the solver, `sbatch`, or a worker) and one
read-only pass of the fvm harvester over the August SQLS trial, both writing
only under `/tmp/sweep-check/`. No solver run, no sweep, no git write.

Companion deliverable (draft, not to be run):
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml`

Headline findings:

1. The April 2026 CFL sweep is the only fvm campaign that went through our
   sweeper end to end. The 2026-04-05 run captured the full fragment set; the
   2026-04-08 and 2026-04-10 runs lost every solver-side fragment because the
   TOML still pointed `_case_postproc` at `codes/`, a path the harvester had
   left on 2026-04-05. That stale path is still in `aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml` today.
2. `q8020-sweep` is installed only inside three repo venvs (metautil,
   backend-utils, ch-lbm), all editable against
   `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src`, which is checked
   out on `feature/solverfw-v2` (4 commits ahead of `main`), not `main`.
3. The current fvm harvester does run on SQLS output and emits all six
   solver-side fragments, but `artifacts.transpile_passes` and
   `circuit_timing_total_s` come out all zeros, the SQLS-specific columns
   (`cx_count`, `circuit_depth`, `solve_time`, `method`, `k`, `repeats`) are
   dropped, and the per-iteration LU/quantum solution vectors are not parsed
   (the SQLS stdout table header says `SQLS sol`, the parser keys on
   `HHL sol`).
4. SQLS `cx_count`/`circuit_depth` are only recorded with `-v 2`; the draft
   TOML sets that for SQLS groups and resets `-v 1` for the HHL control.

## 1. Past invocation modes

| When (UTC) | Where | Mechanism | Who | Metadata captured |
|---|---|---|---|---|
| 2025-11-11 (solver runs); fragments 2026-02-09T19:52Z | Frontier (`/lustre/orion/ard189/proj-shared/nozzle_1d_results/`), qiskit 1.2.4 | Solver-native: `scripts/submit_parallel_shots.sbatch` + `scripts/run_shots_parallel.py` (conda-pack + sbcast, one `srun` per trial) | M. Alhawwary (commit `b7bb0d4c`) | None at run time. `run.log` per trial. Harvested post hoc on the laptop: `q8020_{case,code,backend,artifacts,results,analysis,experiment}_<id>_0.json` + `q8020_metadata_<id>.json`; no `params`, `exec_stats`, `env_*`, or `sweep_*` fragments |
| 2026-02-24 / 2026-02-26 (LuGo) | Frontier, ORNL-run (`.../LuGo_rst/output_parallel_shots`) | Harvest-only: `harvest_lugo_all.sh` copies raw output and runs the fvm harvester + `harvest_metadata` | ORNL ran; Andy harvested | Solver-side six fragments + `q8020_metadata_trial_N.json`; no sweeper provenance |
| 2026-04-05T00:10Z submit, job 4336936 ran 06:10Z to ~06:50Z | Frontier, `/lustre/orion/ard189/proj-shared/agallojr/q8020/2026-04-04/_52d087d1/` | `q8020-sweep` (metautil), `_slurm=true`, parallel, one sbatch, 50 exclusive nodes, venvs sbcast to NVMe | Andy | Complete: sweeper fragments (`params`, `env_before/after`, `sweep_{case,code,artifacts,exec_stats,experiment}`), solver fragments via `_case_postproc` harvester, `q8020_metadata_<id>.json` rollup, `pipeline_args/result.json`, sweep meta + expanded cases + sbatch + slurm logs |
| 2026-04-09T00:18Z submit, job 4355227 ran 18:42Z + 77 min 20 s | Frontier, `.../2026-04-08/_85fd6d17/` | same (30 nodes, `more_iters` group, 60 iters) | Andy | Sweeper fragments only; `_case_postproc` failed on all 30 cases (exit 2, harvester path missing) so no `case/code/backend/artifacts/results/analysis` fragments |
| 2026-04-10T16:32Z submit, job 4371377 ran 23:38Z + 94 min 28 s | Frontier, `.../2026-04-10/_f1112a1f/` | same (20 nodes, `more_iters` CFL 2,3, 120 iters) | Andy | Same failure mode as 2026-04-08 |
| 2026-08-17T20:11Z to 22:28Z | Laptop `MH-DT9TLJQR2V`, qiskit 2.3.1 then 2.5.2 | Manual `./.venv/bin/python nozzle_1d_solver.py ...` into a bus `agent-tmp` dir, copied into results | Andy (+ Claude) | HHL trials: harvester fragments `_0.json` + hand-authored `q8020_{params,experiment,exec_stats,code_provenance}_local.json`, `q8020_env_{before,after}_local.json`. SQLS trial: raw solver output only, zero `q8020_*` files |

### 1a. The Frontier sweeps of April 2026 (`q8020-sweep` + SLURM)

Evidence: the three run directories under
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/`
(`2026-04-05/_52d087d1`, `2026-04-08/_85fd6d17`, `2026-04-10/_f1112a1f`).

**Command line.** Not logged anywhere: `grep -rn 'q8020-sweep\|--set'` over
the sbatch, slurm logs and sweep meta JSON returns nothing; the sweeper does
not record `sys.argv`. It can be reconstructed from the meta file
(`config_file`, `output_dir`), the `cwd` in `q8020_sweep_case_*.json`, and
the fact that only one of the TOML's groups ran each time (group selection is
by positional argument, see 2b). Reconstructed for 2026-04-05:

```
cd /autofs/nccs-svm1_home1/agallojr/proj/src/q8020 && \
q8020-sweep q8020-cfd-metautil/examples/fvm_1d_smoke_test.toml time_steps \
  --set _slurm=true \
  --set _output_dir=/lustre/orion/ard189/proj-shared/agallojr/q8020
```

For 2026-04-08 and 2026-04-10 the TOML was
`q8020-cfd-experiments/input/cases/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`,
the group was `more_iters`, and the cwd was
`/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020` (project area, not
home). The TOML header's own example writes `_output_dir=/lustre/orion/ard189/q8020`,
which is not what was used.

**TOML sections used** (`q8020_fvm_1d_smoke_test.toml`, 2026-04-05):
`[global]` with path variables `_solver_dir = "./fvm_euler_1d_solver"`,
`_metautil_dir`, `_experiment_dir = "./q8020-cfd-experiments"`,
`_postproc_venv = "./.venv"` (an umbrella venv at
`~/proj/src/q8020/.venv` on Frontier; its package list is the
`sweeper_library_versions` block in the meta JSON: Python 3.12.9, qiskit
2.3.1, qiskit-aer 0.17.2, q8020-cfd-metautil 0.1.0, quantum-linear-solvers
0.1.0); SLURM block `_slurm=false` (flipped by `--set`), `_run_mode="parallel"`,
`_slurm_project="ard189"`, `_slurm_partition="batch"`,
`_slurm_walltime="02:00:00"`, `_slurm_exclusive_node=true`,
`_slurm_pack_venvs=["${_solver_dir}/.venv","${_postproc_venv}"]`; the two
command strings

```
_script        = source ${_solver_dir}/.venv/bin/activate && python3 ${_solver_dir}/nozzle_1d_solver.py
_case_postproc = source ${_postproc_venv}/bin/activate && python3 ${_experiment_dir}/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py
_inject_outdir = "-outdir"
```

and global solver params `-nelem 2`, `-time_scheme BDF1`, `-linsolver HHL`,
`-localdt true`, `-noshow true`. Groups: `[ideal]`, `[shots]`, `[bigshots]`,
`[fvm_1d_nelem_5_sv_shots]`, `[time_steps]` (`-cfl = [1, 5, 10, 25, 1e10]`,
`-nelem 5`, `-shots 150000`, `-iters 15`, `-initers 1`, `_trials 10`). The
later `fvm_cfl_sweeps.toml` keeps `[time_steps]` and adds `[more_iters]`
(`-cfl [1,5,10]`, `-iters 60` on 04-08; `-cfl [2,3]`, `-iters 120` on 04-10).

**How `_trials` expanded.** `expand_case_lists` (sweep.py:2212) first takes
the cartesian product of list-valued keys, naming subcases `<group>_<i>`
(`time_steps_0` .. `time_steps_4` for the five CFLs), then replicates each
`_trials` times as `<group>_<i>_trial_<t>` carrying `_trial_index` and
`_parent_case_id`. The case directory is
`run_dir/<parent_case_id>/trial_<t>_<experiment_id>` with an 8-hex
experiment id, e.g. `time_steps_0/trial_0_5066b4fb`. 5 CFL x 10 trials = 50
cases = 50 nodes.

**SLURM settings** (generated `q8020_sweep.sbatch`): `-J q8020_sweep`,
`-A ard189`, `-t 02:00:00`, `-N 50`, `-C nvme`, `-p batch`, `-o/-e` into the
run dir; `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1`;
`sbcast -pf <run_dir>/<venv>.tar.gz /mnt/bb/$USER/venv_{0,1}.tar.gz`, `srun`
untar on every node and `sed` the `VIRTUAL_ENV` line of `bin/activate`; then
one `srun -N 1 -n 1 -c 1 --exclusive python3 -m q8020_cfd_metautil.sweep_worker <case>/pipeline_args.json &`
per case and `wait`. The `pipeline_args.json` command strings were rewritten
by the sweeper from `./fvm_euler_1d_solver/.venv` to `/mnt/bb/agallojr/venv_0`
and from `./.venv` to `/mnt/bb/agallojr/venv_1`. The packed tarballs were
named from the resolved venv path
(`autofs_nccs-svm1_home1_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz`).
The sweeper returned 4 min 30 s after start (00:10:19Z to 00:14:49Z), almost
all of it venv packing; the job started 6 h later and ran 39 min 17 s.

**Output tree layout** (as copied into the results repo; the `2026-04-04`
date directory on Lustre is the sweeper's *local* date, `datetime.now()` at
20:10 EDT, see 2d):

```
/lustre/orion/ard189/proj-shared/agallojr/q8020/<yyyy-mm-dd>/_<8hex>/
  q8020_<config>.toml            copy of the input TOML
  q8020_expanded_cases.json      {"cases": {<case_id>: merged params}, "global": {...}}
  q8020_sweep_meta_<8hex>.json   config_file, run_dir, start/end, sweeper_library_versions, cases{status}
  q8020_sweep.sbatch
  slurm_<job>.out / .err
  <group>_<i>/trial_<n>_<8hex>/
    pipeline_args.json           cmd, case_dir, ids, case_params, case_postproc
    pipeline_result.json         status, returncode, overhead{pre,post,preproc,postproc,harvest}_seconds
    q8020_params_<id>.json       resolved command + solver args          (sweeper)
    q8020_env_before|after_<id>.json                                      (sweeper)
    q8020_stdout|stderr_<id>.txt                                          (sweeper)
    q8020_sweep_{case,code,artifacts,exec_stats,experiment}_<id>_0.json   (sweeper)
    q8020_case_postproc_<id>.json  context handed to _case_postproc
    q8020_postproc_stderr_<id>.txt
    q8020_{case,code,backend,artifacts,results,analysis}_<id>_0.json      (harvester)
    q8020_metadata_<id>.json     rollup of all fragments (harvest_metadata)
    <solver files: dq_*.csv, results_*.csv, final_results_*.csv, residual_*.csv,
     hhl_metrics_*.csv, qc_metadata_*.csv, metadata_*.pkl, system_Ab_*.pkl, solution_plot_*.png>
```

**What the harvester wrote** (trial `5066b4fb`, CFL 1): `q8020_case_*`
(nelem 5, BDF1, cfl 1.0, max_iters 15, conv_tol 1e-10, res_tol 0.01,
localdt, nondim, area equation, reference values), `q8020_code_*`
(`algorithm: HHL`), `q8020_backend_*` (`ideal_statevector`, simulator,
`num_qubits 5`, `nshots 150000`), `q8020_artifacts_*` (20874 bytes:
`transpile_passes[]` per step with before/after depth, qubits, gate count and
generate/transpile/execute wall times; `circuit_timing_total_s`;
`linear_system` sizes 15/16/32 and condition-number range; file inventory),
`q8020_results_*` (51663 bytes: final solution, per-iteration solution and
dq, residual history, LU and HHL solution vectors parsed from stdout),
`q8020_analysis_*` (iterations 15, converged false, fidelity 0.99958,
l2_error_normalized 0.02054, residual 0.02805, residual_reduction 0.041115,
per-step `hhl_metrics[]`). The sweeper's `q8020_sweep_exec_stats_*` gives
start 2026-04-05T06:10:51Z, end 06:29:36Z, `duration_seconds 1125.23`
(this is CFL 1; the August README puts the matched CFL-1e10 trial
`b9da8a4e` at 2354.9 s including postproc, ~1653 s solver). `pipeline_result`
overhead: pre 0.885 s, post 0.508 s, postproc 0.419 s, harvest 0.014 s. The
rollup `q8020_metadata_5066b4fb.json` (124617 bytes) has sections
`case[2] artifacts[2] results[1] analysis[1] backend[1] exec_stats[1]
experiment[1] code[2]` (two `case`/`code`/`artifacts` entries because the
sweeper's `_source: sweep` fragments sit beside the harvester's
`_source: solver` ones).

**The 2026-04-08 and 2026-04-10 failure.** Every case's
`q8020_postproc_stderr_*.txt` reads
`python3: can't open file '/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020/./q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py': [Errno 2] No such file or directory`
and the slurm log shows `Postproc error (code 2)` for all 30 + 20 cases.
The experiments repo had moved the harvester `codes/` -> `src/codes/` in
`26547573` (2026-04-05T19:38:57Z, "cfl results") and again to `input/codes/`
in `30ce6fe6` (2026-04-09T00:11:53Z, the same commit that added
`input/cases/.../fvm_cfl_sweeps.toml`), but the TOML's `_case_postproc` kept
`${_experiment_dir}/codes/...`. Those 50 trial dirs therefore have only
sweeper fragments and raw solver CSVs; the solver-side fragments can still be
regenerated from the CSVs (`q8020_stdout_*.txt` is present, so even the LU/HHL
vectors are recoverable) by re-running the harvester with `--outdir`.

### 1b. The Nov 2025 shot study (solver-native SLURM tooling)

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/`
holds `exact_09899a29/` and `shots_{500,1000,5000,10000,50000,100000,150000}/trial_{0..9}_<8hex>/`
(70 shot trials + 1 exact), a 53-byte `README.md` ("Baseline results from
as-is fvm euler 1d solver"), and the solver's then-current
`requirements.txt` / `requirements-quantum.txt` (qiskit 1.2.4, qiskit-aer
0.15.1, qiskit-algorithms 0.3.1, `quantum_linear_solvers @ git+https://github.com/jw676/...`).
There is no sbatch, no sweep meta, no `pipeline_args.json` anywhere under it
(`find` for `q8020_sweep*`, `pipeline_args.json`, `*.sbatch` is empty). Each
trial has a `run.log` written by the solver; the exact run's log ends
`Completed: 7 steps in 4221.68s` and `Saved metadata to /lustre/orion/ard189/proj-shared/nozzle_1d_results/nelem5/statevector/exact/metadata_nelem5_HHL_statevector.pkl`,
which is the Frontier output root of that campaign.

Those runs used the solver's own SLURM path, added in fvm commit `b7bb0d4c`
(2025-11-11T14:17:28Z, Mohammad Alhawwary, "Add parallel shot studies with
SLURM integration"): `scripts/submit_parallel_shots.sbatch` (`-J qhhl_shots`,
`-A <PROJECT_ID>`, `-t 02:00:00`, `-N 1` or more, `-C nvme`, `-p batch`;
conda-pack archive `$MEMBERWORK/$PROJECT/qiskit_conda_env.tar.gz` sbcast to
NVMe) which runs `scripts/run_shots_parallel.py <RESULTS_DIR> <SOLVER_DIR>`;
that script hard-codes `shot_counts = [0, 1000, 10000, 100000]`,
`n_trials = 5`, `nelem = 5` in source, builds one `srun` per (shots, trial)
via `subprocess.Popen`, and lays out `nelem<N>/statevector/{exact,shots_<s>}/trial_<t>/`
(the same shape the LuGo tree has). Documentation:
`docs/QUICKSTART_PARALLEL.md`, `docs/FRONTIER_CONDA_SETUP.md`, README
section "Parallel Shot Studies". **All of it is still present on `main`
today** (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/scripts/{run_shots.py,run_shots_parallel.py,submit_parallel_shots.sbatch}`,
`utils/list_fake_backends.py`, `docs/{DETAILED_GUIDE,FRONTIER_CONDA_SETUP,QUICKSTART_PARALLEL}.md`;
`git branch --contains b7bb0d4c` = `main`). It captures no metadata of its
own and knows nothing of `-linsolver SQLS` or the `-sqls_*` flags; it is the
older path we are replacing, not deleting.

The `q8020_*` fragments in the Nov tree were produced afterwards on the
laptop: `q8020_experiment_1530692c_0.json` has `_source: harvest`,
`timestamp 2026-02-09T19:52:50Z`, `hostname MH-DT9TLJQR2V` (the
`run_solver_harvester` path of `harvest.py`, which stamps a generic
experiment fragment and then calls `generate_metadata`). Commit `75270106`
(2026-02-09) "fvm results from 2025-11-11" is that import. The harvester's
`_read_stdout` fallback to `run.log` exists precisely for this tree.

### 1c. The LuGo runs (harvest-only mode)

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/harvest_lugo_all.sh`
is the template for ingesting a foreign output tree: it walks
`SRC_ROOT=/ccs/home/agallojr/ard189-lustre/proj-shared/LuGo_rst/output_parallel_shots/nelem{5,10,20}/statevector/{exact,shots_*}/trial_{0..9}`,
copies every file except `*.qpy` into
`DST_ROOT=.../results/fvm_euler_1d_solver/2026-02-26-LuGo/...`, then in one
Python call runs `generate_metadata(dst, write_dir=dst)` from the fvm
harvester and `harvest_metadata(dst, read_only=True)` to write
`q8020_metadata_trial_N.json`. It skips trials that already have
`q8020_results_*.json`. No sweeper is involved, so there is no `params`,
`exec_stats` or environment capture; whatever ORNL's run recorded lives only
in the solver CSVs and pickles. Note it also hard-codes
`HARVESTER_DIR=.../q8020-cfd-experiments/codes/fvm_euler_1d_nozzle`, the
pre-April path, and would fail today with "Harvester not found".

### 1d. The August 2026 local runs (manual, hand-authored provenance)

`results/fvm_euler_1d_solver/2026-08-17-qiskit23-local/` and
`2026-08-17-qiskit25-local/` each hold one `trial_0/` (78 files) and a
README stating the run was manual on the laptop, not a sweep: HHL, nelem 5,
cfl 1e10, 150k shots, 15 outer / 1 inner, 817.7 s (qiskit 2.3.1,
2026-08-17T20:11Z to 20:25Z) and 859.34 s (qiskit 2.5.2, 20:56:07Z to
21:09:25Z). Provenance is in two layers: the fvm harvester invoked with
`--outdir` (fragments `q8020_{case,code,backend,artifacts,results,analysis}_0.json`,
no experiment id in the name), plus hand-authored
`q8020_{params,experiment,exec_stats,code_provenance}_local.json` and
`q8020_env_{before,after}_local.json` with `_source: manual` and a `note`
field, the `_local` suffix standing in for the 8-hex experiment id. The
`.qpy` circuit files (~1.5 GB) were deliberately not copied.

`results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/` (34 files,
pickle timestamp 2026-08-17T22:28:07Z) is the only SQLS run so far and has
**no `q8020_*` files at all** and no README; the write-up lives in
`aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`. What is there:
`metadata_nelem5_SQLS_statevector_nshots150000.pkl` (`linear_solver: SQLS`,
`final_iters 6`, `elapsed_time 0.619 s`, `final_residual 1.26e-9`,
`quantum_circuit: {method: full_svd, k: 128, state_prep: initialize, repeats: 1}`),
`hhl_metrics_nelem5_statevector_shots150000.csv` (SQLS reuses the HHL
metrics filename, `time_solvers.py:435`),
`qc_metadata_sqls_nelem5_full_svd_shots150000.csv` (columns `step, iter,
matrix_size_orig, matrix_size_pow2, condition_number, nnz_per_row, nqubits,
method, k, state_prep, repeats, n_data_qubits, m_ancilla, cx_count,
circuit_depth, aer_device, solve_time`; 7 rows, solve_time 0.075 to
0.103 s, 4 qubits, 200 to 201 CX, depth 397 to 398), `final_results_*`,
`residual_*`, per-iteration `results_*`/`dq_*`, `system_Ab_*.pkl`,
`solution_plot_*.png`. No stdout was kept, so the per-iteration LU/SQLS
comparison table is gone for that trial.

## 2. The sweeper and metautil today

### 2a. Install location and repo state

- Repo: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`, remote
  `Q8020-CFD/q8020-cfd-metautil`. **Checked out on `feature/solverfw-v2`**,
  HEAD `753b97e` (2026-07-26T23:28:56Z, "solverfw v2c: QuantumLinearSystemSolver
  + §9 acceptance sweep"); `main` is `8ccab91` (2026-07-15T18:28:33Z,
  "preserve code"). The feature branch is 4 commits ahead, 0 behind; its
  diff to `main` touches `sweep.py` (+165 lines, additive: registry pruning
  hooks) and `meta_fragment.py` (+69/-6), nothing in `harvest.py`. Branches:
  `main`, `feature/solverfw-v2`, `origin/feature/ishan_testing`. Working tree
  clean.
- Entry points (`pyproject.toml [project.scripts]`): `q8020-sweep` and
  `q8020-sweeper` -> `q8020_cfd_metautil.sweep:main`, `q8020-harvest` ->
  `q8020_cfd_metautil.harvest:main`.
- **Where `q8020-sweep` is installed:** not on `PATH` (`which -a` empty),
  not in `~/.venvs/tooling`, not in the fvm venv, no `~/proj/src/q8020/.venv`
  on this laptop (the April `_postproc_venv = "./.venv"` was a Frontier
  umbrella venv). It exists in three repo venvs, all editable installs of the
  same checkout (`__editable__.q8020_cfd_metautil-0.1.0.pth` ->
  `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src`):
  - `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep` (Python 3.12.10; also `q8020-harvest`, `q8020-sweeper`) -- the one to use
  - `/Users/agallojr/proj/src/q8020/q8020-backend-utils/.venv/bin/q8020-sweep`
  - `/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/.venv/bin/q8020-sweep`

  Because they are editable, all three run whatever branch the checkout is
  on, i.e. `feature/solverfw-v2` right now.
- Layout: `src/q8020_cfd_metautil/{sweep.py (3529 lines), sweep_worker.py,
  sweep_postproc.py, harvest.py (433), meta_fragment.py (459), metakeys.py,
  compare.py, args.py, solverfw/}`; `docs/{experiment_metadata_schema.md,
  llm-metadata-review.md, metapatches.md, SPEC-solverfw.md}`; `examples/`
  holds only `acceptance_sweep.py`. **`examples/fvm_1d_smoke_test.toml`, the
  file the 2026-04-05 run used, was deleted in `46fa917`
  (2026-07-15T16:26:57Z, "refactor, docs")**; `examples/` is empty on
  `origin/main`. The only surviving copy is
  `results/fvm_euler_1d_solver/2026-04-05/_52d087d1/q8020_fvm_1d_smoke_test.toml`.
  The fvm TOMLs now live in the experiments repo under
  `aux/fvm_euler_1d_nozzle/` (`fvm_cfl_sweeps.toml`, `fvm_euler_1d_nozzle.toml`).
- The fvm venv (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv`,
  Python 3.12) has qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime
  0.49.0, `linear_solvers` (the `quantum_linear_solvers` distribution) and
  `sqls` as an editable install (`__editable__.sqls-0.1.0.pth` ->
  `/Users/agallojr/proj/src/q8020/sqls/src`; sqls HEAD `9a4346a`,
  2026-06-30T14:40:52Z). It does not contain metautil, which is fine: the
  harvester runs in `_postproc_venv`.

### 2b. CLI (`sweep.py:3383-3529`)

```
usage: q8020-sweep [-h] [--dry-run] [--set KEY=VALUE] toml_file [groups ...]
```

- `toml_file` -- the config.
- `groups` (positional, zero or more) -- run only these groups. **With no
  group named, every group whose name starts with `_` is skipped**
  (`run_sweep`, sweep.py:2613); the README's `--groups ideal shots` form is
  stale, the flag does not exist.
- `--dry-run` -- see 2d.
- `--set KEY=VALUE` (repeatable) -- override or add a `[global]` key before
  template expansion. Values are coerced `true/false` -> bool, then int, then
  float, else string (sweep.py:2528-2557). A bare key matches an existing
  dashed variant (`--set shots=0` overrides `"-shots"`), and `--set` values
  win over group-level copies of the same key.
- Flow: `load_sweep_config` -> apply overrides -> `_expand_templates`
  (single pass, `${VAR}` from `[global]`, unresolved tokens left as-is) ->
  re-merge globals into cases -> group filter -> run.

### 2c. TOML schema (as implemented in `load_sweep_config`, `expand_case_lists`, `build_command_args`)

- `[global]` (or `[_global]`) plus one section per group; `[stage.*]`
  sections switch to the multi-stage orchestrator instead.
- Keys starting with `_` are sweeper directives and are never passed to the
  solver. Any other key becomes a CLI argument: a key already starting with
  `-` is used verbatim (`"-nelem" = 5` -> `-nelem 5`), otherwise it becomes
  `--key-name`; `true` emits a bare flag, `false` emits nothing; a float
  prints as Python `str()` (`1e10` -> `10000000000.0`, accepted by the solver's
  `type=float`).
- **List values are expanded as a cartesian product** (`itertools.product`
  over all list-valued keys in the group), subcases named `<group>_<i>` in
  product order; `_trials = N` then replicates each subcase as
  `<subcase>_trial_<t>` with `_trial_index`/`_parent_case_id`. Lists inside
  `_` keys (e.g. `_slurm_pack_venvs`, `_case_postproc`) are not expanded.
- Directives seen in `sweep.py`: `_output_dir` (default `./sweep_results`,
  `~` expanded), `_script`, `_env` (venv to activate and snapshot),
  `_run_mode` (`sequential` default | `parallel`), `_case_timeout`,
  `_trials`, `_inject_outdir` / `_inject_experiment_id` /
  `_inject_workflow_id`, `_case_preproc` / `_case_postproc` /
  `_group_postproc` / `_final_postproc` (str or list; each receives a JSON
  context path as last arg; `&&`/`|`/`$(` trigger `bash -c`), `_slurm`,
  `_slurm_interactive`, `_slurm_project`, `_slurm_partition`,
  `_slurm_walltime`, `_slurm_poll_wait`, `_slurm_cores_per_task`,
  `_slurm_exclusive_node`, `_slurm_cores_per_node`, `_slurm_pack_venvs`,
  `_slurm_postproc_job`, `_slurm_postproc_dependency_type`, `_poll_interval`.
  `_set` is not a TOML key; overrides come only from the CLI.
- Any `_`-prefixed key you invent (`_solver_dir`, `_experiment_dir`, ...) is
  legal, ignored by the solver, and usable in `${...}` templates -- that is
  how the April TOML parameterizes paths. Caveat found in the code: template
  expansion is one pass over the original `[global]`, so a variable whose
  value itself contains `${...}` reaches the *global* `_script` unresolved
  (groups get a second expansion and come out right). Keep path variables
  literal.

### 2d. What `--dry-run` does (from code, then verified)

From `sweep.py`: in **sequential** mode the per-case branch prints
`Command: ...` and the dry-run postproc lines, records `status: dry_run`, and
`continue`s before any `mkdir`, `subprocess` or `write` (2823-2918; the
`if not dry_run:` guards cover `date_dir.mkdir`, `run_dir.mkdir`, the TOML
copy, `q8020_expanded_cases.json` and `q8020_sweep_meta*.json`). In
**parallel** mode `_collect_parallel_cases` calls `_build_case_launch_info`,
which has no `dry_run` parameter and unconditionally `mkdir`s each case dir
and writes `pipeline_args.json` (1040-1123); then `_finalize_local_parallel`
returns after printing `Would launch: ...` without `Popen` (1298-1312), and
`_finalize_slurm` writes `q8020_sweep.sbatch`, prints `Would pack:` for each
venv without creating a tarball (`_pack_venvs`, 1456-1461), and returns
`None` before `subprocess.run(["sbatch", ...])` (1890-1893). The only
`subprocess` calls in the file are the solver run, pre/post-proc,
`sbatch`, `sacct` polling and `pip list` for venv snapshots, all behind
non-dry-run paths. Conclusion: `--dry-run` never launches the solver, a
worker, or `sbatch`; in parallel/SLURM mode it does create case directories
and `pipeline_args.json` (and the sbatch file) under `_output_dir`.

Verified 2026-10-15T01:47Z against a copy of
`aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml` at
`/tmp/sweep-check/fvm_cfl_sweeps.toml` with the four path variables made
absolute (`_postproc_venv` -> the metautil venv), using
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`:

| Invocation | Printed | Wrote | Elapsed |
|---|---|---|---|
| `--dry-run --set _output_dir=/tmp/sweep-check/out/parallel` (TOML's `_run_mode="parallel"`) | `Running sweep: 70 cases in 2 groups [parallel]`, 70 x `Prepared: <case> (<id>)`, 70 x `Would launch: python -m q8020_cfd_metautil.sweep_worker .../pipeline_args.json`, `Total: 70 (dry run)` | `/tmp/sweep-check/out/parallel/2026-10-14/_7656cce8/{time_steps_0..4,more_iters_0..1}/trial_<n>_<id>/pipeline_args.json` (70 files) | 0.73 s |
| `... --set _run_mode=sequential` | 70 x `Case:` + `Command: bash -c "source .../fvm_euler_1d_solver/.venv/bin/activate && python3 .../nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir .../time_steps_0/trial_0_<id>"` + `Postproc (dry-run): bash -c "source .../q8020-cfd-metautil/.venv/bin/activate && python3 .../q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py .../q8020_case_postproc_<id>.json"`, `Total: 70 (dry run)` | nothing (`/tmp/sweep-check/out/sequential` does not exist) | 0.14 s |
| `... time_steps --set _slurm=true --set _output_dir=/tmp/sweep-check/out/slurm` | `Running sweep: 50 cases in 1 groups [parallel (slurm)]`, `Would pack: .../fvm_euler_1d_solver/.venv -> .../Users_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz`, same for the metautil venv, `Generated: .../q8020_sweep.sbatch`, `50 cases in one job`, `Total: 50 (dry run)` | `q8020_sweep.sbatch` (`-N 50 -A ard189 -t 02:00:00 -C nvme -p batch`) + 50 case dirs with NVMe-rewritten `pipeline_args.json` (`source /mnt/bb/agallojr/venv_0/bin/activate && ...`); 0 tarballs | 0.21 s |

The expanded case list is the same 70 the April TOML implies: `time_steps`
5 CFL x 10 trials and `more_iters` 2 CFL x 10 trials. The dry-run also shows
the stale postproc path (`.../q8020-cfd-experiments/codes/...`) that the real
runs of 04-08 and 04-10 tripped on. The date directory is the local date
(`2026-10-14` for a 01:47Z run), consistent with April's `2026-04-04` for a
00:10Z submit.

The draft TOML for SQLS (section 3) was given the same treatment in its
default sequential mode: it parses, `_smoke` expands to 1 case, the four
real groups to 145 cases (70 + 50 + 15 + 10), the rendered commands carry
the current harvester path, and nothing was written.

### 2e. `harvest.py` and the fragment schema

- Fragment files match `^q8020_([a-z_]+)_(?:([a-f0-9]{8})_)?(\d+)\.json$`
  (`meta_fragment.FRAGMENT_PATTERN`); sweeper-origin fragments use the
  `q8020_sweep_<section>_<id>_<n>.json` variant. Valid sections
  (`VALID_SECTIONS`): `experiment`, `case`, `code`, `backend`, `artifacts`,
  `exec_stats`, `results`, `analysis`; the first four are conceptually
  singletons, the rest multi. The `q8020_params_<id>.json`,
  `q8020_env_*_<id>.json`, `q8020_case_postproc_<id>.json` files the sweeper
  also writes are side files, not schema sections, and are not rolled up.
- `harvest_metadata(outdir, read_only=False) -> (metadata, warnings, counts)`
  (harvest.py:107) reads all fragments with `read_fragments`, builds
  `{section: [fragment dicts ordered by index]}` for every valid section
  (empty list when absent), and -- unless `read_only=True` -- first writes a
  `results` fragment if `q8020_stdout*.txt` parses as a JSON object (not the
  case for fvm). `run_solver_harvester(outdir, harvester_path, experiment_id,
  write_dir)` loads a harvester module by path, requires it to expose
  `generate_metadata(outdir, experiment_id, write_dir)`, writes a generic
  `experiment` fragment (`_source: harvest`, user, hostname, UTC timestamp)
  and calls it. `q8020-harvest --source DIR [--harvester FILE] [--dest DIR]`
  discovers case dirs recursively (falling back to leaf dirs when a harvester
  is given on a fresh tree) and writes `q8020_metadata_<id>.json` per case.
  Inside a sweep, `run_case_pipeline` (sweep.py:780) calls the same
  `harvest_metadata` after `_case_postproc`, which is where
  `q8020_metadata_<id>.json` in the April trial dirs came from.

### 2f. The solver-specific harvesters and their path drift

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
(21194 bytes, last content change `e55c32a1` 2026-02-24T02:01:49Z) parses, in
the case dir: `metadata_*.pkl` (first match; case params, `linear_solver`,
backend type/method, `nshots`, `quantum_circuit`), `hhl_metrics_*.csv`
(fidelity, L2 errors, linsys residual per step), `qc_metadata_*.csv` (circuit
size/timing per step; first row's `nqubits` -> `backend.num_qubits`),
`final_results_*.csv`, `residual_*.csv`, `results_nelem*_iter*_*.csv` and
`dq_nelem*_iter*_*.csv`, and `q8020_stdout_*.txt` or `run.log` (regex for
`Backend:`/`Shots:` fallback, and the `LU sol ... HHL sol` table for
solution vectors). It inventories all non-`q8020_` files. It writes
`case`, `code` (`algorithm` = pickle `linear_solver`), `backend`,
`artifacts`, `results`, `analysis` via `meta_fragment.write_*` into
`write_dir`. CLI: `--outdir DIR` (manual) or a positional postproc JSON
(sweep mode, reads `case_dir` and `experiment_id`). It imports only stdlib
and `q8020_cfd_metautil.meta_fragment`.

`backend_meta_harvester.py` (2464 bytes, last change `887ba49c`
2026-07-15T16:22:40Z) reads the postproc JSON's `-backend` param, and for a
`fake <name>` backend instantiates it through `q8020_backend_utils.ibm`
(`get_backend`, `make_backend_meta`) to overwrite the thin `backend` fragment
with noise-model detail; with no `-backend` param (ideal statevector, our
case) it prints "skipping" and exits. It needs a venv with
`q8020_backend_utils` and qiskit; the metautil venv alone will not run it.
Not needed for the SQLS protocol.

Path history (`git log --follow`): `codes/fvm_euler_1d_nozzle/` (Feb 2026)
-> `src/codes/fvm_euler_1d_nozzle/` (`26547573`, 2026-04-05T19:38:57Z) ->
`input/codes/fvm_euler_1d_nozzle/` (`30ce6fe6`, 2026-04-09T00:11:53Z) ->
`aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/` (`bd3c7438`,
2026-07-08T20:39:45Z, "reorg for burgers study"). The sweep TOML moved
`input/cases/fvm_euler_1d_nozzle/` -> `aux/fvm_euler_1d_nozzle/` in the same
`bd3c7438`. **Stale references today:** `aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`
and `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml` (`_case_postproc` ->
`.../codes/fvm_euler_1d_nozzle/...`), `harvest_lugo_all.sh`
(`HARVESTER_DIR=.../codes/fvm_euler_1d_nozzle`), and the docstring of
`backend_meta_harvester.py`. The harvester's own code has no path
assumptions, so only the callers are stale. Experiments repo is on `main` at
`6f646617` (2026-09-21T01:37:41Z); the only untracked item is this
`sqls-for-aiaa-4Q26/` folder.

### 2g. Metadata-capture gaps for SQLS (nothing changed; verified by a read-only pass)

Run 2026-10-15T01:46Z: `generate_metadata(<sqls trial_0>, experiment_id='5q15chk0', write_dir=/tmp/sweep-check/harvest-sqls)`
from the metautil venv. It wrote all six fragments and left the source dir
untouched (still 0 `q8020_*` files). What came out, and what would need to
change:

| Fragment | Result on SQLS output | Gap / change needed |
|---|---|---|
| `code` | `{"algorithm": "SQLS"}` | OK. Should also carry `sqls_method`, `sqls_k`, `sqls_state_prep`, `sqls_repeats` (available in the pickle's `quantum_circuit` dict, and in the `-sqls_*` CLI params the sweeper records in `q8020_params`) |
| `case` | nelem 5, BDF1, cfl 1e10, 15/1 iters, tolerances, nondim | OK |
| `backend` | `ideal_statevector`, `num_qubits 4`, `nshots 150000` | OK (`qc_metadata_*.csv` glob matches `qc_metadata_sqls_*.csv`, and `nqubits` is a shared column) |
| `analysis` | 7 iterations, fidelity 0.4510 (the known final-step tail collapse), residual 1.23e-9, `hhl_metrics[]` | Works because SQLS writes `hhl_metrics_*.csv` (`time_solvers.py:435`). Key name `hhl_metrics` is a misnomer for SQLS; `converged` is false because it tests the CFD residual against `conv_tol` while the solver stopped on the `dq` criterion |
| `results` | final solution, 7 per-iteration solution/dq entries, residual history | `lu_reference_vector`/`hhl_solution_vector` absent: no stdout kept for that trial, and `_parse_stdout_lu_solutions` requires `HHL sol` in the header while SQLS prints `LU sol \t SQLS sol L1_diff(%)` (`time_solvers.py:667`), two columns not three. Under the sweeper stdout *will* exist (`q8020_stdout_<id>.txt`), so the parser needs an `SQLS sol` branch |
| `artifacts` | `transpile_passes[*]` all zeros, `circuit_timing_total_s` all 0.0, `linear_system {15, 16, hermitian 0}` with condition range, file inventory | SQLS CSV columns differ from HHL's (`circ_*` vs `cx_count`, `circuit_depth`, `solve_time`, `method`, `k`, `state_prep`, `repeats`, `n_data_qubits`, `m_ancilla`, `aer_device`); `_build_artifacts` silently defaults them to 0. Needs an SQLS branch keyed on the filename (`qc_metadata_sqls_*`) or on the `method` column, mapping `cx_count`/`circuit_depth` -> `after.gate_count`/`after.depth` (`{u3,cx}` basis -- record the basis), `solve_time` -> `wall_time_execute_s`, and surfacing `method/k/state_prep/repeats/n_data_qubits/m_ancilla/aer_device`. `matrix_size_hermitian = 0` is correct (no doubling) and worth stating explicitly |
| `cx_count` / `circuit_depth` | 200 / 398 in the August CSV | Only computed when the solver runs with `-v 2` (`quantum_tools.py:829`, `sqls/runtime/quantum.py:count_cx_depth`); otherwise written as -1. The sweep must pass `-v 2` to SQLS cases, or accept -1 |

Nothing in the sweeper side is SQLS-specific; `params`, `env_*`,
`sweep_exec_stats` etc. will be captured exactly as for HHL. The
hand-authored `_local` fragments of August are not needed under the sweeper.

## 3. Proposed SQLS invocation (not executed)

### 3a. Draft TOML summary

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml`
-- modeled on the April `fvm_cfl_sweeps.toml`, with these deliberate
differences: `_run_mode = "sequential"` by default (laptop-safe; Frontier
sets `--set _run_mode=parallel --set _slurm=true`), path variables are
laptop-absolute literals to be overridden on Frontier, `_case_postproc`
points at the current harvester path under `aux/`, and `-v 2` is set
globally for the circuit metrics with `-v 1` restored in the HHL control.
Global solver params: `-time_scheme BDF1 -localdt -noshow -linsolver SQLS
-sqls_method full_svd -sqls_repeats 1 -sqls_state_prep initialize -v 2`.
Verified by sequential dry-run (section 2d): the rendered `_smoke` command is

```
bash -c "source /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/activate && python3 /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py -time_scheme BDF1 -localdt -noshow -linsolver SQLS -sqls_method full_svd -sqls_repeats 1 -sqls_state_prep initialize -v 2 -nelem 2 -iters 2 -initers 1 -cfl 10000000000.0 -shots 0 -outdir <run_dir>/<id>"
```

| Group | Overrides | Cases | Purpose |
|---|---|---|---|
| `_smoke` (must be named) | `-nelem 2 -iters 2 -initers 1 -cfl 1e10 -shots 0` | 1 | Prove the chain: solver, harvester, rollup. ~1-2 s solver |
| `sqls_shots` | `-nelem 5 -cfl 1e10 -iters 15 -initers 1 -shots [0,1000,5000,10000,50000,100000,150000]`, `_trials 10` | 70 | Shot sweep incl. exact statevector |
| `sqls_cfl` | `-nelem 5 -cfl [1,5,10,25,1e10] -iters 15 -initers 1 -shots 150000`, `_trials 10` | 50 | Matches April `time_steps` for HHL |
| `sqls_nelem` | `-nelem [5,11,21,42,85] -cfl 1e10 -iters 15 -initers 1 -shots 150000`, `_trials 3` | 15 | Mesh scaling; padded N = 16, 64, 64, 128, 256 (4..8 qubits), vs HHL 32..512 |
| `hhl_matched` | `-linsolver HHL -v 1 -nelem 5 -cfl 1e10 -iters 15 -initers 1 -shots 150000`, `_trials 10` | 10 | Same-stack HHL control (qiskit 2.5.2) |

Total 145 cases plus the smoke. `_trials = 3` for `sqls_nelem` because the
quantities that group measures (qubits, CX count, depth, solve time, exact
accuracy) are deterministic in N; 3 trials bound the fixed-150k-shot spread
and keep the three nelem-85 cases (the only slow ones) to a handful. Raise to
10 if the paper's scaling plot needs shot-noise error bars (open question 1).
Nit visible in the dry-run: the `-sqls_*` flags are inherited by the HHL
control command; the solver's argparse accepts and ignores them, but they
will appear in `q8020_params` for those cases. Move them into the three SQLS
groups if that bothers the record.

### 3b. Procedure (i): laptop smoke via `q8020-sweep`, sequential

Every step below that runs the solver needs Andy's go-ahead; the dry-runs do
not.

1. Dry-run the smoke group (writes nothing in sequential mode):
   ```
   cd /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26
   /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml _smoke --dry-run
   ```
2. **[needs approval]** Run it (~5 s wall including harvester and rollup):
   ```
   /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml _smoke
   ```
   Output lands in `~/q8020/<yyyy-mm-dd>/_<8hex>/<8hex>/` (no trial nesting
   for a single case). Check `pipeline_result.json` status `success`,
   `q8020_postproc_stderr_<id>.txt` reads `Metadata fragments written to`,
   and that `q8020_{case,code,backend,artifacts,results,analysis}_<id>_0.json`
   and `q8020_metadata_<id>.json` exist beside `qc_metadata_sqls_nelem2_full_svd.csv`.
3. **[needs approval, optional]** A laptop pass of the cheap SQLS groups is
   feasible: `sqls_shots` 70 cases at ~3 s (0.6-1.5 s solver + ~1.5 s
   sweeper/harvester overhead) is ~4 min; `sqls_cfl` 50 cases ~3-4 min;
   `sqls_nelem` 15 cases ~0.5-1 h, dominated by nelem 85. Command, one group
   at a time so a problem stops early:
   ```
   /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml sqls_shots
   ```
   Do not run `hhl_matched` on the laptop (10 x ~860 s = 2.4 h sequential).

### 3c. Procedure (ii): Frontier via `--set _slurm=true`

Preconditions first (3d). Then, from the Frontier directory that holds the
four repos (April used `/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020`;
confirm with `pwd -P`), with the metautil venv's `q8020-sweep` on PATH or
called by absolute path:

1. Dry-run with the Frontier overrides. In parallel/SLURM mode this *does*
   create the run dir, case dirs, `pipeline_args.json` and
   `q8020_sweep.sbatch` under `_output_dir` (and nothing else; no tarball,
   no `sbatch`). Point it at a scratch root so the real tree stays clean:
   ```
   q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml sqls_shots sqls_cfl sqls_nelem --dry-run \
     --set _slurm=true --set _run_mode=parallel \
     --set _output_dir=/lustre/orion/ard189/proj-shared/agallojr/q8020-dryrun \
     --set _solver_dir=$PWD/fvm_euler_1d_solver \
     --set _metautil_dir=$PWD/q8020-cfd-metautil \
     --set _experiment_dir=$PWD/q8020-cfd-experiments \
     --set _postproc_venv=$PWD/q8020-cfd-metautil/.venv
   ```
   Read the generated `q8020_sweep.sbatch` (node count = 135, `-A ard189`,
   `-p batch`, `-t 02:00:00`, two `sbcast` blocks) and one `pipeline_args.json`.
2. **[needs approval]** Submit the SQLS groups as one job. Same command
   without `--dry-run`, `_output_dir=/lustre/orion/ard189/proj-shared/agallojr/q8020`
   (the April root), and a shorter walltime since every case is seconds to
   minutes:
   ```
   q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml sqls_shots sqls_cfl sqls_nelem \
     --set _slurm=true --set _run_mode=parallel --set _slurm_walltime=00:30:00 \
     --set _output_dir=/lustre/orion/ard189/proj-shared/agallojr/q8020 \
     --set _solver_dir=$PWD/fvm_euler_1d_solver --set _metautil_dir=$PWD/q8020-cfd-metautil \
     --set _experiment_dir=$PWD/q8020-cfd-experiments --set _postproc_venv=$PWD/q8020-cfd-metautil/.venv
   ```
   The sweeper packs the two venvs (minutes; April took ~4 min), writes
   `q8020_expanded_cases.json`, `q8020_<toml>.toml`, `q8020_sweep.sbatch`,
   submits, records `slurm_job_id` in `q8020_sweep_meta_<id>.json` and
   returns. 135 exclusive nodes for seconds-long cases is wasteful; the
   README documents packed mode (`--set _slurm_exclusive_node=false
   --set _slurm_cores_per_task=4`, 64 cores/node -> ~9 nodes), untested here
   (open question 7).
3. **[needs approval]** Submit the HHL control separately, so its ~20-40 min
   cases do not hold the SQLS nodes:
   ```
   q8020-sweep fvm_sqls_aiaa_sweeps.DRAFT.toml hhl_matched \
     --set _slurm=true --set _run_mode=parallel --set _slurm_walltime=02:00:00 \
     --set _output_dir=/lustre/orion/ard189/proj-shared/agallojr/q8020 \
     (same four path overrides)
   ```
4. Monitor with `squeue -u agallojr` / `sacct -j <job>`; when done, check
   `slurm_<job>.out` for `Postproc completed` on every case (April 04-08
   and 04-10 showed `Postproc error (code 2)` -- that is the signal the
   harvester path is wrong) and `grep -L '"status": "success"' */trial_*/pipeline_result.json`.

### 3d. What has to be true on Frontier first

- fvm checkout at `main` `ef7f0a8b` (or later) with a `.venv` built **on
  Frontier** from `pyproject.toml`/`uv.lock` (Python 3.12, qiskit 2.5.2,
  qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0, `quantum_linear_solvers` from
  `git+https://github.com/Q8020-CFD/quantum_linear_solvers`), plus
  `pip install -e <sqls checkout> --no-deps` as the pyproject comment
  prescribes (sqls pins qiskit 2.1.2 in its own pyproject; `--no-deps`
  against 2.5.2 is the verified route). The ORNL URL
  `https://code.ornl.gov/olcf-qcfd/sqls.git` returned HTTP 504 on 2026-10-14,
  so plan on copying the laptop clone (`/Users/agallojr/proj/src/q8020/sqls`,
  HEAD `9a4346a`, clean) or a `git bundle` rather than cloning
  non-interactively. Verify on a login node:
  `.venv/bin/python -c "import sqls, linear_solvers, qiskit; print(qiskit.__version__)"`.
- A metautil venv on Frontier (April's was the umbrella `~/proj/src/q8020/.venv`)
  with `q8020-cfd-metautil` installed editable from a checkout at the branch
  Andy picks (`main` `8ccab91` or `feature/solverfw-v2` `753b97e`; the
  sweeper code paths used here are identical on both) and `subprocess_tee`.
  This venv runs `q8020-sweep` and is `_postproc_venv` for the harvester.
  Both venvs get tarred and `sbcast` to NVMe, so they must be real
  directories, not symlinks to another filesystem.
- The experiments repo checked out at `main` `6f646617` or later so
  `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
  exists at the path the TOML uses; the draft TOML itself is untracked and
  must be copied over (or committed first).
- `/lustre/orion/ard189/proj-shared/agallojr/q8020` writable; Lustre is
  purged, so copy back promptly.

### 3e. Harvest and copy back

Per-case harvesting and the `q8020_metadata_<id>.json` rollup happen inside
the job (`sweep_worker` -> `run_case_pipeline` -> `_case_postproc` ->
`harvest_metadata`), so nothing further is required when `Postproc completed`
is seen. If any case shows a postproc error, re-run the harvester in place
without touching anything else:
`<metautil venv>/bin/python <experiments>/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py <case_dir>/q8020_case_postproc_<id>.json`
then `q8020-harvest --source <case_dir>` to rebuild the rollup. Copy back
mirroring the April layout, excluding circuit dumps:

```
rsync -av --exclude '*.qpy' \
  frontier:/lustre/orion/ard189/proj-shared/agallojr/q8020/<yyyy-mm-dd>/_<8hex>/ \
  /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/<yyyy-mm-dd>-sqls-frontier/_<8hex>/
```

so the results dir holds `q8020_fvm_sqls_aiaa_sweeps.DRAFT.toml`,
`q8020_expanded_cases.json`, `q8020_sweep_meta_<id>.json`, `q8020_sweep.sbatch`,
`slurm_<job>.{out,err}` and `<group>_<i>/trial_<n>_<id>/` exactly as
`2026-04-05/_52d087d1` does, one `_<8hex>` per submission (SQLS groups, HHL
control). Add a `README.md` in the August style (host, UTC window, solver
SHA, stack, caveats). SQLS writes no `.qpy`; HHL does, and April kept none.

### 3f. Cost estimates (units on everything)

| Case type | Solver elapsed | Basis | Group total |
|---|---|---|---|
| SQLS full_svd, nelem 5, 150k shots, CFL 1e10 | 0.62 s (6 Newton iters, laptop); ~1.5 s if all 15 iters run | August trial pickle `elapsed_time`; per-solve 0.075-0.103 s from `qc_metadata_sqls` | `sqls_shots` 70 cases: ~4 min laptop sequential incl. ~1.5 s/case sweeper+harvester overhead (April overhead 0.885 + 0.508 + 0.419 s) |
| SQLS, nelem 5, CFL 1 to 25 | 1-2 s (CFL 1 does not converge in 15 iters for HHL; expect the full 15 for SQLS too) | same | `sqls_cfl` 50 cases: ~3-4 min laptop |
| SQLS, nelem 11/21 (N = 64, 6 qubits) | seconds per case | QSD synthesis ~(23/48)*4^6 ~ 1.9k CX per unitary | small |
| SQLS, nelem 42 (N = 128, 7 qubits) | ~0.5-2 min per case | ~7.8k CX per unitary; `-v 2` adds a `{u3,cx}` transpile per step | small |
| SQLS, nelem 85 (N = 256, 8 qubits) | ~5-15 min per case (estimate) | dense SVD of 256x256 ~10 ms; two 8-qubit `UnitaryGate`s -> QSD ~31k CX each (~60k total, vs 200 at 4 qubits); Aer statevector of ~9 qubits x 60k gates ~1 s; synthesis + the `-v 2` count transpile dominate at tens of seconds per Newton step x 15 steps | `sqls_nelem` 15 cases (3 trials): ~0.5-1 h laptop, ~15 min wall on Frontier (one node each). Feasible. Expect accuracy, not cost, to be the story: 150k shots over 256 basis states is ~586 counts per amplitude, so the shot-reconstruction error grows with N; the `-shots 0` exact run separates the two effects (open question 12) |
| HHL, nelem 5, 150k shots, CFL 1e10 | 859 s laptop (qiskit 2.5.2); 1125 s (CFL 1) to ~1653 s (CFL 1e10) Frontier node | August README; April `sweep_exec_stats` | `hhl_matched` 10 cases: 2.4 h laptop sequential (not advised); ~20-40 min wall on 10 Frontier nodes |

Memory is trivial throughout (largest dense object is 512x512 complex for
HHL at nelem 5; 256x256 for SQLS at nelem 85). HHL at nelem 85 would be
~18-20 qubits with QPE and is not proposed.

### 3g. Open questions for Andy

1. `sqls_nelem` trials: 3 (draft) or 10 for protocol uniformity / error bars?
2. Include `-sqls_method truncated_mps` (and `truncated_qr`, with a `-sqls_k`
   sweep) now, or defer per qtsuite #54? Adding a `[sqls_mps]` group is a
   few lines; the harvester gap in 2g applies equally.
3. HHL control: re-run on qiskit 2.5.2 (`hhl_matched`, ~10 node-hours) so
   the comparison is same-stack, or reuse April 2026 (qiskit 2.3.1,
   `2026-04-05/_52d087d1/time_steps_4`)? The August 2.3-vs-2.5 pair showed
   transpile 3.7x slower, depth -6.5 %, quality unchanged.
4. Which metautil branch runs the sweep: `main` `8ccab91` or the laptop's
   `feature/solverfw-v2` `753b97e`? The sweep code paths exercised here are
   identical; the branch is recorded only indirectly (via
   `sweeper_library_versions`), so pick one and note it in the README.
5. Patch the fvm harvester for SQLS (artifacts columns, `SQLS sol` stdout
   table, `sqls_*` params into `code`) before the runs, or run as-is and
   re-harvest later? Fragments are fully regenerable from the kept CSVs and
   `q8020_stdout_<id>.txt`, so re-harvesting is safe; the metapatches
   mechanism is the other route.
6. Fix the stale `codes/` path in `aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`,
   `fvm_euler_1d_nozzle.toml` and `harvest_lugo_all.sh` (durable change,
   not done here), and restore a `fvm_1d_smoke_test.toml` example somewhere
   tracked?
7. Exclusive node per case (April, draft default) vs packed mode for the
   seconds-long SQLS cases (`--set _slurm_exclusive_node=false`)? Packed mode
   with `_slurm_pack_venvs` is in the sweeper but untested by us.
8. Keep `-v 2` at nelem 85? It is the only way to get `cx_count`/`depth`,
   but verbosity 2 also prints matrices to stdout (255x255 per Newton step,
   a few MB per case) and adds a `{u3,cx}` transpile per step.
9. Output root on Frontier (`/lustre/orion/ard189/proj-shared/agallojr/q8020`
   as in April?) and who copies back before purge.
10. The `-cfl 1e10, -shots 150000` cell appears in both `sqls_shots` and
    `sqls_cfl` (20 trials in total). Accept, or drop it from one group?
11. Does `hhl_matched` need `-hhl_scale`/other HHL flags beyond April's, or
    is the April command line the exact control?
12. Add `-shots 0` to `sqls_nelem` (doubling it to 30 cases at 3 trials) so
    mesh-scaling error can be split into discretization vs sampling?

## Sources

Results and artifacts (read-only):
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-05/_52d087d1/` -- `q8020_fvm_1d_smoke_test.toml`, `q8020_sweep.sbatch`, `q8020_sweep_meta_52d087d1.json`, `q8020_expanded_cases.json`, `slurm_4336936.{out,err}`, `time_steps_0/trial_0_5066b4fb/*`
- `.../2026-04-08/_85fd6d17/` -- `q8020_fvm_cfl_sweeps.toml`, `q8020_sweep_meta_85fd6d17.json`, `slurm_4355227.{out,err}`, `more_iters_0/trial_0_40373d9d/q8020_postproc_stderr_40373d9d.txt`
- `.../2026-04-10/_f1112a1f/` -- `q8020_fvm_cfl_sweeps.toml`, `q8020_sweep_meta_f1112a1f.json`, `q8020_sweep.sbatch`, `slurm_4371377.{out,err}`, `more_iters_0/trial_0_5c9bff98/*`
- `.../2025-11-11/` -- `README.md`, `requirements.txt`, `requirements-quantum.txt`, `exact_09899a29/run.log`, `shots_1000/trial_0_1530692c/*`
- `.../2026-08-17-qiskit23-local/README.md`, `.../2026-08-17-qiskit25-local/{README.md,trial_0/q8020_*_local.json}`, `.../2026-08-17-sqls-local-v2/trial_0/*`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/{fvm_cfl_sweeps.toml,fvm_euler_1d_nozzle.toml}`, `.../fvm_euler_1d_nozzle/{fvm_euler_1d_solver_harvester.py,backend_meta_harvester.py,harvest_lugo_all.sh}`, `.../sqls-vs-hhl-2026-08-17/README.md`, `.../sqls-for-aiaa-4Q26/WORKPLAN.md`
- `git log --follow` / `git show --name-status` in `q8020-cfd-experiments` for commits `e2b90872`, `e55c32a1`, `26547573`, `30ce6fe6`, `119cc94f`, `bd3c7438`, `887ba49c`, `6f646617`

Code (read-only):
- `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/` -- `README.md`, `pyproject.toml`, `src/q8020_cfd_metautil/{sweep.py,harvest.py,meta_fragment.py,sweep_worker.py,sweep_postproc.py}`, `git branch -a`, `git log`, `git diff --stat main...HEAD`, `git ls-tree origin/main examples/`
- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/` -- `nozzle_1d_solver.py` (argparse lines 53-147, metadata pickle 338-371), `time_solvers.py` (370-460, 667), `quantum_tools.py` (665-680, 829-897), `pyproject.toml`, `README.md`, `scripts/{run_shots_parallel.py,submit_parallel_shots.sbatch}`, `docs/QUICKSTART_PARALLEL.md`, `git show --stat b7bb0d4c`, `.venv` package probe
- `/Users/agallojr/proj/src/q8020/sqls/` -- `git log -1`, `pyproject.toml`, `src/sqls/runtime/quantum.py` (count_cx_depth)
- Venv probes: `which -a q8020-sweep`, `ls ~/.venvs/*/bin/q8020-sweep`, `ls /Users/agallojr/proj/src/q8020/*/.venv/bin/q8020-sweep`, `__editable__*.pth` files

Scratch produced by this task (disposable):
- `/tmp/sweep-check/fvm_cfl_sweeps.toml` (absolute-path copy), `/tmp/sweep-check/out/{parallel,slurm}/2026-10-14/_*` (dry-run artifacts), `/tmp/sweep-check/harvest-sqls/q8020_*_5q15chk0_0.json` (read-only harvester pass over the August SQLS trial)
