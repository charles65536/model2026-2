# last_two

This folder contains tools to infer the judges' "last-two" saving behavior:

- `infer_last_two.py`: script to estimate the probability that, when faced with the bottom-two contestants in a given week, the judges save the contestant with the higher judge score (vs. the lower one).

Outputs (written to this folder):
- `last_two_summary.csv`: per-season summary (counts, fraction saving higher, confidence intervals, p-value vs 0.5).
- `last_two_details.csv`: per-week diagnostic rows used in the inference.

Usage:
```
python3 infer_last_two.py --min-season 28
```

The script defaults to analyzing seasons `>= 28` but accepts `--min-season` and `--max-season` arguments.

Notes:
- The script uses `total_judge_score` (if present) as the judge-score metric. It only counts weeks where (a) exactly one contestant was eliminated that week and (b) the eliminated contestant is one of the bottom-two by judge score (ties at the bottom that make the bottom group larger than two are skipped).
- A Wilson confidence interval and two-sided binomial p-value (via `scipy.stats.binomtest`) are reported when `scipy` is available.
