# Reproduce 11 -- benchmark fairness numbers, independent recomputation

Independent reproduction of the numerical claims of work item 11 (fixed-basis
circuit metrics, effective shots, reference-free sign, seeds) in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` at
`feature/sqls-aiaa-4q26` @ `484b24ed`. All numbers below were recomputed with
the code shown here; none were taken from the build / verify / status notes
(not read). Session 2026-10-15T08:49Z to 2026-10-15T09:01Z, Apple M3 Pro,
macOS 26.7.1, Python 3.12.10 (`.venv`), qiskit 2.5.2, qiskit-aer 0.17.2,
numpy 2.5.2, scipy 1.18.0.

Dependencies as found on disk (both carry uncommitted local edits, which the
fb_* numbers rely on):

- sqls `/Users/agallojr/proj/src/q8020/sqls` @ `9a4346a` + modified
  `src/sqls/runtime/quantum.py` (exposes `sqls_out['qc']`, keyword-only `seed`).
- quantum_linear_solvers `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`
  @ `66eadf0` + 8 modified files (`linear_solvers/hhl.py`, matrices, tests).

Inputs: archived systems in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/tests/data/`
(`system_Ab_nelem5_iter0.pkl` 15x15, cond 95.98, ||b|| 12.375;
`system_Ab_nelem5_iter6.pkl` 15x15, cond 67.39, ||b|| 1.260e-9;
`system_Ab_nelem2_iter0.pkl` 6x6, cond 38.31, ||b|| 1.314; sha256s in
`tests/data/provenance.json`). Scratch was `/tmp/order3-reproduce-11/`
(195 MB, deleted at the end). No repo was written to (`git status` clean in
fvm, sqls, quantum_linear_solvers afterwards; `output/` mtimes unchanged).

## Solver runs (all `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`, from the fvm repo root)

| run | extra flags | start (UTC) | wall |
|---|---|---|---|
| sqls_n5_sv | `-nelem 5 -linsolver SQLS -shots 0 -iters 1` | 2026-10-15T08:53:31Z | 2.14 s |
| sqls_n2_s5000_r2 | `-nelem 2 -linsolver SQLS -shots 5000 -sqls_repeats 2 -iters 1` | 08:53:33Z | 1.99 s |
| hhl_n2_sv | `-nelem 2 -linsolver HHL -shots 0 -iters 1` | 08:53:36Z | 12.90 s |
| seed7_a / seed7_b | `-nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -seed 7 -iters 2` | 08:53:49Z / 08:53:51Z | 2.52 s / 2.23 s |
| noseed_a / noseed_b | `-nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2` | 08:53:54Z / 08:53:56Z | 2.15 s / 2.18 s |
| HHL nelem 5 in-process (one solve) | `QuantumHHL.solve_one_step` on archived iter-0 system | 08:57:21Z | 101.44 s |

Each run: `.venv/bin/python nozzle_1d_solver.py <flags> -outdir /tmp/order3-reproduce-11/<run>`.
Six short CLI runs, one HHL nelem-2 CLI run, one HHL nelem-5 in-process solve.

## A. Fixed-basis circuit metrics

Solver recipe (read from `quantum_tools.count_circuit_metrics`, lines 167-192):
`transpile(circ.remove_final_measurements(inplace=False), basis_gates=['u3','cx'],
optimization_level=0, seed_transpiler=0)`; `fb_total_gates` = every op of the
result including the `reset`s of `Initialize`; wall time to `t_count_s`.
The counter runs on the generated (pre-Aer-transpile) circuit for HHL and on
`sqls_out['qc']` for SQLS. My counter (same recipe, my own call):

```python
def my_count(qc, basis=('u3', 'cx'), level=0):
  c = qc.remove_final_measurements(inplace=False)
  tc = transpile(c, basis_gates=list(basis), optimization_level=level,
                 seed_transpiler=0)
  ops = tc.count_ops()
  return dict(cx=int(ops.get('cx', 0)), depth=int(tc.depth()),
              total=int(sum(ops.values())), ops=dict(ops))
```

SQLS circuit built as `QuantumSQLS.solve_one_step` does (lines 913-985):

```python
A2, b2 = convert_to_pow2(A, b, verbosity=0, eps=0.0)       # 15 -> 16, 4 qubits
k = resolve_sqls_k(None, 16, 'full_svd')                    # 8 (ignored by full_svd)
quantum_solve(csr_matrix(A2), b2, 4, AerSimulator(method='statevector'),
              psi_norm=b2, mode='statevector', k=k, method='full_svd',
              state_prep='initialize', shots=int(1e6), repeats=1,
              sqls_out=out, timings=tm, count_cx=False, gpu=False)
qc = out['qc']    # raw ops {'unitary': 2, 'initialize': 1} on 4 qubits
```

