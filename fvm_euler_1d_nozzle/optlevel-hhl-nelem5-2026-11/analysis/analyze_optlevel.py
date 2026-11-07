"""Analysis of the HHL nelem 5 optimization-level sweep (nov2025 vs nov2026).

Usage: analyze_optlevel.py <results_dir> <out_dir>
results_dir layout: <codebase>/shots<N>/opt<L>/ (harvested case dirs).
Writes per_step.csv, summary.csv, summary.md and plots into out_dir.
Python: use ~/.venvs/tooling/bin/python (pandas, matplotlib).
"""
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


def read_csv(path: str) -> pd.DataFrame:
  df = pd.read_csv(path, skipinitialspace=True)
  df.columns = [c.strip() for c in df.columns]
  return df


def first_json(d: str, pattern: str) -> dict:
  fs = sorted(glob.glob(os.path.join(d, pattern)))
  return json.load(open(fs[0])) if fs else {}


def load_case(d: str, cb: str, shots: int, lvl: int):
  """Return (per-step DataFrame, summary dict) for one case directory."""
  one = lambda p: (glob.glob(os.path.join(d, p)) or [None])[0]
  m = one("hhl_metrics_*.csv")
  q = one("qc_metadata_*.csv")
  summ = dict(codebase=cb, opt_level=lvl, shots=shots)
  if not (m and q):
    summ["note"] = "no per-step data"
    return None, summ
  hm, qm = read_csv(m), read_csv(q)
  df = hm.merge(qm[[c for c in (
      "step", "circ_qubits_transpile", "circ_depth_transpile",
      "circ_gates_transpile", "circ_generate_time", "circ_transpile_time",
      "circ_run_time") if c in qm.columns]], on="step", how="left")
  df.insert(0, "codebase", cb)
  df.insert(1, "opt_level", lvl)
  df.insert(2, "shots", shots)
  ana = first_json(d, "q8020_analysis_*_0.json")
  exp = first_json(d, "q8020_experiment_*_0.json")
  stats = first_json(d, "q8020_sweep_exec_stats_*_0.json")
  res = first_json(d, "q8020_results_*_0.json")
  steps = ana.get("iterations_completed", len(df))
  summ.update(
      exit=stats.get("exit_code", ""),
      newton_steps=steps,
      converged=ana.get("converged", ""),
      final_l2_rel=df["l2_error_rel"].iloc[-1],
      final_l2_norm=df["l2_error_normalized"].iloc[-1],
      max_width=df["circ_qubits_transpile"].max(),
      max_depth=df["circ_depth_transpile"].max(),
      max_gates=df["circ_gates_transpile"].max(),
      transpile_s=df["circ_transpile_time"].sum(),
      execute_s=df["circ_run_time"].sum(),
      generate_s=df["circ_generate_time"].sum(),
      wall_s=stats.get("duration_seconds", ""),
  )
  return df, summ


def main(rd: str, out: str) -> None:
  os.makedirs(out, exist_ok=True)
  steps, rows = [], []
  for d in sorted(glob.glob(os.path.join(rd, "*", "shots*", "opt*"))):
    p = d.split(os.sep)
    cb, shots, lvl = p[-3], int(p[-2][5:]), int(p[-1][3:])
    df, s = load_case(d, cb, shots, lvl)
    if df is not None:
      steps.append(df)
    rows.append(s)
  per = pd.concat(steps, ignore_index=True)
  summ = pd.DataFrame(rows).sort_values(["codebase", "shots", "opt_level"])
  per.to_csv(os.path.join(out, "per_step.csv"), index=False)
  summ.to_csv(os.path.join(out, "summary.csv"), index=False)
  with open(os.path.join(out, "summary.md"), "w") as f:
    f.write(summ.to_markdown(index=False, floatfmt=".4g"))
    f.write("\n")

  # plots: one figure per metric; panels shots 0 / 150000; lines opt level
  # by codebase (solid nov2026, dashed nov2025)
  metrics = [("l2_error_rel", "L2 error vs LU (relative), per step", True),
             ("circ_depth_transpile", "Transpiled depth", False),
             ("circ_transpile_time", "Transpile time (s)", False),
             ("circ_run_time", "Execute time (s)", False)]
  colors = {0: "C0", 1: "C1", 2: "C2", 3: "C3"}
  for col, title, logy in metrics:
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, sh in zip(axs, (0, 150000)):
      for (cb, lvl), g in per[per.shots == sh].groupby(["codebase", "opt_level"]):
        ax.plot(g["step"], g[col], color=colors[lvl], marker="o", ms=3,
                ls="-" if cb == "nov2026" else "--",
                label=f"{cb} opt{lvl}")
      ax.set_title(f"shots {sh}")
      ax.set_xlabel("Newton step")
      if logy:
        ax.set_yscale("log")
      ax.grid(alpha=0.3)
    axs[0].set_ylabel(title)
    axs[1].legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"{col}.png"), dpi=130)
    plt.close(fig)

  # nov2025 vs nov2026 at each level: totals
  tot = summ.pivot_table(index=["shots", "opt_level"], columns="codebase",
                         values=["max_depth", "transpile_s", "execute_s",
                                 "final_l2_rel"])
  tot.to_csv(os.path.join(out, "codebase_comparison.csv"))
  with open(os.path.join(out, "codebase_comparison.md"), "w") as f:
    f.write(tot.to_markdown(floatfmt=".4g"))
    f.write("\n")


if __name__ == "__main__":
  main(sys.argv[1], sys.argv[2])
