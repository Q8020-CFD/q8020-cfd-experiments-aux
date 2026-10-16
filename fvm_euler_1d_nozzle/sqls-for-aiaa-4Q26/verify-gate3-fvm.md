# VERDICT: PASS

Order-3 gate re-verification of the fix-up round 9e8fc7fe..1ec8abcf on
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26`, HEAD 1ec8abcf83cf66f031bd55f5dfe81206efef8519,
main ef7f0a8b2247615b56e4391fa1804b59825de217 (42 commits behind HEAD, untouched).
Independent re-verifier; read-only on the repo, venv untouched; all runs under
`/tmp/order3-reverify-fvm/` (deleted after this report). Window
2026-10-15T10:56:50Z to 2026-10-15T11:18:00Z. Python
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.

The six fix-up commits (`git log --oneline 9e8fc7fe..1ec8abcf`):

```
1ec8abcf TESTING: record fix-up round suite and gate fixture timings
27545386 README and TESTING: fix-up round docs for fb_cached, hhl_kernel_rel_err, CSV rotation, circ_qubits authority, deflation index convention, sqls probe
61ebdb21 nozzle: a non-ideal HHL backend without -shots records the 128 shots actually used in the case name and pickle
e3d2e7b8 Move the dry-check-only helpers out of deflation.py into tests/deflation_drycheck.py
1c54a0d0 time_solvers and deflation fix-ups: hhl_kernel_rel_err metric, Hermitian LU of A prime only when consumed, one system pickle writer, condition number passed into deflation_columns
e50f4800 quantum_tools fix-ups: sqls signature probe, fixed-basis count cache with fb_cached, seed only for Aer backends, CSV header rotation, SQLS circ_qubits from the circuit, deflate_k qpy key
```

16 files, +684 / -277 lines. Every fix-up below is real in the diff and
confirmed by a probe or run; nothing regressed. One pre-existing defect outside
the range was found and is reported under Findings (F1), it does not fail this
gate.

Summary table

| item | result | key evidence |
|---|---|---|
| Q1 sqls signature probe | PASS | monkeypatched `quantum_solve` without `seed` -> `RuntimeError` in `__init__`, no solve reached |
| Q2 fb cache / `fb_cached` | PASS | 2-step nelem-2 run: step 0 `t_count_s` 0.997 s / False, step 1 0.0 s / True, same 234899 CX; fresh step-1 count equals it |
| Q3 seed only for Aer | PASS | stub backend: ideal/fake get `seed_simulator`, real-ibm/real-iqm get `{}`; fake_manila seeded twice identical |
| Q4 CSV rotation | PASS | both stale files moved to `rotated/<name>.pre-20261015T110634Z.csv`, 2 `[csv]` lines, singleton globs 1/1 |
| Q5 SQLS `circ_qubits` | PASS | CSV `circ_qubits` 3 = `n_data_qubits` 3 + `m_ancilla` 0 at nelem 2 |
| Q6/Q7/R1 docs | PASS | README lines 104, 230, 245-253, 262, 266, 292-299; `QuantumSQLS` docstring has the reference-free rule |
| Q8 qpy key / refusal | PASS | `..._iter0_deflate2.qpy`; empty-dir `-loadcirc` rc 1, `FileNotFoundError` names the file; no qpy / CSV |
| Q9 `hhl_kernel_rel_err` | PASS | nelem 5 K = 2 recomputed 5.7347387648e-03 vs CSV 5.7347387648e-03; K = 0 3.399247e-03 (gate print and fixture) |
| T1 LU of A' gated | PASS | `dq_herm_q = None` unless `true_sol` or shots (time_solvers.py 565-571) |
| T2 one pickle writer, original A | PASS | duplicate `QuantumHHL` writer gone; K = 2 run pickle sha256 7c2551de... == fixture, `cmp` identical |
| T3 cond passed in | PASS | `deflation_columns(deflation, matrix_props_orig['condition_number'], ...)`; no `np.linalg.cond` in deflation.py |
| D1/D2 module split, `-h` test | PASS | deflation.py public: `DEFLATION_COLUMNS, Deflation(.correction, .recombine), deflate, x_share, deflation_columns`; dry-check helpers in tests; third `-h` test removed |
| N1 fake 128 shots | PASS (code + partial run) | `args.nshots = linsolv_args['shots']` (128); capped run already wrote `circuit_transpile_fake_guadalupe_shots128_nelem2_iter0.qpy` |
| R2 06a 60 % / 73 % | PASS | lines 71-72 read 60 % / 73 %, correction note at 74-76 |
| Regression | PASS | suite 150 tests OK (1 opt-in skip) 129.9 s; gate 7/7 104.9 s; 4 CLI runs rc 0 under `-W error::DeprecationWarning`; hygiene clean; tree clean; nothing pushed |

---

## Q1. `QuantumSQLS.__init__` probes `quantum_solve` for `seed`

Code (quantum_tools.py 920-930 at HEAD): `from sqls.runtime.quantum import
quantum_solve` then `if 'seed' not in inspect.signature(quantum_solve).parameters:
raise RuntimeError(...)` with the sqls-patches install hint. Probe
`/tmp/order3-reverify-fvm/probe_q1.py` (in-process, `PYTHONPATH` = repo): the
installed patched sqls has `seed` (keyword-only, confirmed:
`(..., restore_sign=True, *, seed=None)`); positive control constructs; then
`sqls.runtime.quantum.quantum_solve` was replaced by a stock-signature function
whose body raises `AssertionError('a solve was reached')`:

```
installed sig has seed: True
positive control: patched sqls -> QuantumSQLS() constructed OK
RuntimeError raised in __init__ (before any solve):
    SQLS back-end needs the locally patched sqls (quantum_solve with the keyword-only seed= and sqls_out['qc']); the installed quantum_solve has no 'seed' parameter. Apply the patch from the experiments repo aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/ to the sibling ../sqls clone (README).
