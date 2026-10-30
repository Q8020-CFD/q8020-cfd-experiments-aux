#!/usr/bin/env python3
"""Split one group of a sweep TOML into one single-case TOML per case.

Each output TOML keeps the source [global] table verbatim and holds a single
group, named after the case id the sweeper itself would assign (e.g.
``time_steps_4_trial_0``), with that case's scalar parameters and no
``_trials``.  Expansion uses the sweeper's own ``expand_case_lists``, so case
ids and parameter values match a normal ``q8020-sweep`` run of the group.

Usage: fvm_cases.py <sweep.toml> <group> <out_dir>
Prints the written paths, one per line.
"""
import json
import sys
import tomllib
from pathlib import Path

from q8020_cfd_metautil.sweep import expand_case_lists

DROP_KEYS = {"_trial_index", "_parent_case_id"}


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value)  # JSON string escapes are valid TOML basic strings
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(v) for v in value) + "]"
    raise TypeError(f"unsupported TOML value: {value!r}")


def _table(name: str, params: dict) -> str:
    lines = [f"[{name}]"]
    lines += [f"{json.dumps(k)} = {_toml_value(v)}" for k, v in params.items()]
    return "\n".join(lines) + "\n"


def split(toml_path: Path, group: str, out_dir: Path) -> list[Path]:
    config = tomllib.loads(toml_path.read_text())
    if group not in config:
        sys.exit(f"error: group [{group}] not in {toml_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    header = (f"# Single case split from {toml_path} [{group}] by fvm_cases.py\n")
    written = []
    for case_id, params in expand_case_lists(group, dict(config[group])):
        case_params = {k: v for k, v in params.items() if k not in DROP_KEYS}
        text = header + _table("global", config["global"]) + "\n" + _table(case_id, case_params)
        tomllib.loads(text)  # fail fast on anything we could not serialize
        path = out_dir / f"{case_id}.toml"
        path.write_text(text)
        written.append(path)
    return written


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    for p in split(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])):
        print(p)
