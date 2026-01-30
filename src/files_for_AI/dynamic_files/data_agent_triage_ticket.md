## Data Agent Triage 工单（可复制粘贴的完整文本）

**[Triage Ticket | Problem C DWTS | P0: KPI runnable + baseline runnable]**

### 1) Goal（本轮数据目标）

* **中文**：在 2–4 小时内跑通“每季-每周-每选手”的评委分数面板，支持以下最小评审问题：

  1. 在 **Rank / Percent 两种合成规则**下，用一个可复现 baseline 产生“预测淘汰者”，并计算与真实淘汰的一致性（consistency）。
  2. 为后续“估算 fan votes”预留接口：能接入任意 `fan_share_est` 或 `fan_rank_est` 并重算淘汰。
* **English**: Build a reproducible weekly panel from judges’ scores, enabling elimination-consistency evaluation under both **rank-based** and **percent-based** combination schemes, with a plug-in interface for future fan-vote estimates.

### 2) P0字段清单（≤8；来自题面/数据说明；若不确定标注）

> 只使用题面表 1 中明确给出的字段。

1. `season`（赛季）
2. `celebrity_name`（选手）
3. `ballroom_partner`（职业舞者搭档，用于后续派生“搭档历史表现”）
4. `results`（如 “Eliminated Week k / 1st Place / Withdrew”）
5. `placement`（最终名次，1最好）
6. `weekX_judgeY_score`（X=1..11, Y=1..4；含小数/bonus已摊）
7. **派生字段** `week`（由列名展开得到）
8. **派生字段** `total_judge_score`（同一周对可用评委分求和；judge4 可能缺失）

### 3) Hard Rules（恰好5条 IF… THEN… drop/repair…）

1. **IF** 某行在某 `week` 的四个 judge 分数 **全为 NaN**（该周未开播/该季不足周数） **THEN** 对该行该周 **drop from weekly panel**（不计入 active 集合与任何KPI分母）。
2. **IF** `results` 匹配 `Eliminated Week k` **THEN** 标记该选手在周 `k` 为 **eliminated_at_end_of_week=1**，并对 `week > k` 的记录 **drop from active set**（即使分数为0也不当作参赛）。
3. **IF** `results == "Withdrew"` **THEN** 令 `exit_week = last week with total_judge_score > 0`，并标记 `exit_type="withdrew"`；对 `week > exit_week` **drop from active set**（同时在备注中保留该异常）。
4. **IF** 某周 `total_judge_score == 0` 且该周 **不是** 由规则2/3确定的退出周 **THEN** 将该周记录标记 `data_anomaly_zero_score=1` 且 **drop from active set**（默认视作“已退出后的0分延展”）。
5. **IF** 同一 `(season, week)` 出现 **>1 名** `eliminated_at_end_of_week=1`（多淘汰周）或 **=0 名**（不淘汰周） **THEN** 计算 consistency 时：

   * 多淘汰周：允许预测集合与真实集合做 set-match（top-k），
   * 不淘汰周：该周从“淘汰一致性”分母中 **drop**，但仍保留在面板用于后续分析。

### 4) Keep-but-Explain（恰好3条：异常现象 + 报告里怎么写）

1. **小数分/bonus导致非整数分**：保留原值；写作中说明“题面已说明多舞/bonus被平均/摊到周分数中”。
2. **被淘汰后周分数为0**：不作为参赛周参与排名/百分比；写作中说明“0分是数据编码规则，用于表示已淘汰后的延展”。
3. **评委人数变化 & judge序号不固定**：`judgeY`仅表示打分顺序，不代表同一人跨周一致；写作中说明“我们只使用周内总分/分位，不追踪具体评委身份”。

### 5) Minimal KPI Computation（≤25行伪代码：主KPI+约束KPI）

```pseudo
INPUT: raw_csv
EXPAND wide weekX_judgeY_score -> long rows (season, celeb, week, judge_scores[1..4])
total_judge_score = sum(judge_scores, skipna=True)
active = (not all_nan(judge_scores)) AND (not dropped by exit rules)

FOR each (season, week):
  A = {rows where active==True}
  if |A| < 2: continue
  judge_rank = rank_desc(total_judge_score within A)   # 1 best
  judge_percent = total_judge_score / sum(total_judge_score over A)

  # baseline fan estimate (reproducible, no external data)
  fan_percent_est = 1 / |A|        # uniform
  combined_percent = judge_percent + fan_percent_est
  pred_elim_percent = argmin(combined_percent)

  combined_rank = judge_rank       # uniform fan rank adds constant, omitted
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

### 6) Minimal Baseline Interface（baseline需要哪些输入/输出；如何落盘）

* **Input**：`weekly_panel.csv`（每行=season-week-celeb，含 `total_judge_score`, `judge_rank`, `judge_percent`, `active`, `true_elim_flag`）
* **Baseline Output**：

  1. `pred_elim_percent` / `pred_elim_rank`（每个 season-week 一个预测淘汰者或集合）
  2. `combined_score_percent` / `combined_score_rank`（便于 eval/viz）
* **落盘**：

  * `output/table/intermediate_weekly_panel.csv`（供 eval/viz/后续 fan vote 模型共用）
  * `output/table/intermediate_baseline_preds.csv`（season-week 粒度预测与 true 对照）

### 7) Outputs（必须产出接口；并标注对应 Claim/KPI/slice）

1. `output/table/tab_baseline_consistency.tex`（L1 表）

   * 对应：**Claim**“我们能在两种规则下量化 consistency”；**KPI** `ElimMatchRate_rank / ElimMatchRate_percent / FlipRate`；**slice** 全部 season-week（并另列：rank-era vs percent-era）。
2. `output/table/intermediate_weekly_panel.csv`（中间件）

   * 对应：后续 fan vote 估算模型的最小输入面板（避免重复清洗）。
     （可选，若时间允许）
3. `output/figure/fig_fliprate_by_season.pdf`（L2 图）

   * 对应：`FlipRate` 按 season 的分布，用于支撑“哪种规则更偏向谁”的后续讨论入口。

### 8) Report-ready Data Credibility（恰好4句英文；不许编数值）

1. *All metrics are computed strictly from the official COMAP-provided dataset and its stated encoding rules (e.g., post-elimination scores recorded as zeros and varying judge counts).* 
2. *We treat fan votes as unobserved and report only reproducible baseline proxies at this stage, while keeping a clean plug-in interface for future vote-estimation models.* 
3. *Because the exact season of the show’s return to rank-based aggregation is not confirmed, we label the Season-28 switch as an assumption and will stress-test adjacent cutoffs.* 
4. *Weeks with no elimination or multiple eliminations are handled explicitly in the denominator definitions to avoid inflating consistency claims.* 

---