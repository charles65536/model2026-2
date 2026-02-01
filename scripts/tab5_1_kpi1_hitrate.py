"""Compute KPI1 hit-rate table (rank vs percent) by era and overall.
Output: `src/eval/tab5_1_kpi1_hitrate.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--in', default='output/intermediate_baseline_preds.csv')
    p.add_argument('--out', default='src/eval/tab5_1_kpi1_hitrate.csv')
    args = p.parse_args(argv)

    df = pd.read_csv(args.in)
    # Expect columns match_percent and match_rank or similar
    if 'match_percent' not in df.columns and 'match_rank' not in df.columns:
        # try to find likely columns
        for c in df.columns:
            if c.lower().startswith('match'):
                if 'percent' in c.lower():
                    df['match_percent'] = df[c]
                if 'rank' in c.lower():
                    df['match_rank'] = df[c]

    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    # Determine era grouping: user may define era via season cutoff; here just overall and by season
    rows = []
    overall = {'group': 'overall'}
    overall['n_eligible'] = len(df)
    overall['percent_hitrate'] = float(df['match_percent'].astype(bool).mean()) if 'match_percent' in df.columns else None
    overall['rank_hitrate'] = float(df['match_rank'].astype(bool).mean()) if 'match_rank' in df.columns else None
    rows.append(overall)

    for s, g in df.groupby('season'):
        rows.append({'group': s, 'n_eligible': len(g), 'percent_hitrate': float(g['match_percent'].astype(bool).mean()) if 'match_percent' in g.columns else None, 'rank_hitrate': float(g['match_rank'].astype(bool).mean()) if 'match_rank' in g.columns else None})

    pd.DataFrame(rows).to_csv(args.out, index=False)
    print('Wrote', args.out)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
