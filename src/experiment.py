"""
Logika eksperymentu: wczytanie danych, modele w Pipeline (MinMaxScaler + klasyfikator),
stratyfikowana walidacja krzyżowa 5-fold, zespół Majority Voting, eksport do LaTeX.

Brak przecieku: skalowanie jest wewnątrz Pipeline, więc dopasowanie MinMaxScaler
odbywa się wyłącznie na zbiorze treningowym każdej foldy walidacji.
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
    Wczytuje pełny CSV (wszystkie kolumny) do analizy eksploracyjnej i wykresów.

    Ponownie sprawdza brakujące wartości — spójnie z treningiem.
    """
    df = pd.read_csv(sciezka)
    if df.isna().any().any():
        raise ValueError("Wykryto brakujące wartości w zbiorze — usuń lub uzupełnij je przed treningiem.")
    return df


def podziel_na_cechy_i_etykiete(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Z pełnej ramki CSV wycina macierz cech X (bez Id i quality) oraz wektor etykiet y (klasy jakości).
    """
    feature_cols = [c for c in df.columns if c not in ("quality", "Id")]
    X = df[feature_cols]
    y = df["quality"].values
    return X, y, feature_cols


def wczytaj_i_sprawdz_dane(sciezka: Path) -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """
    Wczytuje plik CSV ze zbiorem WineQT.

    Zwraca:
        ramkę z cechami (bez kolumny etykiety i identyfikatora Id),
        wektor etykiet jakości wina (klasy dyskretne),
        listę nazw kolumn cech.

    Sprawdza brakujące wartości; w razie wykrycia podnosi wyjątek.
    """
    df = wczytaj_pelna_ramke(sciezka)
    return podziel_na_cechy_i_etykiete(df)


def utworz_pipeline_z_minmax(
    estymator: Any,
    nazwy_kolumn_cech: list[str],
) -> Pipeline:
    """
    Buduje Pipeline: najpierw skalowanie MinMax do [0, 1] tylko na cechach numerycznych,
    potem przekazany klasyfikator.

    ColumnTransformer z jednym blokiem ('num', MinMaxScaler, columns) pozwala w przyszłości
    dodać inne typy cech bez zmiany zasady: dopasowanie zawsze wewnątrz CV na train.
    """
    preproc = ColumnTransformer(
        transformers=[("num", MinMaxScaler(), nazwy_kolumn_cech)],
        remainder="drop",
    )
    return Pipeline([("preprocess", preproc), ("clf", estymator)])


def definicja_modeli_bazowych() -> list[tuple[str, Any]]:
    """
    Zwraca listę (nazwa, surowy_estymator) dla 9 wariantów:
    Decision Tree × 3, kNN × 3, Random Forest × 3.

    Hiperparametry są celowo proste (3 warianty na algorytm), żeby porównanie było czytelne.
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
    """Mapuje nazwę wariantu na rodzinę modelu (do tabel grupowych)."""
    if nazwa.startswith("dt_"):
        return "DecisionTree"
    if nazwa.startswith("knn_"):
        return "kNN"
    if nazwa.startswith("rf_"):
        return "RandomForest"
    return "Inne"


def uruchom_walidacje(
    X: pd.DataFrame,
    y: np.ndarray,
    nazwy_cech: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Dla każdego modelu bazowego (Pipeline) oraz zespołu Majority Voting wykonuje
    stratyfikowaną 5-krotną walidację krzyżową.

    Metryki: accuracy oraz balanced_accuracy (średnia czułości po klasach).

    Zwraca trzy ramki:
        szczegółowa — jeden wiersz na model z średnią i odchyleniem std,
        agregaty rodzin — max i średnia metryk w obrębie DecisionTree / kNN / RF,
        wynik zespołu — jeden wiersz dla VotingClassifier.
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

    # Zespół: głosowanie większościowe po 9 składowych (każdy to osobny Pipeline)
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

    # Agregaty po rodzinie (tylko modele bazowe, bez zespołu)
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
    Zapisuje tabele w formacie LaTeX przy użyciu pandas.DataFrame.to_latex.

    Pliki trafiają do katalogu results/ (tworzony jeśli nie istnieje).
    """
    katalog.mkdir(parents=True, exist_ok=True)
    fmt = "%.4f"

    szczegoly.to_latex(
        katalog / "wyniki_szczegolowe.tex",
        index=False,
        float_format=fmt,
        caption="Walidacja krzyzowa (5-fold): accuracy i balanced accuracy — warianty i zespol.",
        label="tab:szczegolowe",
        escape=True,
    )

    grupy.to_latex(
        katalog / "wyniki_agregaty_rodzin.tex",
        index=False,
        float_format=fmt,
        caption="Srednie i maksymalne accuracy / balanced accuracy w obrebie rodziny (3 warianty).",
        label="tab:agregaty",
        escape=True,
    )


def uruchom_pelny_eksperyment(sciezka_danych: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Główny punkt wejścia logiki: wczytanie danych, ewaluacja, zapis CSV i LaTeX.

    Zwraca trzy ramki Pandas (szczegóły, agregaty rodzin, wiersz zespołu w osobnej ramce
    ostatniej — tutaj ostatnia ramka jest tylko jednym wierszem zespołu; szczegóły zawierają też zespół).
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
        "Odtwarzalnosc: ten plik zapisuje wersje bibliotek przy generowaniu wynikow.\n"
        f"scikit-learn {sklearn.__version__}\n"
        f"numpy {np.__version__}\n"
        f"pandas {pd.__version__}\n",
        encoding="utf-8",
    )

    return szczegoly, grupy, _zespol
