"""
Wykresy Plotly do prezentacji zbioru oraz wyników walidacji krzyżowej.

Używane w aplikacji Streamlit oraz zapisywane jako HTML do katalogu results/wykresy/
po uruchomieniu pełnego eksperymentu.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def wykres_rozkald_jakosci(df: pd.DataFrame, kolumna_jakosci: str = "quality") -> go.Figure:
    """
    Histogram / słupki liczebności klas jakości wina (zadanie klasyfikacji wieloklasowej).
    """
    vc = df[kolumna_jakosci].value_counts().sort_index()
    fig = px.bar(
        x=vc.index.astype(str),
        y=vc.values,
        labels={"x": "Klasa jakości (etykieta)", "y": "Liczba próbek"},
        title="Rozkład etykiety „quality” w zbiorze",
        color_discrete_sequence=["#2E86AB"],
    )
    fig.update_layout(
        xaxis_title="Jakość (klasa)",
        yaxis_title="Liczba obserwacji",
        showlegend=False,
        template="plotly_white",
        height=420,
    )
    return fig


def wykres_macierz_korelacji(df: pd.DataFrame, kolumny_numeryczne: list[str]) -> go.Figure:
    """
    Mapa ciepła korelacji Pearsona między cechami numerycznymi (w tym etykieta).
    """
    sub = df[kolumny_numeryczne].select_dtypes(include=["number"])
    corr = sub.corr(numeric_only=True)
    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Macierz korelacji (cechy numeryczne)",
    )
    fig.update_layout(height=560, template="plotly_white")
    return fig


def _etykieta_wykresu(wiersz: pd.Series) -> str:
    rodz = str(wiersz.get("rodzina", ""))
    model = str(wiersz.get("model", ""))
    if rodz == "Ensemble":
        return "Zespół (Majority Voting)"
    return f"{rodz}: {model}"


def wykres_porownanie_metryk(szczegoly: pd.DataFrame) -> go.Figure:
    """
    Słupki: średnia accuracy i balanced accuracy dla każdego wariantu i zespołu
    (z paskami błędu = std z foldów).
    """
    df = szczegoly.copy()
    df["etykieta"] = df.apply(_etykieta_wykresu, axis=1)
    # Kolejność: rodziny grupowo, na końcu zespół
    df["_sort"] = df["rodzina"].map(
        {"DecisionTree": 0, "kNN": 1, "RandomForest": 2, "Ensemble": 3}
    ).fillna(9)
    df = df.sort_values(["_sort", "model"])

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Accuracy (średnia ± std z 5 foldów)", "Balanced accuracy (średnia ± std)"),
        horizontal_spacing=0.08,
    )

    x = list(range(len(df)))
    fig.add_trace(
        go.Bar(
            x=x,
            y=df["accuracy_mean"],
            error_y=dict(type="data", array=df["accuracy_std"], visible=True),
            marker_color="#1B998B",
            name="Accuracy",
            showlegend=False,
            hovertext=df["etykieta"],
            hoverinfo="text+y",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=x,
            y=df["balanced_accuracy_mean"],
            error_y=dict(type="data", array=df["balanced_accuracy_std"], visible=True),
            marker_color="#E84855",
            name="Balanced acc.",
            showlegend=False,
            hovertext=df["etykieta"],
            hoverinfo="text+y",
        ),
        row=1,
        col=2,
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=x,
        ticktext=df["model"],
        tickangle=-45,
        row=1,
        col=1,
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=x,
        ticktext=df["model"],
        tickangle=-45,
        row=1,
        col=2,
    )
    fig.update_yaxes(title_text="Accuracy", row=1, col=1, range=[0, 1.05])
    fig.update_yaxes(title_text="Balanced accuracy", row=1, col=2, range=[0, 1.05])

    fig.update_layout(
        title_text="Porównanie modeli bazowych (9 wariantów) i zespołu Majority Voting — klasyfikacja",
        template="plotly_white",
        height=520,
        margin=dict(b=120),
    )
    return fig


def wykres_agregaty_rodzin(agg: pd.DataFrame) -> go.Figure:
    """
    Średnia vs maksimum metryk w obrębie trzech rodzin (DecisionTree, kNN, RandomForest).
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Średnia accuracy (3 warianty)",
            x=agg["rodzina"],
            y=agg["accuracy_srednia"],
            marker_color="#5C4D7D",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Maks. accuracy (3 warianty)",
            x=agg["rodzina"],
            y=agg["accuracy_max"],
            marker_color="#8F7EAF",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Średnia balanced acc.",
            x=agg["rodzina"],
            y=agg["balanced_accuracy_srednia"],
            marker_color="#C17C74",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Maks. balanced acc.",
            x=agg["rodzina"],
            y=agg["balanced_accuracy_max"],
            marker_color="#E8A09A",
        )
    )
    fig.update_layout(
        barmode="group",
        title="Agregacja po rodzinie modelu — średnie i maksima z trzech wariantów hiperparametrów",
        yaxis_title="Wartość metryki",
        template="plotly_white",
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def zapisz_wykresy_html(
    df_zbior: pd.DataFrame,
    szczegoly: pd.DataFrame,
    grupy: pd.DataFrame,
    katalog: Path,
) -> None:
    """
    Zapisuje wykresy jako samodzielne pliki HTML w katalogu results/wykresy/.
    """
    out = katalog / "wykresy"
    out.mkdir(parents=True, exist_ok=True)

    kol_num = [
        c
        for c in df_zbior.columns
        if c != "Id" and pd.api.types.is_numeric_dtype(df_zbior[c])
    ]
    if "quality" in kol_num:
        wykres_rozkald_jakosci(df_zbior).write_html(out / "01_rozkald_jakosci.html", include_plotlyjs="cdn")
    if len(kol_num) >= 2:
        wykres_macierz_korelacji(df_zbior, kol_num).write_html(out / "02_macierz_korelacji.html", include_plotlyjs="cdn")

    wykres_porownanie_metryk(szczegoly).write_html(out / "03_porownanie_modeli.html", include_plotlyjs="cdn")
    wykres_agregaty_rodzin(grupy).write_html(out / "04_agregaty_rodzin.html", include_plotlyjs="cdn")
