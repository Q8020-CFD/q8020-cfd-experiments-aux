VERDICT: PASS

# Verify item 14 rebase: q8020-cfd-metautil main (9ce8669) onto origin/main (d75de45)

- Verifier: independent, read-only, adversarial.
- Repo: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`
- Window: 2026-10-16T01:18:26Z to 2026-10-16T01:23:30Z (about 5 min wall time).
- Python: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python`; all sweeper
  invocations were `--dry-run` or `--dry-run-materialize`, cwd `/Users/agallojr/proj/src/q8020`,
  with `--set _output_dir=/tmp/verify-metautil-rebase/<name>` and
  `--set _postproc_venv=./q8020-cfd-metautil/.venv`. No sweep or solver launched. Nothing
  written under `~/q8020` (verified with `find -newer <marker>` after every run). Scratch dir
  `/tmp/verify-metautil-rebase` deleted at the end.
- ANSI color codes are stripped from quoted sweeper output below.

## Check 1: git state -- PASS

```
$ git log --oneline origin/main..main
9ce8669 Sweeper housekeeping: record the invocation, write nothing on dry-run, UTC date dir, venv fallback on dry-run only, fix harvester paths in the fvm examples

$ git rev-parse --short origin/main; git rev-parse --short main; git rev-parse --short feature/solverfw-v2
d75de45
9ce8669
753b97e

$ git diff --stat origin/main..main
 README.md                                | 125 +++++++-
 src/q8020_cfd_metautil/sweep.py          | 492 +++++++++++++++++++++++++------
 tests/examples/base_case.toml            |   2 +-
 tests/examples/base_case_hhl.toml        |   2 +-
 tests/examples/fvm_1d_smoke_test.toml    |   2 +-
 tests/examples/hhl_time_step_impact.toml |   2 +-
 tests/test_sweep_launcher_env.py         |  31 +-
 7 files changed, 539 insertions(+), 117 deletions(-)

$ git status --porcelain
(empty: working tree clean)

$ git branch --show-current
main

$ git diff --stat origin/main..main -- src/q8020_cfd_metautil/solverfw/
(empty)

$ git rev-parse main:src/q8020_cfd_metautil/solverfw origin/main:src/q8020_cfd_metautil/solverfw
42dc8b4a6249c1d54a634051cc03b668a7062738
42dc8b4a6249c1d54a634051cc03b668a7062738

$ git log --oneline -6 origin/main
d75de45 updating help text to specify backend can take noise model file
a1b2749 feat: portable sweep TOMLs -- synthesized srun launcher, _env_exports, recursive templates
cdf4bbb fix for multi-rank cases landing on same node
85c2220 adding distributed MPI capability
8ccab91 preserve code
3857025 remove unused import
```

Findings: exactly one commit ahead; the seven touched files are exactly the allowed set; tree
clean; `feature/solverfw-v2` at 753b97e; `solverfw/` tree hash identical on both sides (the
directory exists and has 9 modules, so the empty diff is not vacuous).

## Check 2: full test suite, both sides -- PASS (43 / 43 each)

```
$ cd /Users/agallojr/proj/src/q8020/q8020-cfd-metautil && .venv/bin/python -m pytest -q -p no:cacheprovider tests
...........................................                              [100%]
43 passed in 3.74s
```

Upstream (origin/main) extracted with `git archive origin/main | tar -x -C
/tmp/verify-metautil-rebase/upstream`, run in-process so the module path is provable:

```
$ cd /tmp/verify-metautil-rebase/upstream && PYTHONPATH=/tmp/verify-metautil-rebase/upstream/src \
  /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python -c "
import sys, pytest
import q8020_cfd_metautil.sweep as s
print('sweep module:', s.__file__)
print('has dry_run_materialize param:', 'dry_run_materialize' in s.run_sweep.__code__.co_varnames)
rc = pytest.main(['-q', '-p', 'no:cacheprovider', 'tests'])
print('pytest rc =', rc)"
sweep module: /tmp/verify-metautil-rebase/upstream/src/q8020_cfd_metautil/sweep.py
has dry_run_materialize param: False
...........................................                              [100%]
43 passed in 2.83s
pytest rc = 0
```

