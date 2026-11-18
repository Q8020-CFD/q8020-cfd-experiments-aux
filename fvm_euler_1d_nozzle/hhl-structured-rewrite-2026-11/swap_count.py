"""SWAP gates routing inserts into the Table 8 circuits, on FakeMarrakesh
(Heron r2) and FakeNighthawk.

A transpiled circuit holds no SWAP: the basis translation turns each routed
SWAP into 3 two-qubit native gates (some later merge with neighbours). So the
SWAPs are counted on the circuit after the init, layout and routing stages
of the same preset pass manager as Table 8 (level 2, seed_transpiler 1), and
set against the two-qubit gates the full transpile adds over all-to-all.

Circuits: the qiskit 2.6.0 base HHL (built as table8_columns.py builds it),
the nov26 LuGo, and the structured rewrite with real L, exact (122 CX) and
with L fitted by AQC at 106, 90, 74 and 58 CX, barriers after every block.
Run with the fvm solver venv. Usage: swap_count.py [--skip-hhl] [--out CSV]
"""
import argparse
import csv
import sys
import time
from pathlib import Path

from qiskit.transpiler import StagedPassManager, generate_preset_pass_manager
from qiskit_ibm_runtime.fake_provider import FakeMarrakesh, FakeNighthawk

sys.path.insert(0, str(Path(__file__).resolve().parent))
import structured_rewrite as sr  # noqa: E402
import table8_columns as t8  # noqa: E402


def circuits(skip_hhl: bool) -> list[tuple[str, object]]:
    feb = t8.load_qpy(str(t8.LUGO_FEB / "circuit_generated_nelem5_iter0.qpy"))
    out = [("LuGo nov26", t8.load_qpy(
        str(t8.LUGO_NOV / "circuit_generated_statevector_nelem5_iter0.qpy"),
        recip=t8.recip_params(feb)))]
    items, nb, _ = sr.walk(feb)
    mats = sr.block_unitaries(items)
    for cx in (None, 106, 90, 74, 58):
        rl = sr.RealL() if cx is None else sr.RealL(cx=cx)
        new, _ = sr.build(feb, items, nb, mats, barriers=True, real_l=rl)
        out.append((f"rewrite, L {cx or 122} CX", new))
    if not skip_hhl:
        out.insert(0, ("HHL", t8.build_hhl(Path.home() / "q8020")))
    return out


def two_q(c) -> int:
    return sum(1 for i in c.data if i.operation.num_qubits == 2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--skip-hhl", action="store_true")
    ap.add_argument("--out", type=Path, default=Path.home() / "q8020/swaps.csv")
    a = ap.parse_args()
    rows = []
    a2a = generate_preset_pass_manager(optimization_level=2, seed_transpiler=1,
                                       basis_gates=["cx", "rz", "sx", "x"])
    for name, circ in circuits(a.skip_hhl):
        circ = circ.remove_final_measurements(inplace=False)
        n_a2a = two_q(a2a.run(circ))
        for label, be in (("Heron r2", FakeMarrakesh()),
                          ("Nighthawk", FakeNighthawk())):
            pm = generate_preset_pass_manager(optimization_level=2,
                                              seed_transpiler=1, backend=be)
            t0 = time.time()
            routed = StagedPassManager(
                stages=["init", "layout", "routing"], init=pm.init,
                layout=pm.layout, routing=pm.routing).run(circ)
            swaps = routed.count_ops().get("swap", 0)
            final = two_q(pm.run(circ))
            row = {"circuit": name, "target": label, "swaps": swaps,
                   "two_qubit_a2a": n_a2a, "two_qubit_backend": final,
                   "added_two_qubit": final - n_a2a,
                   "swap_share_of_backend_2q": round(3 * swaps / final, 3),
                   "seconds": round(time.time() - t0, 1)}
            rows.append(row)
            print(row, flush=True)
            a.out.parent.mkdir(parents=True, exist_ok=True)
            with open(a.out, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)


if __name__ == "__main__":
    main()
