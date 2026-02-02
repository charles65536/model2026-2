"""
Compute Bias Index for replayed rules.

Bias (per Task B, model_3.md) is defined per season as:
  Bias = (1/T) * sum_t ( mean_rank_survivors(t) - mean_rank_eliminated(t) )

Here rank is computed from fan vote share `p_est` within the active set at week t,
with higher rank value meaning higher fan-share (rank 1 = smallest, higher = more popular).
So positive Bias means the rule tends to keep contestants with higher fan-shares.

The script scans replay files `replay_{method}_season{S}.csv` under `src/eval` or `src/sim`,
loads the corresponding `fan_shares_s{S}_alpha{a}.csv` p_est files (default alpha=0.5),
and computes the Bias index per season and an overall aggregate.

Usage:
  python3 src/eval/compute_bias_index.py --method percent --alpha 0.5 --seasons all

Output:
  src/eval/bias_index_{method}_alpha{a}.csv

"""
from __future__ import annotations
import os
import sys
import glob
import argparse
import pandas as pd
from typing import Dict, List, Set

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
EVAL_DIR = os.path.join(ROOT, 'src', 'eval')
SIM_DIR = os.path.join(ROOT, 'src', 'sim')


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


def find_replay(method: str, season: str) -> str:
    p1 = os.path.join(EVAL_DIR, f'replay_{method}_season{season}.csv')
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(SIM_DIR, f'replay_{method}_season{season}.csv')
    if os.path.exists(p2):
        return p2
    return ''


def find_pest(season: int, alpha: float) -> str:
    a_str = str(alpha).replace('.', 'p')
    p1 = os.path.join(SIM_DIR, f'fan_shares_s{season}_alpha{a_str}.csv')
    if os.path.exists(p1):
        return p1
    # fallback to global alpha
    p2 = os.path.join(SIM_DIR, f'fan_shares_alpha{a_str}.csv')
    if os.path.exists(p2):
        return p2
    return ''


def compute_bias_for_season(season: int, method: str, panel: pd.DataFrame, pest_df: pd.DataFrame, replay_path: str):
    panel_s = panel[panel['season'].astype(int) == int(season)].copy()
    if panel_s.empty:
        return None
    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())

    # load replay preds
    if not os.path.exists(replay_path):
        print(f'Warning: replay not found for season {season} method {method} (expected {replay_path})')
        return None
    rep = pd.read_csv(replay_path)

    # precompute p_est table indexed by (week, name)
    pest_df_local = pest_df.copy()
    if 'week' in pest_df_local.columns:
        pest_df_local['week'] = pd.to_numeric(pest_df_local['week'], errors='coerce')
    pest_index = pest_df_local.set_index(['week', 'celebrity_name'])['p_est'].to_dict()

    # iterate weeks building predicted survivors and compute bias per week
    curr_pred = set(A_t[weeks[0]]) if weeks else set()
    week_biases = []
    for _, r in rep.iterrows():
        try:
            w = int(r['week'])
        except Exception:
            continue
        # make sure this week is in our panel weeks
        if w not in weeks:
            # still need to update curr_pred by removing preds if names present
            pred_field = r.get('elim_pred', '')
            preds = [p.strip() for p in str(pred_field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]
            curr_pred = set(curr_pred) - set(preds)
            continue

        # get p values for active set A_t[w]
        names = A_t[w]
        p_vals = []
        for n in names:
            key = (w, n)
            p = pest_index.get(key, None)
            # if missing, try to get from last available week for that contestant
            if p is None:
                # fallback: look up any available p for that contestant in pest_df_local
                rows = pest_df_local[pest_df_local['celebrity_name'] == n]
                if not rows.empty:
                    p = float(rows['p_est'].iloc[0])
            if p is None:
                p = 0.0
            p_vals.append((n, p))

        # build rank (higher p -> higher rank number)
        p_series = pd.Series({n: p for n, p in p_vals})
        if p_series.empty:
            continue
        ranks = p_series.rank(method='dense', ascending=True)  # smallest -> 1, largest -> bigger

        # determine eliminated this week (from replay)
        pred_field = r.get('elim_pred', '')
        preds = [p.strip() for p in str(pred_field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]

        # update curr_pred to reflect elimination happening this week
        before_curr = set(curr_pred)
        curr_pred = set(curr_pred) - set(preds)
        survivors_after = set(curr_pred)

        # compute mean rank for survivors (after elimination) and for eliminated (this week)
        # rank values are computed on the pre-elim active set A_t[w]
        ranks_series = ranks
        # filter to names that exist in ranks (may miss some preds)
        surv_ranks = [ranks_series.get(n, float('nan')) for n in survivors_after if n in ranks_series.index]
        elim_ranks = [ranks_series.get(n, float('nan')) for n in preds if n in ranks_series.index]

        if len(elim_ranks) == 0:
            # no elimination recorded or not present in ranks - skip this week
            continue

        mean_surv = float(pd.Series(surv_ranks).dropna().mean()) if len(surv_ranks) else float('nan')
        mean_elim = float(pd.Series(elim_ranks).dropna().mean()) if len(elim_ranks) else float('nan')

        if pd.isna(mean_surv) or pd.isna(mean_elim):
            continue

        bias_week = mean_surv - mean_elim
        week_biases.append({'season': season, 'week': w, 'mean_rank_survivors': mean_surv, 'mean_rank_eliminated': mean_elim, 'bias_week': bias_week})

    if not week_biases:
        return None

    dfb = pd.DataFrame(week_biases)
    bias_season = float(dfb['bias_week'].mean())
    return {'season': season, 'method': method, 'bias_season': bias_season, 'weeks_compared': len(dfb)}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--method', default='percent', help='Replay method name (percent, rank, percent_last_two, js_sr)')
    p.add_argument('--alpha', type=float, default=0.5, help='Alpha used for p_est filenames (default 0.5)')
    p.add_argument('--seasons', default='all', help='Comma-separated seasons or "all"')
    p.add_argument('--panel', default=PANEL)
    p.add_argument('--out', default=os.path.join(EVAL_DIR, 'bias_index_{method}_alpha{a}.csv'))
    args = p.parse_args(argv)

    if not os.path.exists(args.panel):
        raise SystemExit('Panel not found at ' + args.panel)
    panel = pd.read_csv(args.panel)

    all_seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    if args.seasons.strip().lower() == 'all':
        seasons = [int(float(s)) for s in all_seasons]
    else:
        seasons = [int(float(s)) for s in str(args.seasons).split(',') if s.strip()!='']

    results = []
    a_str = str(args.alpha).replace('.', 'p')
    out_path = args.out.format(method=args.method, a=a_str)

    for s in seasons:
        replay_path = find_replay(args.method, str(s))
        if replay_path == '':
            print(f'Replay for method {args.method} season {s} not found; skipping')
            continue
        pest_path = find_pest(s, args.alpha)
        if pest_path == '':
            print(f'Warning: p_est for season {s} alpha {args.alpha} not found; skipping season')
            continue
        pest_df = pd.read_csv(pest_path)
        out = compute_bias_for_season(s, args.method, panel, pest_df, replay_path)
        if out is not None:
            results.append(out)

    if not results:
        raise SystemExit('No results computed')

    dfres = pd.DataFrame(results).sort_values('season')
    dfres.to_csv(out_path, index=False)
    print('Wrote', out_path)
    print('\nAggregate Bias (mean across seasons):', float(dfres['bias_season'].mean()))


if __name__ == '__main__':
    main()
