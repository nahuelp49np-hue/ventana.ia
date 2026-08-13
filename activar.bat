@echo off
title ventana.ia
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Falta el entorno. Instala Python 3.12 y corre: python -m venv .venv
  echo Despues: .venv\Scripts\pip install -r requirements.txt
  pause
  exit /b 1
)
echo.
echo  SYS.VENTANA  ·  ventana.ia
echo  http://127.0.0.1:5202
echo.
".venv\Scripts\python.exe" run.py
pause
