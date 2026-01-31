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

下面给你一份**“按你们题目 & 模型模块对齐”的权威文献列表**：每条都包含**怎么用（写进哪一段/支撑哪类口径与论证）**，并附**可直接点开的链接**（我把 URL 放在代码块里，便于你们复制到参考文献管理器或 BibTeX 备注里）。

---

## 0) 题面与编码口径（必须引用，最高优先级）

### 1. COMAP 2026 MCM Problem C（官方题面 PDF）

**怎么用：**

* 作为你们所有“规则回放（rank vs percent）”“N/A / 0 分编码”“赛季分段（era slice）”的唯一权威锚点。
* 报告里写“数据编码/规则定义完全遵循题面”时必须引用它。 ([COMAP 竞赛][1])

```text
https://www.contest.comap.com/undergraduate/contests/mcm/contests/2026/problems/2026_MCM_Problem_C.pdf
```

---

## 1) 约束优化 / 可识别性（支撑你们“欠定反推 fan 份额 + 约束 + 正则/平滑”的数学合法性）

### 2. Stephen Boyd & Lieven Vandenberghe, *Convex Optimization*（2004）

**怎么用：**

* 用于你们把“未知 fan votes / weights”写成**带约束的优化问题（QP/凸优化）**时的权威背书：可行域、KKT、松弛、稳定性等。 ([Stanford University][2])

```text
https://stanford.edu/~boyd/cvxbook/
```

### 3. Sébastien Bubeck, *Convex Optimization: Algorithms and Complexity*（Foundations and Trends in ML, 2015）

**怎么用：**

* 当你们需要说明“我们用的优化求解/复杂度/收敛性属于现代可扩展凸优化范式”时，用这本比只引 2004 更“靠近今天且仍权威”。 ([Sbubeck][3])

```text
https://sbubeck.com/Bubeck15.pdf
```

### 4. Boyd et al., “Distributed Optimization and Statistical Learning via ADMM”（Foundations and Trends in ML, 2011）

**怎么用：**

* 如果你们的实现里出现“分块变量、交替更新、带惩罚项的可复现求解流程”，用 ADMM 综述来背书“工程可落地、可扩展求解”。 ([Stanford University][4])

```text
https://stanford.edu/~boyd/papers/admm_distr_stats.html
```

### 5. Benning & Burger, “Modern Regularization Methods for Inverse Problems”（Acta Numerica, 2018）

**怎么用：**

* 你们“用淘汰/名次这种弱信号去反推不可观测 fan 投票”本质是**不适定反问题**；用这篇权威综述证明“正则化/先验/稳健性检查”是标准做法，而不是拍脑袋。 ([Cambridge University Press & Assessment][5])

```text
https://www.cambridge.org/core/journals/acta-numerica/article/modern-regularization-methods-for-inverse-problems/1C84F0E91BF20EC36D8E846EF8CCB830
```

### 6. Kaipio & Somersalo, *Statistical and Computational Inverse Problems*（Springer, 2005/2006）

**怎么用：**

* 用于你们写“可识别性不是唯一解，而是**可行集合/区间**；以及不确定性如何传播到结论（KPI2 叙事）”的统计反问题权威参考。 ([Springer][6])

```text
https://link.springer.com/book/10.1007/b138659
```

### 7. Tikhonov & Arsenin, *Solutions of Ill-posed Problems*（1977）

**怎么用：**

* 若你们报告里希望一句话把“为什么需要正则（平滑/最小扭曲）”钉死为经典理论来源，可引用 Tikhonov 正则的源头级文献。 ([Google 图书][7])

```text
https://books.google.com/books/about/Solutions_of_Ill_posed_Problems.html?id=ECrvAAAAMAAJ
```

---

## 2) 排名/规则差异与聚合（支撑你们 KPI3 FlipRate：为什么规则会系统性翻转）

### 8. Brandt et al. (eds.), *Handbook of Computational Social Choice*（Cambridge, 2016）

