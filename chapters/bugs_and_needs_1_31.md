# section 3 图表需求
**P0 必做**

1. **Tab 3.1 Data inventory（原始数据列概览）**
   * 原因：评审要知道有哪些属性字段、有哪些 weekly score 字段
   * 输入：`2026_MCM_Problem_C_Data.csv`
2. **Fig 3.1 Judges availability（每行 n_judges_obs 的分布）**
   * 原因：证明评委人数变动/缺失已被你们的聚合方法吸收
   * 输入：`intermediate_weekly_panel.csv`
3. **Fig 3.2 Irregular weeks summary（true_k=0 / >1 的周数占比）**
   * 原因：解释为什么要定义 eligible weeks、为什么 KPI 用 bottom-k set-match
   * 输入：`intermediate_baseline_preds.csv`（true_k）
4. **Fig 3.3 Active vs post-exit placeholders（active=False/zero-score 标记数量）**
   * 原因：直接回应“淘汰后 0 分编码”的清洗策略
   * 输入：`intermediate_weekly_panel.csv`

**P1 建议（让数据章更“有用”）**
5. **Fig 3.4 Active set size by week（n_active 随 week 的变化）**

  * 原因：解释为什么用 share/percent 而不是 raw score
  * 输入：`intermediate_baseline_preds.csv`（n_active）


# section 4 的内容bug: KPI2 实操清单（Vote Identifiability / interval tightness）

## 0. 这段正文“已经定死”的口径（避免自相矛盾）
- [ ] 规则：percent-based（与 Task A 的 QP 一致）
- [ ] vote 变量：share p_{i,t}（不是 rank）
- [ ] ε：写死 ε = 1e-6（避免 1/0）
- [ ] KPI2 输出：对每个 (season, week, contestant) 给 interval + ID，再做聚合统计
> ⚠️ 如果团队未来改成 rank-based 或改 vote 变量，这段必须同步重写。

---

## 1. 仍可能存在的漏洞
### 漏洞 1：KPI2 区间“无限宽”或“过宽”
原因：仅用可行性约束（elimination constraints + simplex）会导致 inverse problem 自由度太大。
解决：
- [ ] 必须加 near-optimal shell：L(p,ξ) ≤ (1+δ_obj) OPT
- [ ] 推荐 δ_obj 默认 0.01（1%）; 若 infeasible 再放宽到 0.05（5%）

### 漏洞 2：Slack (ξ) 被用来“作弊”扩大区间
原因：min/max 会把 ξ 拉大，从而放松淘汰一致性，扩大 p 的范围。
解决（两选一，建议 A）：
- [ ] A. 强约束：对所有周 ξ_t ≤ ξ̂_t + δ_ξ
- [ ] B. 或者只约束目标周：ξ_t ≤ ξ̂_t + δ_ξ
- [ ] 推荐 δ_ξ 默认 0（最严格）；若数值不稳可用 1e-3

### 漏洞 3：区间计算口径与主 QP 不一致（导致 p̂ 不在 [pmin,pmax] 里）
原因：profile QP 少了某些约束 / smoothness 项 / active-set 定义不同。
必须做 sanity check：
- [ ] 检查：pmin_{i,t} ≤ p̂_{i,t} ≤ pmax_{i,t} 对所有计算点成立
- [ ] 若不成立：说明“profile 问题”与主问题不一致（优先检查 active set、smoothness项、ξ约束）

### 漏洞 4：到底算“单周区间”还是“整季联合区间”没统一
推荐统一为“整季联合 profile”：
- [ ] profile 的变量仍是整季所有 p_{·,·} 与 ξ_{·}（与主 QP 同维度）
- [ ] 这样得到的区间才和你们主解的正则偏好一致（评审更认可）

### 漏洞 5：计算量爆炸（2 × #weeks × #contestants × #seasons）
工程策略（必须选一个并写在论文/实现注释里）：
- [ ] 只算 late-phase weeks（例如每季后 1/3 周）
- [ ] 或只算“争议人物/争议周”（case study 需要的那些）
- [ ] 或每周抽样 N 个 contestants（报告中用 median/quantile 统计仍合理）
- [ ] 或并行化（按 season 并行最自然）

---

## 2. KPI2 具体怎么做
### Step A：先跑主 QP（每季一次）
- [ ] 解 Task A 的 season-wise QP，拿到：
  - p̂_{i,t}（全部 active i,t）
  - ξ̂_t（每周）
  - OPT_s（目标函数最优值）

### Step B：为每个 (i,t) 解两次 profile QP（min/max）
- [ ] profile-min：minimize p_{i,t}
- [ ] profile-max：maximize p_{i,t}
两者共同约束：
- [ ] 与主 QP 相同的 simplex 约束：p_{·,t}≥0 且 sum=1（每周）
- [ ] 与主 QP 相同的 elimination-consistency 约束（含 ξ）
- [ ] near-optimal shell：L(p,ξ) ≤ (1+δ_obj) OPT_s
- [ ] slack cap：ξ_τ ≤ ξ̂_τ + δ_ξ（建议对所有 τ）