HHL circuit built as `QuantumHHL.solve_one_step` does (lines 620-653):
`scale_Ab_by_spectral_radius` -> `convert_to_pow2` (eps 1e-8) ->
`convert_system_to_herm` (16 -> 32 for nelem 5, 8 -> 16 for nelem 2) ->
`QuantumHHL(...).generate_circuit(A_herm, b_herm, nelem, step=0)`
(raw ops `{'measure': n, 'circuit-46': 1, 'QPE': 1, 'ExactReciprocal': 1,
'QPE_dg': 1, 'barrier': 1}`; 14 qubits at nelem 5, 12 at nelem 2).

### A1. SQLS, nelem 5, archived iteration 0

| quantity | mine | solver CSV (`sqls_n5_sv/qc_metadata_sqls_nelem5_full_svd.csv`) | expected |
|---|---|---|---|
| fb_cx_count | 200 | 200 | 200-201 |
| fb_depth | 400 | 400 | 400-401 |
| fb_total_gates | 574 (u3 370, cx 200, reset 4) | 574 | 572-577 |
| circ_qubits | 4 | 4 | |
| count wall | 0.568 s | t_count_s 0.502 s | |
| sqls level-1 {u3,cx} (continuity) | cx 200, depth 398, total 540 | cx_count -1, circuit_depth -1 (only logged at `-v 2`) | August CSV: 200 / 398 |

