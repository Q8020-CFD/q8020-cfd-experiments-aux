"""Step-0 depth and 150k-shot fidelity of HHL, LuGo, the real-L rewrite
and AQC at nelem 5.

Six circuits of the fvm nozzle's first Newton step (nelem 5, 14 qubits):
HHL built by qiskit 1.x and by 2.x, LuGo built by qiskit 1.x (2026-02-26)
and by 2.x (2026-11-03 rerun), the LuGo 2.x circuit after the exact real-L
structured rewrite, and that rewrite with L refitted by AQC at 74 CX
(approximate). All six are compiled the same way, with qiskit
2.6.0 at optimization level 2, seed_transpiler 1, to all-to-all
cx/rz/sx/x, FakeMarrakesh (IBM Heron r2) and FakeNighthawk. Nothing is run
here: depths and 150k-shot fidelities are read from recorded results.

Writes depth_nelem5.csv, fidelity_nelem5.csv and figures/depth_nelem5.{pdf,png}
next to this script. Run with the tooling venv (pandas, matplotlib).
"""
import glob
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import LogLocator, NullFormatter

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
RES = EXP / "results" / "fvm_euler_1d_solver"
LUGO_RW = RES / "2026-11-17-hhl-structured-rewrite-from-lugo"
TABLE8 = RES / "2026-11-18-table8-qiskit26" / "table8_columns.csv"
CASES = RES / "nov2025-rerun" / "analysis" / "cases.csv"
FEB26 = RES / "2026-02-26-LuGo" / "nelem5" / "statevector" / "shots_150000"

METHODS = ["HHL 1.x", "HHL 2.x", "LuGo 1.x", "LuGo 2.x", "rewrite",
           "AQC 74"]
LABELS = ["HHL\nqiskit 1.x", "HHL\nqiskit 2.x", "LuGo\nqiskit 1.x",
          "LuGo\nqiskit 2.x", "LuGo 2.x +\nrewrite",
          "+ AQC (74 CX)"]
