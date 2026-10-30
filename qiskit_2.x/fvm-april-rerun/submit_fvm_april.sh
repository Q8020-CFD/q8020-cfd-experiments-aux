#!/bin/bash
# Re-run the April 2026 Frontier fvm HHL sweeps on AWS Batch, one job per case.
#
#   q8020-cfd-experiments-aux/qiskit_2.x/fvm-april-rerun/submit_fvm_april.sh <stack> [--dry-run] [apr05] [apr08] [apr10]
#   (runs from anywhere; paths are resolved from the workspace root)
#
#   old  fvm 9e76e398 + the April package stack   (stacks/old)
#   new  fvm 38a41e52 + latest packages           (stacks/new)
#   code-new_pkgs-old  fvm 38a41e52 + HHL 99231b8, April third-party packages
#   code-old_pkgs-new  fvm 9e76e398 + HHL 66eadf0, latest third-party packages
#   no sweep names = all three (50 + 30 + 20 = 100 jobs)
#
# Each job builds its solver at job start from the image's fvm clone
# (submit.sh --repo/--ref/--reqs/--python; see docker/setup_solver.sh).
# Sweeps use the TOMLs archived with each April run, unchanged; each group is
# split into single-case TOMLs by fvm_cases.py (kept under
# stacks/<stack>/cases/<sweep>/, next to the stack's lock). Every job runs on 1 vCPU with
# OMP/MKL/OpenBLAS threads = 1, as April ran each case (srun -c 1).
# Results land in s3://<bucket>/runs/fvm-april-rerun/<label>/<sweep>/<case id>/<job id>/.
#
# PY: a Python with q8020_cfd_metautil installed (default: python3).
# QISKIT_OPT_LEVEL (optional, 0-3): before the solver starts, write
#   ~/.qiskit/settings.conf with transpile_optimization_level = <level>, the
#   default qiskit uses for every transpile() call that does not pass a level
#   (the solver's HHL transpile). Unset = qiskit's default (2). Runs are labelled
#   <stack>-opt<level> in job names and S3 prefix; their cases go to stacks/<stack>/cases-opt<level>/.
set -euo pipefail
# This script lives in <workspace>/q8020-cfd-experiments-aux/qiskit_2.x/fvm-april-rerun/;
# TOML, harvester and docker/ paths below are relative to <workspace>.
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../../.."

STACK="${1:?usage: $0 <stack> [--dry-run] [apr05] [apr08] [apr10]}"; shift
case "$STACK" in
  old) REF=9e76e398; PYVER=3.12.9 ;;
  new) REF=38a41e52; PYVER=3.12 ;;
  code-new_pkgs-old) REF=38a41e52; PYVER=3.12.9 ;;
  code-old_pkgs-new) REF=9e76e398; PYVER=3.12 ;;
  *) echo "stack must be old, new, code-new_pkgs-old or code-old_pkgs-new" >&2; exit 1 ;;
esac
# submit.sh uploads the local copy to S3, so stacks added after the image build work too
REQS="${HERE}/stacks/${STACK}/requirements.lock.txt"
[ -f "$REQS" ] || { echo "no lock file: $REQS" >&2; exit 1; }
DRY_RUN=false
if [ "${1:-}" = "--dry-run" ]; then DRY_RUN=true; shift; fi
SWEEPS=("$@"); [ "${#SWEEPS[@]}" -gt 0 ] || SWEEPS=(apr05 apr08 apr10)

PY="${PY:-python3}"
R=q8020-cfd-experiments/results/fvm_euler_1d_solver
declare -A TOML=(
  [apr05]="$R/2026-04-05/_52d087d1/q8020_fvm_1d_smoke_test.toml"
  [apr08]="$R/2026-04-08/_85fd6d17/q8020_fvm_cfl_sweeps.toml"
  [apr10]="$R/2026-04-10/_f1112a1f/q8020_fvm_cfl_sweeps.toml"
)
declare -A GROUP=([apr05]=time_steps [apr08]=more_iters [apr10]=more_iters)

HARVESTER=./q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/fvm_euler_1d_nozzle/fvm_euler_1d_solver_harvester.py
SWEEP_ARGS=(
  --set "_output_dir=~/q8020-runs"
  --set "_postproc_venv=./q8020-cfd-ch-lbm/.venv"
  --set "_case_postproc=source \${_postproc_venv}/bin/activate && python3 ${HARVESTER}"
  --set "_run_mode=sequential"
  --set "_slurm=false"
)
LABEL="$STACK"
SETUP=()
if [ -n "${QISKIT_OPT_LEVEL:-}" ]; then
  case "$QISKIT_OPT_LEVEL" in 0|1|2|3) ;; *) echo "QISKIT_OPT_LEVEL must be 0-3" >&2; exit 1 ;; esac
  LABEL="${STACK}-opt${QISKIT_OPT_LEVEL}"
  SETUP=(--setup "mkdir -p ~/.qiskit && printf '[default]\ntranspile_optimization_level = ${QISKIT_OPT_LEVEL}\n' > ~/.qiskit/settings.conf"
         --env "QISKIT_OPT_LEVEL=${QISKIT_OPT_LEVEL}")
fi
SUBMIT_OPTS=(
  --repo fvm_euler_1d_solver --ref "$REF" --reqs "$REQS" --python "$PYVER"
  "${SETUP[@]}"
  --vcpu "${VCPU:-1}" --memory "${MEMORY_MB:-6144}"
  --env OMP_NUM_THREADS=1 --env MKL_NUM_THREADS=1 --env OPENBLAS_NUM_THREADS=1
)

n=0
for sweep in "${SWEEPS[@]}"; do
  [ -n "${TOML[$sweep]:-}" ] || { echo "unknown sweep: $sweep" >&2; exit 1; }
  out="${HERE}/stacks/${STACK}/cases${QISKIT_OPT_LEVEL:+-opt${QISKIT_OPT_LEVEL}}/${sweep}"
  rm -rf "$out"
  mapfile -t cases < <("$PY" "${HERE}/fvm_cases.py" "${TOML[$sweep]}" "${GROUP[$sweep]}" "$out")
  echo "== ${LABEL}/${sweep}: ${#cases[@]} cases from ${TOML[$sweep]} [${GROUP[$sweep]}]"
  for case_toml in "${cases[@]}"; do
    # S3 config key must be unique across stacks and sweeps
    named="${out}/fvm-${LABEL}-${sweep}-$(basename "$case_toml")"
    mv "$case_toml" "$named"
    case_id="$(basename "$case_toml" .toml)"
    job="fvm-${LABEL}-${sweep}-${case_id}"
    if $DRY_RUN; then
      echo "  would submit ${job}  (fvm@${REF}, stacks/${STACK}, Python ${PYVER})"
    else
      ./docker/submit.sh --name "$job" --prefix "fvm-april-rerun/${LABEL}/${sweep}/${case_id}" \
        "${SUBMIT_OPTS[@]}" "$named" "${SWEEP_ARGS[@]}"
    fi
    n=$((n + 1))
  done
done
echo "${n} jobs $($DRY_RUN && echo 'would be ' || true)submitted for ${LABEL}"
