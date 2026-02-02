# Case Studies — Controversial Figures

Data source: `output/data_cleaned/clean_long_data_new1.csv`

This short report summarizes four case studies and the insights drawn from judge-score trajectories and season-level statistics. The four contestants are: Jerry Rice (Season 2), Billy Ray Cyrus (Season 4), Bristol Palin (Season 11), and Bobby Bones (Season 27).

**Key columns used**: `season`, `week`, `celebrity_name`, `celebrity_industry`, `age`, `placement`, `elim_week`, `J_total`, `J_sum_week`, `J_pct`, `active`.

---

**Season 2 — Jerry Rice**

- Industry / Age: Athlete, 43
- Placement: 2 (runner-up)
- Weeks observed: 8 (active all weeks)
- Judge support: mean J_pct = 0.1652, median = 0.1523, std = 0.0697
- Judge total (mean / max): 22.52 / 26.67
- Last-week J_pct: 0.3162
- Percentile among season peers (mean J_pct): 70.0%

Weekly trajectory (week, J_total, J_sum_week, J_pct, active):
- Week 1: 21.0, 195.0, 0.1077, True
- Week 2: 23.0, 200.0, 0.1150, True
- Week 3: 19.0, 182.0, 0.1044, True
- Week 4: 24.0, 158.0, 0.1519, True
- Week 5: 23.0, 151.0, 0.1523, True
- Week 6: 23.0, 133.0, 0.1729, True
- Week 7: 20.5, 102.0, 0.2010, True
- Week 8: 26.6666, 84.3329, 0.3162, True

Interpretation: Jerry Rice shows a clear late surge in judge support, consistent with a contestant who gains momentum and finishes strongly.

---

**Season 4 — Billy Ray Cyrus**

- Industry / Age: Singer/Rapper, 45
- Placement: 5 (eliminated Week 8)
- Weeks observed: 10 (8 active)
- Judge support: mean J_pct = 0.0850, median = 0.0963, std = 0.0507
- Judge total (mean / max): 15.20 / 21.00
- Last-week J_pct (last active): 0.1514; subsequent weeks show inactive (0.0) rows after elimination
- Percentile among season peers (mean J_pct): 54.5%

Trajectory summary (week 1→8 active): modest judge scores early-to-mid season (0.06–0.12), occasional higher weeks but not sustained.

Interpretation: Billy Ray's judge support was middling and inconsistent, explaining elimination before the final despite some moderately strong weeks.

---

**Season 11 — Bristol Palin**

- Industry / Age: TV Personality, 19
- Placement: 3 (finalist)
- Weeks observed: 10 (active all weeks)
- Judge support: mean J_pct = 0.1463, median = 0.1174, std = 0.0752
- Judge total (mean / max): 22.92 / 32.50
- Last-week J_pct: 0.3092
- Percentile among season peers (mean J_pct): 75.0%

Trajectory: modest early judge support with clear growth in weeks 6–10 and a strong final week (J_pct ≈ 0.309). Highest single-week judge total in season (32.50).

Interpretation: Bristol shows classic late improvement — judges became more favorable late in the run, consistent with a controversial figure consolidating judge support near the finale.

---

**Season 27 — Bobby Bones**

- Industry / Age: Radio Personality, 38
- Placement: 1 (winner)
- Weeks observed: 9 (active all weeks)
- Judge support: mean J_pct = 0.1120, median = 0.0946, std = 0.0505
- Judge total (mean / max): 22.39 / 27.00
- Last-week J_pct: 0.2338
- Percentile among season peers (mean J_pct): 69.2%

Trajectory: steady judge support with gradual increases and a noticeable late jump; strong enough across weeks to secure the championship.

Interpretation: steady and improving judge support culminating in winning the season.

---

**Cross-case Insights**

- Late surges in judge support are common among high-placing contestants here (Jerry Rice, Bristol Palin, Bobby Bones). Strong final-week judge support correlates with final placement.
- Controversial figures may start with mixed or moderate judge support but can consolidate judge favor later, producing high placements.
- Mid-season middling judge support (Billy Ray Cyrus) can still lead to elimination before final despite occasional better weeks.
- Percentile context (mean J_pct relative to peers) provides clearer sense of relative judge favor than absolute values alone.

