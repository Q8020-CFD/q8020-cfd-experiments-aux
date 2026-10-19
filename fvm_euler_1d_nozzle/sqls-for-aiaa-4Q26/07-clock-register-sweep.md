# Clock-register sweep: does HHL eigenvalue precision change outer convergence?

Written 2026-10-18 (UTC) for work item 20 of `WORKPLAN.md` in this folder.
Design only, from an interactive session with Andy. Code was read, not run or
changed. No solver output was generated.

Summary. Lapworth (arXiv 2209.07964, bus ref-20260809-0020) showed that the
number of HHL clock qubits changes how many outer CFD iterations are needed.
We can repeat that on the compressible nozzle, but not with today's code.
There is no flag that sets the clock register. The library sizes it itself,
and at CFL 1e10 the default is already the smallest that works. The plan is
a small `-hhl_clock N` override, then a statevector sweep at two CFL values.
The sweep is over the sweep fence and needs Andy's go-ahead.

## Why this belongs in the paper

- Lapworth 2022 (2209.07964), implicit coupled incompressible solver, 9x9
  mesh: the full eigenvalue register matches the classical solver. One fewer
  fraction qubit costs 2 extra outer iterations. Two fewer costs about 5x
  more iterations. His explanation is a feed-forward: eigenvalue error in one
  iteration re-enters the next. Unresolved small eigenvalues under-correct
  the smooth error modes. Unresolved large eigenvalues let grid-scale
  oscillations grow.
- Goldfriend, Lapworth et al. 2026 (2606.01067, bus ref-20260809-0038),
  incompressible 1D nozzle: the outer loop tolerates an inexact solve if the
  high-frequency (large-eigenvalue) part is accurate. Errors there flip sign
  each iteration and stall convergence.
- Our abstract: noise-free HHL needs about 8 iterations where LU needs 3, at
  n_t ~ 8 (Table 2). We do not yet say why. A clock sweep, plus the
  error-spectrum analysis of the archived updates, would answer it.
- It is a direct test of a published claim on a different flow class
  (compressible Euler, BDF Newton), which is the kind of extension a reviewer
  credits.

## How the clock register is sized today

Fork `Q8020-CFD/quantum_linear_solvers`, branch `feature/sqls-aiaa-4q26`,
`linear_solvers/hhl.py`, `HHL.construct_circuit`:

    n_t = max(n_b + 1, ceil(log2(kappa + 1))) + neg_vals

- n_b is the state register: 5 qubits at nelem 5 (N_h = 32 after padding
  and Hermitian doubling).
- neg_vals = 1 is the sign qubit, so the magnitude bits are m = n_t - 1.
- kappa is the library's own full SVD of the encoded matrix (`internal`), or
  the value passed in by `-hhl_spectrum deflation` (item 19, uncommitted in
  the fork and fvm working trees as of this writing).

`fvm_euler_1d_solver/nozzle_1d_solver.py` has no flag that sets n_t. The only
indirect lever is `-hhl_deflate_k`, which lowers kappa and can drop n_t by one
(item 6: 8 -> 7 at k = 2).

## Catch 1: the default is already the minimum at high CFL

`HHL._get_delta` scales the spectrum so that lambda_min lands on a whole
clock tick:

    lambda_min_tilde = (2^m - 1) / kappa,  delta = int(lambda_min_tilde) as a binary fraction

If (2^m - 1) / kappa < 1, the integer part is 0, delta is 0, and the
evolution time is 0. The solve is broken, not just less accurate. So the
smallest usable m is the smallest m with 2^m - 1 >= kappa.

| Case | kappa (iter 0 / iter 14) | default n_t | smallest usable n_t | Room below default |
|------|--------------------------|-------------|---------------------|--------------------|
| CFL 1e10 | 96.0 / 67.2 | 8 | 8 (m = 7: 127 / 96 = 1.32; m = 6: 63 / 68 < 1) | none |
| CFL 1 | 7.1 / 7.2 | 7 (set by the n_b + 1 floor) | 5 (m = 4: 15 / 7.2 = 2.1; m = 3: 7 / 7.2 < 1) | 2 qubits |

