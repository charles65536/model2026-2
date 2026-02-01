# **Input**
Currently, our .py code files are located at `2026_MCM/src/LI_play_data/*.py`, and we expect the generated charts to be saved to `2026_MCM/output/fig` (or `2026_MCM/output/tab` for tables, and the required data to be saved to `2026_MCM/output/data_cleaned`).

I have several questions:
1. Do we need to manually create the `output/fig` and `output/tab` directories in advance?
2. If not, do we need to modify the paths in the Python files, and how? (We do not plan to use .ipynb files.)
3. After modifying the paths in the files, how should I run the script on a Windows computer to generate the new files?
Will the newly generated files overwrite the existing ones after running the script?

---

# **Output**
Understood: You currently place the entry script at `2026_MCM/src/LI_play_data/*.py` and expect outputs to be saved to:
- `2026_MCM/output/fig`
- `2026_MCM/output/tab`
- `2026_MCM/output/data_cleaned`

Below are step-by-step answers to your 4 questions, along with a **minimal modification approach** (only adjust paths/directory creation without changing core logic).

---

## 1) Do we need to manually create `output/fig` and `output/tab` in advance?

**No (recommended)**.
It is more reliable to let the script automatically create directories using `mkdir(parents=True, exist_ok=True)` (pathlib) or `os.makedirs(..., exist_ok=True)` (os module).

You only need to ensure the parent directory of `2026_MCM/output` exists (this is typically already present in the repository).

---

## 2) Do we need to modify paths in the .py files? How (without using ipynb)?

### ✅ Recommended: Keep the `--outdir` parameter, only modify "subdirectory name mapping"

Since you want outputs in `output/fig`, `output/tab`, and `output/data_cleaned`, modify the following lines in the script (usually in `main()` or before writing outputs):

Original code:
```py
table_dir = outdir / "table"
fig_dir   = outdir / "figure"
```

Modified code:
```py
tab_dir  = outdir / "tab"
fig_dir  = outdir / "fig"
data_dir = outdir / "data_cleaned"

# Automatically create directories (no error if already exists)
tab_dir.mkdir(parents=True, exist_ok=True)
fig_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)
```

Then replace all file-writing paths accordingly:
- LaTeX tables: Save to `tab_dir / "tab_baseline_consistency.tex"`
- Intermediate panel CSV: Save to `data_dir / "intermediate_weekly_panel.csv"` (as you specified "data to be saved in data_cleaned")
- Baseline predictions: Also save to `data_dir` (optional)
- PDF charts: Save to `fig_dir / "fig_fliprate_by_season.pdf"`

> **Note**: If your original code wrote to `<outdir>/table/...`, update it to `<outdir>/tab/...`; similarly, `<outdir>/figure/...` → `<outdir>/fig/...`.

### Another common issue: Default relative paths may fail due to script location changes

Your script is in `src/LI_play_data/`. If it uses relative paths (e.g., `../2026_MCM_Problem_C_Data.csv`), it is recommended to **avoid hardcoding** and continue passing the input path via the `--input` command-line argument.

---

## 3) How to run the script on Windows to generate new files?

Since you do not plan to use notebooks, run the script via the command line.

### Method A: Run from the repository root directory (the level containing `2026_MCM/`)

Works for both PowerShell and CMD. Example (PowerShell):
```powershell
cd <your-repository-root-directory>
python .\2026_MCM\src\LI_play_data\p0_triage_build_weekly_panel.py `
  --input .\2026_MCM\2026_MCM_Problem_C_Data.csv `
  --outdir .\2026_MCM\output
```

CMD syntax (no backticks; use `^` for line breaks or write as one line):
```cmd
cd <your-repository-root-directory>
python .\2026_MCM\src\LI_play_data\p0_triage_build_weekly_panel.py --input .\2026_MCM\2026_MCM_Problem_C_Data.csv --outdir .\2026_MCM\output
```

### Method B: Run from the `2026_MCM` directory (cleaner)
```powershell
cd .\2026_MCM
python .\src\LI_play_data\p0_triage_build_weekly_panel.py --input .\2026_MCM_Problem_C_Data.csv --outdir .\output
```

**After successful execution, you should see the following files**:
- `2026_MCM/output/tab/tab_baseline_consistency.tex`
- `2026_MCM/output/data_cleaned/intermediate_weekly_panel.csv`
- `2026_MCM/output/fig/fig_fliprate_by_season.pdf`

---

## 4) Will the new files overwrite existing ones after running?

**Most likely yes** (functions like `to_csv` and `savefig` overwrite files with the same name by default).
Overwriting is actually beneficial for "reproducible outputs", but if you need to preserve old versions, there are two minimal modification options:

### Option 1: Add a run ID/timestamp to filenames (most reliable)
Example:
- `intermediate_weekly_panel_20260130_1530.csv`
- `fig_fliprate_by_season_20260130_1530.pdf`

### Option 2: Add an `--overwrite` flag (throw an error if overwriting is disabled)
Pseudocode:
```py
if (out_path.exists() and not args.overwrite):
    raise FileExistsError(f"File {out_path} already exists. Use --overwrite to replace it.")
```

---

## Minimal Code Modification Recommendation

To fully align with your desired structure, you only need to make 3 changes in the script:
1. Keep `--outdir` pointing to `2026_MCM/output`
2. Change `table/figure` to `tab/fig` in the script
3. Save data products (e.g., `intermediate_weekly_panel.csv`) to `data_cleaned/`

---

If you share the exact filename of your script (e.g., `p0_triage_build_weekly_panel.py` or the actual name under `LI_play_data`) and the 10-line snippet where output directories are defined, I can provide **exact copy-paste replacement code** tailored to your script structure.