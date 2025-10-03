# 🔧 Alternativas ao Docker para Qdrant

> **Problema**: Alunos não podem instalar Docker  
> **Solução**: 3 alternativas funcionais

---

## 🎯 Opção 1: Qdrant Standalone (RECOMENDADO)

### O que é?
Qdrant tem um **executável standalone** que roda sem Docker!

### Instalação Windows

#### Passo 1: Download do Qdrant

**Opção A: Download Manual**
1. Acesse: https://github.com/qdrant/qdrant/releases
2. Procure a versão mais recente (ex: v1.7.0)
3. Baixe: `qdrant-x86_64-pc-windows-msvc.zip`
4. Extraia para: `C:\qdrant\`

**Opção B: Via PowerShell (Automático)**
```powershell
# Criar pasta
mkdir C:\qdrant
cd C:\qdrant

# Baixar (ajuste versão se necessário)
Invoke-WebRequest -Uri "https://github.com/qdrant/qdrant/releases/download/v1.7.0/qdrant-x86_64-pc-windows-msvc.zip" -OutFile "qdrant.zip"

# Extrair
Expand-Archive -Path qdrant.zip -DestinationPath . -Force

# Limpar
Remove-Item qdrant.zip
```

#### Passo 2: Executar Qdrant

**⚠️ IMPORTANTE**: Na versão 1.7+, o dashboard precisa ser habilitado explicitamente!

**Opção A: Usar o script automático (RECOMENDADO)**

Na raiz do projeto FalaProduto, execute:
```powershell
.\start-qdrant.bat
```

Este script:
- Copia a configuração necessária
- Inicia o Qdrant com dashboard habilitado
- Mostra o link do dashboard

**Opção B: Manual**

1. Copie o arquivo `qdrant-config.yaml` da raiz do projeto para `C:\qdrant\`
2. Execute:
```powershell
cd C:\qdrant
.\qdrant.exe --config-path qdrant-config.yaml
```

**Você verá:**
```
Qdrant | high-performance vector search at scale
Version: 1.7.0
Listening on http://0.0.0.0:6333
Web UI enabled
```

✅ **Pronto!** Qdrant está rodando com dashboard!

#### Passo 3: Verificar

Abra no navegador: http://localhost:6333/dashboard

#### Passo 4: Configurar o Projeto

No arquivo `.env` da raiz do projeto:
```bash
# Manter assim (já está correto!)
QDRANT_URL=http://localhost:6333
```

#### Passo 5: Usar Normalmente

```powershell
# Terminal 1: Qdrant standalone
cd C:\qdrant
.\qdrant.exe

# Terminal 2: Backend
cd C:\Caminho\Para\FalaProduto\api
.\run-local.bat

# Terminal 3: Frontend
cd C:\Caminho\Para\FalaProduto\web
npm run dev
```

### ✅ Vantagens
- Não precisa Docker
- Rápido de instalar (~50MB)
- Funciona exatamente igual
- Dados persistem localmente

### ❌ Desvantagens
- Precisa baixar executável
- Mais um executável para gerenciar

---

## 🌐 Opção 2: Qdrant Cloud (Gratuito)

### O que é?
Qdrant oferece um **tier gratuito** na nuvem!

### Configuração

#### Passo 1: Criar Conta

1. Acesse: https://cloud.qdrant.io/
2. Crie conta gratuita
3. Crie um **cluster** (Free Tier: 1GB grátis)

#### Passo 2: Obter Credenciais

Após criar o cluster, anote:
- **URL**: `https://xxx-xxx-xxx.us-east.aws.cloud.qdrant.io:6333`
- **API Key**: `xxx-xxx-xxx`

#### Passo 3: Configurar Projeto

No arquivo `.env`:
```bash
# Mudar para URL do Qdrant Cloud
QDRANT_URL=https://seu-cluster.us-east.aws.cloud.qdrant.io:6333

# Adicionar API key
QDRANT_API_KEY=sua-api-key-aqui
```

#### Passo 4: Atualizar Código (Uma Única Vez)

**Arquivo**: `api/app/retrieval/qdrant_store.py`

**Linha 26**, mudar de:
```python
def __init__(self):
    self.client = QdrantClient(url=settings.qdrant_url)
```

**Para:**
```python
def __init__(self):
    # Suportar API key para Qdrant Cloud
    api_key = getattr(settings, 'qdrant_api_key', None)
    if api_key:
        self.client = QdrantClient(url=settings.qdrant_url, api_key=api_key)
    else:
        self.client = QdrantClient(url=settings.qdrant_url)
```

