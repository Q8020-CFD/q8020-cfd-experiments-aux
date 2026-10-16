# Qiskit upgrade plan and solverfw usage analysis

Work-plan item 3 of `WORKPLAN.md` (same folder). Analysis only, written
2026-10-14 (UTC) on the Mac laptop. Nothing was installed, no venv / lock /
pyproject was touched, the solver was not run. The one piece of Python executed
was an import-only probe of the existing venv (section 3.4) to read deprecation
warnings off the installed packages.

Headline, so the rest can be read as detail:

- **qiskit 2.5.2 and qiskit-aer 0.17.2 are already the latest stable releases.**
  The only stable bump available is `qiskit-ibm-runtime` 0.49.0 -> 0.50.0.
  Qiskit 2.6.0 exists only as `2.6.0rc1` (pre-release, PyPI 2026-10-02).
- The upgrade that matters is therefore small, but it carries one new
  deprecation that touches our code: **runtime 0.50.0 deprecates `SamplerV2`**,
  which both `fvm_euler_1d_solver/quantum_tools.py` and `sqls/runtime/quantum.py`
  import. It still works (warning only).
- The bigger, pre-existing exposure is in the HHL library fork: it is built on
  four classes already deprecated in qiskit 2.1 / 2.2 and slated for removal in
  **qiskit 3.0** (`BlueprintCircuit`, `PhaseEstimation`, `ExactReciprocal`,
  `QFT` via `PhaseEstimation`). No action needed for this upgrade, but the HHL
  path dies at 3.0 unless the fork is ported.
- `uv.lock` is stale relative to `pyproject.toml` (the `[sqls]` extra was added
  without re-locking), so any `uv lock` / `uv sync` will try to reach
  `code.ornl.gov`, which has blocked us before. The plan handles this.
- **solverfw: the direct `fvm` + `sqls` route for the paper does not touch
  solverfw at all.** Only the archived `fvm` branch, the metautil feature branch,
  and the Z-Keep adapter do.

---

## 1. Current stack

Verified 2026-10-14 on the laptop. Repo and venv paths are absolute.

### 1.1 fvm solver (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`)

| Item | Value | Source |
|---|---|---|
| branch / commit | `main` @ `ef7f0a8b` "Add optional SQLS linear solver alongside HHL", tree clean | `git rev-parse`, `git status` |
| Python in venv | 3.12.10 (`.python-version` = `3.12`) | `.venv/bin/python --version` |
| `requires-python` | `>=3.12,<3.14` | `pyproject.toml` |
| `uv` | 0.7.2 (Homebrew 2025-04-30) at `/opt/homebrew/bin/uv` | `uv --version` |
| pin `qiskit` | `==2.5.2` | `pyproject.toml` |
| pin `qiskit-aer` | `==0.17.2` | `pyproject.toml` |
| pin `qiskit-ibm-runtime` | `==0.49.0` | `pyproject.toml` |
| pin `qiskit-qasm3-import` | `>=0.6.0` | `pyproject.toml` |
| pin `numpy` / `scipy` | `>=1.20.0` / `>=1.7.0` | `pyproject.toml` |
| `quantum_linear_solvers` | `git+https://github.com/Q8020-CFD/quantum_linear_solvers` (no rev pinned in pyproject) | `pyproject.toml` |
| optional extra `[sqls]` | `sqls @ git+https://code.ornl.gov/olcf-qcfd/sqls.git` | `pyproject.toml` |

Locked versions in `uv.lock` (`requires-python = ">=3.12, <3.14"`, lock
`revision = 2`):

| Package | Locked | Notes |
|---|---|---|
| qiskit | 2.5.2 | |
| qiskit-aer | 0.17.2 | |
| qiskit-ibm-runtime | 0.49.0 | |
| qiskit-qasm3-import | 0.6.0 | |
| numpy | 2.5.2 | |
| scipy | 1.18.0 | |
| quantum-linear-solvers | 0.1.0 @ git `66eadf0b4edcff100b20edf70a99e79cc69c5923` | fork tip (see 1.3) |
| rustworkx / stevedore / dill | 0.18.1 / 5.9.0 / 0.4.1 | qiskit deps |
| sqls | **absent** | see below |

**Stale-lock finding.** `uv.lock` was last written by commit `a885ef47`
(2026-08-17T21:16:25Z). The later commit `ef7f0a8b` (2026-08-17T23:22:59Z) added
the `[project.optional-dependencies] sqls` extra to `pyproject.toml` but did not
touch `uv.lock` (`git show --stat ef7f0a8b` lists only `nozzle_1d_solver.py`,
`pyproject.toml`, `quantum_tools.py`, `time_solvers.py`). The lock's
`[package.metadata] requires-dist` for `fvm-euler-1d-solver` has no
`extra == 'sqls'` entry and the string `code.ornl.gov` does not occur in the
lock. Consequence: the next `uv lock` (or an un-frozen `uv sync`) must resolve
the ORNL git URL. See section 4, step 1.

Installed `dist-info` in `.venv/lib/python3.12/site-packages` (relevant subset):
`qiskit-2.5.2`, `qiskit_aer-0.17.2`, `qiskit_ibm_runtime-0.49.0`,
`qiskit_qasm3_import-0.6.0`, `quantum_linear_solvers-0.1.0`, `sqls-0.1.0`
(editable, `__editable__.sqls-0.1.0.pth` -> `/Users/agallojr/proj/src/q8020/sqls/src`),
`numpy-2.5.2`, `scipy-1.18.0`, `samplomatic-0.20.0`,
`ibm_quantum_schemas-0.10.20260723`, `pydantic-2.13.4`, `rustworkx-0.18.1`.
`fvm_euler_1d_solver-0.1.0` is itself installed editable. No
`q8020_cfd_metautil`, no `qiskit_algorithms` in this venv.

Installed package metadata that constrains the upgrade:

| Package | `Requires-Python` | Key `Requires-Dist` |
|---|---|---|
| qiskit 2.5.2 | `>=3.10` | `numpy<3,>=2.0`, `scipy>=1.14`, `rustworkx>=0.15.0`, `dill>=0.3`, `stevedore>=3.0.0` |
| qiskit-aer 0.17.2 | `>=3.7` | `qiskit>=1.1.0` (no upper bound), `numpy>=1.16.3`, `scipy>=1.0`, `psutil>=5`, `python-dateutil>=2.8.0` |
| qiskit-ibm-runtime 0.49.0 | `>=3.10` | `qiskit>=2.3.0`, `pydantic>=2.13.0`, `samplomatic>=0.18.0`, `ibm-quantum-schemas<1,>=0.10.20260723`, `numpy>=1.26.2` |
| quantum_linear_solvers 0.1.0 | `~=3.12` | `qiskit>=2.0`, `numpy`, `scipy`, `ddt` |

### 1.2 sqls (`/Users/agallojr/proj/src/q8020/sqls`)

| Item | Value |
|---|---|
| branch / commit | `main` @ `9a4346a`, clean; remote `https://code.ornl.gov/olcf-qcfd/sqls.git` |
| `pyproject.toml` deps | `qiskit==2.1.2`, `qiskit-aer==0.17.1`, `numpy==2.3.3`, `scipy==1.16.2`; `requires-python >=3.10`; extras `examples = [matplotlib, qiskit-ibm-runtime]` |
| `requirements.txt` | same four pins plus `qiskit-ibm-runtime`, `matplotlib`; comments list optional `torch` and `qiskit-aer-gpu` (CUDA only) |
| how installed in fvm venv | editable, `--no-deps` (`direct_url.json`: `file:///Users/agallojr/proj/src/q8020/sqls`, `editable: true`), so it runs on fvm's qiskit 2.5.2 / aer 0.17.2 / numpy 2.5.2 / scipy 1.18.0, not its own pins |
| tests | none tracked; README line 378: "There is no linter / formatter / pytest harness"; correctness is checked by `python examples/potential_flow.py sim --nx 16` |

