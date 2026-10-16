# Re-verification: gate-3 close mini-round (643cba0c..d2e5c6a5)

VERDICT: PASS

Independent re-verifier, read-only, 2026-10-15T12:36:25Z to 2026-10-15T12:48Z.
Repo `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch
`feature/sqls-aiaa-4q26`, HEAD `d2e5c6a5a179f7d1eced6799f7b7a145729b1bb5`.
Range: two commits, `6f96d9fa` (7 files, +208/-128) and `d2e5c6a5` (3 files,
+58/-28); 9 files, +265/-155 total. Python
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.
Scratch `/tmp/order3-final-recheck/` (deleted after this report). Machine
shared with other agents (suite user time 347 s against 199.6 s wall).

## Points

1. `circuit_key` separates controlled base gates and Pauli operators. PASS.
   In-process probe (`annotated=False`, new module): RY(0.3).control(2) key
   `0d74ad24...` vs RZ(0.3).control(2) `75d316a4...` differ; a repeated RY
   pair gives the same key; PauliEvolutionGate XX `2b14a353...` vs ZZ
   `a873ad33...` differ; XX repeated same. Adversarial control: the SAME
   probe against `git show 643cba0c:quantum_tools.py` gives RY == RZ
   (`5774b727...` both) and XX == ZZ (`a80b35eb...` both), so the new test
   catches a real pre-change collision. The new test alone under
   `-W error::DeprecationWarning`
   (`tests.test_circuit_metrics.TestFixedBasisCache.test_key_separates_controlled_base_gates_and_pauli_operators`):
   1 test OK in 24.253 s (24.25 s of it the cached nelem-2 HHL run in
   setUpClass, the test body 0.01 s), 0 occurrences of "deprecat" in the log.
   Code: `_hash_operation` hashes `base_gate` (class + params, no definition)
   and, for `PauliEvolutionGate`, `pauli:<label>:` plus the complex
   coefficient bytes per term (`quantum_tools.py` lines 204-237).
2. Default `-circ_metrics u3cx` counts every step, no hashing. PASS.
   2-step nelem-2 HHL statevector run (24.57 s process, 60.38 s user):
   `qc_metadata_nelem2_statevector.csv` rows fb_cached False / False,
   t_count_s 1.4841 s / 1.4706 s, fb_cx_count 234899 / 234899,
   fb_total_gates 630388, fb_depth 470394, fb_basis u3cx on both. Code:
   `fixed_basis_metrics` line 527 `if self.circ_metrics != 'u3cx-once':
   return circuit_metrics(circ, self.circ_metrics)` reaches no hash;
   `grep -rn circuit_key --include='*.py'` outside tests hits only the
   `def` (line 254) and two comments (lines 175, 516): no call site anywhere
   in the solver path. In-process: `u3cx` on the identical tiny circuit
   twice gives fb_cached False / False, t_count_s > 0 both, `_fb_cache`
   stays None.
3. `-circ_metrics u3cx-once` reuses on a shape guard. PASS. 2-step run
   (22.73 s process): fb_cached False / True, t_count_s 1.4739 s / 0.0 s,
   counts identical to point 2 (234899 CX / 630388 / 470394). Code: cache
   row is `((int(circ.num_qubits), len(circ.data)), fb)` (lines 529, 537);
   a mismatch prints `[fb] circuit (qubits, instructions) changed ... :
   re-counting` when verbosity is nonzero and re-counts. In-process probe,
   verbosity 1: 2-qubit 3-instruction circuit counted (fb_cached False),
   a different 2-qubit 3-instruction circuit reused (fb_cached True,
   t_count_s 0.0), then a 3-qubit 3-instruction circuit re-counted
   (fb_cached False, t_count_s > 0, CX 2) with exactly one log line
   `[fb] circuit (qubits, instructions) changed (2, 3) -> (3, 3):
   re-counting`; `_fb_cache[0]` afterwards (3, 3). No `[fb]` line in either
   CLI run's stdout (the two nelem-2 steps share the shape, as expected).
4. Constructor probe needs `sqls_out['qc']` only when counting. PASS.
   In-process, `sqls.runtime.quantum.quantum_solve` mocked: a stub
   accepting `seed=` but exposing no `qc` is ACCEPTED with
   `circ_metrics='none'` (probe_time_s 0.000293 s) and REFUSED with `'u3cx'`
   and `'u3cx-once'` (RuntimeError text ends "The probe solve exposed no
   sqls_out['qc'] (needed for -circ_metrics u3cx)", names `sqls-patches`); a
   stub WITHOUT `seed` is refused for both `'none'` and `'u3cx'` ("The
   installed quantum_solve has no 'seed' parameter"), the signature check
   (`quantum_tools.py` line 1015) runs before the probe solve. The per-step
   check (line 1174) keeps the same `circ_metrics != 'none'` condition.
5. `helper_tools.append_csv_row` edge cases. PASS. Scratch probes: a file
   holding `'  \n\n \n'` is treated as new (`'a, b\n1, 2\n'`, no `rotated/`,
   nothing printed); `'\n0, 0, 1\n'` is ROTATED to
   `rotated/blank.pre-20261015T124556.947540Z.csv` with its bytes intact and
   the new file is `'a\n3\n'` (one `[csv]` log line); a stale header
   `'old, cols\n5, 6\n'` rotates to `rotated/stale.pre-20261015T124556.955929Z.csv`
   (regex `\d{8}T\d{6}\.\d{6}Z` matches, microsecond stamp). Code reads the
   whole file, `first = content.split('\n', 1)[0]`, new only when
   `content.strip() == ''`.
6. `tests/test_sqls.py` lines 568-569: `assertGreater(probe_time_s, 0.0)`,
   `assertLess(probe_time_s, 5.0)`; the new `'none'` acceptance branch
   (line 560) asserts `> 0.0`. PASS.
7. `time_solvers.py` line 1 `import functools`, line 574 `dq_herm_q =
   functools.cache(lambda: ...)`; `grep -rn "herm_q_memo\|_memo"` over the
   repo's .py files (venv excluded) is empty. `grep -n csr_matrix
   quantum_tools.py`: line 9 (module top import), 1073, 1157 (uses); no
   function-level import. PASS.
8. Docs. PASS. README line 276 (`fb_cached` row): "every step is counted and
   the column is always False", "while the generated circuit keeps the same
   (qubits, instruction count)", "re-counts with one `[fb] ...` log line",
   "0.36 s for the 12-qubit circuit, 3.0 s for the 14-qubit one", "tested
   and available but not used by the solver path"; README line 106 the
   probe rule "unless `-circ_metrics none`, expose the built circuit".
   TESTING lines 113-119 (hash ~0.4 s / ~3 s, u3cx counts every step,
   u3cx-once (qubits, instruction count) guard), 273-279 (probe bound
   (0, 5 s), `qc` unless `circ_metrics` is `none`, no-`qc` stub accepted
   with `'none'`), 420 (blank first line above data rotates), 472-486
   (default never reuses and never hashes, RY vs RZ separation).

## Regression

- Suite once: `.venv/bin/python -m unittest discover -s tests`: Ran 157
  tests in 197.988 s, OK (skipped=1), 199.56 s process (user 347.10 s),
  2026-10-15T12:37:42Z to 12:41:01Z.
- Gate once: `FVM_GATE_TESTS=1 ... -m unittest tests.test_gate_fixture -v`:
  7/7 ok in 133.588 s (134.67 s process), 12:42:50Z to 12:45:04Z. Printed
  metrics: HHL nelem-5 fidelity 0.999957137763, linsys_residual
  4.206694e-02, hhl_kernel_rel_err 3.399247e-03 (122.05 s); HHL nelem-2
  fidelity 0.999998635611, linsys_residual 3.351933e-03, hhl_kernel_rel_err
  2.550734e-03 (11.47 s); SQLS nelem-5 1.0 / 4.763167e-14 / 3.848910e-15;
  SQLS nelem-2 1.0 / 1.471831e-15 / 1.120025e-15. Same digits as TESTING.
- Hygiene: `git diff 643cba0c..d2e5c6a5 -- '*.py' | grep '^+' | awk 'length
  > 89'`: 0 lines; trailing whitespace on added lines (all 9 files): 0.
- Nothing pushed: `git branch -r --contains d2e5c6a5` empty, no upstream
  configured for the branch. `main` = ef7f0a8b2247615b56e4391fa1804b59825de217,
  untouched. `git status --short` clean, stash empty, reflog shows only the
  two commits after 643cba0c.

## Findings (non-blocking)

- Observed t_count_s 1.47 to 1.48 s per nelem-2 step against TESTING's
  "about 1.1 s each"; the machine was shared with other agents (suite user
  time 1.74x wall), consistent with TESTING's own loaded-machine note. Not a
  defect.
- The `[fb]` re-count line is emitted only when verbosity is nonzero (default
  1); README says "one `[fb] ...` log line" without the verbosity caveat.
  Cosmetic.

## Not checked

- The hash-cost figures (0.36 s at 12 qubits, 3.0 s at 14) were not
  re-measured; the pytest run was not repeated; no nelem-5 solve beyond the
  gate's own; no CLI run exercising a real shape change under `u3cx-once`
  (clock register 13 <-> 14 or `-hhl_deflate_k`), covered in-process only;
  no Frontier, no network.