**怎么用：**

* 用于支撑“不同投票/聚合规则会导致不同社会选择结果（翻转、争议、非直觉结果）”，把你们的“规则回放对照”写成计算社会选择的标准范式。 ([Cambridge University Press & Assessment][8])

```text
https://www.cambridge.org/core/books/handbook-of-computational-social-choice/8AF63E87F76A5FC974D5E73536C52BD6
```

### 9. Donald G. Saari, *Decisions and Elections: Explaining the Unexpected*（Cambridge, 2001）

**怎么用：**

* 适合写进 memo/讨论段：解释“同一偏好/分数输入，在不同聚合规则下出现‘意外淘汰/逆转’是机制性现象”，从理论上支持你们 FlipRate 的解释口径。 ([Cambridge University Press & Assessment][9])

```text
https://www.cambridge.org/core/books/decisions-and-elections/C5A8C567FA56349016B25EF04AFA7170
```

### 10. Kenneth Arrow, *Social Choice and Individual Values*（1951；后续版本再版）

**怎么用：**

* 当你们要强调“不存在完美无瑕的投票制度，因此我们用多 KPI + 约束来权衡可解释性/公平性/可执行性”时，这是最权威的理论锚点。 ([Yale University Press][10])

```text
https://yalebooks.yale.edu/book/9780300179316/social-choice-and-individual-values/
```

---

## 3) Rank aggregation / 排序数据（支撑你们把周内表现转成排序、并比较两种方案）

### 11. R. L. Plackett, “The Analysis of Permutations”（JRSS-C, 1975）

**怎么用：**

* 如果你们要把“周内 contestants 的排序/淘汰”表述为**permutation / ranking**对象（而非普通连续变量），Plackett 是经典概率排序模型的重要来源。 ([OUP Academic][11])

```text
https://academic.oup.com/jrsssc/article/24/2/193/6953554
```

### 12. Wang et al., “A Survey on Rank Aggregation”（IJCAI 2024 Survey Track）

**怎么用：**

* 用于把你们的“rank vs percent 输出差异”放进**近年 rank aggregation 研究脉络**：你们做的是“同一对象多信号排序的聚合/对照”的特例。 ([IJCAI][12])

```text
https://www.ijcai.org/proceedings/2024/915
```

### 13. Maystre & Grossglauser, “Fast and Accurate Inference of Plackett–Luce Models”（NeurIPS 2015）

**怎么用：**

* 若你们后续想用概率排序模型做“扩展 baseline/稳健性对照”（不一定要主线采用），这篇是 ML 社区在 Plackett–Luce 推断上非常常用、可信度高的参考。 ([NeurIPS Proceedings][13])

```text
https://proceedings.neurips.cc/paper/2015/hash/2a38a4a9316c49e5a833517c45d31070-Abstract.html
```

---

## 4) 成分数据（vote share 是 sum-to-one 的比例向量：写对统计口径很关键）

### 14. John Aitchison, *The Statistical Analysis of Compositional Data*（1986）

**怎么用：**

* fan vote **share**（各选手比例且总和为 1）属于典型 compositional data；引用 Aitchison 用来说明“不能把 share 当普通数做线性处理，应使用 log-ratio/合适的概率模型”。 ([ACM数字图书馆][14])

```text
https://dl.acm.org/doi/10.5555/17272
```

### 15. Pawlowsky-Glahn, Egozcue, Tolosana-Delgado, *Modeling and Analysis of Compositional Data*（Wiley, 2015）

**怎么用：**

* 用于“更靠近今天”的 compositional 工具背书：你们若在方法段写 log-ratio、或解释 share 的相关/回归，这是现代教材级权威。 ([Wiley Online Library][15])

```text
https://onlinelibrary.wiley.com/doi/book/10.1002/9781119003144
```

### 16. Filzmoser, Hron, Templ, *Applied Compositional Data Analysis*（Springer, 2018）

