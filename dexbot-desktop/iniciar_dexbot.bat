@echo off
setlocal
title Dexbot - IA propria
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python nao foi encontrado.
    echo Instale Python 3 pelo site python.org e marque Add Python to PATH.
    pause
    exit /b 1
)

if not exist "dexbot.py" (
    echo Baixando o nucleo da Dexbot do GitHub...
    curl.exe -L "https://raw.githubusercontent.com/henry4663/dn-ss/main/dexbot-desktop/dexbot.py" -o "dexbot.py"
)

if not exist "dexbot.py" (
    echo Nao consegui baixar dexbot.py. Verifique sua internet.
    pause
    exit /b 1
)

echo Iniciando Dexbot...
py -3 dexbot.py
if errorlevel 1 (
    echo.
    echo A Dexbot encontrou um erro. Confira se Python 3 esta instalado.
    pause
)
endlocal
