# Verify 12 (re-verify): sqls detachment in the fvm build, after fix-up rounds 1 and 2

**VERDICT: PASS**

- Verifier: independent re-verifier (Claude, Fable 5.1), strictly read-only.
- Window: 2026-10-15T07:44:57Z to 2026-10-15T07:53:41Z (UTC).
- Target: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `e13cbb1e54f1823f33ac12753a078a357662e9d3`.
- Prior FAIL clause (first verifier): `pyproject.toml` `dependencies` carried
  `sqls @ git+https://code.ornl.gov/...` and
  `quantum_linear_solvers @ git+https://github.com/...` as PEP 508 sources, and
  the Frontier docs said `pip install .`. Both are resolved (checks 1, 3, 4
  below); the fix landed in `c0af3997` (pyproject + offline re-lock),
  `61e7ca08` / `7831d352` (README, docs). No regression found in checks 2, 5,
  6, 7.
- Tool versions: `uv 0.7.2 (Homebrew 2025-04-30)`; `.venv` Python 3.12.10.
- Not read, per the brief: `build-*.md`, `verify-*.md`, `reproduce-*.md`,
  `STATUS.md`.

---

## Check 1: pyproject.toml - PASS

Command:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && cat -n pyproject.toml
```

Observed (relevant lines, verbatim):

```
    24	# uv-only project: pip ignores [tool.uv.sources] and the overrides below.
    25	# sqls (SVD-based Quantum Linear Solver, ORNL) and the HHL fork are bare names
    26	# resolved from sibling checkouts (see [tool.uv.sources]); `uv sync` never
    27	# clones them. Upstream origins, for provenance only:
    28	#   sqls                    https://code.ornl.gov/olcf-qcfd/sqls.git
    29	#   quantum_linear_solvers  https://github.com/Q8020-CFD/quantum_linear_solvers
    32	dependencies = [
    33	    "numpy>=1.20.0",
    34	    "scipy>=1.7.0",
    35	    "matplotlib>=3.3.0",
    36	    "PyYAML",
    37	    "python-dotenv",
    38	    "quantum_linear_solvers",
    39	    "sqls",
    40	    "qiskit==2.5.2",
    41	    "qiskit-aer==0.17.2",
    42	    "qiskit-ibm-runtime==0.50.0",
    43	    "qiskit-qasm3-import>=0.6.0",
    44	]
    46	[dependency-groups]
    47	dev = ["pytest>=8"]
    53	[tool.uv.sources]
    54	sqls = { path = "../sqls", editable = true }
    55	quantum_linear_solvers = { path = "../quantum_linear_solvers", editable = true }
    62	[tool.uv]
    63	override-dependencies = [
    64	    "qiskit==2.5.2",
    65	    "qiskit-aer==0.17.2",
    66	    "numpy>=1.20.0,<3",
    67	    "scipy>=1.7.0,<2",
    68	]
```

Fix-up evidence, the diff that resolved the FAIL clause:

```
git show c0af3997 -- pyproject.toml | grep -n '^[-+]'
33:-    "quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers",
34:-    "sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git",
35:+    "quantum_linear_solvers",
36:+    "sqls",
51:-    "numpy>=1.20.0",
52:-    "scipy>=1.7.0",
53:+    "numpy>=1.20.0,<3",
54:+    "scipy>=1.7.0,<2",
```

Findings: bare `"sqls"` and `"quantum_linear_solvers"` in `dependencies`; no
`@ git+` anywhere in the dependency list; the two upstream URLs appear only in
the comment block (lines 28-29); `[tool.uv.sources]` has both editable sibling
paths; `[tool.uv] override-dependencies` has bounded numpy/scipy plus exact
qiskit / qiskit-aer; `[dependency-groups] dev` has pytest;
`qiskit-ibm-runtime==0.50.0`. All clauses met.

Cosmetic nit (non-blocking): pyproject line 22 still says "the
requirements*.txt files are deprecated" but `ls requirements*.txt` finds none
in the tree, so the sentence refers to files that no longer exist.

---

## Check 2: uv.lock - PASS

Commands and observed output:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
grep -c 'git+' uv.lock                 -> 0
grep -c 'source = { git' uv.lock       -> 0
grep -n 'revision\|rev =\|git' uv.lock -> 2:revision = 2        (lock-format field only)
grep -n 'editable' uv.lock
284:source = { editable = "." }
314:    { name = "quantum-linear-solvers", editable = "../quantum_linear_solvers" },
316:    { name = "sqls", editable = "../sqls" },
962:source = { editable = "../quantum_linear_solvers" }
1088:source = { editable = "../sqls" }
```

