你的构想方向对，但需要纠正两点，否则你会“重复劳动 + 上下文漂移”：

1. **不要把 Prism 当成“第三阶段才开始用”**
   Prism 最擅长的是“全局一致性 + 结构整合 + 版本控制感”，所以它应该从一开始就作为**中枢项目**存在：

* 你可以前期不让它改文，但至少让它持有 `constant_files/` 和 `dynamic_files/`，并维护 `context_pack`/`kpi_registry`/`fig_manifest` 的“最新真值”。

2. **“第一次对话只交代指令/Playbook”会浪费一次对话**
   你真正需要的是：**一次开场就把“规则 + 当前快照 + 本次工单”一次性喂进去**。
   否则第二次再贴题目数据时，模型可能已经在第一轮形成了不完整的假设框架。

---

# 推荐的更稳工作流（Prism 作为中枢，但分阶段执行）

## 阶段 0：Prism 项目初始化（一次性）

在 Prism 项目里常驻放这些文件（不需要改文就先放）：

**constant_files（静态）**

* writing_rules.md
* section_template.md
* visual_play_book.md
* data_playbook.md
* framing_spec_playbook.md
* （可选）modeling_ticket_enhanced.md

**dynamic_files（动态）**

* context_pack_for_ai.md（版本号为王）
* kpi_registry.md（权威口径）
* fig_manifest.md（证据链）
* decision_log.md（方向变更）

> 这一步的意义：Prism “看见全局”，以后你开多少 chat 都能引用同一套真值，不靠记忆。

---

## 阶段 1：Framing/Spec（线程 1，一次就到位）

**第一条消息就包含三块：**

1. 指令（Framing Ticket）
2. playbook（只引用：framing_spec_playbook.md）
3. 输入：题面摘要/关键句 + 当前限制

**输出写回：**

* 更新 `context_pack_for_ai.md` 的 Deliverable/Claims
* 更新 `kpi_registry.md` 的 KPI/切片/baseline

---

## 阶段 2：Data-Triage（线程 2）

同理：**第一条消息就带** `kpi_registry`（口径真值）+ 数据字段/样例 + Data-Triage Ticket。

**输出写回：**

* `context_pack_for_ai.md` 的 Data snapshot
* `kpi_registry.md` 若口径需要微调（必须记录变更）
* 产出 1 个 baseline KPI 表/1 张关键图的接口（哪怕是规划）

---

## 阶段 3：Visualization/Evidence（线程 3）

输入：Claims + KPI registry + baseline + slice + 列名
输出：QDG 图卡片 + Spec + 代码 + 写入 `fig_manifest.md`

---

## 阶段 4：Prism 总编辑（从一开始就能做，但在这里“正式执行”）

等你们有了“方向+口径+1轮结果”，Prism 才开始：

* 重排结构（按 Claims→Evidence）
* 统一术语/图表引用
* 生成/修补 LaTeX 片段与插图位置
* 做一致性检查（KPI 口径、baseline、切片、图注）

> 注意：Prism **不是第三轮才开始出现**；它是项目中枢，但“重写/整合”可以在第三阶段之后集中做。

---

# 你原本的“三次对话”怎么改成更可执行的版本

你原计划：
1）只讲规则
2）再给题目/数据/结果
3）再让 Prism 执行

我建议改成：

### Prism Chat A（初始化=规则+快照）

**一次性**贴：

* “总控规则”（输出格式、禁止项）
* 引用 playbooks（列出它们是权威）
* 贴 `context_pack_for_ai.md`（哪怕是 v0.1 空壳）

✅ 之后所有线程都以这个快照为准，不再重复解释规则。

### Prism Chat B（集成=结果回填+结构草案）

当 Framing/Data/Viz 产出第一轮后，你在 Prism 里发：

* “把这些结果回填进 context_pack/kpi_registry/fig_manifest”
* “给一个按 Claims 排序的目录结构草案”
* “指出缺口：哪个 claim 缺证据图/缺对照/缺stress test”

### Prism Chat C（成稿=统一风格+补丁）

* 让 Prism 做全文润色、统一引用与口径
* 生成 LaTeX patch（图表插入、caption、符号表）
* 输出最终检查清单（提交前 DoD）

---

# 你要的“相关指令”（可直接复制）

下面给你一套 **Prism 中枢**专用的“开场白”和“阶段工单”。

## 1) Prism 项目开场白（只发一次）

