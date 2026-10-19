# Item 18 reproduction (round 1): AC18-5 and AC18-7

Independent reproducer report. Work ran 2026-10-19T00:20:56Z to
2026-10-19T00:35Z (UTC). I did not trust the builder's numbers. I wrote my
own scripts, recomputed AC18-5 and AC18-7, and compared against
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/build-18.md`.
No code was edited. Nothing was committed. Scratch lived in
`/tmp/item18-19-reproducer/` and was removed at the end.

## Verdict

**PASS.** Every numeric claim in AC18-5 and AC18-7 reproduces within its
stated tolerance. Timings agree to a few percent (the criterion was a
factor of 2). Details and caveats follow.

## Setup I verified first

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90`. `git diff | shasum -a 256` =
  `ba85da2213c8285941ed8f5ed15732e5a1102281cce5f6864458fdea856a0931`
  before and after my work. That is the builder's "after" value. I changed
  nothing.
- HHL fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers` at
  `9d1d7bb`. `git diff | shasum -a 256` =
  `67e9f74ab95956ab67e9c67f8d0a9ec569a0b7332464f22cf3b7f73b59c65e76`.
  This equals the sha256 of `fork-patches/UNCOMMITTED-item19.diff`. The
  editable override is installed in the fvm venv (`direct_url.json`:
  `file:///Users/agallojr/proj/src/q8020/quantum_linear_solvers`,
  editable true).
- sqls: `/Users/agallojr/proj/src/q8020/sqls` at `187a7a5`, clean. The
  fvm venv has the pinned git install at that commit.
- Stack: Python 3.12.10, numpy 2.5.2, scipy 1.18.0. Machine: Apple M3 Pro,
  12 cores, 36 GiB RAM, macOS 26.7.1 (arm64). This is the same laptop the
  builder used, so close timing agreement is expected.
- In-process Jacobian assembly. My helper rebuilds the first Newton step
  with `SimCase('compressible_cinf')`, `Mesh(nelem, 0, 10, nondim=True)`,
  `BDFTimeSolver(..., cfl=1e10, localdt=True, 'BDF1', 'LU')` and calls
  `compute_Jacobian_matrix_FD` the way `solve_one_step` does. It
  reproduces `tests/data/system_Ab_nelem2_iter0.pkl` (N = 6) and
  `system_Ab_nelem5_iter0.pkl` (N = 15) **bitwise** (`np.array_equal`
  True for A and b). So the timing matrices are what the CLI passes.

## AC18-5: equivalence on the archived Jacobians

