# **Input**
What should we do regarding the previous conversation? Because the `investigation` file is **non-authoritative**; the files we feed to the agent do not include the `investigation`—it is only used for us to check if our framing/spec agent has any important omissions.
Now clearly tell me how to use the information you provided above (e.g., 3. Place the Data Agent Triage work order in... file / place it separately in the conversation as a prompt).

# **Output**
In line with your current constraints (**the `investigation` file is non-authoritative and will not be fed to the Data Agent**; it is only used to check for omissions in the framing/spec), you can use my previous output as two types of materials: **(1) an executable work order for the Data Agent** + **(2) minimal standard patches for backfilling `dynamic_files`**. The specific operations are as follows (step by step, no need to modify the `investigation` file further).

---

## 4-Step Operations You Need to Do Now (Most Stable, Minimal Modifications)

### Step 1) Freeze the "Authoritative Standard Sources"

* **From now on**: The Data Agent will only refer to
  * `dynamic_files/context_pack_for_ai.md`
  * `dynamic_files/kpi_registry.md`
  * Competition raw materials (PDF + CSV)
* **`investigation` file**: Reserved solely for you to check for omissions—**it will not be included in any agent’s input**.

> You do not need to modify the `investigation` file; just clearly add one sentence in the `context_pack`: “The `investigation` file is non-authoritative / not used by agents.”

---

### Step 2) Paste the **`kpi_registry` patch** I provided (Mandatory)

You need to copy and paste the **"kpi_registry.md Patch"** from my previous output into:
* `dynamic_files/kpi_registry.md`

And in accordance with the rules I wrote, **only replace that 1 table + 2 paragraphs** (slice / baseline + changelog).

**Purpose**: To enable the Data Agent to obtain the sole authoritative standards for "which KPIs to calculate, how to slice data, and what the baseline is"; otherwise, they will definitely deviate or get stuck.

---

### Step 3) Paste the **`context_pack` patch** I provided (Mandatory)

Copy and paste the **"context_pack_for_ai.md Patch"** from my previous output into:
* `dynamic_files/context_pack_for_ai.md`

Focus on two key things:
1. Correct the engineering directories: **`output/figure/` & `output/table/`** (consistent with your current global constraints)
2. Clearly document the **P0 data snapshot and cleaning rules** (so the Data Agent can follow them directly)

---

### Step 4) How to Use the "Data Agent Triage Work Order" (Choose One of Two Options)

#### Option A (Recommended): **Create a New Work Order File** (Most Stable, Traceable)

Create a new file:
* `dynamic_files/data_agent_triage_ticket.md`

Simply copy and paste the entire **Part 3: Data Agent Triage Work Order** from my previous output into it.

Then, the only prompt you need to give to the Data Agent is one sentence:
> “Please read `dynamic_files/context_pack_for_ai.md`, `dynamic_files/kpi_registry.md`, `dynamic_files/data_agent_triage_ticket.md`, and the competition raw materials (PDF/CSV), and implement P0 according to the work order.”

Advantages: Version-controllable and least likely to cause confusion in team collaboration.

#### Option B: **Do Not Create a File, Send Directly as a Conversation Prompt to the Data Agent**

Directly copy the entire **Data Agent Triage Work Order** from my previous output and use it as your "system/first task message" to the Data Agent.

Advantages: Fastest. Disadvantages: Slightly poorer subsequent traceability and version management.

> Regarding your question of "placing it in... a file / separately in the conversation"—I recommend Option A; choose Option B if you are in a hurry.

---

## How to "Use the `investigation` File to Check for Omissions" (Without Feeding It to the Agent)

You only need to do one thing: Extract the content that appears in the `investigation` file but is not present in the competition statement/`registry`, and create a **"To-Be-Confirmed List (≤3 items)"**. Place this list in the "Open Questions" paragraph of the `context_pack` (only write "To Be Confirmed/Assumption"—do not state them as facts).

Example (based on my audit results, these are usually the only worthwhile items to retain for confirmation):
1. **Whether the Season-28 cutoff is merely a reasonable assumption** (the competition statement says it is unknown, with only Season 28 as a reasonable assumption)
2. How to include multi-elimination/no-elimination weeks in the denominator (I have provided a safe default: drop no-elimination weeks; use set-match for multi-elimination weeks)
3. Whether external data is allowed to estimate fan votes (the competition statement permits it but requires complete citation; not used by default)

These 3 items are sufficient; all other "thresholds/tests/targets" from the `investigation` file must not be included in any standard files.

---

## Finally, a "Shortest Guiding Prompt You Can Directly Copy to the Data Agent"

(Applicable for both Option A and Option B)

**Data Agent Instructions (English)**
* Only refer to `dynamic_files/context_pack_for_ai.md` and `dynamic_files/kpi_registry.md` as the authoritative standards; do not read or reference `problem_C_investigation.md`.
* Implement the following in accordance with `dynamic_files/data_agent_triage_ticket.md` (or the Triage Work Order I pasted in the conversation): P0 Cleaning → KPI Calculable → Baseline Runnable → Deliver `output/table/tab_baseline_consistency.tex` and all intermediate CSV files.

If you tell me whether you prefer **Option A (create a file)** or **Option B (conversation prompt)**, I can write the "Data Agent’s first message" as a single paragraph that you can directly copy and paste (no need for you to assemble it yourself).