"""Compare quantum_linear_solvers HHL circuits across two branches.

feature/hhl-lugo-csd (qpe_method lugo / structured, l_synthesis real /
qsd, reciprocal_ucry) against feature/sqls-aiaa-4q26 at 99231b8 (the fvm
venv's install), on the same inputs.

  build <out_dir> [--cases ...]   run under one venv; per case an npz of
                                  exact statevectors, a json record and,
                                  on the new branch, a qpy per build
  hw <new_dir> [--cases ...]      run under the fvm venv (IBM fake
                                  backends): 2q counts on Heron r2
                                  (FakeMarrakesh), Heron r3 (FakeBoston) and
                                  Nighthawk, and for the fvm cases 150000
                                  Aer shots x seeds 1-10, fvm extraction
                                  (lugo-qpy-rewrite-2026-11/run_step0.py)
  compare <base_dir> <new_dir>    state equality, HHL fidelity, counts

All transpiles: level 2, seed_transpiler 1; all-to-all is cx, rz, sx, x.

Cases: rand3, rand4 (random real A plus 4 I, Hermitian embedding,
b = [0, r]) and fvm5, fvm10 (fvm nozzle first Newton step: H*t and b_herm
read from the 2026-02-26 LuGo generated qpy, as in
lugo-qpy-rewrite-2026-11/run_step0.py; HHL rebuilds the same U from them).
"""

import argparse
import inspect
import json
import platform
import subprocess
import sys
import time
from dataclasses import asdict
from importlib import metadata
from pathlib import Path

import numpy as np
import qiskit
import scipy.linalg as sla
from qiskit import QuantumCircuit, qpy, transpile
from qiskit.quantum_info import Operator, Statevector

from linear_solvers import HHL

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
FEB = EXP / "results/fvm_euler_1d_solver/2026-02-26-LuGo/circuits"
BASIS = ["cx", "rz", "sx", "x"]
COMBOS = {
    "standard": {"qpe_method": "standard", "reciprocal_ucry": False},
    "lugo+ucry": {"qpe_method": "lugo", "reciprocal_ucry": True},
    "structured-qsdL+ucry": {"qpe_method": "structured",
                             "reciprocal_ucry": True, "l_synthesis": "qsd"},
    "structured-realL+ucry": {"qpe_method": "structured",
                              "reciprocal_ucry": True, "l_synthesis": "real"},
    "default": {},
}
SHOT_BUILDS = ("structured-realL+ucry", "structured-qsdL+ucry", "lugo+ucry")
CASES = ("rand3", "rand4", "fvm5", "fvm10")


def qls_provenance() -> dict:
    """Commit of the installed linear_solvers (git url or editable path)."""
    dist = metadata.distribution("quantum-linear-solvers")
    url = json.loads(dist.read_text("direct_url.json") or "{}")
    out = {"url": url.get("url"), "commit": url.get("vcs_info", {})
           .get("commit_id"), "dirty": None}
    if url.get("dir_info", {}).get("editable"):
        path = url["url"].removeprefix("file://")
        run = lambda *a: subprocess.run(["git", "-C", path, *a], text=True,
                                        capture_output=True).stdout.strip()
        out.update(commit=run("rev-parse", "HEAD"),
                   branch=run("branch", "--show-current"),
                   dirty=bool(run("status", "--porcelain")))
    return out


def embedded(n: int, seed: int) -> tuple[np.ndarray, np.ndarray, int]:
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(n, n)) + 4 * np.eye(n)
    h = np.block([[np.zeros((n, n)), a], [a.T, np.zeros((n, n))]])
    b = np.concatenate([np.zeros(n), rng.normal(size=n)])
    return h, b, n


def fvm_case(nelem: int) -> tuple[np.ndarray, np.ndarray, int]:
    """H*t and b_herm from the LuGo generated qpy (first QPE block)."""
    with open(FEB / f"circuit_generated_nelem{nelem}_iter0.qpy", "rb") as fh:
        gen = qpy.load(fh)[0]
    nl = [i for i in gen.data if i.operation.name == "1/x"][0] \
        .operation.num_qubits - 1
    nb = gen.num_qubits - nl - 1
    sp = [i for i in gen.data if i.operation.name not in
          ("QPE", "1/x", "inv_QPE", "barrier", "measure")][0]
    b = np.array(sp.operation.definition.data[0].operation.params, complex)
    qpe = [i for i in gen.data if i.operation.name == "QPE"][0].operation
    blk = [i for i in qpe.definition.data
           if i.operation.num_qubits == nb + 1][0]
    w = Operator(blk.operation).data[1::2, 1::2]
    ht = -1j * sla.logm(w)
    return (ht + ht.conj().T) / 2, b.real, 3 * nelem