### 1.3 quantum_linear_solvers fork

- Installed from `https://github.com/Q8020-CFD/quantum_linear_solvers` at commit
  `66eadf0b4edcff100b20edf70a99e79cc69c5923` (`direct_url.json`). Top-level
  import name is **`linear_solvers`**, not `quantum_linear_solvers`
  (`top_level.txt`); modules: `hhl.py`, `linear_solver.py`,
  `numpy_linear_solver.py`, `matrices/{linear_system_matrix,numpy_matrix,tridiagonal_toeplitz}.py`,
  `observables/{absolute_average,linear_system_observable,matrix_functional}.py`.
- Upstream check via `gh api` (read-only, 2026-10-14): default branch `main`,
  last push 2026-03-07T20:52:49Z, tip `66eadf0b` "re-add the init constructor"
  (2026-03-07T20:52:47Z), preceded by `7a9b48f2` "port to qiskit 2.3". So the
  installed commit IS the fork tip; there is nothing newer to pull.
- Read-only local checkout `/Users/agallojr/proj/src/q8020/Z-Keep/quantum_linear_solvers`
  is also at `66eadf0` on `main` and has identical qiskit imports.

---

## 2. Latest available

PyPI JSON queried 2026-10-14 (dates are PyPI `upload_time_iso_8601`, UTC).

### 2.1 Versions

| Package | Pinned now | Latest stable | Latest pre-release | Stable gap |
|---|---|---|---|---|
| qiskit | 2.5.2 | **2.5.2** (2026-08-13T19:08:04Z) | 2.6.0rc1 (2026-10-02T22:27:15Z) | none |
| qiskit-aer | 0.17.2 | **0.17.2** (2025-09-17T13:53:56Z) | none | none |
| qiskit-ibm-runtime | 0.49.0 | **0.50.0** (2026-09-24T18:24:35Z) | none | one minor |
| qiskit-qasm3-import | 0.6.0 | **0.6.0** (2025-06-10T16:34:10Z) | none | none |

Recent release history:

| qiskit | date (UTC) | | qiskit-ibm-runtime | date (UTC) | | qiskit-aer | date (UTC) |
|---|---|---|---|---|---|---|---|
| 2.4.0 | 2026-04-16 | | 0.45.0 | 2026-01-08 | | 0.16.0 | 2025-01-09 |
| 2.4.1 | 2026-04-24 | | 0.45.1 | 2026-02-12 | | 0.16.1 | 2025-02-06 |
| 2.4.2 | 2026-06-12 | | 0.46.0 / 0.46.1 | 2026-03-23 | | 0.16.2 | 2025-03-03 |
| 2.5.0rc1 | 2026-06-18 | | 0.47.0 | 2026-05-12 | | 0.16.3 / 0.16.4 | 2025-03-04 |
| 2.5.0 | 2026-07-02 | | 0.48.0 | 2026-07-14 | | 0.17.0 | 2025-03-13 |
| 2.5.1 | 2026-07-23 | | 0.49.0 | 2026-08-10 | | 0.17.1 | 2025-06-04 |
| 2.5.2 | 2026-08-13 | | 0.50.0 | 2026-09-24 | | 0.17.2 | 2025-09-17 |
| 2.6.0rc1 | 2026-10-02 | | | | | | |

Qiskit's 2.5 cycle went rc1 -> GA in 14 days (2026-06-18 -> 2026-07-02); on that
cadence 2.6.0 GA is plausible around 2026-10-16 but was not out on 2026-10-14.
qiskit-aer has had no release for 13 months (0.17.2, 2025-09-17) and no 0.18;
its metadata caps nothing (`qiskit>=1.1.0`), and the 0.17.2 notes say its GPU
builds and tests target "Qiskit>=2.1". No open qiskit-aer issue mentions 2.5 or
2.6 incompatibility (GitHub issue search, 2026-10-14).

### 2.2 Wheel coverage (platform check for laptop vs Frontier)

- **qiskit 2.5.2** and **2.6.0rc1**: `cp310-abi3` wheels (one wheel covers
  Python 3.10 through 3.13+) for `macosx_11_0_arm64` (laptop) and
  `manylinux_2_28_x86_64` (Frontier, glibc >= 2.28), plus `macosx_10_12_x86_64`,
  `manylinux_2_28_aarch64/ppc64le/s390x`, `win_amd64`. `requires_python >=3.10`.
  2.6.0rc1 `requires_dist` is identical to 2.5.2 (`numpy<3,>=2.0`,
  `scipy>=1.14`, `rustworkx>=0.15.0`).
- **qiskit-aer 0.17.2**: per-ABI wheels `cp39`..`cp313` for
  `macosx_11_0_arm64`, `macosx_10_13_x86_64`,
  `manylinux_2_17_x86_64.manylinux2014_x86_64`, `manylinux_2_17_aarch64`,
  `ppc64le`, `i686`, `win32/win_amd64`; `cp314` wheels added 2026-02-04
  (`macosx_11_0_arm64`, `macosx_10_15_x86_64`, `manylinux_2_27_x86_64.manylinux_2_28_x86_64`,
  `win_amd64`). So Python 3.12 and 3.13 are covered on both laptop (arm64) and
  Frontier (x86_64) with CPU wheels. There is still **no ROCm wheel**; AMD-GPU
  Aer on Frontier remains a source build (lore-20260720-0004, lore-20260720-0005).
- **qiskit-ibm-runtime 0.50.0**: pure-Python `py3-none-any`; `requires_python
  >=3.10`; `requires_dist` includes `qiskit<3,>=2.3.0`, `numpy>=1.26.2`,
  `python-dateutil>=2.9.0` and a **new hard dependency `qiskit-mitigation>=0.1.1`**.

### 2.3 Deprecations and removals in the window

Sources: IBM docs release notes (redirected from `docs.quantum.ibm.com` to
`quantum.cloud.ibm.com`, fetched), GitHub release pages (fetched), and the
`releasenotes/notes/2.5/` and `releasenotes/notes/2.6/` reno files in the
`Qiskit/qiskit` repo at tags `2.5.2` and `2.6.0rc1` (listed and scanned via
`gh api`, read-only). The two IBM docs URLs given in the task both 301-redirect;
the redirected pages were fetched successfully. The per-version page for 2.6 is
not yet published on the docs site.

**qiskit 2.5.0 (2026-07-02)** - upgrade notes: minimum NumPy is now 2.0 (SPEC 0);
formal dependency policy (NumPy/SciPy follow SPEC 0, two years); Clifford+T
transpile workflow changed; MSRV 1.87. Deprecation notes (removal in 3.0):
`qs_decomposition` arguments `opt_a1`/`opt_a2` and callable
`decomposer_1q`/`decomposer_2q`; `CommutationChecker` cache API
(`cache_max_entries`, `clear_cached_commutations()`, `num_cached_entries()`).
**None of these touch our code.** 2.5.1 and 2.5.2 are bug-fix only (notably
`Statevector.evolve` no longer mutates its input; an
`Optimize1qGatesDecomposition` deadlock; a Suzuki-Trotter synthesis memory leak).

**qiskit 2.6.0rc1 (2026-10-02)** - 79 reno files; **zero `deprecations_*`
sections**. Upgrade notes: QPY format 18 (files written by 2.6 are not readable
by <= 2.5; v17-and-older files still load); `Delay` `dt` capped at 2^63-1;
**Python `multiprocessing` in `parallel_map` / `transpile` / `PassManager.run`
disabled by default on Linux** (opt back in with `QISKIT_PARALLEL=TRUE`, a
`fork`/`forkserver` start method, or `parallel = true` in the user config);
OpenQASM 2 expression evaluator moved to Rust; `DAGCircuit.metadata/name` no
longer tracked inside nested control-flow blocks; a C-API delay change. Features
include `transpile(circuit, target)` accepting a `Target` positionally. MSRV
1.89. Python support unchanged (`>=3.10`).

