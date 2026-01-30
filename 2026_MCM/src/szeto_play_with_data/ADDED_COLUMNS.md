# Added Columns (summary)

This file documents the new columns added by the preprocessing and analysis scripts in `src/szeto_play_with_data`.

## Source scripts

- `preprocessing.py` — aggregates judge scores per week, computes weekly ranks per season, and counts episodes participated.
- `compute_controversial.py` — computes summary statistics comparing average weekly ranks with final placement and exposes parsed fields for analysis.

## Columns added by `preprocessing.py`

- `agg_week_{n}`
  - Description: Aggregated judge score for week `n` (SUM of the judges' numeric scores for that week for that contestant).
  - Notes: Values <= 0 are treated as missing (NaN) during aggregation to reflect absent scores in the dataset. If all judges for a contestant-week are missing, the aggregated value is NaN (not zero).
  - Example column names: `agg_week_1`, `agg_week_2`, ...

- `rank_of_week_{n}`
  - Description: Per-season rank for week `n` computed from `agg_week_{n}`. Rank 1 is best (highest aggregated score).
  - Notes: Ranks are computed within each `season` group using `method='min'` for tie handling (ties get the best rank).
  - Example column names: `rank_of_week_1`, `rank_of_week_2`, ...

- `episodes_participated`
  - Description: Integer count of weeks for which the contestant has a non-missing `agg_week_{n}` value.
  - Notes: This measures how many weeks the contestant actually received judge scores in the dataset (used as a proxy for how many episodes they participated in).

- `var_week_{n}`
  - Description: Variance of the aggregated judge scores for week `n`, computed within each season among contestants who have a non-missing `agg_week_{n}` value.
  - Notes: Implemented as population variance (ddof=0). Each `var_week_{n}` column contains the season-specific variance for that week repeated for every row of the same season.

- `season_mean_week_variance`
  - Description: For each contestant row, the mean of that season's `var_week_{n}` across all weeks present (a seasonal average of per-week variances).

- `season_flag`
  - Description: Boolean column marking `True` if numeric `season <= 27`, `False` otherwise. Non-numeric seasons map to `False`.

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

- `avg_agg_score`
  - Description: The contestant's mean aggregated weekly score across the season (mean of `agg_week_{n}` for that row, ignoring NaNs).

- `avg_week_variance`
  - Description: The mean of per-week variances (`var_week_{n}`) for the contestant's season (same as `season_mean_week_variance` unless var_week columns are absent).

- `season_mean_week_variance`
  - Description: Same as in preprocessing — included in the controversial output and summary for convenience.

- `rank_difference`
  - Description: Numeric difference `avg_weekly_rank - final_rank_parsed`.
  - Interpretation: Positive -> contestant's average weekly rank is worse (higher number) than their final placement (i.e., they finished higher than expected by judges). Negative -> contestant finished lower than their judges' weekly average suggested.

## Behavior changes

- `compute_controversial.py` now sorts candidates by `season` (ascending numeric) and then by controversy magnitude (absolute `rank_difference`, descending), before selecting top-N or thresholded items. That makes sure the output is grouped by season and highlights the largest controversies within each season.

## Important parsing & aggregation assumptions

- Week columns are detected by patterns like `week{n}_judge{m}_score` (case-insensitive). If your actual column names differ, update the regex in `_group_judge_columns_by_week` in `preprocessing.py`.
- Scores <= 0 are treated as missing when aggregating judges because the dataset uses `0` to indicate "no score / absent" in many cells.
- If all judges for a given contestant-week are missing, `agg_week_{n}` is recorded as NaN and that week is not counted toward `episodes_participated`.
- `var_week_{n}` is computed per season using only contestants who have an `agg_week_{n}` value for that season and week.
- `season_mean_week_variance` is the mean of the season's `var_week_{n}` columns and is recorded per row for convenience.

If you want this documentation expanded (e.g., include exact week numbers detected in your file, sample rows, or a machine-readable schema), tell me which format you prefer and I will add it.
