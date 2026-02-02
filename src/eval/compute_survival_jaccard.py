"""
Compute per-week Jaccard similarity between actual surviving contestants and predicted surviving contestants
from replay, then average per season. Writes summary and per-week detail CSVs under src/eval/.

Outputs:
 - src/eval/jaccard_summary_allseasons.csv
 - src/eval/jaccard_details_{method}.csv for each method

Methods expected: 'percent' and 'rank' replay files under src/eval/replay_{method}_season{S}.csv
"""
from __future__ import annotations
import pandas as pd
import os
import csv
import glob
from typing import Dict, List, Set
from src.tools.paths import REPLAYS_DIR, DATA_CLEAN, EVAL_DIR, ensure_dirs

PANEL = os.path.join(DATA_CLEAN, 'intermediate_weekly_panel.csv')
ensure_dirs([EVAL_DIR])
SUMMARY_OUT = os.path.join(EVAL_DIR, 'jaccard_summary_allseasons.csv')

# helper to build participants per week from panel (handles contestant-level exit_week or weekly rows)
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
    # otherwise use weekly panel
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t

# main
panel = pd.read_csv(PANEL)
if 'true_elim_flag' not in panel.columns:
    raise SystemExit('Panel missing true_elim_flag column; cannot compute actual elimination sequence')

seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
# detect available replay methods by scanning replay files in the eval dir
# prefer canonical replays dir, fall back to eval dir
replay_files = glob.glob(os.path.join(REPLAYS_DIR, 'replay_*_season*.csv'))
if not replay_files:
    replay_files = glob.glob(os.path.join(EVAL_DIR, 'replay_*_season*.csv'))
methods = set()
for fp in replay_files:
    fname = os.path.basename(fp)
    parts = fname.split('_')
    if len(parts) >= 3 and parts[0] == 'replay':
        methods.add(parts[1])
methods = sorted(list(methods))
if not methods:
    # fallback to default expected methods
    methods = ['percent', 'rank']
summary_rows = []
for method in methods:
    details = []
    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        if panel_s.empty:
            continue
        # build actual participants per week
        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())
        # build actual elimination sets per week from true_elim_flag
        actual_elim_by_week: Dict[int, Set[str]] = {}
        if 'week' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s.get('week') == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            # if no week column, try exit_week? but build_week_participants handled exit_week; actual_elim likely not present then
            for w in weeks:
                actual_elim_by_week[w] = set()
        # reconstruct actual survivors after each week by sequential removal
        actual_survivors = {}
        curr = set(A_t[weeks[0]]) if weeks else set()
        for w in weeks:
            elim = actual_elim_by_week.get(w, set())
            # remove those eliminated at this week
            curr = set(curr) - set(elim)
            actual_survivors[w] = set(curr)
        # load replay predictions
        replay_path = os.path.join(EVAL_DIR, f'replay_{method}_season{str(s)}.csv')
        if not os.path.exists(replay_path):
            # no replay output for this season-method
            continue
        rep = pd.read_csv(replay_path)
        # reconstruct predicted survivors by sequentially applying elim_pred
        pred_survivors = {}
        curr_pred = set(A_t[weeks[0]]) if weeks else set()
        for _, r in rep.iterrows():
            w = int(r['week'])
            pred_list = [p for p in str(r.get('elim_pred','')).split(';') if p!='']
            # remove predicted elim
            curr_pred = set(curr_pred) - set(pred_list)
            pred_survivors[w] = set(curr_pred)
        # compute per-week Jaccard between actual_survivors[w] and pred_survivors[w] for weeks present in both
        jaccards = []
        for w in weeks:
            a = actual_survivors.get(w, set())
            pset = pred_survivors.get(w, None)
            if pset is None:
                # missing prediction for this week — skip
                continue
            inter = len(a & pset)
            union = len(a | pset)
            j = (inter / union) if union > 0 else 1.0
            jaccards.append(j)
            details.append({'season': s, 'method': method, 'week': w, 'jaccard': j, 'actual_count': len(a), 'pred_count': len(pset), 'intersection': inter})
        mean_j = float(sum(jaccards) / len(jaccards)) if jaccards else None
        summary_rows.append({'season': s, 'method': method, 'mean_jaccard': mean_j, 'weeks_compared': len(jaccards)})
    # write per-method details
    details_df = pd.DataFrame(details)
    out_details = os.path.join(EVAL_DIR, f'jaccard_details_{method}.csv')
    details_df.to_csv(out_details, index=False)

# write summary
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(SUMMARY_OUT, index=False)
print('Wrote', SUMMARY_OUT)
print(summary_df.groupby('method').agg(mean_season_jaccard=('mean_jaccard','mean'), seasons=('season','count')).reset_index())
