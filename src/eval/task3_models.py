"""Fit Task 3 models: Judges (A), Audience (B), Elimination risk (C).

Outputs:
 - `src/eval/task3/modelA_judges_summary.txt`
 - `src/eval/task3/modelB_audience_summary.txt`
 - `src/eval/task3/modelC_elim_summary.txt`
 - pickled model objects in `src/eval/task3/`
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEFAULT_PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'clean_long_data_with_p_est_alpha0p5.csv')
OUT_DIR = os.path.join(ROOT, 'src', 'eval', 'task3')
os.makedirs(OUT_DIR, exist_ok=True)


def logit_clip(s: pd.Series, eps: float = 1e-6) -> pd.Series:
    s2 = s.clip(eps, 1 - eps)
    return np.log(s2 / (1 - s2))


def safe_category(df, col, default='Unknown'):
    if col not in df.columns:
        df[col] = default
    df[col] = df[col].fillna(default).astype(str)
    return col


def fit_modelA(df, out_dir):
    # Model A: Judges y^J ~ age + C(industry) + week + FE season; random effects celebrity & pro
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM

    df = df.copy()
    # yJ from J_pct if available else compute
    if 'J_pct' in df.columns:
        df['qJ'] = pd.to_numeric(df['J_pct'], errors='coerce')
    elif 'J_total' in df.columns and 'J_sum_week' in df.columns:
        df['qJ'] = pd.to_numeric(df['J_total'], errors='coerce') / pd.to_numeric(df['J_sum_week'], errors='coerce')
    else:
        raise RuntimeError('No judge share column available')
    df['yJ'] = logit_clip(df['qJ'])

    df['age'] = pd.to_numeric(df.get('age', 0), errors='coerce').fillna(0)
    industry = safe_category(df, 'celebrity_industry')
    df['week_num'] = pd.to_numeric(df.get('week', 0), errors='coerce').fillna(0)
    df['season'] = df.get('season', 0).astype(str)
    df['celebrity_name'] = df['celebrity_name'].astype(str)
    df['ballroom_partner'] = df.get('ballroom_partner', 'Unknown').astype(str)

    formula = 'yJ ~ age + C(%s)' % industry
    vc = {'celebrity': '0 + C(celebrity_name)', 'pro': '0 + C(ballroom_partner)'}
    md = MixedLM.from_formula(formula, groups=df['season'], vc_formula=vc, data=df)
    mdf = md.fit(reml=True, method='lbfgs')

    out_sum = os.path.join(out_dir, 'modelA_judges_summary.txt')
    with open(out_sum, 'w') as f:
        f.write(str(mdf.summary()))
    try:
        import pickle
        with open(os.path.join(out_dir, 'modelA_judges_result.pkl'), 'wb') as f:
            pickle.dump(mdf, f)
    except Exception:
        pass
    return mdf


def fit_modelB(df, out_dir):
    # Model B: Audience y^V ~ y^J + age + C(industry) + week + FE season; random effects celebrity & pro
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM

    df = df.copy()
    # p_est
    if 'p_est' not in df.columns:
        raise RuntimeError('p_est not found in panel')
    df['p_est'] = pd.to_numeric(df['p_est'], errors='coerce')
    df = df[df['p_est'].notna()].copy()
    df['yV'] = logit_clip(df['p_est'])

    # ensure yJ available
    if 'yJ' not in df.columns:
        if 'J_pct' in df.columns:
            df['qJ'] = pd.to_numeric(df['J_pct'], errors='coerce')
        else:
            df['qJ'] = 0.0
        df['yJ'] = logit_clip(df['qJ'])

    df['age'] = pd.to_numeric(df.get('age', 0), errors='coerce').fillna(0)
    industry = safe_category(df, 'celebrity_industry')
    df['week_num'] = pd.to_numeric(df.get('week', 0), errors='coerce').fillna(0)
    df['season'] = df.get('season', 0).astype(str)
    df['celebrity_name'] = df['celebrity_name'].astype(str)
    df['ballroom_partner'] = df.get('ballroom_partner', 'Unknown').astype(str)

    formula = 'yV ~ yJ + age + C(%s)' % industry
    vc = {'celebrity': '0 + C(celebrity_name)', 'pro': '0 + C(ballroom_partner)'}
    md = MixedLM.from_formula(formula, groups=df['season'], vc_formula=vc, data=df)
    mdf = md.fit(reml=True, method='lbfgs')

    out_sum = os.path.join(out_dir, 'modelB_audience_summary.txt')
    with open(out_sum, 'w') as f:
        f.write(str(mdf.summary()))
    try:
        import pickle
        with open(os.path.join(out_dir, 'modelB_audience_result.pkl'), 'wb') as f:
            pickle.dump(mdf, f)
    except Exception:
        pass
    return mdf


def fit_modelC(df, out_dir):
    # Model C: discrete-time logistic for elimination; use GEE with cluster=ballroom_partner (pro)
    import statsmodels.api as sm
    from statsmodels.genmod.generalized_estimating_equations import GEE
    from statsmodels.genmod.families import Binomial
    from statsmodels.genmod.cov_struct import Exchangeable

    df = df.copy()
    # outcome: eliminated or eliminated flag
    if 'eliminated' in df.columns:
        df['E'] = df['eliminated'].astype(bool).astype(int)
    elif 'true_elim_flag' in df.columns:
        df['E'] = df['true_elim_flag'].astype(bool).astype(int)
    else:
        # try placement/elim_week logic
        df['E'] = 0
        if 'elim_week' in df.columns:
            df.loc[df['week'] == df['elim_week'], 'E'] = 1

    # predictors: yJ and yV
    if 'p_est' in df.columns:
        df['yV'] = logit_clip(pd.to_numeric(df['p_est'], errors='coerce').fillna(0.0))
    else:
        df['yV'] = 0.0
    if 'J_pct' in df.columns:
        df['qJ'] = pd.to_numeric(df['J_pct'], errors='coerce').fillna(0.0)
        df['yJ'] = logit_clip(df['qJ'])
    else:
        df['yJ'] = 0.0

    df['age'] = pd.to_numeric(df.get('age', 0), errors='coerce').fillna(0)
    industry = safe_category(df, 'celebrity_industry')
    df['week_num'] = pd.to_numeric(df.get('week', 0), errors='coerce').fillna(0)
    df['season'] = df.get('season', 0).astype(str)
    df['ballroom_partner'] = df.get('ballroom_partner', 'Unknown').astype(str)

    # build design matrix with dummies for industry and season
    # ensure index alignment and numeric dtypes for GEE
    df = df.reset_index(drop=True)
    X = pd.DataFrame({'yJ': df['yJ'], 'yV': df['yV'], 'age': df['age']})
    # add industry dummies
    inds = pd.get_dummies(df['celebrity_industry'], prefix='ind', drop_first=True)
    X = pd.concat([X, inds], axis=1)
    # add season dummies
    seasons = pd.get_dummies(df['season'], prefix='sea', drop_first=True)
    X = pd.concat([X, seasons], axis=1)
    X = sm.add_constant(X, has_constant='add')

    # coerce to numeric and fill missing values (GEE requires numeric float ndarray)
    X = X.astype(float).fillna(0.0)

    groups = df['ballroom_partner'].astype(str)
    fam = Binomial()
    cov = Exchangeable()
    # ensure endog is numeric
    endog = pd.to_numeric(df['E'], errors='coerce')
    # drop rows with NA in endog or exog
    valid_idx = (~endog.isna()) & (~X.isna().any(axis=1))
    if valid_idx.sum() == 0:
        raise RuntimeError('No valid rows for Model C after cleaning')
    endog = endog.loc[valid_idx]
    Xm = X.loc[valid_idx]
    groupsm = groups.loc[valid_idx]

    model = GEE(endog, Xm, groups=groupsm, family=fam, cov_struct=cov)
    result = model.fit()

    out_sum = os.path.join(out_dir, 'modelC_elim_summary.txt')
    with open(out_sum, 'w') as f:
        f.write(str(result.summary()))
    try:
        import pickle
        with open(os.path.join(out_dir, 'modelC_elim_result.pkl'), 'wb') as f:
            pickle.dump(result, f)
    except Exception:
        pass
    return result


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--data', default=DEFAULT_PANEL)
    p.add_argument('--out_dir', default=OUT_DIR)
    args = p.parse_args(argv)

    df = pd.read_csv(args.data)
    print('Loaded', len(df), 'rows from', args.data)

    # Fit models
    print('Fitting Model A (Judges)')
    mA = fit_modelA(df, args.out_dir)
    print('Model A done')

    print('Fitting Model B (Audience)')
    mB = fit_modelB(df, args.out_dir)
    print('Model B done')

    print('Fitting Model C (Elimination risk)')
    mC = fit_modelC(df, args.out_dir)
    print('Model C done')

    print('Saved summaries and model objects to', args.out_dir)


if __name__ == '__main__':
    main(sys.argv[1:])
