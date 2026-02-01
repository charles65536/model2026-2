"""Compute counts of active vs post-exit placeholder records per season and overall.
Output: `src/eval/fig3_3_active_placeholders.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='infile', default='output/data_cleaned/intermediate_weekly_panel.csv')
    parser.add_argument('--output', dest='outfile', default='src/eval/fig3_3_active_placeholders.csv')
    args = parser.parse_args(argv)

    df = pd.read_csv(args.infile)
    if 'active' not in df.columns:
        for alt in ['is_active', 'Active', 'active_flag']:
            if alt in df.columns:
                df['active'] = df[alt]
                break

    out_rows = []
    for s, g in df.groupby('season'):
        total = len(g)
        if 'active' in g.columns:
            active = int(g['active'].astype(bool).sum())
            inactive = int((~g['active'].astype(bool)).sum())
        else:
            active = inactive = None
        out_rows.append({'season': s, 'rows': total, 'active_count': active, 'inactive_count': inactive})

    overall = {'season': 'overall', 'rows': len(df)}
    if 'active' in df.columns:
        overall['active_count'] = int(df['active'].astype(bool).sum())
        overall['inactive_count'] = int((~df['active'].astype(bool)).sum())
    else:
        overall['active_count'] = overall['inactive_count'] = None

    out_rows.append(overall)
    pd.DataFrame(out_rows).to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
