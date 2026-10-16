# Can the SQLS SVD machinery prime the HHL solve?

Written 2026-10-14 (UTC) for work item 6 of `WORKPLAN.md` in this folder.
Design analysis from an interactive session with Andy. Code was read, not run
or changed. No solver output was generated.

Summary. Partly. A full SVD cannot prime HHL, because the full SVD already is
the solution. A partial SVD and the sqls state-prep code can help in three
ways. (1) Load $|b\rangle$ into the HHL circuit with the sqls MPS loader. This
is the smallest change. (2) Deflate the k smallest singular modes classically,
so HHL only sees a better-conditioned remainder. This is the real payoff for
HHL. (3) Reuse those modes across Newton iterations. Today the fvm code does
none of this: `-linsolver` selects HHL or SQLS, never both. All three can be
added without touching the sqls package.

## Background

### What the fvm solver does

Each Newton inner iteration in `fvm_euler_1d_solver` builds a finite-difference
Jacobian $A$ (size $3 \cdot n_\text{elem}$) and residual $b$, then solves
$A \, \Delta Q = b$. The solver for that one step is picked by `-linsolver`:
LU (default), GMRES, HHL, or SQLS. The result updates $q$, and the next
iteration rebuilds $A$ classically.

LuGo does not change this picture. It is an enhanced quantum phase estimation
(QPE) inside HHL (Lu et al., arXiv 2503.15439), giving shallower circuits for
the same math. We do not have the library; the LuGo nozzle results were run by
ORNL on Frontier.

### What `-linsolver SQLS` does today

Code: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/time_solvers.py`
(`linear_sys_solve` at line 424, `sqls_solve` at line 605) and
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py`
(`QuantumSQLS` at line 720).

1. Pickle $A$ and $b$ to the output dir.
2. Solve the same system with classical LU (`dq_lu`) as the reference.
3. `QuantumSQLS.solve_one_step` pads to a power of 2 and calls
   `sqls.runtime.quantum.quantum_solve`. It passes the general,
   non-Hermitian $A$ directly: no Hermitian doubling and no spectral-radius
   scaling, so the data register is $\log_2 N$ qubits versus HHL's
   $2 \log_2 N$. It runs on Aer only (`backend_type` must be `ideal`).
4. Magnitude comes from the classically known $\lVert \text{final\_b} \rVert$.
   In statevector mode the global sign is aligned to `dq_lu`. In shots mode
   sqls restores per-component signs from `final_b`.
5. $q \mathrel{+}= \Delta Q_\text{SQLS}$. Log $\lVert A x - b \rVert_2$ and the
   fidelity versus LU.

Default `-sqls_method full_svd` does a dense SVD, so the answer is known
classically before the circuit runs. The circuit reproduces it.

## Why a full SVD cannot prime HHL

With $A = U \Sigma V^H$ in hand, $x = V \Sigma^{-1} U^H b$ costs a few
matrix-vector products. There is nothing left for HHL to compute. Any useful
priming must use partial information: a few singular modes, or a cheaper way
to load the state.

## Three ways it can help

### 1. MPS state prep for $|b\rangle$ (smallest change)

HHL must load $b$. The fvm HHL path hands a NumPy vector to
`self.hhl.construct_circuit(A_herm, b_herm)`
(`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/quantum_tools.py:325`),
which loads it exactly at $O(2^n)$ CX.

sqls has a TT-SVD staircase loader,
`vector_to_mps` and `mps_to_circuit` in
`/Users/agallojr/proj/src/q8020/sqls/src/sqls/core/mps_state_prep.py`
(lines 56 and 300). It costs $O(n \chi^2)$ CX plus $\lceil \log_2 \chi \rceil$
bond ancillas, and is lossy at finite bond dimension $\chi$.

