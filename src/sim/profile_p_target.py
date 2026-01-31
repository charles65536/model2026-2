"""
Profile p_{i,t} credibility by fixing its value on a grid and re-solving the QP.

Usage example:
  py profile_p_target.py --panel output/data_cleaned/intermediate_weekly_panel.csv --name "Rachel Hunter" --season 1 --week 2 --pest src/sim/test_fan_p.csv --alpha 0.5 --lambda_reg 1000

Outputs a CSV `src/sim/profile_{season}_{name}_{week}.csv` with columns: v (fixed p), objective, max_xi, success
"""
from __future__ import annotations
import argparse
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

try:
    from scipy.optimize import minimize
except Exception as e:
    raise ImportError("scipy is required") from e


def build_problem(season_panel: pd.DataFrame, alpha: float = 0.5, hard_consistency: bool = False):
    # similar to model_main's setup but returns mappings and helper data for objective/constraints
    df = season_panel.copy()
    name_col = 'celebrity_name' if 'celebrity_name' in df.columns else [c for c in df.columns if df[c].dtype==object][0]
    week_col = 'week'
    df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
    weeks = sorted(df[week_col].dropna().unique())
    A_t: Dict[int, List[str]] = {}
    for w in weeks:
        names = df.loc[(df[week_col]==w) & (~df['total_judge_score'].isna()), name_col].astype(str).tolist()
        A_t[w] = sorted(list(dict.fromkeys(names)))

    rev_map: List[Tuple[str,int]] = []
    var_index: Dict[Tuple[str,int],int] = {}
    for w in weeks:
        for name in A_t[w]:
            idx = len(rev_map)
            rev_map.append((name,w))
            var_index[(name,w)] = idx
    n_p = len(rev_map)
    n_xi = 0 if hard_consistency else len(weeks)
    week_to_xi_idx = {w:i for i,w in enumerate(weeks)}
    n_var = n_p + n_xi

    # compute smooth_pairs
    smooth_pairs = []
    for i in range(1,len(weeks)):
        w_prev,w_curr = weeks[i-1], weeks[i]
        common = sorted(list(set(A_t[w_prev]) & set(A_t[w_curr])))
        for name in common:
            smooth_pairs.append((var_index[(name,w_prev)], var_index[(name,w_curr)]))

    # qJ
    qJ = {}
    for w in weeks:
        sub = df[df[week_col]==w]
        sub = sub[sub[name_col].astype(str).isin(A_t[w])]
        totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
        denom = totals.sum()
        if denom==0:
            for name in A_t[w]:
                qJ[(name,w)] = 1.0/max(1,len(A_t[w]))
        else:
            for _,r in sub.iterrows():
                qJ[(str(r[name_col]),w)] = float(r['total_judge_score'])/float(denom)

    # elimination sets
    elim_col = None
    for cand in ('true_elim_flag','is_elim_exit_week','is_elim'):
        if cand in df.columns:
            elim_col = cand
            break
    E_t = {w: [] for w in weeks}
    if elim_col:
        for w in weeks:
            E_t[w] = df.loc[(df[week_col]==w) & (df[elim_col].astype(bool)), name_col].astype(str).tolist()

    return {
        'rev_map': rev_map,
        'var_index': var_index,
        'weeks': weeks,
        'n_var': n_var,
        'n_p': n_p,
        'n_xi': n_xi,
        'week_to_xi_idx': week_to_xi_idx,
        'smooth_pairs': smooth_pairs,
        'qJ': qJ,
        'A_t': A_t,
        'E_t': E_t,
        'name_col': name_col,
        'week_col': week_col,
        'alpha': alpha,
    }


