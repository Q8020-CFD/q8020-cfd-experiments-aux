"""Generate metadata JSON from FVM Euler 1D solver output directory.

Parses the output files from nozzle_1d_solver.py runs and produces a
structured metadata.json conforming to the make_meta schema.

Usage:
    fvm-euler-1d-meta --outdir /tmp/fvm
    fvm-euler-1d-meta --outdir /tmp/fvm --output metadata.json
"""

import argparse
import csv
import json
import pickle
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from q8020_cfd_metautil.meta_fragment import (
    write_analysis,
    write_artifacts,
    write_backend,
    write_case,
    write_code,
    write_results,
)

# Gate basis the circuit metrics are counted in; never compare across bases.
HHL_BASIS = "aer_simulator"  # transpile(circ, AerSimulator), all gates
SQLS_BASIS = "{u3,cx}"       # sqls count_cx_depth; CX count in after.cx_count


def _parse_csv_to_dicts(csv_path: Path) -> list[dict[str, Any]]:
    """Parse a CSV file with header row into list of dicts."""
    if not csv_path.exists():
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        return [row for row in reader]


def _parse_csv_to_floats(csv_path: Path) -> list[dict[str, float]]:
    """Parse CSV and convert all values to floats where possible."""
    rows = _parse_csv_to_dicts(csv_path)
    result = []
    for row in rows:
        converted = {}
        for k, v in row.items():
            k = k.strip()
            try:
                converted[k] = float(v)
            except (ValueError, TypeError):
                converted[k] = v
        converted = {k: v for k, v in converted.items() if k}
        result.append(converted)
    return result


def _iter_no(path: Path) -> int:
    """Iteration number N from an ``...iter<N>...`` filename; -1 if absent."""
    m = re.search(r"iter(\d+)", path.name)
    return int(m.group(1)) if m else -1


def _load_pickle(pkl_path: Path) -> dict[str, Any] | None:
    """Load a pickle file, returning None if not found."""
    if not pkl_path.exists():
        return None
    with open(pkl_path, "rb") as f:
        return pickle.load(f)


def _inventory_files(outdir: Path) -> dict[str, list[dict[str, Any]]]:
    """Categorize FVM solver-created files in output directory by type.
    
    Skips sweeper-created files (q8020_*, stdout.txt, stderr.txt, metadata.json, etc.)
    """
    inventory: dict[str, list[dict[str, Any]]] = {
        "qpy_generated": [],
        "qpy_transpiled": [],
        "csv": [],
        "pkl": [],
        "png": [],
        "other": [],
        "rotated_csv": [],
    }

    for file_path in outdir.iterdir():
        if not file_path.is_file():
            continue

        # Skip sweeper-created files (all prefixed with q8020_)
        if file_path.name.startswith("q8020_"):
            continue

        stat = file_path.stat()
        info = {
            "name": file_path.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
        }

        if file_path.suffix == ".qpy":
            if "generated" in file_path.name:
                inventory["qpy_generated"].append(info)
            elif "transpile" in file_path.name:
                inventory["qpy_transpiled"].append(info)
            else:
                inventory["other"].append(info)
        elif file_path.suffix == ".csv":
            inventory["csv"].append(info)
        elif file_path.suffix == ".pkl":
            inventory["pkl"].append(info)
        elif file_path.suffix == ".png":
            inventory["png"].append(info)
        else:
            inventory["other"].append(info)

    # Stale-header CSVs the solver rotated into rotated/ (fvm e50f4800):
    # listed only, never parsed (the metric globs are non-recursive).
    rotated = outdir / "rotated"
    if rotated.is_dir():
        for file_path in sorted(rotated.glob("*.csv")):
            stat = file_path.stat()
            inventory["rotated_csv"].append({
                "name": f"rotated/{file_path.name}",
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat().replace("+00:00", "Z"),
            })

    return inventory


def _extract_run_params(outdir: Path) -> dict[str, Any]:
    """Extract run parameters from metadata pickle file."""
    # Find metadata pickle
    pkl_files = list(outdir.glob("metadata_*.pkl"))
    if not pkl_files:
        return {}

    metadata = _load_pickle(pkl_files[0])
    if metadata is None:
        return {}

    # Convert numpy types to Python types for JSON serialization
    result = {}
    for k, v in metadata.items():
        if hasattr(v, "item"):  # numpy scalar
            result[k] = v.item()
        elif isinstance(v, dict):
            result[k] = {
                kk: vv.item() if hasattr(vv, "item") else vv
                for kk, vv in v.items()
            }
        else:
            result[k] = v
    return result


