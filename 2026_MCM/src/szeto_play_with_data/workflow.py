"""
Unified workflow script combining preprocessing, variance fixing, debugging, controversial computation, and demo printing.

Usage examples:
  py workflow.py preprocess input.csv --output preprocessed.csv
  py workflow.py fix-variances --input preprocessed.csv --output preprocessed_fixed.csv
  py workflow.py compute-controversial preprocessed_fixed.csv --output controversial.csv --top 20
  py workflow.py debug-variance-check --input preprocessed.csv
  py workflow.py demo --input controversial.csv --top 12

This consolidates the logic previously spread across multiple scripts into one file with subcommands.
"""
from __future__ import annotations
import argparse
import math
import os
import re
import sys
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def detect_result_col(df: pd.DataFrame) -> Optional[str]:
    pattern = re.compile(r"Eliminated|Place|Withdrew", flags=re.IGNORECASE)
    for col in df.columns:
        try:
            if df[col].astype(str).fillna("").str.contains(pattern).any():
                return col
        except Exception:
            continue
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


def detect_season_col(df: pd.DataFrame, result_col: str) -> Optional[str]:
    cols = list(df.columns)
    if result_col in cols:
        idx = cols.index(result_col)
        if idx > 0:
            cand = cols[idx - 1]
            if _looks_like_season_column(df[cand]):
                return cand
    for col in cols:
        if _looks_like_season_column(df[col]):
            return col
    return None


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


