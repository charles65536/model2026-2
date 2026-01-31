# Fan-share estimator (Task A) — Developer Guide

This module implements the constrained-smoothness estimator for weekly fan vote shares described in the project modeling notes (Task A). It consumes a canonical, pre-cleaned weekly panel and produces two CSV outputs:

- fan shares (`p_est`): per-season-per-week estimated fan vote share p_{i,t} for every active contestant i and week t
- slack variables (`xi`): per-season-per-week non-negative slack values that quantify how much the elimination consistency constraints had to be relaxed for feasibility

This README duplicates and expands on the inline comments in `model_main.py` so other developers can pick up, run, and integrate the solver quickly.

Contents
- Purpose
- Concepts: what `fan_p` and `xi` mean
- Modeling significance of the solved variables (mapping to the math spec)
- Expected input (weekly panel) schema
- Outputs and example columns
- CLI usage examples
- Important design choices & internals (objective, constraints)
- Troubleshooting & common gotchas
- Testing and quick sanity checks
- Integration notes (where to call from run script)
- Recommendations (solver alternatives and next improvements)

---

Purpose

The estimator reconstructs relative fan voting shares p_{i,t} (normalized to sum to 1 across participants each week) that are consistent with known weekly eliminations and are temporally smooth. Because the problem is underdetermined (actual votes are unobserved), we select the most "reasonable" solution using a smoothness prior and a small slack for elimination constraints.

Concepts — `fan_p` (p_est) and `xi`

- fan_p / p_est (CSV column name `p_est`)
  - Meaning: estimated fraction of the weekly fan vote received by contestant i in week t, i.e. p_{i,t} in [0,1], and for each week t, sum_{i in A_t} p_{i,t} = 1.
  - Interpretation: these are relative (percentage-like) shares, not absolute vote counts. They are the model's best reconstruction under the specified smoothness and elimination constraints.
  - Use cases: feed into rule-replay/simulation modules to see how alternative voting/elimination rules would have changed outcomes; compute contestant-level season averages; analyze discrepancies between judge ranks and fan support.

- xi (CSV column name `xi`)
  - Meaning: non-negative slack (one value per season-week) introduced to relax the hard requirement that eliminated contestants must strictly be among the bottom m of the combined score S_{i,t}. xi_t quantifies how much the model had to "bend" elimination consistency for that week to make the optimization feasible.
  - Interpretation: larger xi indicates that under the modeling assumptions (alpha, percent/rank formula, judge percent qJ), the recorded elimination for that week is less consistent with any plausible fan-share assignment unless one allows relaxation. xi is therefore a flag for ambiguous/exceptional weeks (special rules, judge saves, data noise, or inconsistent recording).

Modeling significance of the solved variables (mapping to `files_for_AI/first_stage_modeling.md`)

This section connects the solver outputs directly to the mathematical formulation in the modeling spec (Task A). It explains what the solver is estimating and how the outputs should be interpreted in downstream analyses.

- Notation mapping
  - p_est -> p_{i,t}
    - The CSV `p_est` column stores the estimated p_{i,t} for each row (season, contestant, week).
    - In the spec, p_{i,t} is the unknown fan vote share for contestant i in week t with constraints p_{i,t} >= 0 and sum_{i in A_t} p_{i,t} = 1.
  - xi -> \xi_t
    - The CSV `xi` column stores the slack variable \xi_t for each (season, week).
    - \xi_t appears in the elimination consistency constraints as a non-negative slack allowing S_{e,t} <= S_{i,t} + \xi_t for eliminated e and non-eliminated i.

- How these feed into the combined score S_{i,t}
  - The solver computes judges' percentage q^{J}_{i,t} from the panel (qJ in code) and forms the combined score used in the elimination constraints:
    S_{i,t} = alpha * q^{J}_{i,t} + (1 - alpha) * p_{i,t}
  - p_est is the model's estimate of q^{V}_{i,t} in the spec (fan vote share). Downstream simulations should use S_{i,t} with the same alpha to replay Percent-rule eliminations.