Lock header (lines 1-12):

```
version = 1
revision = 2
requires-python = ">=3.12, <3.14"

[manifest]
overrides = [
    { name = "numpy", specifier = ">=1.20.0,<3" },
    { name = "qiskit", specifier = "==2.5.2" },
    { name = "qiskit-aer", specifier = "==0.17.2" },
    { name = "scipy", specifier = ">=1.7.0,<2" },
]
```

Package versions (`grep -n -A2 '^name = "..."$' uv.lock`):

```
481:name = "numpy"                 482-version = "2.5.2"    source = { registry = "https://pypi.org/simple" }
790:name = "pytest"                791-version = "9.1.1"    source = { registry = ... }
855:name = "qiskit"                856-version = "2.5.2"    source = { registry = ... }
878:name = "qiskit-aer"            879-version = "0.17.2"   source = { registry = ... }
908:name = "qiskit-ibm-runtime"    909-version = "0.50.0"   source = { registry = ... }
932:name = "qiskit-mitigation"     933-version = "0.1.1"    source = { registry = ... }
960:name = "quantum-linear-solvers" 961-version = "0.1.0"   962-source = { editable = "../quantum_linear_solvers" }
1046:name = "scipy"                1047-version = "1.18.0"  source = { registry = ... }
1086:name = "sqls"                 1087-version = "0.1.0"   1088-source = { editable = "../sqls" }
```

The fvm package block's `[package.metadata] requires-dist` (lock lines
301-315) restates pyproject exactly: `qiskit ==2.5.2`, `qiskit-aer ==0.17.2`,
`qiskit-ibm-runtime ==0.50.0`, `qiskit-qasm3-import >=0.6.0`,
`quantum-linear-solvers editable = "../quantum_linear_solvers"`,
`sqls editable = "../sqls"`, `numpy >=1.20.0`, `scipy >=1.7.0`,
`matplotlib >=3.3.0`; `[package.metadata.requires-dev] dev = [{ name =
"pytest", specifier = ">=8" }]`. The sqls block records sqls's own hard pins
(`numpy ==2.3.3`, `qiskit ==2.1.2`, `qiskit-aer ==0.17.1`, `scipy ==1.16.2`)
as metadata only; the resolved versions are the overridden ones above.

`uv tree --frozen --offline` (exit 0), depth 1:

```
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
```

Note: `uv tree` in uv 0.7.2 prints package names and versions, not source
paths, so the "two editable paths" are evidenced by the lock lines above and
by `uv export --frozen --offline` (exit 0), which emits:

```
3:-e .
4:-e ../quantum_linear_solvers
6:-e ../sqls
```

and contains no `git+` line.

`git status --short` before and after `uv tree` / `uv export`: empty (clean).

---

## Check 3: URL grep - PASS

Command:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && \
  grep -rn "code.ornl.gov\|github.com/Q8020-CFD" pyproject.toml uv.lock README.md docs/