### Step C：计算 KPI2
- [ ] width：w_{i,t} = pmax_{i,t} - pmin_{i,t}
- [ ] ID：ID_{i,t} = 1 / (w_{i,t} + ε)

### Step D：聚合输出（与 registry 一致）
- [ ] 同一 week 内对 ID_{i,t} 取 median + (25%, 75%) quantiles
- [ ] 按 season 聚合；按 phase（early/mid/late）再聚合一版
- [ ] Case study 时：输出具体 contestant 的 w_{i,t} 随周变化（图放结果章）

---

## 2) KPI2 怎么实操（这个应该与上面是差不多的）

下面按你们 Task A（percent + share + QP）**最稳妥的实现方式**来写。

---

### Step 1 — 先“定死 KPI2 的口径”（这一步必须写进论文）

在 Task A 中建议固定为：

* 规则：**percent-combination**（与主 QP 一致）
* 变量：**fan vote share** (p_{i,t})
* (\varepsilon)：建议 (\varepsilon=10^{-6}) 或 (10^{-5})（避免分母为 0）
* near-optimal 壳：

  * (\delta_{\text{obj}} = 0.01)（允许目标值比最优差 1%）
  * (\delta_{\xi} = 0) 或 0.001（强约束 slack 不许“作弊”）

> 如果你们担心 1% 太紧，会 infeasible：改成 5%（0.05）通常够用。

---

### Step 2 — 先跑你们主 QP（必须有 (\hat p), (\hat\xi), OPT）

对每个 season (s) 解一次主问题得到：

* (\hat p_{i,t}) for all active (i,t)
* (\hat\xi_t) for all (t)
* (\text{OPT}_s)：主目标最优值

这一步你们已经在做/或马上会做。

---

### Step 3 — KPI2 的“可行区间”要怎么求（核心）

对每个 season (s)、每个 week (t)、每个 active contestant (i\in A_{s,t})，要算：

[
p^{\min}*{i,t}=\min p*{i,t},\quad
p^{\max}*{i,t}=\max p*{i,t}
]

但注意：**这两个优化问题必须在同一套约束下解**，并且要防止 slack 作弊、以及防止区间无限宽。

#### 3.1 建议采用“整季联合 profile optimization”（最一致、最不容易被挑刺）

也就是说，求 (p_{i,t}) 的 min/max 时，优化变量仍然是 **整季所有 ({p_{j,\tau}}) 与 ({\xi_\tau})**，约束仍然是：

* 每周 share simplex：(p_{j,\tau}\ge0,\ \sum_{j\in A_{s,\tau}}p_{j,\tau}=1)
* 每周淘汰一致性（带 slack）：
  (S^{(P)}*{e,\tau}\le S^{(P)}*{j,\tau}+\xi_\tau)
* slack 非负：(\xi_\tau\ge0)

然后加上 **near-optimal 壳**（强烈建议）：

* 目标壳：
  [
  \mathcal{L}(p,\xi)\le (1+\delta_{\text{obj}})\cdot \text{OPT}_s
  ]
  其中 (\mathcal{L}) 就是你们主 QP 的目标函数（smoothness + (\lambda \xi^2)）

* slack 壳（防作弊）：
  [
  \xi_\tau \le \hat\xi_\tau + \delta_{\xi}, \quad \forall \tau
  ]
  或者只对目标周 t 限制：(\xi_t \le \hat\xi_t + \delta_\xi)

这样做的意义：

> 你们算的是“在与主解同样合理（near-optimal）的解释里，(p_{i,t}) 可以波动多大”。

#### 3.2 复杂度与工程建议

* 纯暴力：每个 ((i,t)) 要解 2 次优化 → 量很大
* 工程上可以先做：

  * 只对“争议人物/争议周”算 KPI2（registry 也提了 controversial weeks slice）
  * 或者每季只对后期 Top-k 候选人算（更有叙事价值）
  * 或者每周只算 median interval（对每周随机抽样 i）

> 论文写法：说清 “we compute KPI2 on selected slices to control computational cost” 就行。

---

### Step 4 — KPI2 计算与聚合（严格对齐 registry）

算完区间后：

* width：(w_{i,t}=p^{\max}*{i,t}-p^{\min}*{i,t})
* identifiability：(\mathrm{ID}*{i,t}=1/(w*{i,t}+\varepsilon))

聚合建议（与你们 registry 一致）：

1. 先在同一 week（或同一 season phase）对 (\mathrm{ID}_{i,t}) 取 **median / quantiles**
2. 再按 season 或 early/mid/late phase 汇总

---

### Step 5 — 必做 sanity checks（不做很容易出现“看似能算，实际错”）

* **可行性检查**：min/max 是否都 feasible；如果 infeasible，放宽 (\delta_{\text{obj}}) 或 (\delta_\xi)。
* **包含性检查**：应该满足
  (p^{\min}*{i,t} \le \hat p*{i,t} \le p^{\max}_{i,t})
  若不满足，说明你壳的定义跟主问题不一致。
* **slack 作弊检查**：如果 min/max 解里 (\xi) 明显变大，说明需要加 (\xi) 壳。

## 4) 你要的“实操清单”