def load_case(name: str) -> tuple[np.ndarray, np.ndarray, int]:
    if name == "rand3":
        return embedded(4, 7)
    if name == "rand4":
        return embedded(8, 11)
    return fvm_case(int(name.removeprefix("fvm")))


def build(out: Path, cases: list[str], skip_standard: bool = False) -> None:
    out.mkdir(parents=True, exist_ok=True)
    new = "l_synthesis" in inspect.signature(HHL.__init__).parameters
    combos = dict(COMBOS) if new else {"standard": {}}
    if skip_standard:
        combos.pop("standard", None)
    prov = {"qls": qls_provenance(), "qiskit": qiskit.__version__,
            "python": platform.python_version(), "machine": platform.machine()}
    for case in cases:
        h, b, nsys = load_case(case)
        rec, arrays = {"case": case, "nsys": nsys, "prov": prov,
                       "builds": {}}, {"h": h, "b": b}
        for key, kw in combos.items():
            t0 = time.perf_counter()
            hhl = HHL(**kw)
            qc = hhl.construct_circuit(h, b)
            t_build = time.perf_counter() - t0
            t0 = time.perf_counter()
            sv = Statevector(qc).data
            t_sv = time.perf_counter() - t0
            arrays[key] = sv
            info = getattr(hhl, "qpe_info", None)
            rec["builds"][key] = {
                "build_s": t_build, "statevector_s": t_sv,
                "num_qubits": qc.num_qubits,
                "nl": qc.qregs[1].size, "nb": qc.qregs[0].size,
                "qpe_info": asdict(info) if info else None}
            # standard at nb >= 5 is ~1e6 CX: not transpiled, no qpy (its
            # ExactReciprocalGate does not survive qpy in qiskit 2.x)
            if not (key == "standard" and qc.qregs[0].size >= 5):
                rec["builds"][key]["counts"] = counts(qc)
            if new and key != "standard":
                with open(out / f"{case}_{key}.qpy", "wb") as fh:
                    qpy.dump(qc, fh)
            print(f"{case} {key}: build {t_build:.1f} s, "
                  f"statevector {t_sv:.1f} s, "
                  f"{rec['builds'][key].get('counts', {})}", flush=True)
        np.savez(out / f"{case}.npz", **arrays)
        (out / f"{case}.json").write_text(json.dumps(rec, indent=1))


def fidelities(sv: np.ndarray, h: np.ndarray, b: np.ndarray, nb: int,
               nsys: int, fvm: bool) -> dict:
    """HHL fidelity against the classical solve: the system register at
    flag 1, clock 0 (as fvm get_sol_ideal_backend), whole and x part."""
    half = len(sv) // 2
    z = sv[half:half + 2 ** nb].real
    z_ref = np.linalg.solve(h, b)
    fid = lambda u, v: float(abs(np.dot(u / np.linalg.norm(u),
                                         v / np.linalg.norm(v))) ** 2)
    out = {"fid_system": fid(z, z_ref), "fid_x": None}
    if fvm:  # x is the second half (fvm extract_true_sol_from_herm)
        n2 = 1 << (nsys - 1).bit_length()
        out["fid_x"] = fid(z[n2:n2 + nsys], z_ref[n2:n2 + nsys])
    return out


def counts(qc: QuantumCircuit) -> dict:
    t0 = time.perf_counter()
    t = transpile(qc, basis_gates=BASIS, optimization_level=2,
                  seed_transpiler=1)
    two_q = lambda ins: ins.operation.num_qubits == 2
    return {"cx": t.count_ops().get("cx", 0),
            "depth_2q": t.depth(filter_function=two_q),
            "depth": t.depth(), "transpile_s": time.perf_counter() - t0}


