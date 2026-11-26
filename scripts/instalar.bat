@echo off
setlocal
cd /d "%~dp0\.."
echo.
echo MEETINGSPLIT 0.8.10 - Preparar entorno local de desarrollo
where py >NUL 2>NUL
if errorlevel 1 (
  echo Se requiere el lanzador Python y Python 3.14.10 x64.
  exit /b 1
)
py -3.14 -c "import sys,struct;sys.exit(0 if sys.version_info[:3]==(3,14,10) and struct.calcsize('P')==8 else 1)"
if errorlevel 1 (
  echo ERROR: se requiere Python 3.14.10 x64 exacto para este candidato.
  exit /b 1
)
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe qa\check_build_runtime.py
  if errorlevel 1 (
    echo ERROR: entorno anterior. Conserva .venv como respaldo y crea otro entorno.
    exit /b 1
  )
) else (
  py -3.14 -m venv .venv
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe qa\check_build_runtime.py
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install --upgrade pip==26.3
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m pip check
if errorlevel 1 exit /b 1
echo.
echo ATENCION: preparar FFmpeg LGPL y PyAV mediante scripts\prepare_lgpl_media.ps1 antes de empaquetar.
echo La descarga inicial de un modelo Whisper requiere acceso a Internet.
exit /b 0
