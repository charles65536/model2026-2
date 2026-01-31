"""
Replay simulator for Percent and Rank rules.

Produces per-week predicted elimination lists and final ranking by simulating eliminations sequentially.

Usage examples:
  py src/sim/replay_simulator.py --panel output/data_cleaned/intermediate_weekly_panel.csv --pest src/sim/fan_shares_entropy_1.0.csv --season 1 --alpha 0.5

Outputs:
 - src/sim/replay_percent_season{S}.csv
 - src/sim/replay_rank_season{S}.csv
 - src/sim/replay_summary_season{S}.csv (combined)

Notes:
 - Tie-breaks: for Percent rule (lower S worse) tie broken by lower judge score, lower p_est, then name.
 - For Rank rule: rank_J and rank_V (descending) summed; higher sum worse; ties broken by lower judge score, lower p_est, then name.
 - The simulator constructs an initial active set from the earliest week in the panel for the season and removes predicted eliminated contestants sequentially.
"""
from __future__ import annotations
import argparse
import os
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


def choose_default_pest():
    candidates = [
        'src/sim/fan_shares_entropy_1.0.csv',
        'src/sim/fan_shares_entropy.csv',
        'src/sim/fan_shares_refined.csv',
        'src/sim/test_fan_p.csv',
        'src/sim/fan_shares.csv',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError('No p_est file found; generate one with src/sim/model_main.py')


def build_week_participants(panel_s: pd.DataFrame) -> Dict[int, List[str]]:
    panel_s = panel_s.copy()
    # If the panel is already weekly (multiple rows per week), use that directly.
    panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
    weeks = sorted(panel_s['week'].dropna().unique())
    # Heuristic: if the dataset only contains one week but contains 'exit_week', it's a contestant-level panel.
    if len(weeks) <= 1 and 'exit_week' in panel_s.columns:
        # reconstruct weeks from 1..max_exit
        panel_s['exit_week'] = pd.to_numeric(panel_s['exit_week'], errors='coerce')
        max_w = int(panel_s['exit_week'].max()) if not panel_s['exit_week'].isna().all() else 1
        A_t = {}
        for w in range(1, max_w + 1):
            # active if exit_week >= w (they participated up to and including their exit week)
            names = panel_s.loc[panel_s['exit_week'].fillna(max_w) >= w, 'celebrity_name'].dropna().astype(str).tolist()
            A_t[int(w)] = sorted(list(dict.fromkeys(names)))
        return A_t
    # otherwise treat as weekly panel already
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t


def infer_elim_counts(A_t: Dict[int, List[str]]) -> Dict[int, int]:
    # Infer elimination counts by checking which names disappear from week t to week t+1.
    weeks = sorted(A_t.keys())
    m = {}
    for i, w in enumerate(weeks):
        if i + 1 < len(weeks):
            next_w = weeks[i + 1]
            # count names present in current week but not in next week
            dropped = set(A_t[w]) - set(A_t[next_w])
            m[w] = max(0, len(dropped))
        else:
            m[w] = 0
    return m


def infer_elim_counts_from_col(panel_s: pd.DataFrame, elim_col: str) -> Dict[int, int]:
    """Build elimination counts per week from an explicit elimination flag column in the panel."""
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
    q = {}
    # align
    name_to_score = {str(r['celebrity_name']): float(r['total_judge_score']) for _, r in sub.iterrows()}
    for name in active:
        q[name] = name_to_score.get(str(name), 0.0) / denom
    # normalize to sum 1 in case of numeric issues
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
        # uniform
        return {name: 1.0 / max(1, len(active)) for name in active}
    for _, r in sub.iterrows():
        p_map[str(r['celebrity_name'])] = float(r['p_est'])
    # normalize
    s = sum(p_map.values())
    if s <= 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for k in p_map:
        p_map[k] /= s
    return p_map


def tie_break_sort_percent(df: pd.DataFrame) -> pd.DataFrame:
    # df must contain columns: 'S', 'total_judge_score', 'p_est', 'celebrity_name'
    # We want ascending S (worst first). For tie-breaking: lower judge score, lower p_est, then name
    return df.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, True, True, True])


