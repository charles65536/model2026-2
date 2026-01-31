# 第三章
According to a document from 2026-01-30, 你们的 **Section 3: Data Processing and EDA (model-driven)** 应该写成“**口径说明 + 可审计接口**”而不是“深度清洗/深度EDA”，并把目前已经稳定落盘的产物（两张清洗后 CSV + 1 张表 + 1 张图）作为**可复现证据**嵌入正文或附录即可。

## 1) 中文解释（这一章在报告里怎么放、怎么写才安全）

**放置位置**：`snapshots/chapters/3_data_processing_and_analysis.tex`（你们目录结构里明确存在该文件名）。

**写作策略（保守版）**

* 这一章只做三件事：

  1. 解释题面数据的关键编码（0 分与 N/A）以及你们如何避免它污染 KPI 分母；
  2. 给出你们“唯一输入接口”——season–week–celebrity 周面板（weekly panel）的定义；
  3. 告诉评审你们的 KPI1/KPI3 如何被一致地计算，并把现成的 **`tab_baseline_consistency.tex`** 与 **`fig_fliprate_by_season.pdf`** 当作审计附件引用（不需要在这里展开讨论结论）。

**你们目前能“安全写进正文”的客观事实（不会被追问）**

* 数据被重塑为 (season, week, celebrity) 的周面板；并构造了 `active / exit_week / exit_type / true_elim_flag` 等确定性标签，使后续优化与回放模型能够接入统一输入。
* Active set 口径：当周四位评委分数不是 all-NaN，且 week 不晚于 exit week；退赛按最后一个有意义的周定义退出；淘汰后出现的 0 分只作为“已退出的编码痕迹”，不进入 active 集合与 KPI 分母。
* KPI 分母口径：无淘汰周剔除；多淘汰周用 bottom-(k) set-match；Era 切片按 registry 固化（Rank-era: 1,2,28–34；Percent-era: 3–27），并明确 Season 28 是假设需要敏感性测试。

**关于你提到的“我们暂时不想把数据处理写太多”**
没问题——这一版 Section 3 的英文正文会刻意写成“接口 + 口径”，不会像传统论文那样写一堆 EDA 结论，更不会写“我们还没做完”。


## A1 中文解释（这一章要怎么写才像美赛强队）

第 3 章写作要点是：**只写“服务于模型”的数据处理与 EDA**，不要把它写成流水账。评审关心三件事：

1. **数据结构复杂性**：DWTS 数据里评委人数变动、无淘汰/多淘汰周、淘汰后 0 分编码、缺失分数（N/A）这些都会直接影响模型可行性与 KPI 口径。
2. **统一输入接口**：你们已经把 wide（weekX_judgeY）整理成了 season–week–celebrity 周面板，这是后面 Task A QP、Task B/C replay、Task D1 mixed effects 的统一输入。
3. **验证闭环**：用 BL-0 baseline（judge-only + uniform-fan-proxy）跑通 KPI1/KPI3，证明“数据口径无穿帮”，同时强调这只是 sanity-check 不是最终模型结论。

我们目前已经有足够素材写出一版“可交付”的第 3 章：原始数据列、周面板字段、active set 口径、eligible 周的定义、BL-0 的 KPI 统计（264 eligible weeks，Rank hit-rate 0.364、Percent hit-rate 0.375、FlipRate 0.038）。
但如果你希望把 **“清洗操作细节”**写得更可复现（比如每一步脚本逻辑、具体异常周处理规则），我建议你补充上传下面文件（见文末“缺失素材清单”）。

---

# 4 Task A: Fan Vote Inference Model

## 1) 中文解释（你写作时要抓的主线）

这一章你要让评审在 30 秒内读懂三件事：

1. **我们在估计什么**：每周每个在赛选手的粉丝投票“份额” (p_{i,t})（sum-to-one 的 composition），不是绝对票数。
2. **我们凭什么能估**：用“淘汰一致性”作为约束 + 用“周际平滑”作为正则，从而在多解中选出稳定解；特殊周/异常通过 slack (\xi_t) 吸收。
3. **我们如何报告不确定性**：反问题不适定 → 不只给点估计，还给可行区间、翻转边际（margin）、以及 slack 作为失败周诊断。
4. * **先确认 KPI2 存在但不承诺已产出**：它是 P1 指标，当前版本是“接口保留/定义齐了就能算”。
* **然后写清楚你们在本模型中选定的 KPI2 计算口径**：

  * vote 变量：用 share (p_{i,t})（与你们 QP 一致）
  * 规则：基于 percent-combination 的淘汰一致性约束（以及 slack）
  * 区间：对每个 ((s,t,i)) 做两次优化求 (p_{i,t}^{\min}, p_{i,t}^{\max})
  * identifiability：( \text{ID}_{i,t} = 1/( (p^{\max}-p^{\min}) + \varepsilon))
  * 聚合：先对 (celebrity, week) 取中位数/分位数，再按 season/phase 汇总（按 registry 写法）

