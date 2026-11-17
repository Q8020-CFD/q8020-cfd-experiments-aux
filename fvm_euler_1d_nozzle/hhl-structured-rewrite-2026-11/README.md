# fvm HHL step 0: an exact structured rewrite from the pre-LuGo circuit

Takes the first-Newton-step HHL circuit of the fvm Euler nozzle solver
(nelem 5) as the fvm solver itself generated it, before any LuGo step, and
rewrites it into an equivalent circuit with 8.3x (exact) to 15.5x (AQC,
1 - F 2.5e-12) less two-qubit depth all-to-all than the ORNL LuGo circuit
for the same step, and 6.7x to 17.5x on IBM Heron. Everything here is
simulation (Aer) and transpilation on a macos-laptop. Nothing ran on
quantum hardware; the IBM Heron and Nighthawk numbers are transpile-only.

## Input

`results/fvm_euler_1d_solver/nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/circuit_generated_statevector_nelem5_iter0.qpy`
(70 MB): fvm `main` `ef7f0a8b` on the 2025-11 package stack (qiskit 1.2.4,
`jw676/quantum_linear_solvers@a94cf63`), run on Frontier on 2026-11-03.
Recorded step-0 statevector fidelity 0.9999571 (`hhl_metrics_nelem5_statevector.csv`),
the same as the LuGo runs.

Its top level is state preparation of b (5 system qubits), `QPE` (8 clock
qubits plus the system), `1/x` (clock plus ancilla) and `QPE_dg`, 14 qubits
in all. Inside `QPE`, clock qubit k carries one instruction
`ccircuit-...**2^k`: a gate-by-gate controlled copy of a synthesized U
circuit, repeated 2^k times. `QPE_dg` holds the inverses. So the pre-LuGo
circuit has 2 x 255 = 510 controlled-U copies, about 1.75M CX all-to-all
(estimate: one copy transpiled, 3436 CX, times 510, plus the rest).

## What the rewrite does (`structured_rewrite.py`)

**Input: LuGo's qpy or the pre-LuGo one.** Both give the same circuit,
because both hold the same U (to 2.5e-14). `run_test.py --input lugo`
starts from `2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy`
(results in `results/fvm_euler_1d_solver/2026-11-17-hhl-structured-rewrite-from-lugo/`).
The default is the pre-LuGo qpy above.

**Classical work, counted against LuGo's.** LuGo builds each of its 16
blocks (8 powers, 8 inverse powers, synthesized separately) with qiskit's
quantum Shannon decomposition (QSD) of U^(+-2^k), then controls it gate by
gate. This was verified: its base circuits equal qiskit 1.2.4
`qs_decomposition` gate for gate, 444 CX each. The pre-LuGo build ran one
QSD of U the same way.

The rewrite takes those QSD intermediate values as available and recomputes
the ones it needs, since LuGo's code is not:

- U itself;
- the first-step CSD factor of U^1 (`u1`, `u2` of the same `cossin` call;
  identical values);
- one demultiplex and two 4-qubit QSDs, the next level of the same
  algorithm. These run on that factor with a diagonal phase folded in, so
  their values differ from LuGo's by that diagonal.

Everything else is matrix products and 2 x 2 arithmetic. AQC, the second
pass, is a numerical fit with no counterpart in LuGo.

1. **U** is read from the first block by multiplying out its gates. For
   LuGo input, each block's power, which its name does not carry, is found
   by matching its unitary against L Rx(m theta) L^dag.
2. **One CSD of U**, split on the system MSB (the Hermitian-embedding
   qubit): U = L T L^dag with L = L0 (+) L1 block diagonal, and T a direct
   sum of 16 2 x 2 blocks. Because U = exp(iHt) with H = [[0, A], [A^T, 0]],
   L0 and L1 are the singular-vector matrices of A (up to signs, phases and
   order). Each 2 x 2 block is put in the form D^dag Rx(theta_i) D with D
   diagonal, and D is folded into L.
3. **Every controlled-U^m** (m = +-2^k) becomes
   `L^dag . H(msb) . UCRZ . H(msb) . L`, where the UCRZ carries m theta_i
   on clock 1 and 0 on clock 0. U^m = L T^m L^dag holds for every integer
   m, so one L serves all 16 blocks; only the middle UCRZ is controlled.
   L is synthesized once: demultiplexed into a 4-qubit W, a 16-CX UCRZ and
   a 4-qubit V; L^dag is its circuit inverse.
4. **1/x** becomes one `UCRYGate` (`_rewrite_recip` from the sibling
   `lugo-qpy-rewrite-2026-11`).

