Scripts to produce CSVs for figures/tables referenced in the report.

Usage examples:

```bash
# Canonicalize replay-ready panel
python3 scripts/make_replay_ready_panel.py --in output/data_cleaned/clean_long_data_new1.csv --out output/data_cleaned/canonical_replay_ready.csv

# Figure 3.1 data inventory
python3 scripts/fig3_1_data_inventory.py --in data_raw/2026_MCM_Problem_C_Data.csv --out src/eval/fig3_1_data_inventory.csv

# Figure 3.2 irregular weeks
python3 scripts/fig3_2_irregular_weeks.py --in output/intermediate_baseline_preds.csv --out src/eval/fig3_2_irregular_weeks.csv

# Figure 3.3 active placeholders
python3 scripts/fig3_3_active_placeholders.py --in output/data_cleaned/intermediate_weekly_panel.csv --out src/eval/fig3_3_active_placeholders.csv

# Figure 5.1 flip rate by season
python3 scripts/fig5_1_fliprate_by_season.py --in output/intermediate_baseline_preds.csv --out src/eval/fig5_1_fliprate_by_season.csv

# Table 5.1 KPI1 hit-rate
python3 scripts/tab5_1_kpi1_hitrate.py --in output/intermediate_baseline_preds.csv --out src/eval/tab5_1_kpi1_hitrate.csv
```

Notes:
- These scripts produce CSVs used by the visualization notebook or plotting code. They try to be defensive about column names.
- For figures that require replays you may need to run existing replay scripts in `src/sim` first to ensure `src/sim/replay_*` files exist.
