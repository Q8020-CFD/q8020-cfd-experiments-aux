# Item 19 build: optional, recorded HHL spectral computations

Builder report. Work ran 2026-10-18T22:48Z to 2026-10-18T23:30Z (UTC).
Nothing is committed. The criteria AC19-1 to AC19-8 are for the verifier
to judge; this report only says what was built and measured.

## Summary

- The HHL fork now takes two optional arguments on `construct_circuit` and
  `solve`: `condition_bound` (kappa) and `eigenvalue_bounds`
  (lambda_min, lambda_max). When they are given, the library does not call
  `condition_bounds()` or `eigs_bounds()`.
- The fork records what it used in `HHL.spectral_info` (a `SpectralInfo`
  with values, sources and wall time). `solve()` also puts it on the
  result.
- Without the arguments the circuit is the same as at 9d1d7bb. The
  circuit keys match on four systems (below).
- fvm has a new flag `-hhl_spectrum {internal, deflation}`. The default
  `internal` is the old path. `deflation` needs `-hhl_deflate_k K >= 1`.
  It scales A' by sigma_max and supplies kappa and the eigenvalue bounds
  from the pre-step SVD.
- fvm has a second flag `-hhl_spectral_diag {on, off}`. `off` skips the
  diagnostic full-spectrum metadata columns. It is valid only with
  `-hhl_spectrum deflation`.
- Six new qc_metadata columns and two new pickle keys record the source
  and the values used.
- With `-v 0 -hhl_spectrum deflation -hhl_spectral_diag off`, the only
  dense spectral call left on the HHL path is the pre-step SVD.
- At nelem 2, K = 1, the deflation spectrum gives the same clock register
  (6 qubits). The solution differs from the internal path by
  1.1e-14 max-abs (same encoded matrix) and 1.9e-12 max-abs (default
  spectral-radius path).
- Full fvm suite: 180 tests, 175 pass, 4 fail, 1 skipped, 272.1 s. The 4
  failures are `test_code_versions`. They come from the editable fork
  override the task said to leave in place (details below).

## Repos and state

- fvm: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `1b4abd90`, uncommitted.
- HHL fork: `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, HEAD
  `9d1d7bb`, uncommitted. The fvm venv has the fork working tree as an
  editable dev override (left in place, as asked).
- Fork patch: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-item19.diff`
  (577 lines, sha256 `67e9f74a...5e76`, equal to `git diff` of the fork).
  It applies cleanly to an export of 9d1d7bb and reproduces the working
  tree exactly.
