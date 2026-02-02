from src.tools.paths import REPLAYS_DIR
"""
Compare three replay strategies per-week:
 - `percent` (S = alpha*qJ + (1-alpha)*p_est)
 - `rank` (Rsum = rank_J + rank_V)
 - `percent_last_two` (same as percent but when active size==2, eliminate the contestant with lower judge score)

Generates `src/sim/replay_percent_last_two_season{S}.csv` and writes pairwise Jaccard
details + season summaries to `src/eval/`.
"""
from __future__ import annotations
import os
import pandas as pd
from typing import Dict, List, Set
import argparse


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


def infer_elim_counts_from_col(panel_s: pd.DataFrame, elim_col: str) -> Dict[int, int]:
    panel_s = panel_s.copy()
    panel_s['week'] = pd.to_numeric(panel_s['week'], errors='coerce')
    weeks = sorted(panel_s['week'].dropna().unique())
    m = {}
    if elim_col not in panel_s.columns:
        return {int(w): 0 for w in weeks}
    for w in weeks:
        mask = (panel_s['week'] == w) & (panel_s[elim_col].astype(bool))
        m[int(w)] = int(mask.sum())
    return m


def compute_qJ_for_week(panel_s: pd.DataFrame, week: int, active: List[str]) -> Dict[str, float]:
    sub = panel_s[panel_s['week'] == week]
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
    sub = pest_s[pest_s['week'] == week]
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


def tie_break_sort_percent_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, True, True, True])


def tie_break_sort_rank_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by=['Rsum', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[False, True, True, True])


def simulate_percent_last_two(panel_s: pd.DataFrame, pest_s: pd.DataFrame, alpha: float = 0.5, m_map: Dict[int,int] = None):
    A_t = build_week_participants(panel_s)
    if not A_t:
        return []
    weeks = sorted(A_t.keys())
    if m_map is None:
        m_map = {w: 0 for w in weeks}

    active_set = list(A_t[weeks[0]])
    history = []
    for w in weeks:
        if len(active_set) == 0:
            break
        m = m_map.get(w, 0)
        if m <= 0:
            history.append({'week': w, 'm': 0, 'elim_pred': [], 'active_count': len(active_set)})
            next_idx = weeks.index(w) + 1
            if next_idx < len(weeks):
                next_week = weeks[next_idx]
                active_set = [a for a in active_set if a in A_t.get(next_week, []) or a in active_set]
            continue

        elim = []
        for _ in range(m):
            if len(active_set) == 0:
                break
            if len(active_set) == 2:
                # Decide by smoothed-percent S = alpha * qJ + (1-alpha) * p_est (use percentage not raw judge rank)
                qJ = compute_qJ_for_week(panel_s, w, active_set)
                pmap = get_p_for_week(pest_s, w, active_set)
                rows2 = []
                for name in active_set:
                    total_j = float(panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]['total_judge_score'].astype(float).sum())
                    rows2.append({'celebrity_name': name, 'qJ': qJ.get(name, 0.0), 'p_est': pmap.get(name, 0.0), 'total_judge_score': total_j})
                df2 = pd.DataFrame(rows2)
                df2['S'] = alpha * df2['qJ'] + (1.0 - alpha) * df2['p_est']
                # eliminate the contestant with the lowest S (worst under smoothed-percent)
                elim_name = df2.sort_values(by=['S', 'total_judge_score', 'p_est', 'celebrity_name'], ascending=[True, True, True, True])['celebrity_name'].iloc[0]
                elim.append(elim_name)
                active_set = [a for a in active_set if a != elim_name]
                continue

            qJ = compute_qJ_for_week(panel_s, w, active_set)
            pmap = get_p_for_week(pest_s, w, active_set)
            rows = []
            for name in active_set:
                total_j = float(panel_s[(panel_s['week'] == w) & (panel_s['celebrity_name'].astype(str) == name)]['total_judge_score'].astype(float).sum())
                rows.append({'celebrity_name': name, 'qJ': qJ.get(name, 0.0), 'p_est': pmap.get(name, 0.0), 'total_judge_score': total_j})
            df = pd.DataFrame(rows)
            df['S'] = alpha * df['qJ'] + (1.0 - alpha) * df['p_est']
            df_sorted = tie_break_sort_percent_df(df)
            elim_name = df_sorted.head(1)['celebrity_name'].iloc[0]
            elim.append(elim_name)
            active_set = [a for a in active_set if a != elim_name]

        history.append({'week': w, 'm': m, 'elim_pred': elim.copy(), 'active_count': len(active_set) + len(elim)})
        next_idx = weeks.index(w) + 1
        if next_idx < len(weeks):
            next_week = weeks[next_idx]
            active_set = [a for a in active_set if a in A_t.get(next_week, [])]

    return history


