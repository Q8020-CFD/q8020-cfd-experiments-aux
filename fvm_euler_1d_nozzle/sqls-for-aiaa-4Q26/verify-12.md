# verify-12 — Make the sqls detachment real in the build

VERDICT: FAIL

Independent read-only verification of work item 12. One sub-clause of
criterion 1 fails; criteria 2, 3, 4, 5 pass in full. Nothing was edited,
added, committed, stashed, checked out, reset, pushed, locked or synced in
any repo. Scratch `/tmp/order2-verify-12/` was deleted at the end.

- Verifier session: 2026-10-15T05:35:49Z to 2026-10-15T05:46Z (UTC)
- Host: laptop, macOS (Darwin 25.6.0), Apple silicon
- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1481073cd8fefe6436e57b194d210e28da6f02aa`,
  work tree clean (`git status --porcelain` empty)
- sqls: `/Users/agallojr/proj/src/q8020/sqls`, branch
  `local/sampler-port-2026-10`, HEAD `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d`
  (2026-06-30T14:40:52Z, "Lu, Chao", merge of `to_be_released`), one
  uncommitted file `src/sqls/runtime/quantum.py`
- fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, branch
  `feature/qiskit3-api-port`, HEAD `66eadf0b4edcff100b20edf70a99e79cc69c5923`
  (2026-03-07T15:52:47-05:00 = 2026-03-07T20:52:47Z), 7 uncommitted files
- uv on PATH: `uv 0.7.2 (Homebrew 2025-04-30)`; only `uv tree --frozen
  --offline` and `uv export --frozen --offline` were run (read the lock, no
  resolve, no install)

## Why FAIL (one line)

`pyproject.toml` line 36 still carries `"sqls @
git+https://code.ornl.gov/olcf-qcfd/sqls.git"` inside `dependencies = [...]`.
Criterion 1 requires every `code.ornl.gov` hit in pyproject/uv.lock/README to
be a comment or prose, "never a dependency source". A PEP 508 direct-URL
requirement in `project.dependencies` is a dependency source: uv ignores it
because `[tool.uv.sources]` overrides, but pip does not, and the repo's own
Frontier instructions (`docs/FRONTIER_CONDA_SETUP.md` lines 78 and 225,
`docs/QUICKSTART_PARALLEL.md` line 19, all `pip install .`) would clone from
`code.ornl.gov` on Frontier, the exact event the item exists to rule out.
Remedy is small: make the two entries bare names (`"sqls"`,
`"quantum_linear_solvers"`), keep the origin URLs in the comment block, re-lock,
and point the Frontier docs at `uv sync`. Everything else in criterion 1 and
all of criteria 2 to 5 hold.

---

## Criterion 1 — build resolves sqls from the local path: FAIL (one sub-clause)

### 1a `[tool.uv.sources]` — PASS

```
$ sed -n 45,51p pyproject.toml
# ... See README.
[tool.uv.sources]
sqls = { path = "../sqls", editable = true }
quantum_linear_solvers = { path = "../quantum_linear_solvers", editable = true }
```

### 1b `uv.lock` has sqls editable, no `git+` — PASS

```
$ grep -c 'git+' uv.lock
0
$ grep -n 'source = {' uv.lock | grep -v 'registry = "https://pypi.org/simple"'
284:source = { editable = "." }
962:source = { editable = "../quantum_linear_solvers" }
1088:source = { editable = "../sqls" }
$ grep -n 'editable' uv.lock
284:source = { editable = "." }
314:    { name = "quantum-linear-solvers", editable = "../quantum_linear_solvers" },
316:    { name = "sqls", editable = "../sqls" },
962:source = { editable = "../quantum_linear_solvers" }
1088:source = { editable = "../sqls" }
```

Note `grep -c 'git+'` alone is a weak test: uv writes git sources as
`source = { git = "https://..." }` (the pre-re-lock lock at `f16720b3` had
`source = { git = "https://github.com/Q8020-CFD/quantum_linear_solvers#66eadf0b..." }`
at its line 876 and also 0 hits for `git+`). The `source = {` grep above is
the one that proves there is no git/url source of any form in the current lock.

Read-only lock view (no resolve, no install):

