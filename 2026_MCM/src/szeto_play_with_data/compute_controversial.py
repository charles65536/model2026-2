"""
Compute controversial figures by comparing average weekly ranks with final placement.

Usage:
  py compute_controversial.py input_csv --output out.csv --top 10 --threshold 2.0

Behavior:
- Detects columns named like `rank_of_week_1`, `rank_of_week_2`, ... and computes the row-wise mean (ignoring NaNs).
- Extracts final rank from `placement` column if numeric; otherwise tries to parse a leading integer from `results` or `placement`.
- Computes difference = avg_weekly_rank - final_rank (positive means average rank is worse than final -> they finished higher than their weekly average).
- Produces a CSV with added columns and prints/saves a JSON-like summary of the most controversial figures.
"""
from __future__ import annotations
import argparse
import json
import re
from typing import List, Optional

import pandas as pd
import numpy as np


def parse_final_rank(row: pd.Series) -> Optional[float]:
    # Try placement column first
    for col in ("placement", "final_placement", "final", "place"):
        if col in row.index:
            v = row[col]
            try:
                # direct numeric
                num = float(str(v).strip())
                return num
            except Exception:
                # try to extract leading integer from strings like '2nd Place' or 'Eliminated Week 3'
                m = re.search(r"(\d+)", str(v))
                if m:
                    return float(m.group(1))
    # fallback: try results-like column
    for col in ("results", "result"):
        if col in row.index:
            v = row[col]
            m = re.search(r"(\d+)", str(v))
            if m:
                return float(m.group(1))
    return None


def _parse_episodes_participated(row: pd.Series) -> Optional[int]:
    # parse episodes_participated as integer if available
    for col in ("episodes_participated", "episodes", "weeks_participated"):
        if col in row.index:
            v = row[col]
            try:
                if v is None:
                    return None
                s = str(v).strip()
                if s == "":
                    return None
                return int(float(s))
            except Exception:
                return None
    return None


