@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
echo MeetingSplit - diagnostico de ejecutable sin audio real
if not exist dist\MeetingSplit\MeetingSplit.exe (
 echo No existe una compilacion portable; ejecuta compilar_windows.bat primero.
 exit /b 1
)
set "CHECK=%TEMP%\meetingsplit-diagnostic-%RANDOM%.json"
start /wait "" "dist\MeetingSplit\MeetingSplit.exe" --self-check "%CHECK%"
set "EXITCODE=%ERRORLEVEL%"
if not exist "%CHECK%" (
 echo ERROR: no se creo el informe. Posible fallo de inicio del EXE.
 exit /b 1
)
type "%CHECK%"
del /q "%CHECK%" >nul 2>&1
if not "%EXITCODE%"=="0" echo ATENCION: faltan componentes obligatorios.
exit /b %EXITCODE%
