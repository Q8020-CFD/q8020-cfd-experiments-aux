"""HHL (defaults) against QSVT (best shots settings), nelem 5, 150000 shots.

Reads the two case dirs that qsvt_vs_hhl_shots.toml writes (one HHL, one
QSVT) and draws one figure of four panels per outer (Newton) iteration:
relative L2 error of the update against the LU solution, the CFD residual,
the fixed-basis {u3,cx} circuit depth per solve, and the shots kept on the
solution register with the postselection rate. Prints per-step markdown
tables and the cross-checks of the kept-shot counts.

HHL kept shots come from the counts dict its -v 2 stdout prints per solve:
postselected = ancilla 1 and clock register 0, solution register = the
indices the solver keeps (extract_true_sol_from_herm: 16..30 at nelem 5).
QSVT kept shots are qsvt_postselect_shots (ancillas 0); with -pad_eps 0 the
pad amplitudes are exactly zero, checked here by rebuilding integer counts
from the saved update.

Usage:
  ~/.venvs/tooling/bin/python plot_qsvt_vs_hhl_shots.py \
      --hhl <case dir> --qsvt <case dir> --out <png/svg path stem>
"""

import argparse
import ast
import csv
import json
import pickle
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# reference palette (dataviz skill), light mode; validated for 2 slots
SURFACE = '#fcfcfb'
INK = '#0b0b0b'
INK2 = '#52514e'
MUTED = '#898781'
GRID = '#e1e0d9'
AXIS = '#c3c2b7'
COLOR = {'HHL': '#2a78d6', 'QSVT': '#eb6834'}
SMALL_DQ = 1e-6  # mark steps whose ||dq_lu||_2 is below this
NSHOTS = 150000


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f, skipinitialspace=True))
    return [{k.strip(): v for k, v in r.items() if k and k.strip()}
            for r in rows]


def num(v: str) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float('nan')


def stdout_text(case: Path) -> str:
    files = sorted(case.glob('q8020_stdout_*.txt'))
    return files[0].read_text() if files else ''


def load_case(case: Path, log: Path | None) -> dict:
    """Per-step arrays and run facts of one case dir."""
    meta_files = sorted(case.glob('metadata_*.pkl'))
    meta = {}
    if meta_files:
        with open(meta_files[0], 'rb') as f:
            meta = pickle.load(f)
    params = json.loads(next(case.glob('q8020_params_*.json')).read_text())
    solver = params['-linsolver']
    text = stdout_text(case)
    if not text and log is not None and log.exists():
        text = log.read_text()

    # updates: dq_lu and the applied update, one file per solve
    dq_files = {}
    for p in case.glob('dq_nelem*_iter*_statevector*.csv'):
        k = int(re.search(r'_iter(\d+)_', p.name).group(1))
        dq_files[k] = p
    steps = sorted(dq_files)
    rel_l2, dq_lu_norm, dq_list = [], [], []
    for k in steps:
        a = np.loadtxt(dq_files[k], delimiter=',', skiprows=1,
                       usecols=(0, 1))
        dq_lu, dq_x = a[:, 0], a[:, 1]
        nlu = np.linalg.norm(dq_lu)
        rel_l2.append(np.linalg.norm(dq_x - dq_lu) / nlu)
        dq_lu_norm.append(nlu)
        dq_list.append((dq_lu, dq_x))

    # residual entering each step: the end-of-run CSV, else stdout
    res_files = sorted(case.glob('residual_*.csv'))
    if res_files:
        rr = read_csv(res_files[0])
        residual = {int(num(r['iters'])): num(r['residual_total'])
                    for r in rr}
    else:
        residual = {int(m.group(1)): float(m.group(2)) for m in re.finditer(
            r'^step: (\d+)/\d+ res:([0-9.eE+-]+),', text, re.M)}

    qc_glob = ('qc_metadata_qsvt_nelem*.csv' if solver == 'QSVT'
               else 'qc_metadata_nelem*.csv')
    qc_rows = {int(num(r['step'])): r
               for r in read_csv(next(case.glob(qc_glob)))}

    out = {'solver': solver, 'meta': meta, 'params': params,
           'steps': steps, 'rel_l2': np.array(rel_l2),
           'dq_lu_norm': np.array(dq_lu_norm), 'dq': dq_list,
           'residual': residual, 'qc': qc_rows, 'text': text}
    out['depth'] = np.array([num(qc_rows[k]['fb_depth']) for k in steps])
    out['cx'] = np.array([num(qc_rows[k]['fb_cx_count']) for k in steps])
    out['qubits'] = np.array([int(num(qc_rows[k]['circ_qubits']))
                              for k in steps])
    if solver == 'QSVT':
        kept = np.array([num(qc_rows[k]['qsvt_postselect_shots'])
                         for k in steps])
        out['kept_sol'] = kept
        out['postselected'] = kept
        out['t_step'] = np.array([sum(num(qc_rows[k][c]) for c in (
            'qsvt_t_spectral_s', 'qsvt_t_angles_s', 'circ_build_time',
            'circ_run_time', 't_count_s')) for k in steps])
        out['degree'] = np.array([int(num(qc_rows[k]['qsvt_degree']))
                                  for k in steps])
        out['kappa'] = np.array([num(qc_rows[k]['qsvt_kappa'])
                                 for k in steps])
    else:
        hhl_counts(out, qc_rows)
        out['t_step'] = np.array([sum(num(qc_rows[k][c]) for c in (
            'circ_generate_time', 'circ_transpile_time', 'circ_run_time',
            't_count_s')) for k in steps])
        out['kappa'] = np.array([num(qc_rows[k]['condition_number'])
                                 for k in steps])
    return out