kappa values are from Table 3 of the abstract. At CFL 1e10 the sweep can
only go up. Going below the default there would need a different scaling
rule in the library, which changes the method and is out of scope.

## Catch 2: our sweep probes the large-eigenvalue end

Because lambda_min is always pinned to a tick, removing bits mostly coarsens
the large eigenvalues (grid-scale modes): the tick spacing is lambda_max /
2^m. That is Lapworth's second failure mode and the one the 2026 Classiq
paper says matters. His sweep in 2209.07964 cut fraction bits, which mainly
hits the lambda_min end. The paper must say which end ours tests.

## Code change needed

1. Fork: optional `num_clock_qubits` argument on `HHL.construct_circuit`
   that replaces the computed n_t.
   - Validate it: if (2^(n_t - 1) - 1) / kappa < 1, raise a ValueError that
     names the minimum, instead of letting delta round to 0.
   - Record the value and its source (`computed` or `supplied`) in
     `spectral_info`.
   - Test: supplying the computed value gives the identical circuit (same
     gate for gate as the 1e-10 fixture of item 15).
2. fvm: `-hhl_clock N` flag, HHL only, default automatic, passed through to
   the library. The `n_clock` metadata column already exists; add the
   source next to it.
3. Smoke test: at nelem 2 (tiny circuit), the default and an explicit equal
   value give the same solution; one value below the minimum fails fast with
   a clear message.

About 30 lines plus tests. It sits on the item 19 changes, so it goes on the
same `feature/sqls-aiaa-4q26` branch in both repos after item 19 lands.

## Sweep design

- Statevector (`-shots 0`), one trial per point, so shot noise does not mix
  with clock precision. Shots can be added later at one n_t if the
  statevector result is interesting.
- nelem 5, BDF1, `-localdt`, `-initers 1`, standard construction (no LuGo).
- Raise the iteration cap from 15 to 40, so a slow case is counted rather
  than cut off.
- Metric: outer iterations to the 1e-10 residual drop, plus the residual
  history, final L2 error against LU, and per-iteration fidelity.

| Group | CFL | n_t values | Purpose |
|-------|-----|------------|---------|
| low-kappa | 1 | 5, 6, 7 (default), 8, 9 | The only place "fewer qubits, more iterations" can be measured |
| high-kappa | 1e10 | 8 (default), 9, 10, 11 | Does extra precision buy fewer iterations, as for Lapworth? |

Command shape once the flag exists (fvm venv):

    python nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver HHL \
      -localdt -noshow -shots 0 -iters 40 -initers 1 -cfl 1 -hhl_clock 6 \
      -outdir <dir>

Better as a group in the sweep TOML (item 16) so metadata is captured by
`q8020-sweep` and the harvester.

## Cost and fence

Standard QPE construction grows as O(2^n_t). Today a 15-iteration trial at
n_t = 8 takes about 5,000 s with shots. Statevector is cheaper, but n_t = 10
to 11 is still hours per point. Run the CFL 1 group first; it is the cheap
one and the one that answers the question. With LuGo the cost would
collapse, but we do not have the library (ORNL-held); a LuGo version of the
high-kappa group could be a request to ORNL.

Every point is a solver run over 60 s, so the whole sweep needs Andy's
explicit go-ahead.

## Related

- Error-spectrum analysis of the archived HHL updates (project HHL minus LU
  updates onto the Jacobian eigenmodes). Post-processing only, no fence.
  Tells us which end of the spectrum the current n_t = 8 runs get wrong, and
  so which group above to prioritize.
- Lapworth refs: bus `memory/refs/ref-20260809-0020` (clock precision),
  `ref-20260809-0038` (high-frequency tolerance).