```

Observed, verbatim (uv.lock: zero hits):

```
pyproject.toml:28:#   sqls                    https://code.ornl.gov/olcf-qcfd/sqls.git
pyproject.toml:29:#   quantum_linear_solvers  https://github.com/Q8020-CFD/quantum_linear_solvers
pyproject.toml:51:# git host code.ornl.gov is unreliable and we push nowhere) and
README.md:77:**Why path sources.** `sqls` comes from `code.ornl.gov`, which has been
README.md:117:`uv sync --frozen`; nothing may be cloned from `code.ornl.gov` at build
docs/FRONTIER_CONDA_SETUP.md:77:(copied to Frontier, never cloned from code.ornl.gov at build time):
```

Wider sweep over every tracked file (`git grep -n 'git+\|code\.ornl\.gov\|github\.com/Q8020-CFD' -- . ':!uv.lock'`)
returned the same six lines and nothing else: no `git+` anywhere in tracked
files. All hits are TOML comments or prose; none is a dependency source or an
install command.

---

## Check 4: Frontier docs - PASS (one minor note)

Command:

```
grep -n 'pip install\|python=3\.\|python 3\.\|sed \|uv sync\|commit_source\|--no-deps\|editable\|-e \.\./' \
  docs/FRONTIER_CONDA_SETUP.md docs/QUICKSTART_PARALLEL.md
git grep -n '3\.10' -- . ':!uv.lock'     -> (no output)
cat .python-version                        -> 3.12
```

`docs/FRONTIER_CONDA_SETUP.md`, verbatim lines:

```
    50	# Create environment with Python 3.12 (pyproject needs >=3.12,<3.14)
    51	conda create -p $CONDA_ENV_PATH python=3.12 -c conda-forge -y
    72	> Superseded 2026-10-15: `pip install .` no longer works (the project is
    73	> uv-only; pip ignores `[tool.uv.sources]`). See the README, Installation.
    75	Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. sqls
    76	and the HHL fork come from sibling clones, which must sit next to this repo
    77	(copied to Frontier, never cloned from code.ornl.gov at build time):
    78	`<parent>/fvm_euler_1d_solver`, `<parent>/sqls`,
    79	`<parent>/quantum_linear_solvers`. sqls and the fork MUST stay editable
    80	installs of those clones: only then does each run's
    81	`metadata_*.pkl` `code_versions` record their git commit. Check after
    82	installing that `code_versions['sqls']['commit_source']` and
    83	`code_versions['linear_solvers']['commit_source']` read `git`; anything else
    84	(None, `direct_url`) means the provenance is not valid.
    86	Preferred, when uv is available and a plain venv is acceptable:
    89	cd /path/to/fvm_euler_1d_solver
    90	uv sync --frozen                  # editable siblings, exactly the lock
    93	For the conda env (packed and broadcast below), install the locked set with
    94	the editable lines kept, from the repo root so `../sqls` resolves:
    97	pip install uv                    # uv itself only
    98	cd /path/to/fvm_euler_1d_solver
    99	uv export --frozen --no-hashes --no-emit-project --no-dev \
   100	  > /tmp/fvm-requirements.txt   # keeps the two -e sibling lines
   101	uv pip install --python $CONDA_ENV_PATH/bin/python --no-deps \
   102	  -r /tmp/fvm-requirements.txt
   105	`--no-deps` is correct because the export is the complete locked set; it
   106	also keeps sqls's own hard pins out of the resolution. Equivalent explicit
   107	form: export without the two siblings and install them afterwards with
   108	`uv pip install --python $CONDA_ENV_PATH/bin/python --no-deps -e ../sqls -e
   109	../quantum_linear_solvers`. The editable `.pth` files point at the clone
   110	paths, so the clones must be readable at the same absolute path on the
   111	compute nodes; if `conda pack` refuses the editable packages, pass
   112	`--ignore-editable-packages` (the `.pth` files are packed as they are).
   252	conda create -p $CONDA_ENV_PATH python=3.12 -c conda-forge -y
   255	# 2. Install the locked set (uv-only project; sqls and
   256	#    quantum_linear_solvers clones must sit next to this repo)
   258	pip install uv
   259	uv export --frozen --no-hashes --no-emit-project --no-dev \
   260	  > /tmp/fvm-requirements.txt   # keeps the two -e sibling lines
   261	uv pip install --python $CONDA_ENV_PATH/bin/python --no-deps \
   262	  -r /tmp/fvm-requirements.txt
