# Code inventory — fvm_euler_1d_solver and sqls

Read-only inventory taken 2026-10-15T01:30Z to 2026-10-15T01:45Z on the
macOS laptop (mesh librarian node). No fetch, pull, install, or solver run was
performed. Tokens in remote URLs are redacted. All times are UTC ISO 8601 unless
a source carried only a local offset, in which case both are given.

The two code bases we will modify:

| | Code base | The repo we modify | Local path |
|---|---|---|---|
| A | 1D Euler nozzle FVM solver | `Q8020-CFD/fvm_euler_1d_solver` (our private GitHub fork; parent is Mohammad Alhawwary's `mhawwary/fvm_euler_1d_solver`) | `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` |
| B | ORNL SVD-based quantum linear solver | `olcf-qcfd/sqls` on ORNL GitLab (`https://code.ornl.gov/olcf-qcfd/sqls.git`); we hold a plain clone, no fork | `/Users/agallojr/proj/src/q8020/sqls` |

## A. fvm_euler_1d_solver

### A.1 Repo identity

- Path: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`
- `git remote -v` (token redacted):
  `origin  https://github.com/Q8020-CFD/fvm_euler_1d_solver.git (fetch)` /
  `(push)`
- Current branch: `main`
- HEAD: `ef7f0a8b2247615b56e4391fa1804b59825de217`
  "Add optional SQLS linear solver alongside HHL", authored
  2026-08-17T19:22:59-04:00 = 2026-08-17T23:22:59Z (Andy Gallo).
- `git status --short`: empty (clean working tree; ignored entries are `.venv/`,
  `__pycache__/`, `fvm_euler_1d_solver.egg-info/`, `output/`, `src/`).
- Ahead/behind `origin/main`: 0 / 0 (as of the last fetch; GitHub `pushedAt`
  2026-08-17T23:23:05Z matches HEAD, so the remote is current).
- Tags: none.
- GitHub: `gh repo view Q8020-CFD/fvm_euler_1d_solver` ->
  `isFork: true`, `parent: mhawwary/fvm_euler_1d_solver` (parent node id
  `R_kgDOQF9MNQ`), `pushedAt: 2026-08-17T23:23:05Z`, `visibility: PRIVATE`.

### A.2 Branches (`git branch -a -v`, full shas)

| Branch | Tip sha | Subject |
|---|---|---|
| `main` (local, current) | `ef7f0a8b2247615b56e4391fa1804b59825de217` | Add optional SQLS linear solver alongside HHL |
| `archive/solverfw-v2-port` (local, upstream shows `[gone]`) | `2b63f6f7c2a75cfbfb1f29125f8877b5ff95fc10` | Point quantum reqs at the Q8020-CFD fork + qiskit 2.3+ |
| `origin/HEAD` | -> `origin/main` | |
| `origin/main` | `ef7f0a8b2247615b56e4391fa1804b59825de217` | Add optional SQLS linear solver alongside HHL |
| `origin/archive/solverfw-v2-port` | `2b63f6f7c2a75cfbfb1f29125f8877b5ff95fc10` | Point quantum reqs at the Q8020-CFD fork + qiskit 2.3+ |
| `origin/archive-master` | `11b181c6fce66d573b8a7018406c275f6c26a40b` | Mark master as deprecated; use main |
| `origin/archive/feature/agmods` | `9f243fa39103f05a0b845d384ec04837d0d7eacc` | add global verbosity and nozzle cmd line switch to control matrix printing |
| `origin/archive/feature/tpile` | `ee18798cb0126c9c79f41391e0626d576d57500a` | add heat map to report |
| `origin/archive/feature/wf-pkg` | `ccf8fbfe4c30ae71609ac997b04355f3374e3303` | logging |
| `origin/archive/qiskit-hhl-2` | `9e76e398487ee3cd9fd9abdde80d47053619f423` | Merge Mohammad's feature/qiskit-hhl changes: steady mode, improved plotting, detailed guide, timing metadata |
| `origin/backup-old-main` | `913c793df71ee806c7311556f5580cabeff74a14` | Initial commit |
| `origin/bloqade-test` | `3eeca2229266cb068bd7664cd0bea23fbd22abe0` | add gitignore |
| `origin/feature/qiskit-hhl` | `a5317f2b06a93b6d466239d956f89b3569049cc3` | Adding the detailed guide |

Note: the local `archive/solverfw-v2-port` reports its upstream as `[gone]`
although `origin/archive/solverfw-v2-port` exists at the same sha; its
`branch.<name>.merge` setting points at a ref name that no longer exists. Harmless.

Recent history of `main` (last 15, `%h %ad %an %s`):

```
ef7f0a8b 2026-08-17T23:22:59Z Andy Gallo          Add optional SQLS linear solver alongside HHL
a885ef47 2026-08-17T21:16:25Z Andy Gallo          Bump quantum stack to latest qiskit 2.5 line
3c20cff8 2026-08-17T20:44:30Z Andy Gallo          Repin to qiskit 2.3 + Q8020-CFD fork; go uv-native, drop requirements*.txt
fbe6ef10 2026-08-17T20:44:14Z Andy Gallo          Reconcile solver code with archive/qiskit-hhl-2 (verbosity, checkpointing)
60d973c5 2026-08-17T18:32:12Z Andy Gallo          Deliver feature/qiskit-hhl to main
a5317f2b 2025-11-12T01:00:44Z Mohammad Alhawwary  Adding the detailed guide
eadc43d3 2025-11-12T00:55:02Z Mohammad Alhawwary  Adding steady mode option to write files with only iter instead of step when inner iters = 1
157869b3 2025-11-12T00:01:18Z Mohammad Alhawwary  Allowing the solver to work as a linear solver using 1 subiteration only
a7d5bc8d 2025-11-12T00:00:41Z Mohammad Alhawwary  saving circuit, generation, transpilation, and run time to qc_metadata
b02eda19 2025-11-11T22:49:54Z Mohammad Alhawwary  improved data writing and added information about each step/iter dq, fidelity and l2 errors
7bb8f288 2025-11-11T21:38:53Z Mohammad Alhawwary  modified README and created a detailed one in docs
fd6ba8a5 2025-11-11T20:16:18Z Mohammad Alhawwary  modify read me
5dc43eb2 2025-11-11T15:52:12Z Mohammad Alhawwary  Updates to Read ME
b7bb0d4c 2025-11-11T14:17:28Z Mohammad Alhawwary  Add parallel shot studies with SLURM integration. Added also some documentation for Frontier workflow.
81fdb6d9 2025-11-08T21:44:32Z Mohammad Alhawwary  minor modification to the read me
```

(Source timestamps were `-06:00` for Mohammad's and `-04:00` for Andy's commits;
converted to UTC above.)

### A.3 Upstream relation (parent `mhawwary/fvm_euler_1d_solver`)

The parent is Mohammad Alhawwary's original (GE Aerospace Research, "LEAD
Engineer, CFD Methods" per `README.md`). It is private; default branch `main`;
last push 2026-03-14T02:51:40Z. **We modify our fork, `Q8020-CFD/fvm_euler_1d_solver`;
the parent is read-only reference.**

Parent branches (`gh api repos/mhawwary/fvm_euler_1d_solver/branches`):
`archive/feature/agmods 9f243fa3`, `archive/feature/tpile ee18798c`,
`archive/feature/wf-pkg ccf8fbfe`, `archive/qiskit-hhl-2 9e76e398`,
`archive-master 11b181c6`, `backup-old-main 913c793d`,
`feature/qiskit-hhl a5317f2b`, `feature/qiskit-hhl-qrisp f72751ed`,
`main 4314eba4`. Eight of these exist in our fork under the same names and shas;
the parent additionally has `feature/qiskit-hhl-qrisp`; we additionally have
`bloqade-test` and `archive/solverfw-v2-port`.

Parent `main`, last 10 commits:

```
4314eba4 2025-11-08T21:43:28Z Scaling updates for counts solution sign, more changes for writing data code, visualization, and test automation  (#2)
1de1b377 2025-11-04T02:23:13Z Enable quantum simulators and fake backends (#1)
03b921b7 2025-10-29T23:31:40Z edit readme to reflect requirements changes
623adcba 2025-10-29T23:27:52Z Fixing issues with requirements for quantum circuit generation
f4e72b57 2025-10-23T02:11:08Z further editing of read me file
462d62c8 2025-10-23T02:04:32Z Adding a more comprehensive Read me file
67a788e7 2025-10-23T02:04:08Z Adding minimal requirements files
bd4ab045 2025-10-20T18:09:19Z Create README.md
702e4f1f 2025-10-20T17:27:30Z small modification to avoid the requirement of qiskit if not running quantum
0c1da074 2025-10-15T01:22:58Z Implemented non-dimensionalization for the solver. Also, successfully used qiskit hhl to generate the circuit
```

Containment (checked on existing local objects only, no fetch):

- Parent `main` tip `4314eba4`: `git cat-file -t` -> `commit` (present
  locally); `git branch -a --contains 4314eba4` lists `main`, `origin/main`,
  `archive/solverfw-v2-port`, `origin/bloqade-test`. **Our `main` contains the
  parent's `main` tip.** Nothing on the parent's `main` is missing from ours.
- Parent `feature/qiskit-hhl` tip `a5317f2b` is an ancestor of our `main`
  (merged by `60d973c5` "Deliver feature/qiskit-hhl to main").
- `origin/archive/qiskit-hhl-2` (`9e76e398`) is NOT an ancestor of our `main`;
  its content was ported by `fbe6ef10` "Reconcile solver code with
  archive/qiskit-hhl-2".
- Parent `feature/qiskit-hhl-qrisp` tip `f72751ed`
  (2026-03-14T02:51:38Z, "capturing - DO NOT PULL") exists locally as an object
  (`git cat-file -t` -> `commit`) but is on **no** local or remote-tracking
  branch here. It is the parent's only work newer than what we carry, and its
  own subject says not to pull it.

### A.4 File inventory (`git ls-files`, 48 tracked files)

Flat module layout: solver modules live at the repo root (declared in
`[tool.setuptools] py-modules`). Files touched by the SQLS integration commit
`ef7f0a8b` are marked **[SQLS]** (`git show --stat ef7f0a8b`: 4 files,
+346 / -12 lines: `nozzle_1d_solver.py` +51/-, `pyproject.toml` +11,
`quantum_tools.py` +181, `time_solvers.py` +115).

| Tracked file | Lines | Role |
|---|---|---|
| `.gitignore` | | Ignores `__pycache__/`, `*.egg-info/`, `.venv/`, `*.csv`, `*.png`, `*.pdf`, `*.pkl`, `*.qpy`, logs, IDE/OS files. (The tracked `post_process/ref_sol/*.csv` predate / override the `*.csv` rule.) |
| `.python-version` | | `3.12` |
| `README.md` | | Top-level user doc: 1D converging-diverging nozzle, Mach 1.5 -> 2.5, MUSCL + Rusanov, RK1-3 / BDF1-2, LU / GMRES / HHL linear solvers. Author Mohammad Alhawwary, v0.1 (Nov 2025). Does not yet mention SQLS. |
| `case.py` | 104 | `SimCase` (gas constants, inlet state, reference scaling / nondimensionalisation) and `Nozzle1D` (area law `S(x)`, `dS/dx`). |
| `checkpoint_tools.py` | 80 | Pickle checkpoint save / load / resume of outer-iteration state for BDF1 + HHL runs. |
| `docs/DETAILED_GUIDE.md` | | Mohammad's detailed solver guide. |
| `docs/FRONTIER_CONDA_SETUP.md` | | Conda + SBCAST environment recipe for OLCF Frontier. |
| `docs/QUICKSTART_PARALLEL.md` | | Parallel shot-study quick start on Frontier. |
| `helper_tools.py` | 132 | `write_csv`, `plot_solution_and_residual`. |
| `math_tools.py` | 273 | Global verbosity; `convert_to_pow2` (pad system to 2^n), `convert_system_to_herm` (Hermitian doubling for HHL), spectral-radius scaling, `extract_true_sol_from_herm`, matrix property report / scientific printing. |
| `mesh.py` | 20 | `Mesh`: uniform 1D cells, `dx`, nondim flag. |
| `nozzle_1d_solver.py` **[SQLS]** | 410 | CLI driver (argparse). `-linsolver {LU,GMRES,HHL,SQLS}` (line 61-62); SQLS flags `-sqls_method`, `-sqls_k` (default 128), `-sqls_state_prep`, `-sqls_repeats` (lines 106-121; help text: "full_svd is exact (default)"); builds mesh / case / space / time solvers, runs, writes CSV and plots, checkpoint / resume. SQLS branch at line 201. |
| `post_process/plot_comparison.py` | 262 | CSV comparison plotter for final-solution files. |
| `post_process/ref_sol/nelem{3,4,5,10,200}/*.csv` | 25 files | LU reference solutions per grid size: `final_results_*`, `residual_*`, `results_*_nsteps{0,1,2}.csv`. |
| `pyproject.toml` **[SQLS]** | | Packaging + dependency source of truth (quoted in A.5); added the `sqls` optional extra. |
| `quantum_tools.py` **[SQLS]** | 895 | `QuantumHHL` (line 155: circuit build via `linear_solvers.HHL`, ideal / fake / real IBM backends, shots, fidelity, `qpy` save/load, timing metadata) and `QuantumSQLS` (line 720: "SVD-based Quantum Linear Solver (SQLS) drop-in for QuantumHHL"; `backend_type='ideal'` only; imports `sqls.runtime.quantum.quantum_solve` at line 816). Helpers `get_ancillaqubit`, `fidelity`, `compate_state_exact_vs_counts_vecs`. |
| `scripts/run_shots.py` | 149 | Serial HHL shot-count parametric study. |
| `scripts/run_shots_parallel.py` | 337 | Same study fanned out with SLURM `srun` on Frontier. |
| `scripts/submit_parallel_shots.sbatch` | | SLURM batch wrapper for the above. |
| `space_solvers.py` | 317 | `SpaceSolver`: MUSCL reconstruction, Rusanov flux, ghost cells / BCs, nozzle source term, prim <-> cons, local time step, plotting. |
| `time_solvers.py` **[SQLS]** | 691 | `TimeSolver` -> `ExplicitRK` (`RK1/2/3`), `ImplicitTimeSolver` -> `BDFTimeSolver`; `LinearSystemSolver` (line 232) with `scheme_type` LU / GMRES / HHL / SQLS, FD Jacobian, `hhl_solve` (492), `sqls_solve` (605), metrics writer. Constructs `QuantumSQLS` at lines 277-291. |
| `utils/list_fake_backends.py` | 151 | Enumerates `qiskit_ibm_runtime` fake backends and properties. |
| `uv.lock` | | uv lockfile (181899 bytes, 2026-08-17). |

`src/` on `main`: `git ls-files src` returns nothing (untracked). On disk
`src/` holds only `__pycache__/` (mtime 2026-08-17 14:26 local), ignored via
`.gitignore:8:__pycache__/` (`git check-ignore -v`), so `git status --ignored`
shows `!! src/`. It is a stale leftover from an earlier `src/`-layout branch
(`archive/solverfw-v2-port`), safe to delete. Also ignored on disk:
`fvm_euler_1d_solver.egg-info/` (editable-install artifact), `output/` (29
entries, last written 2026-09-01), `__pycache__/`. No `LICENSE` file exists.

### A.5 Environment

`pyproject.toml`, dependency sections verbatim:

```toml
[project]
name = "fvm-euler-1d-solver"
version = "0.1.0"
requires-python = ">=3.12,<3.14"

dependencies = [
    "numpy>=1.20.0",
    "scipy>=1.7.0",
    "matplotlib>=3.3.0",
    "PyYAML",
    "python-dotenv",
    "quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers",
    "qiskit==2.5.2",
    "qiskit-aer==0.17.2",
    "qiskit-ibm-runtime==0.49.0",
    "qiskit-qasm3-import>=0.6.0",
]

[project.optional-dependencies]
sqls = ["sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git"]
```

The pyproject comment above the extra says, verbatim: "SQLS (SVD-based Quantum
Linear Solver) is an ORNL repo (access-gated), so it is NOT a base dependency ...
Install with `pip install -e ".[sqls]"` if you have access to the git remote, or
point the extra at a local checkout: `pip install -e ../sqls --no-deps` ... SQLS
pins qiskit==2.1.2 in its own pyproject, but only touches stable core APIs
(QuantumCircuit / Initialize / UnitaryGate / AerSimulator / SamplerV2), so
--no-deps against this repo's qiskit 2.5.2 stack is intended and verified."

