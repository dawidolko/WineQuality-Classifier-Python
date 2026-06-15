"""
Experiment logic: data loading, models inside a Pipeline (MinMaxScaler + classifier),
stratified 5-fold cross-validation, a Majority Voting ensemble, export to LaTeX.

No leakage: scaling happens inside the Pipeline, so MinMaxScaler is fitted
exclusively on the training fold of each validation split.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier

from src.config import DATA_PATH, RANDOM_STATE, RESULTS_DIR
from src.wykresy import zapisz_wykresy_html

warnings.filterwarnings("ignore", category=UserWarning)


def wczytaj_pelna_ramke(sciezka: Path) -> pd.DataFrame:
    """
    Loads the full CSV (all columns) for exploratory analysis and plotting.

    Re-checks for missing values — consistently with training.
    """
    df = pd.read_csv(sciezka)
    if df.isna().any().any():
        raise ValueError("Missing values detected in the dataset — remove or impute them before training.")
    return df


def podziel_na_cechy_i_etykiete(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Splits the full CSV frame into a feature matrix X (without Id and quality) and a label vector y (quality classes).
    """
    feature_cols = [c for c in df.columns if c not in ("quality", "Id")]
    X = df[feature_cols]
    y = df["quality"].values
    return X, y, feature_cols


