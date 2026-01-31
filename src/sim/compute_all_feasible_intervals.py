"""
Compute feasible min/max intervals for p_{i,t} for all contestant-week pairs (or selected seasons).

This implements A7.1: for each target variable p_{i,t}, solve two LPs:
 - max p_{i,t} subject to linear constraints (simplex per-week and elimination consistency with xi >= 0)
 - min p_{i,t} subject to same constraints

By default this script runs a demo on season=1 to keep runtime reasonable. Use --season all to run across all seasons.

Outputs a CSV with columns: season, celebrity_name, week, pmin, pmax, p_est (if provided)

Usage examples:
  py compute_all_feasible_intervals.py --panel output/data_cleaned/intermediate_weekly_panel.csv --season 1 --out src/sim/feasible_intervals_season1.csv
  py compute_all_feasible_intervals.py --panel output/data_cleaned/intermediate_weekly_panel.csv --season all --out src/sim/feasible_intervals_all.csv --max-per-season 200
"""
from __future__ import annotations
import argparse
import math
import numpy as np
import pandas as pd
import os
from typing import Dict, List, Tuple

try:
    from scipy.optimize import linprog
except Exception as e:
    raise ImportError("scipy is required (linprog). Install scipy") from e


def build_lp_matrices_for_season(panel_s: pd.DataFrame, alpha: float = 0.5):
    """Build LP matrices similar to earlier helper. Returns mapping and matrices for LP solves."""
    df = panel_s.copy()
    name_col = 'celebrity_name'
    week_col = 'week'
    df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
    weeks = sorted(df[week_col].dropna().unique())
    A_t: Dict[int, List[str]] = {}
    for w in weeks:
        names = df.loc[(df[week_col] == w) & (~df['total_judge_score'].isna()), name_col].astype(str).tolist()
        A_t[w] = sorted(list(dict.fromkeys(names)))

    rev_map: List[Tuple[str,int]] = []
    var_index: Dict[Tuple[str,int],int] = {}
    for w in weeks:
        for name in A_t[w]:
            idx = len(rev_map)
            rev_map.append((name,w))
            var_index[(name,w)] = idx
    n_p = len(rev_map)
    n_xi = len(weeks)
    n_var = n_p + n_xi
    week_to_xi_idx = {w:i for i,w in enumerate(weeks)}

    # A_eq: per-week simplex
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

    # compute qJ
    qJ = {}
    for w in weeks:
        sub = df[df[week_col]==w]
        sub = sub[sub['celebrity_name'].astype(str).isin(A_t[w])]
        totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
        denom = totals.sum()
        if denom == 0:
            for name in A_t[w]:
                qJ[(name,w)] = 1.0/max(1,len(A_t[w]))
        else:
            for _, r in sub.iterrows():
                qJ[(str(r['celebrity_name']), w)] = float(r['total_judge_score'])/float(denom)

    # A_ub, b_ub from elimination constraints
    A_ub_rows = []
    b_ub_rows = []
    elim_col = None
    for cand in ('true_elim_flag','is_elim_exit_week','is_elim','elim'):
        if cand in df.columns:
            elim_col = cand
            break
    if elim_col is not None:
        for w in weeks:
            E = df.loc[(df[week_col]==w) & (df[elim_col].astype(bool)), name_col].astype(str).tolist()
            others = [n for n in A_t[w] if n not in set(E)]
            for e in E:
                for i_name in others:
                    row = np.zeros(n_var)
                    row[var_index[(e,w)]] = (1.0 - alpha)
                    row[var_index[(i_name,w)]] = -(1.0 - alpha)
                    row[n_p + week_to_xi_idx[w]] = -1.0
                    rhs = alpha * (qJ.get((i_name,w),0.0) - qJ.get((e,w),0.0))
                    A_ub_rows.append(row)
                    b_ub_rows.append(rhs)
    A_ub = np.array(A_ub_rows) if A_ub_rows else np.empty((0,n_var))
    b_ub = np.array(b_ub_rows) if b_ub_rows else np.empty((0,))

    bounds = [(0.0,1.0)] * n_p + [(0.0,None)] * n_xi
    return {
        'rev_map': rev_map,
        'var_index': var_index,
        'weeks': weeks,
        'n_var': n_var,
        'n_p': n_p,
        'n_xi': n_xi,
        'A_eq': A_eq,
        'b_eq': b_eq,
        'A_ub': A_ub,
        'b_ub': b_ub,
        'bounds': bounds,
        'A_t': A_t,
    }


def compute_intervals_for_season(panel_s: pd.DataFrame, alpha: float = 0.5, max_targets: int = None):
    mats = build_lp_matrices_for_season(panel_s, alpha=alpha)
    rev_map = mats['rev_map']
    var_index = mats['var_index']
    A_eq = mats['A_eq']; b_eq = mats['b_eq']; A_ub = mats['A_ub']; b_ub = mats['b_ub']; bounds = mats['bounds']
    n_var = mats['n_var']; n_p = mats['n_p']

    results = []
    targets = list(range(n_p))
    if max_targets:
        targets = targets[:max_targets]
    for idx in targets:
        name, w = rev_map[idx]
        # maximize p_idx
        c_max = np.zeros(n_var); c_max[idx] = -1.0
        res_max = linprog(c=c_max, A_ub=A_ub if A_ub.size else None, b_ub=b_ub if b_ub.size else None, A_eq=A_eq if A_eq.size else None, b_eq=b_eq if b_eq.size else None, bounds=bounds, method='highs')
        # minimize p_idx
        c_min = np.zeros(n_var); c_min[idx] = 1.0
        res_min = linprog(c=c_min, A_ub=A_ub if A_ub.size else None, b_ub=b_ub if b_ub.size else None, A_eq=A_eq if A_eq.size else None, b_eq=b_eq if b_eq.size else None, bounds=bounds, method='highs')

        if not res_max.success or not res_min.success:
            pmax = None; pmin = None; note = f"LP fail max:{res_max.message} min:{res_min.message}"
        else:
            pmax = float(-res_max.fun); pmin = float(res_min.fun); note = ''
        results.append({'celebrity_name': name, 'week': w, 'pmin': pmin, 'pmax': pmax, 'note': note})
    return results


def main(argv: list[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--season', required=True, help='season number or "all"')
    p.add_argument('--out', required=True)
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--max-per-season', type=int, default=None, help='limit number of targets per season (for demo)')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '',1).isdigit() else str(x))
    out_rows = []
    if args.season != 'all':
        seasons = [s for s in seasons if str(s) == str(args.season)]
    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        print('Processing season', s)
        res = compute_intervals_for_season(panel_s, alpha=args.alpha, max_targets=args.max_per_season)
        for r in res:
            r['season'] = s
            r['celebrity_name'] = r['celebrity_name']
            out_rows.append(r)
    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(args.out, index=False)
    print('Wrote', args.out)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
