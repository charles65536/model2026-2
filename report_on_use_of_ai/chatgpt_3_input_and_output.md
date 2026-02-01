# **Input**
* Document Descriptions / Authoritative Standards:
  - 2026_MCM_Problem_C.pdf: Problem statement information (authoritative)
  - 2026_MCM_Problem_C_Data.csv: Raw data (authoritative, most critical)
  - data_play_book.md: Your playbook (must be followed)
  - visual_play_book.md: Playbook for the downstream visualization_agent (for reference only, secondary)
  - dynamic_files/context_pack_for_ai.md and dynamic_files/kpi_registry.md: The **sole authoritative standards** for this project (in case of conflicts, these shall prevail)
  - dynamic_files/data_agent_triage_ticket.md: Triage ticket for you (must be satisfied item by item)

* Prohibitions:
  - Do not read/cite content from any documents not listed above as "authoritative/required" to define fields, KPIs, units or problem implications; mark as "to be confirmed" if uncertain and adopt the safest defaults provided in the ticket.

* Your Tasks (strictly follow the Definition of Done (DoD) in the ticket):
Implement in accordance with dynamic_files/data_agent_triage_ticket.md:
P0 Cleaning → KPIs Calculable → Baseline Executable → Deliverables
1) output/table/tab_baseline_consistency.tex
2) output/table/intermediate_weekly_panel.csv (or the intermediate csv required by the ticket)
Clearly list the paths of the generated files and their corresponding KPIs/slices in your response.

* Engineering Constraints:
  - Code entry scripts shall be placed under src/ and ensure direct execution to generate the aforementioned deliverables (manifest points to the entry).
  - No general EDA shall be conducted; only minimal cleaning/slicing/summarization serving KPI and baseline comparison shall be performed.

* Acceptance is based on file deliverables: Failure to generate output/table/tab_baseline_consistency.tex and the intermediate csv file shall be deemed incomplete.
---
# **Output**
The season-week-contestant weekly panel has been successfully built in accordance with the P0 standards of **dynamic_files/data_agent_triage_ticket.md**, and the specified files have been delivered (including reproducible BL-0 baseline and consistency KPIs).

---
## Deliverable Paths (for Acceptance)

1. **L1 Table: Baseline Consistency (including Rank/Percent + FlipRate + era slice)**
   * Path: `/mnt/data/output/table/tab_baseline_consistency.tex`
   * Download: [tab_baseline_consistency.tex](sandbox:/mnt/data/output/table/tab_baseline_consistency.tex)
   * Corresponding to: KPI1 (Rank/Percent consistency hit rate) + KPI3 (Rule Divergence Rate FlipRate); Slices: Overall, Rank-era(1–2,28–34), Percent-era(3–27)

2. **Middleware: Weekly Panel (directly usable for recalculation by subsequent fan_share_est / fan_rank_est plug-ins)**
   * Path: `/mnt/data/output/table/intermediate_weekly_panel.csv`
   * Download: [intermediate_weekly_panel.csv](sandbox:/mnt/data/output/table/intermediate_weekly_panel.csv)
   * Corresponding to: Minimal input panel for all KPIs (at season-week-celebrity granularity), including active/true elimination flag/intra-week rank & percent

(Additional, non-acceptance-affecting: season-week granularity prediction comparison table)
   * Path: `/mnt/data/output/table/intermediate_baseline_preds.csv`
   * Download: [intermediate_baseline_preds.csv](sandbox:/mnt/data/output/table/intermediate_baseline_preds.csv)

---
## Code Entry and Reproducible Execution Method (Engineering Constraints)
   * Entry Script: `/mnt/data/src/p0_triage_build_weekly_panel.py`
   * Manifest: `/mnt/data/manifest.json`

Execution Command (directly generates all the aforementioned deliverables):
```bash
python src/p0_triage_build_weekly_panel.py \
  --input /mnt/data/2026_MCM_Problem_C_Data.csv \
  --outdir /mnt/data/output/table
```

---
## Triage Ticket DoD (Chinese-English Comparison)

### 1) P0 Fields (≤8; one reason per field)
1. `season`
   * CN: One of the primary keys for the weekly panel and era slicing.
   * EN: Primary key for weekly panel and era slicing.

2. `celebrity_name`
   * CN: Unique contestant identifier, used for intra-week ranking and elimination comparison.
   * EN: Unique contestant identifier for intra-week ranking and elimination matching.

3. `ballroom_partner`
   * CN: To derive "partner's historical performance/dancer effect" in subsequent steps.
   * EN: Required for deriving partner performance and dancer effect features in follow-up work.

4. `results`
   * CN: Parse actual elimination/withdrawal weeks for ground truth and active set filtering.
   * EN: Provides ground-truth elimination and withdrawal information for active set definition and label assignment.

5. `placement`
   * CN: Final ranking (for subsequent champion/final round comparison).
   * EN: Final contestant placement for subsequent season outcome analysis and validation.

6. `weekX_judgeY_score (X=1..11, Y=1..4)`
   * CN: The only observed data for constructing weekly total judge scores, ranks and percentages.
   * EN: Core observed input features for calculating weekly total judge scores, ranks and percentage shares.

