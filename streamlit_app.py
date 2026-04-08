#!/usr/bin/env python3
"""
Aplikacja Streamlit: checklista wymogów, EDA (wykresy), wyniki klasyfikacji, pobieranie plików.

Uruchomienie z katalogu projektu:
    streamlit run streamlit_app.py

Skrypty start.sh / start.bat najpierw uruchamiają run_experiment.py (pełne wyniki w results/).
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
    """Wyświetla zawartość pliku .tex w bloku kodu (czytelny podgląd w Streamlit)."""
    if not sciezka.is_file():
        st.caption(f"Brak pliku: `{sciezka.name}` — uruchom najpierw ewaluację.")
        return
    tresc = sciezka.read_text(encoding="utf-8")
    st.code(tresc, language="latex", line_numbers=True)


st.set_page_config(
    page_title="Wine Quality — klasyfikacja",
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

st.title("Klasyfikacja jakości wina (Wine Quality)")
st.caption(
    "Zadanie: **klasyfikacja wieloklasowa** — przewidywanie etykiety `quality` na podstawie cech chemicznych."
)

csv_szczegol = RESULTS_DIR / "wyniki_szczegolowe.csv"
csv_agregat = RESULTS_DIR / "wyniki_agregaty_rodzin.csv"
folder_wykresy = RESULTS_DIR / "wykresy"

with st.sidebar:
    st.header("Akcje")
    if st.button("Uruchom ponownie pełną ewaluację", type="primary", use_container_width=True):
        with st.spinner("Walidacja krzyżowa 5-fold, zapis CSV / LaTeX / wykresów…"):
            uruchom_pelny_eksperyment()
        st.success("Zapisano wyniki w katalogu `results/`.")
        st.rerun()
    st.markdown("---")
    st.markdown(
        "**Uruchomienie z terminala:** `python run_experiment.py`  \n"
        "**Start z GUI:** `./start.sh` lub `start.bat` — najpierw eksperyment, potem ta aplikacja."
    )
    st.markdown("---")
    st.markdown(
        "Pełny opis przebiegu badania, definicje pojęć, zgodność z wymaganiami oraz **podgląd plików `.tex`** — zakładka **Opis projektu**."
    )

tab_opis, tab_wymogi, tab_dane, tab_wyniki = st.tabs(
    ["Opis projektu", "Wymogi i metodologia", "Zbiór danych (EDA)", "Wyniki klasyfikacji"]
)

with tab_opis:
    st.info(
        "Poniżej: **cel badania**, **kolejne etapy obliczeń** (co robimy, dlaczego, jaki jest efekt), **definicje pojęć** "
        "oraz powiązanie z wymaganiami projektu. Szczegóły implementacji (moduły, funkcje) są w zakładce *Wymogi i metodologia*."
    )

    st.subheader("Cel i zakres porównania")
    st.markdown(
        """
Zbiór zawiera **próbki wina** opisane cechami numerycznymi (m.in. kwasowość, alkohol) oraz **znaną etykietę jakości**
`quality` (kilka dyskretnych klas, np. w zakresie od 3 do 8). Zadanie to **klasyfikacja wieloklasowa**: model na podstawie cech
ma przypisać obserwację do **jednej z klas** — nie estymujemy tu wartości ciągłej, tylko kategorię.

**Porównujemy** trzy rodziny algorytmów — **drzewo decyzyjne**, **kNN**, **las losowy** — każdy w **trzech wariantach hiperparametrów**
(łącznie **9** niezależnych klasyfikatorów w pipeline z `MinMaxScaler`). Dodatkowo badamy **zespół Majority Voting**:
dziewięć klasyfikatorów zwraca każdy swoją klasę; wynik zespołu to **klasa z największą liczbą głosów** (`voting="hard"`).
"""
    )

    st.subheader("Słownik pojęć")
    with st.expander("Rozwiń tabelę definicji", expanded=True):
        st.markdown(
            """
