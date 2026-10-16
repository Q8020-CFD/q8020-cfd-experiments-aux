# Build 03 (fvm): SamplerV2 port, code_versions, re-lock prep (items 3, 12)

Repo `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26`, base `f16720b3` (main @ `ef7f0a8b`). Builder: FVM
re-lock builder, order 2.

## Phase 1 (2026-10-15T04:25Z to 04:40Z): source and config edits, venv unchanged

No `uv lock` / `uv sync` / `pip` was run; `.venv` and `uv.lock` are untouched
(venv still qiskit 2.5.2, aer 0.17.2, runtime 0.49.0, fork `66eadf0`
non-editable, sqls editable from `/Users/agallojr/proj/src/q8020/sqls/src`).

### Commits

```
$ git log --oneline main..HEAD   (top 4 are this phase)
abf74941 Runtime 0.50.0 pin, sqls and fork as sibling path sources with overrides, dev group, docs
6c672f2b SQLS unavailable hint points at the sibling clone and uv sync
4f44d5be Record code_versions in run metadata for fvm sqls fork and stack
7a1542a6 Aer SamplerV2 for ideal HHL shots, runtime SamplerV2 only for fake and real
f16720b3 Tests: use sys.executable, top-level imports, pin 71c02aed SQLS fixups and convergence metadata
71c02aed SQLS review fixups: backend method check, shared k rule, zero b, import hints, -v 0, convergence metadata
5af4dd2f Add unittest regression suite and gate fixtures for LU GMRES HHL SQLS paths
3a88a37d SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse
d7658f6a SQLS: default sqls_k to N//2, validate k and ideal backend early, narrow import except

$ git diff f16720b3..HEAD --stat
 README.md                     | 77 ++++++++++++++++++++++++++--------
 TESTING.md                    | 46 +++++++++++++++-----
 helper_tools.py               | 97 ++++++++++++++++++++++++++++++++++++++++++-
 nozzle_1d_solver.py           |  7 +++-
 pyproject.toml                | 45 ++++++++++++++------
 quantum_tools.py              | 13 ++++--
 tests/contract.py             | 11 ++++-
 tests/test_output_contract.py | 33 ++++++++++++++-
 tests/test_sqls.py            |  4 +-
 time_solvers.py               |  4 +-
 10 files changed, 285 insertions(+), 52 deletions(-)
```

### What changed (file:line at `abf74941`)

**P1, SamplerV2 port (`7a1542a6`).**
- `quantum_tools.py` old L11 `from qiskit_ibm_runtime import SamplerV2 as
  Sampler` removed; nothing else in fvm used `Sampler`
  (`FakeProviderForBackendV2` stays lazy at L241, and in
  `utils/list_fake_backends.py` L7).
- `quantum_tools.py` L491-499 (`run_circuit_ibm`): `backend_type == 'ideal'`
  -> `qiskit_aer.primitives.SamplerV2.from_backend(self.backend)`; else
  (`fake`, `real-ibm`) -> lazy `from qiskit_ibm_runtime import SamplerV2`.
  `from_backend` keeps the very AerSimulator object when it is one
  (`sampler_v2.py` L96-103: `if isinstance(backend, AerSimulator):
  sampler._backend = backend`), so `method` and `device='GPU'` are preserved;
  `options={"backend_options": ...}` would build a new simulator and was not
  used. Result handling (`result[0].data.meas.get_counts()`) unchanged; no
  seed set (as before).
- Note: under runtime 0.49.0, `qiskit_ibm_runtime.SamplerV2(AerSimulator)`
  ran in local mode through qiskit's `BackendSamplerV2`
  (`fake_provider/local_service.py` L262), not through Aer's SamplerV2. Both
  sample `shots` times from the same circuit on the same simulator; the
  sampler implementation differs, the distribution does not.

**P2, `code_versions` (`4f44d5be`).**
- `helper_tools.py` L1-20 (stdlib imports moved to the top, constants
  `CODE_VERSION_SOURCES`, `CODE_VERSION_DISTS`, `_GIT_TIMEOUT_S = 5.0`),
  L153-226 (`_git`, `_dist_version`, `_git_state`, `_source_version`,
  `get_code_versions`).
- `nozzle_1d_solver.py` L5-6 (import), L392-393
  (`'code_versions': get_code_versions()` in the metadata dict, so every run,
  LU included, carries it).
- How it works, never imports a module: versions from
  `importlib.metadata.version`; package dir from `sys.modules[name].__file__`
  if already imported, else `importlib.util.find_spec(name).origin`; commit
  from `git -C <dir> rev-parse HEAD` only if `git -C <dir> ls-files
  --error-unmatch <file>` succeeds (guards against a site-packages copy
  inside this repo's ignored `.venv`, which would otherwise report the fvm
  commit); else the PEP 610 `direct_url.json` `vcs_info.commit_id`
  (`commit_source: 'direct_url'`). `dirty` = `git status --porcelain`
  non-empty (whole work tree, untracked files included). Every subprocess has
  `timeout=5 s`, `check=True`, `OSError` / `SubprocessError` caught; the
  whole function is wrapped so a failure becomes an `'error'` key, never a
  failed run. Wall time 0.195 s per call (laptop).
- Keys beyond the spec, deliberately: `dirty` and `commit_source` on the
  `sqls` / `linear_solvers` entries, `version` on `fvm`, and `python`.
- LU run: `python -X importtime` shows 0 `qiskit*` imports
  (`-nelem 2 -linsolver LU -iters 2`).
- Tests: `tests/contract.py` L49 (`'code_versions'` added to
  `METADATA_KEYS_COMMON`), L55-63 (`CODE_VERSIONS_KEYS`,
  `CODE_VERSIONS_FVM_KEYS`, `CODE_VERSIONS_SOURCE_KEYS`,
  `CODE_VERSIONS_COMMIT_SOURCES`, `SQLS_CHECKOUT`);
  `tests/test_output_contract.py` L96-123 `test_code_versions` on the SQLS,
  HHL and LU contract runs: exact key set, `fvm.commit` 40-hex, `fvm.dirty`
  bool, `fvm.path` = repo root, both source entries 40-hex with
  `commit_source` in (`git`, `direct_url`), stack entries look like versions,
  `numpy == np.__version__`; SQLS run only: `sqls.commit ==
  git -C /Users/agallojr/proj/src/q8020/sqls rev-parse HEAD`, `commit_source
  == 'git'`, `path == .../sqls/src/sqls`.

`code_versions` from a real run, verbatim (`-nelem 2 -linsolver SQLS
-shots 0 -iters 2`, at `abf74941`, 2026-10-15T04:38Z; `pprint` sorts keys,
the stored order is fvm, sqls, linear_solvers, qiskit, qiskit_aer,
qiskit_ibm_runtime, numpy, scipy, python):

```
{'fvm': {'commit': 'abf749413b98a0a9a99900c74361390807e40dc7',
         'dirty': False,
         'path': '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver',
         'version': '0.1.0'},
 'linear_solvers': {'commit': '66eadf0b4edcff100b20edf70a99e79cc69c5923',
                    'commit_source': 'direct_url',
                    'dirty': None,
                    'path': '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/linear_solvers',
                    'version': '0.1.0'},
 'numpy': '2.5.2',
 'python': '3.12.10',
 'qiskit': '2.5.2',
 'qiskit_aer': '0.17.2',
 'qiskit_ibm_runtime': '0.49.0',
 'scipy': '1.18.0',
 'sqls': {'commit': '9a4346a7d0255cb1b59429d3b9454358a5b5bb4d',
          'commit_source': 'git',
          'dirty': True,
          'path': '/Users/agallojr/proj/src/q8020/sqls/src/sqls',
          'version': '0.1.0'}}
```

`sqls.dirty` is True because the sqls builder's uncommitted SamplerV2 edit
(`src/sqls/runtime/quantum.py`) was in the work tree at that moment; this is
the flag doing its job. After phase 2, `linear_solvers` is expected to switch
to `commit_source: 'git'` with path
`/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers`.

