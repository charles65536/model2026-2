# **Input**
I just completed Step 4) and the relevant text is as follows:
## Slice/Window Definitions
- Unit of analysis: (season, week, celebrity) following the reshaping of wide columns named `weekX_judgeY_score` into a long panel dataset.
- Active set definition: A celebrity is classified as active in a given (season, week) if and only if their weekly scores are not all NaN, and the week falls before or in their exit week (Eliminated Week k / inferred withdrawal week).
- Era slices for voting-scheme comparison:
  - Rank-era: seasons {1,2,28–34} (**Season 28 is an assumed cutoff; stress-test analyses to be conducted for 27/28/29 cutoffs**).
  - Percent-era: seasons {3–27}.
- Weeks with no eliminations or multiple eliminations: Excluded from the denominator of single-elimination consistency metrics; weeks with multiple eliminations are assessed via set matching where necessary.
- Special exit handling (deterministic):
  - If `results == "Withdrew"`, define `exit_week` as the last week with non-missing judge scores (or where `total_judge_score > 0`); all weeks subsequent to `exit_week` are excluded from the active set and the denominators of all KPIs.
  - Withdrawals are not counted as "true eliminations" in elimination-consistency KPIs by default; they are reported separately with the tag `exit_type="withdrew"` for sensitivity analysis.

I reviewed our KPIs again and noticed you removed a lot of metrics compared to our original version. Could you explain the reasons for this? Also, is it possible to retain some of the original KPIs?

This is our original KPI framework:
## KPI Table
| KPI                                     | Direction | Calculation Methodology                                | Slicing Dimensions                                                                 | Notes                                                                 |
| --------------------------------------- | -------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **KPI1 Elimination Hit-Rate**            | Higher Better | For weeks with eliminations: the proportion of cases where the predicted elimination set exactly matches the actual elimination set; for weeks with multiple eliminations, measured by bottom-k hit rate | Season; Voting Rule Era (1–2/3–27/28–34); Single/Multiple/No Elimination Weeks     | Actual eliminations can be inferred from `results` or a score of 0 in the week following elimination |
| **KPI2 Vote Identifiability**            | Higher Better | For each (celebrity, week), derive the feasible interval/rank interval for votes; define identifiability as 1/(interval width+ε), and aggregate results by median | Season; Week Stage (Early/Mid/Late); Weeks with Controversial Celebrities           | Reflects the degree of "non-unique voting outcomes"; to be explained in the report in relation to the strength of underlying assumptions |
| **KPI3 Rule Divergence Rate**            | Higher Better | Using the same set of vote estimates, the percentage of weeks where the rank-based vs. percentage-based voting schemes (including the bottom-two judge save mechanism) yield different elimination/Champion outcomes | Individual Season; Controversial Seasons; Weeks with Narrow Total Judge Score Gaps | Core output of the comparative analysis; a higher value indicates greater **impact** (not "better performance") |
| **Constraint KPI1 Fan Agency Floor**     | Higher Better | In simulation, the proportion of cases where the fan vote 1st place (or top x%) is eliminated should be below a predefined threshold; or the equivalent lower bound of retention rate | Voting Rule Scheme; Season Stage                                                    | Prevents excessive dilution of fan vote influence, especially when the judge save mechanism is applied |
| **Constraint KPI2 Rule Simplicity**      | Lower Better | Number of tunable hyperparameters in the rule + a binary indicator for reliance on unavailable external information (0/1) | Scheme Version                                                                     | Ensures operational feasibility and interpretability for the show; to be included in the **feasibility section** of the memo |

---

# **Output**
When you said "I removed many KPIs", the reason is straightforward: **I was defining the P0/Triage metrics framework**—only retaining metrics that are 100% implementable with the **core research brief + existing official CSV data**, runnable within 2–4 hours, and require no data fabrication due to missing information. Several metrics in your original framework fall under the **P1/P2 categories** (requiring vote estimation models, additional assumptions, external data, or threshold calibration). To prevent the data team from being forced to "guess/impute/fabricate" data during the P0 phase, I temporarily excluded them from the minimal version of the **authoritative KPI table**.

This does **not** mean these KPIs are discarded; the better approach is to: **retain all original KPIs but explicitly stratify them in the registry as P0 (computable out-of-the-box) vs. P1 (assumption/model-dependent) vs. P2 (external data-dependent)**. This preserves your original analytical framework while keeping the data team focused during the initial P0 phase.

Below is a line-by-line explanation of **why each original KPI was excluded from the P0 table** and the **safest way to retain it**.

---

## 1) Rationale for Exclusions: Line-by-Line KPI Comparison
### KPI1 Elimination Hit-Rate
* **This metric is a mandatory P0 inclusion**. I retained it in the framework, renaming it to `ElimMatchRate_rank` / `ElimMatchRate_percent` and adding clear denominator rules (for no-elim/multi-elim/withdrawal weeks).
* For your note stating "actual eliminations can be inferred from `results` or a score of 0 post-elimination", I opted for a **`results`-first approach in the triage framework (with 0 scores treated as coding anomalies)** during P0, to avoid misinterpretation of the "0 score = elimination" heuristic.

