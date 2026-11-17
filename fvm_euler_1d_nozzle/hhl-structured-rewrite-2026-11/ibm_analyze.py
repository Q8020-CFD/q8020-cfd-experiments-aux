"""Analyze an IBM run of the structured HHL step-0 circuit, or offline counts.

Inputs: the run's prep JSON (ibm_submit.py) and either --job (fetches the
SamplerV2 result) or --counts (JSON {"main": {...}, "cal0": {...},
"cal1": {...}} of bitstring counts, clbit 0 rightmost). Estimates:

  raw        counts as measured
  readout    per-qubit flip rates from cal0 and cal1 (measurement twirling
             makes them symmetric), tensored inverse on the 14-bit
             distribution, clipped to >= 0 and renormalized (TREX-style for
             counts)
  readout+bg readout, then the mean probability per outcome over ancilla 1,
             clock != 0 subtracted from the used outcomes (ancilla 1,
             clock 0); the ideal circuit holds 1.2e-4 of its probability there

Each is scored as fvm hhl_solve does (lugo-qpy-rewrite-2026-11/run_step0.py
extract_counts: used outcomes, x part, least-squares length, signs of x_ref).
Null test as in note-20260924-0007: each estimator is applied, with the same
flip rates, to --n-null synthetic maximally mixed count sets with the same
shots, and the observed fidelity is given as z against that estimator's
null. The x_ref signs make even pure noise score well above zero (about
0.54), so the null, not zero, is the baseline.

The positive control (ctrl, state preparation only) is scored as the
classical fidelity of its readout-corrected system marginal against |b|^2;
it should be near 1 if layout, bit order and correction are right.
"""

import argparse
import json
from pathlib import Path

import numpy as np

import structured_rewrite as sr  # noqa: F401  (puts run_step0 on the path)
from run_step0 import extract_counts



def to_prob(counts: dict, n: int) -> tuple[np.ndarray, int]:
    p = np.zeros(2 ** n)
    for k, v in counts.items():
        p[int(k.replace(" ", ""), 2)] += v
    shots = int(p.sum())
    return p / shots, shots


def flip_rates(cal0: dict, cal1: dict, n: int) -> np.ndarray:
    """e[c] = (P(1 | 0), P(0 | 1)) for clbit c."""
    p0, _ = to_prob(cal0, n)
    p1, _ = to_prob(cal1, n)
    idx = np.arange(2 ** n)
    e = np.zeros((n, 2))
    for c in range(n):
        bit = (idx >> c) & 1
        e[c, 0] = p0[bit == 1].sum()
        e[c, 1] = p1[bit == 0].sum()
    return e


def readout_correct(p: np.ndarray, e: np.ndarray) -> np.ndarray:
    n = e.shape[0]
    t = p.reshape((2,) * n)  # axis j is clbit n - 1 - j
    for c in range(n):
        a = np.array([[1 - e[c, 0], e[c, 1]], [e[c, 0], 1 - e[c, 1]]])
        t = np.moveaxis(np.tensordot(np.linalg.inv(a), t,
                                     axes=([1], [n - 1 - c])), 0, n - 1 - c)
    q = np.clip(t.reshape(-1), 0, None)
    return q / q.sum()


def subtract_background(p: np.ndarray, n: int, nb: int) -> np.ndarray:
    nl = n - 1 - nb
    idx = np.arange(2 ** n)
    anc = idx >> (n - 1)
    clock = (idx >> nb) & (2 ** nl - 1)
    bg = p[(anc == 1) & (clock != 0)].mean()
    q = p.copy()
    used = (anc == 1) & (clock == 0)
    q[used] = np.clip(q[used] - bg, 0, None)
    return q


def score(p: np.ndarray, shots: int, n: int, ref: dict) -> dict:
    counts = {format(i, f"0{n}b"): v * shots
              for i, v in enumerate(p) if v > 0}
    return extract_counts(counts, n, ref["nb"], ref)


