# LuGo HHL: an exact qpy rewrite of the step-0 circuit, against feb26 and nov26

Takes the step-0 (first Newton step) HHL circuit that the 2026-02-26 ORNL
LuGo run stored as qpy, rewrites it into an exactly equivalent circuit with
about 3.5x fewer two-qubit gates, and runs the stored and rewritten circuits
on the Aer ideal simulator (exact statevector and 150000 shots, Aer seeds 1
to 10) on a macos-laptop with qiskit 2.6.0 / Aer 0.17.2. The results are set
beside the recorded LuGo runs:

| set | what | qiskit | where |
|---|---|---|---|
| feb26 | ORNL LuGo run, 2026-02-26, recorded results | 1.4.5 (the version that wrote its qpy) | Frontier |
| nov26 | LuGo rerun, 2026-11-03, recorded results | 2.6 (per operator; not recorded in its results folder) | Frontier |
| rewrite | feb26 step-0 qpy, rewritten here, transpiled and run here | 2.6.0, Aer 0.17.2 | macos-laptop |
| control | feb26 step-0 qpy as stored, and re-transpiled, run here | 1.4.5 transpile / 2.6.0 | macos-laptop |

Everything here is simulation. No step touches quantum hardware. The
all-to-all and IBM Heron gate counts come from transpiling only, to show
what each circuit would cost on hardware.

Only step 0 can be compared like for like: the qpy files kept locally are
step 0 only (the Frontier run wrote one per step and trial; they were not
copied over), and nov26 kept none. The rewrite is a circuit-level result,
not a Newton solve.

## What the qpy post-processor does (`qpy_rewrite.py`)

Input: the generated (untranspiled) circuit, e.g.
`results/fvm_euler_1d_solver/2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy`.
Its top level is state preparation of b on the nb system qubits, `QPE` (nl
clock qubits plus the system register), `1/x` (clock plus ancilla),
`inv_QPE`, a barrier and the measurements. For nelem 5, nb = 5 (15 unknowns,
padded to 16, Hermitian embedding to 32), nl = 8, 14 qubits in all.

1. **QPE and inv_QPE blocks.** Each instruction inside `QPE` and `inv_QPE`
   that acts on nb + 1 qubits is one controlled-U^(2^k) block: one clock
   qubit and the system register. LuGo stores each as a controlled
   6-qubit gate of about 1349 cu, ccx and cp gates (3436 CX after
   decomposition). The post-processor computes the block's 64 x 64 unitary
   from those stored gates and replaces the block with qiskit's quantum
   Shannon decomposition (`qs_decomposition`) of that matrix, 1004 CX for
   nelem 5. There are 2 nl = 16 such blocks. The H gates and the QFT inside
   `QPE` are kept as stored.
2. **1/x.** The post-processor computes its 2^(nl+1) x 2^(nl+1) unitary and
   checks that it is a uniformly controlled RY on the ancilla: block diagonal
   over the 2^nl clock values, a real 2 x 2 rotation in each block. It reads
   the 2^nl angles from the matrix and replaces the block with one
   `UCRYGate` (256 CX for nelem 5, against 2176 as stored). If the check
   fails the block is kept.
3. **Everything else** (state preparation, barrier, measurements) is kept.

Each replacement is checked against the stored block by matrix equality,
global phase included (largest entry difference 1.6e-13 for the QSD blocks
and 4.2e-15 for 1/x at nelem 5). The rewrite uses only each block's own
unitary. It never diagonalizes anything and never merges blocks: those steps
would amount to solving Ax = b classically (see the project-space note).

## How the circuits are run and scored (`run_step0.py`)

- Variants per nelem: `feb26_stored` (the stored transpiled circuit, run as
  is), `feb26_qiskit26` (the stored generated circuit, transpiled here) and
  `rewrite_qiskit26` (the rewrite, transpiled here). Transpiles use level 2,
  `seed_transpiler` 1, for `AerSimulator(method="statevector")`; the
  measurement-free copy is transpiled separately for the statevector run.
- Gate counts: the same circuits transpiled only, at level 2, for an
  all-to-all `cx, rz, sx, x` basis and for `FakeMarrakesh` (IBM Heron r2,
  heavy-hex, cz).
- Reference, from the qpy alone: H t is the matrix log of the first QPE
  block's controlled unitary (its eigenphases lie inside +-pi, and the second
  block is checked to be its square); b_herm is the state-preparation
  amplitudes; x_ref is the x part of H^-1 b_herm. Its direction matches the
  feb26 recorded LU solution to 1 - 2e-16.
- Extraction and metrics mirror the fvm HHL step (`time_solvers.hhl_solve`
  and `quantum_tools` at fvm `a5317f2b`): the amplitudes (statevector) or
  counts (shots) with ancilla 1 and clock 0, normalized; the x part of the
  Hermitian solution; the least-squares length fit against A and b
  (`-hhl_scale leastsq`, which the feb26 run used: it reproduces the recorded
  relative L2 error to 1.6e-12, and the `true_sol` length does not); for
  shots, the signs of x_ref after the fit; then fidelity, relative and
  normalized L2 error. All are invariant to the unknown scale t.

