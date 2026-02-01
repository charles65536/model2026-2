# Fan-share estimator (Task A) — Developer Guide

This module implements the constrained-smoothness estimator for weekly fan vote shares described in the project modeling notes (Task A). It consumes a canonical, pre-cleaned weekly panel and produces two CSV outputs:

- fan shares (`p_est`): per-season-per-week estimated fan vote share p_{i,t} for every active contestant i and week t
- slack variables (`xi`): per-season-per-week non-negative slack values that quantify how much the elimination consistency constraints had to be relaxed for feasibility

This README duplicates and expands on the inline comments in `model_main.py` so other developers can pick up, run, and integrate the solver quickly.

Contents
- Purpose
- Concepts: what `fan_p` and `xi` mean
- Modeling significance of the solved variables (mapping to the math spec)
- Expected input (weekly panel) schema
- Outputs and example columns
- CLI usage examples
- Important design choices & internals (objective, constraints)
- Troubleshooting & common gotchas
- Testing and quick sanity checks
- Integration notes (where to call from run script)
- Recommendations (solver alternatives and next improvements)

---

Purpose

The estimator reconstructs relative fan voting shares p_{i,t} (normalized to sum to 1 across participants each week) that are consistent with known weekly eliminations and are temporally smooth. Because the problem is underdetermined (actual votes are unobserved), we select the most "reasonable" solution using a smoothness prior and a small slack for elimination constraints.

Concepts — `fan_p` (p_est) and `xi`

- fan_p / p_est (CSV column name `p_est`)
  - Meaning: estimated fraction of the weekly fan vote received by contestant i in week t, i.e. p_{i,t} in [0,1], and for each week t, sum_{i in A_t} p_{i,t} = 1.
  - Interpretation: these are relative (percentage-like) shares, not absolute vote counts. They are the model's best reconstruction under the specified smoothness and elimination constraints.
  - Use cases: feed into rule-replay/simulation modules to see how alternative voting/elimination rules would have changed outcomes; compute contestant-level season averages; analyze discrepancies between judge ranks and fan support.

- xi (CSV column name `xi`)
  - Meaning: non-negative slack (one value per season-week) introduced to relax the hard requirement that eliminated contestants must strictly be among the bottom m of the combined score S_{i,t}. xi_t quantifies how much the model had to "bend" elimination consistency for that week to make the optimization feasible.
  - Interpretation: larger xi indicates that under the modeling assumptions (alpha, percent/rank formula, judge percent qJ), the recorded elimination for that week is less consistent with any plausible fan-share assignment unless one allows relaxation. xi is therefore a flag for ambiguous/exceptional weeks (special rules, judge saves, data noise, or inconsistent recording).

Modeling significance of the solved variables (mapping to `files_for_AI/first_stage_modeling.md`)

This section connects the solver outputs directly to the mathematical formulation in the modeling spec (Task A). It explains what the solver is estimating and how the outputs should be interpreted in downstream analyses.

- Notation mapping
  - p_est -> p_{i,t}
    - The CSV `p_est` column stores the estimated p_{i,t} for each row (season, contestant, week).
    - In the spec, p_{i,t} is the unknown fan vote share for contestant i in week t with constraints p_{i,t} >= 0 and sum_{i in A_t} p_{i,t} = 1.
  - xi -> \xi_t
    - The CSV `xi` column stores the slack variable \xi_t for each (season, week).
    - \xi_t appears in the elimination consistency constraints as a non-negative slack allowing S_{e,t} <= S_{i,t} + \xi_t for eliminated e and non-eliminated i.

- How these feed into the combined score S_{i,t}
  - The solver computes judges' percentage q^{J}_{i,t} from the panel (qJ in code) and forms the combined score used in the elimination constraints:
    S_{i,t} = alpha * q^{J}_{i,t} + (1 - alpha) * p_{i,t}
  - p_est is the model's estimate of q^{V}_{i,t} in the spec (fan vote share). Downstream simulations should use S_{i,t} with the same alpha to replay Percent-rule eliminations.

- Elimination-consistency constraints (how xi is used)
  - For a week with elimination set E_t of size m, the spec requires eliminated contestants to be among the bottom m by S_{i,t}. We relax that hard combinatorial constraint into linear inequalities with slack \xi_t:
    For each e in E_t and each i in A_t \ E_t:
      S_{e,t} <= S_{i,t} + \xi_t
  - In the solver, xi is penalized in the objective as lambda * \sum_t xi_t^2, so the optimizer prefers small xi but allows positive values when the elimination record cannot be explained exactly under the percent rule and smoothness prior.

