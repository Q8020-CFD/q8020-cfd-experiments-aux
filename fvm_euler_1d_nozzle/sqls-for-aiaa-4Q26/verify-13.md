VERDICT: PASS

# verify-13 — independent verification of work item 13 (stale harvester path)

- Verifier run: 2026-10-15T03:07:26Z to 2026-10-15T03:16Z (UTC)
- Experiments repo: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments` (main @ `6f646617`)
- Metautil repo: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil` (feature/solverfw-v2 @ `753b97e`)
- Tools: `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep` (dry-run only),
  `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python` (Python 3.12.10)
- Scratch: `/tmp/order1-verify-13/` (deleted at end). No `build-*.md`, `verify-*.md`,
  `reproduce-*.md` or `STATUS.md` was opened (a few lines of STATUS.md / build-13.md
  surfaced as hits of the required `grep -rn codes/fvm_euler_1d_nozzle aux/`; they were
  not read further).
- Nothing was edited, added, committed, stashed or checked out in either repo. Nothing was
  written under `results/`. The only file created is this one.

## Criterion 1 — path references and diff hygiene: PASS

Command (cwd `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments`):

    git diff --stat
    git diff
    grep -rn codes/fvm_euler_1d_nozzle aux/
    grep -rn --exclude-dir=.git --exclude-dir=results codes/fvm_euler_1d_nozzle . | grep -v '^./aux/'

Observed `git diff --stat`:

    aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml        |   2 +-
    aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml   |   4 +-
    .../fvm_euler_1d_nozzle/backend_meta_harvester.py  |   3 +-
    .../fvm_euler_1d_solver_harvester.py               | 268 ++++++++++++++++++---
    .../fvm_euler_1d_nozzle/harvest_lugo_all.sh        |   2 +-

Per-file check of the four files named by the criterion (diff content only):

