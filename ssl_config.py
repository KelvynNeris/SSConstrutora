"""
Configuração de HTTPS/SSL para Flask
"""

import os
import ssl
from pathlib import Path

# Diretor de certificados
CERT_DIR = Path(__file__).parent / "certs"
CERT_FILE = CERT_DIR / "certificate.crt"
KEY_FILE = CERT_DIR / "private.key"

# Configurações de SSL
SSL_CONFIG = {
    # Modo de SSL
    "mode": os.getenv("SSL_MODE", "auto"),  # auto, adhoc, custom
    
    # Certificado e chave privada (para custom)
    "certfile": str(CERT_FILE) if CERT_FILE.exists() else None,
    "keyfile": str(KEY_FILE) if KEY_FILE.exists() else None,
    
    # Configurações adicionais
    "ssl_context": "adhoc" if os.getenv("USE_ADHOC_SSL", "false").lower() == "true" else None,
}

def criar_contexto_ssl():
    """
    Cria um contexto SSL apropriado usando ssl.SSLContext.
    Retorna um SSLContext ou None.
    """
    
    # Se modo está desabilitado
    if os.getenv("DISABLE_SSL", "false").lower() == "true":
        return None
    
    # Modo auto-detect
    if SSL_CONFIG["mode"] == "auto":
        # Se tem certificado e chave, usar custom
        if SSL_CONFIG["certfile"] and SSL_CONFIG["keyfile"]:
            try:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(SSL_CONFIG["certfile"], SSL_CONFIG["keyfile"])
                return context
            except Exception as e:
                print(f"⚠️  Erro ao carregar certificado: {e}")
                return None
        # Senão, tentar adhoc
        try:
            import OpenSSL
            return "adhoc"
        except ImportError:
            return None
    
    # Modo adhoc
    elif SSL_CONFIG["mode"] == "adhoc":
        try:
            import OpenSSL
            return "adhoc"
        except ImportError:
            print("❌ pyopenssl não instalado para modo adhoc")
            return None
    
    # Modo custom
    elif SSL_CONFIG["mode"] == "custom":
        if SSL_CONFIG["certfile"] and SSL_CONFIG["keyfile"]:
            try:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(SSL_CONFIG["certfile"], SSL_CONFIG["keyfile"])
                return context
            except Exception as e:
                print(f"❌ Erro ao carregar certificado: {e}")
                return None
    
    return None

def obter_contexto_ssl():
    """
    Retorna o contexto SSL apropriado.
    Opções:
    - None: HTTP normal
    - "adhoc": HTTPS ad-hoc (requer pyopenssl)
    - SSLContext: contexto SSL configurado
    """
    return criar_contexto_ssl()

def verificar_https_disponivel():
    """Verifica se HTTPS está disponível."""
    contexto = criar_contexto_ssl()
    
    if contexto is None:
        # Verificar se é porque está desabilitado
        if os.getenv("DISABLE_SSL", "false").lower() == "true":
            return False, "HTTPS desabilitado via DISABLE_SSL"
        # Verificar se é porque os arquivos não existem
        if not SSL_CONFIG["certfile"] or not SSL_CONFIG["keyfile"]:
            return False, f"Certificado não encontrado em {CERT_DIR}"
        return False, "Erro ao criar contexto SSL"
    
    if contexto == "adhoc":
        try:
            import OpenSSL
            return True, "HTTPS modo ad-hoc (pyopenssl)"
        except ImportError:
            return False, "pyopenssl não instalado. Execute: pip install pyopenssl"
    
    # É um SSLContext
    return True, f"HTTPS com certificado custom ({CERT_FILE.name})"

if __name__ == "__main__":
    disponivel, mensagem = verificar_https_disponivel()
    print(f"HTTPS Disponível: {'✅' if disponivel else '❌'}")
    print(f"Status: {mensagem}")