- `.python-version`: `3.12`
- `uv.lock`: present (181899 bytes, mtime 2026-08-17 16:54 local). Locked:
  `qiskit 2.5.2`, `qiskit-aer 0.17.2`, `qiskit-ibm-runtime 0.49.0`,
  `qiskit-qasm3-import 0.6.0`, `numpy 2.5.2`, `scipy 1.18.0`,
  `quantum-linear-solvers 0.1.0` from
  `git+https://github.com/Q8020-CFD/quantum_linear_solvers#66eadf0b4edcff100b20edf70a99e79cc69c5923`.
  `grep -n sqls uv.lock` -> **no matches**: the `sqls` extra is not locked.
- `.venv/bin/python --version` -> `Python 3.12.10` (uv-managed CPython at
  `/Users/agallojr/.local/share/uv/python/cpython-3.12.10-macos-aarch64-none`;
  `pyvenv.cfg`: `uv = 0.7.2`, `prompt = fvm_euler_1d_solver`). `python -m pip`
  is absent (uv venv), so versions come from `site-packages` dist-info names:

```
numpy-2.5.2.dist-info
qiskit-2.5.2.dist-info
qiskit_aer-0.17.2.dist-info
qiskit_ibm_runtime-0.49.0.dist-info
qiskit_qasm3_import-0.6.0.dist-info
quantum_linear_solvers-0.1.0.dist-info
scipy-1.18.0.dist-info
sqls-0.1.0.dist-info
fvm_euler_1d_solver-0.1.0.dist-info   (editable, setuptools finder)
```

