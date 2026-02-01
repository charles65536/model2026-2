import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIG_DIR = os.path.join(ROOT, 'output', 'fig')
TAB_DIR = os.path.join(ROOT, 'output', 'tab')
for d in (FIG_DIR, TAB_DIR):
    os.makedirs(d, exist_ok=True)

# Paths
raw_data_path = os.path.join(ROOT, 'data_raw', '2026_MCM_Problem_C_Data.csv')
panel_path = os.path.join(ROOT, 'output', 'data_cleaned', 'intermediate_weekly_panel.csv')
baseline_path = os.path.join(ROOT, 'output', 'data_cleaned', 'intermediate_baseline_preds.csv')

# Read
print('Reading files...')
df_raw = pd.read_csv(raw_data_path)
df_panel = pd.read_csv(panel_path)
df_base = pd.read_csv(baseline_path)
print('Shapes:', df_raw.shape, df_panel.shape, df_base.shape)

# === Tab 3.1: Data inventory (columns overview) ===
inv = []
for col in df_raw.columns:
    inv.append({
        'column': col,
        'n_nonnull': int(df_raw[col].notnull().sum()),
        'n_unique': int(df_raw[col].nunique(dropna=True)),
        'dtype': str(df_raw[col].dtype)
    })
inv_df = pd.DataFrame(inv)
inv_df.to_csv(os.path.join(TAB_DIR, 'tab3_1_data_inventory.csv'), index=False)
print('Wrote', os.path.join(TAB_DIR, 'tab3_1_data_inventory.csv'))

# === Fig 3.1 Judges availability: distribution of n_judges_obs (approx by non-null judge columns) ===
judge_cols = [c for c in df_panel.columns if c.startswith('judge') and 'rank' not in c and 'percent' not in c]
# count non-null judge score per row
df_panel['n_judges_obs'] = df_panel[judge_cols].notnull().sum(axis=1)
plt.figure(figsize=(6,4))
sns.countplot(x='n_judges_obs', data=df_panel, palette='Blues')
plt.xlabel('Observed number of judges (per row)')
plt.ylabel('Count of contestant-weeks')
plt.title('Fig 3.1 Judges availability (n_judges_obs distribution)')
plt.tight_layout()
fig3_1 = os.path.join(FIG_DIR, 'fig3_1_judges_availability.png')
plt.savefig(fig3_1, dpi=150)
plt.close()
print('Wrote', fig3_1)

# === Fig 3.2 Irregular weeks summary: true_k ==0 and true_k >1 proportions by season ===
# Use df_base true_k column
if 'true_k' in df_base.columns:
    tmp = df_base.groupby('season').apply(lambda g: pd.Series({
        'pct_true_k0': (g['true_k']==0).mean(),
        'pct_true_k_gt1': (g['true_k']>1).mean(),
        'n_weeks': len(g)
    })).reset_index()
    plt.figure(figsize=(8,4))
    x = np.arange(len(tmp))
    plt.plot(tmp['season'], tmp['pct_true_k0'], marker='o', label='pct true_k == 0')
    plt.plot(tmp['season'], tmp['pct_true_k_gt1'], marker='s', label='pct true_k > 1')
    plt.xlabel('Season')
    plt.ylabel('Proportion of weeks')
    plt.title('Fig 3.2 Irregular weeks summary by season')
    plt.legend()
    plt.tight_layout()
    fig3_2 = os.path.join(FIG_DIR, 'fig3_2_irregular_weeks_by_season.png')
    plt.savefig(fig3_2, dpi=150)
    plt.close()
    tmp.to_csv(os.path.join(TAB_DIR, 'fig3_2_irregular_weeks_by_season.csv'), index=False)
    print('Wrote', fig3_2)
    print('Wrote', os.path.join(TAB_DIR, 'fig3_2_irregular_weeks_by_season.csv'))
else:
    print('true_k not found in baseline preds; skipping Fig 3.2')

# === Fig 3.3 Active vs post-exit placeholders ===
# Count active True vs False and data_anomaly_zero_score
if 'active' in df_panel.columns:
    df_panel['active_bool'] = df_panel['active'].astype(bool)
    counts = df_panel['active_bool'].value_counts().rename(index={True:'active', False:'inactive'})
    # also count zero-score placeholders where data_anomaly_zero_score True
    if 'data_anomaly_zero_score' in df_panel.columns:
        zero_counts = df_panel['data_anomaly_zero_score'].astype(bool).value_counts().rename(index={True:'anomaly_zero', False:'not_anomaly'})
    else:
        zero_counts = pd.Series()
    plt.figure(figsize=(6,4))
    sns.barplot(x=counts.index, y=counts.values, palette='muted')
    plt.ylabel('Count rows')
    plt.title('Fig 3.3 Active vs placeholders (inactive rows)')
    plt.tight_layout()
    fig3_3 = os.path.join(FIG_DIR, 'fig3_3_active_vs_placeholders.png')
    plt.savefig(fig3_3, dpi=150)
    plt.close()
    counts.to_csv(os.path.join(TAB_DIR, 'fig3_3_active_counts.csv'))
    if not zero_counts.empty:
        zero_counts.to_csv(os.path.join(TAB_DIR, 'fig3_3_zero_score_anomalies.csv'))
    print('Wrote', fig3_3)
    print('Wrote', os.path.join(TAB_DIR, 'fig3_3_active_counts.csv'))
