"""Statevector fidelity two ways, per AQC level: as is (signs from the state)
and as the shot extraction scores it (magnitudes, signs of x_ref)."""
import sys
from pathlib import Path
import numpy as np
from qiskit import qpy, transpile
from qiskit_aer import AerSimulator
AUX = Path(__file__).resolve().parent
sys.path.insert(0, str(AUX))
import structured_rewrite as sr  # noqa: E402
from run_step0 import extract_sv, reference, scaled, x_part  # noqa: E402

with open(AUX.parents[2] / "results/fvm_euler_1d_solver/2026-02-26-LuGo/"
          "circuits/circuit_generated_nelem5_iter0.qpy", "rb") as fh:
    circ = qpy.load(fh)[0]
items, nb, nl = sr.walk(circ)
mats = sr.block_unitaries(items)
ht, b = reference(circ, nb)
ref = {"x": x_part(np.linalg.solve(ht, b).real, 15),
       "A": ht[:16, 16:].real[:15, :15], "b": b[:15].real}
sim = AerSimulator(method="statevector")
for cx in [int(c) for c in sys.argv[1:]]:
    info = []
    synth = sr.aqc_factory([cx], [1, 2, 3], 1e-11, lambda m: None, info)
    new, _ = sr.build(circ, items, nb, mats, synth=synth, check=False,
                      barriers=True)
    t = transpile(new, basis_gates=sr.BASIS, optimization_level=2,
                  seed_transpiler=1)
    t.save_statevector()
    sv = np.asarray(sim.run(t).result().get_statevector())
    as_is = extract_sv(sv, nb, ref)["fidelity"]
    half = len(sv) // 2
    z = np.abs(sv[half:half + 2 ** nb])
    z /= np.linalg.norm(z)
    with_signs = scaled(x_part(z, 15), ref, shots=True)["fidelity"]
    xs = x_part(sv[half:half + 2 ** nb].real, 15)
    flips = int(np.sum(np.sign(xs) != np.sign(ref["x"])))
    print(f"AQC {cx}: statevector fidelity {as_is:.6f}; scored like shots "
          f"(x_ref signs) {with_signs:.6f}; sign flips vs x_ref {flips}/15",
          flush=True)