- fvm item-19 changes alone, as a patch on top of the earlier uncommitted
  state:
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/build-19-fvm-item19-only.diff`
  (1617 lines). Applied to HEAD plus the earlier diff, it gives the
  current working tree.
- sqls: not touched.
- Harvester: not touched (needed changes listed below).

### The earlier uncommitted fvm changes

They are intact. `pyproject.toml`, `uv.lock`, both docs files,
`tests/test_output_contract.py` and `tests/test_sqls.py` are byte-equal to
their state before my work. In `README.md`, `TESTING.md`,
`quantum_tools.py`, `time_solvers.py` and `tests/contract.py` my edits sit
on top; the earlier hunks are unchanged.

One thing to know. My first check matched the given fingerprint
`8b541216...1ae71dd`. At 2026-10-18T22:59Z, before I had edited any fvm
file, `git diff | shasum -a 256` gave `1eb11fd3...744220` instead.
`quantum_tools.py` and `TESTING.md` have mtime 2026-10-18T22:49:03Z. So
another actor changed them between my first check and 22:59Z. The content
is the sqls / fork pin wording of the earlier work. I built on the
`1eb11fd3` state. After my work the fvm diff hash is `5bd4c7e5...a126c`.

## AC19-1: inventory of dense full-spectrum calls on the fvm HHL path

Classes: (a) circuit sizing, (b) scaling of the system, (c) metadata or
diagnostic, (d) print only. "Before" lines are 9d1d7bb (fork) and the
pre-item-19 fvm tree. "Now" lines are the current working trees.

| # | Where (before -> now) | Call | Class | Runs when (before) | Now, `-hhl_spectrum deflation` |
|---|---|---|---|---|---|
| F1 | fork `linear_solvers/hhl.py:421-426` -> `hhl.py:515-525` via `numpy_matrix.py:106 -> 111` | `NumPyMatrix.condition_bounds()` = `np.linalg.cond(H)`, a full SVD of the 2N_pow2 matrix | (a) sets `nl` | every circuit, called twice | not called (supplied); internal path now calls it once |
| F2 | fork `hhl.py:431-437` -> `hhl.py:529-541` via `numpy_matrix.py:99-100 -> 102` | `NumPyMatrix.eigs_bounds()` = `np.linalg.eigvals(H)` | (a) sets delta and the evolution time | every circuit, method called twice, each doing eigvals twice (4 eigvals) | not called (supplied); internal path now 1 call, 1 eigvals |
| F3 | fork `tridiagonal_toeplitz.py:220` | `np.linalg.cond` in `TridiagonalToeplitz.condition_bounds()` | (a) | not on the fvm path (fvm passes a NumPy array) | skipped when supplied (tested) |
| F4 | fork `numpy_matrix.py:149 -> 154` | `scipy.linalg.expm(i A t)` | not a spectral decomposition; it is the Hamiltonian simulation itself | every circuit | unchanged, listed for completeness |
| V1 | fvm `deflation.py:104` | `np.linalg.svd(A)` | the item-6 pre-step; the source of the supplied spectrum (item 18 replaces it) | `-hhl_deflate_k K > 0` | runs once; timed in `t_svd_s` |
| V2 | fvm `math_tools.py:180 -> 223` | `np.linalg.eig(A_q)` in the spectral-radius scale | (b) | every HHL step | not called; scale = sigma_max (supplied) |
| V3 | fvm `math_tools.py:178 -> 244` | `np.linalg.cond(A_q)` for `lambda_min`, N > 200 only | (d) printed only | N > 200 at any verbosity | now only at `-v >= 1`; never on the supplied path |
| V4 | fvm `math_tools.py:201 -> 248` | `np.linalg.cond(A_q)` | (d) | `-v >= 1` | not on the supplied path (that branch prints the scale only) |
| V5 | fvm `math_tools.py:209 -> 258` | `np.linalg.eig(A_q / rho)` | (d) printed only | every HHL step with N <= 200, at any verbosity (discarded at `-v 0`) | now gated on `-v >= 1`; not on the supplied path |
| V6 | fvm `math_tools.py:219 -> 268` | `np.linalg.cond(A_q / rho)` | (d) | `-v >= 1` | not on the supplied path |
| V7 | fvm `math_tools.py:121 -> 147` | `np.linalg.cond(A_padded)` in `convert_to_pow2` | (d) | `-v >= 1` | still at `-v >= 1`; `-v 0` skips it |
| V8 | fvm `math_tools.py:160 -> 187` | `np.linalg.cond(A_herm)` in `convert_system_to_herm` | (d) | `-v >= 1` | still at `-v >= 1`; `-v 0` skips it |
| V9 | fvm `math_tools.py:293 -> 352` via `quantum_tools.py:793 -> 859` | `np.linalg.cond(A_q)` in `get_matrix_properties` | (c) `condition_number` column; also the k = 0 `kappa` column | every HHL step | runs with `-hhl_spectral_diag on` (default); skipped with `off` |
| V10 | fvm `math_tools.py:302 -> 361` via `quantum_tools.py:793 -> 859` | `np.linalg.eigvals(A_q)` | (c) `lambda_*_orig` columns | every HHL step | as V9 |
| V11 | fvm `math_tools.py:293, 302 -> 352, 361` via `quantum_tools.py:804 -> 869` | cond and eigvals of `A_q / rho` | (c) `lambda_*_scaled` (cond unused) | every HHL step | as V9 |

Not dense spectral calls, so not counted: `np.linalg.det` in the prints,
the LU solves (`scipy.linalg.solve`, `np.linalg.solve`), the power-iteration
estimate for N > 200, and the unitary synthesis inside qiskit's transpiler.

The inventory was also measured. A call log wraps `numpy.linalg` and
`scipy.linalg` (svd, cond, eig, eigvals, eigh, eigvalsh) and counts calls
made directly from fvm modules or the fork. One `hhl_solve` on the
archived nelem-2 system:

| Configuration | Calls (function, file: count) |
|---|---|
| `-v 0`, K = 0, internal | cond math_tools 2, eigvals math_tools 2, eig math_tools 1, cond numpy_matrix 1, eigvals numpy_matrix 1 |
| `-v 0`, K = 1, internal | the same plus svd deflation 1 |
| `-v 0`, K = 1, deflation, diag on | svd deflation 1, cond math_tools 2, eigvals math_tools 2 |
| `-v 0`, K = 1, deflation, diag off | svd deflation 1 |
| `-v 1`, K = 0, internal | cond math_tools 6, eig math_tools 2, eigvals math_tools 2, cond numpy_matrix 1, eigvals numpy_matrix 1 |
| `-v 1`, K = 1, deflation, diag off | svd deflation 1, cond math_tools 2 (V7, V8, print only) |

`tests/test_hhl_spectrum.py` pins the `-v 0` internal and the
deflation-with-diag-off rows.

## AC19-4: how the singular values become the encoded matrix's bounds

The HHL path hands the library H, not A. Let A_q be the matrix given to
HHL (A, or A' under deflation) and s the scale.

1. Scale: A_s = A_q / s. Every singular value is divided by s.
2. Pad to the next power of 2: P = [[A_s, 0], [0, I_p]]. The p new
   singular values are exactly 1.
3. Hermitian doubling: H = [[0, P], [P^H, 0]]. Its eigenvalues are plus and
   minus the singular values of P. So |eig(H)| is the set of singular
   values of P. (If P is already Hermitian it is not doubled. Then
   |eig(P)| = sigma(P) too, because a Hermitian matrix is normal.)
4. If sigma_min(A_q) <= s <= sigma_max(A_q), the padded ones never set a
   bound. Then lambda_min(H) = sigma_min(A_q) / s, lambda_max(H) =
   sigma_max(A_q) / s, and kappa(H) = sigma_max / sigma_min. The scale and
   the padding drop out of kappa.
5. The default scale is the spectral radius rho(A_q). Every |eigenvalue|
   lies between sigma_min and sigma_max, so rho does too. The identity
   therefore also describes the internal path.

For A' (singular values sigma_k .. sigma_{N-1} of A plus k copies of
sigma_max; 0-based ascending, sigma_k is the (k+1)-th smallest):

- sigma_min(A') = sigma_k and sigma_max(A') = sigma_max.
- The deflation option uses s = sigma_max. Then lambda_min = sigma_k /
  sigma_max, lambda_max = 1, and kappa = sigma_max / sigma_k = `kappa_eff`.

Why s = sigma_max and not rho(A'): rho(A') needs a full eig of A', which
the pre-step does not give. The HHL circuit depends on A only through
A / lambda_min and lambda_min / lambda_max (evolution time
2 pi delta / lambda_min / 2; delta from the ratio). So the quantum solve
of the system block is the same for any s. Only the small absolute offsets
fvm adds to b (1e-12 on every entry, 1e-8 on padded entries) do not scale
with s; they leave round-off-level differences. The circuit itself differs
from the rho-scaled one (the padding block sits at another phase), so the
qpy files carry a `_specdeflation` key.

Checked numerically (before coding) on the nelem-2 and two nelem-5
archived systems for k = 0, 1, 2: predicted and `np.linalg.cond` /
`eigvals` of H agree to about 1e-15 relative. The test
`TestEncodedSpectrumDerivation` checks it to 1e-10 on all nine archived
systems, k = 1 to 4, plus a synthetic 8 x 8 (no padding) and 5 x 5 (three
pad rows) system.

For item 18: the sqls backend must supply sigma_k, the (k+1)-th smallest
singular value, and sigma_max. `smallest_k_svd` with k returns sigma_0 ..
sigma_{k-1} only, so the call needs k + 1 triplets (or a separate estimate
of sigma_k), plus the sigma_max estimate the work plan already mentions.

## What changed

### Fork (`/Users/agallojr/proj/src/q8020/quantum_linear_solvers`)

- `linear_solvers/hhl.py:15-19` imports `math`, `time`, `dataclass`.
- `hhl.py:35-68` new `SpectralInfo` dataclass: `kappa`, `lambda_min`
  (after the near-zero substitution), `lambda_max`, `kappa_source`,
  `eigs_source` (`internal`, `supplied` or `none`), `wall_s`, and the
  property `source` (`internal`, `supplied` or `mixed`).
- `hhl.py:71-92` validation of supplied values (`ValueError`): kappa finite
  and >= 1; bounds finite, 0 <= lambda_min <= lambda_max, lambda_max > 0.
- `hhl.py:187-188` `HHL.spectral_info` attribute (None until a build).
- `hhl.py:422-464` `construct_circuit(..., condition_bound=None,
  eigenvalue_bounds=None)` with docstring; validation first.
- `hhl.py:513-574` the bound logic. Each internal method is called at most
  once (before: twice each). Supplied values skip the call. The wall time
  of the internal calls is measured. `SpectralInfo` is stored.
- `hhl.py:644-686` `solve(..., condition_bound=None,
  eigenvalue_bounds=None)` passes them on and sets
  `solution.spectral_info`.
- `linear_solvers/linear_solver.py` `LinearSolverResult.spectral_info`
  property (and `Any` import).
- `linear_solvers/matrices/numpy_matrix.py:96-111` `eigs_bounds()`
  computes `eigvals` once (before: twice, same values); docstrings name
  the full SVD / eigendecomposition.
- `linear_solvers/__init__.py` exports `SpectralInfo`.
- `test/test_linear_solvers.py:460-635` new class `TestSuppliedSpectrum`
  (8 tests): internal provenance; supplied values skip both internal
  methods (they raise if called) for four NumPy matrices and a
  TridiagonalToeplitz; supplied exact internal values give the same
  registers, instruction count and statevector (exact array equality) and
  the same `scaling`; supplied kappa sizes `nl` (1 -> 3, 2 -> 3, 7 -> 4,
  100 -> 8 clock qubits for nb = 1); eigenvalue bounds alone; invalid
  values rejected; `solve()` passes the bounds through.
- `README.md` new section "Supplied spectral bounds".

### fvm (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`)

