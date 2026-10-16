VERDICT: FAIL

One criterion fails: 6 / rung 5b solution-quality thresholds (fidelity >= 0.98 every
iteration, residual_total at iteration 14 <= 1e-2). Observed: fidelity 0.9623 at step 1 (four
of 15 steps below 0.98) and residual_total 1.546 at iteration 14. Every other criterion (1, 2,
3, 4, 5, 7) and every other rung (1, suites, gate, 3b, 4b, 5a, and the circuit-size / wall-time
parts of 5b) passes. The evidence in sec. 6.5b and 8.1 says the failing thresholds are not met
by the historical ensemble on the old stack either (2 of 10 Nov 2025 trials would pass both)
and that the Aer SamplerV2 port is behaviorally equivalent to the runtime sampler on the
identical circuit, so this reads as a miscalibrated acceptance threshold on an unseeded,
high-variance case rather than a port defect. The verdict follows the criteria as written; the
new run is nevertheless the worst of 13 recorded runs of this case, so a re-run (needs
approval) or a re-specified 5b is the way to close it.

# Verification of work item 3: qiskit-ibm-runtime 0.49.0 -> 0.50.0, Aer SamplerV2 port, re-lock

Independent verifier session 2026-10-15T05:34:49Z to 2026-10-15T06:14Z, laptop (Apple
silicon, Darwin 25.6.0). Other agents were active on the machine, so wall times are upper
bounds. Interpreter for every run:
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python` (Python 3.12.10).
Read-only everywhere: no edit / add / commit / stash / checkout / reset / push in any repo, no
`uv lock`, `uv sync`, `uv add`, `uv pip`, no pip, no network. Scratch `/tmp/order2-verify-3/`
deleted at the end. Not read: `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`,
`sqls-patches/`.

Work under test:

- fvm `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26`,
  HEAD `1481073cd8fefe6436e57b194d210e28da6f02aa`; `git log --oneline f16720b3..HEAD` =
  1481073c, fa9eab2d, c074dc95, abf74941, 6c672f2b, 4f44d5be, 7a1542a6 (7 commits, 2026-10-15
  04:32Z to 05:29Z). `git status --short` empty before and after every run.
- sqls clone `/Users/agallojr/proj/src/q8020/sqls`, branch `local/sampler-port-2026-10` at
  `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` (same commit as `main`; no commits on the branch),
  port uncommitted: `git diff main --stat` = `src/sqls/runtime/quantum.py | 29 ++++---` (19
  insertions, 10 deletions, one file). No stash, no untracked files.
- fork clone `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, branch
  `feature/qiskit3-api-port` at `66eadf0b4edcff100b20edf70a99e79cc69c5923`, 7 files modified
  uncommitted (the qiskit-3 port, item 15; only its commit / dirty flag matters here).

## 1. sqls clone `src/sqls/runtime/quantum.py` -- PASS

Read: `git -C /Users/agallojr/proj/src/q8020/sqls diff main` and the full working-tree file.

- Shots path: `_run_shots` does `from qiskit_aer.primitives import SamplerV2 as Sampler`
  (line 209, function-local, lazy) and `sampler = Sampler.from_backend(simulator, seed=seed)`
  (line 220). Statevector path untouched (`simulator.run(qc_save, shots=1)`).
- `grep -rn qiskit_ibm_runtime /Users/agallojr/proj/src/q8020/sqls/src/sqls` -> no hit, rc 1.
  (Repo-wide, only `README.md` and `examples/potential_flow.py` still mention it; examples are
  outside `src/`.)