1. 固定 KPI2 口径：percent + share；设 (\varepsilon=1e{-6})，(\delta_{\text{obj}}=0.01)，(\delta_\xi=0)（不行就 0.05/0.001）。
2. 每季解主 QP 得到 (\hat p, \hat\xi, \text{OPT}_s)。
3. 对每个候选 ((i,t))（先只算争议周/后期周）：

   * 解 **min**：minimize (p_{i,t})
   * 解 **max**：maximize (p_{i,t})
   * 约束 = 主问题约束 + (\mathcal{L}\le (1+\delta)\text{OPT}) + (\xi\le \hat\xi+\delta_\xi)
4. width (w=p^{max}-p^{min})，ID (=1/(w+\varepsilon))。
5. sanity check：(\hat p) 落在区间内；slack 不爆；不 feasible 就放宽 δ。
6. 聚合：按 week/season phase 取 median + quantiles，再按 season 汇总。

---

## 3. 必做验证（不做就容易“算出来但错了”）
- [ ] Feasibility：profile-min/max 必须可行；不可行 → 放宽 δ_obj 或 δ_ξ
- [ ] Containment：p̂ 落在区间内
- [ ] No-cheating：profile 解出来的 ξ 不应显著大于 ξ̂（否则 cap 太松）
- [ ] 复现实验：同一 season 同一参数应稳定复现（随机初始化不应影响解）

---

## 4. 推荐默认参数（先用这个跑通）
- ε = 1e-6
- δ_obj = 0.01（若 infeasible → 0.05）
- δ_ξ = 0（若 infeasible/数值不稳 → 1e-3）
- 计算切片：优先 late-phase + controversial cases（性价比最高）

# Task A（主QP）仍需解决的关键问题清单（KPI2 之外）

## A. Active set / Outcome labeling（最常见根因）
- [ ] 明确定义 A_{s,t}：当周“在赛”选手集合（排除 post-exit 0 分记录）
- [ ] 明确定义 E_{s,t}：当周“被淘汰”集合（支持空集/多淘汰）
- [ ] 特殊周标记：non-elimination / double elimination / withdrawal / return 等，决定 E_{s,t} 如何编码
- [ ] sanity：每周 |A_{s,t}| 合理递减；E_{s,t} ⊆ A_{s,t}

## B. Feasibility & Slack diagnostics（主QP跑不通就先查这里）
- [ ] 若主QP infeasible：优先检查 A/E 构造，而不是先改 λ
- [ ] 检查淘汰一致性约束索引是否正确（e∈E vs u∈A\E）
- [ ] 检查 q^J_{i,t} 的归一化是否只在 active set 上做
- [ ] 记录每周 ξ̂_t：大 ξ̂_t 的周应对应格式异常或规则不匹配，而不是普遍现象

## C. Hyperparameter tuning（λ、α 的落地策略）
- [ ] 固定 α=0.5 作为主设定；α 做敏感性（不要在 Task A 里同时搜索 α 和 λ）
- [ ] λ 的初始网格（例如 0.1, 1, 10, 100）并定义选择准则：
      - ξ̂_t 的分布（过大/过多说明 λ 太小）
      - vote trajectory 的周际波动（过大说明 λ 太大或 active set 有误）
      - 下游 replay agreement（Task B 的 week-level match）

## D. Solver & numerical stability（工程坑）
- [ ] 主QP：选择稳定的 QP solver（季级求解，便于调试）
- [ ] KPI2 profile（若用 SOC）：选 ECOS/SCS 等支持 SOC 的 solver
- [ ] 数值检查：p 负值（容忍1e-8截断）、sum-to-one 误差（投影/重归一化）
- [ ] 缓存约束结构：profile-min/max 复用同一 season 的约束矩阵（性能关键）

## E. Outputs contract（给 Task B/C/D 的接口必须一致）
- [ ] 明确输出表结构：索引 (season, week, contestant_id)，字段 p_hat, xi_hat, S_hat, (optional) pmin/pmax
- [ ] Replay 输入时：只使用 active set，且对缺失周做显式处理（避免 silent drop）


# Task B & C

下面我给你两块交接材料（都以美赛评审视角设计，兼顾论文辅助与美观）：

1. **第 5 章图/表需求清单（交接给队友即可开工）**
2. **第 5 章当前文字里“未经实证支撑的结论点”清单 + 需要补的验证图/程序**
3. **本节文字的表达/内容修正建议（一次性纠正）**

---

## 1) 第 5 章图/表需求清单（MCM 视角，尽量可执行）

> 总原则（评审最看重）：**每张图回答一个问题**，并且能直接支撑 5.1–5.4 的论断链条；避免“好看但不解释结论”的图。
> 数据口径必须遵守 KPI registry：例如 KPI1/KPI3 用 **eligible weeks**（排除无淘汰/多淘汰等）并按 era 分组。
我按“必做（P0）/ 强烈建议（P1）/ 锦上添花（P2）”分层，队友可以按优先级交付。
---

### ✅ P0 必做（没有这些，第五章很难站住）

#### **Fig 5.1 — FlipRate by season（跨季规则差异强度）**

