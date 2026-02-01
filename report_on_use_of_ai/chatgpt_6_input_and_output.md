# **Input**
You are the "Data Phase Master Controller + Standard Auditor" for my MCM/ICM project. Our problem-solving approach focuses on optimization/strategy/simulation, and we will not conduct general EDA. Please work only based on the files I upload; do not fabricate any data, results, fields, units, or problem requirements. If uncertain, mark it as "Not Provided/To Be Confirmed" and provide minimal supplementary information requirements (≤3 items) along with the safest default handling plan.

【Files I Will Upload (Please Read and Cite Their Information One by One)】
1) dynamic_files/context_pack_for_ai.md (Current project snapshot)
2) dynamic_files/kpi_registry.md (Authoritative standard registry)
3) problem_and_raw_data/2026_MCM-ICM_Problems/problem_C_investigation.md (My first-round investigation notes on the problem)
4) Competition raw materials (problem statement PDF/data description/data samples, etc.; read all if multiple)

【Your Tasks】
A. Alignment Audit (Most Important)
1) Compare "Competition Raw Materials" vs "Investigation Notes" vs "context_pack/kpi_registry" and list differences and conflicts:
   - Are the problem objectives/deliverables consistent?
   - Are the KPI names/definitions/directions/aggregation methods (mean/P95/P99/ratio) consistent?
   - Are the definitions of Slice/Window (peak, weekday/weekend, scenario) consistent?
   - Is the Baseline definition consistent and sufficiently implementable?
   - Are the data fields (column names, meanings, units) consistent? Are there fields "assumed in notes but not mentioned in the problem statement"?
2) Output a "Conflict List (sorted by severity)": Each item includes
   - Conflict Point (one sentence)
   - Impact (will cause incorrect KPI calculation/deviation/unreproducibility in the Data phase)
   - Repair Suggestion (specifically where to modify: context_pack, kpi_registry, or investigation notes)

B. Generate "Data Agent’s First-Round Work Order (Triage)"
Goal: Enable the data handler to achieve within 2–4 hours: P0 Cleaning + KPI Calculable + Baseline Runnable + Output 1 chart/table interface.
Based on the audit results, you must generate a work order that can be copied and pasted to the Data Agent, strictly including:
1) Goal (Data objective for this round: which KPIs can be calculated, which Claims/review questions are supported)
2) P0 Field List (≤8; must be from the problem statement/data description or clearly marked "To Be Confirmed")
3) Hard Rules (exactly 5 IF… THEN… drop/repair…; do not fabricate fields)
4) Keep-but-Explain (exactly 3 items: possible abnormal phenomena + how to write them in the report)
5) Minimal KPI Computation (≤25 lines of pseudocode: how to calculate main KPIs and constraint KPIs according to standards)
6) Minimal Baseline Interface (what inputs/outputs the baseline requires; how to save to disk for eval/viz use)
7) Outputs (file interfaces that must be delivered in this round, according to our engineering conventions):
   - output/table/tab_<name>.tex or intermediate csv
   - output/figure/fig_<name>.pdf (if appropriate)
   - For each deliverable, write "which Claim/KPI/slice it corresponds to"
8) Report-ready Data Credibility (exactly 4 English sentences: no fabricated values, emphasize standards and risks)

C. Provide "Backfill/Revision Suggestions" (to make my dynamic_files more usable)
Please output two "directly copy-pasteable patch contents" for me to manually update the files:
1) For context_pack_for_ai.md: Provide suggested paragraphs to add/modify (write complete replaceable paragraphs in Markdown blocks)
2) For kpi_registry.md: Provide the suggested updated KPI table rows, slice definitions, baseline definitions, and change log (also provide replaceable contents in Markdown blocks)
Requirements: Only modify necessary parts; all definitions must be consistent with the problem statement; if not provided in the problem statement, mark as "To Be Confirmed/Assumption" and suggest stress testing.

