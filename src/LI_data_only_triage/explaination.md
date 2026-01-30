
These files in LI_data_only_triage are only used to get a first stage understanding of the data, which was far from a mature project. You need to continue your data analysis work!!!
===

P0 Triage: Build weekly panel (season-week-celebrity) from official DWTS dataset,
and compute BL-0 baseline elimination predictions + consistency KPIs.

* Authoritative definitions:
  - dynamic_files/data_agent_triage_ticket.md
  - dynamic_files/kpi_registry.md

* Outputs (relative to --outdir):
  - table/intermediate_weekly_panel.csv
  - table/intermediate_baseline_preds.csv
  - table/tab_baseline_consistency.tex
  - figure/fig_fliprate_by_season.pdf

---

## 1) 产物验收结论：基本没问题（DoD 达标）

### ✅ 结构与口径一致性检查（关键项都过了）

* 周面板粒度正确：`(season, week, celebrity)`；包含 `judge1..4_score / total_judge_score / judge_rank / judge_percent / active / true_elim_flag / exit_type / exit_week / data_anomaly_zero_score` 等。
* `preds` 与 `panel` 一致：`preds.n_active` 与面板中同 `(season,week)` 的 active 数量 **完全一致**；`true_k` 与 active 集合内 `true_elim_flag` 求和 **完全一致**。
* eligible 周数：`eligible=True` 共 **264** 周；与你们之前表述一致。
* era 切片：`percent-era` 仅 seasons 3–27，`rank-era` 仅 seasons 1–2 与 28+，**无穿帮**。
* 结构性 all-NaN 周：本次上传的面板里 **all-judge-NaN 行为 0**（说明你们已经做了 drop 或未纳入）。✅

**CN（易懂可执行）**

1. 我们已将原始 `weekX_judgeY_score` 从 wide 展开为 long，得到 season–week–celebrity 周面板，并生成 `active / exit_week / exit_type / true_elim_flag` 等标签，作为后续模型（QP 反推 fan votes + 规则回放仿真）的统一输入。
2. P0 baseline（BL-0）已可复现：以 judge-only/ uniform-fan-proxy 产生每周淘汰预测，并输出逐周对照表与汇总 LaTeX 表。
3. 分母规则已显式处理：无淘汰周从一致性 KPI 分母剔除；多淘汰周用 bottom-k set-match。
4. 数据编码风险：淘汰后周分数常被编码为 0（我们标记为 inactive，不参与排名/百分比）；另存在极少数“淘汰当周总分=0”的边界异常（目前仅 1 例），后续将作为敏感性测试点处理。

**EN (report-ready, academic tone)**

1. We reshaped the official weekly judge-score columns into a season–week–contestant panel and constructed deterministic labels for the active set and exit timing (eliminated/withdrew/finished) to serve as the canonical input for downstream modeling.
2. A fully reproducible BL-0 baseline is implemented, producing week-level elimination predictions and audit-friendly intermediate outputs (panel + predictions + LaTeX summary table).
3. Weeks with no elimination are excluded from the consistency denominator, while multi-elimination weeks are evaluated via bottom-k set matching to avoid overstating agreement.
4. The dataset encodes post-exit weeks as zeros and may contain rare edge cases where elimination-week scores are recorded as zeros; these are documented as data-credibility caveats and will be stress-tested in the sensitivity stage.

---