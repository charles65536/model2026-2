# 文件使用说明与日志

2.1 晚

---

## 1.弃用

经过实践，我们决定弃用intermediate_baseline_preds.scv和intermediate_weekly_panel.csv，不将它们作为我们项目中使用和进入文章的数据集

## 2.新数据集的使用与说明

### clean_long_data_new1.csv

下面是对这个数据集的一些解释，由AI生成，注意辨别。这并不代表你不需要再分析一遍

你想弄明白 Step 2A-2F（技术实现流程）和题目「4 个核心问题（问腿）」之间的对应关系，其实核心逻辑很清晰：2A-2F 是「落地实现的技术链路」（偏 “怎么做”），4 个问题是「题目要求的业务结论」（偏 “要回答什么”），技术链路是为了支撑业务结论，二者是「手段」与「目的」的关系。
下面我帮你把这个对应关系讲透，同时结合你当前的进度，明确每一步技术工作对应的题目得分点：
一、先明确两个核心维度的定义

Step 2A-2F：是针对 MCM Problem C 的「数据处理→建模→分析→输出」的技术实现流程，是从原始数据到最终结论的 “工具链”，偏工程实现和建模严谨性，决定了你的答案是否 “站得住脚”。
4 个核心问题（问腿，MCM Problem C 常规设问）：是题目要求你解答的业务 / 场景问题，偏结论输出和行业洞察，决定了你的答案是否 “切中题意”，一般包括以下 4 类（对应你提到的 2F 模块）：
问题 1：规则对比（rank vs percent 评分规则的差异、优劣、对结果的影响）
问题 2：争议复盘（指定争议选手的淘汰 / 晋级合理性，量化分析）
问题 3：机制模拟（judges save、bottom two 等机制的作用，量化评估）
问题 4：新系统设计（提出更合理的评分 / 淘汰系统，并用数据验证其有效性）



二、Step 2A-2F 与 4 个问题的逐环节对应关系
1. Step 2A（数据清洗，已完成 ✅）：所有 4 个问题的「基础底座」

对应关系：无直接对应某个问题，但支撑所有 4 个问题的分析。
核心作用：把混乱的原始宽表转化为标准、干净的长表（clean_long_data_新生成的长表.csv），是后续所有建模、分析、对比的前提。没有 2A 的干净数据，4 个问题的分析都无从谈起（比如无法准确回放某季某周的比赛结果）。
对题目价值：保证后续所有结论的「数据准确性」，是冲奖的 “底线要求”。

2. Step 2B（评委指标计算，已完成核心 ✅）：所有 4 个问题的「指标支撑」

对应关系：支撑问题 1（规则对比）、问题 4（新系统设计），同时辅助其他问题。
核心作用：生成J_total、J_pct（已完成）、J_rank（可选）等评委评分相关指标，是后续对比「rank 规则」和「percent 规则」的核心数据基础。
对题目价值：为规则对比提供「量化指标」，避免主观臆断，让结论更有说服力。

3. Step 2C（淘汰似然模块，已完成 ✅）：所有 4 个问题的「核心模型」

对应关系：支撑所有 4 个问题，是整个建模的 “心脏”。
核心作用：实现了基于rank/percent的 softmax 淘汰似然函数，能够量化计算每个选手的淘汰概率，这是：
问题 1（规则对比）：回放不同规则下的淘汰结果，量化差异；
问题 2（争议复盘）：计算争议选手当时的淘汰概率，判断是否 “合理”；
问题 3（机制模拟）：模拟 judges save 机制对淘汰概率的影响；
问题 4（新系统设计）：验证新系统下的淘汰结果稳定性和合理性。


对题目价值：把 “定性分析” 转化为 “定量建模”，是 MCM 冲奖的「核心加分项」（体现建模能力）。

4. Step 2D（MAP/MCMC 求 pi,s,w​，已完成 MAP ✅，MCMC 待做 ⏳）：所有 4 个问题的「核心参数」

对应关系：支撑所有 4 个问题，pi,s,w​（粉丝票份额）是关键隐藏参数。
核心作用：
MAP 求解得到p_hat（粉丝票份额估计）：能够还原每场比赛的 “粉丝偏好”，结合评委得分，就能完整回放比赛结果，是所有分析的核心参数；
MCMC/bootstrap（待做）：为p_hat提供不确定性区间，让结论更严谨（比如 “某选手淘汰概率为 0.3397，95% 置信区间为 [0.28, 0.39]”）。


对题目价值：解决了 “粉丝票不可观测” 的核心痛点，是整个模型能够落地的关键，MCMC 部分更是冲奖的「高分亮点」（体现统计严谨性）。

5. Step 2E（三类指标体系，正在开始 ⏳）：所有 4 个问题的「说服力支撑」

