# 📊 Solução: Dashboard do Qdrant 1.7+ não abre

## 🔍 O Problema

A partir da versão 1.7 do Qdrant, o dashboard (Web UI) **não é mais habilitado por padrão** por razões de segurança. Isso afeta quem usa o Qdrant standalone (executável local, sem Docker).

## ✅ Solução Rápida

### Se você está usando Qdrant standalone no Windows:

1. **Pare o Qdrant** se estiver rodando (Ctrl+C no terminal)

2. **Execute o novo script** na raiz do projeto:
   ```powershell
   .\start-qdrant.bat
   ```

3. **Acesse o dashboard**:
   - Abra no navegador: **http://localhost:6333/dashboard**
   - Deve aparecer a interface do Qdrant

## 📁 Arquivos Criados

Este projeto agora inclui:

### 1. `qdrant-config.yaml`
Arquivo de configuração que habilita o dashboard:
```yaml
web_ui:
  enabled: true
```

### 2. `start-qdrant.bat`
Script que:
- Verifica se o Qdrant está instalado
- Copia a configuração
- Inicia o Qdrant com dashboard habilitado
- Mostra os links de acesso

## 🎯 Como Usar

### Workflow Completo

```powershell
# Terminal 1 - Qdrant com Dashboard
.\start-qdrant.bat

# Terminal 2 - Backend
cd api
.\run-local.bat

# Terminal 3 - Frontend
cd web
npm run dev
```

### Acessar

- 📊 **Dashboard Qdrant**: http://localhost:6333/dashboard
- 🔌 **API Qdrant**: http://localhost:6333
- 🖥️ **Backend API**: http://localhost:8000
- 🌐 **Frontend**: http://localhost:3000

## 🔧 Solução Manual (Alternativa)

Se preferir fazer manualmente:

1. Copie `qdrant-config.yaml` para `C:\qdrant\`
2. Execute:
   ```powershell
   cd C:\qdrant
   .\qdrant.exe --config-path qdrant-config.yaml
   ```

## ✅ Como Verificar se Funcionou

### Nos logs do Qdrant você deve ver:
```
Qdrant | high-performance vector search at scale
Version: 1.7.x
Listening on http://0.0.0.0:6333
Web UI enabled          ← Deve aparecer esta linha!
```

### No navegador:
- http://localhost:6333/dashboard deve abrir a interface
- Você verá a lista de coleções, pontos, etc.

## 🐛 Problemas?

### Dashboard ainda não abre

**Verificar:**
1. Qdrant foi iniciado com o `start-qdrant.bat`?
2. Nos logs aparece "Web UI enabled"?
3. Está acessando http://localhost:6333/dashboard (com /dashboard no final)?

**Solução:**
```powershell
# Parar o Qdrant (Ctrl+C)
# Iniciar novamente com o script
.\start-qdrant.bat
```

### Erro: "Qdrant não encontrado"

**Causa:** Qdrant não está instalado em `C:\qdrant\`

**Solução:**
1. Baixe: https://github.com/qdrant/qdrant/releases
2. Procure: `qdrant-x86_64-pc-windows-msvc.zip`
3. Extraia para: `C:\qdrant\`

Veja instruções completas em `ALTERNATIVAS-SEM-DOCKER.md`

### Porta 6333 já em uso

**Causa:** Outra instância do Qdrant ou outro processo

**Solução:**
```powershell
# Ver o que está usando a porta
netstat -ano | findstr :6333

# Parar processos do Qdrant
taskkill /F /IM qdrant.exe
```

## 📚 Mais Informações

- Documentação completa: `ALTERNATIVAS-SEM-DOCKER.md`
- Documentação oficial: https://qdrant.tech/documentation/
- Releases do Qdrant: https://github.com/qdrant/qdrant/releases

## 💡 Dica

O dashboard é útil para:
- ✅ Ver as coleções criadas
- ✅ Inspecionar vetores e metadados
- ✅ Fazer queries de teste
- ✅ Verificar o número de documentos
- ✅ Debug e monitoramento

---

**✨ Agora o dashboard está habilitado e funcionando!**

