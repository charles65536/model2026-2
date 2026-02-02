"""Fit mixed-effects models for fan share (Task C).

Produces a MixedLM fit for logit(p_est) with fixed effects for age, industry,
and judge score, plus random intercepts for `season` and variance component
for `celebrity_name` (if present).

Usage:
  PYTHONPATH=. python3 src/eval/fit_mixed_effects.py --data output/data_cleaned/clean_long_data_new1.csv --out_dir src/eval

Outputs:
  - `{out_dir}/mixed_effects_summary.txt`
  - `{out_dir}/mixed_effects_result.pkl`
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
import numpy as np

def find_p_column(df: pd.DataFrame):
    candidates = ['p_est', 'p', 'p_mean', 'p_pct', 'fan_share', 'p_at_key']
    for c in candidates:
        if c in df.columns:
            return c
    return None


def logit_clip(s: pd.Series, eps: float = 1e-4) -> pd.Series:
    s2 = s.clip(eps, 1 - eps)
    return np.log(s2 / (1 - s2))


def main(argv=None):
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM

    p = argparse.ArgumentParser()
    p.add_argument('--data', default=os.path.join('output', 'data_cleaned', 'clean_long_data_new1.csv'))
    p.add_argument('--out_dir', default=os.path.join('src', 'eval'))
    p.add_argument('--force_pcol', default=None)
    args = p.parse_args(argv)

    os.makedirs(args.out_dir, exist_ok=True)
    if not os.path.exists(args.data):
        print('Data file not found:', args.data)
        sys.exit(2)

    df = pd.read_csv(args.data)
    print('Loaded', len(df), 'rows from', args.data)

    pcol = args.force_pcol or find_p_column(df)
    if pcol is None:
        print('No p-like column found in data. Please provide `--force_pcol` or include p_est in the dataset.')
        sys.exit(2)

    print('Using p column:', pcol)
    df = df.copy()
    df['p_for_model'] = pd.to_numeric(df[pcol], errors='coerce')
    df = df[df['p_for_model'].notna()].copy()
    if df.empty:
        print('No rows with valid p values found.')
        sys.exit(2)

    # create logit response
    df['y_logit_p'] = logit_clip(df['p_for_model'])

    # ensure key covariates exist or create defaults
    if 'age' not in df.columns:
        df['age'] = pd.to_numeric(df.get('Age', np.nan)).fillna(0)
    else:
        df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)

    # use judge percent if available
    if 'J_pct' in df.columns:
        df['J_pct_num'] = pd.to_numeric(df['J_pct'], errors='coerce').fillna(0)
    elif 'J_total' in df.columns and 'J_sum_week' in df.columns:
        df['J_pct_num'] = pd.to_numeric(df['J_total'], errors='coerce') / pd.to_numeric(df['J_sum_week'], errors='coerce')
        df['J_pct_num'] = df['J_pct_num'].fillna(0)
    else:
        df['J_pct_num'] = 0.0

    # industry categorical
    industry_col = None
    for c in ['celebrity_industry', 'industry', 'Industry']:
        if c in df.columns:
            industry_col = c
            break
    if industry_col is None:
        df['celebrity_industry'] = 'Unknown'
        industry_col = 'celebrity_industry'

    # grouping vars
    if 'season' not in df.columns:
        print('No `season` column found — adding dummy season=0')
        df['season'] = 0
    df['season'] = df['season'].astype(str)

    if 'celebrity_name' not in df.columns:
        df['celebrity_name'] = df.get('celebrity', df.get('name', 'unknown')).astype(str)

    # build formula
    formula = 'y_logit_p ~ age + J_pct_num + C(%s)' % industry_col

    print('Fitting MixedLM with formula:', formula)

    # Use season as groups (random intercept) and celebrity_name as variance component if present
    vc = None
    try:
        vc = {'celebrity': '0 + C(celebrity_name)'}
        md = MixedLM.from_formula(formula, groups=df['season'], vc_formula=vc, data=df)
        mdf = md.fit(method='lbfgs')
    except Exception as e:
        print('MixedLM with variance components failed:', e)
        print('Retrying MixedLM with season as groups only.')
        md = MixedLM.from_formula(formula, groups=df['season'], data=df)
        mdf = md.fit(method='lbfgs')

    out_sum = os.path.join(args.out_dir, 'mixed_effects_summary.txt')
    with open(out_sum, 'w') as f:
        f.write(str(mdf.summary()))
        f.write('\n\n')
        # variance components if available
        try:
            f.write('Random effects covariance (cov_re):\n')
            f.write(str(mdf.cov_re))
            f.write('\n\n')
        except Exception:
            pass
        try:
            f.write('Variance components (vcomp):\n')
            f.write(str(mdf.vcomp))
            f.write('\n\n')
        except Exception:
            pass
        f.write('Residual scale: %s\n' % getattr(mdf, 'scale', 'NA'))

    # save model
    try:
        import pickle
        with open(os.path.join(args.out_dir, 'mixed_effects_result.pkl'), 'wb') as f:
            pickle.dump(mdf, f)
    except Exception as e:
        print('Could not pickle model:', e)

    print('Wrote summary to', out_sum)


if __name__ == '__main__':
    main(sys.argv[1:])