- `from_backend` in qiskit-aer 0.17.2 is `from_backend(cls, backend, **options)`:
  `sampler = cls(**options)`; if `isinstance(backend, AerSimulator)` then
  `sampler._backend = backend` (the caller's object, all options kept). `__init__(self, *,
  default_shots=1024, seed=None, options=None)`, so `seed=seed` is a valid forward.
- Method / device honored (probe `/tmp/order2-verify-3/probe_c1_method.py`, built exactly as
  sqls does, 2-qubit Bell circuit, 3 pubs x 1000 shots, `-W error::DeprecationWarning`):
  `AerSimulator(method='statevector')` -> `sampler._backend is sim` True,
  `backend.options.method = statevector`, `device = CPU`; `method='matrix_product_state'` ->
  `sampler._backend is sim` True, `options.method = matrix_product_state`, `device = CPU`. Both
  ran, counts ~50/50 on `00`/`11`. The result `metadata['simulator_metadata']` carries no
  `method` key in Aer 0.17.2 (keys: time_taken_parameter_binding, max_memory_mb,
  time_taken_execute, omp_enabled, max_gpu_memory_mb, parallel_experiments), so the proof is
  via the backend options plus a behavioral check: the same construction with
  `AerSimulator(method='stabilizer')` on a circuit with a T gate fails with Aer's
  `Circuit ... contains invalid instructions {"gates": {t}} for "stabilizer" method`, while
  statevector and MPS run. The sampler runs on the caller's method.
- `repeats` semantics unchanged: `sampler.run([qc_meas] * repeats, shots=shots)` and the
  accumulation loop (`for i in range(repeats): ... result[i].data.meas.get_counts()`,
  `data_probs += c`, `recon += amps / na * target_norm`, `recon /= repeats`) are context lines
  in the diff (not modified). Probe `/tmp/order2-verify-3/probe_c1_seed.py` wrapped
  `SamplerV2.run` and recorded `(n_pubs, shots, seed)` for `quantum_solve(..., mode='shots')`:
  `repeats=2, shots=2000` -> `(2, 2000, seed)`; `repeats=3, shots=5000` -> `(3, 5000, None)`.
- `get_counts()` handling unchanged (`result[i].data.meas.get_counts()`, context line).
- Optional `seed`: present, keyword-only (`*, seed=None`), documented in the docstring,
  threaded to `_run_shots(..., seed=seed)`. Probe (4x4 random system, `full_svd`, k=2,
  repeats=2, shots=2000): `seed=123` twice -> identical reconstruction (max |diff| 0.0);
  `seed=None` twice -> different (max |diff| 5.0e-3); seed=123 vs None differ. Fidelity to the
  exact solution: statevector 1.0000000000000002, shots 0.99996 (seed 123) / 0.99989 (None).
- Hygiene of the sqls diff: 0 added lines > 88 chars, 0 trailing-whitespace lines,
  `git diff --check main` rc 0.

## 2. fvm `quantum_tools.py` -- PASS

Read: `git show 7a1542a6`, `grep -n qiskit_ibm_runtime quantum_tools.py`.

- Module-level `from qiskit_ibm_runtime import SamplerV2 as Sampler` removed. `run_circuit_ibm`
  (lines 488 to 499): `if self.backend_type == 'ideal': from qiskit_aer.primitives import
  SamplerV2 as AerSampler; sampler = AerSampler.from_backend(self.backend)` else
  `from qiskit_ibm_runtime import SamplerV2 as Sampler; sampler = Sampler(self.backend)`
  (fake / real-ibm). `self.backend` for `ideal` is `AerSimulator(method=self.backend_method
  [, device='GPU'])` (lines 223 to 232). Remaining `qiskit_ibm_runtime` references in the file:
  line 241 (`fake_provider` import inside `get_backend`, fake branch), line 250 (comment),
  line 493 (comment), line 498 (the lazy import). No module-level runtime import anywhere in
  `quantum_tools.py`, `time_solvers.py`, `nozzle_1d_solver.py`, `math_tools.py`;
  `helper_tools.py` line 18 is only the distribution-name string for `code_versions`.
- Where the 0.50.0 deprecation fires (probe, `-W always`): importing
  `qiskit_ibm_runtime.SamplerV2` emits nothing; instantiating `SamplerV2(AerSimulator())`
  emits `DeprecationWarning: The SamplerV2 class is deprecated as of qiskit-ibm-runtime 0.50.0
  and will be removed no sooner than 3 months after the release date ...`; under
  `-W error::DeprecationWarning` the instantiation raises. So `-W error` on an ideal run is a
  real guard against any use of the runtime sampler.
- Probe runs (exact CLI, `-W error::DeprecationWarning -X importtime`, output to
  `/tmp/order2-verify-3/r3b`, `r4b`):
  - ideal SQLS shots (rung 3b flags): rc 0, 1.48 s wall, 2026-10-15T05:41:08Z. importtime: 0 of
    1545 import records match `^qiskit_ibm_runtime`; `stevedore` not imported.
  - ideal HHL shots (rung 4b flags): rc 0, 8.52 s wall, 05:41:10Z to 05:41:18Z. importtime: 311
    of 2502 records are `qiskit_ibm_runtime.*`, all at top-level indent with no record for the
    package or for `qiskit_ibm_runtime.transpiler.plugin` itself, which is the signature of
    `importlib.import_module` from entry-point loading (stevedore and
    `qiskit.transpiler.preset_passmanagers.plugin` are both present in this run only).
    Confirmed independently: a bare `transpile(QuantumCircuit(2), AerSimulator())` in a fresh
    interpreter flips `'qiskit_ibm_runtime' in sys.modules` from False to True (and loads
    `qiskit_ibm_runtime.transpiler.plugin`). qiskit-ibm-runtime 0.50.0 registers three
    `qiskit.transpiler.translation` entry points (`ibm_backend`, `ibm_dynamic_and_fractional`,
    `ibm_dynamic_circuits` -> `qiskit_ibm_runtime.transpiler.plugin:*`), so qiskit's
    translation-stage plugin discovery imports the package on every `transpile`. Not fvm's
    doing; the deprecated class is imported as a side effect but never instantiated (rc 0 under
    `-W error`).

## 3. `pyproject.toml` -- PASS

Read in full at HEAD (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/pyproject.toml`).