def tie_break_sort_rank(df: pd.DataFrame) -> pd.DataFrame:
    # df must contain 'Rsum', 'total_judge_score', 'p_est', 'celebrity_name'
    # eliminate largest Rsum; tie-break by lower judge score, lower p_est, then name
    return df.sort_values(by=['Rsum', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[False, True, True, True])


def simulate_season(panel_s: pd.DataFrame, pest_s: pd.DataFrame, alpha: float = 0.5, method: str = 'percent', m_map: Dict[int,int] = None, verbose: bool = False) -> List[Dict]:
    A_t = build_week_participants(panel_s)
    if not A_t:
        return []
    weeks = sorted(A_t.keys())
    if m_map is None:
        m_map = infer_elim_counts(A_t)
    # warn if all m==0 and verbose
    if verbose:
        if all(v == 0 for v in m_map.values()):
            print('Warning: inferred elimination counts are zero for all weeks; pass --elim-col if your panel has an explicit elimination flag or check panel structure.')

    # initial active set: participants in first week
    active_set = list(A_t[weeks[0]])
    history = []

    for w in weeks:
        if len(active_set) == 0:
            break
        m = m_map.get(w, 0)
        if m <= 0:
            history.append({'week': w, 'm': 0, 'elim_pred': [], 'active_count': len(active_set)})
            # update active_set to intersection with next week's panel participants to avoid adding newcomers
            if w in A_t:
                next_idx = weeks.index(w) + 1
                if next_idx < len(weeks):
                    next_week = weeks[next_idx]
                    # restrict to those that appear in next week panel if present (but do not add new ones)
                    active_set = [a for a in active_set if a in A_t[next_week] or a in active_set]
            continue

        # get qJ and p for current active set and week
        qJ = compute_qJ_for_week(panel_s, w, active_set)
        pmap = get_p_for_week(pest_s, w, active_set)

        # build DataFrame for sorting
        rows = []
        for name in active_set:
            rows.append({'celebrity_name': name, 'qJ': qJ.get(name, 0.0), 'p_est': pmap.get(name, 0.0), 'total_judge_score': float(panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]['total_judge_score'].astype(float).sum())})
        df = pd.DataFrame(rows)
        if method == 'percent':
            df['S'] = alpha * df['qJ'] + (1.0 - alpha) * df['p_est']
            df_sorted = tie_break_sort_percent(df)
            elim = df_sorted.head(m)['celebrity_name'].tolist()
        else:
            # rank rule
            # rank_J: higher judge score -> rank 1
            df['rank_J'] = df['total_judge_score'].rank(method='min', ascending=False)
            df['rank_V'] = df['p_est'].rank(method='min', ascending=False)
            df['Rsum'] = df['rank_J'] + df['rank_V']
            df_sorted = tie_break_sort_rank(df)
            elim = df_sorted.head(m)['celebrity_name'].tolist()

        # record
        history.append({'week': w, 'm': m, 'elim_pred': elim.copy(), 'active_count': len(active_set)})
        # remove eliminated from active set for next iterations
        active_set = [a for a in active_set if a not in set(elim)]
        # optionally intersect with next week's panel participants to avoid reintroducing absent contestants
        next_idx = weeks.index(w) + 1
        if next_idx < len(weeks):
            next_week = weeks[next_idx]
            # remove any who do not appear in next week's panel unless they were kept
            active_set = [a for a in active_set if a in A_t.get(next_week, [])]

    return history


def write_history_csv(history: List[Dict], out_path: str, season: str, method: str):
    rows = []
    for h in history:
        rows.append({'season': season, 'method': method, 'week': h['week'], 'm': h['m'], 'active_count': h['active_count'], 'elim_pred': ';'.join(h['elim_pred'])})
    pd.DataFrame(rows).to_csv(out_path, index=False)


def main(argv: List[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', default=None, help='p_est CSV (if not provided, fallback tries a few defaults)')
    p.add_argument('--season', required=True, help='season number or "all"')
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--methods', default='percent,rank', help='comma separated list of methods to run')
    p.add_argument('--elim-col', default=None, help='Optional column in panel that marks eliminated contestants for a week (bool-like)')
    p.add_argument('--verbose', action='store_true', help='Print warnings and extra info')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest_path = args.pest if args.pest and os.path.exists(args.pest) else None
    if pest_path is None:
        pest_path = choose_default_pest()
    pest = pd.read_csv(pest_path)

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    if args.season != 'all':
        seasons = [s for s in seasons if str(s) == str(args.season)]

    methods = [m.strip() for m in args.methods.split(',') if m.strip()]
    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        pest_s = pest[pest['season'].astype(str) == str(s)].copy()
        # compute m_map from elim_col if provided
        m_map = None
        if args.elim_col and args.elim_col in panel_s.columns:
            m_map = infer_elim_counts_from_col(panel_s, args.elim_col)
            if args.verbose:
                print(f'Using elim_col {args.elim_col} to infer elimination counts: {m_map}')
        for method in methods:
            history = simulate_season(panel_s, pest_s, alpha=args.alpha, method=method, m_map=m_map, verbose=args.verbose)
            out_p = f'src/sim/replay_{method}_season{str(s)}.csv'
            write_history_csv(history, out_p, s, method)
            print('Wrote', out_p)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
