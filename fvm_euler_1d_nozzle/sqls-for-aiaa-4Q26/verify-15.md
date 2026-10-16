# verify-15: independent verification of the HHL fork Qiskit 3.0 API port

**VERDICT: PASS**

- Verified: 2026-10-15T05:34:49Z to 2026-10-15T05:58:00Z (UTC), macOS laptop
- Fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers` (import name
  `linear_solvers`), branch `feature/qiskit3-api-port`, HEAD = `main` =
  `origin/main` = 66eadf0, port as uncommitted working tree
- Pre-port reference: detached worktree of 66eadf0 at `/tmp/order2-verify-15/pre`
  (created with `git worktree add --detach`, run via `PYTHONPATH=`, removed after)
- Interpreter: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
  (Python 3.12.10, qiskit 2.5.2, qiskit-aer 0.17.2); `linear_solvers` is installed
  editable from the clone, confirmed by `linear_solvers.__file__` in every run
- Method: own reading of `git diff main`, own probes; I did not read any
  `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md` or `fork-patches/`
- All wall times are single runs on this laptop. My own runs did not overlap
  each other; other agents may have been running solver jobs, so times can be
  inflated (the default fvm suite took 60.36 s against a nominal ~47 s)
- Budget used: 3 HHL nelem-5 statevector solves (gate fixture, AFTER, BEFORE;
  limit 4), gate fixture once (limit 2), default fvm suite once, fork tests 3
  times, 2 nelem-5 construct+transpile for metrics (inside the solves)

## Diff summary (own reading)

`git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers diff main --stat`

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

- `hhl.py`: imports `ExactReciprocalGate, PiecewiseChebyshevGate, phase_estimation`
  from `qiskit.circuit.library`; new method `HHL.qpe_circuit(num_clock_qubits,
  unitary) -> QuantumCircuit` wrapping `phase_estimation(..., name="QPE")`;
  `construct_circuit` calls `self.qpe_circuit(nl, matrix_circuit)`;
  `ExactReciprocalGate(nl, delta, neg_vals=neg_vals)` appended to `ql[::-1] + [qf[0]]`
  as before; `PiecewiseChebyshevGate(reciprocal_angle, nl, degree, breakpoints)`
  with a wrapper `reciprocal_angle` that returns `arcsin(1)` outside
  `[a, 2**nl - 1]`; reciprocal ancilla count now `gate.num_qubits - nl - 1`.
- `linear_system_matrix.py`: `class LinearSystemMatrix(QuantumCircuit, ABC)`;
  lazy build kept explicitly (`_is_built`, `_build()` composing `power(1)` after
  `_check_configuration()`, `_reset_registers()` re-running `QuantumCircuit.__init__`);
  readers overridden to build first: `data`, `__len__`, `__getitem__`, `decompose`,
  `draw`, `size`, `depth`, `count_ops`, `num_nonlocal_gates`,
  `num_connected_components`, `to_instruction`, `to_gate`; new abstract
  `_registers()` and `_check_configuration()`.
- `numpy_matrix.py`, `tridiagonal_toeplitz.py`: duplicate `num_state_qubits`
  property, `_reset_registers`, `_build` and the `_invalidate()` calls removed;
  `_registers()` implemented. `grep -rn "_invalidate" linear_solvers` is empty.
- `test/test_linear_solvers.py`: `ExactReciprocalGate` replaces `ExactReciprocal`;
  `.control()` -> `.control(annotated=False)` in `TestMatrices`.
- `pyproject.toml`: `qiskit>=2.0` -> `qiskit>=2.2`. `README.md`: 7-line note.

## Criterion 1: API replacements and plain QuantumCircuit base -- PASS

```
cd /Users/agallojr/proj/src/q8020/quantum_linear_solvers
grep -rn "BlueprintCircuit\|PhaseEstimation\b\|ExactReciprocal\b\|PiecewiseChebyshev\b" linear_solvers test
```

Output (3 hits, all prose):

```
linear_solvers/hhl.py:271:        former ``PhaseEstimation`` class produced).
linear_solvers/hhl.py:439:            # what the former PiecewiseChebyshev circuit did through its identity
linear_solvers/matrices/linear_system_matrix.py:34:    contract the former ``BlueprintCircuit`` base provided (deprecated in Qiskit
```

- QPE built by `phase_estimation()` (hhl.py:288) via `qpe_circuit` (hhl.py:472).
- `ExactReciprocalGate` at hhl.py:399; `PiecewiseChebyshevGate` at hhl.py:448.
- `LinearSystemMatrix(QuantumCircuit, ABC)`; lazy build preserved explicitly (see
  diff summary); both subclasses updated; test file off `ExactReciprocal`.
- `python -m py_compile` on the five changed Python files: OK.

## Criterion 2: zero qiskit deprecation warnings -- PASS

AFTER (clone):

```
/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python -W error::DeprecationWarning \
  -c "import linear_solvers; from linear_solvers import HHL, NumPyMatrix, TridiagonalToeplitz; print(linear_solvers.__file__)"
-> /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py   exit 0
```

Same import with `-W always`: zero warnings of any category. A 2x2
`HHL().construct_circuit` plus `TridiagonalToeplitz(2,...).power(1)` under a
record-everything hook: 0 warnings. Full fvm-path nelem-5 and nelem-2 solves
(`LinearSystemSolver.hhl_solve`, see criterion 3) under a record-everything hook
(`warnings.simplefilter("always")` + custom `showwarning`): **total=0
DeprecationWarning=0**. Gate fixture under `-W error::DeprecationWarning`: passed
(criterion 3). Fork tests under `-W error::DeprecationWarning`: 21 OK (criterion 4).
A strict probe of `HHL().construct_circuit(TridiagonalToeplitz(2, 1, -1/3,
trotter_steps=2), b)` and `.solve(...)` also passed with no warning.

BEFORE (worktree of 66eadf0 on `PYTHONPATH`): the **import itself is silent** even
under `-W always` (the work item's "four DeprecationWarnings fire on import" is
inaccurate: they fire at first construction). Constructing a matrix and an HHL
circuit emits them. Recorded during the BEFORE nelem-5 fvm-path solve: 10
DeprecationWarnings, 4 distinct, verbatim:

```
DeprecationWarning /tmp/order2-verify-15/pre/linear_solvers/matrices/linear_system_matrix.py:39: The class ``qiskit.circuit.library.blueprintcircuit.BlueprintCircuit`` is deprecated as of Qiskit 2.1. It will be removed in Qiskit 3.0. There is no direct replacement other than the QuantumCircuit class.
DeprecationWarning /tmp/order2-verify-15/pre/linear_solvers/hhl.py:368: The class ``qiskit.circuit.library.arithmetic.exact_reciprocal.ExactReciprocal`` is deprecated as of Qiskit 2.2. It will be removed in Qiskit 3.0. Use the class qiskit.circuit.library.ExactReciprocalGate instead.
DeprecationWarning /tmp/order2-verify-15/pre/linear_solvers/hhl.py:426: The class ``qiskit.circuit.library.phase_estimation.PhaseEstimation`` is deprecated as of Qiskit 2.1. It will be removed in Qiskit 3.0. Use qiskit.circuit.library.phase_estimation instead.
DeprecationWarning /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/qiskit/circuit/library/phase_estimation.py:96: The class ``qiskit.circuit.library.basis_change.qft.QFT`` is deprecated as of Qiskit 2.1. It will be removed in Qiskit 3.0. ('Use qiskit.circuit.library.QFTGate or qiskit.synthesis.qft.synth_qft_full instead, for access to all previous arguments.',)
```

(`PiecewiseChebyshev` carries no `deprecate_func` of its own in 2.5.2; it inherits
the `BlueprintCircuit` deprecation. The fvm path never reaches it.)

## Criterion 3: gate fixture reproduces the pre-port references -- PASS

Command (strict, with `linear_solvers.__file__` printed in the same interpreter):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -W error::DeprecationWarning -c "
import sys, unittest, linear_solvers, qiskit, qiskit_aer
print('linear_solvers.__file__ =', linear_solvers.__file__)
sys.argv = ['unittest', '-v', 'tests.test_gate_fixture']; unittest.main(module=None)"
```

Start 2026-10-15T05:45:56Z, end 2026-10-15T05:47:38Z, `real 101.92 s`
(`user 248.75 s`, Aer multithreaded). Output:

```
linear_solvers.__file__ = /Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/__init__.py
qiskit 2.5.2 qiskit_aer 0.17.2
test_archived_sources_unchanged ... ok                 0.00 s
test_fixture_files_match_recorded_sha256 ... ok         0.00 s
test_systems_are_well_posed ... ok                      0.00 s
TestHHLFixture.test_nelem2_iter0_statevector_matches_reference ... ok    7.47 s
TestHHLFixture.test_nelem5_iter0_statevector_matches_reference ... ok   93.37 s
TestSQLSFixture.test_nelem2_iter0_statevector_matches_reference ... ok   0.03 s
TestSQLSFixture.test_nelem5_iter0_statevector_matches_reference ... ok   0.01 s
Ran 7 tests in 100.878s  OK
```

The fixture only prints max-abs on failure, so I recomputed it with my own script
(`/tmp/order2-verify-15/run_solve.py`, deleted) that calls
`tests.helpers.make_linsys_solver(nelem, 'HHL').hhl_solve(A, b, step=0)` on
`tests/data/system_Ab_nelem{2,5}_iter0.pkl` and compares to
`tests/data/ref_hhl_nelem{2,5}_iter0.npz` (tolerance 1e-10 max-abs):

| system | code | `hhl_solve` wall | max-abs dq vs ref | fidelity diff vs ref | linsys_residual diff vs ref |
|---|---|---|---|---|---|
| nelem 2 (6 x 6) | AFTER (clone) | 7.8 s | 1.887e-15 (1.055e-15 in a first run) | 4.44e-16 | 9.14e-16 |
| nelem 2 (6 x 6) | BEFORE (66eadf0) | 8.1 s | 5.829e-16 (1.277e-15 in a first run) | 4.44e-16 | 2.53e-15 |
| nelem 5 (15 x 15) | AFTER (clone) | 99.8 s | 3.908e-14 | 0.00e+00 | 3.56e-14 |
| nelem 5 (15 x 15) | BEFORE (66eadf0) | 102.3 s | 3.908e-14 | 4.44e-16 | 9.39e-15 |

AFTER vs BEFORE directly: max |dq_after - dq_before| = 1.832e-15 (nelem 2),
6.328e-15 (nelem 5); max |dq| is 0.437 and 1.527 respectively, so relative
differences are at the 1e-15 level. Fidelities: 0.999998635611331 (nelem 2),
0.999957137762986 (nelem 5), identical to the stored references to 15 digits.
The 3.9e-14 at nelem 5 is the same for both codes, i.e. transpiler run-to-run
noise relative to the reference generated at 2026-10-15T03:10:42Z, not a port effect.

Default fvm suite (`cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver &&
.venv/bin/python -m unittest discover -s tests -v`, 2026-10-15T05:54:15Z):
`Ran 82 tests in 59.243s  OK (skipped=1)` (the skip is the gate-only nelem-5 HHL
test), `real 60.36 s`.

## Criterion 4: fork's own tests before and after -- PASS

```
cd /tmp/order2-verify-15/pre && <venv python> -m unittest discover -s test -v        # BEFORE
cd /Users/agallojr/proj/src/q8020/quantum_linear_solvers && <venv python> -m unittest discover -s test -v   # AFTER
cd /Users/agallojr/proj/src/q8020/quantum_linear_solvers && <venv python> -W error::DeprecationWarning -m unittest discover -s test -v
```

| run | result | unittest time | real |
|---|---|---|---|
| BEFORE (worktree, 2026-10-15T05:39:19Z) | Ran 21 tests, OK | 5.773 s | 6.52 s |
| AFTER (clone, 2026-10-15T05:39:25Z) | Ran 21 tests, OK | 5.762 s | 6.32 s |
| AFTER strict `-W error::DeprecationWarning` | Ran 21 tests, OK | 5.654 s | 6.23 s |

Pass count 21 >= 21; no failures. BEFORE output showed two qiskit
DeprecationWarnings (`ExactReciprocal` at test line 213; `Gate.control()`'s
`annotated` argument, via `matrix.power(power).control()` in `test_matrices_3`)
plus scipy `diags` FutureWarnings; AFTER shows only the scipy FutureWarnings
(pre-existing, not qiskit).

## Criterion 5: circuit metrics re-recorded -- PASS

Built exactly as `quantum_tools.QuantumHHL` does, by running the fvm path:
`QuantumHHL(backend_type='ideal', backend_method='statevector')` ->
`HHL(quantum_instance=AerSimulator(method='statevector')).construct_circuit(A_herm,
b_herm)`, `circ.measure_all()`, then `transpile(circ, self.backend)` (the ideal
branch at `quantum_tools.py:443`: no `basis_gates`, no `seed_transpiler`,
default optimization level). Metrics read from the saved
`circuit_transpile_statevector_nelem{2,5}_iter0.qpy` with `qpy.load`; "total
ops" is `sum(count_ops().values())` as QuantumHHL prints it (includes 1 barrier
and the final measures).

