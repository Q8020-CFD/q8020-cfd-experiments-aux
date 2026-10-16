# verify-14 — independent verification of work item 14 (sweeper housekeeping)

**VERDICT: PASS**

All six acceptance criteria hold on evidence. One pre-existing defect outside
the criteria was surfaced and is reported as Finding 1 (multi-stage TOMLs
ignore `--set _output_dir`; with the new `--dry-run-materialize` that writes
into the TOML's real `_output_dir`). Three stray 1201-byte JSON files landed
under `/Users/agallojr/q8020/` as a result of that defect during this
verification; I did not delete them (rule: never write under `~/q8020`). See
Finding 1 for the exact paths and the one-line cleanup.

- Verifier: independent subagent, read-only in all repos.
- Verified: 2026-10-15T08:18Z to 2026-10-15T08:31Z.
- Subject: uncommitted working-tree changes in
  `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil` (branch
  `feature/solverfw-v2`, HEAD `753b97eb8b2ff1235ac2a59baa94ebab7709251c`),
  files `src/q8020_cfd_metautil/sweep.py` (+217/-19 lines) and `README.md`
  (+76/-8 lines). Four `tests/examples/*.toml` are modified by an earlier item
  (2 lines each) and were not reviewed.
- Tools: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`
  (only `--dry-run` / `--dry-run-materialize`), cwd
  `/Users/agallojr/proj/src/q8020`, `_output_dir` always overridden to
  `/tmp/order3-verify-14/<name>`. Scratch deleted at the end.
- Line numbers below refer to the working-tree `sweep.py` (post-change).
- Wall times are from bash `time` (real), on the laptop.

---

## Criterion 1 — README

Command: `git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil diff -- README.md`
plus `grep -n -- '--groups' README.md`.

Quoted lines (verbatim from the working-tree README):

Positional groups and `_`-prefixed groups:

```
q8020-sweep sweep_config.toml ideal shots     # only these groups
q8020-sweep sweep_config.toml _smoke          # _-prefixed group, by name
```
```
**Groups** are positional arguments after the TOML (there is no
`--groups` flag).  With no group named, every group runs except those
whose name starts with `_`; a `_`-prefixed group (e.g. `_smoke`) runs
only when named explicitly.  An unknown group name is an error.
```

The only remaining `--groups` occurrence is that sentence (README line 205,
`grep -c -- '--groups' README.md` = 1); the stale usage line
`q8020-sweep sweep_config.toml --groups ideal shots` is gone.

Laptop path, not on PATH:

```
**Where it is installed.**  `q8020-sweep` is a console script of this
package and is not on `PATH` by default.  On the laptop call the copy in
this repo's venv by absolute path:
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`.
The install is editable, so it runs whatever branch the checkout is on.
```

`--set KEY=VALUE` and coercion:

```
**`--set KEY=VALUE`** overrides or adds a `[global]` key before
`${VAR}` template expansion.  Repeatable (`--set _output_dir=/tmp
--set _slurm=false`).  Coercion: `true`/`false` (any case) become bool,
then int is tried, then float, otherwise the value stays a string.  A
bare key matches an existing dashed variant (`--set shots=0` overrides
`"-shots"`), and `--set` values win over group-level copies of the same
key.
```

UTC date directory:

```
`<date>` is the sweep start date in **UTC** (`yyyy-mm-dd`).  Behavior
change 2026-10-15: earlier sweeps used the local date, so e.g. the
Frontier run submitted 2026-04-05T00:10Z landed under `2026-04-04/`.
```

`_postproc_venv` fallback:

```
**`_postproc_venv` fallback.**  If the TOML sets `_postproc_venv` (the
venv a `_case_postproc` command activates, e.g. `source
${_postproc_venv}/bin/activate && ...`) to a directory that does not
exist, the sweeper warns, naming the configured path and the
replacement, and uses the running interpreter's own environment
(`sys.prefix`, i.e. the venv `q8020-sweep` was started from) instead.
```

Also documented: the `usage:` block with `[--dry-run] [--dry-run-materialize]
[--set KEY=VALUE] toml_file [groups ...]`, the `--dry-run` /
`--dry-run-materialize` semantics, the `invocation` provenance keys, and
`q8020_sweep_invocation.json` in the directory-layout tree.

Accuracy caveat (not a criterion failure, see Finding 2): the `--set shots=0`
example only holds when `"-shots"` is in `[global]`; in all three fvm TOMLs
`"-shots"` is group-level and the observed result is `--shots 0`.

**PASS.**

---

## Criterion 2 — command-line provenance

### 2a. Materialized record

Command (cwd `/Users/agallojr/proj/src/q8020`):

```
date -u   -> 2026-10-15T08:24:53Z   (before)
/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep \
  q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml \
  --dry-run-materialize --set _output_dir=/tmp/order3-verify-14/mat
date -u   -> 2026-10-15T08:24:53Z   (after)
```

Wall 0.210 s, exit 0. File written:
`/tmp/order3-verify-14/mat/2026-10-15/_00bc04e5/q8020_sweep_invocation.json`,
verbatim:

```json
{
  "command_line": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml --dry-run-materialize --set _output_dir=/tmp/order3-verify-14/mat",
  "argv": [
    "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep",
    "q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml",
    "--dry-run-materialize",
    "--set",
    "_output_dir=/tmp/order3-verify-14/mat"
  ],
  "python_executable": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python3",
  "toml_path": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml",
  "toml_path_resolved": "/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml",
  "cwd": "/Users/agallojr/proj/src/q8020",
  "groups": null,
  "overrides": {
    "_output_dir": "/tmp/order3-verify-14/mat"
  },
  "start_time_utc": "2026-10-15T08:24:53.475653Z",
  "user": {
    "username": "agallojr",
    "hostname": "MH-DT9TLJQR2V"
  },
  "metautil": {
    "version": "0.1.0",
    "commit": "753b97eb8b2ff1235ac2a59baa94ebab7709251c",
    "branch": "feature/solverfw-v2",
    "dirty": true
  }
}
```

Key-by-key check:

| key | expected | observed | ok |
|---|---|---|---|
| `command_line` | shell-joined `sys.argv` | matches the command typed (relative TOML path preserved) | yes |
| `argv` | 5 tokens | 5 tokens, identical | yes |
| `toml_path` | absolute | `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml` | yes |
| `toml_path_resolved` | symlinks resolved | same (no symlinks on that path) | yes |
| `cwd` | `/Users/agallojr/proj/src/q8020` | same | yes |
| `overrides` | raw `--set` strings | `{"_output_dir": "/tmp/order3-verify-14/mat"}` | yes |
| `groups` | `null` when none named | `null`; with `shots` named (coerce run) -> `["shots"]` | yes |
| `start_time_utc` | ISO 8601 UTC within 1 min of clock | `2026-10-15T08:24:53.475653Z` vs `date -u` 08:24:53Z before and after (delta < 1 s) | yes |
| `metautil.version` | pyproject `version = "0.1.0"` | `0.1.0` | yes |
| `metautil.commit` | `git rev-parse HEAD` = `753b97eb8b2ff1235ac2a59baa94ebab7709251c` | identical | yes |
| `metautil.branch` | `feature/solverfw-v2` | identical | yes |
| `metautil.dirty` | true (uncommitted changes) | `true` | yes |

### 2b. Code path into the final sweep meta (read-only; a real sweep was not run)

`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/src/q8020_cfd_metautil/sweep.py`:

- `make_invocation_record()` lines 2576-2599 builds the dict above
  (`shlex.join(argv)`, `Path(toml_path).expanduser().absolute()` /
  `.resolve()`, `os.getcwd()`, `dict(overrides)`, `_get_iso_timestamp()`
  which is `datetime.now(timezone.utc).isoformat()` with `Z`, line 64-66,
  `make_user_meta()`, `_metautil_provenance()` lines 2545-2573).
- `INVOCATION_FILE = "q8020_sweep_invocation.json"` line 2601;
  `write_invocation_record()` lines 2604-2614.
- `main()` line 3627 builds the record from `sys.argv` once and passes it
  to both entry points (lines 3651 and 3689).
- `run_sweep()`: line 2817-2820 falls back to building it if `None`; line
  2821-2822 `if not dry_run or dry_run_materialize: write_invocation_record(run_dir, invocation)`;
  line 2849 `"invocation": invocation,` inside the `results` dict (lines
  2842-2851); line 3402-3405 `if not dry_run: results_file = run_dir / f"q8020_sweep_meta{workflow_id}.json"; json.dump(results, ...)`.
  So the same dict object is in the final sweep meta of every real sweep.
- `_run_multi_stage_sweep()`: lines 3441-3448 (build + side file in
  `base_run_dir`), line 3473 `"invocation": invocation,` in
  `all_stage_results`, lines 3546-3551 dumped to
  `base_run_dir / f"q8020_sweep_meta{workflow_id}.json"`. Each stage's
  `run_sweep` also receives the same `invocation` (line 3525), so stage metas
  carry it too.

Note: `start_time_utc` is stamped in `main()` (line 3627), a few ms before
`results["start_time"]` (line 2814). Harmless; both are UTC ISO 8601.

**PASS.**

---

## Criterion 3 — dry-run hygiene

All runs from cwd `/Users/agallojr/proj/src/q8020` with
`SWEEP=/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep`.
Counts via `grep -c 'Command:'` / `grep -c 'Postproc (dry-run)'` on captured
stdout; emptiness via `find <dir> | wc -l`.

| run | TOML | mode | wall | cases | `Command:` | `Postproc (dry-run):` | `find _output_dir \| wc -l` |
|---|---|---|---|---|---|---|---|
| (a) | `.../fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml` `--dry-run` | parallel | 0.841 s | 70 (time_steps 50 + more_iters 20) | 70 | 70 | 0 |
| (a') | same `--set _slurm=true` | parallel (slurm) | 0.145 s | 70 | 70 | 70 | 0 |
| (b) | `.../tests/examples/fvm_1d_smoke_test.toml` `--dry-run` | parallel | 0.143 s | 66 (1+1+4+10+50) | 66 | 66 | 0 |
| (c) | `.../sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml _smoke sqls_shots sqls_cfl sqls_nelem hhl_matched --dry-run` | sequential | 0.139 s | 146 (1+70+50+15+10) | 146 | 146 | 0 |

Full TOML paths:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`,
`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/fvm_1d_smoke_test.toml`,
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fvm_sqls_aiaa_sweeps.DRAFT.toml`.

(a) selects SLURM via `_slurm = false` in `[global]` (TOML line 22, header
comment "enable with --set _slurm=true"), so `--set _slurm=true` is the right
switch; the banner changed to `[parallel (slurm)]`. SLURM dry-run tail,
verbatim (ANSI stripped):

```
  Would pack: /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv -> /tmp/order3-verify-14/cfl_slurm/2026-10-15/_77698b57/Users_agallojr_proj_src_q8020_fvm_euler_1d_solver_.venv.tar.gz
  Would pack: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv -> /tmp/order3-verify-14/cfl_slurm/2026-10-15/_77698b57/Users_agallojr_proj_src_q8020_q8020-cfd-metautil_.venv.tar.gz
Would generate: /tmp/order3-verify-14/cfl_slurm/2026-10-15/_77698b57/q8020_sweep.sbatch
  #SBATCH -J q8020_sweep
  #SBATCH -A ard189
  #SBATCH -t 02:00:00
  #SBATCH -N 70
  #SBATCH -C nvme
  #SBATCH -p batch
  #SBATCH -o /tmp/order3-verify-14/cfl_slurm/2026-10-15/_77698b57/slurm_%j.out
  #SBATCH -e /tmp/order3-verify-14/cfl_slurm/2026-10-15/_77698b57/slurm_%j.err
70 cases in one job
```

First case block of (a), verbatim:

```
  Prepared: time_steps_0_trial_0 (87336b65)
    Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/order3-verify-14/cfl/2026-10-15/_82e302eb/time_steps_0/trial_0_87336b65"
  Postproc (dry-run): bash -c "source /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order3-verify-14/cfl/2026-10-15/_82e302eb/time_steps_0/trial_0_87336b65/q8020_case_postproc_87336b65.json"
```

(c) group headers, verbatim: `=== Group: _smoke (1 cases) ===`,
`=== Group: sqls_shots (70 cases) ===`, `=== Group: sqls_cfl (50 cases) ===`,
`=== Group: sqls_nelem (15 cases) ===`, `=== Group: hhl_matched (10 cases) ===`;
summary `Total: 146 (dry run)`. No `Pruned case` lines on stderr (0).

### `--dry-run-materialize` on (b)

Same run as Criterion 2a (wall 0.210 s). Tree under
`/tmp/order3-verify-14/mat`: `find | wc -l` = 142 = 75 directories + 67
files. Files: 66 `pipeline_args.json` (one per case: 1 + 1 + 4 + 10 trial dirs
+ 50 trial dirs) + 1 `q8020_sweep_invocation.json`. Directories: 75 = 3
(`mat`, `2026-10-15`, `_00bc04e5`) + 6 trial-parent dirs + 66 case dirs.
`*.tar.gz` = 0, `*.sbatch` = 0 (parallel, non-SLURM), `q8020_sweep_meta*` = 0,
no TOML copy, no `q8020_expanded_cases.json` (those are `if not dry_run`,
lines 2824-2835).

SLURM-mode materialize (the coercion probe run, `shots` group,
`--set _slurm=true`, wall 0.156 s) wrote exactly 3 files:
`q8020_sweep.sbatch`, `q8020_sweep_invocation.json`,
`cc058a14/pipeline_args.json`; 0 tarballs.

Code path (sbatch never called in any dry run):

- `_finalize_slurm()` line 1933 `if dry_run: ... return None` precedes the
  only compute `subprocess.run(["sbatch", ...])` at lines 1939-1940.
- `_pack_venvs()` line 1464 `if dry_run:` prints `Would pack:` and
  `continue`s before `tarfile.open` at line 1475.
- `_finalize_local_parallel()` line 1306 `if dry_run:` prints `Would launch:`
  and returns before `subprocess.Popen` (line 1342).
- `_finalize_slurm_postproc()` writes `q8020_postproc.sbatch` unconditionally
  (lines 2109-2112) before its `if dry_run: return None` (line 2120), but its
  only caller is guarded by `use_slurm and slurm_job_id and _slurm_postproc_job`
  (lines 3371-3375) and `slurm_job_id` is `None` on every dry run, so it is
  unreachable in dry-run mode.
- `_build_case_launch_info(write_files=...)` lines 1065-1066 and 1117-1119;
  `_collect_parallel_cases(dry_run, materialize)` line 1681
  `write_files=(not dry_run) or materialize`; `main()` lines 3609-3610 make
  `--dry-run-materialize` imply `--dry-run`.

### Date directory is UTC

Code: `run_sweep()` line 2795 and `_run_multi_stage_sweep()` line 3437 both
read `date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")` (the diff
replaced `datetime.now()` in both).

Observation: the materialized run's date dir is `2026-10-15` and `date -u` was
2026-10-15. Because local EDT date equalled the UTC date at 08:24Z, I also ran
a discriminating check under `TZ=Pacific/Honolulu` (UTC-10):

```
TZ=Pacific/Honolulu date  -> 2026-10-14T22:26:55-1000     (UTC 2026-10-15T08:26:55Z)
TZ=Pacific/Honolulu $SWEEP .../fvm_1d_smoke_test.toml shots --dry-run --set _output_dir=/tmp/order3-verify-14/tz
  Output directory: /tmp/order3-verify-14/tz/2026-10-15/_80ded7db          (run_sweep path)
TZ=Pacific/Honolulu $SWEEP .../tests/examples/multi_stage_local.toml --dry-run --set _output_dir=/tmp/order3-verify-14/ms
  Output directory: /Users/agallojr/q8020/2026-10-15/_1e375fd8             (multi-stage path; see Finding 1 for the path)
```

Both paths produce the UTC date (`2026-10-15`) while the process-local date
was 2026-10-14. (Both of those dry-runs wrote nothing: `find` count 0 under
scratch; nothing new under `~/q8020` from the plain `--dry-run`.)

**PASS.**

---

## Criterion 4 — `_postproc_venv` fallback

CFL TOML line 19: `_postproc_venv = "./.venv"`; `/Users/agallojr/proj/src/q8020/.venv`
does not exist. Run (a) above, stderr verbatim (ANSI stripped):

```
Warning: _postproc_venv ./.venv (/Users/agallojr/proj/src/q8020/.venv) does not exist; falling back to the running interpreter's environment /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv
```

Names the configured path (relative and absolute) and the replacement. The
postproc lines use the fallback:
`Postproc (dry-run): bash -c "source /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/activate && ..."`
(70 of 70 lines). In SLURM mode the fallback also flows into
`_slurm_pack_venvs` (`Would pack: /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv -> ...`).

With the override (wall 0.231 s):

```
$SWEEP q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml --dry-run \
  --set _output_dir=/tmp/order3-verify-14/cfl_venv --set _postproc_venv=./q8020-cfd-metautil/.venv
```

stderr: 0 bytes (no warning). First postproc line:
`Postproc (dry-run): bash -c "source ./q8020-cfd-metautil/.venv/bin/activate && python3 ./q8020-cfd-experiments/.../fvm_euler_1d_solver_harvester.py /tmp/order3-verify-14/cfl_venv/2026-10-15/_9fdad6b6/time_steps_0/trial_0_4d186d3c/q8020_case_postproc_4d186d3c.json"`.
70 `Command:` / 70 `Postproc` lines, `find` count 0.

Code: `_fallback_postproc_venv()` lines 2617-2645, called at line 2710 after
`--set` application and before template expansion; falls back to
`sys.prefix` only if `<prefix>/bin/activate` exists, else warns and leaves the
value unchanged.

**PASS.**

---

## Criterion 5 — solverfw untouched, registry hooks untouched, tests

```
git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil diff --stat -- src/q8020_cfd_metautil/solverfw
```
Output: empty (0 lines).

Registry-pruning hooks in `sweep.py` (working-tree line numbers):
`_REGISTRY_SLOTS` 2161-2172, `PRUNED_CONFLICTS` 2179, `reset_pruned_conflicts()`
2182, `pruned_conflicts_provenance()` 2187-2196, `_case_chain()` 2199-,
the `expanded_cases = _prune_expanded_cases(expanded_cases)` call 2305, and
`_prune_expanded_cases()` 2310-2365 (lazy `from q8020_cfd_metautil.solverfw import REGISTRY`,
`plugins_euler/plugins_chlbm/q8020_sqls_encode.plugins register_all()`,
`registry.check_cell(chain)`). `git diff -U0` hunk headers for `sweep.py`
(new-file ranges) are: 15, 19, 1049-1128, 1663-1716, 1837-1927, 2545-2647,
2656-2668, 2710-2711, 2794-2795, 2816-2823, 2849, 2873-2874, 2924, 3302,
3423-3449, 3472-3473, 3524-3525, 3583-3689. No hunk falls in 2157-2365.

Tests (the repo has one test module, `tests/test_slurm_postproc.py`, run with
pytest):

```
cd /Users/agallojr/proj/src/q8020/q8020-cfd-metautil && ./.venv/bin/python -m pytest tests -q -p no:cacheprovider
............                                                             [100%]
12 passed in 0.04s
```
Wall 0.540 s.

**PASS.**

---

## Criterion 6 — nothing committed

Checked at start (2026-10-15T08:18Z) and again after all runs (08:30Z):

```
git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil log -1 --oneline
753b97e solverfw v2c: QuantumLinearSystemSolver + §9 acceptance sweep
git -C /Users/agallojr/proj/src/q8020/q8020-cfd-metautil status --short
 M README.md
 M src/q8020_cfd_metautil/sweep.py
 M tests/examples/base_case.toml
 M tests/examples/base_case_hhl.toml
 M tests/examples/fvm_1d_smoke_test.toml
 M tests/examples/hhl_time_step_impact.toml
```

`--untracked-files=all` adds nothing outside `.venv`; `git stash list` is
empty; branch `feature/solverfw-v2`.

**PASS.**

---

## Findings

### Finding 1 (pre-existing defect, exposed by the new materialize mode): multi-stage sweeps ignore `--set _output_dir`

`_run_multi_stage_sweep()` derives the base run dir from the raw TOML
`[global]` (`output_dir_str = outer_global.get("_output_dir", "./sweep_results")`,
line 3436; identical at HEAD line 3266, so not introduced by item 14) and
never applies `--set` overrides to it; each stage then gets
`_run_dir_override=stage_run_dir` (line 3528), so the per-stage `run_sweep`
override logic is bypassed too. Result: with
`multi_stage_local.toml` (`_output_dir = "~/q8020"`) and
`--set _output_dir=/tmp/order3-verify-14/...`, the banner reads
`Output directory: /Users/agallojr/q8020/2026-10-15/_1e375fd8`.

A plain `--dry-run` still writes nothing. But the NEW `--dry-run-materialize`
path (lines 3447-3448 and, per stage, 2821-2822) wrote three invocation
records into the production tree during this verification, at
2026-10-15T08:29:01Z:

```
/Users/agallojr/q8020/2026-10-15/_78bdc328/q8020_sweep_invocation.json          1201 bytes
/Users/agallojr/q8020/2026-10-15/_78bdc328/coarse/q8020_sweep_invocation.json   1201 bytes
/Users/agallojr/q8020/2026-10-15/_78bdc328/fine/q8020_sweep_invocation.json     1201 bytes
```

(The record's own `overrides` field honestly says
`{"_output_dir": "/tmp/order3-verify-14/msmat"}`, which is what makes the
mismatch obvious.) I did not delete them, per the no-writes-under-`~/q8020`
rule. They are the only new entries under `~/q8020` since 08:18Z
(`find /Users/agallojr/q8020 -newer <first log>` lists exactly that
`_78bdc328` subtree; `/Users/agallojr/q8020/2026-10-15/` contained nothing
else at 08:29Z). Cleanup, for the operator:

```
rm -rf /Users/agallojr/q8020/2026-10-15/_78bdc328 && rmdir /Users/agallojr/q8020/2026-10-15 2>/dev/null
```

(the `rmdir` only succeeds if the date dir is still otherwise empty).

Impact on the paper sweeps: none of the three fvm TOMLs is multi-stage, so
the SQLS runs are unaffected. The README sentence "`--set KEY=VALUE` overrides
or adds a `[global]` key" is false for `_output_dir` in multi-stage TOMLs.
Suggested fix: apply the `--set` overrides (at least `_output_dir`) to
`outer_global` before line 3436, or have `main()` pass an overridden copy.

### Finding 2: README `--set shots=0` example overclaims for the fvm TOMLs

The dashed-variant resolution (lines 2685-2692, pre-existing) searches only
`global_params`. In `fvm_cfl_sweeps.toml`, `fvm_1d_smoke_test.toml` and
`fvm_sqls_aiaa_sweeps.DRAFT.toml`, `"-shots"` is set only in groups (e.g.
SQLS draft lines 126, 137, 149, 172, 187). Observed with
`fvm_1d_smoke_test.toml shots --dry-run-materialize --set shots=0 --set _slurm=true --set _slurm_walltime=1.5`:

```
Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver HHL -localdt -noshow --shots 0 -outdir /tmp/order3-verify-14/coerce/2026-10-15/_043f1b34/cc058a14"
```

The group's `-shots 1024` was dropped (merge code lines 2730-2745 pops the
dashed variant for an override key) and a bare `shots` key was emitted as
`--shots 0`, which `nozzle_1d_solver.py` (option `-shots`) would not accept.
Behavior is pre-existing; the new README text documents it inaccurately.
Suggested wording: "a bare key replaces an existing dashed variant only when
that variant is set in `[global]`; otherwise pass the dashed form
(`--set -shots=0`)". Not a criterion failure (coercion rules themselves are
documented correctly and verified below).

