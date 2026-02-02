"""Compatibility wrapper: delegate to `src.sim.replay_simulator` but emit replays under `src/eval/` to preserve past behavior.

This wrapper centralizes simulation logic in `src/sim/replay_simulator.py` while keeping the historical
file layout for downstream eval scripts that read `src/eval/replay_*.csv`.
"""
from __future__ import annotations
import argparse
import os
from typing import List
import pandas as pd

from src.sim.replay_simulator import simulate_season, choose_default_pest, write_history_csv
from src.tools.paths import REPLAYS_DIR, ensure_dirs

# ensure the replays dir exists
ensure_dirs([REPLAYS_DIR])


def main(argv: List[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--panel', required=True)
    p.add_argument('--pest', default=None)
    p.add_argument('--season', required=True, help='season number or "all"')
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--methods', default='percent,rank', help='comma separated list of methods to run')
    p.add_argument('--elim-col', default=None)
    p.add_argument('--verbose', action='store_true')
    args = p.parse_args(argv)

    panel = pd.read_csv(args.panel)
    pest_path = args.pest if args.pest and os.path.exists(args.pest) else None
    if pest_path is None:
        pest_path = choose_default_pest()
    pest = pd.read_csv(pest_path)

    seasons = sorted(panel['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    if args.season != 'all':
        seasons = [s for s in seasons if str(s) == str(args.season)]

    methods = [m.strip() for m in args.methods.split(',') if m.strip()]
    for s in seasons:
        panel_s = panel[panel['season'].astype(str) == str(s)].copy()
        pest_s = pest[pest['season'].astype(str) == str(s)].copy()
        m_map = None
        if args.elim_col and args.elim_col in panel_s.columns:
            # reuse sim implementation for infer_elim_counts_from_col by calling simulate_season with m_map later
            # but we need m_map here; import from sim module if available
            from src.sim.replay_simulator import infer_elim_counts_from_col

            m_map = infer_elim_counts_from_col(panel_s, args.elim_col)
            if args.verbose:
                print(f'Using elim_col {args.elim_col} to infer elimination counts: {m_map}')

        for method in methods:
            history = simulate_season(panel_s, pest_s, alpha=args.alpha, method=method, m_map=m_map, verbose=args.verbose)
            out_p_eval = os.path.join('src', 'eval', f'replay_{method}_season{str(s)}.csv')
            out_p_replay = os.path.join(REPLAYS_DIR, f'replay_{method}_season{str(s)}.csv')
            # write both places for backward compatibility
            write_history_csv(history, out_p_eval, s, method)
            write_history_csv(history, out_p_replay, s, method)
            print('Wrote', out_p_eval, 'and', out_p_replay)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
