@echo off
setlocal EnableExtensions
title Dexbot - Iniciar
if not exist "%USERPROFILE%\Dexbot" mkdir "%USERPROFILE%\Dexbot"
cd /d "%USERPROFILE%\Dexbot"

echo Baixando o inicializador atualizado...
curl.exe -fL --retry 2 "https://raw.githubusercontent.com/henry4663/dn-ss/main/dexbot-desktop/instalar_ia_local.bat" -o "instalar_ia_local.bat"
if errorlevel 1 (
    echo ERRO: nao consegui baixar o inicializador.
    pause
    exit /b 1
)

call "%USERPROFILE%\Dexbot\instalar_ia_local.bat"
