#!/usr/bin/env python3
"""Compute mean number of judges per season.

Reads `output/data_cleaned/intermediate_weekly_panel.csv`, counts non-null
judge score columns (`judge1_score`..`judge4_score`) per row, aggregates to a
per-week judge count (max across contestants in that week), then computes per
season mean/median/std and writes `src/eval/mean_number_of_judges_per_season.csv`.
"""
import os
import sys
import pandas as pd


def main(panel_path=None, out_path=None):
    if panel_path is None:
        panel_path = os.path.join('output', 'data_cleaned', 'intermediate_weekly_panel.csv')
    if out_path is None:
        out_path = os.path.join('src', 'eval', 'mean_number_of_judges_per_season.csv')

    df = pd.read_csv(panel_path)

    judge_cols = [c for c in df.columns if c.startswith('judge') and c.endswith('_score')]
    if not judge_cols:
        raise KeyError('No judge score columns found in panel (expected judge1_score..judge4_score)')

    # count non-null judge scores per row
    df['judge_count_row'] = df[judge_cols].notnull().sum(axis=1)

    # per-week judge count: take max across contestants to be robust
    per_week = (
        df.groupby(['season', 'week'], as_index=False)
        ['judge_count_row']
        .max()
        .rename(columns={'judge_count_row': 'judge_count_week'})
    )

    summary = (
        per_week.groupby('season')['judge_count_week']
        .agg(n_weeks='count', mean_num_judges='mean', median_num_judges='median', std_num_judges='std')
        .reset_index()
    )

    summary['std_num_judges'] = summary['std_num_judges'].fillna(0.0)
    summary.to_csv(out_path, index=False)
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    panel = None
    out = None
    if len(sys.argv) >= 2:
        panel = sys.argv[1]
    if len(sys.argv) >= 3:
        out = sys.argv[2]
    main(panel, out)
