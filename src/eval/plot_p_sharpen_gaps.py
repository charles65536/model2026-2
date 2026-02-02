#!/usr/bin/env python3
"""Plot gap metrics from p_est sharpening runs.

Reads `src/sim/p_sharpen_gap_summary.csv` and per-gamma detail files
`src/sim/p_sharpen_gap_details_gamma*.csv` and writes PNGs to `output/fig/`.
"""
from __future__ import annotations
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


OUT_DIR = 'output/fig'
SUMMARY_CSV = 'src/sim/p_sharpen_gap_summary.csv'
DETAIL_GLOB = 'src/sim/p_sharpen_gap_details_gamma*.csv'


def ensure_out():
    os.makedirs(OUT_DIR, exist_ok=True)


def plot_summary():
    df = pd.read_csv(SUMMARY_CSV)
    # ensure gamma numeric
    df['gamma'] = df['gamma'].astype(float)
    df = df.sort_values('gamma')

    plt.figure(figsize=(8,4))
    sns.lineplot(data=df, x='gamma', y='median_gap', marker='o', label='median_gap')
    sns.lineplot(data=df, x='gamma', y='mean_gap', marker='o', label='mean_gap')
    plt.xlabel('gamma')
    plt.ylabel('gap (second - worst)')
    plt.title('Gap metrics vs gamma')
    plt.legend()
    out = os.path.join(OUT_DIR, 'p_sharpen_gap_summary.png')
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print('Wrote', out)


def plot_boxplots():
    files = sorted(glob.glob(DETAIL_GLOB))
    if not files:
        print('No detail files found for boxplots')
        return
    parts = []
    for f in files:
        try:
            g = pd.read_csv(f)
        except Exception:
            continue
        # extract gamma from filename
        base = os.path.basename(f)
        gamma = base.replace('p_sharpen_gap_details_gamma', '').replace('.csv','')
        parts.append(g.assign(gamma=gamma))
    allg = pd.concat(parts, ignore_index=True)
    # convert gamma for ordering
    allg['gamma_f'] = allg['gamma'].str.replace('p', '.').astype(float)

    plt.figure(figsize=(10,6))
    order = sorted(allg['gamma_f'].unique())
    sns.boxplot(data=allg, x='gamma_f', y='gap', order=order)
    plt.xlabel('gamma')
    plt.ylabel('gap (second - worst)')
    plt.title('Distribution of worst->second gap by gamma')
    out = os.path.join(OUT_DIR, 'p_sharpen_gap_boxplot.png')
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print('Wrote', out)


def main():
    ensure_out()
    if os.path.exists(SUMMARY_CSV):
        plot_summary()
    else:
        print('Summary CSV not found:', SUMMARY_CSV)
    plot_boxplots()


if __name__ == '__main__':
    main()