```

`docs/QUICKSTART_PARALLEL.md`, verbatim lines:

```
    15	conda create -p $MEMBERWORK/<PROJECT>/envs/qiskit_conda_env python=3.12 -c conda-forge -y
    18	# 2. Install the locked set (uv-only project, `pip install .` is superseded;
    19	#    the sqls and quantum_linear_solvers clones sit next to this repo;
    20	#    see README and FRONTIER_CONDA_SETUP.md section 2.1; sqls and the
    21	#    fork stay editable so code_versions records their git commits)
    22	pip install uv
    23	uv export --frozen --no-hashes --no-emit-project --no-dev \
    24	  > /tmp/fvm-requirements.txt   # keeps the two -e sibling lines
    25	uv pip install --python $MEMBERWORK/<PROJECT>/envs/qiskit_conda_env/bin/python \
    26	  --no-deps -r /tmp/fvm-requirements.txt
```

Recipe validation (read-only): the exact export the docs prescribe,
`uv export --frozen --offline --no-hashes --no-emit-project --no-dev`,
exits 0 and begins

```
-e ../quantum_linear_solvers
    # via fvm-euler-1d-solver
-e ../sqls
    # via fvm-euler-1d-solver
annotated-types==0.8.0
```

with no `pytest` line (dev group excluded) and no `git+` line; 49 pinned
`==` lines follow. No `sed` strips `-e`; the editable sibling installs are
kept, and the explicit `-e ../sqls -e ../quantum_linear_solvers` form is
documented as the equivalent.

Relative-path probe for the recipe's "from the repo root so `../sqls`
resolves" assumption. A requirements file at
`/tmp/order2-reverify-12/relpath/req.txt` containing only
`-e ../order2-reverify-12-NONEXISTENT-probe` was fed to
`uv pip install --dry-run --offline --no-deps --python .venv/bin/python -r <file>`
from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` (a dry run on a
nonexistent target: nothing can be resolved, built, or installed). Output:

```
error: Distribution not found at: file:///Users/agallojr/proj/src/q8020/order2-reverify-12-NONEXISTENT-probe
```

So uv 0.7.2 resolves a relative `-e` path in a requirements file against the
current working directory, not against the requirements file's directory
(`/tmp/...`); the doc's instruction is correct for this uv. `uv pip list` and
`git status --short` afterwards were unchanged. Caveat for Frontier: `pip
install uv` there installs whatever uv is current; if a future uv changed
this resolution rule the recipe would need `-e` lines rewritten to absolute
paths. The docs state the assumption explicitly, which is the right
mitigation.

Minor note (non-blocking): `docs/QUICKSTART_PARALLEL.md` does not itself
contain the literal strings `uv sync --frozen` or `commit_source`. Its
"Quick summary" block says the siblings "stay editable so code_versions
records their git commits" and defers to "README and FRONTIER_CONDA_SETUP.md
section 2.1", both of which carry `uv sync --frozen` and the `commit_source`
must read `git` statement. The clause's substance (no `pip install .`, no
`python=3.10`, editable siblings kept, provenance requirement stated) is met
across the two docs.

---

## Check 5: README - PASS

Command: `cat -n README.md` in `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`.
Verbatim lines:

uv-only with the reason:

