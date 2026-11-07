"""Build the nov2025 vs nov2026 optimization-level comparison data.

Reads the harvested case folders of the HHL nelem 5 optimization-level sweep
(final run only; run 1, where the level flag had no effect, is excluded) and
writes, next to this file:
  data/per_step.csv  one row per (codebase, opt level, shots, Newton step)
  data/per_case.csv  one row per case, summarised over its Newton steps
  data/compare.xlsx  the two tables as sheets, for Excel

Usage: ~/.venvs/tooling/bin/python build_compare_data.py [results_dir]
"""
import argparse
import glob
import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(os.path.dirname(HERE), "inputs")
DEFAULT_RESULTS = os.path.normpath(os.path.join(
    HERE, "..", "..", "..", "..", "results", "fvm_euler_1d_solver",
    "2026-11-07-hhl-nelem5-optlevel"))
CODEBASES = {"nov2025": "venv-freeze-nov2025.txt",
             "nov2026": "venv-freeze-nov2026.txt"}

# source column -> output column, per source file
METRIC_COLS = {"fidelity": "fidelity", "l2_error_rel": "l2_error_rel",
               "l2_error_normalized": "l2_error_normalized",
               "linsys_residual": "linsys_residual"}
CIRC_COLS = {"circ_qubits_transpile": "circ_qubits",
             "circ_depth_transpile": "circ_depth",
             "circ_gates_transpile": "circ_gates",
             "circ_depth_orig": "circ_depth_generated",
             "circ_gates_orig": "circ_gates_generated",
             "circ_generate_time": "circ_generate_s",
             "circ_transpile_time": "circ_transpile_s",
             "circ_run_time": "circ_run_s",
             "condition_number": "condition_number"}


def read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def one(case_dir: str, pattern: str) -> str:
    hits = sorted(glob.glob(os.path.join(case_dir, pattern)))
    if not hits:
        raise FileNotFoundError(f"{pattern} in {case_dir}")
    return hits[0]


def package_versions(freeze_file: str) -> dict:
    text = open(os.path.join(INPUTS, freeze_file)).read()
    out = {}
    for pkg in ("qiskit", "qiskit-aer"):
        m = re.search(rf"^{pkg}==(\S+)$", text, re.M)
        out[pkg.replace("-", "_")] = m.group(1) if m else ""
    return out


def load_case(case_dir: str) -> tuple[pd.DataFrame, dict]:
    """Per-step frame and run-level facts for one harvested case folder."""
    hm = read_csv(one(case_dir, "hhl_metrics_*.csv"))
    qm = read_csv(one(case_dir, "qc_metadata_*.csv"))
    rs = read_csv(one(case_dir, "residual_*.csv"))
    df = hm[["step"] + list(METRIC_COLS)].rename(columns=METRIC_COLS)
    circ = qm[["step"] + [c for c in CIRC_COLS if c in qm.columns]]
    df = df.merge(circ.rename(columns=CIRC_COLS), on="step", how="left")
    # residual_*.csv row n is the Newton residual after step n
    res = pd.DataFrame({"step": rs["iters"].astype(int),
                        "newton_residual": rs["residual_total"]})
    df = df.merge(res, on="step", how="left")
    ana = json.load(open(one(case_dir, "q8020_analysis_*_0.json")))
    return df, {"converged": ana.get("converged", "")}


def summarize(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    body = df.iloc[:-1] if len(df) > 1 else df
    return {
        "newton_steps": len(df),
        "circ_qubits": int(df["circ_qubits"].max()),
        "circ_depth_max": int(df["circ_depth"].max()),
        "circ_depth_step0": int(df["circ_depth"].iloc[0]),
        "circ_gates_max": int(df["circ_gates"].max()),
        "circ_gates_step0": int(df["circ_gates"].iloc[0]),
        "circ_transpile_s_total": df["circ_transpile_s"].sum(),
        "circ_transpile_s_mean": df["circ_transpile_s"].mean(),
        "circ_run_s_mean": df["circ_run_s"].mean(),
        "fidelity_mean": df["fidelity"].mean(),
        "fidelity_mean_excl_last": body["fidelity"].mean(),
        "fidelity_min_excl_last": body["fidelity"].min(),
        "fidelity_max_excl_last": body["fidelity"].max(),
        "fidelity_last": last["fidelity"],
        "l2_error_rel_last": last["l2_error_rel"],
        "newton_residual_last": last["newton_residual"],
    }


def main(results_dir: str) -> None:
    steps, cases = [], []
    for cb, freeze in CODEBASES.items():
        vers = package_versions(freeze)
        for case_dir in sorted(glob.glob(os.path.join(results_dir, cb,
                                                      "shots*", "opt*"))):
            shots = int(os.path.basename(os.path.dirname(case_dir))[5:])
            level = int(os.path.basename(case_dir)[3:])
            df, facts = load_case(case_dir)
            key = {"codebase": cb, **vers, "opt_level": level, "shots": shots}
            steps.append(df.assign(**key)[list(key) + list(df.columns)])
            cases.append({**key, **facts, **summarize(df)})
    per_step = pd.concat(steps, ignore_index=True).sort_values(
        ["shots", "codebase", "opt_level", "step"])
    per_case = pd.DataFrame(cases).sort_values(
        ["shots", "codebase", "opt_level"])
    out = os.path.join(HERE, "data")
    os.makedirs(out, exist_ok=True)
    per_step.to_csv(os.path.join(out, "per_step.csv"), index=False)
    per_case.to_csv(os.path.join(out, "per_case.csv"), index=False)
    with pd.ExcelWriter(os.path.join(out, "compare.xlsx")) as xw:
        per_case.to_excel(xw, sheet_name="per_case", index=False)
        per_step.to_excel(xw, sheet_name="per_step", index=False)
    print(f"{len(per_case)} cases, {len(per_step)} step rows -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("results_dir", nargs="?", default=DEFAULT_RESULTS)
    main(ap.parse_args().results_dir)
