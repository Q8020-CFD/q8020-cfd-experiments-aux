"""Dump the preset transpiler pass list per optimization level.

Builds the preset pass manager that transpile(circ, AerSimulator()) uses at
levels 0-3, with seed_transpiler 1 as in the sweep patch, and prints every
stage's passes, nesting loops and conditions. Run it with each codebase's
venv python; it writes passes_qiskit<version>.txt next to this file.
"""

import sys
from pathlib import Path

import qiskit
import qiskit_aer
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator


def walk(task, depth: int, out: list[str]) -> None:
    """Append one line per pass; indent the bodies of flow controllers."""
    pad = "  " * depth
    name = type(task).__name__
    children = getattr(task, "tasks", None)
    if children is None:
        out.append(f"{pad}{name}")
        return
    if name == "FlowControllerLinear":
        for child in children:
            walk(child, depth, out)
        return
    out.append(f"{pad}[{name}]")
    for child in children:
        walk(child, depth + 1, out)


def main() -> None:
    backend = AerSimulator()
    target = backend.target
    lines = [
        f"qiskit {qiskit.__version__}, qiskit-aer {qiskit_aer.__version__}, "
        f"python {sys.version.split()[0]}",
        f"AerSimulator target: num_qubits={target.num_qubits}, "
        f"coupling_map={target.build_coupling_map()}, "
        f"{len(target.operation_names)} operations",
        "operations: " + " ".join(sorted(target.operation_names)),
        "",
    ]
    for level in range(4):
        spm = generate_preset_pass_manager(
            optimization_level=level, backend=backend, seed_transpiler=1
        )
        lines.append(f"===== optimization_level {level}")
        for stage in spm.expanded_stages:
            pm = getattr(spm, stage, None)
            if pm is None:
                continue
            body: list[str] = []
            walk(pm.to_flow_controller(), 2, body)
            if body:
                lines.append(f"  {stage}:")
                lines.extend(body)
        lines.append("")
    out = Path(__file__).with_name(f"passes_qiskit{qiskit.__version__}.txt")
    out.write_text("\n".join(lines) + "\n")
    print(out)


if __name__ == "__main__":
    main()