def hw(new: Path, cases: list[str]) -> None:
    """IBM fake-backend counts and Aer shot fidelities (fvm venv only)."""
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime.fake_provider import (FakeBoston, FakeMarrakesh,
                                                  FakeNighthawk)
    sys.path.insert(0, str(HERE.parent / "lugo-qpy-rewrite-2026-11"))
    from run_step0 import extract_counts, x_part
    backends = {"heron_r2": FakeMarrakesh(), "heron_r3": FakeBoston(),
                "nighthawk": FakeNighthawk()}
    sim = AerSimulator(method="statevector")
    out = json.loads((new / "hw.json").read_text()) \
        if (new / "hw.json").exists() else {}
    for case in cases:
        rec = json.loads((new / f"{case}.json").read_text())
        z = np.load(new / f"{case}.npz")
        h, b, nsys = z["h"], z["b"], rec["nsys"]
        for key in rec["builds"]:
            path = new / f"{case}_{key}.qpy"
            if not path.exists():
                continue
            with open(path, "rb") as fh:
                qc = qpy.load(fh)[0]
            row = {}
            for name, be in backends.items():
                t0 = time.perf_counter()
                t = generate_preset_pass_manager(
                    optimization_level=2, seed_transpiler=1,
                    backend=be).run(qc)
                two_q = lambda ins: ins.operation.num_qubits == 2
                row[name] = {"two_q": sum(1 for i in t.data if two_q(i)),
                             "depth_2q": t.depth(two_q),
                             "depth": t.depth(),
                             "transpile_s": time.perf_counter() - t0}
            if case.startswith("fvm") and key in SHOT_BUILDS:
                nb = qc.qregs[0].size
                n2 = 2 ** (nb - 1)
                ref = {"x": x_part(np.linalg.solve(h, b).real, nsys),
                       "A": h[:n2, n2:].real[:nsys, :nsys],
                       "b": b[:nsys].real}
                tsh = transpile(qc.measure_all(inplace=False), sim,
                                optimization_level=2, seed_transpiler=1)
                fs = []
                t0 = time.perf_counter()
                for seed in range(1, 11):
                    cnt = sim.run(tsh, shots=150000, seed_simulator=seed) \
                        .result().get_counts()
                    fs.append(extract_counts(cnt, tsh.num_qubits, nb, ref)
                              ["fidelity"])
                row["shots_150k"] = {"median": float(np.median(fs)),
                                     "min": float(min(fs)),
                                     "max": float(max(fs)), "fidelities": fs,
                                     "wall_s": time.perf_counter() - t0}
            out.setdefault(case, {})[key] = row
            print(case, key, json.dumps(row)[:300], flush=True)
            (new / "hw.json").write_text(json.dumps(out, indent=1))


def compare(base: Path, new: Path, cases: list[str]) -> None:
    rows = []
    hwall = json.loads((new / "hw.json").read_text()) \
        if (new / "hw.json").exists() else {}
    for case in cases:
        if not (new / f"{case}.npz").exists():
            continue
        nz = np.load(new / f"{case}.npz")
        nrec = json.loads((new / f"{case}.json").read_text())
        builds = {}
        if (base / f"{case}.npz").exists():
            bz = np.load(base / f"{case}.npz")
            brec = json.loads((base / f"{case}.json").read_text())
            if not (np.array_equal(bz["h"], nz["h"])
                    and np.array_equal(bz["b"], nz["b"])):
                raise SystemExit(f"{case}: inputs differ between builds")
            ref, ref_label = bz["standard"], "base standard"
            builds["base standard"] = (ref, brec["builds"]["standard"])
        else:  # no base build (fvm10: standard too slow): new lugo+ucry
            bz, ref, ref_label = nz, nz["lugo+ucry"], "new lugo+ucry"
        for key, b in nrec["builds"].items():
            builds[f"new {key}"] = (nz[key], b)
        for label, (sv, b) in builds.items():
            row = {"case": case, "build": label, "nb": b["nb"], "nl": b["nl"],
                   "num_qubits": b["num_qubits"], "ref": ref_label,
                   "bitwise_equal_ref": bool(np.array_equal(sv, ref)),
                   "max_abs_diff_ref": float(np.max(np.abs(sv - ref))),
                   "infid_vs_ref": float(
                       1 - abs(np.vdot(ref, sv)) ** 2
                       / (np.vdot(ref, ref).real * np.vdot(sv, sv).real)),
                   "build_s": b["build_s"], "statevector_s": b["statevector_s"],
                   "qpe_method_used": (b["qpe_info"] or {}).get("method",
                                                               "standard"),
                   "fallback": (b["qpe_info"] or {}).get("fallback"),
                   "l_cx": (b["qpe_info"] or {}).get("l_cx")}
            row.update(fidelities(sv, bz["h"], bz["b"], b["nb"],
                                  nrec["nsys"], case.startswith("fvm")))
            row.update(b.get("counts", {}))
            hwrec = hwall.get(case, {}).get(label.removeprefix("new "), {})
            for tgt in ("heron_r2", "heron_r3", "nighthawk"):
                for k, v in hwrec.get(tgt, {}).items():
                    if k != "transpile_s":
                        row[f"{tgt}_{k}"] = v
            if "shots_150k" in hwrec:
                row["shots_150k_median"] = hwrec["shots_150k"]["median"]
                row["shots_150k_min"] = hwrec["shots_150k"]["min"]
                row["shots_150k_max"] = hwrec["shots_150k"]["max"]
            qi = b["qpe_info"] or {}
            row["l_method"] = qi.get("l_method")
            row["l_fallback"] = qi.get("l_fallback")
            row["qpe_build_s"] = qi.get("wall_s")
            rows.append(row)
            print(json.dumps(row), flush=True)
    prov = lambda d: json.loads(next(d.glob("*.json")).read_text())["prov"]
    summary = {"base": prov(base), "new": prov(new), "rows": rows}
    (new.parent / "summary.json").write_text(json.dumps(summary, indent=1))
    write_xlsx(new.parent / "summary.xlsx", rows)


