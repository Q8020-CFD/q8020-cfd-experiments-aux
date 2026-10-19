# Tuning the HHL call once fvm owns the SVD

Written 2026-10-19T19:08Z for the next round of HHL changes in this folder
(after items 6, 18 and 19 of `WORKPLAN.md`). This is a design note from an
interactive session with Andy. Code was read; two short timing probes were
run on the archived nelem 2 and nelem 5 Jacobians. No solver output was
generated.

Summary. fvm is about to hand HHL a modified A and b, and it already holds the
SVD data (sigma_max, sigma_k, the deflated triplets) and the scale s. This
note lists every lever on the HHL call, what each one sets in the circuit,
what fvm can supply, and how each one fails if it is set wrong. Two
conclusions:

- The classical kappa and lambda calls in the library cost about 0.2 ms. A
  circuit build costs 2.5 s to 27 s. So supplying the spectrum is for
  control and provenance, not speed. The build time is spent in Qiskit
  building the controlled powers of exp(iHt).
- The supplied bounds have to bracket the true spectrum of the matrix
  actually encoded, including padding and doubling. If lambda_min is set too
  high, modes are silently dropped. If lambda_max is set too low, modes wrap
  into the negative-eigenvalue half and are inverted with the wrong sign.
  Neither failure raises an error today.

Code paths below are on branch `feature/sqls-aiaa-4q26` of both repos,
working trees as of this writing (item 19 is uncommitted in both).

- Fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers/linear_solvers/hhl.py`
- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/` (`time_solvers.py`
  `hhl_solve`, `quantum_tools.py` `solve_one_step` and `generate_circuit`,
  `math_tools.py`, `hhl_spectrum.py`, `deflation.py`)

## 1. The call today, end to end

fvm side, per Newton iteration (`time_solvers.py` `hhl_solve`, then
`quantum_tools.py` `solve_one_step`):

1. Deflation pre-step, if `-hhl_deflate_k K > 0`:
   A' = A + sum_{i<K} (sigma_max - sigma_i) u_i v_i^T. A_q is A' (or A).
2. Scale: A_q / s and b / s. With `-hhl_spectrum internal`, s = rho(A_q),
   the spectral radius from a full eig. With `deflation`, s = sigma_max.
3. Pad to 2^n (`convert_to_pow2`). Zeros, with 1.0 on the padded diagonal,
   so each padded row adds a singular value of exactly 1.
4. Hermitian-double (`convert_system_to_herm`): H = [[0, A], [A^H, 0]],
   b_herm = (b, 1e-8 ones) + 1e-12. This is skipped if A is already
   Hermitian, which never happens for our Jacobians.
5. `HHL(quantum_instance=backend)`, then
   `construct_circuit(A_herm, b_herm, **supplied)`. supplied is empty for
   `internal`. For `deflation` it is `condition_bound = sigma_max /
   sigma_K` and `eigenvalue_bounds = (sigma_K / sigma_max, 1)`.
6. After measurement, fvm takes the x half of the solution and fixes sign
   and norm with `-hhl_scale` (leastsq or true_sol). Then it adds back the
   rank-K correction. fvm never calls `HHL.solve()` and never reads
   `hhl.scaling`.

Library side (`construct_circuit`):

| Step | Code | Sets |
|------|------|------|
| State prep | `initialize(b / norm(b))` for an ndarray; a circuit is used as given | nb = log2(len(b)) |
| Matrix wrap | `NumPyMatrix(H, evolution_time=2 pi)` for an ndarray; checks square, 2^n, Hermitian | the e^{iHt} circuit |
| kappa | supplied, else `condition_bounds()` = `np.linalg.cond(H)` (full SVD) | nl = max(nb + 1, ceil(log2(kappa + 1))) + neg_vals |
| lambda bounds | supplied, else `eigs_bounds()` = min/max of abs(eigvals(H)) | lambda_min, lambda_max |
| near-zero guard | if lambda_min < 1e-10, use max(1e-10, lambda_max / 1000) and print a warning | lambda_min |
| delta | `_get_delta(nl - neg_vals, lambda_min, lambda_max)` | delta |
| evolution time | t = 2 pi delta / lambda_min / 2^neg_vals, written onto the matrix circuit | t |
| scaling | `self.scaling = lambda_min` (read only by `solve()`) | unused by fvm |
| reciprocal | `ExactReciprocalGate(nl, delta, neg_vals)` (default) or `PiecewiseChebyshevGate` | the 1/lambda rotation |
| QPE | `qpe_circuit(nl, matrix_circuit)`: Hadamards, `U.power(2^j).control()`, inverse QFT | the circuit body |