def compute_controversial(input_csv: str, output_csv: Optional[str] = None, top: int = 10, threshold: Optional[float] = None):
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False, na_values=["", "N/A", "NA"])
    # find rank_of_week columns
    rank_cols = [c for c in df.columns if re.match(r"rank_of_week_\d+$", c)]
    if not rank_cols:
        raise ValueError("No 'rank_of_week_{n}' columns found in the CSV. Run preprocessing first.")

    # convert rank columns to numeric
    ranks = df[rank_cols].apply(pd.to_numeric, errors="coerce")
    # compute average weekly rank (skip NaNs)
    df["avg_weekly_rank"] = ranks.mean(axis=1, skipna=True)

    # parse final rank
    final_ranks = []
    for _, row in df.iterrows():
        final = parse_final_rank(row)
        final_ranks.append(final)
    df["final_rank_parsed"] = pd.Series(final_ranks)

    # compute episodes_participated for transparency if present in input
    episodes = []
    for _, row in df.iterrows():
        episodes.append(_parse_episodes_participated(row))
    df["episodes_participated_parsed"] = pd.Series(episodes)

    # compute difference: avg_weekly_rank - final_rank
    df["rank_difference"] = df["avg_weekly_rank"] - df["final_rank_parsed"]

    # include season_flag if present
    if "season_flag" in df.columns:
        df["season_flag_parsed"] = df["season_flag"].astype(str)
    else:
        df["season_flag_parsed"] = "unknown"

    # compute avg aggregated score across weeks (agg_week_*)
    agg_cols = [c for c in df.columns if re.match(r"agg_week_\d+$", c)]
    if agg_cols:
        df["avg_agg_score"] = df[agg_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    else:
        df["avg_agg_score"] = np.nan

    # compute average week variance (var_week_*) if present
    var_cols = [c for c in df.columns if re.match(r"var_week_\d+$", c)]
    if var_cols:
        # var_week_* are season-specific constants per column; but we keep average across available var columns
        df["avg_week_variance"] = df[var_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
        # also add season_mean_week_variance if present
        if "season_mean_week_variance" in df.columns:
            df["season_mean_week_variance"] = pd.to_numeric(df["season_mean_week_variance"], errors="coerce")
        else:
            df["season_mean_week_variance"] = df[var_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    else:
        df["avg_week_variance"] = np.nan
        df["season_mean_week_variance"] = np.nan

    # identify controversial figures
    df_candidates = df.dropna(subset=["rank_difference"]).copy()  # only rows with a numeric difference
    df_candidates["abs_diff"] = df_candidates["rank_difference"].abs()

    # sort by season asc then controversy desc
    df_candidates["season_sort"] = pd.to_numeric(df_candidates.get("season", pd.Series("")), errors="coerce").fillna(9999)
    df_candidates = df_candidates.sort_values(by=["season_sort", "abs_diff"], ascending=[True, False])

    if threshold is not None:
        controversial = df_candidates[df_candidates["abs_diff"] >= float(threshold)].copy()
        controversial = controversial.sort_values(by="abs_diff", ascending=False)
    else:
        controversial = df_candidates.head(top)

    # build summary list including episodes_participated
    summary: List[dict] = []
    for _, r in controversial.iterrows():
        name = r.get("celebrity_name") or r.get("name") or "<unknown>"
        season = r.get("season")
        avg_rank = r.get("avg_weekly_rank")
        final_rank = r.get("final_rank_parsed")
        diff = r.get("rank_difference")
        episodes_part = r.get("episodes_participated_parsed")
        season_flag = r.get("season_flag_parsed")
        avg_agg = r.get("avg_agg_score")
        avg_var = r.get("avg_week_variance")
        season_var_mean = r.get("season_mean_week_variance")
        reason = ""
        if pd.isna(avg_rank) or pd.isna(final_rank):
            reason = "missing data"
        else:
            if diff > 0:
                reason = "finished higher (better) than their weekly average"
            elif diff < 0:
                reason = "finished lower (worse) than their weekly average"
            else:
                reason = "no difference"
        rec = {
            "celebrity_name": name,
            "season": season,
            "episodes_participated": None if pd.isna(episodes_part) else int(episodes_part),
            "season_flag": season_flag,
            "avg_agg_score": None if pd.isna(avg_agg) else float(avg_agg),
            "avg_week_variance": None if pd.isna(avg_var) else float(avg_var),
            "season_mean_week_variance": None if pd.isna(season_var_mean) else float(season_var_mean),
            "avg_weekly_rank": None if pd.isna(avg_rank) else float(avg_rank),
            "final_rank": None if pd.isna(final_rank) else float(final_rank),
            "difference": None if pd.isna(diff) else float(diff),
            "abs_difference": None if pd.isna(diff) else float(abs(diff)),
            "note": reason,
        }
        # attach per-week variances for visibility if present
        for vc in var_cols:
            rec[vc] = None if pd.isna(r.get(vc)) else float(r.get(vc))
        summary.append(rec)

    # optionally write output CSV with added columns
    if output_csv:
        df.to_csv(output_csv, index=False)

    # print a concise summary including episodes
    print("Controversial figures summary (top):")
    for item in summary:
        ep = item.get("episodes_participated")
        ep_str = "unknown" if ep is None else str(ep)
        sf = item.get("season_flag")
        avgagg = item.get("avg_agg_score")
        avgv = item.get("avg_week_variance")
        smeanvar = item.get("season_mean_week_variance")
        print(f"- {item['celebrity_name']} (Season {item['season']} | episodes_participated={ep_str} | season_flag={sf}): avg_rank={item['avg_weekly_rank']}, final={item['final_rank']}, diff={item['difference']:.2f} -> {item['note']}")
        print(f"    avg_agg_score={avgagg}, avg_week_variance={avgv}, season_mean_week_variance={smeanvar}")
        # print per-week variances compactly
        for vc in var_cols[:6]:
            if vc in item:
                print(f"    {vc}={item.get(vc)}", end='')
        print()

    # also return the dataframe and summary for programmatic use
    return df, summary


def main(argv: List[str]):
    p = argparse.ArgumentParser(prog="compute_controversial")
    p.add_argument("input_csv", help="CSV file with rank_of_week_* columns")
    p.add_argument("--output", "-o", help="Optional CSV to write with added columns")
    p.add_argument("--top", type=int, default=10, help="Number of top controversial figures to show (default 10)")
    p.add_argument("--threshold", type=float, default=None, help="Absolute difference threshold to select controversial figures (overrides --top)")
    args = p.parse_args(argv)

    compute_controversial(args.input_csv, args.output, top=args.top, threshold=args.threshold)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