* **放置**：5.1（KPI1 & KPI3 总结段落之后）
* **回答的问题**：规则一换，淘汰对象改变的频率到底多大？哪些季最敏感？
* **数据输入**：`intermediate_baseline_preds.csv`（你们已生成的 BL-0 输出）
* **计算口径**：仅 `eligible=1` 的 (season, week)；对 `flip` 取均值（=比例）
* **图形建议**：按 season 排序的柱状图；加一条 Overall 平均水平虚线；可按 era 用浅色分块背景（不必上色太多，保持干净）
* **输出文件名建议**：`fig_fliprate_by_season.pdf`
* **验收标准**：能复现语境文件里提到的 BL-0 flip rate 级别，并能解释“少数季明显更高”。

#### **Tab 5.1 — KPI1 hit-rate（rank vs percent）按 era 汇总**

* **放置**：紧跟 Fig 5.1 或置于 Fig 5.1 之前（5.1 内）
* **回答的问题**：两套规则在 BL-0 下对“真实淘汰”的一致性谁更高？差多少？
* **数据输入**：同上
* **计算口径**：`eligible=1`；分别计算 `match_rank`、`match_percent` 的均值；按 era（rank-era / percent-era）再分组（按 registry 的切片定义）
* **表格样式**：3 行（Overall / Rank-era / Percent-era）× 2 列（Rank hit-rate / Percent hit-rate）+ 1 列（#eligible weeks）
* **输出文件名建议**：`tab_baseline_consistency.tex`
* **验收标准**：能复现语境文件里给出的 overall hit-rate 数值（Rank 0.364 / Percent 0.375）并标注“仅为 sanity-check baseline”。

#### **Fig 5.2 — Stress-test: era cutoff 27/28/29 对 KPI3 的影响**

* **放置**：5.1 “era cutoff assumption and stress-test plan” 段落后
* **回答的问题**：你们“Season-28 切换”假设是否会改变宏观结论？
* **数据输入**：`intermediate_baseline_preds.csv`
* **计算口径**：分别用 cutoff=27/28/29 重算 rank-era / percent-era 分组下的 FlipRate（和/或 KPI1），画出三组点/条
* **图形建议**：点图（3 个 cutoff × 2 个 era），配置信区间/误差条（bootstrap over weeks）
* **验收标准**：如果结论对 cutoff 不敏感 → 你们可写“robust”；敏感 → 第五章需要加限定语。registry 已要求 stress-test。

---

### ✅ P1 强烈建议（有了这些，第五章会“像美赛强队”）

#### **Fig 5.3 — FlipRate by week index（赛季阶段效应：早/中/晚）**

* **放置**：5.4 结论前（支撑“后期更敏感/更稳定”的论断）
* **回答的问题**：规则差异是否集中在赛季后期？
* **数据输入**：`intermediate_baseline_preds.csv` + 每季周序号标准化（week / max_week）
* **计算口径**：eligible only；按 normalized_week 分箱（例如 0–0.33/0.33–0.66/0.66–1）计算 FlipRate
* **图形建议**：三段柱状 + 误差条；或折线（按分箱中心）
* **验收标准**：明确显示阶段差异是否存在；若不显著，则 5.4 里不能写“often increases late-season”。

#### **Fig 5.4 — “Judge–fan disagreement” 与 flip 的关系（机制解释核武器）**

* **放置**：5.4（支撑“分歧越大越容易 flip”）
* **回答的问题**：规则为何会翻？是否由评委/观众偏好冲突驱动？
* **数据输入**：Task A 的 (\hat p) 输出（或你们现在的 proxy 先占位）+ judges ranks
* **核心变量**：discordance 指标（例如 (|R^J - R^V|_1)、或 Kendall tau 的负值）
* **计算口径**：eligible weeks；回归/分箱比较 `flip` vs discordance
* **图形建议**：散点+平滑线（loess/分箱均值）；或两组箱线（flip=0/1）
* **验收标准**：至少能给出单调趋势或显著差异，否则 5.4 的机制论断要改成“可能/我们观察到在若干季出现”。

#### **Fig 5.5 — Case study timeline（每个案例 1 张：评委/粉丝轨迹 + 被淘汰预测）**

* **放置**：5.2（每个案例段落中间）
* **回答的问题**：为什么这个人“争议”？在哪几周、哪条机制导致结局变化？
* **案例建议**：你们语境里点名的 Jerry Rice 与 Bobby Bones（先做这俩就够强）
* **图形内容**（同图多层）：

  * 线 1：judges rank（或 judges percent）
  * 线 2：fan rank（由 (\hat p) 得出）
  * 标记：真实淘汰周、rank/percent 回放淘汰周
* **验收标准**：读者不看文字，也能一眼看出“哪个规则在何周导致结果改变”。

---

### ✅ P2 锦上添花（有则加分，无则不影响主线）

#### **Tab 5.2 — Most-sensitive seasons list（Top-5 FlipRate + 说明）**

* **放置**：5.1 末尾或 5.2 开头
* **内容**：列出 FlipRate 最高 5 季，附 #eligible weeks、是否含特殊机制（save）、是否多淘汰多
* **作用**：帮你们“选案例”和控制 narrative。