### `--set` coercion (probe result)

From the same materialized run, `pipeline_args.json` -> `case_params`
(JSON types):

```
'shots': 0 (int)
'_slurm': True (bool)
'_slurm_walltime': 1.5 (float)
```

and the generated sbatch shows `#SBATCH -t 1.5`. Bool coercion is real, not
just truthiness: `--set _slurm=true --set _slurm=false` (last wins) gives
banner `[parallel]`, whereas the non-coercible string `--set _slurm=yes` gives
`[parallel (slurm)]` (truthy string) and `--set _slurm=0` (int) gives
`[parallel]`. Matches the README's stated order: true/false, int, float,
string. The invocation record keeps the raw strings
(`"overrides": {"shots": "0", "_slurm": "true", "_slurm_walltime": "1.5", ...}`),
as documented.

### Provenance side-file name vs harvester patterns

`FRAGMENT_PATTERN = ^q8020_([a-z_]+)_(?:([a-f0-9]{8})_)?(\d+)\.json$` and
`SWEEP_FRAGMENT_PATTERN = ^q8020_sweep_([a-z_]+)_(?:([a-f0-9]{8})_)?(\d+)\.json$`
(`meta_fragment.py` lines 53-54; used by `harvest.py` lines 99 and 160 and
`meta_fragment.py` 434-436). Both require a trailing `_<digits>.json`.
`q8020_sweep_invocation.json` has no digit suffix, so it matches neither
(tested with `re`: both `False`). The code comment at lines 2608-2609 states
this rationale. No collision. Note that a suffixed variant
(`q8020_sweep_invocation_1.json`) WOULD match, so the fixed name must stay
unsuffixed.