- Objective and interpretation
  - Objective minimized by solver:
    Sum_{t=2..T} Sum_{i in A_t ∩ A_{t-1}} (p_{i,t} - p_{i,t-1})^2  +  lambda * Sum_t xi_t^2
  - Temporal smoothness term enforces the modeling assumption that fan preference evolves smoothly (A5.2 in the spec). The lambda*xi^2 term enforces the "minimum distortion" (A5.3): prefer solutions that explain eliminations while minimizing violations.

- Uncertainty and diagnostics derived from outputs
  - xi_t as a diagnostic signal:
    - If xi_t ≈ 0: elimination for week t is well explained by some p_{·,t} under the model assumptions.
    - If xi_t is relatively large: the recorded elimination is inconsistent / ambiguous; investigate the week for special rules, judge-saves, or data issues.
  - Delta (elimination margin) \Delta_t (computed from outputs, not directly written by the solver):
    - Define S_hat_{i,t} using p_est.
    - Compute \Delta_t = min_{i in A_t \ E_t} S_hat_{i,t} - max_{e in E_t} S_hat_{e,t}.
    - Small or negative \Delta_t indicates the eliminated contestant(s) were not obviously the bottom by S_hat; corresponds to larger xi.
  - Feasible interval approach (A7.1): compute p^{min}_{i,t} and p^{max}_{i,t} by solving LPs that fix the same constraints but optimize one p_{i,t} at a time. These intervals quantify multi-solution uncertainty.

- Suggested downstream uses of p_est and xi (aligned to the spec sections A and B):
  - Use p_est as q^{V}_{i,t} when replaying Percent-rule eliminations in the simulator (Task B) and compute E^{(P)}_t and R^{(P)}.
  - Use p_est to compute R^{V}_{i,t} (fan ranking) when replaying Rank-rule eliminations and then form R^{(R)}_{i,t} = R^{J}_{i,t} + R^{V}_{i,t}.
  - Use xi to flag weeks to treat specially in analysis (e.g., exclude from some metrics, or mark as "contestable" weeks in the paper/appendix).
  - Use p_est seasonal averages to compare contestants' overall fan support vs final placement (controversy analysis) and to compute the discrepancy metrics described in the repo (avg_weekly_rank vs final_rank difference).

Expected statistical meaning and caveats
- p_est is an estimate under the chosen priors and constraints. Because true votes are unobserved, different priors or lambda/alpha choices will lead to different p_est; treat p_est as a model-based reconstruction, not ground truth.
- xi reports how much the percent-rule explanation needs to be relaxed; large xi weeks should be interpreted carefully and investigated qualitatively (show episodes, special rules).
- The solver's smoothness objective can cause oversmoothing if lambda is too small or alpha is mis-specified; include sensitivity checks in experiments (alpha ∈ [0.4,0.6], lambda grid search as recommended in the spec).

Expected input (weekly panel)

This module expects the weekly panel CSV to be the authoritative, pre-cleaned input. It explicitly does NOT attempt to recreate or re-clean the panel. The canonical panel (the triage script produces) should have at least these columns (defaults):

- `season` (int or string): season identifier
- `celebrity_name` (string): contestant identifier — use `--name-col` if your panel uses a different name
- `week` (int): week index within season
- `total_judge_score` (numeric): judges' aggregated score for that contestant-week

Optional columns supported (if present, pass via CLI flags):
- `active` (bool-like): whether the contestant performed and is considered active that week. If not provided, rows with non-null `total_judge_score` and >0 are treated as active.
- `true_elim_flag` or other elimination indicator (bool-like): mark rows that correspond to the eliminated contestant(s) that week. If absent, the solver will not add elimination constraints.

If your column names differ, use the CLI flags `--name-col`, `--score-col`, `--week-col`, `--active-col`, and `--elim-col` to map them.

Outputs

Two CSVs are produced (paths provided through CLI):

1) Fan shares: CSV with columns (example)
- `season` — copied from panel
- `celebrity_name` (or your name_col) — contestant id
- `week` — week index
- `p_est` — estimated fan share for the contestant-week

2) Xi (slack) CSV: columns
- `season`
- `week`
- `xi` — non-negative slack indicating violation magnitude of elimination consistency for that week

CLI usage and examples

Basic example (use canonical panel produced by triage):

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares.csv" \
  --out-xi "src\sim\xi.csv" \
  --alpha 0.5 --lambda_reg 1000 --verbose
