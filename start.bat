@echo off
chcp 65001 >nul
title 银翼出击 - 战机射击游戏

echo ====================================
echo       银翼出击 - 战机射击游戏
echo ====================================
echo.

REM 查找 Python
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    )
)

if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    )
)

if "%PYTHON_CMD%"=="" (
    if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe"
    )
)

if "%PYTHON_CMD%"=="" (
    for /f "tokens=*" %%i in ('where python3 2^>nul') do (
        set PYTHON_CMD=%%i
    )
)

if "%PYTHON_CMD%"=="" (
    echo [错误] 找不到 Python！
    echo 请先安装 Python 3.12: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 使用: %PYTHON_CMD%
cd /d "%~dp0"

%PYTHON_CMD% -c "import pygame" 2>nul
if %errorlevel% neq 0 (
    echo [提示] 正在安装 pygame...
    %PYTHON_CMD% -m pip install pygame
    if %errorlevel% neq 0 (
        echo [错误] pygame 安装失败！
        pause
        exit /b 1
    )
)

echo 启动游戏中...
echo.
%PYTHON_CMD% main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 游戏运行出错！错误代码: %errorlevel%
    pause
)
