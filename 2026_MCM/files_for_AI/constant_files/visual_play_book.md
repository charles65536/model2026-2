# Visual Playbook (MCM/ICM)

**Goal:** Make plots judge-friendly: consistent style, clear claims, and a tight evidence chain.

---

## 1. Figure hierarchy (L0–L3)

### L0 — Story overview (1–2 figures total)
**Purpose:** 30-second understanding: what we built, what improved.
- Pipeline/architecture diagram (inputs → modules → outputs; include fallback).
- One “headline results” figure comparing final vs baseline on key KPIs (tail + cost).

### L1 — Claim evidence (1–2 per claim)
**Purpose:** Turn each core claim into a visual proof.
Common claim→figure mapping:
- “Demand has modes” → time×floor heatmap; mode timeline.
- “Prediction is usable” → error distribution + peak-window MAE/P95.
- “Policy improves tail” → ECDF / P95–P99 bar + confidence bands.
- “Trade-off is acceptable” → Pareto frontier (service vs cost).

### L2 — Diagnostics / robustness (appendix-first)
**Purpose:** Show we didn’t hand-wave.
- Sensitivity curves (one parameter at a time)
- Ablation bars (remove module → metric change)
- Calibration checks / slice consistency
- Residual diagnostics (if applicable)

### L3 — Raw EDA / reference (appendix only)
**Purpose:** Evidence of diligence without narrative interruption.
- Histograms, full scatter matrices, large faceting, etc.

**Memory rule:** **L0 tells the story, L1 proves it, L2 shows we were careful, L3 is backup.**

---

## 2. The QDG workflow (Question-Driven Graphics)

**Never ask AI “what plots should we make?”**  
Instead write a **Figure Card** and force the plot to answer it.

### Figure Card template (must fill)
- **Q:** What question would a judge ask?
- **Claim:** What statement do we want to support?
- **Metric:** Definition + aggregation (e.g., P95 wait, P99 rate)
- **Slice:** Window definition (peak/weekday/etc.) and date range
- **Baseline:** What we compare against
- **Pass/Fail:** What visual pattern supports/refutes the claim
- **Columns:** Which data columns are used
- **Output name:** `fig_<short_name>`

---

## 3. Global style guide (use across all plots)

### 3.1 Semantic colors (max 6 meanings)
- **Baseline:** gray
- **Final method:** dark (e.g., deep blue/black)
- **Other candidates:** lighter same-hue variants
- **Threshold/risk line:** red (warning-only)
- **Modes:** 3–4 distinct colors (used only in mode plots)

**Rule:** Same object = same color across the paper.

### 3.2 Typography (suggested defaults)
- Title: 11
- Axis label: 9
- Tick labels: 9
- Caption text (in LaTeX): 9

### 3.3 Layout rules
- Prefer **single-column** figures.
- Side-by-side only for strict comparisons (weekday vs weekend).
- Legends must not cover data (use outside or empty corner).
- Avoid rotated axis labels; if labels don’t fit, change the chart type.

### 3.4 Annotation
- Each L0/L1 figure must annotate **1–2 key numbers** (e.g., P99 drop).
- Always label slices/windows on the plot or in caption.

---

## 4. Recommended “high-value” figure set (generic)

**Must-have (often 6–10 total):**
1. L0 pipeline diagram (system overview)
2. L0 headline KPI comparison (final vs baseline)
3. L1 tail improvement (ECDF or P95/P99 bars)
4. L1 trade-off (Pareto frontier)
5. L1 slice comparison (peak vs non-peak / weekday vs weekend)
6. L2 sensitivity (1 page)
7. L2 ablation (1 page)

**Appendix (as needed):**
- Data credibility plots
- Additional slices
- Diagnostics

---

## 5. Figure caption mini-template (≤2 lines)

**Slice + Metric + Baseline**:
> “Peak windows (top 20% demand), P95/P99 waiting time; baseline = last-stop policy.”

---

## 6. Minimal matplotlib expectations (for code outputs)

- Save both: PDF for LaTeX + PNG for quick view
- Deterministic ordering of categories/windows
- Print-friendly (line styles differ; not color-only)
- No clutter: remove unnecessary gridlines, keep margins reasonable