```

If your panel uses different column names:

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares.csv" \
  --out-xi "src\sim\xi.csv" \
  --name-col "name" --score-col "total_score" --week-col "week_num" \
  --active-col "active" --elim-col "true_elim_flag" \
  --alpha 0.5 --lambda_reg 2000
```

CLI flags (summary)
- `--panel` (required): path to canonical weekly panel CSV
- `--out-p` (required): path to write fan-shares CSV
- `--out-xi` (required): path to write xi CSV
- `--alpha` (optional, default=0.5): weight on judges when forming combined score S (alpha ∈ [0,1])
- `--lambda_reg` (optional, default=1000): regularization for xi in objective
- `--name-col` (default=`celebrity_name`)
- `--score-col` (default=`total_judge_score`)
- `--week-col` (default=`week`)
- `--active-col` (optional)
- `--elim-col` (optional)
- `--hard-consistency` (optional): enforce elimination consistency as a hard constraint (no xi allowed). Use when you want to prevent inconsistency at all costs; may cause infeasibility.
- `--verbose` (optional)

Findings summary (diagnostics & sensitivity)

- Identification: The weekly panel + elimination constraints alone are often insufficient to uniquely reconstruct fan-share p_{i,t} (LP feasibility checks show wide p_min/p_max ranges for many contestant-week pairs). In short: the data are under-determined in many weeks.
- Prior effect: Adding a small per-week regularizer (variance or entropy) strongly biases solutions toward more uniform distributions when information is weak. In our experiments a modest entropy regularization (e.g., entropy_reg ≈ 0.1) already produces near-uniform weekly p vectors; larger values saturate quickly because entropy is bounded by log(n).
- Slack (xi): The solver required almost no slack (xi values ≈ 1e-7) across runs — eliminations are not highly contradictory to judge scores under the model; the observed uniformity therefore comes from the prior, not from forced feasibility via xi.
- Practical recommendation: Treat the reconstructed p_est as model-based, not ground truth. If you want a conservative, defensible default when data are weak, use a small entropy prior (entropy_reg in [0.01, 0.1]) and report sensitivity (0.0 and 0.1 or 1.0) in any analysis/appendix.
- Next steps to improve robustness: (1) run a documented grid sweep and include those tables in the appendix (done in `src/sim/grid_sensitivity_report.csv`), (2) flag weakly-identified contestant-week pairs using LP intervals + profiling so results can be annotated or excluded, and (3) for production, consider reimplementing the QP in matrix form and solving with a dedicated QP solver (cvxpy + OSQP) for stability/performance.

---

Important design choices & internals (brief)

- Objective: temporal smoothness on p_{i,t} (squared differences between consecutive-week shares for the same contestant) plus lambda * sum(xi_t^2). Minimizes change over time and penalizes slack usage.
- Constraints:
  - Per-week simplex: sum_{i in A_t} p_{i,t} = 1, p_{i,t} >= 0.
  - For weeks with elimination info, the model enforces "elimination consistency" via linear inequalities with xi slack: for each eliminated e and each non-eliminated i, S_{e,t} <= S_{i,t} + xi_t, where S_{i,t} = alpha*qJ_{i,t} + (1-alpha)*p_{i,t} and qJ is judges' share.
- Solver: SciPy SLSQP via `scipy.optimize.minimize`. This is dependency-light and works for our problem sizes. For large seasons or heavier production use, consider moving to a QP solver (`cvxpy` + `OSQP`) for speed and numeric robustness.