Per-file collection on main: test_sbatch_mpi_cases.py 12, test_slurm_postproc.py 12,
test_sweep_launcher_env.py 11, test_template_expansion.py 8 (sum 43). Note: `python -I`
ignores `PYTHONPATH`, so the editable install resolves instead; the run above deliberately
did not use `-I`, and the printed module path plus the absent `dry_run_materialize` parameter
prove the upstream tree was the one under test.

## Check 3: adapted upstream test -- PASS

`git diff origin/main..main -- tests/test_sweep_launcher_env.py` (31 lines changed) contains
only:

1. Docstring: "Driven through `run_sweep(dry_run=True)`: even in dry-run the sweeper writes
   per-case pipeline_args.json ..." becomes "Driven through
   `run_sweep(dry_run=True, dry_run_materialize=True)`: a materialized dry run writes
   per-case pipeline_args.json ... (a plain dry run writes nothing)."
2. New constant: `_MATERIALIZE = {"dry_run": True, "dry_run_materialize": True}` with a
   one-line comment.
3. Eleven call sites: `run_sweep(str(toml), None, dry_run=True)` -> `run_sweep(str(toml),
   None, **_MATERIALIZE)` (the `overrides={"_script": ...}` call keeps its extra kwarg).

No assertion line is touched (every `assert` in the diff is context, not +/-).

Judgement: preserved. The test helper `_pipeline_cmds` reads each case's `pipeline_args.json`
from disk, which a plain dry run no longer writes by design, so `dry_run_materialize=True` is
the minimal correct adaptation. In `sweep.py`, `write_files=(not dry_run) or materialize`
gates only `case_dir.mkdir` and the `json.dump` of pipeline_args in `_build_case_launch_info`
(and the sbatch write / NVMe rewrite-to-file in `_finalize_slurm`); the command construction
(synthesized srun, `_script` merge, `_env_exports`, `${_launch}` template) is shared and
unchanged. The upstream intent -- assert the exact launcher command the compute node would
run -- is what the materialized dry run still exercises. All 11 tests pass.

## Check 4: upstream features intact (all_directives_reference.toml) -- PASS

Local mode:

```
$ ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/all_directives_reference.toml --dry-run \
  --set _output_dir=/tmp/verify-metautil-rebase/c4-local --set _postproc_venv=./q8020-cfd-metautil/.venv
Running sweep: 36 cases in 6 groups [sequential]
Output directory: /tmp/verify-metautil-rebase/c4-local/2026-10-16/_45849229
Invocation: ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/all_directives_reference.toml --dry-run --set _output_dir=/tmp/verify-metautil-rebase/c4-local --set _postproc_venv=./q8020-cfd-metautil/.venv
Env export: Q8020_DEMO_VAR=1

=== Group: ideal (1 cases) ===
  Case: ideal
    Command: bash -c "source /Users/agallojr/proj/src/q8020/.venv/bin/activate && python3 examples/smoke_test_solver.py -time_scheme BDF1 -localdt -noshow -nelem 5 -outdir /tmp/verify-metautil-rebase/c4-local/2026-10-16/_45849229/61412a9b -exp 61412a9b -wf _45849229"
  ...
=== Summary ===
Total: 36 (dry run)
exit=0
```

Counts: `Env export:` lines 1; `Case:` lines 36; `Command:` lines 36.

SLURM mode (`--set _slurm=true --set _run_mode=parallel --set _slurm_tasks_per_case=16`):