```
$ uv tree --frozen --offline --depth 1
fvm-euler-1d-solver v0.1.0
├── matplotlib v3.11.1
├── numpy v2.5.2
├── python-dotenv v1.2.3
├── pyyaml v6.0.3
├── qiskit v2.5.2
├── qiskit-aer v0.17.2
├── qiskit-ibm-runtime v0.50.0
├── qiskit-qasm3-import v0.6.0
├── quantum-linear-solvers v0.1.0
├── scipy v1.18.0
├── sqls v0.1.0
└── pytest v9.1.1 (group: dev)
$ uv export --frozen --offline --no-hashes | grep -n -i 'sqls\|linear\|^-e'
3:-e .
4:-e ../quantum_linear_solvers
6:-e ../sqls
```

### 1c `code.ornl.gov` only as provenance, never a dependency source — FAIL

```
$ grep -rn code.ornl.gov pyproject.toml uv.lock README.md
README.md:74:**Why path sources.** `sqls` comes from `code.ornl.gov`, which has been
README.md:105:repo before syncing; nothing may be cloned from `code.ornl.gov` at build
pyproject.toml:36:    "sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git",
pyproject.toml:48:# git host code.ornl.gov is unreliable and we push nowhere) and
```

README:74, README:105 and pyproject:48 are prose/comment: fine. pyproject:36 is
not. Context:

```
$ sed -n 30,40p pyproject.toml
dependencies = [
    "numpy>=1.20.0",
    "scipy>=1.7.0",
    "matplotlib>=3.3.0",
    "PyYAML",
    "python-dotenv",
    "quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers",
    "sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git",
    "qiskit==2.5.2",
```

The comment at pyproject lines 24-26 says the URLs are kept "so the published
metadata names their origin, but uv resolves both from sibling checkouts". For
uv that is true (1b, 1d). For any non-uv consumer it is a live VCS source, and
the repo documents such a consumer for Frontier:

```
$ git grep -n 'pip install \.' -- docs
docs/FRONTIER_CONDA_SETUP.md:78:pip install .
docs/FRONTIER_CONDA_SETUP.md:225:pip install .
docs/QUICKSTART_PARALLEL.md:19:pip install .
$ git log --format='%h %aI %s' -1 -- docs/FRONTIER_CONDA_SETUP.md
a885ef47 2026-08-17T17:16:25-04:00 Bump quantum stack to latest qiskit 2.5 line
```

README line 107 links to `docs/FRONTIER_CONDA_SETUP.md` as the Frontier setup;
that doc (unchanged by item 12) builds a `python=3.10` conda env and runs
`pip install .`, which would (a) violate `requires-python = ">=3.12,<3.14"` and
(b) try to `git clone https://code.ornl.gov/olcf-qcfd/sqls.git` and the GitHub
fork. README line 81-82 does say "Plain `pip install -e .` is not supported",
but the Frontier doc it links to prescribes exactly that.

Ruling: the literal clause fails; the functional intent (uv never fetches from
code.ornl.gov) holds. Item 12 offered two routes; the one taken (keep extra as
a base dep + `tool.uv.sources`) did not drop the URL from `dependencies`.

### 1d venv imports sqls from the sibling clone — PASS

```
$ .venv/bin/python -c "import sqls; print(sqls.__file__)"
/Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py
$ cat .venv/lib/python3.12/site-packages/__editable__.sqls-0.1.0.pth
/Users/agallojr/proj/src/q8020/sqls/src
$ cat .venv/lib/python3.12/site-packages/sqls-0.1.0.dist-info/direct_url.json
{"url":"file:///Users/agallojr/proj/src/q8020/sqls","dir_info":{"editable":true}}
$ cat .venv/lib/python3.12/site-packages/sqls-0.1.0.dist-info/INSTALLER
uv
$ .venv/bin/python -c "import linear_solvers; print(linear_solvers.__file__)"
/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py
```

(The fork's import name is `linear_solvers`, distribution name
`quantum-linear-solvers`; `import quantum_linear_solvers` is
`ModuleNotFoundError` by design, not a defect.)