Per block: L^dag (206 CX) + controlled UCRZ (32) + L (206) = 444 CX, against
3436 in each LuGo block and in each pre-LuGo controlled-U copy.

Blocks are not merged with each other: each keeps its own L and L^dag.
Cancelling L between blocks would collapse the QPE into diagonal phases in
A's singular basis, which amounts to solving the system classically; see the
project-space notes. The compiler does hold A's singular vectors (L) and
values (in theta): the same information the pre-LuGo transpile and LuGo's
own block synthesis compute.

**Variants.** `exact` synthesizes W and V with `qs_decomposition` (95 CX
each). `aqc` uses qiskit's Approximate Quantum Compiling (AQC) on W and V:
a fixed CX layout whose single-qubit angles are optimized numerically
against the target. It is approximate in principle; the run records 1 - F
per piece.

## Checks and counts (`run_test.py`)

- Every block against the stored block's 64 x 64 unitary, global phase
  included.
- Exact statevector against the stored circuit (blocks as their unitaries),
  and the HHL metrics of `lugo-qpy-rewrite-2026-11/run_step0.py`
  (extraction as fvm `hhl_solve`), beside the recorded run.
- 10 Aer seeds x 150000 shots, the same seeds for the stored circuit; the
  used outcomes (ancilla 1, clock 0) compared count for count.
- Gate counts at level 2, `seed_transpiler` 1: all-to-all `cx, rz, sx, x`,
  `FakeMarrakesh` (IBM Heron r2) and `FakeNighthawk`, for both variants and
  for the LuGo step-0 qpy (feb26, generated).

## Results (nelem 5, step 0, run 2026-11-15T19:59:53Z)

Full tables and provenance:
`results/fvm_euler_1d_solver/2026-11-15-hhl-structured-rewrite/`.

| target | metric | LuGo | exact | AQC | LuGo / exact | LuGo / AQC |
|---|---|---|---|---|---|---|
| all-to-all | 2q gates | 57280 | 7347 | 5296 | 7.8x | 10.8x |
| all-to-all | 2q depth | 57179 | 6867 | 3689 | 8.3x | 15.5x |
| all-to-all | total depth | 143699 | 25166 | 16695 | 5.7x | 8.6x |
| Heron | 2q gates | 78993 | 12257 | 6837 | 6.4x | 11.6x |
| Heron | 2q depth | 73567 | 10929 | 4208 | 6.7x | 17.5x |
| Heron | total depth | 287084 | 43754 | 18753 | 6.6x | 15.3x |
| Nighthawk | 2q gates | 81818 | 12614 | 6421 | 6.5x | 12.7x |
| Nighthawk | 2q depth | 73670 | 10975 | 4285 | 6.7x | 17.2x |
| Nighthawk | total depth | 271971 | 41884 | 19043 | 6.5x | 14.3x |

- **Equivalence.** Exact: every block equals the stored block to 4.6e-12,
  the full state equals the stored circuit's to 1 - F = 1.2e-12, and the
  step-0 fidelity 0.99995714 matches the recorded run to 3e-14. AQC (both
  4-qubit pieces of L at 62 CX, 1 - F 1.0e-12 and 1.6e-12): block entries
  within 1.5e-6, full state 1 - F = 2.5e-12, fidelity unchanged to 5e-9.
- **Shots** (10 seeds x 150000): exact used counts equal the stored
  circuit's for all 10 seeds, AQC for 7; fidelity spreads are the same.
- **Two-qubit depth below count.** The AQC pieces use qiskit's `spin` CX
  layout, which puts disjoint CX pairs side by side, so two-qubit depth
  (3689) falls well below the count (5296). The exact form is serial
  (6867 of 7347).
- **Against the pre-LuGo circuit** (about 1.75M CX all-to-all), the exact
  rewrite is about 240x fewer two-qubit gates and AQC about 330x.
- **Hardware.** The AQC rewrite is 6421 CZ and two-qubit depth 4285 on
  Nighthawk, under the 10000-gate figure IBM gives for later Nighthawk
  revisions. Depth, not count, is the binding limit for this serial circuit:
  about 4300 two-qubit layers plus single-qubit layers is of order 1 ms
  against coherence times of order 0.1 to 0.3 ms.

## Regenerate

```
# fvm repo venv (qiskit 2.6.0, Aer 0.17.2), from this folder
../../../../fvm_euler_1d_solver/.venv/bin/python run_test.py --input lugo --out ~/q8020/hhl-structured-rewrite-lugo
../../../../fvm_euler_1d_solver/.venv/bin/python run_test.py --out ~/q8020/hhl-structured-rewrite
# then copy ~/q8020/hhl-structured-rewrite/nelem5 to
# results/fvm_euler_1d_solver/2026-11-15-hhl-structured-rewrite/
```

