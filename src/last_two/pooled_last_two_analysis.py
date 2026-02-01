"""
Pooled statistical analysis comparing last-two behavior between two season groups.

Default compares seasons 2-26 (early) vs 29+ (late).

Usage:
  python3 src/last_two/pooled_last_two_analysis.py

Outputs:
  - src/last_two/pooled_last_two_results.txt  (human-readable summary)
  - src/last_two/pooled_last_two_data.csv     (per-week rows used)

Tests performed:
  - Two-proportion z-test for fraction saved_higher
  - Two-sample t-test and Mann-Whitney U for delta = saved_score - elim_score

Tie handling modes:
  - strict: skip weeks where bottom-two ambiguity (ties) cannot be resolved
  - deterministic: break ties by `judge_percent` then `judge_rank` then name to select bottom-two

"""
from __future__ import annotations
import os
import math
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import argparse
import scipy.stats as stats

HERE = os.path.dirname(__file__)
PANEL = os.path.join(HERE, '..', 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
OUT_TXT = os.path.join(HERE, 'pooled_last_two_results.txt')
OUT_CSV = os.path.join(HERE, 'pooled_last_two_data.csv')


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


def select_bottom_two(scores_df: pd.DataFrame, tie_mode: str = 'strict') -> Tuple[List[str], List[float], str]:
    """
    Given a dataframe with columns ['celebrity_name', 'score', 'rank'], return bottom_two_names, bottom_scores, note.
    tie_mode: 'strict' or 'deterministic'
    """
    df = scores_df.copy()
    df = df.dropna(subset=['score'])
    if df.shape[0] < 2:
        return [], [], 'insufficient_scores'
    df_sorted = df.sort_values(by=['score', 'rank', 'celebrity_name'], ascending=[True, True, True]).reset_index(drop=True)
    # check tie beyond two
    if tie_mode == 'strict':
        if df_sorted.shape[0] >= 3 and df_sorted.loc[1, 'score'] == df_sorted.loc[2, 'score']:
            return [], [], 'bottom_tie_more_than_two'
        bottom = df_sorted.head(2)
        return bottom['celebrity_name'].tolist(), bottom['score'].tolist(), ''
    else:
        # deterministic: pick first two after sorting
        bottom = df_sorted.head(2)
        return bottom['celebrity_name'].tolist(), bottom['score'].tolist(), ''


def gather_data(panel: pd.DataFrame, early_range: Tuple[int, int] = (2, 26), late_min: int = 29, tie_mode: str = 'deterministic'):
    rows = []
    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    for s in seasons:
        try:
            s_num = int(float(s))
        except Exception:
            continue
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        if panel_s.empty:
            continue
        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())

        # actual elim per week
        actual_elim_by_week = {}
        if 'week' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            for w in weeks:
                actual_elim_by_week[w] = set()

        # choose score column: prefer judge_percent then total_judge_score then judge_rank
        score_col = None
        for c in ('judge_percent', 'total_judge_score', 'judge_rank'):
            if c in panel_s.columns:
                score_col = c
                break
        if score_col is None:
            raise SystemExit('No judge score column found')

        for w in weeks:
            active = A_t.get(w, [])
            if len(active) < 2:
                continue
            elim = actual_elim_by_week.get(w, set())
            if len(elim) != 1:
                continue
            elim_name = list(elim)[0]

            scores = panel_s.loc[panel_s['celebrity_name'].isin(active), ['celebrity_name', score_col]].copy()
            scores = scores.rename(columns={score_col: 'score'})
            # for judge_rank normalize by active count so higher rank -> worse; we want direction consistent (lower score = worse)
            if score_col == 'judge_rank':
                scores['score'] = pd.to_numeric(scores['score'], errors='coerce') / max(1, len(active))
            else:
                scores['score'] = pd.to_numeric(scores['score'], errors='coerce')
            # attach rank for tie-break
            scores['rank'] = scores['score'].rank(method='dense')

            bottom_names, bottom_scores, note = select_bottom_two(scores[['celebrity_name', 'score', 'rank']], tie_mode=tie_mode)
            if note:
                continue
            if elim_name not in bottom_names:
                # eliminated not among bottom two -> skip
                continue
            saved = [n for n in bottom_names if n != elim_name]
            if not saved:
                continue
            saved_name = saved[0]
            elim_score = float(scores.loc[scores['celebrity_name'] == elim_name, 'score'].iloc[0])
            saved_score = float(scores.loc[scores['celebrity_name'] == saved_name, 'score'].iloc[0])
            # saved_is_higher: True if saved_score > elim_score (note direction: higher means better for judge_percent/total_judge_score)
            saved_is_higher = saved_score > elim_score

            group = None
            if early_range[0] <= s_num <= early_range[1]:
                group = 'early'
            elif s_num >= late_min:
                group = 'late'
            else:
                group = 'other'

            rows.append({'season': s_num, 'week': w, 'group': group, 'elim': elim_name, 'elim_score': elim_score, 'saved': saved_name, 'saved_score': saved_score, 'saved_is_higher': int(saved_is_higher), 'delta': saved_score - elim_score})

    df = pd.DataFrame(rows)
    return df


