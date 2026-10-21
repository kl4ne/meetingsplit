@echo off
setlocal
cd /d "%~dp0\.."
echo.
echo  MEETINGSPLIT 0.4 - Preparar entorno local de desarrollo
where py >NUL 2>NUL
if errorlevel 1 (
  echo Python Launcher no disponible. Se necesita Python 3.11 o 3.12 de 64 bits.
  pause
  exit /b 1
)
py -3.11 --version >NUL 2>NUL
if not errorlevel 1 (
  py -3.11 -m venv .venv
) else (
  py -3.12 --version >NUL 2>NUL
  if errorlevel 1 (
    echo No hay Python 3.11/3.12 disponible. No se instalaron paquetes.
    pause
    exit /b 1
  )
  py -3.12 -m venv .venv
)
if errorlevel 1 (
  echo No se pudo crear un entorno local Python.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo No se instalaron todas las dependencias; consulta la salida.
  pause
  exit /b 1
)
echo.
echo ATENCION: Debes contar con FFmpeg y FFprobe en bin\ o en el PATH.
echo La descarga inicial de un modelo Whisper requiere acceso a Internet.
echo.
pause
