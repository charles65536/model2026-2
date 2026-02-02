"""
Simulate the "Professional Bottom Two" rule and evaluate against canonical replays.

Rule: among the two contestants with the lowest judge scores (J_total), eliminate
the one with the lower combined score S = alpha * qJ + (1-alpha) * p_est.

Outputs:
 - `src/sim/replay_professional_bottom_two_season{S}.csv` per season
 - `src/eval/professional_bottom_two_jaccard.csv` per-season mean Jaccard vs methods
 - `src/eval/professional_bottom_two_contestant_summary.csv` per-contestant (four targets)

Usage:
  PYTHONPATH=. python3 src/eval/professional_bottom_two.py --seasons 2,4,11,27 --alpha 0.5
"""
from __future__ import annotations
import os
import sys
import argparse
import pandas as pd
from typing import List, Dict

from src.sim.replay_simulator import build_week_participants, compute_qJ_for_week, get_p_for_week, infer_elim_counts_from_col

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
SIM_DIR = os.path.join(ROOT, 'src', 'sim')
EVAL_DIR = os.path.join(ROOT, 'src', 'eval')
os.makedirs(EVAL_DIR, exist_ok=True)


def run_professional_bottom_two(season: int, panel_df: pd.DataFrame, pest_df: pd.DataFrame, alpha: float = 0.5, elim_col: str = 'true_elim_flag'):
    panel_s = panel_df[panel_df['season'].astype(int) == int(season)].copy()
    if panel_s.empty:
        return []
    A_t = build_week_participants(panel_s)
    weeks = sorted(A_t.keys())
    # m_map
    if elim_col in panel_s.columns:
        m_map = infer_elim_counts_from_col(panel_s, elim_col)
    else:
        m_map = {}
        for i, w in enumerate(weeks):
            if i + 1 < len(weeks):
                m_map[w] = max(0, len(set(A_t[w]) - set(A_t[weeks[i+1]])))
            else:
                m_map[w] = 0

    history = []
    active_set = list(A_t[weeks[0]]) if weeks else []

    for w in weeks:
        if len(active_set) == 0:
            break
        m = m_map.get(w, 0)
        if m <= 0:
            history.append({'season': season, 'week': w, 'm': 0, 'active_count': len(active_set), 'elim_pred': ''})
            next_idx = weeks.index(w) + 1
            if next_idx < len(weeks):
                next_week = weeks[next_idx]
                active_set = [a for a in active_set if a in A_t.get(next_week, []) or a in active_set]
            continue

        elim_list = []
        for _ in range(m):
            if len(active_set) == 0:
                break
            # choose bottom two by judge total (J_total in panel)
            rows = []
            for name in active_set:
                rows_panel = panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]
                jt = float(rows_panel['J_total'].astype(float).sum()) if not rows_panel.empty and 'J_total' in rows_panel.columns else 0.0
                rows.append({'celebrity_name': name, 'J_total': jt})
            df = pd.DataFrame(rows)
            if df.empty:
                break
            df_sorted = df.sort_values(by=['J_total','celebrity_name'], ascending=[True, True])
            bottom = df_sorted.head(2)
            if bottom.shape[0] == 0:
                break
            if bottom.shape[0] == 1:
                elim_candidate = bottom['celebrity_name'].iloc[0]
            else:
                names = bottom['celebrity_name'].tolist()
                # compute qJ and p for these two
                qJ = compute_qJ_for_week(panel_s, w, active_set)
                pmap = get_p_for_week(pest_df, w, active_set)
                b1, b2 = names[0], names[1]
                S1 = alpha * qJ.get(b1, 0.0) + (1 - alpha) * pmap.get(b1, 0.0)
                S2 = alpha * qJ.get(b2, 0.0) + (1 - alpha) * pmap.get(b2, 0.0)
                if S1 < S2:
                    elim_candidate = b1
                elif S2 < S1:
                    elim_candidate = b2
                else:
                    # tie-break: lower p_est eliminated; then name
                    if pmap.get(b1, 0.0) < pmap.get(b2, 0.0):
                        elim_candidate = b1
                    elif pmap.get(b2, 0.0) < pmap.get(b1, 0.0):
                        elim_candidate = b2
                    else:
                        elim_candidate = sorted([b1, b2])[0]
            elim_list.append(str(elim_candidate))
            active_set = [a for a in active_set if a != elim_candidate]

        history.append({'season': season, 'week': w, 'm': m, 'active_count': len(active_set) + len(elim_list), 'elim_pred': ';'.join(elim_list)})

    return history


def write_history(history: List[Dict], out_path: str, season: int):
    rows = []
    for h in history:
        rows.append({'season': season, 'method': 'professional_bottom_two', 'week': h['week'], 'm': h['m'], 'active_count': h['active_count'], 'elim_pred': h['elim_pred']})
    pd.DataFrame(rows).to_csv(out_path, index=False)