Out-of-scope observation (pre-existing): `q8020_sweep_meta_<wfid>.json`
matches both patterns when the 8-hex workflow id happens to be all digits
(e.g. `q8020_sweep_meta_12345678.json` -> `True`, section `meta`), probability
(10/16)^8 = 2.3 % per sweep. Section `meta` is not in `VALID_SECTIONS`, so
`meta_fragment.py` skips it (line 444-445); `harvest._next_results_index`
only counts section `results`. Harmless today, but fragile.

### Hygiene of added `sweep.py` lines

`git diff -U0 -- src/q8020_cfd_metautil/sweep.py | grep '^+'`: 217 added
lines; 0 lines longer than 88 characters; 0 lines with trailing whitespace.
New imports `import importlib.metadata` (line 15) and `import shlex` (line 19)
sit in the stdlib group at the top, alphabetically. (The `import
importlib.metadata` at line 156 is inside a pre-existing string literal, not a
real import.) `pyflakes`/`pylint` are not installed in the venv, so no lint
run.

### Minor observations (no action required for item 14)

- `results["timestamp"]` (line 2837, `datetime.now().strftime("%Y%m%d_%H%M%S")`)
  and two fragment timestamps (lines 580, 859, `datetime.now().isoformat()`)
  are still local time without offset; pre-existing, not part of this item,
  but inconsistent with the UTC convention now used for the date dir.