## 2. What it costs today

Measured 2026-10-19 on this laptop, through fvm's own pre-processing and
the fork working tree. The "kappa + lambda" column is `spectral_info.wall_s`.

| Case | H size | nl | kappa | kappa + lambda calls | `construct_circuit` |
|------|--------|----|-------|----------------------|---------------------|
| nelem 2, iter 0 | 16 x 16 | 7 | 38.31 | 0.23 ms | 2.54 s |
| nelem 5, iter 0 | 32 x 32 | 8 | 95.98 | 0.21 ms | 26.6 s |

A cProfile of the nelem 5 build shows the split:

- `np.linalg.cond`, `eigvals`, `_get_delta`, state prep: under 1 ms
  together.
- `expm` for the 8 QPE powers: about 1 ms (`NumPyMatrix.power` in total
  73 ms).
- Building the 16 controlled unitaries (`UnitaryGate.control()`, with its
  internal transpiles and 510 Quantum Shannon Decompositions): all the rest.
  This grows like 4^nb, not N^3.

Dense-call scaling, random Hermitian-doubled matrices (best of 1 to 3
repeats):

| N | cond (SVD) | eigvals | both | one expm |
|---|------------|---------|------|----------|
| 32 | 0.1 ms | 0.1 ms | 0.1 ms | 0.1 ms |
| 512 | 21 ms | 116 ms | 137 ms | 59 ms |
| 1024 | 0.10 s | 0.51 s | 0.61 s | 0.51 s |
| 2048 | 1.45 s | 3.02 s | 4.48 s | 4.15 s |
| 4096 | 12.4 s | 23.4 s | 35.7 s | 33.4 s |

The kappa and lambda pair costs about the same as one expm, and a build does
nl of those. The controlled-unitary synthesis becomes infeasible long before
N = 4096 (12 system qubits). Probe scripts:
`/Users/agallojr/proj/src/research-notes/bus/agent-tmp/hhl-spectral-cost/probe.py`
and `profile_cc.py` in the same folder.

fvm's own pre-scaling also does dense work: `scale_Ab` runs a full eig of
A_q for rho, and a second eig of A_q / rho for the printout at N <= 200.
With `-hhl_spectrum deflation` the rho eig is skipped. This is also cheap at
our sizes.

## 3. How the clock maps eigenvalues (needed to read the levers)

With neg_vals = 1, nl clock qubits give m = nl - 1 magnitude bits. Let
L = floor((2^m - 1) * lambda_min / lambda_max), using the supplied or
internal bounds. Then:

- delta = L / 2^m.
- An eigenvalue lambda lands on clock integer j = L * lambda / lambda_min.
  lambda_min lands exactly on j = L. lambda_max lands on L * kappa_lambda,
  where kappa_lambda = lambda_max / lambda_min, at or below 2^m - 1.
- `ExactReciprocalGate` rotates the flag by 2 arcsin(L / j) only where
  L / j <= 1. So the output amplitude is lambda_min / lambda: the inverse,
  up to the constant lambda_min.
- Clock values j < L get no rotation. Those modes are dropped from the
  solution, not amplified.
- Clock values j >= 2^m fall in the negative-eigenvalue half and are
  inverted as negative eigenvalues.

Where lambda_min sits today (nb = 5 at nelem 5, nb = 4 at nelem 2):

