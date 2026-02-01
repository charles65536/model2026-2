# 粉丝投票与竞赛规则建模体系
## Task A: 粉丝票数反推模型 (The Vote Reconstruction Model)
### 核心改进
为解决“众生平等（1-3%差异）”问题，在目标函数中新增“锚定项”(Anchoring Term)。假设：无强烈反常信号时，粉丝票数分布趋势应大致“锚定”于评委评分分布（强者恒强），而非平均分布。

### 1. 符号定义
- $s$: 赛季，$t$: 周次，$i$: 选手
- $A_{s,t}$: 第 $s$ 季第 $t$ 周在场选手集合
- $E_{s,t}$: 第 $s$ 季第 $t$ 周实际被淘汰的选手集合
- $J_{i,t}$: 选手 $i$ 在第 $t$ 周的评委原始总分
- $q_{i,t}^J$: 评委分数份额（已知），$q_{i,t}^J = J_{i,t} / \sum_{k \in A_{s,t}} J_{k,t}$
- $p_{i,t}$: 待求解的粉丝投票份额（Fan Vote Share）
- $\xi_t$: 待求解的松弛变量（Slack Variable），代表该周规则无法解释的程度

### 2. 优化目标函数 (Objective Function)
最小化以下三项总和：
$$\min_{p, \xi} \quad \sum_{t=1}^{T} \left( \underbrace{\sum_{i \in A_t} (p_{i,t} - p_{i,t-1})^2}_{\text{Term 1: Temporal Smoothness}} + \lambda_1 \underbrace{\sum_{i \in A_t} (p_{i,t} - q_{i,t}^J)^2}_{\text{Term 2: Judge Anchor Prior}} + \lambda_2 \underbrace{\xi_t^2}_{\text{Term 3: Violation Penalty}} \right)$$

- Term 1 (时间平滑)：防止票数在一周内发生剧烈跳变（除非必要）
- Term 2 (评委锚定 - 救命项)：解决核心问题的关键
  - 迫使粉丝票 $p_{i,t}$ 在默认情况下趋向于评委给出的份额 $q_{i,t}^J$
  - 效果：评委分高的选手倾向于获得高票，评委分低的获得低票，自然拉开差距（不再是全员10%）
  - 仅当“评委分高但被淘汰”的强约束出现时，才牺牲该项强行压低票数
- Term 3 (违规惩罚)：迫使松弛变量 $\xi$ 尽可能为0，即尽可能满足淘汰规则

### 3. 约束条件 (Constraints)
1. 概率归一化：
$$\sum_{i \in A_{s,t}} p_{i,t} = 1, \quad \forall t$$

2. 非负性：
$$p_{i,t} \ge 0, \quad \xi_t \ge 0$$

3. 淘汰一致性约束 (带松弛变量)：对于每一个被淘汰者 $e \in E_{s,t}$ 和每一个幸存者 $k \in A_{s,t} \setminus E_{s,t}$：
$$S_{e,t} \le S_{k,t} + \xi_t$$

其中综合得分 $S$ 定义为 Percent 规则（大多数赛季）：
$$S_{i,t} = \alpha \cdot q_{i,t}^J + (1-\alpha) \cdot p_{i,t}$$

> 注：如果是 Rank 规则的赛季，$S$ 定义为 $Rank(q^J) + Rank(p)$，但这会导致整数规划。建议统一用 Percent 规则反推票数（假设底层人气是连续的），然后在 Task B 再进行 Rank 规则的离散仿真。

## Task B: 规则回放仿真 (The Simulation Engine)
需处理“如果选手未被淘汰，下一周得多少分”的缺失值插补 (Imputation) 问题。

### 1. 缺失数据处理 (The Zombie Logic)
若新规则让选手 $i$ 在第 $t$ 周存活（现实中已被淘汰），需生成其第 $t+1$ 周的评委分 $\hat{J}_{i,t+1}$ 和粉丝份额 $\hat{p}_{i,t+1}$：
- 评委分插补：使用该选手的历史平均水平
$$\hat{J}_{i,t+1} = \frac{1}{t} \sum_{k=1}^{t} J_{i,k}$$

- 粉丝份额插补：沿用 Task A 算出的上一周份额（平滑假设）
$$\hat{p}_{i,t+1} = p_{i,t}$$

### 2. 仿真流程
对每个赛季 $s$，初始化 $A_{s,1}$ 为全员。

For $t = 1$ to $T_s$:
1. 输入：当周在场选手的 $J_{i,t}$ (或插补值) 和 $p_{i,t}$ (来自 Task A)
2. 计算规则结果：
   - Rule 1 (Percent): 计算 $S_i^{Pct} = 0.5 q_i^J + 0.5 p_i$，淘汰 $S$ 最低的 $m_t$ 人
   - Rule 2 (Rank): 计算 $R_i^{Total} = R(J_i) + R(p_i)$，淘汰 $R$ 最大的 $m_t$ 人
   - Rule 3 (Bottom-2 + Save): 找出 $S_i^{Pct}$ 最低的 2 人，比较其 $J_{i,t}$，保留 $J$ 高者，淘汰 $J$ 低者
3. 更新集合：$A_{s,t+1} = A_{s,t} \setminus \{ \text{Eliminated} \}$
4. 记录差异：记录本周被淘汰者，若与历史不同则记为“Reversal”