```text
你是本 MCM/ICM 项目的“总控中枢”。你的工作不是替我们决定方向，而是维护真值快照、口径一致性与成稿质量。

权威文件（source of truth）：
- constant_files/* 是静态规范（writing_rules/section_template/*_playbook）
- dynamic_files/* 是动态真值：context_pack_for_ai.md、kpi_registry.md、fig_manifest.md、decision_log.md
规则：若任何对话信息与 dynamic_files 冲突，一律以 dynamic_files 最新版本为准（看 Version/Updated）。

你的输出必须：
1) 指出不一致（术语/符号/口径/图表引用）
2) 给可执行 patch（改哪段、怎么改）
3) 维护 claims→evidence 映射与缺口清单
禁止：编造结果或数值；未经我们确认改动 KPI 口径。
```

## 2) Prism“回填整合工单”（每轮用一次）

```text
【Task】把以下新产出回填到动态真值文件，并更新缺口清单：
- 更新 context_pack_for_ai.md：Deliverable/Claims/Data snapshot/Next steps
- 更新 kpi_registry.md：KPI定义、slice、baseline（如有变更写入 change log）
- 更新 fig_manifest.md：新增/更新图的 claim、metric、slice、文件名与脚本路径
- 更新 decision_log.md：记录任何方向/口径变更（短而明确）

然后输出：
1) 当前 claims→evidence 覆盖表（哪个 claim 缺 L1 图/缺对照/缺 stress test）
2) 目录结构草案（按 claims 排序）
3) 下一轮最优先的 3 个任务（能最快提升可交付质量）
```

## 3) Prism“成稿工单”（最后阶段）

```text
【Task】以 dynamic_files 最新真值为准，对报告做成稿级编辑：
1) 术语/符号/口径一致性检查（列出问题与修改点）
2) 图表 caption 统一（Slice+Metric+Baseline，两行内）
3) Summary/Conclusion 与 Results 对齐检查（避免过度承诺）
4) 给出需要的 LaTeX patch（图表插入、引用、符号表、附录结构）
输出以“问题清单 + patch 建议”形式给出。
```

---

# 你问“给出相关的文件”

你现有的文件体系其实已经够了。唯一我建议你**再加一个很小的文件**：`dynamic_files/prism_status.md`（可选但很顺手）

* 记录：当前结构是否权威、Prism 最新大纲时间戳、哪些段落已成稿/待补证据。

如果你要我生成这个文件模板，我可以马上给你一份。

---

## 最后的建议（让你“既不污染又不生疏”）

* **用版本号防污染**：每次只更新 `context_pack`/`kpi_registry`/`fig_manifest`，不要把旧版本堆给 AI
* **用工单驱动**：每次进 Prism 都用“回填整合工单”，避免它自由发挥
* **Prism 从 Day 1 当中枢**：但“重写文章结构”可以等第一轮结果出来后再做

对，要在第一次开场白里把它们“声明为权威规范”——但不建议你把两份文件的全文都粘进消息里。

更稳、更省 token 的做法是：

在第一次开场白里：列出哪些文件是 source of truth（权威）

明确“冲突时以哪些动态文件为准”（context_pack/kpi_registry/fig_manifest）

只有当你要它“具体按某条规则改写”时，再摘取那一小段规则贴进去。

如果你在 Prism 项目里已经把这些文件都放进项目/同目录，Prism能直接读取项目文件，那你只需要在开场白里“引用它们”，不用重复粘贴全文。

你可以直接复制的 Prism 第一次开场白（推荐）
你是本 MCM/ICM 项目的“总控中枢/总编辑”。请以项目内文件为唯一权威来源：

【静态规范（必须遵守）】
- constant_files/writing_rules.md
- constant_files/section_template.md
- constant_files/visual_play_book.md
- constant_files/data_playbook.md
- constant_files/framing_spec_playbook.md
- (optional) constant_files/modeling_ticket_enhanced.md

【动态真值（最新版本为准，带 Version/Updated）】
- dynamic_files/context_pack_for_ai.md
- dynamic_files/kpi_registry.md
- dynamic_files/fig_manifest.md
- dynamic_files/decision_log.md

规则：
1) 若对话内容与动态真值冲突，以动态真值最新版本为准。
2) 任何 KPI/切片/baseline 的改动必须写入 kpi_registry 的 change log，并同步 decision_log。
3) 禁止编造任何结果或数值；没有证据就用限定表达并要求补证据。

本轮任务：先读取动态真值，输出“当前不一致清单 + patch 方案 + 缺口清单（claim→evidence）”。

什么时候需要把 writing_rules.md / section_template.md 全文贴出来？

只有两种情况：