- How sqls is installed: `cat .venv/lib/python3.12/site-packages/__editable__.sqls-0.1.0.pth`
  -> `/Users/agallojr/proj/src/q8020/sqls/src` (a plain path-entry editable
  install). `sqls-0.1.0.dist-info/direct_url.json` ->
  `{"url":"file:///Users/agallojr/proj/src/q8020/sqls","dir_info":{"editable":true}}`.
  So the venv imports `sqls` straight from the sibling clone; nothing from
  code.ornl.gov is needed at install or import time. Note the venv runs
  qiskit 2.5.2 / aer 0.17.2 / numpy 2.5.2 / scipy 1.18.0 against sqls's own
  pins of qiskit 2.1.2 / aer 0.17.1 / numpy 2.3.3 / scipy 1.16.2 (B.3), i.e. the
  `--no-deps` install the pyproject comment describes.

### A.6 Linear-solver library: quantum_linear_solvers

- `ls .venv/lib/python3.12/site-packages | grep -i quantum_linear` ->
  `quantum_linear_solvers-0.1.0.dist-info`; its `direct_url.json` records
  `https://github.com/Q8020-CFD/quantum_linear_solvers` at commit
  `66eadf0b4edcff100b20edf70a99e79cc69c5923` (matches uv.lock). The import name
  is `linear_solvers` (`from linear_solvers import HHL` in `quantum_tools.py`).
