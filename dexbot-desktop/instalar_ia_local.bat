@echo off
setlocal
title Dexbot - Inicializador
cd /d "%~dp0"
cls
echo ==========================================
echo          DEXBOT - INICIALIZADOR
echo ==========================================
echo.

if not exist "%~dp0dexbot.py" (
    echo ERRO: dexbot.py nao esta na mesma pasta deste instalador.
    echo Baixe os dois arquivos para a pasta %%USERPROFILE%%\Dexbot.
    echo.
    pause
    exit /b 1
)

set "PYTHON="
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python313\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python311\python.exe"
if not defined PYTHON if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python310\python.exe"
if not defined PYTHON (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON=python"
)
if not defined PYTHON (
    echo ERRO: Python nao foi encontrado.
    echo Instale Python 3.10 ou superior e marque Add Python to PATH.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

where ollama >nul 2>nul
if errorlevel 1 (
    echo ERRO: Ollama nao foi encontrado.
    echo Instale o Ollama para Windows. Depois abra este arquivo novamente.
    start "" "https://ollama.com/download"
    pause
    exit /b 1
)

echo Verificando o servico local do Ollama...
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>nul
if errorlevel 1 (
    echo Iniciando Ollama...
    start "Ollama" /min cmd /c "ollama serve"
    timeout /t 5 /nobreak >nul
)

echo.
echo Conferindo o modelo Qwen 2.5 1.5B...
ollama show qwen2.5:1.5b >nul 2>nul
if errorlevel 1 (
    echo Baixando o modelo. Aguarde; pode demorar.
    ollama pull qwen2.5:1.5b
    if errorlevel 1 (
        echo ERRO: nao foi possivel baixar o modelo.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando Dexbot...
echo Para sair, digite /sair dentro da Dexbot.
echo.
"%PYTHON%" "%~dp0dexbot.py"
echo.
echo Dexbot foi encerrada. Codigo de saida: %errorlevel%
pause