def write_history_csv(history: List[Dict], out_path: str, season: str, method: str):
    rows = []
    for h in history:
        rows.append({'season': season, 'method': method, 'week': h['week'], 'm': h['m'], 'active_count': h['active_count'], 'elim_pred': ';'.join(h['elim_pred'])})
    pd.DataFrame(rows).to_csv(out_path, index=False)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', required=True)
    p.add_argument('--elim-col', default='eliminated')
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--out-dir', default=str(REPLAYS_DIR))
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest = pd.read_csv(args.pest)

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))

    pairwise_details = []
    pairwise_summary = []

    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        if panel_s.empty:
            continue
        pest_s = pest[pest['season'].astype(str) == str(s)].copy()

        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())
        m_map = infer_elim_counts_from_col(panel_s, args.elim_col)

        history_last_two = simulate_percent_last_two(panel_s, pest_s, alpha=args.alpha, m_map=m_map)
        outp = os.path.join(args.out_dir, f'replay_percent_last_two_season{str(s)}.csv')
        write_history_csv(history_last_two, outp, s, 'percent_last_two')
        print('Wrote', outp)

        replays = {}
        for method in ['percent', 'rank', 'percent_last_two']:
            path = os.path.join(args.out_dir, f'replay_{method}_season{str(s)}.csv')
            if os.path.exists(path):
                replays[method] = pd.read_csv(path)

        pred_survivors_by_method = {}
        for method, df_rep in replays.items():
            curr = set(A_t[weeks[0]]) if weeks else set()
            pred_survivors_by_week = {}
            for _, r in df_rep.iterrows():
                w = int(r['week'])
                pred_list = [p for p in str(r.get('elim_pred','')).split(';') if p!='']
                curr = set(curr) - set(pred_list)
                pred_survivors_by_week[w] = set(curr)
            pred_survivors_by_method[method] = pred_survivors_by_week

        methods = sorted(pred_survivors_by_method.keys())
        for i in range(len(methods)):
            for j in range(i+1, len(methods)):
                m1 = methods[i]
                m2 = methods[j]
                details = []
                jaccs = []
                for w in weeks:
                    s1 = pred_survivors_by_method.get(m1, {}).get(w, None)
                    s2 = pred_survivors_by_method.get(m2, {}).get(w, None)
                    if s1 is None or s2 is None:
                        continue
                    inter = len(s1 & s2)
                    union = len(s1 | s2)
                    j = (inter / union) if union > 0 else 1.0
                    details.append({'season': s, 'week': w, 'method1': m1, 'method2': m2, 'jaccard': j, 'count1': len(s1), 'count2': len(s2), 'intersection': inter})
                    jaccs.append(j)
                mean_j = float(sum(jaccs)/len(jaccs)) if jaccs else None
                pairwise_summary.append({'season': s, 'method1': m1, 'method2': m2, 'mean_jaccard': mean_j, 'weeks_compared': len(jaccs)})
                pairwise_details.extend(details)

    out_details = 'src/eval/jaccard_pairwise_details.csv'
    out_summary = 'src/eval/jaccard_pairwise_summary.csv'
    pd.DataFrame(pairwise_details).to_csv(out_details, index=False)
    pd.DataFrame(pairwise_summary).to_csv(out_summary, index=False)
    print('Wrote', out_details, out_summary)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