def hhl_counts(out: dict, qc_rows: dict) -> None:
    """Kept shots per HHL solve from the counts dicts of the -v 2 stdout."""
    lines = out['text'].splitlines()
    dicts = [ast.literal_eval(lines[i + 1]) for i, s in enumerate(lines)
             if s.strip() == 'counts:' and i + 1 < len(lines)]
    steps = out['steps']
    if len(dicts) != len(steps):
        raise SystemExit(f'HHL: {len(dicts)} counts dicts for '
                         f'{len(steps)} solves')
    kept_sol, posts, checks = [], [], []
    for k, counts, (dq_lu, dq_x) in zip(steps, dicts, out['dq']):
        herm = int(num(qc_rows[k]['matrix_size_herm']))
        nq = herm.bit_length() - 1
        nsys = int(num(qc_rows[k]['matrix_size_orig']))
        npow2 = int(num(qc_rows[k]['matrix_size_pow2']))
        hist = np.zeros(herm)
        for key, c in counts.items():
            bits = key.replace(' ', '')
            pre = '1' + '0' * (len(bits) - nq - 1)
            if bits.startswith(pre):
                hist[int(bits[-nq:], 2)] += c
        sol = hist[npow2:npow2 + nsys]
        kept_sol.append(sol.sum())
        posts.append(hist.sum())
        # mapping check: |dq_hhl_i| / sqrt(count_i) constant where both > 0
        m = (sol > 0) & (np.abs(dq_lu) > 1e-8)
        ratio = np.abs(dq_x[m]) / np.sqrt(sol[m])
        zero_ok = bool(np.all(dq_x[sol == 0] == 0))
        spread = (float(np.ptp(ratio) / np.mean(ratio)) if m.sum() > 1
                  else float('nan'))
        checks.append((k, spread, zero_ok))
    out['kept_sol'] = np.array(kept_sol)
    out['postselected'] = np.array(posts)
    out['count_check'] = checks


def qsvt_check(case: dict) -> list[tuple]:
    """Rebuild integer counts from the QSVT update: |dq_i| = s sqrt(c_i)
    (1 + 1e-15/|dq_lu_i|)^-1, sum c_i = qsvt_postselect_shots if the pad
    holds no shot. Returns (step, max |c - round(c)|, sum c)."""
    res = []
    for k, (dq_lu, dq_x), kept in zip(case['steps'], case['dq'],
                                      case['kept_sol']):
        f = np.abs(dq_lu) / (np.abs(dq_lu) + 1e-15)
        r = np.where(f > 0, (np.abs(dq_x) / np.where(f > 0, f, 1)) ** 2, 0)
        c = kept * r / r.sum()
        res.append((k, float(np.max(np.abs(c - np.round(c)))),
                    float(c.sum())))
    return res