- `gh api repos/Q8020-CFD/quantum_linear_solvers/commits?per_page=3`:

```
66eadf0b 2026-03-07T20:52:47Z re-add the init constructor
7a9b48f2 2026-03-07T20:47:59Z port to qiskit 2.3
a94cf634 2025-04-21T20:27:33Z Minor updates to files.
```

  Only branch is `main` at `66eadf0b`; repo is public, a fork of
  `jw676/quantum_linear_solvers`, last pushed 2026-03-07T20:52:49Z.
  **`66eadf0b` is still the tip**; the lock is current.

## B. sqls

### B.1 Repo identity

- Path: `/Users/agallojr/proj/src/q8020/sqls`
- `git remote -v`: `origin  https://code.ornl.gov/olcf-qcfd/sqls.git (fetch)` /
  `(push)` (no embedded credential).
- Branch: `main`, tracking `origin/main`. Branches: local `main`
  `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d`; `origin/main` same;
  `origin/dev-bluffbody` `6308afedbec09b616db650b569c69c6c9e08def5`
  ("Integrated all bluff body to single code; added airfoil"). No tags.
- HEAD: `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d`
  "Merge branch 'to_be_released' into 'main'", 2026-06-30T14:40:52Z (Chao Lu).
- `git status --short`: empty (clean).
- Clone date: directory mtime 2026-07-26T10:03:43-0400 = 2026-07-26T14:03:43Z,
  and the reflog's only entry is
  `9a4346a HEAD@{2026-07-26T10:03:43-04:00}: clone: from https://code.ornl.gov/olcf-qcfd/sqls.git`.
  `.git/ORIG_HEAD` mtime 2026-08-17T01:19:05Z (a pull/merge that day left HEAD
  unchanged). `.git/FETCH_HEAD` mtime 2026-10-15T00:52:34Z and **0 bytes** — a
  fetch/pull started then and did not complete (see Part C).

`git log --format='%h %ad %an %s' --date=iso-strict -15` (UTC-normalised):

```
9a4346a 2026-06-30T14:40:52Z Lu, Chao  Merge branch 'to_be_released' into 'main'
ba0051b 2026-06-30T14:35:36Z Lu, Chao  Edit README.md
02eaf20 2026-06-16T15:12:07Z Lu, Chao  Edit README.md
0642ec0 2026-06-16T13:20:10Z luc1      Change everything to SQLS
ab6cce0 2026-06-16T13:19:32Z luc1      renamed: src/qlsa/... -> src/sqls/... (package rename qlsa -> sqls; qpde.py -> sqls.py)
c0d33c0 2026-06-06T16:55:31Z luc1      name change to SQLS
6d55943 2026-06-06T02:34:16Z luc1      updated readme file
5b0a047 2026-06-06T02:34:07Z luc1      updated readme
bc3a1e9 2026-06-06T02:31:01Z luc1      final version 2
6e39c93 2026-06-06T02:30:33Z luc1      final version
d6b7739 2026-05-28T18:12:05Z luc1      init commit
f318e9c 2026-03-12T16:43:55Z Lu, Chao  Merge branch 'dev-bluffbody' into 'main'
6308afe 2026-03-09T18:11:49Z Murali    Integrated all bluff body to single code; added airfoil
754155f 2026-03-09T18:10:12Z Murali    Added oak leaf bluff body; updated fig names, requirements
65366e9 2026-01-29T20:29:59Z luc1      Made some changes about GPU acceleration of SVD decomposition, ibm quantum computer job submission, and data plotting
```

