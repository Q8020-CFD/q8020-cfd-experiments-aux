# April 2026 fvm CFL sweep: AWS reruns vs the Frontier original

Case: fvm_euler_1d_solver nozzle, nelem 5, BDF1, HHL on the Aer statevector
simulator, 150k shots, 15 outer / 1 inner Newton iterations, CFL in
{1, 5, 10, 25, 1e10}, 10 trials per CFL (the `time_steps` group of
`results/fvm_euler_1d_solver/2026-04-05/_52d087d1`).

| Set | Where | Code | Stack |
|---|---|---|---|
| april | Frontier, 1 core per case | fvm 9e76e398 (reconstructed) | qiskit 2.3.1, aer 0.17.2, HHL Q8020-CFD@66eadf0 |
| old | AWS Batch Fargate, 1 vCPU | fvm 9e76e398 | identical packages, Python 3.12.9 |
| new | AWS Batch Fargate, 1 vCPU | fvm 38a41e52 | qiskit 2.6.1, aer 0.18.2, HHL @99231b8, latest everything |

Full package lists: `../{old,new}/apr05/*/<job>/fvm-*_STACK_FREEZE.txt`.

Reproduce: `python collect.py` (writes `cases.csv`), `python summarize.py`,
`python plot.py` (needs numpy/scipy/matplotlib; any fvm venv works). The
reference solutions in `lu_ref/` are classical LU runs of the same solver
(fvm-old) at each CFL: `iters15_*` with the same 15-iteration budget,
`converged_*` run to convergence.

## Results

All 150 cases ran to completion.

**old reproduces april.** Final residual, final-solution error, mean HHL
fidelity and mean HHL L2 error are statistically indistinguishable at every
CFL (Mann-Whitney U, p >= 0.05 everywhere; CFL 25 is p = 0.05 with old the
better of the two). The iter-0 transpiled circuits take the same two gate
counts as April at every CFL (e.g. 649,089 / 604,520 at CFL 1e10): the
transpile is unseeded and bimodal, and old lands on April's two modes.

**new converges far better at CFL >= 5**, and this is a solver fix, not the
qiskit or HHL update. With shots the circuit gives only |x_i|, so both
versions take the component signs from the classical Hermitian LU solution and
fit the magnitude by least squares, alpha = <b, Ax>/<Ax, Ax>. The old code fits
alpha to |x| and overwrites the signs afterwards, which leaves a wrong scale and
an error floor; the new code (38a41e52, "Restore HHL shot signs before the
magnitude fit") restores the signs first. The Newton iteration then converges
linearly, as an inexact Newton with bounded relative error should:

| CFL | final residual, april / old / new (median) | LU, 15 iters | final rel. L2 vs steady, april / old / new |
|---|---|---|---|
| 1 | 0.51 / 0.51 / 0.51 | 0.51 | 2.4e-2 / 2.4e-2 / 2.4e-2 |
| 5 | 3.5e-3 / 3.8e-3 / 1.7e-4 | 1.5e-5 | 1.8e-4 / 1.8e-4 / 5.3e-6 |
| 10 | 7.9e-4 / 3.7e-4 / 5.9e-7 | 3.0e-8 | 3.6e-5 / 1.7e-5 / 5.1e-9 |
| 25 | 2.4e-2 / 2.1e-3 / 6.4e-10 | 3.8e-10 | 9.3e-4 / 1.2e-4 / 1.9e-11 |
| 1e10 | 3.4e-3 / 9.5e-3 / 8.7e-10 | 2.0e-13 | 5.7e-5 / 2.4e-4 / 1.2e-11 |

new met the convergence tolerance in 18 of 20 trials at CFL 25 and 1e10
(iteration 12 to 15); no april or old case converged. CFL 1 is
pseudo-time-step limited: LU itself is at 0.51 after 15 iterations, and all
three sets match it.

Isolating the fix (`replay_sign_order.py`): replaying both post-processing
orders on the 750 linear systems the old-stack runs saved, with the same
simulated 150k-shot readout for each, reproduces the measured runs. The old
order's Newton-update error climbs from 0.05 at step 0 to 0.80 by step 14; the
new order's stays at 0.04 to 0.05. Measured runs (hhl_metrics l2_error_rel, CFL
1e10): old 0.06 -> 0.83, new 0.06 -> 0.12. Step 0 is unaffected because every
component of its update has the same sign; the old order only goes wrong once
the update has mixed signs (from step 2 on, 7% to 73% negative components),
because the fit then scales the unsigned vector, whose A-image is not A x. With
zero circuit error the old order still reaches 0.82, so the stall is entirely
post-processing. The commit's other change (pad b with 0, not 1e-8) only
matters when ||b|| nears 1e-8, which old never reached.

