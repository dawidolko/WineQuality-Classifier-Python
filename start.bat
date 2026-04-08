@echo off
REM Uruchamia aplikacje Streamlit z katalogu projektu (Windows).
cd /d "%~dp0"

if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo === 1/2: Pelna ewaluacja: 5-fold CV, CSV, LaTeX, wykresy HTML ===
python run_experiment.py
if errorlevel 1 (
  echo Blad podczas eksperymentu — sprawdz komunikat powyzej.
  pause
  exit /b 1
)

echo.
echo === 2/2: Aplikacja Streamlit — http://localhost:8501 ===
streamlit run streamlit_app.py
