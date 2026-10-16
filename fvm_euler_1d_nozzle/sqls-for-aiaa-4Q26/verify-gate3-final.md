VERDICT: PASS

# Independent re-verification: final fix-up round (gate 3, final)

- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
  `feature/sqls-aiaa-4q26`, HEAD `643cba0cf74ac338172df0919f523b7374528c0c`.
- Range: `1ec8abcf..643cba0c`, seven commits (`git log --oneline`):
  `95782e61` shared deflate suffix / `qpy_path`; `cdf7103b` lazy Hermitian
  LU + reused matvec; `d8a071ba` exact cache key + `u3cx-once`;
  `651fc276` `append_csv_row` edge cases; `a87bb510` SQLS probe solve;
  `eb131de8` docs; `643cba0c` TESTING timings.
- Verified 2026-10-15T11:53:54Z to 2026-10-15T12:08:23Z, read-only, with
  `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.
  Scratch `/tmp/order3-recheck-fvm/` (deleted at the end).
- Hidden files not read, as instructed: `build-*.md`, `verify-*.md`,
  `reproduce-*.md`, `STATUS.md`. README.md and TESTING.md were read.

Diff stat of the range: 12 files, +531 / -139 lines (README.md, TESTING.md,
deflation.py, helper_tools.py, math_tools.py, nozzle_1d_solver.py,
quantum_tools.py, tests/contract.py, tests/test_circuit_metrics.py,
tests/test_output_contract.py, tests/test_sqls.py, time_solvers.py).

## Z1. Exact fixed-basis cache key -- PASS

Code read (`quantum_tools.py`): `circuit_key(circ)` is
`hashlib.sha256` over `_hash_circuit`, which per instruction hashes the
operation's `base_class.__name__` (not `name`), `num_qubits`, `num_clbits`,
`num_ctrl_qubits`, `ctrl_state`, the qubit / clbit indices (int64 bytes) and
the parameters through `_hash_params`: ndarrays as dtype + shape + raw
`tobytes()`, scalars as complex128 bytes, sub-circuits recursively, anything
else by `repr`. Parameter-less non-standard gates are hashed through their
`definition` recursively; standard gates and measure / barrier / reset are
leaves. `QuantumHHL.fixed_basis_metrics` keys its one-entry `_fb_cache` on
this key; under `u3cx-once` it returns the cached row for every call after
the first without hashing; a fresh row's `t_count_s` includes the hash time.

In-process probe (scratch `z1_probe.py`, run from the repo root, 12:07:05Z
to 12:07:25Z). Systems: `system_Ab_nelem2_iter0.pkl` / `iter1.pkl` written
by the CLI u3cx run below; the CLI iter-0 pickle is bit-identical to the
archived `tests/data/system_Ab_nelem2_iter0.pkl`:

```
sha256 CLI iter0        : b0354a9d8a3dcd832b051c8cf0b28043ea328ba4184ea95e246c39d5cb5ce631
sha256 tests/data iter0 : b0354a9d8a3dcd832b051c8cf0b28043ea328ba4184ea95e246c39d5cb5ce631 | identical: True
sha256 CLI iter1        : 38ad2a333373e115ea20e453215b0ebd56dd473f5a9f36a55d9de4eefbb1a9de
```

Circuits built through `QuantumHHL.generate_circuit` (the production
builder: `hhl.construct_circuit` + `measure_all`) after the same
`scale_Ab_by_spectral_radius` -> `convert_to_pow2` -> `convert_system_to_herm`
preprocessing `solve_one_step` applies:

```
circ_metrics mode: u3cx | cache empty: True
built iter0 (2.51 s), iter1 (2.50 s), iter0 again (2.51 s); widths 12/12/12 qubits; len(data) 17/17/17; measure present: True
structure (normalized names, arities) iter0 == iter1: True
raw op names iter0 == iter0-again: False
key iter0       = 8c8dff6f198958a8498185d9740a8ab0d5c95e6292bf7017fbff1bcfc54dc4a9  (488.6 ms)
key iter1       = 406b2ea206b4905bb4882ff360450a809b10ea8e77f40b3a016a38405c95531b  (485.5 ms)
key iter0 again = 8c8dff6f198958a8498185d9740a8ab0d5c95e6292bf7017fbff1bcfc54dc4a9  (486.3 ms)
(a) k0 != k1: True | (b) k0 == k0b: True | 64-hex: True
(b) first count : {'fb_depth': 470394, 'fb_total_gates': 630388, 'fb_cx_count': 234899, 'fb_basis': 'u3cx', 't_count_s': 2.6401617527008057, 'fb_cached': False} | cache key == k0: True
(b) rebuild     : {'fb_depth': 470394, 'fb_total_gates': 630388, 'fb_cx_count': 234899, 'fb_basis': 'u3cx', 't_count_s': 0.0, 'fb_cached': True}
(a) iter1       : {'fb_depth': 470394, 'fb_total_gates': 630388, 'fb_cx_count': 234899, 'fb_basis': 'u3cx', 't_count_s': 1.9314520359039307, 'fb_cached': False} | cache key now == k1: True
hit cached True & t 0.0: True | miss cached False: True | counts equal iter0/iter1: True
u3cx-once in-process: step0 cached False t 2.013 s; step1 (different key) cached True t 0.0
```

(a) The iter-0 and iter-1 circuits have the same structure (the old
structure key would have collided: identical normalized names and arities)
but different sha256 keys. (b) The same system built twice gives the same
key although the raw auto-generated `circuit-<n>` names differ; the rebuild
is a cache hit (`fb_cached` True, `t_count_s` 0.0); the iter-1 circuit
misses and is re-counted. Hash cost of the 12-qubit circuit: 0.486 to
0.489 s here (measured while rung 4b ran concurrently; README says about
0.36 s).

(c) Tiny circuits:

```
(c) Initialize [1,0,0,0] vs [1,1,0,0] keys differ: True | same amplitudes twice equal: True
    keys: b220d6e5c9e8e327 e333642500ada155 b220d6e5c9e8e327
