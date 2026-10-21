@echo off
cd /d "%~dp0\.."
if not exist .venv\Scripts\pythonw.exe (
  echo Primero ejecuta scripts\instalar.bat
  pause
  exit /b 1
)
.venv\Scripts\pythonw.exe run.py
