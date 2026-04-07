@echo off
echo Iniciando Sistema Nutricional...

:: Nos posicionamos en la carpeta donde está este archivo .bat
cd /d "%~dp0"

:: Activamos el entorno virtual
call venv\Scripts\activate

:: Ejecutamos streamlit desde esta misma carpeta
streamlit run app.py

pause