else:
    print('active column not present; skipping Fig 3.3')

# === Fig 5.1 FlipRate by season (eligible weeks only) ===
if 'flip' in df_base.columns and 'eligible' in df_base.columns:
    df_eligible = df_base[df_base['eligible']==True]
    flip_by_season = df_eligible.groupby('season')['flip'].mean().reset_index()
    plt.figure(figsize=(8,4))
    sns.barplot(x='season', y='flip', data=flip_by_season, palette='viridis')
    plt.axhline(df_eligible['flip'].mean(), color='red', linestyle='--', label='Overall mean')
    plt.xlabel('Season')
    plt.ylabel('Flip rate (proportion eligible weeks with flip)')
    plt.title('Fig 5.1 FlipRate by season (eligible weeks)')
    plt.legend()
    plt.tight_layout()
    fig5_1 = os.path.join(FIG_DIR, 'fig5_1_fliprate_by_season.png')
    plt.savefig(fig5_1, dpi=150)
    plt.close()
    flip_by_season.to_csv(os.path.join(TAB_DIR, 'fig5_1_fliprate_by_season.csv'), index=False)
    print('Wrote', fig5_1)
    print('Wrote', os.path.join(TAB_DIR, 'fig5_1_fliprate_by_season.csv'))

    # Tab 5.1 KPI1 hit-rate (rank vs percent) by era
    if 'match_rank' in df_base.columns and 'match_percent' in df_base.columns and 'era' in df_base.columns:
        tab = df_eligible.groupby('era').agg(
            match_rank_mean = ('match_rank', lambda s: s.map({True:1,False:0}).mean()),
            match_percent_mean = ('match_percent', lambda s: s.map({True:1,False:0}).mean()),
            n_eligible = ('eligible', 'sum')
        ).reset_index()
        # Add overall
        overall = pd.DataFrame({'era':['overall'], 'match_rank_mean':[df_eligible['match_rank'].map({True:1,False:0}).mean() if 'match_rank' in df_eligible.columns else np.nan],'match_percent_mean':[df_eligible['match_percent'].map({True:1,False:0}).mean() if 'match_percent' in df_eligible.columns else np.nan], 'n_eligible':[df_eligible['eligible'].sum()]})
        tab_out = pd.concat([overall, tab], ignore_index=True)
        tab_out.to_csv(os.path.join(TAB_DIR, 'tab5_1_kpi1_hitrate.csv'), index=False)
        # also write a simple latex table
        tex_path = os.path.join(TAB_DIR, 'tab5_1_kpi1_hitrate.tex')
        with open(tex_path, 'w') as f:
            f.write(tab_out.to_latex(index=False, float_format="%.3f"))
        print('Wrote', os.path.join(TAB_DIR, 'tab5_1_kpi1_hitrate.csv'))
        print('Wrote', tex_path)
    else:
        print('match_rank/match_percent/era not found; skipping Tab 5.1')
else:
    print('flip/eligible not found in baseline preds; skipping Fig 5.1 & Tab 5.1')

# === Fig 5.2 Era cutoff stress test (cutoffs 27/28/29): recompute flip rate grouping by era cutoff ===
# We'll simulate by recomputing era based on cutoff and plotting flip rate aggregated by new 'era' groupings.
for cutoff in (27,28,29):
    df_base_copy = df_base.copy()
    df_base_copy['era_cut'] = df_base_copy['season'].apply(lambda s: 'rank-era' if s<=cutoff else 'percent-era')
    df_elig_cut = df_base_copy[df_base_copy['eligible']==True]
    flip_cut = df_elig_cut.groupby('era_cut')['flip'].mean().reset_index()
    plt.figure(figsize=(5,3))
    sns.barplot(x='era_cut', y='flip', data=flip_cut, palette='coolwarm')
    plt.ylim(0,1)
    plt.title(f'Fig 5.2 FlipRate by era (cutoff={cutoff})')
    plt.tight_layout()
    out = os.path.join(FIG_DIR, f'fig5_2_cutoff_{cutoff}_fliprate.png')
    plt.savefig(out, dpi=150)
    plt.close()
    flip_cut.to_csv(os.path.join(TAB_DIR, f'fig5_2_cutoff_{cutoff}_fliprate.csv'), index=False)
    print('Wrote', out)

print('All P0 visuals attempted.')
