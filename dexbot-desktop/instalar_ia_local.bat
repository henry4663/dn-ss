@echo off
setlocal EnableExtensions
title Dexbot - Inicializador
cd /d "%~dp0"
cls
echo ==========================================
echo          DEXBOT - INICIALIZADOR
echo ==========================================
echo.

where curl.exe >nul 2>nul
if errorlevel 1 (
    echo ERRO: curl.exe nao foi encontrado no Windows.
    pause
    exit /b 1
)

echo Atualizando o nucleo da Dexbot...
curl.exe -fL --retry 2 "https://raw.githubusercontent.com/henry4663/dn-ss/main/dexbot-desktop/dexbot.py" -o "%~dp0dexbot.py"
if errorlevel 1 (
    echo ERRO: nao consegui baixar dexbot.py.
    pause
    exit /b 1
)

set "PYTHON="
for %%V in (313 312 311 310 39) do (
    if not defined PYTHON if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python%%V\python.exe"
)
if not defined PYTHON if exist "%LocalAppData%\Programs\Python\Python313-32\python.exe" set "PYTHON=%LocalAppData%\Programs\Python\Python313-32\python.exe"
if not defined PYTHON (
    where python.exe >nul 2>nul
    if not errorlevel 1 set "PYTHON=python.exe"
)
if not defined PYTHON (
    where py.exe >nul 2>nul
    if not errorlevel 1 set "PYTHON=py.exe -3"
)
if not defined PYTHON (
    echo ERRO: Python nao foi encontrado.
    echo Instale Python 3.10 ou superior e marque Add Python to PATH.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

set "OLLAMA="
where ollama.exe >nul 2>nul
if not errorlevel 1 for /f "delims=" %%I in ('where ollama.exe') do if not defined OLLAMA set "OLLAMA=%%I"
if not defined OLLAMA if exist "%LocalAppData%\Programs\Ollama\ollama.exe" set "OLLAMA=%LocalAppData%\Programs\Ollama\ollama.exe"
if not defined OLLAMA if exist "%ProgramFiles%\Ollama\ollama.exe" set "OLLAMA=%ProgramFiles%\Ollama\ollama.exe"
if not defined OLLAMA (
    echo ERRO: Ollama nao foi encontrado.
    echo Instale com: winget install --id Ollama.Ollama -e
    pause
    exit /b 1
)

echo.
echo Verificando Ollama...
curl.exe -s --max-time 2 "http://127.0.0.1:11434/api/tags" >nul 2>nul
if errorlevel 1 (
    echo Iniciando o servidor Ollama...
    start "Ollama Server" /min "%OLLAMA%" serve
)

set "SERVIDOR_OK="
for /L %%N in (1,1,15) do (
    if not defined SERVIDOR_OK (
        curl.exe -s --max-time 2 "http://127.0.0.1:11434/api/tags" >nul 2>nul
        if not errorlevel 1 set "SERVIDOR_OK=1"
        if not defined SERVIDOR_OK timeout /t 1 /nobreak >nul
    )
)
if not defined SERVIDOR_OK (
    echo ERRO: Ollama nao iniciou na porta 11434.
    echo Abra o aplicativo Ollama e tente novamente.
    pause
    exit /b 1
)

echo.
echo Conferindo o modelo Qwen Coder...
"%OLLAMA%" show qwen2.5-coder:1.5b >nul 2>nul
if errorlevel 1 (
    echo Baixando o modelo. Aguarde...
    "%OLLAMA%" pull qwen2.5-coder:1.5b
    if errorlevel 1 (
        echo ERRO: falha ao baixar o modelo Qwen.
        pause
        exit /b 1
    )
)

echo.
echo Iniciando Dexbot...
echo Para sair, digite /sair.
echo.
"%PYTHON%" "%~dp0dexbot.py"
set "CODIGO=%errorlevel%"
echo.
echo Dexbot encerrou. Codigo: %CODIGO%
pause
exit /b %CODIGO%
