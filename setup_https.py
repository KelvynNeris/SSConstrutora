#!/usr/bin/env python3
"""
Script para gerar certificado SSL auto-assinado para desenvolvimento.
Para produção, use Let's Encrypt (veja: setup_letsencrypt.sh)
"""

import subprocess
import os
import sys
from pathlib import Path

def criar_certificado_autoassinado():
    """Gera certificado auto-assinado válido por 365 dias."""
    
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / "certificate.crt"
    key_file = cert_dir / "private.key"
    
    # Verificar se já existe
    if cert_file.exists() and key_file.exists():
        print("✅ Certificado já existe em ./certs/")
        return True
    
    print("🔐 Gerando certificado SSL auto-assinado...")
    print("   Este certificado é para DESENVOLVIMENTO apenas!")
    
    try:
        # Gerar chave privada e certificado
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:4096",
            "-keyout", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-nodes",
            "-subj", "/C=BR/ST=SP/L=SaoPaulo/O=SSConstrutora/CN=localhost"
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        print(f"✅ Certificado criado em: {cert_file}")
        print(f"✅ Chave privada em: {key_file}")
        print("\n⚠️  IMPORTANTE:")
        print("   - Este certificado é AUTO-ASSINADO (não confiável)")
        print("   - O navegador mostrará aviso de segurança")
        print("   - Para PRODUÇÃO, use Let's Encrypt\n")
        
        return True
        
    except FileNotFoundError:
        print("❌ OpenSSL não encontrado. Instalando...")
        print("\n📦 Windows: Instale OpenSSL ou use WSL2")
        print("📦 macOS: brew install openssl")
        print("📦 Linux: sudo apt install openssl")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao gerar certificado: {e}")
        return False

def gerar_certificado_python():
    """Alternativa usando Python puro (sem OpenSSL)."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
        
        print("🔐 Gerando certificado usando Python (cryptography)...")
        
        cert_dir = Path("certs")
        cert_dir.mkdir(exist_ok=True)
        
        cert_file = cert_dir / "certificate.crt"
        key_file = cert_dir / "private.key"
        
        # Gerar chave privada
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Gerar certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"SP"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"SaoPaulo"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"SSConstrutora"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())
        
        # Salvar certificado
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Salvar chave privada
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ Certificado criado em: {cert_file}")
        print(f"✅ Chave privada em: {key_file}")
        return True
        
    except ImportError:
        print("❌ Pacote 'cryptography' não instalado")
        print("   Execute: pip install cryptography")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("=" * 60)
    print("  🔐 SETUP HTTPS - SSConstrutora")
    print("=" * 60 + "\n")
    
    # Tentar com OpenSSL
    if criar_certificado_autoassinado():
        print("\n✅ HTTPS configurado!")
        print("\n🚀 Para iniciar com HTTPS:")
        print("   python app.py")
        return 0
    
    # Fallback para Python puro
    print("\n⚠️  Tentando alternativa com Python...\n")
    if gerar_certificado_python():
        print("\n✅ HTTPS configurado!")
        print("\n🚀 Para iniciar com HTTPS:")
        print("   python app.py")
        return 0
    
    print("\n❌ Não foi possível criar certificado")
    return 1

if __name__ == "__main__":
    sys.exit(main())
