#!/usr/bin/env python3
"""
Streamlit app: requirements checklist, EDA (charts), classification results, file downloads.

Run from the project directory:
    streamlit run streamlit_app.py

The start.sh / start.bat scripts first run run_experiment.py (full results in results/).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from src.config import DATA_PATH, RESULTS_DIR
from src.experiment import uruchom_pelny_eksperyment, wczytaj_pelna_ramke
from src.wykresy import (
    wykres_agregaty_rodzin,
    wykres_macierz_korelacji,
    wykres_porownanie_metryk,
    wykres_rozkald_jakosci,
)

TEX_SZCZEGOLY = RESULTS_DIR / "wyniki_szczegolowe.tex"
TEX_AGREGATY = RESULTS_DIR / "wyniki_agregaty_rodzin.tex"


def wyswietl_plik_tex(sciezka: Path) -> None:
    """Displays the contents of a .tex file in a code block (readable preview in Streamlit)."""
    if not sciezka.is_file():
        st.caption(f"Missing file: `{sciezka.name}` — run the evaluation first.")
        return
    tresc = sciezka.read_text(encoding="utf-8")
    st.code(tresc, language="latex", line_numbers=True)


st.set_page_config(
    page_title="Wine Quality — classification",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.block-container { padding-top: 1.2rem; }
div[data-testid="stMetricValue"] { font-size: 1.35rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("Wine Quality Classification")
st.caption(
    "Task: **multiclass classification** — predicting the `quality` label from chemical features."
)

csv_szczegol = RESULTS_DIR / "wyniki_szczegolowe.csv"
csv_agregat = RESULTS_DIR / "wyniki_agregaty_rodzin.csv"
folder_wykresy = RESULTS_DIR / "wykresy"

with st.sidebar:
    st.header("Actions")
    if st.button("Re-run full evaluation", type="primary", use_container_width=True):
        with st.spinner("5-fold cross-validation, saving CSV / LaTeX / charts…"):
            uruchom_pelny_eksperyment()
        st.success("Results saved to the `results/` directory.")
        st.rerun()
    st.markdown("---")
    st.markdown(
        "**Run from the terminal:** `python run_experiment.py`  \n"
        "**Start from GUI:** `./start.sh` or `start.bat` — the experiment first, then this app."
    )
    st.markdown("---")
    st.markdown(
        "Full description of the study, definitions of terms, requirements compliance, and a **preview of the `.tex` files** — see the **Project description** tab."
    )

tab_opis, tab_wymogi, tab_dane, tab_wyniki = st.tabs(
    ["Project description", "Requirements & methodology", "Dataset (EDA)", "Classification results"]
)

with tab_opis:
    st.info(
        "Below: the **goal of the study**, the **successive computation stages** (what we do, why, and the effect), **definitions of terms** "
        "and the link to the project requirements. Implementation details (modules, functions) are in the *Requirements & methodology* tab."
    )

    st.subheader("Goal and scope of the comparison")
    st.markdown(
        """
The dataset contains **wine samples** described by numeric features (e.g. acidity, alcohol) and a **known quality label**
`quality` (a few discrete classes, e.g. ranging from 3 to 8). The task is **multiclass classification**: based on the features the model
assigns an observation to **one of the classes** — we are not estimating a continuous value here, only a category.

**We compare** three algorithm families — **decision tree**, **kNN**, **random forest** — each in **three hyperparameter variants**
(9 independent classifiers in total, each in a pipeline with `MinMaxScaler`). We additionally study a **Majority Voting ensemble**:
the nine classifiers each return their class; the ensemble result is the **class with the most votes** (`voting="hard"`).
"""
    )

    st.subheader("Glossary of terms")
    with st.expander("Expand the definitions table", expanded=True):
        st.markdown(
            """
