# Build 13: stale harvester paths, metautil smoke example, April re-harvest feasibility

Work-plan item 13 (`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/WORKPLAN.md`).
Built 2026-10-15T02:55Z to 03:00Z (UTC) by builder C. Nothing committed in
either repo:

- experiments `main` @ `6f646617`
- metautil `feature/solverfw-v2` @ `753b97e`

Both `git log -1` values are unchanged.

## 1. What changed

All four callers now point at the current harvester location,
`aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/<harvester>.py`, instead of the
stale `codes/` prefix.

| File:line | Before (stale part) | After |
|---|---|---|
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml:37` | `${_experiment_dir}/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` | `${_experiment_dir}/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` (same form as `fvm_sqls_aiaa_sweeps.DRAFT.toml:88`) |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml:7-8` | `q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/{fvm_euler_1d_solver_harvester,backend_meta_harvester}.py` | `q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/{...}.py` (relative form kept; this file has no `_experiment_dir` variable) |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/harvest_lugo_all.sh:22` | `HARVESTER_DIR=".../q8020-cfd-experiments/codes/fvm_euler_1d_nozzle"` | `HARVESTER_DIR="/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle"` (Frontier prefix untouched) |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py:9` (docstring) | `python q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/backend_meta_harvester.py <postproc_json>` | `python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py <postproc_json>` |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/examples/fvm_1d_smoke_test.toml` (new, untracked) | -- | Restored from `git show 46fa917^:examples/fvm_1d_smoke_test.toml` (deleted in `46fa917`, 2026-07-15T16:26:57Z). Two changes: line 37 harvester path updated the same way as `fvm_cfl_sweeps.toml`, and the trailing space on line 54 (`"-shots" = [ ... ] `) removed. The original is byte-identical to `results/fvm_euler_1d_solver/2026-04-05/_52d087d1/q8020_fvm_1d_smoke_test.toml` |

Why: the April 2026-04-08 and 2026-04-10 Frontier sweeps lost every solver-side
fragment. Each case's `q8020_postproc_stderr_<id>.txt` reads `python3: can't open
file '/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020/./q8020-cfd-experiments/`
followed by the stale prefix and `fvm_euler_1d_solver_harvester.py': [Errno 2]
No such file or directory`.

Grep check: `grep -rn` for the stale `codes/` + `fvm_euler_1d_nozzle` string
under `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/` now finds no
live config or code. It hits only:

- `aux/Z-Keep/input/cases/_smoke_tests/local_parallel.toml` (2 hits) and
  `slurm_parallel.toml` (2 hits). This is a holding area, left alone by rule.
- The historical prose in this folder's own reports: `05-sweep-mechanism.md`
  (9 hits), `WORKPLAN.md` (2 hits) and `STATUS.md` (1 hit). These describe the
  old path and are outside my write scope.

So the acceptance criterion "hits only under `aux/Z-Keep/`" holds for every
config and code file. It does not hold for these three report files, which I
must not edit.

## 2. Dry runs

All runs used `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`.

Setup:

- cwd: `/Users/agallojr/proj/src/q8020`. The TOMLs use `./`-relative paths
  resolved from the q8020 checkout root, the same root as April's `/autofs/.../q8020/`.
- Output: always `--set _output_dir=/tmp/order1-build-10-13/dry/<name>`.
- Mode: sequential, which writes nothing (report 05 sec. 2d). Afterwards
  `/tmp/order1-build-10-13/dry` did not exist, which confirms that.

Neither TOML needed a Frontier-only path or an extra variable to expand.