- `hhl_spectrum.py` (new, 101 lines): the derivation in its docstring,
  `SPECTRUM_COLUMNS`, `EncodedSpectrum`, `encoded_bounds(sigma_max,
  sigma_min, scale)` (raises if the scale is outside the range),
  `encoded_spectrum(defl)`, `spectrum_columns(...)`.
- `math_tools.py:1-4` imports; `:37-53` `HHL_SPECTRUM_CHOICES`,
  `HHL_SPECTRAL_DIAG_CHOICES` and defaults; `:65-71` `spectrum_suffix()`;
  `:200-273` `scale_Ab(A, b, verbosity, rho=None)` returns the scale time
  too and skips every spectral call when `rho` is given;
  `:276-279` `scale_Ab_by_spectral_radius` kept as a wrapper (same
  numbers); class (d) labels on V3 to V8; V5 gated on verbosity;
  `:344-349` docstring labels `get_matrix_properties` as diagnostic (c).
- `quantum_tools.py:346-392` `QuantumHHL(spectral_diag=True)`;
  `:410-417` `circ_spectrum`, `t_library_spectrum_s`; `:513-528`
  `qpy_path(..., hhl_spectrum)` adds `_spec<source>`; `:557-620`
  `generate_circuit(..., spectrum=None)` passes the bounds, checks the
  library's `source` (RuntimeError on a fork without the API), stores the
  record in `circ.metadata` (kept in the qpy) and reads it back on
  `-loadcirc`; `:640-662` `transpile_circuit(..., hhl_spectrum)`;
  `:829-890` `solve_one_step(..., spectrum=None, a_scale=None)`;
  `:958-968` and `:1014-1019` the pickle and CSV spectrum values;
  `:1032-1040` `_matrix_properties` (diag off gives empty cells).