【Output Format (Must Follow Strictly in Order)】
1. Executive Summary (≤8 lines): How to conduct this round of Data work and what the biggest risk is
2. Conflict List (table)
3. Data Agent Triage Work Order (complete text that can be copied and pasted)
4. context_pack_for_ai.md Patch (Markdown block: replace paragraphs/add paragraphs)
5. kpi_registry.md Patch (Markdown block: KPI table + slice + baseline + changelog)

【Engineering and Standard Constraints】
- Our deliverable directories are: output/figure/ and output/table/ (do not use plurals)
- The code entry is under src/ (the script path in the manifest refers to the entry file that can be directly run to generate deliverables)
- Do not conduct general EDA; all cleaning/slicing/indicators must serve KPI and baseline comparison
- If information is missing from the problem statement/data description: do not guess; provide "the safest default plan + minimal information to be confirmed"


> "For each file, the patch content can modify at most 2 paragraphs + 1 table; full file rewrite is not allowed."

This is our global prompt for the data agent, for your reference:
# 1 Data Agent – Triage (Early Stage: Run Indicators)

**Role**
You are a "Minimum Viable Data Auditor". The goal is to quickly run through KPIs and baselines before determining the model.

**I Will Provide**
* Field names (preferably with units) + 3–20 lines of samples (or field descriptions)
* KPI standards given in the Framing/Spec

**You Must Output**
1. **P0 Fields**: Fields that must be cleaned (one reason per field)
2. **Hard Filters Rules (5 executable rules)**: Each written as `IF ... THEN drop/repair ...`
3. **Keep-but-Explain (3 items)**: List as many abnormal phenomena as possible that should not be deleted, and how to explain them in the report (one sentence per item)
4. **Minimal KPI Computation**: Write how to calculate main KPIs and constraint KPIs (≤25 lines)
5. **Data Credibility Notes (for writing)**: 4 English sentences for the writer, which can be directly placed in the report (no fabricated numbers)

**Prohibitions**
* Suggest complex imputation/in-depth model cleaning
* Suggest unexecutable complex repairs (such as in-depth imputation, complex anomaly detection)

**DoD**
Output results that allow the implementer to run baseline indicators within 1–2 hours and generate as many useful charts as possible.
Please output explanatory text in both Chinese and English! Chinese should be easy to understand, and English should be academic, so that it is easy to understand and can be used relatively directly.


# 2 Data Agent – Deep (Late Stage: Serve the Model)

**Role**
You are a "Model Sensitivity and Data Risk Diagnostician". Goal: Focus on the 3 most likely data risk points that affect conclusions around the current model/strategy and provide repairs/verifications.

**I Will Provide**
* Current model/strategy overview (3–10 lines)
* Current indicator results (can be rough)
* Problems we are worried about (such as long tails, zero inflation, drift)

**You Must Output**
1. **Top-3 Risks (sorted)**: Risk phenomenon + each includes "why it is fatal"
2. **Detection**: Provide 1 executable detection for each risk (statistical test/quantile comparison/slicing/comparison)
3. **Mitigation (with side effect)**: Provide 1 repair plan + 1 side effect for each risk
4. **Sensitivity Test Plan**: Provide 3 stress tests (change thresholds/switch time windows/delete a certain segment of data, etc.)
5. **Report Wording (2–3 English sentences)**: How to "downplay but close the loop"

**Prohibitions**
* Directly overthrow the main model line (unless you explicitly request it)
* Fabricate sentences like "We have verified..."

DoD: The detections and stress tests you provide can be directly turned into L2 charts or appendix tables to support "credibility/sensitivity". Please output in both Chinese and English! Chinese should be easy to understand, and English should be academic, so that it is easy to understand and can be used relatively directly.