REAL = LUGO_RW / "nelem5-barriers-realL-aqc106"
AQC74 = LUGO_RW / "nelem5-barriers-realL-aqc74"
TARGETS = ["all-to-all", "heron", "nighthawk"]
TARGET_LABELS = ["ideal (all-to-all)", "IBM Heron r2", "IBM Nighthawk"]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3
MARKERS = ["o", "s", "D"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#ffffff"


def depths() -> pd.DataFrame:
    t8 = pd.read_csv(TABLE8).replace({"target": {"a2a": "all-to-all"}})
    raw = pd.read_csv(LUGO_RW / "hhl-raw-depth" / "hhl_raw_depth.csv")
    raw = raw.replace({"target": {"a2a": "all-to-all"}})
    lugo1 = pd.read_csv(LUGO_RW / "nelem5-barriers" / "counts.csv")
    real = pd.read_csv(REAL / "counts.csv")
    aqc = pd.read_csv(AQC74 / "counts.csv")
    parts = [
        ("HHL 1.x", raw, LUGO_RW / "hhl-raw-depth" / "hhl_raw_depth.csv"),
        ("HHL 2.x", t8[t8.circuit == "hhl_qiskit26"], TABLE8),
        ("LuGo 1.x", lugo1[lugo1.circuit == "lugo"],
         LUGO_RW / "nelem5-barriers" / "counts.csv"),
        ("LuGo 2.x", t8[t8.circuit == "lugo_nov26"], TABLE8),
        ("rewrite", real[real.circuit == "exact"], REAL / "counts.csv"),
        ("AQC 74", aqc[aqc.circuit == "aqc"], AQC74 / "counts.csv"),
    ]
    rows = []
    for m, df, src in parts:
        for _, r in df.iterrows():
            rows.append({"method": m, "target": r.target,
                         "depth": int(r.depth),
                         "two_qubit_gates": int(r.two_qubit_gates),
                         "two_qubit_depth": int(r.two_qubit_depth),
                         "source": str(src.relative_to(EXP))})
    d = pd.DataFrame(rows)
    assert len(d) == 18 and set(d.target) == set(TARGETS), d
    return d


def fidelities() -> pd.DataFrame:
    c = pd.read_csv(CASES)
    c = c[(c.nelem == 5) & (c.shots == 150000)]
    feb = []
    for f in sorted(glob.glob(str(FEB26 / "*" / "hhl_metrics_*.csv"))):
        m = pd.read_csv(f, skipinitialspace=True)
        feb.append(float(m[m.step == 0].fidelity.iloc[0]))
    shots = pd.read_csv(REAL / "shots.csv")
    shots74 = pd.read_csv(AQC74 / "shots.csv")
    sets = {
        "HHL 1.x": (c[c.top == "nov_pkgs"].step0_fidelity,
                    "nov2025-rerun nov_pkgs (Frontier, 11-04 and 11-05)"),
        "HHL 2.x": (c[c.top == "latest_pkgs"].step0_fidelity,
                    "nov2025-rerun latest_pkgs (Frontier, qiskit 2.6.2)"),
        "LuGo 1.x": (pd.Series(feb), "2026-02-26-LuGo shots_150000"),
        "LuGo 2.x": (c[c.top == "LuGo-rerun"].step0_fidelity,
                     "nov2025-rerun LuGo-rerun (qiskit 2.6.1)"),
        "rewrite": (shots[shots.variant == "exact"].fidelity,
                    "realL rewrite, Aer seeds 1-10"),
        "AQC 74": (shots74[shots74.variant == "aqc"].fidelity,
                   "realL AQC at 74 CX, Aer seeds 1-10"),
    }
    rows = []
    for m, (v, src) in sets.items():
        v = pd.Series(v, dtype=float)
        rows.append({"method": m, "n": len(v), "median": v.median(),
                     "min": v.min(), "max": v.max(), "source": src})
    return pd.DataFrame(rows)


def compact(n: int) -> str:
    if n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if n >= 1e5:
        return f"{n / 1e3:.0f}k"
    return f"{n / 1e3:.1f}k"


def plot(d: pd.DataFrame, f: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2,
                         "axes.labelcolor": INK2, "xtick.color": INK,
                         "ytick.color": INK2, "font.family": "sans-serif"})
    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    # markers, not bars: on a log axis a bar's length from an arbitrary
    # floor means nothing; shape is the secondary encoding of the target
    w = 0.18
    for j, (tgt, lab, col, mk) in enumerate(zip(TARGETS, TARGET_LABELS,
                                                COLORS, MARKERS)):
        xs, ys = [], []
        for i, m in enumerate(METHODS):
            xs.append(i + (j - 1) * w)
            ys.append(int(d[(d.method == m) & (d.target == tgt)].depth.iloc[0]))
        ax.plot(xs, ys, linestyle="none", marker=mk, markersize=8,
                color=col, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label=lab, zorder=3)
        if tgt == "all-to-all":  # selective direct labels
            for x, y in zip(xs, ys):
                ax.text(x - 0.07, y, compact(y), ha="right", va="center",
                        fontsize=7.5, color=INK, zorder=4)
    ax.set_yscale("log")
    ax.set_ylim(5e3, 3e7)
    ax.set_xlim(-0.6, len(METHODS) - 0.4)
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylabel("Transpiled circuit depth (log scale)")
    ax.set_xticks(range(len(METHODS)))
    ax.set_xticklabels(LABELS)
    ax.tick_params(axis="x", length=0)
    # fidelity as a third label line under each column (one y axis only);
    # the caption says it is the median 150k-shot Aer fidelity
    fmed = f.set_index("method")["median"]
    for i, m in enumerate(METHODS):
        ax.annotate(f"F = {fmed[m]:.4f}", xy=(i, 0), xycoords=("data",
                    "axes fraction"), xytext=(0, -34), textcoords="offset "
                    "points", ha="center", va="top", fontsize=8, color=INK2)
    ax.grid(axis="y", which="major", color=GRID, linewidth=0.8, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", frameon=False, fontsize=8,
              labelcolor=INK2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.24)
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    fig.savefig(out / "depth_nelem5.pdf")
    fig.savefig(out / "depth_nelem5.png", dpi=200)


def main() -> None:
    d, f = depths(), fidelities()
    d.to_csv(HERE / "depth_nelem5.csv", index=False)
    f.to_csv(HERE / "fidelity_nelem5.csv", index=False, float_format="%.5f")
    print(d.pivot(index="method", columns="target", values="depth")
          .loc[METHODS, TARGETS].to_string())
    print(f.to_string(index=False))
    plot(d, f)


if __name__ == "__main__":
    main()
