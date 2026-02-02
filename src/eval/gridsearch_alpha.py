"""
Gridsearch over alpha: for each alpha, run the solver to produce p_est, run canonical replay using that p_est, compute canonical fidelity, and record the aggregate mean-season Jaccard.

Usage:
    python3 src/eval/gridsearch_alpha.py --alphas 0.0,0.25,0.5,0.75,1.0

Outputs:
    src/eval/alpha_gridsearch_results.csv

Notes:
    - This script invokes the existing CLI tools `src/sim/model_main.py`, `src/sim/replay_simulator.py`, and `src/eval/compute_fidelity_canon.py`.
    - It expects the canonical panel at `output/data_cleaned/intermediate_weekly_panel.csv` and will pass `--elim-col true_elim_flag` to the solver and replay where appropriate.
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
OUT_SUM = os.path.join(ROOT, 'src', 'eval', 'alpha_gridsearch_results.csv')

DEFAULT_ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]


def run_cmd(cmd, cwd=None, timeout=600):
    print('RUN:', ' '.join(cmd))
    res = subprocess.run(cmd, cwd=cwd or ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
    print(res.stdout)
    if res.returncode != 0:
        raise SystemExit(f'Command failed: {cmd}\nExit {res.returncode}')


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--alphas', default=','.join(map(str, DEFAULT_ALPHAS)), help='Comma-separated list of alphas to try')
    p.add_argument('--lambda-reg', type=float, default=1000.0, help='Lambda regularization for xi (passed to solver)')
    p.add_argument('--elim-col', default='true_elim_flag', help='Elim column to pass to solver/replay')
    p.add_argument('--panel', default=PANEL)
    p.add_argument('--overwrite', action='store_true')
    args = p.parse_args(argv)

    if not os.path.exists(args.panel):
        raise SystemExit('Panel not found at ' + args.panel)

    alphas = [float(x) for x in str(args.alphas).split(',') if x.strip()!='']
    results = []

    for a in alphas:
        # prepare output pest path
        a_str = str(a).replace('.', 'p')
        pest_out = os.path.join(ROOT, 'src', 'sim', f'fan_shares_alpha{a_str}.csv')
        xi_out = os.path.join(ROOT, 'src', 'sim', f'xi_alpha{a_str}.csv')
        # run solver
        if os.path.exists(pest_out) and not args.overwrite:
            print('Skipping solver for alpha', a, 'p_est exists:', pest_out)
        else:
            cmd = [sys.executable, MODEL, '--panel', args.panel, '--out-p', pest_out, '--out-xi', xi_out, '--alpha', str(a), '--elim-col', args.elim_col, '--lambda_reg', str(args.lambda_reg)]
            run_cmd(cmd)

        # run replay simulator in canon mode using this p_est
        # remove old replay files for cleanliness
        replay_cmd = [sys.executable, REPLAY, '--panel', args.panel, '--pest', pest_out, '--season', 'all', '--alpha', str(a), '--methods', 'canon', '--elim-col', args.elim_col]
        run_cmd(replay_cmd)

        # run fidelity computation (this writes src/eval/fidelity_summary_canon.csv)
        run_cmd([sys.executable, FIDEL])

        # read summary and compute aggregate mean-season jaccard
        summ_path = os.path.join(ROOT, 'src', 'eval', 'fidelity_summary_canon.csv')
        if not os.path.exists(summ_path):
            raise SystemExit('Fidelity summary not found at ' + summ_path)
        df = pd.read_csv(summ_path)
        mean_unweighted = df['mean_jaccard'].dropna().mean()
        weighted = (df['mean_jaccard'] * df['weeks_compared']).sum() / df['weeks_compared'].sum()
        results.append({'alpha': a, 'mean_jaccard_unweighted': mean_unweighted, 'mean_jaccard_weighted': weighted, 'n_seasons': len(df), 'total_weeks': int(df['weeks_compared'].sum())})
        # small sleep to avoid tight loop
        time.sleep(1)

    out_df = pd.DataFrame(results).sort_values('alpha')
    out_df.to_csv(OUT_SUM, index=False)
    print('Wrote', OUT_SUM)
    print(out_df.to_string(index=False))


if __name__ == '__main__':
    main(sys.argv[1:])