- `dependencies`: `qiskit==2.5.2`, `qiskit-aer==0.17.2`, `qiskit-ibm-runtime==0.50.0`; also
  `quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers` and
  `sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git` (origin names only, see sources).
- `[tool.uv.sources]`: `sqls = { path = "../sqls", editable = true }`,
  `quantum_linear_solvers = { path = "../quantum_linear_solvers", editable = true }`.
- `[tool.uv] override-dependencies = ["qiskit==2.5.2", "qiskit-aer==0.17.2",
  "numpy>=1.20.0", "scipy>=1.7.0"]` neutralizes sqls's hard pins (`qiskit==2.1.2`,
  `qiskit-aer==0.17.1`, `numpy==2.3.3`, `scipy==1.16.2`, read from
  `/Users/agallojr/proj/src/q8020/sqls/pyproject.toml`). The lock's `[manifest] overrides`
  records the same four.
- `[dependency-groups] dev = ["pytest>=8"]`. The old `[project.optional-dependencies] sqls`
  extra is gone.
- Documented sync command: README "Installation" has exactly one, `uv sync` (line 65), and
  states `pip install -e .` is not supported (line 81). TESTING.md refers to the same `uv sync`
  in prose. The only other install-type commands in README are inside the Rollback block
  (sec. 7). Finding: `docs/FRONTIER_CONDA_SETUP.md` (lines 78, 83, 225) and
  `docs/QUICKSTART_PARALLEL.md` (line 19) still say `pip install .`; outside this criterion's
  scope (README / TESTING.md) but stale.
- Hygiene: no line > 88 chars added by these commits (1481073c reflowed the one comment that
  was). Pre-existing line 8 (`description = ...`) is 98 chars and was already so at f16720b3.

## 4. `uv.lock` and the venv -- PASS

