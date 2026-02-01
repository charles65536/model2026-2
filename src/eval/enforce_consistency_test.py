"""
Enforce exact-match consistency test using replay files in current folder.

This script looks for replay CSVs named `replay_percent_season{S}.csv` and
`replay_rank_season{S}.csv` in the same directory (`src/eval/`) and compares each
replay's predicted eliminations per week to the canonical panel's `true_elim_flag`.

Behavior:
- Prints offending weeks (season, method, week, actual_list, pred_list) when mismatches occur.
- Exits with code 2 if any mismatch is found.
- Exits 0 when all compared weeks exactly match.

Usage:
  python3 src/eval/enforce_consistency_test.py

Requires:
  - `output/data_cleaned/intermediate_weekly_panel.csv`
  - replay CSVs located in `src/eval/` (this script searches the current directory)
"""
from __future__ import annotations
import pandas as pd
import os
import sys
import glob
from typing import Dict, List, Set

HERE = os.path.dirname(__file__)
PANEL = os.path.join(HERE, '..', 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
# fallback path if repository layout runs from repo root
if not os.path.exists(PANEL):
    PANEL = os.path.join('output', 'data_cleaned', 'intermediate_weekly_panel.csv')

# helper: build participants per week from panel (handles contestant-level exit_week or weekly rows)
def build_week_participants(panel_s: pd.DataFrame) -> Dict[int, List[str]]:
    df = panel_s.copy()
    # prefer constructing participants using 'exit_week' when available and plausible
    if 'exit_week' in df.columns and df['exit_week'].notna().any():
        df['exit_week'] = pd.to_numeric(df['exit_week'], errors='coerce')
        max_w = int(df['exit_week'].max()) if not df['exit_week'].isna().all() else 1
        A_t = {}
        for w in range(1, max_w + 1):
            names = df.loc[df['exit_week'].fillna(max_w) >= w, 'celebrity_name'].dropna().astype(str).tolist()
            A_t[int(w)] = sorted(list(dict.fromkeys(names)))
        return A_t

    # fallback: use explicit weekly rows
    if 'week' in df.columns:
        df['week'] = pd.to_numeric(df['week'], errors='coerce')
        weeks = sorted(df['week'].dropna().unique()) if df['week'].notna().any() else []
    else:
        weeks = []
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t

# main
if not os.path.exists(PANEL):
    print(f"Panel file not found at expected path: {PANEL}")
    sys.exit(3)

panel = pd.read_csv(PANEL)
if 'true_elim_flag' not in panel.columns:
    print('Panel missing true_elim_flag column; cannot compute actual eliminations')
    sys.exit(4)

# find replay files in this directory
replay_files = glob.glob(os.path.join(HERE, 'replay_*_season*.csv'))
if not replay_files:
    print('No replay files (replay_*.csv) found in src/eval/. Nothing to compare.')
    sys.exit(0)

# group by method-season
files_by_method_season = {}
for fp in replay_files:
    fname = os.path.basename(fp)
    # expected form: replay_{method}_season{S}.csv
    parts = fname.split('_')
    if len(parts) < 3:
        continue
    method = parts[1]
    season_part = parts[2]
    if not season_part.startswith('season'):
        continue
    season = season_part.replace('season', '').replace('.csv', '')
    files_by_method_season[(method, season)] = fp

# compare each found replay file to panel
mismatches = []
for (method, season), fp in files_by_method_season.items():
    panel_s = panel[panel['season'].astype(str) == str(season)].copy()
    if panel_s.empty:
        # no panel data for this season
        continue
    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())

    # build actual elimination sets per week
    actual_elim_by_week: Dict[int, Set[str]] = {}
    if 'week' in panel_s.columns:
        for w in weeks:
            names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
            actual_elim_by_week[w] = set(names)
    else:
        for w in weeks:
            actual_elim_by_week[w] = set()

    # reconstruct actual survivors after each week by sequential removal (same as jaccard script)
    actual_survivors = {}
    curr_actual = set(A_t[weeks[0]]) if weeks else set()
    for w in weeks:
        elim = actual_elim_by_week.get(w, set())
        curr_actual = set(curr_actual) - set(elim)
        actual_survivors[w] = set(curr_actual)

    # read replay file and reconstruct predicted survivors by sequentially applying elim_pred
    try:
        rep = pd.read_csv(fp)
    except Exception as e:
        print(f"Failed to read replay file {fp}: {e}")
        continue

    pred_survivors = {}
    curr_pred = set(A_t[weeks[0]]) if weeks else set()
    for _, r in rep.iterrows():
        try:
            w = int(r['week'])
        except Exception:
            continue
        pred_field = r.get('elim_pred', '')
        # normalize: treat literal 'nan' or empty strings as no prediction
        preds = [p.strip() for p in str(pred_field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]
        curr_pred = set(curr_pred) - set(preds)
        pred_survivors[w] = set(curr_pred)

    # compare weeks that appear in both actual and predicted using survivor sets (aligns with jaccard indexing)
    for w in sorted(weeks):
        actual = actual_survivors.get(w, set())
        pred = pred_survivors.get(w, None)
        if pred is None:
            # missing prediction for this week — treat as empty survivor set
            pred = set()
        # ignore weeks where both actual and predicted survivors are empty
        if (not actual) and (not pred):
            continue
        if actual != pred:
            mismatches.append({'season': season, 'method': method, 'week': w, 'actual_list': ';'.join(sorted(actual)), 'pred_list': ';'.join(sorted(pred))})

# report and exit
if mismatches:
    print('\nConsistency enforcement failed: some replay weeks do not exactly match actual eliminations.')
    print('Offending weeks (season, method, week, actual_list, pred_list):')
    for r in mismatches:
        print(f"season={r['season']} method={r['method']} week={r['week']} actual=[{r['actual_list']}] pred=[{r['pred_list']}]")
    # Run simple shift-analysis: check if mismatches are explained by a one-week shift
    print('\nShift-analysis (counts where predicted==actual_next_week or predicted==actual_prev_week):')
    # build a mapping of actual elim by season-week for quick lookup
    actual_map = {}
    for s in sorted(panel['season'].dropna().unique(), key=lambda x: str(x)):
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())
        actual_elim_by_week = {}
        if 'week' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            for w in weeks:
                actual_elim_by_week[w] = set()
        for w in weeks:
            actual_map[(str(s), int(w))] = actual_elim_by_week.get(w, set())

    shift_next = 0
    shift_prev = 0
    for r in mismatches:
        s = str(r['season']); w = int(r['week'])
        pred_set = set([p for p in r['pred_list'].split(';') if p])
        next_key = (s, w + 1)
        prev_key = (s, w - 1)
        if next_key in actual_map and pred_set == actual_map[next_key]:
            shift_next += 1
        if prev_key in actual_map and pred_set == actual_map[prev_key]:
            shift_prev += 1
    print(f"one-week-forward matches: {shift_next}, one-week-back matches: {shift_prev}")
    # non-zero exit code to signal failure; use 2 for consistency failure
    sys.exit(2)

print('\nConsistency enforcement passed: all compared replay weeks exactly match actual eliminations.')
sys.exit(0)