| Pojęcie | Znaczenie |
|--------|-----------|
| **Klasyfikacja** | Przypisanie obserwacji do jednej z **dyskretnych klas** (tu: wartość `quality`). |
| **Cecha (wejście)** | Zmienna opisująca wino (np. alkohol); stanowi wektor **X** używany do uczenia i predykcji. |
| **Etykieta / klasa (wyjście)** | Kolumna `quality` — wartość, której model ma się nauczyć przewidywać. |
| **Model** | Funkcja uczona na danych: **cechy → przewidywana klasa**; różne algorytmy mają inną strukturę decyzji. |
| **Hiperparametry** | Parametry ustawiane przed uczeniem (np. `max_depth`, `n_neighbors`); w projekcie **3 warianty na algorytm**. |
| **Walidacja 5-fold** | Pięć podziałów train/test; model oceniamy na części danych **niewykorzystanej do treningu** w danej iteracji. |
| **Stratyfikacja** | W train i test zachowujemy **proporcje klas** zbliżone do całego zbioru — stabilniejsza ocena przy niezbalansowaniu. |
| **Pipeline ze skalowaniem** | `MinMaxScaler` i klasyfikator w jednym obiekcie: skaler **dopasowuje się tylko do treningu** danej foldy. |
| **Przeciek danych** | Wykorzystanie informacji z części testowej przy przygotowaniu cech — **zawyża** metryki; pipeline + CV temu zapobiega. |
| **Majority Voting** | Agregacja głosów 9 klasyfikatorów; wygrywa klasa z **większością** oddanych głosów. |
| **Accuracy** | Ułamek próbek, w których **przewidywana klasa = rzeczywista** (globalna trafność). |
| **Balanced accuracy** | Średnia czułości po klasach — **mniej myląca**, gdy klasy mają bardzo różne liczebności. |
| **Średnia / odchylenie (`mean` / `std`)** | Po 5 foldach: **średnia metryki** oraz **rozrzut** między foldami (miara stabilności). |
"""
        )

    st.subheader("Komponenty repozytorium — co robią i po co są")
    st.markdown(
        """
| Element | Funkcja | Wynik / zapis |
|--------|---------|----------------|
| **`data/WineQT.csv`** | Dane źródłowe: cechy + etykieta `quality`. | Wejście do `run_experiment.py` i zakładki EDA. |
| **`run_experiment.py` / przycisk ewaluacji** | Uruchamia pełny pipeline obliczeń od zera. | Katalog `results/` uzupełniony o CSV, TeX, HTML, `wersje_bibliotek.txt`. |
| **`src/experiment.py`** | Wczytanie, pipeline (skaler + klasyfikator), CV, zespół, `to_latex`. | Tabele numeryczne i pliki `.tex`. |
| **`src/wykresy.py`** | Wykresy Plotly + eksport HTML. | `results/wykresy/*.html`. |
| **`wyniki_szczegolowe.*`** | Jedna tabela na wszystkie warianty + zespół. | Metryki `mean`/`std` per model. |
| **`wyniki_agregaty_rodzin.*`** | Agregacja po rodzinie algorytmu (3 warianty → statystyki). | Średnia i maksimum metryk w obrębie DT / kNN / RF. |
| **`wersje_bibliotek.txt`** | Zapis wersji bibliotek w momencie generowania wyników. | Ułatwia odtworzenie zbliżonych rezultatów w innym środowisku. |
"""
    )

    st.subheader("Przebieg eksperymentu — kolejne kroki")
    st.markdown(
        """
1. **Wczytanie CSV** — **Cel:** załadować macierz cech i etykiety. **Efekt:** obiekt danych w pamięci. Kolumna `Id` jest pomijana w uczeniu (identyfikator wiersza).

2. **Kontrola braków** — **Cel:** upewnić się, że żadna cecha ani `quality` nie jest pusta. **Efekt:** kontynuacja albo przerwanie z komunikatem (bez treningu na uszkodzonych danych).

3. **Rozdzielenie X i y** — **Cel:** rozdzielić wejście modelu od zmiennej objaśnianej. **Efekt:** macierz cech `X`, wektor klas `y`.

