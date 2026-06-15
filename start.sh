#!/usr/bin/env bash
# Runs the Streamlit app from the project directory (Unix/macOS).
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "=== 1/2: Full evaluation (5-fold CV, CSV, LaTeX, HTML charts) ==="
python run_experiment.py

echo ""
echo "=== 2/2: Streamlit app — http://localhost:8501 ==="
exec streamlit run streamlit_app.py
