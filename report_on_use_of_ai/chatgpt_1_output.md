# **Output**
# List of Authoritative Supporting Literature  
This list is curated **based on your current problem statement scope + KPI framework + Model v1 direction**: it directly supports your **KPI1/KPI3 (elimination consistency/rule divergence)**, **KPI2 (identifiability/feasible intervals)**, and the **Kendall/Spearman correlation and bottom-two + judges save simulation modules** explicitly mentioned in `first_stage_modeling.md`. Additionally, the problem statement itself provides official explanations for "Rank vs Percent rule examples, N/A encoding, and 0-score encoding after elimination"—these serve as your most robust "scope anchors".  

---

## 1) Must-Cite: Problem Statement Scope (As the sole authoritative anchor for "rules/encoding")  

1. **COMAP MCM Problem C (2026) – Official Problem Statement PDF**  

* Key points to cite:  
  * Rank scheme applied to Seasons 1, 2, 28a–34; Percent scheme applied to Seasons 3–27a (explicitly stated in the problem statement)  
  * Definition of N/A (missing 4th judge, unaired weeks of the season) and "0-score encoding after elimination"  
* Purpose: **All rule simulations, active set definitions, and denominator scopes for KPI1/KPI3 must be derived from this document**.  

---

## 2) Optimization/Constraints/Identifiability (Supports the narrative of "inferring fan votes/feasible intervals/regularization")  

2. **Boyd, S., & Vandenberghe, L. (2004). *Convex Optimization*** (One of the most authoritative textbooks on QP/constrained optimization) ([Stanford University][1])  

* Key endorsements:  
  * Methodological validity of formulating the estimation of unobservable fan votes as a constrained convex optimization/quadratic program, and robustifying it with regularization terms.  
* Corresponding components: KPI2 (feasible intervals/identifiability) and the mathematical foundation for your subsequent vote-estimation plug-in.  

3. **Tikhonov, A. N., & Arsenin, V. Y. (1977). *Solutions of Ill-Posed Problems*** (Classic work on "ill-posed/underdetermined inverse problems + regularization") ([Reddit][2])  

* Key endorsements:  
  * Your current information structure—essentially "inferring latent variables (fan votes) via elimination constraints"—falls under the category of **ill-posed/underdetermined inverse problems**. Regularization (smoothness/penalty terms) is not an arbitrary choice.  
* Corresponding components: KPI2 + the core narrative of "why smoothness priors/regularization are needed to enhance identifiability" (you also mentioned "adjacent-week smoothness" in your context).  

4. **Hansen, P. C. (1998). *Rank-Deficient and Discrete Ill-Posed Problems*** (Discrete underdetermined problems, regularization, and numerical stability) ([JSTOR][3])  

* Key endorsements:  
  * Under "rank deficiency + discrete constraints", solutions are non-unique; regularization and sensitivity testing are standard practices to control uncertainty.  
* Corresponding components: Your core narrative.  

---

## 3) "Formal Mathematical Language" for Modeling Share/Proportion Variables (Fan Vote Share)  

> Under the Percent scheme, you will naturally encounter **vote shares (compositional data, sum-to-one)**; ordinary linear regression is "misaligned" for such variables, requiring appropriate transformations or distributions.  

5. **Aitchison, J. (1986). *The Statistical Analysis of Compositional Data*** (Foundational work on compositional data analysis) ([Law School][4])  

* Key endorsements:  
  * Fan vote **shares** qualify as compositional data; approaches such as log-ratio transformations or logistic-normal distributions are orthodox methods for their analysis.  
* Corresponding components: Estimation, constraints, and interpretation of any "vote share" under the Percent scheme.  

6. **Aitchison, J. (1982). The statistical analysis of compositional data (JRSS-B paper, classic review/theory on compositional data)** ([JSTOR][5])  

* Purpose: A more "paper-like" citation alternative if you prefer not to cite an entire book.  

7. **Aitchison, J., & Shen, S. M. (1980). Logistic-normal distributions (commonly used for share modeling)** ([SCIRP][6])  

* Key endorsements:  
  * Using logistic-normal/correlated structures to model "adjacent-week smoothness and individual heterogeneity" for shares is a statistically valid approach.  

---

## 4) Orthodox Model References for "Ranking Data" (Ranking/Elimination)  

8. **Plackett, R. L. (1975). The analysis of permutations (JRSS-C)** (One of the origins of the Plackett–Luce family) ([OUP Academic][7])  

* Key endorsements:  
  * Converting "composite scores" of contestants into rankings/eliminations in a given week is equivalent to inference and comparison on permutations/rank data.  
* Corresponding components: Rank scheme and theoretical grounding for "comparing ranking differences caused by two schemes".  

9. **Hunter, D. R. (2004). MM algorithms for generalized Bradley–Terry models (Annals of Statistics)** ([Project Euclid][8])  

* Key endorsements:  
  * Bradley–Terry type models are an orthodox framework for "inferring latent strengths from wins/losses/relative comparisons"; your "elimination/retention" can also be viewed as partial order information.  
* Corresponding components: An alternative route (can be cited as related work even if not fully adopted) for converting "elimination signals" into "latent fan preference strengths".  

---