Note: Regarding the hierarchical standards of our deliverable charts:
```
### Level 0: Understand the overall situation at a glance (1–2 charts) **Purpose:** Allow reviewers to know what you have done, what the results are, and why they are credible within 30 seconds. **Typical Charts:** * **Pipeline Overview Chart** (Forecast→Mode→Decision / A-B Route / Fail-Safe) * **Core Result Comparison Chart** (1 chart: Best Strategy vs Baseline, P95/P99 + Cost in Key Windows) **Judgment Standards:** * No detailed parameters allowed; only talk about "modules, inputs and outputs, conclusions" * The title must be a **conclusion sentence** (not a noun like "Results") --- ### Level 1: Evidence Charts Supporting Claims (1–2 charts per claim) **Purpose:** Turn each of your "innovation points" into visual evidence one by one. You usually have 3–4 claims, which correspond to 4–8 L1 charts. **Common Claims → Corresponding Charts:** * "Patterns exist and are distinguishable" → Daily Heat Map / Mode Timeline * "Prediction is effective" → Error Distribution/Quantiles + Key Window MAE * "Strategy improves tail performance" → P95/P99/ECDF/Box Plot * "Trade-off is reasonable" → Pareto Frontier (Cost-Service) **Judgment Standards:** * Each chart answers one question: **Q → A** * The chart must be labeled with: Sample Range (Date/Window), Indicator Definition (AWT/P95, etc.), Who the Baseline Is --- ### Level 2: Method Rationality and Diagnostic Charts (placed in Appendix or Edge of Main Text) **Purpose:** Let reviewers believe you did not make arbitrary decisions (but do not occupy main text space). **Typical Charts:** * Model Diagnosis (Residuals/ACF, Hyperparameter Sensitivity Curve) * Ablation Experiment Bar Chart (Performance Change After Removing a Module) * Calibration/Alignment Check Chart (Proxy vs Actual/Comparison Standard Consistency) **Judgment Standards:** * At most 1–2 charts in the main text, the rest go to the appendix * The title writes the "diagnostic conclusion", not "ACF plot" --- ### Level 3: Raw EDA/Reference Charts (Appendix) **Purpose:** Prove you have looked at the data without interrupting the narrative. **Typical Charts:** * Distribution Histogram, Scatter Cloud Chart, A Large Number of Faceted Charts * Full Floor Full Time Period Detailed Chart **Judgment Standards:** * The appendix can be many, but each must have one sentence of annotation (tell reviewers "what this chart wants to illustrate") --- ### A Mnemonic (Can Be Used On-Site) **L0 tells the story, L1 provides evidence, L2 proves no arbitrary decisions, L3 is for reference.** 
```

---
# **Output**
## 1. Executive Summary（≤8 lines）

* The sole goal of this round of Data work: **Successfully build a judge score panel at the "season-week-contestant" granularity** and be able to **calculate elimination consistency** under the two combination rules of "Rank / Percent" (baseline runnable, KPIs calculable, output 1 table/chart interface).
* The biggest risk: Your dynamic files (`context_pack`/`kpi_registry`) currently have **empty tables + "this file wins"**, which will make standards unimplementable and prevent the Data Agent from determining "what to calculate, how to slice, and what the baseline is".
* The second biggest risk: The `investigation` notes contain **KPI target values/statistical tests/vote distribution and total vote settings not provided in the problem statement**; if treated as facts from the problem statement, it will lead to "incorrect KPI calculation/wrong assumptions in the Data phase".
* The safest way to proceed: Based on the fields in Table 1 of the problem statement (`season, results, placement, weekX_judgeY_score...`), first build the **weekly panel + judge-total/rank/percent**; for fan votes, only reserve an **interface** and a "uniform vote" baseline (reproducible, no extrapolation) for now.

---

## 2. Conflict List (Table)