(c) unitary eye vs swap keys differ: True | CX counts 0 vs 3 | structure (name, arity) equal: True
(c) same random unitary twice equal: True | one entry phase-perturbed by 1e-12 rad differs: True
(c) wrapped sub-circuit auto names: circuit-2803 vs circuit-2807 | keys equal: True | angle 0.31 differs: True
(c) cx(0,1) vs cx(1,0) keys differ: True
(c) cx ctrl_state 1 vs 0 keys differ: True
```

The eye-vs-swap pair is the case that motivated the change: same structure,
0 vs 3 CX at level 0, now different keys.

(d) CLI, 2-step nelem-2 HHL statevector
(`-nelem 2 -linsolver HHL -shots 0 -iters 2 -time_scheme BDF1 -localdt
-cfl 1e10 -initers 1 -noshow`):

Default `-circ_metrics u3cx` (rc 0, 12:03:58Z to 12:04:17Z),
`qc_metadata_nelem2_statevector.csv` columns `fb_depth, fb_total_gates,
fb_cx_count, fb_basis, t_count_s, fb_cached`:

```
step 0: 470394, 630388, 234899, u3cx, 1.4677634239196777, False
step 1: 470394, 630388, 234899, u3cx, 1.4797072410583496, False
pickle circ_metrics = 'u3cx' | nshots 0 | hhl_deflate_k 0
```

`-circ_metrics u3cx-once` (rc 0, 12:04:18Z to 12:04:36Z):

```
step 0: 470394, 630388, 234899, u3cx, 1.4940173625946045, False
step 1: 470394, 630388, 234899, u3cx, 0.0, True
pickle circ_metrics = 'u3cx-once' | nshots 0
```

Two real counts under `u3cx` (False / False, `t_count_s` 1.47 s / 1.48 s);
`u3cx-once` gives False / True with `t_count_s` 0.0 on step 1; the metadata
pickle records `circ_metrics` in both. `-h` lists
`-circ_metrics {none,u3cx,u3cx-once}` and says "u3cx-once counts the first
HHL step only and declares the later rows cached (about 9 s per nelem-5
step saved, counts ASSUMED constant across Newton steps; SQLS still counts
every step)". README `-circ_metrics` row: "`u3cx-once`: count the first HHL
step only and declare later rows cached, an assumption"; `fb_cached` row
describes the sha256 key, the entry dependence (2-qubit unitary 0 to 3 CX,
`initialize` dropping all-zero angles) and the `u3cx-once` ASSUMPTION.

## Z2. QuantumSQLS 2 x 2 probe solve at construction -- PASS

Code read: `QuantumSQLS.__init__` checks `inspect.signature(quantum_solve)`
for `seed`, builds the backend, then
`self.probe_time_s = self._probe_patched_sqls(quantum_solve)`, a 2 x 2
`full_svd` statevector solve with `seed=0` and `sqls_out=out`, stdout
redirected; raises `RuntimeError` with `SQLS_PATCH_HINT` on `TypeError`,
missing `out['qc']`, or a wrong answer (`allclose` atol 1e-8). The time is
printed at verbosity 2 and kept as the attribute `probe_time_s`
(`quantum_tools.py:1027`, `:1035`); it is not written to any CSV / pickle.

Probe (scratch `z2_probe.py`, 12:04:40Z, `sqls.runtime.quantum.quantum_solve`
monkeypatched in-process):

```
[verbosity 2 lines mentioning probe]:
    SQLS probe solve (2 x 2 full_svd, statevector): 1.42 ms