- `time_solvers.py:9-16` imports; `:29-49` `check_hhl_spectrum()`, the
  one rule set for CLI and class; `:314-322` reads the options; `:333-334`
  passes `spectral_diag`; `:600-609` builds the spectrum from the
  deflation record; `:621-623` passes it.
- `nozzle_1d_solver.py:3-4` import; `:131-157` the two flags with help;
  `:268-274` HHL-only rejection; `:291-298` parse-time rule check;
  `:516-519` pickle keys.
- `tests/contract.py` `QC_METADATA_SPECTRUM_COLUMNS`,
  `QC_METADATA_DIAGNOSTIC_COLUMNS`, the choice constants, the HHL column
  list, `METADATA_KEYS_HHL_ONLY`, `QUANTUM_CIRCUIT_KEYS['HHL']`,
  `expected_files(..., hhl_spectrum=)`.
- `tests/test_hhl_spectrum.py` (new, 23 tests, section (m) of TESTING.md).
- `README.md` CLI table rows, pickle-key sentence, new section
  "Supplied spectrum (`-hhl_spectrum`, work-plan item 19)", code tree.
- `TESTING.md` run record, layout row, contract row, section (m), the
  column order sentence in (l).

## AC19-6: the output-contract change

New HHL `qc_metadata` columns, after `t_svd_s` and before the nine fairness
columns. All existing columns keep their names, order and values.

