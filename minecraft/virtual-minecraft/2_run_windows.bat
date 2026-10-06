@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Virtual Minecraft tester
if not exist "%~dp0runtime\py.bat" (
  echo Run 1_install_windows.bat first.
  echo.
  pause
  exit /b 1
)
call "%~dp0runtime\py.bat" "%~dp0vmc.py" menu "%~1"
if errorlevel 1 pause
