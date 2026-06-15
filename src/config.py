"""
Project configuration constants.

Fixing a single seed across all random components improves
result reproducibility, in line with the scikit-learn documentation.
"""

from pathlib import Path

# Repository root (the parent directory of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Path to the Wine Quality dataset (Kaggle / yasserh)
DATA_PATH = PROJECT_ROOT / "data" / "WineQT.csv"

# Directory for numeric results and LaTeX tables
RESULTS_DIR = PROJECT_ROOT / "results"

# One shared seed for CV, randomized models and optional shuffling
RANDOM_STATE = 42