Observation, no criterion impact: the sqls editable records
(`__editable__.sqls-0.1.0.pth`, `sqls-0.1.0.dist-info/`) are dated
2026-08-17 17:47 local while `quantum_linear_solvers-0.1.0.dist-info/` and
`__editable__.fvm_euler_1d_solver-0.1.0.pth` are 2026-10-15 01:08 local: the
re-lock `uv sync` left the pre-existing sqls editable install in place (same
path, same version). It points at the right tree, so the import is correct;
just note that this venv has not demonstrated a from-scratch sqls install off
the new lock.

---

## Criterion 2 — README records the commits, branches, rationale, sync, layout, rollback, Frontier: PASS

File: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/README.md`

| Required | Where | Observed | Cross-check |
|---|---|---|---|
| sqls commit 9a4346a7, 2026-06-30, Chao Lu | line 88 | `9a4346a7` (main, 2026-06-30T14:40:52Z, Chao Lu) | `git -C sqls log -1`: `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d Lu, Chao 2026-06-30T14:40:52Z`; `git -C sqls rev-parse main` = `9a4346a7...` |
| local branch `local/sampler-port-2026-10` | line 88 | present | `git -C sqls rev-parse --abbrev-ref HEAD` = `local/sampler-port-2026-10` |
| fork commit 66eadf0 | line 89 | `66eadf0` (main) | `git -C fork rev-parse HEAD main origin/main` all `66eadf0b4edcff100b20edf70a99e79cc69c5923` |
| fork branch `feature/qiskit3-api-port` | line 89 | present | `git -C fork rev-parse --abbrev-ref HEAD` = `feature/qiskit3-api-port` |
| why path sources: no pushes; code.ornl.gov unreliable | lines 74-77 | "`code.ornl.gov`, which has been unreliable (HTTP 504 ..., 403 rate blocks), and we push to no remote; our clone is the source of record" | n/a |
| the one sync command | line 65 | `uv sync` | `uv tree --frozen` resolves both path deps (1b) |
| sibling-clone layout | lines 55-59 | `<parent>/fvm_euler_1d_solver`, `<parent>/sqls`, `<parent>/quantum_linear_solvers` | matches `../sqls`, `../quantum_linear_solvers` in pyproject/uv.lock |
| rollback recipe | lines 94-102 | `git checkout f16720b3 -- pyproject.toml uv.lock`; `uv sync`; `VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps` | `git ls-tree f16720b3 -- pyproject.toml uv.lock` lists both blobs (`38b2825a`, `a38ba437`); `f16720b3:pyproject.toml` has the `[project.optional-dependencies] sqls = [...]` extra, runtime 0.49.0, fork from git |
| Frontier precondition: copy both clones alongside fvm | lines 104-106 | "Copy both sibling clones (at the commits above) next to this repo before syncing; nothing may be cloned from `code.ornl.gov` at build time." | n/a; see Findings F2, F3 |

Verbatim README lines 84-89:

```
**Commits of record (AIAA 4Q26 work).**