```
    49	This is a **uv-only** project: dependencies are managed with
    50	[uv](https://docs.astral.sh/uv/) via `pyproject.toml` + `uv.lock` (single
    51	source of truth). pip is not supported, because it ignores
    52	`[tool.uv.sources]` and `[tool.uv] override-dependencies` and so cannot find
    53	sqls or the fork. The two quantum
    54	linear-solver back-ends are resolved from sibling clones, so all three repos
    55	must sit side by side in one parent directory, on every machine (Frontier
    56	too):
    67	```bash
    68	uv sync
    69	```
    77	**Why path sources.** `sqls` comes from `code.ornl.gov`, which has been
    78	unreliable (HTTP 504 on this repo, 403 rate blocks), and we push to no
    79	remote; our clone is the source of record and our fixes live on a local
    80	branch. `pyproject.toml` lists both as bare names; their upstream git URLs
    81	appear only in a comment, as provenance, and nothing fetches them. ...
```

Commits of record:

```
    86	**Commits of record (AIAA 4Q26 work).**
    90	| `../sqls` | `9a4346a7` (main, 2026-06-30T14:40:52Z, Chao Lu); branch `local/sampler-port-2026-10` | our patch (shots mode runs `simulator.run(..., seed_simulator=seed)` directly, no runtime primitive), for later hand-off to ORNL; see `STATUS.md` in the experiments repo (`aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`) |
    91	| `../quantum_linear_solvers` | `66eadf0` (main); branch `feature/qiskit3-api-port` | Q8020-CFD fork, ported off the qiskit 3.0 removals |
```

Cross-checked against git:

```
git -C /Users/agallojr/proj/src/q8020/sqls log -1 --format='%H %an %aI %s' 9a4346a7
9a4346a7d0255cb1b59429d3b9454358a5b5bb4d  author=Lu, Chao 2026-06-30T14:40:52Z  Merge branch 'to_be_released' into 'main'
git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers log -1 --format='%H %an %aI %s' 66eadf0
66eadf0b4edcff100b20edf70a99e79cc69c5923  author=Andy Gallo 2026-03-07T15:52:47-05:00 (2026-03-07T20:52:47Z)  re-add the init constructor
```

Both ports UNCOMMITTED, branch tips equal main, diff files as interim record,
`uv sync --frozen` on other nodes:

```
    93	**Status (2026-10-15): both ports are UNCOMMITTED.** In both clones the
    94	branch exists but its tip still equals `main` (`9a4346a7`, `66eadf0`); the
    95	ports live only as uncommitted working trees, pending the operator's
    96	commit. Until then the interim record is the patch files in the
    97	experiments repo,
    98	`aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff`
    99	and `.../fork-patches/UNCOMMITTED-qiskit3-api-port.diff`, and the run
   100	metadata shows `dirty: True` for both. On other nodes, apply those patches
   101	to the clones and use `uv sync --frozen` (never a re-lock) until the
   102	commits exist. The run metadata (`code_versions`) is the authoritative
   103	record of what ran.
```

Rollback recipe:

```
   105	**Rollback** (to the pre-re-lock state: runtime 0.49.0, fork from git, sqls
   106	installed by hand):
   109	git checkout f16720b3 -- pyproject.toml uv.lock   # pre-re-lock state
   110	uv sync                      # re-fetches the fork from GitHub
   111	VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps
   112	VIRTUAL_ENV=.venv uv pip list | grep -i -E 'qiskit|sqls|linear'
```

Rollback target verified: `f16720b3` is an ancestor of HEAD
(`git merge-base --is-ancestor f16720b3 HEAD` -> yes), and
`git show f16720b3:pyproject.toml` has the pre-fix sources
(line 28 `"quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers"`,
line 44 `sqls = ["sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git"]`),
so the recipe does roll back to the described state. Its `uv sync` fetching
the fork from GitHub is the documented rollback behavior, not the recommended
path.

Frontier precondition:

```
   115	**Frontier.** Copy both sibling clones (at the commits above, with the
   116	patches applied) next to this repo before syncing, and use
   117	`uv sync --frozen`; nothing may be cloned from `code.ornl.gov` at build
   118	time. The Aer GPU (ROCm) build there is separate, see
   119	[Frontier Setup](docs/FRONTIER_CONDA_SETUP.md).
```

