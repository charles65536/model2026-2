# Data Playbook (Optimization / Policy / Simulation Track)

**Purpose:** Turn raw data into *model-ready* inputs and *judge-facing* evidence without getting lost in aimless EDA.

This playbook is designed for MCM/ICM-style work where the end product is typically a **policy/strategy** validated by **simulation** and compared against **baselines**.

---

## 0) Data work principles (non-negotiables)

1. **KPI-first, Slice-first.** Data work serves evaluation. Define KPIs and slices/windows before heavy cleaning.
2. **Baseline must run early.** If you can’t compute KPIs for a baseline, the rest is premature.
3. **Reproducibility > perfection.** Prefer deterministic, explainable rules over fancy imputation.
4. **Keep-but-explain beats delete.** Many “weird” tails are the story (and what judges care about).
5. **Always report caveats.** If a field is missing/zero-inflated/unclear units, write it down and stress-test.

---

## 1) Two-mode workflow (Triage → Deep)

### Mode A: TRIAGE (first 2–4 hours)
**Goal:** Make KPIs computable and produce a first baseline comparison.

**Outputs (must deliver):**
- P0 field list (≤8)
- 5 hard cleaning rules (IF-THEN)
- 3 keep-but-explain notes
- Minimal KPI computation pseudocode
- 1 baseline KPI table *or* 1 L1-ready plot

**Do not:** produce 20 plots, do complex missing-value modeling, or optimize models.

### Mode B: DEEP (after model/policy direction is set)
**Goal:** Support the chosen policy with credibility: sensitivity, diagnostics, robustness.

**Outputs (must deliver):**
- Top-3 data risks (ranked)
- 1 executable detection test per risk
- mitigation + side effects
- 3 stress tests
- L2 appendix plot/table candidates

---

## 2) KPI & slice design (what Data must lock down)

For each KPI, you must specify:
- **Definition** (words or formula)
- **Direction** (higher/lower better)
- **Aggregation** (mean/median/P95/P99/rate)
- **Slice/window** (time bucket, peak definition, segments)
- **Baseline(s)**

**Recommended for optimization/policy tasks:**
- Service quality: mean + tail (P95/P99) + violation rate
- Cost: energy/effort/distance/number of actions
- Stability: performance variance across slices; robustness under stress tests
- Fairness (optional): gap/variance across groups

**Slices that judges understand:**
- Peak vs off-peak (define peak operationally)
- Weekday vs weekend
- Geographic/segment groups (if relevant)
- High-demand quantiles (top 20% demand windows)

---

## 3) Cleaning rules: the standard taxonomy

### 3.1 Hard filters (drop/repair rules)
Use for broken records that break KPI computation.
Write rules as `IF ... THEN drop/repair ...` and keep them in a short list.

### 3.2 Keep-but-explain
Use when values look odd but are plausible and informative.
Typical cases: heavy tails, zero inflation, censoring/timeouts.

**Rule:** keep unless you can defend deletion *and* show deletion does not change ranking.

### 3.3 Derived features
Features must be reproducible and documented:
- Hour/weekday/weekend
- Rolling demand proxy
- Peak indicator (definition locked in KPI registry)

---

## 4) Credibility risks: what to watch for (and how to phrase)

- **Zero-inflation:** rely on relative comparisons + stress tests; report caveat.
- **Heavy tails:** focus on P95/P99/ECDF; keep tail evidence.
- **Leakage:** enforce time-respecting splits; document.
- **Unit ambiguity:** use ratios/rank stability; avoid absolute claims.

---

## 5) Standard deliverables & interfaces (files)

- Processed data: `data/processed/vX/` + short README
- Tables: `tables/tab_<name>.tex`
- Figures: `figures/fig_<name>.pdf` (+ png)
- Each asset must include script path + data version tag.

---

## 6) “Data Ticket” template (copy/paste)

**Goal:**  
**KPIs (with aggregation):**  
**Slices/windows (definitions):**  
**Baselines:**  
**Columns available:**  
**Outputs needed (table/plot):**  

**Return exactly:**
1) P0 fields (≤8)  
2) 5 hard rules (IF-THEN)  
3) 3 keep-but-explain notes  
4) KPI pseudocode (≤25 lines)  
5) 4 report-ready sentences (no fabricated numbers)
