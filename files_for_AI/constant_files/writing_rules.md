# MCM/ICM Writing Rules (Team Standard)

**Purpose:** Keep the report *judge-friendly*: clear claims, evidence-first results, consistent terminology, and reproducible figures/tables.

---

## 0. Non-negotiables

- **No fabricated numbers.** If a value is unknown, write qualitative trends or clearly mark an assumption.
- **One paragraph = one point.** Each paragraph must contain:
  - **Claim (what we found / propose)**
  - **Evidence (metric, comparison, figure/table reference)**
  - **Qualifier (assumptions / limits / scope)**
- **Consistency beats novelty.** Same metric names, same baselines, same time windows across the paper.
- **Reproducibility:** Every figure/table must be traceable to a script and a data version (even if just a short note).

---

## 1. Report structure (recommended)

1. **Summary (≈1 page max)**
   - What problem, what we did, key results (top 3), why credible, what to deploy.
2. **Introduction / Problem Restatement**
   - Define objective + constraints; define KPIs early.
3. **Data & Preprocessing**
   - What data, how cleaned, known caveats; define slices/windows.
4. **Model/Method**
   - Assumptions → variables → objective → algorithm (pseudocode) → complexity.
5. **Evaluation**
   - Baselines, metrics, experimental design, sensitivity/robustness.
6. **Results & Discussion**
   - Evidence-driven: claim → figure/table → interpretation → trade-offs.
7. **Conclusion & Recommendations**
   - Bullet outcomes + deployment notes + rollback logic.
8. **Appendix**
   - Diagnostics, extra plots (L2/L3), derivations, extended tables.

---

## 2. Language rules (MCM tone)

### 2.1 Clarity and scope
- Prefer **short sentences** and **active voice**.
- Use **scope qualifiers**: “in peak windows”, “for weekday data”, “under the assumed demand proxy”.
- Avoid absolute claims unless proven: use **may / likely / suggests / indicates** when appropriate.

### 2.2 What judges like to see
- A **tight narrative**: a small number of claims, each backed by evidence.
- **Trade-offs**: show improvements and costs.
- **Robustness**: stress tests, sensitivity, and failure modes + fallback.

---

## 3. Metrics & baselines (must be explicit)

For every metric, specify:
- Definition (formula or words)
- Direction (lower/higher is better)
- Aggregation (mean / median / P95 / P99 / rate)
- Slice/window (time range, peak definition, weekday/weekend)
- Baseline(s)

**Rule:** Put metric definitions *once* in a “Metrics” subsubsection, then only reference names afterward.

---

## 4. Figure/table writing

### 4.1 Titles and captions
- **Figure title must be a conclusion sentence**, not a noun phrase.
  - Bad: “Waiting Time Comparison”
  - Good: “Our policy reduces P95 waiting time during peak periods”
- Caption (≤2 lines) must include:
  - Slice/window + metric definition shorthand + baseline name(s)

### 4.2 Referencing
- Every figure/table must be referenced in the main text and explained:
  - “Fig. 3 shows …; the tail improvement is …; cost increases …”

### 4.3 Placement
- Put a figure *right after* the paragraph that introduces the claim it supports.

---

## 5. Math & notation

- Create a **symbol table** for core variables.
- Keep notation minimal; reuse symbols consistently.
- Any optimization model must specify:
  - Decision variables
  - Objective
  - Constraints
  - Solution method (exact/heuristic)
  - Complexity or runtime notes

---

## 6. Assumptions & limitations

### 6.1 Assumption budget (≤5 in main text)
- Each assumption must be:
  - **Necessary**
  - **Plausible**
  - **Tested or stress-tested** if possible

### 6.2 Limitation phrasing
- Prefer **bounded statements**:
  - “Our evaluation relies on proxy X; if X is biased, absolute values may shift, but relative rankings were stable in stress tests.”

---

## 7. Reproducibility & file interface (lightweight)

- All generated assets should follow:
  - Figures: `figures/fig_<short_name>.pdf` (+ `.png` if needed)
  - Tables: `tables/tab_<short_name>.tex` (booktabs)
- For each figure/table, maintain:
  - Script path (e.g., `src/viz/fig_tail_ecdf.py`)
  - Data version tag (e.g., `data/processed/v3/`)

---

## 8. AI usage transparency (do not overpromise)
- Describe where AI helped (editing, code assistance) and how you verified outputs.
- Never claim AI-verified correctness unless you actually validated.

---

## 9. Quick checklist (before submission)

- [ ] Summary contains: problem, method, top results, credibility, recommendation.
- [ ] Every claim has a figure/table or numeric evidence.
- [ ] Baselines are clearly defined and consistent.
- [ ] KPIs definitions appear once and are reused.
- [ ] Sensitivity/robustness exists (appendix acceptable).
- [ ] Figures have conclusion titles + 2-line captions with slice/metric/baseline.
- [ ] PDF compiles cleanly; references resolve; no broken figure links.