**怎么用：**

* 适合写进“实现细节/附录”：强调 log-ratio 处理与稳健统计的实践性，给你们后续可视化或敏感性分析提供规范语言。 ([Springer][16])

```text
https://link.springer.com/book/10.1007/978-3-319-96422-5
```

---

## 5) 仿真与敏感性（支撑你们“规则回放仿真 + 参数压力测试”的方法论）

### 17. Averill M. Law, *Simulation Modeling and Analysis*（6th ed., 2024）

**怎么用：**

* 你们的“按规则回放一季、比较淘汰/冠军差异”就是 simulation study；引用它可把仿真设计写得更标准：输入/输出、对照方案、复现性、实验协议。 ([麦格劳希尔][17])

```text
https://www.mheducation.com/highered/mhp/product/simulation-modeling-analysis-sixth-edition.html
```

### 18. Saltelli et al., *Global Sensitivity Analysis: The Primer*（Wiley, 2008）

**怎么用：**

* 用于你们写“对关键超参（如权重 α、正则强度 λ、bottom-two/judges-save 触发规则）做系统敏感性/压力测试”的权威入口。 ([Wiley Online Library][18])

```text
https://onlinelibrary.wiley.com/doi/book/10.1002/9780470725184
```

---

## 6) 你们在报告里会用到的 Kendall/Spearman：给它们配原始权威来源

### 19. M. G. Kendall, “A New Measure of Rank Correlation”（Biometrika, 1938）

**怎么用：**

* 当你们用 Kendall’s τ 评价“周内排序/综合排序 vs 最终名次/淘汰序”的一致性，这是 τ 的源头级引用。 ([OUP Academic][19])

```text
https://academic.oup.com/biomet/article-abstract/30/1-2/81/176907
```

### 20. C. Spearman, “The Proof and Measurement of Association between Two Things”（1904）

**怎么用：**

* 当你们用 Spearman’s ρ 作为“秩相关”的替代指标或稳健性对照，这是原始文献（可作为经典引用）。 ([Shippensburg University][20])

```text
https://webspace.ship.edu/pgmarr/Geo441/Readings/Spearman%201904%20-%20The%20Proof%20and%20Measurement%20of%20Association%20between%20Two%20Things.pdf
```

---

# 你们实际落地时怎么选（避免引用太多）

如果你们只想保留 **8–10 条核心引用**（最常见、最干净），我建议优先保留：
**1, 2, 5, 6, 8, 9, 12, 15, 17, 18**
（题面 + 优化/反问题/正则 + 社会选择/规则差异 + 近年 rank aggregation 综述 + compositional + 仿真/敏感性）

