# verify-03-reverify: item 3 (runtime 0.50.0 bump, Aer-native shots, single re-lock) after fix-up rounds 1 and 2

VERDICT: PASS

Independent re-verification, read-only in all repos, 2026-10-15T07:44:55Z to
2026-10-15T07:56Z (UTC). Machine: 12-core macOS laptop, load average 5.9 to
7.8 during the run (other agents active); wall times below are inflated where
noted.

Targets:

- fvm `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `e13cbb1e`, working tree clean
  (`git status --porcelain` empty).
- sqls clone `/Users/agallojr/proj/src/q8020/sqls`, branch
  `local/sampler-port-2026-10` at `9a4346a` (main), one uncommitted file:
  `src/sqls/runtime/quantum.py` (+30/-15 vs main).
- Python `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
  (3.12.10).

Rules honored: no edits, no git writes, no `uv lock`/`uv sync`, no network, no
15-min matched HHL run, no `build-*.md` / `verify-*.md` / `reproduce-*.md` /
`STATUS.md` / `sqls-patches/` read. Scratch `/tmp/order2-reverify-3/` deleted
at the end.

Summary table

| # | Check | Result |
|---|-------|--------|
| 1 | sqls shots path: direct `simulator.run`, seed handling, A/B vs Aer SamplerV2 | PASS |
| 2 | fvm `quantum_tools`: shared `_run_on_backend`, no Aer primitives, runtime only on unreachable `real-*` branch, fake Bell probe | PASS |
| 3 | pyproject / uv.lock / venv / deprecation-clean import | PASS |
| 4 | Tests: unittest 96 and pytest 96, 1 opt-in skip, coverage items present | PASS |
| 5 | Gate `FVM_GATE_TESTS=1`: 7/7 at 1e-10 | PASS |
| 6 | Ladder rungs 3b / 4b / 5a under `-W error::DeprecationWarning`, module audit | PASS |
| 7 | Matched-HHL criterion (from diffs): circuit path untouched | PASS |

Findings (non-blocking): one stale README clause and one pre-existing cosmetic
error message, both listed under "Findings" below.

---

## Check 1: sqls shots path

File: `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`

Command: `git -C /Users/agallojr/proj/src/q8020/sqls diff main -- src/sqls/runtime/quantum.py`

Observed (diff, load-bearing hunks):

- `_run_shots` now reads
  `result = simulator.run([qc_meas] * repeats, shots=shots, **run_kw).result()`
  with `run_kw = {} if seed is None else {"seed_simulator": seed}`; the
  `from qiskit_ibm_runtime import SamplerV2 as Sampler` import and
  `Sampler(simulator).run(...)` are removed.
- The per-repeat loop is unchanged except for the counts accessor:
  `for bitstring, c in result[i].data.meas.get_counts().items()` became
  `for bitstring, c in result.get_counts(i).items()`; `data_mask`, `kept`,
  `data_probs /= kept`, `sqrt`, normalization, `recon /= repeats` and the
  `t_sim` timing are byte-for-byte as on main. `repeats x shots` semantics
  preserved (`[qc_meas] * repeats`, `shots=shots`).
- `quantum_solve` signature gains `*, seed=None` (keyword-only) and validates
  it immediately after the `sqls_out` / `timings` defaults, before the GPU
  swap and before `SQLS(...)` is built:
  `seed = int(operator.index(seed))` inside `try/except TypeError` raising
  `ValueError("seed must be an integer or None; got ...")`.
- `import operator` added at module top (stdlib group).

Command: `grep -n "primitives\|qiskit_ibm_runtime" /Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`
Observed: no output, rc 1. PASS.

Probe (seed validation, reproducibility, cregs), script run with
`.venv/bin/python -W error::DeprecationWarning -I /tmp/order2-reverify-3/probe_seed.py`
at 2026-10-15T07:55:05Z, 4x4 SPD system, `num_q=2`, `method='full_svd'`,
`k=2`, `repeats=2`, `shots=5000`; bad seeds passed with `A_csr=None, b=None,
simulator=None` so any heavy work would have raised a different exception
first:

```
seed=1.5: ValueError in 0.0000 s: seed must be an integer or None; got 1.5
seed='12': ValueError in 0.0000 s: seed must be an integer or None; got '12'
positional seed: TypeError (keyword-only enforced): quantum_solve() takes from 5 to 19 positional arguments but 20 were given
np.int64 seed accepted; same seed twice identical: True ; int(5)==np.int64(5): True
seed None accepted; two None runs differ: True
fidelity vs exact: seeded 0.99990, unseeded 0.99992
SQLS circuit cregs: [] num_clbits: 0 num_qubits: 2
simulator-option seed with seed=None reproducible: True
```

