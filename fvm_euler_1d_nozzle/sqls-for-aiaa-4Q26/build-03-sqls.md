# Build 03: sqls shots path ported to the Aer-native SamplerV2

Written 2026-10-15T04:33Z by the SQLS-PORT builder (work-plan item 3).

## Status: code done and verified, NOT COMMITTED (blocked by the git-gate hook)

The branch `local/sampler-port-2026-10` exists in
`/Users/agallojr/proj/src/q8020/sqls`, created from `main` @ 9a4346a7 and
checked out. The change sits in its working copy as an uncommitted edit to one
file. `main` was not touched. Nothing was fetched or pushed.

The git-gate PreToolUse hook refused to stage the file. The message was:
"target repo '/Users/agallojr/proj/src/q8020/sqls' is not on the mesh-git
allowlist". The allowlist is `/Users/agallojr/.claude/mesh-git-allowlist.txt`.
That file is permission config, so this agent did not edit it. To finish,
either the operator adds the repo to the allowlist, or the operator stages and
commits `src/sqls/runtime/quantum.py` by hand on that branch. The message is
"Port shots path to qiskit_aer SamplerV2 and add optional seed" plus the
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` trailer. Then run:

```
git -C /Users/agallojr/proj/src/q8020/sqls format-patch main..local/sampler-port-2026-10 -o /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/
```

Because nothing is committed yet, `git format-patch` had nothing to export.
For now, `sqls-patches/` holds a plain diff against `main`. The final
format-patch output will replace it.

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff`
  (4262 bytes, sha256 fbea1c9a048d80e9d806cfea5ffc071c4f179f9a9f7eef7606cfb7ab4a70af77)
- `git apply --check -v` of that diff on a detached worktree of 9a4346a7
  (`/tmp/order2-build-sqls/base`) passed: "Checking patch
  src/sqls/runtime/quantum.py..." with rc 0. The worktree was then removed and
  pruned.

## What changed

The only file changed is `/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`:
19 lines added, 10 removed. Line numbers below are in the new file.

- L209: the lazy import is now `from qiskit_aer.primitives import SamplerV2
  as Sampler`. It used to be `from qiskit_ibm_runtime import SamplerV2`. Run
  `grep -rn qiskit_ibm_runtime src/` and the only hit is
  `src/sqls.egg-info/PKG-INFO`, which is an untracked README copy. Nothing in
  `runtime/quantum.py` matches. The import comment above it (L205-208) was
  updated to match.
- L220: `sampler = Sampler.from_backend(simulator, seed=seed)` replaces
  `Sampler(simulator)`. The comment at L218-219 explains why.
- L43: a new keyword-only parameter `quantum_solve(..., *, seed=None)`. It is
  documented at L69-71 and passed through at L139. `_run_shots` gets
  `seed=None` (L192-193).
- L47-48: the docstring now says "Aer SamplerV2".
- Not changed:
  - `run([qc_meas] * repeats, shots=shots)`
  - the `result[i].data.meas.get_counts()` loop
  - masking and accumulation
  - `restore_sign`
  - the statevector path
  - `examples/potential_flow.py`, which has the real-hardware runtime use.

## How method and device are kept

Source checked: `.venv/lib/python3.12/site-packages/qiskit_aer/primitives/sampler_v2.py`
(qiskit-aer 0.17.2).

- `from_backend(backend, **options)` first runs `cls(**options)`. When
  `backend` is an `AerSimulator`, it then sets `sampler._backend = backend`.
  The sampler uses the caller's simulator object itself, so method, device and
  every other option carry over.
- `_run_pubs` calls `self._backend.run(circuits, shots=shots,
  seed_simulator=self._seed, parameter_binds=..., memory=True)`.
- By contrast, the plain constructor `SamplerV2()` builds a fresh
  `AerSimulator(**backend_options)`, and its method is `automatic`. That is why
  `from_backend` is the right call here and the plain constructor is not.
- The old path, runtime `SamplerV2(mode=AerSimulator)` in local mode, wrapped
  the same simulator object in qiskit's `BackendSamplerV2`
  (`qiskit_ibm_runtime/fake_provider/local_service.py`,
  `_run_backend_primitive_v2`). Old and new both end in
  `simulator.run(circuits, shots=, memory=True)` on the caller's object.

Probe results, from `.venv/bin/python -W error::DeprecationWarning`:

