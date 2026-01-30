Context Pack for AI 
---

**version:** v0.1
**updated:** 2026.1.30_8:00
**owner:** Jincan LI
**Rule:** If any earlier info conflicts, **this file wins**.

我们现在进行美赛论文的写作，这个文件用于作为AI的语境文件，用以兼做团队日志与AI阅读材料
# 1 问题分解与概述 (Problem Decomposition)
## 1.1 问题中文版：
### 题目名称：星光相伴的数据（Data With The Stars）
《与星共舞》（DWTS）是英国《舞动奇迹》的美国版国际电视节目，已播出34季。明星与专业舞者搭档，每周表演舞蹈，由专业评委打分，观众通过电话/网络投票支持喜爱的组合（仅可投票留任，不可投票淘汰）。评委得分与观众投票结合，每周淘汰得分最低的组合，最终3支（或更多）组合晋级决赛并排名。

节目曾采用两种投票结合方式：前两季用“排名法”，因争议（如第2季Jerry Rice评委得分极低仍晋级决赛），第3-27季改用“百分比法”；第27季Bobby Bones评委得分持续低迷却夺冠引发争议后，第28季起调整淘汰规则（先按综合得分确定后两名，再由评委投票淘汰其一），并恢复“排名法”。

### 核心任务
1. 基于提供的34季数据（明星信息、比赛结果、每周评委得分），构建数学模型估算每位明星每周的观众投票数（未知机密数据），验证模型是否与每周淘汰结果一致，并量化估算确定性；
2. 对比“排名法”和“百分比法”两种投票结合方式的结果差异，分析哪种更偏向观众投票；针对有争议的明星（如Jerry Rice、Bobby Bones等），分析两种方式是否会改变其结局，以及“评委从后两名中淘汰”规则的影响；
3. 分析专业舞者及明星特征（年龄、行业等）对比赛结果的影响，及其对评委得分和观众投票的影响差异；
4. 设计更“公平”或“更具观赏性”的投票结合系统，为节目制作方提供建议；
5. 提交含1-2页备忘录的报告，总结核心结论与建议。

### 数据说明
数据文件包含34季明星信息（姓名、行业、年龄等）、比赛结果、每周各评委打分（1-10分，含小数/加分/团队舞平均分），存在评委人数变动、部分赛季无淘汰/多淘汰、淘汰后得分为0等情况。



# 2 本次对话目标交付成果
## 2.2 Deliverable (1 sentence)

交付一个**“隐变量粉丝投票估计 + 规则复盘仿真 + 新投票结合规则建议”**的可复现实验包：对每季每周估计粉丝投票（含不确定性），复盘并对照“排名法/百分比法/底二评委救人”在历史34季上的淘汰与冠军差异，并给出推荐规则与理由.

# 3 结论与进程快照
## 3.1 Claims (3–5 bullets，以 “We claim that …” 开头)

* We claim that **存在一组（非唯一）粉丝投票估计**能在大多数“有淘汰周”上复现实际淘汰结果，并且我们能用量化指标报告其一致性与失败周的模式。 (todo)
* We claim that **“排名法”与“百分比法”在若干赛季/周会产生不同淘汰/最终名次**，且差异主要集中在“评委评分差距小但粉丝偏好强”的对局。 (todo)
* We claim that 对争议选手（如题面示例），“排名法/百分比法/底二评委救人”三种机制下的结果存在可解释的分歧来源，并可用同一套投票估计进行反事实复盘。 (todo)
* We claim that 明星特征（年龄、行业等）与舞伴（职业舞者）会对**评委分数**与**粉丝投票**产生不同方向/强度的影响，从而改变淘汰风险（且这种差异可在跨季切片中稳定观察到）。 (todo)
* We claim that 我们提出的新规则在历史回放下能在**公平性/观赏性/稳定性**之间取得更优权衡，并保持可解释性与低复杂度。 (todo)

## 3.2 Assumption Budget (≤5，每条≤1句，可辩护)