### B.2 File inventory (`git ls-files`, 18 tracked files)

| Tracked file | Lines | Role (from README "Layout" and module docstrings) |
|---|---|---|
| `.gitignore` | | Python caches, generated `results_*.json` / `scaling_results.csv` / figures / `ibm_submit.json`, IDE / OS files. |
| `README.md` | | Methods table (`full_svd`, `truncated_qr`, `truncated_mps`), layout, install, `sim` / `submit` / `retrieve` usage, GPU table, API, fidelity decomposition, gotchas, constraints when extending, contributors (Chao Lu lead; Kalyan Gottiparthi; Muralikrishnan Gopalakrishnan Meena), citation: Gottiparthi, Lu, Gopalakrishnan Meena, Chaudhary, El-Araby, "Quantum Solver Using Singular Value Decomposition for Computational Fluid Dynamics", AIAA SciTech 2026 Forum, paper 1934. |
| `pyproject.toml` | | Package metadata and pins (quoted in B.3). |
| `requirements.txt` | | Pinned deps + optional GPU notes (quoted in B.3). |
| `examples/potential_flow.py` | 724 | The single driver: `sim` (Aer statevector / shots), `submit`, `retrieve` (IBM hardware). Prepends `../src` to `sys.path` so it runs in-tree. |
| `src/sqls/__init__.py` | 43 | Exports `SQLS`; package docstring documents the three methods and two state-prep loaders. |
| `src/sqls/sqls.py` | 433 | The entry point `SQLS(...)` -> `QuantumCircuit`; `_VALID_METHODS`, `_prepare_state`, `fidelity`. |
| `src/sqls/gpu.py` | 163 | torch / Aer GPU detection, `resolve(gpu)`, `GPUConfig`, `make_aer_simulator`. |
| `src/sqls/core/__init__.py` | 4 | Internal building blocks, not a user entry point. |
| `src/sqls/core/truncated_svd.py` | 258 | `smallest_k_svd` (sparse LU + shift-invert Lanczos on CPU, torch eigh on GPU), `complete_to_unitary` (sign-fixed QR completion). |
| `src/sqls/core/mps_state_prep.py` | 445 | TT-SVD (MPS) state preparation replacing Mottonen `Initialize`. |
| `src/sqls/core/mps_isometry.py` | 759 | MPS encoding of an N x k isometry V_k as a circuit (data + input + bond ancillas). |
| `src/sqls/pde/__init__.py` | 3 | Problem-setup helpers. |
| `src/sqls/pde/cfd.py` | 171 | 2D Laplace (potential flow past an obstacle) 5-point-stencil builder + classical reference solves. |
| `src/sqls/pde/obstacle_shapes.py` | 317 | Parametric obstacle masks (cylinder, square, NACA airfoils, ...). |
| `src/sqls/pde/plotting.py` | 96 | Contour / streamline / error plots. |
| `src/sqls/runtime/__init__.py` | 1 | Execution wrappers. |
| `src/sqls/runtime/quantum.py` | 237 | `quantum_solve` (build + Aer run + ancilla projection / marginalisation), `count_cx_depth`, `_run_statevector`, `_run_shots`. |

No `LICENSE` file; `grep -ri 'license|copyright|UT-Battelle|SPDX'` over the
tree finds nothing; `pyproject.toml` has no `license` field. The library note
`note-20260924-0014` §6.1 recorded the same on 2026-09-23 (no LICENSE in any of
the five q8020 repos, including this one and `fvm_euler_1d_solver`). Default
copyright therefore applies: all rights reserved by the authors / ORNL.

### B.3 Pins

`pyproject.toml`, full:

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "sqls"
version = "0.1.0"
description = "Quantum linear-system solver (SQLS) for elliptic PDEs"
readme = "README.md"
requires-python = ">=3.10"
# Core deps only -- pinned to the versions in requirements.txt.  The example
# driver additionally needs the [examples] extras below (the core package
# imports them lazily, so `from sqls import SQLS` works without them).
dependencies = [
    "qiskit==2.1.2",
    "qiskit-aer==0.17.1",
    "numpy==2.3.3",
    "scipy==1.16.2",
]

[project.optional-dependencies]
examples = [
    "matplotlib",
    "qiskit-ibm-runtime",
]

[tool.setuptools.packages.find]
where = ["src"]
```

`requirements.txt`, full:

```
qiskit==2.1.2
qiskit-aer==0.17.1
qiskit-ibm-runtime
numpy==2.3.3
scipy==1.16.2
matplotlib

# Optional GPU acceleration (any one of these enables --gpu):
#   torch              # PyTorch with CUDA or ROCm; powers SVD/QR/MPS on the GPU
#   qiskit-aer-gpu     # AerSimulator(device='GPU'); CUDA-only
#
# If torch is missing, --gpu silently falls back to CPU for the classical
# decomposition.  If qiskit-aer-gpu is missing, AerSimulator stays on CPU
# but the classical paths still benefit from torch GPU when available.
```

The qiskit pin is `qiskit==2.1.2` as expected. These hard `==` pins conflict
with the fvm pins (`qiskit==2.5.2`, `qiskit-aer==0.17.2`) — relevant in Part C.

### B.4 Public API we call

`SQLS` is a **function**, not a class (`def SQLS(...)` at
`/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py:105-107`):

```python
def SQLS(matrix, b, gpu=None, k=128, method="truncated_mps",
         out=None, state_prep="initialize", mps_chi=None, iso_chi=None,
         mps_chi_max=None, GPU=None):
    """Build the SQLS circuit from an SVD of ``matrix``.
    matrix : (N, N) scipy.sparse matrix OR dense ndarray, N a power of 2.
             Truncated methods strongly prefer the sparse form; the full-SVD
             path requires a dense N x N matrix.
    b      : (N,) array.  Must be nonzero.
    gpu    : enable GPU paths (torch / Aer); None means CPU.  ``GPU`` is a
             deprecated alias (DeprecationWarning).
    k      : truncation rank, power of 2 with 2 <= k < N; ignored by full_svd.
    method : one of "truncated_mps", "truncated_qr", "full_svd".
    state_prep : "initialize" or "mps" (full_svd / truncated_qr only).
    mps_chi, iso_chi, mps_chi_max : MPS bond-dimension knobs.
    out    : optional dict, populated with method-specific bookkeeping
             (final_b, U_k, s_k, V_k, n_data_qubits, m_ancilla, t_* timings, gpu).
    Returns
    -------
    QuantumCircuit.  The final statevector on the data register is
    proportional to V_k . diag(1/s_k) . U_k^H . b (or A^{-1} b for full_svd).
    """
