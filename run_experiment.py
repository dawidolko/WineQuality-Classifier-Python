#!/usr/bin/env python3
"""
Script that runs the full experiment from the repository root.

Usage (from the project directory):
    python run_experiment.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allows importing the `src` package when running the file without installing it as a package
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment import uruchom_pelny_eksperyment  # noqa: E402


def main() -> None:
    print("Evaluating models (this may take a few minutes)...")
    szczegoly, grupy, zespol = uruchom_pelny_eksperyment()
    print("\n--- Summary (excerpt) ---")
    print(szczegoly.to_string(index=False))
    print("\n--- Family aggregates ---")
    print(grupy.to_string(index=False))
    print("\n--- Ensemble (Majority Voting) ---")
    print(zespol.to_string(index=False))
    print("\nSaved to results/: CSV, LaTeX (.tex), HTML charts (wykresy/), wersje_bibliotek.txt")


if __name__ == "__main__":
    main()