1. 同一赛季同一周的粉丝总投票量只影响**比例/排序**，我们把绝对规模当作可缩放常数处理（关注相对票）。 
2. 评委给分数据视为观测到的“技术表现信号”，允许跨周/跨评委存在噪声但不系统造假。 
3. 每周淘汰由题面规则产生：排名法或百分比法的“综合最低者淘汰”，以及（若启用）“综合底二后评委二选一”。 
4. 选手在被淘汰后不再获得有效周得分（数据中的后续0分代表退出而非真实表演得分）。 
5. 粉丝投票对同一选手在相邻周之间变化相对平滑（可用作正则/先验以提升可识别性）。

## 3.3 数据清洗

- **P0 Data Triage 已跑通（可复现）**：已将原始 wide 格式 `weekX_judgeY_score` 展开为 **season–week–celebrity** 周面板，并按口径生成 **BL-0 baseline** 与一致性 KPI 表，形成后续“fan vote 估计模型”的可插拔输入接口。
- **P0 sanity-check（可写入报告，但仅代表 BL-0）**：Overall（eligible weeks = 264）下，BL-0 的 Hit-Rate 为 **Rank 0.364 / Percent 0.375**，两种规则预测淘汰对象不一致的 FlipRate 为 **0.038**；分 era 切片后仍可复现（见 `tab_baseline_consistency.tex` 与 `fig_fliprate_by_season.pdf`）。
- **重要风险标注（必须在报告轻描淡写但闭环）**：题面明确 season 28 的规则切换赛季“不确定但合理假设为 28”，因此 Rank-era/Percent-era 切片需做 27/28/29 的 stress test；同时数据存在结构性 N/A 周与淘汰后 0 分编码，需要在 active set 口径中显式处理。

(English, report-ready) We have constructed a reproducible season–week–contestant panel and a BL-0 baseline pipeline that produces elimination-consistency metrics and rule-divergence summaries. Under BL-0, the overall hit-rate is 0.364 (rank) and 0.375 (percent) across 264 eligible weeks, with a flip rate of 0.038, serving as a sanity check rather than a final model result. Since the exact season of the return to rank-based aggregation is not confirmed, we explicitly treat the Season-28 switch as an assumption and will stress-test adjacent cutoffs (27/28/29).:contentReference[oaicite:4]{index=4}


# 4 关键指标 (KPI)

