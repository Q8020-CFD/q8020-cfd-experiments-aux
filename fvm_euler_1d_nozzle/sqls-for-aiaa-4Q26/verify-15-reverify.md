# Work item 15 re-verification: HHL fork lazy-build fix-up (Qiskit 3.0 port)

VERDICT: PASS

Independent re-verifier, 2026-10-15T07:44:56Z to 2026-10-15T07:57:19Z (UTC).
Read-only in all repos; venv untouched; scratch `/tmp/order2-reverify-15/`
(deleted at the end).

## Subject

- Fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, branch
  `feature/qiskit3-api-port`, HEAD `66eadf0b4edcff100b20edf70a99e79cc69c5923`
  = `main` = `origin/main`; `git log origin/main..HEAD | wc -l` = 0 (nothing
  pushed); port is the uncommitted working tree; no untracked files, empty stash.
- Interpreter: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
  (Python 3.12.10, qiskit 2.5.2); `linear_solvers.__file__` =
  `/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py`
  (editable from the clone).
- Reference for "the old base": the installed
  `qiskit/circuit/library/blueprintcircuit.py` (deprecated since 2.1, still
  present in 2.5.2). Its hook set: `data`, `parameters`, `num_parameters`,
  `_append`, `compose`, `inverse`, `__len__`, `__getitem__`, `size`,
  `to_instruction`, `to_gate`, `depth`, `count_ops`, `num_nonlocal_gates`,
  `num_connected_components`, `decompose`, `draw`, `copy_empty_like`, `copy`,
  `qregs` setter. The fork's `LinearSystemMatrix` hooks all of these except
  `inverse` (both subclasses override `inverse()` to return a fresh matrix with
  negated `evolution_time`; verified below) and the `qregs` setter (register
  replacement goes through the `num_state_qubits` setter instead; no caller
  assigns `qregs`). BlueprintCircuit's own `copy_empty_like` also returns a
  plain `QuantumCircuit` without building, so the fork's matches it.

All probes ran with `-W error::DeprecationWarning`. `A` is the 4x4 tridiagonal
`[[1/2,1/6,0,0],[1/6,1/2,1/6,0],[0,1/6,1/2,1/6],[0,0,1/6,1/2]]`;
`maxdiff(a, b)` = max |a - b| over matrix entries (dimensionless, operator
entries); `names(c)` = `[i.operation.name for i in c.data]`.

## F1. Failed build must not leave `_is_built=True` with an empty body: PASS

Probe:
```python
m = NumPyMatrix(A); m.num_state_qubits = 3          # 4x4 matrix on 3 qubits
for i in range(3):
    try: d = m.data; print(f"data access {i}: NO RAISE len={len(d)}")
    except Exception as e: print(f"data access {i}: raised {type(e).__name__}: ...")
    print(f"   _is_built={m._is_built} raw_len={len(m._data)}")
# then size(), depth(), to_gate(), x(0), len(), Operator(); then m.num_state_qubits = 2
# B: built matrix, then m2.matrix = non-hermitian 2x2 -> .data
# C: m3.power = lambda p, **kw: QuantumCircuit(5)  (power OK, compose fails) -> .data; del m3.power
```
Output:
```
after resize: num_qubits 3 num_state_qubits 3 _is_built False raw_len 0
data access 0: raised CircuitError: 'The amount of qubit(3)/clbit(0) arguments does not match the gate expectation (
   _is_built=False raw_len=0
data access 1: raised CircuitError: ...   _is_built=False raw_len=0
data access 2: raised CircuitError: ...   _is_built=False raw_len=0
size(): raised CircuitError        _is_built=False raw_len=0
depth(): raised CircuitError       _is_built=False raw_len=0
to_gate(): raised CircuitError     _is_built=False raw_len=0
x(0): raised CircuitError          _is_built=False raw_len=0
len(): raised CircuitError         _is_built=False raw_len=0
Operator(): raised CircuitError    _is_built=False raw_len=0
restored to 2: len(data) 1 _is_built True Op vs expm(iA) 0.0
--- B: _check_configuration failure on a built matrix ---
built True
after bad matrix set: _is_built False raw_len 0
nonherm: raised AttributeError Input matrix must be hermitian!
   _is_built False raw_len 0
--- C: power OK but compose fails (monkeypatched power -> 5-qubit circuit) ---
bad-compose: raised CircuitError 'Cannot compose onto a circuit with fewer qubits (5 > 2).'
   _is_built False raw_len 0
after restoring power: len(data) 1 _is_built True
```
Every access raises, `_is_built` stays False, the body stays empty, and the
object recovers once the configuration is fixed. The `try/except` around
`compose` in `_build` (which sets the flag before composing) is exercised by
case C and restores the unbuilt state. Note: for the F1 mismatch the exception
comes from `power(1)` (`unitary()` on 3 qubits), not from
`_check_configuration`, which does not compare `matrix.shape` against
`num_state_qubits`; the outcome meets the spec either way.

