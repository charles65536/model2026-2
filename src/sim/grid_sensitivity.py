"""
Grid sensitivity driver: run the estimator across lambda_reg x entropy_reg grid
and compute concise summary metrics for each run (mean normalized entropy, mean KL to qJ, mean xi).

Usage: py grid_sensitivity.py

Outputs:
 - src/sim/grid_sensitivity_report.csv
 - per-run fan_shares and xi files under src/sim/ (kept)
"""
from __future__ import annotations
import subprocess
import itertools
import csv
import math
import os
from typing import List, Tuple

import numpy as np
import pandas as pd

PANEL = "output/data_cleaned/intermediate_weekly_panel.csv"
OUT_REPORT = "src/sim/grid_sensitivity_report.csv"

# grid to run
LAMBDA_GRID = [100.0, 1000.0, 10000.0]
ENTROPY_GRID = [0.0, 0.1, 1.0, 10.0]

EPS = 1e-12


def safe_entropy(p_vec):
    p = np.array(p_vec, dtype=float)
    p = np.clip(p, EPS, 1.0)
    return float(-np.sum(p * np.log(p)))


def safe_kl(p, q):
    p = np.clip(np.array(p, dtype=float), EPS, 1.0)
    q = np.clip(np.array(q, dtype=float), EPS, 1.0)
    return float(np.sum(p * np.log(p / q)))


def summarize_run(pest_path: str, xi_path: str, panel_path: str) -> dict:
    pest = pd.read_csv(pest_path)
    panel = pd.read_csv(panel_path)
    xi = pd.read_csv(xi_path) if os.path.exists(xi_path) else None

    pest['week'] = pd.to_numeric(pest['week'], errors='coerce')
    pest['p_est'] = pd.to_numeric(pest['p_est'], errors='coerce').fillna(0.0)
    weeks = sorted(pest['week'].dropna().unique())

    entropies = []
    norm_ent = []
    variances = []
    kl_qj_list = []
    xi_list = []

    for w in weeks:
        g = pest[pest['week'] == w]
        if g.empty:
            continue
        names = g['celebrity_name'].astype(str).tolist()
        p_vec = g['p_est'].astype(float).values
        n = len(p_vec)
        sum_p = float(np.sum(p_vec))
        if sum_p > 0:
            p_vec = p_vec / sum_p
        else:
            p_vec = np.ones(n) / max(1, n)
        H = safe_entropy(p_vec)
        entropies.append(H)
        norm_ent.append(H / math.log(n) if n > 1 else 1.0)
        variances.append(float(np.var(p_vec, ddof=0)))

        # qJ from panel
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

        if xi is not None:
            row_x = xi[(xi['week'] == w) & (xi['season'].astype(str) == str(g['season'].iloc[0]))]
            if not row_x.empty:
                xi_list.append(float(row_x['xi'].iloc[0]))

    return {
        'mean_entropy': float(np.mean(entropies)) if entropies else None,
        'median_entropy': float(np.median(entropies)) if entropies else None,
        'mean_norm_entropy': float(np.mean(norm_ent)) if norm_ent else None,
        'mean_variance': float(np.mean(variances)) if variances else None,
        'mean_kl_qJ': float(np.mean(kl_qj_list)) if kl_qj_list else None,
        'mean_xi': float(np.mean(xi_list)) if xi_list else None,
        'n_weeks': len(entropies),
    }


def run_grid(lambda_grid: List[float], entropy_grid: List[float]):
    rows = []
    for lam, ent in itertools.product(lambda_grid, entropy_grid):
        lam_s = str(int(lam)) if float(lam).is_integer() else str(lam)
        ent_s = str(ent).replace('.', '_')
        out_p = f"src/sim/fan_shares_grid_lambda{lam_s}_entropy{ent_s}.csv"
        out_xi = f"src/sim/xi_grid_lambda{lam_s}_entropy{ent_s}.csv"
        cmd = ["py", "src/sim/model_main.py", "--panel", PANEL, "--out-p", out_p, "--out-xi", out_xi, "--alpha", "0.5", "--lambda_reg", str(lam), "--entropy-reg", str(ent)]
        print('Running', ' '.join(cmd))
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print('Run failed for', lam, ent)
            print(res.stdout)
            print(res.stderr)
            rows.append({'lambda': lam, 'entropy': ent, 'error': res.stderr})
            continue
        summary = summarize_run(out_p, out_xi, PANEL)
        row = {'lambda': lam, 'entropy': ent}
        row.update(summary)
        rows.append(row)
    # write consolidated CSV
    keys = ['lambda', 'entropy', 'n_weeks', 'mean_entropy', 'median_entropy', 'mean_norm_entropy', 'mean_variance', 'mean_kl_qJ', 'mean_xi']
    with open(OUT_REPORT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, '') for k in keys})
    print('Wrote', OUT_REPORT)


if __name__ == '__main__':
    run_grid(LAMBDA_GRID, ENTROPY_GRID)
