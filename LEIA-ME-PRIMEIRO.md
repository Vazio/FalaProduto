# 👋 Bem-vindo ao FalaProduto RAG System!

## 🎯 Comece por Aqui

### Para Formação Completa (RECOMENDADO)

📚 **[GUIA-FORMACAO.md](GUIA-FORMACAO.md)** - Guia Master Completo

Este guia único contém TUDO que você precisa:
- ✅ Instalação passo a passo
- ✅ Primeiro uso e testes
- ✅ Comandos essenciais
- ✅ Validação com ground truth
- ✅ Configuração de embeddings (local vs Azure)
- ✅ Desenvolvimento e customização
- ✅ Troubleshooting completo
- ✅ Exercícios práticos

⏱️ **Tempo estimado:** 4-6 horas para domínio completo

---

## 🚀 Quick Start (3 Passos)

### 1. Configurar Ambiente
```powershell
copy env.example .env
notepad .env  # Adicione suas chaves API
```

### 2. Instalar
```powershell
cd api
python -m venv venv
.\install-all.bat

cd ..\web
npm install
```

### 3. Iniciar

**Com Docker (3 terminais):**
```powershell
# Terminal 1: Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 2: Backend
cd api
.\run-local.bat

# Terminal 3: Frontend
cd web
npm run dev
```

**Sem Docker?** Veja: [ALTERNATIVAS-SEM-DOCKER.md](ALTERNATIVAS-SEM-DOCKER.md)

**Acesse:** http://localhost:3000

---

## 📁 Estrutura Simplificada

```
FalaProduto/
├── 📚 GUIA-FORMACAO.md       ⭐ COMECE AQUI!
├── 📖 README.md               Docs técnicas
│
├── api/                      Backend Python
│   ├── install-all.bat       Instalar dependências
│   └── run-local.bat         Rodar API
│
├── web/                      Frontend Next.js
│   └── package.json          Dependências
│
├── data/
│   ├── pdfs/                 Seus documentos
│   └── groundtruth/          Q&A para validação
│
└── .env                      Suas configurações
```

---

## ❓ Precisa de Ajuda?

1. **Consulte primeiro:** [GUIA-FORMACAO.md](GUIA-FORMACAO.md) → Seção "Problemas Comuns"
2. **Verificar logs:** Nos terminais abertos
3. **Pedir ajuda:** Professor ou colegas

---

## ✅ Checklist Rápido

- [ ] Python 3.11+ instalado
- [ ] Node.js 20+ instalado
- [ ] Docker Desktop instalado e rodando (ou alternativa sem Docker)
- [ ] Chaves API (OpenAI ou Azure) obtidas
- [ ] `.env` configurado
- [ ] Li o [GUIA-FORMACAO.md](GUIA-FORMACAO.md)

---

**🎉 Pronto para começar? Abra o [GUIA-FORMACAO.md](GUIA-FORMACAO.md)!**