```

The `AssertionError` never fired, so the failure is before any solve. PASS.

## Q2. Fixed-basis count cache, `fb_cached` column

Code: `QuantumHHL.structure_key(circ)` = `(circ.num_qubits, tuple((name with
'circuit-<n>' normalized to 'circuit', n_qubits, n_clbits) for ins in circ.data))`;
`fixed_basis_metrics` keeps a one-entry `self._fb_cache` and on a key hit returns
`dict(cached, t_count_s=0.0, fb_cached=True)`; `-circ_metrics none` bypasses it.
`FB_COLUMNS` gained `fb_cached` (and dropped `fb_num_qubits`, now redundant with
the authoritative `circ_qubits`).

Run (`-nelem 2 -linsolver HHL -shots 0 -iters 2 -time_scheme BDF1 -localdt -cfl
1e10 -initers 1 -noshow`, 2026-10-15T11:04:23Z to 11:04:40Z, 17.50 s wall, rc 0),
`qc_metadata_nelem2_statevector.csv` tail columns
(`circ_qubits, fb_depth, fb_total_gates, fb_cx_count, fb_basis, t_count_s, fb_cached, effective_shots, seed`):

```
step 0: 12, 470394, 630388, 234899, u3cx, 0.9972360134124756, False, 0,
step 1: 12, 470394, 630388, 234899, u3cx, 0.0, True, 0,
```

Step 0 `t_count_s` 0.997 s / `fb_cached` False; step 1 `t_count_s` 0.0 s /
`fb_cached` True; identical fb counts. In-process probe
(`probe_q2.py`): Bell circuit counted twice -> second row `fb_cached` True,
`t_count_s` 0.0, same counts; a 3-qubit circuit then re-counts (`fb_cached`
False); a same-width circuit with a different op sequence has a different key;
two `Initialize` circuits with different amplitudes share one key (by design);
two `to_instruction()` wrappers named `circuit-53` / `circuit-56` compare equal
after normalization; `circ_metrics='none'` returns the placeholder row and leaves
the cache `None`.

Key invalidation on a width change (13 <-> 14 qubits) by code reading: the key's
first element is `circ.num_qubits` and the op tuple length grows with the clock
register, so a clock-width change (kappa crossing a power of 2, or a different
`-hhl_deflate_k` that changes kappa_eff enough) produces a different key and a
fresh count. Observed across processes: K = 0 nelem 2 is 12 qubits / `n_clock` 7,
K = 2 nelem 2 is 11 qubits / `n_clock` 6. Note `deflate_k` itself is not part of
the key; within one run it is a fixed CLI flag, so this is moot (see F5).

Adversarial check of the stated assumption ("the {u3, cx} level-0 count depends
on the structure, not the matrix entries"), `probe_q2_fresh.py`: two FRESH
`LinearSystemSolver` instances (empty cache each) solving the iter-0 fixture
system and my run's `system_Ab_nelem2_iter1.pkl` (kappa 38.31 vs 33.77):

```
iter0 fb_depth 470394, fb_total_gates 630388, fb_cx_count 234899, fb_cached False, t_count_s 1.060 s
iter1 fb_depth 470394, fb_total_gates 630388, fb_cx_count 234899, fb_cached False, t_count_s 1.062 s
fresh step-1 count == fresh step-0 count: True
cached row equals fresh step-1 count: True
```

So the reused row is exactly what a re-count would have produced at nelem 2. PASS.

## Q3. `seed_simulator` only for `backend_type in ('ideal', 'fake')`

Code (quantum_tools.py 619-625): `if self.seed is not None and
self.backend_type in ('ideal', 'fake'): run_kwargs.setdefault('seed_simulator',
self.seed)`. Probe `probe_q3.py` with a recording stub backend
(`seed=1234, nshots=100`):

```
ideal     -> backend.run kwargs: {'seed_simulator': 1234}  shots=100
fake      -> backend.run kwargs: {'seed_simulator': 1234}  shots=100
real-ibm  -> backend.run kwargs: {}  shots=100
real-iqm  -> backend.run kwargs: {}  shots=100
ideal with explicit seed_simulator=7 -> {'seed_simulator': 7}
fake, seed None -> {}
```

Real `fake_manila` Bell circuit (500 shots, `seed=1234`), two runs through
`_run_on_backend`: `{'00': 237, '01': 14, '10': 20, '11': 229}` both times
(0.090 s each), identical True; unseeded, two runs differ (`00` 245 vs 226). The
real-iqm branch never receives a seed (the `real-*` backends are commented out
in `_setup_backend`, so this is the only place the rule can bite). PASS.

## Q4. CSV header rotation

Code: `helper_tools.append_csv_row(path, row, verbosity)` (new): reads the
first line, and if it differs from `', '.join(row.keys())` moves the file to
`<dir>/rotated/<stem>.pre-<UTC %Y%m%dT%H%M%SZ>.csv` (`os.replace`), prints one
`[csv] ...` line, then appends (header on a new file). All three per-step
writers now use it: `QuantumHHL.save_metadata`, `QuantumSQLS.save_metadata`,
`LinearSystemSolver.save_hhl_metrics`.

Names learned from a clean nelem-2 SQLS `-shots 0` run (shots 0 is falsy, so no
`_shots0` suffix): `qc_metadata_sqls_nelem2_full_svd.csv` and
`hhl_metrics_nelem2_statevector.csv`. In a fresh dir I planted stale one-line
headers (`step, iter, old_col_a, old_col_b` and the pre-item-6 7-column metrics
header), then ran `-nelem 2 -linsolver SQLS -shots 0 -sqls_method full_svd
-iters 1 ...` at 2026-10-15T11:06:33Z (rc 0):

```
[csv] /tmp/order3-reverify-fvm/q4_stale/qc_metadata_sqls_nelem2_full_svd.csv: existing header differs from the current columns; moved the old file to /tmp/order3-reverify-fvm/q4_stale/rotated/qc_metadata_sqls_nelem2_full_svd.pre-20261015T110634Z.csv and started a new one
[csv] /tmp/order3-reverify-fvm/q4_stale/hhl_metrics_nelem2_statevector.csv: existing header differs from the current columns; moved the old file to /tmp/order3-reverify-fvm/q4_stale/rotated/hhl_metrics_nelem2_statevector.pre-20261015T110634Z.csv and started a new one
```

Exactly 2 `[csv]` lines; `rotated/` holds the two stale files byte-for-byte
(33 bytes and 87 bytes); the new files carry the current 26-column and 8-column
headers (`..., hhl_kernel_rel_err`) with 1 data row each (2 lines); non-recursive
`ls qc_metadata_*.csv` and `ls hhl_metrics_*.csv` in the dir each match exactly
one file. A second identical run appended in place: 0 `[csv]` lines, 3 lines per
file, still 2 files in `rotated/`. PASS.

## Q5. SQLS `circ_qubits` from the circuit

Code (quantum_tools.py 1088-1090): `circ_qubits = (qc.num_qubits if qc is not
None else qc_metadata_numerical['n_data_qubits'] + qc_metadata_numerical['m_ancilla'])`
where `qc = sqls_out.get('qc')`; with `circ_metrics != 'none'` a missing `qc`
raises `RuntimeError` first, so the fallback is reachable only under
`-circ_metrics none`. Run above (`initialize`, nelem 2, N 6 -> 8 padded):
`nqubits 3, n_data_qubits 3, m_ancilla 0, circ_qubits 3` and fixed-basis
`fb_depth 88, fb_total_gates 130, fb_cx_count 42, fb_cached False`. 3 = 3 + 0.
PASS.

## Q6 / Q7 / R1. Documentation

README.md (`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/README.md`):
- line 104: `QuantumSQLS.__init__` probes `quantum_solve`'s signature for the keyword-only `seed=`
- line 230: `hhl_metrics_*` entry defines `hhl_kernel_rel_err` = ||A_q y - b|| / ||b|| on the system handed to the circuit, after scaling, BEFORE recombination, SQLS rows the same quantity
- lines 245-253: "Per-step CSV header rotation", `<outdir>/rotated/<name>.pre-<UTC stamp>.csv`, one `[csv]` log line, harvester singleton globs
- line 262: `circ_qubits` "the AUTHORITATIVE circuit width", HHL legacy `circ_qubits_orig` / `circ_qubits_transpile`, SQLS `qc.num_qubits` = `n_data_qubits + m_ancilla`
- line 266: `fb_cached` row, cache key, 13 <-> 14 invalidation, the stated assumption, always False for SQLS
- lines 292-299: the deflation sums with "ascending order and 0-based indices (i = 0 the smallest singular value, so i < K are the K smallest, exactly as in `deflation.py`)", `sum_{i<K}` in both pre- and post-step. Stated once; deflation.py (lines 6, 9, 75) and time_solvers.py 612 use the same `sum_{i<k}` / `sum_{i<K}` form.
- lines 308-315: Hermitian LU of A' only when consumed, `hhl_kernel_rel_err` before recombination, `_deflate<K>` qpy key and the `-loadcirc` refusal.

R1: `QuantumSQLS` class docstring (quantum_tools.py 884-890 at HEAD): "the
caller fixes reference-free from ``||A(+x) - b|| <= ||A(-x) - b||`` on the
original system (``math_tools.choose_global_sign``; no classical solution
consulted); shots mode restores per-component signs from ``final_b``", plus the
patched-sqls requirement. `math_tools.choose_global_sign` (lines 50-58)
implements exactly that rule and `sqls_solve` calls it on `(A, b, dq_sqls)`.
PASS (with the notation note F2).

## Q8. `_deflate<k>` qpy key; `-loadcirc` refusal

Code: `QuantumHHL.deflate_suffix(k)` -> `'_deflate<k>'` for k > 0, `''` at k = 0;
applied to both `circuit_generated_...` and `circuit_transpile_...` names;
`generate_circuit` raises `FileNotFoundError` when `load_circ and deflate_k and
not os.path.exists(fname)`. Run `-nelem 2 -linsolver HHL -shots 0 -iters 1
-hhl_deflate_k 2 ...` (rc 0) wrote
`circuit_generated_statevector_nelem2_iter0_deflate2.qpy` and
`circuit_transpile_statevector_nelem2_iter0_deflate2.qpy`; the pickle carries
`hhl_deflate_k 2` and `quantum_circuit['deflate_k'] 2`; the CSV row has
`deflate_k 2, kappa 38.306, kappa_eff 5.1989, n_clock 6, x_share_classical 0.9525,
circ_qubits 11`.

Same command with `-loadcirc` into an EMPTY dir: rc 1, stderr ends

```
FileNotFoundError: -loadcirc with -hhl_deflate_k 2: no saved circuit for this deflation rank at /tmp/order3-reverify-fvm/q8_loadcirc/circuit_generated_statevector_nelem2_iter0_deflate2.qpy. Run the case once without -loadcirc to generate the deflate2 circuits; k = 0 circuits are not reusable for A'.
```

Dir afterwards: `run.err`, `run.log` (mine) and `system_Ab_nelem2_iter0.pkl`
(531 bytes). No qpy, no CSV. The system pickle is written by `hhl_solve` before
the quantum call and is not gated by `-savedata` (pre-existing behaviour, see F3).
PASS. The positive `-loadcirc` path is broken for every K by a defect outside
this range, see F1.

## Q9. `hhl_kernel_rel_err` recomputed

Code (time_solvers.py 604-616): after the `true_sol` / `leastsq` scaling and the
shots-mode re-sign, `kernel_rel_err = ||A_q @ dq_hhl - b|| / ||b||` with `A_q =
defl.a_shifted` (K > 0) or `A` (K = 0), computed BEFORE `defl.recombine`; SQLS
rows use `linsys_res / ||b||`. The saved `system_Ab_*.pkl` holds the ORIGINAL A,
b; `dq_*.csv` holds `dq_hhl` AFTER recombination at full repr precision
(`print(*d.ravel(), sep=',')`), so I rebuilt A' and y myself
(`recompute_kernel.py`): numpy SVD of A sorted ascending, A' = A + sum_{i<K}
(sigma_max - sigma_i) u_i v_i^T, correction = sum_{i<K} (u_i . b)(1/sigma_i -
1/sigma_max) v_i, y = dq_hhl - correction (both cross-checked against
`deflation.deflate` to 1e-14).

nelem 5, K = 2 (`-nelem 5 -linsolver HHL -shots 0 -iters 1 -hhl_deflate_k 2
-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`, 2026-10-15T11:06:42Z
to 11:07:25Z, 42.59 s wall, rc 0; the one allowed nelem-5 solve):

```
K=2  ||b||=12.37536841  N=15
linsys_residual CSV 7.0908606604e-02 vs recomputed ||A dq_hhl - b|| 7.0908606604e-02
A' matches deflation.a_shifted: True  corr matches: True
kappa(A)=95.9779 kappa(A')=16.3158 = sigma_max/sigma_K 16.3158
K=2: ||A' y - b||/||b|| recomputed 5.7347387648e-03  CSV hhl_kernel_rel_err 5.7347387648e-03  rel diff 1.03e-14
x_share_classical = 0.9234
```

CSV row: `fidelity 0.9999948974490167, linsys_residual 0.07090860660423984,
hhl_kernel_rel_err 0.0057347387648299455`; qc_metadata `n_clock 7, circ_qubits
13, fb_cx_count 1022314, fb_depth 2024100, t_count_s 4.43 s`.

nelem 5, K = 0: from the gate run's new `[metrics]` print (below)
`hhl_kernel_rel_err 3.399247e-03`, and independently from the fixture
`tests/data/ref_hhl_nelem5_iter0.npz`: ||A dq_ref - b|| 0.0420669369586384 /
||b|| 12.375368413827264 = 3.3992472427e-03 (fidelity 0.9999571377629862).

nelem 2 analogues (same script): K = 0 recomputed 2.5507342761e-03 = CSV
exactly (rel diff 0); K = 2 recomputed 8.6391256690e-03 vs CSV 8.6391256690e-03
(rel diff 2.4e-15), kappa 38.31 -> 5.20, classical share 95.2 %.

Statement: at the nelem-5 iteration-0 Jacobian the quantum kernel is LESS
accurate at K = 2 than at K = 0: relative residual 5.73e-3 vs 3.40e-3, a factor
1.69 worse, even though the overall fidelity is higher (0.99999490 vs
0.99995714) because 92.3 % of ||x||^2 comes from the exact classical rank-2
part. The same direction holds at nelem 2 (8.64e-3 vs 2.55e-3, factor 3.4). The
expected magnitudes (about 5.7e-3 and 3.4e-3) are confirmed. PASS.

## T1. Hermitian LU of A' only when consumed

time_solvers.py 565-571 at HEAD:

```
      A_q = defl.a_shifted
      dq_herm_q = None
      if self.hhl_scale_type == 'true_sol' or self.linsolv_args['shots']:
        dq_herm_q = self.herm_lu_solve(A_q, b)
```

The only consumers are the `true_sol` branch (`np.linalg.norm(dq_herm_q)`) and
the shots-mode re-sign, both inside the same conditions; at K = 0 `dq_herm_q`
is `dq_herm` (set before the block). No `None` dereference path. PASS.

## T2. One `system_Ab_*.pkl` writer, ORIGINAL A, b

At 9e8fc7fe `pickle.dump({'A': ..., 'b': ...})` had three sites: time_solvers.py
556 (`hhl_solve`), 700 (`sqls_solve`) and quantum_tools.py 829
(`QuantumHHL.save_metadata_and_matrices`, the HHL-path duplicate). At HEAD the
quantum_tools writer is gone (`save_metadata` writes only the CSV); the two
remaining sites are one per solver path (hhl_solve 546, sqls_solve 703),
mutually exclusive in a run, both dumping the `A, b` handed to the solve, i.e.
the original system. Evidence on the K = 2 nelem-5 run:

```
cmp /tmp/order3-reverify-fvm/q9_nelem5/system_Ab_nelem5_iter0.pkl tests/data/system_Ab_nelem5_iter0.pkl -> identical
sha256 7c2551de3f326b7aa493d8a8014f6ad880302cbcdcacb0f6c514c98f113b148f (both)
```

The fixture is the August SQLS-run archive, so a bit-identical pickle from a
deflated HHL run proves the stored A is the original, not A'. The nelem-2 iter-0
pickle from my K = 0 run is also sha256-identical to
`tests/data/system_Ab_nelem2_iter0.pkl`. PASS.

## T3. `deflation_columns(defl, cond_a, n_clock)`

deflation.py 119: `def deflation_columns(defl: Deflation | None, cond_a: float,
n_clock: int)`, `kappa = float(cond_a)` at K = 0. Caller quantum_tools.py 845:
`deflation_columns(deflation, matrix_props_orig['condition_number'],
circ.qregs[1].size)`; `condition_number` is the one `np.linalg.cond(A)` in
`math_tools.get_matrix_properties` (line 282). `grep -n linalg.cond deflation.py
quantum_tools.py time_solvers.py` returns nothing. PASS.

## D1 / D2. Module split, dry-check helpers, `-h` test

`deflation.py` public names (runtime `dir()` minus imports): `DEFLATION_COLUMNS`
(the six column names), `Deflation` (dataclass with `shift`, `kappa`,
`kappa_eff`, `x_share_classical`, `correction()`, `recombine()`), `deflate`,
`x_share`, `deflation_columns`. `math` import removed. `tests/deflation_drycheck.py`
(new, 48 lines) holds `state_qubits`, `clock_qubits`, `success_prob`, `b_share`
verbatim from the old module; `tests/test_deflation.py` imports them from there.

`-h` tests: at 9e8fc7fe three tests called `run_solver(['-h'])`
(`tests/test_cli.py` 156, `tests/test_circuit_metrics.py` 211,
`tests/test_deflation.py` 343). At HEAD the deflation one is gone and its
`x_share_classical` assertion is folded into
`test_cli.TestCLIValidation.test_help_lists_all_linear_solvers` (e50f4800).
Two remain, in different modules with different assertions
(`test_circuit_metrics.test_help_lists_circ_metrics` checks `-circ_metrics` and
`u3cx`); no exact duplicate. PASS, read as "the deflation `-h` test exists
once, merged into the CLI help test".

## N1. Fake backend without `-shots`: 128 recorded

Code (nozzle_1d_solver.py 256-260): `if not (backend_type == 'ideal') and
args.nshots == 0: linsolv_args['shots'] = 128; args.nshots = linsolv_args['shots']`.
Downstream: `case_name += f'_nshots{args.nshots}'` (369-370),
`metadata['nshots'] = args.nshots` (457), `metadata['effective_shots'] =
linsolv_args['shots']` for HHL (469), so the pickle gets `nshots == effective_shots
== 128` and the case name `nelem2_HHL_fake_guadalupe_nshots128`. Run attempt
`-nelem 2 -linsolver HHL -backend fake fake_guadalupe -iters 1 ...` (no `-shots`),
capped at 75 s with `perl -e 'alarm 75; exec @ARGV'`: killed by SIGALRM (rc 142)
at 2026-10-15T11:10:21Z after generate and transpile, during the noisy 128-shot
run, so no metadata pickle was produced. Partial evidence from the dir: the
transpiled circuit was saved as
`circuit_transpile_fake_guadalupe_shots128_nelem2_iter0.qpy`, i.e. `self.nshots`
is already 128 inside `QuantumHHL` with no `-shots` given. The pickle values rest
on the code reading above. PASS (code reading, as the task allows).

## R2. 06a numbers

`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/06a-deflation-numbers-and-recommendation.md`
lines 71-72: `| 3 | 13.7 | 7 | 0.0531 | 9.7 | 60 % |` and
`| 4 | 7.9 | 7 | 0.1113 | 20.2 | 73 % |`; lines 74-76: "(x-share rounded from
the output file's 0.225 / 0.352 / 0.602 / 0.727; the k = 3 and k = 4 cells first
read 59 % and 72 %, corrected 2026-10-15 in the item-6 fix-up round.)". Line 113
also says 73 %. PASS.

---

## Regression

- Suite: `.venv/bin/python -m unittest discover -s tests -v`,
  2026-10-15T11:12:35Z to 11:14:46Z: `Ran 150 tests in 129.919s`, `OK (skipped=1)`,
  rc 0; the skip is `test_gate_fixture.TestHHLFixture.test_nelem5_iter0_statevector_matches_reference`
  ("gate-only (~90 s): set FVM_GATE_TESTS=1"). 150 tests / 1 opt-in skip as
  expected (TESTING.md records 115.6 s; 129.9 s here, nothing else running).
- Gate: `FVM_GATE_TESTS=1 .venv/bin/python -m unittest tests.test_gate_fixture -v`,
  11:14:46Z to 11:16:32Z: `Ran 7 tests in 104.932s`, `OK`, 7/7 at
  `MAX_ABS_TOL = 1e-10`; nelem-5 HHL 95.83 s. The new `[metrics]` prints:
  `HHL system_Ab_nelem5_iter0.pkl: fidelity 0.999957137763, linsys_residual 4.206694e-02, hhl_kernel_rel_err 3.399247e-03`;
  `HHL system_Ab_nelem2_iter0.pkl: ... hhl_kernel_rel_err 2.550734e-03`;
  SQLS nelem 5 / nelem 2 `hhl_kernel_rel_err` 3.848910e-15 / 1.120025e-15.
- Rungs under `.venv/bin/python -W error::DeprecationWarning nozzle_1d_solver.py`
  (11:16:32Z to 11:16:56Z), all rc 0, no deprecation text in stderr:
  HHL nelem 2 statevector (`-shots 0 -iters 1`); HHL nelem 2 `-shots 1000 -seed 7
  -iters 1`; SQLS nelem 2 statevector (`-shots 0 -sqls_method full_svd -iters 1`);
  SQLS nelem 2 `-shots 10000 -sqls_repeats 1 -seed 7 -iters 1`; each with
  `-time_scheme BDF1 -localdt -cfl 1e10 -initers 1 -noshow`. "Rung 3b / 4b" are
  not defined in README.md or TESTING.md; I read them as the HHL and SQLS nelem-2
  CLI smoke runs and covered both statevector and shots variants (F7).
- Hygiene: `git diff 9e8fc7fe..1ec8abcf -- '*.py' | grep '^+' | awk 'length > 89'`
  -> no lines; added lines with trailing whitespace -> none.
- Tree / history: `git status --porcelain | wc -l` = 0 before and after all
  runs; HEAD 1ec8abcf, main ef7f0a8b (unchanged, 42 commits behind HEAD); no
  `origin/feature/sqls-aiaa-4q26` remote-tracking ref (nothing pushed); no stash;
  one worktree.

## Findings

F1 (pre-existing, outside 9e8fc7fe..1ec8abcf, follow-up recommended). The
positive `-loadcirc` path is broken for every K at HEAD. `-loadcirc` into the
dir that holds the matching `..._deflate2.qpy` (rc 1) and a K = 0 `-loadcirc`
control on a copy of the 2-step run's dir (rc 1) both die in
`QuantumHHL.generate_circuit` at `circ = qpy.load(fd)[0]` with
`TypeError: ExactReciprocalGate.__init__() missing 2 required positional
arguments: 'num_state_qubits' and 'scaling'` (qiskit 2.5.2 qpy cannot rebuild
that gate). The fvm `qpy.load` line is unchanged in the range (only file names
changed); `ExactReciprocalGate` comes from the fork's UNCOMMITTED item-15 port
(`/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, working tree
`linear_solvers/hhl.py` 464; the committed fork HEAD 66eadf0 still uses qiskit's
`ExactReciprocal`). The suite covers only the refusal
(`test_loadcirc_without_deflated_circuit_refused`). Not a regression of this
round; the Q8 refusal works as specified. The same defect blocked my first
attempt to re-count the saved step-1 qpy, so the structure check used fresh
solves instead.