Caveats on new:
- The signs still come from the classical LU solution (work-plan item 17,
  open), so new's convergence leans on classical information.
- The quantum solve itself is unchanged. On identical inputs (Newton steps 0
  to 2) HHL fidelity is the same in all three sets (e.g. CFL 1e10 step 0:
  0.9987 / 0.9984 / 0.9982, p >= 0.10). new's lower mean fidelity at CFL 1e10
  (0.949 vs april 0.994) comes from its later steps, which solve the nearly
  converged systems april and old never reach; the metric definition is the
  same in both codes.
- Iter-0 circuits are about 1% smaller (641,654 vs 649,089 gates at CFL 1e10)
  and identical across trials.

## Timing

| Set | wall clock | case-hours | of which transpile | median case, CFL 1-25 / 1e10 |
|---|---|---|---|---|
| april | 0.7 h (50 cases at once) | 19.1 | 0.9 h | 19 / 38 min |
| old | 4.2 h (8 at once) | 28.0 | 2.1 h | 29 / 53 min |
| new | 13.5 h (8 at once) | 92.2 | 69.0 h | 100 / 162 min |

- old vs april: about 1.5x slower per case, across circuit generation,
  transpile and simulation alike; a Fargate vCPU is slower than a Frontier core.
- new vs old: about 3.4x slower per case, almost all of it transpile (~300 s per
  solve vs ~8 s). Generation and simulation times are about the same. The new
  solver also runs a second, fixed-basis {u3, cx} transpile for circuit metrics
  (`-circ_metrics u3cx`, ~17 s per solve).
- The slowdown is qiskit 2.6's transpiler. Both solvers make the same call,
  `transpile(circ, AerSimulator(method='statevector'))` (default optimization
  level, unseeded). One CFL 1e10 iteration-0 solve on the laptop, swapping one
  library at a time on fvm 9e76e398, pinned to one core:

  | variant | transpile |
  |---|---|
  | old stack (qiskit 2.3.1, aer 0.17.2, HHL 66eadf0) | 20 s |
  | qiskit 2.6.1 | 457 s |
  | + aer 0.18.2 | 460 s |
  | + HHL 99231b8 | 602 s |
  | new stack (fvm 38a41e52) | 589 s |

  Per-pass profile (callback on that transpile call): qiskit 2.6 spends
  ~430 s of it in `TwoQubitPeepholeOptimization`, a pass the 2.3 run does not
  use (2.3's whole transpile is ~17 s, mostly ConsolidateBlocks). It buys a ~6%
  shallower circuit (597k vs 638k depth).
- Threads: qiskit 2.3 is effectively single-threaded here (CPU/wall 0.98 even
  with 12 cores free, 16.5 s). qiskit 2.6's peephole pass is parallel: with 12
  cores it ran 114 s wall on 1,248 CPU-s (CPU/wall 11). On AWS each case is its
  own 1-vCPU Fargate task, so cases never competed for cores; each new case just
  ran the pass serially. Packing several new-stack cases onto one multi-core
  machine (e.g. a Frontier node) would make them contend.
