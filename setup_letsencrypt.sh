#!/bin/bash
# Script para configurar Let's Encrypt com Certbot
# Para produção com domínio real

echo "=================================================="
echo "  🔐 SETUP Let's Encrypt - SSConstrutora"
echo "=================================================="
echo ""
echo "Este script configura certificado SSL grátis com Let's Encrypt"
echo ""

# Verificar se certbot está instalado
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot não está instalado"
    echo ""
    echo "📦 Instalação:"
    echo "   Ubuntu/Debian: sudo apt install certbot"
    echo "   macOS: brew install certbot"
    echo "   Windows: Use WSL2 ou instale manualmente em https://certbot.eff.org/"
    echo ""
    exit 1
fi

# Pedir domínio
read -p "📝 Digite seu domínio (ex: ssconstrutora.com): " DOMINIO

if [ -z "$DOMINIO" ]; then
    echo "❌ Domínio vazio"
    exit 1
fi

# Pedir email
read -p "📧 Digite seu email para notificações: " EMAIL

if [ -z "$EMAIL" ]; then
    echo "❌ Email vazio"
    exit 1
fi

# Criar diretório de certificados
mkdir -p certs

echo ""
echo "🔄 Gerando certificado para: $DOMINIO"
echo ""

# Gerar certificado (modo standalone)
sudo certbot certonly --standalone \
    -d "$DOMINIO" \
    -d "www.$DOMINIO" \
    -m "$EMAIL" \
    --agree-tos \
    --non-interactive

if [ $? -eq 0 ]; then
    # Copiar certificados para pasta do projeto
    CERT_PATH="/etc/letsencrypt/live/$DOMINIO"
    
    echo ""
    echo "✅ Certificado gerado com sucesso!"
    echo ""
    echo "📋 Copiando certificados..."
    
    # Precisa de sudo para acessar /etc/letsencrypt
    sudo cp "$CERT_PATH/fullchain.pem" certs/certificate.crt
    sudo cp "$CERT_PATH/privkey.pem" certs/private.key
    sudo chown $USER:$USER certs/*
    
    echo "✅ Certificados copiados para ./certs/"
    echo ""
    echo "🔄 Configurar renovação automática:"
    echo "   sudo certbot renew --dry-run"
    echo ""
    echo "🚀 Iniciar servidor:"
    echo "   python app.py"
    echo ""
else
    echo "❌ Erro ao gerar certificado"
    echo ""
    echo "💡 Dicas:"
    echo "   - Certifique-se que a porta 80 está livre"
    echo "   - Seu domínio deve estar apontando para este servidor"
    echo "   - Tente usar --preferred-challenges dns para DNS validation"
    exit 1
fi

# Adicionar renovação automática ao crontab
echo ""
read -p "Deseja adicionar renovação automática ao crontab? (s/n): " ADD_CRON

if [ "$ADD_CRON" = "s" ] || [ "$ADD_CRON" = "S" ]; then
    # Adicionar job para renovar certificados diariamente
    (crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet --post-hook 'systemctl restart ssconstrutora'") | crontab -
    echo "✅ Renovação automática configurada"
fi

echo ""
echo "✅ Setup Let's Encrypt concluído!"
