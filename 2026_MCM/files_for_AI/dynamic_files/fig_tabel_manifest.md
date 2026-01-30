# Figure Manifest (Authoritative)

**Version:** v0.1  
**Updated:** 2026-1-30 10:00  
**Owner:** 李金灿 
**Root:** 2026_MCM/output  
**Rule:** Every L0/L1 figure must support a Claim. No orphan figures.

| Fig ID | Level | Claim Supported | Q (Judge Question) | Metric | Slice/Window | Baseline | File (pdf/png) | Script Path | Where in Report | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| Fig01 | L0 | (overview) | What did you build? | — | — | — | output/figures/fig_pipeline.pdf / .png | src/viz/fig_pipeline.py | Summary/Method | TODO |
| Fig02 | L0 | Headline result | Did it improve KPIs? | KPI set | main slice | baseline A | output/figure/fig_headline.pdf / .png | src/viz/fig_headline.py | Summary/Results | TODO |
| Fig10 | L1 | Claim-1 | Does it reduce tail? | P95/P99/ECDF | peak windows | baseline A/B | output/figure/fig_tail_ecdf.pdf / .png | src/viz/fig_tail_ecdf.py | Results | TODO |
| Fig11 | L1 | Claim-2 | Trade-off acceptable? | cost vs service | all / peak | baseline A | output/figure/fig_pareto.pdf / .png | src/viz/fig_pareto.py | Results | TODO |
| Fig20 | L2 | Robustness | Sensitive to params? | KPI vs param | stress tests | baseline A | output/figure/fig_sensitivity.pdf / .png | src/viz/fig_sensitivity.py | Appendix | TODO |

| Tab ID | Purpose | Metric/KPI | Slice/Window | Baseline | File (.tex) | Script/Source | Where in Report | Status |
|---|---|---|---|---|---|---|---|---|
| Tab01 | KPI summary | main KPIs | main slice | A/B | output/table/tab_kpi_summary.tex | src/eval/make_tables.py | Results | TODO |
| Tab02 | Ablation | delta KPIs | peak | A | output/table/tab_ablation.tex | src/eval/ablation.py | Appendix | TODO |