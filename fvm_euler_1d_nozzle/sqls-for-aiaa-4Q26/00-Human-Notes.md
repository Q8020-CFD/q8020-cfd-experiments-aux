(Note to the agent - don't touch this file!)



## Software Changes

- ORNL SQLS repo URL is broken. Made a new repo in the q8020 org with the contents of a prior pull taken from ORNL on 2026-07-26. 

- Added switches to fvm_euler_1d_solver to accept various SVD pre-step options, from SQLS, from numpy. 

- Removed quantum_linear_solver use of deprecated methods slated for removal in a future Qiskit 3.x. 

- To quantum_linear_solver, added args to suppress the HHL code's own internal SVD. This was performed not to alter the A matrix, but to compute the condition number which sets the number of required clock qubits, and eigenvalue bounds. An fvm-supplied SVD step would have these, and can now pass them into HHL to use.

- Upgraded IBM  qiskit-ibm-runtime lib to 0.50. 

- Added test files to fvm_euler_1d_solver. Added switches to support SQLS. Fixed harness-level bugs.

- Harvester fixes - made need to reharvest (not rerun) April runs. 


## Shots and Sign Handling

Current code handling:

- SQLS without shots: the solver tries both x and −x. It keeps whichever one fits A x = b better. This uses only A and b. The classical LU answer is still computed, but only afterward, to report error numbers.

- SQLS with shots: SQLS returns the signs of each component itself. The solver does not set them.

- HHL, default scaling: this is unchanged. A least-squares scale factor computed from A and b sets both sign and size.

- HHL, optional "true_sol" scaling: the size still comes from the classical answer. The sign now uses the same rule as SQLS.

- HHL with shots: not fixed. Shots give only magnitudes, so the sign of each component still comes from the classical answer. The code documents this. It is the one remaining place where the quantum path leans on the classical answer, and the paper should say so.


## Lapworth Papers


What the Lapworth papers say

1. Hybrid CFD with HHL (2022, arXiv 2206.00419). HHL runs on a simulator as the pressure solve inside a classical SIMPLE loop, on a lid-driven cavity. The main finding is a hidden classical cost: splitting the matrix into Pauli terms took 32,767 terms and about 2 hours at 65×65. Classical preparation can wipe out any advantage.
2. Implicit hybrid CFD with HHL (2022, 2209.07964). All the flow equations go into one coupled matrix, which converges in about 15 iterations instead of 786. HHL's clock register limits how precisely it resolves the largest and smallest eigenvalues. Errors at either end feed into the next iteration: one fewer clock qubit costs 2 extra iterations, and two fewer cost about 5× as many. "Every logical qubit counts."
3. L-QLES (2024, 2402.12266). An open-source generator of Laplacian test matrices with a tunable condition number κ, from about 10 to 500,000. κ = 17,000 fits in 13 qubits, so small matrices can still be hard ones. Small changes, like renumbering the grid, can blow up the cost of loading the matrix.
4. Measurement schemes, with Patterson (2024, 2411.00723). Reading the answer out costs about 1/ε² shots, which can cancel the speedup. Amplitude estimation brings that down to about 1/ε. CFD correction vectors have only a few large peaks, so it's enough to measure those and recover their signs. The full loop still converges.
5. Preconditioned block encodings, with Sünderhauf (2025, 2502.20908). Preconditioning helps only if the product PA is formed classically and then loaded. Loading P and A separately cancels the gain. With a sparse approximate inverse, κ drops by about 10× and the phase-gate count by about 25× at 1024×1024.
6. Data-loading compiler, with Xanadu (2025, 2512.05183). The tool treats error as a budget and searches loading methods for the cheapest one. On a CFD vector it cut resources by more than 10⁴×. Solving a slightly simplified problem exactly often beats solving the exact problem imperfectly.
7. Chebyshev-LCU, with Classiq (2026, 2606.01067).
   - Case: an incompressible 1D nozzle, 16×16 matrix, κ ≈ 80.
   - Iterations to converge: 3 classical versus 11 quantum.
   - The outer loop tolerates an inexact solver as long as the high-frequency modes are accurate. Errors in the smooth modes get absorbed.
   - That tolerance allows about 20× fewer rotation gates (256 → 12).

Together they argue that the expensive parts are around the solver, not the inversion itself: setup, eigenvalue precision, conditioning, readout, and data loading.


## We Add

- Compressible Euler with an implicit BDF Newton loop and a supersonic nozzle. Lapworth's cases are all incompressible: SIMPLE, pressure correction, or an incompressible nozzle.
- Shot statistics. 10 trials per shot count, with fidelity confidence bands and L2 error against shots. About 100k shots are needed for 2 % error. His work is mostly statevector or analytic.
- CFL drives κ, and κ drives accuracy and cost. CFL 1 gives κ ≈ 7 and 2.0 % error. CFL 1e10 gives κ ≈ 96, 10 % error, and about twice the wall time. His implicit paper only implies this trade-off; we measure it.
- Circuit construction is the bottleneck. About 700k gates, and shot count barely changes cost. LuGo gives a 28–56× end-to-end speedup with no fidelity loss. It also makes circuit generation feasible at Nₕ = 512, where the standard construction takes hours already at 64. This parallels his 2022 setup-cost warning, but at the circuit-construction stage.
- Real HHL and real backends. We run textbook HHL through Qiskit on Frontier. He works with QSVT and resource estimates.
- Benchmarking discipline. Metadata capture, a fixed outer loop so solvers can be swapped fairly, and reproducible sweeps.
- SQLS as a third solver, coming in the final paper.

What we could add readily

No new solver runs needed:
1. Related-work paragraph and citations.
   - Lapworth's 2022 papers are the precedent for a quantum solver inside an iterative CFD loop. Our intro line on [7] needs fixing.
   - Cite the Classiq nozzle paper as the closest comparison. Our 3 versus 8 iterations matches their 3 versus 11.
   - Cite paper 2 for our κ-dependent clock register (nₜ ≈ 8, Table 2).
2. Frame the deflation result against paper 5. Our work-plan item 6 has a classical rank-k deflation that cuts κ from 68 to 15 and saves one clock qubit. That's Lapworth's lesson in a different form: do the conditioning classically, then encode. It fits the existing "classical deflation + HHL, no speedup claim" label.
3. Readout cost. We say reconstruction takes O(N) to O(N²) shots. Set that against paper 4's amplitude-estimation figure of about 1/ε and its "measure only the peaks" result. Also state plainly that our HHL shot path still takes its signs from the classical answer (item 17), and cite paper 4's sign-recovery scheme as the fix.
4. Error spectrum of the HHL updates. Project HHL's update minus the LU update onto the eigenmodes of the Jacobians we already archived. That tests whether our errors fall where papers 2 and 7 say they hurt: high-frequency modes stall convergence, unresolved small eigenvalues feed forward. It's analysis of existing outputs only, and it would explain why HHL needs 8 iterations where LU needs 3. I'd rank this as the most valuable addition.

5. Treat Hermitian doubling and padding as a measured cost. Report κ before and after, and the qubit and gate overhead, the same way paper 1 accounts for decomposition time.

Small new runs. These need your go-ahead under the sweep fence.

6. Clock-qubit sweep at nelem 5, nₜ = 6, 7, 8, 9, counting outer iterations. It's a direct replication of paper 2 on compressible flow and a natural partner to the CFL table.
7. One L-QLES matrix of comparable κ, run through our HHL, LuGo and SQLS. It ties our results to a shared open benchmark, which supports the QC4PDE standardization pitch. This one is optional and lower priority.

Items 1 to 5 fit in the final paper with no new solver output. I'd start with item 4. I can write the related-work paragraph and its bib entries now if you want them.

