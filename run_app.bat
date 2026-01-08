@echo off

:: Create virtual environment
call python -m venv my_venv

:: Activate virtual environment
call my_venv\Scripts\activate.bat

:: Install requirements on virtual environment
call pip install -r requirements.txt

:: Add source directory to PYTHONPATH
set PYTHONPATH=%cd%;%PYTHONPATH%

:: Start application
streamlit run src\streamlit_app.py