`structured_rewrite.py <in.qpy> [-o out.qpy]` writes the exact rewritten
circuit (no measurements).

## IBM hardware run, ibm_chicago, 2026-11-15: null, as predicted

`ibm_submit.py` (dry run by default) and `ibm_analyze.py`. The circuit is
the AQC rewrite, written by
`structured_rewrite.py <in.qpy> --aqc 62,64,68,72 -o <out.qpy>` (same AQC
pieces as the test run, block error 1.48e-6).

**Job design.** One SamplerV2 job with four PUBs on the same 14 physical
qubits:

- `main`: the circuit, 1,000,000 shots;
- `cal0` and `cal1`: readout calibration, 100,000 shots each;
- `ctrl`: a positive control, 100,000 shots. It is only the state
  preparation of b (39 CZ after routing) and should give |b|^2 on the
  system register.

Error suppression and mitigation:

- dynamical decoupling, XY4, ALAP;
- Pauli twirling of gates and measurements, 10,000 shots per
  randomization;
- readout correction of the counts. Measurement twirling makes readout
  errors symmetric, so per-qubit flip rates from `cal0` and `cal1` give a
  tensored inverse. This is the counts analogue of TREX, which itself is an
  Estimator option;
- noise-floor subtraction from the ancilla 1, clock not 0 outcomes;
- `max_execution_time` set to 1.5x the QPU estimate.

**Not used: PEC, PEA, ZNE.** These are EstimatorV2 methods for expectation
values.

- PEC's sampling overhead is about exp(4 lambda), with lambda = -log ESP
  ≈ 11, so about e^45 ≈ 1e19 times the shots.
- ZNE needs a measurable signal to extrapolate from.

**Pre-flight, ibm_chicago** (Nighthawk r2, live calibration,
2026-11-15T20:28Z, best of 16 layout seeds):

| quantity | value |
|---|---|
| CZ | 6549 |
| two-qubit depth | 4427 |
| scheduled duration | 569 us |
| median T1 / T2 on the chosen qubits | 159 / 176 us |
| ESP (gates and readout, no idling) | 1.2e-5 |
| expected signal share of the used outcomes | 1.8e-4 |
| QPU estimate | 685 s (11.4 min) |
| `max_execution_time` cap | 1028 s |

ibm_phoenix was 10x worse (ESP 8.6e-7).

**Detectability.** `ibm_analyze.py` scores every estimator against its own
maximally mixed null. The fvm sign step (signs of x_ref) makes pure noise
score fidelity about 0.54, so the null is the baseline, not zero.

On synthetic counts (global depolarizing to circuit fidelity F, 1.5 %
readout flips, 1e6 shots), the signal is detected at F = 0.03 (z about 10)
and indistinguishable from the null at F = 0.003. The pre-flight ESP is
about 250x below that, so the expected result is a null, in line with the
Cole-Hopf hardware runs: about 19.3k CZ depolarized fully
(note-20260924-0006, note-20260924-0007). The control should still come
out near 1.

A local noiseless run of the four PUBs (`--local 20000`) checks the job
structure, bit order and qubit mapping: main fidelity 0.985, control
0.99984.

**Outcome** (job `dbt1dqreq3sc73ev92sg`, submitted 2026-11-15T20:32:44Z,
774 s QPU; full record in
`results/fvm_euler_1d_solver/2026-11-15-hhl-structured-ibm-chicago/`):

- **The output is maximally mixed.** P(ancilla 1) is 0.500 (ideal 0.0144),
  and the used outcomes hold 0.00191 (uniform 0.00195, ideal 0.0143).
- **The fidelity is on the null.** It is 0.541 against a null of
  0.536 +- 0.017 (z +0.26), and readout correction and background
  subtraction change nothing.
- **The control** puts the right states on top in the right order, but
  scores only 0.60 against |b|^2, where its ESP is 0.90: the device ran
  below its calibration.

## Per-block counts (`--barriers`, added 2026-11-17)

`--barriers` on `structured_rewrite.py` and `run_test.py` puts a barrier
after every block. Without it, qiskit's level-2 transpile cancels some
gates across block seams, where one block's L meets the next block's L^dag:
150 CX at nelem 5, 7347 against 7497. With it, the whole-circuit count is
the sum of the parts, and nothing is merged across blocks.

The paper's table uses these counts:
`results/fvm_euler_1d_solver/2026-11-17-hhl-structured-rewrite-from-lugo/nelem5-barriers/`,
and `nelem10-barriers/` for the exact rewrite at nelem 10: 1820 CX per
block, 33472 in all against LuGo's 264516.
