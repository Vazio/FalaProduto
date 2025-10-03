@echo off
echo ============================================
echo   Iniciando Qdrant com Dashboard Habilitado
echo ============================================
echo.

REM Verifica se o executável existe
if not exist "C:\qdrant\qdrant.exe" (
    echo ERRO: Qdrant nao encontrado em C:\qdrant\
    echo.
    echo Por favor, instale o Qdrant seguindo as instrucoes:
    echo 1. Baixe de: https://github.com/qdrant/qdrant/releases
    echo 2. Extraia para: C:\qdrant\
    echo.
    pause
    exit /b 1
)

REM Copia o arquivo de configuração para a pasta do Qdrant
echo Copiando arquivo de configuracao...
copy /Y "%~dp0qdrant-config.yaml" "C:\qdrant\qdrant-config.yaml" >nul

REM Inicia o Qdrant com a configuração
cd C:\qdrant
echo.
echo ✅ Qdrant iniciando com dashboard habilitado
echo.
echo 📊 Dashboard: http://localhost:6333/dashboard
echo 🔌 API: http://localhost:6333
echo.
echo Pressione Ctrl+C para parar
echo.

qdrant.exe --config-path qdrant-config.yaml