| TOML | Invocation | Result | Wall time |
|---|---|---|---|
| `fvm_cfl_sweeps.toml` | `q8020-sweep /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run --set _run_mode=sequential --set _output_dir=/tmp/order1-build-10-13/dry/cfl_seq` | rc 0, `70 cases in 2 groups` (time_steps 50, more_iters 20), 70 `Postproc (dry-run)` lines, all with the new path, `Total: 70 (dry run)` | 0.59 s |
| `fvm_euler_1d_nozzle.toml` | `q8020-sweep /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml --dry-run --set _output_dir=/tmp/order1-build-10-13/dry/nozzle` (no `_run_mode`, so sequential by default) | rc 0, `4 cases in 4 groups` (the `_`-prefixed groups are skipped), 2 postproc lines per case, both with the new path, `Total: 4 (dry run)` | 0.11 s |
| `examples/fvm_1d_smoke_test.toml` (metautil) | `q8020-sweep q8020-cfd-metautil/examples/fvm_1d_smoke_test.toml --dry-run --set _run_mode=sequential --set _output_dir=/tmp/order1-build-10-13/dry/smoke` | rc 0, `66 cases in 5 groups` (ideal 1, shots 1, bigshots 4, fvm_1d_nelem_5_sv_shots 10, time_steps 50), new path in postproc, `Total: 66 (dry run)` | 0.15 s |

Output head of the `fvm_cfl_sweeps.toml` run, with ANSI codes stripped:

```
Running sweep: 70 cases in 2 groups [sequential]
Output directory: /tmp/order1-build-10-13/dry/cfl_seq/2026-10-14/_fe8ad4a5

=== Group: time_steps (50 cases) ===
  Case: time_steps_0_trial_0
    Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/order1-build-10-13/dry/cfl_seq/2026-10-14/_fe8ad4a5/time_steps_0/trial_0_95e2cc48"
  Postproc (dry-run): bash -c "source ./.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order1-build-10-13/dry/cfl_seq/2026-10-14/_fe8ad4a5/time_steps_0/trial_0_95e2cc48/q8020_case_postproc_95e2cc48.json"
```

The `fvm_euler_1d_nozzle.toml` run printed this for the first case:

```
=== Group: fvm_1d_nelem_5_smoke (1 cases) ===
  Case: fvm_1d_nelem_5_smoke
    Command: bash -c "source /Users/agallojr/proj/src/q8020/../fvm_euler_1d_solver/.venv/bin/activate && python ../fvm_euler_1d_solver/nozzle_1d_solver.py -linsolver HHL -nelem 5 -localdt -noshow -shots 150000 -iters 1 -initers 1 -outdir /tmp/order1-build-10-13/dry/nozzle/2026-10-14/_7c28a71a/c7401ea7"
  Postproc (dry-run): python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/.../c7401ea7/q8020_case_postproc_c7401ea7.json
  Postproc (dry-run): python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py /tmp/.../c7401ea7/q8020_case_postproc_c7401ea7.json
```

The date directory `2026-10-14` is the sweeper's local date. The runs happened
at about 2026-10-15T02:56Z, which is 2026-10-14 22:56 -0400.

## 3. April re-harvest feasibility (on /tmp copies only)

The April case dirs still hold every raw solver output: pickle, all CSVs,
`q8020_stdout_<id>.txt`. They also hold the sweeper's
`q8020_sweep_{experiment,case,code,artifacts,exec_stats}_<id>_0.json`. What is
missing are the solver-side `case`, `code`, `backend`, `artifacts`, `results` and
`analysis` fragments.

The harvester's postproc-JSON mode cannot be used as-is. It reads `case_dir`
from `q8020_case_postproc_<id>.json`, and that holds the Frontier path
`/lustre/orion/...`. The re-harvest instead calls `generate_metadata(case_dir,
experiment_id=<id from that JSON>)`. That writes exactly the names the sweep
postproc would have written: `q8020_<section>_<id>_0.json`.

I did not use `q8020-harvest --harvester`, because it would mint a new random
experiment_id. It would also add a second `experiment` fragment.

### Single-case runs

The two cases were copied to `/tmp/order1-build-10-13/april/` and run with
`$P april_harvest.py` (0.56 s for both):

| Case | experiment_id | Fragments before -> after (roll-up counts) | New files | Warnings | analysis |
|---|---|---|---|---|---|
| `2026-04-08/_85fd6d17/more_iters_2/trial_8_7b739958` (CFL 10, max_iters 60) | 7b739958 | results 0->1, backend 0->1, analysis 0->1, case 1->2, code 1->2, artifacts 1->2 (sweep + solver) | 6 (`q8020_{analysis,artifacts,backend,case,code,results}_7b739958_0.json`) | none | 45 iterations, converged true (`dq_norm`), residual_reduction 2.673863961402395e-09, equal to the solver's own stdout `res/res0:2.673863961402395e-09` at step 44 |
| `2026-04-10/_f1112a1f/more_iters_0/trial_7_42201eb4` (CFL 2, max_iters 120) | 42201eb4 | same pattern | 6 | none | 67 iterations, converged true (`dq_norm`), residual_reduction 1.749383991070276e-09 |