- Elimination-consistency constraints (how xi is used)
  - For a week with elimination set E_t of size m, the spec requires eliminated contestants to be among the bottom m by S_{i,t}. We relax that hard combinatorial constraint into linear inequalities with slack \xi_t:
    For each e in E_t and each i in A_t \ E_t:
      S_{e,t} <= S_{i,t} + \xi_t
  - In the solver, xi is penalized in the objective as lambda * \sum_t xi_t^2, so the optimizer prefers small xi but allows positive values when the elimination record cannot be explained exactly under the percent rule and smoothness prior.

- Objective and interpretation
  - Objective minimized by solver:
    Sum_{t=2..T} Sum_{i in A_t ∩ A_{t-1}} (p_{i,t} - p_{i,t-1})^2  +  lambda * Sum_t xi_t^2
  - Temporal smoothness term enforces the modeling assumption that fan preference evolves smoothly (A5.2 in the spec). The lambda*xi^2 term enforces the "minimum distortion" (A5.3): prefer solutions that explain eliminations while minimizing violations.

- Uncertainty and diagnostics derived from outputs
  - xi_t as a diagnostic signal:
    - If xi_t ≈ 0: elimination for week t is well explained by some p_{·,t} under the model assumptions.
    - If xi_t is relatively large: the recorded elimination is inconsistent / ambiguous; investigate the week for special rules, judge-saves, or data issues.
  - Delta (elimination margin) \Delta_t (computed from outputs, not directly written by the solver):
    - Define S_hat_{i,t} using p_est.
    - Compute \Delta_t = min_{i in A_t \ E_t} S_hat_{i,t} - max_{e in E_t} S_hat_{e,t}.
    - Small or negative \Delta_t indicates the eliminated contestant(s) were not obviously the bottom by S_hat; corresponds to larger xi.
  - Feasible interval approach (A7.1): compute p^{min}_{i,t} and p^{max}_{i,t} by solving LPs that fix the same constraints but optimize one p_{i,t} at a time. These intervals quantify multi-solution uncertainty.

- Suggested downstream uses of p_est and xi (aligned to the spec sections A and B):
  - Use p_est as q^{V}_{i,t} when replaying Percent-rule eliminations in the simulator (Task B) and compute E^{(P)}_t and R^{(P)}.
  - Use p_est to compute R^{V}_{i,t} (fan ranking) when replaying Rank-rule eliminations and then form R^{(R)}_{i,t} = R^{J}_{i,t} + R^{V}_{i,t}.
  - Use xi to flag weeks to treat specially in analysis (e.g., exclude from some metrics, or mark as "contestable" weeks in the paper/appendix).
  - Use p_est seasonal averages to compare contestants' overall fan support vs final placement (controversy analysis) and to compute the discrepancy metrics described in the repo (avg_weekly_rank vs final_rank difference).

Expected statistical meaning and caveats
- p_est is an estimate under the chosen priors and constraints. Because true votes are unobserved, different priors or lambda/alpha choices will lead to different p_est; treat p_est as a model-based reconstruction, not ground truth.
- xi reports how much the percent-rule explanation needs to be relaxed; large xi weeks should be interpreted carefully and investigated qualitatively (show episodes, special rules).
- The solver's smoothness objective can cause oversmoothing if lambda is too small or alpha is mis-specified; include sensitivity checks in experiments (alpha ∈ [0.4,0.6], lambda grid search as recommended in the spec).

Expected input (weekly panel)

This module expects the weekly panel CSV to be the authoritative, pre-cleaned input. It explicitly does NOT attempt to recreate or re-clean the panel. The canonical panel (the triage script produces) should have at least these columns (defaults):

- `season` (int or string): season identifier
- `celebrity_name` (string): contestant identifier — use `--name-col` if your panel uses a different name
- `week` (int): week index within season
- `total_judge_score` (numeric): judges' aggregated score for that contestant-week

Optional columns supported (if present, pass via CLI flags):
- `active` (bool-like): whether the contestant performed and is considered active that week. If not provided, rows with non-null `total_judge_score` and >0 are treated as active.
- `true_elim_flag` or other elimination indicator (bool-like): mark rows that correspond to the eliminated contestant(s) that week. If absent, the solver will not add elimination constraints.

If your column names differ, use the CLI flags `--name-col`, `--score-col`, `--week-col`, `--active-col`, and `--elim-col` to map them.

Outputs

Two CSVs are produced (paths provided through CLI):

1) Fan shares: CSV with columns (example)
- `season` — copied from panel
- `celebrity_name` (or your name_col) — contestant id
- `week` — week index
- `p_est` — estimated fan share for the contestant-week

