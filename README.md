# Klasyfikacja jakości wina — porównanie modeli

## Krótki opis

- **Zbiór:** [Wine Quality](https://www.kaggle.com/datasets/yasserh/wine-quality-dataset) (`data/WineQT.csv`) — **klasyfikacja wieloklasowa** etykiety `quality` (oceny 3–8, niezbalansowane klasy).
- **Modele:** `DecisionTree`, `kNN`, `RandomForest` — **po 3 warianty hiperparametrów** (łącznie 9 klasyfikatorów).
- **Zespół predykcyjny:** `VotingClassifier` z **majority voting** (`voting="hard"`) nad tymi samymi 9 pipeline’ami.
- **Walidacja:** stratyfikowana **5-fold** CV (`StratifiedKFold(shuffle=True, random_state=42)`).
- **Metryki:** `accuracy` (odsetek poprawnych predykcji) oraz `balanced_accuracy` (średnia czułość po klasach — ważna przy niezbalansowanym rozkładzie ocen wina).
- **Stack:** scikit-learn, Pandas (`groupby`, `to_latex`), Plotly (wykresy), Streamlit (opis przebiegu badania, definicje pojęć, zgodność z wymaganiami, podgląd `.tex`).

## Zabezpieczenie przed przeciekiem danych (data leakage)

Wszystkie operacje skalowania wykonywane są **wewnątrz** obiektu `Pipeline` (scikit-learn):

```
Pipeline([
    ("preprocess", ColumnTransformer([("num", MinMaxScaler(), feature_cols)])),
    ("clf", klasyfikator),
])
```

Dzięki temu `MinMaxScaler` jest **fitowany wyłącznie na folddzie treningowej** — nigdy nie „widzi" danych testowych przed oceną. Przekazanie gotowego `Pipeline` do `cross_validate` gwarantuje to automatycznie dla każdego z 5 podziałów. Szczegóły: [scikit-learn — Common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).

## Brak brakujących danych

Funkcja `wczytaj_pelna_ramke` w `src/experiment.py` wywołuje `df.isna().any().any()` i podnosi wyjątek, jeśli znajdzie brakujące wartości — eksperyment nie uruchomi się na niekompletnym zbiorze.

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

## Odtwarzalność wyników (reproducibility)

Zgodnie z wymaganiem [scikit-learn — Getting reproducible results](https://scikit-learn.org/stable/common_pitfalls.html):

- Jeden stały seed: `RANDOM_STATE = 42` w `src/config.py`; przekazany do każdego klasyfikatora (`random_state`) oraz do `StratifiedKFold(shuffle=True, random_state=RANDOM_STATE)`.
- `StratifiedKFold` z `shuffle=True` wymaga seeda — bez niego kolejność próbek po tasowaniu byłaby inna przy każdym uruchomieniu.
- Ten sam obiekt `cv` przekazywany jest do każdego wywołania `cross_validate`, co gwarantuje identyczne podziały dla wszystkich modeli.
- Plik `results/wersje_bibliotek.txt` zapisuje wersje scikit-learn, numpy i pandas przy generowaniu wyników — umożliwia odtworzenie środowiska.

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
