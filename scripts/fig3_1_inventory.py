"""Produce a column inventory CSV for the raw data file.
Outputs: `src/eval/fig3_1_data_inventory.csv`
"""
import pandas as pd
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='infile', default='data_raw/2026_MCM_Problem_C_Data.csv')
    parser.add_argument('--output', dest='outfile', default='src/eval/fig3_1_data_inventory.csv')
    args = parser.parse_args(argv)

    df = pd.read_csv(args.infile)
    rows = []
    for col in df.columns:
        ser = df[col]
        rows.append({
            'column': col,
            'dtype': str(ser.dtype),
            'non_null': int(ser.notna().sum()),
            'null': int(ser.isna().sum()),
            'unique': int(ser.nunique(dropna=True)),
            'sample': str(ser.dropna().astype(str).head(3).tolist())
        })

    pd.DataFrame(rows).to_csv(args.outfile, index=False)
    print('Wrote', args.outfile)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
