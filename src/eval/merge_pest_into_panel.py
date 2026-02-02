"""Merge p_est (fan_shares) files into the cleaned panel.

Searches `src/sim/` for `fan_shares_s*_alpha{a}.csv` (or `fan_shares_alpha{a}.csv`),
concatenates them, and left-joins onto the panel by `season,week,celebrity_name`.

Usage:
  PYTHONPATH=. python3 src/eval/merge_pest_into_panel.py --alpha 0.5

Outputs:
  - `output/data_cleaned/clean_long_data_with_p_est_alpha{a}.csv`
"""
from __future__ import annotations
import os
import sys
import glob
import argparse
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PANEL = os.path.join(ROOT, 'output', 'data_cleaned', 'clean_long_data_new1.csv')
SIM_DIR = os.path.join(ROOT, 'src', 'sim')
OUT_DIR = os.path.join(ROOT, 'output', 'data_cleaned')
os.makedirs(OUT_DIR, exist_ok=True)


def find_fan_files(alpha_str: str):
    pat1 = os.path.join(SIM_DIR, f'fan_shares_s*_alpha{alpha_str}.csv')
    pat2 = os.path.join(SIM_DIR, f'fan_shares_alpha{alpha_str}.csv')
    files = glob.glob(pat1) + glob.glob(pat2)
    files = sorted(list(set(files)))
    return files


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--alpha', type=float, default=0.5)
    p.add_argument('--panel', default=PANEL)
    p.add_argument('--sim_dir', default=SIM_DIR)
    p.add_argument('--out_dir', default=OUT_DIR)
    args = p.parse_args(argv)

    alpha_str = str(args.alpha).replace('.', 'p')
    files = find_fan_files(alpha_str)
    if not files:
        print('No fan_shares files found for alpha', args.alpha, 'searched in', args.sim_dir)
        sys.exit(1)
    print('Found', len(files), 'fan_shares files; using alpha', args.alpha)

    pest_list = []
    for fpath in files:
        try:
            df = pd.read_csv(fpath)
            # ensure columns
            if {'season','week','celebrity_name','p_est'}.issubset(df.columns):
                pest_list.append(df[['season','week','celebrity_name','p_est']])
        except Exception as e:
            print('Could not read', fpath, e)

    if not pest_list:
        print('No valid pest files parsed.')
        sys.exit(1)

    pest_df = pd.concat(pest_list, ignore_index=True)
    # normalize types
    pest_df['season'] = pest_df['season'].astype(int)
    pest_df['week'] = pest_df['week'].astype(int)
    pest_df['celebrity_name'] = pest_df['celebrity_name'].astype(str)

    panel = pd.read_csv(args.panel)
    # perform left join
    merged = panel.merge(pest_df, how='left', on=['season','week','celebrity_name'])
    out_path = os.path.join(args.out_dir, f'clean_long_data_with_p_est_alpha{alpha_str}.csv')
    merged.to_csv(out_path, index=False)
    print('Wrote merged panel with p_est to', out_path)


if __name__ == '__main__':
    main(sys.argv[1:])
