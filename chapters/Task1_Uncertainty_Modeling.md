# X. Uncertainty and Reliability of Estimated Fan Votes

## X.1 Motivation: Non-Uniqueness of Fan Vote Estimates

In this section, we assess the uncertainty and reliability of the estimated fan vote totals obtained in Task 1. While multiple configurations of fan votes may reproduce the observed eliminations, not all such configurations are equally stable or informative. Therefore, beyond verifying consistency with historical eliminations, we further quantify how sensitive our estimates are to reasonable perturbations and how constrained the feasible solution space is.

The elimination outcome in each week provides only a weak constraint on the underlying fan votes. As long as the eliminated contestant attains the lowest combined score, many different fan vote distributions may satisfy the observed result. Consequently, the estimated fan votes are generally **not unique**, and their credibility must be evaluated through stability and variability rather than exactness.

---

## X.2 Primary Method: Perturbation-Based Robustness Analysis

### X.2.1 Perturbation Design

Let \(\hat v_{i,w}\) denote the estimated fan vote share of contestant \(i\) in week \(w\). To model realistic fluctuations in audience voting behavior, we introduce multiplicative perturbations to the estimates:

\[
v_{i,w}^{(b)} = \hat v_{i,w} \cdot \exp(\eta_{i,w}^{(b)}),
\]

where \(\eta_{i,w}^{(b)} \sim \mathcal{N}(0,\sigma^2)\), and \(b = 1, \dots, B\) indexes Monte Carlo samples. After perturbation, votes are normalized so that the total fan vote share in each week remains constant.

---

### X.2.2 Elimination Stability (Flip Rate)

For each perturbed realization, we recompute the combined judge–fan score using the same aggregation rule as in the original model and identify the eliminated contestant.

We define the **elimination stability** for week \(w\) as:

\[
C_w = \frac{1}{B} \sum_{b=1}^{B} 
\mathbf{1}\left\{ \text{elim}_{w}^{(b)} = \text{elim}_{w}^{\text{true}} \right\},
\]

where \(\text{elim}_{w}^{\text{true}}\) is the actual eliminated contestant in week \(w\).

---

### X.2.3 Contestant-Level Vote Uncertainty

For each contestant \(i\) in week \(w\), the perturbation procedure yields an empirical distribution of \(v_{i,w}^{(b)}\). From this distribution, we compute a central credible interval (e.g., 5th–95th percentile):

\[
[v_{i,w}^{5\%}, \; v_{i,w}^{95\%}].
\]

The width of this interval reflects the uncertainty associated with the estimated fan vote share for that contestant-week pair.

---

## X.3 Supplementary Method: Feasible Solution Interval Analysis

### X.3.1 Feasible Set Definition

For a fixed week, let the combined score for contestant \(i\) be:

\[
S_i = \alpha \cdot \frac{J_i}{\sum_k J_k} + (1-\alpha) \cdot \frac{v_i}{\sum_k v_k},
\]

where \(J_i\) denotes the judge score and \(v_i\) the fan vote.

Given the observed elimination outcome, the feasible set consists of all \( \{v_i\} \) satisfying:

\[
S_e \le S_j \quad \forall j \neq e,
\]

along with non-negativity and normalization constraints on fan votes.

---

### X.3.2 Interval Width as an Uncertainty Measure

For each contestant \(i\), we compute the minimum and maximum feasible fan vote shares \((v_i^{\min}, v_i^{\max})\). We define the **relative feasible interval width** as:

\[
U_i = \frac{v_i^{\max} - v_i^{\min}}{\hat v_i + \varepsilon}.
\]

Large values of \(U_i\) indicate weakly constrained estimates, while small values suggest that the fan vote estimate is tightly restricted by the observed elimination.

---

## X.4 Summary of Uncertainty Findings

By combining perturbation-based robustness analysis with feasible interval examination, we obtain a comprehensive assessment of uncertainty. While fan vote estimates are not unique, the key conclusions derived from them—such as elimination consistency and voting system comparisons—are generally stable, with uncertainty varying meaningfully across weeks and contestants.