## F2. Mutating an unbuilt matrix builds first: PASS

Probe:
```python
m = NumPyMatrix(A); m.x(0); names(m)
m = NumPyMatrix(A); m.compose(other_h0, inplace=True); names(m)
m = NumPyMatrix(A); c = m.compose(other_h0); names(c), names(m)
m = NumPyMatrix(A); m.append(XGate(), [0]); names(m)
# also h+cx, measure_all, body op definition, TridiagonalToeplitz x / compose
```
Output:
```
x(0): ['circuit-41', 'x'] _is_built True
   Op(m) vs X0*expm(iA): 0.0
compose(inplace): ['circuit-50', 'h'] _is_built True
compose(non-inplace): NumPyMatrix ['circuit-54', 'h'] | m untouched: ['circuit-54']
append(XGate,[0]): ['circuit-58', 'x'] _is_built True
h,cx: ['circuit-62', 'h', 'cx']
measure_all: ['circuit-66', 'barrier', 'measure', 'measure'] clbits 2
body op: circuit-70 definition: ['unitary']
tridi x(0): ['x'] _is_built True num_qubits 3 (power(1) body is empty for TridiagonalToeplitz)
tridi compose: ['h'] _is_built True
```
The `power(1)` body (`circuit-N` = `QuantumCircuit.repeat(1)` gate wrapping the
`unitary`) is first, the user's instruction second, and the operator equals
X(0)*exp(iA). `TridiagonalToeplitz.power(1)` is an empty circuit by design
(upstream behaviour, unchanged), so its built body is empty and the flag flips.

## F3. `copy_empty_like`, `reverse_ops`, `remove_final_measurements`, `copy`: PASS

Output (probe calls shown in the left column):
```
copy_empty_like: QuantumCircuit len 0 qregs== True qubits== True m._is_built False e.name circuit-41
   named: foo
reverse_ops: QuantumCircuit len 1 maxdiff vs reversed body 0.0 vs expm(iA) 0.0
remove_final_measurements(inplace=False): NumPyMatrix size 1 orig size 1
   after measure_all: orig size 3 -> rm size 1 ['circuit-62'] clbits 0
copy: NumPyMatrix c._is_built True m._is_built True len 1 1 shares _data False c.data is m.data False name np_matrix
   after c.x(0): len c 2 len m 1
   after m.x(1): len c 2 len m 2
   params: evolution_time 1.0 tolerance 0.01 num_state_qubits 2 matrix equal True
   c.evolution_time=3.0 -> m.evolution_time 1.0 | Op(c) vs expm(3iA) 0.0 | Op(m) vs expm(iA) 0.0
   copy(name='bar').name: bar
tridi copy: TridiagonalToeplitz num_qubits 3 ancillas 1 _is_built True main_diag 1 trotter 1
tridi copy_empty_like: QuantumCircuit len 0 qubits 3 ancillas 1 t._is_built False
```
`copy_empty_like()` on an unbuilt matrix: empty plain `QuantumCircuit`, same
registers/qubits, does not trigger a build. `reverse_ops()` on a fresh matrix:
1 instruction, operator identical to the reversed built body (max diff 0.0).
`remove_final_measurements(inplace=False)`: size 1 (and strips a real
`measure_all`). `copy()`: same class, built, independent body (mutating either
side leaves the other alone; setter on the copy does not touch the original).

## F4. Every body-changing setter invalidates: PASS