| Term | Meaning |
|--------|-----------|
| **Classification** | Assigning an observation to one of the **discrete classes** (here: the `quality` value). |
| **Feature (input)** | A variable describing the wine (e.g. alcohol); forms the **X** vector used for training and prediction. |
| **Label / class (output)** | The `quality` column — the value the model is meant to learn to predict. |
| **Model** | A function trained on the data: **features → predicted class**; different algorithms have different decision structures. |
| **Hyperparameters** | Parameters set before training (e.g. `max_depth`, `n_neighbors`); in this project, **3 variants per algorithm**. |
| **5-fold validation** | Five train/test splits; the model is evaluated on the portion of data **not used for training** in a given iteration. |
| **Stratification** | In train and test we keep the **class proportions** close to the whole dataset — a more stable evaluation under imbalance. |
| **Pipeline with scaling** | `MinMaxScaler` and the classifier in a single object: the scaler **fits only on the training portion** of a given fold. |
| **Data leakage** | Using information from the test portion when preparing features — it **inflates** the metrics; the pipeline + CV prevent this. |
| **Majority Voting** | Aggregation of votes from 9 classifiers; the class with the **majority** of votes wins. |
| **Accuracy** | The fraction of samples where the **predicted class = the true class** (global correctness). |
| **Balanced accuracy** | Mean per-class recall — **less misleading** when classes have very different sizes. |
| **Mean / std (`mean` / `std`)** | Across the 5 folds: the **mean of the metric** and the **spread** between folds (a stability measure). |
"""
        )

    st.subheader("Repository components — what they do and why")
    st.markdown(
        """
| Element | Function | Result / output |
|--------|---------|----------------|
| **`data/WineQT.csv`** | Source data: features + the `quality` label. | Input to `run_experiment.py` and the EDA tab. |
| **`run_experiment.py` / the evaluation button** | Runs the full computation pipeline from scratch. | The `results/` directory filled with CSV, TeX, HTML, `wersje_bibliotek.txt`. |
| **`src/experiment.py`** | Loading, the pipeline (scaler + classifier), CV, ensemble, `to_latex`. | Numeric tables and `.tex` files. |
| **`src/wykresy.py`** | Plotly charts + HTML export. | `results/wykresy/*.html`. |
| **`wyniki_szczegolowe.*`** | A single table for all variants + the ensemble. | `mean`/`std` metrics per model. |
| **`wyniki_agregaty_rodzin.*`** | Aggregation by algorithm family (3 variants → statistics). | Mean and maximum metrics within DT / kNN / RF. |
| **`wersje_bibliotek.txt`** | Records the library versions at the moment results are generated. | Makes it easier to reproduce similar results in another environment. |
"""
    )

    st.subheader("Experiment flow — successive steps")
    st.markdown(
        """
1. **Load the CSV** — **Goal:** load the feature matrix and labels. **Effect:** a data object in memory. The `Id` column is ignored during training (it is a row identifier).

2. **Missing-value check** — **Goal:** ensure that no feature nor `quality` is empty. **Effect:** either continue or stop with a message (no training on corrupted data).

3. **Split X and y** — **Goal:** separate the model input from the target variable. **Effect:** the feature matrix `X` and the class vector `y`.

4. **Pipeline + CV** — **Goal:** for each of the 5 folds fit the scaler **on the training portion only**, then evaluate the classifier on the test portion. **Effect:** a fair, leakage-free measure; five pairs of metric results per variant.

5. **Averaging across folds** — **Goal:** reduce the dependence of the result on a single random split. **Effect:** `accuracy_mean`, `accuracy_std` (and analogously for balanced accuracy).

6. **Nine base variants** — **Goal:** compare algorithms and the effect of hyperparameters. **Effect:** rows in the detailed table for `dt_*`, `knn_*`, `rf_*`.

7. **VotingClassifier ensemble** — **Goal:** combine the votes of 9 classifiers by majority. **Effect:** the `majority_voting_9` row in the results table.

8. **Pandas aggregation by family** — **Goal:** summarise the “typical” and “best” performance within DT, kNN, RF. **Effect:** the aggregates file.

9. **Export** — **Goal:** save for the report and further processing. **Effect:** CSV, LaTeX, HTML in `results/`.
"""
    )

    st.subheader("Characteristics of the compared algorithms")
    st.markdown(
        """
| Algorithm | How it works | Substantive note |
|----------|----------------|---------------------|
| **Decision Tree** | Conditional rules in tree form (thresholds on features). | A single tree can be sensitive to noise; the variants differ e.g. in depth. |
| **kNN** | The class of the **k** nearest observations in feature space (after scaling). | Sensitive to variable scale — hence `MinMaxScaler` in the pipeline. |
| **Random Forest** | A set of trees trained on random subsets; aggregation inside the model. | Usually lower variance than a single tree on a similar task. |
| **Majority Voting (9 classifiers)** | External aggregation: majority vote across **different** pipelines. | The ensemble result should be interpreted alongside the best individual variants — it is not always higher. |
"""
    )

    st.subheader("Application tabs")
    st.markdown(
        """