```
Running sweep: 36 cases in 6 groups [parallel (slurm)]
Output directory: /tmp/verify-metautil-rebase/c4-slurm/2026-10-16/_9c58c513
    Command: bash -c "source /Users/agallojr/proj/src/q8020/.venv/bin/activate && srun -N 2 -n 16 --ntasks-per-node=8 --exclusive python3 examples/smoke_test_solver.py -time_scheme BDF1 -localdt -noshow -nelem 5 -outdir /tmp/verify-metautil-rebase/c4-slurm/2026-10-16/_9c58c513/a6f93bf4 -exp a6f93bf4 -wf _9c58c513"
  ... (36 such lines)
Would generate: /tmp/verify-metautil-rebase/c4-slurm/2026-10-16/_9c58c513/q8020_sweep.sbatch
  #SBATCH -J q8020_sweep
  #SBATCH -A ard189
  #SBATCH -t 00:30:00
  #SBATCH -N 2
  #SBATCH -C nvme
  #SBATCH -p batch
  #SBATCH -o /tmp/verify-metautil-rebase/c4-slurm/2026-10-16/_9c58c513/slurm_%j.out
  #SBATCH -e /tmp/verify-metautil-rebase/c4-slurm/2026-10-16/_9c58c513/slurm_%j.err
  export Q8020_DEMO_VAR="1"  (_env_exports)
36 cases in one job
Total: 36 (dry run)
exit=0
```

`grep -c 'srun -N 2 -n 16 --ntasks-per-node=8'` = 36 (every command). `#SBATCH -N 2` and
`export Q8020_DEMO_VAR="1"` present.

Files written: none. `ls -la /tmp/verify-metautil-rebase/` after both runs showed only
`.marker-c4` and `upstream/` (no `c4-local`, no `c4-slurm`); `find
/Users/agallojr/proj/src/q8020 -name .git -prune -o -type f -newer .marker-c4 -print` and the
same under `/Users/agallojr/q8020` returned nothing.

## Check 5: item-14 features intact -- PASS

### 5a. CFL TOML, local dry-run (70 cases, zero files)

```
$ ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run \
  --set _output_dir=/tmp/verify-metautil-rebase/c5-cfl-local --set _postproc_venv=./q8020-cfd-metautil/.venv
Running sweep: 70 cases in 2 groups [parallel]
Output directory: /tmp/verify-metautil-rebase/c5-cfl-local/2026-10-16/_5e52bf64
=== Group: time_steps (50 cases) ===
  Prepared: time_steps_0_trial_0 (cab592bf)
    Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/verify-metautil-rebase/c5-cfl-local/2026-10-16/_5e52bf64/time_steps_0/trial_0_cab592bf"
  Postproc (dry-run): bash -c "source ./q8020-cfd-metautil/.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/verify-metautil-rebase/c5-cfl-local/2026-10-16/_5e52bf64/time_steps_0/trial_0_cab592bf/q8020_case_postproc_cab592bf.json"
  ...
=== Group: more_iters (20 cases) ===
  ...
  Would launch: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python3 -m q8020_cfd_metautil.sweep_worker .../more_iters_1/trial_9_0c881749/pipeline_args.json (file written only with --dry-run-materialize)
=== Summary ===
Total: 70 (dry run)
exit=0
```

Counts: `^ *Command:` 70; `^ *Postproc (dry-run):` 70; indented variants (`^[[:space:]]+`)
70 and 70; `/mnt/bb` 0 (local mode, as expected). Output file 292 lines.

### 5b. CFL TOML, `--set _slurm=true` dry-run (all 70 commands carry /mnt/bb)

```
Running sweep: 70 cases in 2 groups [parallel (slurm)]
Output directory: /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147
  Prepared: time_steps_0_trial_0 (72e982ca)
  ... (70 Prepared lines)
  Would pack: /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv -> /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/Users_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz
  Would pack: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv -> /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/Users_agallojr_proj_src_q8020_q8020-cfd-metautil_.venv.tar.gz
  Commands after NVMe venv rewrite:
    Command: bash -c "source /mnt/bb/agallojr/venv_0/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/time_steps_0/trial_0_72e982ca"
  Postproc (dry-run): bash -c "source /mnt/bb/agallojr/venv_1/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/time_steps_0/trial_0_72e982ca/q8020_case_postproc_72e982ca.json"
  ...
Would generate: /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/q8020_sweep.sbatch
  #SBATCH -J q8020_sweep
  #SBATCH -A ard189
  #SBATCH -t 02:00:00
  #SBATCH -N 70
  #SBATCH -C nvme
  #SBATCH -p batch
  #SBATCH -o /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/slurm_%j.out
  #SBATCH -e /tmp/verify-metautil-rebase/c5-cfl-slurm/2026-10-16/_24bf0147/slurm_%j.err
70 cases in one job
Total: 70 (dry run)
exit=0
```

