# Klasyfikacja jakości wina — porównanie modeli

## Krótki opis

- **Zbiór:** [Wine Quality](https://www.kaggle.com/datasets/yasserh/wine-quality-dataset) (`data/WineQT.csv`) — **klasyfikacja wieloklasowa** etykiety `quality` (np. oceny 3–8).
- **Modele:** `DecisionTree`, `kNN`, `RandomForest` — **po 3 warianty hiperparametrów** (łącznie 9 klasyfikatorów).
- **Zespół:** `VotingClassifier` z **majority voting** (`voting="hard"`) nad tymi samymi 9 pipeline’ami (MinMaxScaler + klasyfikator).
- **Bez przecieku:** `MinMaxScaler` w `Pipeline` / `ColumnTransformer`, dopasowanie wyłącznie na treningu każdej foldy.
- **Walidacja:** stratyfikowana **5-fold** CV (`StratifiedKFold`, stały `random_state`).
- **Metryki:** `accuracy`, `balanced_accuracy`.
- **Stack:** scikit-learn, Pandas (`groupby`, `to_latex`), Plotly (wykresy), Streamlit (opis przebiegu badania, definicje pojęć, zgodność z wymaganiami, podgląd `.tex`).

## Wymagania

- Python 3.10+ (zalecane)
- Instalacja: `pip install -r requirements.txt`

## Eksperyment (zapis do `results/`)

Uruchamia walidację, zapisuje m.in. CSV, `.tex`, `wersje_bibliotek.txt` oraz wykresy HTML w `results/wykresy/`.

```bash
python run_experiment.py
```

## Streamlit i skrypty startowe

Skrypty **`start.sh`** (Linux/macOS) oraz **`start.bat`** (Windows) wykonują po kolei:

1. venv + `pip install -r requirements.txt`
2. `python run_experiment.py`
3. `streamlit run streamlit_app.py` → zwykle `http://localhost:8501`

```bash
chmod +x start.sh
./start.sh
```

```cmd
start.bat
```

### Zakładki aplikacji

| Zakładka | Treść |
|----------|--------|
| **Opis projektu** | Cel badania, przebieg eksperymentu (co → po co → efekt), słownik pojęć, zgodność z wymaganiami, **podgląd plików LaTeX** |
| **Wymogi i metodologia** | Tabela: wymaganie → realizacja w kodzie / plikach |
| **Zbiór danych (EDA)** | Rozkład klasy `quality`, macierz korelacji, podgląd danych |
| **Wyniki klasyfikacji** | Wykresy metryk z CV, tabele, podgląd i pobieranie wyników |

## Odtwarzalność

- Seed: `RANDOM_STATE` w `src/config.py`; ten sam obiekt `cv` w `cross_validate` ([Common pitfalls — scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html)).
- Plik `results/wersje_bibliotek.txt` zapisuje wersje bibliotek użytych przy generowaniu wyników.

## Struktura repozytorium

| Ścieżka | Opis |
|---------|------|
| `data/WineQT.csv` | Dane źródłowe |
| `src/config.py` | Ścieżki, seed |
| `src/experiment.py` | Pipeline, CV, zespół, eksport CSV/LaTeX, wywołanie wykresów |
| `src/wykresy.py` | Wykresy Plotly + zapis HTML |
| `run_experiment.py` | Wejście z linii poleceń |
| `streamlit_app.py` | Aplikacja WWW |
| `start.sh` / `start.bat` | Eksperyment + Streamlit |
| `results/` | Wyniki wygenerowane (CSV, TeX, `wykresy/*.html`, `wersje_bibliotek.txt`) |

## `.gitignore`

Ignorowane są m.in. `.venv/`, cache Pythona, pliki IDE. **Wygenerowane pliki w `results/`** można opcjonalnie dodać do ignorowania — w `.gitignore` jest gotowy, zakomentowany blok instrukcji.

## Licencja

Zobacz plik `LICENSE`.
