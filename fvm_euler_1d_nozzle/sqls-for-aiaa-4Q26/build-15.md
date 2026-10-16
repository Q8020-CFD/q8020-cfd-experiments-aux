# Build 15 — HHL fork off the Qiskit 3.0 removals

Builder 15, order-2 pod. Work-plan item 15. Started 2026-10-15T04:33Z, finished
2026-10-15T05:05Z (UTC). Repo `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`
(import name `linear_solvers`), base `main` @ 66eadf0, remote
Q8020-CFD/quantum_linear_solvers.

## Status: ready to commit, blocked by git-gate

The git-gate PreToolUse hook on this machine refuses `git add` / `git commit` in
this clone (not on its repo list; same refusal another builder hit in the sqls
clone). Per the coordinator's instruction the port is left as the UNCOMMITTED
working tree on the branch, nothing was pushed, no configuration was touched:

- branch `feature/qiskit3-api-port` created from `main` @ 66eadf0 (HEAD is still
  66eadf0; `git status --short` shows 7 modified files, no new files)
- patch of the whole change (`git diff main`, 517 lines, 20839 bytes, sha256
  `85071b583135ac7dc84dd8cb554ec8505ea952cde51fc87a31f14d51bb6895d9`):
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-qiskit3-api-port.diff`
- `git apply --check` of that diff on a fresh detached worktree of 66eadf0 passed,
  and the applied tree was byte-identical to the working tree (`diff -rq`); the
  worktree was removed afterwards.

`git diff main --stat` (confined to `linear_solvers/**`, `test/**`, `pyproject.toml`,
`README.md`):

```
 README.md                                       |   7 ++
 linear_solvers/hhl.py                           |  66 +++++++++++--
 linear_solvers/matrices/linear_system_matrix.py | 124 +++++++++++++++++++++---
 linear_solvers/matrices/numpy_matrix.py         |  48 +--------
 linear_solvers/matrices/tridiagonal_toeplitz.py |  58 +++--------
 pyproject.toml                                  |   2 +-
 test/test_linear_solvers.py                     |  12 ++-
 7 files changed, 197 insertions(+), 120 deletions(-)
```

Commit messages I would have used, one per API family, in this order (each with
the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`):

1. `Replace BlueprintCircuit base of LinearSystemMatrix with QuantumCircuit`
   (files: `linear_solvers/matrices/linear_system_matrix.py`, `numpy_matrix.py`,
   `tridiagonal_toeplitz.py`)
2. `Build HHL phase estimation with phase_estimation() behind HHL.qpe_circuit`
   (`linear_solvers/hhl.py`, QPE part)
3. `Use ExactReciprocalGate and PiecewiseChebyshevGate for the HHL reciprocal`
   (`linear_solvers/hhl.py`, reciprocal part)
4. `Port the fork tests to ExactReciprocalGate and control(annotated=False)`
   (`test/test_linear_solvers.py`)
5. `Require qiskit 2.2 and note the Qiskit 3.0 API port in README`
   (`pyproject.toml`, `README.md`)

## What changed (file:line, per API family)

Line numbers are in the ported files.

**PhaseEstimation class -> `phase_estimation()` function, isolated as the QPE seam**
- `linear_solvers/hhl.py:19-23` imports `ExactReciprocalGate`,
  `PiecewiseChebyshevGate`, `phase_estimation` from `qiskit.circuit.library`
  (replacing the three deprecated imports at old L19-21).
- `linear_solvers/hhl.py:261-288` new method `HHL.qpe_circuit(num_clock_qubits,
  unitary) -> QuantumCircuit` (the seam, see Design notes); body is one call,
  `phase_estimation(num_clock_qubits, unitary, name="QPE")`.
- `linear_solvers/hhl.py:472` `pe_circuit = self.qpe_circuit(nl, matrix_circuit)`
  (was `PhaseEstimation(nl, matrix_circuit)` at old L426). The two appends of
  `pe_circuit` and `pe_circuit.inverse()` are unchanged.
- The deprecated `QFT` class went away with `PhaseEstimation`; `phase_estimation()`
  uses `QFTGate(n).inverse()` plus a `PermutationGate` reversal. Checked before
  porting: `Operator(QFT(n, inverse=True, do_swaps=False).reverse_bits())` equals
  the new pair exactly (max abs diff 0.0 for n = 3, 4, 5), and
  `Operator(PhaseEstimation(nl, m)) == Operator(phase_estimation(nl, m))` to
  0.0 for `TridiagonalToeplitz(2, 1, 1/3)` and a 2 x 2 `NumPyMatrix`, nl = 2, 3.

**ExactReciprocal -> ExactReciprocalGate**
- `linear_solvers/hhl.py:399` `ExactReciprocalGate(nl, delta, neg_vals=neg_vals)`
  (old L368). Appended on `ql[::-1] + [qf[0]]` as before (L481). In qiskit 2.5.2
  the old `ExactReciprocal` is already a one-gate wrapper around
  `ExactReciprocalGate`, so the unitary is identical (checked: max abs diff 0.0).
- `test/test_linear_solvers.py:21, 214-215` the test imports and instantiates
  `ExactReciprocalGate` (same arguments; a `Gate` appends like the old circuit).

**PiecewiseChebyshev -> PiecewiseChebyshevGate (non-default branch,
`HHL._exact_reciprocal = False`)**
- `linear_solvers/hhl.py:438-455` `PiecewiseChebyshevGate(reciprocal_angle, nl,
  degree, breakpoints)` (argument order differs from the old class), with
  `num_reciprocal_ancillas = reciprocal_circuit.num_qubits - nl - 1` (0 or 1
  compare qubit; the old circuit carried `nl` ancillas), `na` from that, and the
  append at L484-487 wired `ql[:] + [qf[0]] + qa[:num_reciprocal_ancillas]`.
- `linear_solvers/hhl.py:442-446` `reciprocal_angle(x)`: `arcsin(constant / x)` on
  `[a, 2^nl - 1]` and `arcsin(1)` outside. Needed to keep the old behaviour: the
  old class put identity polynomials (angle pi, i.e. amplitude 1) on the leading
  `[0, a)` and trailing intervals and fitted f only between the user
  breakpoints; the new gate fits f on every interval, including `[0, a)` where
  `arcsin(constant/x)` is a poor fit (first run gave 0.0063 vs the old 0.7993 on
  the Tridiagonal test case). With the saturating wrapper the polynomials are
  identical to the old class's and the HHL observables match the pre-port values
  to 4 decimals (see Checks).

**BlueprintCircuit -> plain QuantumCircuit base**
- `linear_solvers/matrices/linear_system_matrix.py:21` `class
  LinearSystemMatrix(QuantumCircuit, ABC)`; registers passed to
  `QuantumCircuit.__init__` from the new abstract hook `_registers(n)` (L121);
  `_check_configuration` declared abstract in the base (L133); `_reset_registers`
  (L161) now re-initialises the circuit with the new registers (public API only,
  no `CircuitData`); `_build` (L168) = check configuration, mark built, compose
  `power(1)`; the lazy-build triggers are explicit overrides at L176-227 (`data`,
  `__len__`, `__getitem__`, `decompose`, `draw`, `size`, `depth`, `count_ops`,
  `num_nonlocal_gates`, `num_connected_components`, `to_instruction`, `to_gate`).
- `linear_solvers/matrices/numpy_matrix.py:154` `_registers` returns the state
  register; the duplicated `num_state_qubits` property (whose setter called
  `BlueprintCircuit._invalidate`), the Blueprint-style `_reset_registers`
  (`self.qregs = [...]`) and the subclass `_build` are removed; `_check_configuration`
  (L135) unchanged.
- `linear_solvers/matrices/tridiagonal_toeplitz.py:244` `_registers` returns the
  state register plus `AncillaRegister(max(1, n - 1))` for n > 1; same removals as
  above (including the stray `self._ancillas = []` / `self._qubits = ...` writes);
  `_check_configuration` (L230) unchanged.

**Tests / packaging**
- `test/test_linear_solvers.py:62, 67` `matrix.power(power).control(annotated=False)`.
  Without the kwarg `Gate.control()` emits a qiskit 2.3 DeprecationWarning
  ("argument annotated is deprecated ... removed in Qiskit 3.0") that only
  surfaced once the suite ran under `-W error`. Library code never hits it:
  `phase_estimation()` calls `control(annotated=False)` and the TridiagonalToeplitz
  circuits carry their own `control` closures.
- `pyproject.toml:8` `qiskit>=2.2` (the floor at which `ExactReciprocalGate`
  exists; `phase_estimation` / `PiecewiseChebyshevGate` are 2.1).
- `README.md` one paragraph noting the floor, the APIs used, and the seam.

Untouched on purpose (item-6 hooks): clock-register sizing from
`matrix_circuit.condition_bounds()` / `eigs_bounds()` / `_get_delta`
(`hhl.py:358-396`), `NumPyMatrix.eigs_bounds` / `condition_bounds`,
`TridiagonalToeplitz.eigs_bounds` / `condition_bounds`. `linear_solver.py`,
`numpy_linear_solver.py`, `observables/`, `__init__.py` unchanged.

## Design notes

**BlueprintCircuit semantics: preserved explicitly.** The matrix classes keep
the same observable contract as before, now written out on a plain
`QuantumCircuit`:

- The body is empty at construction and built on first read; `_build` runs
  `_check_configuration` (raises `AttributeError` for a non-square / non-2^n /
  non-Hermitian NumPy matrix, or `trotter_steps < 1`), sets `_is_built`, then
  composes `power(1)` in. Setting the flag before the compose keeps the
  `compose` -> `_append` re-entry harmless.
- Triggers are the public readers listed above. Verified post-port that
  `Operator(m)`, `Statevector(m)`, `transpile(m)`, `qc.append(m, ...)`, `len(m)`,
  `m.depth()`, `m.count_ops()` all build the body and give `exp(iAt)` for
  `NumPyMatrix` (as before); `TridiagonalToeplitz`'s body is the identity, as it
  was before (its `power(1)` is an empty circuit carrying only a `control`
  closure, the content lives in `power(k).control()`); `TridiagonalToeplitz(2, 1,
  0, trotter_steps=2)` after the HHL `evolution_time` setter still raises on
  `decompose()` (trotter_steps 0) and still solves fine through HHL, exactly as
  before, because the HHL path never reads the body.
- Resizing through the `num_state_qubits` setter replaces the registers via
  `QuantumCircuit.__init__(self, *regs, name=self.name)` and drops the body
  (verified: a 4 x 4 `NumPyMatrix` resized to 1 state qubit has 1 qubit, empty
  body, unbuilt). This replaces the Blueprint `qregs` setter, which on a plain
  2.5.2 `QuantumCircuit` only relabels registers and would not add qubits.
- Two pre-existing quirks are deliberately kept, not fixed: parameter setters
  other than `num_state_qubits` do not drop an already-built body (upstream
  never called `_invalidate` there), and `TridiagonalToeplitz.inverse()` raises
  `ValueError: cannot convert float NaN to integer` (negative evolution time in
  the trotter-steps sqrt) on `main` as well. Only visible difference: `copy()` of
  an unbuilt matrix is unbuilt (Blueprint built first); a copy of a built one is
  built.
- Removed: `BlueprintCircuit._invalidate` (single in-repo caller was the removed
  duplicate `num_state_qubits` setters), the subclass `_build` overrides (identical
  to the base), the Blueprint-era `_reset_registers` bodies.

**QPE seam.** `HHL.qpe_circuit(self, num_clock_qubits: int, unitary:
QuantumCircuit) -> QuantumCircuit`, `hhl.py:261-288`. Contract (in the
docstring): input is the clock size `nl` as fixed by `construct_circuit` from
the kappa / eigenvalue bounds, and the Hamiltonian-simulation circuit providing
`power(k)` with a `control()`; output is a circuit on `nl + unitary.num_qubits`
qubits, clock first, then the unitary's qubits in its own order (state, then its
ancillas), invertible with `QuantumCircuit.inverse()` because
`construct_circuit` appends it before and its inverse after the conditioned
rotation. A LuGo QPE replaces it by overriding this one method (subclass or
monkeypatch); the clock-register sizing, the controlled-power source and the
reciprocal wiring stay where they are. Default body is the qiskit function; no
behaviour change (unitary identical to the old class, see above).

## Checks

Python: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
(qiskit 2.5.2, qiskit-aer 0.17.2, numpy 2.5.2, scipy 1.18.0, ddt 1.7.2 installed).
"BEFORE" = `main` @ 66eadf0 in a detached worktree `/tmp/order2-build-15/main-wt`;
"AFTER" = the clone's working tree. In every run `linear_solvers.__file__` was
printed from the same interpreter invocation and pointed at the intended tree
(the installed copy in site-packages is a plain, non-editable copy of 66eadf0, so
`PYTHONPATH` wins).

### Deprecation warnings

BEFORE (main): import alone is clean (the decorators are on `__init__`), but
`HHL().construct_circuit(...)` plus `Statevector` under
`warnings.simplefilter('always', DeprecationWarning)` emits 10 DeprecationWarnings
from 4 symbols: `BlueprintCircuit`, `PhaseEstimation`, `QFT`, `ExactReciprocal`.
Under `-W error::DeprecationWarning` the construct fails on `BlueprintCircuit`.

AFTER (clone), all with `PYTHONPATH=/Users/agallojr/proj/src/q8020/quantum_linear_solvers`:

- `python -W error::DeprecationWarning -c "import linear_solvers; from
  linear_solvers import HHL, NumPyMatrix, TridiagonalToeplitz"` -> OK.
- `HHL().solve(...)` on `TridiagonalToeplitz(2, 1, 1/3)` and on a 4 x 4 NumPy
  system, exact and non-exact reciprocal, under `-W error::DeprecationWarning`
  -> OK.
- The full fvm HHL statevector solve on the archived nelem-5 and nelem-2 systems
  (`metrics.py`, i.e. `QuantumHHL.generate_circuit` + `transpile_circuit` +
  `LinearSystemSolver.hhl_solve`) ran under `-W error::DeprecationWarning`,
  exit 0 (the AFTER rows of the metrics table below come from those runs).
- The fork's own suite under `-W error::DeprecationWarning`: 21/21 OK.
- A leftover grep over the repo for `PhaseEstimation`, `ExactReciprocal`,
  `PiecewiseChebyshev`, `BlueprintCircuit`, `_invalidate`, `self.qregs =`,
  `self._qubits` finds only docstring / comment mentions of the former names.

### Gate (acceptance 3), verbatim

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && PYTHONPATH=/Users/agallojr/proj/src/q8020/quantum_linear_solvers FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
# module check in the same env first:
#   .venv/bin/python -c "import linear_solvers; print(linear_solvers.__file__)"
#   -> /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py
# start 2026-10-15T04:58:13Z, rc=0, wall 94 s
test_archived_sources_unchanged ... 0.03 s ok
test_fixture_files_match_recorded_sha256 ... 0.01 s ok
test_systems_are_well_posed ... 0.00 s ok
TestHHLFixture.test_nelem2_iter0_statevector_matches_reference ... 7.80 s ok
TestHHLFixture.test_nelem5_iter0_statevector_matches_reference ... 86.12 s ok
TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference ... 0.07 s ok
TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference ... 0.01 s ok
----------------------------------------------------------------------
Ran 7 tests in 94.039s

OK
```

Note on scope: the fixture holds HHL references for nelem-5 iter 0 and nelem-2
iter 0 only; `system_Ab_nelem5_iter6.pkl` is in the fixture but only enters
`test_systems_are_well_posed` (no stored HHL reference for it), so "iter 6" in
the task statement has no 1e-10 comparison to run. Measured max-abs against the
stored references from my own runs: nelem 2: 9.2e-16 (BEFORE 8.3e-16); nelem 5:
3.6e-14 (BEFORE 5.0e-14). Fidelities agree to 1e-15.

Default fvm suite, same PYTHONPATH:
`.venv/bin/python -m unittest discover -s tests -v` -> `Ran 82 tests in 47.117s
OK (skipped=1)` (the skip is the gate-only nelem-5 HHL test), rc 0, wall 49 s,
start 2026-10-15T04:59:47Z.

### Fork test suite (acceptance 4)

`PYTHONPATH=<tree> python -m unittest test.test_linear_solvers -v`, run from the
tree being tested:

| | tree | flags | result | wall |
|---|---|---|---|---|
| BEFORE | `/tmp/order2-build-15/main-wt` (66eadf0) | `-W ignore::DeprecationWarning` | Ran 21 tests, OK | 5.8 s (7 s incl. startup) |
| AFTER (first) | clone | `-W error::DeprecationWarning` | 20 ok, 1 ERROR (`test_matrices_3`: the test's own `control()` call raised the qiskit 2.3 `annotated` DeprecationWarning) | 5.8 s |
| AFTER (final) | clone | `-W error::DeprecationWarning` | Ran 21 tests, OK | 5.7 s (6 s incl. startup) |

21 = 10 `test_hhl` cases + 3 `test_matrices` + 2 `test_eigs_bounds` + 2
`test_absolute_average` + 2 `test_matrix_functional` + 2 `test_exact_reciprocal`.
No pre-existing failures; after >= before (21 >= 21).

### Circuit metrics (acceptance 5)

Built the way `quantum_tools.QuantumHHL` does it: `scale_Ab_by_spectral_radius`
-> `convert_to_pow2` -> `convert_system_to_herm` -> `HHL(quantum_instance=
AerSimulator(method='statevector')).construct_circuit(A_herm, b_herm)` ->
`measure_all()` -> `transpile(circ, backend)` (the `backend_type == 'ideal'`
branch, `quantum_tools.py:443`, default optimization level, no seed). "gates"
is `sum(count_ops().values())` including the barrier and the measurements, as
the fvm metadata counts it; "cx" is `count_ops()['cx']`. Script:
`/tmp/order2-build-15/metrics.py` (deleted with the scratch dir; it is 70 lines
of the calls above plus `tests.helpers.make_linsys_solver` / `hhl_solve` for the
timed solve).

| system | qubits | depth (orig) | gates (orig) | depth (transpiled) BEFORE -> AFTER | gates (transpiled) BEFORE -> AFTER | cx BEFORE -> AFTER |
|---|---|---|---|---|---|---|
| nelem 2, `system_Ab_nelem2_iter0.pkl` (6 x 6 -> 8 -> 16 Hermitian) | 12 -> 12 | 5 -> 5 | 17 -> 17 | 68964 -> 68964 | 74799 -> 74786 (-13) | 64 -> 64 |
| nelem 5, `system_Ab_nelem5_iter0.pkl` (15 x 15 -> 16 -> 32 Hermitian) | 14 -> 14 | 5 -> 5 | 19 -> 19 | 596688 -> 596688 | 641082 -> 641121 (+39) | 128 -> 128 |

Where the shift is (transpiled `count_ops` deltas AFTER - BEFORE): nelem 2:
cp -5, crx +67, cry +18, crz -151, rxx -58, ryy -26, rzx -44, rzz +199, u1 -13,
u2 -168, u3 +168; nelem 5: cp +378, crx +274, cry -383, crz -626, rxx -52,
ryy -174, rzx +89, rzz +494, u1 +39, u2 -455, u3 +455. ccx, cu, cx, h, ry, p,
measure counts are identical. These come from the different synthesis of the
same unitaries (inverse QFT as `QFTGate` + `PermutationGate` vs the old
`QFT(do_swaps=False).reverse_bits()` gate, and gate-level vs circuit-level
wrapping of the QPE block changes what the Aer-basis unrolling sees); depth, CX
and qubit counts are unchanged. The untranspiled circuit's op names change from
`1/x` to `ExactReciprocal` (same gate).

Wall times, one nelem-5 statevector solve (`LinearSystemSolver.hhl_solve`, which
includes circuit generation, transpile, `Statevector`, and the classical LU
references), laptop, nothing else running:

| | generate | transpile | `hhl_solve` total | nelem-2 `hhl_solve` |
|---|---|---|---|---|
| BEFORE | 19.86 s | 14.44 s | 91.84 s | 7.14 s |
| AFTER | 18.45 s | 14.00 s | 86.83 s | 6.84 s |

(Single runs; the gate fixture's own timing of the same solve was 86.12 s, and
the stored reference was generated in 86.8 s, so the differences are noise.)

### Non-exact reciprocal branch (not on the paper path)

`HHL._exact_reciprocal = False`, same tiny cases BEFORE -> AFTER: 4 x 4 NumPy
system `AbsoluteAverage` 0.0152 -> 0.0152 (classical 0.0526, the branch is a
coarse approximation on both sides); `TridiagonalToeplitz(2, 1, 1/3)`
`MatrixFunctional(1, 1/2)` 0.7993 -> 0.7993 (classical 0.9316). Circuit width
11 -> 8 qubits (the gate needs one compare qubit instead of nl ancillas).

## Commands (exact)

```
# setup
git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers checkout -b feature/qiskit3-api-port 66eadf0
git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers worktree add --detach /tmp/order2-build-15/main-wt main
PY=/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python
CL=/Users/agallojr/proj/src/q8020/quantum_linear_solvers

# PYTHONPATH precedence
PYTHONPATH=$CL $PY -c "import linear_solvers; print(linear_solvers.__file__)"

# fork tests BEFORE (cwd main-wt), 7 s
PYTHONPATH=/tmp/order2-build-15/main-wt $PY -W ignore::DeprecationWarning -m unittest test.test_linear_solvers -v
# fork tests AFTER (cwd clone), 6 s
PYTHONPATH=$CL $PY -W error::DeprecationWarning -m unittest test.test_linear_solvers -v

# deprecation probe AFTER
PYTHONPATH=$CL $PY -W error::DeprecationWarning -c "import linear_solvers; from linear_solvers import HHL, NumPyMatrix, TridiagonalToeplitz"

# metrics BEFORE / AFTER (cwd fvm repo), nelem 2 ~12 s, nelem 5 ~2 min each
PYTHONPATH=/tmp/order2-build-15/main-wt:/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver $PY -W ignore::DeprecationWarning /tmp/order2-build-15/metrics.py 5
PYTHONPATH=$CL:/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver $PY -W error::DeprecationWarning /tmp/order2-build-15/metrics.py 5

# gate (94 s) and default suite (49 s), cwd fvm repo
PYTHONPATH=$CL FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
PYTHONPATH=$CL .venv/bin/python -m unittest discover -s tests -v

# patch + apply check
git -C $CL diff main > .../sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-qiskit3-api-port.diff
git -C $CL worktree add --detach /tmp/order2-build-15/apply-wt 66eadf0
git -C /tmp/order2-build-15/apply-wt apply --check .../UNCOMMITTED-qiskit3-api-port.diff
git -C $CL worktree remove --force /tmp/order2-build-15/apply-wt
```

The gate fixture was run once (budget was 3). Nothing was installed; the fvm venv
is unchanged. No other repo was modified.

## Open doubts

1. **Qiskit `PiecewiseChebyshevGate` quirk.** `_build_polynomials` derives
   `num_state_qubits = self.num_qubits - 1`, ignoring the compare qubit, so with
   more than one interval it appends one extra identity polynomial (4 polynomials
   for 3 intervals in our case). It is harmless here (the extra entry maps to the
   unreachable value 2^nl) but worth knowing if anyone turns the non-exact
   reciprocal on; the saturating `reciprocal_angle` is what keeps the old
   numbers, and whether the old saturation (amplitude 1 below the first
   breakpoint a = N^(2/3)) is the behaviour one actually wants is an upstream
   design question, not changed here.
2. **Lazy-build trigger list.** Twelve public readers are covered (same set as
   `BlueprintCircuit` minus the private `_append` / `compose` overrides and the
   parameter accessors, which the matrices do not need). A qiskit code path that
   reads `circuit._data` directly without touching any of them would see an
   empty body; none of `Operator`, `Statevector`, `transpile`, `append`, `len`,
   `depth`, `count_ops` does in 2.5.2, and the HHL path never reads the body at
   all, so this cannot affect fvm numbers.
3. **`QuantumCircuit.__init__` re-entry** in `_reset_registers` resets metadata
   and global phase along with the registers. The setter is never used to
   actually change the size in-repo or in fvm (NumPyMatrix re-assigns the same
   value), so this is a documented edge, not a live path.
4. **Gate scope.** As noted, there is no stored HHL reference for nelem-5 iter 6
   in `tests/data`, so that system is checked only for well-posedness.
5. **Transpiled gate counts moved by -13 / +39** for identical depth and CX.
   Expected and documented; if the paper quotes "total gates" for the HHL control
   rows, the AFTER numbers (74786 / 641121) are the ones to use from now on.

## Fix-up round (2026-10-15T06:20Z to 2026-10-15T06:40Z)

Nine findings from the independent code review / verifier, all implemented in
the uncommitted working tree on `feature/qiskit3-api-port` (HEAD still 66eadf0,
nothing committed or pushed, no configuration touched, fvm venv unchanged; the
fork is now installed editable in the fvm venv, so no `PYTHONPATH` is needed and
`linear_solvers.__file__` resolves to
`/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py`).
Line numbers are in the fixed files.

| # | fix | where |
|---|---|---|
| F1 | `_build` computes `power(1)` before setting `_is_built`; the flag is set only for the compose (the hooks below re-enter it) and the `except` path calls `_invalidate()` and re-raises, so a failing build raises on every read instead of leaving a silent empty body. | `linear_solvers/matrices/linear_system_matrix.py:184-199` |
| F2 | Build-before-mutate hooks restored: `_append` (covers `append`) and `compose` build first; `parameters` / `num_parameters` readers added too. The full `BlueprintCircuit` 2.5.2 hook list is `data`, `decompose`, `draw`, `num_parameters`, `parameters`, `_append`, `compose`, `inverse`, `__len__`, `__getitem__`, `size`, `to_instruction`, `to_gate`, `depth`, `count_ops`, `num_nonlocal_gates`, `num_connected_components`, `copy_empty_like`, `copy`, plus the `qregs` setter; all are mirrored except `inverse` (both subclasses override it to return a new matrix object, no body read) and `qregs` (replaced by `_reset_registers`, since the plain 2.5.2 setter only relabels registers). | `linear_system_matrix.py:201-224` |
| F3 | `copy_empty_like()` returns a plain `QuantumCircuit` on the same registers with the global phase and a deep copy of the metadata (as `BlueprintCircuit` did), so `reverse_ops`, `remove_final_measurements`, `reverse_bits`, `assign_parameters` rebuild on an empty circuit without re-triggering the lazy build; `copy()` builds first and returns a same-class, built copy (fresh body via `QuantumCircuit.__init__` on the same registers plus `compose`, no `_data` sharing). | `linear_system_matrix.py:226-250` |
| F4 | `_invalidate()` added to the base (`clear()`, phase 0, flag off; no-op before the first build, which also covers the subclass setters that run before the `QuantumCircuit` part of `__init__`). Called from every body-changing setter: base `tolerance` (L99) and `evolution_time` (L114); `NumPyMatrix.matrix` (`numpy_matrix.py:94`); `TridiagonalToeplitz.main_diag` (L116), `off_diag` (L130), `trotter_steps` (L168); the Tridiagonal `evolution_time` setter invalidates through `trotter_steps`, which it always sets. | `linear_system_matrix.py:174-182` and the setters listed |
| F5 | `HHL(..., exact_reciprocal: bool = True)` constructor switch (`hhl.py:94, 119`; attribute `_exact_reciprocal` kept for callers that set it). The Chebyshev reciprocal construction moved to `HHL._chebyshev_reciprocal(nl, constant, kappa, nb) -> PiecewiseChebyshevGate` (`hhl.py:295-345`, documented) so a test can reach it. Two new fork tests: `TestReciprocal.test_chebyshev_reciprocal_matches_legacy` (2 cases, `test/test_linear_solvers.py:249`) builds the legacy `PiecewiseChebyshev` (import guarded, warnings suppressed; skips on Qiskit >= 3.0) with the same degree / user breakpoints and asserts the target-qubit rotation amplitude for every clock value equal to 1e-10; `TestLinearSolver.test_hhl_chebyshev_reciprocal` (2 cases, L431) runs `HHL(exact_reciprocal=False).solve` end to end and checks the fidelity of the solution read off the flag qubit against the classical solution. | `hhl.py`, `test/test_linear_solvers.py` |
| F6 | Deleted the byte-identical subclass copies of the `tolerance` / `evolution_time` property pairs in `numpy_matrix.py` (and the redundant re-sets of `num_state_qubits` / `tolerance` / `evolution_time` after `super().__init__`) and the `tolerance` pair in `tridiagonal_toeplitz.py`; the Tridiagonal `evolution_time` setter stays because it also recomputes `trotter_steps`. The base setters now carry the invalidation (F4). | `numpy_matrix.py:62-77`, `tridiagonal_toeplitz.py:118-150` |
| F7 | README L10 and L21 now say Qiskit >= 2.2 (fork URL changed to Q8020-CFD); `setup.py:5` comment `# requires Qiskit >= 2.2`. | `README.md`, `setup.py` |
| F8 | `AncillaRegister(num_state_qubits - 1)` under the `> 1` guard. | `tridiagonal_toeplitz.py:241` |
| F9 | Blank line between the stdlib and third-party import groups. | `numpy_matrix.py:15-18` |
| note | Docstring examples in both matrix classes now call `power(k).control(annotated=False)`. | `numpy_matrix.py:41-46`, `tridiagonal_toeplitz.py:53-58` |

### Fidelity on the Chebyshev path: why the pin is not 0.99 everywhere

The two end-to-end cases the review named give, with the legacy-faithful
reciprocal (identical to the old class by the agreement test):

| case | clock values of the eigenvalues (a = 6, nl = 4, delta = 0.25) | fidelity, Chebyshev | fidelity, exact | pinned |
|---|---|---|---|---|
| `TridiagonalToeplitz(2, 1, 1/3)`, rhs [1, -2.1, 3.2, -4.3] | 2.00, 3.45, 5.24, 6.68 (one fitted, three saturated) | 0.9897 (0.9948 unsquared) | 0.9998 | >= 0.98 |
| NumPy 4 x 4 [[4,1,0,0],...], rhs [1, 0, 0, 0] | 2.00, 2.84, 3.88, 4.72 (all saturated) | 0.5756 | 0.9990 | >= 0.5 |

Fidelity here is the squared normalised overlap of the solution amplitudes
(flag qubit 1, other work qubits 0) with the classical solution. The
verifier's 0.995 matches the UNSQUARED overlap of the Toeplitz case (0.9948).
The 4 x 4 case cannot honestly be pinned at 0.99: with `delta = 0.25` every
eigenvalue maps to a clock value below the first breakpoint `a = round((2^nl)^(2/3)) = 6`,
where the legacy approximation saturates the rotation at `arcsin(1)`, so the
circuit returns ~b instead of A^-1 b. That is upstream's (Carrera Vazquez)
breakpoint choice meeting this fork's `_get_delta` scaling, present on `main`
before the port and reproduced exactly; even a well-conditioned 4 x 4 whose
eigenvalues land exactly at a (checked, off-diagonal 0.1) only reaches 0.978 to
0.990. The row is pinned at the measured value so a future change of the
saturation shows up; the exact reciprocal (the paper path, default) is >= 0.999
on both rows. Fixing the non-exact path's breakpoint / scaling mismatch would be
a behaviour change outside this port.

### Probe output (same script before and after; the F-numbers are the review's)

`/tmp/order2-fixup-15/probe.py` (deleted with the scratch dir): NumPyMatrix on a
2 x 2 and a 4 x 4 (A = [[4,1,0,0],...]), `TridiagonalToeplitz(2, 1, 1/3)`,
evolution time t = 0.7 (dimensionless), run under
`warnings.simplefilter("error", DeprecationWarning)`.

BEFORE the fix-up (2026-10-15T06:22Z):
```
F1 failing build, two reads: ['raises CircuitError', 'data ok len=0'] | _is_built True
F2 append on unbuilt -> op order: ['x', 'circuit-42']
F2 compose on unbuilt -> op order: ['x', 'circuit-47']
F2 append(gate) on unbuilt -> op order: ['circuit-46', 'circuit-53']
F3 copy_empty_like on unbuilt: type NumPyMatrix len 1 qubits 2
F3 reverse_ops on unbuilt: size 2 max|U-exp(iAt)| 1.258e+00
F3 remove_final_measurements(inplace=False) on unbuilt: size 1 max|U-exp(iAt)| 0.000e+00
F3 reverse_bits on unbuilt: size 1 max|U-P exp(iAt) P| 0.000e+00
F3 assign_parameters({}) on unbuilt: size 1 max|U-exp(iAt)| 0.000e+00
F3 copy() on unbuilt: type NumPyMatrix built False size 1 max|U-exp(iAt)| 0.000e+00 | source body shared? False
F4 NumPy evolution_time: body==exp(2iAt) max diff 1.258e+00
F4 NumPy matrix: body==exp(i 2A t) max diff 1.258e+00
F4 NumPy tolerance: invalidated False rebuilt==exp(iAt) 0.000e+00
F4 Tridi setters invalidate: {'main_diag': False, 'off_diag': False, 'trotter_steps': False, 'evolution_time': False, 'tolerance': False}
F4 Tridi body after build is identity: True qubits 3
resize 4x4 -> 1 state qubit: qubits 1 built False
copy.copy keeps class: NumPyMatrix
```
(In F2 `append(gate)` both names are auto-generated `circuit-N`; the first is
the user's gate, i.e. inverted. `remove_final_measurements(inplace=False)` came
out right here because its `copy()` path happened to carry the unbuilt flag; the
verifier saw size 2 on another path.)

AFTER the fix-up (2026-10-15T06:28:07Z), probe rc 0:
```
F1 failing build, two reads: ['raises CircuitError', 'raises CircuitError'] | _is_built False
F2 append on unbuilt -> op order: ['circuit-43', 'x']
F2 compose on unbuilt -> op order: ['circuit-48', 'x']
F2 append(gate) on unbuilt -> op order: ['circuit-54', 'circuit-47']
F3 copy_empty_like on unbuilt: type QuantumCircuit len 0 qubits 2
F3 reverse_ops on unbuilt: size 1 max|U-exp(iAt)| 0.000e+00
F3 remove_final_measurements(inplace=False) on unbuilt: size 1 max|U-exp(iAt)| 0.000e+00
F3 reverse_bits on unbuilt: size 1 max|U-P exp(iAt) P| 0.000e+00
F3 assign_parameters({}) on unbuilt: size 1 max|U-exp(iAt)| 0.000e+00
F3 copy() on unbuilt: type NumPyMatrix built True size 1 max|U-exp(iAt)| 0.000e+00 | source body shared? False
F4 NumPy evolution_time: body==exp(2iAt) max diff 0.000e+00
F4 NumPy matrix: body==exp(i 2A t) max diff 0.000e+00
F4 NumPy tolerance: invalidated True rebuilt==exp(iAt) 0.000e+00
F4 Tridi setters invalidate: {'main_diag': True, 'off_diag': True, 'trotter_steps': True, 'evolution_time': True, 'tolerance': True}
F4 Tridi body after build is identity: True qubits 3
resize 4x4 -> 1 state qubit: qubits 1 built False
copy.copy keeps class: NumPyMatrix
```

### Tests and gate

- Strict import: `python -W error::DeprecationWarning -c "import linear_solvers;
  from linear_solvers import HHL, NumPyMatrix, TridiagonalToeplitz"` -> OK.
- Fork suite, strict, from the clone: `python -W error::DeprecationWarning -m
  unittest discover -s test -v` -> `Ran 25 tests in 6.244s OK` (21 + 4 new;
  wall 7 s, 2026-10-15T06:31:02Z). A first run with the 0.99 pin failed the two
  end-to-end rows (0.9897 and 0.5756, see above); the pins were set to the
  measured, documented values and the suite re-run.
- Gate, once (`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver &&
  FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`, no
  `PYTHONPATH`; module check printed the clone path): start 2026-10-15T06:31:24Z,
  `Ran 7 tests in 92.592s OK` (HHL nelem-2 7.68 s, HHL nelem-5 84.87 s, SQLS
  0.03 s / 0.00 s, provenance 3 x 0.00 s).
- Default fvm suite (`.venv/bin/python -m unittest discover -s tests -v`): start
  2026-10-15T06:32:57Z, `Ran 82 tests in 59.767s OK (skipped=1)`, rc 0.
- Style: every added line <= 88 characters except two README prose lines (L10,
  inside the installation code fence, 94 chars; L21, a pre-existing 266-char
  paragraph in which only the version words changed); no trailing whitespace.

### Patch

Regenerated: `git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers diff
main > .../fork-patches/UNCOMMITTED-qiskit3-api-port.diff` -> 949 lines, 37688
bytes, sha256 `98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f`.
`git diff main --stat`: 8 files, 423 insertions, 208 deletions (`setup.py` is
the one file added to the set since the first round). No untracked files
(`git ls-files --others --exclude-standard` is empty; the clone does contain the
git-ignored `quantum_linear_solvers.egg-info/` from the editable install and a
`.pytest_cache/`, neither mine, neither in the patch). `git apply --check` on a
fresh detached worktree of 66eadf0 passed and the applied tracked tree was
identical to the working tree; worktree removed. Commit messages as listed in
the first round still apply, with the fix-up folded into messages 1 (base
class), 3 (reciprocal switch and helper), 4 (tests) and 5 (README / setup.py).
Scratch `/tmp/order2-fixup-15` deleted.

## Committed (2026-10-16T00:28Z to 2026-10-16T00:35Z)

The operator authorized commits in the clone; the git-gate accepted them. The
former working tree was committed on `feature/qiskit3-api-port` in the
per-API-family split recorded above; both fix-up rounds are folded into the
commits they belong to (base class -> 1, reciprocal switch and helper -> 3,
tests -> 4, README / setup.py -> 5) rather than a separate fix-up commit.
Nothing pushed; `main` untouched at 66eadf0. Each `git add` / `git commit` was a
literal `git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers ...` with
absolute paths; `hhl.py` was committed in two steps (an intermediate QPE-only
version generated from `main` for commit 2, then the final file for commit 3,
restored byte-identical from a saved copy).

`git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers log --oneline
main..feature/qiskit3-api-port` (author Andy Gallo, 2026-10-16T00:28:34Z to
00:30:21Z; each message one line plus the
`Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` trailer):

```
9d1d7bb Require qiskit 2.2 and note the Qiskit 3.0 API port in README and setup.py
1164a45 Port fork tests to ExactReciprocalGate and add Chebyshev reciprocal tests
90b177a Use ExactReciprocalGate and PiecewiseChebyshevGate for the HHL reciprocal
3fe7192 Build HHL phase estimation with phase_estimation() behind HHL.qpe_circuit
e7be361 Replace BlueprintCircuit base of LinearSystemMatrix with QuantumCircuit
```

| commit | files | fork tests on that commit's tree (detached worktree) |
|---|---|---|
| e7be361 | `linear_solvers/matrices/{linear_system_matrix,numpy_matrix,tridiagonal_toeplitz}.py` (+208/-152) | 21 OK (non-strict: the test file still imported the deprecated `ExactReciprocal`) |
| 3fe7192 | `linear_solvers/hhl.py` (+31/-2, `phase_estimation` import, `qpe_circuit`, call site) | 21 OK (non-strict) |
| 90b177a | `linear_solvers/hhl.py` (+82/-46, gate imports, `exact_reciprocal` kwarg, `_chebyshev_reciprocal`, wiring) | 21 OK (non-strict) |
| 1164a45 | `test/test_linear_solvers.py` (+92/-5) | 25 OK, strict `-W error::DeprecationWarning` |
| 9d1d7bb | `pyproject.toml`, `README.md`, `setup.py` | 25 OK, strict, on the working tree (== HEAD) |

Checks after the last commit:

1. `git status --short` is empty; the five commits above are exactly
   `main..feature/qiskit3-api-port`.
2. `git format-patch main..feature/qiskit3-api-port -o
   /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/`
   wrote
   `0001-Replace-BlueprintCircuit-base-of-LinearSystemMatrix-.patch` (19958 bytes),
   `0002-Build-HHL-phase-estimation-with-phase_estimation-beh.patch` (3327 bytes),
   `0003-Use-ExactReciprocalGate-and-PiecewiseChebyshevGate-f.patch` (8233 bytes),
   `0004-Port-fork-tests-to-ExactReciprocalGate-and-add-Cheby.patch` (6851 bytes),
   `0005-Require-qiskit-2.2-and-note-the-Qiskit-3.0-API-port-.patch` (2643 bytes);
   the interim `UNCOMMITTED-qiskit3-api-port.diff` was deleted. Applying the
   five patches in order (`git apply`) onto a fresh detached worktree of 66eadf0
   reproduced HEAD's tracked tree exactly (`diff -rq`); worktree removed.
3. `git diff main..HEAD --stat`: 8 files changed, 423 insertions, 208 deletions;
   sha256 of the `git diff main` output
   `98690527c404a143da87919d053e55d336bb367472498e0d3e850b104403df1f`, equal to
   the fix-up round's uncommitted diff, so the committed tree is the verified
   working tree byte for byte.
4. Fork suite strict on the committed tree: `Ran 25 tests in 8.278s OK`
   (2026-10-16T00:30:53Z). Gate, once, editable install (`linear_solvers.__file__`
   is the clone path, no `PYTHONPATH`): `cd
   /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver && FVM_GATE_TESTS=1
   .venv/bin/python -m unittest tests.test_gate_fixture -v` -> `Ran 7 tests in
   141.567s OK` (start 2026-10-16T00:31:03Z; HHL nelem-5 123.28 s, nelem-2
   18.08 s; slower than the 92 s to 94 s of the earlier runs because the machine
   was loaded by other builders, all 1e-10 comparisons passed).
5. One short SQLS statevector run, `nozzle_1d_solver.py -nelem 2 -linsolver SQLS
   -shots 0 -sqls_method full_svd -iters 1 -time_scheme BDF1 -localdt -cfl 1e10
   -initers 1 -noshow -outdir <scratch>` (4 s, 2026-10-16T00:33:52Z);
   `metadata_nelem2_SQLS_statevector.pkl` -> `code_versions['linear_solvers']`:

   ```
   path: /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers
   commit: 9d1d7bbb083785a52baea9605d6b2d01e50d5cdc
   dirty: false
   diff_sha256: null
   commit_source: git
   version: 0.1.0
   ```

   (before committing the same record read `commit 66eadf0..., dirty: true,
   diff_sha256: 98690527...`; fvm d2e5c6a5 clean, sqls 9a4346a7.)
6. This section. Scratch `/tmp/order2-commit-15` deleted, no worktrees left.
