# **Input**
Now let's go through the materials and prompt to be handed over to the Data Agent for triage:
```
* File Description:
In the global files,
2026_MCM_Problem_C.pdf contains the problem statement, and 2026_MCM_Problem_C_Data.csv is the raw data (critical for you!).
Our data_play_book.md is your playbook; visual_play_book.md is the playbook for other agents, which you only need to regard as a document to be followed by the downstream visualization_agent in the overall workflow and is of secondary importance to you.
Take dynamic_files/context_pack_for_ai.md and dynamic_files/kpi_registry.md as the authoritative standards.
In accordance with dynamic_files/data_agent_triage_ticket.md (our triage ticket for you),
implement the following process: P0 Data Cleansing → KPI Computation Feasibility → Baseline Model Execution → Generate output/table/tab_baseline_consistency.tex and intermediate CSV files.
Output the results as required in our triage ticket.
```
Could you check if there are any issues with this prompt?

---

# **Output**
Your prompt is on the right track overall (with clear authoritative standards, ticket-driven execution and product delivery paths), but I recommend making **3 minor revisions**; otherwise, the Data Agent may still make mistakes or deviate from the requirements during implementation:

### 3 Potential Issues with Your Current Prompt
1) The sentence "In the global files…" may mislead the Agent into thinking it can freely reference other files (especially the investigation-related ones)
You have not explicitly stated **"Do not read/reference any investigation materials"**. Yet you previously decided that investigation materials are invalid and not to be provided to the Agent.
**Recommendation**: Explicitly prohibit the use of non-authoritative files (including investigation materials) in the prompt to prevent the Agent from "using them casually" once they appear in the context.

2) The phrase "Output the results" is a bit vague: prevent the Agent from producing a "written summary" instead of deliverable files
You have specified the need to generate `tab_baseline_consistency.tex` and intermediate CSV files, but it is better to add one more sentence:
* **Deliverables are files only**, and list the paths of the generated files in the response (you have also emphasized the manifest/script entry point).

3) One engineering constraint is missing: the entry point is in `src/` and executable as directed by the manifest
Your global requirements specify that "the code entry point is under src/". This is not mentioned in your prompt, and the Agent may scatter scripts in the root directory or notebooks.

### Recommended "More Robust Version" (Can be used directly as a replacement)
I have made minimal changes to your original text to make the meaning more definitive and less prone to misinterpretation:
```text
* File Description / Authoritative Standards:
- 2026_MCM_Problem_C.pdf: Problem statement (authoritative)
- 2026_MCM_Problem_C_Data.csv: Raw data (authoritative, top priority)
- data_play_book.md: Your playbook (must be followed)
- visual_play_book.md: Playbook for the downstream visualization_agent (for reference only, secondary importance)
- dynamic_files/context_pack_for_ai.md & dynamic_files/kpi_registry.md: The "sole authoritative standards" for this project (in case of conflicts, these shall prevail)
- dynamic_files/data_agent_triage_ticket.md: Triage ticket for you (must be complied with item by item)

* Prohibitions:
- Do not read/reference the content of problem_C_investigation.md or any files not listed above as "authoritative/required" to define fields, KPIs, units or problem interpretations; mark as "To Be Confirmed" if in doubt, and adopt the safest defaults provided in the triage ticket.

* Your Tasks (strictly follow the Definition of Done in the triage ticket):
Implement the following in accordance with dynamic_files/data_agent_triage_ticket.md:
P0 Data Cleansing → KPI Computation Feasibility → Baseline Model Execution → Generate
1) output/table/tab_baseline_consistency.tex
2) output/table/intermediate_weekly_panel.csv (or the intermediate CSV files required in the triage ticket)
Clearly list the paths of the generated files and their corresponding KPIs/slices in your response.

* Engineering Constraints:
- Place code entry scripts under src/ and ensure they can be run directly to generate the aforementioned deliverables (the manifest points to the entry point).
- No extensive EDA; only perform minimal cleansing/slicing/summarization to support KPI calculation and baseline comparison.
```

### Which Content in Your Original Prompt Can Remain Unchanged?
* "Take context_pack/kpi_registry as the authoritative standards" ✅
* "Implement P0→KPI→Baseline→Deliverables in accordance with data_agent_triage_ticket" ✅
* "visual_play_book is downstream of you, of secondary importance" ✅ (but it is recommended to just keep the phrase "for reference only")

If you want to make it even more **foolproof**, I can add a **final acceptance clause** for you (it does not increase the length but can significantly reduce deviations):

> "Acceptance is based solely on file deliverables: the task shall be deemed incomplete if `output/table/tab_baseline_consistency.tex` is not generated."