[1]: https://www.contest.comap.com/undergraduate/contests/mcm/contests/2026/problems/2026_MCM_Problem_C.pdf?utm_source=chatgpt.com "2026 MCM Problem C: Data With The Stars"
[2]: https://stanford.edu/~boyd/cvxbook/?utm_source=chatgpt.com "Convex Optimization – Boyd and Vandenberghe"
[3]: https://sbubeck.com/Bubeck15.pdf?utm_source=chatgpt.com "Convex Optimization: Algorithms and Complexity"
[4]: https://stanford.edu/~boyd/papers/admm_distr_stats.html?utm_source=chatgpt.com "Distributed Optimization and Statistical Learning via the ..."
[5]: https://www.cambridge.org/core/journals/acta-numerica/article/modern-regularization-methods-for-inverse-problems/1C84F0E91BF20EC36D8E846EF8CCB830?utm_source=chatgpt.com "Modern regularization methods for inverse problems"
[6]: https://link.springer.com/book/10.1007/b138659?utm_source=chatgpt.com "Statistical and Computational Inverse Problems | SpringerLink"
[7]: https://books.google.com/books/about/Solutions_of_Ill_posed_Problems.html?id=ECrvAAAAMAAJ&utm_source=chatgpt.com "Solutions of Ill-posed Problems"
[8]: https://www.cambridge.org/core/books/handbook-of-computational-social-choice/8AF63E87F76A5FC974D5E73536C52BD6?utm_source=chatgpt.com "Handbook of Computational Social Choice"
[9]: https://www.cambridge.org/core/books/decisions-and-elections/C5A8C567FA56349016B25EF04AFA7170?utm_source=chatgpt.com "Decisions and Elections"
[10]: https://yalebooks.yale.edu/book/9780300179316/social-choice-and-individual-values/?utm_source=chatgpt.com "Social Choice and Individual Values"
[11]: https://academic.oup.com/jrsssc/article/24/2/193/6953554?utm_source=chatgpt.com "Analysis of Permutations | Journal of the Royal Statistical ..."
[12]: https://www.ijcai.org/proceedings/2024/915?utm_source=chatgpt.com "A Survey on Rank Aggregation"
[13]: https://proceedings.neurips.cc/paper/2015/hash/2a38a4a9316c49e5a833517c45d31070-Abstract.html?utm_source=chatgpt.com "Fast and Accurate Inference of Plackett–Luce Models - NIPS"
[14]: https://dl.acm.org/doi/10.5555/17272?utm_source=chatgpt.com "The statistical analysis of compositional data: | Guide books"
[15]: https://onlinelibrary.wiley.com/doi/book/10.1002/9781119003144?utm_source=chatgpt.com "Modelling and Analysis of Compositional Data"
[16]: https://link.springer.com/book/10.1007/978-3-319-96422-5?utm_source=chatgpt.com "Applied Compositional Data Analysis - Springer Link"
[17]: https://www.mheducation.com/highered/mhp/product/simulation-modeling-analysis-sixth-edition.html?utm_source=chatgpt.com "Simulation Modeling and Analysis, Sixth Edition"
[18]: https://onlinelibrary.wiley.com/doi/book/10.1002/9780470725184?utm_source=chatgpt.com "Global Sensitivity Analysis. The Primer"
[19]: https://academic.oup.com/biomet/article-abstract/30/1-2/81/176907?utm_source=chatgpt.com "NEW MEASURE OF RANK CORRELATION | Biometrika"
[20]: https://webspace.ship.edu/pgmarr/Geo441/Readings/Spearman%201904%20-%20The%20Proof%20and%20Measurement%20of%20Association%20between%20Two%20Things.pdf?utm_source=chatgpt.com "The Proof and Measurement of Association between Two ..."

下面给你两样东西：

1. **Reference 映射表**：按你们论文结构（Framing/Data/Baseline/Method/Simulation/Sensitivity/Discussion）把每条文献“放哪里、用来支撑什么”写清楚。
2. **第 1 条（COMAP 题面 PDF）怎么引用**：给你可直接用的 BibTeX 条目 + LaTeX 正文引用示例（含“访问日期/本地备份”最佳实践）。

---

## 1) References 映射表（章节 → 引用 → 用法一句话）

> 你们引用的最小目标是：**每个关键主张至少有 1 条“题面权威” + 1 条“方法论权威”。**
> 下面按“最常见 MCM 报告结构”映射；你们如果章节名不同，照同类位置放即可。

### A. Introduction & Problem Restatement（问题重述 / 任务拆解）

* **[R1] COMAP 2026 Problem C（题面）**
  用法：锚定任务目标、规则变迁（rank vs percent）、数据编码说明的权威来源。
* **[R8] Handbook of Computational Social Choice (2016)** 或 **[R9] Saari (2001)**
  用法：用 1–2 句把“规则差异会引发结果翻转/争议”提升为理论动机（支撑你们做 KPI3 FlipRate）。

### B. Data & Encoding Notes（数据与编码口径；不做泛 EDA）

* **[R1] COMAP 题面**（必须）
  用法：引用 0 分编码、N/A 的语义、赛季分段（era slices）的来源；作为“active set/分母规则”的根。