4. **Pipeline + CV** — **Cel:** dla każdej z 5 foldów dopasować skaler **tylko na treningu**, potem ocenić klasyfikator na teście. **Efekt:** uczciwa miara bez przecieku; pięć par wyników metryk na wariant.

5. **Uśrednienie po foldach** — **Cel:** zredukować zależność wyniku od jednego losowego podziału. **Efekt:** `accuracy_mean`, `accuracy_std` (i analogicznie dla balanced accuracy).

6. **Dziewięć wariantów bazowych** — **Cel:** porównać algorytmy i wpływ hiperparametrów. **Efekt:** wiersze w tabeli szczegółowej dla `dt_*`, `knn_*`, `rf_*`.

7. **Zespół VotingClassifier** — **Cel:** połączyć głosy 9 klasyfikatorów większością. **Efekt:** wiersz `majority_voting_9` w tabeli wyników.

8. **Agregacja Pandas po rodzinie** — **Cel:** podsumować „typową” i „najlepszą” skuteczność w obrębie DT, kNN, RF. **Efekt:** plik agregatów.

9. **Eksport** — **Cel:** zapis do raportu i dalszej obróbki. **Efekt:** CSV, LaTeX, HTML w `results/`.
"""
    )

    st.subheader("Charakterystyka porównywanych algorytmów")
    st.markdown(
        """
| Algorytm | Idea działania | Uwaga merytoryczna |
|----------|----------------|---------------------|
| **Decision Tree** | Reguły warunkowe w postaci drzewa (progi na cechach). | Pojedyncze drzewo bywa wrażliwe na szum; warianty różnią m.in. głębokością. |
| **kNN** | Klasa z **k** najbliższych obserwacji w przestrzeni cech (po skalowaniu). | Wrażliwy na skalę zmiennych — stąd `MinMaxScaler` w pipeline. |
| **Random Forest** | Zbiór drzew uczonych na losowych podzbiorach; agregacja wewnątrz modelu. | Zwykle mniejsza wariancja niż pojedyncze drzewo przy podobnym zadaniu. |
| **Majority Voting (9 klasyfikatorów)** | Zewnętrzna agregacja: głos większości między **różnymi** pipeline’ami. | Wynik zespołu należy interpretować obok najlepszych wariantów pojedynczych — nie zawsze jest wyższy. |
"""
    )

    st.subheader("Zakładki aplikacji")
    st.markdown(
        """
| Zakładka | Zawartość |
|----------|-----------|
| **Opis projektu** | Przebieg badania, definicje, zgodność z wymaganiami, **podgląd `.tex`**. |
| **Wymogi i metodologia** | Tabela odniesień: wymaganie → plik / mechanizm w kodzie. |
| **Zbiór danych (EDA)** | Rozkład `quality`, macierz korelacji, podgląd tabeli. |
| **Wyniki klasyfikacji** | Wykresy metryk z CV, tabele liczb, podgląd i pobranie plików wynikowych. |
"""
    )

    st.subheader("Zgodność z wymaganiami projektu")
    st.success(
        "Poniżej skrót checklisty; szczegóły techniczne i odwołania do kodu: zakładka *Wymogi i metodologia*."
    )
    st.markdown(
        """
- **Zbiór inny niż Iris** — Wine Quality (`data/WineQT.csv`).
- **Braki w danych** — weryfikacja przed modelem; brak wartości blokuje eksperyment.
- **Brak przecieku** — skalowanie w pipeline dopasowywane per fold na treningu.
- **Odtwarzalność** — `RANDOM_STATE`, ten sam obiekt CV, seed w modelach losowych.
- **MinMaxScaler** — w pipeline, nie na całym zbiorze przed podziałem na foldy.
- **Stratyfikowany 5-fold CV** — zachowane proporcje klas między train a test w każdej iteracji.
- **3 × 3 modele** — Decision Tree, kNN, Random Forest × 3 hiperparametry każdy.
- **Majority voting** — `VotingClassifier` nad 9 estymatorami.
- **Metryki** — `accuracy`, `balanced_accuracy`.
- **Pandas** — agregaty rodzin, eksport `to_latex`.
"""
    )

    st.subheader("Interpretacja metryk w tabelach")
    st.markdown(
        """