```
statevector -> same object: True method: statevector device: CPU
matrix_product_state -> same object: True method: matrix_product_state device: CPU
plain SamplerV2() method: automatic
statevector executed method: statevector device: CPU   (result.results[0].metadata)
matrix_product_state executed method: matrix_product_state device: CPU
GPU-configured sim: sampler backend device option = GPU same object: True
available devices: ('CPU',)
```

GPU execution was not tested here, because this host only has the CPU device.
From the code: the GPU swap in `quantum_solve` (L95-106,
`make_aer_simulator(gpu=True)`) runs before `_run_shots`. `from_backend` keeps
that object as-is, so `device='GPU'` reaches `backend.run`. The probe confirms
that an `AerSimulator(method='statevector', device='GPU')` keeps
`options.device == 'GPU'` inside the sampler.

## Commands and wall times

All commands ran from `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`
using `.venv/bin/python`. Outputs went under `/tmp/order2-build-sqls/`, which
has since been deleted.

| check | command (abridged) | wall | result |
|---|---|---|---|
| deprecation | `-W error::DeprecationWarning nozzle_1d_solver.py -nelem 2 -time_scheme BDF1 -linsolver SQLS -shots 10000 -sqls_repeats 1 -localdt -cfl 1e10 -iters 2 -initers 1 -noshow -outdir ...` | 1.82 s | rc 0 |
| all warnings | same with `-W always`, grep "warning" | about 2 s | zero warning lines |
| targeted tests | `-m unittest tests.test_sqls tests.test_output_contract -v` | 28.60 s | 41 tests OK |
| full suite (1 run) | `-m unittest discover -s tests -t .` | 48.01 s | 79 tests OK, 1 skipped (pre-existing gate-only `FVM_GATE_TESTS` skip) |
| matched case x3 | `-nelem 5 -time_scheme BDF1 -linsolver SQLS -localdt -shots 150000 -iters 15 -initers 1 -cfl 1e10 -sqls_method full_svd -sqls_repeats 1 -noshow` | 2.04 s, 2.05 s, 1.85 s | converged at iteration 6 in all 3 runs |
| repeats 3 | nelem 2, `-shots 10000 -sqls_repeats 3`, `-W error::DeprecationWarning` | 1.92 s | rc 0; `qc_metadata_sqls_nelem2_full_svd_shots10000.csv` has `repeats` = 3 on both steps; fidelity 0.999979 and 0.999964 |

## Matched case: fidelity per step (3 runs)

Fidelity is the state overlap (dimensionless, 1 = exact), taken from
`hhl_metrics_nelem5_statevector_shots150000.csv`. Each run had 7 steps (0-6).

| step | run1 | run2 | run3 | min | max |
|---|---|---|---|---|---|
| 0 | 0.999966 | 0.999977 | 0.999982 | 0.999966 | 0.999982 |
| 1 | 0.999973 | 0.999980 | 0.999966 | 0.999966 | 0.999980 |
| 2 | 0.999985 | 0.999980 | 0.999977 | 0.999977 | 0.999985 |
| 3 | 0.999984 | 0.999967 | 0.999971 | 0.999967 | 0.999984 |
| 4 | 0.999968 | 0.999981 | 0.999976 | 0.999968 | 0.999981 |
| 5 | 0.999984 | 0.999981 | 0.999982 | 0.999981 | 0.999984 |
| 6 | 0.999993 | 0.999979 | 0.999982 | 0.999979 | 0.999993 |

The lowest value over all 21 steps is 0.9999655, which clears the 0.9999
floor.

For comparison, the same case was run 3 times on the pre-port code. That run
used `PYTHONPATH` pointing at a scratch copy of `src/` with `main`'s
`quantum.py`; the import was checked to resolve there. All 3 converged at
iteration 6. Fidelity ranged from 0.999958 to 0.999992, with mean infidelity
2.34e-5. The ported code gives 0.999966 to 0.999993, with mean infidelity
2.23e-5. For scale, the shot-noise expectation is about (N-1)/(4 x shots) =
15/600000 = 2.5e-5. Both versions sit in that band, so the results are
statistically unchanged.

## Seed demonstration

The test calls `quantum_solve` on a 4x4 SPD system with `full_svd`, 20000 shots
and `AerSimulator(method="statevector")`:

