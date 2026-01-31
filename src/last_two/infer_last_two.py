"""
Infer last-two judge saving behavior.

Produces `last_two_summary.csv` and `last_two_details.csv` in this folder.

Run from repo root:
  python3 src/last_two/infer_last_two.py --min-season 28
"""
from __future__ import annotations
import argparse
import os
import pandas as pd
import math
from typing import Dict, List, Set, Tuple

HERE = os.path.dirname(__file__)
PANEL = os.path.join(HERE, '..', 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
OUT_SUM = os.path.join(HERE, 'last_two_summary.csv')
OUT_DET = os.path.join(HERE, 'last_two_details.csv')


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


def wilson_ci(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(phat * (1 - phat) / n + (z * z) / (4 * n * n))) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def infer(panel: pd.DataFrame, min_season: int = 28, max_season: int | None = None):
    rows = []
    detail_rows = []
    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    for s in seasons:
        try:
            s_num = float(s)
        except Exception:
            continue
        if s_num < min_season:
            continue
        if max_season is not None and s_num > max_season:
            continue
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        if panel_s.empty:
            continue
        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())

        # map actual elimination per week
        actual_elim_by_week: Dict[int, Set[str]] = {}
        if 'week' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            for w in weeks:
                actual_elim_by_week[w] = set()

        # choose judge score column
        score_col = None
        for c in ('total_judge_score', 'judge_percent', 'judge_rank'):
            if c in panel_s.columns:
                score_col = c
                break
        if score_col is None:
            raise SystemExit('No judge score column found in panel')

        n_cases = 0
        n_save_higher = 0
        for w in weeks:
            active = A_t.get(w, [])
            if len(active) < 2:
                detail_rows.append({'season': s, 'week': w, 'note': 'too_few_active'})
                continue
            elim = actual_elim_by_week.get(w, set())
            if len(elim) != 1:
                detail_rows.append({'season': s, 'week': w, 'note': 'not_single_elim'})
                continue
            elim_name = list(elim)[0]

            # build scores for active contestants for this week
            scores = panel_s.loc[panel_s['celebrity_name'].isin(active), ['celebrity_name', score_col]].copy()
            # coerce numeric
            scores[score_col] = pd.to_numeric(scores[score_col], errors='coerce')
            # drop NA scores
            scores = scores.dropna(subset=[score_col])
            if scores.shape[0] < 2:
                detail_rows.append({'season': s, 'week': w, 'note': 'insufficient_score_data'})
                continue

            # determine bottom two by judge score (lower score = worse if using total_judge_score or judge_percent)
            # We sort ascending so bottom (worst) are first
            scores_sorted = scores.sort_values(by=score_col, ascending=True)
            # detect ties at the bottom that produce >2 candidates
            bottom = scores_sorted.head(2)
            # if there are ties extending beyond two with identical bottom score, skip
            if scores_sorted.shape[0] >= 3 and scores_sorted.iloc[1][score_col] == scores_sorted.iloc[2][score_col]:
                detail_rows.append({'season': s, 'week': w, 'note': 'bottom_tie_more_than_two'})
                continue

            bottom_names = bottom['celebrity_name'].tolist()
            bottom_scores = bottom[score_col].tolist()

            if elim_name not in bottom_names:
                detail_rows.append({'season': s, 'week': w, 'note': 'elim_not_in_bottom_two', 'elim': elim_name})
                continue

            # identify saved contestant among bottom two
            saved = [n for n in bottom_names if n != elim_name]
            saved_name = saved[0] if saved else None
            # compare scores: saved_is_higher = True if saved_score > elim_score
            elim_score = float(bottom.loc[bottom['celebrity_name'] == elim_name, score_col].iloc[0])
            saved_score = float(bottom.loc[bottom['celebrity_name'] == saved_name, score_col].iloc[0])
            saved_is_higher = saved_score > elim_score

            n_cases += 1
            if saved_is_higher:
                n_save_higher += 1

            detail_rows.append({'season': s, 'week': w, 'bottom_two': ';'.join(bottom_names), 'bottom_scores': ';'.join([str(x) for x in bottom_scores]), 'elim': elim_name, 'elim_score': elim_score, 'saved': saved_name, 'saved_score': saved_score, 'saved_is_higher': saved_is_higher, 'note': ''})

        # compute stats
        if n_cases > 0:
            frac = n_save_higher / n_cases
            try:
                from scipy.stats import binomtest
                pval = binomtest(n_save_higher, n_cases, p=0.5).pvalue
            except Exception:
                pval = None
            ci_low, ci_high = wilson_ci(n_save_higher, n_cases)
        else:
            frac = None
            pval = None
            ci_low, ci_high = (None, None)

        rows.append({'season': s, 'n_cases': n_cases, 'saves_higher_count': n_save_higher, 'saves_higher_frac': frac, 'ci_low': ci_low, 'ci_high': ci_high, 'binom_pvalue': pval})

    # write outputs
    pd.DataFrame(rows).to_csv(OUT_SUM, index=False)
    pd.DataFrame(detail_rows).to_csv(OUT_DET, index=False)
    return OUT_SUM, OUT_DET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-season', type=int, default=28)
    parser.add_argument('--max-season', type=int, default=None)
    args = parser.parse_args()

    if not os.path.exists(PANEL):
        # try repo-root path
        alt = os.path.join(os.getcwd(), 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
        if os.path.exists(alt):
            panel_path = alt
        else:
            raise SystemExit(f'Panel file not found at {PANEL}')
    else:
        panel_path = PANEL

    panel = pd.read_csv(panel_path)
    out_sum, out_det = infer(panel, min_season=args.min_season, max_season=args.max_season)
    print('Wrote', out_sum)
    print('Wrote', out_det)


if __name__ == '__main__':
    main()
