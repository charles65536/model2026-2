"""
Fan-share estimator (Task A from modeling spec).

This version treats the provided weekly panel CSV as the canonical, pre-cleaned input.
It will NOT attempt to re-clean or rebuild the panel. Instead it validates presence of
required columns and uses them directly.

Expected panel columns (defaults):
- 'season'
- 'celebrity_name' (or set via --name-col)
- 'week'
- 'total_judge_score' (or set via --score-col)

Optional columns you may point at with flags:
- active column (bool-like) to indicate whether the row is an active contestant that week (--active-col)
- elimination flag column (bool-like) to indicate this row is an elimination occurrence for that contestant that week (--elim-col)

If optional columns are absent, the solver will make minimal, non-destructive assumptions (e.g., treat rows with non-null score as active).

Usage (example):
  py model_main.py --panel path/to/intermediate_weekly_panel.csv --out-p fan_shares.csv --out-xi xi.csv --alpha 0.5 --lambda_reg 1000 \
    --name-col celebrity_name --score-col total_judge_score --active-col active --elim-col true_elim_flag

Note: This file intentionally avoids reimplementing data cleansing — supply `intermediate_weekly_panel.csv` produced by the triage script.
"""
from __future__ import annotations
import argparse
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

try:
    from scipy.optimize import minimize
except Exception as e:
    raise ImportError("scipy is required for this module. Please install scipy (pip install scipy)") from e