```

`_VALID_METHODS = ("full_svd", "truncated_qr", "truncated_mps")` (line 56);
`_VALID_STATE_PREP` holds `"initialize"` and `"mps"`. Front-door `ValueError`s:
N not a power of 2; k not a power of 2 in `[2, N)` for the truncated methods;
`b == 0`; `b` orthogonal to `col(U_k)`. Small discrepancy: the package
docstring in `src/sqls/__init__.py` advertises a keyword-only signature
`SQLS(A, b, *, k=128, ...)`, but the actual `def` takes all parameters
positionally (and `gpu` is third).

`quantum_solve` at
`/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py:36-43`:

```python
def quantum_solve(A_csr, b, num_q, simulator, psi_norm,
                  mode="statevector", k=128,
                  method="truncated_mps",
                  state_prep="initialize", mps_chi=None, iso_chi=None,
                  mps_chi_max=None,
                  repeats=10, shots=int(1e6),
                  sqls_out=None, timings=None, count_cx=False,
                  gpu=False, restore_sign=True):
    """Build the SQLS circuit for (A_csr, b), run it, and reconstruct a
    length 2**num_q amplitude vector on the data register.
    mode : "statevector" (AerSimulator.save_statevector path; exact)
           or "shots" (SamplerV2 with repeats x shots measurements).
    psi_norm : legacy fallback for the output scale; the reconstruction is
           rescaled to ||final_b|| (known exactly from the classical
           decomposition), so no classical reference solve is needed.
    restore_sign : shots mode only; signs inferred classically from final_b.
    count_cx : transpile to {u3, cx} only to log cx_count / circuit_depth
           (reported as -1 when skipped).
    gpu : route classical decomposition and (if qiskit-aer-gpu) Aer to GPU.
    """
```

Return value: a NumPy vector of length `2**num_q` (data-register amplitudes,
rescaled to `||final_b||`; in `"shots"` mode sign-restored when
`restore_sign=True` and `final_b` is available). Raises `ValueError` for any
other `mode`. Side effects: fills the caller's `sqls_out` and `timings` dicts
(`aer_device`, `cx_count`, `circuit_depth`, run timings) and prints timing
lines. Internally it calls
`SQLS(A_csr, b, k=k, method=method, out=sqls_out, state_prep=..., mps_chi=...,
iso_chi=..., mps_chi_max=..., gpu=gpu)`.

The fvm side (`QuantumSQLS.solve` in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py`, import at
line 816) calls `quantum_solve`; the wiring details are out of scope here.

### B.5 ORNL GitLab group `olcf-qcfd`

The one budgeted live call
`curl -s -m 20 'https://code.ornl.gov/api/v4/groups/olcf-qcfd/projects?per_page=50'`
at 2026-10-15T01:38:16Z returned **no response within 20 s** (HTTP code 000,
empty body) — see Part C. The project list therefore comes from
`lore-20261013-0001` (listing taken 2026-10-13): `olcf-qcfd/DVQLS` (distributed
VQLS on CUDA-Q, created 2026-06-01), `olcf-qcfd/sqls`, `olcf-qcfd/qlsa` (HHL on
Hele-Shaw, unmaintained; successor on GitHub `olcf/hands-on-with-frontier`),
`olcf-qcfd/lugo_benchmarking`, `olcf-qcfd/gitlab-profile`. All were public.

## C. The broken sqls git link

### C.1 Observations (UTC)

Prior context:

- 2026-10-13 ~01:45Z to 01:55Z: after ~10 requests in 3 min, code.ornl.gov
  answered HTTP 403 "Access from your IP address is currently restricted due to
  security controls applied to your network range" to every further request,
  including `git clone` (`lore-20261013-0001`). About 24 h later the same
  endpoints answered 200 in < 0.5 s. The lore's 2026-10-14 follow-up also
  records one operator `git pull` on the sqls clone failing with
  "HTTP 504 ... expected flush after ref listing".
- 2026-10-14 ~01:25Z (operator report in the task brief):
  `GIT_TERMINAL_PROMPT=0 git ls-remote https://code.ornl.gov/olcf-qcfd/sqls.git`
  -> "The requested URL returned error: 504", while
  `olcf-qcfd/lugo_benchmarking.git` and `olcf-qcfd/qlsa.git` answered normally
  and the group API still listed `olcf-qcfd/sqls`.
- 2026-10-15T00:52:34Z: `/Users/agallojr/proj/src/q8020/sqls/.git/FETCH_HEAD`
  was rewritten and left at 0 bytes — a fetch/pull attempt that did not finish.

This session (request budget: 1 API call, 1 project-page request, 2
`ls-remote`; all used, nothing more sent to the GitLab application):

