# 🔐 Guia Completo de HTTPS para SSConstrutora

## Visão Geral

O sistema agora suporta HTTPS com 3 modos diferentes:

1. **Desenvolvimento Local** - Certificado auto-assinado (fácil)
2. **Produção** - Let's Encrypt grátis (recomendado)
3. **Custom** - Seu próprio certificado

---

## ✅ O que foi adicionado

- ✅ Configuração automática de HTTPS
- ✅ Geração de certificado auto-assinado
- ✅ Headers de segurança (HSTS, CSP, X-Frame-Options, etc)
- ✅ Suporte para Let's Encrypt
- ✅ Fallback automático para HTTP se certificado indisponível

---

## 📦 Instalação de Dependências

```bash
pip install -r requirements.txt
```

Principais pacotes adicionados:
- `pyopenssl` - Para HTTPS com certificado
- `cryptography` - Para geração de certificados

---

## 🚀 Setup Rápido (Desenvolvimento)

### 1. Gerar Certificado Auto-Assinado

```bash
# Opção 1: Com OpenSSL (recomendado)
python setup_https.py

# Opção 2: Usar Python puro
python setup_https.py
```

**Resultado:**
- `certs/certificate.crt` - Certificado
- `certs/private.key` - Chave privada

### 2. Iniciar Servidor

```bash
python app.py
```

**Saída esperada:**
```
🔐 HTTPS: HTTPS com certificado custom
📋 Iniciando servidor com HTTPS...
   Certificado: ./certs/certificate.crt
🚀 Servidor iniciando em: https://0.0.0.0:8080
```

### 3. Acessar a Aplicação

```
https://localhost:8080
```

⚠️ **Aviso de Certificado:**
- O navegador mostrará "conexão não segura"
- Clique "Avançado" → "Prosseguir"
- Isso é normal para certificados auto-assinados

---

## 🌍 Setup Produção (Let's Encrypt)

### Pré-requisitos

- Domínio real (ex: ssconstrutora.com)
- Servidor Linux com acesso root
- Porta 80 livre (temporariamente para validação)

### 1. Instalação do Certbot

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install certbot
```

**CentOS/RHEL:**
```bash
sudo yum install certbot
```

**macOS:**
```bash
brew install certbot
```

**Windows:** Use WSL2 ou instale manualmente em https://certbot.eff.org/

### 2. Gerar Certificado

```bash
bash setup_letsencrypt.sh
```

Ou manualmente:
```bash
sudo certbot certonly --standalone \
    -d seu-dominio.com \
    -d www.seu-dominio.com \
    -m seu-email@example.com \
    --agree-tos
```

### 3. Copiar Certificados

```bash
mkdir -p certs
sudo cp /etc/letsencrypt/live/seu-dominio.com/fullchain.pem certs/certificate.crt
sudo cp /etc/letsencrypt/live/seu-dominio.com/privkey.pem certs/private.key
sudo chown $USER:$USER certs/*
```

### 4. Configurar Renovação Automática

Let's Encrypt certificados expiran em 90 dias. Configurar renovação automática:

```bash
# Testar renovação
sudo certbot renew --dry-run

# Adicionar ao crontab (renova diariamente)
sudo crontab -e

# Adicionar linha:
0 12 * * * certbot renew --quiet
```

---

## 🔐 Headers de Segurança Implementados

A aplicação agora adiciona automaticamente:

| Header | Valor | Função |
|--------|-------|--------|
| `Strict-Transport-Security` | `max-age=31536000` | Força HTTPS por 1 ano |
| `X-Frame-Options` | `DENY` | Previne clickjacking |
| `X-Content-Type-Options` | `nosniff` | Previne MIME sniffing |
| `X-XSS-Protection` | `1; mode=block` | XSS protection |
| `Content-Security-Policy` | `default-src 'self'` | Previne injeção de scripts |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controla referrer |
| `Permissions-Policy` | Nega geolocation, camera, mic | Bloqueia recursos perigosos |

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)

```bash
# Modo de SSL: auto, adhoc, custom
SSL_MODE=auto

# Desabilitar SSL (apenas desenvolvimento)
DISABLE_SSL=false

# Usar SSL ad-hoc (requer pyopenssl)
USE_ADHOC_SSL=false
```

### Modo Ad-hoc (Python Puro)

Se preferir não usar certificado de arquivo:

```bash
# No .env:
SSL_MODE=adhoc
USE_ADHOC_SSL=true

# Instalar pyopenssl:
pip install pyopenssl
```

---

## 📊 Verificação de Segurança

### Testar HTTPS

```bash
# Com curl
curl -k https://localhost:8080

# Com Python
python -c "import urllib.request; print(urllib.request.urlopen('https://localhost:8080').read())"
```

### Verificar Headers

```bash
curl -i https://localhost:8080
```

Você deve ver headers como:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
```

### Teste Online

Usar SSL Labs:
- https://www.ssllabs.com/ssltest/

Teste de segurança headers:
- https://securityheaders.com/

---

## ⚠️ Solução de Problemas

### "Certificado não encontrado"

```bash
# Solução: Gerar certificado
python setup_https.py
```

### Erro "pyopenssl não instalado"

```bash
pip install pyopenssl cryptography
```

### Porta 8080 em uso

```bash
# Mudar porta em app.py
app.run(port=8443, ...)  # Usar porta HTTPS padrão

# Ou verificar processo:
netstat -ano | findstr :8080  # Windows
lsof -i :8080  # Linux/Mac
```

### Certificado expirado

```bash
# Renovar Let's Encrypt
sudo certbot renew

# Ou regenerar auto-assinado
python setup_https.py
```

### Navegador recusa certificado auto-assinado

Isso é esperado para certificados auto-assinados. Opções:
1. Clique "Avançado" → "Aceitar risco"
2. Use Let's Encrypt em produção
3. Instale o certificado no navegador/SO

---

## 🔄 Próximos Passos

1. ✅ HTTPS configurado
2. ⏳ Considere usar **Nginx/Apache** como reverse proxy
3. ⏳ Implementar **HTTP/2**
4. ⏳ Adicionar **CSR (Certificate Signing Request)**
5. ⏳ Configurar **pinning de certificado**

---

## 📚 Recursos Úteis

- [Let's Encrypt Docs](https://letsencrypt.org/docs/)
- [OWASP Security Headers](https://owasp.org/www-project-secure-headers/)
- [Flask HTTPS](https://flask.palletsprojects.com/en/latest/ssl/)
- [Mozilla SSL Config Generator](https://ssl-config.mozilla.org/)

---

## 📝 Checklist de Produção

- [ ] Certificado Let's Encrypt gerado
- [ ] Renovação automática configurada
- [ ] Domínio apontando para servidor
- [ ] Porta 443 aberta no firewall
- [ ] HTTPS rodando sem erros
- [ ] Headers de segurança verificados
- [ ] Teste com SSL Labs
- [ ] Logs de acesso configurados
- [ ] Backup de certificados feito
- [ ] Plano de renovação documentado

---

**Status: ✅ HTTPS Implementado com Sucesso!**

O sistema agora está preparado para produção com criptografia end-to-end.
