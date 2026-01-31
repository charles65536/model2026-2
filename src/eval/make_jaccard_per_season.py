"""
Read src/eval/jaccard_summary_allseasons.csv and produce a per-season CSV
with columns: season, mean_jaccard_percent, weeks_percent, mean_jaccard_rank, weeks_rank

Writes: src/eval/jaccard_per_season.csv
"""
from __future__ import annotations
import pandas as pd
import os

IN = 'src/eval/jaccard_summary_allseasons.csv'
OUT = 'src/eval/jaccard_per_season.csv'

if not os.path.exists(IN):
    raise SystemExit(f'Input not found: {IN}')

df = pd.read_csv(IN)

# Pivot to wide format. This will create columns like ('mean_jaccard','percent') etc.
try:
    p = df.pivot(index='season', columns='method', values=['mean_jaccard', 'weeks_compared'])
except Exception as e:
    raise SystemExit(f'Pivot failed: {e}')

# Flatten multiindex columns
p.columns = [f"{stat}_{method}" for stat, method in p.columns]
p = p.reset_index()

# Try to sort seasons numerically when possible
def try_numeric_sort(df_in):
    s = df_in['season'].astype(str)
    if s.str.replace('.', '', 1).str.isnumeric().all():
        df_in['season_num'] = s.astype(float)
        df_out = df_in.sort_values('season_num').drop(columns=['season_num'])
        return df_out
    return df_in.sort_values('season')

p = try_numeric_sort(p)

# Rename columns to consistent names if present
col_map = {}
if 'mean_jaccard_percent' in p.columns:
    col_map['mean_jaccard_percent'] = 'mean_jaccard_percent'
if 'mean_jaccard_rank' in p.columns:
    col_map['mean_jaccard_rank'] = 'mean_jaccard_rank'
if 'weeks_compared_percent' in p.columns:
    col_map['weeks_compared_percent'] = 'weeks_percent'
if 'weeks_compared_rank' in p.columns:
    col_map['weeks_compared_rank'] = 'weeks_rank'
if col_map:
    p = p.rename(columns=col_map)

p.to_csv(OUT, index=False)
print('Wrote', OUT)
