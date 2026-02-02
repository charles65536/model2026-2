"""Aggregate Bias Index across methods, build canonical mapping, and plot comparison.

Produces:
- `src/eval/bias_index_comparison.csv` (mean bias per rule)
- `output/fig/task3/bias_index_comparison.png` (bar chart)
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


def load_bias(method):
    fn = os.path.join(EVAL, f'bias_index_{method}_alpha0p5.csv')
    if os.path.exists(fn):
        return pd.read_csv(fn)
    return pd.DataFrame(columns=['season','method','bias_season'])


def canon_method_for_season(s: int) -> str:
    if s in (1, 2):
        return 'rank'
    if 3 <= s <= 27:
        return 'percent'
    return 'percent_last_two'


def main():
    # Four rules to compare as requested
    methods = ['rank', 'percent', 'percent_last_two', 'professional_bottom_two']
    dfs = {m: load_bias(m) for m in methods}

    combined = []
    for name in methods:
        df = dfs.get(name, pd.DataFrame())
        if df.empty:
            mean_bias = float('nan')
            n_seasons = 0
        else:
            mean_bias = float(df['bias_season'].mean())
            n_seasons = int(len(df))
        combined.append({'rule': name, 'mean_bias': mean_bias, 'n_seasons': n_seasons})

    outdf = pd.DataFrame(combined)
    outcsv = os.path.join(EVAL, 'bias_index_comparison_four_methods_alpha0p5.csv')
    outdf.to_csv(outcsv, index=False)

    # plot bar chart with season counts annotated
    plt.figure(figsize=(7,4))
    ax = sns.barplot(data=outdf, x='rule', y='mean_bias', palette='viridis')
    plt.ylabel('Mean Bias Index (mean across seasons)')
    plt.title('Bias Index Comparison (alpha=0.5)')
    # annotate counts above bars
    for i, row in outdf.iterrows():
        ax.text(i, 0 if pd.isna(row['mean_bias']) else row['mean_bias'] + 0.02, f"n={row['n_seasons']}",
                ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    outfig = os.path.join(OUTFIG, 'bias_index_comparison_four_methods_alpha0p5.png')
    plt.savefig(outfig)
    plt.close()

    print('Wrote', outcsv, 'and', outfig)


if __name__ == '__main__':
    main()