def jaccard_sets(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a and b or a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def compare_with_method(season: int, history, method_name: str):
    # load replay_{method}_season{S}.csv
    f = os.path.join(SIM_DIR, f'replay_{method_name}_season{season}.csv')
    if not os.path.exists(f):
        return None
    ref = pd.read_csv(f)
    # build dict week -> set
    ref_map = {}
    for _, r in ref.iterrows():
        w = int(r['week'])
        s = set([x.strip() for x in str(r.get('elim_pred','')).split(';') if x and x.strip()!=''])
        ref_map[w] = s

    jaccs = []
    for h in history:
        w = int(h['week'])
        pred = set([x.strip() for x in str(h.get('elim_pred','')).split(';') if x and x.strip()!=''])
        ref_set = ref_map.get(w, set())
        jaccs.append(jaccard_sets(pred, ref_set))
    if not jaccs:
        return None
    return float(sum(jaccs) / len(jaccs))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--seasons', default='2,4,11,27')
    p.add_argument('--alpha', type=float, default=0.5)
    args = p.parse_args(argv)

    panel_df = pd.read_csv(PANEL)
    seasons = [int(x) for x in str(args.seasons).split(',') if x.strip()!='']

    jacc_rows = []
    contestant_rows = []
    for s in seasons:
        pest_file = os.path.join(SIM_DIR, f'fan_shares_s{s}_alpha{str(args.alpha).replace(".", "p")}.csv')
        if not os.path.exists(pest_file):
            print('Missing p_est for season', s, 'expected at', pest_file)
            continue
        pest_df = pd.read_csv(pest_file)
        history = run_professional_bottom_two(s, panel_df, pest_df, alpha=args.alpha)
        out_path = os.path.join(SIM_DIR, f'replay_professional_bottom_two_season{s}.csv')
        write_history(history, out_path, s)
        print('Wrote', out_path)

        # compare vs methods
        for method in ['percent','rank','js_sr']:
            j = compare_with_method(s, history, method)
            jacc_rows.append({'season': s, 'method': method, 'jaccard': j})

        # per-contestant summary for target list
        targets = ['Jerry Rice','Billy Ray Cyrus','Bristol Palin','Bobby Bones']
        # compute predicted placement from elimination sequence
        # initial participants
        panel_s = panel_df[panel_df['season'].astype(int) == s].copy()
        A_t = build_week_participants(panel_s) if not panel_s.empty else {}
        weeks = sorted(A_t.keys())
        initial = list(A_t[weeks[0]]) if weeks else []
        N = len(initial)
        # build elimination sequence
        elim_seq = []
        for h in history:
            preds = [p.strip() for p in str(h['elim_pred']).split(';') if p and p.strip()!='']
            elim_seq.extend(preds)
        # survivors
        survivors = [x for x in initial if x not in elim_seq]
        # rank survivors by final-week judge total (descending) if available
        final_week = weeks[-1] if weeks else None
        def judge_total(name):
            if final_week is None:
                return 0.0
            rows = panel_s[(panel_s['week'] == final_week) & (panel_s['celebrity_name'].astype(str) == name)]
            return float(rows['J_total'].astype(float).sum()) if not rows.empty and 'J_total' in rows.columns else 0.0

        survivors_sorted = sorted(survivors, key=judge_total, reverse=True)
        # final ranking: survivors (best first) then reversed elim_seq (best of eliminated last)
        final_ranking = survivors_sorted + list(reversed(elim_seq))
        pred_place = {name: (final_ranking.index(name) + 1) if name in final_ranking else None for name in initial}

        for name in targets:
            pred_week = None
            for h in history:
                preds = [p.strip() for p in str(h['elim_pred']).split(';') if p and p.strip()!='']
                if name in preds:
                    pred_week = h['week']
                    break
            # actual placement (from panel)
            panel_rows = panel_s[panel_s['celebrity_name'] == name]
            actual_placement = None
            if not panel_rows.empty and 'placement' in panel_rows.columns:
                # try to get the placement value (unique per celebrity)
                try:
                    actual_placement = int(panel_rows['placement'].dropna().iloc[0])
                except Exception:
                    actual_placement = None

            contestant_rows.append({'season': s, 'name': name, 'actual_placement': actual_placement, 'pred_placement_professional_bottom_two': pred_place.get(name), 'pred_week_professional_bottom_two': pred_week})

    pd.DataFrame(jacc_rows).to_csv(os.path.join(EVAL_DIR, 'professional_bottom_two_jaccard.csv'), index=False)
    pd.DataFrame(contestant_rows).to_csv(os.path.join(EVAL_DIR, 'professional_bottom_two_contestant_summary.csv'), index=False)
    print('Wrote evaluation summaries to', EVAL_DIR)


if __name__ == '__main__':
    main(sys.argv[1:])
