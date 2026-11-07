#!/bin/bash
# Progress of the 8 lanes: completed Newton steps per case dir.
cd $HOME/q8020/optlvl-hhl || exit 1
for g in nov*; do
  for d in $g/*/*/*/; do
    n=$(ls $d/dq_nelem5_iter*.csv 2>/dev/null | wc -l)
    p=$(grep -o '"-opt_level": [0-9]' $d/q8020_case_postproc_*.json 2>/dev/null | head -1)
    echo "$g $d steps=$n $p"
  done
done
uptime