Output:
```
built True Op vs expm(iA) 0.0
set evolution_time=2.0: _is_built False raw_len 0
   Op vs expm(2iA) 0.0 | vs m.power(1) 0.0 | len 1
set tolerance=1e-3: _is_built False raw_len 0
   rebuilt len 1 _is_built True Op vs expm(2iA) 0.0
set matrix=B: _is_built False raw_len 0
   Op vs expm(2iB) 0.0 | len 1
resize to 3 qubits: num_qubits 3 Op vs expm(2iA8) 0.0 | len 1
--- TridiagonalToeplitz ---
built True num_qubits 3 ancillas 1
set main_diag=2.0: _is_built=False raw_len=0 regs intact=True -> rebuilt _is_built=True
set off_diag=0.25: _is_built=False raw_len=0 regs intact=True -> rebuilt _is_built=True
set trotter_steps=3: _is_built=False raw_len=0 regs intact=True -> rebuilt _is_built=True
set evolution_time=2.0: _is_built=False raw_len=0 regs intact=True -> rebuilt _is_built=True
set tolerance=0.001: _is_built=False raw_len=0 regs intact=True -> rebuilt _is_built=True
tridi params now: main_diag 2.0 off_diag 0.25 evolution_time 2.0 tolerance 0.001 trotter_steps 3
matrix row0: [2.   0.25 0.   0.  ]
```
(`B` = 4x4 tridiagonal with 2 on the diagonal and 1 off it; `A8` =
`diag(0..7)` with `num_state_qubits` reset to 3.) After rebuild `len(data)` is
1, i.e. the old body was dropped, not appended to; `Operator(m)` equals
`scipy.linalg.expm(1j*A*t)` to 0.0 for each setter. All five
`TridiagonalToeplitz` setters drop the body and keep the registers (3 qubits,
1 ancilla); `evolution_time` recomputes `trotter_steps` (2.5 -> 3).

## F5. Non-exact reciprocal reachable and tested: PASS

`grep -n exact_reciprocal linear_solvers/hhl.py`:
```
94:        exact_reciprocal: bool = True,
103:            exact_reciprocal: If True (default) the conditioned rotation uses
119:        self._exact_reciprocal = exact_reciprocal
463:        if self._exact_reciprocal:
499:        if self._exact_reciprocal:
```
`python -W error::DeprecationWarning -m unittest discover -s test -k chebyshev -v`
(2026-10-15T07:53:31Z):
```
test_hhl_chebyshev_reciprocal_1 ... ok
test_hhl_chebyshev_reciprocal_2 ... ok
test_chebyshev_reciprocal_matches_legacy_1__4__0_25__2_6__2_ ... ok
test_chebyshev_reciprocal_matches_legacy_2__5__0_125__6_0__3_ ... ok
Ran 4 tests in 0.610s   OK
```
The legacy-agreement test ran (not skipped): `PiecewiseChebyshev` is still
importable on qiskit 2.5.2 under the test's `warnings.catch_warnings()` guard,
and the `PiecewiseChebyshevGate` amplitudes match it at `atol=1e-10`. The
end-to-end `HHL(exact_reciprocal=False).solve` rows pass their documented
fidelity floors (0.98 and 0.5).

## F6. No duplicated `tolerance` / `evolution_time` pairs: PASS

```
$ grep -n "def tolerance\|def evolution_time" linear_solvers/matrices/*.py
linear_solvers/matrices/tridiagonal_toeplitz.py:133:    def evolution_time(self) -> float:
linear_solvers/matrices/tridiagonal_toeplitz.py:138:    def evolution_time(self, evolution_time: float) -> None:
linear_solvers/matrices/linear_system_matrix.py:88:    def tolerance(self) -> float:
linear_solvers/matrices/linear_system_matrix.py:93:    def tolerance(self, tolerance: float) -> None:
linear_solvers/matrices/linear_system_matrix.py:102:    def evolution_time(self) -> float:
linear_solvers/matrices/linear_system_matrix.py:107:    def evolution_time(self, evolution_time: float) -> None:
```
`numpy_matrix.py` defines neither (its copies, and the `num_state_qubits`
pairs in both subclasses, are removed in the diff). The one override left,
`TridiagonalToeplitz.evolution_time`, is not byte-identical to the base: its
setter recomputes `trotter_steps` (whose own setter calls `_invalidate()`).

