from __future__ import annotations

import argparse
import os
from typing import Dict, List

import numpy as np
import pandas as pd

try:
    from scipy.optimize import linprog
except Exception:
    linprog = None

from src.tools.paths import EVAL_DIR


def build_week_participants(panel_s: pd.DataFrame) -> Dict[int, List[str]]:
    df = panel_s.copy()
    if 'week' in df.columns:
        df['week'] = pd.to_numeric(df['week'], errors='coerce')
    weeks = sorted(df['week'].dropna().unique()) if 'week' in df.columns and df['week'].notna().any() else []
    if (len(weeks) <= 1) and ('exit_week' in df.columns):
        df['exit_week'] = pd.to_numeric(df['exit_week'], errors='coerce')
        max_w = int(df['exit_week'].max()) if not df['exit_week'].isna().all() else 1
        A_t = {}
        for w in range(1, max_w + 1):
            names = df.loc[df['exit_week'].fillna(max_w) >= w, 'celebrity_name'].dropna().astype(str).tolist()
            A_t[int(w)] = sorted(list(dict.fromkeys(names)))
        return A_t
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t


def infer_elim_counts_from_col(panel_s: pd.DataFrame, elim_col: str) -> Dict[int, int]:
    panel_s = panel_s.copy()
    panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
    weeks = sorted(panel_s['week'].dropna().unique())
    m = {}
    if elim_col not in panel_s.columns:
        return {int(w): 0 for w in weeks}
    for w in weeks:
        mask = (panel_s['week'] == w) & (panel_s[elim_col].astype(bool))
        m[int(w)] = int(mask.sum())
    return m


def compute_qJ_for_week(panel_s: pd.DataFrame, week: int, active: List[str]) -> Dict[str, float]:
    sub = panel_s[panel_s['week'] == week]
    sub = sub[sub['celebrity_name'].astype(str).isin(active)]
    if sub.empty:
        return {name: 1.0 / max(1, len(active)) for name in active}
    totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
    denom = totals.sum()
    if denom == 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    name_to_score = {str(r['celebrity_name']): float(r['total_judge_score']) for _, r in sub.iterrows()}
    q = {name: name_to_score.get(str(name), 0.0) / denom for name in active}
    s = sum(q.values())
    if s <= 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for k in q:
        q[k] /= s
    return q


def get_p_for_week(pest_s: pd.DataFrame, week: int, active: List[str]) -> Dict[str, float]:
    sub = pest_s[pest_s['week'] == week]
    sub = sub[sub['celebrity_name'].astype(str).isin(active)]
    p_map = {name: 0.0 for name in active}
    if sub.empty:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for _, r in sub.iterrows():
        p_map[str(r['celebrity_name'])] = float(r['p_est'])
    s = sum(p_map.values())
    if s <= 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for k in p_map:
        p_map[k] /= s
    return p_map


def perturb_p(p_map: Dict[str, float], sigma: float, rng: np.random.Generator) -> Dict[str, float]:
    names = list(p_map.keys())
    base = np.array([p_map[n] for n in names], dtype=float)
    noise = rng.normal(loc=0.0, scale=sigma, size=base.shape)
    pert = base * np.exp(noise)
    s = pert.sum()
    if s <= 0:
        pert = np.ones_like(pert) / len(pert)
    else:
        pert = pert / s
    return {names[i]: float(pert[i]) for i in range(len(names))}


def perturb_flip_and_collect(panel_s: pd.DataFrame, pest_s: pd.DataFrame, alpha: float, sigma: float, B: int, elim_col: str):
    A_t = build_week_participants(panel_s)
    if not A_t:
        return [], []
    weeks = sorted(A_t.keys())
    m_map = infer_elim_counts_from_col(panel_s, elim_col)
    rng = np.random.default_rng(12345)

    per_contestant_rows = []
    per_week_rows = []

    for w in weeks:
        active = list(A_t[w])
        if not active:
            continue
        m = m_map.get(w, 0)
        qJ = compute_qJ_for_week(panel_s, w, active)
        pmap = get_p_for_week(pest_s, w, active)

        # determine true eliminated set for this week
        true_elims = panel_s[(panel_s['week'] == w) & (panel_s.get(elim_col, False))]['celebrity_name'].astype(str).tolist()
        # fallback: use exit_week==w and exit_type contains 'eliminated'
        if len(true_elims) == 0 and 'exit_week' in panel_s.columns:
            true_elims = panel_s[(panel_s['exit_week'] == w) & (panel_s['exit_type'].astype(str).str.contains('eliminated', case=False, na=False))]['celebrity_name'].astype(str).tolist()
        true_elims = [str(x) for x in true_elims]

        # collect per-sample eliminated set equality and perturbed p_est samples
        match_count = 0
        samples = {name: [] for name in active}

        for b in range(B):
            pm = perturb_p(pmap, sigma, rng)
            for name in active:
                samples[name].append(pm.get(name, 0.0))

            # compute S and pick m lowest
            S = {name: alpha * qJ.get(name, 0.0) + (1.0 - alpha) * pm.get(name, 0.0) for name in active}
            sorted_names = sorted(active, key=lambda n: (S.get(n, 0.0), panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == n)]['total_judge_score'].astype(float).sum(), pmap.get(n, 0.0)))
            pred_elim = sorted_names[:m] if m > 0 else []
            if set(pred_elim) == set(true_elims):
                match_count += 1

        flip_rate = match_count / float(B) if B > 0 else None

        # record per-contestant credible intervals
        for name in active:
            arr = np.array(samples[name], dtype=float)
            p_hat = float(pmap.get(name, 0.0))
            p5 = float(np.percentile(arr, 5))
            p95 = float(np.percentile(arr, 95))
            rel_width = (p95 - p5) / (p_hat + 1e-12)
            per_contestant_rows.append({'week': w, 'celebrity_name': name, 'p_est_hat': p_hat, 'p5': p5, 'p95': p95, 'rel_ci_width': rel_width, 'flip_rate': flip_rate, 'm': m, 'active_count': len(active)})

        per_week_rows.append({'week': w, 'flip_rate': flip_rate, 'm': m, 'active_count': len(active)})

    return per_contestant_rows, per_week_rows


