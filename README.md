# 📚 Insurance Knowledge Base - RAG System

Sistema RAG (Retrieval-Augmented Generation) completo para consulta de produtos de seguro com chatbot web, incluindo:

- 🚀 **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- ⚡ **Backend**: FastAPI + Python 3.11+
- 🔍 **Vector DB**: Qdrant para pesquisa semântica
- 🧠 **RAG Pipeline**: Embeddings locais (BGE), re-ranking, citações
- 🛡️ **Guardrails**: Detecção de prompt injection, rate limiting
- 📊 **Avaliação**: RAGAS para métricas de qualidade
- 🐳 **Docker**: Stack completa com Docker Compose

---

## 🎯 Guia de Formação

> **📚 NOVO! Guia Master Completo:** [**GUIA-FORMACAO.md**](GUIA-FORMACAO.md) 
>
> ✨ Tudo que você precisa desde instalação até uso avançado num único documento!

### Guias Disponíveis

| Guia | Para Quem | Conteúdo |
|------|-----------|----------|
| 📚 [**GUIA-FORMACAO.md**](GUIA-FORMACAO.md) | **TODOS** ⭐ | Guia completo: instalação, uso, validação, embeddings, desenvolvimento |
| 👨‍🏫 [**CHECKLIST-PROFESSOR.md**](CHECKLIST-PROFESSOR.md) | Professores | Preparação de aulas e gestão de turma |
| 📝 [**MUDANCAS.md**](MUDANCAS.md) | Curiosos | Histórico de melhorias do projeto |

---

## 📋 Índice

