Context Pack for AI 
---

**version:** v0.1
**updated:** 2026.1.30_8:00
**owner:** Jincan LI
**Rule:** If any earlier info conflicts, **this file wins**.

我们现在进行美赛论文的写作，这个文件用于作为AI的语境文件，用以兼做团队日志与AI阅读材料
# 1 问题分解与概述 (Problem Decomposition)


# 2 本次对话目标交付成果

# 3 已完成结论与进程快照

# 4 关键指标 (KPI)

## 4.1 KPIs / slices / baselines (authoritative) (待填写)
| KPI name | Direction | Aggregation | Slice/Window definition | Baseline(s) |
|---|---|---|---|---|


# 5 数据处理：

## 5.1 Data snapshot (only what affects conclusions)（待填写）

- Data version/tag: ______
- Key columns: ______
- Cleaning rules (≤5):
  1) ...
  2) ...
- Known caveats (≤3):
  - ...

# 6 关键模型 

# 7 Notation Chart(记号说明)

# 8 Work-in-progress outputs (pre-contest can be empty)
- Expected figure set (L0/L1/L2): see `fig_manifest.md`

# 9 风险与回滚

暂无

# 10 鲁棒性清单

暂无

# 11 文献清单

暂无

# 12 重大决策记录

暂无

# 附录 1 已有文件

## 1.1 文件结构

```
2026_MCM\
   snapshots\
    chapters\(这个文件夹用以装我们文章各个章节的内容以避免主内容的拥挤)
        0_summarysheet.tex
        1_introduction.tex
        2_problem_decomposition_and_analysis.tex
        3_data_processing_and analysis.tex
        4_modeling.tex
        5_results.tex
        6_memo.tex
        7_conclusion
        myref.bib
        report_on_use_of_ai.tex
    files_for_ai\                           (与AI的交接文档)
        group_discussion_files\             (这是对内交流文档)
            kaichangbai.md                  (这是使用AI时的开场白)
            log_A_d_t.md                    (这是队友之间交付的文档)
            prism_operation_hand_book.md    (prism的操作手册)
        dynamic_files\
            fig_tabel_manifest.md           (图、表的清单，用于与AI对其颗粒度)
            desicion_log.md                 (重大方向变化，由prism和Jincan LI共同完成)
            context_packed_for_ai.md        (与AI对其颗粒度的核心文件)
            kpi_registery                   (记录核心KPI)
        constans_files\
            framing_spec_playbook.md        (playbook for Framing/spec GPT)
            data_playbook.md                (playbook for data GPT & Visualization/Evidence GPT)
            modeling_playbook.md            (playbook for modeling GPT)
            modeling_ticket_enhanced.md     (interaction playbook for modeling GPT)
            writing_rules.md                (playbook for prism & writer)
            writing_section_template.md     (playbook for prism & writer)
            visual_play_book.md             (playbook for data GPT & Visualization/Evidence GPT)
    src\                                    (核心代码)        
        eval\                               (评估)
        model\                              (模型)
        sim\                                (仿真)
        viz\                                (可视化)
        src_handbook.md                     
    outputs\
        data\
        fig\
        tab\
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
Summary sheet 
1 Introduction 
2 Problem Decomposition and Analysis
    2.1 Objective and decision scope
    2.2 Data-driven closed loop: three tasks
    2.3 Key modeling assumptions (made explicit)
    2.4 Outputs and validation plan
    2.5 Two-route design: performance vs. interpretability
3 Data Processing and Analysis
    3.1 Data Cleaning Principles and Validation
        3.1.1 Cleaning Principles
        3.1.2 Data Cleaning Operations
        3.1.3 Data Cleaning outcomes and Validation
    3.2 Data Visualization
    3.3 Empirical Findings from EDA
    3.4 Feature Engineering
    3.5 Synthesis of Findings
4 Modeling
    4.1 Overview and Modeling Philosophy
    4.2 Model 1: Short-Term Passenger Arrival Forecasting (Task 1)
        4.2.1 Target and Time Discretization
        4.2.2 Feature Engineering
        4.2.3 Model Choice and Validation Protocol
        4.2.4 Output to Downstream Control
        4.3.1 Mode Features with Operational Meaning
        4.3.2 Unsupervised Clustering and Interpretability
        4.3.3 Cluster-to-Mode Naming
        4.3.4 Online Mode Classification
    4.4 Model 3: Mode-Aware Dynamic Parking via Weighted 𝑘-Median (Task 3)
        4.4.1 Mode-Conditioned Floor Demand Distribution
        4.4.2 Optimization Formulation (Weighted 1D 𝑘-Median)
        4.4.3 Solution and Assignment
        4.4.4 Execution Policy
    4.5 Interpretable Baseline and Fallback Policy (Route B)
        4.5.1 Task 1: time-of-day baseline + regime 𝐴𝑅(1)
        4.5.2 Task 2: Rule-based real-time traffic state classification Model.
        4.5.3 Task 3: zone-based state-aware parking rule
        4.5.4 Deployment Fallback: When to Switch from Route A to Route B
    4.6 Simulation-Based Evaluation (Baselines and Metrics) 
        4.6.1 Baselines
        4.6.2 Metrics
        4.6.3 Discussion
    4.7 Robustness and Sensitivity (Brief) 
5 Result Analysis and Robustness Testing 
    5.1 Performance Evaluation 
    5.2 Stress Tests and Robustness
    5.3 Robustness and Sensitivity
6 Memo to Management
7 Conclusion
A Appendix: Data, Algorithms, and Reproducibility
    A.1 Appendix A. Data Dictionary and Preprocessing Details
    A.2 Appendix B. Feature Engineering (Task 1 & Task 2)
    A.3 Appendix C. Mode Clustering Configuration and Naming
    A.4 Appendix D. Weighted 1D 𝑘-Median Solution Sketch
    A.5 Appendix E. Simulation Assumptions and Parameters
    A.6 Appendix F. Additional Results (Stress Tests)
    A.7 Appendix G. Reproducibility Checklist
    A.8 Appendix H. Interpretable Baseline and Fallback Policy (Route B)
    A.9 Validation 21
B Complete Files for Problem B 21
```