## 4.1 KPI table
| KPI name | Status | Direction | Definition (operational) | Aggregation | Slice/window | Baseline(s) | Dependencies / Notes |
|---|---|---|---|---|---|---|---|
| **KPI1 Elimination Hit-Rate (Rank scheme)** | **P0** | higher is better | For each eligible (season, week), compute the predicted eliminated set under **rank-combination** and compare to the true eliminated-at-end-of-week set (from `results`). Multi-elim weeks evaluated by set-match (bottom-k). | Mean over eligible (season, week) | Era: Rank-era seasons {1,2,28–34} (**Season-28 is an assumption; stress-test 27/28/29**). Eligibility rules per Slice/window definitions. | **BL-0:** judge-rank only (uniform fan rank adds constant) | Uses weekly total judge scores from `weekX_judgeY_score`. Withdrawals treated per “Special exit handling”. |
| **KPI1 Elimination Hit-Rate (Percent scheme)** | **P0** | higher is better | For each eligible (season, week), compute the predicted eliminated set under **percent-combination** (judge percent + fan percent proxy/model) and compare to true eliminated set (from `results`). | Mean over eligible (season, week) | Era: Percent-era seasons {3–27}. Eligibility rules per Slice/window definitions. | **BL-0:** judge_percent + uniform fan_percent (1/n_active) | Fan votes are unobserved; BL-0 is a reproducible proxy for P0. |
| **KPI3 Rule Divergence Rate (Rank vs Percent)** | **P0** | **descriptive (no “better”)** | Share of eligible (season, week) where the predicted eliminated set differs between rank vs percent schemes (holding the same baseline/proxy vote input). | Ratio over eligible (season, week) | Same eligibility; can be grouped by season / era. | **BL-0 only** | Report as “impact magnitude” rather than optimization target. |
| **KPI2 Vote Identifiability (interval tightness)** | **P1** | higher is better | For each (season, week, celebrity), derive a feasible interval of fan vote (share or rank) consistent with observed elimination outcome under a specified rule; define identifiability as `1/(interval_width + ε)` and summarize. | Median (or quantiles) over (celebrity, week), then aggregated by season/phase | Season; phase (early/mid/late); “controversial” weeks (close judge totals) | Not defined in P0 | **Requires**: (i) explicit mathematical form of rule & elimination mechanism (incl. bottom-two judges save if used), (ii) definition of vote variable (share vs rank), (iii) choice of ε. Until these are fixed, KPI2 is registry-only. |
| **Constraint KPI1 Fan Agency Floor** | **P1** | higher is better | Under replay, enforce that “fan top-1 (or top-x%) still eliminated” rate is below a chosen threshold, or equivalently maximize a fan-retention lower bound. | Ratio over eligible (season, week) | By rule variant; season phase | Not defined in P0 | **Requires**: fan vote estimate (`fan_rank_est` or `fan_share_est`) and a defined x% / threshold. In P0, keep interface only; do not claim numeric compliance. |
| **Constraint KPI2 Rule Simplicity** | **P2** | lower is better | Complexity score = (# tunable hyperparameters) + external-info dependency flag (0/1). | Per rule variant (not data-aggregated) | By rule variant | N/A | This is a **policy/implementability** metric, not computed from the CSV; used in memo/decision section, not in data cleaning. |


# 5 数据处理：

## 5.1 Data snapshot (only what affects conclusions) (v0.1 for Data Triage)


- **Source of truth**: COMAP dataset `2026_MCM_Problem_C_Data.csv` (seasons 1–34; weekly judge scores + results/placement + basic contestant attributes).

**Key columns (official):**
```
P0 必要字段（没有就做不了）

* `season`（赛季编号） 
* `celebrity_name`（选手唯一标识） 
* `results` 或能推断淘汰周/最终名次的信息（用于周淘汰真值与赛季结局真值） 
* `placement`（最终名次，用于冠军/决赛对比） 
* 每周评委打分列 `weekX_judgeY_score`（用于构造每周评委总分/排名/百分比） 

P1 重要字段（有则显著提升）

* `ballroom_partner`（职业舞者，用于舞者效应分析与分层） 
* `celebrity_age_during_season`、`celebrity_industry`（明星特征：解释粉丝/评委差异） 
* `celebrity_homecountry/region`、`celebrity_homestate`（区域切片：潜在票仓/文化偏好代理） 
```

- **Cleaning rules (≤5):**
  1) Reshape wide `weekX_judgeY_score` into long panel: one row per (season, week, celebrity).
  2) Compute `total_judge_score = sum(weekX_judgeY_score, skipna)`; do not impute missing judges.
  3) Define `active` by excluding weeks with all-NaN scores and weeks after exit (Eliminated Week k / inferred withdraw week).
  4) Treat post-exit zeros as encoding artifacts (kept in raw but excluded from active set and KPI denominators).
  5) Handle weeks with 0 or >1 eliminations explicitly in KPI denominators (no-elim excluded; multi-elim via set-match).
- Known caveats (≤3):
  - Judge index `judgeY` is not a persistent identity across weeks/seasons; only within-week totals/ranks are used.
  - The exact season of the return to rank-based aggregation is not confirmed; we assume Season 28 and will stress-test adjacent cutoffs.
  - Fan votes are unobserved by design; current baselines use only reproducible proxies and keep a plug-in interface for vote estimates.


- **Panel granularity**: season–week–celebrity (built by reshaping `weekX_judgeY_score` wide columns into long rows).
- **P0 eligibility / active-set**: a contestant is active in (season, week) iff at least one judge score exists for that week and the week is not after the exit week; post-elimination scores recorded as zeros are treated as inactive encoding rather than new performances.:contentReference[oaicite:6]{index=6}
- **Known caveats (must be reported)**:
  1) The return-to-rank season is not known with certainty; we use Season-28 as an explicit assumption and will stress-test 27/28/29 cutoffs.:contentReference[oaicite:7]{index=7}
  2) Judge4 may be N/A because some weeks have only 3 judges; we aggregate with `skipna` and do not track judge identity across weeks.:contentReference[oaicite:8]{index=8}
  3) There exist weeks with no elimination and weeks with multiple eliminations; we handle them explicitly in KPI denominators to avoid inflated consistency claims.:contentReference[oaicite:9]{index=9}