**SQLS install hint (`6c672f2b`).** `time_solvers.py` L625-628: the "SQLS
back-end unavailable" message now says clone `../sqls` and run `uv sync`
(the `[sqls]` extra no longer exists); `tests/test_sqls.py` L384-386 asserts
`../sqls`, `` `uv sync` `` and no `[sqls]`.

**P3, pyproject (`abf74941`).** Diff against `f16720b3`:

```diff
-# All dependencies. The quantum HHL stack is pinned to the latest qiskit 2.5
-# line (qiskit 2.5.2 / aer 0.17.2 / ibm-runtime 0.49.0), verified against the
+# All dependencies. The quantum stack is pinned to the latest stable line
+# (qiskit 2.5.2 / aer 0.17.2 / ibm-runtime 0.50.0), verified against the
 # Q8020-CFD linear-solver fork. qiskit-algorithms is intentionally omitted: the
 # fork carries its own minimal AlgorithmResult replacement and does not import
 # it. This file (with uv.lock) is the single source of truth for dependencies;
 # the requirements*.txt files are deprecated.
+#
+# sqls (SVD-based Quantum Linear Solver, ORNL) and the HHL fork keep their git
+# URLs here so the published metadata names their origin, but uv resolves both
+# from sibling checkouts (see [tool.uv.sources]); `uv sync` never clones them.
+# sqls is a base dependency: the local path source makes it as available as
+# any other package, so the old opt-in [sqls] extra is gone.
 dependencies = [
     "numpy>=1.20.0",
     "scipy>=1.7.0",
@@ -26,22 +32,35 @@ dependencies = [
     "PyYAML",
     "python-dotenv",
     "quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers",
+    "sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git",
     "qiskit==2.5.2",
     "qiskit-aer==0.17.2",
-    "qiskit-ibm-runtime==0.49.0",
+    "qiskit-ibm-runtime==0.50.0",
     "qiskit-qasm3-import>=0.6.0",
 ]
 
-# Optional linear-solver back-ends. SQLS (SVD-based Quantum Linear Solver) is
-# an ORNL repo (access-gated), so it is NOT a base dependency: the SQLS scheme
-# is an opt-in add-in. Install with `pip install -e ".[sqls]"` if you have
-# access to the git remote, or point the extra at a local checkout:
-#   pip install -e ../sqls --no-deps        # sibling checkout, keep qiskit 2.5
-# SQLS pins qiskit==2.1.2 in its own pyproject, but only touches stable core
-# APIs (QuantumCircuit / Initialize / UnitaryGate / AerSimulator / SamplerV2),
-# so --no-deps against this repo's qiskit 2.5.2 stack is intended and verified.
-[project.optional-dependencies]
-sqls = ["sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git"]
+[dependency-groups]
+dev = ["pytest>=8"]
+
+# Both solver back-ends come from sibling clones, editable, on every node
+# (Frontier too): ../sqls (our detached sqls clone, source of record; its
+# git host code.ornl.gov is unreliable and we push nowhere) and
+# ../quantum_linear_solvers (the Q8020-CFD fork clone). See README.
+[tool.uv.sources]
+sqls = { path = "../sqls", editable = true }
+quantum_linear_solvers = { path = "../quantum_linear_solvers", editable = true }
+
+# sqls hard-pins qiskit==2.1.2, qiskit-aer==0.17.1, numpy==2.3.3,
+# scipy==1.16.2 but only uses stable core APIs; it is verified on this stack.
+# Overrides replace every requirement on these packages (sqls's and ours), so
+# they restate this project's own specifiers above.
+[tool.uv]
+override-dependencies = [
+    "qiskit==2.5.2",
+    "qiskit-aer==0.17.2",
+    "numpy>=1.20.0",
+    "scipy>=1.7.0",
+]
```

sqls's hard pins, read from `/Users/agallojr/proj/src/q8020/sqls/pyproject.toml`:
`qiskit==2.1.2`, `qiskit-aer==0.17.1`, `numpy==2.3.3`, `scipy==1.16.2` (its
`[examples]` extra, `matplotlib` and unpinned `qiskit-ibm-runtime`, is not
requested). The fork (`../quantum_linear_solvers/pyproject.toml`) needs only
`qiskit>=2.0`, numpy, scipy, ddt, `requires-python ~=3.12`: no override
needed.

Base dependency vs extra: base. With a local path source the access-gating
argument is moot, and a base dep makes the one sync command `uv sync`
(an extra would make it `uv sync --extra sqls`, and a plain `uv sync` would
then silently remove sqls from the venv). Kept the sqls git URL rather than a
bare `"sqls"` so pip-style tools never resolve an unrelated PyPI package of
that name (not checked whether one exists; no network in phase 1).

**P4, docs (`abf74941`).** `README.md` L47-108 (Installation rewritten:
sibling layout, the one sync command `uv sync`, path-source rationale,
override rationale, commits of record table, rollback, Frontier
precondition) and the Dependencies section (L261-271, was stale: qiskit
>= 1.0, qiskit-algorithms). `TESTING.md`: Run section (pytest after the
re-lock, unittest fallback), new 82-test timing, layout row for
`contract.py`, (c) hint text, (f) 22 common keys and a `code_versions`
bullet, pytest note.

Rollback recipe as documented (README L94-103):

```
git checkout f16720b3 -- pyproject.toml uv.lock   # pre-re-lock state
uv sync                      # re-fetches the fork from GitHub
VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps
VIRTUAL_ENV=.venv uv pip list | grep -i -E 'qiskit|sqls|linear'
```

### Verification (laptop, venv unchanged: runtime 0.49.0)

All with `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow -outdir
/tmp/order2-build-fvm/<name>`.

| Check | Command (args) | Wall | Result |
|---|---|---|---|
| SQLS shots, importtime | `-X importtime ... -nelem 2 -linsolver SQLS -shots 10000 -sqls_method full_svd -iters 2` | 1.37 s | rc 0; fidelity 0.99968, 0.99976 (>= 0.999); 0 `qiskit_ibm_runtime` lines in the import log |
| SQLS shots, `-W error::DeprecationWarning` | same args | 1.21 s | rc 0, empty stderr |
| HHL shots | `-X importtime ... -nelem 2 -linsolver HHL -shots 1000 -iters 1` (2026-10-15T04:30:51Z) | 8.45 s | rc 0; fidelity 0.95766 (>= 0.9); 12 files incl. `_shots1000` names |
| `import quantum_tools` | `python -c "import sys, quantum_tools; ..."` | <1 s | `qiskit_ibm_runtime` not in `sys.modules` |
| LU, importtime | `-nelem 2 -linsolver LU -iters 2` | ~1 s | 0 `qiskit*` imports |
| contract module | `python -m unittest tests.test_output_contract` | 23.1 s | 20 tests OK |

Where `qiskit_ibm_runtime` still gets imported: the HHL shots run imports it
(323 import-log lines), entering at top level as
`qiskit_ibm_runtime.transpiler.passes.basis` and
`...transpiler.passes.scheduling`, i.e. through qiskit's transpiler-plugin
entry-point discovery during `transpile()` (runtime registers stage plugins),
not through fvm code. The SQLS path does not call `transpile` (except the
`-v 2` cx count inside sqls), hence 0 there. Not removable from fvm short of
uninstalling runtime. The SQLS-shots 0 count also depends on the sqls
builder's (then uncommitted) port in `src/sqls/runtime/quantum.py` (Aer
SamplerV2 at its L209/L220), which was live in this venv through the
editable install; at sqls `9a4346a7` that function lazy-imports the runtime
sampler. The `-W error::DeprecationWarning` check is weak under runtime
0.49.0 (it does not deprecate SamplerV2); it must be repeated in phase 2 on
0.50.0.

Default suite, once, at the end (2026-10-15T04:37:06Z to 04:38:06Z,
working tree = `abf74941` content):

```
$ .venv/bin/python -m unittest discover -s tests
Ran 82 tests in 55.465s

OK (skipped=1)
real 59.51
```

(79 before + 3 new `test_code_versions`; the skip is the opt-in nelem-5 HHL
gate.) No shots test failed, so no retry for the concurrent sqls edits was
needed.