def two_proportion_ztest(k1, n1, k2, n2):
    p1 = k1 / n1 if n1 > 0 else 0
    p2 = k2 / n2 if n2 > 0 else 0
    p_pool = (k1 + k2) / (n1 + n2) if (n1 + n2) > 0 else 0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) if n1 > 0 and n2 > 0 else float('nan')
    z = (p1 - p2) / se if se and se > 0 else float('nan')
    pval = 2 * (1 - stats.norm.cdf(abs(z))) if not math.isnan(z) else float('nan')
    return {'p1': p1, 'p2': p2, 'z': z, 'pval': pval}


def run_analysis(df: pd.DataFrame, tie_mode: str = 'deterministic'):
    out_lines = []
    out_lines.append(f'Tie mode: {tie_mode}')
    # restrict to early and late groups
    df_e = df[df['group'] == 'early']
    df_l = df[df['group'] == 'late']
    n_e = len(df_e)
    n_l = len(df_l)
    k_e = int(df_e['saved_is_higher'].sum())
    k_l = int(df_l['saved_is_higher'].sum())
    out_lines.append(f'early: n={n_e}, saves_higher={k_e}, frac={k_e/n_e if n_e else None}')
    out_lines.append(f'late:  n={n_l}, saves_higher={k_l}, frac={k_l/n_l if n_l else None}')

    # two-proportion z-test
    prop_res = two_proportion_ztest(k_e, n_e, k_l, n_l)
    out_lines.append('\nTwo-proportion z-test (early vs late):')
    out_lines.append(str(prop_res))

    # delta tests
    delta_e = df_e['delta'].dropna().values
    delta_l = df_l['delta'].dropna().values
    out_lines.append('\nDelta (saved_score - elim_score) summary:')
    out_lines.append(f'early mean={np.mean(delta_e) if len(delta_e) else None}, n={len(delta_e)}')
    out_lines.append(f'late  mean={np.mean(delta_l) if len(delta_l) else None}, n={len(delta_l)}')
    if len(delta_e) and len(delta_l):
        t_res = stats.ttest_ind(delta_e, delta_l, equal_var=False)
        try:
            mw_res = stats.mannwhitneyu(delta_e, delta_l, alternative='two-sided')
        except TypeError:
            mw_res = stats.mannwhitneyu(delta_e, delta_l)
        out_lines.append('\nTwo-sample t-test (delta): ' + str(t_res))
        out_lines.append('Mann-Whitney U (delta): ' + str(mw_res))
    else:
        out_lines.append('\nNot enough delta samples for t-test or MW test')

    return '\n'.join(out_lines), prop_res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--early-start', type=int, default=2)
    parser.add_argument('--early-end', type=int, default=26)
    parser.add_argument('--late-min', type=int, default=29)
    parser.add_argument('--tie-mode', choices=['strict', 'deterministic', 'both'], default='both')
    args = parser.parse_args()

    if not os.path.exists(PANEL):
        alt = os.path.join(os.getcwd(), 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
        if os.path.exists(alt):
            panel_path = alt
        else:
            raise SystemExit(f'Panel file not found at {PANEL}')
    else:
        panel_path = PANEL
    panel = pd.read_csv(panel_path)

    modes = ('strict', 'deterministic') if args.tie_mode == 'both' else (args.tie_mode,)
    dfs = {}
    for tie_mode in modes:
        df = gather_data(panel, early_range=(args.early_start, args.early_end), late_min=args.late_min, tie_mode=tie_mode)
        dfs[tie_mode] = df

    # run analyses and write outputs
    with open(OUT_TXT, 'w') as f:
        for tie_mode, df in dfs.items():
            f.write('==== MODE: ' + tie_mode + '\n')
            txt, prop = run_analysis(df, tie_mode=tie_mode)
            f.write(txt + '\n\n')
    # save pooled data for inspection (use deterministic mode by default if present)
    if 'deterministic' in dfs:
        dfs['deterministic'].to_csv(OUT_CSV, index=False)
    else:
        next(iter(dfs.values())).to_csv(OUT_CSV, index=False)
    print('Wrote', OUT_TXT)
    print('Wrote', OUT_CSV)


if __name__ == '__main__':
    main()