#### **Fig 5.6 — Confusion matrix 风格的淘汰预测（rank vs percent）**

* **放置**：5.1
* **作用**：漂亮、直观；但不是必须。

---

## 2) 第 5 章当前文字里：哪些“实证结论”尚未被数据/程序论证？

你们现在的文字（按你说的“已经照我的版本贴了”）里，有几句属于**经验性判断**，不加证据会被评审当成“空口解释”。下面我逐条列出，并把“需要补的图/程序”绑定到上面的清单，队友就能对齐。

### 2.1 需要证据支撑或改写为“假设/观察”的句子（按 5.4 四条）

1. **“Rule choice matters most when judges and fans disagree.”**

   * 需要：Fig 5.4（discordance → flip 的定量关系）
   * 否则改写建议：把 *matters most* 改成 *tends to matter more in seasons/weeks where ...*（更安全）

2. **“Divergence is not uniform across the season… often increases in late-season weeks …”**

   * 需要：Fig 5.3（按阶段的 FlipRate 或 margin）
   * 否则改写：改成 *we evaluate whether divergence concentrates late in the season by phase-sliced FlipRate (reported in Fig...).*

3. **“Judges’ save … reducing the ability of extreme popularity alone …”**

   * 需要：一个 Save effect 图（建议在 P1/P2 新增一个 Fig：`save_flip_rate` 或 “saved contestant has lower fan rank but higher judges rank” 的比例）
   * 否则改写：改成 *shifts final elimination authority toward judges by construction; we quantify how frequently this changes the eliminated contestant in Section 5.3.*

4. **“percent preserves score magnitude while rank amplifies ordering.”**

   * 这是合理的机制解释，但最好用一个“rank compression / magnitude loss”小图支撑（P2 可做）
   * 没图也可保留，但措辞改成 *conceptually* / *by design* 会更稳。

---
以下是交接清单：
## Chapter 5 deliverables (P0 must-have)

- [ ] Fig 5.1 FlipRate by season (eligible only) -> fig_fliprate_by_season.pdf
- [ ] Tab 5.1 KPI1 hit-rate (rank vs percent), Overall + era slices -> tab_baseline_consistency.tex
- [ ] Fig 5.2 Era cutoff stress-test (27/28/29) effect on FlipRate/KPI1 -> fig_cutoff_stress_test.pdf

## Chapter 5 deliverables (P1 strong)
- [ ] Fig 5.3 FlipRate by season phase (early/mid/late via normalized week)
- [ ] Fig 5.4 Discordance (judge vs fan ranks) vs flip probability
- [ ] Fig 5.5 Case-study timelines for Jerry Rice & Bobby Bones (judges rank, fan rank, elim markers)

## Claims that must be backed by evidence (otherwise hedge wording)
- [ ] "Rule choice matters most when judges and fans disagree" -> needs Fig 5.4
- [ ] "Divergence increases late-season" -> needs Fig 5.3
- [ ] "Judges' save reduces extreme popularity deciding outcomes" -> needs Save-effect figure

## Text fixes to apply now (avoid reviewer pushback)
- [ ] Explicitly define KPI denominators as 'eligible weeks' (exclude no-elim & multi-elim per registry)
- [ ] Label BL-0 metrics as sanity-check baseline (not final)
- [ ] Shorten tie-handling in main text; move details to appendix
- [ ] Add case-study selection criteria (FlipRate high + discordance high)

---

# 第6章
**“论证闭环审计”**，把第六章里哪些句子是“方法描述”、哪些是“需要跑出数来才能说”的结论点分开，
### 必须等模型跑完才能说的结论（否则就是无依据结论）

这些属于**经验性/结果性陈述**，在正文里出现就要配输出表或图，否则要改成“我们将评估/我们报告”：

1. **“哪些特征显著影响 judges / fans、方向如何、强度如何”**

   * 需要：(\beta_X)、(\gamma_X) 的估计值（带 SE/CI）
   * 你现在的正文如果出现“fans 更偏好某特征 / judges 更偏好某特征”，都必须等结果表。

2. **“(\gamma_J)（评委到粉丝的传导强度）有多大、是否显著”**

   * 需要：Vote Model 的 (\gamma_J) 点估计 + 置信区间（最好 bootstrap 过）

3. **“pro dancer 的影响显著/不显著”**

   * 需要：(\sigma_v^2)（Judge model 的 pro 随机效应方差）和/或似然比检验 (H_0:\sigma_v^2=0) 的结果

4. **“pro dancer 影响在 judges vs fans 哪边更强”**

   * 需要：(ICC^J_{pro})、(ICC^V_{pro}) 的数值

5. **“top/bottom 5 pro 的 BLUP 排名是否一致/不一致”**

   * 需要：两套模型的 pro 随机效应 BLUP 列表（并排）

6. **任何关于“赛季后期更容易吸票/更高分”的趋势判断**

   * 你们的文档里把周次趋势 (f(t)) 当成候选项是合理的
   * 但如果正文写了“后期更明显/显著上升”，要么用模型里 (f(t)) 的可视化来支撑，要么改成“我们用 (f(t)) 控制该效应”。

