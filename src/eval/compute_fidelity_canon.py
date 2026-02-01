"""
Compute fidelity (Jaccard) of a canonical method per season against the real panel.

Canon rule mapping per season:
 - seasons 1-2: 'rank'
 - seasons 3-27: 'percent'
 - seasons 28+: 'percent_last_two'

This script looks for replay files `replay_{method}_season{S}.csv` under `src/eval/` (or `src/sim/`),
computes per-week Jaccard between the canon method's predicted survivors and the actual survivors,
and writes `src/eval/fidelity_details_canon.csv` and `src/eval/fidelity_summary_canon.csv`.
"""
from __future__ import annotations
import os
import glob
import pandas as pd
from typing import Dict, List, Set

PANEL = 'output/data_cleaned/intermediate_weekly_panel.csv'
EVAL_DIR = 'src/eval'
OUT_DETAILS = os.path.join(EVAL_DIR, 'fidelity_details_canon.csv')
OUT_SUMMARY = os.path.join(EVAL_DIR, 'fidelity_summary_canon.csv')


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


def find_replay(method: str, season: str) -> str:
    # prefer src/eval, fallback to src/sim
    p1 = os.path.join(EVAL_DIR, f'replay_{method}_season{season}.csv')
    if os.path.exists(p1):
        return p1
    p2 = os.path.join('src', 'sim', f'replay_{method}_season{season}.csv')
    if os.path.exists(p2):
        return p2
    return ''


def canon_method_for_season(s: int) -> str:
    if s in (1, 2):
        return 'rank'
    if 3 <= s <= 27:
        return 'percent'
    return 'percent_last_two'


def main():
    if not os.path.exists(PANEL):
        raise SystemExit(f'Panel not found at {PANEL}')
    panel = pd.read_csv(PANEL)
    if 'true_elim_flag' not in panel.columns:
        raise SystemExit('Panel missing true_elim_flag column; cannot compute actual eliminations')

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))

    details = []
    summary = []

    for s in seasons:
        s_int = int(float(s))
        method = canon_method_for_season(s_int)
        replay_path = find_replay(method, str(s))
        if replay_path == '':
            print(f'Warning: replay for season {s} method {method} not found; skipping')
            continue

        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        if panel_s.empty:
            continue

        A_t = build_week_participants(panel_s)
        weeks = sorted(A_t.keys())

        # actual elim sets per week
        actual_elim_by_week: Dict[int, Set[str]] = {}
        if 'week' in panel_s.columns:
            for w in weeks:
                names = panel_s.loc[(panel_s.get('week') == w) & (panel_s['true_elim_flag'].astype(bool)), 'celebrity_name'].astype(str).tolist()
                actual_elim_by_week[w] = set(names)
        else:
            for w in weeks:
                actual_elim_by_week[w] = set()

        # actual survivors after each week
        actual_survivors = {}
        curr = set(A_t[weeks[0]]) if weeks else set()
        for w in weeks:
            elim = actual_elim_by_week.get(w, set())
            curr = set(curr) - set(elim)
            actual_survivors[w] = set(curr)

        # read replay predictions and reconstruct predicted survivors
        rep = pd.read_csv(replay_path)
        pred_survivors = {}
        curr_pred = set(A_t[weeks[0]]) if weeks else set()
        for _, r in rep.iterrows():
            try:
                w = int(r['week'])
            except Exception:
                continue
            pred_field = r.get('elim_pred', '')
            preds = [p.strip() for p in str(pred_field).split(';') if p and str(p).strip().lower() not in ('', 'nan', 'none')]
            curr_pred = set(curr_pred) - set(preds)
            pred_survivors[w] = set(curr_pred)

        # compute per-week jaccard for weeks present in both
        jaccs = []
        for w in weeks:
            a = actual_survivors.get(w, set())
            pset = pred_survivors.get(w, None)
            if pset is None:
                continue
            inter = len(a & pset)
            union = len(a | pset)
            j = (inter / union) if union > 0 else 1.0
            jaccs.append(j)
            details.append({'season': s, 'canon_method': method, 'week': w, 'jaccard': j, 'actual_count': len(a), 'pred_count': len(pset), 'intersection': inter})

        mean_j = float(sum(jaccs) / len(jaccs)) if jaccs else None
        summary.append({'season': s, 'canon_method': method, 'mean_jaccard': mean_j, 'weeks_compared': len(jaccs)})

    pd.DataFrame(details).to_csv(OUT_DETAILS, index=False)
    pd.DataFrame(summary).to_csv(OUT_SUMMARY, index=False)
    print('Wrote', OUT_DETAILS, OUT_SUMMARY)
    # print aggregate
    if summary:
        df = pd.DataFrame(summary)
        mean_all = df['mean_jaccard'].dropna().mean()
        print(f'Aggregate mean-season Jaccard for canon mapping: {mean_all:.6f}')


if __name__ == '__main__':
    main()