def wczytaj_i_sprawdz_dane(sciezka: Path) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Loads the WineQT CSV dataset.

    Returns:
        a frame of features (without the label column and the Id identifier),
        a vector of wine quality labels (discrete classes),
        a list of feature column names.

    Checks for missing values; raises an exception if any are found.
    """
    df = wczytaj_pelna_ramke(sciezka)
    return podziel_na_cechy_i_etykiete(df)


def utworz_pipeline_z_minmax(
    estymator: Any,
    nazwy_kolumn_cech: list[str],
) -> Pipeline:
    """
    Builds a Pipeline: first MinMax scaling to [0, 1] applied only to numeric features,
    then the supplied classifier.

    A ColumnTransformer with a single block ('num', MinMaxScaler, columns) makes it possible
    to add other feature types later without changing the principle: fitting always happens
    inside CV on the training split.
    """
    preproc = ColumnTransformer(
        transformers=[("num", MinMaxScaler(), nazwy_kolumn_cech)],
        remainder="drop",
    )
    return Pipeline([("preprocess", preproc), ("clf", estymator)])


def definicja_modeli_bazowych() -> list[tuple[str, Any]]:
    """
    Returns a list of (name, raw_estimator) for the 9 variants:
    Decision Tree × 3, kNN × 3, Random Forest × 3.

    The hyperparameters are deliberately simple (3 variants per algorithm) to keep the comparison readable.
    """
    drzewa = [
        ("dt_gleb_5", DecisionTreeClassifier(max_depth=5, min_samples_leaf=2, random_state=RANDOM_STATE)),
        ("dt_gleb_15", DecisionTreeClassifier(max_depth=15, min_samples_leaf=5, random_state=RANDOM_STATE)),
        ("dt_gleb_25", DecisionTreeClassifier(max_depth=25, min_samples_leaf=10, random_state=RANDOM_STATE)),
    ]
    knn = [
        ("knn_k5", KNeighborsClassifier(n_neighbors=5, weights="uniform")),
        ("knn_k11", KNeighborsClassifier(n_neighbors=11, weights="distance")),
        ("knn_k21", KNeighborsClassifier(n_neighbors=21, weights="uniform")),
    ]
    lasy = [
        ("rf_50", RandomForestClassifier(n_estimators=50, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1)),
        ("rf_100", RandomForestClassifier(n_estimators=100, max_depth=15, random_state=RANDOM_STATE, n_jobs=-1)),
        ("rf_200", RandomForestClassifier(n_estimators=200, max_depth=20, random_state=RANDOM_STATE, n_jobs=-1)),
    ]
    return drzewa + knn + lasy


def rodzina_z_nazwy(nazwa: str) -> str:
    """Maps a variant name to a model family (for grouped tables)."""
    if nazwa.startswith("dt_"):
        return "DecisionTree"
    if nazwa.startswith("knn_"):
        return "kNN"
    if nazwa.startswith("rf_"):
        return "RandomForest"
    return "Other"


def uruchom_walidacje(
    X: pd.DataFrame,
    y: np.ndarray,
    nazwy_cech: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Runs stratified 5-fold cross-validation for every base model (Pipeline)
    and for the Majority Voting ensemble.

    Metrics: accuracy and balanced_accuracy (mean per-class recall).

    Returns three frames:
        detailed — one row per model with the mean and std,
        family aggregates — max and mean of metrics within DecisionTree / kNN / RF,
        ensemble result — one row for the VotingClassifier.
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    wiersze: list[dict[str, Any]] = []
    for nazwa, clf in definicja_modeli_bazowych():
        pipe = utworz_pipeline_z_minmax(clf, nazwy_cech)
        cv_wynik = cross_validate(
            pipe,
            X,
            y,
            cv=cv,
            scoring=["accuracy", "balanced_accuracy"],
            n_jobs=-1,
            return_train_score=False,
        )
        wiersze.append(
            {
                "model": nazwa,
                "rodzina": rodzina_z_nazwy(nazwa),
                "accuracy_mean": float(np.mean(cv_wynik["test_accuracy"])),
                "accuracy_std": float(np.std(cv_wynik["test_accuracy"])),
                "balanced_accuracy_mean": float(np.mean(cv_wynik["test_balanced_accuracy"])),
                "balanced_accuracy_std": float(np.std(cv_wynik["test_balanced_accuracy"])),
            }
        )

    szczegoly = pd.DataFrame(wiersze)

    # Ensemble: majority voting over the 9 components (each a separate Pipeline)
    estimators: list[tuple[str, Pipeline]] = []
    for nazwa, clf in definicja_modeli_bazowych():
        estimators.append((nazwa, utworz_pipeline_z_minmax(clf, nazwy_cech)))

    ensemble = VotingClassifier(estimators=estimators, voting="hard", n_jobs=-1)
    cv_ens = cross_validate(
        ensemble,
        X,
        y,
        cv=cv,
        scoring=["accuracy", "balanced_accuracy"],
        n_jobs=-1,
        return_train_score=False,
    )
    wiersz_zespol = {
        "model": "majority_voting_9",
        "rodzina": "Ensemble",
        "accuracy_mean": float(np.mean(cv_ens["test_accuracy"])),
        "accuracy_std": float(np.std(cv_ens["test_accuracy"])),
        "balanced_accuracy_mean": float(np.mean(cv_ens["test_balanced_accuracy"])),
        "balanced_accuracy_std": float(np.std(cv_ens["test_balanced_accuracy"])),
    }
    szczegoly = pd.concat([szczegoly, pd.DataFrame([wiersz_zespol])], ignore_index=True)

    # Aggregates by family (base models only, without the ensemble)
    bazowe = szczegoly[szczegoly["rodzina"] != "Ensemble"].copy()
    grupy = bazowe.groupby("rodzina", as_index=False).agg(
        accuracy_srednia=("accuracy_mean", "mean"),
        accuracy_max=("accuracy_mean", "max"),
        balanced_accuracy_srednia=("balanced_accuracy_mean", "mean"),
        balanced_accuracy_max=("balanced_accuracy_mean", "max"),
    )

    return szczegoly, grupy, pd.DataFrame([wiersz_zespol])


def zapisz_latex(
    szczegoly: pd.DataFrame,
    grupy: pd.DataFrame,
    katalog: Path,
) -> None:
    """
    Saves tables in LaTeX format using pandas.DataFrame.to_latex.

    Files are written to the results/ directory (created if it does not exist).
    """
    katalog.mkdir(parents=True, exist_ok=True)
    fmt = "%.4f"

    szczegoly.to_latex(
        katalog / "wyniki_szczegolowe.tex",
        index=False,
        float_format=fmt,
        caption="Cross-validation (5-fold): accuracy and balanced accuracy — variants and ensemble.",
        label="tab:detailed",
        escape=True,
    )

    grupy.to_latex(
        katalog / "wyniki_agregaty_rodzin.tex",
        index=False,
        float_format=fmt,
        caption="Mean and maximum accuracy / balanced accuracy within a family (3 variants).",
        label="tab:aggregates",
        escape=True,
    )


def uruchom_pelny_eksperyment(sciezka_danych: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main entry point of the logic: data loading, evaluation, CSV and LaTeX export.

    Returns three Pandas frames (details, family aggregates, and the ensemble row in a separate last
    frame — here the last frame is only the single ensemble row; the detailed frame also includes the ensemble).
    """
    path = sciezka_danych or DATA_PATH
    df_pelny = wczytaj_pelna_ramke(path)
    X, y, nazwy = podziel_na_cechy_i_etykiete(df_pelny)
    szczegoly, grupy, _zespol = uruchom_walidacje(X, y, nazwy)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    szczegoly.to_csv(RESULTS_DIR / "wyniki_szczegolowe.csv", index=False)
    grupy.to_csv(RESULTS_DIR / "wyniki_agregaty_rodzin.csv", index=False)
    zapisz_latex(szczegoly, grupy, RESULTS_DIR)
    zapisz_wykresy_html(df_pelny, szczegoly, grupy, RESULTS_DIR)

    meta = RESULTS_DIR / "wersje_bibliotek.txt"
    meta.write_text(
        "Reproducibility: this file records the library versions used when generating the results.\n"
        f"scikit-learn {sklearn.__version__}\n"
        f"numpy {np.__version__}\n"
        f"pandas {pd.__version__}\n",
        encoding="utf-8",
    )

    return szczegoly, grupy, _zespol
