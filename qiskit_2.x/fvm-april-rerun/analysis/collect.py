"""Collect per-case metrics for the April 2026 fvm CFL sweep and its AWS reruns.

Sets compared (nelem 5, HHL statevector, 150k shots, 15 outer / 1 inner, BDF1):
  april  original Frontier run, results/fvm_euler_1d_solver/2026-04-05/_52d087d1
  old    AWS rerun on the April stack (fvm 9e76e398, qiskit 2.3.1)
  new    AWS rerun on the latest stack (fvm 38a41e52, qiskit 2.6.1)

Writes analysis/cases.csv, one row per case. Reference solutions are the
classical LU runs in analysis/lu_ref/ (same solver, same CFL).

Usage: python collect.py   (from anywhere; paths are relative to this file)
"""
import csv
import glob
import json
import math
import os
import re
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
RERUN = os.path.dirname(HERE)
WORKSPACE = os.path.abspath(os.path.join(RERUN, "..", "..", ".."))
APRIL = os.path.join(WORKSPACE, "q8020-cfd-experiments", "results",
                     "fvm_euler_1d_solver", "2026-04-05", "_52d087d1")
CFL_BY_GROUP = {0: "1", 1: "5", 2: "10", 3: "25", 4: "1e10"}


def read_csv(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f, skipinitialspace=True))
    head = [h.strip() for h in rows[0]]
    return [dict(zip(head, (float(v) if _num(v) else v for v in r))) for r in rows[1:] if r]


def _num(v):
    try:
        float(v)
        return True
    except ValueError:
        return False


def one(pattern):
    hits = glob.glob(pattern, recursive=True)
    if len(hits) != 1:
        raise FileNotFoundError(f"{len(hits)} matches for {pattern}")
    return hits[0]


def rel_l2(sol, ref):
    num = sum((s[k] - r[k]) ** 2 for s, r in zip(sol, ref) for k in ("rho", "u", "p"))
    den = sum(r[k] ** 2 for r in ref for k in ("rho", "u", "p"))
    return math.sqrt(num / den)


REF_CONV = {c: read_csv(one(f"{HERE}/lu_ref/converged_cfl{c}/final_results_*.csv"))
            for c in CFL_BY_GROUP.values()}
REF_15 = {c: read_csv(one(f"{HERE}/lu_ref/iters15_cfl{c}/final_results_*.csv"))
          for c in CFL_BY_GROUP.values()}
REF_15_RES = {c: read_csv(one(f"{HERE}/lu_ref/iters15_cfl{c}/residual_*.csv"))[-1]["residual_total"]
              for c in CFL_BY_GROUP.values()}


def metrics(case_dir, label, group, trial):
    cfl = CFL_BY_GROUP[group]
    meta = json.load(open(one(f"{case_dir}/q8020_metadata_*.json")))
    qc = read_csv(one(f"{case_dir}/qc_metadata_*.csv"))
    hhl = read_csv(one(f"{case_dir}/hhl_metrics_*.csv"))
    res = read_csv(one(f"{case_dir}/residual_*.csv"))
    sol = read_csv(one(f"{case_dir}/final_results_*.csv"))
    exec_stats = meta["exec_stats"][0]
    return {
        "set": label, "cfl": cfl, "group": group, "trial": trial,
        "case_dir": os.path.relpath(case_dir, WORKSPACE),
        "success": exec_stats.get("success"),
        "n_solves": len(qc),
        "residual_final": res[-1]["residual_total"],
        "residual_reduction": res[-1]["residual_total"] / res[0]["residual_total"],
        "lu15_residual_final": REF_15_RES[cfl],
        "relL2_vs_steady": rel_l2(sol, REF_CONV[cfl]),
        "relL2_vs_lu15": rel_l2(sol, REF_15[cfl]),
        "fidelity_mean": mean(h["fidelity"] for h in hhl),
        "fidelity_min": min(h["fidelity"] for h in hhl),
        "l2n_mean": mean(h["l2_error_normalized"] for h in hhl),
        "kappa_iter0": qc[0]["condition_number"],
        "gates_iter0": qc[0]["circ_gates_transpile"],
        "depth_iter0": qc[0]["circ_depth_transpile"],
        "gates_mean": mean(q["circ_gates_transpile"] for q in qc),
        "t_generate_s": sum(q["circ_generate_time"] for q in qc),
        "t_transpile_s": sum(q["circ_transpile_time"] for q in qc),
        "t_run_s": sum(q["circ_run_time"] for q in qc),
        "t_case_s": exec_stats["duration_seconds"],
        "start": exec_stats["start_time"], "end": exec_stats["end_time"],
        "host": (meta.get("experiment") or [{}])[0].get("hostname", ""),
    }


def collect():
    rows = []
    for d in glob.glob(f"{APRIL}/time_steps_*/trial_*"):
        g = int(re.search(r"time_steps_(\d)", d)[1])
        t = int(re.search(r"trial_(\d+)_", d)[1])
        rows.append(metrics(d, "april", g, t))
    for label in ("old", "new"):
        for d in glob.glob(f"{RERUN}/{label}/apr05/time_steps_*_trial_*"):
            m = re.search(r"time_steps_(\d)_trial_(\d+)$", d)
            case_dir = os.path.dirname(one(f"{d}/**/q8020_metadata_*.json"))
            rows.append(metrics(case_dir, label, int(m[1]), int(m[2])))
    rows.sort(key=lambda r: (r["set"], r["group"], r["trial"]))
    out = os.path.join(HERE, "cases.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} cases -> {out}")


if __name__ == "__main__":
    collect()