### Open doubts

1. **uv: path source + direct URL in `project.dependencies`.** The deps keep
   their `@ git+...` URLs while `[tool.uv.sources]` points at paths. I
   believe uv lets the source win, but I am not certain; older/newer uv may
   reject it ("conflicting URLs"). I grepped the installed uv 0.7.2
   (`/opt/homebrew/bin/uv`, Homebrew 2025-04-30) binary for such an error
   text and found none, which is suggestive, not proof. Fallback if `uv lock`
   rejects it in phase 2: bare names `"quantum_linear_solvers"` and `"sqls"`
   (pip metadata then loses the origin URL; record it in the comment).
2. **uv 0.7.2 is old** (2025-04-30). `[dependency-groups]`,
   `override-dependencies`, `editable = true` path sources are all supported
   there, but the lock it writes may differ in format from the one in
   `uv.lock` today; check `uv.lock` `version`/`revision` header in phase 2.
3. **Overrides are absolute.** `numpy>=1.20.0` / `scipy>=1.7.0` replace every
   numpy/scipy requirement in the graph, including matplotlib's and runtime
   0.50.0's lower bounds. With the existing lock's preferences uv should keep
   numpy 2.5.2 / scipy 1.18.0; verify in the phase-2 lock diff that neither
   moves. Same for `qiskit==2.5.2` vs runtime 0.50.0 / qiskit-mitigation /
   qasm3-import requirements on qiskit (an override would mask a real
   incompatibility; check their declared ranges in the lock).
4. **The fork becomes editable from `../quantum_linear_solvers`** (branch
   `feature/qiskit3-api-port`) instead of the git install of `66eadf0`. That
   changes the HHL code under test to whatever that branch's tip is at sync
   time; the 1e-10 gate fixtures (item 15) are the check.
5. **Lock still contacts PyPI** for `qiskit-ibm-runtime 0.50.0`,
   `qiskit-mitigation`, and pytest; only the two sibling packages are
   offline. "uv sync never touches the network" holds only after the cache
   is warm.
6. **pyproject comment** says the 0.50.0 stack is "verified against the
   fork"; true only after phase 2.
7. The SQLS contract assertion compares the run's `sqls.commit` to
   `rev-parse HEAD` at assertion time; a commit landing in the sqls clone
   between the cached run and the assertion (concurrent builder) would fail
   it spuriously. Window is a few seconds per suite run.

## Phase 2 (2026-10-15T05:05Z to 05:30Z): the single re-lock, sync, ladder

Sibling clones as handed over (not changed during phase 2, uncommitted, so
`dirty` True is expected): fork `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`
on `feature/qiskit3-api-port` (HEAD `66eadf0`, working tree modifies
`hhl.py`, three `matrices/*.py`, `pyproject.toml` with `qiskit>=2.2`, README,
test); sqls `/Users/agallojr/proj/src/q8020/sqls` on
`local/sampler-port-2026-10` (HEAD `9a4346a7`, working tree modifies
`src/sqls/runtime/quantum.py`). uv is `/opt/homebrew/bin/uv` 0.7.2.

### 1. Baseline

`git status --short` clean at `abf74941`. `uv.lock` copied to scratch.
`VIRTUAL_ENV=.venv uv pip list` (52 lines), relevant lines before:

```
numpy                  2.5.2
qiskit                 2.5.2
qiskit-aer             0.17.2
qiskit-ibm-runtime     0.49.0
qiskit-qasm3-import    0.6.0
quantum-linear-solvers 0.1.0
samplomatic            0.20.0
scipy                  1.18.0
sqls                   0.1.0         /Users/agallojr/proj/src/q8020/sqls
```

### 2. `uv lock` (once, 2026-10-15T05:07:36Z, 1.33 s, rc 0)

The `@ git+` URL plus path source combination was accepted on the first
attempt (phase-1 doubt 1 resolved: the source wins); dependency names
unchanged. `uv lock -v` log: `Ignoring existing lockfile due to mismatched
overrides` (expected, overrides are new), static `pyproject.toml` read from
`file:///.../quantum_linear_solvers` and `file:///.../sqls`; the only hosts
in the log are `https://pypi.org` (160 mentions) and
`https://files.pythonhosted.org` (54); no code.ornl.gov, no github.com fetch
(one DEBUG line names the old lock's github reference as a resolver
preference, no request).

```
Resolved 57 packages in 1.30s
Added colorama v0.4.6
Updated ibm-quantum-schemas v0.10.20260723 -> v0.12.20260921
Added iniconfig v2.3.1
Added pluggy v1.6.0
Added pygments v2.21.0
Added pytest v9.1.1
Updated qiskit-ibm-runtime v0.49.0 -> v0.50.0
Added qiskit-mitigation v0.1.1
Updated samplomatic v0.20.0 -> v0.21.0
Added sqls v0.1.0
```

Inspection: `qiskit-ibm-runtime` 0.50.0, `qiskit` 2.5.2, `qiskit-aer`
0.17.2, `qiskit-mitigation` 0.1.1, `pytest` 9.1.1 (all `registry =
https://pypi.org/simple`); `sqls` 0.1.0 `source = { editable = "../sqls" }`;
`quantum-linear-solvers` 0.1.0 `source = { editable =
"../quantum_linear_solvers" }` (was `git = ...#66eadf0b...`);
`grep -c 'git+' uv.lock` = 0; numpy 2.5.2 and scipy 1.18.0 unchanged;
lock header still `version = 1`, `revision = 2`; new `[manifest] overrides`
block and `[package.dev-dependencies]`. `git diff --stat uv.lock`: 140 lines
(+128, -12).

Phase-1 doubt 3 (overrides masking a real conflict): checked the installed
METADATA after sync: runtime 0.50.0 needs `qiskit<3,>=2.3.0`,
`numpy>=1.26.2`, `qiskit-mitigation>=0.1.1`; qiskit-mitigation 0.1.1 needs
`qiskit<3,>=2.3.0`, `numpy>=1.26`; samplomatic 0.21.0 `qiskit>=2.3.0`,
`numpy>=1.26`. All are satisfied by 2.5.2 / 2.5.2 without the overrides; the
overrides only neutralize sqls's own pins.

### 3. `uv sync` (2026-10-15T05:08:00Z, 2.58 s, rc 0)

```
Resolved 57 packages in 1ms
   Building fvm-euler-1d-solver @ file:///Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
   Building quantum-linear-solvers @ file:///Users/agallojr/proj/src/q8020/quantum_linear_solvers
Downloading qiskit-ibm-runtime (1.9MiB)
Prepared 6 packages in 2.08s
Uninstalled 5 packages in 255ms
Installed 10 packages in 42ms
 ~ fvm-euler-1d-solver==0.1.0 (from file:///Users/agallojr/proj/src/q8020/fvm_euler_1d_solver)
 - ibm-quantum-schemas==0.10.20260723
 + ibm-quantum-schemas==0.12.20260921
 + iniconfig==2.3.1
 + pluggy==1.6.0
 + pygments==2.21.0
 + pytest==9.1.1
 - qiskit-ibm-runtime==0.49.0
 + qiskit-ibm-runtime==0.50.0
 + qiskit-mitigation==0.1.1
 - quantum-linear-solvers==0.1.0 (from git+https://github.com/Q8020-CFD/quantum_linear_solvers@66eadf0b4edcff100b20edf70a99e79cc69c5923)
 + quantum-linear-solvers==0.1.0 (from file:///Users/agallojr/proj/src/q8020/quantum_linear_solvers)
 - samplomatic==0.20.0
 + samplomatic==0.21.0
```

sqls was already the editable install of the same path, so uv kept it.

Version line:

```
$ .venv/bin/python -c "import sqls, linear_solvers, qiskit, qiskit_aer, qiskit_ibm_runtime, pytest; print(...)"
/Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py 2.5.2 0.17.2 0.50.0 9.1.1
```

After (`uv pip list | grep -i -E 'qiskit|sqls|linear|mitigation|pytest|numpy|scipy|samplomatic'`):