---

## C. “结论点 → 最小证据输出”对照表（这就是交接清单的骨架）

> 你们接下来写交接清单时，实际上就是把下面每一条变成：**输入数据 → 代码产物 → 图表 → 论文句子**。

### C1. Judges vs Fans 对同一特征是否同向/同强度？

* **结论句式（可写在 6.2）**：
  “For attribute (k), judges reward it more / fans favor it more, as indicated by (\Delta_k).”
* **最小证据**：

  1. 系数表：(\beta_k,\gamma_k)（含 SE/CI）
  2. (\Delta_k) 的图（带 CI）

### C2. 评委分向粉丝票的传导强度 (\gamma_J)

* **结论句式**：
  “(\gamma_J) is (positive/weak/strong), suggesting (limited/meaningful) transmission from judges to fans.”
* **最小证据**：

  1. (\gamma_J) 点估计 + CI（最好 bootstrap）
  2. 可选：按 era/阶段分组的 (\gamma_J) 稳健性

### C3. pro dancer 是否“显著影响” judges / fans？

* **结论句式**：
  “We find non-zero pro-dancer variance in the Judge/Vote model…”
* **最小证据**：

  1. (\sigma_v^2)、(\sigma_b^2) 估计值
  2. (H_0:\sigma^2=0) 的检验或信息准则对比

### C4. pro dancer 的影响“强度多大”？（ICC）

* **结论句式**：
  “Pro dancers account for (ICC^J_{pro}) of judge-score variation and (ICC^V_{pro}) of fan-vote variation…”
* **最小证据**：
  ICC 两个数 + 可选 bootstrap CI

### C5. 哪些 pro “对评委好/对粉丝好”？一致吗？

* **结论句式**：
  “Top/bottom pro dancers differ between judge and fan outcomes, implying…”
* **最小证据**：
  两套 BLUP 列表并排（top/bottom 5）

---


# Chapter 6 交接清单（Task D1：Pro Dancer 与 Celebrity Attributes 影响分析）
> 目标：让第六章所有“结论性表述”都有模型输出支撑；没跑出数之前，正文只能写“我们将量化/我们报告”。

---

## 0. 统一口径（必须先对齐，否则跑出来无法写进论文）
- [ ] 因变量（Judges）：q^J_{i,t} = J_{i,t}/sum_{active} J_{r,t}；再做 logit：y^J_{i,t}=log((q^J+ε)/(1-q^J+ε))
- [ ] 因变量（Fans）：p_{i,t} = Task A 推断的 vote share；再做 logit：y^V_{i,t}=log((p+ε)/(1-p+ε))
- [ ] ε 推荐：1e-6（避免边界）
- [ ] Active set 口径：只包含当周在赛选手；排除 post-exit “0 分占位”记录
- [ ] 周次趋势 f(t)：先用线性 t 或分段/样条（视实现难度）
- [ ] Season FE：必须有（跨季可比）
- [ ] Random effects：celebrity 随机截距 + pro dancer 随机截距（两边都要）
- [ ] 粉丝票是估计值：Vote 模型必须做不确定性传播（bootstrap 或加权）——至少选一种跑通

---

## 1. 数据输入与字段准备（实现同学先做这个）
### 输入文件
- [ ] intermediate_weekly_panel.csv（周面板，含 judges score、week、season、celebrity_id、pro_dancer_id、属性特征 X）
- [ ] Task A 输出（推荐 output.csv 或你们专门导出的 p_hat 表）
  - 必需字段：season, week, celebrity_id, p_hat
  - 可选字段：pmin, pmax（如果 KPI2 跑了 slice）

### 必须生成/校验的中间字段（并输出到一个“用于第6章建模的panel”）
- [ ] qJ_share（只在 active set 内归一化）
- [ ] yJ_logit（用 ε）
- [ ] yV_logit（用 ε）
- [ ] week_index（整数周次） + 可选 normalized_week = week/max_week
- [ ] X_i（属性向量：年龄/职业/性别/知名度proxy等，按你们 Feature 列表）
- [ ] pro_id = d(i)，celebrity_id
- [ ] season_id（用于 FE）
- [ ] 过滤：只保留 active weeks（必要时剔除特殊周/异常周，用你们的规则）

### 验收标准
- [ ] 每个 (season, week) active set 的 qJ_share 求和≈1
- [ ] yJ/yV 没有 NaN/inf（ε 生效）
- [ ] 与 Task A 输出 join 后，p_hat 覆盖率足够（缺失要有明确处理：剔除该周或插值/不纳入D1）

---

## 2. 模型要跑什么（核心交付）
> 你们第六章只允许写“跑出来的东西”，所以至少要有以下 2 个模型 + 2 类衍生输出。

### 2.1 Model J（Judge Model）
形式：
yJ_{i,t} = β0 + βX^T X_i + βT f(t) + FE_season + u_i + v_{pro(i)} + ε_{i,t}

产物（必须输出）：
- [ ] βX 系数表（点估计、SE、p值或95%CI）
- [ ] βT 与 f(t) 的估计（至少能解释“我们控制了周次趋势”）
- [ ] 方差分量：σ_u^2（celebrity）、σ_v^2（pro）、σ^2（残差）
- [ ] pro random effect 的 BLUP：v_pro（每个 pro 一个数）

