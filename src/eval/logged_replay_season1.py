"""
Produce a logged replay for season 1: print the names left in game after each week's elimination.
Reads replay files under src/eval/replay_{method}_season1.csv and reconstructs survivors.
Writes logs to src/eval/logged_replay_season1_{method}.txt and prints the same to stdout.
"""
from __future__ import annotations
import pandas as pd
import os
import argparse
from typing import List, Dict, Set

EVAL_DIR = 'src/eval'
PANEL = 'output/data_cleaned/intermediate_weekly_panel.csv'


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


def logged_replay_for_method(method: str, season: str = '1') -> str:
    panel = pd.read_csv(PANEL)
    panel_s = panel[panel['season'].astype(str) == str(season)].copy()
    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())
    if not weeks:
        raise SystemExit('No weeks found for season in panel')
    init_participants = list(A_t[weeks[0]])
    # load replay predictions
    replay_path = os.path.join(EVAL_DIR, f'replay_{method}_season{season}.csv')
    if not os.path.exists(replay_path):
        raise SystemExit(f'Replay file not found: {replay_path}')
    rep = pd.read_csv(replay_path)
    # reconstruct survivors
    curr = set(init_participants)
    lines = []
    lines.append(f'Replay logged for season {season}, method={method}')
    lines.append(f'Initial participants (week {weeks[0]}): {", ".join(sorted(curr))}')
    # Ensure rep rows are sorted by week
    rep = rep.sort_values(by='week')
    for _, r in rep.iterrows():
        w = int(r['week'])
        pred_field = r.get('elim_pred', '')
        pred_list = [p for p in str(pred_field).split(';') if p!='']
        # remove predicted eliminated contestants
        curr = set(curr) - set(pred_list)
        lines.append(f'After week {w} elimination -> survivors ({len(curr)}): {", ".join(sorted(curr))}')
    # write log
    out_path = os.path.join(EVAL_DIR, f'logged_replay_season{season}_{method}.txt')
    with open(out_path, 'w', encoding='utf8') as f:
        for L in lines:
            f.write(L + '\n')
    # also print to stdout
    for L in lines:
        print(L)
    return out_path


def main(argv: List[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--methods', default='percent', help='comma separated methods: percent,rank or both')
    p.add_argument('--season', default='1')
    args = p.parse_args(argv)
    methods = [m.strip() for m in args.methods.split(',') if m.strip()]
    out_paths = []
    for m in methods:
        try:
            out = logged_replay_for_method(m, season=args.season)
            print('Wrote', out)
            out_paths.append(out)
        except Exception as e:
            print('Error for method', m, ':', e)
    return out_paths


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
