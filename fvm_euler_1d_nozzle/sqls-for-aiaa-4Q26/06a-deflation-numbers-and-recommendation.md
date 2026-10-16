# Item 6 follow-up: what SVD deflation would buy HHL on the real nozzle Jacobians

Written 2026-10-15 (UTC). Post-processing only, on Jacobians already archived
in `results/fvm_euler_1d_solver/` (no solver run). Script and full output in
this folder: `kappa_eff_deflation_check.py`, `kappa_eff_deflation_output.txt`.
Run with the fvm venv python.

## Position

Using `sqls` as-is is not interesting as a quantum solver and should not be
presented as one. `full_svd` computes the SVD classically, loads
Sigma^-1 U^T b classically, and the circuit only applies V. `truncated_mps`
still needs the k smallest singular triplets, obtained by shift-invert Lanczos
on a sparse LU of A, which is a classical solve in disguise. What SQLS does
show is cheap quantum readout of a classically known answer (4 qubits, ~200 CX
at N = 16). As a row in the paper it has to be labeled that way (work item 11).

The interesting object is the hybrid: use SVD information to PREPARE the
system, then let the existing HHL path in `fvm_euler_1d_solver` solve it,
inside the Newton loop as it runs today. This matches the direction of
`06-svd-priming-hhl.md` (its option 2). Two refinements below change how it
should be implemented and what should be claimed.

## Refinement 1: deflate by shifting the matrix, not by projecting b

`06-svd-priming-hhl.md` proposes HHL(A, b') with b' = (I - U_k U_k^T) b. That
leaves the small singular values inside A; the library then has to be told
the reduced kappa and lambda_min by hand (its first "point to check"), and any
QPE leakage or state-prep error re-excites modes whose reciprocal rotation is
mis-sized. Safer and simpler:

    A' = A + sum_{i<=k} (sigma_shift - sigma_i) u_i v_i^T,   sigma_shift = sigma_max
    solve A' y = b with the UNCHANGED HHL path (pad, Hermitian-double, scale)
    x = y + sum_{i<=k} (u_i . b) (1/sigma_i - 1/sigma_shift) v_i

A' is nonsingular with kappa(A') = sigma_max / sigma_{k+1} exactly, so the
library's own `condition_bounds()` sizes the clock register correctly with no
override, and the Hermitian doubling of A' has no eigenvalue below
sigma_{k+1} in magnitude for leakage to land on. The identity above was
checked numerically on every archived Jacobian: relative error 1e-15 to 1e-16
(column `identity` in the output). Implementation is a pre-step and a
post-step around `hhl_solve`; nothing inside `QuantumHHL` changes. The fvm
Jacobian is handled dense already, so the rank-k update costs nothing here.

## Refinement 2: measure how much of the answer went classical

Deflation moves the k worst-conditioned modes to a classical rank-k solve.
The honest metric is the share of ||x||^2 those modes carry (`x-share`), not
the share of ||b||^2, because 1/sigma weighting makes a 0.1 % slice of b into
a large slice of x. The paper must report it next to any HHL saving.

## Numbers (nelem 5, N = 15, padded and doubled N_h = 32, n_b = 5)

Clock width n_l = max(n_b + 1, ceil(log2(kappa + 1))) + 1 as in
`linear_solvers/hhl.py`. P_succ = HHL post-selection probability proxy with
reciprocal constant C = lambda_min; `shots x` = P_succ(k) / P_succ(0) is the
factor by which the shot budget drops for the same post-selected statistics.

Spectrum at CFL 1e10, iteration 14 (singular values, ascending):
0.861, 1.65, 3.88, 4.24, 7.39, 8.21, 13.5, 15.4, 18.4, 20.2, 27.3, 28.8, 39.6,
51.2, 58.2. A smooth ladder in near-pairs, no isolated gap: deflation is a
dial, not a switch.

### CFL 1e10 (the paper's steady case), iteration 14, kappa = 67.6

| k | kappa_eff | n_l | P_succ | shots x | x-share classical |
|---|-----------|-----|--------|---------|-------------------|
| 0 | 67.6 | 8 | 0.0055 | 1.0 | 0 % |
| 1 | 35.2 | 7 | 0.0157 | 2.9 | 23 % |
| 2 | 15.0 | 7 | 0.0722 | 13.1 | 35 % |
| 3 | 13.7 | 7 | 0.0531 | 9.7 | 60 % |
| 4 | 7.9 | 7 | 0.1113 | 20.2 | 73 % |