| Tab | Content |
|----------|-----------|
| **Project description** | Study flow, definitions, requirements compliance, **`.tex` preview**. |
| **Requirements & methodology** | A reference table: requirement → file / mechanism in the code. |
| **Dataset (EDA)** | `quality` distribution, correlation matrix, table preview. |
| **Classification results** | Metric charts from CV, numeric tables, preview and download of result files. |
"""
    )

    st.subheader("Compliance with project requirements")
    st.success(
        "Below is a checklist summary; technical details and code references are in the *Requirements & methodology* tab."
    )
    st.markdown(
        """
- **Dataset other than Iris** — Wine Quality (`data/WineQT.csv`).
- **Missing data** — verified before modelling; missing values block the experiment.
- **No leakage** — scaling inside the pipeline, fitted per fold on the training portion.
- **Reproducibility** — `RANDOM_STATE`, the same CV object, seed in the randomized models.
- **MinMaxScaler** — inside the pipeline, not on the whole dataset before the fold split.
- **Stratified 5-fold CV** — class proportions preserved between train and test in each iteration.
- **3 × 3 models** — Decision Tree, kNN, Random Forest × 3 hyperparameters each.
- **Majority voting** — `VotingClassifier` over the 9 estimators.
- **Metrics** — `accuracy`, `balanced_accuracy`.
- **Pandas** — family aggregates, `to_latex` export.
"""
    )

    st.subheader("Interpreting the metrics in the tables")
    st.markdown(
        """
- **Accuracy** — the fraction of correctly classified samples (**predicted class = true class**). Under strong class imbalance, accuracy alone can be optimistic with respect to rare classes.
- **Balanced accuracy** — the average across classes (mean recall); **better reflects** the situation when classes have very different sizes.
- **`mean`** — the metric mean over the **5 folds** (a reference point for comparisons).
- **`std`** — the standard deviation between folds (**larger** = greater variability of the result when the split changes).
"""
    )

    st.subheader("Interpreting the charts")
    st.markdown(
        """
- **`quality` distribution** — the class count distribution; lets you assess the **imbalance** of the dataset (affects both metrics).
- **Correlation matrix** — feature co-variation (Pearson); **exploration**, it does not introduce test information into scaling (scaling happens in the pipeline on the training portion).
- **Metric comparison (2 panels)** — the CV mean; **error bars** = `std` between folds. X axis: variant identifiers and the ensemble.
- **Family aggregates** — within DT, kNN, RF: the **mean** and **maximum** of the chosen metric across the three hyperparameter variants.
"""
    )

    st.subheader("LaTeX files — content preview")
    st.markdown(
        """
Below you can see the **exact text** of the files generated by the program (to paste into a LaTeX document).
In the document preamble it helps to use e.g. `\\usepackage{booktabs}` (for `\\toprule`, `\\midrule`, `\\bottomrule`).
The files can also be downloaded in the **Classification results** tab.
"""
    )
    st.markdown("##### `wyniki_szczegolowe.tex` — all variants and the ensemble")
    wyswietl_plik_tex(TEX_SZCZEGOLY)
    st.markdown("##### `wyniki_agregaty_rodzin.tex` — means and maxima within model families")
    wyswietl_plik_tex(TEX_AGREGATY)

with tab_wymogi:
    st.subheader("Meeting the project requirements (classification)")
    st.caption(
        "A reference table **requirement → implementation** (modules, classes, files). General description of the goal and flow: the **Project description** tab."
    )
    st.markdown(
        """