## F7. README / setup.py no longer claim Qiskit 1.x: PASS

```
$ grep -n "1\.4\|1\.x\|Qiskit 1" README.md setup.py
(exit 1, no matches)
```
README now says "ported to Qiskit >= 2.2" and lists the surviving APIs;
`setup.py` comment reads `# requires Qiskit >= 2.2`; `pyproject.toml` pins
`qiskit>=2.2`.

## F8. `AncillaRegister(num_state_qubits - 1)` without `max(1, ...)`: PASS

```
$ grep -n "AncillaRegister(" linear_solvers/matrices/tridiagonal_toeplitz.py
241:            regs.append(AncillaRegister(num_state_qubits - 1))
290:            qr_ancilla = AncillaRegister(max(1, self.num_state_qubits - 2))
332:                qr_ancilla = AncillaRegister(max(1, self.num_state_qubits - 1))
406:                qr_ancilla = AncillaRegister(max(1, self.num_state_qubits - 1))
```
Line 241 is `_registers()` (the port's register setup, guarded by
`if num_state_qubits > 1`): no redundant `max`. Lines 290/332/406 are inside
the pre-existing `_off_diag_circ` / `power().control` closures, untouched by
`git diff main` (upstream code, out of scope).

## F9. Import groups separated in `numpy_matrix.py`: PASS

```
$ sed -n '15,23p' linear_solvers/matrices/numpy_matrix.py | cat -e
from typing import List, Tuple$
$
import numpy as np$
import scipy as sp$
$
from qiskit.circuit import QuantumCircuit, QuantumRegister, Register$
$
from .linear_system_matrix import LinearSystemMatrix$
```
stdlib / numpy+scipy / qiskit / local, each group separated by a blank line.

## Docstrings and removed-API grep: PASS

Docstring examples in `numpy_matrix.py` (lines 42-46) and
`tridiagonal_toeplitz.py` (lines 58-63) use `.control(annotated=False)`.
```
$ grep -rn "BlueprintCircuit\|PhaseEstimation\b\|ExactReciprocal\b\|PiecewiseChebyshev\b" linear_solvers test
linear_solvers/hhl.py:276:        former ``PhaseEstimation`` class produced).           (docstring)
linear_solvers/hhl.py:303:        which is what the former ``PiecewiseChebyshev`` ...  (docstring)
test/test_linear_solvers.py:251:  ... PiecewiseChebyshev circuit ...                    (docstring)
test/test_linear_solvers.py:257:                    PiecewiseChebyshev,                 (import-guarded legacy import)
test/test_linear_solvers.py:260:            self.skipTest("legacy PiecewiseChebyshev not available")
test/test_linear_solvers.py:266:            legacy = PiecewiseChebyshev(                (inside the guarded test)
test/test_linear_solvers.py:420:            # is the legacy PiecewiseChebyshev behaviour ... (comment)
linear_solvers/matrices/linear_system_matrix.py:37:  ... former ``BlueprintCircuit`` ...  (docstring)
linear_solvers/matrices/linear_system_matrix.py:200: # ... former BlueprintCircuit hooks  (comment)
linear_solvers/matrices/linear_system_matrix.py:229: ... (as ``BlueprintCircuit`` did) ... (docstring)
```
No live use. All `from qiskit...` imports across `linear_solvers/` and `test/`
are `qiskit`, `qiskit.circuit`, `qiskit.circuit.library` (`ExactReciprocalGate`,
`PiecewiseChebyshevGate`, `phase_estimation`, `MCMTGate`, `UGate`),
`qiskit.quantum_info`, `qiskit.transpiler.passes`.

## Extra adversarial probes (all consistent)

