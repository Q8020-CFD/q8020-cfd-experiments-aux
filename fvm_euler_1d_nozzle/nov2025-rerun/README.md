# Rerun of the 2025-11-11 fvm baseline on Frontier

Reruns `q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11` with
the reconstructed stack: nelem=5 nozzle, HHL on the ideal statevector
simulator, 1 exact case plus 7 shot counts x 10 trials (71 cases).

| Piece | Value |
|---|---|
| Solver | `Q8020-CFD/fvm_euler_1d_solver@a5317f2b` (`feature/qiskit-hhl`) |
| HHL library | `jw676/quantum_linear_solvers@a94cf63` |
| Python | 3.10 |
| Packages | [requirements.nov2025.txt](requirements.nov2025.txt) |
| Sweep | [fvm_nov2025_rerun.toml](fvm_nov2025_rerun.toml) |

Assumptions: no uncommitted edits in the original checkout; `-hhl_scale`,
`-x` and `-backend` at their defaults; shot sampling was unseeded, so shot
trials can only match statistically.

## Setup (Frontier login node; compute nodes have no internet)

Run from the workspace root, the directory holding the sibling repos
(`fvm_euler_1d_solver`, `q8020-cfd-metautil`, `q8020-cfd-experiments-aux`, ...).
Keep it on NFS (home or `/ccs/proj`), not Lustre, which is purged.

```bash
# 1. Pinned solver code as a worktree next to the main checkout
git -C fvm_euler_1d_solver fetch origin
git -C fvm_euler_1d_solver worktree add ../fvm_euler_1d_solver-a5317f2b a5317f2b

# 2. Solver venv: Python 3.10 + pinned stack
uv venv --python 3.10 fvm_euler_1d_solver-a5317f2b/.venv
uv pip install --python fvm_euler_1d_solver-a5317f2b/.venv \
    -r q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/requirements.nov2025.txt

# 3. Sweeper / harvester venv (skip if ./.venv with metautil already exists)
uv venv --python 3.12 .venv
uv pip install --python .venv -e q8020-cfd-metautil
```

## Run

```bash
source .venv/bin/activate
TOML=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/fvm_nov2025_rerun.toml

q8020-sweep $TOML --dry-run                     # expect 71 cases in 2 groups

# Exact case first, to validate the stack (~70 min)
q8020-sweep $TOML exact --set _slurm=true \
    --set _output_dir=/lustre/orion/ard189/proj-shared/q8020

# Then the shots ladder (70 cases packed on 2 nodes, up to ~2.6 h each)
q8020-sweep $TOML shots --set _slurm=true \
    --set _output_dir=/lustre/orion/ard189/proj-shared/q8020
```

## Checking the result

Exact case vs `results/.../2025-11-11/exact_09899a29`:

- `qc_metadata_*.csv`, step 0: `circ_gates_transpile` = 689027
- converged in 7 iterations, final residual ~8.9e-11
- `system_Ab_*.pkl` per iteration matches the original

Shot cases: per-shot-count error spread across the 10 trials should fall
within the original trials' range.
