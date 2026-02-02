"""Plot leaderboards using seaborn and save PNGs.

Produces:
- `output/fig/task3/top10_stars_judges_audience.png` (side-by-side bars)
- `output/fig/task3/top10_pros_judges_audience.png`
- `output/fig/task3/top10_stars_elim.png` (elim log-odds)
- `output/fig/task3/top10_pros_elim.png`
- `output/fig/task3/industries_elim.png`
"""
from __future__ import annotations
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TASK3 = os.path.join(ROOT, 'src', 'eval', 'task3')
OUTFIG = os.path.join(ROOT, 'output', 'fig', 'task3')
os.makedirs(OUTFIG, exist_ok=True)


def plot_top10_side_by_side(df, key1, key2, title, outpath):
    df2 = df.dropna(subset=[key1, key2]).sort_values(key1 + '|' + key2 if False else key1, ascending=False).head(10)
    # build long form
    long = df2.melt(id_vars=['entity'], value_vars=[key1, key2], var_name='metric', value_name='value')
    plt.figure(figsize=(10, 6))
    sns.barplot(data=long, x='value', y='entity', hue='metric')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def plot_single_metric(df, key, title, outpath, top=True):
    df2 = df.dropna(subset=[key]).sort_values(key, ascending=not top).head(10)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df2, x=key, y='entity')
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def main():
    stars = pd.read_csv(os.path.join(TASK3, 'leaderboards_stars.csv'))
    pros = pd.read_csv(os.path.join(TASK3, 'leaderboards_pros.csv'))
    inds = pd.read_csv(os.path.join(TASK3, 'leaderboards_industries.csv'))

    # Ensure expected columns exist
    for df in (stars, pros, inds):
        if 'entity' not in df.columns:
            raise SystemExit('leaderboard missing entity column')

    # Side-by-side judges vs audience for stars and pros
    if 'judges_blup' in stars.columns and 'audience_blup' in stars.columns:
        plot_top10_side_by_side(stars.rename(columns={'celebrity_name':'entity'}), 'judges_blup', 'audience_blup',
                                'Top 10 Stars: Judges vs Audience BLUPs', os.path.join(OUTFIG, 'top10_stars_judges_audience.png'))
    if 'judges_blup' in pros.columns and 'audience_blup' in pros.columns:
        plot_top10_side_by_side(pros.rename(columns={'ballroom_partner':'entity'}), 'judges_blup', 'audience_blup',
                                'Top 10 Pros: Judges vs Audience BLUPs', os.path.join(OUTFIG, 'top10_pros_judges_audience.png'))

    # Top10 by elimination empirical log-odds (higher = more likely eliminated)
    if 'elim_emp_logodds' in stars.columns:
        stars2 = stars.rename(columns={'celebrity_name':'entity'}) if 'celebrity_name' in stars.columns else stars
        plot_single_metric(stars2, 'elim_emp_logodds', 'Top 10 Stars by Empirical Elimination Log-odds (highest = less safe)',
                           os.path.join(OUTFIG, 'top10_stars_elim.png'), top=True)
    if 'elim_emp_logodds' in pros.columns:
        pros2 = pros.rename(columns={'ballroom_partner':'entity'}) if 'ballroom_partner' in pros.columns else pros
        plot_single_metric(pros2, 'elim_emp_logodds', 'Top 10 Pros by Empirical Elimination Log-odds (highest = less safe)',
                           os.path.join(OUTFIG, 'top10_pros_elim.png'), top=True)

    if 'elim_emp_logodds' in inds.columns:
        plot_single_metric(inds.rename(columns={'celebrity_industry':'entity'}), 'elim_emp_logodds', 'Industries by Empirical Elimination Log-odds',
                           os.path.join(OUTFIG, 'industries_elim.png'), top=True)

    print('Saved figures to', OUTFIG)


if __name__ == '__main__':
    main()
