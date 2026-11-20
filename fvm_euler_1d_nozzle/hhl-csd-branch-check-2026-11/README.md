# HHL branch check: feature/hhl-lugo-csd against feature/sqls-aiaa-4q26

Checks the quantum_linear_solvers branch `feature/hhl-lugo-csd`. The branch
builds the AIAA 4Q26 rewrite of the HHL circuit inside
`HHL.construct_circuit`, and it is the default:

1. one block per clock qubit, as in LuGo;
2. each controlled-U^(2^k) as L^dag (controlled middle) L, from one CSD of
   U, with L the real fit of the paper (`l_synthesis="real"`) or, where
   that does not apply, the complex L;
3. the inverse QPE as the circuit's adjoint;
4. 1/x as one UCRY.

The check runs against the parent branch `feature/sqls-aiaa-4q26` at
`99231b8`, which is what the fvm venv installs. It is the post-processors of
`hhl-structured-rewrite-2026-11` (real L: `realfit.py`, `real_structure.py`)
and `lugo-qpy-rewrite-2026-11` moved into the library. AQC is not in the
library.

All of it ran on a macos-laptop: exact statevector (`qiskit.quantum_info`),
Aer shots and transpilation. Nothing ran on hardware. This run supersedes
the one of 2026-11-19 about 20:30Z, which predated the real L.

## Method (`compare_branches.py`)

- **Baseline:** `build` under the fvm venv (quantum_linear_solvers `99231b8`,
  qiskit 2.6.0, Python 3.12.10), default `HHL()`.
- **New:** `build` under the branch clone's `.venv` (qiskit 2.6.0, Python
  3.12.12). The builds:
  - `standard`, the old build: `qpe_method="standard"`,
    `reciprocal_ucry=False`;
  - `lugo+ucry`: one dense controlled U^(2^k) per clock qubit, each
    synthesized by qiskit 2.6 directly;
  - `structured-qsdL+ucry`: the complex L;
  - `structured-realL+ucry`: the real L;
  - `default`: plain `HHL()`.
- **Cases:**
  - `rand3`, `rand4`: a random real A plus 4 I, as the Hermitian embedding
    [[0, A], [A^T, 0]] with b = [0, r];
  - `fvm5`, `fvm10`: the fvm nozzle first Newton step. H*t and b_herm are
    read from the 2026-02-26 LuGo generated qpy, as in
    `lugo-qpy-rewrite-2026-11/run_step0.py`. HHL rescales its evolution
    time, so it rebuilds the same U.
- **`hw`, under the fvm venv:**
  - two-qubit counts on FakeMarrakesh (Heron r2), FakeBoston (Heron r3) and
    FakeNighthawk;
  - for the fvm cases, 150000 Aer shots with seeds 1 to 10 and the fvm
    extraction of `run_step0.py`, the paper's shot protocol.
- **Scores:**
  - the statevector against the baseline's, bitwise and as a max amplitude
    difference;
  - HHL fidelity against `numpy.linalg.solve` on the system register at
    flag 1 and clock 0;
  - counts at level 2, `seed_transpiler` 1; all-to-all is `cx, rz, sx, x`.
- **Not run:**
  - the standard build is not transpiled at nb >= 5 (about 1.7e6 CX);
  - `fvm10` has no baseline build (an estimated 10 min). Its rows are
    scored against the new `lugo+ucry` state.

## Results (run 2026-11-19, about 23:40Z to 23:55Z)

Full rows: `results/fvm_euler_1d_solver/2026-11-19-hhl-csd-branch-check/`
(`summary.json`, `summary.xlsx`, `new/hw.json`).

Each cell gives two-qubit gates / two-qubit depth / depth.

| case | build | all-to-all | Heron r2 | Nighthawk | 150k-shot F median [min, max] |
|---|---|---|---|---|---|
| fvm5 | lugo+ucry | 16457 / 16210 / 49503 | 26375 / 24742 / 97153 | 27056 / 24563 / 93775 | 0.99835 [0.99718, 0.99897] |
| fvm5 | structured, complex L | 7497 / 7314 / 27005 | 12201 / 11382 / 45258 | 12473 / 11258 / 43789 | same |
| fvm5 | structured, real L (default) | 4810 / 3315 / 15795 | 6306 / 4226 / 16429 | 5836 / 3991 / 16372 | same |
| fvm5 | paper "LuGo 2.x + rewrite" | 4810 / 3222 / 15455 | 6305 / 4155 / 15932 | 5767 / 3775 / 15839 | 0.99835 [0.99718, 0.99897] |
| fvm10 | lugo+ucry | 75232 / 74361 / 223808 | 120820 / 113530 / 446839 | 125012 / 113109 / 429155 | 0.99715 [0.99621, 0.99842] |
| fvm10 | structured, complex L | 33472 / 32961 / 120054 | 57371 / 53612 / 206329 | 59085 / 52891 / 197720 | same |
| fvm10 | structured, real L (default) | 20585 / 11038 / 55997 | 23648 / 12771 / 54377 | 22595 / 12203 / 53204 | same |