Troubleshooting & common gotchas
- If the solver fails to converge or returns infeasible, try:
  - Check that the panel is canonical and `elim_col` points to correct boolean elimination rows.
  - Increase `--lambda_reg` (gives more slack penalty but can help numeric stability) or reduce it (if you want xi small it's opposite) depending on symptoms.
  - Use `--verbose` to print per-season variable counts and see which season the solver struggled on.
- If many xi values are large:
  - That indicates recorded eliminations are not consistent with the percent rule & judge scores for reasonable p_{i,t}. Investigate the panel rows (special weeks, judge-save events, or data inconsistencies).
- If `p_est` values look like exact 0/1 spikes: check that the panel's `active` flags and judge scores are correct (edge case participants in a week with zero judge totals can cause the solver fallback to uniform qJ).

Testing and quick sanity checks
- Sanity: After running, for every (season, week) verify that the p_est sum across contestants is ~1.0 within floating tolerance (1e-9). A small helper script can assert this and print failing weeks.
- xi inspection: Sort xi descending to find weeks where elimination consistency was most violated.
- Reproducibility: the SLSQP solver is deterministic for the same starting point and environment; keep `alpha` and `lambda_reg` recorded for experiments.

Integration notes
- Where to call: call this module after `p0_triage_build_weekly_panel.py` (which writes `output/data_cleaned/intermediate_weekly_panel.csv`). The typical pipeline:
  1. Build weekly panel (triage step) → `intermediate_weekly_panel.csv`
  2. Run this estimator → `fan_shares.csv` (p_est) + `xi.csv`
  3. Merge `fan_shares.csv` into contestant-level preprocessed CSV if you need aggregated columns (season averages, comparisons with final rank)
  4. Run rule-replay simulations that require p_{i,t} (Percent vs Rank)

- Suggested filenames (project conventions):
  - panel: `output/data_cleaned/intermediate_weekly_panel.csv`
  - fan-shares: `src/sim/fan_shares.csv` (or `output/data_cleaned/fan_shares.csv`)
  - xi: `src/sim/xi.csv`

Recommendations & next improvements
- Swap SLSQP for a QP solver: rewrite the objective as quadratic form and constraints as matrices; use `cvxpy` with `OSQP` to gain speed and better numerical stability.
- Add a small wrapper to compute p_min/p_max intervals for selected contestants/weeks (A7.1 from modeling notes). This requires solving LPs and can be computationally heavier.
- Add automated unit tests (small fixture panels) that validate per-week sum-to-1, known toy seasons, and check handling of missing elim_col.
- If you need to prevent any inconsistency (xi > 0) use the `--hard-consistency` flag. The solver will enforce elimination constraints without slack. If the instance is infeasible under these hard constraints, the optimizer may fail; use `--verbose` to diagnose which season failed. A recommended diagnostic workflow is:
  1) Run with `--hard-consistency` to detect immediate infeasibility: if the run completes without errors and `xi` output is empty, you have strict-consistency solutions.
  2) If infeasible, run without `--hard-consistency` but with a very large `--lambda_reg` (e.g., 1e6) to force xi to be as small as possible; inspect `xi.csv` to see which weeks require slack and how large it is.
  3) Use the `xi` outputs and `Delta_t` diagnostics to investigate specific weeks (data issues or special rules).

Example: strict enforcement (may fail if data incompatible):

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares_hard.csv" \
  --out-xi "src\sim\xi_hard.csv" \
  --hard-consistency --alpha 0.5
```

If the above fails (infeasible), try forcing small xi via a large lambda:

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares_forced.csv" \
  --out-xi "src\sim\xi_forced.csv" \
  --lambda_reg 1000000 --alpha 0.5 --verbose
```

Notes on additive penalties
- Yes: the objective is additive: Smoothness + lambda * (sum of xi^2). `--lambda_reg` is the proportion-level parameter that trades off inconsistency vs smoothness. Increasing `lambda_reg` makes the optimizer penalize inconsistency more strongly. Setting `--hard-consistency` turns off xi entirely (equivalent to lambda = +infty but handled as a hard constraint).

If you'd like, I can also add a `--fail-on-xi` flag that runs with slack allowed but returns a non-zero exit code (and optionally a report) if any xi exceeds a given threshold; this can help automation (CI) to enforce a tolerable level of inconsistency.

Contact & context
- Modeling spec: `files_for_AI/first_stage_modeling.md` — the mathematics and assumptions implemented here are drawn from that document.
- Code location: `src/sim/model_main.py` (solver implementation)

---
# 粉丝投票占比估计器（任务A）——开发者指南(中文版)

本模块实现了项目建模说明（任务A）中描述的、用于周度粉丝投票占比的**带约束平滑估计器**。该模块接收规范化、预清洗的周度面板数据，并生成两个CSV格式输出文件：

- 粉丝投票占比文件（`p_est`）：包含每个赛季每周、每位在役选手`i`在第`t`周的粉丝投票占比估计值`p_{i,t}`
- 松弛变量文件（`xi`）：包含每个赛季每周的非负松弛值，用于量化为保证优化可行性，需放宽淘汰赛一致性约束的程度

本README文档复刻并扩展了`model_main.py`中的内置注释，便于其他开发者快速理解、运行该求解器并将其集成到现有流程中。

## 目录
- 功能用途
- 核心概念：`fan_p`与`xi`的含义
- 求解变量的建模意义（与数学规范的映射关系）
- 预期输入（周度面板数据）的字段结构
- 输出文件及示例列说明
- 命令行接口（CLI）使用示例
- 重要设计选择与内部实现（目标函数、约束条件）
- 故障排除与常见问题
- 测试与快速合理性校验
- 集成说明（在运行脚本中的调用位置）
- 改进建议（求解器替代方案与后续优化方向）