### 3. 衡量指标
- Reversal Rate (翻盘率)：新规则导致淘汰结果改变的周数比例
- Bias Index (偏向性)：
$$Bias = \frac{1}{T} \sum_t (Rank(p_{survivor}) - Rank(p_{eliminated}))$$

> 若 Bias 大，说明该规则倾向于保留粉丝票高的人。

### 4. 稳健性检验（Robustness Check）：基准插补方案的合理性

在 Task B 的反事实规则回放仿真中，当某选手在假想规则下存活、但在真实比赛中已被淘汰时，其后续周次的评委评分与粉丝投票份额在数据中不可观测，必须通过插补获得。由于反事实结果本身不可验证，本文采用保守的基准插补方案，并对其合理性进行说明，以确保仿真结论不依赖于人为引入的激进假设。

#### 基准插补方案

主分析中采用保守的基准插补方案，以尽量减少人为引入的动态变化。对于在第 \(t\) 周在假想规则下存活的选手 \(i\)，其第 \(t+1\) 周的插补值定义为：

\[
\hat{J}_{i,t+1}
= \frac{1}{t}\sum_{k=1}^{t} J_{i,k},
\qquad
\hat{p}_{i,t+1}
= p_{i,t}.
\]

该方案假设在缺乏额外信息的情况下，选手的技术表现与粉丝支持度在短期内保持在其历史平均或最近水平附近，不会人为制造上升或下降趋势。同时，该假设与 Task A 中所采用的时间平滑与正则化思想保持一致，从而在模型整体上形成一致的行为假设。

#### 稳健性说明

基准插补方案通过最小化对反事实路径的主观干预，确保规则对比结果主要由不同投票与淘汰机制的结构性差异所驱动，而非由插补过程中引入的趋势假设所主导。因此，在后续规则比较中观察到的翻盘率（Reversal Rate）与偏向性指标（Bias Index）可被视为对规则本身影响的保守估计。


## Task C: 混合效应模型 (Factor Analysis)
使用线性混合模型 (LMM) 隔离“舞者效应”和“选手特征”。

### 1. 模型形式
将因变量设为粉丝份额的 Logit 变换（将 $(0,1)$ 映射到实数轴）：
$$Y_{i,t} = \ln\left(\frac{p_{i,t}}{1 - p_{i,t}}\right)$$

方程如下：
$$Y_{i,t} = \beta_0 + \underbrace{\beta_1 \text{Age}_i + \beta_2 \text{Gender}_i + \beta_3 \text{Industry}_i}_{\text{Fixed Effects (Star Traits)}} + \underbrace{\gamma \cdot \text{JudgeScore}_{i,t}}_{\text{Control Variable}} + \underbrace{u_{Partner(i)}}_{\text{Random Effect (Pro)}} + \underbrace{v_{Season(s)}}_{\text{Random Effect (Season)}} + \epsilon_{i,t}$$

### 2. 关键检验
- 职业舞者影响 (Pro Effect)：检验随机效应方差 $\sigma_u^2$
  - 计算 ICC (Intra-Class Correlation): $\text{ICC} = \frac{\sigma_u^2}{\sigma_u^2 + \sigma_v^2 + \sigma_\epsilon^2}$
  - 若 ICC 显著（例如 > 0.1），说明职业舞者对人气有很大加成（自带粉丝或编舞能力强）
- 特征偏好差异：
  - 建立两个模型，一个 $Y$ 是粉丝票，一个 $Y$ 是评委分
  - 比较 $\beta_{Age}$ 在两个模型中的正负。例如：评委模型中 $\beta_{Age} \approx 0$，但粉丝模型中 $\beta_{Age} < 0$（显著），说明粉丝比评委更歧视大龄选手

## Task D: 新规则 (The "Merit-Safe" Rule)
提出 "Judge Safeguard + Smoothed Rank" (JS-SR) 规则。

### 1. 设计逻辑
纯 Percent 制易让人气王碾压，纯 Rank 制易抹杀巨大分数差距。新规则引入“技术保护区”(Safeguard Zone)。

### 2. 数学定义
对于第 $t$ 周的选手集 $A_t$：
1. 定义保护阈值：
设 $\tau$ 为当周评委分位点（如前 30%）
$$\text{Threshold}_t = \text{Percentile}(J_{i,t}, 70\%)$$

2. 生成安全名单：
$$\text{SafeSet}_t = \{ i \in A_t \mid J_{i,t} \ge \text{Threshold}_t \}$$

> 这些选手本周豁免淘汰，无论粉丝票多低。

3. 危险区决胜 (The Battleground)：
对于剩下的选手 $D_t = A_t \setminus \text{SafeSet}_t$：
计算加权综合分：
$$Score_i = 0.4 \cdot q_{i,t}^J + 0.6 \cdot p_{i,t}$$

淘汰 $Score_i$ 最低的 $m_t$ 人。

### 3. 优势阐述
- 公平性：杜绝“评委第一名因无粉丝而被淘汰”的悲剧（如 Jerry Rice 案例的反面）
- 观赏性：危险区内粉丝投票权重提升（0.6），保证剩余选手中粉丝意愿起决定性作用，制造“神仙打架（安全区）”和“生死乱斗（危险区）”的双重看点