| Severity          | Conflict Point (one sentence)                                                                                              | Evidence (from files)                                                                                    | Impact                                                        | Repair Suggestion (where to modify)                                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **CRITICAL** | `context_pack`/`kpi_registry` claim "this file wins in case of conflict", but KPIs/slices/baselines are **empty**, making audit alignment impossible. | Both files are v0.1 with empty KPI tables/definitions marked "to be filled/empty rows".                                                             | The Data phase cannot determine "which KPIs to calculate, how to aggregate/slice, and what the baseline is", leading to **incorrect calculation/deviation/unreproducibility** | **Prioritize filling**: Write main KPIs/slices/baselines in `kpi_registry.md`; synchronize the "data snapshot that only affects conclusions" in `context_pack_for_ai.md`. |
| **CRITICAL** | Inconsistent engineering directory constraints: You require `output/figure` and `output/table`, but the internal structure example in `context_pack` is `outputs/fig` and `outputs/tab`. | The "file structure" in `context_pack` shows `outputs/fig` and `outputs/tab`.                                      | The Data Agent will **write to the wrong path** if implementing according to the example, and manifest/latex references will be broken.             | In the data/deliverable convention paragraph of `context_pack_for_ai.md`, clearly state: **Subject to the constraints of this conversation: `output/figure/` & `output/table/`**.  |
| **HIGH**     | The `investigation` notes state "the return to rank + bottom-two judges save starting from Season 28" as a confirmed fact; the problem statement says the **exact season is unknown**, only "reasonable assumption = 28".          | The problem statement clearly states: "exact season … not known… reasonable to assume… 28".                                  | If the standard is written as fixed, it will lead to doubts about "cross-season comparison/sensitivity" (assumptions not explicitly stated).                             | In the slice definition of `kpi_registry`, mark Season 28 as an **assumption to be confirmed** and require stress tests: three cutting methods (27/28/29).         |
| **HIGH**     | The `investigation` notes introduce KPI target thresholds (such as "accuracy ≥80%/≥90%"), various statistical test conclusions, vote distribution, and total vote settings not provided in the problem statement, which may be mistaken for "problem requirements". | The `investigation` notes contain target descriptions such as "accuracy ≥80%" and "p-value"; the problem statement only requires "provide measures of consistency/certainty" without giving thresholds. | The writing/review standards will become "self-created indicator requirements", and may also force the Data phase to make incorrect alignments.                     | Demote all these thresholds to **team-internal goals** and mark in `context_pack` that "they are not problem requirements".                        |
| **MEDIUM**   | "Fan votes are an unknown secret"; the problem statement allows external data but requires complete citation; your current dynamic files do not specify an external data strategy.                                         | Problem statement: You may "choose to include additional information… must completely document sources".           | If external popularity/social media data is used later without standards, it will cause reproducibility risks.                              | Add a paragraph in `context_pack`: External data is **not used by default**; if used, sources, timestamps, and field mappings must be recorded in References/Appendix.               |
| **MEDIUM**   | Field level: The problem statement data description only provides `weekX_judgeY_score`, etc.; "pro dancer popularity/historical performance" mentioned in the `investigation` notes are not original fields.                  | Table 1 of the problem statement only includes partner names, current season results, and weekly scores; there is no "popularity".                                                      | If the Data phase directly assumes the existence of such fields, it will **fabricate columns**.                                | Clearly state in the triage work order: Pro dancer impact can only be **derived from historical placement** (derived feature), and "derivation standards" must be marked.           |

---

## 3. Data Agent Triage Work Order (Complete Text for Copy-Paste)

**[Triage Ticket | Problem C DWTS | P0: KPI runnable + baseline runnable]**

### 1) Goal (Data Objective for This Round)

* **Chinese**: Build a judge score panel at the "season-week-contestant" granularity within 2–4 hours to support the following minimal review questions:
  1. Use a reproducible baseline to generate "predicted eliminations" under the two combination rules of **Rank / Percent**, and calculate consistency with actual eliminations.
  2. Reserve an interface for subsequent "fan vote estimation": Can access any `fan_share_est` or `fan_rank_est` and recalculate eliminations.
* **English**: Build a reproducible weekly panel from judges’ scores, enabling elimination-consistency evaluation under both **rank-based** and **percent-based** combination schemes, with a plug-in interface for future fan-vote estimates.

### 2) P0 Field List (≤8; from problem statement/data description; mark if uncertain)

> Only use fields explicitly given in Table 1 of the problem statement.

1. `season` (Season)
2. `celebrity_name` (Contestant)
3. `ballroom_partner` (Professional dancer partner, used to derive "partner's historical performance" later)
4. `results` (e.g., "Eliminated Week k / 1st Place / Withdrew")
5. `placement` (Final ranking, 1 is the best)
6. `weekX_judgeY_score` (X=1..11, Y=1..4; includes decimals/bonus already allocated)
7. **Derived Field** `week` (Obtained by expanding column names)
8. **Derived Field** `total_judge_score` (Sum of available judge scores in the same week; judge4 may be missing)