---

## 功能用途
该估计器重构出满足以下条件的相对粉丝投票占比`p_{i,t}`（每周所有选手的占比之和归一化为1）：
1. 与已知的周度淘汰结果一致；
2. 具有时间平滑性。

由于该问题是**欠定的**（实际投票数据不可观测），我们通过平滑先验和为淘汰约束设置小幅松弛的方式，选择最“合理”的解。

## 核心概念——`fan_p`（p_est）与`xi`
### fan_p / p_est（CSV列名`p_est`）
- 含义：第`t`周选手`i`获得的粉丝投票占比估计值，即`p_{i,t} ∈ [0,1]`，且对每一周`t`，满足`∑_{i ∈ A_t} p_{i,t} = 1`（`A_t`为第`t`周在役选手集合）。
- 解读：该值为相对占比（类百分比），而非绝对投票数。是模型在指定平滑性和淘汰约束下的最优重构结果。
- 适用场景：
  - 输入到规则重放/仿真模块，分析不同投票/淘汰规则对结果的影响；
  - 计算选手在赛季内的平均投票占比；
  - 分析评委排名与粉丝支持度的差异。

### xi（CSV列名`xi`）
- 含义：非负松弛变量（每个赛季-周维度一个值），用于放宽“被淘汰选手必须严格处于综合得分`S_{i,t}`倒数`m`名”的硬性要求，以保证优化问题可行。`xi_t`量化了为使第`t`周的优化问题可行，需放宽淘汰一致性约束的程度。
- 解读：`xi`值越大，说明在当前建模假设下（`alpha`、百分比/排名计算公式、评委占比`qJ`），该周记录的淘汰结果与任何合理的粉丝占比分配方案的一致性越低（需通过放宽约束才能解释）。因此`xi`可作为识别“异常/模糊周”的标志（如特殊规则、评委豁免、数据噪声或记录不一致）。

## 求解变量的建模意义（与`files_for_AI/first_stage_modeling.md`的映射）
本节将求解器输出直接关联到建模规范（任务A）中的数学公式，说明求解器估计的对象，以及下游分析中如何解读这些输出。

### 符号映射
- `p_est` → `p_{i,t}`
  - CSV列`p_est`存储每行（赛季、选手、周）对应的`p_{i,t}`估计值；
  - 建模规范中，`p_{i,t}`为选手`i`在第`t`周的未知粉丝投票占比，满足约束`p_{i,t} ≥ 0`且`∑_{i ∈ A_t} p_{i,t} = 1`。
- `xi` → `\xi_t`
  - CSV列`xi`存储每个（赛季、周）对应的松弛变量`\xi_t`；
  - `\xi_t`出现在淘汰一致性约束中，作为非负松弛项，使得被淘汰选手`e`和未被淘汰选手`i`满足`S_{e,t} ≤ S_{i,t} + \xi_t`。

### 变量与综合得分`S_{i,t}`的关联
- 求解器从面板数据计算评委占比`q^{J}_{i,t}`（代码中记为`qJ`），并构建淘汰约束中使用的综合得分：
  `S_{i,t} = alpha * q^{J}_{i,t} + (1 - alpha) * p_{i,t}`
- `p_est`对应建模规范中的`q^{V}_{i,t}`（粉丝投票占比）。下游仿真应使用相同`alpha`的`S_{i,t}`来重放百分比规则下的淘汰过程。

### 淘汰一致性约束（`xi`的使用方式）
- 对于淘汰集合为`E_t`（大小为`m`）的周，建模规范要求被淘汰选手需处于`S_{i,t}`倒数`m`名。我们将该硬性组合约束松弛为带`\xi_t`的线性不等式：
  对任意`e ∈ E_t`和任意`i ∈ A_t \ E_t`：
  `S_{e,t} ≤ S_{i,t} + \xi_t`

### 目标函数及解读
- 求解器最小化的目标函数：
  `∑_{t=2..T} ∑_{i ∈ A_t ∩ A_{t-1}} (p_{i,t} - p_{i,t-1})^2 + lambda * ∑_t xi_t^2`
- 时间平滑项：强制“粉丝偏好随时间平滑演变”的建模假设（对应规范A5.2）；
- `lambda*xi^2`项：强制“最小失真”原则（对应规范A5.3）：优先选择能解释淘汰结果且约束违反程度最小的解。