| system | code | qubits | depth | total ops | cx | ccx | cu | depth / ops without final measurements |
|---|---|---|---|---|---|---|---|---|
| nelem 2 | BEFORE | 12 | 68964 | 74787 (74821 in a first run) | 64 | 24258 | 24060 | 68963 / 74774 |
| nelem 2 | AFTER | 12 | 68964 | 74845 (74808 in a first run) | 64 | 24258 | 24060 | 68963 / 74832 |
| nelem 5 | BEFORE | 14 | 596688 | 641104 | 128 | 215986 | 195140 | 596687 / 641089 |
| nelem 5 | AFTER | 14 | 596688 | 641105 | 128 | 215986 | 195140 | 596687 / 641090 |

Non-local gate count without measurements: 65203 (nelem 2) and 570973 (nelem 5),
identical BEFORE and AFTER. Qubits unchanged (12 / 14). Depth identical. CX
identical. Total ops differ by tens, but identical code also differs by tens
between runs (AFTER nelem 2: 74808 then 74845; BEFORE: 74821 then 74787), because
the ideal-path `transpile` has no seed; the moving counts are the 1q/2q rotation
families (crz, u3, u1, rzz, rzx, cry, cp), not ccx/cu/cx. No gate-count shift is
attributable to the port at this resolution.