(x-share rounded from the output file's 0.225 / 0.352 / 0.602 / 0.727; the
k = 3 and k = 4 cells first read 59 % and 72 %, corrected 2026-10-15 in the
item-6 fix-up round.) Iterations 3 and 7 are within a few percent of these.
The August HHL and SQLS trials (same case, laptop) give the same table to
three digits.

### CFL 1e10, iteration 0, kappa = 96.0 (first Newton step)

| k | kappa_eff | n_l | shots x | x-share classical |
|---|-----------|-----|---------|-------------------|
| 0 | 96.0 | 8 | 1.0 | 0 % |
| 1 | 43.3 | 7 | 0.4 | 91 % |
| 2 | 16.3 | 7 | 2.7 | 92 % |
| 4 | 7.9 | 7 | 6.5 | 96 % |

The first update is almost entirely the two slowest modes; deflating them
leaves HHL a small correction. Expected: the initial uniform-flow guess is
far from the steady solution along exactly those modes.

### CFL 1, iteration 14, kappa = 7.2

| k | kappa_eff | n_l | shots x | x-share classical |
|---|-----------|-----|---------|-------------------|
| 0 | 7.2 | 7 | 1.0 | 0 % |
| 2 | 5.5 | 7 | 0.6 | 67 % |
| 4 | 3.9 | 7 | 0.4 | 90 % |

Nothing to gain: kappa is already small, deflation removes the bulk of the
solution and the shot budget gets worse. Same at CFL 5 and 10 (gains 0.4x to
2.7x, mostly below 1.5x).

## Reading

- The payoff is where the paper's problem is: the steady CFL 1e10 case, where
  Table 4 reports 10 % mean error with a 3.6 to 24.1 % trial range and 37 min
  per run. With k = 2, kappa falls 68 -> 15, the clock register loses one
  qubit (8 -> 7, halving the standard-QPE blowup and cutting LuGo's O(k) by
  one eighth), and the post-selected shot budget drops about 13x while 65 % of
  the solution energy still comes from the quantum solve. k = 2 is the
  sensible default to test; k = 4 buys 20x shots but hands 73 % of the answer
  to the classical side.
- At small CFL (unsteady or dual-time-stepping regimes the paper's conclusion
  points to) deflation is unnecessary and counterproductive.
- The clock-register saving is capped at one qubit at nelem 5 by the
  n_b + 1 floor; at nelem 85 (n_b = 9, floor 10) kappa would have to exceed
  ~1000 before kappa sizes the register at all. So the durable benefit of
  deflation is shots and accuracy, not circuit width. The paper's existing
  figures (kappa per iteration, fidelity vs shots, circuit cost per iteration)
  are exactly the axes on which to show it.
- Fairness accounting: the k smallest triplets of a 15 x 15 (or 255 x 255)
  Jacobian cost a classical SVD or a shift-invert Lanczos, which at this scale
  is a full solve. State it plainly: this is resource reduction for the
  quantum kernel given a classical rank-k preconditioner, with no speedup
  claim. Reusing the deflation space across Newton iterations (the Jacobian
  and its spectrum are stable after iteration ~3, see the tables and Fig. 13
  of the abstract) is the route to amortizing that cost, and is future work.
- The MPS state-prep idea (option 1 in `06-svd-priming-hhl.md`) is the
  smallest change but also the smallest payoff: at N_h = 32 loading b is ~30
  CX against a ~600k-gate QPE, and it is lossy. Defer it.

## Proposed work (not started)

1. `-hhl_deflate_k K` on the HHL path: shifted deflation pre-step, classical
   correction post-step, no change inside `QuantumHHL` (same flag name as in
   `06-svd-priming-hhl.md`, different mechanics). Record kappa, kappa_eff,
   n_l, k, x-share, and the classical SVD time in `qc_metadata`.
2. Classical dry check first (this script extended): per-iteration
   kappa_eff(k), x-share(k), P_succ(k) for all archived CFL trials, as a
   figure.
3. Runs, when approved: CFL 1e10, nelem 5, 150k shots, k in {0, 2, 4}, 10
   trials; compare fidelity, L2 error and residual history against the k = 0
   baseline and LU. Estimated cost per k: same as the HHL baseline (~1125 to
   1653 s per trial on Frontier) since the circuit is at most one clock qubit
   smaller.
4. Paper framing: a "hybrid SVD-deflated HHL" row, labeled classical
   deflation plus HHL on the remainder, with x-share reported.