Counts: `Command:` 70, of which with `/mnt/bb` 70 (without: 0); `Postproc` 70, with `/mnt/bb`
70. The TOML sets `_slurm_pack_venvs = ["${_solver_dir}/.venv", "${_postproc_venv}"]`, so
the post-NVMe-rewrite display path (`_slurm_will_rewrite` -> deferred printing in
`_finalize_slurm`) was exercised. No tarball was packed (`Would pack:` only).

### 5c. Smoke TOML dry-run (66 cases, zero files)

```
$ ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml --dry-run \
  --set _output_dir=/tmp/verify-metautil-rebase/c5-smoke --set _postproc_venv=./q8020-cfd-metautil/.venv
Running sweep: 66 cases in 5 groups [parallel]
Output directory: /tmp/verify-metautil-rebase/c5-smoke/2026-10-16/_71e20ad2
=== Group: ideal (1 cases) ===
=== Group: shots (1 cases) ===
=== Group: bigshots (4 cases) ===
=== Group: fvm_1d_nelem_5_sv_shots (10 cases) ===
=== Group: time_steps (50 cases) ===
Total: 66 (dry run)
exit=0
```

Counts: `Command:` 66; `Postproc` 66. Every postproc line uses the corrected harvester path
`./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`,
which exists (`-rw-r--r-- 40115 bytes`); the old `codes/fvm_euler_1d_nozzle/...` path does
not exist on disk.

Files written by 5a/5b/5c: none. After all three, `ls -la /tmp/verify-metautil-rebase/`
contained only the marker files, my captured `*.out` logs, `upstream/` and (from 5d) `c5-mat/`;
no `c5-cfl-local`, `c5-cfl-slurm` or `c5-smoke` directory. `find -newer` under
`/Users/agallojr/proj/src/q8020` and `/Users/agallojr/q8020` returned nothing.

### 5d. `--dry-run-materialize` of multi_stage_local.toml (exactly one invocation record)

```
$ ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/multi_stage_local.toml --dry-run-materialize \
  --set _output_dir=/tmp/verify-metautil-rebase/c5-mat --set _postproc_venv=./q8020-cfd-metautil/.venv
Multi-stage sweep: 2 stages
Output directory: /tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697
Invocation: ./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/multi_stage_local.toml --dry-run-materialize --set _output_dir=/tmp/verify-metautil-rebase/c5-mat --set _postproc_venv=./q8020-cfd-metautil/.venv
  Stage 1: coarse (1 cases)
  Stage 2: fine (1 cases)
Stage: coarse
Running sweep: 1 cases in 1 groups [sequential]
Output directory: /tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/coarse
    Command: python fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -linsolver LU -iters 4 -initers 1 -localdt -noshow -outdir /tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/coarse/77766535
Stage: fine
Running sweep: 1 cases in 1 groups [sequential]
Output directory: /tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/fine
    Command: python fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 10 -linsolver LU -iters 4 -initers 1 -localdt -noshow -outdir /tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/fine/d2a2b75b
=== Multi-Stage Summary ===
  coarse: 1 cases, dry run
  fine: 1 cases, dry run
exit=0

$ find /tmp/verify-metautil-rebase/c5-mat -name q8020_sweep_invocation.json
/tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/q8020_sweep_invocation.json
count=1

$ find /tmp/verify-metautil-rebase/c5-mat -maxdepth 3
/tmp/verify-metautil-rebase/c5-mat
/tmp/verify-metautil-rebase/c5-mat/2026-10-16
/tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697
/tmp/verify-metautil-rebase/c5-mat/2026-10-16/_5f3a4697/q8020_sweep_invocation.json
```