## Criterion 6: clean QPE seam -- PASS (with one caveat)

`HHL.qpe_circuit(self, num_clock_qubits: int, unitary: QuantumCircuit) ->
QuantumCircuit` (hhl.py:261-288) is the only place QPE is built; it returns
`phase_estimation(num_clock_qubits, unitary, name="QPE")`. `construct_circuit`
calls it once (hhl.py:472) and appends the result to `ql[:] + qb[:] +
qa[:matrix_circuit.num_ancillas]`, then `pe_circuit.inverse()` after the rotation.
`grep -rn "phase_estimation\|qpe_circuit\|QFT\|PhaseEstimation" linear_solvers`
finds nothing else. The docstring states the contract: clock qubits first, then
the unitary's qubits in its own order; `unitary.power(k)` must return something
with `.control()`; the result must be invertible with `QuantumCircuit.inverse()`.

Judgement: a LuGo-style QPE can be dropped in by subclassing `HHL` and overriding
`qpe_circuit`, without touching `construct_circuit`, as long as it fits in
`num_clock_qubits + unitary.num_qubits` qubits and is uncomputed by `inverse()`.
A QPE that needs extra ancillas, or a different uncompute, would still need
`construct_circuit` changes (register sizing `na`, the inverse step). The seam
hands over the Hamiltonian-simulation *circuit*; a plug-in wanting the matrix and
evolution time can read `unitary.matrix` / `unitary.evolution_time` on
`NumPyMatrix` but that is not in the signature.

