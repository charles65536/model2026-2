"""Compute flip rate by season using intermediate baseline preds.
Output: `src/eval/fig5_1_fliprate_by_season.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--in', default='output/intermediate_baseline_preds.csv')
    p.add_argument('--out', default='src/eval/fig5_1_fliprate_by_season.csv')
    args = p.parse_args(argv)

    df = pd.read_csv(args.in)
    # determine flip indicator
    if 'flip' in df.columns:
        df['flip_flag'] = df['flip'].astype(bool)
    else:
        # try to infer from match columns
        possible = []
        for c in ['match_percent', 'match_rank', 'match_baseline']:
            if c in df.columns:
                possible.append(c)
        if possible:
            # assume flip means not both match_percent and match_rank true
            if 'match_percent' in df.columns and 'match_rank' in df.columns:
                df['flip_flag'] = (~(df['match_percent'].astype(bool) & df['match_rank'].astype(bool))).astype(bool)
            else:
                df['flip_flag'] = (~df[possible[0]].astype(bool)).astype(bool)
        else:
            # fallback: no flip info
            df['flip_flag'] = False

    out_rows = []
    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    for s, g in df.groupby('season'):
        eligible = g
        total = len(eligible)
        flips = int(eligible['flip_flag'].sum())
        out_rows.append({'season': s, 'weeks': total, 'flips': flips, 'flip_rate': flips / total if total>0 else None})

    pd.DataFrame(out_rows).to_csv(args.out, index=False)
    print('Wrote', args.out)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