下面的形式把这些都定死成一个**凸优化问题**：

* profile 是 **整季联合**（与主 QP 同维度、最一致）
* near-optimal shell 用一个 **二范数（SOC）约束**写出来，保证可解、也方便 CVXPY/ECOS/SCS 实现
* min/max 的目标是线性的（最简单）

这一章**只写方法与定义，不写任何结果数值**（数值和图表去第 5/6/7 章）。

---

# 第五章

好，我们直接开写 **第五章（Task B + Task C：规则回放与反事实）**。我会按你们分章策略输出：**中文解释 + 学术英文正文 + LaTeX**，并且告诉你**贴在哪个文件、哪个位置**。本章先写“方法与指标”，结果与图表后面你们跑出来再补。

---

# 放置位置（非常具体）

把下面整章内容粘贴到：
✅ `snapshots/chapters/5_rule_reply_volting_system_and_counterfactuials.tex`

建议在文件中使用如下结构（你可直接照标题贴）：

* `\section{Rule Replay: Voting Systems and Counterfactuals (Task B \& C)}`

  * `\subsection{Replay engine and week-by-week simulation}`
  * `\subsection{Implementing percent-based vs.\ rank-based aggregation}`
  * `\subsection{Bottom-two and judges' save module}`
  * `\subsection{Replay metrics: divergence, fan-bias, and stability}`
  * （可选）` \subsection{Case-study protocol for controversial contestants}`（我也写了一个短而硬的版本，方便你们后面填案例）

---

# 1) 中文解释（本章应该写清楚什么）

第五章的使命很明确：把 Task A 推断出来的 (\hat p_{i,t}) 变成**可复现的反事实证据链**：

1. **定义一个统一 replay engine**：输入每周 active set、评委分、(\hat p)，输出每周淘汰/晋级（支持多淘汰/无淘汰）。
2. **实现两套规则**：percent-based（权重合成） vs rank-based（名次合成），并明确 tie-handling。
3. **加入 bottom-two + judges’ save**：作为可插拔模块（Task C 的关键）。
4. **定义“对比指标”**：一致率、淘汰集合差异、赛季结果差异、fan-bias 指标、保护率、稳定性（margin）。
5. 最后给一个 **case-study protocol**：争议人物只需要把“规则→轨迹差异→原因解释”三步写完整，就能形成强证据。

> 注意：这一章仍然**先不写任何数值结论**，只写方法与指标。结果等队友跑完后填入图表与统计。

---

# 第六章

第六章是 Task D1 的核心：**用统计模型分解“谁在影响评委、谁在影响观众”**，并且要能回答两类问题：

1. **Outcome definitions（6.1）**

   * 评委侧：用“评委得分份额” (q^J_{i,t})（避免不同季/不同周评分尺度不同），再做 logit 变换得到 (y^J_{i,t})。
   * 观众侧：用 Task A 推断出来的投票份额 (p_{i,t})（即 (q^V_{i,t})），同样 logit 得到 (y^V_{i,t})。
     这一步是为了确保跨季可比、系数解释稳定。

2. **Modeling results（6.2）**

   * 建两个混合效应模型：Judge Model 和 Vote Model。
   * 两个模型都包含：选手属性 (X_i)、赛季固定效应 (FE_s)、周次趋势 (f(t))、以及“选手随机效应 + 职业舞者随机效应”。
   * Vote Model 里额外加入 (y^J_{i,t})，用 (\gamma_J) 衡量“评委表现向粉丝票的传导强度”。
   * 为了回答“评委/观众偏好是否一致”，对每个特征 (k) 定义差异 (\Delta_k=\gamma_k-\beta_k)：
     (\Delta_k>0) 表示观众更偏好该特征，(\Delta_k<0) 表示评委更偏好。

3. **舞者影响要用“可解释量化”呈现**
   不要只写“显著”，而要给出强度：

   * ICC：舞者方差占比（评委侧 (ICC^{J}*{pro}) 与投票侧 (ICC^{V}*{pro})）
   * BLUP：随机效应估计的舞者 top/bottom 排名，比较其对评委与粉丝的影响是否一致。

4. **必须承认并传播“粉丝票是估计值”的不确定性**

   * 推荐 bootstrap：重复得到多组 (p^{(b)}_{i,t}) 再拟合投票模型，给 (\gamma) 与 (\Delta) 的置信区间；
   * 或者用区间宽度 (U_{i,t}) 做加权回归（不确定性大权重小）。

---