The record (keys sorted): `argv, command_line, cwd, groups, metautil, overrides,
python_executable, start_time_utc, toml_path, toml_path_resolved, user`. Contents:

```json
{
  "command_line": "./q8020-cfd-metautil/.venv/bin/q8020-sweep ./q8020-cfd-metautil/tests/examples/multi_stage_local.toml --dry-run-materialize --set _output_dir=/tmp/verify-metautil-rebase/c5-mat --set _postproc_venv=./q8020-cfd-metautil/.venv",
  "argv": ["./q8020-cfd-metautil/.venv/bin/q8020-sweep", "./q8020-cfd-metautil/tests/examples/multi_stage_local.toml", "--dry-run-materialize", "--set", "_output_dir=/tmp/verify-metautil-rebase/c5-mat", "--set", "_postproc_venv=./q8020-cfd-metautil/.venv"],
  "python_executable": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python3",
  "toml_path": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/multi_stage_local.toml",
  "toml_path_resolved": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/multi_stage_local.toml",
  "cwd": "/Users/agallojr/proj/src/q8020",
  "groups": null,
  "overrides": {"_output_dir": "/tmp/verify-metautil-rebase/c5-mat", "_postproc_venv": "./q8020-cfd-metautil/.venv"},
  "start_time_utc": "2026-10-16T01:20:34.472825Z",
  "user": {"username": "agallojr", "hostname": "MH-DT9TLJQR2V"},
  "metautil": {"version": "0.1.0", "commit": "9ce8669122ff7e6dba84110434162dce64a04e01", "branch": "main", "dirty": false, "commit_source": "git"}
}
```

All eleven required keys present; `metautil.commit` = 9ce8669..., `branch` = main, `dirty` =
false. The `--set _output_dir` override was honored by the multi-stage orchestrator (base run
dir under `c5-mat`), which is the "overrides applied in multi-stage sweeps too" fix
(`_run_multi_stage_sweep` now calls `_apply_overrides` on a copy of the outer `[global]`). Only
the one JSON was written: the stages are sequential-mode, where dry-run never creates case
dirs, so the base run dir plus the record is the complete expected footprint.

### 5e. Real-run path with missing `_postproc_venv` raises a clear ValueError before any write

From the code (`src/q8020_cfd_metautil/sweep.py`, in the diff): `run_sweep` does
`load_sweep_config` -> `_apply_overrides` -> `_fallback_postproc_venv(global_params, dry_run)`
-> template expansion -> date dir / run dir creation. The check sits before every `mkdir`.

Direct call of the check, and a `run_sweep` real-run call on a scratch TOML with no groups
(so nothing could launch even if the check had been bypassed):

```
$ cat /tmp/verify-metautil-rebase/c5-venv-probe/nogroups.toml
[global]
_output_dir = "/tmp/verify-metautil-rebase/c5-venv-probe/out"
_script = "echo solver"
_postproc_venv = "/tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv"
_case_postproc = "echo postproc"

$ ./q8020-cfd-metautil/.venv/bin/python - <<'PY'
from q8020_cfd_metautil import sweep
gp = {"_postproc_venv": "/tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv"}
try: sweep._fallback_postproc_venv(gp, False)
except ValueError as e: print("ValueError raised:", e)
PY
signature: (global_params: dict[str, typing.Any], dry_run: bool) -> None
ValueError raised: _postproc_venv /tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv (/tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv) does not exist. Run from the directory the TOML's relative paths assume, or pass --set _postproc_venv=<path to the postproc venv> (e.g. --set _postproc_venv=./q8020-cfd-metautil/.venv).
global_params after: {'_postproc_venv': '/tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv'}
--- dry_run=True fallback:
Warning: _postproc_venv ... does not exist; dry run shows the running interpreter's environment /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv instead (a real run would stop with an error)
global_params after dry-run fallback: {'_postproc_venv': '/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv'}
--- unset _postproc_venv, real run (should be a no-op):
global_params: {}

$ ./q8020-cfd-metautil/.venv/bin/python - <<'PY'
import os
from q8020_cfd_metautil.sweep import run_sweep
try: run_sweep("/tmp/verify-metautil-rebase/c5-venv-probe/nogroups.toml", [], dry_run=False)
except ValueError as e: print("ValueError raised:", e)
print("out dir exists after:", os.path.exists("/tmp/verify-metautil-rebase/c5-venv-probe/out"))
PY
ValueError raised: _postproc_venv /tmp/verify-metautil-rebase/c5-venv-probe/does-not-exist-venv (...) does not exist. Run from the directory the TOML's relative paths assume, or pass --set _postproc_venv=<path to the postproc venv> (e.g. --set _postproc_venv=./q8020-cfd-metautil/.venv).
out dir exists after: False

$ find /tmp/verify-metautil-rebase/c5-venv-probe | sort
/tmp/verify-metautil-rebase/c5-venv-probe
/tmp/verify-metautil-rebase/c5-venv-probe/nogroups.toml
```