- [Características](#-características)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Utilização](#-utilização)
- [Configuração](#-configuração)
- [Desenvolvimento](#-desenvolvimento)
- [Testes](#-testes)
- [Avaliação](#-avaliação)
- [Troubleshooting](#-troubleshooting)
- [Estrutura do Projeto](#-estrutura-do-projeto)

## ✨ Características

### Frontend
- Interface de chat moderna e responsiva
- Streaming de respostas em tempo real
- Painel lateral com fontes citadas
- Indicadores de latência e uso de tokens
- Dark mode support

### Backend RAG
- **Embeddings**: BGE-large-en-v1.5 local (opcional OpenAI)
- **Retrieval**: Qdrant com pesquisa por cosine similarity
- **Re-ranking**: BGE-reranker-base para melhor relevância
- **LLM**: OpenAI (gpt-4o-mini) ou Azure OpenAI
- **Chunking**: Hierárquico preservando estrutura de documentos
- **Citações**: Referências automáticas com título, página e excerto

### Segurança & Guardrails
- Rate limiting por IP
- Detecção de prompt injection
- Sanitização de queries
- Termos bloqueados configuráveis
- Limite de contexto e tokens

### Observabilidade
- Logging estruturado (JSON)
- Métricas de latência por componente
- Contagem de tokens
- Tracking de documentos recuperados

## 🏗️ Arquitetura

```
┌─────────────┐
│   Browser   │
│  (Next.js)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   FastAPI   │
│     API     │
└──────┬──────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌──────────┐  ┌──────────┐
│  Qdrant  │  │   LLM    │
│ VectorDB │  │ (OpenAI) │
└──────────┘  └──────────┘
```

### Pipeline RAG

```
Query → Sanitize → Embed → Retrieve (Qdrant) → Re-rank → 
Build Prompt → LLM Generate → Extract Citations → Response
```

## 📦 Pré-requisitos

- **Docker** & **Docker Compose** (recomendado)
- OU
  - Python 3.11+
  - Node.js 20+
  - Qdrant (local ou cloud)

### APIs (Opcional)
- **OpenAI API Key**: Para LLM e embeddings OpenAI
- **Azure OpenAI**: Alternativa ao OpenAI
- **Cohere API Key**: Para re-ranking Cohere (opcional)

> **Nota**: O sistema funciona **sem chaves de API** usando modelos locais (embeddings BGE) e um provider dummy para testes. Para produção, configure pelo menos a OpenAI API key.

## 🚀 Instalação

> **📚 RECOMENDADO:** Siga o [**GUIA-FORMACAO.md**](GUIA-FORMACAO.md) - Guia completo passo a passo!

### Instalação Local (Windows) - Recomendado para Formação

**Veja passo a passo completo em:** [**GUIA-FORMACAO.md → Seção 2**](GUIA-FORMACAO.md#-2-instalação-completa)

**Resumo rápido:**

```powershell
# 1. Configurar .env
copy env.example .env
notepad .env  # Adicionar suas chaves

# 2. Instalar Backend
cd api
python -m venv venv
.\install-all.bat

# 3. Instalar Frontend
cd ..\web
npm install
```

### Instalação com Docker (Avançado)

```bash
# Build completo com embeddings locais
make dev

# OU build rápido (requer OpenAI key)
make dev-fast
```

---

Aguarde até todos os serviços estarem rodando:
- ✅ Qdrant: http://localhost:6333
- ✅ API: http://localhost:8000
- ✅ Web: http://localhost:3000

## 💡 Utilização

### 1. Verificar saúde do sistema

```bash
make health
```

Ou:

```bash
curl http://localhost:8000/health
```

### 2. Ingerir documentos

Coloque seus PDFs, DOCX ou TXT em `data/pdfs/` (já incluídos 3 exemplos em TXT) e execute:

```bash
make ingest
```

Ou:

```bash
curl -X POST http://localhost:8000/ingest
```

Resposta esperada:
```json
{
  "files_processed": 3,
  "chunks_created": 150,
  "documents_upserted": 150,
  "elapsed_seconds": 12.5,
  "status": "success"
}
```

### 3. Usar o chatbot

Abra http://localhost:3000 no navegador e faça perguntas como:

- "Quais as exclusões da cobertura de Danos Próprios no seguro Auto?"
- "Qual é o período de carência para cirurgias?"
- "O seguro de Saúde cobre implantes dentários?"

### 4. Testar via API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais as coberturas do seguro Auto?",
    "top_k": 5
  }'
```

### 5. Com filtros por produto

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Qual a franquia?",
    "top_k": 5,
    "filters": {
      "product": "Auto"
    }
  }'
```

## ⚙️ Configuração

### Variáveis de Ambiente Principais

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave API OpenAI | - |
| `LLM_MODEL` | Modelo LLM | `gpt-4o-mini` |
| `EMBEDDINGS_PROVIDER` | `local` ou `openai` | `local` |
| `LOCAL_EMBEDDING_MODEL` | Modelo BGE | `BAAI/bge-large-en-v1.5` |
| `TOP_K` | Docs a recuperar | `6` |
| `RERANK_TOP_K` | Docs após re-ranking | `3` |
| `CHUNK_SIZE` | Tamanho dos chunks | `800` |
| `MAX_CONTEXT_CHARS` | Limite de contexto | `12000` |
| `BLOCKED_TERMS` | Termos bloqueados | `segredo;senha;...` |
| `RATE_LIMIT_PER_MINUTE` | Limite de requisições | `20` |

### Configuração de Embeddings

#### Embeddings Locais (Padrão - Sem API Key)
```bash
EMBEDDINGS_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
```

**Vantagens**: Gratuito, privado, funciona offline  
**Desvantagens**: Requer GPU para melhor performance (funciona em CPU)

#### Embeddings OpenAI
```bash
EMBEDDINGS_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_API_KEY=sk-...
```

**Vantagens**: Rápido, sem recursos locais  
**Desvantagens**: Custo por requisição, requer internet

### Configuração de LLM

#### OpenAI
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...
```

#### Azure OpenAI
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://seu-recurso.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### Re-ranking

#### Local (BGE - Padrão)
```bash
RERANKER=local
LOCAL_RERANKER_MODEL=BAAI/bge-reranker-base
```

#### Cohere (Opcional)
```bash
RERANKER=cohere
COHERE_API_KEY=...
```

## 🛠️ Desenvolvimento

### Estrutura de desenvolvimento

```bash
# Backend (FastAPI)
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (Next.js)
cd web
npm install
npm run dev
```

### Adicionar novos documentos

1. Coloque PDFs, DOCX ou TXT em `data/pdfs/`
2. Execute `make ingest`
3. Os documentos serão:
   - Extraídos (texto + metadados)
   - Divididos em chunks
   - Convertidos em embeddings
   - Armazenados no Qdrant

**Formatos suportados:**
- `.pdf` - PDFs com texto extraível
- `.docx` - Documentos Word
- `.txt` - Ficheiros de texto simples (UTF-8)

### Formato de Metadados

Cada chunk armazenado contém:
```json
{
  "text": "Conteúdo do chunk...",
  "doc_id": "nome_documento_pagina",
  "title": "Nome do Documento",
  "section": "Secção/Heading",
  "page": 5,
  "source_path": "caminho/ficheiro.pdf",
  "chunk_index": 42
}
```

### Personalizar o System Prompt

Edite `api/app/rag/pipeline.py`, método `_get_system_prompt()`:

```python
def _get_system_prompt(self) -> str:
    return """És um assistente especializado em produtos de seguro.
    
Regras:
1. Responde APENAS com base nas fontes
2. Inclui SEMPRE citações
3. ...
"""
```

## 🧪 Testes

### Testes da API

```bash
make test-api
```

Ou:

```bash
cd api
pytest -v
```

Cobertura dos testes:
- ✅ Endpoint `/health`
- ✅ Endpoint `/chat` (com mock)
- ✅ Endpoint `/ingest` (com mock)
- ✅ Rate limiting
- ✅ Validação de inputs
- ✅ Tratamento de erros

### Testes do Frontend

```bash
make test-web
```

## 📊 Avaliação

### Avaliação Básica (Sempre Disponível)

O sistema inclui avaliação básica que **não requer dependências extras**:

```bash
make eval
```

Ou:

```bash
docker compose -f infra/docker-compose.yml exec api python eval/run_ragas.py
```

Isto executa todas as perguntas do ground truth e mostra:
- Perguntas vs Respostas geradas
- Contextos recuperados
- Salva resultados em `data/evaluation_results_basic.json`

### Avaliação Avançada com RAGAS (Opcional)

Para métricas avançadas (faithfulness, relevancy, etc.), instale as dependências de avaliação:

```bash
# Dentro do container API
docker compose -f infra/docker-compose.yml exec api pip install -r requirements-eval.txt

# Depois execute a avaliação
make eval
```

> **Nota**: RAGAS requer OpenAI API key e adiciona ~500MB de dependências (langchain, etc.)

### Métricas Avaliadas

- **Faithfulness**: Quão fiel é a resposta ao contexto recuperado?
- **Answer Relevancy**: Quão relevante é a resposta para a pergunta?
- **Context Recall**: O contexto recuperado cobre a resposta esperada?
- **Context Precision**: Os documentos relevantes estão bem ranqueados?

### Ground Truth

Adicione pares pergunta-resposta em `data/groundtruth/qa.jsonl`:

```json
{
  "question": "Pergunta exemplo?",
  "answer": "Resposta esperada...",
  "metadata": {"product": "Auto"}
}
```

O sistema já inclui 15 exemplos para começar.

### Resultados

Os resultados são salvos em `data/evaluation_results.json`:

```json
{
  "faithfulness": 0.87,
  "answer_relevancy": 0.91,
  "context_recall": 0.84,
  "context_precision": 0.78
}
```

## 🔧 Troubleshooting

### Problema: Erro ao instalar dependências no Docker

**Sintoma**: `Failed to establish a new connection` durante build

**Causas**:
- Problema de conexão internet/DNS
- Proxy/firewall bloqueando
- Dependências muito pesadas (RAGAS/langchain)

**Solução**:
```bash
# Limpar cache e tentar novamente
docker compose -f infra/docker-compose.yml down
docker system prune -f
docker compose -f infra/docker-compose.yml up --build
```

O sistema agora usa **apenas dependências core** (rápidas e leves). RAGAS é opcional.

### Problema: Modelos locais muito lentos

**Solução 1**: Use GPU se disponível
```bash
# No Dockerfile da API, adicione suporte CUDA
# Ou use CPU com batch pequeno (já configurado)
```

**Solução 2**: Use embeddings OpenAI
```bash
EMBEDDINGS_PROVIDER=openai
```

### Problema: Qdrant não inicia

**Verificar**:
```bash
docker compose -f infra/docker-compose.yml logs qdrant
```

**Solução**: Garantir portas 6333 e 6334 livres
```bash
# Windows
netstat -ano | findstr 6333

# Linux/Mac
lsof -i :6333
```

### Problema: Erro ao ingerir PDFs

**Causa comum**: PDFs digitalizados (imagens)

**Solução**: 
- Use PDFs com texto extraível
- Converta para TXT se necessário
- Ou adicione OCR (pytesseract) ao pipeline

**Alternativa**: Use ficheiros `.txt` para documentos de texto simples (como os exemplos fornecidos)

### Problema: Respostas sem citações

**Verificar**:
1. Documentos foram ingeridos? `curl http://localhost:8000/stats`
2. Embeddings estão funcionando?
3. Query está sanitizada corretamente?

**Debug**:
```bash
# Ver logs da API
make logs-api
```

### Problema: "Rate limit exceeded"

**Solução temporária**: Aumentar limite
```bash
RATE_LIMIT_PER_MINUTE=100
```

**Solução permanente**: Implementar Redis para rate limiting distribuído

### Problema: Contexto truncado

**Sintoma**: Respostas incompletas

**Solução**: Aumentar limite
```bash
MAX_CONTEXT_CHARS=20000
```

### Problema: Encoding UTF-8

**Erro**: `UnicodeDecodeError`

**Solução**: Garantir ficheiros em UTF-8
```python
# Ao criar documentos
with open(file, 'r', encoding='utf-8') as f:
    ...
```

### Problema: OpenAI API timeout

**Solução**: Aumentar timeout no provider
```python
# Em app/llm/provider.py
self.client = OpenAI(
    api_key=...,
    timeout=60.0  # segundos
)
```

## 📁 Estrutura do Projeto

```
FalaProduto/
├── api/                          # Backend FastAPI
│   ├── app/
│   │   ├── main.py              # FastAPI app + endpoints
│   │   ├── config.py            # Configurações
│   │   ├── embeddings/          # Providers de embeddings
│   │   ├── llm/                 # Providers LLM
│   │   ├── rag/                 # Pipeline RAG
│   │   ├── rerank/              # Re-ranking
│   │   └── retrieval/           # Qdrant store
│   ├── eval/
│   │   └── run_ragas.py         # Script avaliação RAGAS
│   ├── tests/
│   │   └── test_chat.py         # Testes unitários
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
│
├── web/                          # Frontend Next.js
│   ├── app/
│   │   ├── layout.tsx           # Layout principal
│   │   ├── page.tsx             # Página chat
│   │   └── globals.css          # Estilos globais
│   ├── components/
│   │   ├── Chat.tsx             # Componente chat
│   │   └── Citations.tsx        # Componente citações
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── data/
│   ├── pdfs/                     # Documentos a ingerir
│   │   ├── Produto_Auto_Condicoes_Gerais.txt
│   │   ├── Produto_Saude_Coberturas_Exclusoes.txt
│   │   └── Produto_Habitacao_Multirriscos.txt
│   └── groundtruth/              # Q&A para avaliação
│       └── qa.jsonl
│
├── infra/
│   └── docker-compose.yml        # Orquestração Docker
│
├── env.example                   # Template variáveis ambiente
├── Makefile                      # Comandos úteis
└── README.md                     # Este ficheiro
```

## 🎯 Próximos Passos & TODOs

### Funcionalidades
- [ ] Histórico de conversação persistente
- [ ] Suporte para múltiplos idiomas
- [ ] Export de conversas (PDF/JSON)
- [ ] Feedback do utilizador (👍/👎)
- [ ] Sugestões de perguntas relacionadas

### Técnico
- [ ] Function calling para queries estruturadas
- [ ] OCR para PDFs digitalizados
- [ ] Cache de embeddings (Redis)
- [ ] Métricas com Prometheus/Grafana
- [ ] CI/CD pipeline
- [ ] Deploy em cloud (AWS/Azure/GCP)

### Segurança
- [ ] Autenticação (JWT)
- [ ] Rate limiting com Redis
- [ ] Audit logging
- [ ] HTTPS/TLS
- [ ] Sanitização avançada de inputs

### Performance
- [ ] Batch embedding generation
- [ ] Lazy loading de modelos
- [ ] Caching de resultados frequentes
- [ ] Compressão de respostas
- [ ] CDN para frontend

## 📝 Licença

Este projeto é fornecido "as-is" para fins educacionais e de demonstração.

## 🤝 Contribuir

Sugestões e melhorias são bem-vindas! 

## 📧 Contacto

Para questões ou suporte, contacte o administrador do sistema.

---

**Desenvolvido com ❤️ usando FastAPI, Next.js, Qdrant e OpenAI**


