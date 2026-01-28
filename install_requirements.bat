@echo off
title Setup Dependencies - XeQ SN Factory
echo Checking for Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not installed.
        pause
        exit
    )
)

echo Python found. Installing required libraries (requests, pyyaml)...
pip install requests pyyaml
echo.
echo [SUCCESS] Dependencies installed. You can now run the Factory!
pause