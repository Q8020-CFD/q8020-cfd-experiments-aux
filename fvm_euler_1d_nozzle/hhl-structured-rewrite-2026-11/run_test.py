"""Test and count the structured rewrite of the fvm HHL step-0 circuit.

Input (--input): the LuGo step-0 qpy (feb26, generated), or the pre-LuGo
HHL qpy (fvm main on the 2025-11 stack, Frontier; the default). The
recorded step-0 metrics come from the matching run's hhl_metrics csv.
Variants of the rewrite (structured_rewrite.py):

  exact  W and V of L by qs_decomposition
  aqc    W and V of L by qiskit AQC at the first CX count in --aqc-cx that
         reaches 1 - F <= --aqc-tol per piece (approximate in principle)

For each variant: every block against the stored block's 64 x 64 unitary;
the exact statevector against the stored circuit (blocks as their unitaries)
and HHL metrics as in lugo-qpy-rewrite-2026-11/run_step0.py, beside the
recorded run; --seeds x --shots on Aer with the same seeds as the stored
circuit; gate counts all-to-all (cx/rz/sx/x), FakeMarrakesh (IBM Heron r2)
and FakeNighthawk, level 2, seed_transpiler 1. The LuGo step-0 qpy (feb26,
generated) is counted the same way; for pre-LuGo input, that circuit's
all-to-all CX is estimated from one block. Nothing runs on hardware.
"""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import qiskit
import qiskit_aer
import qiskit_ibm_runtime
import scipy.linalg as sla
from qiskit import QuantumCircuit, qpy
from qiskit.quantum_info import Operator
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeMarrakesh, FakeNighthawk

import structured_rewrite as sr
from run_step0 import counts_sha1, extract_counts, extract_sv, x_part

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
RES = EXP / "results/fvm_euler_1d_solver"
CASE = RES / "nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa"
ORIG = "circuit_generated_statevector_nelem{n}_iter0.qpy"
LUGO_REC = (RES / "2026-02-26-LuGo/nelem{n}/statevector/exact/"
            "hhl_metrics_nelem{n}_statevector.csv")
LUGO = RES / "2026-02-26-LuGo/circuits/circuit_generated_nelem{n}_iter0.qpy"
OPT, SEED_T = 2, 1


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(path: Path) -> str:
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--short=8",
                        "HEAD"], capture_output=True, text=True)
    d = subprocess.run(["git", "-C", str(path), "status", "--porcelain",
                        "."], capture_output=True, text=True)
    return r.stdout.strip() + (" (dirty)" if d.stdout.strip() else "")


def counts(c: QuantumCircuit, target: str) -> tuple[QuantumCircuit, dict]:
    if target == "a2a":
        pm = generate_preset_pass_manager(optimization_level=OPT,
                                          seed_transpiler=SEED_T,
                                          basis_gates=sr.BASIS)
    else:
        be = FakeMarrakesh() if target == "heron" else FakeNighthawk()
        pm = generate_preset_pass_manager(optimization_level=OPT,
                                          seed_transpiler=SEED_T, backend=be)
    t0 = time.time()
    t = pm.run(c)
    n2 = sum(1 for i in t.data if i.operation.num_qubits == 2)
    d2 = t.depth(lambda i: i.operation.num_qubits == 2)
    return t, {"two_qubit_gates": n2, "two_qubit_depth": d2,
               "depth": t.depth(), "transpile_s": round(time.time() - t0, 1)}


