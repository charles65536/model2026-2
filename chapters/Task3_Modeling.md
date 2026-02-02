## Task 3: Impact of Professional Dancers and Celebrity Characteristics on Competition Outcomes

### 3.1 Modeling Objective

The goal of Task 3 is to quantify how **professional dancers** and observable **celebrity characteristics** influence competition outcomes in *Dancing with the Stars*.
Since outcomes arise through multiple channels, we decompose the analysis into three components:

1. **Judges’ evaluations** (technical performance channel),
2. **Audience voting behavior** (popularity channel),
3. **Final competition outcomes** (elimination risk).

This decomposition allows us to examine whether professional dancers and celebrity attributes affect judges and audiences in the same way, and how these effects translate into survival in the competition.

---

### 3.2 Data Structure and Explanatory Variables

All explanatory variables are restricted to fields explicitly provided in the official dataset, ensuring full auditability.

**Celebrity characteristics**
- Age during the season (`celebrity_age_during_season`)
- Industry category (`celebrity_industry`)
- Home region (simplified as U.S. vs. non-U.S.)

**Professional dancer**
- Ballroom partner identifier (`ballroom_partner`)

**Structural controls**
- Week index (or early / mid / late competition phase)
- Season fixed effects

---

### 3.3 Outcome Definitions

Let \(i\) index celebrity–dancer pairs, \(t\) index weeks, and \(s\) index seasons.

#### Judges’ score share

For each active contestant in week \(t\):

\[
q^J_{i,t} = \frac{J_{i,t}}{\sum_{r \in A_{s,t}} J_{r,t}},
\]

where \(J_{i,t}\) is the total judges’ score and \(A_{s,t}\) is the set of active contestants.

To ensure unbounded support, we apply a logit transformation:

\[
y^J_{i,t} = \log\frac{q^J_{i,t} + \varepsilon}{1 - q^J_{i,t} + \varepsilon}.
\]

#### Fan vote share

From Task 1, we obtain inferred audience vote shares \(p_{i,t}\), which are similarly transformed:

\[
y^V_{i,t} = \log\frac{p_{i,t} + \varepsilon}{1 - p_{i,t} + \varepsilon}.
\]

#### Elimination outcome

Define a binary indicator:

\[
E_{i,t} =
\begin{cases}
1, & \text{if contestant } i \text{ is eliminated in week } t, \\
0, & \text{otherwise}.
\end{cases}
\]

---

### 3.4 Model A: Judges’ Evaluation Model (Technical Channel)

We first examine how professional dancers and celebrity characteristics affect judges’ evaluations.

\[
y^J_{i,t}
=
\beta_0
+ \beta^\top X_i
+ f(t)
+ \text{FE}_s
+ u_i
+ v_{\text{pro}(i)}
+ \varepsilon_{i,t},
\]

where:
- \(X_i\) includes celebrity age, industry, and region,
- \(f(t)\) captures week-level scoring trends,
- \(\text{FE}_s\) denotes season fixed effects,
- \(u_i \sim \mathcal{N}(0, \sigma_u^2)\) is a celebrity random effect,
- \(v_{\text{pro}} \sim \mathcal{N}(0, \sigma_{\text{pro}}^2)\) is a professional dancer random effect.

The variance component \(\sigma_{\text{pro}}^2\) measures the extent to which professional dancers systematically influence judges’ scores.

---

### 3.5 Model B: Audience Voting Model (Popularity Channel)

To isolate audience preferences beyond technical performance, we control for judges’ evaluations when modeling fan votes.

\[
y^V_{i,t}
=
\gamma_0
+ \gamma_J y^J_{i,t}
+ \gamma^\top X_i
+ f(t)
+ \text{FE}_s
+ a_i
+ b_{\text{pro}(i)}
+ \eta_{i,t}.
\]

Here:
- \(\gamma_J\) captures the transmission of judges’ evaluations into audience voting,
- \(b_{\text{pro}}\) represents a professional dancer’s independent influence on fan support.

To compare audience and judges’ preferences for a given celebrity attribute \(k\), we define:

\[
\Delta_k = \gamma_k - \beta_k.
\]

A positive \(\Delta_k\) indicates stronger audience preference relative to judges, while a negative value indicates the opposite.

---

### 3.6 Model C: Elimination Risk Model (Competition Outcome)

Finally, we link both evaluation channels to competition outcomes using a discrete-time survival model.