### 从输出推导的不确定性与诊断指标
1. `xi_t`作为诊断信号：
   - 若`xi_t ≈ 0`：该周淘汰结果可通过模型假设下的某个`p_{·,t}`很好地解释；
   - 若`xi_t`相对较大：记录的淘汰结果不一致/模糊，需核查该周是否存在特殊规则、评委豁免或数据问题。
2. 淘汰边际`Delta`（`\Delta_t`）：由输出计算得出（求解器不直接输出）：
   - 基于`p_est`计算`S_hat_{i,t}`；
   - `\Delta_t = min_{i ∈ A_t \ E_t} S_hat_{i,t} - max_{e ∈ E_t} S_hat_{e,t}`；
   - `\Delta_t`过小或为负，说明被淘汰选手并非明显处于`S_hat`倒数位置，对应更大的`xi`值。
3. 可行区间法（规范A7.1）：通过求解线性规划（LP）固定相同约束，逐一对`p_{i,t}`进行优化，计算`p^{min}_{i,t}`和`p^{max}_{i,t}`。这些区间量化了多解带来的不确定性。

### `p_est`和`xi`的下游使用建议（对应规范A、B节）
- 将`p_est`作为`q^{V}_{i,t}`，在仿真器中重放百分比规则下的淘汰过程（任务B），计算`E^{(P)}_t`和`R^{(P)}`；
- 重放排名规则下的淘汰过程时，用`p_est`计算`R^{V}_{i,t}`（粉丝排名），进而得到`R^{(R)}_{i,t} = R^{J}_{i,t} + R^{V}_{i,t}`；
- 利用`xi`标记分析中需特殊处理的周（如从部分指标中排除，或在论文/附录中标记为“有争议周”）；
- 基于`p_est`的赛季平均值，对比选手的整体粉丝支持度与最终排名（争议性分析），并计算仓库中定义的差异指标（周均排名 vs 最终排名差值）。

## 预期统计意义与注意事项
- `p_est`是在选定先验和约束下的估计值。由于真实投票不可观测，不同先验或`lambda/alpha`取值会得到不同的`p_est`；应将`p_est`视为基于模型的重构结果，而非真实值。
- `xi`反映百分比规则解释淘汰结果所需的松弛程度；`xi`值大的周需谨慎解读，并结合定性分析（如查看赛事集、特殊规则）。
- 若`lambda`过小或`alpha`设定错误，求解器的平滑目标可能导致过度平滑；实验中需包含敏感性校验（`alpha ∈ [0.4,0.6]`，按规范建议进行`lambda`网格搜索）。

## 预期输入（周度面板数据）
本模块要求周度面板CSV为权威、预清洗的输入，**不尝试**重新生成或清洗面板数据。规范化面板（由分类脚本生成）至少应包含以下列（默认名称）：

- `season`（整数/字符串）：赛季标识
- `celebrity_name`（字符串）：选手标识——若面板使用其他名称，可通过`--name-col`参数指定
- `week`（整数）：赛季内的周索引
- `total_judge_score`（数值型）：该选手-周的评委总分

支持的可选列（若存在，需通过CLI参数指定）：
- `active`（布尔型）：选手该周是否参赛并视为在役。若未提供，非空且大于0的`total_judge_score`行将被视为在役。
- `true_elim_flag`或其他淘汰标识（布尔型）：标记该周被淘汰选手的行。若缺失，求解器将不添加淘汰约束。

若列名不符，可使用CLI参数`--name-col`、`--score-col`、`--week-col`、`--active-col`和`--elim-col`进行映射。

## 输出文件
生成两个CSV文件（路径通过CLI指定）：

### 1) 粉丝投票占比文件：列说明（示例）
- `season` — 从面板数据复制
- `celebrity_name`（或自定义`name_col`） — 选手ID
- `week` — 周索引
- `p_est` — 该选手-周的粉丝投票占比估计值

### 2) Xi（松弛变量）文件：列说明
- `season`
- `week`
- `xi` — 非负松弛值，表示该周淘汰一致性约束的违反程度

## 命令行接口（CLI）使用示例
### 基础示例（使用分类脚本生成的规范化面板）：
```powershell
py "src\sim\model_main.py" ^
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" ^
  --out-p "src\sim\fan_shares.csv" ^
  --out-xi "src\sim\xi.csv" ^
  --alpha 0.5 --lambda_reg 1000 --verbose
```

