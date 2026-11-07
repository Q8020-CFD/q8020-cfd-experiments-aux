"""Copy finished cases from ~/q8020/optlvl-hhl into the experiments repo.

Layout: <dest>/<codebase>/shots<N>/opt<L>/ ; drops *.qpy and system_Ab_*.pkl.
A case is finished when its q8020_sweep_exec_stats JSON exists. With --clear
the source case dir is removed after the copy (file count checked).
Sweep-level metadata (TOML copy, invocation, expanded cases) goes to
<dest>/logs/<lane>/.
"""
import glob
import json
import os
import shutil
import sys

SRC = os.path.expanduser("~/q8020/optlvl-hhl")
DEST = sys.argv[1]
CLEAR = "--clear" in sys.argv
SKIP = ("*.qpy", "system_Ab_*.pkl")

for lane in sorted(glob.glob(f"{SRC}/nov*")):
  cb = os.path.basename(lane).split("_")[0]
  for run in glob.glob(f"{lane}/*/_*"):
    for case in glob.glob(f"{run}/[0-9a-f]*"):
      if not glob.glob(f"{case}/q8020_sweep_exec_stats_*_0.json"):
        continue
      p = json.load(open(glob.glob(f"{case}/q8020_params_*.json")[0]))
      dst = f"{DEST}/{cb}/shots{p['-shots']}/opt{p['-opt_level']}"
      if os.path.exists(dst):
        shutil.rmtree(dst)
      shutil.copytree(case, dst, ignore=shutil.ignore_patterns(*SKIP))
      print("harvested", case, "->", dst)
      if CLEAR:
        shutil.rmtree(case)
    meta = f"{DEST}/logs/{os.path.basename(lane)}"
    os.makedirs(meta, exist_ok=True)
    for f in glob.glob(f"{run}/*.json") + glob.glob(f"{run}/*.toml"):
      shutil.copy(f, meta)