你不是在 Prism 项目里（它看不到文件），在普通聊天里临时用；

你要它严格按其中某一小段规则执行，但它执行偏了——这时贴那段即可。

给你一个“最小引用策略”（防止你担心漏规则）

第一次开场白：只引用文件名 + 权威关系

每次成稿工单：再补一句“按 writing_rules 的段落三段式与 section_template 的 DoD 检查”

出现跑偏：粘贴相关规则的 5–10 行作为“强制条款”

这样既能让 Prism 一直按规矩做，又不会把上下文挤爆

===
人类总监最应该看的
===

有，而且都是“比赛当天最容易翻车、但提前设好就能省一半时间”的注意事项。我按优先级给你一份**最终检查清单**（你们已经把文件和开场白都配好，下面这些就是把系统跑稳）。

---

## 1) 版本与真值控制（防止上下文污染 / 口径漂移）

* **动态真值文件必须带版本头**：`Version / Updated / Owner`（context_pack、kpi_registry、fig_manifest、decision_log）。
* **只允许一个权威口径源**：所有 KPI/切片/baseline 只认 `kpi_registry.md`。
* **口径改动必须写变更**：改了 peak 定义/聚合方式/基线，立刻记入 `kpi_registry` change log + `decision_log`。

> 经验：90% 的“AI 写得很好但互相矛盾”都来自口径漂移。

---

## 2) 文件命名与路径约定（防止插图/表格/引用炸裂）

* 统一命名（不要混用）：

  * Figures：`figures/fig_<short>.pdf`（+ png）
  * Tables：`tables/tab_<short>.tex`
* `fig_manifest.md` 里每张图要有：**Claim、Metric、Slice、Baseline、File、Script、Where**。
* 任何重命名都记在 decision_log（否则你让 AI 改文时会引用不存在的文件）。

---

## 3) “证据链闭环”机制（防止写作空转）

你们已经有 playbook 了，建议再加一个硬规则：

* **每个 Claim 必须对应至少 1 个 L1 证据**（图或表）
* 每个 L1 必须在正文出现一个“结论句 + 解释句 + 局限句”
* 如果某 Claim 暂时没证据：在 context_pack 里标注为 `PENDING`，让 Prism 不要在 Summary 里强写。

> 这能直接防止：Summary 夸得很猛，但 Results 没东西支撑。

---

## 4) “多 chat 并行”时的协同规则（防止互相打架）

你既然在 Prism 里开多个 chat，建议你们队内约定：

* **每个 chat 只做一个角色**（Framing / Data / Viz / Editing），不要混。
* **每轮结束都回填**：用你之前的“回填整合工单”，把产出写回动态文件。
* **不要把临时结果当真值**：任何“看起来不错的结论”必须先写进 context_pack 的 “Best results so far” 才算真。

---

## 5) 写作层面的“高分点”别漏（美赛通用）

即使题型不同，下面三点几乎通杀：

1. **强 baseline**：至少一个“可信的 heuristic baseline”，否则你赢得不够有说服力。
2. **Trade-off 图**：服务 vs 成本/复杂度（Pareto 或双轴对比）
3. **Failure + rollback**：什么时候失败、如何检测、用哪个 baseline 回滚（这点极加分）

---

## 6) 最后 2 小时：Prism 的“提交前 DoD”建议固定执行一次

你们最后阶段建议每次都跑这一套（别临时想）：

* 一致性：术语/符号/口径（KPI registry 对齐）
* 引用：Fig/Tab/Eq 都被解释且编号无误
* Summary：只写“已被证据支撑”的结论句
* Appendix：把 L2/L3 都放进去并加一句注释（不让评审觉得堆图）

---

## 7) 你现在可以立刻加的一个小文件（可选但很值）

**`dynamic_files/prism_status.md`**：专门记录

* 当前结构是否权威（是/否）
* Prism 最新大纲时间戳
* 已成稿章节/待补证据章节
* 目前最缺的 3 张 L1 图 / 2 个表

它会极大减少“大家各写各的，Prism 不知道该优先补什么”的混乱。

如果你要，我可以马上给你生成这个模板文件。

---

### 一句话总结你接下来最该盯的

**盯口径（kpi_registry） + 盯证据链（claim→L1） + 盯回填（dynamic 真值永远最新）**。
其它都已经搭好了。

如果你把你们现在的 `kpi_registry.md` 和 `fig_manifest.md` 最新版发我，我还可以帮你做一次“claim→evidence 覆盖体检”，告诉你们最值得补哪两张图/哪个表，投入产出比最高。