def read_recorded(path: Path) -> dict:
    with open(path) as fh:
        rows = list(csv.DictReader(fh, skipinitialspace=True))
    r = rows[0]
    return {k: float(r[k]) for k in ("fidelity", "l2_error_rel",
                                     "l2_error_normalized")}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--nelem", type=int, default=5)
    ap.add_argument("--input", choices=["lugo", "pre-lugo"],
                    default="pre-lugo")
    ap.add_argument("--out", type=Path,
                    default=Path.home() / "q8020/hhl-structured-rewrite")
    ap.add_argument("--shots", type=int, default=150000)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--aqc-cx", default="62,64,68,72")
    ap.add_argument("--aqc-tol", type=float, default=1e-11)
    ap.add_argument("--no-aqc", action="store_true")
    ap.add_argument("--no-hw", action="store_true")
    ap.add_argument("--no-lugo", action="store_true")
    ap.add_argument("--barriers", action="store_true",
                    help="barrier after every block: no cross-block "
                    "cancellation by the transpiler")
    a = ap.parse_args()
    out = a.out / f"nelem{a.nelem}"
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "log.txt", "w")

    def log(msg: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "\
               f"{msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    t_all = time.time()
    if a.input == "lugo":
        src = Path(str(LUGO).format(n=a.nelem))
        rec = Path(str(LUGO_REC).format(n=a.nelem))
    else:
        src = CASE / ORIG.format(n=a.nelem)
        rec = CASE / f"hhl_metrics_nelem{a.nelem}_statevector.csv"
    summary = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "node": platform.node(), "python": platform.python_version(),
        "qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__,
        "qiskit_ibm_runtime": qiskit_ibm_runtime.__version__,
        "experiments_repo": git_head(EXP), "input": str(src),
        "input_kind": a.input, "input_sha256": sha256(src),
        "nelem": a.nelem, "recorded_step0": read_recorded(rec),
        "barriers": a.barriers,
        "recorded_csv": str(rec),
    }
    log(f"load {src.name}")
    with open(src, "rb") as fh:
        circ = qpy.load(fh)[0]
    items, nb, nl = sr.walk(circ)
    n = circ.num_qubits
    t0 = time.time()
    mats = sr.block_unitaries(items)
    log(f"nb {nb} nl {nl} n {n}: {len(mats)} block unitaries "
        f"({time.time() - t0:.0f} s)")

    # HHL reference, from the circuit alone (as run_step0.reference)
    u = mats[0][1::2, 1::2]
    if np.max(np.abs(np.angle(np.linalg.eigvals(u)))) > np.pi - 1e-6:
        raise RuntimeError("eigenphases of U reach pi: log ambiguous")
    ht = -1j * sla.logm(u)
    ht = (ht + ht.conj().T) / 2
    b = [p for k, p, _ in items if k == "sp"][0]
    nsys, n2 = 3 * a.nelem, 2 ** (nb - 1)
    ref = {"x": x_part(np.linalg.solve(ht, b).real, nsys),
           "A": ht[:n2, n2:].real[:nsys, :nsys], "b": b[:nsys].real}
    summary["cond_H"] = float(np.linalg.cond(ht))

    variants = {}
    new, rep = sr.build(circ, items, nb, mats, barriers=a.barriers)
    log(f"exact: {rep}")
    variants["exact"] = (new, rep, None)
    if not a.no_aqc:
        info = []
        synth = sr.aqc_factory([int(x) for x in a.aqc_cx.split(",")],
                               [1, 2, 3], a.aqc_tol, log, info)
        new, rep = sr.build(circ, items, nb, mats, synth=synth,
                            barriers=a.barriers)
        log(f"aqc: {rep} pieces {info}")
        variants["aqc"] = (new, rep, info)

    sim = AerSimulator(method="statevector")
    pm0 = generate_preset_pass_manager(optimization_level=0, backend=sim)

    def run_sv(t: QuantumCircuit) -> np.ndarray:
        q = t.copy()
        q.save_statevector()
        return np.asarray(sim.run(q).result().get_statevector())

    def run_shots(t: QuantumCircuit, seed: int) -> dict:
        q = t.copy()
        q.measure_all()
        return sim.run(q, shots=a.shots, seed_simulator=seed).result()\
            .get_counts()

    reft = pm0.run(sr.reference(circ, items, mats))
    sv_ref = run_sv(reft)
    half = 2 ** (n - 1)
    p_ref = float(np.vdot(sv_ref[half:half + 2 ** nb],
                          sv_ref[half:half + 2 ** nb]).real)
    sv_rows = [{"variant": "stored", "one_minus_F_vs_stored": 0.0,
                "P_used": p_ref, **extract_sv(sv_ref, nb, ref)}]
    sv_rows.append({"variant": "recorded", **summary["recorded_step0"]})
    count_rows, shot_rows = [], []
    seeds = list(range(1, a.seeds + 1))
    pre = "1" + "0" * nl
    ref_used = {}
    for s in seeds:
        c = run_shots(reft, s)
        ref_used[s] = {k: v for k, v in c.items() if k.startswith(pre)}
        shot_rows.append({"variant": "stored", "seed": s,
                          "used_sha1": counts_sha1(ref_used[s]),
                          **extract_counts(c, n, nb, ref)})
    log("stored circuit: statevector and shots done")

    summary["variants"] = {}
    for name, (new, rep, info) in variants.items():
        t, row = counts(new, "a2a")
        count_rows.append({"circuit": name, "target": "all-to-all", **row})
        log(f"{name} all-to-all: {row}")
        sv = run_sv(t)
        z = sv[half:half + 2 ** nb]
        f_full = float(abs(np.vdot(sv_ref, sv)) ** 2)
        sv_rows.append({"variant": name, "one_minus_F_vs_stored": 1 - f_full,
                        "P_used": float(np.vdot(z, z).real),
                        **extract_sv(sv, nb, ref)})
        for s in seeds:
            c = run_shots(t, s)
            used = {k: v for k, v in c.items() if k.startswith(pre)}
            shot_rows.append({"variant": name, "seed": s,
                              "used_sha1": counts_sha1(used),
                              "used_equal_stored": used == ref_used[s],
                              **extract_counts(c, n, nb, ref)})
        log(f"{name}: statevector 1-F vs stored {1 - f_full:.2e}, shots done")
        if not a.no_hw:
            for tgt in ("heron", "nighthawk"):
                _, row = counts(new, tgt)
                count_rows.append({"circuit": name, "target": tgt, **row})
                log(f"{name} {tgt}: {row}")
        summary["variants"][name] = {**rep.__dict__, "aqc_pieces": info}

    if not a.no_lugo:
        lp = Path(str(LUGO).format(n=a.nelem))
        summary["lugo_input"], summary["lugo_sha256"] = str(lp), sha256(lp)
        with open(lp, "rb") as fh:
            lugo = qpy.load(fh)[0].remove_final_measurements(inplace=False)
        for tgt in ("a2a",) + (() if a.no_hw else ("heron", "nighthawk")):
            _, row = counts(lugo, tgt)
            count_rows.append({"circuit": "lugo",
                               "target": "all-to-all" if tgt == "a2a"
                               else tgt, **row})
            log(f"lugo {tgt}: {row}")

    # pre-LuGo HHL, all-to-all CX estimate: one stored block times count
    blk = [p[0] for k, p, _ in items if k == "block"][0]
    if a.input == "lugo":
        blk = None
    if blk is not None:
        one = QuantumCircuit(nb + 1)
        one.append(blk, range(nb + 1))
        _, r1 = counts(one, "a2a")
        rest = QuantumCircuit(*circ.qregs)
        for k, p, idx in items:
            if k == "sp":
                rest.append(sr.StatePreparation(p), idx)
            elif k != "block":
                rest.append(p, idx)
        _, rr = counts(rest, "a2a")
        reps = 2 * (2 ** nl - 1)
        summary["pre_lugo_estimate"] = {
            "cx_per_controlled_U": r1["two_qubit_gates"],
            "controlled_U_copies": reps, "cx_rest": rr["two_qubit_gates"],
            "cx_total": reps * r1["two_qubit_gates"]
            + rr["two_qubit_gates"]}
        log(f"pre-LuGo estimate: {summary['pre_lugo_estimate']}")

    for fname, rows in (("counts.csv", count_rows),
                        ("statevector.csv", sv_rows),
                        ("shots.csv", shot_rows)):
        keys = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        with open(out / fname, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    summary["seconds"] = round(time.time() - t_all, 1)
    summary["ended_utc"] = datetime.now(timezone.utc).isoformat()
    with open(out / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=1, default=str)
    log(f"done in {summary['seconds']} s: {out}")


if __name__ == "__main__":
    main()