- `uv.lock` (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/uv.lock`, 187543 bytes,
  mtime 2026-10-15 01:07 -0400 = 05:07Z, committed in c074dc95 at 05:12:50Z; `git status`
  clean): qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, qiskit-mitigation 0.1.1
  (new hard dep of runtime 0.50.0; samplomatic bumped 0.20.0 -> 0.21.0), pytest 9.1.1, numpy
  2.5.2, scipy 1.18.0; `sqls 0.1.0 source = { editable = "../sqls" }`,
  `quantum-linear-solvers 0.1.0 source = { editable = "../quantum_linear_solvers" }`;
  `grep -c 'git+' uv.lock` = 0; root `requires-dist` lists both as `editable = "../..."`;
  `[package.dev-dependencies] dev = [pytest]`. 57 packages.
- venv: `python -c "import sqls, linear_solvers, qiskit, qiskit_aer, qiskit_ibm_runtime,
  pytest; ..."` -> `sqls /Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py`,
  `linear_solvers /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py`,
  qiskit 2.5.2, qiskit_aer 0.17.2, qiskit_ibm_runtime 0.50.0, pytest 9.1.1, numpy 2.5.2,
  scipy 1.18.0. `site-packages/__editable__.sqls-0.1.0.pth` points at
  `/Users/agallojr/proj/src/q8020/sqls/src`; both `direct_url.json` records are
  `file:///...` with `"editable": true`.
- `python -W error::DeprecationWarning -c "import linear_solvers, sqls, qiskit_aer,
  qiskit_ibm_runtime; from linear_solvers import HHL"` -> `ok`, rc 0. Also rc 0 for
  `import sqls.runtime.quantum, quantum_tools, time_solvers, nozzle_1d_solver` under the same
  filter.
- Read-only uv checks (2026-10-15T05:40:02Z): `uv lock --locked --offline` -> `Resolved 57
  packages in 1ms`, rc 0 (lock matches pyproject). `uv sync --frozen --offline --dry-run` ->
  rc 0, `Found up-to-date lockfile`, would only uninstall / reinstall the root project
  `fvm-euler-1d-solver` itself (uv always re-reports the root editable in a dry run); no other
  package would change. `uv.lock` mtime unchanged afterwards.

## 5. Metadata `code_versions` -- PASS

Pickles from the sec. 2 / 6 runs, checked with `pickle.load` against `git -C <clone>
rev-parse HEAD` (fvm 1481073cd8fe..., sqls 9a4346a7d025..., fork 66eadf0b4edc...):

| run | fvm commit == HEAD / dirty | sqls commit == HEAD / dirty / path | linear_solvers commit == HEAD / dirty | stack |
|---|---|---|---|---|
| SQLS nelem 2 shots 10000 (`metadata_nelem2_SQLS_statevector_nshots10000.pkl`) | yes / False | yes / True / `/Users/agallojr/proj/src/q8020/sqls/src/sqls` | yes / True | qiskit 2.5.2, qiskit_aer 0.17.2, qiskit_ibm_runtime 0.50.0, numpy 2.5.2, scipy 1.18.0, python 3.12.10 |
| HHL nelem 2 shots 1000 | yes / False | yes / True | yes / True | same |
| LU nelem 2 | yes / False | yes / True | yes / True | same |

Keys exactly `fvm, sqls, linear_solvers, qiskit, qiskit_aer, qiskit_ibm_runtime, numpy,
scipy, python`; all commits 40-hex; `commit_source` `git` for sqls and linear_solvers; fvm
`version` 0.1.0. LU run importtime: 0 of 642 import records match `^(qiskit|sqls|
linear_solvers)` (only the `.pth` editable finder hooks load). Contract: `tests/contract.py`
`CODE_VERSIONS_KEYS` / `_FVM_KEYS` / `_SOURCE_KEYS` and
`tests/test_output_contract.py::test_code_versions` (runs for SQLS, HHL, LU) pin it; the
suite below passes them.

## 6. Ladder on the new stack

### Rung 1, import smoke -- PASS
2026-10-15T05:39:57Z, `python -W always -c "import linear_solvers, sqls, qiskit_aer,
qiskit_ibm_runtime; from linear_solvers import HHL; ..."` -> `smoke ok 2.5.2 0.17.2 0.50.0`,
rc 0, 1.21 s, zero warnings of any kind (none of the four old fork warnings). Variant that also
does `from qiskit_ibm_runtime import SamplerV2`: still zero warnings (the deprecation is
emitted at instantiation, sec. 2), rc 0.

### Default suite, unittest -- PASS
`.venv/bin/python -m unittest discover -s tests -v`, 05:42:44Z to 05:43:31Z: `Ran 82 tests in
46.196s`, `OK (skipped=1)`, 47.04 s process wall. Skip =
`test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`
("gate-only (~90 s): set FVM_GATE_TESTS=1"). No FAIL / ERROR lines. `git status` clean.

### Default suite, pytest -- PASS
`.venv/bin/python -m pytest tests -q -p no:cacheprovider`, 05:44:10Z to 05:44:58Z: `81 passed,
1 skipped, 36 subtests passed in 47.48s`, 47.87 s process wall; `--collect-only` = `82 tests
collected`, the same count as unittest. No `.pytest_cache/` left behind.

### Gate fixture -- PASS
`FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`, 05:46:38Z to
05:48:22Z: `Ran 7 tests in 103.037s`, `OK`, 7/7 at `MAX_ABS_TOL = 1e-10` (plus fidelity and
residual to 1e-8, provenance sha256). Per-test: nelem-5 HHL 94.73 s, nelem-2 HHL 8.21 s, SQLS
0.02 to 0.08 s, provenance 0.00 s. 103.74 s process wall (TESTING.md documents 94.4 s / 86.6 s
for the nelem-5 solve; the difference is CPU contention from the other agents).

### Rung 3b, SQLS nelem 2 shots -- PASS
`python -W error::DeprecationWarning nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver
SQLS -shots 10000 -sqls_repeats 1 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow` (plus
`-X importtime`, `-outdir`), 05:41:08Z: rc 0, 1.48 s. `hhl_metrics` fidelity 0.99996190
(step 0), 0.99996438 (step 1), both >= 0.999. 16 output files (file set as in the contract).

### Rung 4b, HHL nelem 2 shots -- PASS
`python -W error::DeprecationWarning nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver
HHL -shots 1000 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow` (plus `-X importtime`,
`-outdir`), 05:41:10Z: rc 0, 8.52 s. Fidelity 0.96331950 >= 0.9. `qc_metadata`: 12 transpiled
qubits, depth 68964, gates 74816, nqubits 4, run 1.65 s.

### Rung 5a, SQLS nelem 5 150000 shots -- PASS
`python -W error::DeprecationWarning nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver
SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats
1 -noshow -outdir /tmp/order2-verify-3/r5a`, 05:42:42Z: rc 0, 1.97 s wall (solver
`elapsed_time` 0.589 s). `SOLUTION CONVERGED at iteration 6`; metadata `converged True`,
`converged_by residual_ratio`, `final_iters 6`; residual_total 12.375368413827264 -> 0.6025 ->
0.05745 -> 3.278e-3 -> 3.114e-5 -> 1.866e-7 -> 8.127e-10 (7 rows, 0..6). Fidelity per step:
0.99997142, 0.99997396, 0.99998499, 0.99998473, 0.99995166, 0.99998644, 0.99997892 (min
0.99995 at step 4, all >= 0.999 including the last). `final_results_nelem5_SQLS_statevector_
nshots150000.csv` vs `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/
fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/final_results_nelem5_SQLS_statevector_
nshots150000.csv`: max |diff| xp 0.0, rho 1.88e-11, u 6.94e-11, p 2.45e-11, Mach 1.66e-10;
overall 1.66e-10 <= 1e-6.

### Rung 5b, HHL nelem 5 150000 shots -- FAIL (quality thresholds); circuit size and wall PASS
`python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -shots 150000
-iters 15 -initers 1 -cfl 1e10 -noshow -outdir /tmp/order2-verify-3/r5b` (exactly as
specified, no `-W` flag), single approved run in the tool's background mode, nothing else
heavy meanwhile. 2026-10-15T05:49:01Z to 06:04:28Z, rc 0, **927.01 s** process wall (`user`
2937.92 s; metadata `elapsed_time` 925.0 s). 15 iterations completed (`final_iters 14`,
`converged False`, 15 rows in each CSV). Per iteration (`qc_metadata_nelem5_statevector_
shots150000.csv`, `hhl_metrics_...csv`, `residual_...csv`):

| step | fidelity | linsys_residual | residual_total | qubits_t | depth_t | gates_t | gen s | transpile s | run s |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.998054 | 2.717e+00 | 1.2375e+01 | 14 | 596688 | 641124 | 19.6 | 14.3 | 19.9 |
| 1 | 0.962336 | 2.602e+00 | 3.1863e+00 | 14 | 595700 | 640090 | 21.1 | 15.7 | 26.0 |
| 2 | 0.983195 | 2.301e+00 | 2.6066e+00 | 14 | 595939 | 640348 | 22.6 | 14.8 | 20.9 |
| 3 | 0.968033 | 2.251e+00 | 2.3018e+00 | 14 | 597461 | 641903 | 20.7 | 21.1 | 22.1 |
| 4 | 0.980637 | 2.169e+00 | 2.2507e+00 | 14 | 596202 | 640615 | 22.5 | 14.7 | 20.2 |
| 5 | 0.982941 | 2.106e+00 | 2.1688e+00 | 14 | 596441 | 641121 | 22.9 | 14.8 | 20.3 |
| 6 | 0.985516 | 2.068e+00 | 2.1061e+00 | 14 | 597732 | 642443 | 19.7 | 13.5 | 20.0 |
| 7 | 0.985337 | 2.006e+00 | 2.0683e+00 | 14 | 596712 | 641079 | 20.0 | 14.6 | 19.8 |
| 8 | 0.973244 | 1.886e+00 | 2.0065e+00 | 14 | 596433 | 640734 | 19.7 | 14.5 | 19.7 |
| 9 | 0.986586 | 1.770e+00 | 1.8857e+00 | 14 | 596720 | 641098 | 19.6 | 13.7 | 19.9 |
| 10 | 0.981907 | 1.704e+00 | 1.7701e+00 | 14 | 595939 | 640592 | 19.7 | 13.6 | 19.8 |
| 11 | 0.987989 | 1.701e+00 | 1.7038e+00 | 14 | 596696 | 641109 | 19.7 | 13.5 | 19.9 |
| 12 | 0.982656 | 1.650e+00 | 1.7013e+00 | 14 | 596433 | 640897 | 19.7 | 13.9 | 19.9 |
| 13 | 0.980460 | 1.546e+00 | 1.6500e+00 | 14 | 595429 | 639893 | 19.8 | 13.5 | 19.8 |
| 14 | 0.973571 | 1.493e+00 | 1.5463e+00 | 14 | 595676 | 640140 | 19.8 | 13.6 | 19.9 |

(gen / transpile / run are `circ_generate_time`, `circ_transpile_time`, `circ_run_time` in s;
sums 307.2 s, 219.9 s, 308.0 s.)

Against the criterion:
- 15 iterations completed: PASS.
- `circ_qubits_transpile` 14 at iteration 0: PASS (14 at every iteration).
- `circ_depth_transpile` at iteration 0 596688 vs 596688: +0.000 %; all iterations within
  -0.211 % .. +0.175 %: PASS (5 % band).
- `circ_gates_transpile` at iteration 0 641124 vs 641145: -0.003 %; all iterations within
  -0.195 % .. +0.202 %: PASS.
- fidelity >= 0.98 every iteration: **FAIL**. Min 0.962336 at step 1; below 0.98 at steps 1
  (0.9623), 3 (0.9680), 8 (0.9732), 14 (0.9736).
- residual_total at iteration 14 <= 1e-2: **FAIL**. Observed 1.5463.
- wall 800 to 1000 s: PASS (927.01 s).

Context for the two failures (details in sec. 8.1): the iter-0 system is bit-identical to the
archived fixture `tests/data/system_Ab_nelem5_iter0.pkl`, the iter-0 depth / gates equal the
August reference to 0.003 %, and on the identical saved iter-0 circuit the Aer sampler and the
runtime sampler produce statistically indistinguishable counts. The Newton residual stalls
because `hhl_solve`'s least-squares scale `alpha_ls = (b @ A dq)/(A dq @ A dq)` collapses the
step when the sampled direction is 1 to 2 % off (cond(A) 38 to 64 amplifies the error in
`A @ dq_hhl`): `||dq_hhl|| / ||dq_lu||` is 0.001 to 0.20 from iteration 1 on (median 0.036)
versus 0.06 to 0.83 (median 0.39) in the August run, while the direction (cos) is 0.981 to
0.994 versus 0.994 to 0.999. Sign agreement is 15/15 at every step in both runs.

## 7. Rollback recipe -- PASS (read, not executed)

README lines 94 to 102:

```
git checkout f16720b3 -- pyproject.toml uv.lock   # pre-re-lock state
uv sync                      # re-fetches the fork from GitHub
VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps
VIRTUAL_ENV=.venv uv pip list | grep -i -E 'qiskit|sqls|linear'
```

Consistency with the layout, checked against `git show f16720b3:pyproject.toml` and
`git show f16720b3:uv.lock`: at f16720b3 the pin is `qiskit-ibm-runtime==0.49.0`, the fork is
`quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers` (lock source
`git = ...#66eadf0b...`, no path sources, no overrides), sqls is the opt-in
`[project.optional-dependencies] sqls` extra, and the lock has no `sqls`, `pytest` or
`qiskit-mitigation` entries (samplomatic 0.20.0). So `uv sync` on the restored files
reinstalls runtime 0.49.0 and the fork from GitHub (network, as the comment says), removes
sqls / pytest / qiskit-mitigation, and the third line re-adds the sibling `../sqls` editable
with `--no-deps` (keeping qiskit 2.5.2), which is the pre-re-lock state. The sqls port in the
working tree (Aer SamplerV2) also runs on 0.49.0 (Aer 0.17.2 is unchanged), so the rollback
does not need the sqls tree touched. The recipe leaves `pyproject.toml` / `uv.lock` modified
in the fvm tree, as a rollback must; it does not restore pytest (correct for "pre-re-lock",
TESTING.md keeps unittest as the fallback).

## 8. Findings

### 8.1 Rung 5b: variance of the case, and the sampler A/B
- Historical runs of the identical case (`hhl_metrics_nelem5_statevector_shots150000.csv`
  under `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/`):

| run | min fidelity | median fidelity | steps < 0.98 | residual_total at iter 14 |
|---|---|---|---|---|
| 2025-11-11/shots_150000/trial_0_de74c43a | 0.9551 | 0.9742 | 11 | 1.710e-05 |
| 2025-11-11/shots_150000/trial_1_91f8c3cc | 0.9267 | 0.9821 | 6 | 1.858e-03 |
| 2025-11-11/shots_150000/trial_2_5ae8dfdb | 0.9919 | 0.9943 | 0 | 4.624e-01 |
| 2025-11-11/shots_150000/trial_3_eb33a593 | 0.9715 | 0.9845 | 4 | 1.017e-01 |
| 2025-11-11/shots_150000/trial_4_9f21cf9f | 0.9564 | 0.9907 | 2 | 5.205e-03 |
| 2025-11-11/shots_150000/trial_5_9e98b39b | 0.9975 | 0.9985 | 0 | 4.991e-02 |
| 2025-11-11/shots_150000/trial_6_02c7e361 | 0.9897 | 0.9970 | 0 | 1.100e-01 |
| 2025-11-11/shots_150000/trial_7_078abc68 | 0.9943 | 0.9967 | 0 | 5.331e-03 |
| 2025-11-11/shots_150000/trial_8_1cf0fedb | 0.9873 | 0.9938 | 0 | 8.084e-03 |
| 2025-11-11/shots_150000/trial_9_32c52422 | 0.6898 | 0.9765 | 10 | 3.239e-07 |
| 2026-08-17-qiskit23-local/trial_0 | 0.9801 | 0.9903 | 0 | 4.688e-03 |
| 2026-08-17-qiskit25-local/trial_0 (runtime 0.49.0, the 596688 / 641145 reference, 859 s) | 0.9880 | 0.9932 | 0 | 6.795e-03 |
| this run (runtime 0.50.0, Aer SamplerV2) | 0.9623 | 0.9827 | 4 | 1.546e+00 |

  Only 2 of the 10 Nov 2025 trials (7, 8) satisfy both 5b thresholds; the final residual
  spans six decades across identical unseeded runs. This run's min fidelity, median fidelity
  and count of sub-0.98 steps are inside that envelope; its final residual is the worst of the
  13 (3.3x the previous worst, 0.46). The thresholds were evidently taken from the two August
  single trials, which are favorable samples.
- Sampler A/B on the identical circuit (`/tmp/order2-verify-3/probe_ab_sampler.py`, loads the
  saved `circuit_transpile_statevector_shots150000_nelem5_iter0.qpy` from this run: 14
  qubits, one `meas[14]` register, depth 596688, 641123 ops; 06:09:27Z to 06:10:28Z). Exact
  distribution from `save_statevector` on the measurement-stripped circuit (10.2 s), then
  150000 shots each: Aer `SamplerV2.from_backend(AerSimulator(method='statevector'))` -> TVD to
  exact 0.0013, Bhattacharyya fidelity 0.99966, 19.7 s; runtime `SamplerV2(AerSimulator(...))`
  (local mode, the 0.49.0-era path) -> TVD 0.0025, fidelity 0.99964, 17.5 s; TVD between the
  two samplers 0.0033, against a sampling scale sqrt(K / 2 pi N) = 0.0061 for K = 35 effective
  outcomes. Ancilla clbit 13: P(1) = 0.0144 exact, 0.0145 / 0.0143 sampled (2177 / 2150 kept
  shots); postselected amplitude fidelity 0.98614 (Aer) vs 0.98569 (runtime). The port does
  not change the sampled distribution; the ~1.4 % postselection success at 150000 shots sets
  an intrinsic per-step amplitude-fidelity floor near 0.986 for this system.
- Mechanism of the stall, per-iteration `||dq_hhl|| / ||dq_lu||` (this run vs August
  qiskit25): 0.940/0.962, 0.203/0.828, 0.110/0.393, 0.022/0.600, 0.038/0.586, 0.029/0.133,
  0.018/0.290, 0.030/0.241, 0.060/0.131, 0.064/0.356, 0.036/0.396, 0.001/0.063, 0.031/0.071,
  0.062/0.397, 0.032/0.492. Zero components in `dq_hhl` (unsampled amplitudes): 1 to 4 per
  step in both runs. Recommendation (not a criterion): respecify 5b as an ensemble or seeded
  check (a `seed` now exists in sqls; the fvm HHL path exposes none), or gate on the
  statevector solve (already pinned at 1e-10 by the gate fixture) plus the circuit-size and
  per-step-fidelity-floor checks, which this run passes.

### 8.2 Other findings
- `tests/contract.py` hard-codes `SQLS_CHECKOUT = '/Users/agallojr/proj/src/q8020/sqls'` and
  `test_output_contract.py::test_code_versions` runs `git -C <that path> rev-parse HEAD` with
  `check=True` and no existence guard; on any other node (Frontier) the SQLS contract test
  raises `CalledProcessError` unless the clone sits at that exact path.
- `docs/FRONTIER_CONDA_SETUP.md` and `docs/QUICKSTART_PARALLEL.md` still instruct
  `pip install .`, contradicting README's `uv sync`-only install.
- Frontier readiness of the lock (uv.lock wheel lists, `tomllib` parse of all 57 packages):
  every registry package has either a pure-Python wheel (`py3-none-any`: qiskit-ibm-runtime
  0.50.0, qiskit-mitigation 0.1.1, samplomatic 0.21.0, ...) or a Linux x86_64 wheel usable by
  cp312 (qiskit 2.5.2 `cp310-abi3-manylinux_2_28_x86_64`, qiskit-aer 0.17.2
  `cp312-manylinux_2_17_x86_64`, rustworkx 0.18.1 `manylinux2014_x86_64`, numpy, scipy,
  matplotlib, pillow, pydantic-core, cffi, cryptography, orjson, pybase64, psutil, pyyaml,
  kiwisolver, contourpy, fonttools, charset-normalizer). The single exception, `sspilib 0.5.0`
  (Windows wheels only, sdist), is gated by `marker = "sys_platform == 'win32'"` under
  pyspnego and is not installed on Linux or macOS. Caveats: qiskit's wheel needs glibc >= 2.28;
  `requires-python >=3.12,<3.14`; the two editable path sources require `../sqls` and
  `../quantum_linear_solvers` beside the repo (README says so); the lock pins the CPU
  `qiskit-aer` wheel, so a ROCm Aer on Frontier has to be layered outside `uv sync` (README
  defers to `docs/FRONTIER_CONDA_SETUP.md`, which is the stale `pip install .` doc above).
- Hygiene on the fvm commits: `git diff f16720b3..HEAD -- '*.py' | grep '^+' | awk 'length >
  89'` -> 0 lines; trailing whitespace in added lines (all files) -> 0.
- sqls `pyproject.toml` keeps its hard pins and the `[examples]` extra still lists
  `qiskit-ibm-runtime`; the lock records the pins in sqls's `requires-dist` and the overrides
  neutralize them. `examples/potential_flow.py` still imports the runtime sampler (outside
  `src/`, not part of the port).
- Deprecation surface: runtime 0.50.0 warns on `SamplerV2(...)` instantiation only; a plain
  import is silent. The `-W error` guard therefore protects the ideal path but a smoke import
  cannot detect a stray runtime import.
- Timing deltas vs TESTING.md are all contention-sized: unittest 47.04 s vs 46.1 s, pytest
  47.87 s vs 46.2 s, gate 103.74 s vs 94.4 s, 5b 927 s vs the August 859 s.

## 9. Not checked, and why
- No real `uv sync` (forbidden); only `uv lock --locked --offline` and
  `uv sync --frozen --offline --dry-run`, both read-only, both rc 0.
- The fake / real-ibm HHL paths (runtime SamplerV2 instantiation, deprecated but functional):
  not in the criteria, not run.
- A baseline rung-5b run at f16720b3 / runtime 0.49.0, or a second 5b run on the new stack:
  not approved (one 5b run was). Either would settle regression-vs-variance directly; the
  sampler A/B on the identical circuit (sec. 8.1) is the closest read-only surrogate.
- Whether a fixed `seed` with `repeats > 1` gives distinct counts per pub inside one Aer
  sampler call (Aer's per-circuit seed handling): not probed; only run-to-run reproducibility
  was.
- Frontier install itself: no access.
- `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`, `sqls-patches/` not read, per
  instructions; the 5b reference values were instead traced to
  `results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/`.

Scratch `/tmp/order2-verify-3/` (r3b, r4b, rlu, r5a, r5b outputs, probes, suite logs) deleted
at 2026-10-15T06:14Z. No file other than this one was created or modified in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/`.
