#!/usr/bin/env python3
"""Compute mean number of judges per season and write CSV summary.

Reads `output/data_cleaned/clean_long_data_replay_ready.csv` and computes
per-week judge counts (from `J_total`) then averages across weeks per season.
Writes `src/eval/mean_judges_per_season.csv` with columns: season, n_weeks,
mean_J_total, median_J_total, std_J_total.
"""
import os
import sys
import pandas as pd


def main(panel_path=None, out_path=None):
    if panel_path is None:
        panel_path = os.path.join("output", "data_cleaned", "clean_long_data_replay_ready.csv")
    if out_path is None:
        out_path = os.path.join("src", "eval", "mean_judges_per_season.csv")

    df = pd.read_csv(panel_path)

    if 'J_total' not in df.columns:
        raise KeyError('Input panel does not contain column "J_total"')

    # get one J_total value per (season, week). Use max to be robust to any duplicates.
    per_week = (
        df.groupby(['season', 'week'], as_index=False)
        ['J_total']
        .max()
        .rename(columns={'J_total': 'J_total_week'})
    )

    summary = (
        per_week.groupby('season')['J_total_week']
        .agg(n_weeks='count', mean_J_total='mean', median_J_total='median', std_J_total='std')
        .reset_index()
    )

    # fill NaN std with 0 for seasons with single week
    summary['std_J_total'] = summary['std_J_total'].fillna(0.0)

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