def feasible_intervals_lp(panel_s: pd.DataFrame, pest_s: pd.DataFrame, alpha: float, elim_col: str):
    if linprog is None:
        raise RuntimeError('scipy.linprog not available; install scipy to compute feasible intervals')

    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())
    m_map = infer_elim_counts_from_col(panel_s, elim_col)

    rows = []
    for w in weeks:
        active = list(A_t[w])
        if not active:
            continue
        m = m_map.get(w, 0)
        qJ = compute_qJ_for_week(panel_s, w, active)

        # find true eliminated set similarly to perturb
        true_elims = panel_s[(panel_s['week'] == w) & (panel_s.get(elim_col, False))]['celebrity_name'].astype(str).tolist()
        if len(true_elims) == 0 and 'exit_week' in panel_s.columns:
            true_elims = panel_s[(panel_s['exit_week'] == w) & (panel_s['exit_type'].astype(str).str.contains('eliminated', case=False, na=False))]['celebrity_name'].astype(str).tolist()
        true_elims = [str(x) for x in true_elims]

        n = len(active)
        name_idx = {name: i for i, name in enumerate(active)}

        # Build constraints: v_i >= 0, sum v_i = 1
        # For each eliminated e and non-elim j, require S_e <= S_j -> v_e - v_j <= alpha/(1-alpha)*(qJ_j - qJ_e)
        A_ub = []
        b_ub = []
        for e in true_elims:
            for j in active:
                if j in true_elims:
                    continue
                row = [0.0] * n
                row[name_idx[e]] = 1.0
                row[name_idx[j]] = -1.0
                rhs = (alpha / (1.0 - alpha)) * (qJ.get(j, 0.0) - qJ.get(e, 0.0))
                A_ub.append(row)
                b_ub.append(rhs)

        # equality sum v_i = 1
        A_eq = [[1.0] * n]
        b_eq = [1.0]

        bounds = [(0.0, 1.0) for _ in range(n)]

        # For each variable, minimize and maximize
        for name in active:
            c_min = [0.0] * n
            c_min[name_idx[name]] = 1.0
            res_min = linprog(c=c_min, A_ub=A_ub if A_ub else None, b_ub=b_ub if A_ub else None, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            c_max = [-x for x in c_min]
            res_max = linprog(c=c_max, A_ub=A_ub if A_ub else None, b_ub=b_ub if A_ub else None, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
            vmin = float(res_min.x[name_idx[name]]) if res_min.success else None
            vmax = float(res_max.x[name_idx[name]]) if res_max.success else None
            rows.append({'week': w, 'celebrity_name': name, 'vmin': vmin, 'vmax': vmax, 'm': m, 'active_count': n})

    return rows


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', required=True)
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--sigma', type=float, default=0.1, help='std dev for log-normal perturbation')
    p.add_argument('--B', type=int, default=200, help='Monte Carlo samples')
    p.add_argument('--elim-col', default='true_elim_flag')
    p.add_argument('--out-dir', default=str(EVAL_DIR))
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest = pd.read_csv(args.pest)

    per_contestant, per_week = perturb_flip_and_collect(panel, pest, args.alpha, args.sigma, args.B, args.elim_col)
    out_c = os.path.join(args.out_dir, f'credibility_contestant_B{args.B}_sigma{args.sigma}.csv')
    out_w = os.path.join(args.out_dir, f'credibility_week_B{args.B}_sigma{args.sigma}.csv')
    pd.DataFrame(per_contestant).to_csv(out_c, index=False)
    pd.DataFrame(per_week).to_csv(out_w, index=False)
    print('Wrote', out_c, out_w)

    # feasible intervals
    try:
        rows = feasible_intervals_lp(panel, pest, args.alpha, args.elim_col)
        out_f = os.path.join(args.out_dir, f'credibility_feasible_intervals.csv')
        pd.DataFrame(rows).to_csv(out_f, index=False)
        print('Wrote', out_f)
    except RuntimeError as e:
        print('Skipping feasible interval LP:', str(e))


if __name__ == '__main__':
    main()
