@echo off
title Dexbot - Conexao publica
set "PYTHON=%LocalAppData%\Programs\Python\Python313\python.exe"
set "CLOUDFLARED=C:\Program Files (x86)\cloudflared\cloudflared.exe"

if not exist "%PYTHON%" (
  echo Python 3.13 nao encontrado em:
  echo %PYTHON%
  pause
  exit /b 1
)
if not exist "%CLOUDFLARED%" (
  echo cloudflared nao encontrado em:
  echo %CLOUDFLARED%
  pause
  exit /b 1
)

echo Iniciando a API local do Dexbot...
start "Dexbot API" "%PYTHON%" "%~dp0interface\dexbot_web.py"
timeout /t 4 /nobreak >nul

if exist "%~dp0.dexbot-token" (
  echo Abrindo o token privado para configurar no Worker.
  start "" notepad.exe "%~dp0.dexbot-token"
)

echo.
echo Iniciando o tunel HTTPS. Mantenha esta janela aberta.
echo Copie a URL https://....trycloudflare.com exibida abaixo.
echo.
"%CLOUDFLARED%" tunnel --url http://127.0.0.1:8765
pause