## 5.2 最大的数据缺口/口径风险（≤3条）

1. **规则切换季不确定**（题面说“合理假设第28季”但非确定），需要把“规则版本”作为敏感性场景而不是硬编码单点。 
2. **“无淘汰/多淘汰/团队舞平均/加分”周**会改变分数可比性与淘汰约束形式，清洗时必须先标注这些周再建模。 
3. **评委身份不固定且列名为 JudgeY**（跨周/跨季不可直接对齐同一评委），因此“评委偏好”只能做为“当周评委组”层面的随机效应或被忽略。 

## 5.3 P0 triage outcome (reproducible baseline + interfaces)

**CN（团队同步/写作可用）**  
我们已将官方 `weekX_judgeY_score` 从宽表展开为 season–week–celebrity 的周面板，并按 registry 的 active/退出口径构造了 `active / exit_type / exit_week / true_elim_flag` 等最小标签（后续模型与仿真只依赖该面板与规则函数，不依赖额外 EDA 结论）。在此基础上，我们实现了可复现的 BL-0（judge-only proxy）并产出一致性对照表：Rank-scheme 与 Percent-scheme 的淘汰命中率（KPI1）以及两规则预测淘汰集合不同的比例（KPI3, FlipRate）。注意：面板中保留了“结构性缺失周(all judges NaN)”以及“退出后 0 分延展”等编码痕迹，但它们均被标记为 `active=False`，不会进入 KPI 分母/计算；另存在极少数“淘汰当周总分=0”的边界样本，已记录为风险点，后续在敏感性分析中单独 stress-test。

**EN (report-ready)**  
We reshape the official weekly judge-score columns into a season–week–contestant panel and construct deterministic eligibility/exit labels (`active`, `exit_type`, `exit_week`, `true_elim_flag`) as the canonical input to downstream vote-estimation and replay simulation. On top of this panel, we implement a fully reproducible BL-0 (judge-only proxy) and report baseline consistency metrics: elimination hit-rate under rank- and percent-combination (KPI1) and the rule divergence rate between the two schemes (KPI3, FlipRate). Structural missingness (all-judge-NaN weeks) and post-exit zero-score encodings are retained for auditability but excluded from denominators via `active=False`; rare edge cases (e.g., elimination-week scores recorded as zeros) are documented and will be stress-tested in the robustness stage.

**BL-0 baseline summary (from `output/table/tab_baseline_consistency.tex`)**

| Slice | N_weeks (eligible) | Hit-Rate (Rank) | Hit-Rate (Percent) | FlipRate (Rank vs Percent) |
|---|---:|---:|---:|---:|
| Overall | 264 | 0.364 | 0.375 | 0.038 |
| Rank-era (S1-2,28-34) | 66 | 0.348 | 0.364 | 0.015 |
| Percent-era (S3-27) | 198 | 0.369 | 0.379 | 0.045 |

**Canonical artifacts (for reproducibility & downstream agents)**  
- `output/table/intermediate_weekly_panel.csv` (canonical weekly panel; plug-in input)  
- `output/table/intermediate_baseline_preds.csv` (week-level predictions; audit/debug)  
- `output/table/tab_baseline_consistency.tex` (LaTeX table for KPI1/KPI3, BL-0)  
- `output/figure/fig_fliprate_by_season.pdf` (optional L2: where rules diverge by season; supports KPI3 narrative)



# 6 关键模型 

# 7 Notation Chart(记号说明)

# 8 Work-in-progress outputs (pre-contest can be empty)

- Expected figure set (L0/L1/L2): see `fig_manifest.md`(todo)