✅ Conclusion: **KPI1 to be retained in the authoritative P0 KPI table**.

---
### KPI2 Vote Identifiability
* This metric is inherently non-P0: calculating the "feasible vote/rank interval" depends on modeling choices for the **mathematical formulation of voting rules, vote-score aggregation logic, inclusion of the bottom-two judge save mechanism, and the domain/scale of vote variables**. Raw vote values are **unknown and proprietary**, with no direct data available.
* Including KPI2 in the **authoritative P0 KPI table** would force the data team to:
  * Arbitrarily define a vote scale (e.g., percentage/rank/logit), or
  * Fabricate values for ε/thresholds/interval boundaries.
  This directly violates the core rule of **no data guesswork**.

✅ Conclusion: **Retain KPI2 as a P1 metric (assumption/model-dependent)**; do not let it block P0 delivery.

---
### KPI3 Rule Divergence Rate
* **The core of this metric was retained**: I renamed it to `FlipRate_rank_vs_percent`, which measures the percentage of weeks where rank-based vs. percentage-based schemes yield divergent elimination predictions.
* Your original label of "Higher Better" carries semantic risk: this is an **impact indicator**, not a performance metric. I revised it to a descriptive label ("lower values = more stable outcomes") to avoid reviewer confusion about why a higher value would be desirable.

✅ Conclusion: **KPI3 to be retained in the authoritative P0 KPI table**, with its direction/description revised to **purely descriptive** (excluding "Higher Better").

---
### Constraint KPI1 Fan Agency Floor
* This metric is analogous to KPI2: it relies on a clear definition of the "fan vote 1st place (or top x%)", yet raw fan vote data is unavailable. Calculating it requires at minimum a `fan_rank_est` or `fan_share_est` estimation model (P1). Without this, only a trivial "uniform vote" baseline is possible—**which renders the constraint meaningless**.

✅ Conclusion: **Retain as a P1 Constraint KPI (fan vote estimation-dependent)**; P0 to only reserve a metric interface with no numerical calculations.

---
### Constraint KPI2 Rule Simplicity
* This is a **qualitative/count-based metric for scheme feasibility**, independent of data cleaning. It falls under the **strategy/scheme review module** (more suited for the memo) rather than the P0 data analysis phase.
* The data team should not be responsible for this metric during the initial P0 phase.

✅ Conclusion: **Retain the metric but classify it under "Policy/Decision-layer Metrics (non-data-driven)" or P2**; do not include it in the data cleaning KPI table to avoid the data team mistakenly attempting to compute it from the CSV dataset.

---

## 2) Is It Possible to Retain Some Original KPIs?
Yes, and it is **recommended**. The **safest retention method** is to add two columns to the KPI table in `kpi_registry.md`:
- **Status**: P0/P1/P2
- **Dependencies**: Explicit list of required additional definitions, models, or external data.

This preserves your original analytical framework without causing scope creep for the P0 data implementation.

Your current updates to the slice/window definitions are highly accurate (especially the withdrawal handling logic) and will not introduce major issues; on the contrary, they will ensure the **stability and reproducibility** of subsequent KPI1/KPI3 calculations.

---

## 3) Recommended Revision Plan (Minimal Structural Changes, No P0 Complexity)
There is no need to discard the current P0 framework; simply implement these steps:
1. **Keep KPI1/KPI3 as the core authoritative P0 KPIs** (per the current version).
2. **Add KPI2, Constraint KPI1, and Constraint KPI2 back to the table** with clear P1/P2 status tags, and document their dependencies (mark as "TBD/Not Computed" if dependencies are unmet).

This approach avoids downstream issues because:
- P0 implementation remains focused solely on KPI1/KPI3.
- P1/P2 metrics are only **registered** (no impact on data cleaning/denominator rules).
- P1/P2 metrics can be activated once the strategy/vote estimation models are finalized.

---

## 4) Minimal Information Requirements for Activating KPI2/Constraint KPI1 (≤3 Items)
If you plan to move KPI2 or Constraint KPI1 from "registered" to "computable" in subsequent phases, the following 3 key details must be confirmed first:
1. **Fan vote variable representation**: Will fan votes be modeled as `fan_percent` or `fan_rank` (or another format)?
2. **Mathematical formulation of the aggregation rule**: Exact combine formula for the percentage-based scheme, and the combine rule for the rank-based scheme (including whether the bottom-two judge save mechanism is applied).
3. **Definition of "fan vote 1st place/top x%"**: Ranked by `fan_percent_est` or the aggregated total score? What is the value of x (mark as TBD if not specified)?

Until these 3 details are finalized, KPI2 and Constraint KPI1 can only be treated as **conceptual KPIs**.