### 3) Hard Rules (Exactly 5 IF… THEN… drop/repair…)

1. **IF** all four judge scores for a row in a certain `week` are **all NaN** (the week has not aired/the season has fewer weeks) **THEN** **drop from weekly panel** for that row and week (not included in the active set or any KPI denominator).
2. **IF** `results` matches `Eliminated Week k` **THEN** mark the contestant as **eliminated_at_end_of_week=1** in week `k`, and **drop from active set** for records where `week > k` (even if the score is 0, it is not regarded as participation).
3. **IF** `results == "Withdrew"` **THEN** set `exit_week = last week with total_judge_score > 0` and mark `exit_type="withdrew"`; **drop from active set** for `week > exit_week` (retain the anomaly in notes).
4. **IF** `total_judge_score == 0` in a certain week and the week is **not** the exit week determined by Rules 2/3 **THEN** mark the weekly record as `data_anomaly_zero_score=1` and **drop from active set** (default to "post-exit zero-score extension").
5. **IF** there are **>1 contestants** with `eliminated_at_end_of_week=1` (multi-elimination week) or **=0 contestants** (no-elimination week) in the same `(season, week)` **THEN** when calculating consistency:
   * Multi-elimination week: Allow set-match (top-k) between the predicted set and the actual set.
   * No-elimination week: Drop the week from the denominator of "elimination consistency" but retain it in the panel for subsequent analysis.

### 4) Keep-but-Explain (Exactly 3 Items: Abnormal Phenomena + How to Write in Report)

1. **Non-integer scores caused by decimals/bonus points**: Retain the original values; explain in writing that "the problem statement indicates that scores from multiple dances/bonus points have been averaged/allocated to weekly scores".
2. **Zero scores in weeks after elimination**: Do not participate in ranking/percent calculation as participating weeks; explain in writing that "zero scores are a data encoding rule used to indicate extension after elimination".
3. **Changes in the number of judges & non-fixed judge serial numbers**: `judgeY` only indicates the scoring order, not the same person across weeks; explain in writing that "we only use weekly total scores/percentiles and do not track specific judge identities".

### 5) Minimal KPI Computation（≤25 Lines of Pseudocode: Main KPIs + Constraint KPIs）

```pseudo
INPUT: raw_csv
EXPAND wide weekX_judgeY_score -> long rows (season, celeb, week, judge_scores[1..4])
total_judge_score = sum(judge_scores, skipna=True)
active = (not all_nan(judge_scores)) AND (not dropped by exit rules)

FOR each (season, week):
  A = {rows where active==True}
  if |A| < 2: continue
  judge_rank = rank_desc(total_judge_score within A)   # 1 is the best
  judge_percent = total_judge_score / sum(total_judge_score over A)

  # Baseline fan estimate (reproducible, no external data)
  fan_percent_est = 1 / |A|        # Uniform distribution
  combined_percent = judge_percent + fan_percent_est
  pred_elim_percent = argmin(combined_percent)

  combined_rank = judge_rank       # Uniform fan rank adds a constant, omitted
  pred_elim_rank = argmax(judge_rank)

  true_elims = {celeb in A with eliminated_at_end_of_week==1}
  update counters for:
    kpi_elim_match_percent += set_match(pred_elim_percent, true_elims)
    kpi_elim_match_rank    += set_match(pred_elim_rank, true_elims)

OUTPUT KPIs:
  ElimMatchRate_percent = mean over eligible (season,week)
  ElimMatchRate_rank    = mean over eligible (season,week)
  FlipRate = share of weeks where pred_elim_percent != pred_elim_rank
```

### 6) Minimal Baseline Interface (Inputs/Outputs Required for Baseline; How to Save to Disk)

* **Input**: `weekly_panel.csv` (each row = season-week-celeb, including `total_judge_score`, `judge_rank`, `judge_percent`, `active`, `true_elim_flag`)
* **Baseline Output**:
  1. `pred_elim_percent` / `pred_elim_rank` (one predicted eliminator or set per season-week)
  2. `combined_score_percent` / `combined_score_rank` (for eval/viz convenience)