验收标准：
- [ ] 模型收敛（或给出原因：奇异拟合/方差为0）
- [ ] 能导出完整的系数表与方差表（csv/tex 都可）

---

### 2.2 Model V（Vote Model）
形式：
yV_{i,t} = γ0 + γJ*yJ_{i,t} + γX^T X_i + γT f(t) + FE_season + a_i + b_{pro(i)} + η_{i,t}

产物（必须输出）：
- [ ] γJ（“评委→粉丝传导强度”）点估计 + SE/CI
- [ ] γX 系数表（点估计、SE、CI）
- [ ] 方差分量：σ_a^2（celebrity）、σ_b^2（pro）、σ_η^2（残差）
- [ ] pro random effect 的 BLUP：b_pro

验收标准：
- [ ] 模型收敛
- [ ] γJ 可解释（方向与量级合理），并能给出不确定性

---

## 3. 必须补齐的不确定性传播（至少选一种跑通）
> 否则第六章关于 fans 的结论会被质疑“用估计值当真值”。

### 方案 A：Bootstrap（推荐）
- [ ] 生成 B 组 p_hat^(b)（从 Task A 不确定性来源：不同 α/λ、或从 pmin/pmax 内采样、或重跑 Task A）
- [ ] 每组拟合一次 Vote Model，记录 γJ^(b), γX^(b), b_pro^(b)
- [ ] 输出：γJ 的 CI、Δ_k 的 CI、以及关键 pro 排名稳定性（比如 top-5 出现频率）

验收标准：
- [ ] 至少 B=50（能出稳定 CI）
- [ ] CI 合理，不是全崩（若崩，说明 vote 不确定性太大或模型设定需简化）

### 方案 B：加权回归（备选）
- [ ] 用 KPI2 的区间宽度 U_{i,t}=pmax-pmin 做权重：w_{i,t}=1/(U_{i,t}+δ)
- [ ] 拟合加权 Vote Model，输出加权后的 γ、CI
- [ ] 注意：KPI2 可能只跑 slice，那就只在 slice 上加权或说明限制

---

## 4. 第六章必须给出的“可写进论文的证据图/表”（对应插入位置）
> 没有这些图表，第六章不能写“fans更偏好/ judges更偏好/ pro影响更强”等结论。

### Fig 6.1（必做）：Judges vs Fans 系数并排图（β_k vs γ_k）
- 输入：Model J 的 βX + Model V 的 γX（同一组特征）
- 形式：每个特征一行，两根条（或两点+误差条），带 95%CI
- 插入位置：6.2 “Comparing judges vs fans” 段落之后
- 验收标准：读者能一眼看出“方向一致/相反、强度差异”

### Fig 6.2（必做）：Δ_k = γ_k - β_k 的差异图（带CI）
- 输入：Δ_k 点估计 + CI（bootstrap 或 delta method）
- 插入位置：紧跟 Fig 6.1 之后
- 验收标准：能支持“哪个特征 fans更偏好/ judges更偏好”的句子（否则文字要改成“未观察到显著差异”）

### Tab 6.1（建议）：ICC^{J}_{pro} 与 ICC^{V}_{pro}
- 输入：方差分量 → ICC
- 插入位置：6.2 “Quantifying pro-dancer impact” 段落
- 验收标准：给出 pro 对 judges 与 fans 的影响占比（若接近 0，也是一条结论）

### Tab 6.2（建议）：pro dancer 的 BLUP Top/Bottom 5（judges vs fans 并列）
- 输入：v_pro 与 b_pro 的 BLUP
- 插入位置：6.2 pro影响解释段落末尾
- 验收标准：能支撑“同一 pro 是否同时利于 judges 与 fans”的叙述（若排名不稳，则用 bootstrap 频次表替代）

---

## 5. 第六章里哪些句子属于“不能先写死”的结论（写作警戒线）
> 如果你们正文出现这些句子，必须对应上面某个图/表已经产出，否则要改成“我们将评估/我们报告”。

- [ ] “fans 更偏好 X / judges 更偏好 X”（必须有 Fig 6.2 支撑）
- [ ] “γJ 强/弱/显著”（必须有 γJ 点估计+CI）
- [ ] “pro dancer 影响显著/占比很大”（必须有 Tab 6.1 或方差检验）
- [ ] “某 pro 是最强/最弱/对 fans 更有利”（必须有 Tab 6.2，且最好有稳定性检验）
- [ ] “后期更…”（如果提到 phase 趋势，需要 f(t) 可视化或分段分析）

---

## 6. 最小可交付版本（MVP）建议（按时间紧迫程度）
### MVP-1（最小能写进论文）
- [ ] 跑通 Model J + Model V（不做bootstrap）
- [ ] 产出：β、γ 系数表 + 方差分量表
- [ ] 画：Fig 6.1（不带CI也行但不推荐），Tab 6.1（ICC）