| Clone | Commit / branch | Notes |
|---|---|---|
| `../sqls` | `9a4346a7` (main, 2026-06-30T14:40:52Z, Chao Lu) plus local branch `local/sampler-port-2026-10` | branch carries our patches (Aer SamplerV2 port), kept as a patch list for hand-off to ORNL; see `STATUS.md` in the experiments repo (`aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`) |
| `../quantum_linear_solvers` | `66eadf0` (main) plus branch `feature/qiskit3-api-port` | Q8020-CFD fork, ported off the qiskit 3.0 removals on the branch |
```

Wording nit (not a failure): "branch carries our patches" / "ported ... on the
branch" overstate slightly. Both branches sit AT their main commit with zero
commits of their own; the sampler port and the qiskit3 port are uncommitted
working-tree changes (sqls: 1 file; fork: 7 files). The patch lists in
`sqls-patches/` and `fork-patches/` are what actually carry them (criterion 4
confirms the sqls one is exact).

---

## Criterion 3 — run metadata carries the commits; harvester puts them in the code fragment: PASS

### 3a solver run

```
$ cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
$ .venv/bin/python nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow -outdir /tmp/order2-verify-12/run
...
step: 0/1 res:1.3141049901831434, res/res0:1.0  dq_norm: [0.17301961 0.17364062 0.48569569]
Completed: 0 steps in 0.02s
Saved metadata to /tmp/order2-verify-12/run/metadata_nelem2_SQLS_statevector.pkl
...
real 0m3.108s   (2026-10-15T05:38:01Z to 2026-10-15T05:38:04Z)   exit=0
```

Output dir held 10 files (dq, final_results, hhl_metrics, metadata pkl,
qc_metadata_sqls, residual, 2x results, solution_plot png, system_Ab pkl).

### 3b `code_versions` in the pickle (fvm venv)

```
$ .venv/bin/python -c "import glob,pickle,json; m=pickle.load(open(glob.glob('/tmp/order2-verify-12/run/metadata_*.pkl')[0],'rb')); print(json.dumps(m['code_versions'],indent=2))"
{
  "fvm": {
    "path": "/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver",
    "commit": "1481073cd8fefe6436e57b194d210e28da6f02aa",
    "dirty": false,
    "version": "0.1.0"
  },
  "sqls": {
    "path": "/Users/agallojr/proj/src/q8020/sqls/src/sqls",
    "commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
    "dirty": true,
    "commit_source": "git",
    "version": "0.1.0"
  },
  "linear_solvers": {
    "path": "/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers",
    "commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923",
    "dirty": true,
    "commit_source": "git",
    "version": "0.1.0"
  },
  "qiskit": "2.5.2",
  "qiskit_aer": "0.17.2",
  "qiskit_ibm_runtime": "0.50.0",
  "numpy": "2.5.2",
  "scipy": "1.18.0",
  "python": "3.12.10"
}
```

Expected vs observed: sqls `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` dirty
true (work tree has ` M src/sqls/runtime/quantum.py`): match. linear_solvers
`66eadf0b4edcff100b20edf70a99e79cc69c5923` dirty true (7 modified files):
match. fvm commit = `git -C fvm rev-parse HEAD` = `1481073cd8fe...`, dirty
false (`git status --porcelain` empty): match.

### 3c harvest the fresh run (metautil venv)

```
$ /Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py --outdir /tmp/order2-verify-12/run
✅ Metadata fragments written to: /private/tmp/order2-verify-12/run      (2026-10-15T05:39:04Z, exit=0)
$ cat /tmp/order2-verify-12/run/q8020_code_0.json
{
  "_source": "solver",
  "algorithm": "SQLS",
  "sqls_method": "full_svd",
  "sqls_k": 4,
  "sqls_state_prep": "initialize",
  "sqls_repeats": 1,
  "code_versions": { ...identical to 3b, all 9 keys, same values... },
  "fvm_commit": "1481073cd8fefe6436e57b194d210e28da6f02aa",
  "sqls_commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
  "linear_solvers_commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923"
}
```

`code_versions` is carried verbatim (every key and value of 3b, including the
`dirty` booleans and `commit_source`); the three flat keys equal the three shas.

### 3d harvest a copy of the archived August trial

```
$ cp -Rp /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0 /tmp/order2-verify-12/archived_trial_0
$ rm -f /tmp/order2-verify-12/archived_trial_0/q8020_*.json      # 0 left
$ <metautil python> <harvester> --outdir /tmp/order2-verify-12/archived_trial_0
✅ Metadata fragments written to: /private/tmp/order2-verify-12/archived_trial_0   exit=0
$ cat /tmp/order2-verify-12/archived_trial_0/q8020_code_0.json
{
  "_source": "solver",
  "algorithm": "SQLS",
  "sqls_method": "full_svd",
  "sqls_k": 128,
  "sqls_state_prep": "initialize",
  "sqls_repeats": 1,
  "code_versions": null,
  "fvm_commit": null,
  "sqls_commit": null,
  "linear_solvers_commit": null
}
```

All four provenance fields null for the archived run (its pickle predates
`code_versions`): as required.

sha256 of the six fragments, scratch copy vs the six untracked
`q8020_*_0.json` in the real dir:

```
MATCH   q8020_analysis_0.json  711cf6a4b38da13b64cd1eecb35dc330fba7286edb2d7bdfc44e98e54bd8b606
MATCH   q8020_artifacts_0.json 1addd1016efce9227c3edd8b081cc999676b0dd1e70c4f6ee6a2aabc2064e7c3
MATCH   q8020_backend_0.json   5b74731160f951e3306d67bd56e5deff4098bf60e95f52692af56bbd073ebaac
MATCH   q8020_case_0.json      3dd93d5f230ad3a75a81f3182edd45a01176aac9e924e09d5b9d31df71c8d36a
MATCH   q8020_code_0.json      75d552a9b350f2121f612afeca4879936ec82a02a6a3d1bc3e9e89718b9bd1e3
MATCH   q8020_results_0.json   6e4a2356a7d947814125178b7db4faa0d1cd8a37c6d7682fddc8b9a03c82b0bf
```

The real dir's six files kept their 2026-10-15 00:43:57 local mtimes (not
touched by this verification).

---

## Criterion 4 — sqls patch list exists and matches the tree exactly: PASS

```
$ ls -laT /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/
-rw-r--r--@  1 agallojr  staff  4262 Oct 15 00:33:04 2026 UNCOMMITTED-sampler-port.diff      (79 lines)
$ shasum -a 256 .../sqls-patches/UNCOMMITTED-sampler-port.diff
fbea1c9a048d80e9d806cfea5ffc071c4f179f9a9f7eef7606cfb7ab4a70af77
```

(b) patch text equals the live `git diff main`:

```
$ git -C /Users/agallojr/proj/src/q8020/sqls diff main > /tmp/order2-verify-12/sqls-diff-main.diff
$ shasum -a 256 /tmp/order2-verify-12/sqls-diff-main.diff
fbea1c9a048d80e9d806cfea5ffc071c4f179f9a9f7eef7606cfb7ab4a70af77
$ diff <patchfile> /tmp/order2-verify-12/sqls-diff-main.diff && echo IDENTICAL
IDENTICAL
```

Byte-identical (same sha256), so no whitespace-only header differences to
report.

(a) forward `apply --check` must NOT apply (change already present):

```
$ git -C /Users/agallojr/proj/src/q8020/sqls apply --check <patchfile>
error: patch failed: src/sqls/runtime/quantum.py:40
error: src/sqls/runtime/quantum.py: patch does not apply
exit=1
```

(c) reverse `apply --check` must succeed:

```
$ git -C /Users/agallojr/proj/src/q8020/sqls apply --check --reverse <patchfile>
exit=0
```

Tree unchanged afterwards (`git status --porcelain` still exactly
` M src/sqls/runtime/quantum.py`, HEAD still `9a4346a7...`). Patch content:
one file, `src/sqls/runtime/quantum.py`, adding a keyword-only `seed=None` to
`quantum_solve` threaded into `_run_shots` for Aer SamplerV2, plus docstring
edits (header `index 5e9b7dd..7b535a0`).

---

## Criterion 5 — nothing committed where it must not be: PASS

| Check | Command | Observed | Expected | OK |
|---|---|---|---|---|
| experiments HEAD | `git -C q8020-cfd-experiments log -1 --format=%H` | `6f6466172b1509f3484f88db0455ca792defdc81` ("plots for ieee") | 6f646617 | yes |
| metautil HEAD | `git -C q8020-cfd-metautil rev-parse HEAD` | `753b97eb8b2ff1235ac2a59baa94ebab7709251c` | 753b97e | yes |
| sqls HEAD / branch | `git -C sqls rev-parse HEAD; --abbrev-ref HEAD` | `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` / `local/sampler-port-2026-10` | 9a4346a7 on that branch | yes |
| fork HEAD / branch | `git -C quantum_linear_solvers rev-parse HEAD; --abbrev-ref HEAD` | `66eadf0b4edcff100b20edf70a99e79cc69c5923` / `feature/qiskit3-api-port` | 66eadf0 on that branch | yes |
| fvm main | `git -C fvm rev-parse main` | `ef7f0a8b2247615b56e4391fa1804b59825de217` (= origin/main) | ef7f0a8b | yes |
| no `origin/feature/sqls-aiaa-4q26` | `git -C fvm branch -r` | origin/HEAD, origin/archive-master, origin/archive/feature/{agmods,tpile,wf-pkg}, origin/archive/qiskit-hhl-2, origin/archive/solverfw-v2-port, origin/backup-old-main, origin/bloqade-test, origin/feature/qiskit-hhl, origin/main | absent | yes |
| no `origin/local/sampler-port-2026-10` | `git -C sqls branch -r` | origin/HEAD, origin/dev-bluffbody, origin/main | absent | yes |
| no `origin/feature/qiskit3-api-port` | `git -C quantum_linear_solvers branch -r` | origin/HEAD, origin/main, upstream/HEAD, upstream/main | absent | yes |

fvm branch is 12 commits ahead of origin/main, all local. Working-tree state
of experiments and metautil was identical at start and end of this
verification (experiments: 5 ` M` files incl. the harvester, `??
aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`, 6 `??` q8020 json in the
archived trial; metautil: 4 ` M` toml under tests/examples).

---

## Findings (beyond the criteria)

**F1 — Frontier sync and the sibling-path assumption.** No absolute path in
`pyproject.toml` or `uv.lock` (`grep -n '/Users/\|/home/\|/lustre\|/ccs/'` on
both: no hits); the only path sources are `../sqls` and
`../quantum_linear_solvers`, relative to the fvm checkout, so a
`<parent>/{fvm_euler_1d_solver,sqls,quantum_linear_solvers}` layout on
Frontier satisfies the lock. The lock is a universal resolution (no
`resolution-markers` / `environments` restriction) and carries Linux wheels for
the compiled stack: qiskit-aer 0.17.2 `manylinux_2_17_x86_64` (also aarch64,
ppc64le, i686), numpy 2.5.2 and scipy 1.18.0 `manylinux_2_27_x86_64.manylinux_2_28`
(glibc >= 2.28, which SLES 15 on Frontier meets). `uv sync` would still need
pypi/files.pythonhosted.org for the wheels themselves on a fresh node; "never
touches the network" is only true in the sense that matters here (nothing is
cloned from code.ornl.gov or GitHub). Not verifiable here: that `uv` and a
Python 3.12/3.13 are available on Frontier, and how the pypi CPU
`qiskit-aer` wheel coexists with the separate ROCm Aer build README line 106
mentions.

**F2 — The lock pins the fork's UNCOMMITTED pyproject.** `uv.lock` line 975
records `quantum-linear-solvers` `requires-dist` with `qiskit >=2.2`. The fork's
committed `pyproject.toml` at `66eadf0` says `qiskit>=2.0`; `>=2.2` exists only
in the fork's uncommitted work tree (`git -C quantum_linear_solvers diff
pyproject.toml`: `-"qiskit>=2.0"` / `+"qiskit>=2.2"`). uv validates path
dependencies' metadata against the lock on `uv sync`; a clean checkout of the
fork at `66eadf0` (which is what README line 104 "at the commits above" reads
as) would make uv declare the lock stale and re-resolve (rewriting `uv.lock`
and needing index access), while `uv sync --locked` would refuse. Copying the
clone with its work tree (or applying `fork-patches/UNCOMMITTED-qiskit3-api-port.diff`
first) avoids it. The sqls side is clean: its lock `requires-dist` (`qiskit==2.1.2`,
`qiskit-aer==0.17.1`, `numpy==2.3.3`, `scipy==1.16.2`, `examples` extra) equals
the committed `9a4346a7:pyproject.toml`; the only sqls change is `quantum.py`.
Recommendation: commit the fork port on `feature/qiskit3-api-port` (and the
sampler port on `local/sampler-port-2026-10`) so "commit of record + branch"
in README names code that exists in git, and the README sentence "Copy both
sibling clones (at the commits above)" becomes sufficient.

**F3 — Frontier docs contradict the README.** `docs/FRONTIER_CONDA_SETUP.md`
(linked from README line 107 as the Frontier setup) and
`docs/QUICKSTART_PARALLEL.md` still instruct `conda create ... python=3.10` and
`pip install .` (lines 78, 225; 19), last touched 2026-08-17 (`a885ef47`).
With the current `pyproject.toml` that path fails `requires-python` and, via
the direct-URL entries, clones `code.ornl.gov` and GitHub. This is the
concrete consequence of the criterion-1 failure.

**F4 — `dirty` and git-absent behaviour (helper_tools.py lines 153-226).**
`_git_state` returns `(None, None)` unless `git -C <dir> ls-files
--error-unmatch <module file>` succeeds (so a copy under an ignored `.venv`
reports no commit), then `commit = git rev-parse HEAD`, `dirty = (git status
--porcelain != '')`. `--porcelain` from a subdirectory reports the whole work
tree, and untracked (`??`) entries count as dirty, which matches the
criterion's definition. Both branches exercised: fvm clean -> `false`; sqls and
fork with modified files -> `true`. `_git` catches `OSError` and
`subprocess.SubprocessError` (so `FileNotFoundError` for a missing git binary
and the 5 s `TimeoutExpired`) and returns None; `get_code_versions` wraps
everything in `try/except Exception` and writes an `error` key rather than
raising. Empirical git-absent probe (fvm venv, `env PATH=<empty dir>`):

```
git on PATH: None
"fvm": {"path": ".../fvm_euler_1d_solver", "commit": null, "dirty": null, "version": "0.1.0"}
"sqls": {"path": ".../sqls/src/sqls", "commit": null, "dirty": null, "commit_source": null, "version": "0.1.0"}
"linear_solvers": {..., "commit": null, "dirty": null, "commit_source": null, "version": "0.1.0"}
"qiskit": "2.5.2", ... "python": "3.12.10"        exit=0
```

Degrades to nulls, versions still recorded, no exception. Good.

**F5 — Harvester robustness on odd `code_versions`.** Four scratch copies of
the fresh run with the pickle edited (metautil python), then harvested:

| Pickle `code_versions` | Harvest | `code_versions` in json | flat commits |
|---|---|---|---|
| `None` | exit 0 | `null` | all `null` |
| key absent | exit 0 | `null` | all `null` |
| dict with `sqls` removed, `linear_solvers: None`, `fvm: {"path": "/x"}` (no `commit`) | exit 0 | the partial dict verbatim | all `null` |
| the string `"garbage"` | exit 1, `AttributeError: 'str' object has no attribute 'get'` at harvester line 816 `entry = (code_versions or {}).get(name)` | n/a | n/a |

None / missing / partial are handled. A non-dict value crashes the harvest;
the solver can never write one (`get_code_versions` always returns a dict), so
this is a hardening nit, not a defect against the criteria: a
`if not isinstance(code_versions, dict): code_versions = None` guard would
close it.

**F6 — Minor.** TESTING.md line 161 and README are consistent on "no `[sqls]`
extra any more". README line 88 refers readers to `STATUS.md` in this folder
(not read here per the verification rules). `fork-patches/UNCOMMITTED-qiskit3-api-port.diff`
(20839 bytes, 2026-10-15 01:01:30 local) exists alongside `sqls-patches/`; not
in scope, not checked against the fork tree.

---

## Not checked, and why

- `uv sync` / `uv lock` from scratch (fresh venv, fresh node): prohibited by
  the verification rules; the lock was inspected with `uv tree --frozen
  --offline` and `uv export --frozen --offline` only. So "a from-scratch sqls
  install off the new lock" is inferred from the lock, not demonstrated (see
  1d observation).
- Anything on Frontier (uv availability, Python version, ROCm Aer interplay):
  no network, no remote host.
- The fork patch list (`fork-patches/`) vs the fork work tree: outside item 12.
- `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`: not read, per
  the rules.
- The fvm test suite was not run (not asked; TESTING.md records the builder's
  own 2026-10-15T05:08Z to 05:10Z runs).

## Cleanup

- `/tmp/order2-verify-12/` (run, archived_trial_0, four probe dirs, nopath,
  sqls-diff-main.diff) deleted.
- No `__pycache__` was created next to the harvester
  (`.../fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/__pycache__` absent after all
  runs; the harvester is run as a script and imports only `q8020_cfd_metautil`).
- fvm `__pycache__/` is gitignored (`.gitignore` line 8); `git status
  --porcelain` in fvm empty at start and end.
- Only this file was created in
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`.
