"""
Simulate Bottom-2 + Judge-Save rule for selected seasons and compare outcomes
for a set of contestants.

Usage (examples run by the agent):
  python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.5

Outputs:
  - `src/eval/replay_bottom_two_season{S}.csv` per season
  - `src/eval/bottom_two_summary.csv` summary across requested seasons
  - printed short report for the four target contestants
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
from typing import List, Dict

# reuse helpers from the replay simulator
from src.sim.replay_simulator import build_week_participants, compute_qJ_for_week, get_p_for_week, infer_elim_counts_from_col
from src.tools.paths import DATA_CLEAN, SIM_DIR, EVAL_DIR, REPLAYS_DIR, ensure_dirs

# canonical paths
PANEL = os.path.join(DATA_CLEAN, 'intermediate_weekly_panel.csv')
ensure_dirs([EVAL_DIR, REPLAYS_DIR])


def run_bottom_two_for_season(season: int, panel_df: pd.DataFrame, pest_df: pd.DataFrame, alpha: float = 0.5, elim_col: str = 'true_elim_flag'):
    panel_s = panel_df[panel_df['season'].astype(int) == int(season)].copy()
    if panel_s.empty:
        return []
    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())
    # m_map
    m_map = None
    if elim_col in panel_s.columns:
        m_map = infer_elim_counts_from_col(panel_s, elim_col)
    else:
        # infer from participants
        m_map = {}
        for i, w in enumerate(weeks):
            if i + 1 < len(weeks):
                m_map[w] = max(0, len(set(A_t[w]) - set(A_t[weeks[i+1]])))
            else:
                m_map[w] = 0

    active_set = list(A_t[weeks[0]]) if weeks else []
    last_p = {}
    imputed = {}
    history = []

    for w in weeks:
        if len(active_set) == 0:
            break
        m = m_map.get(w, 0)
        if m <= 0:
            history.append({'season': season, 'week': w, 'm': 0, 'active_count': len(active_set), 'elim_pred': ''})
            # update active_set to match next week participants if available
            next_idx = weeks.index(w) + 1
            if next_idx < len(weeks):
                next_week = weeks[next_idx]
                active_set = [a for a in active_set if a in A_t.get(next_week, []) or a in active_set]
            continue

        # compute qJ and p for active set
        qJ = compute_qJ_for_week(panel_s, w, active_set)
        pmap = get_p_for_week(pest_df, w, active_set)

        elim_list = []
        # eliminate m contestants sequentially using bottom-2 judge-save logic
        for _ in range(m):
            if len(active_set) == 0:
                break
            # build dataframe
            rows = []
            for name in active_set:
                # try to get judge total from panel_s for the week
                jt = 0.0
                rows_panel = panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]
                if not rows_panel.empty and 'total_judge_score' in rows_panel.columns:
                    jt = float(rows_panel['total_judge_score'].astype(float).sum())
                rows.append({'celebrity_name': name, 'S': alpha * qJ.get(name, 0.0) + (1.0 - alpha) * pmap.get(name, 0.0), 'total_judge_score': jt, 'p_est': pmap.get(name, 0.0)})
            df = pd.DataFrame(rows)
            if df.empty:
                break
            # find bottom two by S (lowest S values)
            df_sorted = df.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, True, True, True])
            bottom = df_sorted.head(2)
            if bottom.shape[0] == 0:
                break
            if bottom.shape[0] == 1:
                elim_candidate = bottom['celebrity_name'].iloc[0]
            else:
                b1 = bottom.iloc[0]
                b2 = bottom.iloc[1]
                # judge save: compare total_judge_score, save the one with higher judge; eliminate the other
                if b1['total_judge_score'] < b2['total_judge_score']:
                    elim_candidate = b1['celebrity_name']
                elif b2['total_judge_score'] < b1['total_judge_score']:
                    elim_candidate = b2['celebrity_name']
                else:
                    # tie on judge: eliminate the one with lower p_est, then name
                    if b1['p_est'] < b2['p_est']:
                        elim_candidate = b1['celebrity_name']
                    elif b2['p_est'] < b1['p_est']:
                        elim_candidate = b2['celebrity_name']
                    else:
                        elim_candidate = sorted([b1['celebrity_name'], b2['celebrity_name']])[0]
            elim_list.append(str(elim_candidate))
            # remove eliminated and continue
            active_set = [a for a in active_set if a != elim_candidate]

        history.append({'season': season, 'week': w, 'm': m, 'active_count': len(active_set) + len(elim_list), 'elim_pred': ';'.join(elim_list)})

        # imputation for survivors missing next week (carry-forward p_est and mean judge)
        next_idx = weeks.index(w) + 1
        if next_idx < len(weeks):
            next_week = weeks[next_idx]
            next_participants = set(A_t.get(next_week, []))
            missing_survivors = [a for a in active_set if a not in next_participants]
            for name in missing_survivors:
                mask = (panel_s['celebrity_name'].astype(str) == name) & (panel_s['week'] <= w)
                hist = panel_s.loc[mask, 'total_judge_score'].astype(float) if 'total_judge_score' in panel_s.columns else pd.Series([], dtype=float)
                j_mean = float(hist.mean()) if len(hist.dropna()) > 0 else 0.0
                p_cf = float(pmap.get(name, 1.0 / max(1, len(active_set))))
                imputed[(name, next_week)] = {'total_judge_score': j_mean, 'p_est': p_cf}
    return history


def write_history(history: List[Dict], out_path: str, season: int):
    rows = []
    for h in history:
        rows.append({'season': season, 'method': 'bottom_two', 'week': h['week'], 'm': h['m'], 'active_count': h['active_count'], 'elim_pred': h['elim_pred']})
    pd.DataFrame(rows).to_csv(out_path, index=False)


def compare_with_actual(panel_df: pd.DataFrame, history: List[Dict], season: int):
    panel_s = panel_df[panel_df['season'].astype(int) == int(season)].copy()
    # build actual elim_by_week
    actual = {}
    if 'week' in panel_s.columns and 'true_elim_flag' in panel_s.columns:
        for w in sorted(panel_s['week'].dropna().unique()):
            names = panel_s.loc[(panel_s['week'] == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
            actual[int(w)] = set(names)
    else:
        # fallback empty
        actual = {}

    # compare
    diffs = []
    for h in history:
        w = h['week']
        pred = set([p for p in str(h['elim_pred']).split(';') if p and p.strip()!=''])
        act = actual.get(w, set())
        diffs.append({'season': season, 'week': w, 'predicted_elim': ';'.join(sorted(pred)), 'actual_elim': ';'.join(sorted(act)), 'changed': pred != act})
    return diffs


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--seasons', default='2,4,11,27')
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--panel', default=PANEL)
    p.add_argument('--pest_dir', default=SIM_DIR)
    p.add_argument('--out_dir', default=EVAL_DIR)
    args = p.parse_args(argv)

    panel_df = pd.read_csv(args.panel)
    seasons = [int(x) for x in str(args.seasons).split(',') if x.strip()!='']

    all_diffs = []
    per_contestant = []
    for s in seasons:
        pest_file = os.path.join(args.pest_dir, f'fan_shares_s{s}_alpha{str(args.alpha).replace('.', 'p')}.csv')
        if not os.path.exists(pest_file):
            print('Missing p_est for season', s, 'expected at', pest_file)
            continue
        pest_df = pd.read_csv(pest_file)
        history = run_bottom_two_for_season(s, panel_df, pest_df, alpha=args.alpha)
        out_path = os.path.join(REPLAYS_DIR, f'replay_bottom_two_season{s}.csv')
        write_history(history, out_path, s)
        print('Wrote', out_path)
        diffs = compare_with_actual(panel_df, history, s)
        all_diffs.extend(diffs)
        # check our four target contestants if present and compute predicted placement
        targets = ['Jerry Rice','Billy Ray Cyrus','Bristol Palin','Bobby Bones']
        panel_s = panel_df[panel_df['season'].astype(int) == s].copy()
        A_t = build_week_participants(panel_s) if not panel_s.empty else {}
        weeks = sorted(A_t.keys())
        initial = list(A_t[weeks[0]]) if weeks else []
        # build elimination sequence
        elim_seq = []
        for h in history:
            preds = [p.strip() for p in str(h['elim_pred']).split(';') if p and p.strip()!='']
            elim_seq.extend(preds)
        survivors = [x for x in initial if x not in elim_seq]
        # rank survivors by final-week judge total
        final_week = weeks[-1] if weeks else None
        def judge_total(name):
            if final_week is None:
                return 0.0
            rows = panel_s[(panel_s['week'] == final_week) & (panel_s['celebrity_name'].astype(str) == name)]
            return float(rows['total_judge_score'].astype(float).sum()) if not rows.empty and 'total_judge_score' in rows.columns else 0.0

        survivors_sorted = sorted(survivors, key=judge_total, reverse=True)
        final_ranking = survivors_sorted + list(reversed(elim_seq))
        pred_place = {name: (final_ranking.index(name) + 1) if name in final_ranking else None for name in initial}

        for name in targets:
            if name in panel_s['celebrity_name'].values:
                pred_week = None
                for h in history:
                    preds = [p for p in str(h['elim_pred']).split(';') if p and p.strip()!='']
                    if name in preds:
                        pred_week = h['week']
                        break
                # actual placement
                actual_rows = panel_s[panel_s['celebrity_name'] == name]
                actual_placement = None
                if not actual_rows.empty and 'placement' in actual_rows.columns:
                    try:
                        actual_placement = int(actual_rows['placement'].dropna().iloc[0])
                    except Exception:
                        actual_placement = None
                per_contestant.append({'season': s, 'name': name, 'actual_placement': actual_placement, 'pred_placement_bottom_two': pred_place.get(name), 'pred_week_bottom_two': pred_week})

    # write diffs and per-contestant summary to EVAL_DIR
    pd.DataFrame(all_diffs).to_csv(os.path.join(EVAL_DIR, 'bottom_two_diffs.csv'), index=False)
    pd.DataFrame(per_contestant).to_csv(os.path.join(EVAL_DIR, 'bottom_two_contestant_summary.csv'), index=False)
    print('Wrote summaries to', EVAL_DIR)
    print('\nPer-contestant summary:')
    print(pd.DataFrame(per_contestant).to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1:])