def solve_season_qp(panel_season: pd.DataFrame,
                    name_col: str,
                    score_col: str,
                    week_col: str = 'week',
                    active_col: Optional[str] = None,
                    elim_col: Optional[str] = None,
                    alpha: float = 0.5,
                    lambda_reg: float = 1000.0,
                    entropy_reg: float = 0.0,
                    popularity_reg: float = 0.0,
                    verbose: bool = False,
                    maxiter: int = 1000,
                    hard_consistency: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Solve the QP for a single season using the panel as-is.

    Parameters:
      - panel_season: subset of the panel for a single season (no pivoting or reconstruction performed)
      - name_col, score_col: column names in panel_season
      - active_col: optional column name indicating active rows (bool-like). If not provided, rows with non-null scores are treated as active.
      - elim_col: optional column name indicating elimination rows (bool-like). If not provided, no elimination constraints will be used.

    Returns (p_df, xi_df): DataFrames of p estimates and xi per week.
    """
    # Validate required columns exist
    for c in (name_col, score_col, week_col):
        if c not in panel_season.columns:
            raise ValueError(f"Required column '{c}' not found in panel for season. Provide a cleaned weekly panel with this column or use the CLI flags to point to the right column name.")

    # Minimal coercion: ensure week is numeric for sorting
    panel_season = panel_season.copy()
    panel_season[week_col] = pd.to_numeric(panel_season[week_col], errors='coerce')

    # Determine active rows
    if active_col and active_col in panel_season.columns:
        panel_season['__active_flag__'] = panel_season[active_col].astype(bool)
    else:
        # non-destructive minimal assumption: treat rows with non-null score as active
        panel_season['__active_flag__'] = panel_season[score_col].notna() & (panel_season[score_col].astype(float).fillna(0) != 0)

    # Weeks for this season (sorted)
    weeks = sorted(panel_season[week_col].dropna().unique())
    if len(weeks) == 0:
        raise ValueError('No weeks found for season after minimal validation')

    # Build participants list per week directly from the panel
    A_t: Dict[int, List[str]] = {}
    for w in weeks:
        names = panel_season.loc[(panel_season[week_col] == w) & (panel_season['__active_flag__']), name_col].astype(str).tolist()
        A_t[w] = sorted(list(dict.fromkeys(names)))

    # Map variable indices
    index_map: Dict[Tuple[str, int], int] = {}
    rev_map: List[Tuple[str, int]] = []
    for w in weeks:
        for name in A_t[w]:
            idx = len(rev_map)
            index_map[(name, w)] = idx
            rev_map.append((name, w))

    n_p = len(rev_map)
    # number of xi variables: zero when hard_consistency True
    n_xi = 0 if hard_consistency else len(weeks)
    if n_p == 0:
        return pd.DataFrame(columns=['season', name_col, 'week', 'p_est']), pd.DataFrame(columns=['season', 'week', 'xi'])

    week_to_xi_idx: Dict[int, int] = {w: i for i, w in enumerate(weeks)}
    # build per-week index lists for entropy penalty
    week_to_p_idxs: Dict[int, List[int]] = {w: [index_map[(name, w)] for name in A_t[w]] for w in weeks}

    if verbose:
        print(f"Season has {len(weeks)} weeks and {n_p} p-variables")

    # Compute qJ from the panel directly (normalize per-week among active participants)
    qJ: Dict[Tuple[str, int], float] = {}
    for w in weeks:
        mask = (panel_season[week_col] == w) & (panel_season['__active_flag__'])
        sub = panel_season.loc[mask].copy()
        if sub.shape[0] == 0:
            continue
        totals = pd.to_numeric(sub[score_col], errors='coerce').astype(float)
        denom = totals.sum()
        if denom == 0:
            # fallback uniform among listed active participants (minimal, not a cleansing step)
            for name in A_t[w]:
                qJ[(name, w)] = 1.0 / max(1, len(A_t[w]))
        else:
            for _, r in sub.iterrows():
                qJ[(str(r[name_col]), int(r[week_col]))] = float(r[score_col]) / float(denom)

    # Determine elimination sets E_t using the provided elim_col if available
    # Determine elimination sets E_t using the provided elim_col if available
    E_t: Dict[int, List[str]] = {}
    if elim_col and elim_col in panel_season.columns:
        for w in weeks:
            mask = (panel_season[week_col] == w) & (panel_season[elim_col].astype(bool))
            E_t[w] = panel_season.loc[mask, name_col].astype(str).tolist()
    else:
        # No elimination info available in panel -> no elimination constraints will be used
        for w in weeks:
            E_t[w] = []

    # Build smoothness pairs (only for contestants present in consecutive weeks)
    smooth_pairs: List[Tuple[int, int]] = []
    for i in range(1, len(weeks)):
        w_prev, w_curr = weeks[i - 1], weeks[i]
        set_prev = set(A_t[w_prev])
        set_curr = set(A_t[w_curr])
        common = sorted(list(set_prev & set_curr))
        for name in common:
            idx_prev = index_map[(name, w_prev)]
            idx_curr = index_map[(name, w_curr)]
            smooth_pairs.append((idx_prev, idx_curr))

    # Initial guess: uniform per-week distribution among participants
    x0 = np.zeros(n_p + n_xi)
    for w in weeks:
        participants = A_t[w]
        if len(participants) == 0:
            continue
        uniform = 1.0 / max(1, len(participants))
        for name in participants:
            idx = index_map[(name, w)]
            x0[idx] = uniform
    for i_w in range(n_xi):
        x0[n_p + i_w] = 1e-6

    # Objective: temporal smoothness + lambda * xi^2
    def objective(x: np.ndarray) -> float:
        p = x[:n_p]
        xi = x[n_p:] if n_xi > 0 else np.zeros(0)
        s = 0.0
        # smoothness
        for a, b in smooth_pairs:
            d = p[b] - p[a]
            s += d * d
        # per-week entropy penalty: encourage high entropy (more uniform) when entropy_reg>0
        # implement as entropy_reg * sum_i p_i * log(p_i + eps) (minimizing this term encourages larger entropy)
        if entropy_reg and entropy_reg > 0.0:
            eps = 1e-12
            for w, idxs in week_to_p_idxs.items():
                if len(idxs) == 0:
                    continue
                vals = p[idxs]
                s += float(entropy_reg) * float(np.sum(vals * np.log(vals + eps)))
        # popularity coupling: encourage p to be similar to judges' share qJ when requested
        if popularity_reg and popularity_reg > 0.0:
            # build qJ vector aligned with rev_map
            qj_vec = np.zeros(n_p)
            for idx, (name, w) in enumerate(rev_map):
                qj_vec[idx] = float(qJ.get((name, w), 0.0))
            s += float(popularity_reg) * float(np.sum((p - qj_vec) ** 2))
        # regularization on xi
        s += float(lambda_reg) * float(np.sum(xi * xi))
        return float(s)

    # Equality constraints: per-week simplex
    eq_constraints = []
    for w in weeks:
        idxs = [index_map[(name, w)] for name in A_t[w]]

        def make_eq(idxs_local):
            return {
                'type': 'eq',
                'fun': lambda x, idxs_local=idxs_local: float(np.sum(x[idxs_local]) - 1.0)
            }

        eq_constraints.append(make_eq(idxs))

    # Inequality constraints: elimination consistency using provided elim_col (if any)
    ineq_constraints = []
    for w in weeks:
        E = E_t.get(w, [])
        others = [name for name in A_t[w] if name not in set(E)]
        if len(E) == 0 or len(others) == 0:
            continue
        # if hard_consistency is True we enforce S_e <= S_i (no xi), otherwise include xi variable
        if hard_consistency:
            for e in E:
                for i_name in others:
                    idx_e = index_map[(e, w)]
                    idx_i = index_map[(i_name, w)]
                    qJ_e = qJ.get((e, w), 0.0)
                    qJ_i = qJ.get((i_name, w), 0.0)
                    # Inequality (no xi): (1-alpha)*(p_e - p_i) - alpha*(qJ_i - qJ_e) <= 0 -> return -LHS
                    def make_ineq_no_xi(idx_e_local, idx_i_local, const_term):
                        return {
                            'type': 'ineq',
                            'fun': lambda x, ie=idx_e_local, ii=idx_i_local, c=const_term: -(((1.0 - alpha) * (x[ie] - x[ii])) - c)
                        }

                    const_term = alpha * (qJ_i - qJ_e)
                    ineq_constraints.append(make_ineq_no_xi(idx_e, idx_i, const_term))
        else:
            xi_idx = n_p + week_to_xi_idx[w]
            for e in E:
                for i_name in others:
                    idx_e = index_map[(e, w)]
                    idx_i = index_map[(i_name, w)]
                    qJ_e = qJ.get((e, w), 0.0)
                    qJ_i = qJ.get((i_name, w), 0.0)
                    # Inequality with xi: (1-alpha)*(p_e - p_i) - xi_w - alpha*(qJ_i - qJ_e) <= 0
                    def make_ineq(idx_e_local, idx_i_local, xi_idx_local, const_term):
                        return {
                            'type': 'ineq',
                            'fun': lambda x, ie=idx_e_local, ii=idx_i_local, xi_i=xi_idx_local, c=const_term: -(((1.0 - alpha) * (x[ie] - x[ii]) - x[xi_i]) - c)
                        }

                    const_term = alpha * (qJ_i - qJ_e)
                    ineq_constraints.append(make_ineq(idx_e, idx_i, xi_idx, const_term))

    constraints = eq_constraints + ineq_constraints

    # Bounds
    # when hard_consistency: only p bounds; otherwise p and xi bounds
    bnds = [(0.0, 1.0)] * n_p + ([(0.0, None)] * n_xi if n_xi > 0 else [])

    # Use default options (None) to avoid static type-checker mismatch; maxiter can still be supplied via options if needed
    res = minimize(objective, x0, method='SLSQP', bounds=bnds, constraints=constraints, options=None)

    if not res.success and verbose:
        print("Optimization warning/failed:", res.message)

    x_opt = res.x
    p_opt = x_opt[:n_p]
    xi_opt = x_opt[n_p:] if n_xi > 0 else np.zeros(0)

    rows = []
    season_label = str(panel_season.get('season').iloc[0]) if 'season' in panel_season.columns else None
    for idx, (name, w) in enumerate(rev_map):
        rows.append({'season': season_label, name_col: name, 'week': int(w), 'p_est': float(p_opt[idx])})
    p_df = pd.DataFrame(rows)

    if n_xi > 0:
        xi_rows = []
        for i_w, w in enumerate(weeks):
            xi_rows.append({'season': season_label, 'week': int(w), 'xi': float(xi_opt[i_w])})
        xi_df = pd.DataFrame(xi_rows)
    else:
        # empty xi dataframe when hard_consistency enforced
        xi_df = pd.DataFrame(columns=['season', 'week', 'xi'])

    return p_df, xi_df


def solve_panel(panel_csv: str, output_p_csv: str, output_xi_csv: str,
                name_col: str = 'celebrity_name', score_col: str = 'total_judge_score',
                week_col: str = 'week', active_col: Optional[str] = None, elim_col: Optional[str] = None,
                alpha: float = 0.5, lambda_reg: float = 1000.0, entropy_reg: float = 0.0, popularity_reg: float = 0.0, verbose: bool = False, hard_consistency: bool = False):
    panel = pd.read_csv(panel_csv)

    # Validate minimum schema presence
    for req in (name_col, score_col, week_col):
        if req not in panel.columns:
            raise ValueError(f"Panel missing required column '{req}'. Provide a cleaned weekly panel produced by the triage step.")

    if 'season' not in panel.columns:
        panel['season'] = panel.get('season', 1)

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    all_p = []
    all_xi = []
    for s in seasons:
        sub = panel[panel['season'].astype(str) == str(s)].copy()
        if sub.empty:
            continue
        p_df, xi_df = solve_season_qp(sub, name_col=name_col, score_col=score_col, week_col=week_col,
                                      active_col=active_col, elim_col=elim_col, alpha=alpha, lambda_reg=lambda_reg,
                                      entropy_reg=entropy_reg, popularity_reg=popularity_reg, verbose=verbose, hard_consistency=hard_consistency)
        p_df['season'] = s
        xi_df['season'] = s
        all_p.append(p_df)
        all_xi.append(xi_df)

    if all_p:
        pd.concat(all_p, ignore_index=True).to_csv(output_p_csv, index=False)
    else:
        pd.DataFrame(columns=['season', name_col, 'week', 'p_est']).to_csv(output_p_csv, index=False)

    if all_xi:
        pd.concat(all_xi, ignore_index=True).to_csv(output_xi_csv, index=False)
    else:
        pd.DataFrame(columns=['season', 'week', 'xi']).to_csv(output_xi_csv, index=False)


def main(argv: List[str]) -> None:
    p = argparse.ArgumentParser(prog='model_main')
    p.add_argument('--panel', required=True, help='Path to weekly panel CSV (canonical cleaned panel)')
    p.add_argument('--out-p', required=True, help='Output CSV path for estimated p_{i,t}')
    p.add_argument('--out-xi', required=True, help='Output CSV path for xi_t (per season-week)')
    p.add_argument('--alpha', type=float, default=0.5, help='Alpha weight for judges (default 0.5)')
    p.add_argument('--lambda_reg', type=float, default=1000.0, help='Lambda regularization for xi (default 1000)')
    p.add_argument('--entropy-reg', type=float, default=0.0, help='Per-week entropy regularization (default 0.0). Larger values encourage higher entropy per week (more uniform p).')
    p.add_argument('--popularity-reg', type=float, default=0.0, help='Popularity coupling regularization (default 0.0). Larger values encourage p to be closer to judges share qJ via squared difference penalty.')
    p.add_argument('--name-col', default='celebrity_name', help='Column name for contestant name in panel')
    p.add_argument('--score-col', default='total_judge_score', help='Column name for judges total score in panel')
    p.add_argument('--week-col', default='week', help='Column name for week index in panel')
    p.add_argument('--active-col', default=None, help='Optional column name indicating active rows (bool-like)')
    p.add_argument('--elim-col', default=None, help='Optional column name indicating elimination rows (bool-like)')
    p.add_argument('--hard-consistency', action='store_true', help='Enforce elimination consistency as a hard constraint (no slack xi allowed). May cause infeasibility if data cannot be explained under the model).')
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args(argv)

    solve_panel(args.panel, args.out_p, args.out_xi,
                name_col=args.name_col, score_col=args.score_col, week_col=args.week_col,
                active_col=args.active_col, elim_col=args.elim_col,
                alpha=args.alpha, lambda_reg=args.lambda_reg, entropy_reg=args.entropy_reg, popularity_reg=args.popularity_reg, verbose=args.verbose, hard_consistency=args.hard_consistency)


if __name__ == '__main__':
    import sys

    main(sys.argv[1:])