```
seed=123 twice  -> identical: True   [-0.05312295  1.2075981  -1.55424351  0.9091891 ]
seed=None twice -> identical: False  [-0.04337471 ...] vs [-0.04057332 ...]
```

A seed does not make the repeats copies of each other. With
`from_backend(AerSimulator(), seed=5).run([qc]*3, shots=1000)` on a uniform
2-qubit state:
- Each of the 3 PUBs gets a different set of counts, for example
  {00:251, 11:250, 10:241, 01:258} and {00:269, 01:266, 10:222, 11:243}.
- Re-running with the same seed gives identical counts for all 3.

Seeding therefore makes runs reproducible, and the `repeats` average is still
an average over independent draws. fvm does not pass `seed` yet. The default is
None, which keeps the old behaviour: a fresh random seed on every run.

## Open doubts

- The commit and the format-patch are still to do (see the status section).
  Once the commit exists, re-run `git apply --check` on the format-patch file.
  The content is the same as the diff checked above.
- GPU was reasoned from the code only. It was not run on a GPU here.
- The Aer sampler forces `memory=True` and builds counts from per-shot memory.
  The old `BackendSamplerV2` path did the same. The cost of that is linear in
  shots. It was negligible here: the 150000-shot runs took about 2 s wall
  each. It was not measured at 1e6 shots or more.
- The runtime SamplerV2 does not warn on 0.49.0. So the "no new warnings" check
  shows only that nothing new appeared. It starts to matter after the order-2
  re-lock to 0.50.0.

## Fix-up round (2026-10-15T06:22Z)

A code review found that the `qiskit_aer.primitives.SamplerV2` wrapper costs
time and buys nothing. It forces `memory=True` and routes every shot through
Python strings. This round drops the sampler and calls Aer directly. The change
is still uncommitted on `local/sampler-port-2026-10`: the git-gate allowlist
blocker above has not changed. The diff against `main` is now 30 lines added
and 15 removed, all in
`/Users/agallojr/proj/src/q8020/sqls/src/sqls/runtime/quantum.py`.

### What changed (new-file line numbers)

- S1, direct run (L222-228):
  `simulator.run([qc_meas] * repeats, shots=shots, **run_kw).result()`
  - `run_kw` (L226) carries `seed_simulator` only when the seed is not None,
    so a seed already set in the caller's AerSimulator options still applies.
  - The counts loop now reads `result.get_counts(i)` (L237).
  - Unchanged: `repeats` x `shots`, the masking and accumulation, sign
    restoration, and the statevector path.
  - The primitives import is gone. `grep -n "primitives\|qiskit_ibm_runtime"
    src/sqls/runtime/quantum.py` prints nothing (rc 1).
- S2, seed check at entry (L94-100): the seed is converted with
  `int(operator.index(seed))`, and anything that is not an integer raises
  `ValueError("seed must be an integer or None; got ...")`. This happens
  before the classical decomposition. `import operator` is at L11.
  - Probe: `1.5` and `'12'` both raise ValueError. `np.int64(5)` passes.
  - This is stricter than plain `int(seed)`, which would quietly truncate
    `1.5` to 1 and accept the string `'12'`.
- S3, comments: the comment above the run (L222-225) now says what is true.
  - On the CPU path the caller's simulator is used as-is.
  - With `gpu=True`, `quantum_solve` has already rebuilt the simulator from
    `method` alone, so its other options are not carried over.
  - The GPU code itself is unchanged.
  - The docstrings for `mode` and `seed` (L48-49, L70-74) were updated to
    match.

### A/B evidence (old sampler call vs new direct call)

Both calls used the same `AerSimulator(method='statevector')` object and the
same seed.

- 3-qubit `initialize` circuit, `repeats=3`, `shots=20000`, seed 123: the
  three count dicts are **byte-identical** (compared as sorted JSON). The
  counts were:
  - rep 0: {000:81, 001:111, 010:2428, 011:55, 100:1658, 101:788, 110:9687, 111:5192}
  - rep 1: {000:90, 001:91, 010:2459, 011:67, 100:1644, 101:785, 110:9783, 111:5081}
  - rep 2: {000:98, 001:102, 010:2372, 011:52, 100:1668, 101:707, 110:9768, 111:5233}
