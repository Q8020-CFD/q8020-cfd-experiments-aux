VERDICT: PASS

# verify-09 — independent verification of work item 9 (SQLS zero-pad fix)

- Verifier: independent agent (did not build the change); verified 2026-10-15T03:00Z to 2026-10-15T03:12Z (UTC).
- Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, branch `feature/sqls-aiaa-4q26` (checked out, clean apart from an untracked `tests/` dir belonging to another item).
- Base: `main` @ `ef7f0a8b` ("Add optional SQLS linear solver alongside HHL").
- Item-9 commit: `3a88a37d` "SQLS: pad RHS with zero in convert_to_pow2 to stop fidelity tail collapse" (2026-10-15T02:55:48Z; 1 file, +6/-2, `quantum_tools.py` only).
- Also on the branch (not item 9, not verified here): `d7658f6a` (item 7, `-sqls_k` default/validation).
- Python: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python` (3.12.10, numpy 2.5.2, sqls from `/Users/agallojr/proj/src/q8020/sqls/src/sqls`). Nothing installed.
- All run output went to `/tmp/order1-verify-9/<name>` (deleted after this report was written). `main` comparison used a detached worktree at `/tmp/order1-verify-9/main-wt` (removed).
- Wall times below are from the start/end UTC timestamps around each run (1 s resolution; `/usr/bin/time -p` output files came back empty, so no finer figure). Several runs were launched concurrently, so wall times include some contention.

## The change (read from `git show 3a88a37d`)

`quantum_tools.py`, `QuantumSQLS.solve_one_step`, one call changed:

```
-    A_pow2, b_pow2 = convert_to_pow2(A_o, b_o, verbosity=self.verbosity)
+    A_pow2, b_pow2 = convert_to_pow2(A_o, b_o, verbosity=self.verbosity,
+                                     eps=0.0)
```

plus a 4-line comment explaining the eps-pad dominance. `math_tools.py` is byte-identical on `main` and the branch (`diff` clean), so `convert_to_pow2` itself and `convert_system_to_herm` are unchanged.

## Criterion 1 — SQLS pads b with exactly 0.0; A keeps unit-diagonal pad; HHL unchanged — PASS

Static:
- `grep -n convert_to_pow2 *.py` on the branch: definition `math_tools.py:28` (`eps=1e-8` default unchanged); call sites `quantum_tools.py:562` (HHL `solve_one_step`, no eps kwarg, default 1e-8), `quantum_tools.py:829` (SQLS, `eps=0.0`), `time_solvers.py:520` (HHL classical Hermitian reference, `verbosity=0`, default eps). `nozzle_1d_solver.py:219` is a comment only. So the SQLS path has exactly one `convert_to_pow2` call and it is the one changed; both HHL call sites still use the default eps. `convert_system_to_herm` (HHL only) still carries its own `eps=1e-8` and `+1e-12` offsets.
- Item-7 commit `d7658f6a` touches no `eps`/padding code (grep of its diff: only comments and the `-sqls_k` message mention "padded").

In-process (script run from the repo root with `PYTHONPATH=<repo>`; wrapped `quantum_tools.convert_to_pow2` with a spy, then called `QuantumSQLS(backend_type='ideal', method='full_svd', nshots=0 and 150000).solve_one_step(A, b)` on the August collapse-step system `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/system_Ab_nelem5_iter6.pkl`, read-only):

| quantity | observed |
|---|---|
| system | A 15x15, ‖b‖ = 1.260379e-09, ‖dq_LU‖ = 7.353945e-11 |
| eps kwarg passed by SQLS path | `0.0` (both statevector and shots calls) |
| N padded / npad | 16 / 1 |
| `b_pow2[15:]` | `array([0.])` — all pad entries `== 0.0` exactly |
| `b_pow2[:15] == b` | True (exact) |
| `diag(A_pow2)[15:]` | `array([1.])`; pad off-diagonal blocks all 0 |
| statevector result vs LU | fidelity 1.000000000000, max abs diff 1.292e-25, ‖Ax−b‖ = 2.329e-24 |
| 150000-shot result vs LU | fidelity 0.999974 (the same system gave 0.451 in August and 0.753 on `main` today) |

Pad-dominance arithmetic on that system (classical solve of the padded system):

| eps | ‖x_pow2‖ | x_pad | prob. mass on pad entry | expected real-solution shots of 150000 |
|---|---|---|---|---|
| 1e-8 (main) | 1.0000e-08 | 1e-08 | 0.999946 | 8.1 |
| 0.0 (branch) | 7.3539e-11 | 0.0 | 0.000000 | 150000.0 |

This reproduces the "~8 of 150000 shots" root cause stated in the work item exactly.

HHL path not executed (out of scope per the brief); its unchanged call sites were verified by reading the branch files and the `main..HEAD` diff.

## Criterion 2 — Rung 3 statevector at nelem 2 and 5 — PASS

Commands (run from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, `PY=.venv/bin/python`):

```
$PY nozzle_1d_solver.py -nelem 2 -linsolver SQLS -shots 0 -sqls_method full_svd -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir /tmp/order1-verify-9/c2-SQLS-nelem2
$PY nozzle_1d_solver.py -nelem 5 -linsolver SQLS -shots 0 -sqls_method full_svd -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir /tmp/order1-verify-9/c2-SQLS-nelem5
$PY nozzle_1d_solver.py -nelem 2 -linsolver LU -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir /tmp/order1-verify-9/c2-LU-nelem2
$PY nozzle_1d_solver.py -nelem 5 -linsolver LU -time_scheme BDF1 -localdt -cfl 1e10 -iters 3 -initers 1 -noshow -outdir /tmp/order1-verify-9/c2-LU-nelem5
```

All four: exit 0, no exception. Wall: SQLS nelem 2 ≈ 2 s (started 03:03:54Z), SQLS nelem 5 ≈ 2 s (03:03:56Z), LU nelem 2 ≈ 1 s, LU nelem 5 ≈ 1 s. Per-solve SQLS time 0.07 to 0.08 s.

`hhl_metrics_nelem{2,5}_statevector.csv` (bounds: fidelity ≥ 0.999999, linsys_residual ≤ 1e-12):

| nelem | step | fidelity | linsys_residual | result |
|---|---|---|---|---|
| 2 | 0 | 1.000000000000000 | 1.472e-15 | ok |
| 2 | 1 | 1.000000000000000 | 6.225e-17 | ok |
| 2 | 2 | 1.000000000000000 | 3.329e-19 | ok |
| 5 | 0 | 1.000000000000000 | 4.763e-14 | ok |
| 5 | 1 | 1.000000000000000 | 2.843e-15 | ok |
| 5 | 2 | 1.000000000000000 | 2.135e-16 | ok |

`dq_nelem{2,5}_iter{0,1,2}_statevector.csv`, max |dq_lu − dq_sqls| per step (bound 1e-12 abs):

| nelem | iter 0 | iter 1 | iter 2 | worst |
|---|---|---|---|---|
| 2 | 3.053e-16 (‖dq‖ 5.44e-01) | 2.776e-17 (‖dq‖ 1.24e-02) | 5.082e-20 (‖dq‖ 1.21e-04) | 3.053e-16 ok |
| 5 | 1.998e-15 (‖dq‖ 2.71e+00) | 1.249e-16 (‖dq‖ 1.67e-01) | 1.388e-17 (‖dq‖ 2.41e-02) | 1.998e-15 ok |

Final `residual_total` (last row of `residual_*.csv`, i.e. after 3 Newton iterations), SQLS vs LU:

| nelem | SQLS | LU | abs diff | rel diff | bound | result |
|---|---|---|---|---|---|---|
| 2 | 1.326330532423768e-04 | 1.326331354331326e-04 | 8.219e-11 | 6.197e-07 | 1e-10 abs | ok |
| 5 | 5.832885640886122e-02 | 5.832886414347176e-02 | 7.735e-09 | 1.326e-07 | 1e-6 rel | ok |

Note the nelem 2 abs diff (8.2e-11) sits at 82 % of its 1e-10 bound; the nelem 5 relative diff is 1.3e-7, well inside 1e-6. `final_results` SQLS vs LU max abs diff: 3.362e-12 (nelem 2), 4.730e-10 (nelem 5). The residual_total differences arise from roundoff-level dq differences (1e-15 to 1e-16) amplified by the finite-difference Jacobian, as the brief anticipated.

## Criterion 3 — matched 150000-shot case, 3 runs on branch + 1 on main — PASS

Command (identical on branch and on the `main` worktree, run from each tree's root):

```
$PY nozzle_1d_solver.py -nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow -outdir /tmp/order1-verify-9/c3-<branch-matched-rN | main-matched>
```

All four runs: exit 0, 7 linear solves (iter indices 0..6), Newton loop exited before the 15-iteration cap (stop test at `time_solvers.py:389-391`: resconv ≤ 1e-10, or all component residuals ≤ 1e-10, or any ‖dQ_var‖ ≤ 1e-10). Wall ≈ 2 s, 3 s, 2 s (branch r1 03:04:01Z, r2 03:04:03Z, r3 03:04:06Z) and 3 s (main, 03:04:08Z). Branch banner `SQLS: N=16 (padded), k=8, method=full_svd, mode=shots`; main banner `k=128` (item-7 default change; `full_svd` does not use k, so inert here).

Per-iteration fidelity (`hhl_metrics_nelem5_statevector_shots150000.csv`), AFTER (branch) and BEFORE (main):

| iter | branch r1 | branch r2 | branch r3 | main (before) | August trial_0 |
|---|---|---|---|---|---|
| 0 | 0.9999822007 | 0.9999798095 | 0.9999901576 | 0.9999694742 | 0.9999813469 |
| 1 | 0.9999740780 | 0.9999887506 | 0.9999692040 | 0.9999786872 | 0.9999646110 |
| 2 | 0.9999707490 | 0.9999803071 | 0.9999546030 | 0.9999866242 | 0.9999664761 |
| 3 | 0.9999807196 | 0.9999752381 | 0.9999679894 | 0.9999700610 | 0.9999793702 |
| 4 | 0.9999785758 | 0.9999808621 | 0.9999916720 | 0.9999757405 | 0.9999680223 |
| 5 | 0.9999810869 | 0.9999745297 | 0.9999795091 | 0.9999282407 | 0.9999540551 |
| 6 (final) | **0.9999597164** | **0.9999778155** | **0.9999911959** | **0.7532451747** | 0.4510250083 |

- Branch final-iteration fidelity over 3 runs: min 0.9999597164, max 0.9999911959 (bound ≥ 0.99). Every non-final iteration ≥ 0.9999546 (bound ≥ 0.999).
- `main` final-iteration fidelity 0.7532 (fails the ≥ 0.99 bound, as expected for the unfixed code; the August value was 0.451 — shots are unseeded, so the collapse depth varies run to run, but both are far below any branch run).
- Final iteration linsys_residual: branch 6.75e-12 / 4.76e-12 / 1.88e-12 vs main 7.78e-10. Final iteration l2_error_abs: branch 2.8e-13 / 2.0e-13 / 1.1e-13 vs main 5.3e-11 (‖dq‖ ≈ 7e-11, i.e. main's final dq was mostly wrong in magnitude too).

Final `residual_total` (last row of `residual_nelem5_SQLS_statevector_nshots150000.csv`, bound ≤ 5e-9): branch 1.278316e-09, 8.200665e-10, 1.066014e-09 — all ok. (main: 2.646333e-09; August: 1.260379e-09.)

## Criterion 4 — final_results vs August reference (1e-6 abs) — PASS

Reference (read-only): `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/final_results_nelem5_SQLS_statevector_nshots150000.csv`. Same xp grid (0.1 … 0.9), columns `xp, rho, u, p, Mach`.

| run | max abs diff rho | u | p | Mach | result |
|---|---|---|---|---|---|
| branch r1 | 1.894e-11 | 6.855e-11 | 2.436e-11 | 1.647e-10 | ok |
| branch r2 | 1.882e-11 | 6.942e-11 | 2.452e-11 | 1.660e-10 | ok |
| branch r3 | 1.883e-11 | 6.918e-11 | 2.447e-11 | 1.656e-10 | ok |
| main (today) | 2.752e-11 | 1.305e-10 | 4.621e-11 | 3.103e-10 | ok |

All four orders of magnitude inside the 1e-6 bound. The converged flow field is unchanged by the fix (as it should be: the fix only changes the quality of the final, already-tiny update).

## Criterion 5 — committed on the feature branch, nothing pushed — PASS

- `git branch --contains 3a88a37d` → `* feature/sqls-aiaa-4q26` only; `main` does not contain it.
- `git branch -r` lists `origin/HEAD, origin/archive-*, origin/backup-old-main, origin/bloqade-test, origin/feature/qiskit-hhl, origin/main` — no `origin/feature/sqls-aiaa-4q26`.
- `git diff HEAD -- quantum_tools.py` is empty: the file I ran is the committed file. `git status --short` shows only `?? tests/` (another item's untracked work).

## Additional findings

1. **Zero RHS now raises instead of silently returning garbage.** `sqls.SQLS` checks `if float(np.linalg.norm(b)) == 0: raise ValueError("b is the zero vector; ...")` (`/Users/agallojr/proj/src/q8020/sqls/src/sqls/sqls.py:176-178`). `QuantumSQLS.solve_one_step` has no guard, so with `eps=0.0` a zero b propagates that `ValueError` and kills the run (confirmed in-process: `ValueError: b is the zero vector; the SQLS target state is undefined.`). On `main` the same zero b became ‖b_pow2‖ = 1e-8 and sqls would have "solved" a pad-only system and returned a bogus dq without complaint. The new behaviour is the safer one. Reachability: b is the unsteady residual; an exactly-zero b requires an exactly converged state in floating point, and the Newton loop stops on resconv ≤ 1e-10 / ‖dQ‖ ≤ 1e-10 well before that (the collapse-step b has ‖b‖ = 1.26e-9). The LU reference path would also produce dq_lu = 0 and a NaN fidelity in that case, so this is not a new failure surface. Not blocking; a one-line early return of zeros when ‖b‖ == 0 would be a cheap hardening if desired.
2. **No downstream code assumes the pad entry is nonzero.** Checked: `x = np.asarray(x_pow2)[:nsys].real` truncates before anything else (`quantum_tools.py:862`); sign alignment `np.dot(dq_sqls, dq_lu) < 0` and `fidelity()` operate on the truncated vectors (`time_solvers.py:643-652`); in sqls `_run_shots` the sign restore `np.where(final_b.real < 0, -1, 1)` gives +1 at a zero pad entry whose reconstructed amplitude is 0 anyway, and `target_norm = norm(final_b)` now equals ‖dq‖ exactly rather than sqrt(‖dq‖² + npad·eps²) — so the magnitude is also now exact (main's final-step l2_error_abs 5.3e-11 on ‖dq‖ 7e-11 was partly this). `_run_statevector`'s phase removal uses `argmax(|sv|)`, unaffected.
3. **Fix is applied in exactly one place and that is the only SQLS-path call.** See criterion 1 static check. Both HHL call sites keep the default eps.
4. **Diff hygiene: clean.** Added lines are ≤ 75 chars, no trailing whitespace, follow the file's existing 2-space indent convention. The file's 2 lines over 88 chars (`quantum_tools.py:41` 89 chars, `:80` 93 chars) pre-date the branch (blame 2025-10-31). Comment accuracy nit: "dominates the sampled state once ||dq|| < ~eps" is exact for npad = 1 (nelem 5); in general the crossover is ‖dq‖ ≈ sqrt(npad)·eps (nelem 2 has npad = 2). Harmless.
5. **Pre-existing latent bug in `convert_to_pow2` (not item 9, not reachable here).** The entire padding body, including the `return A_padded, B_padded`, is inside `if nsys_nxtpower-nsys > 0:` with no `else` (`math_tools.py:37-87`), so when N is already a power of 2 the function returns `None` (confirmed with a 4x4 system: `TypeError: cannot unpack non-iterable NoneType object`). N = 3·nelem is never a power of 2, so the nozzle solver cannot hit it; worth a follow-up ticket if `convert_to_pow2` is ever reused for a different unknown count.
6. **Before/after at the collapse step is reproducible in isolation.** Feeding the saved August `system_Ab_nelem5_iter6.pkl` to the branch `QuantumSQLS` with 150000 shots gives fidelity 0.999974; the eps=1e-8 arithmetic predicts 8.1 real-solution shots of 150000 (matches the work item's "~8 of 150000").

## Not checked, and why

- **HHL path by execution.** The brief excludes HHL runs; the HHL call sites were verified unchanged by reading (`quantum_tools.py:562`, `time_solvers.py:520`, `main..HEAD` diff). No in-process HHL instantiation was attempted either.
- **`truncated_qr` / `truncated_mps` with the zero pad.** Only `full_svd` is in the criteria and only `full_svd` was run. The zero pad flows into `U_k^H b` for the truncated methods and sqls has its own alpha-zero guard (`sqls.py:200-204`), so nothing suggests a problem, but it is unexercised.
- **Shots mode at nelem 2 (npad = 2).** Criterion 2 only required statevector at nelem 2, where two exact-zero pad amplitudes went through `Initialize` without issue; the shots path at npad > 1 was not run.
- **Precise wall times.** `/usr/bin/time -p` output files were empty on re-read; wall times are from 1 s-resolution timestamps and several runs overlapped. All were under 10 s each regardless.
- **Padded-system save path.** The solver pickles the original A, b (`system_Ab_*.pkl`), not the padded system, so criterion 1 was verified by in-process instrumentation rather than from saved files.
