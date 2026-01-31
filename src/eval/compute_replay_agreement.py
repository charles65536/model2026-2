"""
Compute agreement between replay predictions and actual eliminations for all seasons.
Writes: src/eval/replay_agreement_allseasons.csv and prints summary.
"""
from __future__ import annotations
import pandas as pd
import os
import csv

PANEL = 'output/data_cleaned/intermediate_weekly_panel.csv'
OUT_CSV = 'src/eval/replay_agreement_allseasons.csv'

panel = pd.read_csv(PANEL)
if 'true_elim_flag' not in panel.columns:
    print('Panel missing true_elim_flag column; cannot compute actual eliminations.')
    raise SystemExit(1)

seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
rows = []
methods = ['percent','rank']
for s in seasons:
    panel_s = panel[panel['season'].astype(str) == str(s)].copy()
    # build actual elim per week
    panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
    weeks = sorted(panel_s['week'].dropna().unique())
    actual_by_week = {}
    for w in weeks:
        names = panel_s.loc[(panel_s['week']==w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
        actual_by_week[int(w)] = set(names)

    for method in methods:
        replay_path = f'src/eval/replay_{method}_season{str(s)}.csv'
        if not os.path.exists(replay_path):
            # skip missing
            continue
        rep = pd.read_csv(replay_path)
        for _, r in rep.iterrows():
            w = int(r['week'])
            pred_field = r.get('elim_pred', '')
            preds = [p for p in str(pred_field).split(';') if p!='']
            pred_set = set(preds)
            actual_set = actual_by_week.get(w, set())
            exact = (pred_set == actual_set)
            inter = len(pred_set & actual_set)
            rows.append({'season': s, 'method': method, 'week': w, 'm_actual': len(actual_set), 'm_pred': len(pred_set), 'exact_match': int(exact), 'intersection_size': inter, 'actual_list': ';'.join(sorted(actual_set)), 'pred_list': ';'.join(sorted(pred_set))})

# write CSV
with open(OUT_CSV, 'w', newline='', encoding='utf8') as f:
    writer = csv.DictWriter(f, fieldnames=['season','method','week','m_actual','m_pred','exact_match','intersection_size','actual_list','pred_list'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# summary
df = pd.DataFrame(rows)
if df.empty:
    print('No replay outputs found to compare.')
    raise SystemExit(0)

summary = df.groupby('method').agg(total_weeks=('exact_match','count'), exact_matches=('exact_match','sum'), mean_intersection=('intersection_size','mean'))
summary['exact_rate'] = summary['exact_matches'] / summary['total_weeks']
print('\nAgreement summary by method:')
print(summary.reset_index().to_string(index=False))
print(f"\nWrote {OUT_CSV}")