| UTC | Probe | Result |
|---|---|---|
| 2026-10-15T01:37:53Z | `curl -s -m 20 -o /dev/null -w '%{http_code}' https://code.ornl.gov/olcf-qcfd/sqls` (project page) | `000`, `time_total` 20.004 s — no HTTP response before curl's own 20 s limit |
| 2026-10-15T01:38:16Z | `curl -s -m 20 'https://code.ornl.gov/api/v4/groups/olcf-qcfd/projects?per_page=50'` | `000`, empty body after 20 s |
| 2026-10-15T01:39:47Z | DNS `dig +short code.ornl.gov` | `40.121.118.25` (Microsoft Azure range) |
| 2026-10-15T01:39:47Z | `nc -z -G 10 code.ornl.gov 443` (TCP only) | connected in < 1 s |
| 2026-10-15T01:39:47Z | Controls: `https://pypi.org/simple/`, `https://www.ornl.gov/`, `https://github.com/` | 200 in 3.32 s, 200 in 0.70 s, 200 in 5.98 s |
| 2026-10-15T01:41:06Z | `GIT_TERMINAL_PROMPT=0 GIT_TRACE_CURL=1 git ls-remote https://code.ornl.gov/olcf-qcfd/sqls.git` (1 of 2) | TLS 1.3 handshake OK; HTTP/2 `GET /olcf-qcfd/sqls.git/info/refs?service=git-upload-pack` sent 01:41:06.699; **`HTTP/2 504`** received 01:41:26.748 (20.05 s later) with `server: Microsoft-Azure-Application-Gateway/v2`, `content-type: text/html`, `content-length: 193`; git exit 128, "fatal: unable to access 'https://code.ornl.gov/olcf-qcfd/sqls.git/': The requested URL returned error: 504" |
| 2026-10-15T01:41:31Z | `GIT_TERMINAL_PROMPT=0 git ls-remote https://code.ornl.gov/olcf-qcfd/lugo_benchmarking.git` (2 of 2, control) | OK in 1 s: `3123c40ea85005b8a2e0f858f30877eb2b3856d7  HEAD` and `refs/heads/main` |

Details from the curl trace of the failing call (no credential was sent; git
reported "Couldn't find host code.ornl.gov in the .netrc file"): the server
certificate is **Zscaler-issued** — subject `CN=code.ornl.gov, O=Zscaler Inc.`,
issuer `Zscaler Intermediate Root CA (zscalergov.net)`, valid
2026-10-13T14:06:42Z to 2026-10-24T13:17:11Z — so this laptop's HTTPS to ORNL is
intercepted by the GE Aerospace Zscaler client (the `utun*` interfaces) even on
the home LAN (192.168.1.0/24). The 504 body, however, carries the
`Microsoft-Azure-Application-Gateway/v2` server header, i.e. it was generated
by ORNL's own front door, not by Zscaler.

Credential supply (no secrets printed):

- `git config --show-origin --get-all credential.helper` ->
  `file:/Library/Developer/CommandLineTools/usr/share/git-core/gitconfig  osxkeychain`
  (the Xcode CLT default). `--system` and `--global` scopes: unset. No
  `url.*.insteadOf` rewrites, no `~/.git-credentials`, no `.netrc` entry.
