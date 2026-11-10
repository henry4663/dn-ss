@echo off
setlocal
title Dexbot Web
cd /d "%~dp0"

echo [Dexbot] Atualizando o servidor pelo GitHub...
curl.exe -fL --retry 2 "https://raw.githubusercontent.com/henry4663/dn-ss/main/dexbot-desktop/interface/dexbot_web.py" -o "%~dp0dexbot_web.py"
if errorlevel 1 (
    echo ERRO: nao foi possivel baixar dexbot_web.py.
    echo Confira sua conexao com a internet e tente novamente.
    pause
    exit /b 1
)

set "PYTHON=%LocalAppData%\Programs\Python\Python313\python.exe"
if not exist "%PYTHON%" (
    echo Python 3.13 nao encontrado em: %PYTHON%
    echo Instale o Python 3.13 ou ajuste o caminho neste arquivo.
    pause
    exit /b 1
)

echo [Dexbot] Iniciando servidor...
"%PYTHON%" "%~dp0dexbot_web.py"
pause
