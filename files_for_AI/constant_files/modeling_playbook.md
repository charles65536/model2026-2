# Modeling Playbook (Optimization / Strategy / Simulation Track)

**Purpose:** Ensure modeling outputs are implementable and judge-friendly: assumptions, variables, objective, algorithm, evaluation, robustness, and fallback.

---

## 0) Must-have deliverables (DoD)
1) Assumptions (≤5)  
2) Variable/symbol table  
3) Objective + constraints (aligned with KPIs)  
4) Policy/algorithm pseudocode + complexity notes  
5) Baselines  
6) Ablations (≥2)  
7) Robustness (3 stress tests)  
8) Failure modes + rollback  
9) Report-ready paragraph (150–220 words)

---

## 1) Assumption budget
Write as: “A1: … (impact: …)”. Test with stress tests where possible.

---

## 2) Variables & notation
Provide units, meaning, and keep symbols minimal and consistent.

---

## 3) Objective & constraints
Tie terms to KPIs. If multi-objective, specify weighting or Pareto evaluation.

---

## 4) Algorithm / policy logic
Implementation-first: step-by-step pseudocode + runtime considerations + parameter selection method.

---

## 5) Evaluation design
Must include baselines, KPI table (mean+tail+cost), one tail plot, one trade-off plot, and scenario/split details.

---

## 6) Robustness: standard stress tests
Demand intensity up/down; peak definition change; parameter perturbation; proxy noise/missingness.

---

## 7) Failure modes & rollback
Specify detection trigger + fallback policy.

---

## 8) “Modeling Ticket” template (copy/paste)

**Problem summary (≤5 lines):**  
**Chosen deliverable:** policy / optimization / hybrid  
**KPIs & constraints:**  
**Baselines:**  
**Available inputs:**  

**Return exactly:**
1) Assumptions (≤5)  
2) Variable/symbol table  
3) Objective + constraints  
4) Algorithm pseudocode + complexity  
5) Ablations (≥2)  
6) Robustness plan (3 stress tests)  
7) Failure modes + rollback  
8) Report-ready paragraph (150–220 words)
