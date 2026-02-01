"""Create a replay-ready canonical panel CSV by mapping common column names.
Usage: python3 scripts/make_replay_ready_panel.py --in <input_csv> --out <output_csv>
"""
import argparse
import pandas as pd


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--in', dest='infile', default='output/data_cleaned/clean_long_data_new1.csv')
    p.add_argument('--out', dest='outfile', default='output/data_cleaned/canonical_replay_ready.csv')
    args = p.parse_args(argv)

    df = pd.read_csv(args.infile)

    # Copy relevant columns if present, otherwise try alternative names
    out = df.copy()

    # Standardize common names
    if 'J_total' in out.columns and 'total_judge_score' not in out.columns:
        out['total_judge_score'] = out['J_total']
    if 'J_pct' in out.columns and 'judge_percent' not in out.columns:
        out['judge_percent'] = out['J_pct']
    if 'elim_week' in out.columns and 'exit_week' not in out.columns:
        out['exit_week'] = out['elim_week']
    if 'celebrity_name' not in out.columns and 'name' in out.columns:
        out['celebrity_name'] = out['name']

    # Ensure minimal required columns exist
    required = ['season', 'week', 'celebrity_name', 'total_judge_score', 'judge_percent', 'eliminated', 'active']
    for c in required:
        if c not in out.columns:
            out[c] = pd.NA

    # Write out canonical file
    out.to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
