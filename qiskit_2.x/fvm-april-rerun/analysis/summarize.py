"""Print per-CFL comparison of april / old / new from cases.csv (run collect.py first)."""
import collections
import csv
from statistics import median

from scipy.stats import mannwhitneyu

KEEP_STR = {"set", "cfl", "case_dir", "success", "start", "end", "host"}
R = list(csv.DictReader(open("cases.csv")))
for r in R:
    for k in r:
        if k not in KEEP_STR:
            r[k] = float(r[k])
by = collections.defaultdict(list)
for r in R:
    by[(r["cfl"], r["set"])].append(r)
CFLS = ["1", "5", "10", "25", "1e10"]
SETS = ("april", "old", "new")


def g(v):
    return f"{v:.3g}"


print("== median [min-max] over 10 trials; p = Mann-Whitney U vs april")
for metric in ("residual_final", "relL2_vs_steady", "relL2_vs_lu15", "fidelity_mean", "l2n_mean",
               "t_case_s", "t_generate_s", "t_transpile_s", "t_run_s"):
    print(f"\n-- {metric}")
    for c in CFLS:
        a = [x[metric] for x in by[(c, "april")]]
        line = f"cfl={c:5s}"
        for s in SETS:
            v = [x[metric] for x in by[(c, s)]]
            p = "" if s == "april" else f" p={mannwhitneyu(v, a).pvalue:.2f}"
            line += f" | {s}: {g(median(v))} [{g(min(v))}-{g(max(v))}]{p}"
        if metric == "residual_final":
            line += f" | LU15: {g(by[(c, 'april')][0]['lu15_residual_final'])}"
        print(line)

print("\n== iter-0 transpiled gate counts (value x count)")
for c in CFLS:
    print(f"cfl={c:5s} " + " | ".join(
        f"{s}: " + ", ".join(f"{int(k)}x{n}" for k, n in
                             sorted(collections.Counter(x["gates_iter0"] for x in by[(c, s)]).items()))
        for s in SETS))
print("\n== kappa at iter 0:", {c: round(by[(c, "april")][0]["kappa_iter0"], 2) for c in CFLS})