```
inverse: NumPyMatrix evolution_time -1.0 Op vs expm(-iA) 0.0 m._is_built False
deepcopy unbuilt: NumPyMatrix _is_built False len 1 Op vs expm(iA) 0.0
qc.compose(unbuilt m): ['circuit-52'] Op vs expm(iA) 0.0
qc.append(unbuilt m): ['np_matrix'] Op vs expm(iA) 0.0
Statevector(unbuilt m) vs ref: 0.0
num_parameters: 0 params: [] _is_built True
HHL exact_reciprocal fidelity TridiagonalToeplitz 0.999819 qubits 8
HHL exact_reciprocal fidelity ndarray 0.999824 qubits 7
```
Composing or appending an unbuilt matrix into another circuit builds it (Qiskit's
`compose` touches `other.data`; `append` goes through `to_instruction`), as do
`Statevector`/`Operator`; `copy.deepcopy` yields an unbuilt copy that builds on
demand. Exact-reciprocal HHL end to end on both matrix classes reaches 0.9998
fidelity against `numpy.linalg.solve`.

## Regression

- Fork tests, strict (`-W error::DeprecationWarning -m unittest discover -s test -v`,
  2026-10-15T07:53:33Z): `Ran 25 tests in 6.326s  OK` (6.903 s process wall).
  One `FutureWarning` printed from `scipy.sparse.diags` (int64 input) in
  `TridiagonalToeplitz.matrix` during `test_matrices_2`: pre-existing upstream
  code not touched by the port, scipy-version driven, and not a
  `DeprecationWarning`, so strict mode is unaffected.
- Strict import: `import linear_solvers; from linear_solvers import HHL,
  NumPyMatrix, TridiagonalToeplitz` OK, module at the clone path above.
- Gate fixture (`FVM_GATE_TESTS=1 .venv/bin/python -m unittest
  tests.test_gate_fixture -v`, 2026-10-15T07:54:44Z to 07:56:21Z): 7/7 OK,
  `Ran 7 tests in 95.564s` (96.187 s process wall; nelem-5 HHL 86.14 s,
  nelem-2 HHL 9.39 s); `linear_solvers.__file__` printed from the clone with
  the same interpreter; qiskit 2.5.2. The 1e-10 tolerance is the fixture's own.
- Default fvm suite (`.venv/bin/python -m unittest discover -s tests -v`,
  2026-10-15T07:56:21Z to 07:57:19Z): `Ran 96 tests in 56.443s  OK (skipped=1)`
  (57.256 s process wall); fvm `git status` identical before and after. The
  fixture and the default suite ran concurrently with each other and with other
  agents, so wall times are upper bounds.
- `git -C <fork> diff main --stat`: `README.md`, `linear_solvers/hhl.py`,
  `linear_solvers/matrices/{linear_system_matrix,numpy_matrix,tridiagonal_toeplitz}.py`,
  `pyproject.toml`, `setup.py`, `test/test_linear_solvers.py`; 8 files,
  423 insertions, 208 deletions; confined to the allowed set. HEAD = main =
  origin/main = 66eadf0; 0 commits ahead; no untracked files; empty stash.
- Style: `git diff main -- '*.py' | grep '^+' | awk 'length > 89'` -> none;
  no trailing whitespace on any added `.py` line.

## Not checked, and why

- Behaviour under an actual Qiskit 3.0 install: only 2.5.2 is in the venv and
  no network/venv changes were allowed. Verified instead that no removed name
  is used live (grep above) and that the test suite is clean under
  `-W error::DeprecationWarning`.
- `transpile()` of a bare matrix object (bypasses the Python `data` property
  via `circuit._data`): not an HHL code path (HHL only calls
  `power(k).control()`, `num_ancillas`, bounds and setters) and the same
  limitation applied to `BlueprintCircuit`.
- Frontier, sweeps, pytest runner variant, and the forbidden `build-*/verify-*/
  reproduce-*/STATUS.md/fork-patches/` artefacts (not read, per the rules).

## Observations (non-blocking)

- `inverse` and the `qregs` setter are the two BlueprintCircuit hooks not
  mirrored in `LinearSystemMatrix`; both shipped subclasses override `inverse()`
  (verified) and nothing assigns `qregs`.
- `NumPyMatrix._check_configuration` does not cross-check `matrix.shape[0]`
  against `2**num_state_qubits`; the F1 mismatch is caught one step later by
  `power(1)` (CircuitError) with the same safe outcome.
- `tridiagonal_toeplitz.py` keeps `from typing ...` and `import numpy` in one
  block without a blank line (pre-existing; F9 only names `numpy_matrix.py`).
