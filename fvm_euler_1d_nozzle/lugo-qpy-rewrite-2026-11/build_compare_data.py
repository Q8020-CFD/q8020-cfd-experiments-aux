"""Gather the LuGo comparison into data/: feb26, nov26 and the qpy rewrite.

Sets (nozzle nelem 5 and 10, HHL with the LuGo QPE, Aer ideal simulator):
  feb26    ORNL run 2026-02-26 on Frontier, qiskit 1.4.5 (the version that
           wrote its qpy), recorded results
  nov26    LuGo rerun 2026-11-03 on Frontier, qiskit 2.6 (per operator; the
           results folder does not record it), recorded results
  rewrite  the feb26 step-0 qpy after qpy_rewrite, transpiled and executed
           on a macos-laptop with qiskit 2.6.0 / Aer 0.17.2 (run_step0.py)
  control  the feb26 step-0 qpy executed by run_step0.py as stored and
           re-transpiled, to show the pipeline reproduces the recorded run

Only step 0 can be compared like for like: the rewrite exists for step 0 only.
Full-run columns (Newton steps, final residual) are filled for feb26 and
nov26 as context.

Writes data/per_set.csv, data/step0_trials.csv and data/compare.xlsx.
Usage: ~/.venvs/tooling/bin/python build_compare_data.py [--res DIR] [--nelem 5 10]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
RES = EXP / "results/fvm_euler_1d_solver"
REWRITE = RES / "2026-11-08-lugo-qpy-rewrite"
RECORDED = {"feb26": RES / "2026-02-26-LuGo",
            "nov26": RES / "nov2025-rerun/LuGo-rerun"}
QISKIT = {"feb26": "1.4.5", "nov26": "2.6", "rewrite": "2.6.0",
          "control_stored": "1.4.5 transpile, Aer 0.17.2 run",
          "control_qiskit26": "2.6.0"}
WHERE = {"feb26": "Frontier", "nov26": "Frontier", "rewrite": "macos-laptop",
         "control_stored": "macos-laptop", "control_qiskit26": "macos-laptop"}
VARIANT_SET = {"rewrite_qiskit26": "rewrite", "feb26_stored": "control_stored",
               "feb26_qiskit26": "control_qiskit26"}
SHOTS = 150000
NELEM = (5, 10)


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, skipinitialspace=True)


def one(d: Path, pat: str) -> Path | None:
    hits = sorted(d.glob(pat))
    return hits[0] if hits else None


def recorded_case(d: Path) -> dict:
    """Step-0 metrics and full-run outcome of one recorded case folder."""
    h = read(one(d, "hhl_metrics_*.csv"))
    q = read(one(d, "qc_metadata_*.csv"))
    r = read(one(d, "residual_*.csv"))
    h0, q0 = h[h.step == 0].iloc[0], q[q.step == 0].iloc[0]
    return {
        "fidelity": h0.fidelity, "l2_error_rel": h0.l2_error_rel,
        "l2_error_normalized": h0.l2_error_normalized,
        "qubits": int(q0.circ_qubits_transpile),
        "aer_depth": int(q0.circ_depth_transpile),
        "aer_gates": int(q0.circ_gates_transpile),
        "generate_s": q0.circ_generate_time,
        "transpile_s": q0.circ_transpile_time, "run_s": q0.circ_run_time,
        "newton_steps": int(len(r)),
        "final_residual": float(r.iloc[-1].residual_total),
    }


def recorded(setname: str, nelem: int) -> tuple[dict, list[dict]]:
    base = RECORDED[setname] / f"nelem{nelem}/statevector"
    ex = recorded_case(base / "exact")
    trials = []
    for t in sorted((base / f"shots_{SHOTS}").glob("trial_*")):
        c = recorded_case(t)
        trials.append({"set": setname, "nelem": nelem,
                       "trial": int(t.name.split("_")[1]), **c})
    return ex, trials


def summarize(setname: str, nelem: int, ex: dict, trials: list[dict],
              circ: dict) -> dict:
    tr = pd.DataFrame(trials)
    row = {"set": setname, "qiskit": QISKIT[setname], "machine": WHERE[setname],
           "nelem": nelem, "qubits": ex.get("qubits", circ.get("qubits")),
           "aer_depth": ex.get("aer_depth", circ.get("aer_depth")),
           "aer_gates": ex.get("aer_gates", circ.get("aer_gates")),
           "a2a_cx": circ.get("a2a_cx", np.nan),
           "a2a_2q_depth": circ.get("a2a_2q_depth", np.nan),
           "a2a_depth": circ.get("a2a_depth", np.nan),
           "heron_cz": circ.get("heron_cz", np.nan),
           "heron_2q_depth": circ.get("heron_2q_depth", np.nan),
           "heron_depth": circ.get("heron_depth", np.nan),
           "sv_fidelity": ex["fidelity"], "sv_l2_error_rel": ex["l2_error_rel"],
           "sv_l2_error_normalized": ex["l2_error_normalized"],
           "shots": SHOTS, "shots_n": len(tr)}
    for k in ("fidelity", "l2_error_rel", "l2_error_normalized"):
        row[f"shots_{k}_min"] = tr[k].min()
        row[f"shots_{k}_median"] = tr[k].median()
        row[f"shots_{k}_max"] = tr[k].max()
    if "shots_used" in tr:
        row["shots_used_median"] = tr.shots_used.median()
    for k in ("newton_steps", "final_residual"):
        row[f"sv_{k}"] = ex.get(k, np.nan)
    if "final_residual" in tr:
        row["shots_final_residual_median"] = tr.final_residual.median()
        row["shots_newton_steps_median"] = tr.newton_steps.median()
    for k in ("generate_s", "transpile_s", "run_s"):
        row[f"step0_{k}"] = ex.get(k, np.nan)
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--res", default=str(REWRITE), help="run results folder")
    ap.add_argument("--nelem", type=int, nargs="+", default=list(NELEM))
    a = ap.parse_args()
    rdir = Path(a.res).expanduser()
    circ = pd.concat([read(p) for p in rdir.glob("nelem*/circuits_*.csv")])
    sv = pd.concat([read(p) for p in rdir.glob("nelem*/step0_statevector_*.csv")])
    sh = pd.concat([read(p) for p in rdir.glob("nelem*/step0_shots_*.csv")])
    rows, trials = [], []
    for nelem in a.nelem:
        stored = circ[(circ.nelem == nelem) & (circ.variant == "feb26_stored")]
        for s in ("feb26", "nov26"):
            ex, tr = recorded(s, nelem)
            c = stored.iloc[0].to_dict() if s == "feb26" and len(stored) else {}
            c = {k: v for k, v in c.items() if k.startswith(("a2a", "heron"))}
            rows.append(summarize(s, nelem, ex, tr, c))
            trials += tr
        for var, s in VARIANT_SET.items():
            c = circ[(circ.nelem == nelem) & (circ.variant == var)]
            if not len(c):
                continue
            c = c.iloc[0].to_dict()
            e = sv[(sv.nelem == nelem) & (sv.variant == var)].iloc[0].to_dict()
            ex = {k: e[k] for k in ("fidelity", "l2_error_rel",
                                    "l2_error_normalized")}
            ex.update(generate_s=c.get("rewrite_s") or np.nan,
                      transpile_s=c.get("aer_transpile_s") or np.nan,
                      run_s=c.get("sv_run_s"))
            t = sh[(sh.nelem == nelem) & (sh.variant == var)]
            tr = [{"set": s, "nelem": nelem, "trial": int(r.seed),
                   "fidelity": r.fidelity, "l2_error_rel": r.l2_error_rel,
                   "l2_error_normalized": r.l2_error_normalized,
                   "shots_used": int(r.shots_used)} for r in t.itertuples()]
            rows.append(summarize(s, nelem, ex, tr, c))
            trials += tr
    out = HERE / "data"
    out.mkdir(exist_ok=True)
    per_set = pd.DataFrame(rows)
    per_trial = pd.DataFrame(trials)
    per_set.to_csv(out / "per_set.csv", index=False)
    per_trial.to_csv(out / "step0_trials.csv", index=False)
    with pd.ExcelWriter(out / "compare.xlsx") as xw:
        per_set.to_excel(xw, sheet_name="per_set", index=False)
        per_trial.to_excel(xw, sheet_name="step0_trials", index=False)
    cols = ["set", "nelem", "qubits", "aer_depth", "a2a_cx", "heron_cz",
            "sv_fidelity", "sv_l2_error_rel", "shots_fidelity_min",
            "shots_fidelity_median", "shots_fidelity_max"]
    print(per_set[cols].to_string(index=False))


if __name__ == "__main__":
    main()
