"""
Debug helper: print reconstructed weekly participants and inferred elimination counts for a season.
"""
from __future__ import annotations
import pandas as pd
import sys

p = 'output/data_cleaned/intermediate_weekly_panel.csv'
season = '1'
panel = pd.read_csv(p)
panel_s = panel[panel['season'].astype(str) == season].copy()

# reconstruct participants using replay_simulator logic
panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
weeks = sorted(panel_s['week'].dropna().unique())
print('Unique week values in panel for season', season, ':', weeks)

if len(weeks) <= 1 and 'exit_week' in panel_s.columns:
    print('Detected contestant-level panel with exit_week; reconstructing A_t from exit_week')
    panel_s['exit_week'] = pd.to_numeric(panel_s['exit_week'], errors='coerce')
    max_w = int(panel_s['exit_week'].max()) if not panel_s['exit_week'].isna().all() else 1
    A_t = {}
    for w in range(1, max_w+1):
        names = panel_s.loc[panel_s['exit_week'].fillna(max_w) >= w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
else:
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))

print('\nReconstructed A_t:')
for w in sorted(A_t.keys()):
    print(f' week {w}: {len(A_t[w])} participants ->', A_t[w])

# infer elim counts by set difference
weeks_sorted = sorted(A_t.keys())
m = {}
for i,w in enumerate(weeks_sorted):
    if i+1 < len(weeks_sorted):
        next_w = weeks_sorted[i+1]
        dropped = set(A_t[w]) - set(A_t[next_w])
        m[w] = len(dropped)
    else:
        m[w] = 0

print('\nInferred elimination counts m_map:')
for w in sorted(m.keys()):
    print(f' week {w}: m={m[w]}')

# also show sample rows for season
print('\nSample rows from panel (first 10):')
print(panel_s.head(10).to_string(index=False))
