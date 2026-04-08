"""
Stałe konfiguracyjne projektu.

Ustalenie jednego seeda dla wszystkich komponentów losowych zwiększa
odtwarzalność wyników zgodnie z dokumentacją scikit-learn.
"""

from pathlib import Path

# Katalog główny repozytorium (katalog nadrzędny względem src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ścieżka do zbioru Wine Quality (Kaggle / yasserh)
DATA_PATH = PROJECT_ROOT / "data" / "WineQT.csv"

# Katalog na wyniki numeryczne i tabele LaTeX
RESULTS_DIR = PROJECT_ROOT / "results"

# Jeden wspólny seed dla CV, modeli losowych i ewentualnego mieszania
RANDOM_STATE = 42
