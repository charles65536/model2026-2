下面这四块内容（**principle / operation / validation / panel construction 写法**）我都只基于你们本轮“P0 周面板 + BL-0 baseline”这条已落盘口径来整理；所有关键点都能在**题面数据说明**、你们的 **context_pack**、**kpi_registry** 和 **p0_triage_build_weekly_panel.py** 中找到依据。   

---

## 1) 我们本次对数据处理的 principle（原则）

### P1. **“口径优先、指标导向”，不做泛 EDA**

* 只做能让 KPI 分母/切片/回放 baseline 可复现的最小处理：构建 season–week–celebrity 周面板作为“唯一输入接口”。
* 原因：你们后续的核心模型（投票份额反推 + 规则回放）明确依赖 (A_{s,t})、(J_{i,t})、(E_{s,t})、(p_{i,t}) 这一套周粒度定义。

### P2. **“保留编码痕迹，但用 eligibility 规则排除其对指标的污染”**

* 题面明确：**淘汰后周分数为 0**；**N/A** 既可能表示“当周没第 4 位评委”，也可能表示“该季节目周数不够，后续周不存在”。
* 因此我们不把这些“清洗成正常值”，而是：保留为审计证据，同时通过 `active=False` 把它们排出 KPI 分母。

### P3. **确定性、可复现（deterministic）优先**

* 退赛/淘汰的处理要可复算：`Eliminated Week k` 用解析得到的周次；`Withdrew` 用“最后一个非缺失/或最后一个正分周”推断退出周并标注 `exit_type`。
* 周内评委缺失（3 vs 4 judge）只做 `skipna` 汇总，不做插补。 

### P4. **评委身份不追踪，只使用周内相对量**

* 题面指出 judge 序号不是固定身份（“Judge Y may not be the same judge…”）。
* 因此只使用当周总分、当周 rank、当周 percent，不用“judge1/2/3/4 的跨周人格化特征”。

### P5. **不把“特殊周”硬塞进同一分母**

* 题面指出存在**无淘汰周**与**多淘汰周**。
* 口径上：无淘汰周从单淘汰一致性分母剔除；多淘汰周用 set-match（bottom-k 命中）处理。

---

## 2) 我们本次对数据处理的实际 operation（操作做了什么）

下面按“可落盘复现的流水线”写（你们代码就是这么做的）：

### O1. **Wide → Long：周面板构建**

* 扫描列名匹配 `weekX_judgeY_score`，展开为每行一个 `(season, celebrity_name, week)`。

### O2. **周内汇总：缺失不插补**

* `all_judges_nan = (judge1..judge4 全 NaN)`
* `total_judge_score = sum(judge_scores, skipna=True)`（允许 3 judge）

### O3. **退出/淘汰标签：解析 results + 推断 withdrew 的 exit_week**

* 从 `results` 解析 `Eliminated Week k` 得到 `elim_week`；并派生 `exit_type ∈ {withdrew, eliminated, finished}`。
* `exit_week` 推断逻辑：优先 `elim_week`；否则取“最后一个正分周”，再不行取“最后一个非缺失周”。
* `true_elim_flag` 只标记淘汰周（withdraw 默认不算 true elimination）。

### O4. **Eligibility / Active set：把编码痕迹排出 KPI 分母**

* `active = (not all_judges_nan) & (week <= exit_week)`
* 额外边界：`total_judge_score==0` 且不是 `exit_week` → 标记 `data_anomaly_zero_score=1` 并强制 `active=False`（避免“退出后 0 分延展”污染 active）。

### O5. **周内相对量：rank / percent（仅对 active）**

* 在每个 `(season, week)` 内，对 active 选手计算 `judge_rank` 与 `judge_percent`（为后续 baseline/回放/优化准备输入）。

### O6. **BL-0 baseline 与产物落盘（用于 KPI1/KPI3 对照）**

* kpi_registry 定义：

  * Rank scheme：仅用 `judge_rank`（uniform fan rank 只加常数）。
  * Percent scheme：用 `judge_percent + 1/n_active`（uniform fan percent）。
