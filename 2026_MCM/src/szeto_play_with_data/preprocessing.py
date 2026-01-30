"""
Preprocessing script (renamed from add_rank_of_week).

- Groups judge columns by week
- Computes aggregated weekly score (mean across judges)
- Computes per-season ranks `rank_of_week_{n}` from aggregated weekly scores
- Adds `episodes_participated` column = number of weeks with a non-missing aggregated score

Usage:
  py preprocessing.py input.csv --output out.csv

Returns a DataFrame and optionally writes CSV to --output.
"""
from __future__ import annotations
import sys
import argparse
from typing import Optional, List, Dict
import re

import pandas as pd
import numpy as np


def detect_result_col(df: pd.DataFrame) -> Optional[str]:
    pattern = re.compile(r"Eliminated|Place|Withdrew", flags=re.IGNORECASE)
    for col in df.columns:
        if df[col].astype(str).fillna("").str.contains(pattern).any():
            return col
    return None


def detect_season_col(df: pd.DataFrame, result_col: str) -> Optional[str]:
    cols = list(df.columns)
    idx = cols.index(result_col)
    if idx > 0:
        cand = cols[idx - 1]
        if _looks_like_season_column(df[cand]):
            return cand
    for col in cols:
        if _looks_like_season_column(df[col]):
            return col
    return None


def _looks_like_season_column(series: pd.Series) -> bool:
    s = series.dropna().astype(str).str.strip()
    nums = pd.to_numeric(s, errors="coerce")
    valid = nums.notna()
    if valid.sum() < max(3, int(0.2 * len(series))):
        return False
    vals = nums[valid]
    if vals.between(1, 100).all():
        return True
    return False


def _group_judge_columns_by_week(cols: List[str]) -> Dict[int, List[str]]:
    pattern = re.compile(r"week\s*(\d+)\s*_?\s*judge\s*\d+\s*_?\s*score", flags=re.IGNORECASE)
    groups: Dict[int, List[str]] = {}
    for col in cols:
        m = pattern.search(col)
        if m:
            week = int(m.group(1))
            groups.setdefault(week, []).append(col)
    for w in list(groups.keys()):
        groups[w] = sorted(groups[w])
    return dict(sorted(groups.items()))


def add_rank_of_week(input_csv: str, output_csv: Optional[str] = None) -> pd.DataFrame:
    """Read CSV, compute aggregated weekly scores, weekly ranks per season, and episodes participated."""
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False, na_values=["", "N/A", "NA"])
    result_col = detect_result_col(df)
    if result_col is None:
        raise ValueError("Could not detect a result column (looked for 'Eliminated', 'Place', or 'Withdrew').")
    season_col = detect_season_col(df, result_col)
    if season_col is None:
        raise ValueError("Could not detect a season column automatically.")

    cols = list(df.columns)
    start_idx = cols.index(result_col) + 1
    score_cols = cols[start_idx:]

    week_groups = _group_judge_columns_by_week(score_cols)
    if not week_groups:
        numeric_score_cols: List[str] = []
        for col in score_cols:
            coerced = pd.to_numeric(df[col].replace({np.nan: None}), errors="coerce")
            if coerced.notna().sum() > 0:
                numeric_score_cols.append(col)
        week_groups = {i + 1: [c] for i, c in enumerate(numeric_score_cols)}

    out = df.copy()
    seasons = out[season_col].astype(str).fillna("UNKNOWN").unique()
    agg_cols: List[str] = []

    for week, cols_in_week in week_groups.items():
        agg_col = f"agg_week_{week}"
        rank_col = f"rank_of_week_{week}"
        agg_cols.append(agg_col)
        judges_numeric = []
        for c in cols_in_week:
            num = pd.to_numeric(out[c], errors="coerce")
            # treat 0 or negative as missing
            num = num.where(num > 0, np.nan)
            judges_numeric.append(num)
        if not judges_numeric:
            out[agg_col] = np.nan
            out[rank_col] = np.nan
            continue
        stacked = pd.concat(judges_numeric, axis=1)
        # Aggregate by SUM of judges for the week (user requested sum instead of mean)
        # skipna=True ensures that if some judges are missing, we sum the present scores
        sums = stacked.sum(axis=1, skipna=True)
        # If all judges are missing for this row/week, stacked.sum returns 0.0 by default;
        # detect rows where no judge data is present and set aggregated value to NaN.
        has_any_judge = stacked.notna().any(axis=1)
        sums = sums.where(has_any_judge, np.nan)
        out[agg_col] = sums
        out[rank_col] = np.nan
        for season in seasons:
            mask = out[season_col].astype(str) == str(season)
            if not mask.any():
                continue
            scores = pd.to_numeric(out.loc[mask, agg_col], errors="coerce")
            if scores.notna().sum() == 0:
                continue
            ranks = scores.rank(method="min", ascending=False)
            out.loc[mask, rank_col] = ranks

    # Number of episodes participated: count of agg_week_* with non-missing value
    if agg_cols:
        out["episodes_participated"] = out[agg_cols].notna().sum(axis=1).astype(int)
    else:
        out["episodes_participated"] = 0

    # Compute per-week variance across all participants for each agg_week column
    # and add as var_week_{n} (same scalar repeated for each row)
    var_cols: List[str] = []
    # For each week, compute variance per-season among contestants who have an agg value for that week.
    for agg_col in agg_cols:
        var_col = agg_col.replace("agg_", "var_")
        var_cols.append(var_col)
        out[var_col] = np.nan
        # compute season-specific variances and write them into the var_col for rows of that season
        for season in seasons:
            season_mask = out[season_col].astype(str) == str(season)
            # among this season, consider only participants who have an aggregated score for the week
            nums = pd.to_numeric(out.loc[season_mask, agg_col], errors="coerce")
            nums = nums.dropna()
            if nums.size > 1:
                var_val = float(nums.var(ddof=0))
            else:
                var_val = float("nan")
            out.loc[season_mask, var_col] = var_val

    # Compute seasonal mean of the per-week variances (season_mean_week_variance)
    if var_cols:
        out["season_mean_week_variance"] = out[var_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    else:
        out["season_mean_week_variance"] = np.nan

    # Add season_flag column: True if season <= 27, False otherwise
    season_nums = pd.to_numeric(out[season_col], errors="coerce")
    out["season_flag"] = (season_nums <= 27).fillna(False)

    if output_csv:
        out.to_csv(output_csv, index=False)
    return out


def main(argv: List[str]) -> None:
    p = argparse.ArgumentParser(prog="preprocessing")
    p.add_argument("input_csv", help="Path to input CSV")
    p.add_argument("--output", "-o", help="Path to write output CSV (optional)")
    args = p.parse_args(argv)
    df_out = add_rank_of_week(args.input_csv, args.output)
    if not args.output:
        print("Preprocessing complete. Showing head:")
        print(df_out.head().to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1:])

