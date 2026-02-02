"""Centralized project paths.

Provide canonical directories so scripts can import and avoid repeated ROOT logic.
"""
from __future__ import annotations
import os
from typing import Iterable

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
DATA_RAW = os.path.join(PROJECT_ROOT, 'data_raw')
DATA_CLEAN = os.path.join(PROJECT_ROOT, 'output', 'data_cleaned')
SIM_DIR = os.path.join(SRC_DIR, 'sim')
EVAL_DIR = os.path.join(SRC_DIR, 'eval')
REPLAYS_DIR = os.path.join(PROJECT_ROOT, 'replays')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
OUTPUT_FIG_DIR = os.path.join(PROJECT_ROOT, 'output', 'fig')
REPORTS_DIR = os.path.join(PROJECT_ROOT, 'reports')


def ensure_dirs(paths: Iterable[str]):
    for p in paths:
        if not os.path.exists(p):
            os.makedirs(p, exist_ok=True)
