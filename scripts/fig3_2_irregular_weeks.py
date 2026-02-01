"""Compute per-season irregular week stats (true_k==0, true_k>1).
Output: `src/eval/fig3_2_irregular_weeks.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='infile', default='output/intermediate_baseline_preds.csv')
    parser.add_argument('--output', dest='outfile', default='src/eval/fig3_2_irregular_weeks.csv')
    args = parser.parse_args(argv)

    df = pd.read_csv(args.infile)
    if 'true_k' not in df.columns:
        # try alternative column names
        for alt in ['k_true', 'true_k_elim', 'true_k_value']:
            if alt in df.columns:
                df['true_k'] = df[alt]
                break

    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    out_rows = []
    for s, g in df.groupby('season'):
        total = len(g)
        if 'true_k' in g.columns:
            zero = int((g['true_k'] == 0).sum())
            gt1 = int((g['true_k'] > 1).sum())
        else:
            zero = gt1 = 0
        out_rows.append({'season': s, 'weeks': total, 'true_k_eq_0': zero, 'true_k_gt_1': gt1, 'prop_zero': zero / total if total>0 else None, 'prop_gt1': gt1/total if total>0 else None})

    pd.DataFrame(out_rows).to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
"""Compute per-season irregular week stats (true_k==0, true_k>1).
Output: `src/eval/fig3_2_irregular_weeks.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--in', default='output/intermediate_baseline_preds.csv')
    p.add_argument('--out', default='src/eval/fig3_2_irregular_weeks.csv')
    args = p.parse_args(argv)

    df = pd.read_csv(args.in)
    if 'true_k' not in df.columns:
        # try alternative column names
        for alt in ['k_true', 'true_k_elim', 'true_k_value']:
            if alt in df.columns:
                df['true_k'] = df[alt]
                break

    if 'season' not in df.columns:
        df['season'] = df.get('Season', pd.NA)

    out_rows = []
    for s, g in df.groupby('season'):
        total = len(g)
        if 'true_k' in g.columns:
            zero = int((g['true_k'] == 0).sum())
            gt1 = int((g['true_k'] > 1).sum())
        else:
            zero = gt1 = 0
        out_rows.append({'season': s, 'weeks': total, 'true_k_eq_0': zero, 'true_k_gt_1': gt1, 'prop_zero': zero / total if total>0 else None, 'prop_gt1': gt1/total if total>0 else None})

    pd.DataFrame(out_rows).to_csv(args.out, index=False)
    print('Wrote', args.out)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