| column | type | meaning |
|---|---|---|
| `hhl_spectrum` | str | `internal` or `deflation`; empty only for a `-loadcirc` circuit saved before item 19 |
| `hhl_a_scale` | float | the scale s (spectral radius, or sigma_max under deflation) |
| `hhl_kappa` | float | kappa of H used for the clock register |
| `hhl_lambda_min` | float | lambda_min of H used (after the near-zero substitution) |
| `hhl_lambda_max` | float | lambda_max of H used |
| `t_spectrum_s` | float, s | spectral-radius eig time plus the library's bound-call time (the latter is inside `circ_generate_time`); 0.0 under deflation |

Empty-cell convention: unknown values are empty cells, as the fb_* columns
under `-circ_metrics none`. Under `-hhl_spectral_diag off` the five
diagnostic columns (`condition_number`, `lambda_max_orig`,
`lambda_min_orig`, `lambda_max_scaled`, `lambda_min_scaled`) are empty
cells. Times that did not happen are 0.0, as `t_svd_s` at K = 0.

Pickle: `hhl_spectrum` and `hhl_spectral_diag` (strings) next to
`hhl_deflate_k`. `quantum_circuit` gains `hhl_spectrum`, `hhl_a_scale`,
`hhl_kappa`, `hhl_lambda_min`, `hhl_lambda_max` (last step).

File names: default runs unchanged. `-hhl_spectrum deflation` qpy files end
`_deflate<K>_specdeflation.qpy`.

## Design choices

- Two flags, not one. `-hhl_spectrum` changes the numbers fed to the
  circuit. `-hhl_spectral_diag` only changes what is recorded. Keeping them
  apart lets a deflation run keep the old diagnostic columns for
  comparison.
- `-hhl_spectral_diag off` only with deflation. At K = 0 the `kappa`
  column is the diagnostic `cond(A)`, so turning it off there would leave
  `kappa` empty.
- Only `internal` and `deflation` as choices. AC19-4 asks for these two. A
  user-supplied estimate without deflation was not added; the fork API
  supports it if wanted later.
- The fork dedupes its own calls (each bound method once, eigvals once).
  Values and circuits are unchanged (keys match 9d1d7bb). It halves the
  internal cost that item 18 will compare against.
- The record is stored in the qpy circuit metadata. `-loadcirc` can then
  report what built the circuit.
- `generate_circuit` checks the library's reported source. An old fork
  without the API fails loudly instead of silently ignoring the spectrum.
