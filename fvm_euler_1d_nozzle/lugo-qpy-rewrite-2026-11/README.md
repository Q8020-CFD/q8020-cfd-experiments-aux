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
| nov26 | LuGo rerun, 2026-11-03, recorded results | 2.6.1 (the version in its qpy header; its results folder does not record one) | Frontier |
| rewrite | feb26 step-0 qpy, rewritten here, transpiled and run here | 2.6.0, Aer 0.17.2 | macos-laptop |
| control | feb26 step-0 qpy as stored, and re-transpiled, run here | 1.4.5 transpile / 2.6.0 | macos-laptop |
| rewrite_nov26 | nov26 step-0 qpy (nelem 5), rewritten here, transpiled and run here (added 2026-11-08) | 2.6.0, Aer 0.17.2 | macos-laptop |
| control_nov26_stored, control_nov26_qiskit26 | nov26 step-0 qpy as stored, and re-transpiled, run here | 2.6.1 transpile / 2.6.0 | macos-laptop |

Everything here is simulation. No step touches quantum hardware. The
all-to-all and IBM Heron gate counts come from transpiling only, to show
what each circuit would cost on hardware.

Only step 0 can be compared like for like: the qpy files kept locally are
step 0 only (the Frontier runs wrote one per step and trial; they were not
copied over). feb26 has them for nelem 5, 10 and 20; nov26 for nelem 5 only
(two files, copied to `results/fvm_euler_1d_solver/nov2025-rerun/LuGo-rerun/circuits/`).
The rewrite is a circuit-level result, not a Newton solve.

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

## The nov26 qpy: loading its 1/x (`load_qpy`, `recip_params`)

The nov26 files are `circuit_generated_statevector_nelem5_iter0.qpy` and
`circuit_transpile_statevector_shots150000_nelem5_iter0.qpy`, written by
qiskit 2.6.1 (QPY format 18). The transpiled one is the circuit of the
recorded nov26 run: its Aer-target depth and gate count equal the recorded 19506 and
20976 (plus the measurements run_step0 adds).

The generated one cannot be read by `qpy.load` in qiskit 2.6.0: its 1/x is
qiskit's `ExactReciprocalGate`, which qiskit 2.x writes with no parameters, so
the load fails with `TypeError ... missing 'num_state_qubits' and 'scaling'`,
and the file does not say what the gate was built with. The feb26 file holds
1/x as a plain unitary block, so it loads. For nov26:

- `recip_params` reads (nl, scaling, neg_vals) from the feb26 1/x block of the
  same nelem and accepts a candidate only if the rebuilt gate equals the block
  to 1e-9. Result at nelem 5: nl 8, scaling 2^-7 = 0.0078125, neg_vals True
  (the clock values 128 to 255 carry the negative branch). The first version
  of this check ignored negative angles and could not tell neg_vals apart;
  with the wrong convention the reloaded circuit was off by 1 - F = 0.014.
- `load_qpy(path, recip=(nl, scaling, neg_vals))` rebuilds the gate with those
  values while loading.
- `run_step0.py --source nov26` first checks that the nov26 generated circuit
  holds the same H t and b as feb26 (largest entry difference 2.9e-14 and 0).
- `infer_recip_angles.py` derives the same three values again, without feb26,
  from the nov26 stored run: with psi the stored circuit's final state and phi
  the state after state preparation and QPE, inv_QPE^dagger psi = R phi, and
  R's angle for each clock value c is read from the amplitude ratios.
  neg_vals True with scaling 2^-7 matches all 256 angles to 3e-13; neg_vals
  False is off by 2.0.
- The end-to-end check is in the statevector CSV: the reloaded generated
  circuit, transpiled here, equals the stored one with
  `state_fidelity_vs_nov26_stored` 1 to 1e-14.

## How the circuits are run and scored (`run_step0.py`)