These April runs have real HHL stdout, which exercises the 4-column parser on
real data. All 45 and 67 `per_iteration` entries got `hhl_solution_vector` and
`lu_reference_vector`, and `lu_reference_vector_final` has 15 entries.

### Full-tree run

A full copy of both sweeps (41 MB + 33 MB) went to
`/tmp/order1-build-10-13/aprilfull/`. The full command below ran on it, with
`ROOT` set to that path:

- 50 cases harvested, 0 failed, 17 s wall time. That is 30 cases for 2026-04-08
  and 20 for 2026-04-10.
- 50 fragments each of case, code, backend, artifacts, results and analysis.
- 0 roll-up warnings.

Convergence by group:

| Sweep / group | CFL | max_iters | converged | not converged (stopped at final_iters 59 = cap) |
|---|---|---|---|---|
| 2026-04-08 more_iters_0 | 1 | 60 | 0 | 10 |
| 2026-04-08 more_iters_1 | 5 | 60 | 8 | 2 |
| 2026-04-08 more_iters_2 | 10 | 60 | 10 | 0 |
| 2026-04-10 more_iters_0 | 2 | 120 | 10 | 0 |
| 2026-04-10 more_iters_1 | 3 | 120 | 10 | 0 |

All 38 converged cases are `converged_by "dq_norm"`. In every one the pickle
also shows an early stop. The 12 unconverged cases hit the iteration cap.

The `aprilfull` run was made before the last harvester edit, the `_nsteps`
guard in `_last_dq_converged`. That guard does not apply to these steady-mode
file names, so the output is the same.

### Command that would re-harvest both April sweeps in place

Not run on the real tree. The owner decides. It is about 17 s and writes 300
new files into `results/`:

```
cd /Users/agallojr/proj/src/q8020 && \
for pp in /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-{08,10}/_*/*/trial_*/q8020_case_postproc_*.json; do \
  d=$(dirname "$pp"); id=$(basename "$pp" .json); id=${id#q8020_case_postproc_}; \
  /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python -c "import importlib.util, sys, pathlib; s = importlib.util.spec_from_file_location('h', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); m.generate_metadata(pathlib.Path(sys.argv[2]), experiment_id=sys.argv[3])" \
    /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py "$d" "$id"; \
done
```

It writes 6 x 50 = 300 `q8020_<section>_<id>_0.json` files. It does not touch
the existing `q8020_metadata_<id>.json` roll-ups, which were made in April
without solver fragments.

To refresh those roll-ups as well, run
`harvest_metadata(case_dir, read_only=True)` per case and write the result to
`q8020_metadata_<id>.json`. That is a separate decision, because it overwrites
50 committed files.

## 4. Open doubts

1. **`fvm_euler_1d_nozzle.toml` has inconsistent relative paths, and the fix
   leaves them that way.** `_env = "../fvm_euler_1d_solver/.venv"` and the
   script `../fvm_euler_1d_solver/...` assume cwd = a sibling of the solver,
   such as `q8020-cfd-experiments/`. The postproc paths
   `q8020-cfd-experiments/aux/...` assume cwd = the q8020 root. The dry run
   shows the effect: from the q8020 root the venv resolves to the nonexistent
   `/Users/agallojr/proj/src/q8020/../fvm_euler_1d_solver/.venv`. Making this
   file match the draft TOML (`_solver_dir` / `_experiment_dir` /
   `_postproc_venv` variables) would fix it. That is a bigger change than this
   item asked for.
2. **`backend_meta_harvester.py:9` is now 118 characters, over 88.** It is a
   single path token in a docstring; the original line was 100 characters.
3. **`harvest_lugo_all.sh` was not run.** It is Frontier-only. Only the path
   string was checked.
4. **The draft TOML was not re-dry-run here.** That is
   `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml`.
   Report 05 sec. 2d covers it, and it was not changed.