**Arquivo**: `api/app/config.py`

**Adicionar** após linha 28:
```python
qdrant_url: str = "http://localhost:6333"
qdrant_api_key: str = ""  # Adicionar esta linha
qdrant_collection: str = "insurance_products"
```

#### Passo 5: Usar Normalmente

```powershell
# Agora só precisa de 2 terminais!

# Terminal 1: Backend
cd api
.\run-local.bat

# Terminal 2: Frontend
cd web
npm run dev
```

### ✅ Vantagens
- **Não precisa instalar nada** (nem Docker nem executável)
- Gratuito até 1GB
- Acessível de qualquer lugar
- Dados persistem na nuvem
- Apenas 2 terminais (sem Qdrant local)

### ❌ Desvantagens
- Precisa internet
- Dados na nuvem (não privado)
- Limite de 1GB (suficiente para curso)

---

## 🔄 Opção 3: Qdrant em Memória (Para Testes Rápidos)

### O que é?
Qdrant pode rodar **em memória** sem persistência.

### Configuração

#### Modificar Código

**Arquivo**: `api/app/retrieval/qdrant_store.py`

**Linha 26**, mudar de:
```python
def __init__(self):
    self.client = QdrantClient(url=settings.qdrant_url)
```

**Para:**
```python
def __init__(self):
    # Modo memória (sem servidor)
    if settings.qdrant_url == "memory":
        self.client = QdrantClient(":memory:")
        logger.info("Using in-memory Qdrant (data will be lost on restart)")
    else:
        api_key = getattr(settings, 'qdrant_api_key', None)
        if api_key:
            self.client = QdrantClient(url=settings.qdrant_url, api_key=api_key)
        else:
            self.client = QdrantClient(url=settings.qdrant_url)
```

#### Configurar .env

```bash
# Usar modo memória
QDRANT_URL=memory
```

#### Usar

```powershell
# Apenas 2 terminais!

# Terminal 1: Backend
cd api
.\run-local.bat

# Terminal 2: Frontend
cd web
npm run dev
```

### ✅ Vantagens
- **Mais simples**: sem instalar nada
- Apenas 2 terminais
- Rápido para testes

### ❌ Desvantagens
- ⚠️ **Dados perdidos ao fechar** a API
- Precisa re-ingerir documentos sempre
- Não recomendado para produção

---

## 📊 Comparação das Opções

| Característica | Standalone | Cloud | Memória |
|---------------|------------|-------|---------|
| **Instalação** | Download exe | Criar conta | Nada |
| **Internet** | Não precisa | Precisa | Não precisa |
| **Persistência** | ✅ Sim | ✅ Sim | ❌ Não |
| **Terminais** | 3 | 2 | 2 |
| **Privacidade** | ✅ Total | ⚠️ Nuvem | ✅ Total |
| **Limite** | ✅ Ilimitado | 1GB (free) | RAM |
| **Recomendado?** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎓 Recomendação para Turma

### Cenário 1: Sem Docker, Com Internet
✅ **Qdrant Cloud** (Opção 2)
- Mais fácil: nada para instalar
- Apenas criar conta
- Dados persistem
- 2 terminais apenas

### Cenário 2: Sem Docker, Sem Internet Confiável
✅ **Qdrant Standalone** (Opção 1)
- Download one-time do executável
- Funciona offline
- Dados persistem localmente
- 3 terminais (como Docker)

### Cenário 3: Testes Rápidos
⚠️ **Qdrant Memória** (Opção 3)
- Apenas para demonstrações
- Nada para instalar
- Dados não persistem

---

## 📝 Instruções para os Alunos

### Usando Qdrant Standalone

**Usar o script já criado** (na raiz do projeto existe `start-qdrant.bat`):

```powershell
# Terminal 1 - Qdrant
.\start-qdrant.bat

# Terminal 2 - Backend
cd api
.\run-local.bat

# Terminal 3 - Frontend
cd web
npm run dev
```

💡 **Nota**: O script `start-qdrant.bat` já habilita automaticamente o dashboard!

### Usando Qdrant Cloud

**Criar script helper** `api/setup-qdrant-cloud.bat`:

