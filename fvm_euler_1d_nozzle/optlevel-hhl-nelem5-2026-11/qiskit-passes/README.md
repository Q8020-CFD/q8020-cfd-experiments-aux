# What each optimization level runs: qiskit 1.2.4 vs 2.6.0

The pass lists behind the nov2025 vs nov2026 optimization level sweep
(`results/fvm_euler_1d_solver/2026-11-07-hhl-nelem5-optlevel/`), and a LaTeX
write-up of what the levels do. Built 2026-11-14.

| file | what it is |
|---|---|
| `dump_passes.py` | builds the preset pass manager for `transpile(circ, AerSimulator())` at levels 0 to 3 with `seed_transpiler` 1, and writes every stage's passes with loops and conditions nested |
| `passes_qiskit1.2.4.txt` | its output in the nov2025 venv (qiskit 1.2.4, qiskit-aer 0.15.1) |
| `passes_qiskit2.6.0.txt` | its output in the nov2026 venv (qiskit 2.6.0, qiskit-aer 0.17.2) |
| `optlevel_qiskit124_vs_260.tex` | LaTeX fragment: pass table, measured depth, gates and transpile time per level, and prose. Core LaTeX only; `\input` it into the document body |

Regenerate the pass lists, from `/Users/agallojr/proj/src/q8020`:

```
fvm-optlvl-nov2025/.venv/bin/python -I <this folder>/dump_passes.py
fvm-optlvl-nov2026/.venv/bin/python -I <this folder>/dump_passes.py
```

The numbers in the `.tex` come from
`../compare-nov2025-nov2026/data/per_case.csv` (step 0, shots 0). The gate mix
quoted for qiskit 1.2.4 (cu 346800, ccx 226696, cp 114296 of 689126 gates)
comes from the kept step-0 circuit
`results/fvm_euler_1d_solver/nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/circuit_transpile_statevector_nelem5_iter0.qpy`
(fvm `main` on the qiskit 1.2.4 stack, default level 1). No qiskit 2.x HHL
circuit is kept, so the 2.6.0 gate mix is unknown.

Findings from the source, both versions:

- `transpile()` with no level uses level 1 on 1.2.4 and level 2 on 2.6.0
  (`qiskit/compiler/transpiler.py`).
- The AerSimulator target has no coupling map, so layout and routing are empty
  at every level. The levels differ only in their init and optimization passes.
- 2.6.0 replaces the 1.2.4 two-qubit block resynthesis (`Collect2qBlocks`,
  `ConsolidateBlocks`, `UnitarySynthesis`) with `TwoQubitPeepholeOptimization`,
  and adds `RemoveIdentityEquivalent` at levels 2 and 3.
