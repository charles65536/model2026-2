"""
Tune popularity_reg: run the estimator across a grid of popularity_reg values and report diagnostics.

Produces: src/sim/popularity_tuning_report.csv

Defaults: lambda_reg=1000, entropy_reg=0.1 (changeable in code)
"""
from __future__ import annotations
import subprocess
import itertools
import csv
import os
import math
from typing import List

import numpy as np
import pandas as pd

PANEL = "output/data_cleaned/intermediate_weekly_panel.csv"
OUT_REPORT = "src/sim/popularity_tuning_report.csv"
BASE_OUT = "src/sim/fan_shares_pop_baseline.csv"

# grid to try (you can edit)
POPULARITY_GRID = [0.0, 0.01, 0.1, 1.0, 10.0, 100.0]
LAMBDA = 1000.0
ENTROPY = 0.1

EPS = 1e-12


def safe_entropy(p_vec):
    p = np.array(p_vec, dtype=float)
    p = np.clip(p, EPS, 1.0)
    return float(-np.sum(p * np.log(p)))


def safe_kl(p, q):
    p = np.clip(np.array(p, dtype=float), EPS, 1.0)
    q = np.clip(np.array(q, dtype=float), EPS, 1.0)
    return float(np.sum(p * np.log(p / q)))


def summarize_pest(pest_path: str, panel_path: str):
    pest = pd.read_csv(pest_path)
    panel = pd.read_csv(panel_path)
    pest['week'] = pd.to_numeric(pest['week'], errors='coerce')
    pest['p_est'] = pd.to_numeric(pest['p_est'], errors='coerce').fillna(0.0)

    weeks = sorted(pest['week'].dropna().unique())
    entropies = []
    norm_ent = []
    variances = []
    kl_qj_list = []

    for w in weeks:
        g = pest[pest['week'] == w]
        if g.empty:
            continue
        names = g['celebrity_name'].astype(str).tolist()
        p_vec = g['p_est'].astype(float).values
        n = len(p_vec)
        s = float(p_vec.sum())
        if s > 0:
            p_vec = p_vec / s
        else:
            p_vec = np.ones(n) / max(1, n)
        H = safe_entropy(p_vec)
        entropies.append(H)
        norm_ent.append(H / math.log(n) if n > 1 else 1.0)
        variances.append(float(np.var(p_vec, ddof=0)))

        # qJ
        sub = panel[panel['week'] == w]
        sub = sub[sub['celebrity_name'].astype(str).isin(names)]
        if not sub.empty:
            totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float).values
            denom = float(np.nansum(totals))
            if denom == 0:
                qJ = np.ones(n) / max(1, n)
            else:
                name_to_q = {str(r['celebrity_name']): float(r['total_judge_score']) / denom for _, r in sub.iterrows()}
                qJ = np.array([name_to_q.get(str(name), 0.0) for name in names], dtype=float)
                qJ_sum = qJ.sum()
                if qJ_sum > 0:
                    qJ = qJ / qJ_sum
                else:
                    qJ = np.ones(n) / max(1, n)
        else:
            qJ = np.ones(n) / max(1, n)
        kl_qj_list.append(safe_kl(p_vec, qJ))

    return {
        'mean_entropy': float(np.mean(entropies)) if entropies else None,
        'mean_norm_entropy': float(np.mean(norm_ent)) if norm_ent else None,
        'mean_variance': float(np.mean(variances)) if variances else None,
        'mean_kl_qJ': float(np.mean(kl_qj_list)) if kl_qj_list else None,
        'n_weeks': len(entropies),
    }


def compute_l2_dist(pest_a: str, pest_b: str) -> float:
    a = pd.read_csv(pest_a)
    b = pd.read_csv(pest_b)
    # align rows by season,name,week
    key_cols = ['season', 'celebrity_name', 'week']
    merged = pd.merge(a, b, on=key_cols, how='inner', suffixes=('_a','_b'))
    if merged.empty:
        return float('nan')
    da = merged['p_est_a'].astype(float).values
    db = merged['p_est_b'].astype(float).values
    # normalize per-week block to avoid scale issues
    # compute L2 per-row then mean
    diffs = da - db
    return float(np.sqrt(np.mean(diffs*diffs)))


def run():
    rows = []
    # baseline run (popularity=0)
    baseline_out = BASE_OUT
    cmd = ["py","src/sim/model_main.py","--panel",PANEL,"--out-p",baseline_out,"--out-xi","src/sim/xi_pop_baseline.csv","--alpha","0.5","--lambda_reg",str(LAMBDA),"--entropy-reg",str(ENTROPY),"--popularity-reg","0.0"]
    print('Running baseline:', ' '.join(cmd))
    subprocess.run(cmd, check=True)
    baseline_summary = summarize_pest(baseline_out, PANEL)

    for pop in POPULARITY_GRID:
        out_p = f"src/sim/fan_shares_pop_{str(pop).replace('.','_')}.csv"
        out_xi = f"src/sim/xi_pop_{str(pop).replace('.','_')}.csv"
        cmd = ["py","src/sim/model_main.py","--panel",PANEL,"--out-p",out_p,"--out-xi",out_xi,"--alpha","0.5","--lambda_reg",str(LAMBDA),"--entropy-reg",str(ENTROPY),"--popularity-reg",str(pop)]
        print('Running:', ' '.join(cmd))
        subprocess.run(cmd, check=True)
        summary = summarize_pest(out_p, PANEL)
        l2 = compute_l2_dist(baseline_out, out_p)
        row = {'popularity': pop}
        row.update(summary)
        row['l2_from_baseline'] = l2
        rows.append(row)

    keys = ['popularity','n_weeks','mean_entropy','mean_norm_entropy','mean_variance','mean_kl_qJ','l2_from_baseline']
    with open(OUT_REPORT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, '') for k in keys})
    print('Wrote', OUT_REPORT)


if __name__ == '__main__':
    run()
