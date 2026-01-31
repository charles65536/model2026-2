"""
Compute feasible min/max intervals for selected p_{i,t} under the model constraints (no smoothness).

Reads:
 - panel CSV: output/data_cleaned/intermediate_weekly_panel.csv
 - p_est CSV: src/sim/test_fan_p.csv (or other)

For each requested target (season, week, celebrity_name) this script solves two LPs:
 - maximize p_{target} subject to per-week simplex and elimination-consistency constraints (with xi >=0 allowed)
 - minimize p_{target} similarly

This provides feasible bounds p_min, p_max consistent with the elimination constraints (but NOT the smoothness prior).

Usage example:
  py compute_feasible_intervals.py --panel "output/data_cleaned/intermediate_weekly_panel.csv" --pest "src/sim/test_fan_p.csv" --alpha 0.5 --show-sample

Note: LP can be heavier for long seasons; we only compute intervals for a small subset of targets (near-zero p_est entries) by default.
"""
from __future__ import annotations
import argparse
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

try:
    from scipy.optimize import linprog
except Exception as e:
    raise ImportError("scipy is required (linprog). Install scipy") from e


def build_lp_matrices(season_panel: pd.DataFrame, alpha: float = 0.5):
    """Construct LP matrices for a season. Variables: all p_{i,t} (ordered by week then name), then xi_t for each week.

    Returns:
      - var_index: dict mapping (name,week) -> idx
      - week_index: list of weeks
      - A_eq, b_eq, A_ub, b_ub, bounds
    """
    df = season_panel.copy()
    name_col = 'celebrity_name' if 'celebrity_name' in df.columns else [c for c in df.columns if df[c].dtype==object][0]
    week_col = 'week'

    df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
    weeks = sorted(df[week_col].dropna().unique())
    A_t: Dict[int, List[str]] = {}
    for w in weeks:
        names = df.loc[(df[week_col]==w) & (~df['total_judge_score'].isna()) , name_col].astype(str).tolist()
        A_t[w] = sorted(list(dict.fromkeys(names)))

    # variable ordering
    rev_map: List[Tuple[str, int]] = []
    var_index: Dict[Tuple[str, int], int] = {}
    for w in weeks:
        for name in A_t[w]:
            idx = len(rev_map)
            rev_map.append((name, w))
            var_index[(name, w)] = idx
    n_p = len(rev_map)
    n_xi = len(weeks)

    # xi index mapping
    week_to_xi_idx = {w: i for i,w in enumerate(weeks)}
    # total variables = n_p + n_xi
    n_var = n_p + n_xi

    # Equality constraints: per-week simplex sum p = 1
    A_eq = []
    b_eq = []
    for w in weeks:
        row = np.zeros(n_var)
        for name in A_t[w]:
            row[var_index[(name,w)]] = 1.0
        A_eq.append(row)
        b_eq.append(1.0)
    A_eq = np.array(A_eq) if A_eq else np.empty((0,n_var))
    b_eq = np.array(b_eq) if b_eq else np.empty((0,))

    # Inequality constraints: elimination consistency
    # We expect column marking eliminated rows, try common names
    elim_col = None
    for cand in ('true_elim_flag','is_elim_exit_week','is_elim'):
        if cand in df.columns:
            elim_col = cand
            break
    # Prepare qJ per (name,w)
    qJ = {}
    for w in weeks:
        sub = df[df[week_col]==w]
        # consider only rows present in A_t[w]
        sub = sub[sub[name_col].astype(str).isin(A_t[w])]
        totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
        denom = totals.sum()
        if denom == 0:
            for name in A_t[w]:
                qJ[(name,w)] = 1.0/max(1,len(A_t[w]))
        else:
            for _,r in sub.iterrows():
                qJ[(str(r[name_col]), w)] = float(r['total_judge_score'])/float(denom)

    A_ub_rows = []
    b_ub_rows = []
    if elim_col is not None:
        for w in weeks:
            E = df.loc[(df[week_col]==w) & (df[elim_col].astype(bool)), name_col].astype(str).tolist()
            others = [n for n in A_t[w] if n not in set(E)]
            for e in E:
                for i_name in others:
                    row = np.zeros(n_var)
                    # (1-alpha)*(p_e - p_i) - xi <= alpha*(qJ_i - qJ_e)
                    row[var_index[(e,w)]] = (1.0 - alpha)
                    row[var_index[(i_name,w)]] = -(1.0 - alpha)
                    # xi term coefficient (-1) -> move to LHS: -xi <= RHS => row at xi index = -1
                    row[n_p + week_to_xi_idx[w]] = -1.0
                    rhs = alpha * (qJ.get((i_name,w),0.0) - qJ.get((e,w),0.0))
                    A_ub_rows.append(row)
                    b_ub_rows.append(rhs)
    # If no elim_col, no inequality constraints; we still allow xi>=0 but they won't be used
    A_ub = np.array(A_ub_rows) if A_ub_rows else np.empty((0,n_var))
    b_ub = np.array(b_ub_rows) if b_ub_rows else np.empty((0,))

    # bounds: p in [0,1] (the solver earlier allowed >=0 but not forced <=1; we can limit to [0,1] for LP)
    bounds = [(0.0, 1.0)] * n_p + [(0.0, None)] * n_xi

    return {
        'rev_map': rev_map,
        'var_index': var_index,
        'weeks': weeks,
        'n_var': n_var,
        'A_eq': A_eq,
        'b_eq': b_eq,
        'A_ub': A_ub,
        'b_ub': b_ub,
        'bounds': bounds,
        'n_p': n_p,
        'n_xi': n_xi,
        'week_to_xi_idx': week_to_xi_idx,
    }


