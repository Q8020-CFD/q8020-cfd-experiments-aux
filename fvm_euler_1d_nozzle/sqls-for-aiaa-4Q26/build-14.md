# Build 14: sweeper housekeeping (metautil)

Builder 14, order 3. Written 2026-10-15T08:12Z (system clock, `date -u`; see
doubt 6). Repo `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`, branch
`feature/solverfw-v2`, HEAD `753b97e` (unchanged, nothing committed). All
changes are uncommitted working-tree edits for the owner to commit.

## 1. What changed

Files: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/sweep.py`
and `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/README.md`. Nothing
under `src/q8020_cfd_metautil/solverfw/`; the registry hooks in `sweep.py`
(`_REGISTRY_SLOTS`, `PRUNED_CONFLICTS`, `_case_chain`, `_prune_expanded_cases`,
`expand_case_lists`) are untouched (no diff hunk in lines 2111-2330 of HEAD).

```
 README.md                                |  84 +++++++++--
 src/q8020_cfd_metautil/sweep.py          | 236 ++++++++++++++++++++++++++++---
 tests/examples/base_case.toml            |   2 +-   (pre-existing, not mine)
 tests/examples/base_case_hhl.toml        |   2 +-   (pre-existing, not mine)
 tests/examples/fvm_1d_smoke_test.toml    |   2 +-   (pre-existing, not mine)
 tests/examples/hhl_time_step_impact.toml |   2 +-   (pre-existing, not mine)
 6 files changed, 297 insertions(+), 31 deletions(-)