**Deprecations already in force on 2.5.2 that our code hits** (read from the
installed source and confirmed by the import probe in 3.4):

| Symbol | Deprecated since | Removal | Replacement (present in 2.5.2) |
|---|---|---|---|
| `qiskit.circuit.library.BlueprintCircuit` | 2.1 | Qiskit 3.0 | none; "no direct replacement other than the QuantumCircuit class" |
| `qiskit.circuit.library.PhaseEstimation` (class) | 2.1 | Qiskit 3.0 | `qiskit.circuit.library.phase_estimation` (function) |
| `qiskit.circuit.library.QFT` (class, used inside `PhaseEstimation`) | 2.1 | Qiskit 3.0 | `QFTGate` / `synth_qft_full` |
| `qiskit.circuit.library.arithmetic.exact_reciprocal.ExactReciprocal` | 2.2 | Qiskit 3.0 | `ExactReciprocalGate` |
| `qiskit.circuit.library.arithmetic.piecewise_chebyshev.PiecewiseChebyshev` | no decorator of its own in 2.5.2, but it subclasses `BlueprintCircuit` (warning fires at `piecewise_chebyshev.py:88`) and builds `PiecewisePolynomialPauliRotations` under a suppressed warning | effectively 3.0 | `PiecewiseChebyshevGate` |
| `qiskit.circuit.library.MCMT` (not used; fork uses `MCMTGate`) | 1.4 | - | `MCMTGate` |

**qiskit-ibm-runtime 0.50.0 (2026-09-24)** - deprecation notes: **"`EstimatorV2`
and `SamplerV2` are deprecated. Please use the new client-side implementations
of these primitive interfaces: `Estimator` and `Sampler` instead"**
(`qiskit_ibm_runtime.executor_sampler.Sampler`,
`qiskit_ibm_runtime.executor_estimator.Estimator`); `QuantumProgram`-related
classes moved to the `samplomatic` package; `max_execution_time` in
`EnvironmentOptions` deprecated. Removed: the deprecated `common` and
`documentation` extras. New: local mode for `Executor` with `FakeBackendV2` or
`AerSimulator` out of experimental; `dry_run`; `MeasureReset`, `XSlowGate`.
Fake provider unchanged (0.49.0 had added eight missing backends to
`FakeProviderForBackendV2.backends()`). 0.49.0: option classes became pydantic
`BaseModel` (stdlib `asdict` on them deprecated). 0.48.0: minimum qiskit 2.3.0;
differing `pub.shots` across PUBs deprecated.

**qiskit-aer 0.17.2 (2025-09-17)** - maintenance: GPU build/test fixes for
Qiskit >= 2.1, warning-format fix, Windows compile fix. 0.17.1 added
`python-dateutil` as a requirement. 0.17.0 was the Qiskit 2.0 compatibility
release. No deprecations affecting `AerSimulator(method=, device=)`,
`save_statevector`, `run(...).result().get_statevector()/get_counts()`.

---

## 3. API surface and risk table

Every `from qiskit` / `import qiskit` / `qiskit_aer` / `qiskit_ibm_runtime`
line in the three code bases, with call sites and status against the latest
releases. "Stable" means no deprecation decorator in 2.5.2 and no note in the
2.5/2.6 release notes.

### 3.1 fvm `quantum_tools.py` (and friends)

`time_solvers.py` has no qiskit import of its own; it imports `QuantumHHL` and
`QuantumSQLS` from `quantum_tools.py` (lines 260, 279). `nozzle_1d_solver.py`,
`helper_tools.py`, `checkpoint_tools.py`, `space_solvers.py` import no qiskit.