All clauses present and consistent with git.

---

## Check 6: provenance regression (solver run + harvester) - PASS

Solver run, 2026-10-15T07:45:55Z, wall time 1.49 s (`/usr/bin/time -p`:
real 1.49 s, user 0.79 s, sys 0.22 s), exit 0:

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && .venv/bin/python nozzle_1d_solver.py \
  -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 1 -initers 1 \
  -noshow -outdir /tmp/order2-reverify-12/run
...
step: 0/1 res:1.3141049901831434, res/res0:1.0  dq_norm: [0.17301961 0.17364062 0.48569569]
Completed: 0 steps in 0.01s
Saved metadata to /tmp/order2-reverify-12/run/metadata_nelem2_SQLS_statevector.pkl
```

`code_versions` from the pickle (loaded with `.venv/bin/python`, `pickle` +
`json.dumps`), verbatim:

```
code_versions top-level keys (n=9): ['fvm', 'linear_solvers', 'numpy', 'python', 'qiskit', 'qiskit_aer', 'qiskit_ibm_runtime', 'scipy', 'sqls']
{
  "fvm": {
    "path": "/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver",
    "commit": "e13cbb1e54f1823f33ac12753a078a357662e9d3",
    "dirty": false,
    "diff_sha256": null,
    "version": "0.1.0"
  },
  "sqls": {
    "path": "/Users/agallojr/proj/src/q8020/sqls/src/sqls",
    "commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
    "dirty": true,
    "diff_sha256": "2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9",
    "commit_source": "git",
    "version": "0.1.0"
  },
  "linear_solvers": {
    "path": "/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers",
    "commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923",
    "dirty": true,
    "diff_sha256": "98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f",
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
git rev-parse HEAD (fvm) = e13cbb1e54f1823f33ac12753a078a357662e9d3
```

No `error` key present (per-entry error isolation had nothing to record).

Hash cross-checks (`shasum -a 256`, byte counts via `wc -c`):

```
git -C /Users/agallojr/proj/src/q8020/sqls diff HEAD | shasum -a 256
2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9  -        (5712 bytes)
shasum -a 256 .../sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff
2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9           (5712 bytes)
git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers diff HEAD | shasum -a 256
98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f  -        (37688 bytes)
shasum -a 256 .../sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-qiskit3-api-port.diff
98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f           (37688 bytes)
```

Full paths of the two diff files:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff`
and
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-qiskit3-api-port.diff`.
All four hashes match the recorded `diff_sha256` values exactly.

Implementation read (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/helper_tools.py`
lines 182-198): `dirty` is `git status --porcelain != ''`; when dirty,
`diff_sha256 = sha256(git -C <dir> diff HEAD bytes)`. The docstring states
that untracked files are not in the diff. Consequence (documented, not a
defect): a new untracked file in a sibling clone would set `dirty: true`
without changing `diff_sha256`. `commit_source` is `'git'` when the module's
own file is tracked in a work tree, else falls back to PEP 610
`direct_url.json` (`'direct_url'`) or None, exactly as the Frontier doc
describes.

Installed-state cross-check (read-only), confirming the editables are the
sibling clones the lock names:

```
uv pip list --python .venv/bin/python
quantum-linear-solvers 0.1.0         /Users/agallojr/proj/src/q8020/quantum_linear_solvers
sqls                   0.1.0         /Users/agallojr/proj/src/q8020/sqls
qiskit 2.5.2  qiskit-aer 0.17.2  qiskit-ibm-runtime 0.50.0  qiskit-mitigation 0.1.1  numpy 2.5.2  scipy 1.18.0  pytest 9.1.1
.venv/lib/python3.12/site-packages/sqls-0.1.0.dist-info/direct_url.json
{"url":"file:///Users/agallojr/proj/src/q8020/sqls","dir_info":{"editable":true}}
.venv/lib/python3.12/site-packages/quantum_linear_solvers-0.1.0.dist-info/direct_url.json
{"url":"file:///Users/agallojr/proj/src/q8020/quantum_linear_solvers","dir_info":{"editable":true}}
```

Harvester, 2026-10-15T07:47:56Z, exit 0:

```
/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/.venv/bin/python \
  /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py \
  --outdir /tmp/order2-reverify-12/run
Metadata fragments written to: /private/tmp/order2-reverify-12/run
```

Wrote `q8020_analysis_0.json` (546 bytes), `q8020_artifacts_0.json`
(2738 bytes), `q8020_backend_0.json` (143 bytes), `q8020_case_0.json`
(374 bytes), `q8020_code_0.json` (1394 bytes), `q8020_results_0.json`
(1699 bytes). `q8020_code_0.json` verbatim:

```
{
  "_source": "solver",
  "algorithm": "SQLS",
  "sqls_method": "full_svd",
  "sqls_k": 4,
  "sqls_state_prep": "initialize",
  "sqls_repeats": 1,
  "code_versions": { ...identical to the pickle block above... },
  "fvm_commit": "e13cbb1e54f1823f33ac12753a078a357662e9d3",
  "sqls_commit": "9a4346a7d0255cb1b59429d3b9454358a5b5bb4d",
  "linear_solvers_commit": "66eadf0b4edcff100b20edf70a99e79cc69c5923"
}
```

Programmatic comparison: `json["code_versions"] == pickle["code_versions"]`
-> `True` (verbatim carry-over, all nine keys and nested values). The three
flat keys `fvm_commit`, `sqls_commit`, `linear_solvers_commit` are present
and equal to the nested commits.

No `__pycache__` was created under
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/`
(checked before and after). `/tmp/order2-reverify-12/` deleted after this
report was written.

---

## Check 7: nothing committed where it must not be - PASS

Commands: `git -C <repo> rev-parse --abbrev-ref HEAD`, `rev-parse --short=8 HEAD`,
`status --short`, `branch -a --format='%(refname:short) %(objectname:short)'`,
`for-each-ref refs/remotes/*/<branch>`, `rev-parse --abbrev-ref <branch>@{upstream}`.
Observed:

```
q8020-cfd-experiments   main                        6f646617   (origin/main 6f646617)
   working tree: 5 modified (fvm_cfl_sweeps.toml, fvm_euler_1d_nozzle.toml, backend_meta_harvester.py,
   fvm_euler_1d_solver_harvester.py, harvest_lugo_all.sh); untracked aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/
   and results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/q8020_*_0.json (6 files). Nothing committed.
q8020-cfd-metautil      feature/solverfw-v2         753b97eb   (origin/feature/solverfw-v2 753b97e)
   working tree: 4 modified tests/examples/*.toml. Nothing committed.
sqls                    local/sampler-port-2026-10  9a4346a7   main 9a4346a == origin/main 9a4346a
   working tree:  M src/sqls/runtime/quantum.py   (the uncommitted sampler port)
   reflog: 9a4346a HEAD@{0} checkout: moving from main to local/sampler-port-2026-10; HEAD@{1} clone
quantum_linear_solvers  feature/qiskit3-api-port    66eadf0b   main 66eadf0 == origin/main 66eadf0
   working tree: 8 modified (README.md, linear_solvers/hhl.py, matrices/linear_system_matrix.py,
   matrices/numpy_matrix.py, matrices/tridiagonal_toeplitz.py, pyproject.toml, setup.py, test/test_linear_solvers.py)
   reflog: 66eadf0 HEAD@{0} checkout: moving from main to feature/qiskit3-api-port; HEAD@{1} clone
fvm_euler_1d_solver     feature/sqls-aiaa-4q26      e13cbb1e   main ef7f0a8b == origin/main ef7f0a8b; working tree clean
```

Remote refs for the three feature branches: `for-each-ref refs/remotes/*/...`
printed nothing for `feature/sqls-aiaa-4q26`, `local/sampler-port-2026-10`,
`feature/qiskit3-api-port`; each reports `fatal: no upstream configured for
branch ...`. fvm `branch -a` lists `origin/main ef7f0a8b` and only archive /
legacy remote branches; no `origin/feature/sqls-aiaa-4q26`. sqls remote
branches: `origin/dev-bluffbody`, `origin/main` only. fork remote branches:
`origin/main`, `upstream/main` only. The sqls and fork reflogs show only
clone + checkout, no commits.

All expected: experiments `6f646617`, metautil `753b97e`, sqls `9a4346a7`,
fork `66eadf0`, fvm `main` `ef7f0a8b`; no remote branches for the three
feature branches.

---

## Findings summary

1. The first verifier's FAIL is resolved: `pyproject.toml` `dependencies`
   lists bare `"sqls"` / `"quantum_linear_solvers"` (commit `c0af3997`,
   2026-10-15T06:43:30Z); the upstream URLs survive only as a comment; uv.lock
   has zero `git+` / `source = { git` entries; every tracked file is free of
   `git+`.
2. The Frontier docs no longer recommend `pip install .` or `python=3.10`; the
   only `pip install .` mentions are "superseded" notes. `uv sync --frozen` is
   the stated preferred path; the conda alternative keeps the `-e ../sqls` /
   `-e ../quantum_linear_solvers` lines (verified by running the exact export),
   and FRONTIER_CONDA_SETUP.md states `commit_source` must read `git`.
3. Provenance regression: a fresh SQLS run records nine `code_versions` keys,
   fvm `e13cbb1e...` clean, sqls `9a4346a7...` and fork `66eadf0b...` dirty with
   `commit_source: git`, and both `diff_sha256` values equal the sha256 of the
   live `git diff HEAD` and of the stored `UNCOMMITTED-*.diff` files. The
   harvester carries `code_versions` verbatim plus the three flat commit keys.
4. Nothing was committed in the sibling repos or on fvm `main`; no remote
   branches exist for the three feature branches.
5. Minor, non-blocking: QUICKSTART_PARALLEL.md relies on cross-reference for
   `uv sync --frozen` / `commit_source` wording; pyproject comment line 22
   mentions `requirements*.txt` files that no longer exist; `uv tree` does not
   display source paths (lock and export do).

## Not checked, and why

- The unit/regression test suite (TESTING.md) was not run: outside the
  allowed read-only set for this re-verify, and would write `.pytest_cache` /
  `__pycache__` into the repo.
- `uv lock --check` was not run (forbidden `uv lock` family). Lock-vs-pyproject
  consistency was instead checked by reading the lock's `[manifest] overrides`
  and the fvm block's `requires-dist` / `requires-dev` against pyproject, and by
  `uv tree --frozen --offline` / `uv export --frozen --offline` succeeding.
- `pip install .` was not executed to prove it fails (would be an install).
- The conda-pack / SBCAST Frontier flow itself was not exercised (no Frontier
  access from this node); only the recipe text and the uv export it depends on
  were validated locally with uv 0.7.2.
- The remote GitHub / code.ornl.gov hosts were not contacted (`ls-remote` not
  run); remote-branch absence is from the local tracking refs, which were
  fetched by whoever last synced these clones.

## Scratch and side effects

- `/tmp/order2-reverify-12/` (solver run, harvester output, relative-path
  probe file) deleted after writing this report.
- No `__pycache__` created under the harvester folder; fvm `git status --short`
  was empty before, during and after all commands; experiments repo status
  unchanged except this new file inside the already-untracked
  `sqls-for-aiaa-4Q26/` folder.
- No edit / add / commit / stash / checkout / reset / push / worktree, no
  `uv lock` / `uv sync` / install, in any repo.
