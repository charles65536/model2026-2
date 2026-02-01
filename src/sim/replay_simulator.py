"""
Replay simulator for Percent, Rank, and JS-SR (Judge-Safeguard Smoothed-Rank) rules.

Produces per-week predicted elimination lists and final ranking by simulating eliminations sequentially.

Usage examples:
  py src/sim/replay_simulator.py --panel output/data_cleaned/intermediate_weekly_panel.csv --pest src/sim/fan_shares_entropy_1.0.csv --season 1 --alpha 0.5

Outputs:
 - src/sim/replay_percent_season{S}.csv
 - src/sim/replay_rank_season{S}.csv
 - src/sim/replay_summary_season{S}.csv (combined)
 - src/sim/replay_js_sr_season{S}.csv

Notes:
 - Tie-breaks: for Percent rule (lower S worse) tie broken by lower judge score, lower p_est, then name.
 - For Rank rule: rank_J and rank_V (descending) summed; higher sum worse; ties broken by lower judge score, lower p_est, then name.
 - For JS-SR: construct a judge-safe set (top ~33% by judge score) and eliminate from the battleground
     using the same smoothed-percent score S = alpha*qJ + (1-alpha)*p_est; if battleground is too small,
     fall back to eliminating the worst from the safe set.
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
    # If the panel contains an `active` column, prefer only rows marked active
    if 'active' in panel_s.columns:
        try:
            panel_s = panel_s[panel_s['active'].astype(bool)]
        except Exception:
            # fall back to original if casting fails
            panel_s = panel_s[panel_s['active'] == True]
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
    # imputed rows for counterfactual survivors: dict keyed by (name, week) -> {'total_judge_score':..., 'p_est':...}
    imputed: Dict[Tuple[str,int], Dict[str, float]] = {}
    # track last known p_est for each contestant (carry-forward for imputation)
    last_p: Dict[str, float] = {}
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

        # get qJ and p for current active set and week — incorporate imputed rows when contestants are not present in panel
        # Build effective judge scores for this week: take panel rows for this week plus any imputed rows
        eff_rows = []
        panel_week = panel_s[panel_s['week'] == w]
        for _, r in panel_week.iterrows():
            eff_rows.append({'celebrity_name': str(r['celebrity_name']), 'total_judge_score': float(r.get('total_judge_score', 0.0))})
        # add imputed rows for this week
        for (iname, iw), rec in imputed.items():
            if iw == w:
                eff_rows.append({'celebrity_name': iname, 'total_judge_score': float(rec.get('total_judge_score', 0.0))})
        # compute qJ among active_set using eff_rows
        qJ = {}
        name_to_score = {r['celebrity_name']: r['total_judge_score'] for r in eff_rows}
        denom = sum([name_to_score.get(n, 0.0) for n in active_set])
        if denom <= 0:
            for name in active_set:
                qJ[name] = 1.0 / max(1, len(active_set))
        else:
            for name in active_set:
                qJ[name] = float(name_to_score.get(name, 0.0)) / float(denom)

        # compute pmap: prefer pest_s entries for week; otherwise, fall back to last_p or uniform
        pmap = {name: 0.0 for name in active_set}
        pest_week = pest_s[pest_s['week'] == w]
        for _, r in pest_week.iterrows():
            pname = str(r['celebrity_name'])
            if pname in pmap:
                pmap[pname] = float(r.get('p_est', 0.0))
                last_p[pname] = pmap[pname]
        # for active names missing in pest_week, use last_p if available, else uniform small share
        for name in active_set:
            if pmap.get(name, 0.0) == 0.0:
                if name in last_p:
                    pmap[name] = last_p[name]
                else:
                    pmap[name] = 1.0 / max(1, len(active_set))

        # build DataFrame for sorting
        rows = []
        for name in active_set:
            rows.append({'celebrity_name': name, 'qJ': qJ.get(name, 0.0), 'p_est': pmap.get(name, 0.0), 'total_judge_score': float(panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]['total_judge_score'].astype(float).sum())})
        df = pd.DataFrame(rows)
        if method == 'percent':
            df['S'] = alpha * df['qJ'] + (1.0 - alpha) * df['p_est']
            df_sorted = tie_break_sort_percent(df)
            elim = df_sorted.head(m)['celebrity_name'].tolist()
        elif method == 'js_sr':
            # JS-SR: Judge-Safeguard + Smoothed Rank (conservative)
            # Build a safe set by judge score (top fraction) and eliminate from the battleground
            # Using a default safe fraction of 1/3 (top 33% by judge score are protected)
            safe_frac = 1.0 / 3.0
            scores = df['total_judge_score'].astype(float).values
            if len(scores) == 0:
                elim = []
            else:
                thresh = float(np.percentile(scores, 100.0 * (1.0 - safe_frac)))
                safe_set = set(df.loc[df['total_judge_score'] >= thresh, 'celebrity_name'].tolist())
                battleground = [n for n in df['celebrity_name'].tolist() if n not in safe_set]
                # if battleground empty, treat everyone as battleground
                if len(battleground) == 0:
                    battleground = df['celebrity_name'].tolist()
                # construct battleground df and compute S score like percent rule
                bdf = df[df['celebrity_name'].isin(battleground)].copy()
                bdf['S'] = alpha * bdf['qJ'] + (1.0 - alpha) * bdf['p_est']
                bdf_sorted = tie_break_sort_percent(bdf)
                elim = bdf_sorted.head(m)['celebrity_name'].tolist()
                # if battleground had fewer than m, take remaining from the safe set by worst S
                if len(elim) < m:
                    remaining = m - len(elim)
                    s_df = df[df['celebrity_name'].isin(safe_set)].copy()
                    s_df['S'] = alpha * s_df['qJ'] + (1.0 - alpha) * s_df['p_est']
                    s_sorted = tie_break_sort_percent(s_df)
                    more = s_sorted.head(remaining)['celebrity_name'].tolist()
                    elim = elim + more
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
        # advance to next week: if a surviving contestant does not appear in the panel's next-week rows,
        # we will impute their next-week judge score and carry-forward p_est (zombie logic), and keep them in active_set
        next_idx = weeks.index(w) + 1
        if next_idx < len(weeks):
            next_week = weeks[next_idx]
            next_participants = set(A_t.get(next_week, []))
            # for survivors missing in panel next week, impute and keep them
            missing_survivors = [a for a in active_set if a not in next_participants]
            for name in missing_survivors:
                # compute historical mean judge score up to week w for this contestant
                mask = (panel_s['celebrity_name'].astype(str) == name) & (panel_s['week'] <= w)
                hist = panel_s.loc[mask, 'total_judge_score'].astype(float)
                j_mean = float(hist.mean()) if len(hist.dropna()) > 0 else 0.0
                # p carry-forward
                p_cf = float(last_p.get(name, 1.0 / max(1, len(active_set))))
                # register imputed entry for next_week
                imputed[(name, next_week)] = {'total_judge_score': j_mean, 'p_est': p_cf}
                # also update last_p for future weeks
                last_p[name] = p_cf
            # combine next week's panel participants with kept survivors
            active_set = list(sorted(set(active_set) | next_participants))

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
    # Helper: canonical mapping by season
    def canon_method_for_season(s: int) -> str:
        if s in (1, 2):
            return 'rank'
        if 3 <= s <= 27:
            return 'percent'
        return 'percent_last_two'

    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        pest_s = pest[pest['season'].astype(str) == str(s)].copy()

        # compute m_map: prefer explicit elim_col if provided, else use 'true_elim_flag' column if present
        m_map = None
        elim_col_to_use = args.elim_col
        if elim_col_to_use is None and 'true_elim_flag' in panel_s.columns:
            elim_col_to_use = 'true_elim_flag'
        if elim_col_to_use and elim_col_to_use in panel_s.columns:
            m_map = infer_elim_counts_from_col(panel_s, elim_col_to_use)
            if args.verbose:
                print(f'Using elim_col {elim_col_to_use} to infer elimination counts: {m_map}')

        for method in methods:
            if method == 'canon':
                # apply canonical method per season and write file named by the underlying method
                underlying = canon_method_for_season(int(float(s)))
                history = simulate_season(panel_s, pest_s, alpha=args.alpha, method=underlying, m_map=m_map, verbose=args.verbose)
                out_p = f'src/sim/replay_{underlying}_season{str(s)}.csv'
                write_history_csv(history, out_p, s, underlying)
                print('Wrote', out_p)
            else:
                history = simulate_season(panel_s, pest_s, alpha=args.alpha, method=method, m_map=m_map, verbose=args.verbose)
                out_p = f'src/sim/replay_{method}_season{str(s)}.csv'
                write_history_csv(history, out_p, s, method)
                print('Wrote', out_p)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