| Artifact (engine path) | What it is | Used for (Claim/KPI/Slice) |
|---|---|---|
| `output/table/tab_baseline_consistency.tex` | L1 summary table of BL-0 elimination hit-rate and FlipRate across slices | KPI1 (Rank/Percent Hit-Rate), KPI3 (FlipRate); slices: Overall / Rank-era / Percent-era |
| `output/table/intermediate_weekly_panel.csv` | season–week–celebrity weekly panel with active/exit labels and judge-based rank/percent features | Minimal input interface for fan vote estimation models; supports all downstream KPI recomputation |
| `output/table/intermediate_baseline_preds.csv` | season–week baseline predictions + eligibility flags (true_k, true_elims, pred sets, match flags, flip) | Debug / audit trail; enables exact reproduction of tab_baseline_consistency |
| `output/figure/fig_fliprate_by_season.pdf` | FlipRate by season under BL-0 | L1 evidence for “rule divergence varies by season” (descriptive KPI3) |



# 9 风险与回滚

暂无

# 10 鲁棒性清单

暂无

# 11 文献清单

暂无

# 12 重大决策记录

暂无



# 附录 1 已有文件

## 1.1 文件结构

```
2026_MCM\
   snapshots\
    chapters\(这个文件夹用以装我们文章各个章节的内容以避免主内容的拥挤)
        0_summarysheet.tex
        1_introduction.tex
        2_problem_decomposition_and_analysis.tex
        3_data_processing_and analysis.tex
        4_modeling.tex
        5_results.tex
        6_memo.tex
        7_conclusion
        myref.bib
        report_on_use_of_ai.tex
    files_for_ai\                           (与AI的交接文档)
        group_discussion_files\             (这是对内交流文档)
            kaichangbai.md                  (这是使用AI时的开场白)
            log_A_d_t.md                    (这是队友之间交付的文档)
            prism_operation_hand_book.md    (prism的操作手册)
        dynamic_files\
            fig_tabel_manifest.md           (图、表的清单，用于与AI对其颗粒度)
            desicion_log.md                 (重大方向变化，由prism和Jincan LI共同完成)
            context_packed_for_ai.md        (与AI对其颗粒度的核心文件)
            kpi_registery                   (记录核心KPI)
        constans_files\
            framing_spec_playbook.md        (playbook for Framing/spec GPT)
            data_playbook.md                (playbook for data GPT & Visualization/Evidence GPT)
            modeling_playbook.md            (playbook for modeling GPT)
            modeling_ticket_enhanced.md     (interaction playbook for modeling GPT)
            writing_rules.md                (playbook for prism & writer)
            writing_section_template.md     (playbook for prism & writer)
            visual_play_book.md             (playbook for data GPT & Visualization/Evidence GPT)
    src\                                    (核心代码)        
        eval\                               (评估)
        model\                              (模型)
        sim\                                (仿真)
        viz\                                (可视化)
        src_handbook.md                     
    outputs\
        data\
        fig\
        tab\
    2625838.aux
    2625838.bbl
    2625838.blg
    2625838.log
    2625838.out
    2625838.pdf
    2625838.synctex.gz
    2625838.tex
    2625838.toc
```
## 1.2 文件说明

# 3 report的结构与引用规范
日志：在v0.1版本中，我们沿用的是上此比赛时的文章先作为基础框架，具体内容与此次比赛无关，同时在基于本次内容得到具体实施的框架后会标注相关的章节引用标准。

