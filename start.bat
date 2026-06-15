@echo off
REM Runs the Streamlit app from the project directory (Windows).
cd /d "%~dp0"

if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo === 1/2: Full evaluation: 5-fold CV, CSV, LaTeX, HTML charts ===
python run_experiment.py
if errorlevel 1 (
  echo Error during the experiment - check the message above.
  pause
  exit /b 1
)

echo.
echo === 2/2: Streamlit app — http://localhost:8501 ===
streamlit run streamlit_app.py
