# Framing & Spec Playbook (Optimization / Policy / Simulation Track)

**Purpose:** Convert a problem statement into a *tight* report plan: deliverable, claims, KPIs, baselines, and a 2-hour baseline plan.

---

## 0) What judges reward (practical)
- Clear deliverable: a policy/strategy with implementable logic
- Evidence chain: claims backed by L1 figures/tables
- Baselines: fair comparisons
- Trade-offs: improvements vs cost
- Robustness: sensitivity + failure modes + rollback

---

## 1) Deliverable patterns (pick one primary)
- **Policy + Simulation** (default)
- **Optimization formulation + heuristic**
- **Hybrid: prediction → optimization** (only if needed)

---

## 2) Claim design (3–5 claims, testable)
Claims must be specific (slice+metric), comparative (vs baseline), bounded (assumptions), and testable (pass/fail).

---

## 3) KPI registry (authoritative)
For each KPI define: name, direction, aggregation, slice/window, baseline(s).

Recommended minimal set:
- Service: mean + P95/P99 + violation rate
- Cost: total/mean cost
- Stability: variance across slices
- Optional fairness: gap/variance

---

## 4) Baselines
Include at least one “strong” heuristic baseline and (if possible) ablations.

---

## 5) 2-hour baseline plan (mandatory)
Minimal processing → implement baseline(s) → compute KPIs → output 1 table + 1 tail plot → 4 report-ready sentences.

---

## 6) Plan B (degrade gracefully)
Specify what is simplified, what evidence remains, and what you stop claiming.

---

## 7) “Framing Ticket” template (copy/paste)

**Problem summary (≤5 lines):**  
**Preferred deliverable type:** policy / optimization / hybrid  
**Constraints:**  
**Available data fields:**  

**Return exactly:**
1) Deliverable (1 sentence)  
2) Claims (3–5 bullets “We claim that…”)  
3) KPI table (3 main + 2 constraints)  
4) Assumption budget (≤5)  
5) Data requirements (P0/P1 + top-3 risks)  
6) 2-hour baseline plan (3–5 lines)  
7) Plan B (≤3 lines)
