"""
Per-season alpha gridsearch: for each season, try multiple alphas and pick the alpha that maximizes canonical Jaccard for that season.

Usage:
    python3 src/eval/gridsearch_alpha_per_season.py --alphas 0.3,0.4,0.5,0.6,0.7 --seasons all

Outputs:
    src/eval/alpha_gridsearch_per_season_results.csv
    src/eval/alpha_gridsearch_per_season_full.csv (detailed per-season per-alpha scores)

Notes:
    - This script filters the master panel to each season to run the solver faster (per-season panels).
    - It uses existing CLIs: src/sim/model_main.py, src/sim/replay_simulator.py, src/eval/compute_fidelity_canon.py
    - By default it uses elim_col 'true_elim_flag'.
"""
import argparse
import os
import subprocess
import sys
import time
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
MODEL = os.path.join(ROOT, 'src', 'sim', 'model_main.py')
REPLAY = os.path.join(ROOT, 'src', 'sim', 'replay_simulator.py')
FIDEL = os.path.join(ROOT, 'src', 'eval', 'compute_fidelity_canon.py')
OUT_SUM = os.path.join(ROOT, 'src', 'eval', 'alpha_gridsearch_per_season_results.csv')
OUT_FULL = os.path.join(ROOT, 'src', 'eval', 'alpha_gridsearch_per_season_full.csv')
TMP_DIR = os.path.join(ROOT, 'src', 'eval', 'tmp')

DEFAULT_ALPHAS = [0.3, 0.4, 0.5, 0.6, 0.7]

os.makedirs(TMP_DIR, exist_ok=True)


def run_cmd(cmd, cwd=None, timeout=600):
    print('RUN:', ' '.join(cmd))
    res = subprocess.run(cmd, cwd=cwd or ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    print(res.stdout)
    if res.returncode != 0:
        raise SystemExit(f'Command failed: {cmd}\nExit {res.returncode}\nOutput:\n{res.stdout}')


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--alphas', default=','.join(map(str, DEFAULT_ALPHAS)))
    p.add_argument('--seasons', default='all', help='Comma-separated list of seasons or "all"')
    p.add_argument('--elim-col', default='true_elim_flag')
    p.add_argument('--overwrite', action='store_true')
    p.add_argument('--panel', default=PANEL)
    args = p.parse_args(argv)

    if not os.path.exists(args.panel):
        raise SystemExit('Panel not found at ' + args.panel)

    alphas = [float(x) for x in str(args.alphas).split(',') if x.strip()!='']
    # seasons
    panel_df = pd.read_csv(args.panel)
    all_seasons = sorted(panel_df['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.', '', 1).isdigit() else str(x))
    if args.seasons.strip().lower() == 'all':
        seasons = [int(float(s)) for s in all_seasons]
    else:
        seasons = [int(float(s)) for s in str(args.seasons).split(',') if s.strip()!='']

    full_rows = []
    best_rows = []

    for s in seasons:
        print('\n=== Season', s, '===')
        # filter panel per season and write temp panel
        panel_s = panel_df[panel_df['season'].astype(float) == float(s)].copy()
        if panel_s.empty:
            print('No rows for season', s, 'skipping')
            continue
        tmp_panel = os.path.join(TMP_DIR, f'panel_season{s}.csv')
        panel_s.to_csv(tmp_panel, index=False)

        season_full = []
        best_alpha = None
        best_score = float('nan')
        for a in alphas:
            a_str = str(a).replace('.', 'p')
            pest_out = os.path.join(ROOT, 'src', 'sim', f'fan_shares_s{s}_alpha{a_str}.csv')
            xi_out = os.path.join(ROOT, 'src', 'sim', f'xi_s{s}_alpha{a_str}.csv')
            # run solver on this single-season panel
            if os.path.exists(pest_out) and not args.overwrite:
                print('p_est exists, skipping solver:', pest_out)
            else:
                cmd = [sys.executable, MODEL, '--panel', tmp_panel, '--out-p', pest_out, '--out-xi', xi_out, '--alpha', str(a), '--elim-col', args.elim_col]
                run_cmd(cmd)
            # run replay for this season using this pest
            cmd2 = [sys.executable, REPLAY, '--panel', tmp_panel, '--pest', pest_out, '--season', str(s), '--alpha', str(a), '--methods', 'canon', '--elim-col', args.elim_col]
            run_cmd(cmd2)
            # compute fidelity (this writes full summary for all seasons; we will read it and extract our season)
            run_cmd([sys.executable, FIDEL])
            summ_path = os.path.join(ROOT, 'src', 'eval', 'fidelity_summary_canon.csv')
            if not os.path.exists(summ_path):
                raise SystemExit('Fidelity summary not produced')
            df_summ = pd.read_csv(summ_path)
            row = df_summ[df_summ['season'].astype(int) == int(s)]
            if row.empty:
                print('No fidelity row for season', s, 'alpha', a)
                score = float('nan')
            else:
                score = float(row['mean_jaccard'].iloc[0])
            season_full.append({'season': s, 'alpha': a, 'mean_jaccard': score})
            full_rows.append({'season': s, 'alpha': a, 'mean_jaccard': score})
            print(f'Season {s} alpha {a} mean_jaccard {score}')
            # small pause
            time.sleep(0.5)

        # Determine best alpha for this season. If multiple alphas tie for the
        # max mean_jaccard, take the mean of the tied alpha values as the
        # tie-breaker (instead of choosing the first one seen).
        df_sec = pd.DataFrame(season_full)
        df_valid = df_sec.dropna(subset=['mean_jaccard'])
        if df_valid.empty:
            best_alpha = None
            best_score = float('nan')
        else:
            max_score = df_valid['mean_jaccard'].max()
            tied_alphas = df_valid[df_valid['mean_jaccard'] == max_score]['alpha']
            # take the mean of tied alphas
            best_alpha = float(tied_alphas.mean())
            best_score = float(max_score)

        best_rows.append({'season': s, 'best_alpha': best_alpha, 'best_mean_jaccard': best_score})

    pd.DataFrame(full_rows).to_csv(OUT_FULL, index=False)
    pd.DataFrame(best_rows).to_csv(OUT_SUM, index=False)
    print('\nWrote', OUT_FULL, OUT_SUM)
    print('Done')


if __name__ == '__main__':
    main(sys.argv[1:])