- `security find-internet-password -s code.ornl.gov` -> "The specified item
  could not be found in the keychain"; a metadata-only `dump-keychain | grep -i
  ornl` finds nothing either (for comparison the keychain does hold a
  `github.com` entry for `agallojr`).
- Conclusion: **there is no stored credential for code.ornl.gov on this
  machine.** The 2026-07-26 clone, the 2026-10-14 probes and today's calls were
  all anonymous requests to a public project. The "same stored credential"
  premise in the task brief does not hold; it also means credentials are not a
  variable in the failure.

### C.2 Root-cause hypothesis

The 504 is a **gateway timeout emitted by ORNL's Azure Application Gateway v2
after a 20 s backend wait**: the GitLab backend does not return the `sqls`
repository's ref advertisement (`info/refs?service=git-upload-pack`) within the
gateway's request timeout. Evidence: the response arrives 20.05 s after the
request (a fixed timer, not a network stall), it is a 504 (upstream did not
respond) rather than 502/503, and the control project `lugo_benchmarking` on
the same host, same path, same anonymous client answers in 1 s. DNS, TCP, TLS
(through Zscaler), and the client are therefore fine; the fault is server-side
and specific to the `sqls` repository (most plausibly its Gitaly storage /
repository process hanging or extremely slow, e.g. a repository needing
housekeeping or a stuck ref-advertisement). The project page and the
group-projects API also stalled past 20 s today; both need Gitaly calls against
every project in the group (README / tree render; `default_branch` per project),
so a hung `sqls` repository explains those too, and explains why the group
listing worked on 2026-10-14 when `sqls` momentarily answered.

It is **intermittent and recurring**: 504 at 2026-10-14 ~01:25Z, a 200 later on
2026-10-14 (lore follow-up), a failed pull at 2026-10-15T00:52Z, and 504 again
at 2026-10-15T01:41Z, i.e. over more than 24 h. It is **not** the 403
IP-range burst block of `lore-20261013-0001` (that is host-wide, immediate, and
returns an HTML 403), and **not** an auth problem (public repo; no credential
stored or needed; 504 is not 401/403). Nothing on our side fixes it; the owners
(Chao Lu, ORNL; or ORNL GitLab admins) would need to look at the repository on
the server. Retrying later may succeed, as it did once on 2026-10-14.

### C.3 Consequence for the fvm `sqls` extra

`pyproject.toml` declares
`sqls = ["sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git"]` — an unpinned
(no `@<sha>`), unlocked (`grep -n sqls uv.lock` returns nothing) direct git
reference. `uv sync --extra sqls` or `pip install .[sqls]` would:

1. Need to clone from code.ornl.gov at install time, which **fails right now
   with the 504** and would fail during any 403 burst block; on a node whose IP
   range ORNL restricts, or if the project ever stops being public, it would
   additionally need a non-interactive credential, and none is stored anywhere
   (C.1).
2. Be expected to **fail dependency resolution even with a healthy remote**,
   because sqls hard-pins `qiskit==2.1.2`, `qiskit-aer==0.17.1`,
   `numpy==2.3.3`, `scipy==1.16.2` while fvm pins `qiskit==2.5.2`,
   `qiskit-aer==0.17.2` (and locks numpy 2.5.2 / scipy 1.18.0). The resolver has
   no `--no-deps` escape in `uv sync` / `pip install .[extra]`; the only reason
   the current venv works is that sqls was installed with `--no-deps` from the
   sibling checkout, exactly as the pyproject comment says.
3. Produce a non-reproducible result on success (floating `main`), unlike the
   rest of the lock.

The install that actually exists today — an editable `.pth` pointing at
`/Users/agallojr/proj/src/q8020/sqls/src` — **touches no network** at install or
import time and is unaffected by the 504. Only a `git pull` / `git fetch` of the
sqls clone, or a fresh clone on another node, hits the broken link.

### C.4 Options (not implemented)

| Option | Pros | Cons |
|---|---|---|
| 1. Keep the sibling-checkout editable install (`pip install -e ../sqls --no-deps`) as the documented path; record the expected sqls commit (`9a4346a7`) in the fvm README / pyproject comment | Works today, offline, needs no permission; already how every working venv is built | Each node needs its own clone from code.ornl.gov once; version drift is only documented, not enforced; the `sqls` extra stays a trap |
| 2. Mirror sqls into the private GitHub org `Q8020-CFD` (e.g. `Q8020-CFD/sqls`) and point the extra there | Decouples from code.ornl.gov availability, IP blocks and 504s; GitHub auth already exists on every node; can be pinned and locked | sqls has **no LICENSE** (all rights reserved by default), so a mirror is redistribution that needs explicit ORNL / Chao Lu permission; a private mirror still has to be kept in sync by hand |
| 3. Pin the extra by commit sha: `sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git@9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` | Reproducible | Still hits the flaky host; still fails on the qiskit pin conflict unless sqls relaxes its pins; adds nothing on a node that cannot reach ORNL |
| 4. Vendor `src/sqls/` into the fvm repo | No external dependency at all | Same license problem as 2, plus it forks ORNL's code and hides provenance; the two repos' pins diverge further |

### C.5 Recommendation

Keep option 1 as the documented and only supported path for the AIAA 4Q26 work,
because it is the one configuration that works today, it needs no one's
permission, and it isolates the solver work from an ORNL server fault we cannot
fix. Tighten it by writing the expected sqls commit (`9a4346a7`, 2026-06-30)
and the `--no-deps` rationale into the fvm README and the pyproject comment, and
either remove the `sqls` extra or mark it "manual, see README" so nobody runs
`uv sync --extra sqls` expecting it to work. In parallel, ask Chao Lu / ORNL for
two things: a LICENSE on `olcf-qcfd/sqls` and permission to hold a private mirror
in `Q8020-CFD`; once granted, switch the extra to the mirror pinned by sha
(options 2 + 3 combined) and lock it, which also makes the fvm environment
reproducible on mesh nodes that have never touched code.ornl.gov. Vendoring
(option 4) is the worst choice for provenance and licensing and should be
avoided.

## Sources

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` — `git remote -v`,
  `git branch -a -v`, `git log`, `git ls-files`, `git check-ignore`,
  `git show --stat ef7f0a8b`, `pyproject.toml`, `.python-version`, `uv.lock`,
  `.venv/pyvenv.cfg`, `.venv/lib/python3.12/site-packages/` (dist-info names,
  `__editable__.sqls-0.1.0.pth`, `direct_url.json` files), `README.md`,
  module sources (`quantum_tools.py`, `time_solvers.py`, `nozzle_1d_solver.py`).
- `/Users/agallojr/proj/src/q8020/sqls` — `git remote -v`, `git log`,
  `git reflog`, `git ls-files`, `.git/config`, `.git/FETCH_HEAD` mtime,
  `README.md`, `pyproject.toml`, `requirements.txt`, `src/sqls/sqls.py`,
  `src/sqls/runtime/quantum.py`, `src/sqls/__init__.py`.
- GitHub via `gh`: `gh repo view Q8020-CFD/fvm_euler_1d_solver`;
  `gh api repos/mhawwary/fvm_euler_1d_solver/{branches,commits}`;
  `gh api repos/Q8020-CFD/quantum_linear_solvers/{commits,branches}`.
- code.ornl.gov probes listed in C.1 (one API call, one project-page request,
  two `git ls-remote`), plus DNS / TCP / TLS-layer checks that did not touch the
  GitLab application.
- Library records (cited): `lore-20261013-0001`
  (`/Users/agallojr/proj/src/research-notes/bus/memory/lore/lore-20261013-0001-code-ornl-gov-blocks-ip-after-burst-of-fetches.md`,
  the 403 burst block, its 2026-10-14 follow-up and the group project list);
  `note-20260924-0014` §6.1
  (`/Users/agallojr/proj/src/research-notes/bus/memory/notes/note-20260924-0014-qcfd-edu-matrix-consortium-plan-of-record.md`,
  license audit of the five q8020 repos, 2026-09-23); `note-20260817-0001`
  (`/Users/agallojr/proj/src/research-notes/bus/memory/notes/note-20260817-0001-sqls-fvm-quantum-timestep-frozen-jacobian.md`,
  the SQLS->FVM integration design note); `lore-20260925-0002` (Zscaler TLS
  interception on this laptop, context for the Zscaler-issued certificate seen
  in C.1).
