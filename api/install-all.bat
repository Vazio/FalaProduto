@echo off
echo ================================
echo   Instalando TODOS os pacotes
echo ================================
echo.

call venv\Scripts\activate.bat

echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando pacotes core...
pip install fastapi==0.109.0
pip install uvicorn[standard]==0.27.0
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0

echo.
echo Instalando clientes...
pip install qdrant-client==1.7.3
pip install openai==1.10.0
pip install tiktoken==0.5.2
pip install tenacity==8.2.3

echo.
echo Instalando processadores de documentos...
pip install pypdf==4.0.1
pip install python-docx==1.1.0

echo.
echo Instalando utilitarios...
pip install python-multipart==0.0.6
pip install aiofiles==23.2.1
pip install python-dotenv==1.0.0

echo.
echo Instalando testes...
pip install pytest==7.4.4
pip install pytest-asyncio==0.23.3
pip install httpx==0.26.0

echo.
echo Instalando NumPy (wheel)...
pip install --only-binary :all: "numpy>=1.24.0"

echo.
echo Instalando sentence-transformers (pode demorar 5-10 min)...
pip install --default-timeout=600 "sentence-transformers>=2.0.0"

echo.
echo ================================
echo   Instalacao concluida!
echo ================================
echo.
echo Teste a instalacao:
echo   python -c "import fastapi; import qdrant_client; import sentence_transformers; print('OK!')"
echo.
echo Inicie a API:
echo   uvicorn app.main:app --reload
echo.
pause