**Files referenced / produced**

- Source used: `output/data_cleaned/clean_long_data_new1.csv` (the rows for the four contestants were extracted there)
- Report saved as: `report_on_use_of_ai/case_studies_controversial_figures.md`

**Recommended next steps (left as options — not executed):**
- Generate per-contestant plots `week vs J_pct` and `J_total` and save under `output/fig/` for inclusion in a longer report.
- Compare judge support with model-estimated audience shares (`p_est`) to show judge vs public splits.
- Run replay fidelity checks focused on weeks when these contestants’ survival was marginal.

---

End of report. This file has been written and left in the repository as requested.

---

## Bottom‑Two Judge‑Save Simulation — Additional Findings

I ran a Bottom‑2 + judge‑save replay using the model outputs (alpha = 0.5 p_est) to test whether altering the game rule to allow judges to save a contestant in the Bottom‑2 would have helped or hurt the four controversial figures discussed above.

What I simulated
- For each week with eliminations, identify the two contestants with the lowest S = alpha * qJ + (1 - alpha) * p_est.
- The judges 'save' in the Bottom‑2 by retaining the one with the higher judge total; the other contestant is eliminated.
- When multiple eliminations occur in the same week the elimination step is applied sequentially (recomputing the Bottom‑2 after each elimination).

Files produced
- `src/eval/bottom_two_analysis.py` — simulation script used.
- `src/eval/replay_bottom_two_season{S}.csv` — per‑season replay traces (S in {2,4,11,27}).
- `src/eval/bottom_two_diffs.csv` — per‑week predicted vs actual eliminations across the tested seasons.
- `src/eval/bottom_two_contestant_summary.csv` — per‑contestant summary for the four case studies.
- `src/eval/case_study_fan_support.csv` — previously produced p_est vs judge comparisons used to interpret results.

Main results (alpha = 0.5)
- Jerry Rice (Season 2): predicted eliminated in week 7 under judge‑save. Historical record shows judges were weaker than audience for him (p_est rank 1 vs judge rank 3 at the decisive week). Conclusion: judge‑save would have **nerfed** Jerry Rice (audience rescue removed).
- Billy Ray Cyrus (Season 4): predicted = actual (week 8). No meaningful change; conclusion: judge‑save has **no practical effect** for Billy Ray in this season.
- Bristol Palin (Season 11): predicted elimination in week 9 under judge‑save (differs from the historical outcome). She shows moderately higher p_est than judge rank in the decisive moment. Conclusion: judge‑save would likely have **nerfed** Bristol in this simulation.
- Bobby Bones (Season 27): predicted elimination in week 8 under judge‑save. Case study p_est shows strong fan support vs weaker judge support. Conclusion: judge‑save would have **nerfed** Bobby Bones.

Interpretation
- Judge‑save privileges judge preferences in the critical Bottom‑2 step; contestants whose survival historically relied on audience/fan share are most at risk under judge‑save.
- Where p_est substantially exceeded judge support (Jerry, Bobby), the audience acted as a rescuing force historically — removing that mechanism via judge‑save tends to move elimination earlier for those contestants.
- Where judge and audience support were aligned (Billy Ray), judge‑save made little or no difference.

Caveats and methodological notes
- This run used `alpha = 0.5` (equal weight to modelled judge-derived qJ and audience p_est). Different alpha values change S and can flip marginal cases.
- Some `actual_week` values were missing in `intermediate_weekly_panel.csv` (so `bottom_two_contestant_summary.csv` shows NaN for a few actual weeks). I relied on `bottom_two_diffs.csv` (per‑week predicted vs actual) to confirm which weeks differed.
- Tie‑breaking order in the simulation: compare judge total first, then p_est, then deterministic name sort. Different tie rules can affect edge cases.
- Sequential elimination in multi‑elim weeks is applied stepwise; alternate simultaneous-elimination semantics might yield different results.

