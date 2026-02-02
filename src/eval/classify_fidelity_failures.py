#!/usr/bin/env python3
"""Classify fidelity mismatches and produce per-week and per-season summaries.

Reads:
 - `output/data_cleaned/intermediate_weekly_panel.csv` (actual panel)
 - `src/eval/fidelity_details_canon.csv` (per-week jaccard + counts)
 - replay files `src/eval/replay_{method}_season{S}.csv` or `src/sim/...` as needed

Writes:
 - `src/eval/fidelity_failure_taxonomy.csv` (per-week classification)
 - `src/eval/fidelity_failure_summary_by_season.csv` (counts per class)
"""
from __future__ import annotations
import os
import glob
import pandas as pd
from typing import Dict, Set

PANEL = 'output/data_cleaned/intermediate_weekly_panel.csv'
DETAILS = 'src/eval/fidelity_details_canon.csv'
OUT_TAX = 'src/eval/fidelity_failure_taxonomy.csv'
OUT_SUM = 'src/eval/fidelity_failure_summary_by_season.csv'


def find_replay(method: str, season: str) -> str:
    p1 = os.path.join('src', 'eval', f'replay_{method}_season{season}.csv')
    if os.path.exists(p1):
        return p1
    p2 = os.path.join('src', 'sim', f'replay_{method}_season{season}.csv')
    if os.path.exists(p2):
        return p2
    return ''


def build_actual_survivors(panel: pd.DataFrame, season: str):
    df = panel[panel['season'].astype(str) == str(season)].copy()
    # prefer active rows only
    if 'active' in df.columns:
        try:
            df = df[df['active'].astype(bool)]
        except Exception:
            df = df[df['active'] == True]
    df['week'] = pd.to_numeric(df['week'], errors='coerce')
    weeks = sorted(df['week'].dropna().unique())
    A_t = {int(w): sorted(df.loc[df['week'] == w, 'celebrity_name'].dropna().astype(str).unique().tolist()) for w in weeks}
    # build actual elim_by_week from true_elim_flag if present
    actual_elim = {}
    if 'true_elim_flag' in df.columns:
        for w in weeks:
            mask = (df['week'] == w) & (df['true_elim_flag'].astype(bool))
            actual_elim[int(w)] = set(df.loc[mask, 'celebrity_name'].astype(str).tolist())
    else:
        # infer by disappearance
        for i, w in enumerate(weeks):
            if i + 1 < len(weeks):
                next_w = weeks[i+1]
                dropped = set(A_t[int(w)]) - set(A_t[int(next_w)])
                actual_elim[int(w)] = set(dropped)
            else:
                actual_elim[int(w)] = set()

    # construct survivors after each week
    survivors = {}
    curr = set(A_t[weeks[0]]) if weeks else set()
    for w in weeks:
        elim = actual_elim.get(int(w), set())
        curr = set(curr) - set(elim)
        survivors[int(w)] = set(curr)
    return survivors


def read_pred_survivors(replay_path: str, season: str):
    if not replay_path or not os.path.exists(replay_path):
        return {}
    rep = pd.read_csv(replay_path)
    elim_map = {}
    for _, r in rep.iterrows():
        try:
            w = int(r['week'])
        except Exception:
            continue
        field = r.get('elim_pred', '')
        preds = [p.strip() for p in str(field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]
        elim_map[w] = preds
    return elim_map


def classify_row(row, actual_surv, pred_surv_map, season_weeks):
    w = int(row['week'])
    a = actual_surv.get(w, set())
    pset = pred_surv_map.get(w, None)
    if pset is None:
        return 'missing_pred'
    j = float(row.get('jaccard', 0.0))
    inter = int(row.get('intersection', 0))
    ac = int(row.get('actual_count', 0))
    pc = int(row.get('pred_count', 0))
    if j == 1.0:
        return 'exact'
    if ac != pc:
        return 'count_mismatch'
    if inter == 0:
        # check shift forward/backward
        if (w+1) in season_weeks and pred_surv_map.get(w) == actual_surv.get(w+1):
            return 'shift_forward'
        if (w-1) in season_weeks and pred_surv_map.get(w) == actual_surv.get(w-1):
            return 'shift_backward'
        return 'disjoint'
    if 0 < inter < ac:
        return 'partial_overlap'
    return 'other'


def main():
    if not os.path.exists(PANEL):
        raise SystemExit(f'Panel not found at {PANEL}')
    if not os.path.exists(DETAILS):
        raise SystemExit(f'Details file not found at {DETAILS}; run compute_fidelity_canon.py first')

    panel = pd.read_csv(PANEL)
    details = pd.read_csv(DETAILS)

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    rows = []
    summary = []

    for s in seasons:
        sstr = str(int(float(s)))
        method = 'rank' if int(float(s)) in (1,2) else ('percent' if 3 <= int(float(s)) <= 27 else 'percent_last_two')
        replay_path = find_replay(method, sstr)
        elim_map = read_pred_survivors(replay_path, sstr)

        panel_s = panel[panel['season'].astype(str) == sstr].copy()
        if 'active' in panel_s.columns:
            try:
                panel_s = panel_s[panel_s['active'].astype(bool)]
            except Exception:
                panel_s = panel_s[panel_s['active'] == True]
        panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
        weeks = sorted(panel_s['week'].dropna().unique())
        if not weeks:
            continue
        initial = sorted(panel_s.loc[panel_s['week'] == weeks[0], 'celebrity_name'].dropna().astype(str).unique().tolist())
        pred_survivors = {}
        curr = set(initial)
        for w in weeks:
            preds = elim_map.get(int(w), [])
            curr = set(curr) - set(preds)
            pred_survivors[int(w)] = set(curr)

        actual_surv = build_actual_survivors(panel, sstr)

        det_s = details[details['season'].astype(str) == sstr]
        for _, r in det_s.iterrows():
            cls = classify_row(r, actual_surv, pred_survivors, weeks)
            rows.append({'season': sstr, 'canon_method': method, 'week': int(r['week']), 'jaccard': float(r['jaccard']), 'actual_count': int(r['actual_count']), 'pred_count': int(r['pred_count']), 'intersection': int(r['intersection']), 'classification': cls})

        df_r = pd.DataFrame(rows)
        df_s = df_r[df_r['season'] == sstr]
        counts = df_s['classification'].value_counts().to_dict()
        summary.append({'season': sstr, 'canon_method': method, **counts})

    pd.DataFrame(rows).to_csv(OUT_TAX, index=False)
    pd.DataFrame(summary).fillna(0).to_csv(OUT_SUM, index=False)
    print('Wrote', OUT_TAX, OUT_SUM)


if __name__ == '__main__':
    main()