def estimates(p: np.ndarray, e: np.ndarray, n: int, nb: int) -> dict:
    out = {"raw": p, "readout": readout_correct(p, e)}
    out["readout+bg"] = subtract_background(out["readout"], n, nb)
    return out


def null_scores(shots: int, n: int, e: np.ndarray, ref: dict, rng,
                n_null: int) -> dict:
    """Fidelity of each estimator on maximally mixed counts."""
    out = {}
    for _ in range(n_null):
        c = rng.poisson(shots / 2 ** n, size=2 ** n).astype(float)
        for k, q in estimates(c / c.sum(), e, n, ref["nb"]).items():
            out.setdefault(k, []).append(
                score(q, shots, n, ref)["fidelity"])
    return {k: np.array(v) for k, v in out.items()}


def control_fidelity(counts: dict, e: np.ndarray, n: int, nb: int,
                     b2: np.ndarray, phys: list, phys_ctrl: list) -> dict:
    """Control is routed separately: flip rates by physical qubit (median
    for a qubit the main circuit does not measure)."""
    by_q = dict(zip(phys, e))
    ec = np.array([by_q.get(q, np.median(e, axis=0)) for q in phys_ctrl])
    p, _ = to_prob(counts, n)
    q = readout_correct(p, ec)
    idx = np.arange(2 ** n)
    out = {}
    for name, d in (("raw", p), ("readout", q)):
        sysm = np.bincount(idx & (2 ** nb - 1), weights=d,
                           minlength=2 ** nb)
        out[name] = float(np.sum(np.sqrt(sysm * b2 / b2.sum())) ** 2)
    out["P_rest_zero"] = float(q[(idx >> nb) == 0].sum())
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("prep", type=Path)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--job")
    g.add_argument("--counts", type=Path)
    ap.add_argument("--account", default="default-ibm-cloud")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--n-null", type=int, default=500)
    a = ap.parse_args()
    prep = json.loads(a.prep.read_text())
    ref = {k: np.array(v) if isinstance(v, list) else v
           for k, v in prep["reference"].items()}
    if a.job:
        from qiskit_ibm_runtime import QiskitRuntimeService
        res = QiskitRuntimeService(name=a.account).job(a.job).result()
        keys = ("main", "cal0", "cal1", "ctrl")[:len(res)]
        data = {k: res[i].data.meas.get_counts()
                for i, k in enumerate(keys)}
    else:
        data = json.loads(a.counts.read_text())
    n = 1 + ref["nl"] + ref["nb"]
    p, shots = to_prob(data["main"], n)
    e = flip_rates(data["cal0"], data["cal1"], n)
    est = estimates(p, e, n, ref["nb"])
    rng = np.random.default_rng(1)
    null = null_scores(shots, n, e, ref, rng, a.n_null)
    idx = np.arange(2 ** n)
    used = ((idx >> (n - 1)) == 1) & (((idx >> ref["nb"])
                                       & (2 ** ref["nl"] - 1)) == 0)
    report = {"shots": shots, "flip_rate_median": float(np.median(e)),
              "flip_rate_max": float(e.max()),
              "n_null": a.n_null, "estimates": {}}
    if "ctrl" in data:
        report["control"] = control_fidelity(
            data["ctrl"], e, n, ref["nb"], np.array(prep["control_b_herm"]),
            prep["physical_qubits"], prep["control_physical_qubits"])
    for name, q in est.items():
        s = score(q, shots, n, ref)
        s["P_ancilla1"] = float(q[idx >> (n - 1) == 1].sum())
        s["P_used"] = float(q[used].sum())
        nl_ = null[name]
        s["null_mean"], s["null_sd"] = float(nl_.mean()), float(nl_.std())
        s["z_vs_null"] = float((s["fidelity"] - nl_.mean()) / nl_.std())
        report["estimates"][name] = s
    txt = json.dumps(report, indent=1, default=float)
    print(txt)
    if a.out:
        a.out.write_text(txt)


if __name__ == "__main__":
    main()