def compute_interval_for_target(season_panel, alpha, target, lp_mats):
    # target = (name, week)
    rev_map = lp_mats['rev_map']
    var_index = lp_mats['var_index']
    n_var = lp_mats['n_var']
    A_eq = lp_mats['A_eq']
    b_eq = lp_mats['b_eq']
    A_ub = lp_mats['A_ub']
    b_ub = lp_mats['b_ub']
    bounds = lp_mats['bounds']

    tgt_idx = var_index.get((target[0], target[1]), None)
    if tgt_idx is None:
        return None

    # linprog minimizes c^T x. For maximizing p_tgt, minimize -p_tgt.
    c_max = np.zeros(n_var);
    c_max[tgt_idx] = -1.0
    res_max = linprog(c=c_max, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    c_min = np.zeros(n_var);
    c_min[tgt_idx] = 1.0
    res_min = linprog(c=c_min, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

    if not res_max.success or not res_min.success:
        return {
            'success_max': res_max.success,
            'message_max': res_max.message,
            'success_min': res_min.success,
            'message_min': res_min.message,
        }

    pmax = float(-res_max.fun)
    pmin = float(res_min.fun)
    return {'pmin': pmin, 'pmax': pmax, 'success_max': True, 'success_min': True}


def main(argv: List[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', required=True, help='p_est CSV')
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--threshold', type=float, default=1e-6, help='near-zero threshold')
    p.add_argument('--show-sample', action='store_true')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest = pd.read_csv(args.pest)
    pest['p_est'] = pd.to_numeric(pest['p_est'], errors='coerce').fillna(0.0)

    # find near-zero entries
    near = pest[pest['p_est'].abs() <= args.threshold].copy()
    print(f"Found {len(near)} near-zero entries with threshold {args.threshold}")
    # group by season, process each season
    results = []
    for season, group in near.groupby('season'):
        print(f"Processing season {season} with {len(group)} near-zero targets (will compute intervals)")
        panel_s = panel[panel['season'].astype(str) == str(season)].copy()
        lp_mats = build_lp_matrices(panel_s, alpha=args.alpha)
        # limit to a sample of up to 10 targets to keep runtime reasonable
        targets = group[['celebrity_name','week']].drop_duplicates().values.tolist()[:10]
        for name, week in targets:
            info = compute_interval_for_target(panel_s, args.alpha, (str(name), int(week)), lp_mats)
            row = {'season': season, 'celebrity_name': name, 'week': week, 'p_est': float(group[(group['celebrity_name']==name) & (group['week']==week)]['p_est'].iloc[0])}
            if info is None:
                row.update({'pmin': None, 'pmax': None, 'note': 'target not in rev_map'})
            elif not info.get('success_max', False) or not info.get('success_min', False):
                row.update({'pmin': None, 'pmax': None, 'note': f"LP failed: max_msg={info.get('message_max')} min_msg={info.get('message_min')}"})
            else:
                row.update({'pmin': info['pmin'], 'pmax': info['pmax'], 'note': ''})
            results.append(row)

    out = pd.DataFrame(results)
    if args.show_sample:
        print(out.to_string(index=False))
    out.to_csv('src/sim/feasible_intervals_sample.csv', index=False)
    print('Wrote src/sim/feasible_intervals_sample.csv')


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