```bat
@echo off
echo ============================================
echo   Configurar Qdrant Cloud
echo ============================================
echo.
echo 1. Acesse: https://cloud.qdrant.io/
echo 2. Crie uma conta gratuita
echo 3. Crie um cluster (Free Tier)
echo 4. Copie a URL e API Key
echo.
echo 5. Edite o arquivo .env na raiz do projeto
echo    QDRANT_URL=sua-url-aqui
echo    QDRANT_API_KEY=sua-key-aqui
echo.
pause
```

---

## 🐛 Problemas Comuns

### Dashboard não abre / "404 Not Found" (Standalone v1.7+)

**Causa**: Dashboard não habilitado por padrão na versão 1.7+

**Solução:**
```powershell
# Use o script que habilita o dashboard
.\start-qdrant.bat

# OU inicie manualmente com configuração
cd C:\qdrant
.\qdrant.exe --config-path qdrant-config.yaml
```

**Verificar se funcionou:**
- Abra http://localhost:6333/dashboard
- Deve aparecer a interface do Qdrant
- Nos logs deve aparecer "Web UI enabled"

### Erro: "Connection refused" (Standalone)

**Causa**: Qdrant não está rodando

**Solução:**
```powershell
# Iniciar Qdrant em outro terminal
.\start-qdrant.bat
```

### Erro: "Authentication failed" (Cloud)

**Causa**: API key incorreta

**Solução:**
1. Verificar API key no Qdrant Cloud dashboard
2. Atualizar no `.env`
3. Reiniciar API

### Erro: "Cannot find qdrant.exe" (Standalone)

**Causa**: Executável não baixado

**Solução:**
1. Baixar de: https://github.com/qdrant/qdrant/releases
2. Extrair para `C:\qdrant\`
3. Verificar: `dir C:\qdrant\qdrant.exe`

### Dados perdidos ao reiniciar (Memória)

**Causa**: Modo memória não persiste

**Solução:**
- Use Standalone ou Cloud para persistência
- Ou re-ingira documentos: `curl -X POST http://localhost:8000/ingest`

---

## ✅ Checklist de Implementação

### Para Standalone
- [ ] Baixei Qdrant executável
- [ ] Extraí para `C:\qdrant\`
- [ ] Testei: `.\qdrant.exe`
- [ ] Acesso http://localhost:6333/dashboard
- [ ] `.env` configurado corretamente

### Para Cloud
- [ ] Criei conta em cloud.qdrant.io
- [ ] Criei cluster gratuito
- [ ] Copiei URL e API key
- [ ] Atualizei código do `qdrant_store.py`
- [ ] Atualizei `config.py`
- [ ] Atualizei `.env`
- [ ] Testei conexão

### Para Memória
- [ ] Atualizei código do `qdrant_store.py`
- [ ] Configurei `QDRANT_URL=memory`
- [ ] Entendi que dados não persistem

---

## 🎯 Script de Instalação Completo (Standalone)

**Criar arquivo** `instalar-qdrant-standalone.ps1`:

```powershell
Write-Host "Instalando Qdrant Standalone..." -ForegroundColor Cyan

# Criar diretório
$qdrantDir = "C:\qdrant"
if (-not (Test-Path $qdrantDir)) {
    New-Item -ItemType Directory -Path $qdrantDir
    Write-Host "✅ Pasta criada: $qdrantDir" -ForegroundColor Green
}

# Baixar
Write-Host "Baixando Qdrant..." -ForegroundColor Yellow
$version = "v1.7.0"
$url = "https://github.com/qdrant/qdrant/releases/download/$version/qdrant-x86_64-pc-windows-msvc.zip"
$zipFile = "$qdrantDir\qdrant.zip"

Invoke-WebRequest -Uri $url -OutFile $zipFile
Write-Host "✅ Download concluído" -ForegroundColor Green

# Extrair
Write-Host "Extraindo..." -ForegroundColor Yellow
Expand-Archive -Path $zipFile -DestinationPath $qdrantDir -Force
Remove-Item $zipFile

Write-Host "✅ Qdrant instalado em $qdrantDir" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar:" -ForegroundColor Cyan
Write-Host "  cd $qdrantDir" -ForegroundColor White
Write-Host "  .\qdrant.exe" -ForegroundColor White
```

**Executar:**
```powershell
.\instalar-qdrant-standalone.ps1
```

---

**✨ Escolha a melhor opção para sua turma e siga o guia acima!**

**Recomendação:** Qdrant Cloud para máxima simplicidade ou Standalone para máximo controle.

