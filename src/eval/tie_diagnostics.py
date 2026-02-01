"""
Tie diagnostics for replay mismatches.

Scans `src/eval/replay_*_season*.csv`, compares to the canonical panel and for any
mismatching week writes a detailed row describing the active set, S/Rsum values,
detected exact ties and the resulting top-m under current and alternative tie rules.

Usage:
  python3 src/eval/tie_diagnostics.py

Outputs:
  src/eval/tie_diagnostics.csv
"""
from __future__ import annotations
import os
import glob
import math
from typing import Dict, List, Set, Tuple
import pandas as pd

HERE = os.path.dirname(__file__)
PANEL = os.path.join(HERE, '..', 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
if not os.path.exists(PANEL):
    PANEL = os.path.join('output', 'data_cleaned', 'intermediate_weekly_panel.csv')


def build_week_participants(panel_s: pd.DataFrame) -> Dict[int, List[str]]:
    df = panel_s.copy()
    if 'week' in df.columns:
        df['week'] = pd.to_numeric(df['week'], errors='coerce')
    weeks = sorted(df['week'].dropna().unique()) if 'week' in df.columns and df['week'].notna().any() else []
    if (len(weeks) <= 1) and ('exit_week' in df.columns):
        df['exit_week'] = pd.to_numeric(df['exit_week'], errors='coerce')
        max_w = int(df['exit_week'].max()) if not df['exit_week'].isna().all() else 1
        A_t = {}
        for w in range(1, max_w + 1):
            names = df.loc[df['exit_week'].fillna(max_w) >= w, 'celebrity_name'].dropna().astype(str).tolist()
            A_t[int(w)] = sorted(list(dict.fromkeys(names)))
        return A_t
    A_t = {}
    for w in weeks:
        names = panel_s.loc[panel_s['week'] == w, 'celebrity_name'].dropna().astype(str).tolist()
        A_t[int(w)] = sorted(list(dict.fromkeys(names)))
    return A_t


def infer_elim_counts(A_t: Dict[int, List[str]]) -> Dict[int, int]:
    weeks = sorted(A_t.keys())
    m = {}
    for i, w in enumerate(weeks):
        if i + 1 < len(weeks):
            next_w = weeks[i + 1]
            dropped = set(A_t[w]) - set(A_t[next_w])
            m[w] = max(0, len(dropped))
        else:
            m[w] = 0
    return m


def compute_qJ_for_week(panel_s: pd.DataFrame, week: int, active: List[str]) -> Dict[str, float]:
    sub = panel_s[panel_s.get('week') == week]
    sub = sub[sub['celebrity_name'].astype(str).isin(active)]
    if sub.empty:
        return {name: 1.0 / max(1, len(active)) for name in active}
    totals = pd.to_numeric(sub['total_judge_score'], errors='coerce').astype(float)
    denom = totals.sum()
    if denom == 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    name_to_score = {str(r['celebrity_name']): float(r['total_judge_score']) for _, r in sub.iterrows()}
    q = {name: name_to_score.get(str(name), 0.0) / denom for name in active}
    s = sum(q.values())
    if s <= 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for k in q:
        q[k] /= s
    return q


def get_p_for_week(pest_s: pd.DataFrame, week: int, active: List[str]) -> Dict[str, float]:
    sub = pest_s[pest_s.get('week') == week]
    sub = sub[sub['celebrity_name'].astype(str).isin(active)]
    p_map = {name: 0.0 for name in active}
    if sub.empty:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for _, r in sub.iterrows():
        p_map[str(r['celebrity_name'])] = float(r['p_est'])
    s = sum(p_map.values())
    if s <= 0:
        return {name: 1.0 / max(1, len(active)) for name in active}
    for k in p_map:
        p_map[k] /= s
    return p_map


def nearly_equal(a: float, b: float, tol: float = 1e-9) -> bool:
    if math.isfinite(a) and math.isfinite(b):
        return abs(a - b) <= tol
    return a == b


def format_row(r: dict) -> str:
    return f"{r['celebrity_name']}|S={r.get('S', '')}|J={r.get('total_judge_score', '')}|p={r.get('p_est', '')}|Rsum={r.get('Rsum', '')}"


def main():
    if not os.path.exists(PANEL):
        print('Panel not found; aborting')
        return
    panel = pd.read_csv(PANEL)

    replay_files = glob.glob(os.path.join(HERE, 'replay_*_season*.csv'))
    if not replay_files:
        print('No replay files found in src/eval/. Nothing to do.')
        return

    # pick a default p_est used by eval/replay (fall back to sim defaults)
    candidate_pests = [
        os.path.join('src', 'sim', 'fan_shares_popularity_0_1.csv'),
        os.path.join('src', 'sim', 'fan_shares_entropy_1.0.csv'),
        os.path.join('src', 'sim', 'fan_shares_entropy.csv'),
        os.path.join('src', 'sim', 'fan_shares_refined.csv'),
        os.path.join('src', 'sim', 'test_fan_p.csv'),
        os.path.join('src', 'sim', 'fan_shares.csv'),
    ]
    pest_path = None
    for c in candidate_pests:
        if os.path.exists(c):
            pest_path = c
            break
    if pest_path is None:
        raise SystemExit('No p_est file found; generate one with src/sim/model_main.py')
    pest = pd.read_csv(pest_path)

    rows = []
    # map of actual elimination sets
    for fp in replay_files:
        fname = os.path.basename(fp)
        parts = fname.split('_')
        if len(parts) < 3:
            continue
        method = parts[1]
        season_part = parts[2]
        if not season_part.startswith('season'):
            continue
        season = season_part.replace('season', '').replace('.csv', '')

        panel_s = panel[panel['season'].astype(str) == str(season)].copy()
        if panel_s.empty:
            continue
        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())

        # actual elim sets
        actual_elim_by_week: Dict[int, Set[str]] = {}
        if 'week' in panel_s.columns and 'true_elim_flag' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            for w in weeks:
                actual_elim_by_week[w] = set()

        # read predicted replay
        try:
            rep = pd.read_csv(fp)
        except Exception as e:
            print('Failed to read', fp, e)
            continue

        # build predicted eliminations per week from replay
        pred_by_week: Dict[int, List[str]] = {}
        for _, r in rep.iterrows():
            try:
                w = int(r['week'])
            except Exception:
                continue
            pred_field = r.get('elim_pred', '')
            preds = [p.strip() for p in str(pred_field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]
            pred_by_week[w] = preds

        # for each week with an elimination count > 0, reconstruct the DataFrame and detect ties
        # prefer explicit elimination flags from the panel if available (true_elim_flag), otherwise infer by set differences
        if any(len(s) > 0 for s in actual_elim_by_week.values()):
            m_map = {int(w): len(actual_elim_by_week.get(w, set())) for w in weeks}
        else:
            m_map = infer_elim_counts(A_t)
        for w in weeks:
            m = m_map.get(w, 0)
            if m <= 0:
                continue
            active = list(A_t[w])
            qJ = compute_qJ_for_week(panel_s, w, active)
            pmap = get_p_for_week(pest, w, active)
            rows_df = []
            for name in active:
                total_judge = float(panel_s[(panel_s.get('week') == w) & (panel_s['celebrity_name'].astype(str) == name)]['total_judge_score'].astype(float).sum()) if 'total_judge_score' in panel_s.columns else 0.0
                rows_df.append({'celebrity_name': name, 'qJ': qJ.get(name, 0.0), 'p_est': pmap.get(name, 0.0), 'total_judge_score': total_judge})
            df = pd.DataFrame(rows_df)
            if method == 'percent':
                df['S'] = df['qJ'] * 0.5 + df['p_est'] * 0.5  # alpha is not known here; use 0.5 as reference for diagnostics
                df_curr = df.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, True, True, True]).copy()
                top_curr = df_curr.head(m)['celebrity_name'].tolist()
                # detect exact ties on S among boundary
                df['S_round'] = df['S'].round(12)
                tied_groups = []
                for val, grp in df.groupby('S_round'):
                    if grp.shape[0] > 1:
                        tied_groups.append({'S': float(val), 'members': ';'.join(sorted(grp['celebrity_name'].tolist()))})
                ties_detected = len(tied_groups) > 0
                # alt1: prefer higher judge score (descending) when breaking ties
                df_alt1 = df.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, False, True, True])
                top_alt1 = df_alt1.head(m)['celebrity_name'].tolist()
                # alt2: prefer lower p_est first
                df_alt2 = df.sort_values(by=['S', 'p_est', 'total_judge_score', 'celebrity_name'], ascending=[True, True, True, True])
                top_alt2 = df_alt2.head(m)['celebrity_name'].tolist()
            else:
                # rank rule diagnostics
                df['rank_J'] = df['total_judge_score'].rank(method='min', ascending=False)
                df['rank_V'] = df['p_est'].rank(method='min', ascending=False)
                df['Rsum'] = df['rank_J'] + df['rank_V']
                df_curr = df.sort_values(by=['Rsum', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[False, True, True, True]).copy()
                top_curr = df_curr.head(m)['celebrity_name'].tolist()
                # detect Rsum ties
                df['R_round'] = df['Rsum']  # integers typically; keep raw
                tied_groups = []
                for val, grp in df.groupby('R_round'):
                    if grp.shape[0] > 1:
                        tied_groups.append({'Rsum': float(val), 'members': ';'.join(sorted(grp['celebrity_name'].tolist()))})
                ties_detected = len(tied_groups) > 0
                # alt1: prefer higher judge score (descending) as a stronger tie-break
                df_alt1 = df.sort_values(by=['Rsum', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[False, False, True, True])
                top_alt1 = df_alt1.head(m)['celebrity_name'].tolist()
                # alt2: prefer lower p_est first
                df_alt2 = df.sort_values(by=['Rsum', 'p_est', 'total_judge_score', 'celebrity_name'], ascending=[False, True, True, True])
                top_alt2 = df_alt2.head(m)['celebrity_name'].tolist()

            actual_elim = sorted(list(actual_elim_by_week.get(w, set())))
            pred_elim = pred_by_week.get(w, [])

            rows.append({
                'season': season,
                'method': method,
                'week': w,
                'm': m,
                'active_count': len(active),
                'actual_elim': ';'.join(actual_elim),
                'pred_elim': ';'.join(pred_elim),
                'top_curr': ';'.join(top_curr),
                'top_alt1': ';'.join(top_alt1),
                'top_alt2': ';'.join(top_alt2),
                'ties_detected': ties_detected,
                'tie_groups': ';'.join([f"{g.get('S', g.get('Rsum'))}:{g['members']}" for g in tied_groups]),
            })

    out = os.path.join(HERE, 'tie_diagnostics.csv')
    pd.DataFrame(rows).to_csv(out, index=False)
    print('Wrote', out)


if __name__ == '__main__':
    main()
