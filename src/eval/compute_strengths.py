"""Compute per-entity strength scores (BLUPs) for celebrities and professionals.

Saves CSVs to `src/eval/task3/`:
 - `celebrity_strengths_judges.csv` (blup on log-odds, odds_ratio, n_obs)
 - `celebrity_strengths_audience.csv`
 - `pro_strengths_judges.csv`
 - `pro_strengths_audience.csv`

Also writes `src/eval/task3/strengths_readme.txt` with ICCs.
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PANEL_DEFAULT = os.path.join(ROOT, 'output', 'data_cleaned', 'clean_long_data_with_p_est_alpha0p5.csv')
OUT = os.path.join(ROOT, 'src', 'eval', 'task3')
os.makedirs(OUT, exist_ok=True)


def logit_clip(s, eps=1e-6):
    s2 = s.clip(eps, 1 - eps)
    return np.log(s2 / (1 - s2))


def extract_intercept_from_re(rev):
    # rev may be scalar, array-like, or dict
    if isinstance(rev, dict):
        # take first value
        vals = list(rev.values())
        if len(vals) == 0:
            return 0.0
        v = vals[0]
        try:
            return float(np.asarray(v).ravel()[0])
        except Exception:
            return float(v)
    else:
        try:
            return float(np.asarray(rev).ravel()[0])
        except Exception:
            return float(rev)


def fit_and_extract(df, formula, group_col, vc_formula=None):
    import statsmodels.api as sm
    from statsmodels.regression.mixed_linear_model import MixedLM

    md = MixedLM.from_formula(formula, groups=df[group_col], vc_formula=vc_formula, data=df)
    mres = md.fit(reml=True, method='lbfgs')

    # random effects per group
    res_re = getattr(mres, 'random_effects', {})
    items = []
    # counts per group
    counts = df.groupby(group_col).size()
    for g, cnt in counts.items():
        reval = res_re.get(g, 0.0)
        intercept = extract_intercept_from_re(reval)
        items.append((g, cnt, intercept))

    cols = ['entity', 'n_obs', 'blup_logodds']
    outdf = pd.DataFrame(items, columns=cols)
    outdf['odds_ratio'] = np.exp(outdf['blup_logodds'])

    # variance components
    vcomp = getattr(mres, 'vcomp', None)
    vnames = getattr(mres.model, 'vcomp_names', None)
    scale = getattr(mres, 'scale', np.nan)
    vmap = {}
    if vcomp is not None and vnames is not None:
        vmap = dict(zip(vnames, vcomp))

    return mres, outdf, scale, vmap


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--data', default=PANEL_DEFAULT)
    args = p.parse_args(argv)

    df = pd.read_csv(args.data)
    # prepare yJ and yV
    if 'J_pct' in df.columns:
        df['qJ'] = pd.to_numeric(df['J_pct'], errors='coerce').fillna(0.0)
    else:
        df['qJ'] = 0.0
    df['yJ'] = logit_clip(df['qJ'])

    if 'p_est' in df.columns:
        df['p_est'] = pd.to_numeric(df['p_est'], errors='coerce')
    else:
        df['p_est'] = 0.0
    df['yV'] = logit_clip(df['p_est'].fillna(0.0))

    df['age'] = pd.to_numeric(df.get('age', 0), errors='coerce').fillna(0)
    df['week_num'] = pd.to_numeric(df.get('week', df.get('week_num', 0)), errors='coerce').fillna(0)
    df['celebrity_name'] = df['celebrity_name'].astype(str)
    df['ballroom_partner'] = df.get('ballroom_partner', 'Unknown').astype(str)
    df['celebrity_industry'] = df.get('celebrity_industry', 'Unknown').astype(str)

    # Fit by grouping on celebrity to get celebrity BLUPs (include pro as variance component)
    formula_J = 'yJ ~ age + C(celebrity_industry)'
    vc = {'pro': '0 + C(ballroom_partner)'}
    print('Fitting celebrity-grouped judges model...')
    mresJ, celeb_j_df, scaleJ, vmapJ = fit_and_extract(df, formula_J, 'celebrity_name', vc_formula=vc)
    celeb_j_df.to_csv(os.path.join(OUT, 'celebrity_strengths_judges.csv'), index=False)

    print('Fitting celebrity-grouped audience model...')
    formula_V = 'yV ~ yJ + age + C(celebrity_industry)'
    mresV, celeb_v_df, scaleV, vmapV = fit_and_extract(df, formula_V, 'celebrity_name', vc_formula=vc)
    celeb_v_df.to_csv(os.path.join(OUT, 'celebrity_strengths_audience.csv'), index=False)

    # Fit by grouping on pro to get pro BLUPs (include celebrity as vc)
    print('Fitting pro-grouped judges model...')
    vc2 = {'celebrity': '0 + C(celebrity_name)'}
    mresPJ, pro_j_df, scalePJ, vmapPJ = fit_and_extract(df, formula_J, 'ballroom_partner', vc_formula=vc2)
    pro_j_df.to_csv(os.path.join(OUT, 'pro_strengths_judges.csv'), index=False)

    print('Fitting pro-grouped audience model...')
    mresPV, pro_v_df, scalePV, vmapPV = fit_and_extract(df, formula_V, 'ballroom_partner', vc_formula=vc2)
    pro_v_df.to_csv(os.path.join(OUT, 'pro_strengths_audience.csv'), index=False)

    # write a readme with ICC-like info for celebrity/pro from the celebrity-grouped models
    with open(os.path.join(OUT, 'strengths_readme.txt'), 'w') as f:
        f.write('Model A (celebrity-grouped judges)\n')
        f.write(f'scale (residual var): {scaleJ}\n')
        f.write('vcomp: ' + str(vmapJ) + '\n')
        # compute ICC if possible
        cele_var = vmapJ.get('pro', 0.0)
        # when grouping by celebrity, pro variance appears in vmapJ under 'pro'
        if cele_var is None:
            cele_var = 0.0
        total = cele_var + scaleJ
        f.write(f'approx total (pro_var + resid): {total}\n')

        f.write('\nModel A (celebrity-grouped audience)\n')
        f.write(f'scale (residual var): {scaleV}\n')
        f.write('vcomp: ' + str(vmapV) + '\n')

    print('Saved strength CSVs to', OUT)


if __name__ == '__main__':
    main(sys.argv[1:])