Recommended follow‑ups
- Sensitivity sweep across alphas (0.3–0.7) to test robustness of the four conclusions. Example commands:

```bash
PYTHONPATH=. python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.3
PYTHONPATH=. python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.4
PYTHONPATH=. python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.5
PYTHONPATH=. python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.6
PYTHONPATH=. python3 src/eval/bottom_two_analysis.py --seasons 2,4,11,27 --alpha 0.7
```

- Produce per‑contestant plots (weekly judge total, p_est, and S) and save under `output/fig/` for inclusion in the report — useful to show exactly when audience vs judge diverged.
- Optionally run the bottom‑2 simulation across all seasons to estimate the fraction of historical eliminations that would differ under judge‑save.

Short takeaways for the report
- Changing to a Bottom‑2 + judge‑save rule **reduces audience power** in decisive moments; for the controversial contestants examined, this tends to *hurt* those who benefited from fan support (Jerry Rice, Bristol Palin, Bobby Bones) and leave those aligned with judges largely unaffected (Billy Ray Cyrus).

---

End of additions.

---

## Task C — Mixed‑Effects Model Results (Fan Share)

I fitted a linear mixed‑effects model on the logit transform of the modelled fan share (`p_est`, alpha=0.5) to estimate how star traits and judge support relate to audience support while accounting for season and celebrity identity.

Files and artifacts
- `src/eval/fit_mixed_effects.py` — script used to fit the model.
- `output/data_cleaned/clean_long_data_with_p_est_alpha0p5.csv` — merged panel with `p_est` used for fitting.
- `src/eval/mixed_effects_summary.txt` — full model summary (saved); `src/eval/mixed_effects_result.pkl` — pickled fit object.

Key results (summary highlights)
- Sample: 5,554 observations across 34 seasons.
- Fixed effects (selected):
	- **Age**: coefficient ≈ **−0.056** (SE 0.012), p < 0.001 — older celebrities have **lower** fan‑share on the logit scale.
	- **Judge share (J_pct_num)**: coefficient ≈ **+1.412** (SE 0.153), p < 0.001 — higher judge support strongly correlates with higher fan share.
	- **Industry**: the `Model` industry shows a significant negative effect (coef ≈ **−3.13**, p < 0.001); other industries show heterogeneous and mostly noisy estimates.
- Random / variance components:
	- **Celebrity variance component** (VC for `celebrity_name`) ≈ **9.675** (vcomp); residual scale ≈ **0.267**. This indicates a very large between‑celebrity variance in logit(p_est) relative to residual week‑to‑week variation under the current parametrization.

Interpretation and caveats
- The model confirms two intuitive patterns: (1) judge support and fan support are positively associated, and (2) age is negatively associated with fan support after adjusting for judge support and industry.
- The very large celebrity variance component suggests that a large share of variation in fan support is driven by stable differences across celebrities (idiosyncratic popularity), which the random effects capture. This is expected — some celebrities are consistently more popular than others — but the magnitude here is large and worth diagnostic follow‑up (check scaling, centering, and whether the variance component is absorbing other structural heterogeneity).
- The model used a conservative imputation/merging approach: `p_est` values were read from the solver outputs (`alpha = 0.5`) and merged on `season, week, celebrity_name`. Observations where `p_est` could not be matched are excluded from the fit.

Recommended next steps (for robustness)
- Inspect model diagnostics (random effects distribution, residuals) and consider alternative group/VC specifications (e.g., celebrity as group and season as VC, or include random slopes for `J_pct_num`).
- Refit with standardized covariates (center/scale age and J_pct) to improve interpretability of variance components and reduce numerical issues.
- Fit the model across multiple `alpha` settings (p_est sensitivity) to verify that fixed‑effect signs and magnitudes are stable.

Where to find the full output
- See `src/eval/mixed_effects_summary.txt` for the complete statsmodels summary (coefficients, SEs, and variance components). The pickled model object is saved at `src/eval/mixed_effects_result.pkl` for downstream random‑effects extraction or plotting.

---

End of report additions.