The HHL library already accepts a circuit for the vector:
`construct_circuit(matrix, vector: List | ndarray | QuantumCircuit)` in
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/.venv/lib/python3.12/site-packages/linear_solvers/hhl.py:262`.
So this is close to plug-in.

Notes.

- The bond ancillas must sit outside the HHL `b` register and be projected
  out at readout, as sqls does with `out["m_ancilla"]`.
- The sqls README measures the Schmidt spectrum of solution-like vectors
  decaying fast ($\chi = 4$ gives $F \ge 0.99$ on 16² to 64² Laplace grids).
  How the Euler residual $b$ compresses is unmeasured. Check the fidelity per
  iteration before trusting it.
- This does not need an SVD of $A$ at all. It applies equally to LuGo-HHL.

### 2. Deflate the smallest singular modes (the real payoff)

Compute only the k smallest singular triplets with
`smallest_k_svd(A, k)`
(`/Users/agallojr/proj/src/q8020/sqls/src/sqls/core/truncated_svd.py:161`;
sparse LU plus shift-invert Lanczos). Then split the solve:

$$
x_\text{low} = V_k \, \Sigma_k^{-1} \, U_k^H \, b, \qquad
b' = \left( I - U_k U_k^H \right) b, \qquad
x = x_\text{low} + \text{HHL}(A, b').
$$

$b'$ has no component along the k worst-conditioned directions. In HHL's
Hermitian-doubled form those directions are the eigenvectors with eigenvalues
$\pm\sigma_1 \dots \pm\sigma_k$, so they drop out too. The effective
condition number falls from $\kappa = \sigma_\text{max} / \sigma_\text{min}$
to

$$
\kappa_\text{eff} = \sigma_\text{max} / \sigma_{k+1}.
$$

Why that matters for HHL.

- The library sizes the clock (QPE) register as
  $n_l = \max(n_b + 1, \lceil \log_2(\kappa + 1) \rceil)$ plus one if there
  are negative eigenvalues (`hhl.py:337`). A smaller $\kappa$ means fewer
  clock qubits and a shallower QPE.
- The reciprocal rotation uses a constant bounded by $\lambda_\text{min}$, so
  the post-selection success probability goes roughly as
  $(\lambda_\text{min} / \lambda)^2$. Raising the effective
  $\lambda_\text{min}$ to $\sigma_{k+1}$ means fewer wasted shots.
- LuGo is a QPE enhancement, so the two stack.

Caveats.

- Computing the smallest modes uses a sparse LU of $A$, which nearly solves
  the system on its own. This is a resource-reduction and demonstration
  technique for HHL, not a quantum speedup.
- The library takes $\kappa$ and $\lambda_\text{min}$ from the full matrix
  (`matrix_circuit.condition_bounds()`, near `hhl.py:331`). Unless we pass
  the deflated bounds in (a custom matrix circuit or a small override), HHL
  will size for the full $\kappa$ and nothing is saved.
- The fvm HHL path also scales by spectral radius and Hermitian-doubles
  (`QuantumHHL.solve_one_step`, `quantum_tools.py:539`). Deflation must be
  applied before those steps, on the original $A$ and $b$.
- Lanczos convergence near clustered small $\sigma$ can be slow; time it
  per iteration (sqls already reports `t_splu` and `t_lanczos`).

### 3. Reuse modes across Newton iterations

The Jacobian changes slowly between inner iterations. The previous
iteration's $V_k$ can warm-start the next Lanczos call, or the Jacobian can be
frozen for several steps so one set of modes serves many solves. This ties to
the frozen-Jacobian plan in
`/Users/agallojr/proj/src/research-notes/bus/memory/notes/note-20260817-0001-sqls-fvm-quantum-timestep-frozen-jacobian.md`.

## What the fvm code does today

None of the above. `linear_sys_solve`
(`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver/time_solvers.py:424`)
dispatches to exactly one of `lu_solve`, `gmres_solve`, `hhl_solve`, or
`sqls_solve`. The HHL path loads $b$ exactly and knows nothing about SVD
modes. The SQLS path shares no code with HHL; its LU call is only for sign
alignment and fidelity.

## Proposed changes

Both are opt-in flags on the HHL path. Nothing in `sqls` changes; fvm imports
from it, as it already does for `-linsolver SQLS`.

| Flag | Where | Change |
|---|---|---|
| `-hhl_state_prep {initialize,mps}`, `-hhl_mps_chi N` | `QuantumHHL.generate_circuit` (`quantum_tools.py:296`) | Build the $b$ circuit with `vector_to_mps` + `mps_to_circuit`; pass it to `construct_circuit` in place of the vector; project out bond ancillas at readout. |
| `-hhl_deflate_k K` | `hhl_solve` (`time_solvers.py:492`) and `QuantumHHL` | Call `smallest_k_svd(A, K)`; form $x_\text{low}$ and $b'$; run HHL on $b'$ with the deflated $\kappa_\text{eff}$ and $\lambda_\text{min} = \sigma_{K+1}$; return $x_\text{low} + x_\text{high}$. |

Add to the `qc_metadata` CSV for both: clock-qubit count, CX count, circuit
depth, $\kappa$ and $\kappa_\text{eff}$, deflation rank K, state-prep fidelity,
and `t_splu` / `t_lanczos`. Without those columns the savings cannot be shown.

Order. Do the state-prep flag first (small, low risk, LuGo-compatible), then
deflation (bigger change, bigger payoff).

## Testing

Unit-level checks (fast, no solver runs):

- Deflation identity on a pickled system from the August trial
  (`system_Ab_nelem5_*.pkl` under
  `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0/`):
  check $x_\text{low} + A^{+} b' = A^{-1} b$ classically, and that
  $\kappa_\text{eff}$ and the clock-qubit count drop as expected.
- MPS prep fidelity of $b$ versus $\chi$ on the same pickles.

Nozzle runs at nelem 5 with and without each flag, compared against LU and
the existing HHL baseline, are solver runs and need Andy's go-ahead under the
work-plan guardrails. Exact commands will be given when the code is ready.

## Open questions

- Does the deflation split keep Newton convergence identical to plain HHL at
  matched shots? It should, since $x$ is the same in exact arithmetic, but
  shot noise now only lands on $x_\text{high}$.
- What K is worth it? Measure $\kappa_\text{eff}$ versus K on the Euler
  Jacobians before picking a default.
- Is this worth a paper paragraph? It is a fair "hybrid SVD-HHL" row for the
  AIAA 2027 comparison, as long as it is described as classical deflation
  plus HHL on the remainder, with no speedup claim.