Cases: `system_Ab_nelem5_iter{0,1,2,3,4,5,6,14}.pkl` (15 x 15) for
k = 1..4 (32 cases, the ones the criterion names), plus
`system_Ab_nelem2_iter0.pkl` (6 x 6) for k = 1..4 (the builder's extra 4).
Tolerance 1e-12, one run of the sqls backend per case.

My reference is my own `np.linalg.svd(A)`, sorted ascending. I called the
installed `sqls.core.truncated_svd.smallest_k_svd` directly (k + 1
triplets) and, separately, the code under test `deflate(A, b, k,
svd='sqls')` and `deflate(A, b, k)`.

Principal angles: `arccos` of the cosines cannot resolve angles below
about 1.5e-8 rad in double precision. I therefore used the sine form
`arcsin(||(I - Q1 Q1^T) Q2||_2)`, and I also report the `arccos` value.

| quantity | builder worst | my worst (36 cases) | asked | result |
|---|---|---|---|---|
| smallest k + 1 singular values, relative (via `deflate`) | 5.0e-15 | 4.6e-15 | 1e-8 | REPRODUCED |
| same, direct `smallest_k_svd` call | (not stated) | 4.6e-15 | 1e-8 | REPRODUCED |
| principal angle, left k-subspace (sine form) | 2.4e-14 rad | 1.8e-14 rad | 1e-6 rad | REPRODUCED |
| principal angle, right k-subspace (sine form) | 8.6e-15 rad | 1.1e-14 rad | 1e-6 rad | REPRODUCED |
| same two, `arccos` form (precision floor) | - | 4.7e-8 rad, 3.9e-8 rad | 1e-6 rad | within tolerance |
| sigma_max_est, relative, signed range | -2.7e-16 to +6.1e-16 | -2.7e-16 to +6.1e-16 | tol 1e-12 | REPRODUCED (identical; the start vector is seeded) |
| A', relative Frobenius, sqls vs numpy `deflate` | 9.3e-15 | 8.4e-15 | 1e-8 | REPRODUCED |
| A', sqls vs an A' built from my own SVD | - | 8.4e-15 | 1e-8 | REPRODUCED |
| kappa_eff, relative | 2.4e-15 | 3.4e-15 | "identical" | REPRODUCED (agree to round-off, not bitwise; same as the builder's statement) |
| kappa (sigma_max / sigma_0), relative | - | 4.6e-15 | - | consistent |
| n_clock (nl) and QPE delta integer, internal and supplied, both backends | identical | identical in all 36 cases | identical | REPRODUCED |
| x_share_classical, absolute | 1.4e-13 | 8.1e-14 | (not set) | REPRODUCED |
| recombine(A'^-1 b) vs A^-1 b, relative (sqls) | 2.5e-13 | 1.5e-13 | 1e-8 | REPRODUCED |
| same, numpy backend | - | 3.9e-15 | - | consistent |
| svd_residual (reported by the module) | 2.2e-14 | 1.4e-14 | check limit 1e-6 | REPRODUCED |
| my own residual max(||A^T u - s v||, ||A v - s u||) / sigma_max | - | 1.4e-14 | - | matches the reported value |
| orthonormality defect of the sqls U, V | - | 4.5e-15 | - | consistent |
| smallest relative gap (sigma_k - sigma_{k-1}) / sigma_k | 0.040 | 0.0403 | - | REPRODUCED |

Clock register detail. With N = 15 the padded, doubled H has 32 rows, so
nb = 5 and the floor nb + 1 = 6. ceil(log2(kappa_eff + 1)) is 4 to 6 in
the nelem-5 cases. So nl = 6 + 1 = 7 in every nelem-5 case and 6 in every
nelem-2 case, set by the floor, as the builder says. The internal values
(fork `NumPyMatrix.condition_bounds` / `eigs_bounds` on H built with the
fvm `math_tools` functions) and the supplied values (`encoded_spectrum`)
gave the same (nl, delta) for numpy and sqls in all 36 cases.

Near-degenerate check. The builder's synthetic 9 x 9 case (sigma_1 =
sigma_2 = 2, k = 2, seed 18): kappa_eff identical (4.5 both), singular
values of A' agree to 1.2e-15 relative, recombined solutions agree with
A^-1 b to 6.5e-16 (numpy) and 1.5e-15 (sqls). A' itself differs by 0.28
relative, as expected when the cut goes through a degenerate pair. The
builder quoted 1e-10 as the tested bound; my values are far inside it.
REPRODUCED.

Reproducibility. Five sqls runs on nelem5_iter0, k = 2: A' not bitwise
equal, max 1.2e-14 relative between runs; singular values 1.3e-15;
sigma_max bitwise identical (seeded). numpy runs bitwise identical.
REPRODUCED (the builder's "about 1e-14, not bit for bit").

### AC18-5 CLI: nelem 2, one Newton step, -hhl_deflate_k 1

Four runs, in parallel, 9.6 s wall each (2026-10-19T00:26:26Z to
00:26:36Z). Common flags: `-nelem 2 -linsolver HHL -shots 0 -iters 1
-hhl_deflate_k 1 -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`.

| spectrum | circ_qubits | n_clock | dq_hhl max-abs (numpy vs sqls) | dq_hhl relative | builder |
|---|---|---|---|---|---|
| default (internal) | 11 / 11 | 6 / 6 | 7.4e-15 | 1.8e-14 | 3.8e-15, 7.8e-15 |
| `-hhl_spectrum deflation -hhl_spectral_diag off` | 11 / 11 | 6 / 6 | 3.5e-15 | 8.1e-15 | 1.0e-14, 2.7e-14 |

Both are round-off (the builder's and mine differ by run-to-run noise in
the statevector path). Asked: <= 1e-8. REPRODUCED.

For contrast, numpy internal versus numpy supplied spectrum: 1.89e-12
max-abs (builder 1.9e-12). REPRODUCED. `dq_lu` is bitwise equal across
all four runs.

The qc_metadata rows carried the nine item-18 columns. sqls:
`hhl_deflate_svd=sqls`, `svd_tol=1e-12`, `sigma_max_method=eigsh_ata`,
`sigma_max_tol=1e-12`, `x_share_method=splu_solve`, `svd_residual` about
1.7e-15, `t_svd_s` 1.06 ms, `t_smallest_k_s` 0.50 ms, `t_sigma_max_s`
0.39 ms, `t_xshare_s` 0.042 ms. numpy: `sigma_max_method=numpy_svd`,
`x_share_method=svd`, tolerances and residual empty, `t_svd_s` 0.059 ms.
kappa_eff 6.8498325090581 (numpy) vs 6.849832509058101 (sqls).

## AC18-7: cost of the pre-step (classical only)

My harness, not the builder's. For each nelem I assembled A, b in-process
(see Setup), then for k = 2 and k = 4 ran one warm-up of each backend and
7 timed repeats (5 for nelem 682). Each repeat alternated numpy and sqls.
I recorded:

- `wall`: `perf_counter` around the whole `deflate()` call. For sqls this
  includes the x_share solve.
- `t_svd_s`: the module's own pre-step timer (what the builder tabulated).
- the module's split timers (`t_smallest_k_s`, `t_sigma_max_s`,
  `t_xshare_s`).
- raw independent timings of `np.linalg.svd(A)`, `smallest_k_svd(csr(A),
  k + 1, tol=1e-12)`, my own `eigsh` sigma_max on A^T A (k = 1, 'LA',
  tol 1e-12, seeded v0), and one `splu(A).solve(b)` (nelem 5 to 341
  only).

All medians, wall seconds, default multi-threaded numpy and scipy, tol
1e-12. nnz is `np.count_nonzero(A)`; kappa is `np.linalg.cond(A)`.

| nelem | N | k | nnz | kappa | numpy t_svd_s (builder) | sqls t_svd_s (builder) | smallest-k | sigma_max | x_share | faster (builder) |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 15 | 2 | 149 | 96 | 0.034 ms (0.036) | 0.637 ms (0.633) | 0.284 ms | 0.284 ms | 0.032 ms | numpy 18.6x (17.6x) |
| 5 | 15 | 4 | 149 | 96 | 0.033 ms (0.033) | 0.627 ms (0.623) | 0.281 ms | 0.278 ms | 0.032 ms | numpy 18.8x (19.1x) |
| 11 | 33 | 2 | 383 | 219 | 0.099 ms (0.102) | 0.789 ms (0.800) | 0.376 ms | 0.352 ms | 0.042 ms | numpy 7.9x (7.9x) |
| 11 | 33 | 4 | 383 | 219 | 0.095 ms (0.099) | 0.774 ms (0.781) | 0.374 ms | 0.344 ms | 0.050 ms | numpy 8.1x (7.9x) |
| 21 | 63 | 2 | 773 | 422 | 0.339 ms (0.337) | 1.184 ms (1.198) | 0.458 ms | 0.646 ms | 0.061 ms | numpy 3.5x (3.6x) |
| 21 | 63 | 4 | 773 | 422 | 0.334 ms (0.333) | 1.191 ms (1.195) | 0.462 ms | 0.649 ms | 0.061 ms | numpy 3.6x (3.6x) |
| 42 | 126 | 2 | 3634 | 851 | 1.285 ms (1.288) | 2.515 ms (2.522) | 0.838 ms | 1.529 ms | 0.140 ms | numpy 2.0x (2.0x) |
| 42 | 126 | 4 | 3634 | 851 | 1.285 ms (1.281) | 2.504 ms (2.511) | 0.825 ms | 1.524 ms | 0.138 ms | numpy 1.9x (2.0x) |
| 85 | 255 | 2 | 3269 | 1731 | 5.872 ms (5.914) | 4.312 ms (4.314) | 0.919 ms | 3.090 ms | 0.124 ms | sqls 1.4x (1.4x) |
| 85 | 255 | 4 | 3269 | 1731 | 5.850 ms (5.880) | 4.284 ms (4.302) | 0.927 ms | 3.074 ms | 0.123 ms | sqls 1.4x (1.4x) |
| 170 | 510 | 2 | 44369 | 3469 | 26.251 ms (26.179) | 35.617 ms (35.915) | 6.699 ms | 27.725 ms | 1.693 ms | numpy 1.4x (1.4x) |
| 170 | 510 | 4 | 44369 | 3469 | 26.182 ms (26.254) | 35.659 ms (35.881) | 6.671 ms | 27.740 ms | 1.682 ms | numpy 1.4x (1.4x) |
| 341 | 1023 | 2 | 13253 | 6967 | 0.150 s (0.150) | 37.612 ms (37.338) | 2.638 ms | 31.767 ms | 0.407 ms | sqls 4.0x (4.0x) |
| 341 | 1023 | 4 | 13253 | 6967 | 0.150 s (0.150) | 37.520 ms (37.492) | 2.652 ms | 31.661 ms | 0.407 ms | sqls 4.0x (4.0x) |
| 682 | 2046 | 2 | 629626 | 13940 | 1.117 s (1.133) | 2.660 s (2.667) | 0.167 s | 2.477 s | 27.5 ms | numpy 2.4x (2.4x) |
| 682 | 2046 | 4 | 629626 | 13940 | 1.121 s (1.127) | 2.663 s (2.666) | 0.162 s | 2.478 s | 28.8 ms | numpy 2.4x (2.4x) |

Every row: REPRODUCED. nnz and kappa are identical to the builder's. The
largest timing deviation from the builder is about 3 % (nelem 170
smallest-k, 6.70 ms vs 6.86 ms). The winner and the speedup factor agree
in every row to one decimal, except nelem 5 k = 2 (18.6x vs 17.6x) and
nelem 42 k = 4 (1.9x vs 2.0x), which are sub-0.1 ms noise.

My `wall` around the whole `deflate()` call ran 1 % to 5 % above
`t_svd_s`. For sqls the difference is the x_share solve plus the
`Deflation` object construction. So the module's `t_svd_s` timer is
honest about what it covers.

Raw independent timings (nelem 5 to 341, k = 2 rows; the module's
timers in brackets): `np.linalg.svd` 0.026 ms, 0.083 ms, 0.317 ms,
1.256 ms, 5.771 ms, 25.862 ms, 0.147 s (vs t_svd_s 0.034 ms to 0.150 s,
the difference is the rank-k update); `smallest_k_svd` 0.274 ms, 0.378 ms,
0.453 ms, 0.822 ms, 0.909 ms, 6.638 ms, 2.619 ms (vs 0.284 ms to 6.699
ms); my own eigsh sigma_max 0.183 ms, 0.237 ms, 0.538 ms, 1.406 ms,
2.970 ms, 27.437 ms, 31.322 ms (vs the module's 0.284 ms to 31.767 ms; the
module also computes the norm-bound check, about 0.1 ms at small N);
splu solve 0.031 ms to 1.695 ms (vs 0.032 ms to 1.693 ms). The split
timers match independent measurements.

Accuracy on the same matrices (sqls vs numpy; builder in brackets):

| nelem | N | k | sigma rel | A' rel | sigma_max rel | x_share abs | svd_residual |
|---|---|---|---|---|---|---|---|
| 5 | 15 | 2 | 1.3e-15 (1.3e-15) | 9.3e-15 (6.8e-15) | 2.7e-16 (2.7e-16) | 5.4e-14 (5.8e-14) | 1.7e-14 (7.9e-15) |
| 11 | 33 | 2 | 1.7e-15 (1.7e-15) | 1.6e-14 (1.4e-14) | 1.2e-16 (1.2e-16) | 6.3e-14 (7.3e-14) | 3.5e-14 (2.6e-14) |
| 21 | 63 | 2 | 1.0e-14 (9.6e-15) | 1.8e-14 (2.1e-14) | 6.4e-16 (6.4e-16) | 1.5e-13 (6.9e-14) | 4.8e-14 (5.9e-14) |
| 42 | 126 | 2 | 2.1e-14 (2.1e-14) | 2.4e-14 (3.1e-14) | 7.6e-16 (7.6e-16) | 9.0e-15 (6.7e-16) | 7.4e-14 (1.1e-13) |
| 85 | 255 | 2 | 3.4e-14 (3.7e-14) | 3.9e-14 (4.4e-14) | 5.0e-16 (5.0e-16) | 9.8e-14 (1.6e-13) | 1.5e-13 (2.5e-13) |
| 170 | 510 | 2 | 4.3e-14 (4.2e-14) | 7.6e-14 (6.8e-14) | 3.8e-16 (3.8e-16) | 2.9e-13 (3.7e-15) | 5.2e-13 (4.3e-13) |
| 341 | 1023 | 2 | 1.1e-13 (1.2e-13) | 1.0e-13 (8.8e-14) | 1.5e-15 (1.5e-15) | 5.1e-13 (5.8e-13) | 1.0e-12 (8.4e-13) |
| 682 | 2046 | 2 | 3.1e-13 (3.2e-13) | 1.5e-13 (1.3e-13) | 3.7e-15 (3.7e-15) | 7.3e-14 (8.9e-14) | 2.1e-12 (1.6e-12) |

k = 4 rows are the same to within a factor of 2 to 3 on the round-off
quantities (the sqls start vector is random; sigma_max is seeded and
identical). All far below the AC18-5 tolerances. REPRODUCED. x_share abs
varies more between runs (e.g. nelem 170: 2.9e-13 vs 3.7e-15) because it
is a difference of two numbers near 1 at round-off; still about 1e-13.

Fill in the fvm Jacobian (builder's explanation of the N = 510 and 2046
rows):

| nelem | N | nnz in 5-element band | nnz off band | max off-band entry / max entry | builder |
|---|---|---|---|---|---|
| 42 | 126 | 1708 | 1926 | 1.1e-9 | (named as a fill case, no number) |
| 170 | 510 | 7070 | 37299 | 5.5e-10 | 5.5e-10 |
| 682 | 2046 | 28498 | 601128 | 2.7e-10 | 2.7e-10; 629,626 vs 28,498 |

629626 / 2046^2 = 15.0 % dense. REPRODUCED. nelem 5, 11, 21, 85 and 341
have no off-band entries at all.

Context rows, band-truncated matrices (entries outside the 5-element
block band set to 0; not what fvm passes), 5 repeats:

| nelem | N | k | numpy | sqls | smallest-k | sigma_max | x_share | faster | builder |
|---|---|---|---|---|---|---|---|---|---|
| 170 | 510 | 2 | 26.17 ms | 11.33 ms | 1.59 ms | 8.86 ms | 0.22 ms | sqls 2.3x | 26.19 / 11.38 ms, 2.3x |
| 170 | 510 | 4 | 26.18 ms | 11.27 ms | 1.56 ms | 8.83 ms | 0.21 ms | sqls 2.3x | (same to 1 %) |
| 682 | 2046 | 2 | 1.116 s | 0.168 s | 4.65 ms | 0.152 s | 0.78 ms | sqls 6.6x | 1.133 s / 0.170 s, 6.7x |
| 682 | 2046 | 4 | 1.111 s | 0.171 s | 4.83 ms | 0.153 s | 0.79 ms | sqls 6.5x | (same to 1 %) |

REPRODUCED.

Sigma_max cost notes (builder's secondary claims), my own eigsh on A^T A,
9 repeats:

- Top relative gap (sigma_max - sigma_{N-2}) / sigma_max: 9.4e-5 at
  nelem 85, 4.1e-7 at nelem 341. Builder: 9.4e-5, 4.1e-7. REPRODUCED.
- nelem 341: tol 1e-12 29.9 ms; tol 1e-8 23.0 ms (23 % saved; builder
  "about 25 %", 31 to 24 ms); ncv 40 at tol 1e-12 21.6 ms (1.38x; builder
  "about 1.5x", 31 to 21 ms). All three gave sigma_max to <= 1.9e-15
  relative. REPRODUCED within noise.
- nelem 85: 2.87 ms, 2.25 ms, 2.71 ms for the same three settings.

Where each wins, as I measured it: numpy below N = 255; sqls at N = 255
(1.4x) and N = 1023 (4.0x); numpy at N = 510 (1.4x) and N = 2046 (2.4x)
because of the finite-difference fill. The builder's summary is correct.

## Scope and caveats

- I reproduced AC18-5 and AC18-7 only, as assigned. I did not re-run the
  test suite, the AC18-8 call log, or the AC18-1 bitwise old-versus-new
  comparison (the pre-item-18 reference copy lived in the builder's
  scratch, now gone). A verifier covers those.
- Same machine as the builder. Agreement to a few percent is expected
  here; it does not test cross-machine portability of the timings.
- The AC18-5 in-process script ran concurrently with the four CLI HHL
  runs. Its numbers are not timings, so this is harmless. All AC18-7
  timing runs ran alone.
- The sqls backend draws a random Lanczos start vector, so my round-off
  level numbers differ from the builder's by factors of about 2 to 3 in
  either direction. sigma_max is seeded and matched bitwise.
- The `arccos` principal angle floors at about 1.5e-8 rad in double
  precision. The sine form resolves to 1e-14 rad. Both are within 1e-6 rad.
- Not run (over the 60 s single-run limit), for the operator:

  ```
  cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
  FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
  ```

## Commands and wall times

All with `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`
from the fvm root. Scripts lived in `/tmp/item18-19-reproducer/`.

| what | when (UTC) | wall | result |
|---|---|---|---|
| `check_assembly.py`: in-process Jacobian vs archived nelem 2 and 5 pickles | 00:25Z | about 1 s | bitwise equal; assembly 0.6 ms (N = 6), 1.1 ms (N = 15) |
| `ac18_5.py` (36 cases, both backends, clock check) plus 4 CLI nelem-2 HHL runs (numpy / sqls x internal / supplied), all in parallel | 00:26:26Z to 00:26:36Z | 10 s total; each CLI run 9.6 s | tables above |
| `ac18_7.py 5,11,21,42,85,170,341 7 7` (7 timed repeats, 7 raw repeats) | 00:27:56Z to 00:28:06Z | 9.9 s | table above |
| `ac18_7.py 682 5 0` (5 repeats, alone) | 00:28:43Z to 00:29:35Z | 51.8 s | N = 2046 rows |
| `ac18_7.py 170,682 5 0 band` (band-truncated context) | 00:30:16Z to 00:30:37Z | 21.2 s | context table |
| `probe.py` (tol / ncv / top gap at nelem 85, 341) | 00:30:37Z to 00:30:40Z | 3 s | notes above |
| degenerate 9 x 9 case; 5-run reproducibility; repo sha checks | 00:31Z | under 5 s each | notes above |

CLI output went to `/tmp/item18-19-reproducer/cli/{np_int,sq_int,np_sup,sq_sup}/`
and was deleted with the scratch tree.

## Scratch removal

`rm -rf /tmp/item18-19-reproducer` after this report was written.