def solve_with_fixed_target(problem, lambda_reg, target, fixed_value, hard_consistency=False):
    # target: (name, week)
    rev_map = problem['rev_map']; var_index = problem['var_index']; n_var = problem['n_var']
    n_p = problem['n_p']; n_xi = problem['n_xi']
    smooth_pairs = problem['smooth_pairs']
    qJ = problem['qJ']
    weeks = problem['weeks']
    week_to_xi_idx = problem['week_to_xi_idx']
    alpha = problem['alpha']

    # initial x0 uniform
    x0 = np.zeros(n_var)
    for (name,w), idx in var_index.items():
        # uniform among that week
        cnt = len(problem['A_t'][w])
        x0[idx] = 1.0/ max(1,cnt)
    for i in range(n_p, n_p+n_xi):
        x0[i] = 1e-6

    # objective
    def obj(x):
        p = x[:n_p]
        xi = x[n_p:] if n_xi>0 else np.zeros(0)
        s = 0.0
        for a,b in smooth_pairs:
            d = p[b]-p[a]
            s += d*d
        # entropy penalty if requested in problem dict
        entropy_reg = problem.get('entropy_reg', 0.0)
        if entropy_reg and entropy_reg > 0.0:
            eps = 1e-12
            for w, idxs in problem['week_to_p_idxs'].items():
                if len(idxs) == 0:
                    continue
                vals = p[idxs]
                s += float(entropy_reg) * float(np.sum(vals * np.log(vals + eps)))
        # popularity coupling if requested
        popularity_reg = problem.get('popularity_reg', 0.0)
        if popularity_reg and popularity_reg > 0.0:
            # build qJ vector aligned with var_index (problem['var_index'])
            qj_vec = np.zeros(n_p)
            for idx, (name,w) in enumerate(problem['rev_map']):
                qj_vec[idx] = float(problem['qJ'].get((name,w), 0.0))
            s += float(popularity_reg) * float(np.sum((p - qj_vec)**2))
        s += float(lambda_reg)*float(np.sum(xi*xi))
        return float(s)

    # constraints: equality per-week sum p =1
    cons = []
    def make_eq(idxs_local):
        return {'type': 'eq', 'fun': lambda x, idxs_local=idxs_local: float(np.sum(x[idxs_local]) - 1.0)}
    for w in weeks:
        idxs = [var_index[(name,w)] for name in problem['A_t'][w]]
        cons.append(make_eq(idxs))
    # elimination inequalities
    for w in weeks:
        E = problem['E_t'].get(w, [])
        others = [name for name in problem['A_t'][w] if name not in set(E)]
        if len(E)==0 or len(others)==0: continue
        if hard_consistency:
            for e in E:
                for i_name in others:
                    ie = var_index[(e,w)]; ii = var_index[(i_name,w)]
                    q_e = qJ.get((e,w),0.0); q_i = qJ.get((i_name,w),0.0)
                    # (1-alpha)*(p_e - p_i) - alpha*(q_i - q_e) <= 0 -> implement -LHS >=0
                    cons.append({'type':'ineq', 'fun': lambda x, ie=ie, ii=ii, c=alpha*(q_i - q_e): -(((1-alpha)*(x[ie]-x[ii])) - c)})
        else:
            for e in E:
                for i_name in others:
                    ie = var_index[(e,w)]; ii = var_index[(i_name,w)]; xi_idx = n_p + week_to_xi_idx[w]
                    q_e = qJ.get((e,w),0.0); q_i = qJ.get((i_name,w),0.0)
                    cons.append({'type':'ineq', 'fun': lambda x, ie=ie, ii=ii, xi_i=xi_idx, c=alpha*(q_i - q_e): -(((1-alpha)*(x[ie]-x[ii]) - x[xi_i]) - c)})
    # bounds
    bnds = [(0.0,1.0)]*n_p + ([(0.0,None)]*n_xi if n_xi>0 else [])
    # add equality fixing target
    tgt_idx = var_index.get((target[0], target[1]), None)
    if tgt_idx is None:
        return {'success':False, 'message':'target not present'}
    cons.append({'type':'eq', 'fun': lambda x, idx=tgt_idx, v=fixed_value: float(x[idx] - v)})

    # use default options to satisfy static typing; solver still accepts maxiter in practice if needed
    res = minimize(obj, x0, method='SLSQP', bounds=bnds, constraints=cons, options=None)
    if not res.success:
        return {'success':False, 'message':res.message}
    x = res.x
    p = x[:n_p]
    xi = x[n_p:] if n_xi>0 else np.zeros(0)
    return {'success':True, 'objective': float(res.fun), 'max_xi': float(np.max(xi)) if xi.size>0 else 0.0}


def main(argv: List[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--season', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--week', type=int, required=True)
    p.add_argument('--pest', required=True)
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--lambda_reg', type=float, default=1000.0)
    p.add_argument('--variance_reg', type=float, default=0.0, help='(deprecated) kept for compatibility')
    p.add_argument('--entropy_reg', type=float, default=0.0)
    p.add_argument('--popularity_reg', type=float, default=0.0)
    p.add_argument('--hard', action='store_true')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest = pd.read_csv(args.pest)
    # prepare season
    season_panel = panel[panel['season'].astype(str)==str(args.season)].copy()
    problem = build_problem(season_panel, alpha=args.alpha, hard_consistency=args.hard)
    # attach variance_reg and week_to_p_idxs for profiling objective
    problem['variance_reg'] = float(args.variance_reg)
    problem['entropy_reg'] = float(args.entropy_reg)
    problem['popularity_reg'] = float(args.popularity_reg)
    # build week_to_p_idxs mapping similar to model_main
    problem['week_to_p_idxs'] = {w: [problem['var_index'][(name,w)] for name in problem['A_t'][w]] for w in problem['weeks']}

    # get p_est value
    row = pest[(pest['season'].astype(str)==str(args.season)) & (pest['celebrity_name']==args.name) & (pest['week']==args.week)]
    p0 = None
    if not row.empty:
        p0 = float(row['p_est'].iloc[0])
    else:
        print('Warning: target not found in p_est file; continuing with None')

    # grid
    grid = np.linspace(0.0, 0.2, 21)  # up to 20% for small p testing
    results = []
    for v in grid:
        res = solve_with_fixed_target(problem, args.lambda_reg, (args.name, args.week), v, hard_consistency=args.hard)
        results.append({'v': float(v), 'success': bool(res.get('success',False)), 'objective': res.get('objective',None), 'max_xi': res.get('max_xi',None), 'message': res.get('message','')})
    out = pd.DataFrame(results)
    fname = f"src/sim/profile_{args.season}_{args.name.replace(' ','_')}_{args.week}.csv"
    out.to_csv(fname, index=False)
    print(f"Wrote {fname}")
    print(out.to_string(index=False))

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
