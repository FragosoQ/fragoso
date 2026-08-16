@echo off
REM Arranca a API do Fragoso Bot. Basta fazer duplo-clique neste ficheiro.
REM Sem acentos de proposito: a consola do Windows nao os mostra bem.

cd /d "%~dp0"
title Fragoso Bot - API

echo.
echo  ============================================
echo   Fragoso Bot - API local
echo  ============================================
echo.

REM --- Procurar o Python (primeiro o launcher "py", depois "python") ---
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py"
if defined PY goto :temPython

where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if defined PY goto :temPython

echo  [ERRO] Python nao encontrado neste computador.
echo.
echo  Instale a partir de https://www.python.org/downloads/
echo  IMPORTANTE: na instalacao, marque a caixa "Add python.exe to PATH".
echo  Depois feche esta janela e volte a fazer duplo-clique aqui.
echo.
pause
exit /b 1

:temPython
echo  Python encontrado: %PY%
%PY% --version
echo.

REM --- Instalar dependencias (rapido se ja estiverem instaladas) ---
echo  A verificar as dependencias...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [ERRO] Falhou a instalacao das dependencias.
    echo  Tente manualmente:  %PY% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo  Dependencias OK.
echo.

echo  ============================================
echo   API a correr em:  http://localhost:8000
echo   Teste no browser: http://localhost:8000/health
echo.
echo   Nos Ajustes da app, o URL deve ser:
echo   http://localhost:8000/api/chat
echo.
echo   Para PARAR: feche esta janela ou Ctrl+C
echo  ============================================
echo.

%PY% -m uvicorn server:app --port 8000 --reload

echo.
echo  O servidor parou.
pause
