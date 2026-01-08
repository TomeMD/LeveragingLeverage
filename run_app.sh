#!/usr/bin/env bash
PROJECT_DIR=$(dirname -- "$(readlink -f -- "${BASH_SOURCE}")")

# Create virtual environment
python -m venv my_venv

# Activate virtual environment
source my_venv/bin/activate

# Install requirements on virtual environment
pip install -r requirements.txt

# Add source directory to PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

# Start application
streamlit run "${PROJECT_DIR}/src/streamlit_app.py"