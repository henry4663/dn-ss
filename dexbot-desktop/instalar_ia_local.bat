@echo off
title Dexbot - Instalador da IA local
cd /d "%~dp0"

echo ==========================================
echo       DEXBOT - CONFIGURAR IA LOCAL
echo ==========================================
echo.

where ollama >nul 2>nul
if errorlevel 1 (
    echo Ollama ainda nao esta instalado.
    echo Vou abrir a pagina oficial para instalar.
    start "" "https://ollama.com/download"
    echo.
    echo Instale o Ollama para Windows e depois execute este arquivo novamente.
    pause
    exit /b 1
)

echo Baixando o modelo Qwen 2.5 1.5B.
echo O download acontece uma vez e pode demorar.
ollama pull qwen2.5:1.5b
if errorlevel 1 (
    echo.
    echo Nao foi possivel baixar o modelo. Verifique a internet e tente novamente.
    pause
    exit /b 1
)

echo.
echo Modelo instalado. Iniciando a Dexbot...
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" (
    "%LocalAppData%\Programs\Python\Python313\python.exe" "%~dp0dexbot.py"
) else (
    python "%~dp0dexbot.py"
)
pause