## Key numbers (first Newton step)

| nelem | set | qiskit | Aer-target depth | all-to-all CX | Heron CZ | statevector fidelity | 150000-shot fidelity, min / median / max |
|---|---|---|---|---|---|---|---|
| 5 | feb26 | 1.4.5 | 22394 | 57280 | 78995 | 0.999957 | 0.99670 / 0.99871 / 0.99904 |
| 5 | nov26 | 2.6 | 19506 | no qpy | no qpy | 0.999957 | 0.99693 / 0.99785 / 0.99913 |
| 5 | rewrite | 2.6.0 | 31658 | 16412 | 25915 | 0.999957 | 0.99718 / 0.99835 / 0.99897 |
| 10 | feb26 | 1.4.5 | 103093 | 264516 | 361768 | 0.999673 | 0.99642 / 0.99743 / 0.99934 |
| 10 | nov26 | 2.6 | 89129 | no qpy | no qpy | 0.999673 | 0.99694 / 0.99748 / 0.99860 |
| 10 | rewrite | 2.6.0 | 147413 | 75181 | 113240 | 0.999673 | 0.99621 / 0.99715 / 0.99842 |

- The rewrite cuts two-qubit gates 3.5x on an all-to-all basis and 3.0x
  (nelem 5) to 3.2x (nelem 10) on IBM Heron, with an output state equal to
  the stored circuit's to 1 - F = 2.3e-13 and 1.6e-12. Its statevector
  metrics equal the recorded feb26 and nov26 values to about 1e-12 at
  nelem 5, and to 1e-9 (fidelity) and 2e-8 (relative L2) at nelem 10. For
  every seed its shot counts used by the extraction equal the stored
  circuit's.
- The Aer-target depth, the only depth feb26 and nov26 recorded, makes the
  rewrite look deeper (31658 vs 22394 at nelem 5). The Aer simulator accepts
  cu, ccx and cp as single gates, and the rewrite is already in cx and
  single-qubit gates. In the same native gates the rewrite is shallower as
  well: total depth 143702 to 48041 (nelem 5) and 661024 to 221188
  (nelem 10) all-to-all, 287085 to 94178 and 1329690 to 433044 on Heron,
  3.0x to 3.1x; two-qubit depth 3.1x to 3.6x. Compare circuits on those.
- Shot spreads overlap for all three sets. The rewrite's 10 seeds and the
  recorded 10 trials are independent samples of the same distribution;
  differences in median (for example 0.99835 against 0.99871 at nelem 5) are
  sampling noise. Only about 1.4 to 1.6 % of the 150000 shots (median 2140
  and 2457) have ancilla 1 and clock 0 and feed the solution.
- qiskit 1.x against 2.6: re-transpiling the feb26 qpy with qiskit 2.6
  leaves its CX and CZ counts unchanged (57280, 264516), so the saving comes
  from the rewrite, not from the qiskit version. qiskit 1.2.4 cannot read
  the feb26 qpy (format 13); 2.6.0 reads it.
- Even rewritten, the circuits are far beyond current hardware: about 300
  (Heron) to 1000 (best trapped-ion) two-qubit gates is the budget for a
  usable result, against 16412 and 75181 here.
- Not run: nelem 20. Its qpy is here (18 qubits, Aer-target depth 464200,
  967 s per statevector step on Frontier). The rewrite took 12 s at nelem 5
  and 134 s at nelem 10, mostly computing block unitaries, so nelem 20 would
  take many minutes before any execution; it was left out to keep the runs
  short.

## Files

| file | what it is |
|---|---|
| `qpy_rewrite.py` | the post-processor; `qpy_rewrite.py <in.qpy> [-o out.qpy]` |
| `run_step0.py` | runs the three variants for given nelem; writes CSV and logs |
| `build_compare_data.py` | recorded feb26, nov26 and the run results to `data/` |
| `plot_compare.py` | `data/` to `plots/` |
| `data/per_set.csv` | one row per set and nelem: circuit size, step-0 metrics, full-run context |
| `data/step0_trials.csv` | one row per 150000-shot trial or seed, step 0 |
| `data/compare.xlsx` | the same two tables |
| `plots/circuit_cost_step0.png` | feb26 as stored against the rewrite, in native gates: two-qubit count and total depth, all-to-all and IBM Heron |
| `plots/fidelity_step0.png` | step-0 1 - fidelity per shot trial, with the exact value |

Run results: `results/fvm_euler_1d_solver/2026-11-08-lugo-qpy-rewrite/`.

## Regenerate

```
# runs (fvm repo venv, qiskit 2.6.0 / Aer 0.17.2), from this folder
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 5 --shots-nelem 5 --out ~/q8020/lugo-qpy-rewrite/nelem5
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 10 --shots-nelem 10 --out ~/q8020/lugo-qpy-rewrite/nelem10
# then copy ~/q8020/lugo-qpy-rewrite/* to the results folder above, and
~/.venvs/tooling/bin/python build_compare_data.py
~/.venvs/tooling/bin/python plot_compare.py
```
