# SQLS for the AIAA 2027 QCFD paper — work plan (4Q26)

Created 2026-10-14 (UTC). Owner: Andy Gallo. Status: open, more items will be
added.

## Goal

The AIAA 2027 abstract (`~/Desktop/AIAA27_QCFD_Abstract.pdf`, Alhawwary, Gallo,
Lu, Gottiparthi, Gopalakrishnan Meena) benchmarks HHL and LuGo-HHL on the 1D
supersonic nozzle and promises, for the final paper, a third QLSA: the
SVD-based solver (refs 13 to 15). ORNL's packaging of that solver is `sqls`,
and it was wired into `fvm_euler_1d_solver` on 2026-08-17 as `-linsolver SQLS`.
This plan takes that integration from a one-trial laptop validation to
paper-grade results produced under the same protocol as the HHL and LuGo
cases (10 trials, shot sweep, CFL sweep, mesh scaling), run through our
sweeper with metadata captured by metautil.

We do not have the LuGo library (contact-gated at ORNL); LuGo columns in the
paper stay as ORNL-produced results. Nothing here depends on LuGo.

## Work items

Pri: H = must land before any paper run or gates one that must; M = needed before the Frontier campaign but not blocking the laptop smoke; L = not a paper dependency.

Order: execution order; items sharing a number run in parallel; blank = not yet scheduled; done = finished analysis.

