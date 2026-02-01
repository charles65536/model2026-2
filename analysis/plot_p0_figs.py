"""Plot P0 figures (quick PNGs) from the CSVs generated earlier.
Outputs PNGs to `output/fig/`.
"""
import os
import pandas as pd
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except Exception:
    PLOTTING_AVAILABLE = False


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def plot_fig3_1(inv_csv, out_dir):
    if not PLOTTING_AVAILABLE:
        df = pd.read_csv(inv_csv)
        out = os.path.join(out_dir, 'fig3_1_data_inventory.txt')
        with open(out, 'w') as f:
            f.write('Top columns by nulls:\n')
            f.write(df.sort_values('null', ascending=False).head(50).to_string())
        print('Wrote', out, '(text; install matplotlib to get PNG)')
        return
    df = pd.read_csv(inv_csv)
    # plot null counts per column
    df = df.sort_values('null', ascending=False)
    plt.figure(figsize=(10, max(4, len(df) * 0.2)))
    sns.barplot(x='null', y='column', data=df, color='C0')
    plt.title('Null counts by column')
    plt.tight_layout()
    out = os.path.join(out_dir, 'fig3_1_data_inventory.png')
    plt.savefig(out)
    plt.close()
    print('Wrote', out)


def plot_fig3_2(irreg_csv, out_dir):
    if not PLOTTING_AVAILABLE:
        df = pd.read_csv(irreg_csv)
        out = os.path.join(out_dir, 'fig3_2_irregular_weeks.txt')
        with open(out, 'w') as f:
            f.write(df.to_string())
        print('Wrote', out, '(text; install matplotlib to get PNG)')
        return
    df = pd.read_csv(irreg_csv)
    df = df.sort_values('season')
    plt.figure(figsize=(10,4))
    plt.plot(df['season'].astype(str), df['prop_zero'], marker='o', label='prop true_k==0')
    plt.plot(df['season'].astype(str), df['prop_gt1'], marker='o', label='prop true_k>1')
    plt.xticks(rotation=45)
    plt.xlabel('season')
    plt.ylabel('proportion')
    plt.legend()
    plt.tight_layout()
    out = os.path.join(out_dir, 'fig3_2_irregular_weeks.png')
    plt.savefig(out)
    plt.close()
    print('Wrote', out)


def plot_fig3_3(active_csv, out_dir):
    if not PLOTTING_AVAILABLE:
        df = pd.read_csv(active_csv)
        out = os.path.join(out_dir, 'fig3_3_active_placeholders.txt')
        with open(out, 'w') as f:
            f.write(df.to_string())
        print('Wrote', out, '(text; install matplotlib to get PNG)')
        return
    df = pd.read_csv(active_csv)
    df2 = df.copy()
    df2 = df2[df2['season'] != 'overall']
    df2 = df2.sort_values('season')
    plt.figure(figsize=(10,4))
    plt.bar(df2['season'].astype(str), df2['active_count'].fillna(0), label='active')
    plt.bar(df2['season'].astype(str), df2['inactive_count'].fillna(0), bottom=df2['active_count'].fillna(0), label='inactive')
    plt.xticks(rotation=45)
    plt.ylabel('rows')
    plt.legend()
    plt.tight_layout()
    out = os.path.join(out_dir, 'fig3_3_active_placeholders.png')
    plt.savefig(out)
    plt.close()
    print('Wrote', out)


def plot_fig5_1(flip_csv, out_dir):
    if not PLOTTING_AVAILABLE:
        df = pd.read_csv(flip_csv)
        out = os.path.join(out_dir, 'fig5_1_fliprate_by_season.txt')
        with open(out, 'w') as f:
            f.write(df.sort_values('flip_rate', ascending=False).to_string())
        print('Wrote', out, '(text; install matplotlib to get PNG)')
        return
    df = pd.read_csv(flip_csv)
    df = df.sort_values('flip_rate', ascending=False)
    plt.figure(figsize=(10,4))
    sns.barplot(x='season', y='flip_rate', data=df, color='C2')
    plt.xticks(rotation=90)
    plt.ylabel('flip rate')
    plt.tight_layout()
    out = os.path.join(out_dir, 'fig5_1_fliprate_by_season.png')
    plt.savefig(out)
    plt.close()
    print('Wrote', out)


def plot_tab5_1(tab_csv, out_dir):
    df = pd.read_csv(tab_csv)
    if not PLOTTING_AVAILABLE:
        out = os.path.join(out_dir, 'tab5_1_kpi1_hitrate.txt')
        with open(out, 'w') as f:
            f.write(df.to_string())
        print('Wrote', out, '(text; install matplotlib to get PNG)')
        return
    plt.figure(figsize=(8, max(2, len(df)*0.25)))
    plt.table(cellText=df.values, colLabels=df.columns, loc='center')
    plt.axis('off')
    out = os.path.join(out_dir, 'tab5_1_kpi1_hitrate.png')
    plt.savefig(out, bbox_inches='tight')
    plt.close()
    print('Wrote', out)


def main():
    out_dir = 'output/fig'
    ensure_dir(out_dir)

    plot_fig3_1('src/eval/fig3_1_data_inventory.csv', out_dir)
    plot_fig3_2('src/eval/fig3_2_irregular_weeks.csv', out_dir)
    plot_fig3_3('src/eval/fig3_3_active_placeholders.csv', out_dir)
    plot_fig5_1('src/eval/fig5_1_fliprate_by_season.csv', out_dir)
    plot_tab5_1('src/eval/tab5_1_kpi1_hitrate.csv', out_dir)


if __name__ == '__main__':
    main()