| System | kappa | nl | m | lambda_min tick L | lambda_max tick | of 2^m - 1 |
|--------|-------|----|---|-------------------|-----------------|------------|
| nelem 5 iter 0, k = 0 | 95.98 | 8 | 7 | 1 | 96.0 | 127 |
| nelem 5 iter 14, k = 0 | 67.63 | 8 | 7 | 1 | 67.6 | 127 |
| nelem 5 iter 0, k = 2 | 16.32 | 7 | 6 | 3 | 49.0 | 63 |
| nelem 2 iter 0, k = 0 | 38.31 | 7 | 6 | 1 | 38.3 | 63 |
| nelem 2 iter 0, k = 1 | 6.85 | 6 | 5 | 4 | 27.4 | 31 |
| CFL 1 (Table 3) | 7.2 | 7 | 6 | 8 | 57.6 | 63 |

At high CFL with no deflation, lambda_min sits on tick 1. Every eigenvalue
between lambda_min and 2 lambda_min rounds onto tick 1 or 2. Those are the
modes that carry most of x. Deflation moves lambda_min up to tick 3 with one
fewer clock qubit. This is the resolution argument behind items 6 and 20.

## 4. The levers

| # | Lever | Where | Sets | fvm can supply | Library change |
|---|-------|-------|------|----------------|----------------|
| 1 | The matrix passed (A', s, padding, doubling) | fvm pre-processing | the spectrum everything else is fitted to | already does | none |
| 2 | b as an ndarray or a circuit | `construct_circuit(vector=...)` | state prep, nb | MPS loader from sqls (06, way 1) | none |
| 3 | `condition_bound` | `construct_circuit` | nl (and the Chebyshev degree) | kappa_eff = sigma_max / sigma_k | none (item 19) |
| 4 | `eigenvalue_bounds` | `construct_circuit` | delta, t | (sigma_k / s, sigma_max / s) | none (item 19) |
| 5 | clock size override | not yet | nl directly | any nl at or above the minimum | `num_clock_qubits` (item 20) |
| 6 | `neg_vals` | `construct_circuit` (exists, never passed) | one sign qubit | must stay True for doubled H | none |
| 7 | `exact_reciprocal` | `HHL(...)` constructor | exact vs Chebyshev rotation | False never used in fvm | check before use |
| 8 | `epsilon` | `HHL(...)` constructor | Chebyshev degree only | default 1e-2 | none |
| 9 | the matrix circuit | `construct_circuit(matrix=QuantumCircuit)` | how e^{iHt} is built | an SVD-based circuit | none (see 4.9) |
| 10 | QPE | `HHL.qpe_circuit` override | the phase-estimation block | LuGo or another QPE | subclass only |
| 11 | output scaling | `hhl.scaling` | norm in `solve()` | ignored; fvm uses `-hhl_scale` | none |

### 4.1 The matrix passed

What fvm passes is what the bounds must describe. For H built from A_q / s
with p padded rows, abs(eig(H)) equals sigma_i(A_q) / s plus p ones
(`hhl_spectrum.py` docstring). Three rules follow:

- Keep sigma_min(A_q) <= s <= sigma_max(A_q). Then the padding ones fall
  inside [lambda_min, lambda_max] and never set a bound. If s > sigma_max,
  the ones become the top eigenvalue and a supplied lambda_max =
  sigma_max / s is too low, so those modes wrap (section 3).
  `encoded_bounds` already raises on this. Any new scaling choice must
  keep that check.
- Any other change to A (a new shift, a projection, a preconditioner) needs
  new bounds derived for that matrix. The item-19 formulas hold only for
  the shifted-SVD A'.
- The library still runs its Hermitian check (`np.allclose(H, H^H)`) and
  its size checks on an ndarray. A circuit input skips them.

### 4.2 b

- An ndarray is normalized by the library and loaded exactly with
  `initialize`, at O(2^n) CX.
- A `QuantumCircuit` is used as is. nb becomes its qubit count, it must
  prepare the normalized state itself, and the fvm padding (1e-8 ones,
  plus the 1e-12 offset) has to be built in. The sqls MPS loader
  (`sqls/core/mps_state_prep.py`) is the candidate; it is lossy at finite
  bond dimension and adds about log2(chi) bond ancillas.
- Projection instead of shift (an idea; not built and not checked). If fvm
  removes the deflated modes from b, b' = b - sum_{i<k} (u_i . b) u_i,
  then HHL on the original A never excites sigma_0 .. sigma_{k-1}. A
  supplied lambda_min = sigma_k / s would then be safe. Modes below it get
  no rotation (section 3), so round-off leakage is dropped rather than
  amplified. This avoids forming A'. It needs a check that the QPE phase
  leakage from the unexcited modes is negligible.

### 4.3 condition_bound (kappa)

- It sets nl = max(nb + 1, ceil(log2(kappa + 1))) + 1. It does not enter
  delta or t; those come from the lambda bounds.
- The library does not check kappa against lambda_max / lambda_min. If the
  supplied kappa is smaller than the ratio of the supplied lambda bounds, m
  can be too small. Then L = 0, delta = 0 and t = 0, and the circuit is
  silently broken (07, Catch 1).
- Rule for fvm: pass kappa = lambda_max / lambda_min from the same bounds,
  as item 19 does (kappa_eff = sigma_max / sigma_k with bounds
  (sigma_k / sigma_max, 1)).
- Overstating kappa only adds clock qubits. QPE cost grows about 2x per
  qubit.

### 4.4 eigenvalue_bounds (lambda_min, lambda_max)

| Error | Effect |
|-------|--------|
| lambda_min too low | L drops; resolution at the small end is wasted; still correct |
| lambda_min too high | true eigenvalues below it land at j < L, get no rotation, and their modes vanish from x |
| lambda_max too high | the spectrum uses fewer ticks; still correct |
| lambda_max too low | top eigenvalues reach j >= 2^m, alias into the negative half, and are inverted wrongly |
| lambda_min = 0 supplied | allowed by the validator; the near-zero guard replaces it with lambda_max / 1000 and prints a warning |

So a margin should always go outward: lambda_min * (1 - e) and
lambda_max * (1 + e). Item 19 handles the sqls Lanczos case this way. There,
sigma_max is a lower bound, low by about the tolerance; the overshoot is
1e-15 to 1e-14 relative and sits near phase 1/2 below the wrap (see the
`hhl_spectrum.py` docstring).

A deliberate lambda_min above the true minimum is a valid tuning choice: a
spectral filter, like a truncated pseudo-inverse. It must be recorded as a
choice, and the dropped modes must be added back classically (the
deflation correction does this for the deflated set).

### 4.5 Clock size override

This is planned in item 20 and `07-clock-register-sweep.md`. Once fvm owns
the spectrum, it is the natural partner of 4.3: fvm picks nl, and the
library checks that L >= 1 for the given bounds (raising and naming the
minimum) instead of computing nl from kappa.

### 4.6 neg_vals

The doubled H always has eigenvalue pairs +-sigma, so neg_vals must stay
True. Only a matrix known to be positive definite could drop the sign qubit.
That would save one clock qubit. Our Jacobians are not, so
leave it alone.

### 4.7 exact_reciprocal = False (Chebyshev)

fvm has never used it; the constructor argument first appeared in fork
`90b177a` (2026-10-15). Before using it, check two things:

- The fit range starts at clock value a = round(2^(2 nl / 3)) (40 at
  nl = 8), and the rotation saturates at arcsin(1) below it. But
  `_get_delta` puts lambda_min on tick L, which is 1 at nelem 5 with k = 0.
  So every mode below tick 40 would get the saturated rotation.
- kappa and `epsilon / 3` set the polynomial degree, capped at nb.

So the Chebyshev path needs its own scaling rule, or a check that the two
conventions agree, before it is used.

### 4.8 epsilon

Default 1e-2. It splits into epsilon_r = epsilon / 3 (Chebyshev degree),
epsilon_s = epsilon / 3 (unused) and epsilon_a = epsilon / 6 (set as
`matrix_circuit.tolerance`). `NumPyMatrix` builds e^{iHt} exactly with expm
and ignores the tolerance. So with the exact reciprocal, epsilon changes
nothing.

### 4.9 The matrix circuit

`construct_circuit` accepts any `QuantumCircuit` for the matrix. It needs:
`num_state_qubits` or `num_qubits`, `num_ancillas`, a settable
`evolution_time` (the library overwrites it), and `power(k)` returning
something with `.control()`. `condition_bounds` and `eigs_bounds` are
optional when the bounds are supplied.

With the full SVD in hand (numpy deflation backend), fvm could write e^{iHt}
as W diag(e^{+-i sigma t / s}) W^H, where the columns of W are
(u_i, +-v_i) / sqrt(2). That is the place to cut the dominant build cost
(section 2): controlled diagonals are cheap, and the W factors cancel between
successive QPE powers. But this is the full classical solution again
(06: a full SVD already is the solution). Use it only as a structural or
resource study, never as a speedup claim.

### 4.10 QPE

`HHL.qpe_circuit(num_clock_qubits, unitary)` is the single seam for
replacing phase estimation, for example with LuGo (ORNL-held, Lu et al.
2503.15439). A subclass override is enough; no fork change is needed.

### 4.11 Output scaling

`hhl.scaling = lambda_min` is used only by `solve()`, to un-scale the norm.
fvm recovers the norm and sign itself (`-hhl_scale`), so supplied bounds do
not change fvm's output scaling. Revisit this only if fvm moves to
`solve()`.

## 5. Checks fvm should run before every tuned call

1. sigma_min(A_q) <= s <= sigma_max(A_q) (padding inside the range).
2. Supplied (lambda_min, lambda_max) bracket abs(eig(H)): any margin goes
   outward, and is recorded.
3. kappa >= lambda_max / lambda_min of the supplied bounds. Best is
   exactly equal.
4. With an nl override: L = floor((2^(nl-1) - 1) / kappa_lambda) >= 1.
5. lambda_min > 0. Do not rely on the near-zero guard.
6. A non-default reciprocal, b circuit or matrix circuit is named in the
   metadata.
7. The `-loadcirc` cache key covers every tuned value (see section 6).

## 6. Proposed shape of the change

fvm side:

- One frozen record, built after the deflation pre-step, e.g.
  `HHLTuning(a_scale, kappa, lambda_min, lambda_max, margin, num_clock,
  exact_reciprocal, b_loader, source)`. It holds every supplied value and
  is the only thing `generate_circuit` reads. `EncodedSpectrum`
  (`hhl_spectrum.py`) becomes its spectral part.
- The section 5 checks live in one function next to `encoded_bounds`.
- The cache key. `qpy_path` today keys on `_deflate<k>` and
  `_spec<source>`. Once values can be tuned freely, the label alone no
  longer identifies the circuit, so add a short hash of the `HHLTuning`
  record to the key.
- Metadata. Extend the item-19 columns (`hhl_spectrum`, `hhl_a_scale`,
  `hhl_kappa`, `hhl_lambda_min`, `hhl_lambda_max`, `t_spectrum_s`) with
  nl, its source, L, delta, t, the margin and the reciprocal type.

Fork side (small, each with an identical-circuit test against the 1e-10
fixture of item 15):

1. `num_clock_qubits` on `construct_circuit` (item 20).
2. Raise when delta = 0 (that is, L = 0), instead of building a t = 0
   circuit. This catches a supplied kappa that is too small.
3. Raise on supplied lambda_min = 0, rather than applying the near-zero
   guard. Keep the guard for the internal path.
4. Add nl, delta and evolution_time to `SpectralInfo`, so fvm records what
   the library actually built rather than recomputing it.
5. A Chebyshev scaling check (4.7), or a documented "not for fvm" note,
   before `exact_reciprocal=False` is exposed as an fvm flag.

## Related

- `06-svd-priming-hhl.md`: why a full SVD cannot prime HHL; MPS state
  prep; deflation.
- `06a-deflation-numbers-and-recommendation.md`: deflation numbers.
- `07-clock-register-sweep.md`: the clock override and sweep (item 20).
- `build-18.md`, `build-19.md`: the sqls SVD backend and the supplied
  spectrum.