2) Xi (slack) CSV: columns
- `season`
- `week`
- `xi` — non-negative slack indicating violation magnitude of elimination consistency for that week

CLI usage and examples

Basic example (use canonical panel produced by triage):

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares.csv" \
  --out-xi "src\sim\xi.csv" \
  --alpha 0.5 --lambda_reg 1000 --verbose
```

If your panel uses different column names:

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares.csv" \
  --out-xi "src\sim\xi.csv" \
  --name-col "name" --score-col "total_score" --week-col "week_num" \
  --active-col "active" --elim-col "true_elim_flag" \
  --alpha 0.5 --lambda_reg 2000
```

CLI flags (summary)
- `--panel` (required): path to canonical weekly panel CSV
- `--out-p` (required): path to write fan-shares CSV
- `--out-xi` (required): path to write xi CSV
- `--alpha` (optional, default=0.5): weight on judges when forming combined score S (alpha ∈ [0,1])
- `--lambda_reg` (optional, default=1000): regularization for xi in objective
- `--name-col` (default=`celebrity_name`)
- `--score-col` (default=`total_judge_score`)
- `--week-col` (default=`week`)
- `--active-col` (optional)
- `--elim-col` (optional)
- `--hard-consistency` (optional): enforce elimination consistency as a hard constraint (no xi allowed). Use when you want to prevent inconsistency at all costs; may cause infeasibility.
- `--verbose` (optional)

Findings summary (diagnostics & sensitivity)

- Identification: The weekly panel + elimination constraints alone are often insufficient to uniquely reconstruct fan-share p_{i,t} (LP feasibility checks show wide p_min/p_max ranges for many contestant-week pairs). In short: the data are under-determined in many weeks.
- Prior effect: Adding a small per-week regularizer (variance or entropy) strongly biases solutions toward more uniform distributions when information is weak. In our experiments a modest entropy regularization (e.g., entropy_reg ≈ 0.1) already produces near-uniform weekly p vectors; larger values saturate quickly because entropy is bounded by log(n).
- Slack (xi): The solver required almost no slack (xi values ≈ 1e-7) across runs — eliminations are not highly contradictory to judge scores under the model; the observed uniformity therefore comes from the prior, not from forced feasibility via xi.
- Practical recommendation: Treat the reconstructed p_est as model-based, not ground truth. If you want a conservative, defensible default when data are weak, use a small entropy prior (entropy_reg in [0.01, 0.1]) and report sensitivity (0.0 and 0.1 or 1.0) in any analysis/appendix.
- Next steps to improve robustness: (1) run a documented grid sweep and include those tables in the appendix (done in `src/sim/grid_sensitivity_report.csv`), (2) flag weakly-identified contestant-week pairs using LP intervals + profiling so results can be annotated or excluded, and (3) for production, consider reimplementing the QP in matrix form and solving with a dedicated QP solver (cvxpy + OSQP) for stability/performance.

---

Important design choices & internals (brief)

- Objective: temporal smoothness on p_{i,t} (squared differences between consecutive-week shares for the same contestant) plus lambda * sum(xi_t^2). Minimizes change over time and penalizes slack usage.
- Constraints:
  - Per-week simplex: sum_{i in A_t} p_{i,t} = 1, p_{i,t} >= 0.
  - For weeks with elimination info, the model enforces "elimination consistency" via linear inequalities with xi slack: for each eliminated e and each non-eliminated i, S_{e,t} <= S_{i,t} + xi_t, where S_{i,t} = alpha*qJ_{i,t} + (1-alpha)*p_{i,t} and qJ is judges' share.
- Solver: SciPy SLSQP via `scipy.optimize.minimize`. This is dependency-light and works for our problem sizes. For large seasons or heavier production use, consider moving to a QP solver (`cvxpy` + `OSQP`) for speed and numeric robustness.