# 第七章
**7.1 设计目标与原则、7.2 新聚合规则、7.3 压力测试与仿真（含回放证据）**。这意味着：第七章必须“先讲设计逻辑→再给可实现规则→最后用历史回放+敏感性证明它更稳/更公平/更可操作”，而不是再做一遍第 5 章的规则对比。

## 7.1 设计目标与原则写什么（评审视角）

这一节不是喊口号，而是把第 5–6 章的发现变成**设计约束**：

* **公平（Fairness）**：避免“极端人气”在排名法里被放大导致技术型选手被挤出（第 5 章的 FlipRate 与争议案例就是证据来源）。
* **激励（Incentive compatibility）**：选手提升舞蹈表现（评委分）应该能稳定转化为生存概率，而不是被纯人气完全覆盖。
* **可解释（Interpretability）**：规则要能用一句话解释清楚、观众也能理解“为什么这个人走了”。
* **可操作（Implementability）**：超参数尽量少（对齐 KPI2 Rule Simplicity 的思想：参数越少越好、越少依赖外部信息越好）。
* **稳定性（Stability/Robustness）**：对 (\alpha)（评委权重）、对投票估计误差（Task A/KPI2不确定性）、对 tie-handling / era cutoff 等都要“不太敏感”。敏感性写法可以引用 Andrea Saltelli 的全球敏感性框架；仿真协议可以引用 Averill M. Law 的 simulation study 规范化表述（你们 context pack 已经给了引用入口）。

## 7.2 新规则要怎么设计才“像美赛”

最稳妥、最可实现、也最容易解释的一类方案是：

> **“幂变换压缩人气 + 百分比加权”**（Power-transformed Percent Rule）

做法：把粉丝票份额 (p_{i,t}) 做一个幂变换 (p^\kappa) 后再归一化。

* (\kappa=1)：退化回原始百分比规则（不改变）
* (\kappa<1)：**压缩头部人气优势**、抬升尾部，减少“极端人气碾压”
* (\kappa>1)：相反，会放大人气（一般不推荐，但可用于 stress-test）

然后用一个参数 (\alpha) 把“评委份额 (q^J)”与“压缩后粉丝份额 (\tilde p)”线性合成：
[
S^{(N)}=\alpha q^J + (1-\alpha)\tilde p(\kappa)
]
淘汰最低者即可。

优点（评审会买账）：

* 参数只有 **2 个（(\alpha,\kappa)**），简单；
* 规则仍是“份额加权”，观众好理解；
* 可控地抑制 rank aggregation 的“次序放大效应”，同时不需要引入复杂社会选择机制。

## 7.3 压力测试与仿真证据怎么写

这一节要写成“实验协议”，不是口头承诺：

* **对照组**：现行 percent、现行 rank、(可选) bottom-two + save
* **评估指标（必须复用你们 KPI）**：

  * KPI1：回放淘汰一致率（eligible weeks）
  * KPI3：规则差异 FlipRate（你们第 5 章已在用）
  * * 新规则专用的稳定性指标：例如“参数扰动下冠军/决赛名单稳定率”、“不确定性扰动下淘汰翻转概率”
* **敏感性维度**：(\alpha) 网格、(\kappa) 网格、投票不确定性扰动（用 Task A 的区间或 bootstrap）

这一节最后要落到一句：

> “我们选定的推荐参数（(\alpha^*,\kappa^*)）是在上述多指标下的折中帕累托解（或加权评分最优）。”
> 具体数值等你们跑完再填。

---

# 第八章

第八章不是重复摘要，而是完成三个动作：

1. **回扣四个任务链条**：Task A 推断 fan votes → Task B/C 回放对比规则 → Task D1 分解 drivers（pro/属性）→ Task D2 设计新规则并压力测试。
2. **给出“可复现的核心发现”**：例如哪些季规则敏感、争议来自 judge–fan 冲突、save 的作用方向等（注意：如果你们还没跑出图表，就用“我们评估/我们报告”句式，别写死数值）。
3. **写局限与下一步**：最关键的局限是“真实观众票缺失导致反推不可识别”，你们用 KPI2 与不确定性传播来正面应对。

# 第九章 memo
管理备忘录的写法和正文不一样：要“短、可执行、可控风险”。建议结构：

1. **一句话结论**：我们建议采用新规则（power-transformed percent blending），并给出推荐参数范围与试运行方式。
2. **为什么需要改**：rank 会放大排序差异、在冲突周更易引发争议；save 会改变权力来源。
3. **推荐方案**：给 (\alpha)（评委权重）和 (\kappa)（人气压缩）两个旋钮，强调“可解释、可调”。
4. **怎么落地**：上线前用历史回放校验 + 试播季 shadow mode（不影响播出但内部对比） + 公开透明说明。
5. **风险与对策**：识别不清（KPI2 宽）周要谨慎解读；对极端人气选手的舆情预案；tie-handling 规则公开化。