probe_time_s attribute = 0.001418 s = 1.418 ms ; < 50 ms -> True
second construction probe_time_s = 0.511 ms
installed quantum_solve has seed: True
[stub accepts seed, no qc] RuntimeError: SQLS back-end needs the locally patched sqls (quantum_solve with the keyword-only seed= and sqls_out['qc']). Apply the patch from the experiments repo aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/ to the sibling ../sqls clone (README). The probe solve exposed no sqls_out['qc'].
[stub without seed] RuntimeError: ... The installed quantum_solve has no 'seed' parameter.
[stub with qc, wrong answer] RuntimeError: ... The probe solve returned [0.  1.5] for A^-1 b = [0. 1.].
```

Construction with the installed patched sqls: 1.418 ms cold, 0.511 ms warm.
The `seed`-accepting stub without `qc` is refused at construction with the
install hint, as are the no-`seed` and wrong-answer stubs.

## Z3. `append_csv_row` edge cases -- PASS

Code read (`helper_tools.py`): `new_file = True`; an existing file whose
first line equals the header appends; a first line that is non-empty and
different rotates to `rotated/<stem>.pre-<_rotation_stamp()><ext>` with a
`-1, -2, ...` suffix while the name exists, and logs one line when
`verbosity`; an empty first line (zero-byte or newline-only file) falls
through with `new_file` True, so the file is opened `'w'` and the header
written, nothing rotated, nothing printed. `_rotation_stamp()` is
`%Y%m%dT%H%M%S.%fZ` UTC.

Probe (scratch `z3_probe.py`, 12:04:39Z):

```
empty file size (bytes): 0
[empty -> new] file lines=['a, b', '1, 2'] rotated_dir=None printed=''
[newline-only -> new] file lines=['a, b', '1, 2'] rotated_dir=None printed=''
[matching header -> append] file lines=['a, b', '1, 2', '3, 4'] rotated_dir=None printed=''
[stale header -> rotate] file lines=['a, c', '5, 6'] rotated_dir=['hhl_metrics_x.pre-20261015T120439.745554Z.csv'] printed='[csv] /tmp/order3-recheck-fvm/z3/hhl_metrics_x.csv: existing header differs from the current columns; moved the old file to /tmp/order3-recheck-fvm/z3/rotated/hhl_metrics_x.pre-20261015T120439.745554Z.csv and started a new one\n'
rotated name: hhl_metrics_x.pre-20261015T120439.745554Z.csv microsecond regex match: True
rotated content: ['a, b', '1, 2', '3, 4']
two more rotations in 8.21 ms; rotated files now (3): ['hhl_metrics_x.pre-20261015T120439.745554Z.csv', 'hhl_metrics_x.pre-20261015T120439.758861Z.csv', 'hhl_metrics_x.pre-20261015T120439.766337Z.csv']; distinct=True
live file: ['e', '8']
pinned stamp ->  ['hhl_metrics_x.pre-20260101T000000.000000Z-1.csv', 'hhl_metrics_x.pre-20260101T000000.000000Z.csv']
```

Three rotations within 21 ms of the same second gave three distinct files
with their rows intact; with `_rotation_stamp` pinned the second rotation
took the `-1` suffix.

## Z4. README: `_nshots128` naming, untested -- PASS

README.md lines 245 to 251 (Outputs section): "Shots default on non-ideal
backends: an HHL run on a `fake` (or `real-*`) backend without `-shots` runs
128 shots. Since the fix-up round the case name and every per-step file
carry that number (`..._nshots128`, `..._shots128`) and the pickle's
`nshots` / `effective_shots` are 128; before, the case name and the pickle
said 0 while the per-step files said 128. This path is NOT exercised by the
test suite: no fake backend wide enough for the 12-qubit nelem-2 HHL circuit
runs in test time." The 128 default is `nozzle_1d_solver.py:262`
(`linsolv_args['shots'] = 128`). Not run (no fake backend run in scope).

## Z5. Memoized lazy `dq_herm_q` in `hhl_solve` -- PASS (by reading)

`time_solvers.py` 555 to 579: `dq_herm = self.herm_lu_solve(A, b)` is
computed unconditionally; `defl = None; A_q = A`, set to
`deflate(A, b, K)` / `defl.a_shifted` only when `self.hhl_deflate_k`
(an `int >= 0`, validated at 287 to 290). The closure

```
def dq_herm_q():
  if 'v' not in herm_q_memo:
    herm_q_memo['v'] = (dq_herm if defl is None
                        else self.herm_lu_solve(A_q, b))
  return herm_q_memo['v']
