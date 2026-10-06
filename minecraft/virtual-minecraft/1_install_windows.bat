@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Virtual Minecraft tester - setup

echo ============================================================
echo   Virtual Minecraft tester - one-time setup
echo.
echo   1. Portable Python 3.12 from python.org  (11 MB, stays in this folder)
echo   2. Minecraft Bedrock Dedicated Server from minecraft.net  (90 MB)
echo ============================================================
echo.

set "RT=%~dp0runtime"
set "PYDIR=%~dp0runtime\python"
set "PYURL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
set "PYSHA=4ACBED6DD1C744B0376E3B1CF57CE906F9DC9E95E68824584C8099A63025A3C3"
if not exist "%RT%" mkdir "%RT%"

if exist "%PYDIR%\python.exe" goto write_launcher

echo [1/2] Downloading portable Python ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $zip=Join-Path $env:RT 'python.zip'; Invoke-WebRequest -UseBasicParsing -Uri $env:PYURL -OutFile $zip; if ((Get-FileHash $zip -Algorithm SHA256).Hash -ne $env:PYSHA) { Remove-Item $zip; throw 'checksum mismatch' }; Expand-Archive -Force -Path $zip -DestinationPath $env:PYDIR; Remove-Item $zip"
if exist "%PYDIR%\python.exe" goto write_launcher

echo.
echo Portable Python could not be downloaded. Looking for an installed Python 3.8+ ...
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 (
  > "%RT%\py.bat" echo @py -3 %%*
  goto have_launcher
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 (
  > "%RT%\py.bat" echo @python %%*
  goto have_launcher
)
goto no_python

:write_launcher
> "%RT%\py.bat" echo @"%%~dp0python\python.exe" %%*

:have_launcher
call "%RT%\py.bat" -c "import sys, ssl; print('Python', sys.version.split()[0], 'OK')"
if errorlevel 1 goto no_python

echo.
echo [2/2] Minecraft Bedrock Dedicated Server
call "%RT%\py.bat" "%~dp0vmc.py" setup
if errorlevel 1 goto end

echo.
echo ============================================================
echo   Setup finished.
echo   Next: double-click 2_run_windows.bat
echo         or drag a .mcworld file / world folder onto it.
echo ============================================================
goto end

:no_python
echo.
echo Python is not available. Check the internet connection and run this file again,
echo or install Python 3.8+ from https://www.python.org/downloads/ and run it again.

:end
echo.
pause
