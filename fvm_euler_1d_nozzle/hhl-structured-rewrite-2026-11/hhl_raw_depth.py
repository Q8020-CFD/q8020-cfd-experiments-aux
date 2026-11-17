"""Depth of the raw (pre-LuGo) HHL step-0 circuit, transpiled like the rest.

qiskit 2.6.0, level 2, seed_transpiler 1, to all-to-all cx/rz/sx/x,
FakeMarrakesh and FakeNighthawk. Measurements stripped. Transpile only.
"""
import csv
import sys
import time
from pathlib import Path

from qiskit import qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeMarrakesh, FakeNighthawk

P = ("/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
     "fvm_euler_1d_solver/nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/"
     "719a35aa/circuit_generated_statevector_nelem5_iter0.qpy")
OUT = Path.home() / "q8020/hhl_raw_depth.csv"
with open(P, "rb") as fh:
    c = qpy.load(fh)[0].remove_final_measurements(inplace=False)
rows = []
for tgt in sys.argv[1:] or ["a2a", "heron", "nighthawk"]:
    kw = ({"basis_gates": ["cx", "rz", "sx", "x"]} if tgt == "a2a" else
          {"backend": FakeMarrakesh() if tgt == "heron" else FakeNighthawk()})
    pm = generate_preset_pass_manager(optimization_level=2, seed_transpiler=1,
                                      **kw)
    t0 = time.time()
    t = pm.run(c)
    row = {"target": tgt,
           "two_qubit_gates": sum(1 for i in t.data
                                  if i.operation.num_qubits == 2),
           "two_qubit_depth": t.depth(lambda i: i.operation.num_qubits == 2),
           "depth": t.depth(), "transpile_s": round(time.time() - t0, 1)}
    rows.append(row)
    print(row, flush=True)
    del t
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