* **Save to Disk**:
  * `output/table/intermediate_weekly_panel.csv` (shared by eval/viz/subsequent fan vote models)
  * `output/table/intermediate_baseline_preds.csv` (prediction vs actual comparison at season-week granularity)

### 7) Outputs (Must Deliver Interfaces; Mark Corresponding Claim/KPI/Slice)

1. `output/table/tab_baseline_consistency.tex` (L1 Table)
   * Corresponding to: **Claim** "We can quantify consistency under two rules"; **KPIs** `ElimMatchRate_rank / ElimMatchRate_percent / FlipRate`; **Slices** all season-weeks (and separate columns: rank-era vs percent-era).
2. `output/table/intermediate_weekly_panel.csv` (Middleware)
   * Corresponding to: Minimal input panel for subsequent fan vote estimation models (avoid repeated cleaning).
     (Optional, if time permits)
3. `output/figure/fig_fliprate_by_season.pdf` (L2 Chart)
   * Corresponding to: Distribution of `FlipRate` by season, used as an entry point for subsequent discussions on "which rule favors whom".

### 8) Report-ready Data Credibility（Exactly 4 English Sentences; No Fabricated Values）

1. *All metrics are computed strictly from the official COMAP-provided dataset and its stated encoding rules (e.g., post-elimination scores recorded as zeros and varying judge counts).* 
2. *We treat fan votes as unobserved and report only reproducible baseline proxies at this stage, while keeping a clean plug-in interface for future vote-estimation models.* 
3. *Because the exact season of the show’s return to rank-based aggregation is not confirmed, we label the Season-28 switch as an assumption and will stress-test adjacent cutoffs.* 
4. *Weeks with no elimination or multiple eliminations are handled explicitly in the denominator definitions to avoid inflating consistency claims.* 

---

## 4. context_pack_for_ai.md Patch (Markdown Block: Replace Paragraphs/Add Paragraphs)

> Note: Only modify **2 paragraphs** (one table paragraph + one data snapshot paragraph), no other changes.

```markdown
### [PATCH 1/2] Replace Section 4.1 table block with the following

## 4.1 KPIs / slices / baselines (authoritative) (v0.1 filled for Data Triage)
| KPI name | Direction | Aggregation | Slice/Window definition | Baseline(s) |
|---|---|---|---|---|
| ElimMatchRate_rank | higher is better | mean over eligible (season, week) | Eligible week := active contestants exist AND (exactly one elimination OR evaluated by set-match for multi-elim; no-elim weeks excluded). Rank-era slice uses seasons {1,2,28–34} with **Season-28 as an assumption**. | BL-0: judge-only (uniform fan rank ⇒ adds constant, omitted) |
| ElimMatchRate_percent | higher is better | mean over eligible (season, week) | Same eligibility as above. Percent-era slice uses seasons {3–27}. | BL-0: judge+uniform fan percent (1/n) |
| FlipRate_rank_vs_percent | lower is “more stable” | ratio over eligible (season, week) | Share of weeks where predicted eliminated differs under rank vs percent (using the same baseline fan proxy). | BL-0 only |

> Note: Any numeric “targets” (e.g., 80%/90%) are **team-internal goals**, not problem requirements.
```