| Symbol | Where used | Status in latest (2.5.2 / 2.6.0rc1 / runtime 0.50.0 / aer 0.17.2) | Risk |
|---|---|---|---|
| `from qiskit import qpy` | L7; `qpy.load` L313, L382; `qpy.dump` L340, L463 (circuit cache, `-loadcirc`/`-savedata`) | stable; 2.6 writes QPY v18 that 2.5 cannot read | low; only bites if `.qpy` written under 2.6 is read under 2.5 |
| `from linear_solvers import HHL` | L8; `HHL(quantum_instance=self.backend)` L210 | fork API, ctor accepts `epsilon, expectation, quantum_instance`; works on 2.5.2 | medium (inherits fork's 3.0 exposure, 3.2) |
| `from qiskit.quantum_info import state_fidelity, Statevector` | L9-10; `state_fidelity` L134; `Statevector(circ_transpile)` L530 (statevector readout, `-shots 0`) | stable | low |
| `from qiskit_ibm_runtime import SamplerV2 as Sampler` | L11; `Sampler(self.backend)` L492; `.run([circ], shots=)` L494; `result[0].data.meas.get_counts()` L506 (shot readout, `-shots N`) | **deprecated in runtime 0.50.0** (warning, still functional); runtime 0.49.0 already warns on differing `pub.shots` (not our case) | medium: new `DeprecationWarning` per run; replacement is `qiskit_aer.primitives.SamplerV2` (same V2 result shape) for local Aer, or runtime `executor_sampler.Sampler` |
| `from qiskit_aer import AerSimulator` | L225 (HHL), L794 (SQLS); `AerSimulator(method=..., device='GPU')` L228/L798, CPU L231/L233/L801/L803 | stable | low |
| `from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2` | L242; `.backend(name)` L243 (`-backend fake NAME`); also `utils/list_fake_backends.py` L7 | stable; list grew in 0.49.0 | low |
| `from qiskit import transpile` | L403; `transpile(circ, backend=self.backend, optimization_level=...)` L435-444 | stable; 2.6 turns off Linux multiprocessing by default (timing only) | low on laptop; note for Frontier timing comparisons |
| `self.backend.run(circ, shots=)` | L472 (`run_circuit_iqm`, IQM path only) | `BackendV2.run`, stable | not on paper path |
| `from sqls.runtime.quantum import quantum_solve` | L816 | sqls API (3.3) | - |

Not present anywhere in fvm: `qiskit_algorithms`, `Instruction.c_if`,
`BlueprintCircuit`, `generate_preset_pass_manager`, `EstimatorV2`,
`StatePreparation`, `Initialize`, `UnitaryGate`, `Operator`.

### 3.2 installed `linear_solvers` (Q8020-CFD fork @ 66eadf0)

| Symbol | Where used | Status | Risk |
|---|---|---|---|
| `from qiskit.circuit.library import PhaseEstimation` | `hhl.py` L19; `PhaseEstimation(nl, matrix_circuit)` L426 | **deprecated 2.1, removed in 3.0**; replacement `phase_estimation()`; also triggers the deprecated `QFT` class internally | high at 3.0, none now |
| `from qiskit.circuit.library.arithmetic.piecewise_chebyshev import PiecewiseChebyshev` | `hhl.py` L20; L406 (non-exact reciprocal branch) | `BlueprintCircuit` subclass, **gone at 3.0**; replacement `PiecewiseChebyshevGate` | high at 3.0 |
| `from qiskit.circuit.library.arithmetic.exact_reciprocal import ExactReciprocal` | `hhl.py` L21; `ExactReciprocal(nl, delta, neg_vals=)` L368 (default branch) | **deprecated 2.2, removed in 3.0**; replacement `ExactReciprocalGate` | high at 3.0 |
| `from qiskit.circuit.library import BlueprintCircuit` | `matrices/linear_system_matrix.py` L19; `class LinearSystemMatrix(BlueprintCircuit, ABC)` L22 - base of `NumPyMatrix` and `TridiagonalToeplitz` | **deprecated 2.1, removed in 3.0**, no drop-in replacement | high at 3.0 (structural rewrite) |
| `from qiskit.circuit import QuantumCircuit, QuantumRegister, AncillaRegister` | `hhl.py` L18, `tridiagonal_toeplitz.py` L19, `numpy_matrix.py` L19 | stable | low |
| `from qiskit.circuit.library import MCMTGate, UGate` | `tridiagonal_toeplitz.py` L20 | stable (`MCMTGate` is the non-deprecated form) | low |
| `from qiskit.quantum_info import Operator, Statevector` | `hhl.py` L22, `numpy_linear_solver.py` L18, observables | stable | low |
| `qiskit.transpiler.passes.RemoveResetInZeroState` | `observables/matrix_functional.py` L36 (docstring example) | stable | none |
| `qiskit_algorithms` | **absent**; `linear_solver.py` L27 carries a local `AlgorithmResult` replacement (docstring mentions the name only) | - | none |

### 3.3 `sqls/src`

| Symbol | Where used | Status | Risk |
|---|---|---|---|
| `from qiskit import QuantumCircuit` | `sqls.py` L45, `core/mps_state_prep.py` L48, `core/mps_isometry.py` L51 | stable | low |
| `from qiskit.circuit.library import Initialize, UnitaryGate` | `sqls.py` L46; `Initialize(vec, normalize=True)` L70, L317; `UnitaryGate(W, check_input=False)` L225-226, L413-414; `UnitaryGate` also `mps_state_prep.py` L49/L330, `mps_isometry.py` L52/L688 | stable (no decorator in 2.5.2; 2.5/2.6 notes only fix `Initialize.gates_to_uncompute` for integer input) | low |
| `from qiskit.quantum_info import state_fidelity` | `sqls.py` L47; L433 | stable | low |
| `from qiskit.quantum_info import Statevector` (lazy) | `mps_state_prep.py` L369 | stable | low |
| `from qiskit import transpile` | `runtime/quantum.py` L15 (`transpile(qc, basis_gates=['u3','cx'], optimization_level=...)` L28, cx-count diagnostic); `mps_isometry.py` L709/L746/L752 | stable | low |
| `from qiskit_aer import AerSimulator` (lazy) | `gpu.py` L79 (`available_devices()`), L145/L148/L152 (`AerSimulator(device='GPU', **kw)`); `mps_isometry.py` L708/L722 | stable | low |
| `qc.save_statevector()` + `simulator.run(qc, shots=1).result().get_statevector().data` | `runtime/quantum.py` L155-160 (statevector mode, `-shots 0`), `mps_isometry.py` L751-753 | stable Aer API | low |
| `from qiskit_ibm_runtime import SamplerV2 as Sampler` (lazy) | `runtime/quantum.py` L202; `Sampler(simulator)` L211; `.run([qc_meas]*repeats, shots=)` L213; `result[i].data.meas.get_counts()` L222 (shots mode) | **deprecated in runtime 0.50.0** (warning) | medium; same replacement as fvm; this is ORNL's repo, so fix is a shim or an upstream request |
| `generate_preset_pass_manager`, `QiskitRuntimeService` | `examples/potential_flow.py` L405-406, L528 only | stable | not on our path |

Not present in sqls: `c_if`, `BlueprintCircuit`, `StatePreparation`,
`qiskit_algorithms`, `EstimatorV2`.

### 3.4 Import probe on the current venv (read-only, no solver run)

`.venv/bin/python -W always` importing every symbol above and instantiating the
deprecated-candidate classes at 1-2 qubits (no circuit executed):

```
qiskit 2.5.2 aer 0.17.2 runtime 0.49.0
gate-based replacements present in 2.5.2: ['ExactReciprocalGate', 'PiecewiseChebyshevGate', 'phase_estimation']
HHL ctor kwargs: ('self', 'epsilon', 'expectation', 'quantum_instance')
WARN DeprecationWarning | ExactReciprocal ... deprecated as of Qiskit 2.2 ... removed in Qiskit 3.0 ... Use ExactReciprocalGate
WARN DeprecationWarning | BlueprintCircuit ... deprecated as of Qiskit 2.1 ... removed in Qiskit 3.0   [raised from piecewise_chebyshev.py:88]
WARN DeprecationWarning | PhaseEstimation ... deprecated as of Qiskit 2.1 ... removed in Qiskit 3.0 ... Use qiskit.circuit.library.phase_estimation
WARN DeprecationWarning | QFT ... deprecated as of Qiskit 2.1 ... removed in Qiskit 3.0   [raised from phase_estimation.py:96]
n_warnings_total 5 distinct 4
```

`SamplerV2(AerSimulator())` raised no warning on runtime 0.49.0; it will on
0.50.0. `Initialize`, `UnitaryGate`, `Statevector`, `transpile`, `qpy`,
`FakeProviderForBackendV2` raised nothing.

### 3.5 Risk summary

| Risk | Affects | When | Mitigation |
|---|---|---|---|
| `SamplerV2` deprecation warning | fvm `quantum_tools.py` L11/L492; sqls `runtime/quantum.py` L202/L211; shot-mode runs only | on bump to runtime 0.50.0 | accept the warning for the paper runs (behaviour unchanged); later swap to `qiskit_aer.primitives.SamplerV2` (local Aer, same `result[i].data.meas.get_counts()` shape) |
| new transitive dep `qiskit-mitigation>=0.1.1` | fvm venv | on bump to 0.50.0 | `uv lock` pulls it; check it resolves for py3.12 (pure Python expected) |
| stale `uv.lock` -> `uv lock` reaches `code.ornl.gov` | fvm | first `uv lock` / unfrozen `uv sync` | section 4 step 1 |
| `uv sync` removes the editable `sqls` (not in lock) | fvm venv | every `uv sync` | re-install `sqls` editable `--no-deps` afterwards (August recipe) or use `uv sync --inexact` |
| HHL fork on `BlueprintCircuit` / `PhaseEstimation` / `ExactReciprocal` / `PiecewiseChebyshev` | `linear_solvers` | Qiskit 3.0 (not scheduled yet; 2.x minors every ~3 months) | port fork to `phase_estimation()`, `ExactReciprocalGate`, `PiecewiseChebyshevGate`, plain `QuantumCircuit` base; separate work item |
| QPY v18 cache incompatibility | `-loadcirc` caches | only if mixing 2.6 and 2.5 venvs on one `output/` tree | do not share `.qpy` caches across qiskit minors |
| Linux `multiprocessing` off by default in 2.6 | Frontier transpile timings | only on a 2.6 bump | set `QISKIT_PARALLEL=TRUE` to keep 2.5 behaviour, or accept and record |
| qiskit-aer 0.17.2 untested upstream against 2.6 | any 2.6 bump | 2.6 only | treat 2.6 as a scouting venv until aer ships a release that names 2.6 |
| Frontier doc drift: `docs/FRONTIER_CONDA_SETUP.md` creates `python=3.10` but `pyproject` needs `>=3.12` and the fork needs `~=3.12` | Frontier reproduction | now | fix the doc when the Frontier run is planned (not this item) |

---

## 4. Upgrade plan (ordered; commands NOT executed)

**Scope decision.** Plan A (recommended for the paper): bump only
`qiskit-ibm-runtime` 0.49.0 -> 0.50.0; keep `qiskit==2.5.2`,
`qiskit-aer==0.17.2`, `qiskit-qasm3-import>=0.6.0`. That is "latest stable" in
full. Plan B (optional, later): `qiskit==2.6.0` once GA lands, in a throwaway
venv first, because aer 0.17.2 has not been released against it. Do not put
`2.6.0rc1` in the paper stack.

All commands run from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`.
Scratch and logs go under
`/Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-qiskit-upgrade-2026-10/`
(create it first; it is a staging area, delete after filing).

```
# 0. baseline snapshot (read-only)
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
git status --short                      # expect empty
git rev-parse --short HEAD              # expect ef7f0a8b
mkdir -p /Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-qiskit-upgrade-2026-10
VIRTUAL_ENV=.venv uv pip list > /Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-qiskit-upgrade-2026-10/pip-list-before.txt
cp uv.lock /Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-qiskit-upgrade-2026-10/uv.lock.before

# 1. stale-lock pre-check: the [sqls] extra points at code.ornl.gov, which uv
#    must contact to lock. lore-20261013-0001: that host 403s after ~10 fast
#    requests and has returned 504 on pull; it was healthy again 24 h later.
git ls-remote https://code.ornl.gov/olcf-qcfd/sqls.git HEAD
#    If this fails or hangs: either wait, or (fallback, a pyproject edit) add
#      [tool.uv.sources]
#      sqls = { path = "../sqls", editable = true }
#    so the extra resolves to the local checkout (the pattern Z-Keep
#    q8020-sqls-encode already uses). Decide this together with WORKPLAN item 2.

# 2. bump the pin (the only edit)
sed -i '' 's/"qiskit-ibm-runtime==0.49.0"/"qiskit-ibm-runtime==0.50.0"/' pyproject.toml
git diff pyproject.toml                 # expect exactly one changed line

# 3. re-lock and inspect
uv lock
git diff --stat uv.lock
grep -n -A1 '^name = "qiskit-ibm-runtime"' uv.lock      # expect 0.50.0
grep -n -A1 '^name = "qiskit-mitigation"' uv.lock       # new transitive dep
grep -n -A1 '^name = "qiskit"$' uv.lock                 # still 2.5.2
grep -n -A1 '^name = "qiskit-aer"' uv.lock              # still 0.17.2
grep -n 'extra == .sqls' uv.lock                        # extra now recorded

# 4. sync the venv (note: uv sync removes packages not in the lock; the
#    editable sqls is one of them, hence step 5)
uv sync

# 5. re-install sqls editable with --no-deps (August recipe, note-20260817-0001)
VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps

# 6. verify the venv
VIRTUAL_ENV=.venv uv pip list | grep -i -E 'qiskit|sqls|linear|samplomatic|mitigation'
ls .venv/lib/python3.12/site-packages | grep -E 'dist-info|\.pth' | grep -i -E 'qiskit|sqls|linear'
#    expect: qiskit-2.5.2, qiskit_aer-0.17.2, qiskit_ibm_runtime-0.50.0,
#            qiskit_qasm3_import-0.6.0, quantum_linear_solvers-0.1.0,
#            sqls-0.1.0 + __editable__.sqls-0.1.0.pth, qiskit_mitigation-*

# 7. test ladder, section 5 (rungs 1-4 are short; rung 5 HHL needs approval)

# 8. record: copy rung outputs + pip-list-after into the agent-tmp folder, then
#    summarise in this folder (04/05 reports or a new 03a note); delete the
#    agent-tmp staging folder once filed.
```

**Rollback (any point after step 2):**

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
git checkout -- pyproject.toml uv.lock
uv sync
VIRTUAL_ENV=.venv uv pip install -e ../sqls --no-deps
VIRTUAL_ENV=.venv uv pip list | grep -i -E 'qiskit|sqls|linear'   # back to 0.49.0 stack
```

**Plan B sketch (do not run until 2.6.0 GA and until aer names it):** in a
separate directory, `uv venv /tmp/fvm-q26 && VIRTUAL_ENV=/tmp/fvm-q26 uv pip
install qiskit==2.6.0 qiskit-aer==0.17.2 qiskit-ibm-runtime==0.50.0
git+https://github.com/Q8020-CFD/quantum_linear_solvers -e ../sqls --no-deps -e .`,
then rungs 1-4 only, with `QISKIT_PARALLEL=TRUE` noted if timings are compared.
Expect the same four HHL deprecation warnings (2.6 adds none).

**Pre-existing lore and notes consulted** (grep over
`/Users/agallojr/proj/src/research-notes/bus/memory/{lore,notes}` for `qiskit`):

- `lore-20260720-0004` - no prebuilt Aer+ROCm+MPI on Frontier; source build
  (`AER_THRUST_BACKEND=ROCM`, `AER_MPI=ON`, gfx90a) required. Still true: PyPI
  has no ROCm wheel for 0.17.2.
- `lore-20260720-0005` - ROCm support is upstream in qiskit-aer (`qiskit-aer-gpu-rocm`
  package name, cmake flags), FiQCI/LUMI precedent, OLCF documents only a CPU
  conda Aer (`qiskit-aer=0.16.2`), Frontier moving to ROCm 6.2.4.
- `lore-20260720-0003` - home6 login node has no Cray PE/ROCm/MPI; probe and build
  on a Frontier compute-capable login node.
- `lore-20261013-0001` - `code.ornl.gov` 403 burst block and 504 on `git pull`;
  drives step 1 above.
- `note-20260817-0001` - the SQLS->FVM integration record: "fvm qiskit 2.5.2,
  sqls qiskit 2.1.2 pin but runs under 2.5.2"; the `--no-deps` install line
  (L93); the 150k-shot comparison case (L184). Also records that HHL's raw
  circuit crashes Aer with `AerError: unknown instruction` without transpile,
  while SQLS's `Initialize`/`UnitaryGate` are Aer-native (why SQLS skips
  transpile).