Dry-run fallback also confirmed end-to-end through the CLI on the smoke TOML's `ideal` group
with `--set _postproc_venv=/tmp/verify-metautil-rebase/nope-venv`: warning printed to
stderr, the `Postproc (dry-run):` line shows `source
/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/activate && ...`, exit 0, and no
`c5-fallback` directory created.

## Check 6: hygiene on added lines -- PASS

```
$ git diff origin/main..main -- src/ | grep '^+' | grep -v '^+++' | awk 'length($0)-1 > 88'
(empty)
$ git diff origin/main..main -- src/ | grep '^+' | grep -v '^+++' | grep -nE '[[:space:]]+$'
(empty)
$ git diff origin/main..main -- README.md | grep '^+' | grep -v '^+++' | awk 'length($0)-1 > 88'
(empty)
$ git diff origin/main..main -- README.md | grep '^+' | grep -v '^+++' | grep -nE '[[:space:]]+$'
(empty)
tabs in added src lines: 0
added src lines checked: 400
```

The four TOML changes are each a single `_case_postproc` command-string line
(`codes/fvm_euler_1d_nozzle/` -> `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/`), exempt from
the width rule as specified.

## Findings

- No defects found. All six checks pass; the rebase preserves both the four upstream commits'
  behavior (synthesized srun launcher, `_env_exports`, sbatch header, 36-case reference TOML)
  and every item-14 feature named in the brief.
- Observation (not a defect): in SLURM mode the CFL TOML renders `#SBATCH -N 70` for 70 cases
  because it sets `_slurm_exclusive_node = true`; that is upstream `cdf4bbb` semantics and
  unrelated to this commit.
- Observation (not a defect): `--dry-run-materialize` on a sequential-mode multi-stage TOML
  writes only the base run dir and the invocation record; case dirs / `pipeline_args.json`
  are a parallel/SLURM-mode artifact, consistent with the help text.
- README diff documents `--dry-run` (writes nothing), `--dry-run-materialize`, the invocation
  record and its keys, the `_postproc_venv` check, UTC date dir and timestamp; it also fixes a
  stale `--groups` usage example. Documentation matches observed behavior.

## Not checked

- No real (non-dry-run) sweep, solver or sbatch submission was executed anywhere.
- The real-run CLI path with a launchable group and a missing venv was not run through
  `q8020-sweep` itself (launch risk); it was covered by the `run_sweep(..., [], dry_run=False)`
  probe and by a direct call of `_fallback_postproc_venv`, which is the same code path.
- NVMe tarball packing (`_pack_venvs`) was only observed as `Would pack:`; no archive was built.
- `feature/solverfw-v2` was checked for its tip hash only; its content was not re-tested.
- Behavior on Frontier / a real SLURM controller was not exercised.

Scratch dir `/tmp/verify-metautil-rebase` deleted after this report was written.