| Requirement | Implementation in this repository |
|--------|-------------------------------|
| One dataset (not Iris) | **Wine Quality** — `data/WineQT.csv` (Kaggle) |
| Missing-value check | `isna()` on load; missing → exception |
| No data leakage | `MinMaxScaler` inside `Pipeline` / `ColumnTransformer` — fitted only on the training portion of each fold |
| Reproducibility | `RANDOM_STATE` in `src/config.py`; the same `StratifiedKFold` object; seed in the randomized models |
| Scaling | **MinMaxScaler** (in the pipeline, not on the whole dataset before CV) |
| Validation | **Stratified 5-fold** cross-validation |
| Base models | **DecisionTree**, **kNN**, **RandomForest** — **3 hyperparameter variants each** (9 in total) |
| Ensemble | **Majority voting** — `VotingClassifier(..., voting="hard")` over the 9 pipelines |
| Metrics | **accuracy**, **balanced_accuracy** |
| Pandas | Aggregation of means/maxima by model family; `DataFrame.to_latex()` → `.tex` files |
"""
    )
    st.info(
        "Implementation details: the `src/experiment.py` module (Pipeline, CV, ensemble), "
        "`src/wykresy.py` (Plotly charts)."
    )

with tab_dane:
    st.subheader("Dataset exploration")
    try:
        df_raw = wczytaj_pelna_ramke(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Missing file: {DATA_PATH}")
        st.stop()
    except ValueError as e:
        st.error(str(e))
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Number of rows", str(len(df_raw)))
    c2.metric("Number of features (without Id)", len([c for c in df_raw.columns if c not in ("Id", "quality")]))
    c3.metric("Quality classes (min–max)", f"{int(df_raw['quality'].min())} – {int(df_raw['quality'].max())}")
    c4.metric("Missing values", "0" if not df_raw.isna().any().any() else "yes — check the data")

    st.plotly_chart(wykres_rozkald_jakosci(df_raw), use_container_width=True)

    kol_num = [
        c
        for c in df_raw.columns
        if c != "Id" and pd.api.types.is_numeric_dtype(df_raw[c])
    ]
    st.plotly_chart(wykres_macierz_korelacji(df_raw, kol_num), use_container_width=True)

    with st.expander("Preview of the first rows"):
        st.dataframe(df_raw.head(15), use_container_width=True)

with tab_wyniki:
    if not csv_szczegol.is_file() or not csv_agregat.is_file():
        st.warning(
            "No ready results in `results/`. Use the button in the sidebar or run: `python run_experiment.py`."
        )
    else:
        df = pd.read_csv(csv_szczegol)
        agg = pd.read_csv(csv_agregat)

        st.subheader("Model comparison (CV)")
        st.plotly_chart(wykres_porownanie_metryk(df), use_container_width=True)
        st.plotly_chart(wykres_agregaty_rodzin(agg), use_container_width=True)

        st.subheader("Numeric tables")
        st.markdown("**All variants + the Majority Voting ensemble (mean and std over 5 folds)**")
        st.dataframe(df.round(4), use_container_width=True)
        st.markdown("**Mean and maximum metrics within a family (3 hyperparameter variants)**")
        st.dataframe(agg.round(4), use_container_width=True)

        st.subheader("LaTeX files — preview and download")
        st.markdown("The same `.tex` file preview is available in the **Project description** tab.")
        with st.expander("Show the content of `wyniki_szczegolowe.tex`", expanded=False):
            wyswietl_plik_tex(TEX_SZCZEGOLY)
        with st.expander("Show the content of `wyniki_agregaty_rodzin.tex`", expanded=False):
            wyswietl_plik_tex(TEX_AGREGATY)

        st.subheader("Download files from `results/`")
        cols = st.columns(3)
        meta = RESULTS_DIR / "wersje_bibliotek.txt"

        if TEX_SZCZEGOLY.is_file():
            cols[0].download_button(
                "Download wyniki_szczegolowe.tex",
                data=TEX_SZCZEGOLY.read_text(encoding="utf-8"),
                file_name="wyniki_szczegolowe.tex",
                mime="text/plain",
                key="dl1",
            )
        if TEX_AGREGATY.is_file():
            cols[1].download_button(
                "Download wyniki_agregaty_rodzin.tex",
                data=TEX_AGREGATY.read_text(encoding="utf-8"),
                file_name="wyniki_agregaty_rodzin.tex",
                mime="text/plain",
                key="dl2",
            )
        if meta.is_file():
            cols[2].download_button(
                "Download wersje_bibliotek.txt",
                data=meta.read_text(encoding="utf-8"),
                file_name="wersje_bibliotek.txt",
                mime="text/plain",
                key="dl3",
            )

        if folder_wykresy.is_dir():
            htmls = sorted(folder_wykresy.glob("*.html"))
            st.markdown("**Charts saved as HTML** (generated by `run_experiment.py`):")
            for h in htmls:
                st.caption(f"`{h.relative_to(RESULTS_DIR.parent)}`")
