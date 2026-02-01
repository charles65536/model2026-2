"""Compute flip rate by season using intermediate baseline preds.
Output: `src/eval/fig5_1_fliprate_by_season.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='infile', default='output/intermediate_baseline_preds.csv')
    parser.add_argument('--output', dest='outfile', default='src/eval/fig5_1_fliprate_by_season.csv')
    args = parser.parse_args(argv)

    df = pd.read_csv(args.infile)
    # build flip flag defensively
    if 'flip' in df.columns:
        df['flip_flag'] = df['flip'].astype(bool)
    else:
        if 'match_percent' in df.columns and 'match_rank' in df.columns:
            df['flip_flag'] = (~(df['match_percent'].astype(bool) & df['match_rank'].astype(bool))).astype(bool)
        elif 'match_percent' in df.columns:
            df['flip_flag'] = (~df['match_percent'].astype(bool)).astype(bool)
        else:
            df['flip_flag'] = False

    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    out_rows = []
    for s, g in df.groupby('season'):
        total = len(g)
        flips = int(g['flip_flag'].sum())
        out_rows.append({'season': s, 'weeks': total, 'flips': flips, 'flip_rate': flips / total if total > 0 else None})

    pd.DataFrame(out_rows).to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