The August archive
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/qc_metadata_sqls_nelem5_full_svd_shots150000.csv`
has `cx_count` 200 / `circuit_depth` 398 at step 0 (200-201 / 397-398 over
steps 0-6); my level-1 recount of the same circuit gives exactly 200 / 398, and
level 0 gives the same CX with depth 400 and 34 more u3 (574 vs 540 ops).
Statevector fidelity of the sqls reconstruction vs `numpy.linalg.solve`:
0.9999999999999999.

Conclusion A1: reproduced. All three fixed-basis numbers match the solver's
CSV exactly and sit in the expected ranges; the level-0 vs level-1 difference
is 0 CX, +2 depth, +34 u3.

### A2. HHL, nelem 2, archived iteration 0

| quantity | mine (in-process, archived system) | solver CSV (`hhl_n2_sv/qc_metadata_nelem2_statevector.csv`) | expected |
|---|---|---|---|
| fb_cx_count | 234,899 | 234,899 | ~234,899 |
| fb_depth | 470,394 | 470,394 | ~470,394 |
| fb_total_gates | 630,388 (u3 395,485, cx 234,899, reset 4) | 630,388 | ~630,388 |
| circ_qubits | 12 | 12 | |
| count wall | 1.63 s | t_count_s 1.14 s | |
| Aer-basis depth / gates (`transpile(circ, AerSimulator)`) | 68,963 / 74,797 (unmeasured) ; 68,964 / 74,750 (measured) | 68,963 / 74,811 | |

The CLI run's system (fresh nelem-2 iteration 0) and the archived pickle are
the same system (identical condition number 38.30616160119951 in both CSVs),
so the in-process and CLI circuits are the same circuit.

Conclusion A2: reproduced exactly for the fixed-basis columns. The Aer-basis
gate total differs by 14 to 61 ops between calls (see A4) while the Aer-basis
depth differs by at most 1 (the measurement layer).

### A3. HHL, nelem 5, archived iteration 0 (the one permitted solve)

My count on the generated circuit, then the solver's own `solve_one_step` on
the same system (fresh generation; the `load_circ=True` shortcut failed, see
side findings):

| quantity | mine | solver CSV (`inproc_hhl5_solve/qc_metadata_nelem5_statevector.csv`) | expected |
|---|---|---|---|
| fb_cx_count | 2,054,602 | 2,054,602 | ~2,054,602 |
| fb_depth | 4,067,708 | 4,067,708 | ~4,067,708 |
| fb_total_gates | 5,455,676 (u3 3,401,069, cx 2,054,602, reset 5) | 5,455,676 | ~5,455,676 |
| circ_qubits | 14 | 14 | |
| count wall | 10.55 s | t_count_s 9.64 s | ~9 s |
| solve wall | | 100.52 s total: generate 21.52 s, Aer transpile 14.96 s, statevector run 52.69 s, count 9.64 s | ~95 s |

Ratios at nelem 5, HHL / SQLS, same archived system, same counter:
fb_cx_count 2,054,602 / 200 = 10,273x; fb_depth 4,067,708 / 400 = 10,169x;
fb_total_gates 5,455,676 / 574 = 9,505x.

Conclusion A3: reproduced exactly; the counting transpile took 10.55 s (mine)
and 9.64 s (solver). The statevector run was 52.7 s here versus 18.5 s in the
August CSV, so the whole solve was 100.5 s rather than ~95 s; the circuit
numbers are unaffected.

### A4. Aer-basis numbers for the same circuits and why {u3,cx} is 3 to 7x larger

`transpile(circ, AerSimulator(method='statevector'))` -- the solver's ideal
path, `quantum_tools.py` line 524, default optimization level, no seed:

| circuit | Aer depth / gates, mine | solver today | August archive |
|---|---|---|---|
| HHL nelem 5 iter 0 | 596,687 / 641,114 (14.59 s) | 596,687 / 641,063 | 596,688 / 641,145 (qiskit25-local); 638,237 / 649,089 (qiskit23-local) |
| HHL nelem 2 iter 0 | 68,963 / 74,797; repeat call 68,963 / 74,779; measured 68,964 / 74,750 and 74,812 | 68,963 / 74,811 | |

Aer-basis op mix of the nelem-5 circuit (mine): ccx 215,986; cu 195,140;
crz 140,388; u3 47,432; u1 21,588; crx 5,943; rzx 4,240; rzz 3,423;
cry 2,939; cp 2,338; u2 963; rxx 386; ry 128; cx 128; ryy 61; h 23; p 7;
initialize 1 -- 570,972 multi-qubit gates, of which only 128 are CX.

Basis dependence at nelem 5 (my numbers): fb_cx_count / Aer gates =
2,054,602 / 641,114 = 3.20x; fb_depth / Aer depth = 4,067,708 / 596,687 =
6.82x; fb_total_gates / Aer gates = 8.51x. At nelem 2: 3.14x, 6.82x, 8.43x.

Why: Aer's target basis is the simulator's native instruction set, which
includes three-qubit `ccx`, parameterised controlled rotations (`cu`, `crz`,
`crx`, `cry`, `cp`) and two-qubit Pauli rotations (`rzz`, `rxx`, `ryy`,
`rzx`), plus `initialize`, so the preset pass manager leaves each of those as
one instruction and the Aer-basis count treats a Toffoli and a CX as one gate
each. In a {u3, cx} basis the same circuit must be expressed in hardware
primitives: each `ccx` becomes 6 CX plus single-qubit gates, each controlled
single-qubit rotation and each two-qubit Pauli rotation becomes 2 CX, and the
single-qubit gates in between are rewritten as u3. Applying those textbook
counts to the Aer-basis op mix above gives a floor of 2,005,760 CX; the
measured 2,054,602 is 1.024x that (the gap is the Aer path's level-2
cancellations, which the level-0 fixed-basis count deliberately does not
apply, and the `Initialize` expansion). Depth grows by a similar factor
because every expanded multi-qubit gate adds several CX layers. The 3x (CX),
7x (depth) and 8.5x (all ops) factors are therefore a change of unit, not of
circuit; comparing an HHL Aer-basis count with an SQLS {u3,cx} count, as the
August CSVs did, mixes units. A second reason the Aer-basis figure is a poor
cross-solver yardstick showed up directly: transpiling the identical nelem-2
circuit twice gave 74,797 then 74,779 ops (and 74,750 then 74,812 for the
measured copy), i.e. the default-level Aer transpile is not deterministic at
the ~0.1 % level in gate count (depth was stable), whereas the level-0,
seeded {u3,cx} count was identical on every call and across the in-process and
CLI paths.

Conclusion A4: Aer-basis numbers reproduced to within 0.01 % (depth 596,687 vs
596,688; gates 641,114 vs 641,145 in August, 641,063 today), with the residual
explained by measurement ops and non-deterministic default-level optimization.
The 3 to 7x (to 8.5x for total ops) basis factor is confirmed and is a
decomposition effect of ccx / controlled-rotation gates native to Aer.

## B. Effective shots

Run `sqls_n2_s5000_r2` (`-shots 5000 -sqls_repeats 2`):

| source | nshots | repeats | effective_shots |
|---|---|---|---|
| `qc_metadata_sqls_nelem2_full_svd_shots5000.csv` row 0 | 5000 (file name) | 2 | 10000 |
| `metadata_nelem2_SQLS_statevector_nshots5000.pkl` | 5000 | 2 (`quantum_circuit.repeats`) | 10000 |

Code: `QuantumSQLS.solve_one_step` passes `self.nshots * self.repeats if
self.nshots else 0` to `fairness_columns` (lines 1012-1016);
`nozzle_1d_solver.py` line 441 writes `linsolv_args['shots'] * args.sqls_repeats`
to the pickle. Both give 5000 x 2 = 10000. Statevector runs record 0
(`sqls_n5_sv`, `hhl_n2_sv`: `effective_shots` 0 in CSV and pickle).

Matched case: the August archive
`.../2026-08-17-sqls-local-v2/trial_0/qc_metadata_sqls_nelem5_full_svd_shots150000.csv`
has NO `effective_shots` column (header ends at `solve_time`) and the August
pickle `metadata_nelem5_SQLS_statevector_nshots150000.pkl` has no
`effective_shots` key; it has `nshots` 150000 and `quantum_circuit.repeats` 1,
and the CSV `repeats` column is 1 on all 7 rows, so the arithmetic is
150000 x 1 = 150000 effective shots per linear solve. I produced no
150000-shot row (not in the run budget).

Conclusion B: reproduced. `effective_shots` = 10000 in both the CSV and the
pickle for 5000 x 2; the August matched case is 150000 x 1 = 150000 by
reconstruction from `nshots` and `repeats`, since the column did not exist in
August.

## C. Reference-free sign

`math_tools.choose_global_sign(A, b, x)` (lines 50-59): keep x if
`||A x - b|| <= ||A x + b||`, else return -x; one matvec, two norms, no
classical solution. `time_solvers.sqls_solve` applies it to the
magnitude-exact SQLS vector (line 679); `hhl_solve` applies it only under
`-hhl_scale true_sol` after scaling by `||dq_herm||` (line 567).

```python
x = np.linalg.solve(A, b); ax = A @ x
r_plus, r_minus = np.linalg.norm(ax - b), np.linalg.norm(ax + b)
```

| system | ||b|| | r_plus = ||Ax - b|| | r_minus = ||-Ax - b|| | r_minus / r_plus | (Ax).b |
|---|---|---|---|---|---|
| nelem5_iter0 | 1.237537e1 | 1.075e-14 | 2.475074e1 (= 2||b||) | 2.3e15 | 1.531e2 |
| nelem5_iter6 | 1.260379e-9 | 2.384e-25 | 2.520758e-9 (= 2||b||) | 1.1e16 | 1.589e-18 |
| nelem2_iter0 | 1.314105e0 | 5.875e-16 | 2.628210e0 (= 2||b||) | 4.5e15 | 1.727e0 |

r_plus is round-off; r_minus is 2||b||. The rule is unambiguous on all three
real systems, including the nearly converged iteration 6 where ||b|| is 1e-9.

When is it a tie: `||Ax - b||^2 - ||Ax + b||^2 = -4 (Ax).b`, so the two
residuals are equal iff `x^T A^T b = 0`: x = 0, b = 0, or Ax orthogonal to b.
For the exact solution direction Ax is parallel to b, so (Ax).b = ||Ax|| ||b||
> 0 and no tie is possible unless b = 0. Constructed ties, verified with
numpy: A = I, b = e1, x = e2 gives ||x - b|| = ||-x - b|| = 1.41421356;
b = 0, x = (1,1,1) gives 1.7320508 both ways. The code breaks a tie with the
`<=` comparison, i.e. it keeps +x. In the b = 0 case the SQLS path never
reaches the rule: `QuantumSQLS.solve_one_step` returns the zero vector before
building a circuit (`if not np.any(b_o): return np.zeros(nsys)`), so the rule
sees x = 0 and keeps +0.

One caveat I checked because it is the only way the margin can get thin: the
margin is 4 (Ax).b, which for a unit-norm direction u is 4 (Au).b, not
4 ||b||^2. On the iteration-6 system with u = x / ||x||, ||Au - b|| =
17.138811816592721 and ||A(-u) - b|| = 17.138811819113478, a difference of
2.52e-9 (1.5e-10 relative), still resolvable in double precision but small.
The code never does this: both callers apply the rule after the magnitude has
been fixed (SQLS: ||final_b|| inside `quantum_solve`; HHL true_sol:
||dq_herm||), where the margin is 4 ||b||^2 against r_plus ~ 0.

Conclusion C: reproduced. r_plus is at round-off (1e-14 to 1e-25) against
r_minus = 2||b|| on both archived nelem-5 systems; a tie needs x^T A^T b = 0
(b = 0, x = 0 or Ax perpendicular to b), which cannot happen for a correct
solution direction with b != 0; the `<=` keeps +x on a tie.

## D. Seeds

Two runs with `-seed 7` and two without (`-nelem 2 -linsolver SQLS -shots
10000 -sqls_repeats 1 -iters 2`), compared with `cmp` and sha256:

| file | seed7_a vs seed7_b | noseed_a vs noseed_b |
|---|---|---|
| `dq_nelem2_iter0_statevector_shots10000.csv` | identical (sha256 68d7e37d...87aa4 both) | differ at byte 42 (471c2e56... vs 86e7fea7...) |
| `dq_nelem2_iter1_statevector_shots10000.csv` | identical (sha256 20c846d0...f7ed both) | differ at byte 17 (0998f348... vs dd4c6e5a...) |

Fidelity(true_sol, sqls_sol) from `hhl_metrics_nelem2_statevector_shots10000.csv`
(same values printed in the run logs):

| run | iter 0 | iter 1 | seed column in qc_metadata |
|---|---|---|---|
| seed7_a | 0.9999780104544436 | 0.9998980289752558 | 7 |
| seed7_b | 0.9999780104544436 | 0.9998980289752558 | 7 |
| noseed_a | 0.9998683480066702 | 0.9999178539551274 | (empty) |
| noseed_b | 0.9998142406950390 | 0.9999469320785047 | (empty) |

The seeded pair also agrees to every digit in l2_error and linsys_residual
(0.012106506079040742 at iter 0). The metadata pickles record `seed` 7 /
None and `effective_shots` 10000 in all four runs. Path: `QuantumSQLS`
passes `seed=self.seed` to the patched `quantum_solve`, which hands it to
`simulator.run(..., seed_simulator=seed)`.

Conclusion D: reproduced. Seeded runs are byte-identical across both
iterations; unseeded runs differ in both, with fidelities 0.99981 to 0.99998
for 10000 shots.

## Side findings (outside the item-11 claims)

1. `-loadcirc` for HHL is broken under qiskit 2.5.2: reloading the saved
   `circuit_generated_statevector_nelem5_iter0.qpy` raises
   `TypeError: ExactReciprocalGate.__init__() missing 2 required positional
   arguments: 'num_state_qubits' and 'scaling'` at `quantum_tools.py` line 394
   (`qpy.load`). My first nelem-5 attempt used that path and failed after
   49.26 s without solving; the counts above come from the fresh-generation
   path. Pre-existing, not introduced by item 11.
2. The Aer-basis `circ_gates_transpile` is not deterministic call to call
   (nelem 2: 74,797 / 74,779 / 74,750 / 74,812 on the identical circuit),
   because the ideal path calls `transpile(circ, backend)` with no
   `seed_transpiler`; depth is stable. This supports keeping the seeded
   level-0 fixed-basis count as the comparable figure.
3. The legacy SQLS `cx_count` / `circuit_depth` columns are -1 unless `-v 2`
   (`count_cx = (self.verbosity == 2)`), so a default-verbosity CSV carries
   only the fb_* counts.
4. The fb_* numbers depend on the uncommitted local patch to
   `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`
   (`sqls_out['qc']`); without it `solve_one_step` raises unless
   `-circ_metrics none`.

## Overall

All four claims reproduced with my own code: A (200 / 400 / 574 SQLS;
234,899 / 470,394 / 630,388 HHL nelem 2; 2,054,602 / 4,067,708 / 5,455,676
HHL nelem 5, every figure identical to the solver's CSV; HHL/SQLS CX ratio
10,273x at nelem 5; Aer-basis 596,687 / 641,114 vs August 596,688 / 641,145),
B (effective_shots 10000 = 5000 x 2 in CSV and pickle; August 150000 x 1 by
reconstruction, column absent), C (r_plus round-off vs r_minus = 2||b||, tie
iff x^T A^T b = 0, `<=` keeps +x), D (seeded dq CSVs byte-identical, unseeded
differ). No discrepancies in the claimed quantities; the only deviation from
the stated expectations was wall time (HHL nelem-5 solve 100.5 s vs ~95 s,
dominated by a 52.7 s statevector run).