F2 (minor, notation). deflation.py writes kappa_eff as "sigma_max / sigma_{k+1}"
(module docstring line 12, `Deflation.kappa_eff` docstring, `deflation_columns`
docstring) while the same file's sums are 0-based `sum_{i<k}` and the README
uses `sigma_K` "(0-based: the (K+1)-th smallest)". Same value
(`sigma[-1] / sigma[k]`), mixed index notation inside deflation.py. README is
consistent; tests pin the numbers. Non-blocking.

F3 (precision on Q8 / T2). `hhl_solve` writes `system_Ab_*.pkl` unconditionally
(the `savedata` guard is commented out), before the quantum call, so a refused
`-loadcirc -hhl_deflate_k 2` run leaves that one pickle behind (no qpy, no CSV).
Pre-existing; the pickle holds the original A, b. Non-blocking.

F4 (precision on D2). Two `-h` tests remain in different modules; the removed
third one was the duplicate. See D1/D2.

F5 (precision on Q2). The cache key is (width, op sequence); `deflate_k` is not
in it, so the docstring's "a different deflate_k re-counts" is true only through
the width / clock change it causes. Within a process `deflate_k` is a fixed CLI
flag, so no wrong hit is reachable; the stated assumption was verified at nelem 2
(fresh step-1 count equals the reused step-0 count).

F6 (process). The final check issued one read-only `git ls-remote --heads origin
feature/sqls-aiaa-4q26` (a network call, 0 heads returned) alongside the local
`git branch -r` check (0 refs); the local check alone establishes nothing was
pushed. Noting it since the rules said no network.

F7 (scope). "Rung 3b / 4b" interpreted as above; if they denote something else,
the four nelem-2 CLI runs are the closest in-repo equivalents and all passed.

## Not checked and why

- A real `-loadcirc` round-trip of a deflated circuit: impossible at HEAD (F1).
- N1 end-to-end pickle on a fake backend: the nelem-2 fake_guadalupe run exceeded
  the 75 s cap during the noisy run; code reading plus the `shots128` transpile
  file name stand in.
- `real-iqm` seed behaviour on hardware: no network / hardware; stub probe and
  code reading only.
- The 15-minute run, sweeps, Frontier: out of scope by instruction.
- `build-*.md`, `verify-*.md`, `reproduce-*.md`, `STATUS.md`, WORKPLAN.md in the
  experiments folder: not read, per the rules (only 06a was read there).

Scratch `/tmp/order3-reverify-fvm/` deleted after writing this file. No other
file in this folder was created or modified.
