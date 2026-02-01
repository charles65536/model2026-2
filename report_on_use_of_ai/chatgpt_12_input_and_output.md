# **Input**
Our team members have completed the following work on the data:
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

I think it may not be wise to continue spending time on this data, and our team member's modeling approach has already been finalized. Should we first complete the in-depth data cleaning and then compare with our team members to select the optimal approach, or directly proceed to the core work of our writing team after aligning our dynamic documents?

# **Output**
Your intuition is correct: **it is unwise to continue spending time on "general feature engineering/general cleaning"**. Now that your core modeling approach is finalized (QP inversion for fan share + rule playback simulation + mixed effects), the optimal workflow is:

> **First align and freeze the "specifications and data contract" → immediately integrate Model V1 to complete a closed-loop run → then conduct "model-driven deep cleaning/risk diagnosis (Top-3 risks)" → finally implement visualization and writing.**

Reason: Your model essentially relies on consistent specifications for "active set/ground truth eliminations/within-week normalization (percents)/N/A weeks and post-elimination zero-score encoding"; these are explicitly problematic areas in the problem statement (N/A weeks, zero scores, no/multiple eliminations, uncertainty about the return to rank-based aggregation in Season 28).

---

## 1) Your teammate's new column processing: Usable, but **do not let it become the authoritative master data**

The columns added by your teammate's `preprocessing.py / compute_controversial.py` (`agg_week_n / rank_of_week_n / episodes_participated / avg_weekly_rank / rank_difference ...`) are **more like "analytical derived features"** that can support "controversial case screening/narrative", but they should not replace the **season–week–celebrity long panel** you have already implemented in P0 (this is the most stable interface for subsequent QP and simulation). Your modeling documentation also explicitly defines the core objects as "set of contestants still in competition that week", "total judge scores/judge percentages", "ground truth elimination set", and emphasizes that post-elimination zero scores are only used to identify exit status.

### Two "specification conflict points" that must be audited immediately

1. **Tie-handling conflict**
   Your teammate's `rank_of_week_n` uses `method='min'` (ties receive the best rank). However, your earlier P0 pseudocode and KPI specifications are closer to `average` or require explicit tie-breaking rules.
   → **Action**: Clearly define the "tie-handling rule for within-week ranking" in `kpi_registry.md` and require uniformity across all scripts (otherwise KPI1/KPI3 and subsequent rank-scheme simulations will be unstable). The modeling documentation also specifically reminds that tie-breaking rules for rank mode must be clearly written to avoid criticism.

2. **Boundary between "scores <= 0 treated as missing" and "zero scores encoding post-elimination status"**
   The problem statement clearly states: **zero scores are post-elimination encoding**, and N/A is used for "weeks not aired/missing 4th judge scores".
   Your teammate's treatment of `<=0` as missing for aggregation is a reasonable "engineering measure", but it is premised on:

* `exit_week / eliminated_at_end_of_week` is still determined by `results` or explicit specifications;
* Zero scores are not mistakenly treated as "missing due to non-participation that week", thereby contaminating the active set.

→ **Action**: Hardcode the semantics of `0 score` in the master data contract: **post-exit encoding, never an in-competition performance.** 

---

## 2) What to prioritize now: Deep cleaning vs aligning dynamic documents vs writing?

Conclusion: **First align dynamic documents (one-time, quick task), then immediately proceed to model closed-loop integration; deep cleaning is done after model integration (only for Top-3 risks), and writing can start in parallel but only focus on "structure + specification paragraphs".**

### Recommended execution sequence (most time-efficient, lowest risk of errors)

**Step 0 (30–60 min): Freeze data contract (must do first)**

* Select a "single authoritative input panel": It is recommended to continue using your P0 `intermediate_weekly_panel.csv` (season–week–celebrity long format).
* Treat your teammate's `agg_week_n / rank_of_week_n` set as a **P1 derived table** and do not merge it into the authoritative table.

**Step 1 (immediately): Integrate Model V1 to complete QP→fan_share→simulation closed loop**
The core of your modeling documentation is: use "elimination consistency constraints + smooth priors" for QP inversion of fan vote share, then replay rank/percent/ (optional bottom-two judges save), and finally conduct mixed-effects analysis of influencing factors.
The minimum inputs required for this process are: active set, judge_total, judge_percent, true_elims (handling of multiple/no eliminations required).

**Step 2 (after integration): Data Agent – Deep Cleaning (only for Top-3 model risks)**
Deep cleaning is not "creating a bunch of new columns", but conducting detection + remediation + stress testing for the 3 high-impact points that could alter conclusions, such as:

* Uncertainty of Season-28 cutoff (27/28/29 stress test)
* Implementation details of tie-handling / bottom-two judges-save (will change elimination sequence)
* Consistency of denominator and simulation handling for no-elim / multi-elim weeks

**Step 3: Visualization (generate L1/L2 after specifications stabilize)**
Otherwise, you will "create numerous visualizations only to redo them all after specification changes".

**Step 4: Writing (can start in parallel, but split into two categories)**

* Write now: **Problem framing / Data specification and encoding explanation / Overall model framework and reasons for multiple solutions** (these do not depend on final numerical results).
* Write after model runs: Result tables, case seasons, sensitivity conclusions.

---

## 3) How to update dynamic documents now (minimal and necessary)

You do not need to "rewrite a lot of documents" now. Only two tasks are required:

1. **context_pack_for_ai.md**: Add/update a section "Data contract & canonical artifacts"

* Clearly state: The authoritative panel is the long panel; the new columns added by the teammate belong to P1 derived tables; tie/0-score/N/A specifications are detailed in the registry.
  (Your context_pack currently has inconsistent conventions between "outputs/fig/tab" and "output/figure/table" in the file structure; it is recommended to unify the explanation here to avoid confusion for downstream agents.)

2. **kpi_registry.md**: Only need to add a change log + hardcode tie-handling rules

* You already have a P0/P1/P2 layered KPI table and slice/eligibility paragraphs; what needs to be added now are "implementation differences": tie handling, all-NaN week processing, and boundaries for treating <=0 as missing.

---

## 4) Your question: "When to submit the model files / when to proceed to deep cleaning and visualization?"

**Submitting now** is the most beneficial — because deep cleaning must be customized for the model's sensitive points.
You only need to upload/paste one of the following:

* Model entry script (reads weekly panel, outputs fan_share_est / simulated elimination order)
  or
* Minimal spec (input column names, output column names, QP λ/constraint form, tie-break rules)

Upon receipt, I will condense the deep cleaning phase into "3 risks × 1 detection × 1 remediation × 1 side effect × 3 stress tests", directly translating them into your L2 chart list and writing content (avoiding time wasted on general cleaning).

---

### One-sentence decision

* **First align dynamic documents and freeze the data contract (fast, high return)**
* **Then integrate Model V1 to complete closed-loop runs**
* **Next conduct model-driven deep cleaning (Top-3 risks)**
* **Finally perform visualization and result writing**

If you also paste/upload `src/szeto_play_with_data/preprocessing.py` and your current "QP/simulation entry point", I can immediately point out the **specific conflicting lines** (tie/active/0-score/N/A) with `kpi_registry` and provide a "minimal modification unified solution".