- `_print_dry_run_case()` line 1702 evaluates `cmd[1]` only when
  `cmd[0] == "bash"`; a `_script` of literally `bash` with no args would
  IndexError. Theoretical; same shape as the pre-existing sequential printer
  at line 3044.
- The README says `--dry-run-materialize` writes the run dir, case dirs,
  `pipeline_args.json`, sbatch and invocation record; it indeed does NOT write
  the TOML copy or `q8020_expanded_cases.json` (guarded by `if not dry_run`),
  consistent with the text.

---

## Not checked, and why

- A real (non-dry) sweep end-to-end, so the `invocation` key physically
  inside `q8020_sweep_meta<wf_id>.json` was verified by code reading only
  (Criterion 2b), not by observing a file. Launching a sweep was prohibited.
- SLURM submission itself (`sbatch`) and venv packing: verified unreachable
  in dry-run by code reading and by the absence of tarballs; no Frontier
  access.
- Whether `nozzle_1d_solver.py` rejects `--shots` (Finding 2): inferred from
  its `-shots` option name; the solver was not run.
- The four modified `tests/examples/*.toml` files (earlier item).
- Lint (`pyflakes`/`pylint`) — not installed in the metautil venv; no
  installs allowed.
- Behaviour on a non-git (wheel) install of metautil
  (`metautil.commit/branch/dirty` null path) — only the editable checkout
  was available.

## Scratch

`/tmp/order3-verify-14/` (728 KB: logs, `mat/`, `coerce/`) deleted after this
report was written. No other file in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`
was created or modified.
