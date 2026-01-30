#!/usr/bin/env python3
"""
P0 Triage: Build weekly panel (season-week-celebrity) from official DWTS dataset,
and compute BL-0 baseline elimination predictions + consistency KPIs.

Authoritative definitions:
- dynamic_files/data_agent_triage_ticket.md
- dynamic_files/kpi_registry.md

Outputs (relative to --outdir):
- table/intermediate_weekly_panel.csv
- table/intermediate_baseline_preds.csv
- table/tab_baseline_consistency.tex
- figure/fig_fliprate_by_season.pdf
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

WEEK_JUDGE_RE = re.compile(r"week(\d+)_judge(\d+)_score$")

def parse_elim_week(results: str) -> int | None:
    m = re.match(r"Eliminated Week (\d+)", str(results))
    return int(m.group(1)) if m else None

def build_weekly_panel(df: pd.DataFrame) -> pd.DataFrame:
    # Identify week/judge columns
    week_judge_cols = []
    for c in df.columns:
        m = WEEK_JUDGE_RE.match(c)
        if m:
            week_judge_cols.append((int(m.group(1)), int(m.group(2)), c))
    if not week_judge_cols:
        raise ValueError("No weekX_judgeY_score columns found.")
    max_week = max(w for w,_,_ in week_judge_cols)
    max_judge = max(j for _,j,_ in week_judge_cols)

    id_cols = ["season","celebrity_name","ballroom_partner","results","placement"]
    base = df[id_cols].copy()

    long_rows = []
    for week in range(1, max_week+1):
        r = base.copy()
        r["week"] = week
        for judge in range(1, max_judge+1):
            col = f"week{week}_judge{judge}_score"
            r[f"judge{judge}_score"] = df[col] if col in df.columns else np.nan
        long_rows.append(r)
    panel = pd.concat(long_rows, ignore_index=True)

    judge_cols = [f"judge{j}_score" for j in range(1, max_judge+1)]
    panel["all_judges_nan"] = panel[judge_cols].isna().all(axis=1)
    panel["total_judge_score"] = panel[judge_cols].sum(axis=1, skipna=True)

    # Exit mapping
    exit_map = df[["season","celebrity_name","results"]].copy()
    exit_map["elim_week"] = exit_map["results"].apply(parse_elim_week)
    exit_map["exit_type"] = np.where(exit_map["results"].eq("Withdrew"), "withdrew",
                            np.where(exit_map["elim_week"].notna(), "eliminated", "finished"))

    key = panel[["season","celebrity_name","week","all_judges_nan","total_judge_score"]].copy()
    valid_nonmissing = key[~key["all_judges_nan"]]
    last_nonmissing = valid_nonmissing.groupby(["season","celebrity_name"])["week"].max().rename("last_nonmissing_week")

    valid_positive = key[(~key["all_judges_nan"]) & (key["total_judge_score"] > 0)]
    last_positive = valid_positive.groupby(["season","celebrity_name"])["week"].max().rename("last_positive_week")

    exit_map = exit_map.merge(last_nonmissing.reset_index(), on=["season","celebrity_name"], how="left") \
                     .merge(last_positive.reset_index(), on=["season","celebrity_name"], how="left")

    def infer_exit_week(row) -> float:
        if pd.notna(row["elim_week"]):
            return float(row["elim_week"])
        # withdrew or finished: last positive preferred; fallback last non-missing
        if pd.notna(row["last_positive_week"]):
            return float(row["last_positive_week"])
        return float(row["last_nonmissing_week"]) if pd.notna(row["last_nonmissing_week"]) else np.nan

    exit_map["exit_week"] = exit_map.apply(infer_exit_week, axis=1)
    exit_map = exit_map[["season","celebrity_name","exit_type","exit_week","elim_week"]]

    panel = panel.merge(exit_map, on=["season","celebrity_name"], how="left")
    panel["is_elim_exit_week"] = (panel["elim_week"].notna()) & (panel["week"] == panel["elim_week"])
    panel["true_elim_flag"] = panel["is_elim_exit_week"].astype(int)  # withdrawals excluded by default

    # Active definition
    panel["active"] = (~panel["all_judges_nan"]) & (panel["week"] <= panel["exit_week"].fillna(-1))
    panel["data_anomaly_zero_score"] = (panel["total_judge_score"].eq(0) & (~panel["all_judges_nan"]) &
                                       (panel["week"] != panel["exit_week"]))
    panel.loc[panel["data_anomaly_zero_score"], "active"] = False

    # Within-week rank/percent among active
    panel["judge_rank"] = np.nan
    panel["judge_percent"] = np.nan

    def rank_desc(s: pd.Series) -> pd.Series:
        # higher score -> better rank (1 is best)
        return s.rank(method="average", ascending=False)

    for (season, week), g in panel.groupby(["season","week"], sort=False):
        g_active = g[g["active"]]
        if len(g_active) == 0:
            continue
        scores = g_active["total_judge_score"].astype(float)
        panel.loc[g_active.index, "judge_rank"] = rank_desc(scores).values
        denom = scores.sum()
        if denom > 0:
            panel.loc[g_active.index, "judge_percent"] = (scores / denom).values
    panel = panel[~panel["all_judges_nan"]].copy()
    return panel

def compute_baseline(panel: pd.DataFrame) -> pd.DataFrame:
    # true elimination sets among active
    true_elims = panel[(panel["active"]) & (panel["true_elim_flag"] == 1)].groupby(["season","week"])["celebrity_name"].apply(list)
    true_counts = true_elims.apply(len)

    pred_rows = []
    for (season, week), g in panel.groupby(["season","week"], sort=False):
        g_active = g[g["active"]].copy()
        n_active = len(g_active)
        if n_active == 0:
            continue

        true_set = true_elims.get((season, week), [])
        k = int(true_counts.get((season, week), 0))
        eligible = k > 0

        if eligible:
            fan_uniform = 1.0 / n_active
            combined_percent = g_active["judge_percent"].astype(float) + fan_uniform
            pred_percent = g_active.loc[combined_percent.nsmallest(k).index, "celebrity_name"].tolist()
            pred_rank = g_active.sort_values("judge_rank", ascending=False).head(k)["celebrity_name"].tolist()

            match_percent = set(pred_percent) == set(true_set)
            match_rank = set(pred_rank) == set(true_set)
            flip = set(pred_percent) != set(pred_rank)
        else:
            pred_percent = []
            pred_rank = []
            match_percent = np.nan
            match_rank = np.nan
            flip = np.nan

        pred_rows.append({
            "season": season,
            "week": week,
            "n_active": n_active,
            "true_k": k,
            "true_elims": ";".join(true_set),
            "pred_elim_percent": ";".join(pred_percent),
            "pred_elim_rank": ";".join(pred_rank),
            "match_percent": match_percent,
            "match_rank": match_rank,
            "flip": flip,
            "eligible": eligible
        })
    return pd.DataFrame(pred_rows)

def write_latex_table(summary: pd.DataFrame, out_path: Path) -> None:
    def fmt(x):
        if pd.isna(x): return ""
        if isinstance(x, (float, np.floating)):
            return f"{x:.3f}"
        return str(x)
    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\hline",
        r"Slice & $N_{\mathrm{weeks}}$ & Hit-Rate (Rank) & Hit-Rate (Percent) & FlipRate \\",
        r"\hline",
    ]
    for _, r in summary.iterrows():
        lines.append(f"{r['slice']} & {int(r['n_weeks'])} & {fmt(r['ElimMatchRate_rank'])} & {fmt(r['ElimMatchRate_percent'])} & {fmt(r['FlipRate'])} \\\\")
    lines += [r"\hline", r"\end{tabular}"]
    out_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to 2026_MCM_Problem_C_Data.csv")
    ap.add_argument("--outdir", required=True, help="Output dir (will create table/ and figure/ under it)")
    args = ap.parse_args()

    inp = Path(args.input)
    outdir = Path(args.outdir)
    tab_dir  = outdir / "tab"
    fig_dir  = outdir / "fig"
    data_dir = outdir / "data_cleaned"

    tab_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)


    df = pd.read_csv(inp)
    panel = build_weekly_panel(df)
    preds = compute_baseline(panel)

    # Era slicing per KPI registry
    rank_era = set([1,2] + list(range(28,35)))
    percent_era = set(range(3,28))
    preds["era"] = np.where(preds["season"].isin(rank_era), "rank-era",
                   np.where(preds["season"].isin(percent_era), "percent-era", "other"))

    eligible = preds[preds["eligible"]].copy()

    def agg(d: pd.DataFrame) -> pd.Series:
        return pd.Series({
            "n_weeks": len(d),
            "ElimMatchRate_rank": d["match_rank"].mean(),
            "ElimMatchRate_percent": d["match_percent"].mean(),
            "FlipRate": d["flip"].mean(),
        })

    summary = pd.concat([
        agg(eligible).to_frame().T.assign(slice="Overall"),
        agg(eligible[eligible["era"]=="rank-era"]).to_frame().T.assign(slice="Rank-era (S1-2,28-34)"),
        agg(eligible[eligible["era"]=="percent-era"]).to_frame().T.assign(slice="Percent-era (S3-27)"),
    ], ignore_index=True)

    # Save outputs
    panel_cols = [
        "season","week","celebrity_name","ballroom_partner","results","placement",
        "judge1_score","judge2_score","judge3_score","judge4_score",
        "total_judge_score","judge_rank","judge_percent",
        "active","true_elim_flag","exit_type","exit_week","data_anomaly_zero_score"
    ]
    panel.to_csv(tab_dir / "intermediate_weekly_panel.csv", index=False, columns=panel_cols)
    preds.to_csv(tab_dir / "intermediate_baseline_preds.csv", index=False)
    write_latex_table(summary, tab_dir / "tab_baseline_consistency.tex")

    # L2 figure: flip rate by season (eligible weeks only)
    flip_by_season = eligible.groupby("season")["flip"].mean().reset_index().sort_values("season")
    plt.figure()
    plt.plot(flip_by_season["season"], flip_by_season["flip"], marker="o")
    plt.xlabel("Season")
    plt.ylabel("FlipRate (Rank vs Percent)")
    plt.title("Rule divergence (FlipRate) varies by season under BL-0")
    plt.tight_layout()
    plt.savefig(fig_dir / "fig_fliprate_by_season.pdf")
    plt.close()

if __name__ == "__main__":
    main()