- **Accuracy** — ułamek poprawnie sklasyfikowanych próbek (**przewidywana klasa = rzeczywista**). Przy silnym niezbalansowaniu klas sama accuracy może być optymistyczna względem rzadkich klas.
- **Balanced accuracy** — pośrednia po klasach (średnia czułości); **lepiej odzwierciedla** sytuację, gdy klasy mają bardzo różne liczebności.
- **`mean`** — średnia metryki z **5 foldów** (punkt odniesienia dla porównań).
- **`std`** — odchylenie standardowe między foldami (**większe** = większa zmienność wyniku przy zmianie podziału).
"""
    )

    st.subheader("Interpretacja wykresów")
    st.markdown(
        """
- **Rozkład `quality`** — rozkład liczebności klas; pozwala ocenić **niezbalansowanie** zbioru (wpływa na obie metryki).
- **Macierz korelacji** — współzmienność cech (Pearson); **eksploracja**, nie wprowadza informacji testowej do skalowania (skalowanie jest w pipeline na treningu).
- **Porównanie metryk (2 panele)** — średnia z CV; **paski błędu** = `std` między foldami. Oś X: identyfikatory wariantów i zespół.
- **Agregaty rodzin** — w obrębie DT, kNN, RF: **średnia** i **maksimum** wybranej metryki spośród trzech wariantów hiperparametrów.
"""
    )

    st.subheader("Pliki LaTeX — podgląd treści")
    st.markdown(
        """
Poniżej widać **dokładny tekst** plików wygenerowanych przez program (do wklejenia do pracy w LaTeX).
W preambule dokumentu przydaje się m.in. `\\usepackage{booktabs}` (dla `\\toprule`, `\\midrule`, `\\bottomrule`).
Pliki można też pobrać w zakładce **Wyniki klasyfikacji**.
"""
    )
    st.markdown("##### `wyniki_szczegolowe.tex` — wszystkie warianty i zespół")
    wyswietl_plik_tex(TEX_SZCZEGOLY)
    st.markdown("##### `wyniki_agregaty_rodzin.tex` — średnie i maksima w rodzinach modeli")
    wyswietl_plik_tex(TEX_AGREGATY)

with tab_wymogi:
    st.subheader("Spełnienie wymagań projektu (klasyfikacja)")
    st.caption(
        "Tabela odniesień **wymaganie → implementacja** (moduły, klasy, pliki). Ogólny opis celu i przebiegu: zakładka **Opis projektu**."
    )
    st.markdown(
        """