* （可选）**[R17] Law (2024 Simulation Modeling and Analysis)**
  用法：用来写“我们保留编码痕迹用于审计，但通过 eligibility/denominator 规则排除偏差”的“实验协议”语气（更像工程仿真标准）。

### C. Baselines（BL-0 及其定位）

* **[R1] COMAP 题面**
  用法：baseline 的规则回放必须说清楚“严格遵循题面规则定义”。
* **[R2] Boyd & Vandenberghe (2004 Convex Optimization)**（如果 baseline 里出现任何“优化/约束”就引用，否则可不引）
  用法：说明 baseline 只是 sanity check/对照，不代表最终投票推断。

### D. Proposed Method Overview（方法总览：vote estimation + replay simulation）

* **[R2] Boyd & Vandenberghe (2004)**
  用法：把“未知 fan vote share 的估计”写成带约束的凸优化/二次规划（QP）问题的总背书。
* **[R5] Benning & Burger (2018)** +（可选）**[R6] Kaipio & Somersalo (2005/6)**
  用法：把“用淘汰/名次弱信号反推隐变量”归类为 ill-posed inverse problem，并解释“需要正则/可行集合（identifiability）”。
* **[R3]/[R4] Bubeck (2015) / ADMM (2011)**（二选一）
  用法：让“求解与可扩展性”更现代（尤其你们若写了迭代算法/分块求解）。

### E. Vote Share Modeling Details（份额变量、sum-to-one 约束、解释性）

* **[R14] Aitchison (1986)**（经典锚）
  用法：一句话解释“vote share 是 compositional data，不能当普通连续变量”。
* **[R15] Pawlowsky-Glahn et al. (2015)** 或 **[R16] Filzmoser et al. (2018)**（二选一）
  用法：给“现代 compositional 工具/解释”加一个近十年权威来源（更贴近今天）。

### F. Replay Simulation & Rule Comparison（规则回放仿真、KPI3 FlipRate）

* **[R1] COMAP 题面**（必须）
  用法：规则回放的定义、era 切片、淘汰/无淘汰/多淘汰处理口径。
* **[R17] Law (2024)**
  用法：把你们“回放作为 simulation experiment”的流程写得正规：对照组、可复现、实验协议。
* **[R8]/[R9]/[R10]（社会选择理论，选 1–2 个）**
  用法：解释 FlipRate 是机制性现象而非噪声；支撑你们的讨论段落。

### G. Metrics & Evaluation（KPI1/KPI2/KPI3、秩相关）

* **[R19] Kendall (1938)**
  用法：如果你们报告 Kendall’s τ（或把它当稳健性补充），这是权威来源。
* **[R20] Spearman (1904)**（可选）
  用法：如用 Spearman ρ 作对照，则给原始引用。
* （可选）**[R12] IJCAI 2024 Rank Aggregation Survey**
  用法：把你们“比较两种 scheme 的排名/淘汰差异”放入近年 rank aggregation 的脉络（Related Work/Discussion 里用更合适）。

### H. Sensitivity / Robustness（敏感性：cutoff、tie-handling、α/λ）

* **[R18] Saltelli et al. (2008)**
  用法：敏感性/压力测试的方法论锚点（你们就算只做少量 stress tests，也能引用它来规范表述）。
* **[R5] Benning & Burger (2018)**（如果你们把敏感性写成“ill-posed 的不确定性管理”）
  用法：把“解不唯一/参数扰动”解释为反问题的常态，并说明我们用 stress tests 控制。

### I. Discussion & Limitations（局限性与建议）

* **[R1] COMAP 题面**
  用法：重申我们只在题面可观测数据内做推断，fan votes 不可观测；所有结论是“可复现仿真与约束推断”的产物。
* **[R10] Arrow (1951)**（可选）
  用法：当你们说“没有完美规则，因此我们用多 KPI 平衡 agency/simplicity/fairness”时可加这一条“高举轻放”的理论背书。


