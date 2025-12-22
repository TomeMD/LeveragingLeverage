#!/usr/bin/env bash
PROJECT_DIR=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")

export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}"

streamlit run "${PROJECT_DIR}/src/streamlit_app.py"