- Variants per nelem: `feb26_stored` (the stored transpiled circuit, run as
  is), `feb26_qiskit26` (the stored generated circuit, transpiled here) and
  `rewrite_qiskit26` (the rewrite, transpiled here). With `--source nov26`
  the same three are `nov26_stored`, `nov26_qiskit26` and
  `rewrite_nov26_qiskit26`. Transpiles use level 2,
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
| 5 | nov26 | 2.6.1 | 19506 | 55580 | 79538 | 0.999957 | 0.99693 / 0.99785 / 0.99913 |
| 5 | rewrite | 2.6.0 | 31658 | 16412 | 25915 | 0.999957 | 0.99718 / 0.99835 / 0.99897 |
| 5 | rewrite_nov26 | 2.6.0 | 31658 | 16412 | 25915 | 0.999957 | 0.99718 / 0.99835 / 0.99897 |
| 10 | feb26 | 1.4.5 | 103093 | 264516 | 361768 | 0.999673 | 0.99642 / 0.99743 / 0.99934 |
| 10 | nov26 | 2.6.1 | 89129 | no qpy | no qpy | 0.999673 | 0.99694 / 0.99748 / 0.99860 |
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
- nov26 against feb26, same step-0 problem (H t and b equal to 2.9e-14):
  LuGo as stored needs 55580 all-to-all CX and 79538 Heron CZ with qiskit 2.6.1,
  against 57280 (1.4.5) and 78995 (3.0 % fewer, 0.7 % more). The rewrite of the nov26
  qpy has exactly the gate counts of the rewrite of the feb26 qpy (16412 and
  25915), because it replaces each block by the decomposition of the block's
  own unitary and the two runs hold the same unitaries. Against its own
  stored run it cuts 3.4x (all-to-all CX) and 3.1x (Heron CZ), total depth
  2.9x and 3.0x. The nov26 rewrite reproduces the stored nov26 state to
  1 - F = 8.7e-13, its statevector fidelity to 1.7e-10 and relative L2 error to
  1.2e-8 (absolute differences; the feb26 rewrite matched to about 1e-12 at
  nelem 5 and to 1e-9 and 2e-8 at nelem 10); the used shot counts are identical for all 10 seeds, the
  metrics for 9 (seed 9 differs: fidelity 0.998584 against 0.998616).
  The nov26 control's 10 shot fidelities equal the feb26 control's seed for
  seed (to 2e-15): the stored circuits prepare the same distribution.
- qiskit 1.x against 2.6: re-transpiling the feb26 qpy with qiskit 2.6
  leaves its CX and CZ counts unchanged (57280, 264516), so the saving comes
  from the rewrite, not from the qiskit version. qiskit 1.2.4 cannot read
  the feb26 qpy (format 13); 2.6.0 reads it.
- Even rewritten, the circuits are far beyond current hardware: about 300
  (Heron) to 1000 (best trapped-ion) two-qubit gates is the budget for a
  usable result, against 16412 and 75181 here.
- Not run: nelem 20 (feb26 only; nov26 has no qpy for it). Its qpy is here (18 qubits, Aer-target depth 464200,
  967 s per statevector step on Frontier). The rewrite took 12 s at nelem 5
  and 134 s at nelem 10, mostly computing block unitaries, so nelem 20 would
  take many minutes before any execution; it was left out to keep the runs
  short.

## Files

| file | what it is |
|---|---|
| `qpy_rewrite.py` | the post-processor; `qpy_rewrite.py <in.qpy> [-o out.qpy]` |
| `run_step0.py` | runs the three variants for given nelem and `--source` (feb26 or nov26); writes CSV and logs |
| `infer_recip_angles.py` | recovers the nov26 1/x rotation angles from the stored run and tests them against ExactReciprocalGate |
| `build_compare_data.py` | recorded feb26, nov26 and the run results to `data/` |
| `plot_compare.py` | `data/` to `plots/` |
| `data/per_set.csv` | one row per set and nelem: circuit size, step-0 metrics, full-run context |
| `data/step0_trials.csv` | one row per 150000-shot trial or seed, step 0 |
| `data/compare.xlsx` | the same two tables |
| `plots/circuit_cost_step0.png` | each LuGo run as stored against its qpy rewrite (feb26 at nelem 5 and 10, nov26 at nelem 5), in native gates: two-qubit count and total depth, all-to-all and IBM Heron |
| `plots/fidelity_step0.png` | step-0 1 - fidelity per shot trial, with the exact value, for the recorded runs, the rewrites and the controls |

Run results: `results/fvm_euler_1d_solver/2026-11-08-lugo-qpy-rewrite/`
(`nelem5/`, `nelem10/` for feb26, `nov26-nelem5/` for nov26).

## Regenerate

```
# runs (fvm repo venv, qiskit 2.6.0 / Aer 0.17.2), from this folder
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 5 --shots-nelem 5 --out ~/q8020/lugo-qpy-rewrite/nelem5
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 10 --shots-nelem 10 --out ~/q8020/lugo-qpy-rewrite/nelem10
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --source nov26 --nelem 5 --shots-nelem 5 --out ~/q8020/lugo-qpy-rewrite/nov26-nelem5
# then copy ~/q8020/lugo-qpy-rewrite/* to the results folder above, and
~/.venvs/tooling/bin/python build_compare_data.py
~/.venvs/tooling/bin/python plot_compare.py
```