Troubleshooting & common gotchas
- If the solver fails to converge or returns infeasible, try:
  - Check that the panel is canonical and `elim_col` points to correct boolean elimination rows.
  - Increase `--lambda_reg` (gives more slack penalty but can help numeric stability) or reduce it (if you want xi small it's opposite) depending on symptoms.
  - Use `--verbose` to print per-season variable counts and see which season the solver struggled on.
- If many xi values are large:
  - That indicates recorded eliminations are not consistent with the percent rule & judge scores for reasonable p_{i,t}. Investigate the panel rows (special weeks, judge-save events, or data inconsistencies).
- If `p_est` values look like exact 0/1 spikes: check that the panel's `active` flags and judge scores are correct (edge case participants in a week with zero judge totals can cause the solver fallback to uniform qJ).

Testing and quick sanity checks
- Sanity: After running, for every (season, week) verify that the p_est sum across contestants is ~1.0 within floating tolerance (1e-9). A small helper script can assert this and print failing weeks.
- xi inspection: Sort xi descending to find weeks where elimination consistency was most violated.
- Reproducibility: the SLSQP solver is deterministic for the same starting point and environment; keep `alpha` and `lambda_reg` recorded for experiments.

Integration notes
- Where to call: call this module after `p0_triage_build_weekly_panel.py` (which writes `output/data_cleaned/intermediate_weekly_panel.csv`). The typical pipeline:
  1. Build weekly panel (triage step) → `intermediate_weekly_panel.csv`
  2. Run this estimator → `fan_shares.csv` (p_est) + `xi.csv`
  3. Merge `fan_shares.csv` into contestant-level preprocessed CSV if you need aggregated columns (season averages, comparisons with final rank)
  4. Run rule-replay simulations that require p_{i,t} (Percent vs Rank)

- Suggested filenames (project conventions):
  - panel: `output/data_cleaned/intermediate_weekly_panel.csv`
  - fan-shares: `src/sim/fan_shares.csv` (or `output/data_cleaned/fan_shares.csv`)
  - xi: `src/sim/xi.csv`

Recommendations & next improvements
- Swap SLSQP for a QP solver: rewrite the objective as quadratic form and constraints as matrices; use `cvxpy` with `OSQP` to gain speed and better numerical stability.
- Add a small wrapper to compute p_min/p_max intervals for selected contestants/weeks (A7.1 from modeling notes). This requires solving LPs and can be computationally heavier.
- Add automated unit tests (small fixture panels) that validate per-week sum-to-1, known toy seasons, and check handling of missing elim_col.
- If you need to prevent any inconsistency (xi > 0) use the `--hard-consistency` flag. The solver will enforce elimination constraints without slack. If the instance is infeasible under these hard constraints, the optimizer may fail; use `--verbose` to diagnose which season failed. A recommended diagnostic workflow is:
  1) Run with `--hard-consistency` to detect immediate infeasibility: if the run completes without errors and `xi` output is empty, you have strict-consistency solutions.
  2) If infeasible, run without `--hard-consistency` but with a very large `--lambda_reg` (e.g., 1e6) to force xi to be as small as possible; inspect `xi.csv` to see which weeks require slack and how large it is.
  3) Use the `xi` outputs and `Delta_t` diagnostics to investigate specific weeks (data issues or special rules).

Example: strict enforcement (may fail if data incompatible):

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares_hard.csv" \
  --out-xi "src\sim\xi_hard.csv" \
  --hard-consistency --alpha 0.5
```

If the above fails (infeasible), try forcing small xi via a large lambda:

```powershell
py "src\sim\model_main.py" \
  --panel "output\data_cleaned\intermediate_weekly_panel.csv" \
  --out-p "src\sim\fan_shares_forced.csv" \
  --out-xi "src\sim\xi_forced.csv" \
  --lambda_reg 1000000 --alpha 0.5 --verbose
```

Notes on additive penalties
- Yes: the objective is additive: Smoothness + lambda * (sum of xi^2). `--lambda_reg` is the proportion-level parameter that trades off inconsistency vs smoothness. Increasing `lambda_reg` makes the optimizer penalize inconsistency more strongly. Setting `--hard-consistency` turns off xi entirely (equivalent to lambda = +infty but handled as a hard constraint).

If you'd like, I can also add a `--fail-on-xi` flag that runs with slack allowed but returns a non-zero exit code (and optionally a report) if any xi exceeds a given threshold; this can help automation (CI) to enforce a tolerable level of inconsistency.

Contact & context
- Modeling spec: `files_for_AI/first_stage_modeling.md` — the mathematics and assumptions implemented here are drawn from that document.
- Code location: `src/sim/model_main.py` (solver implementation)
