"""Recover the 1/x rotation angles of the nov26 LuGo circuit from its stored run.

qiskit 2.x writes ExactReciprocalGate to qpy without its scaling, so the nov26
generated qpy does not say what its 1/x block does. The stored transpiled
circuit does, compiled in. With psi the stored circuit's final state, phi the
state after the (loadable) state prep and QPE, and chi = inv_QPE^dagger psi,
the 1/x block R is chi = R phi, and R is a rotation of the ancilla for each
clock value c: theta_c = 2 atan2(chi[anc=1], chi[anc=0]) on every basis state
with phi != 0. This prints how theta_c compares with ExactReciprocalGate(nl,
scaling, neg_vals) for neg_vals False and True. The stored circuit's own global
phase is removed first (chi = e^{ia} R phi with R real).

Usage: infer_recip_angles.py [nelem]   (nov26 qpy, nelem 5 by default)
"""

import sys

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qiskit.circuit.library import ExactReciprocalGate

from qpy_rewrite import load_qpy, recip_angles
from run_step0 import NOV_DIR, SOURCES, strip_meas


SIM = AerSimulator(method="statevector")


def amp(circ: QuantumCircuit) -> np.ndarray:
    q = transpile(circ, SIM, optimization_level=0)
    q.save_statevector()
    return np.asarray(SIM.run(q).result().get_statevector())


def main() -> None:
    nelem = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    src = SOURCES["nov26"]
    stored = strip_meas(load_qpy(str(NOV_DIR / src["stored"].format(n=nelem))))
    # the generated qpy cannot be loaded whole; load it with a stub 1/x of the
    # right size (its angles are not used here, only the other blocks)
    gen = load_qpy(str(NOV_DIR / src["gen"].format(n=nelem)), recip=(8, 2.0 ** -7, True))
    n = gen.num_qubits
    top = {i.operation.name: i for i in gen.data}
    qidx = lambda ins: [gen.find_bit(q).index for q in ins.qubits]
    psi = amp(stored)
    pre = QuantumCircuit(n)
    for ins in gen.data:
        if ins.operation.name in ("1/x", "inv_QPE", "barrier", "measure"):
            break
        pre.append(ins.operation, qidx(ins))
    phi = amp(pre)
    inv = top["inv_QPE"]
    post = QuantumCircuit(n)
    post.initialize(psi, range(n))
    post.append(inv.operation.inverse(), qidx(inv))
    chi = amp(post)
    rec = qidx(top["1/x"])
    nl = len(rec) - 1
    anc = rec[-1]
    idx = np.arange(2 ** n)
    c = np.zeros(2 ** n, dtype=int)
    for j in range(nl):
        c += ((idx >> rec[j]) & 1) << j
    lo = (idx >> anc) & 1 == 0
    use = lo & (np.abs(phi) > 1e-6)
    i0 = idx[use]
    i1 = i0 + (1 << anc)
    # the stored circuit's global phase is its own: chi = e^{i a} R phi with R
    # real, so sum |phi|^2 (r0^2 + r1^2) = e^{2 i a}, r = chi / phi
    w = np.abs(phi[i0]) ** 2
    z = np.sum(w * ((chi[i0] / phi[i0]) ** 2 + (chi[i1] / phi[i0]) ** 2))
    chi = chi * np.exp(-0.5j * np.angle(z))
    r0, r1 = chi[i0] / phi[i0], chi[i1] / phi[i0]
    print("global phase of the stored circuit vs generated prefix/suffix:",
          0.5 * np.angle(z), "; |z| =", abs(z),
          "; max imag of ratios:", max(np.max(np.abs(r0.imag)),
                                       np.max(np.abs(r1.imag))))
    th = 2 * np.arctan2(r1.real, r0.real)
    cc = c[use]
    got = {}
    for v in np.unique(cc):
        t = th[cc == v]
        got[int(v)] = (float(t.mean()), float(np.ptp(t)))
    h = 2 ** nl
    print("distinct c with weight:", len(got), "max spread of theta within c:",
          max(p for _, p in got.values()))
    # compare with ExactReciprocalGate(nl, scaling, neg_vals), both conventions
    arr = np.array([got[v][0] for v in range(h)])
    for neg in (False, True):
        half = h >> int(neg)
        c = np.arange(half)
        ok = (c > 0) & (arr[:half] > 1e-9) & (arr[:half] < np.pi - 1e-6)
        sc = float(np.mean(np.sin(arr[:half][ok] / 2) * c[ok] / half))
        ref = recip_angles(ExactReciprocalGate(nl, sc, neg))
        dev = np.max(np.abs(np.cos(arr / 2) - np.cos(ref / 2))
                     + np.abs(np.sin(arr / 2) - np.sin(ref / 2)))
        print(f"neg_vals={neg!s:5}  scaling={sc!r}  max deviation of "
              f"(cos, sin)(theta/2) over all {h} c: {dev:.2e}")
    print("theta_c at c = 1, 2, 127, 128, 129, 254, 255:",
          {v: round(got[v][0], 6) for v in (1, 2, 127, 128, 129, 254, 255)})


if __name__ == "__main__":
    main()
