# Dependências do Projeto

## 📦 Estrutura de Requirements

O projeto usa uma abordagem modular para dependências:

### `requirements.txt` - Core (Padrão)
**Tamanho**: ~200MB  
**Tempo de instalação**: 2-5 minutos

Dependências essenciais para o sistema RAG funcionar:
- FastAPI & Uvicorn (API web)
- Qdrant Client (vector database)
- Sentence Transformers (embeddings locais BGE)
- OpenAI (LLM)
- PyPDF & python-docx (processamento de documentos)
- Pytest (testes)

**Instalação**:
```bash
pip install -r requirements.txt
```

### `requirements-eval.txt` - Avaliação RAGAS (Opcional)
**Tamanho adicional**: ~500MB  
**Tempo de instalação**: 5-10 minutos

Dependências para avaliação avançada:
- RAGAS (métricas de avaliação)
- LangChain (framework RAG)
- Datasets (Hugging Face)

**Quando usar**:
- Desenvolvimento e pesquisa
- Avaliação formal do sistema
- Otimização de prompts

**Quando NÃO usar**:
- Produção (não necessário)
- Recursos limitados
- Deploy rápido

**Instalação**:
```bash
pip install -r requirements-eval.txt
```

## 🚀 Instalação Rápida (Docker)

O Dockerfile usa apenas `requirements.txt` por padrão para builds rápidos.

Para adicionar RAGAS no container:
```bash
# Depois do container estar rodando
docker compose -f infra/docker-compose.yml exec api pip install -r requirements-eval.txt
```

## 🔧 Instalação Manual (Desenvolvimento Local)

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependências core
pip install -r requirements.txt

# 3. (Opcional) Instalar dependências de avaliação
pip install -r requirements-eval.txt
```

## 📊 Comparação

| Feature | Core | Core + Eval |
|---------|------|-------------|
| API funcionando | ✅ | ✅ |
| RAG pipeline | ✅ | ✅ |
| Embeddings locais | ✅ | ✅ |
| Re-ranking | ✅ | ✅ |
| Testes | ✅ | ✅ |
| Avaliação básica | ✅ | ✅ |
| Métricas RAGAS | ❌ | ✅ |
| LangChain | ❌ | ✅ |
| Tamanho | ~200MB | ~700MB |
| Build time | 2-5 min | 7-15 min |

## 🎯 Recomendação

**Para começar**: Use apenas `requirements.txt`
- Sistema totalmente funcional
- Build rápido
- Menor consumo de recursos

**Para produção**: Use apenas `requirements.txt`
- Não precisa de RAGAS em produção
- Deploy mais rápido
- Menor superfície de ataque

**Para desenvolvimento/pesquisa**: Use `requirements-eval.txt`
- Métricas avançadas
- Experimentação com LangChain
- Análise profunda de qualidade

## ⚠️ Problemas Comuns

### Erro de conexão ao instalar RAGAS
```
HTTPSConnectionPool(host='files.pythonhosted.org'): Max retries exceeded
```

**Solução**: Use apenas requirements.txt para começar. Instale RAGAS depois se necessário.

### Espaço insuficiente
```
No space left on device
```

**Solução**: 
1. Limpe Docker: `docker system prune -af`
2. Use apenas requirements.txt
3. Ou aumente espaço em disco

### Timeout durante instalação
```
ReadTimeoutError
```

**Solução**:
```bash
pip install --default-timeout=200 -r requirements.txt
```

## 📝 Versões Específicas

Todas as dependências usam versões fixas (pinned) para:
- ✅ Builds reproduzíveis
- ✅ Evitar breaking changes
- ✅ Compatibilidade garantida

Para atualizar:
```bash
pip install --upgrade pip
pip list --outdated
pip install <package>==<new_version>
```


