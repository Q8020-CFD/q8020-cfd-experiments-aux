# nov2025 vs nov2026: HHL transpiler optimization level, nelem 5

The data and plot scripts for comparing the two fvm codebases across
transpiler optimization levels 0 to 3. Each codebase runs on its own libraries.
The comparison covers circuit width, depth, gate count, transpile time and
fidelity, for exact statevector (shots 0) and 150000 shots. Built
2026-11-07 from the final run of task 241f3c/20261107T0213-0001.

## Source

- Results: `results/fvm_euler_1d_solver/2026-11-07-hhl-nelem5-optlevel/` in
  q8020-cfd-experiments (commit `4d31eff9f`). It holds 16 cases:
  `<codebase>/shots<N>/opt<L>/`.
- Excluded: `2026-11-07-hhl-nelem5-optlevel-run1-flag-noop/`. In that run the
  level flag did not reach the ideal-backend transpile call, so every case ran
  at qiskit's default level.
- Codebases, with patches and versions in `../inputs/`:

| codebase | fvm commit | qiskit | qiskit-aer |
|---|---|---|---|
| nov2025 | `a5317f2b` + `-opt_level` patch | 1.2.4 | 0.15.1 |
| nov2026 | `d4a531bd` + `-opt_level` patch | 2.6.0 | 0.17.2 |

- Case settings: nelem 5, BDF1, CFL 1e10, at most 15 Newton steps, ideal Aer
  simulator, `seed_transpiler` 1 in both patched trees. nov2026 shots runs use
  `-seed 1` (Aer `seed_simulator`). nov2025 has no seed option, so its shots
  runs are unseeded.

## Files

| file | what it is |
|---|---|
| `build_compare_data.py` | results folder to `data/`; the only script that reads the results |
| `plot_compare.py` | `data/` to `plots/`; reads only the two CSVs; the settings block at the top sets the colors, which shots runs' circuits to plot and which fidelity summary to use |
| `data/per_step.csv` | one row per codebase, level, shots and Newton step (184 rows) |
| `data/per_case.csv` | one row per case (16 rows), summarised over its Newton steps |
| `data/compare.xlsx` | the same two tables as Excel sheets |
| `plots/circuit_vs_opt_level.png` | width, depth, gate count, transpile time per Newton step vs level |
| `plots/fidelity_vs_opt_level.png` | fidelity summary vs level, shots 0 and 150000 |
| `plots/fidelity_per_step.png` | fidelity per Newton step, one line per level |
| `plots/infidelity_per_step.png` | the same as 1 - fidelity on a log scale |

## Regenerate

From this folder, with the shared tooling venv:

```
~/.venvs/tooling/bin/python build_compare_data.py   # only if the results change
~/.venvs/tooling/bin/python plot_compare.py
```

`build_compare_data.py` takes an optional results folder argument. By default
it uses the results path above, relative to this folder.

## Columns

`per_step.csv`:
- `codebase`, `qiskit`, `qiskit_aer`, `opt_level`, `shots`, `step`.
- `fidelity`: the state fidelity of the HHL update against the classical
  Hermitian LU solve of the same Newton step, on normalized vectors.
- `l2_error_rel`, `l2_error_normalized`: the L2 error of the update against
  the LU solve, as a fraction of its norm, and the same on normalized vectors.
- `linsys_residual`: ||A dq - b||, the residual of the step's linear system.
- `newton_residual`: the nonlinear residual after the step.
- `circ_qubits`, `circ_depth`, `circ_gates`: width, depth and total gate
  count of the transpiled circuit. Gates of all types are counted; no codebase
  records the 2-qubit gate count.
- `circ_depth_generated`, `circ_gates_generated`: the circuit before
  transpiling. It is 5 deep with 19 instructions; the high-level blocks
  (QPE, 1/x, QPE inverse) are expanded by the transpiler.
- `circ_generate_s`, `circ_transpile_s`, `circ_run_s`: wall times in s.
- `condition_number`: condition number of the step's matrix.

`per_case.csv` adds:
- `converged`, `newton_steps`.
- `_max` and `_step0` circuit sizes.
- Transpile time, total and mean per Newton step, in s.
- Fidelity: mean over all steps, mean, min and max over all steps except the
  last, and the last step's value.
- The final step's `l2_error_rel` and `newton_residual`.

## Key numbers (shots 0 circuits)

| level | depth nov2025 | depth nov2026 | gates nov2025 | gates nov2026 | transpile s/step nov2025 | transpile s/step nov2026 |
|---|---|---|---|---|---|---|
| 0 | 689284 | 702509 | 689633 | 734779 | 19.6 | 0.68 |
| 1 | 689026 | 638248 | 689112 | 649091 | 17.6 | 1.5 |
| 2 | 689026 | 597460 | 689112 | 641910 | 53.6 | 24.3 |
| 3 | 689026 | 597205 | 689112 | 641755 | 50.8 | 56.5 |

Width is 14 qubits in every case.

## Read these before using the plots

- **Times carry contention.** Eight sweeper lanes ran at once on a 12-core
  laptop. Transpile and run times are indicative only. For example, nov2025
  level 3 with 150000 shots averaged 201 s per step against 51 s for its
  shots 0 twin.
- **Statevector final step.** At the converged last step (step 7), fidelity
  is about 0.165 in every case. The pad (`pad_eps` 1e-8 on each of the 17
  padded b entries) is larger than the real right-hand side, which is about
  4e-9 there. The step still cut the residual from 4.15e-9 to 8.91e-11, so
  convergence is unaffected. For this reason the default fidelity summary
  leaves out the last step.
- **nov2026 shots runs are identical across levels.** They are bit-identical
  over all 15 steps: the same seed samples from output distributions that
  differ only by floating-point rounding. On a noiseless simulator the level
  changes cost, not results, so these four cases amount to one sample.
- **nov2025 shots spread is sampling noise.** Those runs are unseeded, with
  one run per cell. The spread across levels (fidelity 0.969 to 0.999 on
  average) is not a level effect.
- **Shots fidelity measures direction only.** In shots mode the counts give
  only the size of each component. The signs come from the classical solution
  after a least-squares magnitude fit on the unsigned vector (sign-first off,
  the default). The direction is right (normalized L2 error 0.03 to 0.08), but
  the length is not (relative L2 error 0.6 to 0.9 at late steps). That error
  is why none of the shots runs converged in 15 steps.
- **Statevector extraction depends on what levels 2 and 3 leave alone.** It
  reads the amplitudes of the transpiled circuit after stripping its
  measurements. At levels 2 and 3 qiskit may delete diagonal gates just before
  a measurement (`RemoveDiagonalGatesBeforeMeasure`) or remove swaps into
  `circ.layout` (`ElidePermutations`). Neither happened here: the statevector
  results agree across levels to 6 or more digits at steps 0 to 6. A circuit
  that ends differently could break this.
