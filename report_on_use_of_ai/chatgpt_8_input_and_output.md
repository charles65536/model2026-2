# **Input**
'Handling of "Withdrew": Should it be "exclude after inferring the exit week" or "exclude the entire season from the consistency denominator"?
Consistency denominator: Exclude no-elimination weeks, use set-match for multi-elimination weeks (is this acceptable?).'
What is the best way to handle this? Is it part of our cleaning standards? If we only add this one-sentence patch, will it cause huge problems in subsequent data processing?

# **Output**
This is **part of the cleaning standards**, and it must be **implemented in the kpi_registry**; otherwise, two types of "huge problems" will occur later:

1. During the Data phase, everyone will handle withdrew/no-elimination/multi-elimination according to their own intuition, leading to **inconsistent KPI denominators** → irreproducible results;
2. In your writing, you mention "consistency", but when reviewers ask "how is the denominator calculated", you **cannot answer or give inconsistent responses**.

Therefore: **Adding a patch is not a risk; on the contrary, it reduces risk**. The real risk is "not clarifying it clearly".

---

## 1) Is this really considered cleaning?

Yes, but more accurately, it is called **"KPI-aware cleaning / eligibility rules"**, which falls within the scope of "standard audit" in your Data phase.
It does not involve complex imputation or model-based repairs; it only defines which weeks/which contestants are included in the active set and KPI denominators—completely aligned with your "strategy/simulation-oriented, no general EDA" approach.

---

## 2) Will adding only one sentence lead to huge subsequent problems?

**No**. On the contrary, problems will arise if you only add one sentence without implementing it as an executable rule.
The "huge problems" you are worried about mainly come from two points:

### Risk A: The Data Agent sees a single sentence but is still uncertain about the details during implementation

Solution: Do not just write "may be excluded"; instead, write it as an **executable rule** (IF/THEN or eligibility definition). I have already provided a deterministically inferred method in the previous triage.

### Risk B: Will the inference of the exit week for "Withdrew" be "wrong"?

Key point: We are not inferring the real program process, but making a **reproducible coding interpretation**. The problem statement clearly states: scores after elimination will be recorded as 0, and withdrawals exist.
Defining the exit week as "the last active week with non-zero/non-missing scores" is one of the most conservative and common practices; moreover, we can replace it in sensitivity tests.

---

## 3) Which handling method do I recommend (a most stable default for you)

Given that your current goal is to **run through KPIs + baseline for P0**, I recommend adopting:

### ✅ Default Scheme (Recommended, Most Stable and Executable)

**Withdrew: Infer the exit week according to deterministic rules, exclude weeks after the exit week from the active set and KPI denominators; at the same time, retain the withdrawal week (exit_week) in the panel, but mark it separately as `exit_type="withdrew"` in the true value set of "elimination consistency", and do not count it as "predicted elimination hit" by default.**

Why this is the most stable:

* **Reproducible** (does not rely on external information or subjective judgment)
* **Does not overstate KPIs** (does not use withdrawals as evidence of "successful/failed elimination prediction")
* **Will not damage subsequent models**: If you later want to model withdrawals as a type of "non-elimination exit", you only need to modify one standard.

---

## 4) What the patch you actually need should look like (to avoid ambiguity in subsequent implementation)

It is not "adding one sentence", but adding a paragraph of **clear eligibility rules**. You still meet the requirement of "modifying at most 2 paragraphs + 1 table" because this belongs to the slice/eligibility paragraph of the `kpi_registry`.

You can add the following 4 lines to the end of the slice/window definitions in `kpi_registry.md` (**minimal increment but sufficiently executable**):

```markdown
- Special exit handling (deterministic):
  - If `results == "Withdrew"`, define `exit_week` as the last week with non-missing judge scores (or `total_judge_score > 0`); weeks after `exit_week` are excluded from the active set and KPI denominators.
  - Withdrawals are not counted as “true eliminations” in elimination-consistency KPIs by default; they are reported separately as `exit_type="withdrew"` for sensitivity analysis.
```

This will not cause "huge problems"; it will only make subsequent implementations **consistent**.

---

## 5) The minimal "safety net" you still need (no additional workload)

Simply write the handling of withdrawals as a **stress test switch** in the subsequent deep phase (no need to do it now):

* ST1: **Exclude all withdrawal weeks from the consistency denominator** (more conservative)
* ST2: Treat withdrawals as eliminations (more aggressive, usually not recommended, but can be used as an upper bound)

This way, you can close the loop with one sentence in your writing: *"Results are robust to alternative treatment of withdrawals."*

---

### Conclusion

* This is part of the cleaning standards (more accurately: KPI-aware eligibility rules).
* Clarifying it now (in the `kpi_registry`) will not cause trouble; on the contrary, it is the key to avoiding subsequent "standard conflicts".
* Recommended default: **Deterministically infer the exit week + do not count withdrawals as elimination hits**, and retain a stress test switch.

If you wish, I can make this patch into a "precise replacement block" **according to the specific paragraph position of your current `kpi_registry.md`** (to avoid errors when you manually find the position); however, I need you to paste a short section of the current content of `kpi_registry.md` (only the slice definition part, 20–40 lines).