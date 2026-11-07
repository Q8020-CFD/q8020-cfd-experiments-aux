#!/bin/bash
# Launch the 8 sweeper lanes detached. Run from /Users/agallojr/proj/src/q8020.
T=q8020-cfd-experiments/aux/fvm_euler_1d_nozzle/optlevel-hhl-nelem5-2026-11/inputs/hhl_nelem5_optlevel.toml
OUT=$HOME/q8020/optlvl-hhl
mkdir -p $OUT/logs
for g in nov2026_sv_a nov2026_sv_b nov2026_shots_a nov2026_shots_b \
         nov2025_sv_a nov2025_sv_b nov2025_shots_a nov2025_shots_b; do
  nohup ./q8020-cfd-metautil/.venv/bin/q8020-sweep $T $g \
    --set _output_dir=$OUT/$g > $OUT/logs/$g.log 2>&1 &
done