### 2.2 正文里怎么写（LaTeX 示例）

你可以这样写（两种常见写法）：

**写法 A：在数据口径段落第一次出现就引用**

```tex
The scoring rules and the season-wise voting scheme (rank-based vs. percent-based) follow the official COMAP problem statement. \cite{comap2026_mcm_problem_c}
```

**写法 B：把它当“唯一规则锚点”强调一次**

```tex
All rule definitions, data encodings (e.g., N/A and post-exit zeros), and evaluation slices are taken verbatim from the official problem statement. \cite{comap2026_mcm_problem_c}
```

> 小技巧：你们后面所有“口径争议”都可以回指这条引用，避免在正文里反复解释“我们没编造”。
---

# 12 重大决策记录

暂无



# 附录 1 已有文件

## 1.1 文件结构

```
2026_MCM\
   snapshots\
    chapters\(这个文件夹用以装我们文章各个章节的内容以避免主内容的拥挤)
    0_summary_sheet.tex
    1_introduction.tex
    2_problem_decoposition_and_analysis.tex
    3_data_processing_and_analysis.tex
    4_task_a_fan_vote_inference_model.tex
    5_rule_reply_volting_system_and_counterfactuials.tex
    6_impact_analysis_task_d1_prodancers_and_celebrity_attributes.tex
    7_task_d2_new_rule_design_and_stress_testing.tex
    8_conclusion.tex 
    9_memo.tex
    appendix_a.tex
    myref.bib
    report_on_use_of_ai.tex
    files_for_ai\                           (与AI的交接文档)
        group_discussion_files\             (这是对内交流文档)
            first_stage_modeling.md         (建模第一阶段)
            kaichangbai.md                  (这是使用AI时的开场白)
            log_A_d_t.md                    (这是队友之间交付的文档)
            prism_operation_hand_book.md    (prism的操作手册)
        dynamic_files\
            fig_tabel_manifest.md           (图、表的清单，用于与AI对其颗粒度)
            desicion_log.md                 (重大方向变化，由prism和Jincan LI共同完成)
            context_packed_for_ai.md        (与AI对其颗粒度的核心文件)
            kpi_registery.md                (记录核心KPI)
            data_agent_triage_ticket.md     (data Agent的工单)
        constans_files\
            framing_spec_playbook.md        (playbook for Framing/spec GPT)
            data_playbook.md                (playbook for data GPT & Visualization/Evidence GPT)
            modeling_playbook.md            (playbook for modeling GPT)
            modeling_ticket_enhanced.md     (interaction playbook for modeling GPT)
            writing_rules.md                (playbook for prism & writer)
            writing_section_template.md     (playbook for prism & writer)
            visual_play_book.md             (playbook for data GPT & Visualization/Evidence GPT)
    src\                                    (核心代码) 
        LI_data_only_triage\
            explaination.md
            manifest.json
            p0_triage_build_weekly_panel.py
        szeto_play_with_data/
            2026_MCM_Problem_C_Data.csv src
            add_rank_of_week.py src
            ADDED_COLUMNS.md
            compute_controversial.py
            output.csv
            preprocessing.py
            run.py
            workflow.py                
        eval\                               (评估)
        model\                              (模型)
        sim\                                (仿真)
        viz\                                (可视化)
        src_handbook.md     
    data_raw\
        2026_MCM_Problem_C_Data.csv
    outputs\
        data_cleaned\
            intermediate_baseline_preds.csv
            intermediate_weekly_panel.csv
        fig\
            fig_fliprate_by_season.pdf
        tab\
            tab_baseline_consistency.tex
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
**0 Summary Sheet**
**1 Introduction**（问题重述 + 你们的交付物：fan vote estimates / method comparison / recommendations）\label{sec:intro}

**2 Problem Decomposition and Analysis**\label{sec:problem_decomposition_and_analysis}

* 2.1 Problem Decompositions \label{sec:problem_decomposition}
* 2.2 Key Assumptions \label{subsec:assumptions}
* 2.3 Key Notations \label{subsec:notations}
* 2.4 Tasks & Evaluation KPIs（这里强烈建议补：一致性指标、bottom-k set-match、多淘汰/无淘汰周口径、置信度定义） \label{subsec:tasks_and_kpis}

**3 Data Processing and EDA (model-driven)**\label{sec:data}

* 3.1 Data Cleaning Principles and Validation（重点解释：0 分编码、N/A、周数不齐、active 集合构造）\label{subsec:cleaning_principles_validation}
    3.1.1 Cleaning Principles\label{subsubsec:cleaning_principles}
    3.1.2 Data Cleaning Operations\label{subsubsec:cleaning_operations}
    3.1.3 Data Cleaning Outcomes ann Validation\label{subsubsec:cleaning_outcomes_validation}
* 3.2 Panel Construction（season–week–celebrity 周面板：这是后面所有模型的统一输入）\label{subsec:panel_construction}
* 3.3 Empirical Findings from EDA (only what feeds models) \label{subsec:eda_model_driven}
    3.3.1 Data Visualization \label{subsubsec:eda_viz}
    3.3.2 Key Empirical Findings \label{subsubsec:key_findings}
* 3.4 Feature Engineering（职业舞者、年龄、行业、趋势项、周内相对排名/百分比等） \label{subsec:feature_engineering}
* 3.5 synthesis of Findings \label{subsec:synthesis_findings}

**4 Fan Vote Inference Model (核心任务A)**\label{sec:A}

* 4.1 Model philosophy \label{subsec:model_philosophy}
* 4.2 Main inference model \label{subsec:inference_model}
* 4.3 Uncertainty quantification \label{subsec:uncertainty_qualification_and_sensitivity_analysis}
    *4.3.1 KPI2: Vote Identifiability (interval tightness) \label{subsubsec:kpi2_identifiability}
* 4.4 Hyperparameters, tuning, and implementation details \label{subsec:a_hyper_impl}
* 4.5 Outputs and sanity checks \label{subsec:a_outputs_checks}

**5 Rule Replay: Voting Systems & Counterfactuals (任务B+C)**\label{sec:B_and_C}

* 5.1 Rank vs Percent across seasons \label{subsec:rank_vs_percent_across_seasons}
    * 5.1.1 Replay protocol and eligibility \label{subsubsec:replay_protocol_and_eligibility}
    * 5.1.2 Cross-season summary metrics \label{subsubsec:cross_season_summary_metrics}
    * 5.1.3 Era cutoff assumption and stress-test plan \label{subsubsec:era_cutoff_assumption_and_stress_test_plan}
* 5.2 Controversial contestants case studies \label{subsec:controversial_contestants_case_studies}
* 5.3 Bottom-two + judges’ save impact \label{subsec:bottom_two_and_judges_save}
* 5.4 Synthesis Findings From Rules \label{subsec:synthesis_of_findings_from_rules}

**6 Impact Analysis: Pro dancers & Celebrity attributes (任务D的一部分)**\label{sec:D1}

* 6.1 Outcome definitions \label{subsec:outcome_definitions_d1}
* 6.2 Modeling results \label{subsec:modeling_results_d1}

**7 Proposed New System (任务D的另一部分：新机制)**\label{sec:D2}

* 7.1 Design Goals and Principles \label{subsec:d2_design_goals}
* 7.2 Proposed aggregation rule \label{subsec:d2_rule_definition}
* 7.3 Stress Testing and Simulation \label{subsec:d2_stress_testing}


**8 Conclusion & Recommendations**\label{sec:conclusion}

**9 Memo to Management**\label{sec:memo}

**References + Appendix(\label{app:all}) + AI Use Report**（AI use 不计页数，但要放最后）

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