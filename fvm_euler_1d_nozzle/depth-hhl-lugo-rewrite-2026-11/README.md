# Step-0 depth and 150k-shot fidelity: HHL, LuGo, the real-L rewrite and AQC, nelem 5

`plot_depth.py` reads recorded results and writes `depth_nelem5.csv`,
`fidelity_nelem5.csv` and `figures/depth_nelem5.{pdf,png}`. Nothing is run:
no circuit is built, transpiled or simulated here.

Run with the tooling venv: `~/.venvs/tooling/bin/python -I plot_depth.py`.

## The six circuits

These are the first Newton step of the fvm nozzle, nelem 5, 14 qubits. All
are compiled the same way: qiskit 2.6.0, optimization level 2,
`seed_transpiler` 1, to all-to-all `cx, rz, sx, x`, FakeMarrakesh (IBM
Heron r2) and FakeNighthawk, on macos-laptop. "1.x" and "2.x" therefore
name the stack that built each circuit, not the compiler.

| column | circuit | depth source |
|---|---|---|
| HHL 1.x | pre-LuGo HHL built by qiskit 1.2.4 (fvm `ef7f0a8b`, Frontier, 2026-11-03) | `results/.../2026-11-17-hhl-structured-rewrite-from-lugo/hhl-raw-depth/hhl_raw_depth.csv` |
| HHL 2.x | HHL built by qiskit 2.6.0 from the same step-0 system | `results/.../2026-11-18-table8-qiskit26/table8_columns.csv` |
| LuGo 1.x | ORNL LuGo, 2026-02-26 run (qpy written by qiskit 1.4.5) | `results/.../2026-11-17-hhl-structured-rewrite-from-lugo/nelem5-barriers/counts.csv` |
| LuGo 2.x | ORNL LuGo rerun, 2026-11-03 (qiskit 2.6.1) | `results/.../2026-11-18-table8-qiskit26/table8_columns.csv` |
| LuGo 2.x + rewrite | exact structured rewrite, real L at 122 CX, a barrier after each block | `results/.../2026-11-17-hhl-structured-rewrite-from-lugo/nelem5-barriers-realL-aqc106/counts.csv`, variant `exact` |
| rewrite + AQC (L 74 CX) | the rewrite with L refitted at 74 CX (approximate: 1 - F of L 7.0e-2, full state 9.4e-3 against the exact circuit) | `results/.../2026-11-17-hhl-structured-rewrite-from-lugo/nelem5-barriers-realL-aqc74/counts.csv`, variant `aqc` |

The rewrite was run on the LuGo 1.x qpy. It depends only on U, b and the 1/x
angles. All four circuits hold the same QPE blocks: HHL 2.x against LuGo 2.x
to 7.1e-12, and HHL 2.x against HHL 1.x to 8.4e-12 (`table8_check.json`).
The LuGo 1.x circuit agrees with the pre-LuGo HHL to 2.5e-14
(`hhl-structured-rewrite-2026-11/README.md`). So the rewrite of the LuGo 2.x
qpy is the same circuit, and its depth is fixed by the real-L template.

## Fidelity at 150000 shots, step 0

Fidelity is the median over trials, or over Aer seeds for the rewrite (see
`fidelity_nelem5.csv` for min and max):

| column | n | median | source |
|---|---|---|---|
| HHL 1.x | 20 | 0.99816 | `nov2025-rerun` `nov_pkgs`, 11-04 and 11-05 pooled |
| HHL 2.x | 10 | 0.99827 | `nov2025-rerun` `latest_pkgs` (qiskit 2.6.2) |
| LuGo 1.x | 10 | 0.99871 | `2026-02-26-LuGo` `shots_150000` |
| LuGo 2.x | 10 | 0.99785 | `nov2025-rerun` `LuGo-rerun` |
| rewrite | 10 | 0.99835 | real-L run above, Aer seeds 1 to 10 |
| AQC 74 | 10 | 0.96916 | `nelem5-barriers-realL-aqc74`, Aer seeds 1 to 10 |

For the five exact circuits the medians span 0.99785 to 0.99871 and so
differ by less than 0.001. That
is inside the trial-to-trial range of about 0.002: the five are exact
constructions of the same operator, so their shot fidelities differ only by
sampling.

AQC at 74 CX is approximate, and its fidelity is lower: the median is 0.96916.
Its statevector fidelity, 0.968983, agrees, so the fvm sign step does not
inflate the shot score at this level.

The figure shows each median as `F = ...` under its column label. It uses one
y axis, for depth.