def preprocess(input_csv: str, output_csv: Optional[str] = None) -> pd.DataFrame:
    """Perform aggregation per-week (SUM of judges), per-season ranks, episodes_participated,
    per-season per-week variance (var_week_{n}), season_mean_week_variance, and season_flag."""
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
            num = num.where(num > 0, np.nan)
            judges_numeric.append(num)
        if not judges_numeric:
            out[agg_col] = np.nan
            out[rank_col] = np.nan
            continue
        stacked = pd.concat(judges_numeric, axis=1)
        sums = stacked.sum(axis=1, skipna=True)
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

    if agg_cols:
        out["episodes_participated"] = out[agg_cols].notna().sum(axis=1).astype(int)
    else:
        out["episodes_participated"] = 0

    # Compute per-season per-week variance
    var_cols: List[str] = []
    for agg_col in agg_cols:
        var_col = agg_col.replace("agg_", "var_")
        var_cols.append(var_col)
        out[var_col] = np.nan
        for season in seasons:
            season_mask = out[season_col].astype(str) == str(season)
            nums = pd.to_numeric(out.loc[season_mask, agg_col], errors="coerce").dropna()
            if nums.size > 1:
                var_val = float(nums.var(ddof=0))
            else:
                var_val = float("nan")
            out.loc[season_mask, var_col] = var_val

    if var_cols:
        out["season_mean_week_variance"] = out[var_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    else:
        out["season_mean_week_variance"] = np.nan

    season_nums = pd.to_numeric(out[season_col], errors="coerce")
    out["season_flag"] = (season_nums <= 27).fillna(False)

    if output_csv:
        out.to_csv(output_csv, index=False)
    return out


def fix_variances(input_csv: str, output_csv: Optional[str] = None) -> pd.DataFrame:
    df = pd.read_csv(input_csv, dtype=str)
    agg_cols = [c for c in df.columns if c.startswith('agg_week_')]
    var_cols = [c for c in df.columns if c.startswith('var_week_')]
    if not agg_cols:
        raise RuntimeError('No agg_week_* columns found in input')
    if not var_cols:
        var_cols = [c.replace('agg_', 'var_') for c in agg_cols]
        for vc in var_cols:
            df[vc] = np.nan

    for c in agg_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    seasons = sorted(df['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.','',1).isdigit() else 9999)
    for agg_col, var_col in zip(agg_cols, var_cols):
        df[var_col] = np.nan
        for season in seasons:
            mask = df['season'] == season
            nums = df.loc[mask, agg_col].dropna().astype(float)
            if nums.size > 1:
                var_val = float(nums.var(ddof=0))
            else:
                var_val = float('nan')
            df.loc[mask, var_col] = var_val

    df['season_mean_week_variance'] = df[var_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1, skipna=True)

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df


def debug_variance_check(input_csv: str, max_print: int = 50, tol: float = 1e-6):
    df = pd.read_csv(input_csv, dtype=str)
    agg_cols = [c for c in df.columns if c.startswith('agg_week_')]
    var_cols = [c for c in df.columns if c.startswith('var_week_')]
    print(f"Found {len(agg_cols)} agg cols and {len(var_cols)} var cols")
    print('agg_cols:', agg_cols)
    print('var_cols:', var_cols)
    seasons = sorted(df['season'].dropna().unique(), key=lambda x: float(x) if str(x).replace('.','',1).isdigit() else 9999)
    print('seasons (sample up to 20):', seasons[:20])
    print()

    # global uniqueness
    print('Recorded var_week unique values (global):')
    for vc in var_cols:
        uniq = pd.to_numeric(df[vc], errors='coerce').dropna().unique()
        print(f'  {vc}: unique_count={len(uniq)} sample={uniq[:5].tolist()}')
    print()

    mismatches = []
    const_vars = []
    for agg_col, var_col in zip(agg_cols, var_cols):
        per_season_vals = {}
        for season in seasons:
            mask = df['season'] == season
            nums = pd.to_numeric(df.loc[mask, agg_col], errors='coerce').dropna().astype(float)
            calc = float(nums.var(ddof=0)) if nums.size > 1 else float('nan')
            per_season_vals[season] = calc
        rec_vals_by_season = {}
        for season in seasons:
            mask = df['season'] == season
            recs = pd.to_numeric(df.loc[mask, var_col], errors='coerce')
            rec_unique = recs.dropna().unique()
            rec = float(rec_unique[0]) if len(rec_unique) > 0 else float('nan')
            rec_vals_by_season[season] = rec
        rec_all = [v for v in rec_vals_by_season.values() if not math.isnan(v)]
        if len(set([round(float(x), 8) for x in rec_all])) <= 1 and len(rec_all) > 0:
            const_vars.append((var_col, rec_all[0]))
        for season in seasons:
            calc = per_season_vals.get(season, float('nan'))
            rec = rec_vals_by_season.get(season, float('nan'))
            if math.isnan(calc) and math.isnan(rec):
                continue
            if math.isnan(calc) != math.isnan(rec):
                mismatches.append((season, agg_col, var_col, calc, rec))
            else:
                if abs(calc - rec) > tol:
                    mismatches.append((season, agg_col, var_col, calc, rec))

    print(f'Total mismatches found: {len(mismatches)}')
    if mismatches:
        print('Sample mismatches:')
        for item in mismatches[:max_print]:
            season, agg_col, var_col, calc, rec = item
            print(f'  season={season} | {agg_col} calc_var={calc} | {var_col} rec_var={rec}')
    else:
        print('No mismatches found between computed per-season var and recorded var_week_* columns.')
    print()
    if const_vars:
        print('var_week columns that are constant across seasons (possible bug):')
        for vc, val in const_vars:
            print(f'  {vc} = {val}')
    else:
        print('No var_week columns are constant across seasons.')


def parse_final_rank(row: pd.Series) -> Optional[float]:
    for col in ("placement", "final_placement", "final", "place"):
        if col in row.index:
            v = row[col]
            try:
                num = float(str(v).strip())
                return num
            except Exception:
                m = re.search(r"(\d+)", str(v))
                if m:
                    return float(m.group(1))
    for col in ("results", "result"):
        if col in row.index:
            v = row[col]
            m = re.search(r"(\d+)", str(v))
            if m:
                return float(m.group(1))
    return None


def compute_controversial(input_csv: str, output_csv: Optional[str] = None, top: int = 10, threshold: Optional[float] = None):
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False, na_values=["", "N/A", "NA"])
    rank_cols = [c for c in df.columns if re.match(r"rank_of_week_\d+$", c)]
    if not rank_cols:
        raise ValueError("No 'rank_of_week_{n}' columns found in the CSV. Run preprocessing first.")
    ranks = df[rank_cols].apply(pd.to_numeric, errors='coerce')
    df['avg_weekly_rank'] = ranks.mean(axis=1, skipna=True)
    final_ranks = []
    for _, row in df.iterrows():
        final_ranks.append(parse_final_rank(row))
    df['final_rank_parsed'] = pd.Series(final_ranks)
    episodes = []
    for _, row in df.iterrows():
        episodes.append(_parse_episodes_participated(row))
    df['episodes_participated_parsed'] = pd.Series(episodes)
    df['rank_difference'] = df['avg_weekly_rank'] - df['final_rank_parsed']
    if 'season_flag' in df.columns:
        df['season_flag_parsed'] = df['season_flag'].astype(str)
    else:
        df['season_flag_parsed'] = 'unknown'
    agg_cols = [c for c in df.columns if re.match(r"agg_week_\d+$", c)]
    if agg_cols:
        df['avg_agg_score'] = df[agg_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1, skipna=True)
    else:
        df['avg_agg_score'] = np.nan
    var_cols = [c for c in df.columns if re.match(r"var_week_\d+$", c)]
    if var_cols:
        df['avg_week_variance'] = df[var_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1, skipna=True)
        if 'season_mean_week_variance' in df.columns:
            df['season_mean_week_variance'] = pd.to_numeric(df['season_mean_week_variance'], errors='coerce')
        else:
            df['season_mean_week_variance'] = df[var_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1, skipna=True)
    else:
        df['avg_week_variance'] = np.nan
        df['season_mean_week_variance'] = np.nan
    df_candidates = df.dropna(subset=['rank_difference']).copy()
    df_candidates['abs_diff'] = df_candidates['rank_difference'].abs()
    df_candidates['season_sort'] = pd.to_numeric(df_candidates.get('season', pd.Series('')), errors='coerce').fillna(9999)
    df_candidates = df_candidates.sort_values(by=['season_sort', 'abs_diff'], ascending=[True, False])
    if threshold is not None:
        controversial = df_candidates[df_candidates['abs_diff'] >= float(threshold)].copy()
        controversial = controversial.sort_values(by='abs_diff', ascending=False)
    else:
        controversial = df_candidates.head(top)
    # attach per-week variances to summary
    summary = []
    for _, r in controversial.iterrows():
        name = r.get('celebrity_name') or r.get('name') or '<unknown>'
        season = r.get('season')
        avg_rank = r.get('avg_weekly_rank')
        final_rank = r.get('final_rank_parsed')
        diff = r.get('rank_difference')
        episodes_part = r.get('episodes_participated_parsed')
        season_flag = r.get('season_flag_parsed')
        avg_agg = r.get('avg_agg_score')
        avg_var = r.get('avg_week_variance')
        season_var_mean = r.get('season_mean_week_variance')
        reason = ''
        if pd.isna(avg_rank) or pd.isna(final_rank):
            reason = 'missing data'
        else:
            if diff > 0:
                reason = 'finished higher (better) than their weekly average'
            elif diff < 0:
                reason = 'finished lower (worse) than their weekly average'
            else:
                reason = 'no difference'
        rec = {
            'celebrity_name': name,
            'season': season,
            'episodes_participated': None if pd.isna(episodes_part) else int(episodes_part),
            'season_flag': season_flag,
            'avg_agg_score': None if pd.isna(avg_agg) else float(avg_agg),
            'avg_week_variance': None if pd.isna(avg_var) else float(avg_var),
            'season_mean_week_variance': None if pd.isna(season_var_mean) else float(season_var_mean),
            'avg_weekly_rank': None if pd.isna(avg_rank) else float(avg_rank),
            'final_rank': None if pd.isna(final_rank) else float(final_rank),
            'difference': None if pd.isna(diff) else float(diff),
            'abs_difference': None if pd.isna(diff) else float(abs(diff)),
            'note': reason,
        }
        for vc in var_cols:
            rec[vc] = None if pd.isna(r.get(vc)) else float(r.get(vc))
        summary.append(rec)
    if output_csv:
        df.to_csv(output_csv, index=False)
    print('Controversial figures summary (top):')
    for item in summary:
        ep = item.get('episodes_participated')
        ep_str = 'unknown' if ep is None else str(ep)
        sf = item.get('season_flag')
        avgagg = item.get('avg_agg_score')
        avgv = item.get('avg_week_variance')
        smeanvar = item.get('season_mean_week_variance')
        print(f"- {item['celebrity_name']} (Season {item['season']} | episodes_participated={ep_str} | season_flag={sf}): avg_rank={item['avg_weekly_rank']}, final={item['final_rank']}, diff={item['difference']:.2f} -> {item['note']}")
        print(f"    avg_agg_score={avgagg}, avg_week_variance={avgv}, season_mean_week_variance={smeanvar}")
        for vc in var_cols[:6]:
            if vc in item:
                print(f"    {vc}={item.get(vc)}", end='')
        print()
    return df, summary


