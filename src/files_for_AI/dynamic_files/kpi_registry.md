# KPI Registry (Dynamic, Authoritative)

**Version:** v0.1  
**Updated:** 2026-1-30 8:00  
**Owner:** Jincan LI

> Single source of truth for KPI definitions and slices. If conflict exists, **this file wins**.

## KPI table
| KPI name | Status | Direction | Definition (operational) | Aggregation | Slice/window | Baseline(s) | Dependencies / Notes |
|---|---|---|---|---|---|---|---|
| **KPI1 Elimination Hit-Rate (Rank scheme)** | **P0** | higher is better | For each eligible (season, week), compute the predicted eliminated set under **rank-combination** and compare to the true eliminated-at-end-of-week set (from `results`). Multi-elim weeks evaluated by set-match (bottom-k). | Mean over eligible (season, week) | Era: Rank-era seasons {1,2,28–34} (**Season-28 is an assumption; stress-test 27/28/29**). Eligibility rules per Slice/window definitions. | **BL-0:** judge-rank only (uniform fan rank adds constant) | Uses weekly total judge scores from `weekX_judgeY_score`. Withdrawals treated per “Special exit handling”. |
| **KPI1 Elimination Hit-Rate (Percent scheme)** | **P0** | higher is better | For each eligible (season, week), compute the predicted eliminated set under **percent-combination** (judge percent + fan percent proxy/model) and compare to true eliminated set (from `results`). | Mean over eligible (season, week) | Era: Percent-era seasons {3–27}. Eligibility rules per Slice/window definitions. | **BL-0:** judge_percent + uniform fan_percent (1/n_active) | Fan votes are unobserved; BL-0 is a reproducible proxy for P0. |
| **KPI3 Rule Divergence Rate (Rank vs Percent)** | **P0** | **descriptive (no “better”)** | Share of eligible (season, week) where the predicted eliminated set differs between rank vs percent schemes (holding the same baseline/proxy vote input). | Ratio over eligible (season, week) | Same eligibility; can be grouped by season / era. | **BL-0 only** | Report as “impact magnitude” rather than optimization target. |
| **KPI2 Vote Identifiability (interval tightness)** | **P1** | higher is better | For each (season, week, celebrity), derive a feasible interval of fan vote (share or rank) consistent with observed elimination outcome under a specified rule; define identifiability as `1/(interval_width + ε)` and summarize. | Median (or quantiles) over (celebrity, week), then aggregated by season/phase | Season; phase (early/mid/late); “controversial” weeks (close judge totals) | Not defined in P0 | **Requires**: (i) explicit mathematical form of rule & elimination mechanism (incl. bottom-two judges save if used), (ii) definition of vote variable (share vs rank), (iii) choice of ε. Until these are fixed, KPI2 is registry-only. |
| **Constraint KPI1 Fan Agency Floor** | **P1** | higher is better | Under replay, enforce that “fan top-1 (or top-x%) still eliminated” rate is below a chosen threshold, or equivalently maximize a fan-retention lower bound. | Ratio over eligible (season, week) | By rule variant; season phase | Not defined in P0 | **Requires**: fan vote estimate (`fan_rank_est` or `fan_share_est`) and a defined x% / threshold. In P0, keep interface only; do not claim numeric compliance. |
| **Constraint KPI2 Rule Simplicity** | **P2** | lower is better | Complexity score = (# tunable hyperparameters) + external-info dependency flag (0/1). | Per rule variant (not data-aggregated) | By rule variant | N/A | This is a **policy/implementability** metric, not computed from the CSV; used in memo/decision section, not in data cleaning. |

## Slice/window definitions

- Unit of analysis: (season, week, celebrity) after reshaping `weekX_judgeY_score` wide columns into a long panel.
- Active set definition: a celebrity is active in a (season, week) iff week scores are not all-NaN and week is not after the exit week (Eliminated Week k / inferred withdraw week).
- Era slices for voting-scheme comparison:
  - Rank-era: seasons {1,2,28–34} (**Season-28 is an assumption; stress-test 27/28/29 cutoffs**).
  - Percent-era: seasons {3–27}.
- Weeks with no elimination or multiple eliminations: excluded from single-elimination consistency denominators; multi-elim weeks evaluated by set-match when needed.
- Special exit handling (deterministic):
  - If `results == "Withdrew"`, define `exit_week` as the last week with non-missing judge scores (or `total_judge_score > 0`); weeks after `exit_week` are excluded from the active set and KPI denominators.
  - Withdrawals are not counted as “true eliminations” in elimination-consistency KPIs by default; they are reported separately as `exit_type="withdrew"` for sensitivity analysis.


## Baseline definitions

- BL-0 (Reproducible, minimal): "Judge-only proxy"
  - Rank scheme: use `judge_rank` only (uniform fan ranks add a constant to all contestants).
  - Percent scheme: use `judge_percent + 1/n_active` (uniform fan percent), so elimination is driven by judges with a fixed fan offset.
  - Purpose: provides a fully reproducible reference point before introducing any fan-vote estimation model.

## Change log

- v0.1 (2026-01-30): Initialized triage-ready KPI definitions, eligibility rules, and BL-0 baseline; marked Season-28 rank-era switch as an explicit assumption requiring stress tests.

- v0.1.1 (2026-01-30): P0 implementation anchor — canonical artifacts fixed to `output/table/intermediate_weekly_panel.csv`, `output/table/intermediate_baseline_preds.csv`, and `output/table/tab_baseline_consistency.tex`; structural missing weeks (all judges NaN) are retained for auditability but excluded from all KPI denominators via `active=False`; within-week `judge_rank` uses average-tie handling by default (tie method will be stress-tested as a robustness variant).