### 面板列名自定义示例：
```powershell
py "src\sim\model_main.py" ^
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" ^
  --out-p "src\sim\fan_shares.csv" ^
  --out-xi "src\sim\xi.csv" ^
  --name-col "name" --score-col "total_score" --week-col "week_num" ^
  --active-col "active" --elim-col "true_elim_flag" ^
  --alpha 0.5 --lambda_reg 2000
```

### CLI参数汇总
- `--panel`（必填）：规范化周度面板CSV路径
- `--out-p`（必填）：粉丝占比CSV输出路径
- `--out-xi`（必填）：xi CSV输出路径
- `--alpha`（可选，默认=0.5）：综合得分`S`中评委权重（`alpha ∈ [0,1]`）
- `--lambda_reg`（可选，默认=1000）：目标函数中xi的正则化系数
- `--name-col`（默认=`celebrity_name`）
- `--score-col`（默认=`total_judge_score`）
- `--week-col`（默认=`week`）
- `--active-col`（可选）
- `--elim-col`（可选）
- `--hard-consistency`（可选）：强制淘汰一致性为硬约束（不允许xi）。用于需完全避免不一致的场景，可能导致优化不可行。
- `--verbose`（可选）：详细输出模式

## 关键发现总结（诊断与敏感性）
1. **可识别性**：仅靠周度面板+淘汰约束，往往无法唯一重构粉丝占比`p_{i,t}`（LP可行性校验显示，许多选手-周对的`p_min/p_max`区间范围较宽）。简言之：多数周的数据是欠定的。
2. **先验影响**：添加小幅周度正则项（方差/熵）会在信息不足时，显著将解偏向更均匀的分布。实验中，适度的熵正则化（如`entropy_reg ≈ 0.1`）已能产生近乎均匀的周度`p`向量；更大的值会快速饱和（因熵受`log(n)`限制）。
3. **松弛变量（xi）**：多次运行中求解器几乎无需松弛（`xi ≈ 1e-7`）——说明在模型假设下，淘汰结果与评委得分无显著矛盾；观察到的分布均匀性源于先验，而非通过xi强制可行。
4. **实用建议**：将重构的`p_est`视为基于模型的结果，而非真实值。若需在数据不足时选择保守、可辩护的默认值，建议使用小幅熵先验（`entropy_reg ∈ [0.01, 0.1]`），并在分析/附录中报告敏感性结果（如0.0、0.1或1.0）。
5. **提升鲁棒性的后续步骤**：
   (1) 执行有文档记录的网格搜索，并将结果表格纳入附录（已在`src/sim/grid_sensitivity_report.csv`完成）；
   (2) 利用LP区间+剖面分析标记弱识别的选手-周对，以便对结果进行标注或排除；
   (3) 生产环境中，建议将二次规划（QP）重构为矩阵形式，并使用专用QP求解器（cvxpy + OSQP）以提升稳定性/性能。

---

## 重要设计选择与内部实现（简述）
### 目标函数
对`p_{i,t}`的时间平滑性（同一选手连续周占比的平方差） + `lambda * ∑(xi_t^2)`。最小化时间变化量并惩罚松弛项的使用。

### 约束条件
1. 每周单纯形约束：`∑_{i ∈ A_t} p_{i,t} = 1`，`p_{i,t} ≥ 0`；
2. 对有淘汰信息的周，通过带`xi`松弛的线性不等式强制“淘汰一致性”：
   对任意被淘汰选手`e`和未被淘汰选手`i`，满足`S_{e,t} ≤ S_{i,t} + xi_t`，
   其中`S_{i,t} = alpha*qJ_{i,t} + (1-alpha)*p_{i,t}`，`qJ`为评委占比。

### 求解器
使用`scipy.optimize.minimize`调用SciPy SLSQP求解器。该方案依赖少，适用于当前问题规模。对于大型赛季或高频率生产使用，建议迁移至QP求解器（`cvxpy` + `OSQP`）以提升速度和数值稳定性。

## 故障排除与常见问题
### 求解器不收敛/返回不可行
- 检查面板数据是否规范，`elim_col`是否指向正确的布尔型淘汰行；
- 根据症状调整`--lambda_reg`：增大（提升松弛惩罚，改善数值稳定性）或减小（需更小xi时反向调整）；
- 使用`--verbose`打印每赛季变量数量，定位求解器处理失败的赛季。

### 大量xi值偏大
- 表明记录的淘汰结果与百分比规则+评委得分在合理`p_{i,t}`下不一致；核查面板行（特殊周、评委豁免事件或数据不一致）。

### `p_est`出现极端0/1值
- 检查面板的`active`标记和评委得分是否正确（某周评委总分为0的边缘选手可能导致求解器退化为均匀`qJ`）。

