"""AQC compression sweep for the structured rewrite of the LuGo step-0 qpy.

For each CX budget per 4-qubit piece of L (W and V; 64 piece instances in
the circuit), fit AQC (best of seeds 1, 2), build the per-block circuit
(barriers), and report: piece 1 - F, all-to-all CX and two-qubit depth,
FakeNighthawk CZ, the full-state 1 - F against LuGo's stored circuit, the
HHL statevector fidelity, and an ESP estimate at ibm_chicago's measured
average (log ESP -11.31 over 6549 CZ on 2026-11-15, per CZ incl. 1q and
readout amortized). Simulation and transpilation only.
"""

import csv
import sys
import time
from pathlib import Path

import numpy as np
from qiskit import qpy, transpile
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeNighthawk

AUX = Path(__file__).resolve().parent
EXP = AUX.parents[2]  # q8020-cfd-experiments (aux checked out as submodule)
sys.path.insert(0, str(AUX))
import structured_rewrite as sr  # noqa: E402
from run_step0 import extract_sv, reference, x_part  # noqa: E402

LUGO = (EXP / "results/fvm_euler_1d_solver/2026-02-26-LuGo/circuits/"
        "circuit_generated_nelem5_iter0.qpy")
LOG_ESP_PER_CZ = -11.312099 / 6549
OUT = Path.home() / "q8020/aqc_tradeoff.csv"


def main(budgets: list[int]) -> None:
    with open(LUGO, "rb") as fh:
        circ = qpy.load(fh)[0]
    items, nb, nl = sr.walk(circ)
    mats = sr.block_unitaries(items)
    ht, b = reference(circ, nb)
    ref = {"x": x_part(np.linalg.solve(ht, b).real, 15),
           "A": ht[:16, 16:].real[:15, :15], "b": b[:15].real}
    sim = AerSimulator(method="statevector")
    pm0 = generate_preset_pass_manager(optimization_level=0, backend=sim)

    def run_sv(t):
        q = t.copy()
        q.save_statevector()
        return np.asarray(sim.run(q).result().get_statevector())

    sv_ref = run_sv(pm0.run(sr.reference(circ, items, mats)))
    nh = generate_preset_pass_manager(optimization_level=2,
                                      backend=FakeNighthawk(),
                                      seed_transpiler=1)
    rows = []
    for cx in budgets:
        t0 = time.time()
        info = []
        synth = sr.aqc_factory([cx], [1, 2], 1e-11, lambda m: None, info)
        new, rep = sr.build(circ, items, nb, mats, synth=synth, check=False,
                            barriers=True)
        t = transpile(new, basis_gates=sr.BASIS, optimization_level=2,
                      seed_transpiler=1)
        sv = run_sv(t)
        m = extract_sv(sv, nb, ref)
        tn = nh.run(new)
        cz = sum(1 for i in tn.data if i.operation.num_qubits == 2)
        row = {
            "cx_per_piece": cx,
            "piece_1mF_max": max(p["infidelity"] for p in info),
            "cx_per_block": rep.cx_per_block,
            "a2a_cx": t.count_ops().get("cx", 0),
            "a2a_2q_depth": t.depth(lambda i: i.operation.num_qubits == 2),
            "nighthawk_cz": cz,
            "nighthawk_2q_depth": tn.depth(
                lambda i: i.operation.num_qubits == 2),
            "state_1mF_vs_lugo": 1 - float(abs(np.vdot(sv_ref, sv)) ** 2),
            "hhl_fidelity": m["fidelity"],
            "esp_est_chicago": float(np.exp(cz * LOG_ESP_PER_CZ)),
            "seconds": round(time.time() - t0, 1),
        }
        rows.append(row)
        print(" ".join(f"{k} {v:.3g}" if isinstance(v, float) else
                       f"{k} {v}" for k, v in row.items()), flush=True)
        with open(OUT, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or [62, 56, 48, 40, 32, 24, 16])