The `cregs: []` line matters: `Result.get_counts(i)` returns space-joined keys
when a circuit carries more than one classical register, which would break
`int(bitstring, 2)`. `SQLS()` returns a circuit with no classical register, so
`measure_all()` adds exactly one (`meas`) and the keys are plain bitstrings,
identical to the old `data.meas.get_counts()` keys. Rungs 3b and 5a (check 6)
exercise this on real SQLS circuits.

A/B probe (`/tmp/order2-reverify-3/probe_ab.py`, run 2026-10-15T07:48:30Z):
same `AerSimulator(method='statevector')`, 3-qubit circuit (h, cx, ry(0.7),
cx, measure_all), `seed=12345`, `repeats=3`, `shots=20000`. Direct
`sim.run([qc]*3, shots=20000, seed_simulator=12345).result().get_counts(i)`
vs `qiskit_aer.primitives.SamplerV2.from_backend(sim, seed=12345).run([qc]*3,
shots=20000).result()[i].data.meas.get_counts()`, compared as canonical
sorted JSON:

```
rep 0: direct  [["000", 8704], ["011", 1227], ["100", 1190], ["111", 8879]]
rep 0: sampler [["000", 8704], ["011", 1227], ["100", 1190], ["111", 8879]]
rep 0: sum direct=20000 sampler=20000 byte-identical=True
rep 1: direct  [["000", 8838], ["011", 1175], ["100", 1165], ["111", 8822]]
rep 1: sampler [["000", 8838], ["011", 1175], ["100", 1165], ["111", 8822]]
rep 1: sum direct=20000 sampler=20000 byte-identical=True
rep 2: direct  [["000", 8834], ["011", 1185], ["100", 1158], ["111", 8823]]
rep 2: sampler [["000", 8834], ["011", 1185], ["100", 1158], ["111", 8823]]
rep 2: sum direct=20000 sampler=20000 byte-identical=True
ALL byte-identical: True
same seed twice identical (direct): True
seed None twice differs: True
repeats differ among themselves: True
```

Check 1: PASS.

## Check 2: fvm `quantum_tools`