- `note-20260924-0007` - Kingston hardware runs on qiskit 2.4.1/2.4.2 with
  runtime 0.47.0/0.49.0 and aer 0.17.2 (shows 0.49.0 is already exercised on
  hardware in the CH work).
- No lore exists specifically on the 1.x -> 2.x port or on
  `ExactReciprocalGate`; the port history lives in commits (`3c20cff8` "Repin to
  qiskit 2.3", `a885ef47` "Bump quantum stack to latest qiskit 2.5 line", fork
  `7a9b48f2` "port to qiskit 2.3") and in the August result READMEs (section
  5.2). The auto-memory `q8020-euler-repo-layout.md` records that qiskit 1.2.4
  "lacks `ExactReciprocalGate`", i.e. the fork's `ExactReciprocal` -> gate
  migration is the known 1.x/2.x fault line. This report is the first written
  record of the 3.0 exposure; worth filing as lore when the upgrade is done.

---

## 5. Test ladder

### 5.1 What exists today

- **No test suite.** `git ls-files | grep -i test` is empty in fvm; sqls has no
  pytest harness (README L378). "Compilation is not a test" applies.
- fvm `scripts/`: `run_shots.py` (shot study: nelem 5, HHL, `shot_counts =
  [0, 1000, 10000, 100000]`, 5 trials each - a sweep, needs approval),
  `run_shots_parallel.py`, `submit_parallel_shots.sbatch` (Frontier). `utils/`:
  `list_fake_backends.py`. `docs/`: `DETAILED_GUIDE.md`, `FRONTIER_CONDA_SETUP.md`
  (installs `python=3.10`; stale vs `requires-python >=3.12`),
  `QUICKSTART_PARALLEL.md`.
- README example commands: `python nozzle_1d_solver.py -nelem 5 -localdt
  -linsolver HHL`, `... -shots 1024`, `... -backend fake fake_osaka -shots 1024`,
  classical `-time_scheme RK2 -cfl 0.9 -nelem 200 -localdt`, `-time_scheme BDF1
  -cfl 1e5 -nelem 200 -localdt`. README L41: "proof-of-concept for small problems
  (nelem 3-10)". The README option table (L138) still lists only LU/GMRES/HHL;
  the argparse block has SQLS.
