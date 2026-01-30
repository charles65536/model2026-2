"""
Run the full consolidated workflow with hardcoded arguments.

- Input (hardcoded): 2026_MCM_Problem_C_Data.csv (located in the same folder)
- Output (hardcoded): output.csv (written to the same folder)

This script runs the following subcommands from workflow.py in sequence:
  1) preprocess -> writes a temporary preprocessed CSV
  2) fix-variances -> writes a temporary fixed preprocessed CSV
  3) compute-controversial -> writes final `output.csv`

Usage:
  py run.py
#

Note: this script calls the `workflow.py` script in the same directory using the `py` launcher.
"""
from __future__ import annotations
import subprocess
import os
import sys

BASE_DIR = os.path.dirname(__file__)
WORKFLOW = os.path.join(BASE_DIR, "workflow.py")
INPUT_CSV = os.path.join(BASE_DIR, "2026_MCM_Problem_C_Data.csv")
PREPROCESSED = os.path.join(BASE_DIR, "2026_MCM_Problem_C_Data_preprocessed_run.csv")
PREPROCESSED_FIXED = os.path.join(BASE_DIR, "2026_MCM_Problem_C_Data_preprocessed_run_fixed.csv")
OUTPUT_CSV = os.path.join(BASE_DIR, "output.csv")

def run(cmd: list[str]):
    print("\n>>> Running:", " ".join(cmd))
    res = subprocess.run(cmd, shell=False)
    if res.returncode != 0:
        raise SystemExit(f"Command failed with exit code {res.returncode}: {' '.join(cmd)}")


def main():
    # sanity checks
    if not os.path.exists(WORKFLOW):
        raise FileNotFoundError(f"workflow.py not found at {WORKFLOW}")
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input CSV not found at {INPUT_CSV}")

    # 1) preprocess
    cmd1 = ["py", WORKFLOW, "preprocess", INPUT_CSV, "--output", PREPROCESSED]
    run(cmd1)

    # 2) fix-variances
    cmd2 = ["py", WORKFLOW, "fix-variances", "--input", PREPROCESSED, "--output", PREPROCESSED_FIXED]
    run(cmd2)

    # 3) compute controversial -> final output
    cmd3 = ["py", WORKFLOW, "compute-controversial", PREPROCESSED_FIXED, "--output", OUTPUT_CSV, "--top", "50"]
    run(cmd3)

    print(f"\nAll done. Final file: {OUTPUT_CSV}")

if __name__ == '__main__':
    main()