| File (absolute) | Diff | Beyond the path change? |
|---|---|---|
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml` | line 37: `${_experiment_dir}/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` -> `${_experiment_dir}/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` | no (1 line) |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml` | lines 7-8: both `_case_postproc` entries `q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/...` -> `q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/...` | no (2 lines) |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/harvest_lugo_all.sh` | line 22: `HARVESTER_DIR="/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/codes/fvm_euler_1d_nozzle"` -> `HARVESTER_DIR="/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle"` | no (1 line); Frontier prefix `/ccs/home/agallojr/proj/src/q8020/` preserved; `bash -n` exit 0 |
| `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py` | docstring lines 9-10: `python q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/backend_meta_harvester.py <postproc_json>` -> `python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/\\` + newline + `backend_meta_harvester.py <postproc_json>` | no (docstring only; see finding F6 on the wrap) |

`grep -rn codes/fvm_euler_1d_nozzle aux/` hits (18 lines), all within the two allowed classes:

- (a) `aux/Z-Keep/input/cases/_smoke_tests/slurm_parallel.toml:19,20` and
  `aux/Z-Keep/input/cases/_smoke_tests/local_parallel.toml:12,13` — holding area, untouched.
- (b) Markdown under `aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`: `WORKPLAN.md:41,93`,
  `05-sweep-mechanism.md:87,172,236,404,472-474,480,481`, `STATUS.md:69,76`, `build-13.md:20-23`.

No other hit anywhere in the experiments tree outside `aux/` (broader grep excluding
`results/` and `.git` returned only the same `aux/` lines). PASS.

Trailing whitespace in the four edited files and the new example: none (`grep -n ' $'` exit 1).

Note: a fifth modified file, `fvm_euler_1d_solver_harvester.py` (+243/-36 lines of logic), is
in the working tree. It is not among the four files this criterion names and carries no path
change; it is reported as finding F1, not as a criterion failure.

## Criterion 2 — dry-run of both experiments TOMLs: PASS

Required cwd: `/Users/agallojr/proj/src/q8020` (the TOMLs use `./fvm_euler_1d_solver`,
`./q8020-cfd-experiments`, `./q8020-cfd-metautil`; the sweeper resolves relative paths against
`os.getcwd()`, not the TOML's directory). `_output_dir` was overridden to `/tmp` so nothing could
land in `~/q8020` or either repo. ANSI colour codes stripped from the quoted output.

### 2a. `fvm_cfl_sweeps.toml`, sequential (writes nothing)

    cd /Users/agallojr/proj/src/q8020
    /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep --dry-run \
      --set _output_dir=/tmp/order1-verify-13/out/cfl_seq --set _run_mode=sequential \
      q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml

Started 2026-10-15T03:12:15Z; exit 0; wall 0.175 s; 220 output lines.
Cases expanded: 70 (`time_steps` 50 = 5 cfl x 10 trials; `more_iters` 20 = 2 cfl x 10 trials).
`Postproc (dry-run)` lines: 70, all 70 contain the new path, 0 contain `codes/fvm_euler_1d_nozzle`.
Files written under `/tmp/order1-verify-13/out/cfl_seq`: 0.

First lines, verbatim:

    Running sweep: 70 cases in 2 groups [sequential]
    Output directory: /tmp/order1-verify-13/out/cfl_seq/2026-10-14/_3f1fe368

    === Group: time_steps (50 cases) ===
      Case: time_steps_0_trial_0
        Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/order1-verify-13/out/cfl_seq/2026-10-14/_3f1fe368/time_steps_0/trial_0_fda7b077"
      Postproc (dry-run): bash -c "source ./.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order1-verify-13/out/cfl_seq/2026-10-14/_3f1fe368/time_steps_0/trial_0_fda7b077/q8020_case_postproc_fda7b077.json"
      Case: time_steps_0_trial_1
        Command: bash -c "source ./fvm_euler_1d_solver/.venv/bin/activate && python3 ./fvm_euler_1d_solver/nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow -shots 150000 -iters 15 -initers 1 -cfl 1 -outdir /tmp/order1-verify-13/out/cfl_seq/2026-10-14/_3f1fe368/time_steps_0/trial_1_c6e2b2d2"
      Postproc (dry-run): bash -c "source ./.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order1-verify-13/out/cfl_seq/2026-10-14/_3f1fe368/time_steps_0/trial_1_c6e2b2d2/q8020_case_postproc_c6e2b2d2.json"
      Case: time_steps_0_trial_2
      ...
    === Summary ===
    Total: 70 (dry run)

### 2b. `fvm_cfl_sweeps.toml`, DEFAULT mode (`_run_mode = "parallel"` in the TOML)

    cd /Users/agallojr/proj/src/q8020
    /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep --dry-run \
      --set _output_dir=/tmp/order1-verify-13/out/cfl_par \
      q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml

Started 2026-10-15T03:13:47Z; exit 0; wall 0.238 s; 151 lines; `Total: 70 (dry run)`.
In parallel mode the dry-run prints `Prepared: <case> (<id>)` and `Would launch: ... -m
q8020_cfd_metautil.sweep_worker .../pipeline_args.json` instead of per-case `Postproc` lines,
and it DOES write: 80 directories and 70 `pipeline_args.json` files under
`/tmp/order1-verify-13/out/cfl_par/2026-10-14/_9db51d9d/` (`_build_case_launch_info` in
`sweep.py` lines 1061 and 1112 mkdir and write unconditionally). Each `pipeline_args.json` carries
the new path, e.g. `"case_postproc": ["source ./.venv/bin/activate && python3
./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py"]`.
See finding F4.

### 2c. `fvm_euler_1d_nozzle.toml` (no `_run_mode`, so sequential; writes nothing)

    cd /Users/agallojr/proj/src/q8020
    /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep --dry-run \
      --set _output_dir=/tmp/order1-verify-13/out/nozzle \
      q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle.toml

Started 2026-10-15T03:12:15Z; exit 0; wall 0.097 s; 30 lines.
Cases expanded: 4 (`fvm_1d_nelem_5_smoke`, `fvm_1d_nelem_5_15`, `fvm_1d_nelem_5_sv_exact`,
`fvm_1d_nelem_5_sv_shots`; the `_smoke_test` and `_fake_quick` groups are dropped by design,
`sweep.py:2613` filters `_`-prefixed groups). `Postproc (dry-run)` lines: 8 (2 per case), all 8
with the new path, 0 stale. Files written under `/tmp/order1-verify-13/out/nozzle`: 0.

First case, verbatim:

    Running sweep: 4 cases in 4 groups [sequential]
    Output directory: /tmp/order1-verify-13/out/nozzle/2026-10-14/_05b96302

    === Group: fvm_1d_nelem_5_smoke (1 cases) ===
      Case: fvm_1d_nelem_5_smoke
        Command: bash -c "source /Users/agallojr/proj/src/q8020/../fvm_euler_1d_solver/.venv/bin/activate && python ../fvm_euler_1d_solver/nozzle_1d_solver.py -linsolver HHL -nelem 5 -localdt -noshow -shots 150000 -iters 1 -initers 1 -outdir /tmp/order1-verify-13/out/nozzle/2026-10-14/_05b96302/ce9f9893"
      Postproc (dry-run): python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order1-verify-13/out/nozzle/2026-10-14/_05b96302/ce9f9893/q8020_case_postproc_ce9f9893.json
      Postproc (dry-run): python q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/backend_meta_harvester.py /tmp/order1-verify-13/out/nozzle/2026-10-14/_05b96302/ce9f9893/q8020_case_postproc_ce9f9893.json

Note the solver venv resolves to `/Users/agallojr/proj/src/q8020/../fvm_euler_1d_solver/.venv`,
which does not exist; see finding F3 (pre-existing, not introduced by item 13).

`tomllib` parse of both TOMLs: OK. Nothing new appeared in `~/q8020` (`ls -d ~/q8020/2026-10-1[45]`: none).

## Criterion 3 — restored `examples/fvm_1d_smoke_test.toml` in metautil: PASS

    cd /Users/agallojr/proj/src/q8020/q8020-cfd-metautil
    git status --short                       # ?? examples/fvm_1d_smoke_test.toml
    diff <(git show 46fa917^:examples/fvm_1d_smoke_test.toml) examples/fvm_1d_smoke_test.toml

Observed diff (exit 1, two hunks):

    37c37
    < python3 ${_experiment_dir}/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py\
    ---
    > python3 ${_experiment_dir}/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py\
    54c54
    < "-shots" = [ 1000, 10000, 100000, 150000 ] 
    ---
    > "-shots" = [ 1000, 10000, 100000, 150000 ]

Hunk 1 is the harvester path update; hunk 2 removes one trailing space (`diff -w` leaves only
hunk 1). File is 1697 bytes, mtime 2026-10-15T02:56:11Z, untracked (`??`), not ignored.

Dry-run (cwd `/Users/agallojr/proj/src/q8020`):

    /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/q8020-sweep --dry-run \
      --set _output_dir=/tmp/order1-verify-13/out/smoke_seq --set _run_mode=sequential \
      q8020-cfd-metautil/examples/fvm_1d_smoke_test.toml

Started 2026-10-15T03:13:48Z; exit 0; wall 0.097 s; 214 lines; `Total: 66 (dry run)`
(groups: ideal 1, shots 1, bigshots 4, fvm_1d_nelem_5_sv_shots 10, time_steps 50). 66 `Postproc
(dry-run)` lines, 66 with the new path, 0 stale; 0 files written. First postproc line:

      Postproc (dry-run): bash -c "source ./.venv/bin/activate && python3 ./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py /tmp/order1-verify-13/out/smoke_seq/2026-10-14/_86c541b5/3472b45d/q8020_case_postproc_3472b45d.json"

Control: the same dry-run on the TRACKED `tests/examples/fvm_1d_smoke_test.toml` emits 66 lines
containing `codes/fvm_euler_1d_nozzle` (stale). See finding F2.

## Criterion 4 — April re-harvest on /tmp copies, real dirs untouched: PASS

Sources (one trial dir per sweep):

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-08/_85fd6d17/more_iters_0/trial_0_40373d9d` (261 files; cfl 1, 60 iters)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-10/_f1112a1f/more_iters_0/trial_0_5c9bff98` (293 files; cfl 2, 120 max iters)

Pre-state of the real dirs: `git status --short` on both April dirs empty; 0 untracked files;
fragment census over all 50 trial dirs (30 + 20) shows ONLY sweeper-side fragments
(`q8020_sweep_{artifacts,case,code,exec_stats,experiment}`, `q8020_params`, `q8020_env_*`,
`q8020_metadata`, `q8020_case_postproc`) and zero `q8020_{results,analysis,backend,artifacts,code,case}_*`
— confirming the work item's premise. The April `q8020_postproc_stderr_*.txt` files carry the
original failure (`python3: can't open file '/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020/./q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py': [Errno 2]`),
30 occurrences in `2026-04-08/_85fd6d17/slurm_4355227.err` and 20 in `2026-04-10/_f1112a1f/slurm_4371377.err`.

Commands:

    mkdir -p /tmp/order1-verify-13/april && touch /tmp/order1-verify-13/april/.marker
    cp -R <src0408> /tmp/order1-verify-13/april/trial_0_40373d9d_0408
    cp -R <src0410> /tmp/order1-verify-13/april/trial_0_5c9bff98_0410
    cd /tmp/order1-verify-13
    PYTHONPYCACHEPREFIX=/tmp/order1-verify-13/pyc \
      /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python \
      /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py \
      --outdir /tmp/order1-verify-13/april/trial_0_40373d9d_0408
    (same for trial_0_5c9bff98_0410)

Results:

| Copy | Started | Exit | Wall | New solver-side fragments |
|---|---|---|---|---|
| 2026-04-08 trial_0_40373d9d | 2026-10-15T03:13:49Z | 0 | 1.03 s | `q8020_analysis_0.json`, `q8020_artifacts_0.json`, `q8020_backend_0.json`, `q8020_case_0.json`, `q8020_code_0.json`, `q8020_results_0.json` |
| 2026-04-10 trial_0_5c9bff98 | 2026-10-15T03:13:50Z | 0 | 0.66 s | same six |

Content sanity (copies): 04-08 analysis `iterations_completed=60, converged=false,
converged_by=null, fidelity=0.99931, residual_reduction=4.64e-06`; 04-10 analysis
`iterations_completed=68, converged=true, converged_by="dq_norm", fidelity=0.7444,
residual_reduction=1.63e-09`; 04-08 results `per_iteration` has 60 entries with keys
`dq, hhl_solution_vector, lu_reference_vector, solution, step`; 04-10 backend
`ideal_statevector / statevector / num_qubits 5 / nshots 150000`; artifacts 68 transpile passes,
`circuit_basis=aer_simulator`, `linear_system={15, 16, 32, cond 13.20-13.70}`.

Real-dir post-checks (all at 2026-10-15T03:14Z):

    git status --short results/fvm_euler_1d_solver/2026-04-08 results/fvm_euler_1d_solver/2026-04-10   # empty (0 lines)
    git ls-files --others --exclude-standard <both>  | wc -l                                             # 0
    find <both> -newer /tmp/order1-verify-13/april/.marker | wc -l                                       # 0
    ls -l | shasum  (per source trial dir) before/after                                                  # 2543b9bfd61564e3 / fe1c1b5a362d85a2, unchanged
    find . -newer .marker -not -path './.git/*' -not -path './aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26*'  # only ./.git (index mtime from git status)

No `__pycache__` was created in the experiments tree (the three present —
`aux/burgers-ch-lbm-June2026/postproc/`, `aux/burgers-ch-lbm-June2026/seam_shots_figs/`,
`aux/burgers-ch-lbm/cases/` — pre-date the marker and are unrelated). All bytecode went to
`/tmp/order1-verify-13/pyc/`.

## Criterion 5 — nothing committed: PASS

At 2026-10-15T03:14:52Z:

    experiments: git log -1 --oneline -> 6f646617 plots for ieee        (branch main)
    metautil:    git log -1 --oneline -> 753b97e solverfw v2c: QuantumLinearSystemSolver + §9 acceptance sweep   (branch feature/solverfw-v2)
    metautil:    git status --short   -> ?? examples/fvm_1d_smoke_test.toml      (1 line)
    stash lists: 0 entries in both repos

Experiments `git status --short` is unchanged from the start of verification: the five `M`
files listed in criterion 1, plus untracked `aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/` and six
untracked `results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_*_0.json` (see F1).

## Findings

F1. Out-of-scope change riding in the same working tree. `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`
    carries a 268-line logic change (SQLS detection and artifacts, `converged_by` criteria,
    `circuit_basis` labels, `effective_shots`), mtime 2026-10-15T02:58:59Z — between this item's
    TOML edits (02:55:34Z) and docstring edit (03:05:12Z). Six untracked SQLS fragments in
    `results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/` (02:55:11Z) look like its
    test output. It has no path change and is not part of item 13; sibling `build-07/09/10.md`
    files exist, so it is plausibly a concurrent builder's work. It compiles (`py_compile` exit 0)
    and has 5 lines over 88 chars, the same count as at HEAD. The criterion-4 harvests above ran
    THIS modified harvester (that is what is on disk), so the `converged_by` key in the fragments
    comes from it, not from HEAD.

F2. Work item premise about the smoke test is wrong, and stale paths remain in metautil.
    `46fa917` (2026-07-15 12:26:57 -0400) did not delete `examples/fvm_1d_smoke_test.toml`; it
    MOVED it (rename, 0 content changes) to `tests/examples/fvm_1d_smoke_test.toml`, which is
    tracked at HEAD and still has the stale `codes/` path at line 37. The restored
    `examples/fvm_1d_smoke_test.toml` therefore duplicates a tracked file rather than restoring a
    lost one. Three more tracked TOMLs in `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/tests/examples/`
    carry the stale path with a different prefix: `base_case.toml:30`, `base_case_hhl.toml:30`,
    `hhl_time_step_impact.toml:30` (`~/q8020/q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/...`,
    activating `~/venvs/q8020-sweep`). Not fixed, per instructions.

F3. Path resolution from the assumed cwd (`/Users/agallojr/proj/src/q8020`), tested with `ls`:
    - CFL TOML and smoke test: `./q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` EXISTS;
      `./fvm_euler_1d_solver/.venv` and `./fvm_euler_1d_solver/nozzle_1d_solver.py` EXIST;
      `./.venv` (`_postproc_venv`) is MISSING on this laptop, so the expanded postproc
      `source ./.venv/bin/activate && ...` would fail here unless run with
      `--set _postproc_venv=./q8020-cfd-metautil/.venv`. On Frontier the April postproc JSONs
      record cwd `/autofs/nccs-svm1_proj/ard189/agallojr/proj/src/q8020/` with the same layout.
    - `fvm_euler_1d_nozzle.toml` has no cwd that satisfies all its paths: `_env` and `_script`
      use `../fvm_euler_1d_solver/...` (assumes cwd inside a sibling such as
      `q8020-cfd-experiments/`), while `_case_postproc` uses `q8020-cfd-experiments/aux/...`
      (assumes cwd `q8020/`). From `q8020/`, `../fvm_euler_1d_solver/.venv` resolves to
      `/Users/agallojr/proj/src/fvm_euler_1d_solver/.venv` — MISSING; from `q8020-cfd-experiments/`,
      the postproc path is MISSING. Pre-existing (the stale path had the same relative form). Its
      postproc also runs bare `python` with no venv; `backend_meta_harvester.py` needs
      `q8020_backend_utils`, which is NOT importable from the metautil venv
      (`ModuleNotFoundError: No module named 'q8020_backend_utils'`), so that second postproc
      would fail on this laptop even with the corrected path.

F4. Sweeper dry-run is not write-free in parallel mode. With `_run_mode = "parallel"` (the
    default in `fvm_cfl_sweeps.toml` and in the smoke test) `--dry-run` creates every case dir
    and writes `pipeline_args.json` under `_output_dir/<local-date>/_<id>/` (70 files, 80 dirs
    here). With the TOML default `_output_dir = "~/q8020"` a casual dry-run would therefore
    scribble into `~/q8020/`. Sequential mode writes nothing. The date directory uses local time
    (`2026-10-14`) although the run was at 2026-10-15T03:13Z UTC.

F5. Re-harvest mechanics for a real April pass (not done by the builder; the April dirs are
    clean, so "consider re-harvesting" remains outstanding):
    - `--outdir` mode names fragments `q8020_<section>_0.json` with no experiment id
      (`meta_fragment.write_fragment` line 354-355 only embeds the id when given), unlike the
      sweeper's `q8020_sweep_<section>_<id>_0.json`.
    - The postproc-JSON mode is not usable on the laptop: `case_dir` inside every April
      `q8020_case_postproc_<id>.json` is `/lustre/orion/ard189/proj-shared/agallojr/q8020/...`,
      so the harvester exits with "Output directory does not exist" (safe, but useless).
    - The existing rollups `q8020_metadata_<id>.json` have empty `results`, `analysis` and
      `backend` lists and would need re-rolling (`harvest_metadata`) after fragments are added,
      as `harvest_lugo_all.sh` does.
    - Cost estimate: 50 trial dirs at about 0.7-1.0 s each, roughly 1 min total.

F6. `backend_meta_harvester.py` docstring: compiles (`py_compile` exit 0, 0.32 s), longest line
    85 chars (<= 88). The path is wrapped with a `\\` at end of line 9, which renders in the
    docstring as a shell line-continuation (`.../fvm_euler_1d_nozzle/\` newline
    `backend_meta_harvester.py <postproc_json>`); pasted into bash it resolves to the new path,
    but a single-line grep for the full path will not match in this file.

F7. `harvest_lugo_all.sh` line 15 still says "PYTHONPATH includes the codes dir" (generic wording,
    not a path); cosmetic.

## Not checked, and why

- Frontier-side existence of `/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/` — no network.
- A real (non-dry) sweep of any TOML — forbidden; dry-run only.
- Re-harvest of all 50 April trial dirs — only one copy per sweep was tested, as required.
- Runtime behaviour of `backend_meta_harvester.py` — compiled only; its `q8020_backend_utils`
  dependency is not in the metautil venv (F3).
- Whether the F1 harvester logic change is correct — out of scope for item 13.

Scratch `/tmp/order1-verify-13/` deleted after writing this file.