- A prior local SQLS statevector run sits untracked in
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/output/` (nelem 5, `-shots 0`,
  3 outer steps, `-initers` > 1): fidelity 1.0 to 4e-16, `linsys_residual`
  4.8e-14 at step 0, SQLS `solve_time` 0.012 s then ~0.001-0.002 s per solve.
  Those are the statevector-mode reference numbers used below.

CLI flags (from the `argparse` block, `nozzle_1d_solver.py` L46-150):
`-nelem N` (200), `-x x0 xf` ([0 10]), `-time_scheme {BDF1,BDF2,BDF2OPT,RK1,RK2,RK3}`
(BDF1), `-linsolver {LU,GMRES,HHL,SQLS}` (LU), `-cfl` (1e10), `-iters` (2000),
`-initers` (10), `-restol` (1e-2), `-tol` (1e-10), `-localdt`, `-use_dim_form`
(turns nondim OFF), `-backend TYPE NAME` (`ideal statevector`; types ideal /
fake / real-ibm / real-iqm), `-shots` (0 = exact), `-hhl_scale {true_sol,leastsq}`,
`-loadcirc`, `-qc_gpu`, `-sqls_method {full_svd,truncated_qr,truncated_mps}`
(full_svd), `-sqls_k` (128), `-sqls_state_prep {initialize,mps}` (initialize),
`-sqls_repeats` (1), `-noshow`, `-outdir` (`output`), `-v {0,1,2}` (1),
`-savedata`, `-checkpoint`, `-resume`, `-original_max_iters`.
`QuantumSQLS.get_backend` raises `ValueError` for any `-backend` type other than
`ideal`.

### 5.2 What the August validation did

Three manual (non-sweep) laptop runs on 2026-08-17, host `MH-DT9TLJQR2V`, all the
same case `-nelem 5 -time_scheme BDF1 -localdt -shots 150000 -iters 15 -initers 1
-cfl 1e10` (nondim on), ideal statevector backend, Q8020-CFD fork `66eadf0`:

| Run dir (under `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/`) | Stack | Linsolver | Solver elapsed | Key numbers |
|---|---|---|---|---|
| `2026-08-17-qiskit23-local/trial_0` | qiskit 2.3.1 / aer 0.17.2 / runtime 0.46.1 | HHL | 817.7 s (20:11-20:25Z) | depth 638,237; gates 649,089; 14 qubits; transpile 3.9 s/iter; fidelity ~0.990 |
| `2026-08-17-qiskit25-local/trial_0` | qiskit 2.5.2 / aer 0.17.2 / runtime 0.49.0 | HHL | 859.3 s (20:56-21:09Z) | depth 596,688 (-6.5 %); gates 641,145; 14 qubits; transpile 14.3 s/iter (3.7x slower); per-iter generate 20.4 s + transpile 14.4-15.8 s + run 18.2-18.5 s; fidelity 0.988-0.997 every iter; `residual_total` 12.375 -> 6.795e-3 at iter 14; `linsys_residual` 2.12 -> 3.7e-3 |
| `2026-08-17-sqls-local-v2/trial_0` | qiskit 2.5.2 / aer 0.17.2 / runtime 0.49.0 | SQLS `full_svd`, `-sqls_repeats 1` | 0.62 s total; 0.075-0.103 s per solve | 4 qubits; ~201 CX, depth ~398 ({u3,cx}); converged in 6 Newton iters; `residual_total` 12.375 -> 1.26e-9; fidelity 0.99995-0.99998 iters 0-5, collapses to 0.451 at iter 6 (known tail artifact on a ~1e-11 update) |

Written up in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/README.md`
(with `compare_sqls_hhl.py` and two PNGs) and in the two `README.md` files of the
HHL run dirs. The SQLS trial dir has no `README.md` and no `q8020_*.json`
fragments (WORKPLAN items 4/5).

### 5.3 Proposed ladder

Short by design. Run in order; stop at the first failure. Every rung uses
`-noshow -outdir /Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-qiskit-upgrade-2026-10/rung<N>`
so nothing lands in the repo (the repo `.gitignore` would hide `*.csv`/`*.pkl`/
`*.png` anyway, but `output/` already holds an older run). System size for
`-nelem 2`: nsys = 3 x 2 = 6 -> padded to 8 -> HHL Hermitian doubling to 16
(4 data qubits, vs 32 / 5 data qubits at nelem 5); SQLS works on the 8-state
system directly (3 qubits). nelem 2 is below the README's "nelem 3-10" tested
range but the mesh has 2 ghost cells and no stencil wider than that, so it is
expected to run; if it does not, use `-nelem 3`.

`PY=/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`,
`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` first.

| Rung | Command | Expected pass | Est. wall time | Needs approval (>60 s)? |
|---|---|---|---|---|
| 1 import smoke | `$PY -W always -c 'import qiskit, qiskit_aer, qiskit_ibm_runtime, numpy, scipy; print(qiskit.__version__, qiskit_aer.__version__, qiskit_ibm_runtime.__version__, numpy.__version__, scipy.__version__); import linear_solvers, sqls; from linear_solvers import HHL; from sqls.runtime.quantum import quantum_solve; from qiskit_ibm_runtime import SamplerV2; from qiskit_aer import AerSimulator; SamplerV2(AerSimulator()); print("ok", linear_solvers.__file__, sqls.__file__)'` | prints `2.5.2 0.17.2 0.50.0 2.5.2 1.18.0`, `ok`, `linear_solvers` from the venv and `sqls` from `/Users/agallojr/proj/src/q8020/sqls/src`; the only new warning vs today is the runtime `SamplerV2` deprecation; no `ImportError` | ~5 s | no |
| 2 classical baseline | `$PY nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver LU -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir .../rung2` and, for a like-for-like reference with August, the same at `-nelem 5` | runs to completion, no exception, `residual_*.csv` `residual_total` strictly decreasing over the 3 iterations (nelem 5 reference from the SQLS run, which equals LU to ~1e-14: 12.375 -> 0.761 -> 0.0710); no qiskit import on this path | ~1-3 s each | no |
| 3 SQLS statevector | `$PY nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 0 -localdt -cfl 1e10 -iters 3 -initers 1 -sqls_method full_svd -noshow -outdir .../rung3`; repeat at `-nelem 5` | no exception; `hhl_metrics_*.csv` fidelity >= 0.999999 (reference 1.0 - 4e-16) and `linsys_residual` <= 1e-12 (reference 4.8e-14 at iter 0); `dq_*` columns `dq_lu` vs `dq_sqls` agree to ~1e-14; `qc_metadata_sqls_*` `solve_time` ~0.01 s; final `residual_total` matches rung 2 at the same nelem to 1e-10 | ~2-5 s each | no |
| 3b SQLS shots (exercises the deprecated `SamplerV2` path) | `$PY nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 10000 -sqls_repeats 1 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow -outdir .../rung3b` | no exception; a `DeprecationWarning` naming `SamplerV2` is EXPECTED under runtime 0.50.0 and is not a failure; fidelity >= 0.999 on iters 0-1 (150k-shot reference 0.99995) | ~2-5 s | no |
| 4 HHL statevector | `$PY nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver HHL -shots 0 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow -outdir .../rung4` | no exception; the four known `DeprecationWarning`s (ExactReciprocal, BlueprintCircuit, PhaseEstimation, QFT) and nothing new from qiskit itself; fidelity >= 0.98 both iters (150k-shot nelem-5 reference 0.988-0.997; statevector should be at least that); `linsys_residual` iter 1 < iter 0; `qc_metadata_*` shows `circ_qubits_transpile` 12-13 and depth well below the nelem-5 596,688 | 30-80 s for 2 iters (scaled from nelem 5: ~53 s/iter at 14 qubits; nelem 2 is one data qubit smaller) - uncertain | **yes** (borderline; or run `-iters 1` and ask only if it exceeds 60 s) |
| 4b HHL shots (SamplerV2 path for HHL) | same as 4 with `-shots 1000 -iters 1` | no exception; `SamplerV2` deprecation warning expected; fidelity >= 0.9 at 1000 shots | 20-40 s | borderline; bundle with rung 4 approval |
| 5a matched paper case, SQLS | `$PY nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow -outdir .../rung5a` | converges in 6 Newton iters; `residual_total` ~1.3e-9 (ref 1.26e-9); fidelity 0.9999-1.0 iters 0-5 with the iter-6 tail collapse (ref 0.451) allowed; `cx_count` ~200-201, depth ~397-398; solver elapsed ~1 s (ref 0.62 s); `final_results_*` rho/u/p/Mach within 1e-6 of the August CSV | ~1-2 s solver, ~10 s with startup | no (it is the paper case, but it is short) |
| 5b matched paper case, HHL | same with `-linsolver HHL` (drop the `-sqls_*` flags) | completes 15 iters; `circ_qubits_transpile` 14; `circ_depth_transpile` within +-5 % of 596,688 and gates within +-5 % of 641,145 (qiskit unchanged, so expect near-identical); fidelity >= 0.98 every iter; `residual_total` at iter 14 <= 1e-2 (ref 6.80e-3); wall 800-1000 s (ref 859.3 s); per-iter transpile ~14-16 s | **~860 s (14-15 min)** | **yes** |

