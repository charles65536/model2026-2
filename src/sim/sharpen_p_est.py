#!/usr/bin/env python3
"""Sharpen p_est by power / temperature transforms and report gap metrics.

Usage:
  python3 src/sim/sharpen_p_est.py <p_est.csv> --gammas 1.0,1.5,2.0,3.0 --out-dir src/sim

Produces:
 - `<out_dir>/fan_shares_gamma{g}.csv` for each gamma (gamma formatting: 1p0, 1p5, ...)
 - `<out_dir>/p_sharpen_gap_summary.csv` containing per-gamma aggregated gap metrics
 - `<out_dir>/p_sharpen_gap_details_gamma{g}.csv` per-week gap details for each gamma

Transforms implemented:
 - power: p' = p ** gamma; normalize per (season, week)
 - temperature (softmax): p' = softmax(log(p) / T) which is equivalent to p^(1/T) / sum

We use the power transform (gamma>=1) by default; gamma>1 sharpens (increases gaps).
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
import numpy as np


def fmt_gamma(g: float) -> str:
    return str(g).replace('.', 'p')


def sharpen_df(pdf: pd.DataFrame, gamma: float) -> pd.DataFrame:
    # expects columns: season, celebrity_name, week, p_est
    out_rows = []
    for (s, w), group in pdf.groupby(['season', 'week']):
        names = group['celebrity_name'].astype(str).tolist()
        p = group['p_est'].astype(float).values
        # protect zeros by small epsilon
        p = np.maximum(p, 1e-12)
        p_pow = np.power(p, float(gamma))
        if p_pow.sum() <= 0:
            p_norm = np.ones_like(p_pow) / len(p_pow)
        else:
            p_norm = p_pow / float(p_pow.sum())
        for name, pv in zip(names, p_norm):
            out_rows.append({'season': s, 'celebrity_name': name, 'week': w, 'p_est': pv})
    return pd.DataFrame(out_rows)


def compute_gap_metrics(orig: pd.DataFrame, sharp: pd.DataFrame) -> pd.DataFrame:
    # For each (season, week) compute worst and second-worst p, gap, and ratio
    rows = []
    merged = sharp.merge(orig, on=['season', 'celebrity_name', 'week'], suffixes=('_sharp', '_orig'))
    for (s, w), g in merged.groupby(['season', 'week']):
        arr = g[['p_est_sharp']].values.flatten() if 'p_est_sharp' in g.columns else g[['p_est']].values.flatten()
        # ensure mapping in case merge columns differ
        if 'p_est_sharp' in g.columns:
            ps = g['p_est_sharp'].values
        else:
            ps = g['p_est'].values
        if len(ps) == 0:
            continue
        order = np.argsort(ps)  # ascending
        worst = ps[order[0]] if len(ps) >= 1 else 0.0
        second = ps[order[1]] if len(ps) >= 2 else 0.0
        gap = second - worst
        rel_gap = gap / second if second > 0 else 0.0
        rows.append({'season': s, 'week': w, 'worst': float(worst), 'second': float(second), 'gap': float(gap), 'rel_gap': float(rel_gap)})
    return pd.DataFrame(rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('p_est', help='p_est CSV file (season,celebrity_name,week,p_est)')
    p.add_argument('--gammas', default='0.0', help='comma separated gamma values; 0 disables sharpening (copies original normalized p_est)')
    p.add_argument('--out-dir', default='src/sim')
    args = p.parse_args()

    pdf = pd.read_csv(args.p_est)
    # normalize input per (season, week)
    def normalize(df):
        out = []
        for (s, w), g in df.groupby(['season', 'week']):
            pvals = g['p_est'].astype(float).values
            ssum = pvals.sum()
            if ssum <= 0:
                pnorm = np.ones_like(pvals) / len(pvals)
            else:
                pnorm = pvals / ssum
            tmp = g.copy()
            tmp['p_est'] = pnorm
            out.append(tmp)
        return pd.concat(out, ignore_index=True)

    pdf = normalize(pdf)
    gammas = [float(x) for x in args.gammas.split(',') if x]
    os.makedirs(args.out_dir, exist_ok=True)

    summary_rows = []
    for g in gammas:
        if float(g) == 0.0:
            # gamma == 0.0 means no sharpening: use normalized original p_est
            sharp = pdf.copy()
        else:
            sharp = sharpen_df(pdf, g)
        # write sharpened p_est
        out_name = f'fan_shares_gamma{fmt_gamma(g)}.csv'
        out_path = os.path.join(args.out_dir, out_name)
        sharp.to_csv(out_path, index=False)

        # compute gap metrics
        # merge to let compute_gap_metrics find the p_est_sharp column
        merged = sharp.rename(columns={'p_est': 'p_est_sharp'}).merge(pdf, on=['season','celebrity_name','week'])
        gaps = []
        for (s, w), grp in merged.groupby(['season', 'week']):
            ps = grp['p_est_sharp'].astype(float).values
            if len(ps) == 0:
                continue
            order = np.argsort(ps)
            worst = float(ps[order[0]])
            second = float(ps[order[1]]) if len(ps) >= 2 else 0.0
            gap = second - worst
            rel_gap = gap / second if second > 0 else 0.0
            gaps.append({'season': s, 'week': w, 'worst': worst, 'second': second, 'gap': gap, 'rel_gap': rel_gap})
        gaps_df = pd.DataFrame(gaps)
        if gaps_df.empty:
            continue
        # aggregate metrics
        summary_rows.append({'gamma': g, 'min_gap': float(gaps_df['gap'].min()), 'median_gap': float(gaps_df['gap'].median()), 'mean_gap': float(gaps_df['gap'].mean()), 'pct_small_gap': float((gaps_df['gap'] < 1e-3).mean())})
        # write details
        details_path = os.path.join(args.out_dir, f'p_sharpen_gap_details_gamma{fmt_gamma(g)}.csv')
        gaps_df.to_csv(details_path, index=False)

    pd.DataFrame(summary_rows).to_csv(os.path.join(args.out_dir, 'p_sharpen_gap_summary.csv'), index=False)
    print('Wrote sharpened p_est files and summary to', args.out_dir)


if __name__ == '__main__':
    main()