def _parse_episodes_participated(row: pd.Series) -> Optional[int]:
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


def demo(input_csv: Optional[str] = None, top: int = 12):
    default_paths = [
        "C:/Users/Administrator/PycharmProjects/model2026-2/2026_MCM/src/szeto_play_with_data/2026_MCM_Problem_C_Data_with_controversial_fixed.csv",
        "C:/Users/Administrator/PycharmProjects/model2026-2/2026_MCM/src/szeto_play_with_data/2026_MCM_Problem_C_Data_with_controversial.csv",
    ]
    input_path = input_csv
    if not input_path:
        for cand in default_paths:
            if os.path.exists(cand):
                input_path = cand
                break
    if not input_path or not os.path.exists(input_path):
        raise FileNotFoundError("Could not find input CSV for demo. Provide --input or place the file in the default location.")
    df = pd.read_csv(input_path, dtype=str)
    numcols = ['rank_difference', 'avg_weekly_rank', 'final_rank_parsed', 'avg_agg_score', 'season_mean_week_variance', 'episodes_participated']
    for c in numcols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    if 'rank_difference' not in df.columns:
        raise RuntimeError("Input CSV doesn't contain 'rank_difference' column. Run compute_controversial first.")
    df = df.dropna(subset=['rank_difference']).copy()
    df['abs_diff'] = df['rank_difference'].abs()
    df['season_n'] = pd.to_numeric(df.get('season', pd.Series([None] * len(df))), errors='coerce').fillna(9999)
    df_sorted = df.sort_values(by=['season_n', 'abs_diff'], ascending=[True, False])
    df_top = df_sorted.head(top)
    base_cols = ['celebrity_name', 'season', 'episodes_participated', 'season_flag', 'avg_weekly_rank', 'final_rank_parsed', 'rank_difference', 'avg_agg_score', 'season_mean_week_variance']
    var_cols = [c for c in df.columns if c.startswith('var_week_')]
    var_cols = sorted(var_cols, key=lambda x: int(x.split('_')[-1]))[:6]
    show_cols = [c for c in base_cols if c in df.columns]
    show_cols += [c for c in var_cols if c in df.columns]
    print(f"Using input: {input_path}")
    print(f"Showing top {top} controversial figures (sorted by season asc, controversy desc)")
    print()
    print(df_top[show_cols].to_string(index=False))