- 6-qubit `real_amplitudes(6, reps=2)` circuit, 2 x 1e6 shots, seed 7: the
  counts are also byte-identical. Wall time, minimum to maximum over 3 trials
  after a warm-up:

  | call | wall time |
  |---|---|
  | old (SamplerV2) | 0.934 s to 0.997 s |
  | new (direct run) | 0.177 s to 0.181 s |

  The new call is about 5.3 times faster.
- End to end: `quantum_solve` on a 4x4 SPD system with `full_svd`,
  `repeats=3`, `shots=20000` and seed 123. The old tree (loaded through
  `PYTHONPATH`, with the import path checked) and the new tree return an
  identical reconstruction:
  `[-0.055737752639131714, 1.2107917439793627, -1.553208422214751, 0.9064935585238806]`.

### Seed behaviour

- seed=None twice: the counts differ.
- seed=123 twice: the counts are identical.
- Under a fixed seed the 3 repeats differ from each other (see the dicts
  above), because Aer shifts the seed for each experiment.

### Module check (g)

The literal check
`python -c "import sqls.runtime.quantum, sys; print([m for m in sys.modules if 'primitives' in m or 'ibm_runtime' in m])"`
is NOT empty: it lists 28 `qiskit.primitives.*` modules. A bare `import qiskit`
gives the same 28, because `qiskit/__init__.py` L177 imports `primitives`
itself. The same is true of `import qiskit_aer`. So an empty list cannot be
reached, and sqls is not the cause.

What actually matters:
- After an end-to-end shots call, the new code has loaded no
  `qiskit_aer.primitives*` and no `*ibm_runtime*` module.
- The old code, by comparison, also loaded `qiskit_aer.primitives`,
  `.sampler_v2`, `.sampler`, `.estimator` and `.estimator_v2`.

### fvm runs

All runs used `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/bin/python`.
Outputs went to `/tmp/order2-fixup-sqls/`, which has since been deleted.

| check | wall | result |
|---|---|---|
| (c) nelem 2 shots run, `-W error::DeprecationWarning` | 3.46 s | rc 0; zero warning lines with `-W always` |
| (d) `tests.test_sqls tests.test_output_contract` | 33.31 s | 44 tests OK |
| (d) full suite, run once | 47.70 s | 82 tests OK, 1 skipped (gate-only) |
| (e) matched case x3 | 1.61 s, 1.58 s, 1.61 s | converged at iteration 6 in all 3 runs |
| (f) nelem 2, `-sqls_repeats 3 -shots 10000` | 1.43 s | rc 0; `qc_metadata_sqls_nelem2_full_svd_shots10000.csv` has repeats = 3 on steps 0 and 1; fidelity 0.999980 and 0.999975 |

The fvm suite grew from 79 to 82 tests since the first round. fvm `HEAD` is now
1481073c.

### Matched case: fidelity per step (3 runs)

Fidelity is the state overlap (dimensionless, 1 = exact).

| step | run1 | run2 | run3 | min | max |
|---|---|---|---|---|---|
| 0 | 0.999970 | 0.999982 | 0.999951 | 0.999951 | 0.999982 |
| 1 | 0.999980 | 0.999982 | 0.999961 | 0.999961 | 0.999982 |
| 2 | 0.999988 | 0.999977 | 0.999973 | 0.999973 | 0.999988 |
| 3 | 0.999964 | 0.999986 | 0.999991 | 0.999964 | 0.999991 |
| 4 | 0.999985 | 0.999980 | 0.999983 | 0.999980 | 0.999985 |
| 5 | 0.999973 | 0.999971 | 0.999994 | 0.999971 | 0.999994 |
| 6 | 0.999983 | 0.999982 | 0.999982 | 0.999982 | 0.999983 |

Over all 21 steps the lowest fidelity is 0.9999509 and the highest is
0.9999935. Mean infidelity is 2.21e-5, against a shot-noise expectation of
about 2.5e-5.

### Patch

The diff was regenerated from `git -C /Users/agallojr/proj/src/q8020/sqls diff main`:

- `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/sqls-for-aiaa-4Q26/sqls-patches/UNCOMMITTED-sampler-port.diff`
  (5712 bytes, sha256 2d4c5a7c82eaa37228f722d7af33ce931e8412506af0c26d2cfca2494a96d4e9)
- `git apply --check -v` of it on a detached worktree of 9a4346a7 passed with
  rc 0. The worktree was removed and pruned.