```
numpy                  2.5.2
pytest                 9.1.1
qiskit                 2.5.2
qiskit-aer             0.17.2
qiskit-ibm-runtime     0.50.0
qiskit-mitigation      0.1.1
qiskit-qasm3-import    0.6.0
quantum-linear-solvers 0.1.0         /Users/agallojr/proj/src/q8020/quantum_linear_solvers
samplomatic            0.21.0
scipy                  1.18.0
sqls                   0.1.0         /Users/agallojr/proj/src/q8020/sqls
```

Full before/after diff of the pip list: only the lines above plus
`ibm-quantum-schemas` 0.10.20260723 -> 0.12.20260921, and new `iniconfig`
2.3.1, `pluggy` 1.6.0, `pygments` 2.21.0.

`.venv/bin/python -W error::DeprecationWarning -c "import linear_solvers,
sqls, qiskit_aer, qiskit_ibm_runtime; from linear_solvers import HHL"`: rc 0;
the same with `-W always` prints nothing (runtime 0.50.0 does not warn on
import; the fork's four qiskit-3.0 warnings are gone).

### 4. Offline re-sync

`uv sync --offline` rc 0 (`Resolved 57 packages in 1ms`, `Audited 55
packages`, 0.01 s); `uv sync --frozen --offline` rc 0 (0.01 s);
`uv lock --check --offline` rc 0 after the doc commits.

### 5. Test ladder

| Rung | Command (from repo root, `.venv/bin/python`) | Wall | Result |
|---|---|---|---|
| 1 import smoke | report 03 sec. 5.3 rung-1 one-liner, `-W always` | 1.40 s | `2.5.2 0.17.2 0.50.0 2.5.2 1.18.0`, `ok`, linear_solvers from the fork clone, sqls from `sqls/src`; one warning, the expected runtime `SamplerV2` deprecation (raised by the smoke line's own `from qiskit_ibm_runtime import SamplerV2`, not by our code); none of the four fork warnings |
| suite, unittest | `-m unittest discover -s tests -v` (05:08:39Z) | 46.1 s (47.0 s process) | `Ran 82 tests`, `OK (skipped=1)` |
| suite, pytest | `-m pytest tests -q -p no:cacheprovider` (05:09:31Z) | 46.2 s (46.8 s process) | `81 passed, 1 skipped, 36 subtests passed`; same 82 tests |
| gate | `FVM_GATE_TESTS=1 -m unittest tests.test_gate_fixture -v` (05:10:23Z) | 94.4 s (95.1 s process) | 7/7 OK at 1e-10 max-abs with the ported fork; nelem-5 HHL 86.59 s, nelem-2 HHL 7.76 s |
| 3b SQLS shots | `-W error::DeprecationWarning nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 10000 -sqls_repeats 1 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow` | 1.58 s | rc 0, empty stderr; fidelity 0.999940, 0.999910 |
| 4b HHL shots | `-W error::DeprecationWarning ... -nelem 2 -linsolver HHL -shots 1000 -iters 1` | 8.20 s | rc 0, no warning; fidelity 0.971400; transpiled 12 qubits, depth 68964, gates 74809; generate 1.83 s, transpile 2.30 s, run 1.69 s |
| 5a SQLS matched | `-nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow` | 2.13 s (solver 0.59 s) | `SOLUTION CONVERGED at iteration 6`; residual_total 12.375 -> 0.502 -> 0.0677 -> 3.82e-3 -> 5.40e-5 -> 3.10e-7 -> 2.08e-9 (Aug 1.26e-9); final_results max-abs vs Aug 1.65e-10 |
| 5b HHL matched | see below | 851.2 s process (solver 849.3 s) | completes 15 iters, all criteria met |

3b and 4b under `-W error::DeprecationWarning` are the load-bearing SamplerV2
checks on 0.50.0: neither path touches the runtime sampler any more (fvm via
`7a1542a6`, sqls via the sqls builder's port), and the fork port removed the
HHL deprecations, so the whole HHL nelem-2 shots run is warning-free.

Rung 5a fidelity (new / August 2026-08-17-sqls-local-v2):

| iter | new | August |
|---|---|---|
| 0 | 0.999978 | 0.999981 |
| 1 | 0.999980 | 0.999965 |
| 2 | 0.999978 | 0.999966 |
| 3 | 0.999977 | 0.999979 |
| 4 | 0.999972 | 0.999968 |
| 5 | 0.999962 | 0.999954 |
| 6 | 0.999958 | 0.451025 |

(The iter-6 tail collapse is gone: that is the item-9 zero pad, `3a88a37d`.)

Rung 5b: `.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1
-linsolver HHL -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -noshow
-outdir /tmp/order2-build-fvm/rung5b`, 2026-10-15T05:12:57Z to 05:27:08Z, rc
0, stderr only the `time` lines (no warnings). Deviation: the Bash tool caps
foreground commands at 600 s, so it was launched with the tool's background
mode and I waited on it doing nothing else (no detached jobs left behind).
August = `results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0`.

| iter | fidelity | qubits | depth | gates | generate s | transpile s | run s | Aug fidelity | Aug depth | Aug gates |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.998278 | 14 | 596688 | 641137 | 18.57 | 15.86 | 19.67 | 0.999023 | 596688 | 641145 |
| 1 | 0.987220 | 13 | 297051 | 319165 | 9.67 | 6.80 | 7.98 | 0.993408 | 297178 | 319447 |
| 2 | 0.992187 | 14 | 597963 | 642427 | 19.61 | 13.57 | 19.75 | 0.990220 | 596959 | 641325 |
| 3 | 0.991018 | 14 | 598202 | 642639 | 19.67 | 13.54 | 19.87 | 0.992667 | 597198 | 641662 |
| 4 | 0.993613 | 14 | 596951 | 641633 | 19.70 | 14.21 | 19.58 | 0.988029 | 597198 | 641662 |
| 5 | 0.986181 | 14 | 597971 | 642376 | 19.61 | 13.35 | 19.68 | 0.995348 | 597971 | 642435 |
| 6 | 0.992369 | 14 | 597469 | 641898 | 19.65 | 14.63 | 19.60 | 0.993453 | 596441 | 640898 |
| 7 | 0.991715 | 14 | 596449 | 640913 | 19.60 | 13.43 | 19.66 | 0.997279 | 595947 | 640658 |
| 8 | 0.984897 | 14 | 596935 | 641257 | 19.66 | 14.17 | 19.57 | 0.991217 | 596457 | 640824 |
| 9 | 0.994598 | 14 | 596441 | 641132 | 19.67 | 13.43 | 19.57 | 0.991094 | 598473 | 642819 |
| 10 | 0.994820 | 14 | 595923 | 640340 | 19.65 | 13.44 | 19.52 | 0.993216 | 597206 | 641670 |
| 11 | 0.992246 | 14 | 596943 | 641391 | 19.65 | 14.01 | 19.62 | 0.995240 | 596680 | 641098 |
| 12 | 0.993378 | 14 | 598736 | 643200 | 19.68 | 13.88 | 19.78 | 0.988286 | 598712 | 643423 |
| 13 | 0.996006 | 14 | 597461 | 642172 | 19.67 | 13.40 | 19.66 | 0.990884 | 597963 | 642417 |
| 14 | 0.998297 | 14 | 597453 | 641917 | 19.65 | 13.54 | 19.67 | 0.993340 | 596951 | 641370 |

Summary vs August: fidelity 0.98490 to 0.99830 (Aug 0.98803 to 0.99902; all
>= 0.98); residual_total at iter 14 7.149e-4 (Aug 6.795e-3; criterion
<= 1e-2; 9.5x lower, a different shot-noise realisation of an unseeded
150000-shot run, not a code effect we can claim); iter-0 depth identical
(596688), gates 641137 vs 641145 (-8, -0.0012 %); every iter within 0.2 % of
August in depth and gates; transpiled qubits 14 (13 at iter 1, as in
August); total 849.3 s solver (Aug 859.3 s). Same qiskit and aer, so the
near-identical circuit is expected; the per-iter depth jitter of ~0.2 % is
present in August too (it follows the Jacobian).

### 6. `code_versions` from a real run (rung 5b, verbatim, pprint-sorted)

```
{'fvm': {'commit': 'c074dc957f2df98e1b80e12682876ccf4b90506d',
         'dirty': False,
         'path': '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver',
         'version': '0.1.0'},
 'linear_solvers': {'commit': '66eadf0b4edcff100b20edf70a99e79cc69c5923',
                    'commit_source': 'git',
                    'dirty': True,
                    'path': '/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers',
                    'version': '0.1.0'},
 'numpy': '2.5.2',
 'python': '3.12.10',
 'qiskit': '2.5.2',
 'qiskit_aer': '0.17.2',
 'qiskit_ibm_runtime': '0.50.0',
 'scipy': '1.18.0',
 'sqls': {'commit': '9a4346a7d0255cb1b59429d3b9454358a5b5bb4d',
          'commit_source': 'git',
          'dirty': True,
          'path': '/Users/agallojr/proj/src/q8020/sqls/src/sqls',
          'version': '0.1.0'}}
```

(The rung-5a run, before the lock commit, shows `fvm.dirty` True for the
then-uncommitted `uv.lock`.)

### 7. Commits (phase 2)

```
1481073c Reflow pyproject comment to 88 columns
fa9eab2d Docs after re-lock: suite and gate timings, pytest command, verified stack comment
c074dc95 Re-lock: runtime 0.50.0, sqls and fork from sibling path sources, pytest dev group
```

`c074dc95` is `uv.lock` only (committed before rung 5b so that run records a
clean fvm). `fa9eab2d`: TESTING.md (post-lock unittest/pytest counts and
times, gate timing, pytest command with `-p no:cacheprovider`), the
pyproject "verified" comment (now true: suite, gate and ladder green),
`.gitignore` `.pytest_cache/`. `1481073c` fixes a 120-column comment line
that `fa9eab2d` introduced. Dependency names in `pyproject.toml` unchanged.
Working tree clean; nothing pushed; `main` untouched.

### Open doubts (phase 2)

1. **Dirty siblings are not reproducible from `code_versions` alone.** Both
   clones report HEAD (`66eadf0`, `9a4346a7`) plus `dirty: True`; the actual
   code of these runs is the uncommitted working trees. Until those are
   committed on their branches, the rung results cannot be tied to a commit.
   A cheap follow-up is to record `sha256(git diff HEAD)` alongside `dirty`.
2. **The lock embeds the siblings' `requires-dist`** (e.g. the fork's
   `qiskit>=2.2`). If a sibling's pyproject changes, a plain `uv sync` will
   re-resolve (needs PyPI); `uv sync --frozen` will not. Frontier copies must
   carry the same sibling pyprojects.
3. Rung 5b residual 7.1e-4 vs August 6.8e-3: both are shot-noise limited
   with no seed; do not read the 9.5x as an improvement.
4. `pytest tests -q` without `-p no:cacheprovider` writes `.pytest_cache/`
   (now gitignored).
5. uv 0.7.2 accepted the URL plus path-source combination; a newer uv on
   another node might not. If it rejects it, switch to bare names (phase-1
   note) rather than downgrade uv.

## Fix-up round (2026-10-15T06:30Z to 07:00Z): items X1 to X10

Sibling clones unchanged during the round, both still uncommitted: sqls on
`local/sampler-port-2026-10`, HEAD = main = `9a4346a7` (working tree:
`src/sqls/runtime/quantum.py`, shots via `simulator.run(...,
seed_simulator=seed)`); fork on `feature/qiskit3-api-port`, HEAD = main =
`66eadf0` (working tree: `hhl.py`, three `matrices/*.py`, `pyproject.toml`,
`setup.py`, README, test).

### Fixes, file:line at `54c2be0d`

| # | Change | Where |
|---|---|---|
| X1 | bare `"quantum_linear_solvers"`, `"sqls"`; both upstream URLs moved into the comment as provenance; "uv-only" stated | `pyproject.toml` L24-39 |
| X1 | README: uv-only, pip unsupported (ignores `[tool.uv.sources]` and the overrides); the URLs live only in a comment | `README.md` L47-53, L76-85 |
| X1 | Frontier docs: python 3.12, superseded note, uv recipe (`uv export --frozen --no-hashes --no-emit-project --no-dev`, `-e ` stripped so the conda env packs, `uv pip install --python <env>/bin/python --no-deps -r`), sibling layout | `docs/FRONTIER_CONDA_SETUP.md` L49-51, L70-96, L229-241; `docs/QUICKSTART_PARALLEL.md` L14-25 |
| X2 | overrides `numpy>=1.20.0,<3`, `scipy>=1.7.0,<2` (qiskit / aer exact) | `pyproject.toml` L59-68 |
| X4 | commits of record: both ports UNCOMMITTED, branch tips equal main, interim record = `sqls-patches/UNCOMMITTED-sampler-port.diff` and `fork-patches/UNCOMMITTED-qiskit3-api-port.diff`, use `uv sync --frozen` on other nodes; Frontier line says the same | `README.md` L86-103, L115-118 |
| X5 | no hard-coded path: `SIBLING_CHECKOUTS` (code_versions key -> checkout dir, package dir), `CODE_VERSIONS_OPTIONAL_KEYS = ['error']` | `tests/contract.py` L55-71 |
| X5 | `test_code_versions`: exact key order, no `error`; per sibling under `helpers.REPO.parent`: entry None -> readable `fail`, resolved path equal, commit 40-hex and equal to `helper_tools._git(checkout, 'rev-parse', 'HEAD')`, `commit_source == 'git'`, `dirty` bool; checkout absent -> `skipTest` with the path; `assertRegex(x or '', ...)` so no None reaches the regex; raw subprocess dropped | `tests/test_output_contract.py` L107-145 |
| X6 | `CODE_VERSIONS_KEYS` tuple; `get_code_versions` starts from `dict.fromkeys(CODE_VERSIONS_KEYS)`; `error` documented as the optional extra key | `helper_tools.py` L20-24, L212-232 |
| X6 | `TestCodeVersionsHelper`: helper keys equal contract keys; with `_git_state` patched to raise, all keys present (None) plus `error == 'RuntimeError: boom'` | `tests/test_output_contract.py` L148-163 |
| X7 | `run_circuit_ibm`: `ideal` / `fake` -> `self.backend.run(circ_transpile, **run_kwargs)`, `result.get_counts()`; `real-*` -> lazy runtime `SamplerV2`, `result[0].data.meas.get_counts()`; `run_kwargs = {'shots': shots}` is where `seed_simulator` goes later (item 11); no `qiskit_aer.primitives` import; timing and verbosity prints kept. Bitstring keys are identical in both forms because the HHL circuit has one register (`measure_all`, L329) | `quantum_tools.py` L486-518 |
| X8 | `HHL_SHOTS = 1000`, `HHL_SHOTS_NELEM2_ARGS` (`-nelem 2 -linsolver HHL -shots 1000 -iters 1` + base args incl. `-initers 1`) | `tests/helpers.py` L58-61 |
| X8 | `TestHHLShotsNelem2` (fidelity >= 0.9, nshots, 12 transpiled qubits); `TestRunCircuitBackends` (Bell circuit, 2000 shots, ideal only `00`/`11` each > 40 %, `fake_manila` `00`+`11` >= 80 % and each > 30 %, counts sum to shots) | `tests/test_hhl.py` L110-166 |
| X8 | `TestHHLShotsOutputContract` (mixin gained `nshots` / `shots_tag`): exact 12-file set, globs, columns, metadata (nshots 1000), code_versions, qc_metadata name and 21 columns | `tests/test_output_contract.py` L21-35, L246-262 |

### X3: the extra lock (authorized amendment), offline

```
$ uv lock --offline          # 2026-10-15T06:38:56Z, 0.12 s, rc 0
Resolved 57 packages in 93ms
```

Inspection: qiskit-ibm-runtime 0.50.0, qiskit 2.5.2, qiskit-aer 0.17.2,
qiskit-mitigation 0.1.1, pytest 9.1.1, numpy 2.5.2, scipy 1.18.0 (all
registry); `sqls` `source = { editable = "../sqls" }`,
`quantum-linear-solvers` `source = { editable = "../quantum_linear_solvers" }`;
`grep -c 'git+' uv.lock` = 0; `grep -c 'source = { git' uv.lock` = 0.
`git diff --stat uv.lock`: 4 lines (2+, 2-), only the `[manifest]`
override specifiers:

```
-    { name = "numpy", specifier = ">=1.20.0" },
+    { name = "numpy", specifier = ">=1.20.0,<3" },
-    { name = "scipy", specifier = ">=1.7.0" },
+    { name = "scipy", specifier = ">=1.7.0,<2" },
```

(The project's own `requires-dist` for sqls / the fork did not change: the
phase-2 lock had already recorded them as the path sources.)

`uv sync --frozen --offline`: 1.84 s, rc 0; rebuilt only
`fvm-euler-1d-solver` and `quantum-linear-solvers` (the fork's `setup.py` /
pyproject had changed in its working tree), no downloads. Version line
unchanged:

```
/Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py 2.5.2 0.17.2 0.50.0 9.1.1
```

`-W error::DeprecationWarning -c "import linear_solvers, sqls, qiskit_aer,
qiskit_ibm_runtime; from linear_solvers import HHL"`: rc 0.

### X9: ladder on the final tree

| Step | Command | Time (UTC) | Wall | Result |
|---|---|---|---|---|
| suite, unittest | `.venv/bin/python -m unittest discover -s tests -v` | 06:43:37Z | 58.8 s (65.0 s process) | `Ran 95 tests`, `OK (skipped=1)` |
| suite, pytest | `.venv/bin/python -m pytest tests -q -p no:cacheprovider` | 06:44:43Z | 55.0 s (55.5 s process) | `94 passed, 1 skipped, 1 warning, 36 subtests passed`; same 95 tests |
| gate | `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` | 06:45:50Z | 94.5 s (95.2 s process) | `Ran 7 tests`, `OK` (1e-10); nelem-5 HHL 86.52 s, nelem-2 HHL 7.95 s |
| 3b SQLS shots | `-W error::DeprecationWarning -X importtime nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 <base>` | 06:47:34Z | 1.62 s | rc 0, no warnings; fidelity 0.999983, 0.999971; 0 `qiskit_aer.primitives`, 0 `qiskit_ibm_runtime` imports |
| 4b HHL shots | `-W error::DeprecationWarning -X importtime ... -nelem 2 -linsolver HHL -shots 1000 -iters 1 <base>` | 06:47:36Z | 8.00 s | rc 0, no warnings; fidelity 0.937285; 12 qubits, depth 68964, gates 74827; generate 1.87 s, transpile 2.22 s, run 1.47 s |
| 5a SQLS matched | `nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow` | 06:48:08Z | 1.62 s (solver 0.16 s) | `SOLUTION CONVERGED at iteration 6`; fidelity 0.999962 to 0.999986 on all 7 steps (>= 0.9999); final_results max-abs vs August 1.66e-10 (<= 1e-6) |
| 5b HHL matched | see below | 06:48:16Z to 06:58:28Z | 611.9 s process (solver 609.9 s) | gate met |

`<base>` = `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow -outdir
/tmp/order2-fixup-fvm/<rung>`. The pytest warning is runtime's
`UserWarning: Properties of fake_nighthawk are not intended to represent
typical nighthawk error values` (`fake_provider/backends/nighthawk/fake_nighthawk.py:78`),
raised when `FakeProviderForBackendV2` loads its backend list in
`test_fake_bell`; not ours. In-process: `test_ideal_bell` 0.03 s,
`test_fake_bell` 0.51 s; the shared HHL shots CLI run 7.55 s.

5a residual_total: 12.375, 0.621, 0.0607, 3.52e-3, 6.12e-5, 3.04e-7,
1.35e-9.

**Import check (X9).** Ideal SQLS shots: no `qiskit_aer.primitives*` and no
`qiskit_ibm_runtime*` in the import log. Ideal HHL shots: fvm code imports
neither, but both appear transitively. The top-level entry is
`qiskit_ibm_runtime.transpiler.passes.basis` (qiskit's transpiler-plugin
entry-point discovery during `transpile()`, as in phase 2). Importing that
module runs the `qiskit_ibm_runtime` package init (`qiskit_runtime_service`,
`session`, `batch`, ...), which loads `qiskit_ibm_runtime.fake_provider.local_service`
-> `fake_provider.executor.run_quantum_program`, and that imports
`qiskit_aer.primitives` (5 import-log lines: `sampler`, `estimator`,
`estimator_v2`, `sampler_v2`, package). So the remaining `qiskit_aer.primitives`
on the HHL path is runtime's, pulled in by plugin discovery; it is expected
and not ours. The same chain fires when a `fake` backend is built
(`qiskit_ibm_runtime.fake_provider` import).

**Rung 5b** (`.venv/bin/python nozzle_1d_solver.py -nelem 5 -time_scheme
BDF1 -linsolver HHL -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10
-noshow -outdir /tmp/order2-fixup-fvm/rung5b`, rc 0, stderr only the `time`
lines; run in the Bash tool's background mode and waited on, as in phase 2):

| iter | fidelity | residual_total | qubits | depth | gates | generate s | transpile s | run s |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.997655 | 1.2375e+01 | 14 | 596688 | 641136 | 18.80 | 14.25 | 18.20 |
| 1 | 0.996769 | 1.6643e+00 | 13 | 297552 | 319707 | 9.80 | 6.69 | 7.17 |
| 2 | 0.996992 | 1.4916e+00 | 13 | 297051 | 319318 | 9.71 | 6.76 | 7.20 |
| 3 | 0.997946 | 1.3381e+00 | 13 | 297298 | 319459 | 9.77 | 6.77 | 7.15 |
| 4 | 0.996048 | 1.2142e+00 | 13 | 297058 | 319336 | 9.80 | 6.68 | 7.23 |
| 5 | 0.995795 | 1.0851e+00 | 13 | 297559 | 319732 | 9.79 | 7.39 | 7.29 |
| 6 | 0.997570 | 9.6573e-01 | 13 | 297425 | 319529 | 9.77 | 6.86 | 7.16 |
| 7 | 0.997369 | 8.4994e-01 | 13 | 297312 | 319471 | 9.80 | 6.78 | 7.18 |
| 8 | 0.994160 | 7.5050e-01 | 13 | 297552 | 319691 | 9.79 | 7.40 | 7.17 |
| 9 | 0.998231 | 6.4967e-01 | 14 | 593132 | 637495 | 19.39 | 13.36 | 17.76 |
| 10 | 0.998217 | 5.6766e-01 | 14 | 594654 | 639298 | 19.48 | 13.49 | 18.00 |
| 11 | 0.998148 | 5.0227e-01 | 14 | 597724 | 642114 | 19.55 | 13.52 | 17.97 |
| 12 | 0.997358 | 4.4412e-01 | 14 | 597708 | 642122 | 19.53 | 13.42 | 18.19 |
| 13 | 0.998494 | 3.8648e-01 | 14 | 597469 | 641877 | 19.58 | 13.45 | 18.08 |
| 14 | 0.998015 | 3.3800e-01 | 14 | 595939 | 640403 | 19.59 | 13.44 | 18.01 |

(residual_total is the row of `residual_*.csv` for that iteration, i.e. the
residual before that step's update; `final_residual` in the metadata =
0.33800 at iteration 14; `converged` False.)

Gate (re-specified): completes 15 iterations: yes. Iteration-0 circuit 14
qubits, depth 596688 (0.0 % vs 596688), gates 641136 (-0.0014 % vs 641145):
pass. Recorded, not gated: fidelity 0.99416 to 0.99849 (every step >=
0.994); residual_total at iteration 14 = 0.338, inside the envelope (Nov
2025 Frontier 3e-7 to 0.46; August 6.8e-3; new-stack runs 7.15e-4 and 1.546).
This run spent iterations 1 to 8 on 13-qubit circuits (August: only
iteration 1), which is why the total is 610 s against 849 s (phase 2) and
859 s (August); the Newton residual fell only ~6 % per step in that stretch
despite fidelity >= 0.994, the slow-convergence regime the envelope already
spans.

`code_versions` (rung 5b, verbatim, pprint-sorted):

```
{'fvm': {'commit': '54c2be0d646f1c34a9a682b520551afd24b8187e',
         'dirty': False,
         'path': '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver',
         'version': '0.1.0'},
 'linear_solvers': {'commit': '66eadf0b4edcff100b20edf70a99e79cc69c5923',
                    'commit_source': 'git',
                    'dirty': True,
                    'path': '/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers',
                    'version': '0.1.0'},
 'numpy': '2.5.2',
 'python': '3.12.10',
 'qiskit': '2.5.2',
 'qiskit_aer': '0.17.2',
 'qiskit_ibm_runtime': '0.50.0',
 'scipy': '1.18.0',
 'sqls': {'commit': '9a4346a7d0255cb1b59429d3b9454358a5b5bb4d',
          'commit_source': 'git',
          'dirty': True,
          'path': '/Users/agallojr/proj/src/q8020/sqls/src/sqls',
          'version': '0.1.0'}}
```

### X10: commits

```
$ git log --oneline f16720b3..HEAD
54c2be0d TESTING: fix-up round counts, HHL shots and backend tests, code_versions checks
61e7ca08 Docs: uv-only install, uncommitted sibling ports, Frontier uv recipe with python 3.12
c0af3997 Bare sqls and fork names, capped numpy scipy overrides, offline re-lock
a1f20439 Tests: sibling-relative code_versions checks, HHL shots case, ideal and fake run_circuit_ibm
bf20c669 code_versions always carries the full contract key set
5dae1d89 HHL shots: backend.run for ideal and fake, runtime SamplerV2 only for real-ibm
1481073c Reflow pyproject comment to 88 columns
fa9eab2d Docs after re-lock: suite and gate timings, pytest command, verified stack comment
c074dc95 Re-lock: runtime 0.50.0, sqls and fork from sibling path sources, pytest dev group
abf74941 Runtime 0.50.0 pin, sqls and fork as sibling path sources with overrides, dev group, docs
6c672f2b SQLS unavailable hint points at the sibling clone and uv sync
4f44d5be Record code_versions in run metadata for fvm sqls fork and stack
7a1542a6 Aer SamplerV2 for ideal HHL shots, runtime SamplerV2 only for fake and real
```

`git show --stat` of the new ones: `5dae1d89` quantum_tools.py 28 (+14
-14); `bf20c669` helper_tools.py 10 (+8 -2); `a1f20439` tests/contract.py 9,
tests/helpers.py 4, tests/test_hhl.py 67, tests/test_output_contract.py 120
(+168 -32 total); `c0af3997` pyproject.toml 20, uv.lock 4 (+14 -10);
`61e7ca08` README.md 38, docs/FRONTIER_CONDA_SETUP.md 41,
docs/QUICKSTART_PARALLEL.md 12 (+63 -28); `54c2be0d` TESTING.md 50 (+40
-10). The code commits precede the ladder; `54c2be0d` (docs only) landed
before rung 5b finished so that run records a clean fvm. Working tree
clean; nothing pushed; `main` untouched. `7a1542a6`'s Aer-SamplerV2 code is
superseded by `5dae1d89`.

### Open doubts (fix-up round)

1. **Frontier recipe is untested.** The `uv export | sed 's/^-e //' | uv pip
   install --no-deps` path was checked only as far as `uv export --frozen`
   output on the laptop (lists `-e ../quantum_linear_solvers`, `-e ../sqls`
   and the 53 pinned packages, the Windows-only `sspilib` behind a marker).
   The Aer GPU (ROCm) source build on Frontier still replaces the PyPI
   `qiskit-aer` wheel there; that interaction is not covered.
2. **Dirty siblings** (unchanged from phase 2): `code_versions` gives HEAD
   plus `dirty: True`; the code that ran is the uncommitted working trees
   matching the two `UNCOMMITTED-*.diff` files. Recording a diff hash would
   close this.
3. **HHL ideal shots now sample through `AerSimulator.run`** rather than a
   sampler primitive (phase 1: Aer SamplerV2; before: runtime local-mode
   `BackendSamplerV2`). Same circuit, same simulator, same shot count;
   fidelities in the ladder (0.937 and 0.971 at 1000 shots, 0.994 to 0.998
   at 150000) sit in the old range, but unseeded runs cannot prove
   equivalence bit for bit.
4. **5b convergence varies a lot run to run** (iteration-14 residual 0.338,
   7.15e-4, 1.546 on this stack). The circuit metrics are stable to 0.2 %;
   the spread is in the Newton trajectory (13 vs 14 transpiled qubits per
   step changes with the Jacobian). Worth a seeded study under item 11
   before any convergence claim.

## Fix-up round 2 (2026-10-15T07:20Z to 07:45Z): items Y1 to Y7

No venv change, no `uv lock` / `uv sync` (pyproject untouched). Siblings
unchanged and still uncommitted.

### Fixes, file:line at `e13cbb1e`

| # | Change | Where |
|---|---|---|
| Y1 | Frontier recipe keeps sqls and the fork editable: the `sed 's/^-e //'` is gone; preferred path `uv sync --frozen`; conda path = `uv export --frozen --no-hashes --no-emit-project --no-dev` (keeps the two `-e` sibling lines, run from the repo root) + `uv pip install --python $CONDA_ENV_PATH/bin/python --no-deps -r`; explicit alternative `uv pip install --no-deps -e ../sqls -e ../quantum_linear_solvers`; states that `code_versions[...]['commit_source']` must read `git` for valid provenance; clones must be readable at the same absolute path on compute nodes; `conda pack --ignore-editable-packages` if it refuses | `docs/FRONTIER_CONDA_SETUP.md` L76-112, complete-workflow block; `docs/QUICKSTART_PARALLEL.md` L18-27 |
| Y2 | runtime `SamplerV2` branch gets only `shots=self.nshots`; comment says it is unreachable today because `get_backend` raises for `real-ibm` (its `QiskitRuntimeService` construction is commented out); caller comment fixed | `quantum_tools.py` L492-505, L583-584 |
| Y5 | one `_run_on_backend(self, circ, **run_kwargs)` (backend.run with `shots=self.nshots`, job-id print at `-v 2`, `result().get_counts()`, timing print, counts print at `-v 2`); `run_circuit_iqm` is a one-line wrapper; `run_circuit_ibm` tests `in ('ideal', 'fake')` once | `quantum_tools.py` L468-491 |
| Y6 | each code_versions entry collected under its own `try` (collector per key); failures go to `error = {key: 'Type: message'}`, the other entries stay filled | `helper_tools.py` L239-262 |
| Y7 | `diff_sha256` in the fvm, sqls and linear_solvers entries: sha256 hex of the raw `git diff HEAD` bytes when dirty, else None (`_git_bytes` L159-166, `_git_state` L182-201 now returns `(commit, dirty, diff_sha256)`, `_fvm_version` L231-236) | `helper_tools.py` |
| Y7 | contract keys: fvm `[path, commit, dirty, diff_sha256, version]`, sources `[path, commit, dirty, diff_sha256, commit_source, version]`; `error` documented as `{key: message}` | `tests/contract.py` L55-67 |
| Y3, Y7 | `test_code_versions`: every sibling entry must be non-None, its key set and an on-disk `path` are checked always, `diff_sha256` 64-hex iff dirty (helper `assert_diff_sha256` L109-114); only the commit equality, `commit_source == 'git'` and diff-hash-equals-current-`git diff HEAD` checks are skipped for an absent checkout, with the path in the skip reason | `tests/test_output_contract.py` L116-169 |
| Y6 | `test_failure_keeps_key_set_and_other_entries`: `_git_state` raises `TimeoutError` for the `src/sqls` path only; result keeps all keys, `sqls` None, `error == {'sqls': 'TimeoutError: git timed out'}`, fvm / linear_solvers / numpy intact. `test_clean_tree_has_no_diff_hash`: clean tree -> `(commit, False, None)` | `tests/test_output_contract.py` L179-206 |
| Y4 | Bell tests seeded: `transpile(..., seed_transpiler=1234)` and `qh.backend.set_options(seed_simulator=1234)` on both the AerSimulator and `fake_manila`; both honor it (checked: 3 seeded runs each gave identical counts, ideal `{'11': 997, '00': 1003}`, fake `{'01': 52, '10': 70, '11': 907, '00': 971}`), so the tests assert a second seeded run is identical and keep the loose bounds | `tests/test_hhl.py` L141-181 |
| Y4 | CLI HHL 1000-shot fidelity floor 0.9 -> 0.8, comment: unseeded, post-selection keeps ~100 shots, observed 0.937 to 0.97, item 11 adds `-seed` and tightens it | `tests/test_hhl.py` L121-125 |
| hygiene | `grep -rn "/Users/" tests/*.py` was not empty: `tests/make_fixtures.py` (ARCHIVE, SQLS_SRC) and a comment in `tests/test_classical.py` (pre-existing, from `5af4dd2f`); now `REPO.parent / 'q8020-cfd-experiments' / ...` and `REPO.parent / 'sqls'` (resolve to the same paths here), comment says `<repo parent>/...`. The grep is now empty | `tests/make_fixtures.py` L32-35, `tests/test_classical.py` L24 |

### Verification

| Step | Command | Time (UTC) | Wall | Result |
|---|---|---|---|---|
| suite, unittest | `.venv/bin/python -m unittest discover -s tests -v` (code identical to `1165be88`, before the commits) | 07:37:00Z | 56.3 s (57.5 s process) | `Ran 96 tests`, `OK (skipped=1)` |
| suite, pytest | `.venv/bin/python -m pytest tests -q -p no:cacheprovider` (at `7831d352`) | 07:38:20Z | 56.4 s (56.9 s process) | `95 passed, 1 skipped, 1 warning, 36 subtests passed`; same 96 tests; the warning is runtime's `fake_nighthawk` UserWarning |
| gate | `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v` | 07:39:17Z | 93.5 s (94.2 s process) | `Ran 7 tests`, `OK`; nelem-5 HHL 85.74 s |
| 3b | `-W error::DeprecationWarning nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 <base>` | 07:41:01Z | 1.67 s | rc 0, no warnings; fidelity 0.999918, 0.999977 |
| 4b | `-W error::DeprecationWarning ... -nelem 2 -linsolver HHL -shots 1000 -iters 1 <base>` | 07:41:03Z | 7.68 s | rc 0, no warnings; fidelity 0.951109 |
| code_versions | `nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 0 -iters 2 <base>` | 07:41:11Z | ~1.5 s | rc 0, below |
| hygiene | `grep -rn "/Users/" tests/*.py`; added lines <= 88 chars, no trailing whitespace | | | empty; ok |

96 tests = 95 + `test_clean_tree_has_no_diff_hash` (the failure test was
replaced, not added).

`code_versions` (SQLS `-shots 0` nelem 2 at `7831d352`, verbatim,
pprint-sorted; stored key order `fvm, sqls, linear_solvers, qiskit,
qiskit_aer, qiskit_ibm_runtime, numpy, scipy, python`):

```
{'fvm': {'commit': '7831d35230751a86e15cc24994530c7f43599612',
         'diff_sha256': None,
         'dirty': False,
         'path': '/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver',
         'version': '0.1.0'},
 'linear_solvers': {'commit': '66eadf0b4edcff100b20edf70a99e79cc69c5923',
                    'commit_source': 'git',
                    'diff_sha256': '98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f',
                    'dirty': True,
                    'path': '/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers',
                    'version': '0.1.0'},
 'numpy': '2.5.2',
 'python': '3.12.10',
 'qiskit': '2.5.2',
 'qiskit_aer': '0.17.2',
 'qiskit_ibm_runtime': '0.50.0',
 'scipy': '1.18.0',
 'sqls': {'commit': '9a4346a7d0255cb1b59429d3b9454358a5b5bb4d',
          'commit_source': 'git',
          'diff_sha256': '2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9',
          'dirty': True,
          'path': '/Users/agallojr/proj/src/q8020/sqls/src/sqls',
          'version': '0.1.0'}}
```

Both sibling hashes equal `shasum -a 256` of the interim patch files, so the
run metadata now pins the exact uncommitted code:
`sqls-patches/UNCOMMITTED-sampler-port.diff` = `2d4c5a7c...96d4e9`,
`fork-patches/UNCOMMITTED-qiskit3-api-port.diff` = `98690527...03df1f`
(and `git -C <clone> diff HEAD | shasum -a 256` gives the same).

### Commits

```
e13cbb1e TESTING: wrap a long line
9d0157ba TESTING: fix-up round 2 counts, diff_sha256 and seeded Bell test notes
7831d352 Frontier docs: keep sqls and fork editable so code_versions records git commits
1165be88 Tests: diff_sha256 and absent-sibling checks, seeded Bell tests, looser HHL shots floor, no hard-coded paths
0b783a48 code_versions: per-entry error isolation and diff_sha256 for dirty trees
8bdce342 Shared _run_on_backend for IQM and ideal or fake, runtime sampler gets shots only and is marked unreachable
```

`git show --stat`: `8bdce342` quantum_tools.py (+22 -33); `0b783a48`
helper_tools.py (+57 -28); `1165be88` tests/contract.py 11,
tests/make_fixtures.py 7, tests/test_classical.py 2, tests/test_hhl.py 18,
tests/test_output_contract.py 64 (+79 -23); `7831d352`
docs/FRONTIER_CONDA_SETUP.md 32, docs/QUICKSTART_PARALLEL.md 5 (+29 -8);
`9d0157ba` TESTING.md (+44 -26); `e13cbb1e` TESTING.md (+2 -1). Working tree
clean; nothing pushed; `main` untouched.

### Open doubts (round 2)

1. `diff_sha256` covers tracked changes only (`git diff HEAD`); an untracked
   new module in a sibling would show `dirty: True` with a hash that does not
   include it. Neither sibling has untracked files today.
2. The hash is of the bytes git prints, so a user-level git config that
   changes diff output (e.g. `diff.noprefix`, `diff.mnemonicPrefix`, a
   different `core.abbrev`) on another node gives a different hash for the
   same tree. Passing `--no-ext-diff --no-color` and fixed prefixes would
   harden it; not done, to keep `git diff HEAD | shasum -a 256` as the
   one-line reproduction.
3. The Frontier conda path with editable installs and `conda pack` is still
   untested (`--ignore-editable-packages` is from memory of conda-pack's
   CLI, not verified here).

- 2026-10-16T00:39Z (builder 6, doc-only fvm commit `16dbde20`): the fork port is COMMITTED and PUSHED by the operator's decision, fork branch `feature/sqls-aiaa-4q26` (renamed 2026-10-16 from its port-era name) tip `9d1d7bb` (five commits `e7be361`, `3fe7192`, `90b177a`, `1164a45`, `9d1d7bb` over main `66eadf0`, clean tree, equal to `origin/feature/sqls-aiaa-4q26` at `https://github.com/Q8020-CFD/quantum_linear_solvers.git`), so `code_versions.linear_solvers` now reads `9d1d7bb`, `dirty` False; README (commits-of-record table, status and Frontier paragraphs, incl. the not-done option of re-pinning the fork source to `git+...@9d1d7bb` with one re-lock) and TESTING (gate provenance lines) updated; `pyproject.toml` names no fork commit and is untouched.
- The sqls port stays an UNCOMMITTED working tree on `local/sampler-port-2026-10` (tip `9a4346a7`, `M src/sqls/runtime/quantum.py`; the clone is the only copy); its record remains `sqls-patches/UNCOMMITTED-sampler-port.diff`, sha256 `c8425988ddc64d72385dcf026eb5125c665fdbe3d0c1a7b85a9e4b6250090752` re-verified 2026-10-16T00:38Z, and runs show `dirty: True` for sqls only.
