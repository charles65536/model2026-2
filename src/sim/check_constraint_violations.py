"""
Check elimination-consistency inequality residuals using the panel and a p_est CSV.

This script:
- Locates a candidate `p_est` file under `src/sim/` (first CSV containing a `p_est` column).
- Builds participant sets A_t and judges' share qJ from the canonical panel.
- Uses `true_elim_flag` (or other elim columns if present) to form elimination sets E_t.
- For each elimination pair (e in E_t, i not in E_t) computes the LHS of the inequality
    LHS = (1-alpha)*(p_e - p_i) - alpha*(q_i - q_e)
  (this is the quantity that must be <= 0 for consistency without slack xi).
- Reports per-season counts, violation counts, max violation, and writes a CSV of violating rows.

Usage:
  python3 src/sim/check_constraint_violations.py

"""
from __future__ import annotations
import glob
import os
from pathlib import Path
import pandas as pd
import numpy as np

PANEL = Path('output/data_cleaned/intermediate_weekly_panel.csv')
PEST_GLOB = list(Path('src/sim').glob('*.csv'))
ALPHA = 0.5

# helper: find a p_est csv in src/sim that has a 'p_est' column
def find_pest_candidate():
    for p in PEST_GLOB:
        try:
            df = pd.read_csv(p, nrows=2)
            if 'p_est' in df.columns and 'season' in df.columns and 'week' in df.columns and 'celebrity_name' in df.columns:
                return p
        except Exception:
            continue
    return None


def build_A_t_solver_like(panel_s: pd.DataFrame) -> dict:
    df = panel_s.copy()
    # solver default: rows with non-null score and non-zero treated as active
    name_col = 'celebrity_name'
    score_col = 'total_judge_score'
    week_col = 'week'
    df[week_col] = pd.to_numeric(df[week_col], errors='coerce')
    df['__active_flag__'] = df[score_col].notna() & (pd.to_numeric(df[score_col], errors='coerce').astype(float).fillna(0) != 0)
    weeks = sorted(df[week_col].dropna().unique())
    A_t = {}
    for w in weeks:
        names = df.loc[(df[week_col] == w) & (df['__active_flag__']), name_col].astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t


def compute_qJ(panel_s: pd.DataFrame, A_t: dict) -> dict:
    qJ = {}
    for w, names in A_t.items():
        sub = panel_s.loc[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str).isin(names))]
        if sub.shape[0] == 0:
            for n in names:
                qJ[(n, w)] = 1.0 / max(1, len(names))
            continue
        totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
        denom = totals.sum()
        if denom == 0:
            for n in names:
                qJ[(n, w)] = 1.0 / max(1, len(names))
        else:
            name_to_score = {str(r['celebrity_name']): float(r['total_judge_score']) for _, r in sub.iterrows()}
            for n in names:
                qJ[(n, w)] = name_to_score.get(n, 0.0) / denom
    return qJ


