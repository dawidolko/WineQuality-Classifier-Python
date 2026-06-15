"""
Plotly charts presenting the dataset and the cross-validation results.

Used in the Streamlit app and saved as HTML to the results/wykresy/ directory
after running the full experiment.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def wykres_rozkald_jakosci(df: pd.DataFrame, kolumna_jakosci: str = "quality") -> go.Figure:
    """
    Histogram / bar counts of wine quality classes (a multiclass classification task).
    """
    vc = df[kolumna_jakosci].value_counts().sort_index()
    fig = px.bar(
        x=vc.index.astype(str),
        y=vc.values,
        labels={"x": "Quality class (label)", "y": "Number of samples"},
        title="Distribution of the “quality” label in the dataset",
        color_discrete_sequence=["#2E86AB"],
    )
    fig.update_layout(
        xaxis_title="Quality (class)",
        yaxis_title="Number of observations",
        showlegend=False,
        template="plotly_white",
        height=420,
    )
    return fig


def wykres_macierz_korelacji(df: pd.DataFrame, kolumny_numeryczne: list[str]) -> go.Figure:
    """
    Heatmap of Pearson correlations between numeric features (including the label).
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
        title="Correlation matrix (numeric features)",
    )
    fig.update_layout(height=560, template="plotly_white")
    return fig


def _etykieta_wykresu(wiersz: pd.Series) -> str:
    rodz = str(wiersz.get("rodzina", ""))
    model = str(wiersz.get("model", ""))
    if rodz == "Ensemble":
        return "Ensemble (Majority Voting)"
    return f"{rodz}: {model}"


def wykres_porownanie_metryk(szczegoly: pd.DataFrame) -> go.Figure:
    """
    Bars: mean accuracy and balanced accuracy for every variant and the ensemble
    (error bars = std across folds).
    """
    df = szczegoly.copy()
    df["etykieta"] = df.apply(_etykieta_wykresu, axis=1)
    # Order: families grouped, ensemble last
    df["_sort"] = df["rodzina"].map(
        {"DecisionTree": 0, "kNN": 1, "RandomForest": 2, "Ensemble": 3}
    ).fillna(9)
    df = df.sort_values(["_sort", "model"])

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Accuracy (mean ± std over 5 folds)", "Balanced accuracy (mean ± std)"),
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
        title_text="Comparison of base models (9 variants) and the Majority Voting ensemble — classification",
        template="plotly_white",
        height=520,
        margin=dict(b=120),
    )
    return fig


def wykres_agregaty_rodzin(agg: pd.DataFrame) -> go.Figure:
    """
    Mean vs maximum of metrics within the three families (DecisionTree, kNN, RandomForest).
    """
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Mean accuracy (3 variants)",
            x=agg["rodzina"],
            y=agg["accuracy_srednia"],
            marker_color="#5C4D7D",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Max accuracy (3 variants)",
            x=agg["rodzina"],
            y=agg["accuracy_max"],
            marker_color="#8F7EAF",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Mean balanced acc.",
            x=agg["rodzina"],
            y=agg["balanced_accuracy_srednia"],
            marker_color="#C17C74",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Max balanced acc.",
            x=agg["rodzina"],
            y=agg["balanced_accuracy_max"],
            marker_color="#E8A09A",
        )
    )
    fig.update_layout(
        barmode="group",
        title="Aggregation by model family — means and maxima over three hyperparameter variants",
        yaxis_title="Metric value",
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
    Saves the charts as standalone HTML files in the results/wykresy/ directory.
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