def main(argv: List[str] | None = None):
    p = argparse.ArgumentParser(prog='workflow')
    sub = p.add_subparsers(dest='cmd')

    sp = sub.add_parser('preprocess')
    sp.add_argument('input')
    sp.add_argument('--output', '-o')

    sp2 = sub.add_parser('fix-variances')
    sp2.add_argument('--input', '-i', required=True)
    sp2.add_argument('--output', '-o')

    sp3 = sub.add_parser('debug-variance-check')
    sp3.add_argument('--input', '-i', required=True)
    sp3.add_argument('--max-print', type=int, default=50)

    sp4 = sub.add_parser('compute-controversial')
    sp4.add_argument('input')
    sp4.add_argument('--output', '-o')
    sp4.add_argument('--top', type=int, default=10)
    sp4.add_argument('--threshold', type=float, default=None)

    sp5 = sub.add_parser('demo')
    sp5.add_argument('--input', '-i')
    sp5.add_argument('--top', '-n', type=int, default=12)

    args = p.parse_args(argv)
    if args.cmd == 'preprocess':
        preprocess(args.input, args.output)
    elif args.cmd == 'fix-variances':
        fix_variances(args.input, args.output)
    elif args.cmd == 'debug-variance-check':
        debug_variance_check(args.input, max_print=args.max_print)
    elif args.cmd == 'compute-controversial':
        compute_controversial(args.input, args.output, top=args.top, threshold=args.threshold)
    elif args.cmd == 'demo':
        demo(args.input, top=args.top)
    else:
        p.print_help()


if __name__ == '__main__':
    main(sys.argv[1:])