```
Summary sheet 
1 Introduction 
2 Problem Decomposition and Analysis
    2.1 Objective and decision scope
    2.2 Data-driven closed loop: three tasks
    2.3 Key modeling assumptions (made explicit)
    2.4 Outputs and validation plan
    2.5 Two-route design: performance vs. interpretability
3 Data Processing and Analysis
    3.1 Data Cleaning Principles and Validation
        3.1.1 Cleaning Principles
        3.1.2 Data Cleaning Operations
        3.1.3 Data Cleaning outcomes and Validation
    3.2 Data Visualization
    3.3 Empirical Findings from EDA
    3.4 Feature Engineering
    3.5 Synthesis of Findings
4 Modeling
    4.1 Overview and Modeling Philosophy
    4.2 Model 1: Short-Term Passenger Arrival Forecasting (Task 1)
        4.2.1 Target and Time Discretization
        4.2.2 Feature Engineering
        4.2.3 Model Choice and Validation Protocol
        4.2.4 Output to Downstream Control
        4.3.1 Mode Features with Operational Meaning
        4.3.2 Unsupervised Clustering and Interpretability
        4.3.3 Cluster-to-Mode Naming
        4.3.4 Online Mode Classification
    4.4 Model 3: Mode-Aware Dynamic Parking via Weighted 𝑘-Median (Task 3)
        4.4.1 Mode-Conditioned Floor Demand Distribution
        4.4.2 Optimization Formulation (Weighted 1D 𝑘-Median)
        4.4.3 Solution and Assignment
        4.4.4 Execution Policy
    4.5 Interpretable Baseline and Fallback Policy (Route B)
        4.5.1 Task 1: time-of-day baseline + regime 𝐴𝑅(1)
        4.5.2 Task 2: Rule-based real-time traffic state classification Model.
        4.5.3 Task 3: zone-based state-aware parking rule
        4.5.4 Deployment Fallback: When to Switch from Route A to Route B
    4.6 Simulation-Based Evaluation (Baselines and Metrics) 
        4.6.1 Baselines
        4.6.2 Metrics
        4.6.3 Discussion
    4.7 Robustness and Sensitivity (Brief) 
5 Result Analysis and Robustness Testing 
    5.1 Performance Evaluation 
    5.2 Stress Tests and Robustness
    5.3 Robustness and Sensitivity
6 Memo to Management
7 Conclusion
A Appendix: Data, Algorithms, and Reproducibility
    A.1 Appendix A. Data Dictionary and Preprocessing Details
    A.2 Appendix B. Feature Engineering (Task 1 & Task 2)
    A.3 Appendix C. Mode Clustering Configuration and Naming
    A.4 Appendix D. Weighted 1D 𝑘-Median Solution Sketch
    A.5 Appendix E. Simulation Assumptions and Parameters
    A.6 Appendix F. Additional Results (Stress Tests)
    A.7 Appendix G. Reproducibility Checklist
    A.8 Appendix H. Interpretable Baseline and Fallback Policy (Route B)
    A.9 Validation 21
B Complete Files for Problem B 21
```

# 附录 3 参考baseline(低优先级)

## 2-hour Baseline Plan（含对照组与输出指标）

1. 读入CSV→按 `(season, week)` 聚合出每对选手的**周评委总分**与**当周在赛选手集合**，用 `results`/后续0分推断“当周淘汰集合”。 
2. **对照组A（Judge-only）**：假设粉丝票完全与评委一致（粉丝排名=评委排名），回放两种合并法→算 KPI1。
3. **基线B（Minimal-feasible votes）**：为每周求一组“粉丝投票秩/比例”使得合并后最低者=实际淘汰者（可用简单约束求解/贪心），同时输出每人“可行秩区间”→算 KPI1+KPI2。
4. 用同一组投票估计对每季同时回放“排名法/百分比法/底二评委救人（情景）”→输出 KPI3（差异周占比、影响到的选手/冠军列表）。
5. 交付物：1张 KPI 汇总表 + 1个“规则差异热力图(季×周)” + 争议选手的反事实小表（本周评委排名/估计粉丝排名/三规则淘汰结论）。

## 7. Plan B（≤3条降级仍可交付）

1. 若投票“绝对数”不可识别：改为只估计**粉丝投票秩/分位**并完成 KPI1/KPI3 与争议复盘（放弃绝对票数解释）。
2. 若“多淘汰/特殊周”清洗来不及：先仅在“标准单淘汰周”建模并声明适用域，其余周做定性讨论与敏感性占位。
3. 若特征变量缺失或噪声大：舞者/年龄/行业效应分析降级为“仅对评委总分与生存周数的相关性/分层描述”，不做因果解释。