Interpretation guide: rungs 1-3b prove the venv and the SQLS path (the paper's
new column) on the bumped runtime; rungs 4/4b prove HHL still builds and runs
under the same qiskit (nothing changed for it, so this is a regression guard
for the runtime bump only); rung 5 reproduces the August pair and is the only
thing that should be cited as "validated". If rung 5b is skipped for time, say
so explicitly in the write-up; 5a alone validates the SQLS column.

---

## 6. solverfw usage analysis

Vocabulary, from the first sections of the spec notes
(`/Users/agallojr/proj/src/research-notes/bus/memory/notes/`):
`note-20260807-0025` (SPEC v2: "one experiment = one cell of case x code x
backend"; elements `MainLoop`, `SolveContext`, `Backend` element, plugin
registry, encode/readout slots), `note-20260807-0027` (v2b: `ContainerIntegrator`,
`ProblemTransform`, `code.chain` metadata; baseline already landed includes
`Encoder`/`EncodeResult`, `Readout`/`ReadoutContext`, `Backend`, `REGISTRY`,
`SolveContext`), `note-20260924-0002` (canonical vocabulary, plugin catalog,
component-tree reframe), `note-20260807-0021` (brochure). The v2c addition
`QuantumLinearSystemSolver` lives in `solverfw/linsys.py`.

### 6.1 fvm `main` (`ef7f0a8b`)

```
git grep -n -i -E 'solverfw|SolveContext|MainLoop|QuantumLinearSystemSolver|q8020_cfd_metautil|metautil' main
-> no matches (exit 1)
git ls-files src            -> empty
git status --short --ignored src  -> "!! src/"   (ignored, untracked)
```