| Wymóg | Realizacja w tym repozytorium |
|--------|-------------------------------|
| Jeden zbiór (nie Iris) | **Wine Quality** — `data/WineQT.csv` (Kaggle) |
| Sprawdzenie braków | `isna()` przy wczytaniu; brak → wyjątek |
| Brak przecieku danych | `MinMaxScaler` w `Pipeline` / `ColumnTransformer` — dopasowanie tylko na zbiorze treningowym każdej foldy |
| Odtwarzalność | `RANDOM_STATE` w `src/config.py`; ten sam obiekt `StratifiedKFold`; seed w modelach losowych |
| Skalowanie | **MinMaxScaler** (w pipeline, nie na całym zbiorze przed CV) |
| Walidacja | **Stratyfikowana 5-fold** cross-validation |
| Modele bazowe | **DecisionTree**, **kNN**, **RandomForest** — **po 3 warianty hiperparametrów** (łącznie 9) |
| Zespół | **Majority voting** — `VotingClassifier(..., voting="hard")` nad 9 pipeline’ami |
| Metryki | **accuracy**, **balanced_accuracy** |
| Pandas | Agregacja średnich/maksimum po rodzinie modelu; `DataFrame.to_latex()` → pliki `.tex` |
"""
    )
    st.info(
        "Szczegóły implementacji: moduł `src/experiment.py` (Pipeline, CV, zespół), "
        "`src/wykresy.py` (wykresy Plotly)."
    )

with tab_dane:
    st.subheader("Eksploracja zbioru")
    try:
        df_raw = wczytaj_pelna_ramke(DATA_PATH)
    except FileNotFoundError:
        st.error(f"Brak pliku: {DATA_PATH}")
        st.stop()
    except ValueError as e:
        st.error(str(e))
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Liczba wierszy", str(len(df_raw)))
    c2.metric("Liczba cech (bez Id)", len([c for c in df_raw.columns if c not in ("Id", "quality")]))
    c3.metric("Klasy jakości (min–max)", f"{int(df_raw['quality'].min())} – {int(df_raw['quality'].max())}")
    c4.metric("Brakujące wartości", "0" if not df_raw.isna().any().any() else "tak — sprawdź dane")

    st.plotly_chart(wykres_rozkald_jakosci(df_raw), use_container_width=True)

    kol_num = [
        c
        for c in df_raw.columns
        if c != "Id" and pd.api.types.is_numeric_dtype(df_raw[c])
    ]
    st.plotly_chart(wykres_macierz_korelacji(df_raw, kol_num), use_container_width=True)

    with st.expander("Podgląd pierwszych wierszy"):
        st.dataframe(df_raw.head(15), use_container_width=True)

with tab_wyniki:
    if not csv_szczegol.is_file() or not csv_agregat.is_file():
        st.warning(
            "Brak gotowych wyników w `results/`. Użyj przycisku w panelu bocznym lub uruchom: `python run_experiment.py`."
        )
    else:
        df = pd.read_csv(csv_szczegol)
        agg = pd.read_csv(csv_agregat)

        st.subheader("Porównanie modeli (CV)")
        st.plotly_chart(wykres_porownanie_metryk(df), use_container_width=True)
        st.plotly_chart(wykres_agregaty_rodzin(agg), use_container_width=True)

        st.subheader("Tabele numeryczne")
        st.markdown("**Wszystkie warianty + zespół Majority Voting (średnia i std z 5 foldów)**")
        st.dataframe(df.round(4), use_container_width=True)
        st.markdown("**Średnie i maksymalne metryki w obrębie rodziny (3 warianty hiperparametrów)**")
        st.dataframe(agg.round(4), use_container_width=True)

        st.subheader("Pliki LaTeX — podgląd i pobranie")
        st.markdown("Ten sam podgląd plików `.tex` znajduje się w zakładce **Opis projektu**.")
        with st.expander("Pokaż treść `wyniki_szczegolowe.tex`", expanded=False):
            wyswietl_plik_tex(TEX_SZCZEGOLY)
        with st.expander("Pokaż treść `wyniki_agregaty_rodzin.tex`", expanded=False):
            wyswietl_plik_tex(TEX_AGREGATY)

        st.subheader("Pobieranie plików z `results/`")
        cols = st.columns(3)
        meta = RESULTS_DIR / "wersje_bibliotek.txt"

        if TEX_SZCZEGOLY.is_file():
            cols[0].download_button(
                "Pobierz wyniki_szczegolowe.tex",
                data=TEX_SZCZEGOLY.read_text(encoding="utf-8"),
                file_name="wyniki_szczegolowe.tex",
                mime="text/plain",
                key="dl1",
            )
        if TEX_AGREGATY.is_file():
            cols[1].download_button(
                "Pobierz wyniki_agregaty_rodzin.tex",
                data=TEX_AGREGATY.read_text(encoding="utf-8"),
                file_name="wyniki_agregaty_rodzin.tex",
                mime="text/plain",
                key="dl2",
            )
        if meta.is_file():
            cols[2].download_button(
                "Pobierz wersje_bibliotek.txt",
                data=meta.read_text(encoding="utf-8"),
                file_name="wersje_bibliotek.txt",
                mime="text/plain",
                key="dl3",
            )

        if folder_wykresy.is_dir():
            htmls = sorted(folder_wykresy.glob("*.html"))
            st.markdown("**Wykresy zapisane jako HTML** (generowane przy `run_experiment.py`):")
            for h in htmls:
                st.caption(f"`{h.relative_to(RESULTS_DIR.parent)}`")
