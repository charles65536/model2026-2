"""Compute KPI1 hit-rate table (rank vs percent) by era and overall.
Output: `src/eval/tab5_1_kpi1_hitrate.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='infile', default='output/intermediate_baseline_preds.csv')
    parser.add_argument('--output', dest='outfile', default='src/eval/tab5_1_kpi1_hitrate.csv')
    args = parser.parse_args(argv)

    df = pd.read_csv(args.infile)

    # detect match columns
    if 'match_percent' not in df.columns or 'match_rank' not in df.columns:
        for c in df.columns:
            lc = c.lower()
            if 'match' in lc and 'percent' in lc:
                df['match_percent'] = df[c]
            if 'match' in lc and 'rank' in lc:
                df['match_rank'] = df[c]

    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    rows = []
    overall = {
        'group': 'overall',
        'n_eligible': len(df),
        'percent_hitrate': float(df['match_percent'].astype(bool).mean()) if 'match_percent' in df.columns else None,
        'rank_hitrate': float(df['match_rank'].astype(bool).mean()) if 'match_rank' in df.columns else None
    }
    rows.append(overall)

    for s, g in df.groupby('season'):
        rows.append({
            'group': s,
            'n_eligible': len(g),
            'percent_hitrate': float(g['match_percent'].astype(bool).mean()) if 'match_percent' in g.columns else None,
            'rank_hitrate': float(g['match_rank'].astype(bool).mean()) if 'match_rank' in g.columns else None
        })

    pd.DataFrame(rows).to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
