# Wine Quality Classification — Model Comparison

## Short description

- **Dataset:** [Wine Quality](https://www.kaggle.com/datasets/yasserh/wine-quality-dataset) (`data/WineQT.csv`) — **multiclass classification** of the `quality` label (scores 3–8, imbalanced classes).
- **Models:** `DecisionTree`, `kNN`, `RandomForest` — **3 hyperparameter variants each** (9 classifiers in total).
- **Prediction ensemble:** `VotingClassifier` with **majority voting** (`voting="hard"`) over the same 9 pipelines.
- **Validation:** stratified **5-fold** CV (`StratifiedKFold(shuffle=True, random_state=42)`).
- **Metrics:** `accuracy` (the fraction of correct predictions) and `balanced_accuracy` (mean per-class recall — important given the imbalanced distribution of wine scores).
- **Stack:** scikit-learn, Pandas (`groupby`, `to_latex`), Plotly (charts), Streamlit (study walkthrough, term definitions, requirements compliance, `.tex` preview).

## Protection against data leakage

All scaling operations are performed **inside** a scikit-learn `Pipeline` object:

```
Pipeline([
    ("preprocess", ColumnTransformer([("num", MinMaxScaler(), feature_cols)])),
    ("clf", classifier),
])
```

Thanks to this, `MinMaxScaler` is **fitted exclusively on the training fold** — it never "sees" the test data before evaluation. Passing a ready `Pipeline` to `cross_validate` guarantees this automatically for each of the 5 splits. Details: [scikit-learn — Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).

## No missing data

The `wczytaj_pelna_ramke` function in `src/experiment.py` calls `df.isna().any().any()` and raises an exception if it finds missing values — the experiment will not run on an incomplete dataset.

## Requirements

- Python 3.10+ (recommended)
- Install: `pip install -r requirements.txt`

## Experiment (writes to `results/`)

Runs the validation and saves, among others, CSV, `.tex`, `wersje_bibliotek.txt` and HTML charts in `results/wykresy/`.

```bash
python run_experiment.py
```

## Streamlit and start scripts

The **`start.sh`** (Linux/macOS) and **`start.bat`** (Windows) scripts run, in order:

1. venv + `pip install -r requirements.txt`
2. `python run_experiment.py`
3. `streamlit run streamlit_app.py` → usually `http://localhost:8501`

```bash
chmod +x start.sh
./start.sh
```

```cmd
start.bat
```

### Application tabs

| Tab | Content |
|----------|--------|
| **Project description** | Study goal, experiment flow (what → why → effect), glossary of terms, requirements compliance, **LaTeX file preview** |
| **Requirements & methodology** | Table: requirement → implementation in code / files |
| **Dataset (EDA)** | `quality` class distribution, correlation matrix, data preview |
| **Classification results** | CV metric charts, tables, preview and download of results |

## Reproducibility

In line with the requirement [scikit-learn — Getting reproducible results](https://scikit-learn.org/stable/common_pitfalls.html):

- One fixed seed: `RANDOM_STATE = 42` in `src/config.py`; passed to every classifier (`random_state`) and to `StratifiedKFold(shuffle=True, random_state=RANDOM_STATE)`.
- `StratifiedKFold` with `shuffle=True` requires a seed — without it the sample order after shuffling would differ on every run.
- The same `cv` object is passed to each `cross_validate` call, which guarantees identical splits for all models.
- The `results/wersje_bibliotek.txt` file records the versions of scikit-learn, numpy and pandas when the results are generated — making it possible to reproduce the environment.

## Repository structure

| Path | Description |
|---------|------|
| `data/WineQT.csv` | Source data |
| `src/config.py` | Paths, seed |
| `src/experiment.py` | Pipeline, CV, ensemble, CSV/LaTeX export, chart invocation |
| `src/wykresy.py` | Plotly charts + HTML export |
| `run_experiment.py` | Command-line entry point |
| `streamlit_app.py` | Web application |
| `start.sh` / `start.bat` | Experiment + Streamlit |
| `results/` | Generated results (CSV, TeX, `wykresy/*.html`, `wersje_bibliotek.txt`) |

## `.gitignore`

Ignored items include `.venv/`, Python cache, and IDE files. **Generated files in `results/`** can optionally be added to the ignore list — `.gitignore` contains a ready, commented-out block with instructions.

## License

See the `LICENSE` file.
