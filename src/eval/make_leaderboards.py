"""Build leaderboards (top/bottom) for stars, pros and industries.

Stats produced per entity:
- judges_blup: BLUP log-odds from `celebrity_strengths_judges.csv` / `pro_strengths_judges.csv`
- audience_blup: BLUP log-odds from `celebrity_strengths_audience.csv` / `pro_strengths_audience.csv`
- elim_emp_logodds: empirical smoothed elimination log-odds computed from panel

Outputs saved to `src/eval/task3/leaderboards_*.csv` and printed to stdout.
"""
from __future__ import annotations
import os
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TASK3 = os.path.join(ROOT, 'src', 'eval', 'task3')
os.makedirs(TASK3, exist_ok=True)

PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'clean_long_data_replay_ready.csv')
CELEB_J = os.path.join(TASK3, 'celebrity_strengths_judges.csv')
CELEB_V = os.path.join(TASK3, 'celebrity_strengths_audience.csv')
PRO_J = os.path.join(TASK3, 'pro_strengths_judges.csv')
PRO_V = os.path.join(TASK3, 'pro_strengths_audience.csv')


def logit(p, eps=1e-9):
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def load_blups(path):
    if os.path.exists(path):
        df = pd.read_csv(path)
        # ensure columns
        if 'entity' in df.columns and 'blup_logodds' in df.columns:
            return df.set_index('entity')
    return pd.DataFrame(columns=['n_obs', 'blup_logodds', 'odds_ratio']).set_index(pd.Index([], name='entity'))


def compute_elim_empirical(panel):
    df = pd.read_csv(panel)
    # determine elimination flag
    if 'eliminated' in df.columns:
        df['E'] = df['eliminated'].astype(int)
    elif 'true_elim_flag' in df.columns:
        df['E'] = df['true_elim_flag'].astype(int)
    else:
        df['E'] = 0
        if 'elim_week' in df.columns and 'week' in df.columns:
            df.loc[df['week'] == df['elim_week'], 'E'] = 1

    # celebrities
    celebs = df.groupby('celebrity_name').agg(n_obs=('E', 'size'), elim_sum=('E', 'sum'))
    celebs['elim_emp_rate'] = (celebs['elim_sum'] + 0.5) / (celebs['n_obs'] + 1.0)
    celebs['elim_emp_logodds'] = logit(celebs['elim_emp_rate'])

    # pros
    pros = df.groupby('ballroom_partner').agg(n_obs=('E', 'size'), elim_sum=('E', 'sum'))
    pros['elim_emp_rate'] = (pros['elim_sum'] + 0.5) / (pros['n_obs'] + 1.0)
    pros['elim_emp_logodds'] = logit(pros['elim_emp_rate'])

    # industry
    industry = df.groupby('celebrity_industry').agg(n_obs=('E', 'size'), elim_sum=('E', 'sum'))
    industry['elim_emp_rate'] = (industry['elim_sum'] + 0.5) / (industry['n_obs'] + 1.0)
    industry['elim_emp_logodds'] = logit(industry['elim_emp_rate'])

    return celebs, pros, industry


def merge_and_save():
    celebj = load_blups(CELEB_J)
    celebv = load_blups(CELEB_V)
    proj = load_blups(PRO_J)
    prov = load_blups(PRO_V)

    celebs_elim, pros_elim, ind_elim = compute_elim_empirical(PANEL)

    # merge for celebrities
    celebs = celebs_elim.join(celebj[['blup_logodds']].rename(columns={'blup_logodds': 'judges_blup'}), how='left')
    celebs = celebs.join(celebv[['blup_logodds']].rename(columns={'blup_logodds': 'audience_blup'}), how='left')
    celebs = celebs.reset_index().rename(columns={'celebrity_name': 'entity'})
    celebs.to_csv(os.path.join(TASK3, 'leaderboards_stars.csv'), index=False)

    # pros
    pros = pros_elim.join(proj[['blup_logodds']].rename(columns={'blup_logodds': 'judges_blup'}), how='left')
    pros = pros.join(prov[['blup_logodds']].rename(columns={'blup_logodds': 'audience_blup'}), how='left')
    pros = pros.reset_index().rename(columns={'ballroom_partner': 'entity'})
    pros.to_csv(os.path.join(TASK3, 'leaderboards_pros.csv'), index=False)

    # industry: compute weighted mean of celebrity BLUPs by industry where available
    if not celebj.empty:
        cj = celebj.reset_index()
        panel = pd.read_csv(PANEL)
        mapping = panel[['celebrity_name', 'celebrity_industry']].drop_duplicates().set_index('celebrity_name')
        cj = cj.join(mapping, on='entity')
        # use n_obs if present
        if 'n_obs' in cj.columns:
            ind_stats = cj.groupby('celebrity_industry').apply(lambda d: pd.Series({'judges_blup': np.average(d['blup_logodds'], weights=d['n_obs']) if d['n_obs'].sum()>0 else d['blup_logodds'].mean()}))
        else:
            ind_stats = cj.groupby('celebrity_industry').blup_logodds.mean().rename('judges_blup').to_frame()
        ind_stats = ind_stats.reset_index()
        inds = ind_elim.reset_index().merge(ind_stats, on='celebrity_industry', how='left')
    else:
        inds = ind_elim.reset_index()

    inds = inds.rename(columns={'celebrity_industry': 'entity'})
    inds.to_csv(os.path.join(TASK3, 'leaderboards_industries.csv'), index=False)

    print('\nTop 10 stars by judges_blup:')
    print(celebs[['entity', 'n_obs', 'judges_blup']].sort_values('judges_blup', ascending=False).head(10).to_string(index=False))
    print('\nBottom 10 stars by judges_blup:')
    print(celebs[['entity', 'n_obs', 'judges_blup']].sort_values('judges_blup', ascending=True).head(10).to_string(index=False))

    print('\nTop 10 pros by judges_blup:')
    print(pros[['entity', 'n_obs', 'judges_blup']].sort_values('judges_blup', ascending=False).head(10).to_string(index=False))
    print('\nBottom 10 pros by judges_blup:')
    print(pros[['entity', 'n_obs', 'judges_blup']].sort_values('judges_blup', ascending=True).head(10).to_string(index=False))

    print('\nTop 10 industries by elim_emp_logodds (less safe):')
    print(inds[['entity', 'n_obs', 'elim_emp_logodds']].sort_values('elim_emp_logodds', ascending=False).head(10).to_string(index=False))
    print('\nBottom 10 industries by elim_emp_logodds (safer):')
    print(inds[['entity', 'n_obs', 'elim_emp_logodds']].sort_values('elim_emp_logodds', ascending=True).head(10).to_string(index=False))


if __name__ == '__main__':
    merge_and_save()