`src/` on disk holds only `__pycache__/` (dated 2026-08-17T18:26 local) with
`euler_config`, `euler_grid`, `euler_helper_tools`, `euler_integrators`,
`euler_linsys`, `euler_math_tools`, `euler_postprocess`, `euler_spatial`
`.cpython-312.pyc` files - compiled leftovers of the port, ignored via
`__pycache__/` in `.gitignore`. Nothing on `main` imports or names solverfw.
The port itself is on `archive/solverfw-v2-port` (commits `0801015d` "solverfw
v2 port under src/: stock MainLoop, SolveContext, restored quantum CLI",
`b081562e` "v2a: reconcile port drift + wire Backend element", `c60b3a05`
"v2c: HHLSolver as a QuantumLinearSystemSolver", `2b63f6f7` "Point quantum reqs
at the Q8020-CFD fork + qiskit 2.3+"), whose `src/euler_*.py` files all do
`from q8020_cfd_metautil.solverfw import ...`. `main` is 8 commits ahead of
that branch's base and shares none of its `src/` files.

### 6.2 sqls

```
git grep -n -i -E 'solverfw|metautil|SolveContext'   -> no matches (exit 1)
```

sqls is a plain library (`SQLS(A, b, ...)`, `quantum_solve(...)`); it knows
nothing of the framework.

### 6.3 installed `linear_solvers`

```
grep -rn -i -E 'solverfw|metautil|SolveContext' .venv/lib/python3.12/site-packages/linear_solvers  -> no matches
```

### 6.4 q8020-cfd-metautil (`/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`)

- Checked out: **`feature/solverfw-v2`** @ `753b97e` "solverfw v2c:
  QuantumLinearSystemSolver + section 9 acceptance sweep", clean, 4 commits ahead
  of `main` (`28b78e3` v2, `3a65797` v2a, `0246f0f` v2b, `753b97e` v2c).
  Branches: `main`, `feature/solverfw-v2`, `origin/feature/ishan_testing`.
- `src/q8020_cfd_metautil/` contains: `__init__.py`, `args.py`, `compare.py`,
  `harvest.py`, `meta_fragment.py`, `metakeys.py`, `sweep.py`,
  `sweep_postproc.py`, `sweep_worker.py`, and the package `solverfw/`
  (`backend, config, convergence, encode, grid, linsys, loop, plugins_chlbm,
  plugins_euler, postprocess, problem_type, readout, registry, spatial, state,
  time_integrator, transform, validate`). On `main`, `solverfw/` exists in its
  v1 form (9 files: `__init__, config, grid, linsys, loop, postprocess, spatial,
  state, time_integrator`) plus `docs/SPEC-solverfw.md`.
- **Does the sweeper/harvester depend on solverfw?** `harvest.py`: no
  (imports only `meta_fragment`, `metakeys`, stdlib). `sweep.py` on `main`: no
  reference at all. `sweep.py` on `feature/solverfw-v2`: an opt-in, lazy
  dependency - `_REGISTRY_SLOTS` (L2118) mirrors the slot names, and
  `_prune_expanded_cases` (L2267) imports `q8020_cfd_metautil.solverfw`
  (`REGISTRY`, `plugins_euler`, optionally `plugins_chlbm` and
  `q8020_sqls_encode.plugins`, L2288-2306) **only when a case's TOML params use
  the v2 slot vocabulary** (`_case_chain(params)` returns non-None, L2156).
  A sweep TOML like the April `fvm_cfl_sweeps.toml` never triggers it.
- **Reverse direction:** `solverfw/` does not import `sweep`, `harvest`,
  `meta_fragment` or `metakeys` (grep empty). `solverfw/registry.py` L3 states
  the intended direction: "solverfw owns the registry; metautil's ledger and the
  sweeper import it."
- metautil's `pyproject.toml` has no qiskit/sqls deps; nothing under
  `src/q8020_cfd_metautil/` imports qiskit, sqls or `linear_solvers` (the only
  hit is the lazy `import q8020_sqls_encode.plugins` above). It is installed
  editable in its own `.venv` (`q8020_cfd_metautil.__file__` resolves to the
  `src/` tree), so the running `q8020-sweep` sees whatever branch is checked out.

### 6.5 experiments harvesters

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/`:

- `fvm_euler_1d_solver_harvester.py` imports stdlib plus
  `q8020_cfd_metautil.meta_fragment` (L21). **metautil yes (meta_fragment only),
  solverfw no.**
- `backend_meta_harvester.py` imports `q8020_cfd_metautil.meta_fragment.write_backend`
  (L16) and `q8020_backend_utils.ibm.{backend, backend_meta}` (L17-18).
  **metautil yes (meta_fragment), solverfw no.** `q8020-backend-utils` itself
  imports `q8020_cfd_metautil.meta_fragment` and qiskit/aer/runtime pieces; it
  has no solverfw reference (its two "metautil" hits are docstrings about
  relocation from `meta_fragment`).
- A grep for `solverfw|SolveContext|MainLoop` over the whole
  `aux/fvm_euler_1d_nozzle/` tree hits only this folder's `WORKPLAN.md`.

### 6.6 The solverfw <-> sqls adapter

`grep -ril 'sqls' /Users/agallojr/proj/src/q8020/Z-Keep --include='*.py'` finds
exactly one package: `/Users/agallojr/proj/src/q8020/Z-Keep/q8020-sqls-encode/`
(own git repo, `main` @ `b730a75` "Add ForeignPlugin mixin", two commits).
`src/q8020_sqls_encode/{encoder,readout,validator,plugins}.py` import
`q8020_cfd_metautil.solverfw` (`Encoder`, `EncodeResult`, `Readout`,
`ReadoutContext`, `Validator`, `ValidationResult`, `PluginSpec`, ...) and,
lazily, `sqls.SQLS`, `sqls.core.mps_state_prep.extract_data_amplitudes`,
`sqls.sqls.fidelity`. Its `pyproject.toml` depends on `numpy`, `sqls`,
`q8020-cfd-metautil` with `[tool.uv.sources]` pointing both at sibling editable
checkouts. This is the rung-2 "encode-slot" wrapper of SPEC v2 section 8
(auto-memory `sqls-encode-wrapper.md`, built 2026-07-26): it exposes SQLS's
three assembly methods as framework `encode` plugins. It is a **separate,
framework route**. The direct `-linsolver SQLS` path in fvm
(`quantum_tools.QuantumSQLS` -> `sqls.runtime.quantum.quantum_solve`) does not
import it, and nothing in fvm, sqls or the fork imports it; the only consumer is
the lazy, optional import in metautil's feature-branch `sweep.py`.

### 6.7 Conclusion

The direct fvm + sqls route the paper will use does not touch solverfw at any
point: fvm `main` has no solverfw import or reference (only an ignored, stale
`src/__pycache__`), sqls and the HHL fork have none, and the two harvesters use
only `q8020_cfd_metautil.meta_fragment`, which is the metadata-fragment schema,
not the framework. solverfw appears in exactly three places, all off the paper
path: the archived `archive/solverfw-v2-port` branch of fvm (a parallel
`src/euler_*.py` implementation, never merged), metautil's `feature/solverfw-v2`
branch (where `sweep.py` imports the registry lazily and only for TOML cases
written in the v2 slot vocabulary), and the Z-Keep `q8020-sqls-encode` adapter.
The sweeper/metautil is thus a separate tool whose solverfw coupling is dormant
for our TOMLs, though note that the checked-out branch is the feature branch,
so a sweep run today executes the v2 `sweep.py` (harmless for April-style TOMLs,
but worth recording in WORKPLAN item 5). For a later solverfw route to carry
SQLS or HHL results, three things would have to be true: the Euler port on
`archive/solverfw-v2-port` would need to be rebased onto today's `main`
(it predates the SQLS wiring, the 2.5 pin and the `-sqls_*` CLI, and its
`QuantumLinearSystemSolver`-based `HHLSolver` would need an SQLS sibling or
the `q8020-sqls-encode` encode plugins wired into its `ContainerIntegrator`);
metautil `feature/solverfw-v2` would have to be merged or installed into the
fvm venv (fvm's venv has no metautil today); and the sweep TOML would have to
adopt the `code.chain` slot vocabulary so the registry pruning and chain
metadata actually engage. None of that is needed for the AIAA 2027 SQLS column.

---

## Sources

Local files read (all absolute):

- `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/{pyproject.toml,uv.lock,.python-version,.gitignore,README.md,quantum_tools.py,time_solvers.py,nozzle_1d_solver.py,mesh.py}`,
  `docs/{DETAILED_GUIDE.md,FRONTIER_CONDA_SETUP.md}`, `scripts/run_shots.py`,
  `utils/list_fake_backends.py`, `output/*.csv`, `.venv/lib/python3.12/site-packages/*`
  (dist-info metadata, `linear_solvers/`, qiskit source files named in 2.3)
- `/Users/agallojr/proj/src/q8020/sqls/{pyproject.toml,requirements.txt,README.md,src/sqls/**/*.py,examples/potential_flow.py}`
- `/Users/agallojr/proj/src/q8020/Z-Keep/quantum_linear_solvers/` and
  `/Users/agallojr/proj/src/q8020/Z-Keep/q8020-sqls-encode/` (read-only)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil/{pyproject.toml,src/q8020_cfd_metautil/**}` on `feature/solverfw-v2` and `main` (via `git grep`/`git ls-tree`)
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/{WORKPLAN.md,fvm_euler_1d_nozzle/*.py,sqls-vs-hhl-2026-08-17/README.md}`
- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-{qiskit23-local,qiskit25-local,sqls-local-v2}/` (READMEs and CSVs)
- `/Users/agallojr/proj/src/q8020/q8020-backend-utils/src/q8020_backend_utils/**`
- Library: `/Users/agallojr/proj/src/research-notes/bus/memory/lore/lore-20260720-000{3,4,5}-*.md`,
  `lore-20261013-0001-*.md`; `notes/note-20260817-0001-*.md`,
  `note-20260807-00{21,25,27}-*.md`, `note-20260924-000{2,7}-*.md`
- Auto-memory: `/Users/agallojr/.claude/projects/-Users-agallojr-proj-src/memory/{sqls-encode-wrapper,sqls-fvm-integration,solverfw-v2-location,q8020-euler-repo-layout}.md`

Network sources (all read-only, 2026-10-14):

- PyPI JSON: `https://pypi.org/pypi/{qiskit,qiskit-aer,qiskit-ibm-runtime,qiskit-qasm3-import}/json`,
  `https://pypi.org/pypi/qiskit/2.6.0rc1/json`, `https://pypi.org/pypi/qiskit-ibm-runtime/0.50.0/json`
- Qiskit SDK release notes: `https://quantum.cloud.ibm.com/docs/api/qiskit/release-notes`
  (index; redirected from `docs.quantum.ibm.com`) and `.../release-notes/2.5`
- GitHub releases: `https://github.com/Qiskit/qiskit/releases`,
  `.../releases/tag/2.5.0`, `.../releases/tag/2.6.0rc1`,
  `https://github.com/Qiskit/qiskit-aer/releases`,
  `https://github.com/Qiskit/qiskit-ibm-runtime/releases`
- qiskit-ibm-runtime release notes: `https://quantum.cloud.ibm.com/docs/api/qiskit-ibm-runtime/release-notes`
  (redirected from `docs.quantum.ibm.com`; first 100,000 of 175,292 characters read, covering 0.50.0 / 0.49.0 / 0.48.0)
- Qiskit reno source files via `gh api repos/Qiskit/qiskit/contents/releasenotes/notes/{2.5,2.6}` at tags `2.5.2` / `2.6.0rc1` (79 files for 2.6 scanned for `upgrade_*` / `deprecations_*` sections; 2.5 `deprecation_15004`, `numpy-policy`, `bump-numpy` read)
- `gh api repos/Q8020-CFD/quantum_linear_solvers` (default branch, last push, last 5 commits)
- `https://github.com/Qiskit/qiskit-aer/issues?q=is%3Aissue+qiskit+2.6` (no relevant issues)
