"""
Diagnose uniformity of p_est across weeks.

Usage:
  py diagnose_uniformity.py --panel output/data_cleaned/intermediate_weekly_panel.csv --pest src/sim/fan_shares_entropy.csv --xi src/sim/xi_entropy.csv --out report_entropy.csv

This script computes per-week metrics:
 - n_participants
 - entropy H = -sum p log p
 - normalized_entropy = H / log(n)
 - variance of p
 - KL(p || uniform) = log(n) - H
 - KL(p || qJ) (when qJ available, use eps)

Writes per-week CSV and prints a short summary (mean entropy, mean KL, mean variance, mean xi).
"""
from __future__ import annotations
import argparse
import math
import numpy as np
import pandas as pd


def safe_entropy(p_vec, eps=1e-12):
    p = np.array(p_vec, dtype=float)
    p = np.clip(p, eps, 1.0)
    return float(-np.sum(p * np.log(p)))


def safe_kl(p, q, eps=1e-12):
    p = np.clip(np.array(p, dtype=float), eps, 1.0)
    q = np.clip(np.array(q, dtype=float), eps, 1.0)
    return float(np.sum(p * np.log(p / q)))


def main(argv: list[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', required=True)
    p.add_argument('--xi', required=False, default=None)
    p.add_argument('--out', required=False, default='src/sim/diagnose_uniformity_report.csv')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest = pd.read_csv(args.pest)
    xi = pd.read_csv(args.xi) if args.xi and pd.io.common.file_exists(args.xi) else None

    # prepare qJ from panel per week
    panel['week'] = pd.to_numeric(panel['week'], errors='coerce')
    pest['week'] = pd.to_numeric(pest['week'], errors='coerce')
    pest['p_est'] = pd.to_numeric(pest['p_est'], errors='coerce').fillna(0.0)

    weeks = sorted(pest['week'].dropna().unique())
    rows = []
    for w in weeks:
        g = pest[pest['week'] == w]
        if g.empty:
            continue
        names = g['celebrity_name'].astype(str).tolist()
        p_vec = g['p_est'].astype(float).values
        n = len(p_vec)
        sum_p = float(np.sum(p_vec))
        # normalize if not exactly 1
        if sum_p > 0:
            p_vec = p_vec / sum_p
        else:
            # uniform fallback
            p_vec = np.ones(n) / max(1, n)

        H = safe_entropy(p_vec)
        norm_H = H / math.log(n) if n > 1 else 1.0
        var = float(np.var(p_vec, ddof=0))
        KL_uniform = float(math.log(n) - H) if n > 1 else 0.0

        # compute qJ from panel for week
        sub = panel[panel['week'] == w]
        sub = sub[sub['celebrity_name'].astype(str).isin(names)]
        if not sub.empty:
            totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float).values
            denom = float(np.nansum(totals))
            if denom == 0:
                qJ = np.ones(n) / max(1, n)
            else:
                # align order
                name_to_q = {str(r['celebrity_name']): float(r['total_judge_score']) / denom for _, r in sub.iterrows()}
                qJ = np.array([name_to_q.get(str(name), 0.0) for name in names], dtype=float)
                qJ_sum = qJ.sum()
                if qJ_sum > 0:
                    qJ = qJ / qJ_sum
                else:
                    qJ = np.ones(n) / max(1, n)
        else:
            qJ = np.ones(n) / max(1, n)

        KL_qJ = safe_kl(p_vec, qJ)
        xi_val = None
        if xi is not None:
            row_x = xi[(xi['week'] == w) & (xi['season'].astype(str) == str(g['season'].iloc[0]))]
            if not row_x.empty:
                xi_val = float(row_x['xi'].iloc[0])
        rows.append({'season': g['season'].iloc[0], 'week': int(w), 'n': n, 'p_sum': sum_p, 'entropy': H, 'norm_entropy': norm_H, 'variance': var, 'kl_uniform': KL_uniform, 'kl_qJ': KL_qJ, 'xi': xi_val})

    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)

    # print summary
    summary = {
        'weeks': len(out),
        'mean_entropy': out['entropy'].mean(),
        'median_entropy': out['entropy'].median(),
        'mean_norm_entropy': out['norm_entropy'].mean(),
        'mean_variance': out['variance'].mean(),
        'mean_kl_uniform': out['kl_uniform'].mean(),
        'mean_kl_qJ': out['kl_qJ'].mean(),
        'mean_xi': float(out['xi'].dropna().mean()) if 'xi' in out.columns and out['xi'].notna().any() else None,
    }

    print('Wrote', args.out)
    print('Summary:')
    for k, v in summary.items():
        print(f'  {k}: {v}')

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
