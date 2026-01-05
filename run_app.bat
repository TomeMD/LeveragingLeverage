@echo off

:: Activar el entorno virtual
call my_venv\Scripts\activate.bat

:: Añadir el directorio src al PYTHONPATH
set PYTHONPATH=%cd%;%PYTHONPATH%

:: Iniciar la aplicación Streamlit
streamlit run src\streamlit_app.py