File: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py`
(HEAD `e13cbb1e`).

Observed (read, lines 468 to 507):

- `_run_on_backend(self, circ_transpile, **run_kwargs)`:
  `job = self.backend.run(circ_transpile, shots=self.nshots, **run_kwargs)`;
  `counts = job.result().get_counts()`; returns `(counts, t_run)`.
- `run_circuit_iqm` is `return self._run_on_backend(circ_transpile)`.
- `run_circuit_ibm`: `if self.backend_type in ('ideal', 'fake'): return
  self._run_on_backend(circ_transpile)`; otherwise lazy
  `from qiskit_ibm_runtime import SamplerV2 as Sampler` and
  `Sampler(self.backend).run([circ_transpile], shots=self.nshots)` (shots is
  the only run kwarg), `job.result()[0].data.meas.get_counts()`. The comment
  states the branch is unreachable because `get_backend` raises for
  `real-ibm`.
- `get_backend` (lines 214 to 293): `ideal` -> `AerSimulator`, `fake` ->
  `FakeProviderForBackendV2().backend(...)`, `real-ibm` and `real-iqm`
  branches are commented out, `else: raise ValueError("Unknown backend_type:
  ...")`.

Command: `grep -rn "primitives" --include=*.py . | grep -v /.venv/` (fvm root)
Observed: no output, rc 1. PASS.

Command: `grep -rn "SamplerV2\|qiskit_ibm_runtime" --include=*.py . | grep -v /.venv/`
Observed: `quantum_tools.py:241` (fake provider import), `:250` (commented
`QiskitRuntimeService`), `:495` (lazy `SamplerV2` on the real branch),
`helper_tools.py:19` (dist-name string), `tests/contract.py:62`,
`tests/test_output_contract.py:128` (key names), `utils/list_fake_backends.py:7`.
No other sampler use.

Probe (`real-ibm` unreachable), 2026-10-15T07:55Z, constructing
`QuantumHHL(backend_type=bt, ...)`:

```
real-ibm -> ValueError: Unknown backend_type: real-ibm. Must be one of: 'ideal', 'fake', 'real-ibm', 'real-iqm'
real-iqm -> ValueError: Unknown backend_type: real-iqm. Must be one of: 'ideal', 'fake', 'real-ibm', 'real-iqm'
```

Probe (fake branch, `/tmp/order2-reverify-3/probe_fake_bell.py`,
2026-10-15T07:48:30Z): `FakeProviderForBackendV2().backend('fake_manila')`,
`set_options(seed_simulator=7)`, 2-qubit Bell, `transpile(..., seed_transpiler=1)`,
`nshots=4000`, called through `QuantumHHL.run_circuit_ibm` with
`backend_type='fake'`:

```
counts run1: {'00': 1962, '01': 73, '10': 70, '11': 1895} sum 4000 t=0.060 s
counts run2: {'00': 1962, '01': 73, '10': 70, '11': 1895} sum 4000 t=0.014 s
sum==shots: True
two seeded runs identical: True
Bell fraction (00+11): 0.9643  dominate(>0.9): True
ideal counts: {'00': 2004, '11': 1996} iqm-alias identical: True only 00/11: True
```

(The last line is the `ideal` branch on a seeded `AerSimulator` and
`run_circuit_iqm` on the same object: identical counts, as expected from the
shared `_run_on_backend`.)

Check 2: PASS.

## Check 3: pyproject / lock / venv

File: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/pyproject.toml`

Observed: `dependencies` list `"quantum_linear_solvers"` and `"sqls"` as bare
names; `qiskit==2.5.2`, `qiskit-aer==0.17.2`, `qiskit-ibm-runtime==0.50.0`;
`[tool.uv.sources]` `sqls = { path = "../sqls", editable = true }` and
`quantum_linear_solvers = { path = "../quantum_linear_solvers", editable = true }`;
`[tool.uv] override-dependencies = ["qiskit==2.5.2", "qiskit-aer==0.17.2",
"numpy>=1.20.0,<3", "scipy>=1.7.0,<2"]`. PASS.

File: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/uv.lock` (1155 lines)

```
grep -n "git+" uv.lock            -> no output (rc 1)
grep -n "source = { git" uv.lock  -> no output (rc 1)
grep -n "editable" uv.lock        -> 284: source = { editable = "." }
                                     314: { name = "quantum-linear-solvers", editable = "../quantum_linear_solvers" },
                                     316: { name = "sqls", editable = "../sqls" },
                                     962: source = { editable = "../quantum_linear_solvers" }
                                     1088: source = { editable = "../sqls" }
versions: numpy 2.5.2 (l.481), pytest 9.1.1 (l.790), qiskit 2.5.2 (l.855),
          qiskit-aer 0.17.2 (l.878), qiskit-ibm-runtime 0.50.0 (l.908),
          qiskit-mitigation 0.1.1 (l.932), quantum-linear-solvers 0.1.0 (l.960),
          scipy 1.18.0 (l.1046), sqls 0.1.0 (l.1086)
```

Working tree: `git status --porcelain` empty (checked again after all runs).

Venv version line (2026-10-15T07:46:04Z):

```
python 3.12.10
sqls /Users/agallojr/proj/src/q8020/sqls/src/sqls/__init__.py
linear_solvers /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py
qiskit 2.5.2 (.venv site-packages)
qiskit_aer 0.17.2
qiskit_ibm_runtime 0.50.0
pytest 9.1.1
numpy 2.5.2 scipy 1.18.0
```

Command: `.venv/bin/python -W error::DeprecationWarning -c "import sqls,
linear_solvers, qiskit, qiskit_aer, qiskit_ibm_runtime, pytest; from
linear_solvers import HHL; print('ok')"`
Observed: `ok`, rc 0.

Check 3: PASS.

## Check 4: tests

Command (2026-10-15T07:47:32Z to 07:48:29Z, run alongside the two small
probes only):
`.venv/bin/python -m unittest discover -s tests -v`

```
Ran 96 tests in 56.610s
OK (skipped=1)
real 57.43  user 110.77  sys 9.50
skipped: test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference
         'gate-only (~90 s): set FVM_GATE_TESTS=1'
```

Command (2026-10-15T07:49:53Z to 07:50:50Z, run concurrently with the gate
fixture below, so wall is inflated):
`.venv/bin/python -m pytest -q -p no:cacheprovider tests`

```
95 passed, 1 skipped, 1 warning, 36 subtests passed in 56.83s
real 57.23  user 111.14  sys 10.07
```

Same 96 collected under both runners; the one pytest warning is runtime's own
`UserWarning: Properties of fake_nighthawk are not intended to represent
typical nighthawk error values` from `FakeProviderForBackendV2`.

Coverage (read, not inferred):

- Ideal HHL shots CLI case: `tests/test_hhl.py::TestHHLShotsNelem2` on
  `helpers.HHL_SHOTS_NELEM2_ARGS` (`-nelem 2 -linsolver HHL -shots 1000
  -iters 1`, `HHL_SHOTS = 1000`), `assertGreaterEqual(fidelity[0], 0.8)`,
  `meta['nshots'] == 1000`, `backend_type == 'ideal'`, 12 transpiled qubits.
  Also `tests/test_output_contract.py::TestHHLShotsOutputContract`
  (`nshots = helpers.HHL_SHOTS`, file set and columns).
- Seeded `run_circuit_ibm` Bell on ideal and fake:
  `tests/test_hhl.py::TestRunCircuitBackends` (`shots=2000`, `seed=1234`,
  `seed_transpiler` and `backend.set_options(seed_simulator=...)`,
  second run `assertEqual` to the first; ideal keys exactly `{'00','11'}`;
  fake `00+11 >= 0.8 * shots`).
- `get_code_versions` key completeness with per-entry isolation:
  `tests/test_output_contract.py::TestCodeVersionsHelper::test_failure_keeps_key_set_and_other_entries`
  patches `helper_tools._git_state` to raise `TimeoutError` only for a path
  ending `src/sqls`; asserts keys `== CODE_VERSIONS_KEYS + ['error']`,
  `cv['error'] == {'sqls': 'TimeoutError: git timed out'}`, `cv['sqls'] is
  None`, `cv['fvm']` and `cv['linear_solvers']` carry full key sets,
  `cv['numpy'] == np.__version__`.
- `diff_sha256` pinned: `_ContractMixin.assert_diff_sha256` requires
  `^[0-9a-f]{64}$` when `dirty is True` and `None` otherwise (applied to fvm
  and both siblings in `test_code_versions`; for a dirty sibling it also
  asserts equality with `sha256(git -C <checkout> diff HEAD)`);
  `TestCodeVersionsHelper::test_clean_tree_has_no_diff_hash` pins
  `_git_state` -> `('f'*40, False, None)` on a clean tree.
- Portable sibling paths: `grep -rn "/Users/" tests/*.py` -> no output (rc 1).
  `contract.SIBLING_CHECKOUTS` is resolved as `helpers.REPO.parent / dirname`;
  in `test_code_versions` an absent checkout is appended to `missing` after
  the key-set / path-on-disk / version / diff_sha256 asserts have run, and
  only then `self.skipTest(...)`, so only the commit comparison is skipped.

Live confirmation of the contract on this machine (from the rung-5a
`metadata_*.pkl`, check 6): `code_versions['sqls']` = `{commit
9a4346a7d0255cb1b59429d3b9454358a5b5bb4d, dirty True, diff_sha256
2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9,
commit_source git, version 0.1.0}`; `git -C /Users/agallojr/proj/src/q8020/sqls
diff HEAD | shasum -a 256` = `2d4c5a7c82ea...96d4e9` (exact match).
`code_versions['fvm']` = `{commit e13cbb1e54f1823f33ac12753a078a357662e9d3,
dirty False, diff_sha256 None}`.

Check 4: PASS.

## Check 5: gate fixture

Command (2026-10-15T07:50:50Z to 07:52:25Z, concurrent with the pytest run):
`FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`

```
test_fixture_files_match_recorded_sha256 ... ok
test_systems_are_well_posed ... ok
TestHHLFixture.test_nelem2_iter0_statevector_matches_reference ... ok   (8.49 s)
TestHHLFixture.test_nelem5_iter0_statevector_matches_reference ... ok   (85.27 s)
TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference ... ok  (0.02 s)
TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference ... ok  (0.01 s)
Ran 7 tests in 93.795s
OK
real 94.40  user 243.60  sys 2.96
```

Tolerance: `tests/test_gate_fixture.py` `MAX_ABS_TOL = 1e-10` (max-abs on
`dq`), reference LU at `atol=1e-12`. 7/7. PASS.

## Check 6: ladder rungs and module audit

All with `.venv/bin/python -W error::DeprecationWarning nozzle_1d_solver.py ...
-outdir /tmp/order2-reverify-3/<rung>`, from the fvm repo root. The three
rungs ran concurrently with each other and with the two in-process probes
below (wall inflated).

Rung 3b (2026-10-15T07:54:42Z): `-nelem 2 -time_scheme BDF1 -linsolver SQLS
-shots 10000 -sqls_repeats 1 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow`

```
rc=0   real 1.50 s
hhl_metrics_nelem2_statevector_shots10000.csv:
step, iter, fidelity, l2_error_abs, l2_error_rel, l2_error_normalized, linsys_residual
0, 0, 0.9999662303834319, 0.0031615593018721085, 0.005811187629879565, 0.005811187629879565, 0.034043498257881125
1, 0, 0.9998344772107041, 0.00016547568576753257, 0.012865832243238255, 0.01286583224323826, 0.002068068308858398
```

fidelity 0.99997 and 0.99983, both >= 0.999. PASS.

Rung 4b (2026-10-15T07:54:43Z): `-nelem 2 -time_scheme BDF1 -linsolver HHL
-shots 1000 -localdt -cfl 1e10 -iters 1 -initers 1 -noshow`

```
rc=0   real 9.01 s
hhl_metrics_nelem2_statevector_shots1000.csv:
0, 0, 0.9507640805112917, 0.12090794413818072, 0.2222380421319396, 0.22328761393956903, 0.5909652432413967
```

fidelity 0.9508 >= 0.8 (unseeded, as documented). PASS.

Rung 5a (2026-10-15T07:54:53Z): `-nelem 5 -time_scheme BDF1 -linsolver SQLS
-localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd
-sqls_repeats 1 -noshow`

```
rc=0   real 1.84 s
log: SOLUTION CONVERGED at iteration 6
metadata: converged True, converged_by 'residual_ratio', final_iters 6, max_iters 15
hhl_metrics_nelem5_statevector_shots150000.csv (fidelity column, steps 0..6):
0.99997635394201, 0.9999531311961429, 0.9999651820558133, 0.9999694740796065,
0.9999863865917534, 0.9999792151723881, 0.9999802559996314
residual_total: 12.3754, 0.74249, 0.063933, 0.0046037, 1.1465e-4, 4.6564e-7, 9.4236e-10
```

Seven Newton steps (0 to 6), converged at iteration 6; minimum fidelity
0.99995 >= 0.999 on every step. `final_results_nelem5_SQLS_statevector_nshots150000.csv`
vs
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/final_results_nelem5_SQLS_statevector_nshots150000.csv`
(same columns `xp, rho, u, p, Mach`, 5 rows each):

```
max|diff| xp: 0.000e+00   rho: 1.883e-11   u: 6.988e-11   p: 2.466e-11   Mach: 1.669e-10
overall max abs diff: 1.669e-10  (nondimensional)  within 1e-6: True
```

PASS.

Module audit (`/tmp/order2-reverify-3/probe_modules.py`: `runpy.run_path` of
`nozzle_1d_solver.py` with the rung argv, then scan `sys.modules`; run under
`-W error::DeprecationWarning`, 2026-10-15T07:54:55Z to 07:55:05Z):

```
[SQLS-3b] rc=0 aer.primitives=0 [] ibm_runtime=0 []
[SQLS-3b] linear_solvers loaded: True; sqls loaded: True
[HHL-4b]  rc=0 aer.primitives=5 ['qiskit_aer.primitives', 'qiskit_aer.primitives.estimator', 'qiskit_aer.primitives.estimator_v2'] ibm_runtime=307 ['qiskit_ibm_runtime', 'qiskit_ibm_runtime.accounts', 'qiskit_ibm_runtime.accounts.account']
[HHL-4b]  linear_solvers loaded: True; sqls loaded: False
```

Ideal SQLS shots run: no `qiskit_aer.primitives*`, no `qiskit_ibm_runtime*`.
PASS. (`linear_solvers` is loaded because `quantum_tools.py` imports
`from linear_solvers import HHL` at module top; it pulls in neither package.)

What the HHL path imports and why (provenance probe, per-statement
`sys.modules` scan): `import qiskit_aer` -> 0; `from qiskit_aer import
AerSimulator` -> 0; `import sqls.runtime.quantum` -> 0; `from linear_solvers
import HHL` -> 0; `import quantum_tools` -> 0; a bare `transpile(bell,
AerSimulator())` -> 312 modules (`qiskit_ibm_runtime*` plus
`qiskit_aer.primitives*`). `qiskit_ibm_runtime-0.50.0.dist-info/entry_points.txt`
registers three `[qiskit.transpiler.translation]` plugins (`ibm_backend`,
`ibm_dynamic_circuits`, `ibm_dynamic_and_fractional`, all in
`qiskit_ibm_runtime.transpiler.plugin`), so qiskit's transpiler plugin
discovery imports `qiskit_ibm_runtime` on the first `transpile()`, and
runtime itself imports `qiskit_aer.primitives`
(`qiskit_ibm_runtime/fake_provider/executor/run_quantum_program.py`,
`qiskit_ibm_runtime/debug_tools/neat.py`). This is the expected third-party
side effect named in the brief, not an fvm import (check 2 grep is empty).

Check 6: PASS.

## Check 7: re-specified matched-HHL criterion (from diffs, not run)

Commands:
`git show --stat 5dae1d89 8bdce342` and
`git diff 1481073c HEAD -- quantum_tools.py | grep -n "^@@"` (the whole
fix-up span, 1481073c is the parent of 5dae1d89).

Observed: both shots fix-up commits touch only `quantum_tools.py`
(5dae1d89: 14+/14-; 8bdce342: 22+/33-). Across the entire span the file has
exactly two hunks: `@@ -465,56 +465,45 @@` (the `run_circuit_iqm` /
`_run_on_backend` / `run_circuit_ibm` block, lines 468 to 507 at HEAD) and
`@@ -591,8 +580,8 @@` (two comment lines on the `elif self.nshots:` dispatch
in `solve_one_step`; the executed statements are unchanged).
`git diff 1481073c HEAD -- quantum_tools.py | grep "generate_circuit\|def
transpile_circuit\|transpile("` -> no output. `QuantumHHL.generate_circuit`
(line 295) and `QuantumHHL.transpile_circuit` (line 345, `seed_transpiler=42`)
are untouched, so circuit metrics (qubits, depth, gate counts) of the matched
HHL case cannot have changed. The solution numerics on the HHL statevector
path are covered by the exact gate (check 5: nelem 5 iter 0 at 1e-10 max-abs,
7/7), and the shots run path is covered by rung 4b and the Bell tests.

Check 7: PASS.

---

## Findings

1. Stale README clause (doc only, not a code defect).
   `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/README.md` lines 277 to
   278 (Dependencies): "qiskit-ibm-runtime 0.50.0 (fake / real IBM backends
   only; ideal shots runs use Aer's own `SamplerV2`)". After 5dae1d89 /
   8bdce342 ideal shots runs use `AerSimulator.run` via `_run_on_backend`;
   no Aer primitive is used anywhere in fvm. `git blame` attributes the line
   to `abf749413` (the earlier Aer-SamplerV2 round); the fix-up docs commits
   (61e7ca08, 7831d352) did not update it. README line 90 (sqls row) and
   TESTING.md lines 52 and 203 correctly say `backend.run` /
   `simulator.run`. Suggested one-line fix: "ideal shots runs call
   `AerSimulator.run` directly".
2. Pre-existing cosmetic message. `get_backend`'s `ValueError("Unknown
   backend_type: real-ibm. Must be one of: 'ideal', 'fake', 'real-ibm',
   'real-iqm'")` names the two types it rejects as valid (blame `4021a7b44`,
   2025-10-31, predates this work item). Behaviour is correct and is what
   makes the runtime branch unreachable; only the wording misleads.
3. No regression found. Both test runners agree on 96 tests; suite, gate,
   rungs and reference comparison all pass on the e13cbb1e tree with the
   uncommitted sqls port.

## Not checked, and why

- The 15-minute matched HHL case (`nelem 5`, HHL shots): excluded by the
  brief; judged from the diffs (check 7) plus the 1e-10 gate.
- `uv lock` / `uv sync` reproducibility of `uv.lock`: no lock or sync runs
  allowed; the lock was inspected statically and the venv contents were
  compared to it.
- The `real-ibm` runtime `SamplerV2` branch at run time: unreachable today
  (`get_backend` raises), no network allowed; verified by reading and by the
  constructor probe only.
- GPU path (`gpu=True`, `make_aer_simulator`): no GPU on this host; the code
  change (`seed_simulator` kwarg on `simulator.run`) applies to the rebuilt
  simulator identically, read only.
- Frontier docs (`docs/FRONTIER_CONDA_SETUP.md`, `docs/QUICKSTART_PARALLEL.md`)
  content: outside the seven checks; not read.
- `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`, `sqls-patches/`
  in this folder: excluded by the brief, not read.

Scratch `/tmp/order2-reverify-3/` (probe scripts, logs, rung output dirs)
deleted at 2026-10-15T07:57Z. No other file in this folder was created or
modified.