| # | Pri | Order | Item | Deliverable in this folder | Status |
|---|-----|-------|------|----------------------------|--------|
| 1 | H | done | Analysis of what was done in August 2026 | `01-august-2026-analysis.md` | done |
| 2 | H | done | Identify the code: fvm solver and sqls; diagnose the broken sqls git link. Finding: the link is a server-side intermittent HTTP 504 on `olcf-qcfd/sqls.git` (20 s Azure gateway timeout, repo-specific; sibling repos answer), not auth. Decision 2026-10-15: treat our sqls as DETACHED from the cloud source (see Decisions). | `02-code-inventory.md` | done |
| 3 | H | 2 | Upgrade the stack and test it; solverfw usage analysis (analysis only, no solverfw changes). Finding: qiskit 2.5.2 and qiskit-aer 0.17.2 are already the latest stable releases, so the upgrade is qiskit-ibm-runtime 0.49.0 -> 0.50.0 (decided 2026-10-15, see Decisions). 0.50.0 deprecates SamplerV2/EstimatorV2 and adds a hard dep on qiskit-mitigation. Port work: replace the SamplerV2 shot-mode path in fvm `quantum_tools.py` (imports at L11, use at L492) and in sqls `src/sqls/runtime/quantum.py` (L202, L211) with `qiskit_aer.primitives.SamplerV2` (Aer-native, no runtime dependency for simulator runs) and keep the runtime Sampler only for real-backend paths. Re-lock, re-sync, reinstall sqls editable, run the test ladder (sec. 5 of the report); rollback recipe in sec. 4. | `03-qiskit-upgrade-and-solverfw.md` (analysis, done); pin bump + port in `fvm_euler_1d_solver` and in our sqls clone | done (order 2, 2026-10-15; runtime 0.50.0 locked; shots run directly on AerSimulator in fvm and in the sqls clone (uncommitted, patch in `sqls-patches/`), optional seed; ladder green on the new stack incl. three matched-HHL runs; verifier FAIL on a miscalibrated threshold -> re-specified -> re-verifier PASS) |
| 4 | H | done | Validate that sqls is woven into the fvm code | `04-sqls-wiring-validation.md` | done (no blockers; findings -> items 7, 9, 10, 11) |
| 5 | H | done | Validate how sweeps will run: past invocation, future invocation via `q8020-sweep`, metadata via metautil | `05-sweep-mechanism.md` + `fvm_sqls_aiaa_sweeps.DRAFT.toml` (parses; dry-run expands to 1 smoke + 145 cases) | done; open questions in sec. 3g of the report and below |
| 6 | M | 3 | Hybrid SVD-prepared HHL: use SVD information to prepare A x = b, then solve with the existing fvm HHL path. Design in `06-svd-priming-hhl.md`; numbers on the archived Jacobians and the recommended shifted-deflation form in `06a-deflation-numbers-and-recommendation.md` (CFL 1e10, k = 2: kappa 68 -> 15, clock register 8 -> 7 qubits, ~13x fewer post-selected shots, 35 % of ||x||^2 classical; no gain at CFL <= 10). Candidate paper row, labeled as classical deflation + HHL, no speedup claim. | `06-svd-priming-hhl.md`, `06a-deflation-numbers-and-recommendation.md`, `kappa_eff_deflation_check.py` | done (order 3, 2026-10-15; fvm 484b24ed..d2e5c6a5 incl. three fix-up rounds; dry check reproduced through the new module; nelem-5 k = 2: clock 8 -> 7, CX 2,054,602 -> 1,022,314, x-share 0.92 at iteration 0, kernel rel. error 3.4e-3 -> 5.7e-3; verifier + reproducer PASS; qc-skeptic lens: OVERSTATED on the steady-case numbers, see STATUS.md) |
| 7 | H | 1 | Fix the latent `-sqls_k` CLI bug: the default of 128 is invalid at N = 16 (must be a power of two with 2 <= k < N, so 2, 4, or 8 at nelem 5); it bites as soon as anyone tries `truncated_qr` or `truncated_mps` (argparse default in `nozzle_1d_solver.py`; the error surfaces inside sqls). Make the default derive from N (e.g. N/2) or validate early with a clear message. Also from item 4: when `backend_type != 'ideal'` the ValueError raised at SQLS init is swallowed and the user later sees a misleading "install sqls" error; fail fast with the real message. Found by items 1 and 4. | code change in `fvm_euler_1d_solver`; detail in `04-sqls-wiring-validation.md` | done (order 1, 2026-10-15; fvm `feature/sqls-aiaa-4q26` d7658f6a + fix-up 71c02aed; verifier PASS, see STATUS.md) |
| 8 | H | 1 | Author specific smoke tests for the fvm Euler solver. The repo has no tests at all today. Target: a `tests/` module runnable with pytest from the fvm venv, each test well under 60 s, covering (a) classical LU and GMRES baseline at nelem 2 to 3 (residual drop, conservation sanity), (b) SQLS statevector (`-shots 0`) at nelem 2 to 5 against the LU update per step, (c) SQLS shots mode small-N sign and magnitude recovery, (d) HHL statevector at nelem 2 (tiny circuit) for the existing path, (e) CLI argument validation including the `-sqls_k` check from item 7, (f) output-file and metadata schema checks so the harvester contract is pinned. Builds on the test ladder in `03-qiskit-upgrade-and-solverfw.md`; also the regression gate for the qiskit upgrade (item 3). | `tests/` in `fvm_euler_1d_solver` + a short `TESTING.md` recipe | done (order 1, 2026-10-15; fvm 5af4dd2f + fix-up f16720b3; 79 tests, 46 s; gate fixture 7/7, 93 s; verifier PASS) |
| 9 | H | 1 | Fix the fidelity tail collapse at the converged step (0.451 at step 6 in the August trial). Root cause found by item 4: `convert_to_pow2` pads the right-hand side with a constant eps = 1e-8 (`math_tools.py:62-66`). Once the true update falls below that (||dq|| = 7.35e-11 at step 6) the dummy padded unknown dominates the sampled state and only ~8 of 150000 shots land on the real solution. Fix: pad with 0.0 on the SQLS path (HHL keeps its own treatment unless shown equivalent). Verify with a `-shots 0` and a 150k-shot rerun of the matched case. Must land BEFORE any shots sweep. | code change in `fvm_euler_1d_solver`; detail in `04-sqls-wiring-validation.md` sec. 6 | done (order 1, 2026-10-15; fvm 3a88a37d; verifier PASS + reproducer confirmed; final-step fidelity 0.99996 to 0.99999 vs 0.451) |
| 10 | H | 1 | Make the harvester SQLS-aware. Filename globs already match SQLS output, but the column mapping is HHL-only: SQLS columns (method, k, repeats, cx_count, circuit_depth, solve_time) are dropped, HHL-only fields come out as 0 (transpile_passes, circuit_timing_total_s, matrix_size_hermitian), and the stdout parser needs an "HHL sol" header. Also fix the `converged` test, which compares an absolute residual to a ratio tolerance (the SQLS run was marked unconverged) and rounds residual_reduction to 0.0. Then re-harvest `2026-08-17-sqls-local-v2/trial_0` so it carries the same six fragments as the HHL trials. | change to `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`; detail in `04-sqls-wiring-validation.md` sec. 4 | done (order 1, 2026-10-15; uncommitted in experiments for Andy; six fragments written to the August SQLS trial; verifier PASS) |
| 11 | H | 3 | Benchmark-fairness fixes before paper numbers are produced. (a) The SQLS path runs a classical LU solve every Newton step solely to fix the global sign in statevector mode (`time_solvers.py:630,640`); replace with a reference-free rule (pick the sign minimizing ||Ax - b||) so the quantum path does not depend on the classical answer. (b) Circuit metrics use different bases: SQLS counts {u3, cx} via `count_cx_depth` (only at `-v 2`), HHL counts all gates after an Aer-basis transpile; add one shared fixed-basis counter applied to both circuits and report that in the paper. (c) Record effective shots (shots x repeats) in the metadata so the 10x repeats trap cannot recur. (d) Correct two statements in `../sqls-vs-hhl-2026-08-17/README.md`: HHL hit the 15-iteration cap (ratio 5.5e-4), it did not converge in 14; and the "||Ax-b||" row quotes the CFD residual_total, the linear-system residuals are 1.228e-9 (SQLS) vs 3.725e-3 (HHL). | code changes in `fvm_euler_1d_solver`; README edit; detail in `04-sqls-wiring-validation.md` sec. 5 to 6 | done (order 3, 2026-10-15; fvm e13cbb1e..484b24ed + fix-ups; reference-free sign, shared {u3,cx} counter (HHL / SQLS CX ratio 10,273x at nelem 5), effective_shots, -seed, explicit -hhl_scale leastsq, README corrections; verifier + reproducer PASS) |
| 12 | H | 2 | Make the sqls detachment real in the build. Replace the `[sqls]` extra's `git+https://code.ornl.gov/olcf-qcfd/sqls.git` URL with a local path source (`[tool.uv.sources] sqls = { path = "../sqls", editable = true }`, or drop the extra and document the `uv pip install -e ../sqls --no-deps` step), re-run `uv lock` so `uv sync` never touches the network, and record the sqls commit of record (9a4346a7, 2026-06-30, Chao Lu) in README and in every run's metadata (code fragment). Any fix we make to sqls (SamplerV2 port, zero pad if it lands there) becomes a commit on a branch of our local clone, kept as a patch list for later hand-off to ORNL. Precondition for Frontier: the clone must be copied there too. | pyproject/uv.lock change in `fvm_euler_1d_solver`; branch in `~/proj/src/q8020/sqls`; README | done (order 2, 2026-10-15; path sources + bare names, lock has no git source, commits of record in README and every run's `code_versions` incl. `diff_sha256`; sqls patch in `sqls-patches/`; verifier FAIL -> fixed -> re-verifier PASS) |
| 13 | H | 1 | Fix the stale harvester path in the sweep configs. The April 2026-04-08 and 2026-04-10 CFL sweeps LOST all solver-side fragments because `_case_postproc` pointed at `codes/fvm_euler_1d_nozzle/...`, which had moved; the same stale path is still in `aux/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`, `fvm_euler_1d_nozzle.toml` and `harvest_lugo_all.sh`. Point them at `aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py` (the draft TOML already does) and consider re-harvesting the two April sweeps from the raw CSVs still in `results/`. Also restore an `examples/fvm_1d_smoke_test.toml` in metautil (deleted 2026-07-15; only copy is in the 2026-04-05 results dir). | edits in `q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/`; metautil example | done (order 1, 2026-10-15; uncommitted path fixes in experiments and in metautil `tests/examples/*.toml`; premise correction: 46fa917 MOVED the smoke test, no duplicate added; April re-harvest ready, Andy's call; verifier PASS) |
| 14 | M | 3 | Sweeper housekeeping before the SQLS runs: `q8020-sweep` is not on PATH, it lives in `q8020-cfd-metautil/.venv/bin/` (use that one); all three editable installs point at the checkout on `feature/solverfw-v2` @ 753b97e (4 commits ahead of `main` 8ccab91), decide which branch runs the paper sweeps; the README's `--groups` flag is stale (groups are positional, `_`-prefixed groups run only when named); log the full `q8020-sweep` command line into the sweep meta (it was never recorded in April and had to be reconstructed). | metautil README/sweep.py change; branch decision | done (order 3, 2026-10-15; uncommitted in metautil: README, sweep.py provenance + dry-run hygiene + UTC date dir + venv fallback; branch recommendation in build-14.md; verifier PASS) |
| 15 | H | 2 | Port the HHL library off the Qiskit 3.0 removals. Our fork `Q8020-CFD/quantum_linear_solvers` @ 66eadf0 (import name `linear_solvers`) uses PhaseEstimation, ExactReciprocal, PiecewiseChebyshev and BlueprintCircuit, all deprecated in qiskit 2.1/2.2 and removed in 3.0; four DeprecationWarnings fire on import today. Neither jw676 (we are 2 ahead, 0 behind) nor the anedumla upstream (diverged: 26 ahead, 11 behind, their 11 are packaging/CI and they are still on qiskit 1.x) has done this, so it is ours. Targets: `phase_estimation()` function, `ExactReciprocalGate`, `PiecewiseChebyshevGate`, a plain QuantumCircuit base for `LinearSystemMatrix`. Pulled into phase 1 on 2026-10-15 so every HHL number in the paper comes from one code state; gate is an HHL statevector solve on the archived 15 x 15 systems reproducing the pre-port solution to 1e-10 (smoke test, item 8). Circuit metrics will shift and are re-recorded. Keep the phase-estimation slot a clean seam for a future LuGo plug-in. | branch + commit on `Q8020-CFD/quantum_linear_solvers`, picked up by the order-2 re-lock | done (order 2, 2026-10-15; COMMITTED 2026-10-16 as five commits on the fork branch `feature/sqls-aiaa-4q26` (renamed from `feature/qiskit3-api-port` on 2026-10-16 to match the fvm branch), tip 9d1d7bb over main 66eadf0, pushed to origin at Andy's request; patch series in `fork-patches/0001..0005`; zero deprecation warnings; 1e-10 gate reproduced; verifier + re-verifier PASS) |
| 16 | H | 4 | Specify the test-case set and handoff package for Ishan. Contents: (a) the final sweep TOML derived from `fvm_sqls_aiaa_sweeps.DRAFT.toml` with the open questions answered (trials, methods, HHL control, `-hhl_deflate_k` groups from item 6); (b) a Frontier environment recipe: fvm venv on the item 3 stack, sqls from the local clone at the commit of record (item 12), metautil venv and branch (item 14), harvester path (item 13); (c) the exact `q8020-sweep` command lines per group with expected per-case wall time and node count; (d) acceptance criteria per group (residual, fidelity, L2 vs LU) taken from the smoke tests of item 8 and the August numbers; (e) what to copy back into `results/fvm_euler_1d_solver/<date>-sqls-frontier/` and how to run the harvest; (f) a short results-reporting template. | `HANDOFF-ishan.md` + final TOML in this folder | open |
| 17+ | | | (to be added) | | |

A consolidated findings summary is appended at the bottom of this file once
items 1 to 5 report.

## Item 6 — two points to check before anyone implements deflation

- The HHL library computes κ and the smallest eigenvalue from the full matrix.
  The reduced values have to be passed in, or deflation saves nothing.
- Deflation has to be applied to the original A and b, before the HHL path's
  rescaling and symmetric doubling.

Detail in `06-svd-priming-hhl.md`, section "2. Deflate the smallest singular
modes", under Caveats.

## Known facts going in (verified 2026-10-14)

- Paper results live in
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/`:
  shot study `2025-11-11/shots_*` (Frontier, qiskit 1.2.4), CFL sweep
  `2026-04-05/_52d087d1/time_steps_{0..4}` (Frontier, qiskit 2.3.1), LuGo
  `2026-02-2{4,6}-LuGo` (ORNL-run on Frontier). SQLS so far: one laptop trial,
  `2026-08-17-sqls-local-v2/trial_0`, written up in
  `../sqls-vs-hhl-2026-08-17/README.md`.
- fvm solver: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, remote
  `Q8020-CFD/fvm_euler_1d_solver` (private fork of `mhawwary/fvm_euler_1d_solver`),
  `main` @ `ef7f0a8b` "Add optional SQLS linear solver alongside HHL"
  (2026-08-17T23:22:59Z, Andy Gallo, Claude Opus 4.8 co-author), local == origin.
  Stack pinned: qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.49.0,
  `quantum_linear_solvers` @ Q8020-CFD fork `66eadf0`.
- sqls: `/Users/agallojr/proj/src/q8020/sqls`, remote
  `https://code.ornl.gov/olcf-qcfd/sqls.git`, local HEAD `9a4346a7`, clean.
  Installed editable into the fvm venv (`.pth` -> `.../q8020/sqls/src`). The
  pyproject `[sqls]` extra points at the same URL. On 2026-10-14 a
  `git ls-remote` of that URL returned HTTP 504 while sibling repos
  (`olcf-qcfd/lugo_benchmarking`, `olcf-qcfd/qlsa`) answered, and the group
  API still lists `olcf-qcfd/sqls`. Diagnosis is item 2.
- HHL fork: fresh clone of `Q8020-CFD/quantum_linear_solvers` at
  `/Users/agallojr/proj/src/q8020/quantum_linear_solvers` (made 2026-10-15,
  main @ 66eadf0, the commit fvm locks). The old Z-Keep checkout is left alone.
- fvm `main` carries only a stale `src/__pycache__` from the solverfw v2 port;
  the port itself lives on `archive/solverfw-v2-port`. Whether anything on
  `main` imports solverfw is item 3.
- Sweeper: `q8020-sweep` from `/Users/agallojr/proj/src/q8020/q8020-cfd-metautil`
  (`q8020_cfd_metautil.sweep:main`), harvester
  `q8020_cfd_metautil.harvest`. The April CFL sweep ran on Frontier from
  `q8020-cfd-experiments/input/cases/fvm_euler_1d_nozzle/fvm_cfl_sweeps.toml`
  with per-case postproc
  `codes/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py`; both files
  now sit under `aux/fvm_euler_1d_nozzle/` (repo reorganized since).
- The August SQLS trial directory has NO `q8020_*.json` fragments, so either
  the harvester was not run on it or it does not recognize SQLS output. Item 4
  and item 5 check this.

## Execution order (agreed 2026-10-15)

Andy's three phases, mapped onto the items. Items with the same order number
run in parallel; each order is gated by the one before it.

| Order | Phase | Items | Gate to pass before the next order |
|-------|-------|-------|------------------------------------|
| 1 | Phase 1 prep: correctness and tooling fixes on the CURRENT stack, in parallel | 7 (`-sqls_k` + early error), 8 (smoke tests, baseline on qiskit 2.5.2 / runtime 0.49.0), 9 (zero pad), 10 (SQLS-aware harvester), 13 (stale harvester path) | Smoke tests green on the current stack; harvester produces the six fragments for the August SQLS trial |
| 2 | Phase 1 upgrade: one re-lock | 15 (HHL fork off the deprecated APIs, in its own repo) + 12 (sqls as local path source, commit of record) + 3 (runtime 0.50.0 bump, SamplerV2 port in fvm and in our sqls clone); then a single `uv lock` picks up the new fork commit, the sqls path and the runtime pin together | Same smoke tests green on the new stack; `uv sync` touches no network; zero deprecation warnings on import; HHL statevector solution on the archived systems unchanged to 1e-10 |
| 3 | Phase 2 build: hybrid switches and fairness, in parallel | 6 (`-hhl_deflate_k`, shifted deflation around the unchanged HHL path, metadata columns), 11 (reference-free sign, shared circuit-count basis, effective shots, README corrections), 14 (sweeper housekeeping) | Smoke tests extended for the new flags and green; classical dry check of deflation on archived Jacobians reproduced by the new code path |
| 4 | Phase 3 handoff | 16 (test-case set, Frontier recipe, commands, acceptance criteria, copy-back and harvest procedure) | Andy approves the TOML; Ishan can run the `_smoke` group end to end on Frontier |

## Execution pod (phases 1 and 2) — how the work is run

- **Orchestrator (Fable)** assigns items, keeps this file's Status column and
  `STATUS.md` current, gates each order, runs the code-review skill on the
  combined diff at each gate, and writes no code itself.
- **Builder** per item: implements, gets its own unit tests green, writes
  `build-<item>.md` (what changed, commands run with wall times, open doubts).
  Opus 5.5 for the crisply specified items (7, 9, 10, 13, the SamplerV2 port
  in 3); Fable for the judgment-heavy ones (15, 6, 11).
- **Verifier** per item, always a different agent from the builder, always
  Fable, spawned with only the item text, the acceptance criteria, and the repo
  path (never the builder's narrative). Reads the diff, runs the tests itself,
  tries to break the change, writes `verify-<item>.md` with PASS/FAIL and
  evidence. Builders cannot close their own items.
- **Reproducer** for numerical items (9, 6, 11): recomputes the claimed
  numbers from artifacts independently, as `kappa_eff_deflation_check.py` did.
- **One builder per repo at a time.** Order 1: fvm fixes (7, 9) | fvm tests
  (8, new files only) | experiments harvester + paths (10, 13). Order 2: fork
  port (15) | sqls clone port (part of 3) | fvm re-lock (12 + 3), then one
  `uv lock`. Order 3: 6 | 11 | 14, split by code region.
- **Gate = all verifiers PASS + code review clean + ladder green**, then the
  next order starts. After the order-3 gate: one qc-skeptic lens pass on the
  item 6 framing, then stop and report to Andy.
- **Reports live here.** `STATUS.md` is the running log (UTC timestamps, units
  on every number, full paths). Agent scratch goes under `/tmp` and is removed.

## Decisions (dated)

- **2026-10-15 — target qiskit-ibm-runtime 0.50.0.** qiskit 2.5.2 / aer 0.17.2 are
  already current; the runtime bump is the upgrade, and its SamplerV2 deprecation
  is ported now (fvm and our sqls clone) rather than carried as a warning.
  qiskit 2.6 waits for GA and is not a paper dependency.
- **2026-10-15 — the HHL fork is ported off the Qiskit 3.0 removals in phase 1**
  (item 15, order 2), so the paper's HHL control and deflation rows are produced
  by one code state. Circuit metrics are re-recorded; the math is gated by a
  1e-10 statevector reproduction test.
- **2026-10-15 — execution authorizations from Andy (phases 1 and 2).**
  Feature branches MAY be created, and commits MAY be made on those branches,
  in `fvm_euler_1d_solver`, in the fresh HHL-fork clone
  `/Users/agallojr/proj/src/q8020/quantum_linear_solvers`, and in the sqls
  clone `/Users/agallojr/proj/src/q8020/sqls`. NOT in `q8020-cfd-experiments`:
  work there stays on the checked-out tree, uncommitted, for Andy to commit.
  No pushes and nothing on `main` anywhere without a fresh ask. Branch names:
  fvm `feature/sqls-aiaa-4q26`, fork `feature/qiskit3-api-port`, sqls
  `local/sampler-port-2026-10`. Run budget: the test ladder of
  `03-qiskit-upgrade-and-solverfw.md` sec. 5 is approved on the laptop,
  including the ~15 min matched nelem-5 HHL case, as often as the gates need;
  still no Frontier runs and no sweeps beyond that ladder. Phases 1 and 2
  (orders 1 to 3) run, then STOP for Andy's reassessment before phase 3.
- **2026-10-15 — our sqls is detached from the cloud source.** The clone at
  `/Users/agallojr/proj/src/q8020/sqls` (main @ 9a4346a7) is the source of
  record for this work. No step may require reaching code.ornl.gov; the fvm
  build points at the local path (item 12). Upstream drift is checked by hand,
  on request, with a single `git ls-remote`.

## Guardrails for this work

- Solver runs: only the approved test ladder (see Decisions), laptop only.
  No Frontier, no `q8020-sweep` beyond `--dry-run` and the `_smoke` group.
- Analysis of solverfw only; no solverfw code changes in this phase.
- Git: branches and commits only as authorized in Decisions; never push; never
  touch `main`; nothing committed in `q8020-cfd-experiments`.
- Venv changes only in order 2 (the single re-lock) and only in the fvm venv;
  rollback recipe in `03-qiskit-upgrade-and-solverfw.md` sec. 4.
- Units on every number, UTC ISO 8601 for every timestamp, full paths.

## Consolidated findings (items 1 to 5, reported 2026-10-15T01:46Z to 02:12Z)

**Where we stand.** SQLS is wired into fvm correctly (item 4: every keyword and
return field matches sqls @ 9a4346a7, imports and `--help` pass, no blockers),
but it has been exercised exactly once, on a laptop, for 7 Newton solves, with
no provenance fragments, no README, and the metrics written into a file named
`hhl_metrics_*.csv` (item 1). Nothing has run on Frontier, no shot / CFL / mesh
sweep exists, no `truncated_*` method has been tried, and the fvm repo has no
tests at all (items 1, 3). The upgrade target is smaller than expected: qiskit
2.5.2 and aer 0.17.2 are already current, so the stack work is the
qiskit-ibm-runtime 0.50.0 bump and its SamplerV2 port (item 3, Decisions). The
sqls git source is unreliable (server-side 504) and we are treating our clone
as detached (item 2, Decisions). The direct fvm + sqls route touches solverfw
nowhere (item 3). The sweeper path exists and dry-runs cleanly on the draft
TOML, but the harvester is HHL-shaped at column level and two of the three
April sweeps lost their fragments to a stale path (items 4, 5).

**Must-fix before any paper run (in order; these are the Pri = H open items, items 3, 7, 8, 9, 10, 11, 12, 13, 15, 16).**
1. Zero pad on the SQLS path (item 9) — the fidelity tail collapse is a padding
   artifact, not shot noise.
2. `-sqls_k` default (item 7) and the misleading "install sqls" error when
   `backend_type != 'ideal'` (item 4, finding list).
3. Harvester: SQLS columns, convergence test, stdout parser (item 10); stale
   `_case_postproc` path (item 13).
4. Fairness: reference-free sign rule, shared fixed-basis circuit counter,
   effective-shots metadata (item 11).
5. Runtime 0.50.0 port + re-lock with sqls as a local path source (items 3, 12),
   gated by the smoke tests (item 8).
Then: `_smoke` group on the laptop, `sqls_shots` on the laptop (~4 min), the
rest on Frontier (item 5, sec. 3b/3c of the report has the exact commands; every
run needs Andy's approval).

**Numbers to keep in mind** (August laptop trial, nelem 5, cfl 1e10, 150k
shots): SQLS full_svd 4 qubits, ~201 CX / depth 398 in {u3,cx}, 0.082 s per
solve, 0.62 s total, 6 Newton iterations to residual 1.26e-9; HHL 14 qubits,
641,145 gates / depth 596,688 in the Aer basis, 51.7 s per solve, 859 s total,
hit the 15-iteration cap at residual 6.8e-3. Bases differ, so the gate ratio is
order-of-magnitude only (item 11b). Frontier HHL per case: 1125 to 1653 s.
Estimated SQLS at nelem 85 (256 x 256 full SVD + two 8-qubit UnitaryGate
syntheses, ~31k CX each): 5 to 15 min per case, feasible.

**Reports.** `01-august-2026-analysis.md` (47 KB), `02-code-inventory.md`
(39 KB), `03-qiskit-upgrade-and-solverfw.md` (51 KB), `04-sqls-wiring-validation.md`
(51 KB, 15 numbered findings in sec. 6), `05-sweep-mechanism.md` (54 KB) +
`fvm_sqls_aiaa_sweeps.DRAFT.toml`, `06-svd-priming-hhl.md` (parallel session).

## Open questions for Andy (from item 5, sec. 3g; answers feed the TOML)

1. `sqls_nelem` trials: 3 (draft) or 10 for protocol uniformity and error bars?
2. Include `truncated_mps` / `truncated_qr` now (needs item 7 first) or defer per qtsuite #54?
3. HHL control: re-run on qiskit 2.5.2 (`hhl_matched`, ~10 node-hours on Frontier) or reuse the April 2.3.1 results?
4. Which metautil branch runs the sweeps: `main` 8ccab91 or `feature/solverfw-v2` 753b97e?
5. Harvester patch (item 10) before the Frontier runs, or harvest post hoc after patching?
6. Exclusive node per case (April default) or packed mode for the ~1 s SQLS cases?
7. Keep `-v 2` at nelem 85 (only way to get cx_count / depth) given the synthesis cost?
8. Frontier output root: `/lustre/orion/ard189/proj-shared/agallojr/q8020` as in April (purge policy applies)?
9. The `-cfl 1e10, -shots 150000` cell is duplicated across `sqls_shots` and `sqls_cfl`: run twice or dedupe?
10. Any HHL flags beyond April's for `hhl_matched` (note `-hhl_scale` default is not in its own choices list, item 4)?
11. Add `-shots 0` to `sqls_nelem` (30 cases at 3 trials) so the exact-statevector scaling curve exists?
12. Who reaches out to Chao Lu for a sqls LICENSE and a mirror permission (item 12)?

## Open questions added by the orchestrator at the order-3 stop (2026-10-15)

13. **git-gate allowlist (resolved for the fork 2026-10-16: added by Andy, port committed and pushed on `feature/sqls-aiaa-4q26`, renamed from `feature/qiskit3-api-port`; sqls deliberately left off the allowlist as the only copy, port stays uncommitted with its patch as the record).** The fork clone `/Users/agallojr/proj/src/q8020/quantum_linear_solvers` and the sqls clone `/Users/agallojr/proj/src/q8020/sqls` are not on `/Users/agallojr/.claude/mesh-git-allowlist.txt`, so the authorized commits on `feature/qiskit3-api-port` and `local/sampler-port-2026-10` could not be made. Add the two paths, or commit by hand; the patches are `sqls-for-aiaa-4Q26/fork-patches/UNCOMMITTED-qiskit3-api-port.diff` and `sqls-patches/UNCOMMITTED-sampler-port.diff`, pinned by every run's `code_versions.diff_sha256`.
14. **Item 6 framing after the qc-skeptic lens (verdict: overstated).** Keep the row with its numbers reported as a distribution over Newton steps and trials (needs a k in {0, 2, 4} full-Newton statevector run on the CFL-1e10 case, about 11 min per k, sweep fence), fix the row at a stated non-converged iteration, or drop the row. Correct 06a lines 77-78 either way.
15. **metautil branch for the paper sweeps** (open question 4): build-14.md recommends committing item 14 on `feature/solverfw-v2` and fast-forwarding `main`, or cherry-picking onto 8ccab91.
16. **April re-harvest in place** (50 cases, 300 fragments, also re-rolls 50 committed `q8020_metadata_<id>.json`): command in build-13.md.
17. **New work item proposal: make the paper comparison scripts SQLS-aware** (`aux/fvm_euler_1d_nozzle/fvm_euler_1d_solver/{compare_sets,shot_scaling,gather}.py` crash on null fields in SQLS fragments and would otherwise compute a meaningless gate ratio; the fixed-basis columns are the right input).
18. **`-loadcirc` qpy reload is broken under qiskit 2.5.2 with the ported fork** (`ExactReciprocalGate` cannot be rebuilt from qpy); affects only the circuit-cache path; fork-side follow-up.
19. **Unseeded HHL convergence variance.** Three new-stack matched runs gave final residual_total 7.15e-4, 1.546, 0.338 (Frontier envelope 3e-7 to 0.46); `-seed` now exists; the paper's HHL control protocol should state seeds and report distributions.
