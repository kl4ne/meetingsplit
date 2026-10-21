@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
set "RELEASE=0.8.5"
echo.
echo ========= MeetingSplit %RELEASE% - Windows Build =========
if not exist .venv\Scripts\python.exe (
 echo ERROR: prepara Python 3.11 con scripts\instalar.bat antes de compilar.
 exit /b 1
)
if not exist bin\ffmpeg.exe (
 echo ERROR: no se encontro bin\ffmpeg.exe. No se permite un ejecutable incompleto.
 exit /b 1
)
if not exist bin\ffprobe.exe (
 echo ERROR: no se encontro bin\ffprobe.exe. No se permite un ejecutable incompleto.
 exit /b 1
)
.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_ui_language.py --ignore=tests/test_ui_navigation.py
if errorlevel 1 (
 echo ERROR: las pruebas de motor no pasaron. Se suspende la compilacion.
 exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onedir --windowed ^
 --name MeetingSplit --icon "assets\meetingsplit.ico" ^
 --add-data "ui;ui" ^
 --add-binary "bin\ffmpeg.exe;bin" --add-binary "bin\ffprobe.exe;bin" ^
 --collect-all faster_whisper --collect-all ctranslate2 --collect-all PySide6.QtWebEngineWidgets ^
 --hidden-import PySide6.QtWebEngineCore --hidden-import PySide6.QtWebChannel ^
 run.py
if errorlevel 1 (
 echo ERROR: fallo PyInstaller. No se genero instalador.
 exit /b 1
)
if not exist dist\MeetingSplit\MeetingSplit.exe (
 echo ERROR: falta dist\MeetingSplit\MeetingSplit.exe.
 exit /b 1
)
set "CHECK=%TEMP%\meetingsplit-build-check-%RANDOM%.json"
start /wait "" "dist\MeetingSplit\MeetingSplit.exe" --self-check "%CHECK%"
set "PROBE_EXIT=%ERRORLEVEL%"
if not exist "%CHECK%" (
 echo ERROR: el ejecutable no genero diagnostico; Qt o el empaquetado podrian estar incompletos.
 exit /b 1
)
type "%CHECK%"
del /q "%CHECK%" >nul 2>&1
if not "%PROBE_EXIT%"=="0" (
 echo ERROR: el ejecutable no paso sus verificaciones obligatorias.
 exit /b 1
)
powershell.exe -NoProfile -NonInteractive -Command "Compress-Archive -Path '.\dist\MeetingSplit\*' -DestinationPath '.\dist\MeetingSplit-v%RELEASE%-Windows-portable.zip' -Force"
if errorlevel 1 exit /b 1
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
 "%ISCC%" "%CD%\scripts\MeetingSplit.iss"
 if errorlevel 1 exit /b 2
) else (
 echo NOTA: Inno Setup no esta instalado. Se creo un ZIP portable, no un Setup.
)
echo.
echo EXITO: compilacion y prueba basica del EXE completadas en este equipo.
echo NOTA: faltan las pruebas con audio real y NVIDIA en tu ASUS.
exit /b 0