def _extract_hhl_metrics(outdir: Path) -> list[dict[str, float]]:
    """Extract HHL metrics from CSV."""
    csv_files = list(outdir.glob("hhl_metrics_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_qc_metadata(outdir: Path) -> list[dict[str, Any]]:
    """Extract quantum circuit metadata from CSV."""
    csv_files = list(outdir.glob("qc_metadata_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_final_results(outdir: Path) -> list[dict[str, float]]:
    """Extract final solution results from CSV."""
    csv_files = list(outdir.glob("final_results_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_residuals(outdir: Path) -> list[dict[str, float]]:
    """Extract residual history from CSV."""
    csv_files = list(outdir.glob("residual_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _read_stdout(outdir: Path) -> str:
    """Read the first q8020_stdout_*.txt file, or run.log, or return empty string."""
    stdout_files = list(outdir.glob("q8020_stdout_*.txt"))
    if stdout_files:
        return stdout_files[0].read_text(encoding="utf-8", errors="replace")
    # Fallback: Frontier runs produce run.log instead of q8020_stdout
    run_log = outdir / "run.log"
    if run_log.exists():
        return run_log.read_text(encoding="utf-8", errors="replace")
    return ""


# Stdout comparison-table layouts: solver -> (header token, quantum column)
_STDOUT_SOL_LAYOUTS: dict[str, tuple[str, int]] = {
    "HHL": ("HHL sol", 2),    # LU sol, Herm LU sol, HHL sol, L1_diff(%)
    "SQLS": ("SQLS sol", 1),  # LU sol, SQLS sol, L1_diff(%)
}


def _parse_stdout_lu_solutions(text: str) -> list[dict[str, Any]]:
    """Parse LU and quantum solution vectors from stdout comparison tables.

    Each iteration prints a block like (HHL, 4 columns):
        LU sol \t    Herm LU sol    HHL sol    L1_diff(%)
    or (SQLS, 3 columns):
        LU sol \t    SQLS sol    L1_diff(%)
    followed by rows of floats and a ====...==== line.

    Returns list of dicts (one per iteration), each with:
        {"solver": "HHL"|"SQLS", "lu": [float, ...], "qsol": [float, ...]}
    """
    if not text:
        return []

    results: list[dict[str, Any]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        layout = None
        if line.strip().startswith("LU sol"):
            layout = next(
                ((name, col)
                 for name, (tok, col) in _STDOUT_SOL_LAYOUTS.items()
                 if tok in line),
                None,
            )
        if layout is not None:
            solver, col = layout
            i += 1
            lu_vals: list[float] = []
            q_vals: list[float] = []
            while i < len(lines):
                row = lines[i].strip()
                if not row or row.startswith("="):
                    break
                parts = row.split()
                if len(parts) > col:
                    try:
                        lu_vals.append(float(parts[0]))
                        q_vals.append(float(parts[col]))
                    except ValueError:
                        break
                i += 1
            if lu_vals:
                results.append(
                    {"solver": solver, "lu": lu_vals, "qsol": q_vals}
                )
        i += 1

    return results


def _stdout_declares_converged(text: str) -> bool:
    """True if the solver's banner follows the LAST ``step:`` line.

    Anchoring to the last step keeps a banner from an earlier chunk of a
    concatenated/resumed log from counting.
    """
    steps = list(re.finditer(r"^\s*step:", text, re.MULTILINE))
    tail = text[steps[-1].end():] if steps else text
    return "SOLUTION CONVERGED" in tail


def _is_sqls(
    run_params: dict[str, Any], qc_metadata: list[dict[str, Any]]
) -> bool:
    """SQLS run: pickle says so, or the qc_metadata CSV has SQLS columns."""
    if str(run_params.get("linear_solver", "")).upper() == "SQLS":
        return True
    return bool(qc_metadata) and "solve_time" in qc_metadata[0]


def _int_or_none(val: Any) -> int | None:
    """Int of a numeric CSV cell; None if missing or the -1 'not logged' flag."""
    try:
        ival = int(val)
    except (TypeError, ValueError):
        return None
    return None if ival < 0 else ival


def _sqls_params(
    run_params: dict[str, Any], qc_metadata: list[dict[str, Any]]
) -> dict[str, Any]:
    """SQLS method/k/state_prep/repeats from pickle, falling back to the CSV."""
    qc = run_params.get("quantum_circuit") or {}
    first = qc_metadata[0] if qc_metadata else {}
    out: dict[str, Any] = {}
    for key in ("method", "k", "state_prep", "repeats"):
        val = qc.get(key, first.get(key))
        if key in ("k", "repeats") and val is not None:
            val = int(val)
        out[key] = val
    return out


def _float_or_none(val: Any) -> float | None:
    """Float of a numeric CSV cell; None if missing or non-numeric."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _fixed_basis(row: dict[str, Any]) -> dict[str, Any] | None:
    """Shared fixed-basis counts of one step (fvm cca70256 fb_* columns).

    None when the CSV predates the columns. Under -circ_metrics none the
    solver writes -1 counts and basis 'none'; those come out null.
    """
    if "fb_depth" not in row:
        return None
    raw = str(row.get("fb_basis", "")).strip()
    basis = {"u3cx": SQLS_BASIS, "none": None, "": None}.get(raw, raw)
    return {
        "basis": basis,
        "depth": _int_or_none(row.get("fb_depth")),
        "total_gates": _int_or_none(row.get("fb_total_gates")),
        "cx_count": _int_or_none(row.get("fb_cx_count")),
        "t_count_s": (_float_or_none(row.get("t_count_s"))
                      if basis is not None else None),
        "cached": _bool_or_none(row.get("fb_cached")),
    }


def _bool_or_none(val: Any) -> bool | None:
    """Bool of a CSV cell written from a Python bool; None if absent/empty."""
    text = str(val).strip().lower() if val is not None else ""
    return {"true": True, "1": True, "1.0": True,
            "false": False, "0": False, "0.0": False}.get(text)


def _fixed_basis_summary(
    passes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Medians of the fixed-basis counts over steps; t_count_s over steps
    >= 1 only (step 0 carries the transpiler warm-up). None if no step has
    fixed-basis columns."""
    fbs = [(p["step"], p["fixed_basis"]) for p in passes
           if p.get("fixed_basis")]
    if not fbs:
        return None

    def med(vals: list[Any]) -> float | None:
        vals = [v for v in vals if v is not None]
        return statistics.median(vals) if vals else None

    bases = sorted({fb["basis"] for _, fb in fbs if fb["basis"]})
    return {
        "basis": bases[0] if len(bases) == 1 else (bases or None),
        "median_depth": med([fb["depth"] for _, fb in fbs]),
        "median_total_gates": med([fb["total_gates"] for _, fb in fbs]),
        "median_cx_count": med([fb["cx_count"] for _, fb in fbs]),
        # cached rows reuse an earlier count (t_count_s 0.0): excluded
        "median_t_count_s_steps_ge1": med(
            [fb["t_count_s"] for step, fb in fbs
             if step >= 1 and not fb.get("cached")]
        ),
        "n_steps": len(fbs),
        "n_cached_steps": sum(1 for _, fb in fbs if fb.get("cached")),
    }


def _deflation(row: dict[str, Any]) -> dict[str, Any] | None:
    """HHL shifted-SVD deflation record of one step (fvm 8eb40832 columns).

    None when the CSV predates the columns (SQLS, all archived runs).
    kappa is of the original A, kappa_eff of the shifted A' given to HHL.
    """
    if "deflate_k" not in row:
        return None
    return {
        "deflate_k": _int_or_none(row.get("deflate_k")),
        "kappa": _float_or_none(row.get("kappa")),
        "kappa_eff": _float_or_none(row.get("kappa_eff")),
        "n_clock": _int_or_none(row.get("n_clock")),
        "x_share_classical": _float_or_none(row.get("x_share_classical")),
        "t_svd_s": _float_or_none(row.get("t_svd_s")),
    }


def _linear_system_deflation(
    qc_metadata: list[dict[str, Any]],
) -> dict[str, Any]:
    """What condition_number describes (A, or A' when deflate_k > 0) and the
    range of the original-A kappa; null when the columns are absent."""
    defl = [d for d in map(_deflation, qc_metadata) if d is not None]
    if not defl:
        return {"condition_number_refers_to": None,
                "kappa_original_range": None}
    shifted = any((d["deflate_k"] or 0) > 0 for d in defl)
    kappas = [d["kappa"] for d in defl if d["kappa"] is not None]
    return {
        "condition_number_refers_to": "A_shifted" if shifted else "A",
        "kappa_original_range": (
            [round(min(kappas), 4), round(max(kappas), 4)] if kappas else None
        ),
    }


def _deflation_summary(
    passes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Medians over steps of kappa, kappa_eff, x_share_classical and the
    first/last n_clock, for HHL runs with deflate_k > 0; None otherwise."""
    defl = [p["deflation"] for p in passes if p.get("deflation")]
    if not defl or not any((d["deflate_k"] or 0) > 0 for d in defl):
        return None

    def med(key: str) -> float | None:
        vals = [d[key] for d in defl if d[key] is not None]
        return statistics.median(vals) if vals else None

    return {
        "deflate_k": defl[-1]["deflate_k"],
        "median_kappa": med("kappa"),
        "median_kappa_eff": med("kappa_eff"),
        "median_x_share_classical": med("x_share_classical"),
        "n_clock_first": defl[0]["n_clock"],
        "n_clock_last": defl[-1]["n_clock"],
        "n_steps": len(defl),
    }


def _parse_stdout_backend(text: str) -> dict[str, Any]:
    """Parse stdout for backend and shots info as fallback.

    Looks for lines like:
        Backend: aer_simulator_statevector
        Shots: 1024
    """
    if not text:
        return {}

    result: dict[str, Any] = {}

    m = re.search(r"Backend:\s*(\S+)", text)
    if m:
        result["name"] = m.group(1)

    m = re.search(r"Shots:\s*(\d+)", text)
    if m:
        result["nshots"] = int(m.group(1))

    return result


def _extract_dq_by_step(
    outdir: Path,
) -> tuple[dict[int, list[dict[str, float]]], bool]:
    """Parse dq_nelem*_iter*_*.csv by step; flag unsteady (_nsteps) naming."""
    dq_files = sorted(outdir.glob("dq_nelem*_iter*_*.csv"), key=_iter_no)
    dq_by_step: dict[int, list[dict[str, float]]] = {}
    for dq_path in dq_files:
        step = _iter_no(dq_path)
        if step >= 0:
            dq_by_step[step] = _parse_csv_to_floats(dq_path)
    unsteady = any("_nsteps" in p.name for p in dq_files)
    return dq_by_step, unsteady


def _extract_per_iteration_results(
    outdir: Path,
    dq_by_step: dict[int, list[dict[str, float]]],
) -> list[dict[str, Any]]:
    """Glob per-iteration results CSVs, sorted by iter number, with dq."""
    # results_nelem*_iter*_*.csv
    result_files = sorted(
        outdir.glob("results_nelem*_iter*_*.csv"), key=_iter_no
    )

    per_iter: list[dict[str, Any]] = []
    for res_path in result_files:
        step = _iter_no(res_path)
        if step < 0:
            continue
        entry: dict[str, Any] = {
            "step": step,
            "solution": _parse_csv_to_floats(res_path),
        }
        if step in dq_by_step:
            entry["dq"] = dq_by_step[step]
        per_iter.append(entry)

    return per_iter


# ---------------------------------------------------------------------------
# Fragment builders
# ---------------------------------------------------------------------------

def _build_backend(
    run_params: dict[str, Any],
    qc_metadata: list[dict[str, Any]],
    stdout_text: str,
    sqls_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build backend fragment from pickle, qc_metadata CSV, and stdout fallback."""
    # Start with pickle data
    backend_type = run_params.get("backend_type", "")
    backend_method = run_params.get("backend_method", "")
    nshots = run_params.get("nshots", 0)

    # Derive name from pickle fields
    name = ""
    if backend_type and backend_method:
        name = f"{backend_type}_{backend_method}"
    elif backend_type:
        name = backend_type

    # Fallback to stdout if pickle didn't provide backend info
    if not name:
        stdout_info = _parse_stdout_backend(stdout_text)
        name = stdout_info.get("name", "unknown")
        if not nshots:
            nshots = stdout_info.get("nshots", 0)

    # Determine noise from name
    noise = "fake_" in name.lower() or "fake " in str(run_params.get("backend_type", "")).lower()

    # Determine simulator type
    sim_type = "simulator"

    # num_qubits: the actual circuit width circ_qubits when logged (fvm
    # cca70256+); else the legacy rule from the first qc_metadata row:
    # SQLS n_data_qubits + m_ancilla, HHL nqubits (log2 of the Hermitian
    # system, not the circuit). -1 "not logged" cells count as missing.
    num_qubits = None
    num_qubits_source = None
    sqls = sqls_params is not None
    first = qc_metadata[0] if qc_metadata else {}
    if _int_or_none(first.get("circ_qubits")) is not None:
        num_qubits = _int_or_none(first.get("circ_qubits"))
        num_qubits_source = "circ_qubits"
    elif sqls and _int_or_none(first.get("n_data_qubits")) is not None:
        num_qubits = _int_or_none(first["n_data_qubits"]) + (
            _int_or_none(first.get("m_ancilla")) or 0
        )
        num_qubits_source = "legacy"
    elif _int_or_none(first.get("nqubits")) is not None:
        num_qubits = _int_or_none(first.get("nqubits"))
        num_qubits_source = "legacy"

    backend: dict[str, Any] = {
        "name": name,
        "type": sim_type,
        "method": backend_method or "statevector",
        "noise": noise,
        "_source": "solver",
    }
    if num_qubits is not None:
        backend["num_qubits"] = num_qubits
        backend["num_qubits_source"] = num_qubits_source
    if nshots:
        backend["nshots"] = int(nshots) if not isinstance(nshots, int) else nshots
    # Effective shot budget per linear solve: pickle, else CSV column, else
    # the legacy SQLS rule nshots x repeats; null when unknown. 0 means
    # statevector (no sampling).
    effective_shots = _int_or_none(run_params.get("effective_shots"))
    if effective_shots is None:
        effective_shots = _int_or_none(first.get("effective_shots"))
    repeats = sqls_params["repeats"] if sqls_params else None
    if effective_shots is None and nshots and repeats:
        effective_shots = int(nshots) * int(repeats)
    backend["effective_shots"] = effective_shots
    # Shot-sampler seed: pickle, else CSV column ('' = unseeded); null
    # when unseeded or not recorded.
    seed = run_params.get("seed")
    if seed is None:
        seed = _int_or_none(first.get("seed"))
    backend["seed"] = None if seed is None else int(seed)

    return backend


def _build_artifacts_sqls(
    qc_metadata: list[dict[str, Any]],
    file_inventory: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """SQLS artifacts: cx/depth in {u3,cx}, solve_time as execute time.

    SQLS logs no raw circuit and no generate/transpile split, so those are
    null; there is no Hermitian doubling, so matrix_size_hermitian is null.
    """
    transpile_passes: list[dict[str, Any]] = []
    total_solve = 0.0
    condition_numbers: list[float] = []
    for row in qc_metadata:
        solve_time = float(row.get("solve_time", 0.0))
        total_solve += solve_time
        cond = row.get("condition_number")
        if cond is not None:
            condition_numbers.append(float(cond))
        n_data = _int_or_none(row.get("n_data_qubits"))
        m_anc = _int_or_none(row.get("m_ancilla"))
        width = n_data + (m_anc or 0) if n_data is not None else None
        transpile_passes.append({
            "step": int(row.get("step", 0)),
            "wall_time_generate_s": None,
            "wall_time_transpile_s": None,
            "wall_time_execute_s": round(solve_time, 6),
            "before": None,
            "after": {
                "depth": _int_or_none(row.get("circuit_depth")),
                "num_qubits": width,
                "gate_count": None,  # SQLS logs no all-gates count
                "cx_count": _int_or_none(row.get("cx_count")),
                "basis": SQLS_BASIS,
                "gate_count_scope": "none; CX only, in cx_count",
            },
            "sqls": {
                "method": row.get("method"),
                "k": _int_or_none(row.get("k")),
                "state_prep": row.get("state_prep"),
                "repeats": _int_or_none(row.get("repeats")),
                "n_data_qubits": n_data,
                "m_ancilla": m_anc,
                "cx_count": _int_or_none(row.get("cx_count")),
                "circuit_depth": _int_or_none(row.get("circuit_depth")),
                "aer_device": row.get("aer_device"),
                "solve_time": solve_time,
            },
            "fixed_basis": _fixed_basis(row),
            "deflation": _deflation(row),
        })

    linear_system: dict[str, Any] = {}
    if qc_metadata:
        first = qc_metadata[0]
        linear_system["matrix_size_original"] = int(first.get("matrix_size_orig", 0))
        linear_system["matrix_size_padded"] = int(first.get("matrix_size_pow2", 0))
        linear_system["matrix_size_hermitian"] = None
    if condition_numbers:
        linear_system["condition_number_range"] = [
            round(min(condition_numbers), 4),
            round(max(condition_numbers), 4),
        ]
    linear_system.update(_linear_system_deflation(qc_metadata))

    return {
        "transpile_passes": transpile_passes,
        "fixed_basis_summary": _fixed_basis_summary(transpile_passes),
        "circuit_basis": SQLS_BASIS,
        "circuit_timing_total_s": {
            "generate": None,
            "transpile": None,
            "execute": round(total_solve, 6),
            "total": round(total_solve, 6),
        },
        "linear_system": linear_system,
        "file_inventory": file_inventory,
        "_source": "solver",
    }


def _build_artifacts(
    qc_metadata: list[dict[str, Any]],
    file_inventory: dict[str, list[dict[str, Any]]],
    sqls: bool = False,
) -> dict[str, Any]:
    """Build artifacts fragment with transpile_passes[], circuit_timing, linear_system."""
    if sqls:
        return _build_artifacts_sqls(qc_metadata, file_inventory)
    transpile_passes: list[dict[str, Any]] = []
    total_generate = 0.0
    total_transpile = 0.0
    total_execute = 0.0
    condition_numbers: list[float] = []

    for row in qc_metadata:
        step = int(row.get("step", 0))

        gen_time = row.get("circ_generate_time", 0.0)
        trans_time = row.get("circ_transpile_time", 0.0)
        run_time = row.get("circ_run_time", 0.0)
        total_generate += gen_time
        total_transpile += trans_time
        total_execute += run_time

        cond = row.get("condition_number")
        if cond is not None:
            condition_numbers.append(float(cond))

        pass_entry: dict[str, Any] = {
            "step": step,
            "wall_time_generate_s": round(gen_time, 6),
            "wall_time_transpile_s": round(trans_time, 6),
            "wall_time_execute_s": round(run_time, 6),
            "before": {
                "depth": int(row.get("circ_depth_orig", 0)),
                "num_qubits": int(row.get("circ_qubits_orig", 0)),
                "gate_count": int(row.get("circ_gates_orig", 0)),
            },
            "after": {
                "depth": int(row.get("circ_depth_transpile", 0)),
                "num_qubits": int(row.get("circ_qubits_transpile", 0)),
                "gate_count": int(row.get("circ_gates_transpile", 0)),
                "basis": HHL_BASIS,
                "gate_count_scope": "all",
            },
            "fixed_basis": _fixed_basis(row),
            "deflation": _deflation(row),
        }
        transpile_passes.append(pass_entry)

    total_time = total_generate + total_transpile + total_execute

    # Linear system summary from qc_metadata
    linear_system: dict[str, Any] = {}
    if qc_metadata:
        first = qc_metadata[0]
        linear_system["matrix_size_original"] = int(first.get("matrix_size_orig", 0))
        linear_system["matrix_size_padded"] = int(first.get("matrix_size_pow2", 0))
        linear_system["matrix_size_hermitian"] = int(first.get("matrix_size_herm", 0))
    if condition_numbers:
        linear_system["condition_number_range"] = [
            round(min(condition_numbers), 4),
            round(max(condition_numbers), 4),
        ]
    linear_system.update(_linear_system_deflation(qc_metadata))

    artifacts: dict[str, Any] = {
        "transpile_passes": transpile_passes,
        "fixed_basis_summary": _fixed_basis_summary(transpile_passes),
        "circuit_basis": HHL_BASIS,
        "circuit_timing_total_s": {
            "generate": round(total_generate, 6),
            "transpile": round(total_transpile, 6),
            "execute": round(total_execute, 6),
            "total": round(total_time, 6),
        },
        "linear_system": linear_system,
        "file_inventory": file_inventory,
        "_source": "solver",
    }

    return artifacts


def _build_results(
    final_results: list[dict[str, float]],
    residuals: list[dict[str, float]],
    per_iteration: list[dict[str, Any]],
    stdout_text: str,
) -> dict[str, Any]:
    """Build results fragment with final_solution, per_iteration, residual_history."""
    lu_hhl_vectors = _parse_stdout_lu_solutions(stdout_text)

    # Merge LU/quantum solution vectors into per_iteration entries by index;
    # key is <solver>_solution_vector (hhl_... or sqls_...)
    for idx, entry in enumerate(per_iteration):
        if idx < len(lu_hhl_vectors):
            vecs = lu_hhl_vectors[idx]
            entry["lu_reference_vector"] = vecs["lu"]
            entry[f"{vecs['solver'].lower()}_solution_vector"] = vecs["qsol"]

    results: dict[str, Any] = {
        "final_solution": final_results,
        "per_iteration": per_iteration,
        "residual_history": residuals,
        "_source": "solver",
    }

    # Add final iteration's LU reference at top level for parity with axb
    if lu_hhl_vectors:
        results["lu_reference_vector_final"] = lu_hhl_vectors[-1]["lu"]

    return results


def _last_dq_converged(
    dq_by_step: dict[int, list[dict[str, float]]],
    unsteady: bool,
    nelem: int | None,
) -> bool:
    """Solver dq criterion on the last step: all per-equation ||dq|| <= 1e-10.

    Mirrors nozzle_1d_solver.py (np.all(norm(q - qold, axis=1) <= 1e-10)):
    the applied update is the 2nd dq CSV column, laid out (nelem, 3).
    Valid for steady mode (one inner iteration per step). NaN: not converged.
    """
    if not dq_by_step or not nelem or unsteady:
        return False  # unsteady naming (nsteps/iter): criterion not mapped
    rows = dq_by_step[max(dq_by_step)]
    if not rows:
        return False
    col = [k for k in rows[0] if k.startswith("dq_") and k != "dq_lu"]
    if not col or len(rows) < 3 * nelem:
        return False
    dq = [float(r[col[0]]) for r in rows[: 3 * nelem]]
    for eq in range(3):
        norm = sum(dq[e * 3 + eq] ** 2 for e in range(nelem)) ** 0.5
        if not norm <= 1e-10:  # NaN-safe, as np.all(dqnorm <= 1e-10)
            return False
    return True


KERNEL_REL_ERR_DOC = (
    "||A_q y - b|| / ||b|| (dimensionless) of the quantum solution y to the "
    "system actually given to the circuit: A' (shifted) when deflate_k > 0, "
    "A otherwise; HHL: after scaling, before the deflation recombination, "
    "so independent of the classical share. SQLS writes the same column as "
    "linsys_residual / ||b|| on the original system."
)


def _build_analysis(
    hhl_metrics: list[dict[str, float]],
    residuals: list[dict[str, float]],
    run_params: dict[str, Any],
    dq_by_step: dict[int, list[dict[str, float]]] | None = None,
    unsteady: bool = False,
    stdout_text: str = "",
) -> dict[str, Any]:
    """Build analysis fragment with summary scalars and full per-iteration metrics."""
    # Top-level scalars from last iteration
    fidelity = None
    l2_error_normalized = None
    residual = None
    shots = run_params.get("nshots")
    if shots is not None:
        shots = int(shots)

    iterations_completed = len(hhl_metrics)

    # Per-iteration hhl_metrics array with step numbers
    hhl_metrics_out: list[dict[str, Any]] = []
    for row in hhl_metrics:
        entry: dict[str, Any] = {"step": int(row.get("step", 0))}
        for key in ("fidelity", "l2_error_abs", "l2_error_rel",
                    "l2_error_normalized", "linsys_residual",
                    "hhl_kernel_rel_err"):
            if key in row:
                entry[key] = row[key]
        hhl_metrics_out.append(entry)

    if hhl_metrics:
        last = hhl_metrics[-1]
        fidelity = last.get("fidelity")
        l2_error_normalized = last.get("l2_error_normalized")
        residual = last.get("linsys_residual")

    # Residual reduction from CFD residual history; the solver's res0
    # (resnorm_init) is the denominator when the pickle records it
    residual_reduction = None
    if residuals and len(residuals) >= 2:
        first_res = run_params.get("resnorm_init") or residuals[0].get(
            "residual_total"
        )
        last_res = residuals[-1].get("residual_total")
        if first_res and last_res and first_res != 0:
            residual_reduction = last_res / first_res

    # Convergence: newer solver pickles record converged / converged_by;
    # use them as-is. Otherwise (all archived runs) mirror
    # nozzle_1d_solver.py: stop when res/res0 < conv_tol (a RATIO) or all
    # per-equation ||dq|| <= 1e-10, res0 being the first logged residual.
    # The solver's banner after the last step line, or an early stop
    # (0 < final_iters < max_iters - 1; the loop only breaks on
    # convergence), is taken as its declaration.
    if isinstance(run_params.get("converged"), bool):
        converged = run_params["converged"]
        converged_by = run_params.get("converged_by") if converged else None
        converged_source = "solver"
    else:
        conv_tol = run_params.get("conv_tol")
        final_iters = run_params.get("final_iters")
        max_iters = run_params.get("max_iters")
        criteria = {
            "residual_ratio": (conv_tol is not None
                               and residual_reduction is not None
                               and residual_reduction < conv_tol),
            "dq_norm": _last_dq_converged(
                dq_by_step or {}, unsteady, run_params.get("nelem")
            ),
            "solver_stdout": _stdout_declares_converged(stdout_text),
            "solver_early_stop": (final_iters is not None
                                  and max_iters is not None
                                  and int(max_iters) > 1
                                  and 0 < int(final_iters)
                                  < int(max_iters) - 1),
        }
        converged_by = next((k for k, ok in criteria.items() if ok), None)
        converged = converged_by is not None
        converged_source = "heuristic"

    analysis: dict[str, Any] = {
        "iterations_completed": iterations_completed,
        "converged": converged,
        "converged_by": converged_by,
        "converged_source": converged_source,
        "_source": "solver",
    }
    if fidelity is not None:
        analysis["fidelity"] = fidelity
    if l2_error_normalized is not None:
        analysis["l2_error_normalized"] = l2_error_normalized
    if residual is not None:
        analysis["residual"] = residual
    if shots is not None:
        analysis["shots"] = shots
    if residual_reduction is not None:
        analysis["residual_reduction"] = residual_reduction
    analysis["hhl_metrics"] = hhl_metrics_out

    # Quantum kernel's own relative error per step (fvm 1c54a0d0 column;
    # null for archived runs). Series is in hhl_metrics step order.
    kernel = [_float_or_none(r.get("hhl_kernel_rel_err"))
              for r in hhl_metrics if "hhl_kernel_rel_err" in r]
    kernel_vals = [v for v in kernel if v is not None]
    analysis["hhl_kernel_rel_err"] = kernel or None
    analysis["hhl_kernel_rel_err_final"] = kernel[-1] if kernel else None
    analysis["hhl_kernel_rel_err_median"] = (
        statistics.median(kernel_vals) if kernel_vals else None
    )
    analysis["hhl_kernel_rel_err_doc"] = (
        KERNEL_REL_ERR_DOC if kernel else None
    )

    return analysis


def generate_metadata(
    outdir: Path,
    experiment_id: str | None = None,
    write_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Generate structured metadata from FVM Euler 1D solver output.

    This harvester only writes solver-specific metadata fragments.
    The sweeper handles experiment/workflow IDs, user info, and params.

    Args:
        outdir: Path to the solver output directory (read artifacts from here)
        experiment_id: Experiment ID from sweeper (used for fragment filenames)
        write_dir: Directory to write fragment files to.  Defaults to *outdir*.

    Returns:
        Metadata dict conforming to make_meta schema
    """
    if write_dir is None:
        write_dir = outdir
    run_params = _extract_run_params(outdir)
    hhl_metrics = _extract_hhl_metrics(outdir)
    qc_metadata = _extract_qc_metadata(outdir)
    final_results = _extract_final_results(outdir)
    residuals = _extract_residuals(outdir)
    file_inventory = _inventory_files(outdir)
    stdout_text = _read_stdout(outdir)
    dq_by_step, unsteady = _extract_dq_by_step(outdir)
    per_iteration = _extract_per_iteration_results(outdir, dq_by_step)
    sqls = _is_sqls(run_params, qc_metadata)
    sqls_params = _sqls_params(run_params, qc_metadata) if sqls else None

    # Build case section (problem definition - solver-specific)
    case = {
        "_source": "solver",
        "name": "nozzle_1d",
        "nelem": run_params.get("nelem"),
        "time_scheme": run_params.get("time_scheme"),
        "cfl": run_params.get("cfl"),
        "max_iters": run_params.get("max_iters"),
        "max_inner_iters": run_params.get("max_inner_iters"),
        "conv_tol": run_params.get("conv_tol"),
        "res_tol": run_params.get("res_tol"),
        "localdt": run_params.get("localdt"),
        "nondim": run_params.get("nondim"),
        "area_equation": run_params.get("area_equation"),
        "reference_values": {
            "rho_ref": run_params.get("rho_ref"),
            "u_ref": run_params.get("u_ref"),
            "p_ref": run_params.get("p_ref"),
        },
    }

    # Build code section (solver-specific; library_versions captured by sweeper via _env)
    code = {
        "_source": "solver",
        "algorithm": run_params.get("linear_solver", "HHL"),
    }
    if sqls_params is not None:
        code["algorithm"] = "SQLS"
        for key, val in sqls_params.items():
            code[f"sqls_{key}"] = val
    # Code provenance from the solver pickle (code_versions, fvm 4f44d5be+;
    # absent in older runs): carried verbatim, plus flat commit keys.
    code_versions = run_params.get("code_versions")
    code["code_versions"] = code_versions
    # fixed-basis counter mode (u3cx | none) and HHL scaling rule
    # (leastsq | true_sol), fvm cca70256+; null when not recorded
    code["circ_metrics"] = run_params.get("circ_metrics")
    code["hhl_scale"] = (None if sqls_params is not None
                         else run_params.get("hhl_scale"))
    # HHL shifted-SVD deflation rank (fvm 8eb40832+; 0 = plain HHL)
    code["hhl_deflate_k"] = run_params.get("hhl_deflate_k")
    for name in ("fvm", "sqls", "linear_solvers"):
        entry = (code_versions or {}).get(name)
        code[f"{name}_commit"] = (
            entry.get("commit") if isinstance(entry, dict) else None
        )

    # Build fragment sections
    backend = _build_backend(run_params, qc_metadata, stdout_text, sqls_params)
    artifacts = _build_artifacts(qc_metadata, file_inventory, sqls=sqls)
    results = _build_results(final_results, residuals, per_iteration,
                             stdout_text)
    analysis = _build_analysis(hhl_metrics, residuals, run_params,
                               dq_by_step, unsteady, stdout_text)
    analysis["deflation_summary"] = _deflation_summary(
        artifacts["transpile_passes"]
    )

    # Write solver-specific fragments (sweeper handles experiment, params, IDs)
    write_case(write_dir, case, experiment_id=experiment_id)
    write_code(write_dir, code, experiment_id=experiment_id)
    write_backend(write_dir, backend, experiment_id=experiment_id)
    write_artifacts(write_dir, artifacts, experiment_id=experiment_id)
    write_results(write_dir, results, experiment_id=experiment_id)
    write_analysis(write_dir, analysis, experiment_id=experiment_id)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate metadata fragments from FVM Euler 1D solver output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  fvm-euler-1d-meta --outdir /tmp/fvm
  fvm-euler-1d-meta /path/to/q8020_case_postproc.json  (sweep postproc mode)
""",
    )
    parser.add_argument(
        "--outdir", "-d",
        type=str,
        default=None,
        help="Path to solver output directory",
    )
    parser.add_argument(
        "postproc_json",
        nargs="?",
        default=None,
        help="Postproc JSON file from sweep (contains case_dir)",
    )

    args = parser.parse_args()

    # Determine outdir and experiment_id from either --outdir or postproc JSON
    experiment_id = None
    if args.postproc_json:
        with open(args.postproc_json, "r", encoding="utf-8") as f:
            postproc_data = json.load(f)
        outdir = Path(postproc_data["case_dir"]).expanduser().resolve()
        experiment_id = postproc_data.get("experiment_id")
    elif args.outdir:
        outdir = Path(args.outdir).expanduser().resolve()
    else:
        print("Error: Must specify --outdir or provide postproc JSON", file=sys.stderr)
        sys.exit(1)

    if not outdir.exists():
        print(f"Error: Output directory does not exist: {outdir}", file=sys.stderr)
        sys.exit(1)

    generate_metadata(outdir, experiment_id=experiment_id)

    print(f"✅ Metadata fragments written to: {outdir}", file=sys.stderr)


if __name__ == "__main__":
    main()
