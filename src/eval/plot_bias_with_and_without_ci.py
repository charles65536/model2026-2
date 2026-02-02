"""Plot Bias Index comparison for four rules with and without 95% CIs.

Produces:
- `output/fig/task3/bias_index_comparison_noCI_alpha0p5.png`
- `output/fig/task3/bias_index_comparison_CI_alpha0p5.png`
"""
from __future__ import annotations
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
EVAL = os.path.join(ROOT, 'src', 'eval')
OUTFIG = os.path.join(ROOT, 'output', 'fig', 'task3')
os.makedirs(OUTFIG, exist_ok=True)

METHODS = ['rank', 'percent', 'percent_last_two', 'professional_bottom_two']


def load_method_df(method: str, alpha_tag: str = 'alpha0p5') -> pd.DataFrame:
    fn = os.path.join(EVAL, f'bias_index_{method}_{alpha_tag}.csv')
    if not os.path.exists(fn):
        return pd.DataFrame()
    df = pd.read_csv(fn)
    # try to find the bias column
    if 'bias_season' in df.columns:
        df = df.rename(columns={'bias_season': 'bias'})
    elif 'bias' in df.columns:
        pass
    elif 'value' in df.columns:
        df = df.rename(columns={'value': 'bias'})
    # ensure season and bias cols
    if 'season' not in df.columns or 'bias' not in df.columns:
        return pd.DataFrame()
    df = df[['season', 'bias']].copy()
    df['season'] = df['season'].astype(int)
    df['bias'] = pd.to_numeric(df['bias'], errors='coerce')
    df['method'] = method
    return df


def main():
    parts = []
    for m in METHODS:
        d = load_method_df(m)
        if d.empty:
            print('Warning: missing or empty bias CSV for method', m)
        parts.append(d)

    long = pd.concat(parts, ignore_index=True)
    if long.empty:
        print('No data to plot; exiting')
        return

    order = METHODS
    # Bar chart without CI
    plt.figure(figsize=(7,4))
    ax = sns.barplot(data=long, x='method', y='bias', order=order, ci=None, palette='viridis')
    plt.title('Bias Index Comparison (no CI, alpha=0.5)')
    plt.ylabel('Bias Index (per-season)')
    # annotate counts
    counts = long.groupby('method')['season'].nunique().reindex(order).fillna(0).astype(int)
    for i, m in enumerate(order):
        y = long[long['method'] == m]['bias'].mean()
        ax.text(i, 0 if pd.isna(y) else y + 0.02, f'n={counts.loc[m]}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    out_no_ci = os.path.join(OUTFIG, 'bias_index_comparison_noCI_alpha0p5.png')
    plt.savefig(out_no_ci)
    plt.close()

    # Bar chart with 95% CI (bootstrap as seaborn does)
    plt.figure(figsize=(7,4))
    ax = sns.barplot(data=long, x='method', y='bias', order=order, ci=95, palette='viridis')
    plt.title('Bias Index Comparison (95% CI, alpha=0.5)')
    plt.ylabel('Bias Index (per-season)')
    for i, m in enumerate(order):
        y = long[long['method'] == m]['bias'].mean()
        ax.text(i, 0 if pd.isna(y) else y + 0.02, f'n={counts.loc[m]}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    out_ci = os.path.join(OUTFIG, 'bias_index_comparison_CI_alpha0p5.png')
    plt.savefig(out_ci)
    plt.close()

    print('Wrote', out_no_ci, 'and', out_ci)


if __name__ == '__main__':
    main()
