@echo off
title XeQ SN Factory Launcher

:: Check for standard 'python' command
python --version >nul 2>&1
if %errorlevel% == 0 (
    python main.py
    goto end
)

:: Fallback to 'py' launcher (your version)
py --version >nul 2>&1
if %errorlevel% == 0 (
    py main.py
    goto end
)

echo [ERROR] Python not found! 
echo Please install Python from https://www.python.org
echo Make sure to check "Add Python to PATH" during installation.
pause

:end
if %errorlevel% neq 0 pause