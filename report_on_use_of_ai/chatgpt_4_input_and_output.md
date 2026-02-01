# **Input**
Wait, why is the generated .pdf file completely unchanged? Could there be an issue with how we implemented the rules? Also, where in the code you provided do we need to modify the paths for importing and exporting files?
---
# **Output**
The most common reason you see **"no changes" in the PDF** is not an error in the rules, but that **the path/file you’re opening is not the newly generated one**. Additionally, our **BL-0 baseline** inherently results in a FlipRate very close to 0, making the plot appear "largely unchanged".

The plot you uploaded itself shows FlipRate fluctuating around 0 (with a very small coordinate range)—this is an **expected outcome** under BL-0.

---

## 1) Why the PDF Appears Unchanged (Troubleshooting by Priority)

### A. You’re Opening a PDF in an Old Path (Most Common)
The engineering structure in your `context_pack_for_ai.md` specifies `outputs/fig` and `outputs/tab`,
but my script writes to `<outdir>/figure` and `<outdir>/table` by default:

```py
table_dir = outdir / "table"
fig_dir   = outdir / "figure"
```

If you’re viewing `outputs/fig/fig_fliprate_by_season.pdf` while the script writes to `outputs/figure/fig_fliprate_by_season.pdf`, the file will "appear unchanged".

✅ Solution: Verify you’re opening the file the script actually generated:
- `<outdir>/figure/fig_fliprate_by_season.pdf` (default path)
- Or modify the script to write to `<outdir>/fig/...` (see Section 3 below)

---

### B. You Did Regenerate the File, but Plots Show No Obvious Changes Under BL-0 (Also Common)
In the current BL-0 baseline, we use a **uniform fan distribution** (equal fan_percent for every active contestant), meaning:
- `combined_percent = judge_percent + constant`
- Rankings remain unchanged (except for minor tie-breaking differences in implementation)

Thus, FlipRate is almost certainly very low, and it’s normal for the curve to look "nearly identical".

---

### C. The Script Isn’t Overwriting Files (outdir Points Elsewhere)
The script doesn’t print logs, so you might not realize where the output is actually saved after running it. The simplest way to confirm is:

```bash
ls -l <outdir>/figure/fig_fliprate_by_season.pdf
ls -l <outdir>/table/intermediate_weekly_panel.csv
```

Check if the modification timestamps are updated.

---

## 2) Where to Modify "Import/Export Paths"

### ✅ Recommended: Modify Command-Line Arguments (No Code Changes Needed)
The script entry point is already parameterized:

```bash
python src/p0_triage_build_weekly_panel.py \
  --input  path/to/2026_MCM_Problem_C_Data.csv \
  --outdir path/to/outputs
```

- `--input`: Path to the raw CSV file
- `--outdir`: Root output directory (the script creates `table/` and `figure/` subdirectories here)

### If You’re Using a Notebook
The **first code cell** in `p0_triage_build_weekly_panel.ipynb` is:

```bash
!python ../src/p0_triage_build_weekly_panel.py --input ../2026_MCM_Problem_C_Data.csv --outdir ../output
```

Simply update the `--input`/`--outdir` values to match the actual paths in your project.

---

## 3) If You Must Align with context_pack Directories: `outputs/tab` + `outputs/fig`
You only need to modify **two lines in the main() function** (no other logic changes):

Change:
```py
table_dir = outdir / "table"
fig_dir = outdir / "figure"
```

To:
```py
table_dir = outdir / "tab"
fig_dir = outdir / "fig"
```

After modification, run:
```bash
python src/p0_triage_build_weekly_panel.py --input <csv> --outdir outputs
```

Files will now be saved to:
- `outputs/tab/intermediate_weekly_panel.csv`
- `outputs/tab/tab_baseline_consistency.tex`
- `outputs/fig/fig_fliprate_by_season.pdf`

---

## 4) A Quick Trick to "Confirm You’re Viewing the New Plot"
Temporarily modify the plot title (e.g., add "(REGEN)"), then re-run the script and open the file. If the title doesn’t change, you’re not opening the newly generated file:

```py
plt.title("Rule divergence ... under BL-0 (REGEN)")
```

---

If you share the exact command line you’re using to run the script, I can directly tell you:
**the absolute path where the PDF is saved**, and whether the file you’re opening matches this path.