def main():
    if not PANEL.exists():
        print(f'Panel not found at {PANEL}. Run the triage script first.')
        raise SystemExit(2)

    pest_path = find_pest_candidate()
    if pest_path is None:
        print('No candidate p_est CSV found under src/sim/. Please run model_main to generate p_est or place a p_est CSV in src/sim/.')
        raise SystemExit(3)

    print('Using p_est file:', pest_path)

    panel = pd.read_csv(PANEL)
    pest = pd.read_csv(pest_path)
    # coerce types
    panel['week'] = pd.to_numeric(panel['week'], errors='coerce')

    # choose elim column precedence
    elim_cols = [c for c in ['true_elim_flag', 'is_elim_exit_week', 'is_elim'] if c in panel.columns]
    elim_col = elim_cols[0] if elim_cols else None
    if elim_col:
        print('Using elimination column:', elim_col)
    else:
        print('No explicit elim column found; constraints cannot be evaluated where true eliminations are unknown. The script will skip such weeks.')

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: int(x))

    total_checks = 0
    total_violations = 0
    per_season = []
    violation_rows = []

    for s in seasons:
        panel_s = panel[panel['season'].astype(int) == int(s)].copy()
        if panel_s.empty:
            continue
        A_t = build_A_t_solver_like(panel_s)
        qJ = compute_qJ(panel_s, A_t)

        checks = 0
        violations = 0
        max_violation = -np.inf

        for w in sorted(A_t.keys()):
            names = A_t[w]
            if not names:
                continue

            # build p_for_week from pest for this season/week; fallback to uniform then renormalize
            p_for_week = {n: None for n in names}
            pest_sub = pest[(pest['season'].astype(str) == str(s)) & (pest['week'] == w)]
            for _, r in pest_sub.iterrows():
                p_for_week[str(r['celebrity_name'])] = float(r['p_est'])
            # fill missing
            if any(v is None for v in p_for_week.values()):
                avail = [v for v in p_for_week.values() if v is not None]
                if len(avail) == 0:
                    # uniform
                    for n in p_for_week:
                        p_for_week[n] = 1.0 / max(1, len(names))
                else:
                    # set missing to 0 and renormalize
                    for n in p_for_week:
                        if p_for_week[n] is None:
                            p_for_week[n] = 0.0
                    s_total = sum(p_for_week.values())
                    if s_total <= 0:
                        for n in p_for_week:
                            p_for_week[n] = 1.0 / max(1, len(names))
                    else:
                        for n in p_for_week:
                            p_for_week[n] = p_for_week[n] / s_total

            # build E_t
            if elim_col:
                E = set(panel_s.loc[(panel_s['week'] == w) & (panel_s[elim_col].astype(bool)), 'celebrity_name'].astype(str).tolist())
            else:
                E = set()

            others = [n for n in names if n not in E]
            if len(E) == 0 or len(others) == 0:
                continue

            for e in sorted(E):
                for i in sorted(others):
                    p_e = p_for_week.get(e, 0.0)
                    p_i = p_for_week.get(i, 0.0)
                    q_e = qJ.get((e, w), 0.0)
                    q_i = qJ.get((i, w), 0.0)
                    lhs = (1.0 - ALPHA) * (p_e - p_i) - ALPHA * (q_i - q_e)
                    checks += 1
                    total_checks += 1
                    if lhs > 1e-12:
                        violations += 1
                        total_violations += 1
                        max_violation = max(max_violation, lhs)
                        violation_rows.append({
                            'season': int(s), 'week': int(w), 'elim': e, 'non_elim': i,
                            'p_e': p_e, 'p_i': p_i, 'q_e': q_e, 'q_i': q_i, 'lhs': float(lhs)
                        })
        per_season.append({'season': int(s), 'checks': checks, 'violations': violations, 'max_violation': (max_violation if max_violation != -np.inf else 0.0)})

    # summary
    per_season_df = pd.DataFrame(per_season)
    print('\nPer-season violation summary:')
    if per_season_df.empty:
        print('No seasons processed (panel may be missing weeks or elim info).')
    else:
        print(per_season_df.to_string(index=False))

    print(f"\nTotal checks: {total_checks}, total violations: {total_violations}, violation_rate: {total_violations / total_checks if total_checks else 0.0}")

    out_dir = Path('src/sim')
    out_dir.mkdir(parents=True, exist_ok=True)
    if violation_rows:
        vdf = pd.DataFrame(violation_rows)
        out_path = out_dir / 'constraint_violations_detail.csv'
        vdf.to_csv(out_path, index=False)
        print('Wrote detailed violations to', out_path)
    else:
        print('No constraint violations found (given available p_est and elim columns).')

    # write per-season summary to file
    if not per_season_df.empty:
        per_season_df.to_csv(out_dir / 'constraint_violations_summary.csv', index=False)
        print('Wrote per-season summary to', out_dir / 'constraint_violations_summary.csv')

if __name__ == '__main__':
    main()