对应关系：支撑所有 4 个问题的「结论可信度」，是冲奖的「关键加分项」（体现分析的深度和严谨性）。
核心作用：通过计算 Top-1 命中率、log-likelihood、kappa 敏感性等指标，量化评估模型的：
一致性：模型预测结果与真实结果的吻合程度；
确定性：模型参数（如 kappa）变化对结果的影响（稳定性）；
偏向性：不同规则 / 系统对不同类型选手（如年龄、行业）的偏向。


对题目价值：不是直接回答题目问题，而是 “证明你的回答是可靠的”，避免模型 “自说自话”，这是从 “合格答案” 到 “优秀答案” 的关键跨越。

6. Step 2F（子问分析与新系统，未开始 ⏳）：直接对应 4 个问题的「结论输出」

对应关系：1:1 对应题目 4 个核心问题，是整个建模工作的「最终成果展示」。
核心作用：把前面 2A-2E 的所有技术成果，转化为题目要求的业务结论，包括：
用p_hat和淘汰似然，对比 rank vs percent 规则的差异（问题 1）；
复盘 Jerry/Billy 等争议选手的淘汰概率，量化争议点（问题 2）；
模拟 judges save 机制，分析其对比赛结果的影响（问题 3）；
设计新的评分系统，用 2E 的指标体系验证其优越性（问题 4）。


对题目价值：直接满足题目的答题要求，是得分的「核心载体」，前面所有的技术工作，最终都要通过 2F 呈现给评委。

三、核心总结（关键对应逻辑）

2A-2D：是「基础支撑层」，解决 “如何建模” 的问题，为回答 4 个题目问题提供工具和数据，是冲奖的 “地基”。
2E：是「严谨性保障层」，解决 “我的模型是否可靠” 的问题，是冲奖的 “加分项”，实现从合格到优秀的跨越。
2F：是「结论输出层」，解决 “如何回答题目问题” 的问题，直接对应 4 个核心设问，是得分的 “载体”。
整体逻辑：2A→2B→2C→2D→2E→2F 是一条「从数据到模型，从模型到验证，从验证到结论」的完整闭环，最终落地到解答题目 4 个核心问题。


### clean_long_data_new1.csv / clean_long_data_replay_ready.csv / canonical_replay_ready.csv（vNext 数据口径）

**CN（可执行口径）**
- `clean_long_data_new1.csv`：将官方宽表 `2026_MCM_Problem_C_Data.csv` 确定性地 reshape 为长表周面板（1 行 = 1 个 season–week–contestant）。
  - 核心字段：`season, week, contestant_id, celebrity_name`；
  - 评委信息：`J_total`（当周评委总分，按题面 `N/A` 直接 skip-na 求和）、`J_sum_week`（当周 active 选手总分之和）、`J_pct`（当周评委得分占比）；
  - 标签：`active`（是否进入当周分母/回放分母）、`elim_week`（退出周/淘汰周）、`eliminated`（是否为该周末被淘汰者）。
- `clean_long_data_replay_ready.csv`：与 `clean_long_data_new1.csv` 同一面板内容，但增加回放代码对齐字段：
  - `total_judge_score = J_total`，`judge_percent = J_pct`，`exit_week = elim_week`。
- `canonical_replay_ready.csv`：**当前版本与 `clean_long_data_replay_ready.csv` 完全一致**（同列同内容）。项目内建议把它作为唯一 “canonical 输入面板”（后续所有 KPI/回放/推断都从它读），避免多口径漂移。

**关于“插补”(Imputation) 的澄清**
- 本项目提到的 “插补/补全” 指：当做反事实回放时，若某选手在真实历史中已退出，则其后续周的表现对反事实是未观测量。我们只允许使用“保守、最小信息假设”去补全回放所需输入以完成仿真闭环；该补全不用于预测选手真实后续表现，也不用于生成对外的“表现预测”结论。

**EN (report-ready)**
- `clean_long_data_new1.csv` is a deterministic season–week–contestant long panel reshaped from the official wide CSV. It contains within-week judge aggregates (`J_total`, `J_sum_week`, `J_pct`) and minimal replay labels (`active`, `elim_week`, `eliminated`).
- `clean_long_data_replay_ready.csv` is the same panel with field-name aliases required by the replay code (`total_judge_score`, `judge_percent`, `exit_week`).
- `canonical_replay_ready.csv` is currently identical to `clean_long_data_replay_ready.csv` and should be treated as the single canonical input to avoid definition drift.
- “Imputation” (when mentioned) is used only to close counterfactual replays under conservative, minimal-information assumptions for unobserved post-exit segments; it is not interpreted as forecasting contestant performance.
