# Added Columns (summary)

This file documents the new columns added by the preprocessing and analysis scripts in `src/szeto_play_with_data`.

## Source scripts

- `preprocessing.py` — aggregates judge scores per week, computes weekly ranks per season, and counts episodes participated.
- `compute_controversial.py` — computes summary statistics comparing average weekly ranks with final placement and exposes parsed fields for analysis.

## Columns added by `preprocessing.py`

- `agg_week_{n}`
  - Description: Aggregated judge score for week `n` (mean of the judges' numeric scores for that week).
  - Notes: Values <= 0 are treated as missing (NaN) during aggregation to reflect absent scores in the dataset.
  - Example column names: `agg_week_1`, `agg_week_2`, ...

- `rank_of_week_{n}`
  - Description: Per-season rank for week `n` computed from `agg_week_{n}`. Rank 1 is best (highest aggregated score).
  - Notes: Ranks are computed within each `season` group using `method='min'` for tie handling (ties get the best rank).
  - Example column names: `rank_of_week_1`, `rank_of_week_2`, ...

- `episodes_participated`
  - Description: Integer count of weeks for which the contestant has a non-missing `agg_week_{n}` value.
  - Notes: This measures how many weeks the contestant actually received judge scores in the dataset (used as a proxy for how many episodes they participated in).

## Columns added by `compute_controversial.py`

- `avg_weekly_rank`
  - Description: The mean of `rank_of_week_{n}` across all weeks for the contestant (NaNs ignored).
  - Notes: Lower is better (1 is top rank). This is used to represent the contestant's average placement by judges across the season.

- `final_rank_parsed`
  - Description: Parsed final placement extracted from `placement` or `results` columns when possible (e.g., `1` for "1st Place", `3` for "3rd Place", `3` for "Eliminated Week 3").
  - Notes: If no integer can be parsed, this value will be blank/NaN.

- `episodes_participated_parsed`
  - Description: A parsed copy of `episodes_participated` from the input CSV (if present). Kept separate so the script can operate on raw inputs that already include an episodes column.
  - Notes: This value is integer or NaN.

- `rank_difference`
  - Description: Numeric difference `avg_weekly_rank - final_rank_parsed`.
  - Interpretation: Positive -> contestant's average weekly rank is worse (higher number) than their final placement (i.e., they finished higher than expected by judges). Negative -> contestant finished lower than their judges' weekly average suggested.

## Output files (examples created during processing)

- `2026_MCM_Problem_C_Data_with_ranks.csv` — earlier run that contained aggregated weeks and rank columns.
- `2026_MCM_Problem_C_Data_preprocessed.csv` — produced by `preprocessing.py`, includes `agg_week_*`, `rank_of_week_*`, and `episodes_participated`.
- `2026_MCM_Problem_C_Data_with_controversial.csv` — produced by `compute_controversial.py`, includes `avg_weekly_rank`, `final_rank_parsed`, `episodes_participated_parsed`, and `rank_difference`.

## Important parsing & aggregation assumptions

- Columns are detected by patterns like `week{n}_judge{m}_score` (case-insensitive). If your actual column names differ, update the regex in `_group_judge_columns_by_week` in `preprocessing.py`.
- Scores <= 0 are treated as missing when aggregating judges because the dataset uses `0` to indicate "no score / absent" in many cells.
- Final ranking is parsed by extracting the first integer found in `placement` or `results` strings.
- Ranks are computed per-season; ensure the `season` column is present and correctly parsed.

If you want this documentation extended (e.g., include exact week numbers found in your file, sample rows, or a CSV schema), tell me which format you prefer and I will add it.
