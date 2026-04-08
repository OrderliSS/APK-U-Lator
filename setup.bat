@echo off
title APK-Lator Setup
cls
echo.
echo   ========================================
echo      APK-Lator Setup (Windows)
echo      Lightweight Android Emulator
echo   ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found!
    echo.
    echo   Install Python 3.10+ from:
    echo     https://www.python.org/downloads/
    echo.
    echo   Or use: winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)

echo   Python found. Running setup...
echo.

:: Run setup
python "%~dp0setup.py"

echo.
echo   ========================================
echo   To launch APK-Lator:
echo     python __main__.py
echo   ========================================
echo.
pause