## Criterion 7: tree state -- PASS

```
git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers branch --show-current   -> feature/qiskit3-api-port
git rev-parse main HEAD origin/main   -> 66eadf0b4edcff100b20edf70a99e79cc69c5923 (all three)
git branch -r   -> origin/HEAD -> origin/main, origin/main, upstream/HEAD -> upstream/main, upstream/main
git status --short -> 7 modified files (README.md, pyproject.toml, 4 under linear_solvers/, 1 under test/)
git stash list -> empty
```

Diff confined to `linear_solvers/**`, `test/**`, `pyproject.toml`, `README.md`.
Nothing pushed (no remote feature branch). Status identical before and after my
verification; my only writes to the fork were the temporary worktree metadata,
removed with `git worktree remove --force`.

## Findings

1. **Non-exact reciprocal (PiecewiseChebyshev path): numerics preserved.** With
   the parameters hhl.py computes (nl=3,4,5,6; `a = round(2^nl^(2/3))`,
   breakpoints `[a, 2^nl-1]`, degree 1-4), the old `PiecewiseChebyshev` circuit
   and the new `PiecewiseChebyshevGate` + wrapper give the same target amplitude
   for every clock value: max diff 2.4e-15 (nl 3), 4.4e-14 (nl 4), 1.0e-13 (nl 5);
   amplitude 1.0 at x=0 and x=2^nl-1 in both (saturation reproduced). Polynomial
   lists differ in form (old: 3 entries with identity `[pi]` on the padded
   intervals; new: 4 entries, Chebyshev fits of the constant pi/2 on the padded
   intervals, since the gate pads breakpoints before fitting) but are equivalent.
   End-to-end `HHL` with `_exact_reciprocal=False` on a 2x2 and a 4x4 system:
   solution max diff 1.1e-16 and 1.2e-15, euclidean norm diff 2.0e-15 and 4.5e-14
   BEFORE vs AFTER. The qubit count of this branch drops (8 -> 6 and 13 -> 9)
   because the gate uses 1 compare ancilla where the old circuit used nl. The
   task statement's "the fork tests cover it" is wrong: no test sets
   `exact_reciprocal=False` (`grep -n exact_reciprocal test/` finds only the
   `ExactReciprocalGate` test), and `HHL.__init__` has no such argument
   (`_exact_reciprocal = True` hard-coded), so fvm never uses this branch.