- `solve_one_step(a_scale=)` without a spectrum exists for the equivalence
  test: it gives the internal library bounds of the same encoded matrix.

## Commands and wall times

All with `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.
Scratch lived in `/tmp/item18-19-builder/` and was removed at 2026-10-18T23:31Z.

| Command | When (UTC) | Wall | Result |
|---|---|---|---|
| fork `PYTHONPATH=. python -W error::DeprecationWarning -m unittest test.test_linear_solvers` at 9d1d7bb | 22:53:11Z | 9.3 s | 25 tests OK |
| same, after the fork change | 22:58:16Z | 11.0 s | 33 tests OK; the same 3 pre-existing scipy FutureWarnings as at 9d1d7bb |
| same, final | 23:26:12Z | 11.1 s | 33 tests OK |
| `VIRTUAL_ENV=.venv uv pip install -e ../quantum_linear_solvers --no-deps` | 22:59Z | under 1 s | override installed |
| one-off: spectrum transformation check, 3 systems x k 0..2 | 22:56Z | about 2 s | predicted = computed to about 1e-15 |
| smoke CLI: nelem 2, `-iters 1 -hhl_deflate_k 1 -hhl_spectrum deflation -hhl_spectral_diag off`, output in /tmp | 23:02Z | 16.3 s | ran; n_clock 6 |
| one-off: three in-process nelem-2 K = 1 solves | 23:03Z | 16.9 s | dq differences 1.1e-14 and 1.9e-12 max-abs |
| one-off: circuit_key, default path, old vs new fork (nelem 2 and nelem 5 iter 0, k = 0 and 1) | 23:05Z | 53.4 s and 53.1 s (two processes) | all four keys identical |
| one-off: nelem 5 iter 0, k = 0, internal vs supplied exact values (two processes) | 23:15Z | 32.4 s and 32.7 s | identical key `5de2af4e...`, nl 8 |
| one-off: spectral call log, 8 configurations | 23:17Z | not timed (under 60 s) | table above |
| `python -m unittest tests.test_hhl_spectrum` in parts | 23:10Z to 23:13Z | 3.6 s, 58.9 s, 43.2 s | OK |
| full suite `python -W default::DeprecationWarning -m unittest discover -s tests` | 23:19:02Z to 23:23:36Z | 273.7 s (272.1 s unittest) | 180 tests: 175 pass, 4 fail, 1 skipped |

## Results

### Equivalence gates (AC19-7)

- (i) default path. The nelem-2 HHL gate fixture passes at 1e-10
  (10.6 s). Fork tests pass. The full suite has no DeprecationWarning. Its
  only failures are the 4 `test_code_versions` cases explained below.
- (ii) supplied exact internal values give identical circuits
  (`quantum_tools.circuit_key`), with the library's bound methods patched
  to raise:
  - nelem 2, k = 0 and k = 1 (in the suite, 7.0 s and 3.3 s);
  - nelem 5 iteration 0, k = 1 (in the suite, 32.2 s);
  - nelem 5 iteration 0, k = 0 (one-off; 26 s per build, so two builds
    are over 60 s and it is not in the suite);
  - 4 NumPy matrices including a synthetic 8 x 8 (fork tests, exact
    statevector equality).
- (iii) nelem 2, K = 1, deflation spectrum, diagnostics off: clock
  register 6, equal to the internal computation on the same encoded
  matrix and to the default deflated run. Solution max-abs difference
  1.1e-14 against the same encoded matrix and 1.9e-12 against the default
  rho-scaled path (in-process). The CLI run against the cached internal
  K = 1 run also passes at 1e-10.

Default-path circuit identity with 9d1d7bb (fork level, circuit_key):

| system | k | nl | key prefix | old fork | new fork |
|---|---|---|---|---|---|
| nelem 2 iter 0 | 0 | 7 | af09503fa9db61af | same | same |
| nelem 2 iter 0 | 1 | 6 | aa2d204c388f5a15 | same | same |
| nelem 5 iter 0 | 0 | 8 | 5de2af4ef7b124c6 | same | same |
| nelem 5 iter 0 | 1 | 7 | c43ee0d1e55f7ac9 | same | same |

### Cost (honest scale)

At these sizes the full-spectrum work is tiny. On the 32 x 32 nelem-5
encoded matrix, the library's two internal bound calls took 0.2 ms. Circuit
construction took 26 s. The change matters for item 18's pre-step cost
comparison and at larger N, not for today's wall times.

### The 4 failing tests

`test_output_contract.*.test_code_versions` (HHL, HHL shots, LU, SQLS)
assert `commit_source == 'direct_url'` for `linear_solvers`. With the
editable override the entry is `commit_source: git`, `dirty: True`. The
commit itself is `9d1d7bb`, equal to the pinned rev. README documents this
behaviour of the dev override. The tests should pass once the fork change
is committed and pushed, the rev is bumped in `pyproject.toml`, and
`uv lock && uv sync` replaces the override. I did not weaken the test.

## For the operator

Opt-in nelem-5 HHL gate (about 90 s, not run by me):

```
cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver
FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v
```

Example deflation run (nelem 2, about 8 s to 16 s):

```
.venv/bin/python nozzle_1d_solver.py -nelem 2 -linsolver HHL -shots 0 \
  -iters 1 -hhl_deflate_k 1 -hhl_spectrum deflation -hhl_spectral_diag off \
  -time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow -outdir /tmp/x