## 5) Authoritative Sources for Kendall/Spearman (Already Mentioned in `first_stage_modeling.md`)  

10. **Kendall, M. G. (1938). A new measure of rank correlation (Biometrika)** ([OUP Academic][9])  

* Key endorsements:  
  * The original authoritative source for Kendall tau when reporting "correlations between final rankings (Kendall tau / Spearman)".  

(The original Spearman literature can be added if needed, but Kendall tau is generally sufficient for "academic rigor".)  

---

## 6) Hierarchical/Random Effects (For robust interpretation of "season/celebrity random terms" if adopted)  

11. **Bates, D., Maechler, M., Bolker, B., & Walker, S. (2015). Fitting linear mixed-effects models using lme4 (JSS)** ([Journal of Statistical Software][10])  

* Key endorsements:  
  * Mixed-effects models are the standard approach for modeling season-level and celebrity-level heterogeneity (even if only considered as an optional enhancement).  

12. **Gelman, A., & Hill, J. (2007). *Data Analysis Using Regression and Multilevel/Hierarchical Models*** ([JSTOR][11])  

* Key endorsements:  
  * "Interpretive scopes" for hierarchical modeling (partial pooling, avoiding overfitting) will make the report more aligned with formal statistical practice.  

---

## 7) Rule Aggregation/Voting Theory (Supports "why systematic differences arise between rank vs percent")  

13. **Saari, D. G. (2001). *Decisions and Elections: Explaining the Unexpected*** ([Cambridge University Press & Assessment][12])  

* Key endorsements:  
  * Different aggregation rules can lead to "unexpected outcomes/flip-overs"—a core theme in social choice theory; highly relevant to explaining your KPI3 (FlipRate).  

14. **Arrow, K. J. (1951/Subsequent editions). *Social Choice and Individual Values*** ([JSTOR][11])  

* Key endorsements:  
  * If your memo includes statements like "no perfect voting system exists, hence we make trade-offs and impose interpretability constraints", citing Arrow is the most risk-free approach.  

---

### A) Integrate the "Literature List" into `dynamic_files/context_pack_for_ai.md`  

The **#11 Literature List section in your document is currently empty**. Directly paste the 14 entries above categorized into 4 groups:  

* Rule/encoding (COMAP)  
* Optimization & ill-posed (Boyd, Tikhonov, Hansen)  
* Compositional/share (Aitchison series)  
* Rank/voting theory (Plackett, Hunter, Kendall, Saari, Arrow)  

This structure allows writers to **directly cite** the literature and facilitates unified compilation of `myref.bib` later.  

### B) No Need to Update `kpi_registry.md` for Literature Purposes  

The role of `kpi_registry.md` is "scope registration", not a bibliography. Unless you plan to add a new column "Primary reference" to the registry, it is safer to leave it unchanged. The current definitions of KPI1/KPI3/KPI2 and their problem statement anchors are already self-consistent (especially the Season-28 assumption and stress-test annotations).  

---

[1]: https://web.stanford.edu/class/ee364a/lectures.html?utm_source=chatgpt.com "EE364a: Lecture Slides"
[2]: https://www.reddit.com/r/dancingwiththestars/comments/1aqlkwx/dancing_with_the_stars_ep_explains_why_the_judges/?utm_source=chatgpt.com "Dancing With the Stars EP Explains Why the Judges' Save ..."
[3]: https://www.jstor.org/stable/2334029?utm_source=chatgpt.com "Rank Analysis of Incomplete Block Designs"
[4]: https://leg.est.ufpr.br/lib/exe/fetch.php/pessoais%3Aabtmartins%3Athestatisticalanalysisofcompositionaldata.pdf?utm_source=chatgpt.com "The Statistical Analysis of Compositional Data J. Aitchison ..."
[5]: https://www.jstor.org/stable/2345821?utm_source=chatgpt.com "The Statistical Analysis of Compositional Data"
[6]: https://www.scirp.org/reference/referencespapers?referenceid=2923928&utm_source=chatgpt.com "De Borda, J. (1781) Mémoire sur les élections au scrutin. ..."
[7]: https://academic.oup.com/jrsssc/article/24/2/193/6953554?utm_source=chatgpt.com "Analysis of Permutations | Journal of the Royal Statistical ..."
[8]: https://projecteuclid.org/journals/annals-of-statistics/volume-32/issue-1/MM-algorithms-for-generalized-Bradley-Terry-models/10.1214/aos/1079120141.full?utm_source=chatgpt.com "MM algorithms for generalized Bradley-Terry models"
[9]: https://academic.oup.com/biomet/article-abstract/30/1-2/81/176907?utm_source=chatgpt.com "NEW MEASURE OF RANK CORRELATION | Biometrika"
[10]: https://www.jstatsoft.org/v67/i01/?utm_source=chatgpt.com "Fitting Linear Mixed-Effects Models Using lme4"
[11]: https://www.jstor.org/stable/j.ctt1nqb90?utm_source=chatgpt.com "Social Choice and Individual Values"
[12]: https://www.cambridge.org/core/books/decisions-and-elections/C5A8C567FA56349016B25EF04AFA7170?utm_source=chatgpt.com "Decisions and Elections"