2. **Corner-case regression in `copy_empty_like()` (off the HHL path).**
   `BlueprintCircuit.copy_empty_like` returned a plain `QuantumCircuit`; the port
   inherits `QuantumCircuit.copy_empty_like`, which `copy.copy`s the object, so
   the "empty" copy is an unbuilt `LinearSystemMatrix` that self-builds on first
   read. Any qiskit method that uses `copy_empty_like` as a scratch output and
   appends into it gets a doubled body: on a fresh `NumPyMatrix`, `reverse_ops()`
   returns 2 ops with max |U - exp(iAt)| = 0.435 (BEFORE: 1 op, 0.0);
   `remove_final_measurements(inplace=False)` returns size 2 (BEFORE 1);
   `copy_empty_like().data` has 1 op (BEFORE 0). HHL only uses `power()`,
   `control()`, `num_qubits`, `num_ancillas` and the bounds methods on the matrix,
   so the gate is unaffected. Suggested fix: override `copy_empty_like` to return
   a plain `QuantumCircuit` (as `BlueprintCircuit` did) or mark the copy built.
3. **`copy()` semantics shifted slightly.** `BlueprintCircuit.copy()` built first
   so the copy shared the body and `m == m.copy()` was True; now an unbuilt copy
   builds its own `power(1)` (new auto-named inner circuit), so `m == m.copy()`
   is False although the unitaries are identical (max diff 0.0). Harmless.
4. **Qiskit 2.3 `annotated` deprecation (removed in 3.0), outside the work
   item's four targets.** `NumPyMatrix.power(k)` returns a plain `QuantumCircuit`;
   `.control()` on it without `annotated=False` emits, under `-W error`:
   ``DeprecationWarning: ``qiskit.circuit.gate.Gate.control()``'s argument
   ``annotated`` is deprecated as of Qiskit 2.3. It will be removed in Qiskit
   3.0. The method Gate.control() no longer accepts `annotated=None`. ...``.
   The library's HHL path is clean (`phase_estimation` passes
   `annotated=False`; `TridiagonalToeplitz` uses hand-rolled `control`
   closures), and the test was updated, but the docstring examples at
   `linear_solvers/matrices/numpy_matrix.py:41,44` and
   `linear_solvers/matrices/tridiagonal_toeplitz.py:58,61` still show bare
   `.control()`; a user following them hits the warning today and a semantics
   change (AnnotatedOperation) in 3.0.
5. **Work item wording.** The four warnings do not fire on import; they fire on
   first construction (`NumPyMatrix`/`TridiagonalToeplitz.__init__` ->
   `BlueprintCircuit`; `construct_circuit` -> `ExactReciprocal`,
   `PhaseEstimation`, and `QFT` inside it). Intent unaffected.
6. **Pre-existing, not port-related: generated-circuit QPY files do not reload.**
   `circuit_generated_statevector_nelem{2,5}_iter0.qpy` written by
   `QuantumHHL.generate_circuit` fail in `qpy.load` with `TypeError:
   ExactReciprocalGate.__init__() missing 2 required positional arguments:
   'num_state_qubits' and 'scaling'`, for BEFORE and AFTER alike (qpy maps the
   gate name to the library class on load). The transpiled QPY loads fine. This
   breaks fvm's `-load_qcirc` path only.