def write_xlsx(path: Path, rows: list[dict]) -> None:
    """rows as one sheet, stdlib only (zip of inline-string XML)."""
    import zipfile
    from xml.sax.saxutils import escape
    cols = list(dict.fromkeys(k for r in rows for k in r))

    def cell(ref: str, v) -> str:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return f'<c r="{ref}"><v>{v}</v></c>'
        return (f'<c r="{ref}" t="inlineStr"><is><t>'
                f'{escape("" if v is None else str(v))}</t></is></c>')

    def col(i: int) -> str:
        s = ""
        while True:
            i, r = divmod(i, 26)
            s = chr(65 + r) + s
            if i == 0:
                return s
            i -= 1

    data = [cols] + [[r.get(c) for c in cols] for r in rows]
    xml_rows = "".join(
        f'<row r="{j + 1}">'
        + "".join(cell(f"{col(i)}{j + 1}", v) for i, v in enumerate(row))
        + "</row>" for j, row in enumerate(data))
    ns = "http://schemas.openxmlformats.org"
    files = {
        "[Content_Types].xml":
            f'<Types xmlns="{ns}/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/'
            'vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/'
            'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.spreadsheetml.'
            'worksheet+xml"/></Types>',
        "_rels/.rels":
            f'<Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/'
            'relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>',
        "xl/workbook.xml":
            f'<workbook xmlns="{ns}/spreadsheetml/2006/main" xmlns:r="{ns}/'
            'officeDocument/2006/relationships"><sheets><sheet name="compare"'
            ' sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels":
            f'<Relationships xmlns="{ns}/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{ns}/officeDocument/2006/'
            'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>',
        "xl/worksheets/sheet1.xml":
            f'<worksheet xmlns="{ns}/spreadsheetml/2006/main"><sheetData>'
            f"{xml_rows}</sheetData></worksheet>",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, text in files.items():
            zf.writestr(name, '<?xml version="1.0" encoding="UTF-8" '
                        f'standalone="yes"?>{text}')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("out", type=Path)
    b.add_argument("--cases", nargs="+", default=list(CASES), choices=CASES)
    b.add_argument("--skip-standard", action="store_true",
                   help="new branch only: skip the slow standard builds")
    w = sub.add_parser("hw")
    w.add_argument("new", type=Path)
    w.add_argument("--cases", nargs="+", default=list(CASES), choices=CASES)
    c = sub.add_parser("compare")
    c.add_argument("base", type=Path)
    c.add_argument("new", type=Path)
    c.add_argument("--cases", nargs="+", default=list(CASES), choices=CASES)
    a = ap.parse_args()
    if a.cmd == "build":
        build(a.out, a.cases, a.skip_standard)
    elif a.cmd == "hw":
        hw(a.new, a.cases)
    else:
        compare(a.base, a.new, a.cases)


if __name__ == "__main__":
    sys.exit(main())
