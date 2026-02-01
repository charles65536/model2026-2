"""Compute counts of active vs post-exit placeholder records per season and overall.
Output: `src/eval/fig3_3_active_placeholders.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--in', default='output/data_cleaned/intermediate_weekly_panel.csv')
    p.add_argument('--out', default='src/eval/fig3_3_active_placeholders.csv')
    args = p.parse_args(argv)

    df = pd.read_csv(args.in)
    if 'active' not in df.columns:
        # try alternative names
        for alt in ['is_active', 'Active', 'active_flag']:
            if alt in df.columns:
                df['active'] = df[alt]
                break

    out_rows = []
    for s, g in df.groupby('season'):
        total = len(g)
        active = int(g['active'].astype(bool).sum()) if 'active' in g.columns else None
        inactive = int((~g['active'].astype(bool)).sum()) if 'active' in g.columns else None
        out_rows.append({'season': s, 'rows': total, 'active_count': active, 'inactive_count': inactive})

    # overall
    overall = {'season': 'overall', 'rows': len(df)}
    if 'active' in df.columns:
        overall['active_count'] = int(df['active'].astype(bool).sum())
        overall['inactive_count'] = int((~df['active'].astype(bool)).sum())
    else:
        overall['active_count'] = overall['inactive_count'] = None

    out_rows.append(overall)
    pd.DataFrame(out_rows).to_csv(args.out, index=False)
    print('Wrote', args.out)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