```

## Harvester changes needed (not made)

File: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`.

1. Lines 699-701 (HHL artifacts) and 610-612 (SQLS artifacts) do
   `float(row.get("condition_number"))`. An empty cell from
   `-hhl_spectral_diag off` gives `''` and `float('')` raises. Use the
   existing `_float_or_none` and skip None.
2. Read the six new columns. Record `hhl_spectrum` per run, and the
   kappa / lambda bounds used (first and last step, or medians, as done
   for the deflation block near lines 385-440).
3. Add `t_spectrum_s` next to `t_svd_s` in the timing summary, for the
   item-18 cost comparison.
4. Read the pickle keys `hhl_spectrum` and `hhl_spectral_diag` into the
   run parameters.
5. `condition_number_refers_to` (near line 404) can stay. Note that under
   diag off there is no `condition_number`; `kappa_eff` and `hhl_kappa`
   carry it.

## Open doubts

- `-loadcirc` is broken on this stack, on the default path too. qpy on
  qiskit 2.5.2 cannot rebuild `ExactReciprocalGate` (`TypeError:
  ExactReciprocalGate.__init__() missing 2 required positional arguments:
  'num_state_qubits' and 'scaling'`). Seen with a plain nelem-2 K = 0 run
  then `-loadcirc` into the same directory. This predates item 19. So the
  qpy round trip of the spectrum record is tested only by checking the
  bytes in the file and by an in-process read-back with `qpy.load`
  replaced.
- `math_tools.convert_to_pow2` returns None when the size is already a
  power of 2 (its `return` sits inside the padding branch). fvm sizes are
  3 * nelem, never a power of 2, so it never triggers. The 8 x 8 test
  avoids it. Not fixed (out of scope).
- `convert_system_to_herm` decides "already Hermitian" with
  `np.allclose`, whose 1e-8 absolute tolerance depends on the scale. Under
  a different scale a nearly symmetric matrix could flip between doubled
  and not doubled. Both cases have the same |eigenvalue| bounds, so the
  supplied values stay right, but the circuit width would change. Not seen
  on any Euler Jacobian (all are far from symmetric).
- The fork's `_get_delta` floors `lambda_min * (2^n - 1) / lambda_max`.
  Supplied values that differ from the internal ones by round-off could in
  principle land on the other side of an integer. Not seen; the internal
  path has the same fragility.
- AC19-7 (iii) "matches the internal path": I compared against both the
  internal bounds of the same encoded matrix and the default rho-scaled
  path. Both are within 1e-10. The verifier may pick either reading.
- The pre-existing fvm diff changed under me at 2026-10-18T22:49:03Z
  (see "The earlier uncommitted fvm changes"). I did not cause or revert
  it.