```

`git status --short`: ` M README.md`, ` M src/q8020_cfd_metautil/sweep.py`,
plus the four `tests/examples/*.toml`. `git log -1`: `753b97e`.

`sweep.py` (line numbers in the modified file):

- 15, 19: top-level `import importlib.metadata`, `import shlex`.
- 1046-1131 `_build_case_launch_info`: new `write_files=True` parameter;
  the case-dir `mkdir` and the `pipeline_args.json` write are skipped when
  False. The returned info now also carries `case_preproc`/`case_postproc`.
- 1655-1716 `_collect_parallel_cases`: new `dry_run`, `materialize`
  parameters; passes `write_files=(not dry_run) or materialize` (1681);
  on dry-run prints each case via the new `_print_dry_run_case` (1698),
  which emits `Command: ...` and `Preproc/Postproc (dry-run): ...` in the
  sequential dry-run format (it reuses `run_postproc(dry_run=True)`).
- 1831-1930 `_finalize_slurm`: new `materialize` parameter,
  `write_files` (1845). A plain dry-run no longer `mkdir`s the run dir,
  no longer writes `q8020_sweep.sbatch`; it prints `Would generate: <path>`
  and the `#SBATCH` lines instead. The NVMe rewrite loop already skipped
  missing args files, so it is a no-op then. Venv packing was already a
  print-only dry-run (`Would pack:`).
- 2545-2650 new helpers: `_metautil_provenance()` (package version via
  `importlib.metadata`, plus `git -C <pkg dir> rev-parse HEAD --abbrev-ref
  HEAD` and `git status --porcelain --untracked-files=no`, 5 s timeout
  each, null on any failure), `make_invocation_record(argv, toml_path,
  overrides, group_filter, start_time)`, `INVOCATION_FILE`,
  `write_invocation_record(run_dir, record)`, `_fallback_postproc_venv`.
- `run_sweep` (2652-): new keyword-only `dry_run_materialize`,
  `invocation`; `_fallback_postproc_venv(global_params)` after the `--set`
  coercion and before `${VAR}` expansion (2710); date dir in UTC (2795);
  invocation built from `sys.argv` if not passed, written to the run dir
  when `not dry_run or dry_run_materialize` (2816-2822); `"invocation"`
  key added to the results dict that becomes `q8020_sweep_meta<wf>.json`
  (2849); the dry-run header prints `Invocation: <command line>` (2873);
  `materialize` passed to `_collect_parallel_cases` (2924) and
  `_finalize_slurm` (3302).
- `_run_multi_stage_sweep`: same two parameters, UTC date dir (3437),
  invocation record written to the base run dir and embedded in its meta
  (3441-3473), and passed down to each stage's `run_sweep` (3524).
- `main()`: `--dry-run-materialize` flag (3596, implies `--dry-run`),
  group help text says `_`-prefixed groups are skipped unless named, an
  epilog example for `_smoke`, invocation built right after argument
  parsing and passed to both entry paths.

`README.md` (section "Sweeper", lines ~182-262, and "Output structure"
~445-462): positional groups replace the stale `--groups ideal shots`
example; `_`-prefixed groups run only when named; usage line; the laptop
path `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`
(not on PATH, editable install, run from `/Users/agallojr/proj/src/q8020`);
`--set` coercion rules (bool, then int, then float, else string; bare key
matches a dashed variant; `--set` beats group copies); `--dry-run` vs
`--dry-run-materialize` with the 2026-10-15 behavior change; the
provenance file and keys; the `_postproc_venv` fallback and the explicit
`--set _postproc_venv=./q8020-cfd-metautil/.venv` laptop recipe; the
SLURM paragraph updated for the new dry-run; the output tree lists
`q8020_sweep_invocation.json`; `<date>` is UTC (behavior change; April
runs used the local date, e.g. the 2026-04-05T00:10Z submit landed in
`2026-04-04/`).

## 2. Command-line provenance

**Where:** both. A side file `<run_dir>/q8020_sweep_invocation.json`, and
the same dict under the `invocation` key of `q8020_sweep_meta<wf_id>.json`
(and of the multi-stage meta). Why both: the meta file is written only at
the very end of `run_sweep` (after venv packing and `sbatch`, or after all
sequential cases), so a crash or Ctrl-C loses it; the side file is written
as soon as the run dir is created. Embedding it in the meta keeps the one
sweep-level record complete.

**Why no workflow id in the file name:** `FRAGMENT_PATTERN`
(`meta_fragment.py:53`, `^q8020_([a-z_]+)_(?:([a-f0-9]{8})_)?(\d+)\.json$`)
matches `q8020_sweep_invocation_<id>.json` whenever the 8-hex id is all
digits, which would make `metakeys._walk_case_dirs` treat the run dir as a
fragment-only case dir and stop recursing. `q8020_sweep_invocation.json`
cannot match (checked: `FRAGMENT_PATTERN` and `SWEEP_FRAGMENT_PATTERN`
both False). The run dir is already unique per workflow.

**Keys:** `command_line` (`shlex.join(sys.argv)`, copy-pasteable),
`argv`, `python_executable`, `toml_path` (`Path.absolute()`, symlinks
preserved, the module's convention for Frontier `/ccs/home` paths),
`toml_path_resolved` (`Path.resolve()`), `cwd`, `groups` (list or null),
`overrides` (raw `--set` strings, before coercion), `start_time_utc`
(ISO 8601 Z), `user` (`make_user_meta()`: username, hostname),
`metautil` (`version`, `commit`, `branch`, `dirty`).

**Example**, written by
`--dry-run-materialize` (the only dry-run mode that writes it) of the CFL
TOML from cwd `/Users/agallojr/proj/src/q8020`:

```json
{
  "command_line": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run-materialize --set _output_dir=/tmp/order3-build-14/after_mat",
  "argv": ["/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep", "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml", "--dry-run-materialize", "--set", "_output_dir=/tmp/order3-build-14/after_mat"],
  "python_executable": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python3",
  "toml_path": "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml",
  "toml_path_resolved": "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml",
  "cwd": "/Users/agallojr/proj/src/q8020",
  "groups": null,
  "overrides": {"_output_dir": "/tmp/order3-build-14/after_mat"},
  "start_time_utc": "2026-10-15T08:11:32.511280Z",
  "user": {"username": "agallojr", "hostname": "MH-DT9TLJQR2V"},
  "metautil": {"version": "0.1.0", "commit": "753b97eb8b2ff1235ac2a59baa94ebab7709251c",
               "branch": "feature/solverfw-v2", "dirty": true}
}
```

`dirty: true` is correct here (the uncommitted item-14 and TOML edits).
Unit-level check: `make_invocation_record` with fake argv
`[/x/.venv/bin/q8020-sweep, cfg.toml, sqls_shots, --set, _slurm=true,
--set, "_output_dir=/a b/c"]` + `write_invocation_record` into a scratch
dir round-trips through JSON; `command_line` came out
`... --set _slurm=true --set '_output_dir=/a b/c'` (shell-quoted).
API check: `run_sweep(..., dry_run=True)` on the CFL TOML returns a
results dict with an `invocation` key (11 keys) and 70 cases, and writes
nothing. The non-dry write into `q8020_sweep_meta<wf>.json` was not
exercised end to end (that needs a real sweep); it is the same `results`
dict that is dumped at the end of `run_sweep`.

## 3. Dry-run hygiene and UTC date

Before the change (baseline at the start of this build, same commands):
CFL TOML plain `--dry-run` left 150 entries under `_output_dir`
(`find | wc -l`; 70 `pipeline_args.json`, 80 dirs incl. root), the fvm
smoke TOML 141 entries, the SQLS draft (sequential) 0.

After, all from cwd `/Users/agallojr/proj/src/q8020`, binary
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`,
every run with `--set _output_dir=/tmp/order3-build-14/after_<name>`:

| name | TOML + args | printed | `Command:` lines | `Postproc (dry-run)` lines | `find <dir> \| wc -l` | wall |
|---|---|---|---|---|---|---|
| cfl | `q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run` | 70 cases in 2 groups [parallel], Total 70 (dry run) | 70 | 70 | 0 (dir absent) | 0.22 s |
| smoke | `q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml --dry-run` | 66 cases in 5 groups [parallel], Total 66 | 66 | 66 | 0 (absent) | 0.20 s |
| sqls | `.../sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml _smoke sqls_shots sqls_cfl sqls_nelem hhl_matched --dry-run` | 146 cases in 5 groups [sequential], Total 146 | 146 | 146 | 0 (absent) | 0.21 s |
| sqlsdef | same TOML, no groups | 145 cases in 4 groups (`_smoke` skipped) | 145 | 145 | 0 (absent) | 0.18 s |
| cflslurm | CFL TOML `time_steps --dry-run --set _slurm=true` | 50 cases [parallel (slurm)], 2 x `Would pack`, `Would generate: .../q8020_sweep.sbatch` + `#SBATCH -J q8020_sweep -A ard189 -t 02:00:00 -N 50 -C nvme -p batch -o/-e` | 50 | 50 | 0 (absent) | 0.20 s |
| mat | CFL TOML `--dry-run-materialize` | 70 cases, Total 70 | 70 | 70 | 151 (71 files = 70 `pipeline_args.json` + `q8020_sweep_invocation.json`; 80 dirs) | 0.28 s |

A SLURM `--dry-run-materialize` of `time_steps` wrote 52 files (50
`pipeline_args.json` with NVMe-rewritten `source /mnt/bb/agallojr/venv_0/...`,
the sbatch, the invocation record) and 0 tarballs. Both multi-stage
examples (`tests/examples/multi_stage_local.toml`,
`multi_stage_example.toml`) dry-run cleanly and write 0 entries.

Head of the CFL plain dry-run (ANSI stripped, lines cut):

```
Warning: _postproc_venv ./.venv (/Users/agallojr/proj/src/q8020/.venv) does not exist; falling back to the running interpreter's environment /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv
Running sweep: 70 cases in 2 groups [parallel]
Output directory: /tmp/order3-build-14/after_cfl/2026-10-15/_70d8e14a
Invocation: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run --set _output_dir=/tmp/order3-build-14/after_cfl

=== Group: time_steps (50 cases) ===
  Prepared: time_steps_0_trial_0 (c94257b6)
    Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/order3-build-14/after_cfl/2026-10-15/_70d8e14a/time_steps_0/trial_0_c94257b6"
  Postproc (dry-run): bash -c "source /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order3-build-14/after_cfl/2026-10-15/_70d8e14a/time_steps_0/trial_0_c94257b6/q8020_case_postproc_c94257b6.json"
  ...
  Would launch: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python3 -m q8020_cfd_metautil.sweep_worker /tmp/order3-build-14/after_cfl/2026-10-15/_70d8e14a/time_steps_0/trial_0_c94257b6/pipeline_args.json
```

Head of the SQLS dry-run:

```
Running sweep: 146 cases in 5 groups [sequential]
Output directory: /tmp/order3-build-14/after_sqls/2026-10-15/_8cea3f5f
Invocation: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep .../fvm_sqls_aiaa_sweeps.DRAFT.toml _smoke sqls_shots sqls_cfl sqls_nelem hhl_matched --dry-run --set _output_dir=/tmp/order3-build-14/after_sqls

=== Group: _smoke (1 cases) ===
  Case: _smoke
    Command: bash -c "source /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/activate && python3 /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/nozzle_1d_solver.py -time_scheme BDF1 -localdt -noshow -linsolver SQLS -sqls_method full_svd ..."
  Postproc (dry-run): bash -c "source /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/activate && python3 /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py ..."
```

**UTC date directory (behavior change).** `run_sweep` and
`_run_multi_stage_sweep` now use
`datetime.now(timezone.utc).strftime("%Y-%m-%d")`. April runs used the
local date: the 2026-04-05T00:10Z Frontier submit (20:10 EDT on
2026-04-04) landed in `2026-04-04/`. A sweep started between 20:00 and
24:00 EDT now lands under the next day's directory. The per-case
`"timestamp"` (local, `run_single`, `run_case_pipeline`) and the sweep
meta `"timestamp"` (`%Y%m%d_%H%M%S`, local) were left as they were; only
the directory name changed, as specified.

## 4. `_postproc_venv` fallback (laptop usability)

`_fallback_postproc_venv` runs after `--set` and before template
expansion, so `${_postproc_venv}` in `_case_postproc` and
`_slurm_pack_venvs` resolve to the fallback. If `_postproc_venv` is a
non-empty string whose (template-expanded, `~`-expanded, cwd-relative)
path is not a directory, it is replaced by `sys.prefix` when
`sys.prefix/bin/activate` exists, with a stderr warning naming the
configured path, its absolute form, and the replacement (example in the
head above). If the running interpreter is not a venv, it warns and
leaves the value unchanged. An explicit
`--set _postproc_venv=./q8020-cfd-metautil/.venv` gives no warning and
renders `source ./q8020-cfd-metautil/.venv/bin/activate && ...` (checked).
The SQLS draft TOML already sets an absolute existing path, so no
warning there.

## 5. Branch decision support (open question 4)

`git log --oneline 8ccab91..753b97e` (commit times converted to UTC from
the `-04:00` author dates):

```
753b97e 2026-07-26T23:28:56Z solverfw v2c: QuantumLinearSystemSolver + §9 acceptance sweep
0246f0f 2026-07-26T23:18:36Z solverfw v2b: ContainerIntegrator, ProblemTransform, code.chain
3a65797 2026-07-26T22:58:53Z solverfw v2a: fixes + Encoder/Readout seam + plugin registries
28b78e3 2026-07-26T19:21:57Z solverfw v2: problem types, backend element, convergence, validators, registry
```

`git rev-list --left-right --count 8ccab91...753b97e` = `0 4` (feature is
4 ahead, 0 behind; main can fast-forward).
`git diff 8ccab91..753b97e --stat`: 20 files, +1668 / -47 lines; 18 of
them are `solverfw/*` or `examples/acceptance_sweep.py`; the two outside
are `src/q8020_cfd_metautil/sweep.py` (+165, -0) and
`src/q8020_cfd_metautil/meta_fragment.py` (+69, -6). `harvest.py`,
`sweep_worker.py`, `sweep_postproc.py`, `pyproject.toml`: no change.

- `sweep.py`: purely additive. `_REGISTRY_SLOTS`, the `PRUNED_CONFLICTS`
  accumulator with `reset_pruned_conflicts` / `pruned_conflicts_provenance`,
  `_case_chain`, and a call `_prune_expanded_cases(expanded_cases)` at the
  end of `expand_case_lists`. The pass is a no-op unless a case has a
  `chain` dict or a dotted `<slot>.plugin` / `<slot>.knobs.*` key; only
  then is `solverfw` imported. None of the three TOMLs has such a key
  (grep for dotted or bare slot keys returned nothing).
- `meta_fragment.py`: adds `chain_entry`, `make_chain`, and keyword-only
  `chain/problem_type/adaptation/origin/foreign/provenance` arguments to
  `make_code_meta`, emitted only when given (docstring: byte-identical
  output without them).
- fvm harvester
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
  imports only stdlib plus `write_analysis, write_artifacts,
  write_backend, write_case, write_code, write_results` from
  `q8020_cfd_metautil.meta_fragment`; all six exist on `main` 8ccab91
  with no diff to the feature branch. It does not call `make_code_meta`
  or anything in `solverfw`. The fvm solver repo
  (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, excluding
  `.venv`) does not import `q8020_cfd_metautil` at all.
- Empirical check: the item-14 patch (`git diff -- src README.md`)
  applies cleanly to a `git archive 8ccab91` export under `/tmp` (hunks
  offset by -165 lines, no rejects), compiles, and its SQLS dry-run output
  (146 cases, 454 lines, ids and output roots normalized) is identical to
  the feature-branch output; its CFL dry-run gives 70 cases and writes 0
  entries.

**Recommendation:** for the fvm / SQLS paper sweeps the two branches are
functionally identical; nothing on that path depends on the 4 extra
commits. Run them from `feature/solverfw-v2` with item 14 committed on
top, which is what all three editable installs already point to, then
fast-forward `main` to it (0 behind, no merge) so `main` is the branch of
record and the Frontier checkout is a plain `git checkout main`. If Andy
prefers to keep solverfw v2 off `main` until it is reviewed, the item-14
commit cherry-picks onto `8ccab91` cleanly (shown above) and the sweeps
behave the same. Either way the new `invocation.metautil.commit` /
`branch` / `dirty` keys record which one actually ran. No branch switch
was made.

## 6. Tests

`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python -m pytest tests -q -p no:cacheprovider`:
before 12 passed in 0.15 s, after 12 passed in 0.05 s (only
`tests/test_slurm_postproc.py` is collected). No test files added.
`py_compile` clean; no added line over 88 chars, no trailing whitespace
in my hunks (the long lines in `git diff` are in the pre-existing
`tests/examples/*.toml` edits).

## 7. Open doubts

1. Latent bug, not fixed (out of scope): `q8020_sweep_meta_<wf>.json`
   matches `FRAGMENT_PATTERN` / `SWEEP_FRAGMENT_PATTERN` when the 8-hex
   workflow id is all decimal digits (probability (10/16)^8, about 2.3 %
   of sweeps), e.g. `q8020_sweep_meta_12345678.json` -> True. Then
   `metakeys._walk_case_dirs` would classify the run dir as a
   fragment-only case and not descend into it. Worth a small follow-up
   (exclude `q8020_sweep_meta` in `_has_fragment`, or tighten the regex).
2. In a plain dry-run the `Would launch: ... pipeline_args.json` and the
   printed postproc JSON paths name files that are not written; that is
   intended (they show what a real run would use) but could surprise.
3. A plain SLURM dry-run shows the commands before the NVMe rewrite
   (`./fvm_euler_1d_solver/.venv` etc.); the rewritten form is visible
   only with `--dry-run-materialize` in `pipeline_args.json`.
4. The fallback is silent about whether the running venv has the
   harvester's dependencies; it only checks that `bin/activate` exists.
   On Frontier, a missing `_postproc_venv` now falls back to the metautil
   venv (with the warning) rather than failing every postproc as in
   April; that venv is then also what gets packed via
   `${_postproc_venv}` in `_slurm_pack_venvs`.
5. `invocation.start_time_utc` is taken in `main()` right after argument
   parsing, so it precedes the meta's `start_time` by the config load
   (about 0.1 s); for direct `run_sweep` calls it equals `start_time`.
6. Clock: this machine's `date -u` read 2026-10-15T08:08Z-08:12Z during
   the build, while WORKPLAN row 14 says order 3 started
   2026-10-15T12:20Z. One of the two clocks or the WORKPLAN entry is off;
   all times above are this machine's UTC.
7. The materialized invocation example says `dirty: true`; once item 14
   is committed a clean checkout will record `false`.

## 8. Follow-up 2026-10-15T08:37Z-08:40Z (verifier findings)

Same rules: metautil left uncommitted, HEAD still `753b97e`, scratch in
`/tmp/order3-build-14b` (now deleted).

**(1) Multi-stage path ignored `--set`.** This bug was already there:
`_run_multi_stage_sweep` built the base run dir from the raw TOML
`[global]` `_output_dir`. My `--dry-run-materialize` made it worse,
because it writes the invocation JSON into the base and stage dirs; that
is how 3 files landed under `~/q8020` during verification. Fix in
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/sweep.py`:
- The `--set` loop in `run_sweep` is now a shared helper,
  `_apply_overrides(global_params, overrides) -> set[str]` (line 2648).
  It keeps the same dashed-variant matching and the same coercion.
- `run_sweep` calls it at line 2720.
- `_run_multi_stage_sweep` applies it to a copy of `outer_global` at
  line 3449, then template-expands `_output_dir` before building the
  base run dir.
- The stages already received `overrides` through their own `run_sweep`
  calls, and their run dirs are `base/<stage>`.

Evidence. A marker file was touched at 08:37:15Z. Then I ran
`q8020-sweep q8020-cfd-metautil/tests/examples/multi_stage_local.toml --dry-run-materialize --set _output_dir=/tmp/order3-build-14b/ms`
from `/Users/agallojr/proj/src/q8020`. That TOML sets
`_output_dir = "~/q8020"`. The run printed:

```
Output directory: /tmp/order3-build-14b/ms/2026-10-15/_fce206d5
Output directory: /tmp/order3-build-14b/ms/2026-10-15/_fce206d5/coarse
Output directory: /tmp/order3-build-14b/ms/2026-10-15/_fce206d5/fine
```

It wrote these files:
- `/tmp/order3-build-14b/ms/2026-10-15/_fce206d5/q8020_sweep_invocation.json`
- `.../coarse/q8020_sweep_invocation.json`
- `.../fine/q8020_sweep_invocation.json`

`find ~/q8020 -newer <marker> | wc -l` = 0, both after this run and
after all the runs below. More checks:
- A plain `--dry-run` of the same TOML wrote 0 entries.
- A `--dry-run-materialize` of `multi_stage_example.toml` wrote 5 files,
  all under `/tmp/order3-build-14b/ms2`: 3 invocation records and
  2 `pipeline_args.json`.

**(2) README, `--set` and dashed keys.** I checked what the code actually
does on `tests/examples/fvm_1d_smoke_test.toml`. In that file `"-shots"`
is group-level. Dry-run of group `shots`, solver arguments only:

```
--set shots=0     ->  -nelem 2 -time_scheme BDF1 -linsolver HHL -localdt -noshow --shots 0
--set=-shots=0    ->  -nelem 2 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 0
--set -shots=0    ->  error: argument --set: expected one argument
```

On group `bigshots`, where `"-shots"` is a list of 4 values,
`--set=-shots=0` still gives 4 cases, all with `-shots 0`.

So a bare key matches a dashed variant only when that variant is in
`[global]`. Otherwise it adds `--shots` and drops the group's `-shots`.
The dashed form does override group-level and list-valued keys, but it
must be written with `=` (`--set=-shots=0`). The README now says exactly
this. It also gains a "Known issue (not fixed)" paragraph on the
`q8020_sweep_meta_<wf_id>.json` / `FRAGMENT_PATTERN` collision (doubt 1
above). No code change for that.

**Re-runs** (cwd `/Users/agallojr/proj/src/q8020`, `--dry-run`,
`--set _output_dir=/tmp/order3-build-14b/after_<name>`):

| TOML | Cases | `Command:` lines | `Postproc (dry-run)` lines | `find` count |
|---|---|---|---|---|
| CFL | 70 (2 groups, parallel) | 70 | 70 | 0, dir absent |
| fvm smoke | 66 (5 groups, parallel) | 66 | 66 | 0, dir absent |
| SQLS draft, 5 groups named | 146 (sequential) | 146 | 146 | 0, dir absent |

Tests: 12 passed in 0.06 s. Other checks: `py_compile` is clean, no added
line in `src` or `README.md` is over 88 chars, and there is no trailing
whitespace.

`git diff --stat` after the follow-up:

```
 README.md                                | 101 ++++++++++-
 src/q8020_cfd_metautil/sweep.py          | 298 ++++++++++++++++++++++++++-----
 tests/examples/*.toml (4 files, pre-existing, not mine) | 2 +- each
 6 files changed, 354 insertions(+), 53 deletions(-)
```

## 9. Fix-up round 2026-10-15T09:22Z-09:27Z (code review M1-M9)

The rules were unchanged:
- metautil is uncommitted and HEAD is still `753b97e`;
- the `git status --short` list is unchanged;
- nothing under `solverfw/` changed;
- no diff hunk touches HEAD lines 2111-2330, where the registry hooks
  live;
- scratch was `/tmp/order3-fixup-14`, now deleted.

All line numbers below refer to the modified
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/sweep.py`.

**M1. The `_postproc_venv` fallback now applies to dry runs only.**
`_fallback_postproc_venv(global_params, dry_run)` is at line 2702.
- On a real run, a missing venv raises `ValueError` before anything is
  written or launched. `main()` prints it as `Error: ...` and exits 1.
- On a dry run it warns and shows the commands with `sys.prefix`.
- README updated.

Evidence, from cwd `/Users/agallojr/proj/src/q8020`. These are direct
calls, and the `run_sweep` call had zero groups, so nothing could
launch:

```
direct call, dry_run=False -> ValueError: _postproc_venv ./.venv (/Users/agallojr/proj/src/q8020/.venv) does not exist. Run from the directory the TOML's relative paths assume, or pass --set _postproc_venv=<path to the postproc venv> (e.g. --set _postproc_venv=./q8020-cfd-metautil/.venv).
dry_run=True -> {'_postproc_venv': '/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv'}
run_sweep real, 0 groups -> ValueError: (same message); find /tmp/order3-fixup-14/zero | wc -l = 0
```

**M2. Not applied: the review's premise is wrong, so the known issue
stays.** The f-string is `q8020_sweep_meta{workflow_id}.json`, and
`generate_workflow_id()` returns `_<8hex>` (for example `'_90823e72'`).
So the name on disk does have the underscore. The April run dir holds
`q8020_sweep_meta_52d087d1.json`. Regex check:
- `FRAGMENT_PATTERN.match("q8020_sweep_meta_12345678.json")` returns
  True;
- `FRAGMENT_PATTERN.match("q8020_sweep_meta_ab12cd34.json")` returns
  False.

Walk check with `metakeys._walk_case_dirs`, on a scratch run dir that
holds the meta file and a case dir `c1` with a `q8020_metadata_c1.json`:
- with workflow id `_12345678`: `with_metadata=[]`,
  `no_metadata=['_12345678']`, so the real case is missed;
- with `_ab12cd34`: `with_metadata=['c1']`.

The README known issue is kept. Its wording now gives the exact
f-string and the on-disk name. My earlier report was right about this
collision.

**M3. The SLURM dry-run now prints the commands after the NVMe rewrite.**
- New helpers: `_nvme_rewrite` (line 1848), which the
  `pipeline_args.json` rewrite loop now uses too, and
  `_slurm_will_rewrite` (line 1861).
- When packing is active, `_collect_parallel_cases(print_cmds=False)`
  defers the printing.
- `_finalize_slurm` then prints `Commands after NVMe venv rewrite:` and
  one block per case (`Case:`, `Command:`, `Postproc (dry-run):`),
  starting at line 1923.

CFL `time_steps --dry-run --set _slurm=true`: 50 `Command:` lines, all
50 contain `/mnt/bb`, and 0 entries are written. Example:

```
  Case: time_steps_0_trial_0 (abd4f7a6)
    Command: bash -c "source /mnt/bb/agallojr/venv_0/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py ... -cfl 1 -outdir .../time_steps_0/trial_0_abd4f7a6"
  Postproc (dry-run): bash -c "source /mnt/bb/agallojr/venv_1/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py .../q8020_case_postproc_abd4f7a6.json"
```

With `--dry-run-materialize`, the printed command and postproc for one
case are string-equal to the `cmd[2]` and `case_postproc[0]` written
into its `pipeline_args.json` (checked).

**M4. Unwritten args files are now labeled.** New helper
`_unwritten_note` (line 1133), used at both `Would launch:` sites (local
parallel and SLURM interactive). In a plain dry-run the line ends
`.../pipeline_args.json (file written only with --dry-run-materialize)`.
With `--dry-run-materialize` the note is absent (0 matches).

**M5. The meta `timestamp` is now UTC.** Line 2952 is now
`datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`. A dry-run
API call gave `timestamp 2026-10-15T09:25:27Z`. The format change is
noted in the README.

**M6. Provenance only trusts git for the checkout's own code.**
- New `_metautil_editable()` (line 2595) reads PEP 610
  `direct_url.json` `dir_info.editable`.
- `_metautil_provenance` (line 2611) runs
  `git rev-parse --show-toplevel HEAD --abbrev-ref HEAD`. It trusts the
  result only if the module is under `<toplevel>/src` or the install is
  editable.
- Otherwise it records `commit: None, commit_source: "installed"`. If
  git is unavailable on an editable install, it records
  `"unavailable"`.

Checks:
- real editable install: `commit 753b97e…`, `branch
  feature/solverfw-v2`, `dirty True`, `commit_source 'git'`;
- `__file__` pointed into `<repo>/.venv/lib/python3.12/site-packages`
  with editable forced False: `commit None, commit_source 'installed'`;
- module outside any repo: `commit_source 'installed'`.

**M7. One copy of the dry-run print block.** The sequential dry-run now
calls `_print_dry_run_case` (line 3168; the helper is at line 1711).
Before/after check on `fvm_1d_smoke_test.toml --dry-run --set
_run_mode=sequential` (216 lines both times, hex ids normalized): the
only diff is line 1, the M1 warning wording. Every case line is
identical.

One deliberate difference: a `_case_preproc` command is now labeled
`Preproc (dry-run)`. The old sequential code mislabeled it `Postproc`.
None of the three TOMLs uses preproc.

**M8. A multi-stage sweep writes one invocation record.** `run_sweep`
sets `is_stage = _run_dir_override is not None` (line 2930). A stage
does not build, write or print the invocation; its results carry
`invocation_ref` (line 2969), the path of the base-dir record. The
orchestrator writes the record once in the base dir, embeds it once in
the combined results, and prints `Invocation:` once.

Evidence: `multi_stage_local.toml --dry-run-materialize --set
_output_dir=/tmp/order3-fixup-14/ms` wrote exactly one file,
`/tmp/order3-fixup-14/ms/2026-10-15/_d16889ce/q8020_sweep_invocation.json`.
API dry run: combined `invocation` present; the `coarse` and `fine`
stages have no `invocation` key, and their `invocation_ref` is
`.../_0b2f9db4/q8020_sweep_invocation.json`.

**M9. The README no longer hard-codes this laptop's paths.** It now
documents `<checkout>/.venv/bin/q8020-sweep`, run from the checkout's
parent directory. This laptop's path appears once, as a labeled
example, and the example uses `./q8020-cfd-metautil/.venv/bin/q8020-sweep`
(that relative form was used for the re-runs below).

**Re-runs**, from cwd `/Users/agallojr/proj/src/q8020` with
`--set _output_dir=/tmp/order3-fixup-14/after_<name>`:

| TOML | Cases | `Command:` lines | `Postproc (dry-run)` lines | `find` count |
|---|---|---|---|---|
| CFL | 70 (parallel) | 70 | 70 | 0, dir absent |
| fvm smoke | 66 (parallel) | 66 | 66 | 0, dir absent |
| SQLS draft, 5 groups named | 146 (sequential) | 146 | 146 | 0, dir absent |

- `find ~/q8020 -newer <marker touched 2026-10-15T09:22:27Z>` = 0.
- Tests: 12 passed in 0.06 s.
- `py_compile` is clean, no added line is over 88 chars, and there is no
  trailing whitespace.

`git diff --stat`:

```
 README.md                                | 123 +++++++-
 src/q8020_cfd_metautil/sweep.py          | 485 +++++++++++++++++++++++++------
 tests/examples/*.toml (4 files, pre-existing, not mine) | 2 +- each
 6 files changed, 512 insertions(+), 104 deletions(-)
```

## 10. Rebase onto origin/main 2026-10-16T01:12Z-01:17Z

**Setup.** The operator decided item 14 goes to `main`. It was one local
commit, `3e88938`, based on `8ccab91`. `origin/main` had moved to
`d75de45` with four commits:
- `85c2220`: distributed MPI;
- `cdf4bbb`: multi-rank fix;
- `a1b2749`: synthesized srun launcher, `_env_exports`, recursive
  templates;
- `d75de45`: help text.

I ran `git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil rebase
origin/main`. The result is again one commit, with the same message.
Nothing was pushed, and `feature/solverfw-v2` is untouched at `753b97e`.

**The upstream changes that matter for item 14:**
- `_expand_templates_fixpoint` replaces the single-pass expansion.
- The re-merge rule changed: group-level `_` keys now beat globals, and
  only absent keys or `--set` keys are forced in from `[global]`.
- `_synthesize_launcher_prefix` prepends `srun -N .. -n ..` to the group
  executable in SLURM parallel mode.
- `_env_exports` reaches local and interactive runs through
  `_resolve_env_exports`, and SLURM runs through `export` lines in the
  sbatch.
- The sbatch is sized for one case when `_slurm_tasks_per_case > 1`.

**Conflicts and resolutions:**

1. `src/q8020_cfd_metautil/sweep.py`, the only textual conflict. It sat
   at the end of the `--set` loop, where item 14 had moved the loop into
   `_apply_overrides` and upstream had rewritten the comment above the
   expansion call (now `_expand_templates_fixpoint`).
   - Kept item 14's `return resolved_override_keys`, the new `run_sweep`
     signature, the `_apply_overrides(...)` call and
     `_fallback_postproc_venv(global_params, dry_run)`.
   - Kept upstream's fixpoint comment and the fixpoint calls.
2. `README.md` auto-merged with no conflict. Upstream's sections
   (recursive templates, the `_env_exports` table and prose, the
   `_slurm_tasks_per_case` / `_slurm_launcher` rows, distributed cases)
   sit beside the item-14 text. I checked that nothing contradicts.

**Semantic re-wiring** (no textual conflict, but needed so item 14 fits
the new code):

3. `_fallback_postproc_venv` now expands `_postproc_venv` with
   `_expand_templates_fixpoint`, consistent with recursive templates.
4. The multi-stage base `_output_dir` is expanded with
   `_expand_templates_fixpoint`, after `_apply_overrides`.
5. `_env_exports` now show in a dry run:
   - locally or interactive: `Env export: NAME=value` header lines;
   - SLURM plain dry run: `export NAME="value"  (_env_exports)` after
     the `#SBATCH` header.
   README sentence added.
6. The launcher synthesis needed no change. The synthesized prefix is
   part of `group_executable`, so the item-14 dry-run printer and the
   post-NVMe-rewrite printer show it.
7. `tests/test_sweep_launcher_env.py` is an upstream test that asserted
   on `pipeline_args.json` written by a plain `run_sweep(dry_run=True)`.
   Item 14 deliberately removed that write. The 10 dry-run calls now
   pass `dry_run=True, dry_run_materialize=True` through a
   `_MATERIALIZE` constant, and the module docstring says so. The
   assertions are unchanged. The non-dry `_env_exports` test is
   unchanged.

**Verification on the committed tree** (`9ce8669`):
- `py_compile` is clean.
- Full suite: `.venv/bin/python -m pytest -q -p no:cacheprovider tests`
  gives **43 passed in 3.71 s**. Upstream `origin/main` alone, run from
  a `git archive` export, also gives 43 passed.

Dry runs from cwd `/Users/agallojr/proj/src/q8020`, each with
`--set _postproc_venv=./q8020-cfd-metautil/.venv` and
`--set _output_dir=/tmp/metautil-rebase/<name>`:

| name | TOML and args | cases | `Command:` | `Postproc (dry-run)` | `/mnt/bb` commands | `#SBATCH` lines | `find` count |
|---|---|---|---|---|---|---|---|
| cfl | `fvm_cfl_sweeps.toml --dry-run` | 70, parallel | 70 | 70 | 0 | 0 | 0 |
| cflslurm | same, `--set _slurm=true` | 70, parallel (slurm) | 70 | 70 | 70 | 8 (`-N 70 -A ard189 -t 02:00:00 -C nvme -p batch`) | 0 |
| smoke | `tests/examples/fvm_1d_smoke_test.toml --dry-run` | 66, parallel | 66 | 66 | 0 | 0 | 0 |
| sqls | SQLS draft, 5 groups named | 146, sequential | 146 | 146 | 0 | 0 | 0 |

Multi-stage check: `multi_stage_local.toml --dry-run-materialize`
wrote exactly one file,
`/tmp/metautil-rebase/ms/2026-10-16/_50224be5/q8020_sweep_invocation.json`.
It has all 11 keys, and `metautil` reads
`{'version': '0.1.0', 'commit': '9ce8669122ff7e6dba84110434162dce64a04e01',
'branch': 'main', 'dirty': False, 'commit_source': 'git'}`.

Upstream launcher check on `tests/examples/all_directives_reference.toml`:
- Local dry run: 36 cases, an `Env export: Q8020_DEMO_VAR=1` line, 0
  entries written.
- `ideal --set _slurm=true --set _run_mode=parallel --set
  _slurm_tasks_per_case=16`:
  - `Command: bash -c "source .../.venv/bin/activate && srun -N 2 -n 16
    --ntasks-per-node=8 --exclusive python3 examples/smoke_test_solver.py ..."`;
  - `#SBATCH -N 2`;
  - `export Q8020_DEMO_VAR="1"  (_env_exports)`;
  - 0 entries written.

`find ~/q8020 -newer <marker>` = 0.

**Hygiene against origin/main:** in `src`, `README.md` and the test
file, no added line is over 88 chars and no line has trailing
whitespace. The 4 `tests/examples/*.toml` lines from the original commit
(the harvester-path fix) are TOML command strings of 104 and 163 chars.
They were already that long in the files they replace; PEP 8 does not
apply to TOML.

```
$ git log --oneline origin/main..main
9ce8669 Sweeper housekeeping: record the invocation, write nothing on dry-run, UTC date dir, venv fallback on dry-run only, fix harvester paths in the fvm examples
$ git diff --stat origin/main..main
 README.md                                | 125 +++++++-
 src/q8020_cfd_metautil/sweep.py          | 492 +++++++++++++++++++++++++------
 tests/examples/base_case.toml            |   2 +-
 tests/examples/base_case_hhl.toml        |   2 +-
 tests/examples/fvm_1d_smoke_test.toml    |   2 +-
 tests/examples/hhl_time_step_impact.toml |   2 +-
 tests/test_sweep_launcher_env.py         |  31 +-
 7 files changed, 539 insertions(+), 117 deletions(-)
```

**Doubts:**
- Under the new merge rule, a group that sets its own `_postproc_venv`
  keeps it. `_fallback_postproc_venv` checks only the `[global]` value,
  so a missing group-level venv is not caught.
- The dry-run printout for distributed (`_slurm_tasks_per_case > 1`)
  SLURM sweeps was checked only on the reference TOML, not on a real MPI
  case.
