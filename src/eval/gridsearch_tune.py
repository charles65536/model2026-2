"""
Gridsearch orchestration for tuning `--lambda-judge` and `--alpha`.

For each parameter combo the script will:
 - run the solver to produce `src/sim/fan_shares_grid_lambda{L}_alpha{A}.csv`
 - run replays for all seasons (percent, rank, js_sr)
 - generate `percent_last_two` replays
 - copy replays into `src/eval/`
 - run `compute_fidelity_canon.py` to compute canonical-fidelity mean-season Jaccard
 - record the aggregate mean-season Jaccard in `src/eval/gridsearch_results.csv`

Usage: run this script from the repository root with Python 3.
"""
from __future__ import annotations
import subprocess
import os
import itertools
import pandas as pd

PANEL = 'output/data_cleaned/clean_long_data_replay_ready.csv'
OUT_DIR_SIM = 'src/sim'
OUT_DIR_EVAL = 'src/eval'

def run(cmd):
    print('RUN:', cmd)
    res = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(res.stdout)
    return res.returncode, res.stdout


def main():
    # parameter grid
    lambda_vals = [0, 1, 10, 100]
    alphas = [0.3, 0.5, 0.7]

    results = []

    for L, A in itertools.product(lambda_vals, alphas):
        tag = f'lambda{L}_alpha{str(A).replace(".","p")}'
        pest_out = os.path.join(OUT_DIR_SIM, f'fan_shares_{tag}.csv')
        xi_out = os.path.join(OUT_DIR_SIM, f'xi_{tag}.csv')

        # 1) run solver
        cmd1 = f'python3 src/sim/model_main.py --panel {PANEL} --out-p {pest_out} --out-xi {xi_out} --alpha {A} --lambda-judge {L} --verbose'
        rc, out = run(cmd1)
        if rc != 0:
            print(f'Solver failed for {tag}; skipping result record')
            continue

        # 2) run replays for all seasons (percent, rank, js_sr)
        cmd2 = f'python3 src/sim/replay_simulator.py --panel {PANEL} --pest {pest_out} --season all --alpha {A} --methods percent,rank,js_sr --elim-col eliminated'
        run(cmd2)

        # 3) generate percent_last_two + pairwise details
        cmd3 = f'python3 src/eval/compare_three_strategies.py --panel {PANEL} --pest {pest_out} --alpha {A} --out-dir {OUT_DIR_SIM} --elim-col eliminated'
        run(cmd3)

        # 4) copy replays to src/eval
        run(f'cp -v {OUT_DIR_SIM}/replay_*_season*.csv {OUT_DIR_EVAL}/')

        # 5) run canonical-fidelity
        run('python3 src/eval/compute_fidelity_canon.py')

        # 6) read summary and extract mean across seasons
        summary_path = os.path.join(OUT_DIR_EVAL, 'fidelity_summary_canon.csv')
        mean_j = None
        if os.path.exists(summary_path):
            df = pd.read_csv(summary_path)
            mean_j = df['mean_jaccard'].dropna().mean()

        results.append({'lambda_judge': L, 'alpha': A, 'mean_season_jaccard': mean_j})

    out_df = pd.DataFrame(results)
    out_csv = os.path.join(OUT_DIR_EVAL, 'gridsearch_results.csv')
    out_df.to_csv(out_csv, index=False)
    print('Wrote', out_csv)


if __name__ == '__main__':
    main()
