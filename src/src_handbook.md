# src_handbook（源码目录速查）

> 说明：本文件仅供队内自查，**中文即可**。  
> 约定：项目产物目录为 `output/figure/` 与 `output/table/`（**不使用复数**）。  
> - 图：`output/figure/fig_<short>.pdf`（可选同时生成 png）  
> - 表：`output/table/tab_<short>.tex`（LaTeX 表格）

---

## 1) 总览表（框架）

| 子目录 / 模块 | 主要用途（做什么） | 入口脚本（可直接运行） | 典型输入（数据/参数） | 典型输出（文件/对象） | 与产物目录关系 | 依赖/前置 | 维护者 | 备注 |
|---|---|---|---|---|---|---|---|---|
| `src/viz/` | 绘图：把主张变成证据图（L0/L1/L2/L3） | `src/viz/fig_*.py` | 评估结果表 / 处理后数据 / 配色与样式参数 | `output/figure/fig_*.pdf`（+png） | **写入** `output/figure/` | 需要 KPI 口径与切片定义 |  | 每图一脚本，标题用结论句 |
| `src/eval/` | 评估与出表：算 KPI、做对照、消融、敏感性 | `src/eval/tab_*.py` / `src/eval/run_eval.py` | 模拟/策略输出、baseline结果、切片规则 | `output/table/tab_*.tex`，以及中间csv | **写入** `output/table/` | 需要 kpi_registry 定义 |  | 表格建议 booktabs |
| `src/sim/` | 仿真：环境/事件生成/策略执行循环 | `src/sim/run_sim.py` | 场景配置、随机种子、策略参数 | 轨迹/日志/汇总指标（供 eval 用） | 间接产物：eval/viz 使用其输出 | 需要 config / 数据版本 |  | 明确随机种子与场景定义 |
| `src/model/` | 策略/算法：启发式、优化、调参逻辑 | `src/model/run_policy.py`（可选） | 状态/约束/参数 | 动作序列/决策/策略对象 | 通常不直接写 output | 依赖 sim 接口 |  | 保持“可实现伪代码”一致 |
| `src/data/`（可选） | 数据读取/清洗/特征生成（若有） | `src/data/make_processed.py` | raw 数据 + 清洗规则 | processed 数据（供 sim/eval/viz） | 通常写 `data/processed/...` | 需要字段字典 |  | 清洗规则要可追溯 |
| `src/utils/`（可选） | 通用工具：路径、日志、统计、绘图样式 | （被 import） | — | — | — | — |  | 避免散落重复代码 |
| `src/config/`（可选） | 配置：切片定义、参数范围、路径常量 | — | — | — | — | — |  | 用于统一口径与复现 |

---

## 2) 入口脚本“可运行”定义（建议写死）

- 任何写入 `output/figure/` 的脚本应满足：  
  `python src/viz/fig_xxx.py` 能直接生成对应 `output/figure/fig_xxx.pdf`（可选 png）。

- 任何写入 `output/table/` 的脚本应满足：  
  `python src/eval/tab_xxx.py` 能直接生成对应 `output/table/tab_xxx.tex`。

---

## 3) 命名与路径约定（避免后期引用炸裂）

| 类型 | 命名规则 | 例子 |
|---|---|---|
| Figure 文件 | `output/figure/fig_<short>.pdf` | `output/figure/fig_pareto.pdf` |
| Table 文件 | `output/table/tab_<short>.tex` | `output/table/tab_kpi_summary.tex` |
| Figure 入口脚本 | `src/viz/fig_<short>.py` | `src/viz/fig_pareto.py` |
| Table 入口脚本 | `src/eval/tab_<short>.py` | `src/eval/tab_kpi_summary.py` |

---

## 4) 你们要填的最少信息（建议）

每新增一个子模块/入口脚本，至少补全总览表里的：
- 主要用途
- 入口脚本
- 典型输入/输出
- 与产物目录关系（会不会写入 output/figure 或 output/table）