## 测试与快速合理性校验
1. **基础校验**：运行后，对每个（赛季、周）验证选手`p_est`之和在浮点误差范围内≈1.0（1e-9）。可编写简易脚本断言该条件并打印异常周。
2. **xi检查**：按xi降序排序，找出淘汰一致性违反最严重的周。
3. **可复现性**：相同初始值和环境下，SLSQP求解器是确定性的；实验中需记录`alpha`和`lambda_reg`。

## 集成说明
### 调用位置
在`p0_triage_build_weekly_panel.py`（生成`output/data_cleaned/intermediate_weekly_panel.csv`）之后调用本模块。典型流程：
1. 构建周度面板（分类步骤）→ `intermediate_weekly_panel.csv`
2. 运行本估计器 → `fan_shares.csv`（p_est） + `xi.csv`
3. 若需聚合列（赛季平均值、与最终排名对比），将`fan_shares.csv`合并到选手级预处理CSV
4. 运行需使用`p_{i,t}`的规则重放仿真（百分比规则 vs 排名规则）

### 建议文件名（项目规范）
- 面板数据：`output/data_cleaned/intermediate_weekly_panel.csv`
- 粉丝占比：`src/sim/fan_shares.csv`（或`output/data_cleaned/fan_shares.csv`）
- xi文件：`src/sim/xi.csv`

## 改进建议与后续优化
1. **替换求解器**：将SLSQP替换为QP求解器——将目标函数重构为二次型，约束条件重构为矩阵形式；使用`cvxpy`结合`OSQP`提升速度和数值稳定性。
2. **添加可行区间计算**：为选定选手/周添加计算`p_min/p_max`区间的轻量封装（对应建模说明A7.1）。该操作需求解LP，计算量较大。
3. **自动化单元测试**：基于小型测试面板验证每周占比和为1、已知测试赛季的正确性，以及缺失`elim_col`的处理逻辑。
4. **严格一致性约束**：若需完全避免不一致（xi > 0），使用`--hard-consistency`参数。求解器将强制执行无松弛的淘汰约束；若实例在硬约束下不可行，优化器可能失败，需用`--verbose`诊断失败赛季。

### 推荐诊断流程
1) 使用`--hard-consistency`检测直接不可行性：若运行无错误且xi输出为空，说明存在严格一致解；
2) 若不可行，关闭`--hard-consistency`但设置超大`--lambda_reg`（如1e6），强制xi尽可能小；检查`xi.csv`确定哪些周需要松弛及松弛程度；
3) 结合`xi`输出和`Delta_t`诊断指标，核查特定周的问题（数据问题或特殊规则）。

### 示例：严格约束（数据不兼容时可能失败）
```powershell
py "src\sim\model_main.py" ^
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" ^
  --out-p "src\sim\fan_shares_hard.csv" ^
  --out-xi "src\sim\xi_hard.csv" ^
  --hard-consistency --alpha 0.5
```

### 若上述命令失败（不可行），尝试超大lambda强制小幅xi：
```powershell
py "src\sim\model_main.py" ^
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" ^
  --out-p "src\sim\fan_shares_forced.csv" ^
  --out-xi "src\sim\xi_forced.csv" ^
  --lambda_reg 1000000 --alpha 0.5 --verbose
```

### 附加惩罚项说明
目标函数为可加形式：平滑项 + lambda * (xi²之和)。`--lambda_reg`是权衡“不一致性”与“平滑性”的比例参数——增大`--lambda_reg`会让优化器更严厉地惩罚不一致性。设置`--hard-consistency`相当于完全禁用xi（等效于lambda=+∞，但以硬约束方式实现）。

可选扩展：可添加`--fail-on-xi`参数，允许松弛但当任意xi超过阈值时返回非零退出码（可选生成报告），便于自动化流程（CI）强制一致性在可接受范围内。

## 联系方式与上下文
- 建模规范：`files_for_AI/first_stage_modeling.md`——本实现的数学原理和假设均源于此文档
- 代码位置：`src/sim/model_main.py`（求解器实现）

### 总结
1. 该文档是粉丝投票占比估计器的完整开发者指南，核心是通过带约束的平滑优化重构欠定的粉丝投票占比；
2. 关键输出为`p_est`（粉丝占比）和`xi`（淘汰约束松弛度），需结合建模规范解读，且`p_est`并非真实值而是模型重构结果；
3. 使用时需注意数据规范、参数敏感性（alpha/lambda），生产环境建议替换为更稳定的QP求解器。