def stop_label(case: dict) -> str:
    meta = case['meta']
    m = re.search(r'error: (.*) \(step (\d+)\)', case['text'])
    if not meta and m:
        return f'stopped at step {m.group(2)}: no kept shot'
    if meta.get('converged'):
        return f"converged ({meta['converged_by']}) at step " \
               f"{meta['final_iters']}"
    return f"cap reached: {meta.get('max_iters')} solves (steps 0 to " \
           f"{meta.get('final_iters')}), not converged"


def style_axis(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(1)
    ax.tick_params(colors=MUTED, labelcolor=INK2, labelsize=10, width=1)
    ax.grid(True, color=GRID, linewidth=1, linestyle='-')
    ax.set_axisbelow(True)


def line(ax, x, y, solver, hollow=None, **kw):
    """2 px series line, 8 px markers with a 2 px surface ring; hollow
    marks the steps flagged by the boolean mask."""
    c = COLOR[solver]
    ax.plot(x, y, color=c, linewidth=2, solid_capstyle='round',
            solid_joinstyle='round', zorder=3, **kw)
    x, y = np.asarray(x), np.asarray(y)
    mask = np.zeros(len(x), bool) if hollow is None else np.asarray(hollow)
    ax.scatter(x[~mask], y[~mask], s=64, color=c, edgecolors=SURFACE,
               linewidths=2, zorder=4)
    if mask.any():
        ax.scatter(x[mask], y[mask], s=64, facecolors=SURFACE,
                   edgecolors=c, linewidths=2, zorder=4)


def end_label(ax, x, y, text, dy=0) -> None:
    ax.annotate(text, (x, y), xytext=(8, dy), textcoords='offset points',
                color=INK2, fontsize=10, va='center')


def make_figure(hhl: dict, qsvt: dict, out_stem: Path, commit: str) -> None:
    plt.rcParams['font.family'] = ['Helvetica Neue', 'Helvetica', 'Arial',
                                   'DejaVu Sans']
    fig, axes = plt.subplots(2, 2, figsize=(16, 10.6), dpi=100,
                             sharex=True, facecolor=SURFACE)
    (a1, a2), (a3, a4) = axes
    for ax in axes.flat:
        style_axis(ax)
    cases = (hhl, qsvt)
    kmax = max(max(c['steps']) for c in cases)

    # 1. relative L2 error of the update vs LU
    for c in cases:
        small = c['dq_lu_norm'] < SMALL_DQ
        line(a1, c['steps'], c['rel_l2'], c['solver'], hollow=small)
    a1.set_yscale('log')
    a1.set_title(r'Relative L2 error of the update vs LU, '
                 r'$\|dq - dq_{LU}\|_2\, /\, \|dq_{LU}\|_2$', loc='left',
                 color=INK, fontsize=12)
    a1.set_ylabel('relative L2 error (dimensionless)', color=INK2)

    # 2. CFD residual entering each step
    for i, c in enumerate(cases):
        ks = sorted(c['residual'])
        rs = [c['residual'][k] for k in ks]
        line(a2, ks, rs, c['solver'])
        # run outcome, a colored key beside ink text, top right
        y = 0.95 - 0.08 * i
        a2.scatter([0.40], [y], s=64, color=COLOR[c['solver']],
                   edgecolors=SURFACE, linewidths=2, transform=a2.transAxes,
                   clip_on=False, zorder=5)
        a2.text(0.42, y, f"{c['solver']}: {stop_label(c)}", color=INK2,
                fontsize=10, va='center', transform=a2.transAxes)
    tol = hhl['meta'].get('conv_tol', 1e-12) * \
        hhl['meta'].get('resnorm_init', np.nan)
    a2.axhline(tol, color=AXIS, linewidth=1, zorder=2)
    a2.annotate('residual-ratio tolerance, '
                f"{hhl['meta'].get('conv_tol', 1e-12):g} x initial "
                '(the run also stops when every |dq| <= 1e-10)', (0, tol),
                xytext=(2, -12), textcoords='offset points', color=MUTED,
                fontsize=9)
    a2.set_yscale('log')
    a2.set_ylim(bottom=tol / 30)
    a2.set_title(r'CFD residual $\|R(q_k)\|_2$ entering step k',
                 loc='left', color=INK, fontsize=12)
    a2.set_ylabel('residual (non-dimensional)', color=INK2)

    # 3. fixed-basis depth per solve
    for c in cases:
        line(a3, c['steps'], c['depth'] / 1e6, c['solver'])
        q = sorted(set(c['qubits']))
        qtxt = '–'.join(str(v) for v in (q if len(q) < 3 else
                                         (q[0], q[-1])))
        end_label(a3, c['steps'][-1], c['depth'][-1] / 1e6,
                  f"{c['solver']}, {qtxt} qubits")
    a3.set_ylim(bottom=0)
    a3.set_title('Circuit depth per solve, fixed basis {u3, cx}',
                 loc='left', color=INK, fontsize=12)
    a3.set_ylabel('depth (million layers)', color=INK2)

    # 4. kept shots on the solution register, rate on a unit axis
    for c in cases:
        line(a4, c['steps'], c['kept_sol'], c['solver'])
    a4.set_yscale('log')
    sec = a4.secondary_yaxis('right', functions=(lambda s: s / NSHOTS,
                                                 lambda r: r * NSHOTS))
    sec.set_ylabel('postselection rate (fraction of 150000 shots)',
                   color=INK2)
    sec.tick_params(colors=MUTED, labelcolor=INK2, labelsize=10)
    sec.spines['right'].set_color(AXIS)
    a4.set_title('Shots kept on the solution register, of 150000',
                 loc='left', color=INK, fontsize=12)
    a4.set_ylabel('kept shots (count)', color=INK2)

    for ax in (a3, a4):
        ax.set_xlabel('outer (Newton) iteration k', color=INK2)
    for ax in axes.flat:
        ax.set_xlim(-0.5, kmax + 3.5)
        ax.set_xticks(range(0, kmax + 2, 2))
        ax.tick_params(labelbottom=True)

    # legend: series identity plus the two marker conventions
    handles = [
        Line2D([], [], color=COLOR['HHL'], lw=2, marker='o', ms=8,
               mec=SURFACE, mew=2, label='HHL, defaults'),
        Line2D([], [], color=COLOR['QSVT'], lw=2, marker='o', ms=8,
               mec=SURFACE, mew=2, label='QSVT, best shots settings'),
        Line2D([], [], color=MUTED, lw=0, marker='o', ms=8, mfc=SURFACE,
               mec=MUTED, mew=2,
               label=r'hollow (top left): $\|dq_{LU}\|_2 < 10^{-6}$'),
    ]
    fig.legend(handles=handles, loc='upper left', ncol=4, frameon=False,
               bbox_to_anchor=(0.045, 0.935), fontsize=10,
               labelcolor=INK2, handlelength=2.2)

    seed = hhl['meta'].get('seed')
    hm, qm = hhl['meta'], qsvt['meta']
    hhl_off = int(np.sum(hhl['postselected'] - hhl['kept_sol']))
    fig.suptitle('FVM Euler 1D nozzle, nelem 5: HHL (defaults: pad '
                 f'{hm.get("pad_eps", 1e-8):g}, sign-first '
                 f'{hm.get("hhl_shots_sign_first", "off")}) vs QSVT '
                 f'(sign-first {qm.get("qsvt_shots_sign_first")}, pad '
                 f'{qm.get("pad_eps", 0):g}), 150000 shots, seed {seed}, '
                 f'fvm {commit}', x=0.045, y=0.985, ha='left', color=INK,
                 fontsize=15, fontweight='semibold')
    caption = (
        f'Both: steady Newton (BDF1, local dt, CFL {hm.get("cfl", 1e10):g}),'
        f' at most {hm.get("max_iters", 20)} iterations, ideal Aer '
        f'simulator with 150000 shots per solve, seed {seed}, fvm_euler_1d_'
        f'solver {commit}. HHL: every option at its default (pad_eps '
        f'{hm.get("pad_eps", 1e-8):g}, hhl_shots_sign_first '
        f'{hm.get("hhl_shots_sign_first", "off")}, hhl_scale '
        f'{hm.get("hhl_scale", "leastsq")}, hhl_spectrum '
        f'{hm.get("hhl_spectrum", "library")}); kept shots read from its '
        f'-v 2 counts (ancilla 1, clock 0, system indices 16 to 30; '
        f'{hhl_off} postselected shots in the whole run fell off them).\n'
        f'QSVT: qsvt_shots_sign_first {qm.get("qsvt_shots_sign_first")}, '
        f'pad_eps {qm.get("pad_eps", 0):g}, qsvt_eps '
        f'{qm.get("qsvt_eps"):g}, angle solver '
        f'{qm.get("qsvt_angle_solver")}; kept shots = ancillas 0 (pad holds '
        'none at pad_eps 0). Depth: whole circuit (state preparation and '
        'solver, no measurement) transpiled to {u3, cx}. dq_LU: scipy LU '
        'solution of the Newton system A dq = b.')
    fig.text(0.045, 0.012, caption, ha='left', va='bottom', color=INK2,
             fontsize=9.5, wrap=True)
    fig.subplots_adjust(left=0.07, right=0.93, top=0.87, bottom=0.13,
                        hspace=0.28, wspace=0.22)
    png, svg = out_stem.with_suffix('.png'), out_stem.with_suffix('.svg')
    fig.savefig(png, dpi=100, facecolor=SURFACE)
    fig.savefig(svg, facecolor=SURFACE)
    plt.close(fig)
    print(f'wrote {png}\nwrote {svg}')


def fmt(v: float, spec: str = '.3e') -> str:
    return '' if v is None or not np.isfinite(v) else format(v, spec)


def print_tables(c: dict) -> None:
    solver = c['solver']
    print(f'\n### {solver}\n')
    head = ['step', '‖dq_LU‖₂', 'rel L2 vs dq_LU', 'residual entering step',
            'qubits', 'fb_depth (layers)', 'fb_cx_count (gates)',
            'kept on solution register (shots)',
            'postselected, all indices (shots)', 'postselection rate',
            'step wall time (s)']
    if solver == 'QSVT':
        head.insert(5, 'qsvt_degree')
    print('| ' + ' | '.join(head) + ' |')
    print('|' + '---|' * len(head))
    for i, k in enumerate(c['steps']):
        row = [str(k), fmt(c['dq_lu_norm'][i]), fmt(c['rel_l2'][i]),
               fmt(c['residual'].get(k, float('nan'))),
               str(c['qubits'][i]), f"{int(c['depth'][i])}",
               f"{int(c['cx'][i])}", f"{int(c['kept_sol'][i])}",
               f"{int(c['postselected'][i])}",
               fmt(c['postselected'][i] / NSHOTS, '.5f'),
               fmt(c['t_step'][i], '.1f')]
        if solver == 'QSVT':
            row.insert(5, str(c['degree'][i]))
        print('| ' + ' | '.join(row) + ' |')
    extra = sorted(set(c['residual']) - set(c['steps']))
    for k in extra:
        print(f'\nresidual row {k} (no solve): '
              f'{fmt(c["residual"][k])}')


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--hhl', type=Path, required=True)
    ap.add_argument('--qsvt', type=Path, required=True)
    ap.add_argument('--hhl-log', type=Path, default=None)
    ap.add_argument('--qsvt-log', type=Path, default=None)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    hhl = load_case(args.hhl, args.hhl_log)
    qsvt = load_case(args.qsvt, args.qsvt_log)
    for c in (hhl, qsvt):
        cv = c['meta'].get('code_versions', {})
        lib = {k: v for k, v in cv.items() if isinstance(v, str)}
        print(f"{c['solver']}: fvm {cv.get('fvm', {}).get('commit')} dirty "
              f"{cv.get('fvm', {}).get('dirty')}, linear_solvers "
              f"{cv.get('linear_solvers', {}).get('commit')}, {lib}")
    cv = hhl['meta'].get('code_versions') or qsvt['meta'].get(
        'code_versions') or {}
    commit = str(cv.get('fvm', {}).get('commit', ''))[:7]
    for c in (hhl, qsvt):
        print(f"{c['solver']}: {stop_label(c)}, elapsed_time "
              f"{c['meta'].get('elapsed_time', float('nan')):.1f} s")
    print('\nHHL count mapping check (step, spread of |dq|/sqrt(count), '
          'zeros match):')
    for k, spread, zok in hhl['count_check']:
        print(f'  {k}: {spread:.2e} {zok}')
    print('\nQSVT pad check (step, max |c - round(c)|, sum c):')
    for k, dev, tot in qsvt_check(qsvt):
        print(f'  {k}: {dev:.2e} {tot:.3f}')
    make_figure(hhl, qsvt, args.out, commit)
    for c in (hhl, qsvt):
        print_tables(c)


if __name__ == '__main__':
    main()