7. Derived `week` (expanded from column names)
   * CN: Time index generated by reshaping the wide-format data to long format.
   * EN: Time index created by reshaping the dataset from wide to long format.

8. Derived `total_judge_score` (sum of weekly judge scores, skipna; judge4 may be missing)
   * CN: The minimal aggregated metric for the technical performance signal in each week.
   * EN: Minimal aggregated metric representing the weekly technical performance signal of contestants.

---
### 2) Hard Filter Rules (exactly 5 rules; executable IF…THEN…)
1. **IF** all four judge scores for a given (season, celeb, week) are NaN **THEN** `drop` the weekly record (exclude from the weekly panel)
   * EN: If all four judge scores are NaN for a (season, celebrity, week) entry, drop the row from the weekly panel.

2. **IF** `results` matches `Eliminated Week k` **THEN** mark `eliminated_at_end_of_week=1` for week=k, and set `active=0` for `week > k` (post-exit status)
   * EN: If the `results` field indicates elimination in Week k, label `eliminated_at_end_of_week=1` for week k and set `active=0` for all weeks > k (post-elimination status).

3. **IF** `results == "Withdrew"` **THEN** set `exit_week = last week with total_judge_score > 0`, and set `active=0` for `week > exit_week` (retain withdrawal type)
   * EN: If `results == "Withdrew"`, set `exit_week` to the last week with a positive `total_judge_score`, and mark `active=0` for all weeks > exit_week while retaining the withdrawal type attribute.

4. **IF** `total_judge_score == 0` and `week != exit_week` **THEN** mark `data_anomaly_zero_score=1` and set `active=0` (default to post-exit zero-score extension)
   * EN: If `total_judge_score == 0` for a week that is not the `exit_week`, flag `data_anomaly_zero_score=1` and set `active=0`, treated as post-exit zero-score encoding by default.

5. **IF** the number of actual eliminations for the same `(season, week)` is `!= 1` **THEN**
   * Multiple eliminations: use bottom-k set-match for consistency calculation;
   * No eliminations: exclude the week from the denominator of KPI1 while retaining it in the panel
   * EN: For weeks with multiple eliminations, apply bottom-k set matching for consistency assessment; for weeks with no eliminations, exclude the week from the denominator of KPI1 but retain the records in the weekly panel.

---
### 3) Keep-but-Explain (exactly 3 items)
1. Non-integer scores caused by decimal points/bonus points
   * CN: Retain the original values; explain in the report that "scores for multiple dances/bonus points/team dances have been allocated to weekly scores".
   * EN: Retain the original decimal values; explain in the report that decimals result from the allocation of scores for multiple dances, bonus points and team dances to weekly totals.

2. Zero scores in weeks after elimination
   * CN: Excluded from active ranking/ percentage calculation; explained as extended data encoding.
   * EN: Exclude from active set ranking and percentage share calculation; the zero scores are explained as post-elimination data encoding conventions.

3. Changes in the number of judges & non-fixed judge numbering
   * CN: Do not track judge identities, only use weekly total scores/percentiles.
   * EN: Judge identities are not tracked; only intra-week total scores and percentile ranks of judges' scores are used for subsequent analysis.

---
### 4) Minimal KPI Computation (≤25 lines of pseudocode)
```pseudo
INPUT raw_csv
RESHAPE weekX_judgeY_score -> long format (season, celeb, week, judge1..4)
total_judge_score = sum(judges, skipna)

APPLY hard filter rules to define:
  exit_week, exit_type, eliminated_at_end_of_week
  active flag

FOR each (season, week):
  A = set of active contestants
  IF |A| < 2: continue
  judge_rank    = rank_desc(total_judge_score, ties=average)
  judge_percent = total_judge_score / sum(total_judge_score over A)

  fan_percent_est = 1 / |A|     # BL-0 (uniform fan vote distribution)
  combined_percent = judge_percent + fan_percent_est
  pred_elim_percent = bottom-k(combined_percent, k = |true_elim_set| or 1)

  combined_rank = judge_rank    # uniform fan rank adds a constant value
  pred_elim_rank = bottom-k_by_worst_rank(combined_rank, k = |true_elim_set| or 1)

  true_elims = {celeb in A where eliminated_at_end_of_week==1}
  IF |true_elims|==0: exclude the week from KPI1 denominator
  ELSE: calculate set-match for KPI1 (for both rank and percent rules)
KPI3 FlipRate = proportion of (season,week) pairs where pred_elim_percent != pred_elim_rank
```

---
### 5) Data Credibility Notes (for writing; exactly 4 English sentences, no fabricated data)
1. All metrics are computed strictly from the official COMAP-provided dataset and its stated encoding rules (e.g., post-elimination scores recorded as zeros and varying judge counts).
2. We treat fan votes as unobserved latent variables and only report reproducible baseline proxies at this stage, while maintaining a clean plug-in interface for future vote-estimation models.
3. As the exact season when the show reverted to rank-based aggregation is unconfirmed, we designate the Season-28 switch as a modeling assumption and will conduct stress tests on adjacent cutoff points.
4. Weeks with no eliminations or multiple eliminations are explicitly addressed in denominator definitions for relevant KPIs to avoid overstating consistency performance.

---

## Note: All conclusions and code have been reviewed by humans.