\[
\Pr(E_{i,t} = 1)
=
\text{logit}^{-1}
\Big(
\theta_0
+ \theta_J y^J_{i,t}
+ \theta_V y^V_{i,t}
+ \theta^\top X_i
+ g(t)
+ \text{FE}_s
+ r_{\text{pro}(i)}
\Big).
\]

This model quantifies how judges’ scores, audience votes, celebrity characteristics, and professional dancers jointly affect the probability of elimination in each week.

---

### 3.7 Treatment of Uncertainty in Inferred Fan Votes

Since fan vote shares \(p_{i,t}\) are inferred rather than observed, we account for uncertainty by weighting observations according to their identifiability.

Let \(w_{i,t}\) denote the width of the feasible vote interval from Task 1. We assign weights:

\[
\omega_{i,t} = \frac{1}{w_{i,t} + \varepsilon},
\]

so that more precisely identified observations exert greater influence in estimation.

---

### 3.8 Interpretation for Task 3

Together, these models allow us to:

**Task 3 — Modeling Summary**

- **Models:** Model A (judges mixed model), Model B (audience mixed model), Model C (discrete-time elimination via GEE).
- **Output files:** summaries and objects are in `src/eval/task3/` (see `modelA_judges_summary.txt`, `modelB_audience_summary.txt`, `modelC_elim_summary.txt`) and per-entity strengths in `src/eval/task3/` (CSV files `celebrity_strengths_*.csv`, `pro_strengths_*.csv`).

- **Model A — Judges (MixedLM)**
	- Outcome: `yJ` = logit(judge share).
	- Fixed effects: `age`, categorical `celebrity_industry` (season fixed effects included in the main fit).
	- Random effects: celebrity and professional (random intercepts).
	- Key estimates (refit without `week_num`): `age` = -0.090 (SE 0.011, p < 0.001).
	- Variance components: celebrity Var = 3.265, pro Var = 3.265, residual (scale) = 15.2148.
	- ICCs (approx): ICC_celebrity ≈ 0.15, ICC_pro ≈ 0.15 (15% of variance each on the log-odds scale).

- **Model B — Audience (MixedLM)**
	- Outcome: `yV` = logit(p_est) (audience share from solver predictions).
	- Fixed effects: `yJ` (logit judge share), `age`, categorical `celebrity_industry`.
	- Random effects: celebrity and professional (random intercepts).
	- Key estimates (refit without `week_num`): `yJ` = 0.263 (SE 0.051, p < 0.001); `age` = -0.061 (SE 0.016, p < 0.001).
	- Variance components: celebrity Var = 8.614, pro Var = 8.614, residual (scale) = 1.7289.
	- ICCs (approx): ICC_celebrity ≈ 0.45, ICC_pro ≈ 0.45 (about 45% of variance each).

- **Model C — Elimination (GEE, Binomial)**
	- Outcome: `E` = indicator of elimination in a given week.
	- Estimation: GEE (Binomial) with `Exchangeable` working correlation, clustering by `ballroom_partner` (pro). Fixed effects included `yJ`, `yV`, `age`, industry and season dummies.
	- Notes: the GEE run displayed numerical instability for the full design (some coefficients reported as `NaN` due to link overflow / separation). GEE is population-averaged and does not produce BLUPs; use Models A/B BLUPs for per-entity strength estimates.

- **Per-entity strengths (BLUPs)**
	- For Models A and B we extracted random-intercept BLUPs (per-celebrity and per-pro) and saved them as CSVs in `src/eval/task3/`:
		- `celebrity_strengths_judges.csv`, `celebrity_strengths_audience.csv`, `pro_strengths_judges.csv`, `pro_strengths_audience.csv`.
	- Each CSV contains `entity`, `n_obs`, `blup_logodds` and `odds_ratio = exp(blup_logodds)`.
	- Interpretation: BLUPs are shrunken estimates of entity-specific intercepts on the log-odds scale — positive BLUP → higher-than-average baseline log-odds (judges or audience) after adjusting for covariates.

- **Recommendations**
	- Inspect top/bottom ranked entities and their `n_obs` in the strength CSVs to ensure estimates are not dominated by very small samples.
	- If BLUPs for elimination (Model C) are required, consider fitting a logistic GLMM (random intercept) using a GLMM-capable solver (e.g., R `lme4`) as GEE does not provide BLUPs.
	- Produce diagnostic plots for MixedLM residuals and BLUP shrinkage (I can add plotting scripts if you want).

Summary files and CSVs are written to `src/eval/task3/`.