```markdown
### [PATCH 2/2] Replace Section 5.1 block with the following

## 5.1 Data snapshot (only what affects conclusions) (v0.1 for Data Triage)
- Data version/tag: `2026_MCM_Problem_C_Data.csv` (official COMAP file; seasons 1–34)
- Key columns (official): `season`, `celebrity_name`, `ballroom_partner`, `celebrity_industry`, `celebrity_age_during_season`, `results`, `placement`, `weekX_judgeY_score`
- Cleaning rules (≤5):
  1) Reshape wide `weekX_judgeY_score` into long panel: one row per (season, week, celebrity).
  2) Compute `total_judge_score = sum(weekX_judgeY_score, skipna)`; do not impute missing judges.
  3) Define `active` by excluding weeks with all-NaN scores and weeks after exit (Eliminated Week k / inferred withdraw week).
  4) Treat post-exit zeros as encoding artifacts (kept in raw but excluded from active set and KPI denominators).
  5) Handle weeks with 0 or >1 eliminations explicitly in KPI denominators (no-elim excluded; multi-elim via set-match).
- Known caveats (≤3):
  - Judge index `judgeY` is not a persistent identity across weeks/seasons; only within-week totals/ranks are used.
  - The exact season of the return to rank-based aggregation is not confirmed; we assume Season 28 and will stress-test adjacent cutoffs.
  - Fan votes are unobserved by design; current baselines use only reproducible proxies and keep a plug-in interface for vote estimates.
```

---

## 5. kpi_registry.md Patch (Markdown Block: KPI Table + Slice + Baseline + Changelog)

> Note: Only modify **1 table + 2 paragraphs** (one paragraph covers slices, the other covers baseline + changelog).

```markdown
### [PATCH 1/3] Replace the KPI table with:

## KPI table
| KPI name | Direction | Definition | Aggregation | Slice/window | Baseline(s) | Notes |
|---|---|---|---|---|---|---|
| ElimMatchRate_rank | higher is better | Under rank-combination, predicted eliminated set matches the true eliminated-at-end-of-week set for that (season, week). | Mean over eligible (season, week) | Eligible: active set exists; no-elim weeks excluded; multi-elim evaluated by set-match. Rank-era slice: seasons {1,2,28–34} with **Season-28 switch as assumption**. | BL-0 judge-only (uniform fan rank adds constant) | “Judge Y” not persistent; we use within-week total score ranks only. |
| ElimMatchRate_percent | higher is better | Under percent-combination, predicted eliminated set matches the true eliminated-at-end-of-week set for that (season, week). | Mean over eligible (season, week) | Percent-era slice: seasons {3–27}; same eligibility rules. | BL-0 judge percent + uniform fan percent (1/n) | Fan votes are unknown; baseline is a proxy for reproducibility. |
| FlipRate_rank_vs_percent | lower is better | Share of eligible (season, week) where the predicted eliminated differs between rank vs percent schemes (holding the same baseline vote proxy). | Ratio over eligible (season, week) | Same eligibility; additionally can be grouped by season. | BL-0 only | Used to motivate “method sensitivity” analysis. |
```

```markdown
### [PATCH 2/3] Replace "## Slice/window definitions" block with:

## Slice/window definitions
- Unit of analysis: (season, week, celebrity) after reshaping `weekX_judgeY_score` wide columns into a long panel.
- Active set definition: a celebrity is active in a (season, week) iff week scores are not all-NaN and week is not after the exit week (Eliminated Week k / inferred withdraw week).
- Era slices for voting-scheme comparison:
  - Rank-era: seasons {1,2,28–34} (**Season-28 is an assumption; stress-test 27/28/29 cutoffs**).
  - Percent-era: seasons {3–27}.
- Weeks with no elimination or multiple eliminations: excluded from single-elimination consistency denominators; multi-elim weeks evaluated by set-match when needed.
```

```markdown
### [PATCH 3/3] Replace "## Baseline definitions" + "## Change log" blocks with:

## Baseline definitions
- BL-0 (Reproducible, minimal): "Judge-only proxy"
  - Rank scheme: use `judge_rank` only (uniform fan ranks add a constant to all contestants).
  - Percent scheme: use `judge_percent + 1/n_active` (uniform fan percent), so elimination is driven by judges with a fixed fan offset.
  - Purpose: provides a fully reproducible reference point before introducing any fan-vote estimation model.

## Change log
- v0.1 (2026-01-30): Initialized triage-ready KPI definitions, eligibility rules, and BL-0 baseline; marked Season-28 rank-era switch as an explicit assumption requiring stress tests.
```

---

If you want me to write the **specific stress tests (27/28/29 cutting methods)** involved in the "Conflict List" as a supplementary work order for the Data Agent (without changing the output structure you require), I can directly attach it in the next message.