- **Heron r3 equals Heron r2** in every row. FakeBoston and FakeMarrakesh
  give identical transpiles at seed 1.
- **Paper row:** `depth_nelem5.csv` and `fidelity_nelem5.csv` of
  `depth-hhl-lugo-rewrite-2026-11`.
- **Shot fidelities are identical across the three exact builds of a case.**
  Their states agree to 6e-12 per amplitude, so the same Aer seeds draw the
  same samples.

### What the check shows

- **The default is the paper's rewrite.**
  - The CX count at nelem 5 is equal: 4810 all-to-all.
  - Heron gives 6306 against 6305, and the 150k-shot fidelities are equal
    to five digits.
  - Two-qubit depth is 3315 against 3222 (2.9 %) and total depth 15795
    against 15455 (2.2 %). The CX template is the same. The fitted angles
    differ, because the paper fitted L from U read off the LuGo qpy, so the
    transpiler's merges, and with them the layering, differ.
- **The standard build is unchanged.**
  `HHL(qpe_method="standard", reciprocal_ucry=False)` gives a statevector
  bitwise equal to the baseline's default `HHL()` in all three cases built
  on both branches (rand3, rand4, fvm5).
- **Every build is exact.**
  - At fvm5 they match the baseline state to 6e-12 per amplitude; at fvm10
    they match `lugo+ucry` to 7e-12.
  - The HHL fidelity is 0.99995714 at nelem 5 and 0.99967316 at nelem 10,
    the recorded fvm step-0 values.
- **The real L is exact to roundoff.**
  - L is fitted with L-BFGS-B to 1 - F <= 1e-12, then a Gauss-Newton polish
    brings every entry within 1e-11. Measured entry errors are 7.0e-15,
    3.5e-15 and 3.6e-15 for the L circuits at nb 3, 4 and 5.
  - It costs 8, 28, 122 and 520 CX at nb 3, 4, 5 and 6, against 10, 46,
    206 and 878 for the complex L.
- **nelem 10 with real L is new.**
  - 520 CX is the first template tried that fits exactly. 500 CX stalled at
    1 - F 3e-12 after 205 s; 520 reached 1.4e-13 in 60 s from seed 1.
  - The result is 20585 CX all-to-all, against 264516 for the ORNL LuGo
    step-0 circuit (`note-20261108T0326Z-2db9`), 12.9x fewer.
  - The line template places disjoint CX pairs side by side, so two-qubit
    depth (11038) falls well below the count.
- **The levers, at nelem 5 all-to-all:**
  - ORNL LuGo, 57280 CX;
  - controlled blocks synthesized directly by qiskit 2.6 (`lugo+ucry`),
    16457;
  - structured with complex L, 7497;
  - structured with real L, 4810.

  `lugo+ucry` to real L is 3.4x in CX and 3.1x in total depth all-to-all,
  and 5.9x in total depth on Heron r2.
- **Build times** (laptop, one circuit):
  - nelem 5: 13 s with real L (nearly all of it the fit), 0.2 s with
    complex L, 2.0 s for `lugo+ucry`, 20 s standard;
  - nelem 10: 64 s, 0.8 s and 25 s respectively.

## Regenerate

```
B=../../../../fvm_euler_1d_solver/.venv/bin/python
N=../../../../../quantum_linear_solvers-hhl-csd/.venv/bin/python
O=~/q8020/hhl-csd-branch-check
$B compare_branches.py build $O/base --cases rand3 rand4 fvm5   # ~80 s
$N compare_branches.py build $O/new --cases rand3 rand4 fvm5    # ~3 min
$N compare_branches.py build $O/new --cases fvm10 --skip-standard  # ~6 min
$B compare_branches.py hw $O/new        # IBM counts and shots, ~5 min
$N compare_branches.py compare $O/base $O/new   # writes $O/summary.*
```