5. **`fvm_cfl_sweeps.toml` was dry-run only in sequential mode.** Its default is
   `_run_mode = "parallel"`, and parallel dry-run writes `pipeline_args.json`
   under `_output_dir` (report 05 sec. 2d). The postproc string is the same in
   both modes.

## 5. Line-length fix (2026-10-15T03:05:22Z)

At the coordinator's request, `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py:9`
was split at the last `/` with a shell backslash continuation. The second line
starts at column 0 so the shell joins the path back without a space. The
rendered docstring reads:

```
    python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/\
backend_meta_harvester.py <postproc_json>
```

In the source the backslash is written `\\`, so it renders as a single `\`.

`awk 'length > 88'` on that file found line 9 at 118 characters before the
fix, and nothing after. This resolves open doubt 2 above.

`fvm_euler_1d_solver_harvester.py` needed no fix. Its five lines over 88
characters (now lines 316, 321, 379, 503 and 773) and the trailing whitespace on
line 67 are all already in HEAD (`6f646617`, at lines 260, 265, 323, 354 and
572). None is introduced by build 10, so they were left alone.

## 6. Correction: the smoke example was moved, not deleted (2026-10-15T03:20Z)

**The premise was wrong.** Work item 13 said `46fa917` deleted
`examples/fvm_1d_smoke_test.toml`. It did not: the commit moved it. Running
`git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil show --stat -M 46fa917 -- examples tests/examples`
shows `{examples => tests/examples}/fvm_1d_smoke_test.toml | 0`, a pure rename.
Nine other files were renamed the same way.

The file was never lost. It is tracked at
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml`.
So the "restore" in section 1 made a duplicate. Sections 1 and 2 are superseded
wherever they mention `examples/fvm_1d_smoke_test.toml`.

**Actions.** All changes are in metautil, uncommitted.

1. Deleted the untracked duplicate
   `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/examples/fvm_1d_smoke_test.toml`.
   `examples/` still holds the tracked `acceptance_sweep.py`, which was left
   untouched.
2. Path-only edits in four tracked TOMLs. These are every hit of
   `grep -rn` for the stale prefix over `*.toml`, `*.sh` and `*.py` in metautil,
   excluding `.venv/`:

   | File:line | Change |
   |---|---|
   | `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml:37` | `${_experiment_dir}/codes/...` changed to `${_experiment_dir}/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` |
   | `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/base_case.toml:30` | `~/q8020/q8020-cfd-experiments/codes/...` changed to `~/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` |
   | `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/base_case_hhl.toml:30` | same change |
   | `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/hhl_time_step_impact.toml:30` | same change |

   After the edits, that grep finds 0 stale hits in metautil. The only other
   `harvester.py` mentions, `harvest.py:22` and `:343`, are generic
   `/path/to/...` placeholders and were left alone.
3. Unlike the duplicate in section 1, this copy keeps the trailing space on its
   `"-shots" = [ ... ]` line, because the edits are path-only.

**Dry-run.** The TOML's default parallel mode was used, from cwd
`/Users/agallojr/proj/src/q8020`, with the run at 2026-10-15T03:20:06Z:

```
q8020-cfd-metautil/.venv/bin/q8020-sweep q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml --dry-run --set _output_dir=/tmp/order1-build-10-13/dry
```

- rc 0, wall time 0.97 s.
- Output: `Running sweep: 66 cases in 5 groups [parallel]`, then 66 `Prepared:`
  lines, then `Total: 66 (dry run)`.
- In parallel mode the sweeper prints no `Postproc (dry-run)` lines. The postproc
  command goes into each case's `pipeline_args.json` instead. All 66 of those
  files under `/tmp/order1-build-10-13/dry/2026-10-14/_7ba8a32a/` carry
  `source ./.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.
  None carries the stale path.
- Nothing was written under `~/q8020`. The scratch dir was deleted afterwards.

**Not dry-run.** `base_case*.toml` and `hhl_time_step_impact.toml` were not
dry-run. They hard-code `~/q8020/...` and `~/venvs/q8020-sweep` layouts, so
their paths are home-relative to some other machine's tree.