```

returns `dq_herm` at K = 0 and the Hermitian LU of A' at K > 0, computed on
the first call only (dict memo). `herm_lu_solve` -> `lu_solve` ->
`extract_true_sol_from_herm` returns an array slice on every branch
(`math_tools.py:277-285`); `lu_solve` raises rather than returning None if
both solves fail. The two consumers (`true_sol` norm at 594, shots re-sign
at 609) call `dq_herm_q()`; the default leastsq statevector path never
calls it. No path leaves it None.

## Z6. Kernel residual from the existing matvec -- PASS

`time_solvers.py` 596 to 621: leastsq branch keeps `A_dq_hhl = A_q @ dq_hhl`
and sets `A_dq_q = alpha_ls * A_dq_hhl` (the existing matvec, rescaled; no
second matvec); `true_sol` branch sets `A_dq_q = A_q @ dq_hhl` once after
`choose_global_sign`; the shots block sets `A_dq_q = A_q @ dq_hhl` once
after the per-component re-sign; `kernel_rel_err = norm(A_dq_q - b) /
b_norm`. Values unchanged: gate fixture printed nelem-5 K = 0
`hhl_kernel_rel_err 3.399247e-03` and nelem-2 K = 0 `2.550734e-03` (full
precision in the CLI u3cx run's `hhl_metrics_nelem2_statevector.csv` step 0:
`0.0025507342760926408`).

## Z7. One qpy suffix rule -- PASS

`math_tools.deflate_suffix(deflate_k)` (`math_tools.py:39-44`) is the only
f-string builder of `_deflate<k>`; `QuantumHHL.qpy_path`
(`quantum_tools.py:475-487`) and `tests/contract.py:202` call it;
`generate_circuit` and `transpile_circuit` both build their names through
`qpy_path`. `grep -rn "_deflate" *.py tests/*.py`: every other hit is the
`hhl_deflate_k` option name, a comment / docstring, an error message, or a
test assertion literal (`..._iter0_deflate1`, `_deflate1.qpy`); no
`def deflate_suffix` / `self.deflate_suffix` / `QuantumHHL.deflate_suffix`
remains outside `math_tools.py`.

## Z8. `structure_key` and `re` removed -- PASS

`grep -n "structure_key\|^import re\|\bre\.(sub|match|search|compile)"
quantum_tools.py` returns nothing; `structure_key` appears in no `.py` or
`.md` of the repo (hidden build/verify docs excluded from the grep).
quantum_tools top-level imports: contextlib, hashlib, inspect, io, os,
time, pickle, numpy, qiskit (`QuantumCircuit, qpy, transpile`),
linear_solvers, qiskit.quantum_info, deflation, helper_tools, math_tools.

## Docs: deflation.py 0-based convention -- PASS

`deflation.py` module docstring lines 11 to 15: "Indices are 0-based in
ascending order of sigma (sigma_0 the smallest, sigma_max = sigma_{N-1}), as
in the README. A' is nonsingular with kappa(A') = sigma_max / sigma_k
exactly (sigma_k the (k+1)-th smallest singular value, "sigma_{k+1}" in
1-based counting)". `kappa_eff` property docstring (68): "sigma_max /
sigma_k (0-based: ...)"; `deflation_columns` (129): "sigma_max / sigma_k,
0-based". README line 332 agrees (`sigma_max / sigma_K (0-based: the
(K+1)-th smallest singular value)`). The convention is stated once, in the
module docstring; the two later mentions reference it with the same
formula.

## Regression

- Suite: `env -u FVM_GATE_TESTS MPLBACKEND=Agg .venv/bin/python -m unittest
  discover -s tests -v`, 11:58:17Z to 12:00:57Z: `Ran 156 tests in
  153.240s`, `OK (skipped=1)`; the skip is
  `TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`
  ("gate-only (~90 s): set FVM_GATE_TESTS=1"). nelem-2 HHL fixture metrics
  in the suite log: fidelity 0.999998635611, linsys_residual 3.351933e-03,
  hhl_kernel_rel_err 2.550734e-03.
- Gate: `FVM_GATE_TESTS=1 MPLBACKEND=Agg .venv/bin/python -m unittest
  tests.test_gate_fixture -v`, 12:02:11Z to 12:03:58Z: `Ran 7 tests in
  106.095s`, `OK`. Printed metrics: HHL nelem-5 fidelity 0.999957137763 /
  linsys_residual 4.206694e-02 / hhl_kernel_rel_err 3.399247e-03 (96.91 s);
  HHL nelem-2 0.999998635611 / 3.351933e-03 / 2.550734e-03 (9.13 s); SQLS
  nelem-5 1.000000000000 / 4.763167e-14 / 3.848910e-15; SQLS nelem-2
  1.000000000000 / 1.471831e-15 / 1.120025e-15. All equal to the values the
  task gave for the previous round.
- Rung 3b: `.venv/bin/python -W error::DeprecationWarning nozzle_1d_solver.py
  -nelem 2 -linsolver SQLS -shots 10000 -sqls_repeats 1 -iters 2 ...`
  12:04:36Z to 12:04:39Z, rc 0, zero "deprecat" / "traceback" lines in the
  log; `qc_metadata_sqls_nelem2_full_svd_shots10000.csv` 2 rows,
  `effective_shots` 10000, `fb_cached` False / False, fb counts 42 / 41 CX.
- Rung 4b: same flags with `-linsolver HHL -shots 1000 -iters 1`, 12:07:25Z
  to 12:07:38Z, rc 0, zero "deprecat" / "traceback" lines; 1 row,
  `effective_shots` 1000, `fb_cx_count` 234899, `fb_cached` False,
  `t_count_s` 2.015 s; `hhl_kernel_rel_err` 0.883 (shots mode, unseeded,
  not a reference value).
- Hygiene on added lines: `git diff 1ec8abcf..643cba0c -- '*.py' | grep '^+'
  | awk 'length > 89'` empty; no trailing whitespace on any added `.py` /
  `.md` line; all new module-level imports at the top of their files (see
  Findings for one function-level import).
- Nothing pushed: `git branch -r --contains 643cba0c` empty; the feature
  branch has no upstream (`git branch -vv`); the only remote refs are
  `origin/main` and archive branches. main `ef7f0a8b` = `origin/main`
  `ef7f0a8b`, untouched. `git status --short --branch` after all runs:
  `## feature/sqls-aiaa-4q26` with no entries (clean); stash list empty.

## Findings (non-blocking)

1. Hygiene nit: `a87bb510` adds a function-level import
   `from scipy.sparse import csr_matrix` in `_probe_patched_sqls`
   (`quantum_tools.py:1045`); scipy is a hard dependency (imported at the
   top of `time_solvers.py`) and the same local import already existed in
   `sqls_solve`-side code at `quantum_tools.py:1100`, so one module-level
   import would serve both. The file already carries several local imports
   of optional back-ends (`qiskit_aer`, `iqm`, `sqls`), which is the
   pattern followed; this one is not optional. Does not affect the verdict.
2. Observation: under `-circ_metrics u3cx-once` step 0 still computes and
   stores the sha256 key (about 0.4 s at nelem 2, about 3 s at nelem 5 per
   TESTING.md) although later steps never compare against it. One-time
   cost per run; worth a line if the 9 s per-step saving is the point.
3. Observation: the two CLI runs (u3cx, u3cx-once) agree on step 0 to 12
   digits in every `hhl_metrics` column but differ in the 7th significant
   digit of step 1 (`condition_number` 33.77055150 vs 33.77055366): the step
   0 HHL update differs at the 1e-14 level between runs (Aer statevector
   floating-point nondeterminism, pre-existing), which the Newton step
   amplifies. Unrelated to this round.
4. Observation on Z6: a shots run with `-hhl_scale true_sol` forms two
   matvecs (one in the `true_sol` sign step, one after the per-component
   re-sign); each branch forms one as specified, the first is simply
   superseded. 6 x 6 to 15 x 15, negligible.

## Not checked, and why

- Non-ideal (`fake` / `real-*`) HHL runs and the `_nshots128` naming
  itself: out of scope (README text only was to be confirmed; README itself
  states the path is untested).
- nelem-5 HHL solves other than the single gate fixture run; `-hhl_deflate_k
  K > 0` runs; sweeps; Frontier: excluded by the rules. Z5's K > 0 branch
  is verified by reading only.
- pytest collection (TESTING.md quotes both runners): unittest only, as the
  suite was to be run once.
- Timing claims in TESTING.md (146.5 s suite, 107.8 s gate) were not
  reproduced exactly; mine were 153.2 s and 106.1 s with other work
  partially concurrent (the u3cx / u3cx-once CLI runs overlapped the gate).
  No timing is a pass criterion.