* 输出文件接口在脚本头部固定：`intermediate_weekly_panel.csv / intermediate_baseline_preds.csv / tab_baseline_consistency.tex / fig_fliprate_by_season.pdf`。

---

## 3) 我们对这样的数据清洗结果的 validation（验证怎么做）

这里给你们一套**不依赖额外“深度清洗”**、但能写进报告/附录的验证清单（每条都能自动化）：

### V1. **Schema/覆盖验证（“面板构建没跑偏”）**

* 检查是否成功识别到 `weekX_judgeY_score` 列，否则脚本会直接报错（防止列名不匹配 silent failure）。
* 检查周面板粒度：是否确实是一行一个 `(season, week, celebrity)`（这是你们 slice/window 的“单位分析粒度”）。

### V2. **题面编码一致性验证（“0 与 N/A 的语义没搞错”）**

* N/A 的两类来源（缺第 4 judge、以及该季不存在的周）必须在面板里以缺失体现、且不被插补。
* 淘汰后 0 分必须被视作编码延展，不能进入 (A_{s,t})（active set）——这点在你们建模符号定义里已经写死：0 分记录用于识别淘汰后状态，而非新表演。

### V3. **Eligibility 不变量验证（“分母干净”）**

* 对每个 `(season, week)`：

  * 仅在 `active=True` 子集上计算 `judge_percent`，且应满足 (\sum_{i\in A_{s,t}} q^J_{i,t}=1) 的归一性质（定义即如此）。
* `data_anomaly_zero_score` 被标记的样本必须 `active=False`（脚本强制），防止分母污染。

### V4. **结果标签一致性验证（“淘汰/退赛标签靠谱”）**

* `Eliminated Week k` → 仅 week=k 的 `true_elim_flag=1`；withdraw 默认不计入 `true_elim_flag`，但保留 `exit_type="withdrew"` 用于敏感性分析（写作时要明示）。 
* 无淘汰/多淘汰周在 KPI 分母里按口径处理（无淘汰剔除、多淘汰 set-match），避免“命中率虚高”。

> 报告写法建议：把 V1–V4 写成“Data Credibility & Auditability”小节，强调**我们没有把数据洗得更‘漂亮’，而是洗得更‘可审计’**。这与你们 context_pack 的表述完全一致：保留痕迹、靠 `active=False` 排除，边界样本作为 stress-test 风险点记录。

---

## 4) 文章里写的 “panel construction” 是什么？要怎么写？

### 概念一句话

**Panel construction = 把题面提供的“宽表（每周×每评委一个列）”变成“长表周面板（season–week–contestant 一行）”，并补齐 eligibility/exit 标签，使其成为后续优化与回放仿真的统一输入。** 

### 你们论文里建议放的位置

放在 **Data / Preprocessing** 章节开头，紧跟符号定义（(A_{s,t}, J_{i,t}, E_{s,t})）之后最自然。

### 可直接粘贴的英文段落（paper-ready，零数值）

> 这段不会承诺任何数值结果，只描述口径与接口。

We construct a season–week–contestant panel by reshaping the official wide-format judge-score columns (`weekX_judgeY_score`) into long rows, one record per ((s,t,i)). For each record, we aggregate weekly judge performance as (J_{i,t}) using `skipna` to respect varying judge counts and N/A encodings. We then deterministically label eligibility and exits (`active`, `exit_week`, `exit_type`, `true_elim_flag`) based on the official `results` field and the dataset’s post-exit zero-score convention, so that only (i\in A_{s,t}) enters KPI denominators and downstream optimization/replay modules. This panel serves as the canonical, reproducible interface for vote-share inference and rule comparison.   

### 中文注解版（写给组员“怎么操作/怎么理解”）

* “panel” 就是你们后续所有模型统一用的那张表：每行一个 `(season, week, celebrity)`。
* 关键不是“把缺失补齐”，而是：

  1. `skipna` 聚合周内总分；
  2. 依据 `results` + “淘汰后记 0 分”规则做 `exit_week`；
  3. 用 `active` 把“结构性缺失周 + 淘汰后 0 分延展”排出分母。 