7. **Pre-existing behaviours, identical before and after:** the
   `TridiagonalToeplitz` body is empty by upstream design (`power(1)` returns an
   empty raw circuit carrying a closure `control`), so `Operator(tt)` is not
   exp(iAt) and `tt.inverse()` raises `ValueError: cannot convert float NaN to
   integer`; a `NumPyMatrix` body built before `evolution_time` is changed stays
   stale (HHL sets `evolution_time` before any read, so harmless); `data` has no
   setter in either version.
8. **Transpile nondeterminism.** `transpile(circ, backend)` in the ideal path is
   unseeded; total op counts move by about +/-30 (nelem 2) between runs of the
   same code. Depth, cx, ccx, cu are stable. Read the re-recorded counts with that
   spread in mind.
9. **Hygiene.** `git diff main | grep '^+' | awk 'length > 89'`: 0 lines;
   trailing whitespace on added lines: 0; tabs: 0; imports grouped stdlib /
   third-party / local; two blank lines between top-level definitions in the
   added block. Pre-existing over-88 lines remain untouched (hhl.py: 30 lines, max
   111 chars; numpy_matrix.py: 2; tridiagonal_toeplitz.py: 9). No `pycodestyle` /
   `flake8` in the venv and I installed nothing, so no linter run.
10. **`pyproject.toml` `qiskit>=2.2`** is consistent with `ExactReciprocalGate`
    (named as the replacement in the 2.2 deprecation message) and
    `phase_estimation` (named in the 2.1 message); I could not confirm offline
    that `PiecewiseChebyshevGate` exists in 2.2 exactly.

## Lazy-build probe results (criterion 1 support)

On a fresh `NumPyMatrix(2x2, evolution_time=0.7)` AFTER (BEFORE identical unless
noted): `len()` 1, `len(.data)` 1, `depth()` 1, `count_ops()` `{'circuit-N': 1}`,
`size()` 1, `Operator(m)` vs exp(iAt) max diff 0.0, `power(2)` vs exp(2iAt)
4.0e-16, `power(1).control().num_qubits` 2, `inverse()` vs exp(-iAt) 0.0,
`QuantumCircuit.compose(m)` size 1, `append` then `decompose` size 1,
`Statevector(m)` vs exp(iAt)|0> 0.0, `transpile(m, ['u','cx'])` size 1,
`copy().data` 1 op, `to_gate()` 1 qubit, `draw('text')` non-empty, `m[0]` a
`CircuitInstruction`, pickle round-trip builds correctly (max diff 0.0).
`num_state_qubits = 3` after a build: registers reset to 3 qubits, `_data`
emptied, `_is_built` False (same BEFORE). `TridiagonalToeplitz(2, 1.5, 0.5)`:
`len` 0, `depth` 0, `count_ops` `{}` both BEFORE and AFTER (finding 7);
`power(1).control().num_qubits` 4; `Statevector` valid; `transpile` size 0.
No exception that did not also occur BEFORE.

## Not checked, and why

- Qiskit 3.0 itself: not installed; no network and no installs allowed. The port
  is verified against 2.5.2 by the absence of deprecation warnings, so the actual
  3.0 removal behaviour is inferred, not executed.
- The `qiskit>=2.2` floor was not tested against a 2.2 install.
- Non-statevector backends (`fake`, `real-ibm`, `real-iqm`) and shot-based runs:
  outside the gate and not run.
- The non-exact reciprocal branch at nelem-5 size: checked by Operator at
  nl <= 5 and end-to-end at 2x2 / 4x4 only; fvm cannot reach this branch.
- Per instructions, `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`
  and `fork-patches/` were not read.
- No linter (pycodestyle/flake8) run: not present in the venv, nothing installed.

## Cleanup

`git -C /Users/agallojr/proj/src/q8020/quantum_linear_solvers worktree remove
--force /tmp/order2-verify-15/pre` and `rm -rf /tmp/order2-verify-15` (242 MB of
scratch, mostly QPY dumps) were run after this report was written; `git worktree
list` shows only the main checkout. No other file in this folder was created or
modified.