### MVP-2（美赛强队标准）
- [ ] 在 MVP-1 基础上做 bootstrap（B≥50）
- [ ] 产出：Fig 6.2（Δ_k + CI）、γJ 的 CI、pro 排名稳定性

---

## 7. 输出文件命名规范（方便写作手直接插入）
- [ ] figures/fig6_1_coef_compare.pdf
- [ ] figures/fig6_2_delta_ci.pdf
- [ ] tables/tab6_1_icc.tex
- [ ] tables/tab6_2_blup_top_bottom.tex
- [ ] artifacts/model6_judge_coeffs.csv, artifacts/model6_vote_coeffs.csv
- [ ] artifacts/model6_variance_components.csv
- [ ] artifacts/bootstrap_gamma_summary.csv (if bootstrap)

---

# 第七章

---

# 一、第七章所需清单（图表 + 原因 + 交接要点）

> 目标：第七章不是“提出新规则就算完”，而是要在美赛评审视角下完成 **设计—证据—推荐**闭环：
> **(i) 为什么需要新规则**（来自第5章）→ **(ii) 新规则怎么定义**（7.2）→ **(iii) 为什么它更稳/更公平/更可控**（7.3 的仿真证据）

## P0 必做（没有这些，第七章说服力会断）

### **Fig 7.1 参数网格权衡图（trade-off heatmap / Pareto）**

* **放置**：7.3（stress testing）开头或中段
* **作用/原因**（评审会问的关键）：
  你们推荐的 ((\alpha^*,\kappa^*)) 是怎么选出来的？有没有“挑数据调参”？
  → 这张图用一眼能看懂的方式展示：不同 ((\alpha,\kappa)) 下 **KPI1（回放一致性）** vs **稳定性（对扰动不敏感）** 的权衡面，并标出推荐区域。
* **输入**：参数网格结果表（alpha 网格 × kappa 网格）

  * 每个格子至少要有：KPI1（eligible weeks）、稳定性指标（见 Fig 7.2 定义）、可选 KPI3/flip
* **输出文件建议**：`fig7_1_tradeoff_heatmap.pdf`
* **验收**：能明确圈出“推荐区域”（不是唯一点也行，给一个区间更像管理建议）

### **Fig 7.2 不确定性稳定性图（uncertainty stability / flip probability）**

* **放置**：紧跟 Fig 7.1
* **作用/原因**：
  你们的 fan vote 是 Task A 推断值，评审会质疑：误差一来新规则还稳吗？
  → 这张图直接回答：在 vote uncertainty 下，淘汰/名次翻转概率如何随规则变化。
* **输入**：

  * vote 扰动样本：从 KPI2 区间采样 或 Task A bootstrap（二选一，至少一种）
  * 对每个扰动样本运行 replay，统计“淘汰翻转概率/决赛名单变化率/冠军变化率”
* **输出文件建议**：`fig7_2_uncertainty_stability.pdf`
* **验收**：能支持一句话结论：“新规则在不确定性下的波动更小（或至少不更差）”

### **Tab 7.1 规则方案对比表（Rule Variant Summary）**

* **放置**：7.2（新规则定义）之后
* **作用/原因**：
  美赛喜欢“方案对比 + 参数少 + 可解释”。这张表是给评审和管理层看的“一页总览”。
* **内容建议列**：

  * Rule（Percent / Rank / Proposed / +Save）
  * Tunable knobs（参数个数）
  * Interpretability（一句话解释）
  * Implementation burden（数据需求）
  * Expected effect（压缩人气/保留量级信息/放大排序等）
* **输出文件建议**：`tab7_1_rule_variant_summary.tex`
* **验收**：让人不用读公式也能懂你们的新规则“改了什么、为什么合理”

### **Tab 7.2 赛季级结果变化表（Outcome changes）**

* **放置**：7.3 末尾（作为 evidence summary）
* **作用/原因**：
  第七章最终要落到“会不会改变冠军/决赛名单？改变频率如何？”这是一张“管理决策表”。
* **输入**：对每季 replay 的 final placements（baseline vs proposed）
* **表格列建议**：

  * Season
  * baseline champion / proposed champion
  * finalists changed?（Y/N）
  * #weeks elimination changed（或 flip count）
  * stability under uncertainty（可选）
* **输出文件建议**：`tab7_2_outcome_changes.tex`
* **验收**：能支撑你们 Memo 里的推荐（“改变率可控/集中在争议季”）

---

## P1 强烈建议（能把第七章从“像方案”变成“像工程”）

### **Fig 7.3 推荐参数区间的“鲁棒域”图（robust region plot）**

* **原因**：管理层更想听“推荐区间”而不是一个点
* **做法**：在 ((\alpha,\kappa)) 平面上把满足阈值的区域涂出来

  * 例如 KPI1 ≥ baseline 的 95% 且稳定性 ≥ baseline
* **输出**：`fig7_3_robust_region.pdf`

### **Fig 7.4 与基线规则的差异分解（哪里变了）**

* **原因**：解释性增强：不是“平均更好”，而是“在冲突周更稳”
* **做法**：把 season-weeks 按 discordance 分箱，画 proposed vs baseline 的 flip rate / stability

---
















# 以上为ChatGPT所给出，请结合实际情况取舍