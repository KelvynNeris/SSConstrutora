#!/usr/bin/env python3
"""
Teste de configuração HTTPS sem iniciar o servidor
"""

import sys
import os
import ssl

os.chdir("c:/Users/kelvy/OneDrive/Desktop/Programas/SSConstrutora")

print("=" * 70)
print("  ✅ DIAGNÓSTICO HTTPS - SSConstrutora")
print("=" * 70)
print()

# 1. Verificar imports
print("1️⃣  Verificando imports...")
try:
    from app import app
    from ssl_config import criar_contexto_ssl, verificar_https_disponivel
    from pathlib import Path
    print("   ✅ Todos os módulos importados com sucesso\n")
except Exception as e:
    print(f"   ❌ Erro ao importar: {e}\n")
    sys.exit(1)

# 2. Verificar certificados
print("2️⃣  Verificando certificados...")
cert_dir = Path("certs")
cert_file = cert_dir / "certificate.crt"
key_file = cert_dir / "private.key"

if cert_file.exists():
    size_cert = cert_file.stat().st_size
    print(f"   ✅ Certificado: {cert_file} ({size_cert} bytes)")
else:
    print(f"   ❌ Certificado não encontrado: {cert_file}\n")
    sys.exit(1)

if key_file.exists():
    size_key = key_file.stat().st_size
    print(f"   ✅ Chave privada: {key_file} ({size_key} bytes)")
else:
    print(f"   ❌ Chave privada não encontrada: {key_file}\n")
    sys.exit(1)

print()

# 3. Verificar SSL Context
print("3️⃣  Verificando contexto SSL...")
try:
    ctx = criar_contexto_ssl()
    print(f"   ✅ Tipo: {type(ctx).__name__}")
    
    if isinstance(ctx, ssl.SSLContext):
        print(f"   ✅ SSLContext validado")
        print(f"   ✅ Protocolo: {ctx.protocol}")
        print(f"   ✅ Opcções de verificação: {ctx.verify_mode}")
    elif ctx == "adhoc":
        print(f"   ✅ Modo Ad-hoc (pyopenssl)")
    elif ctx is None:
        print(f"   ⚠️  Contexto é None (HTTP)")
    else:
        print(f"   ⚠️  Contexto desconhecido: {ctx}")
    
    print()
except Exception as e:
    print(f"   ❌ Erro ao criar contexto: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Verificar HTTPS disponível
print("4️⃣  Verificando disponibilidade de HTTPS...")
try:
    disponivel, mensagem = verificar_https_disponivel()
    if disponivel:
        print(f"   ✅ HTTPS DISPONÍVEL")
        print(f"   📌 Status: {mensagem}")
    else:
        print(f"   ❌ HTTPS NÃO DISPONÍVEL")
        print(f"   📌 Motivo: {mensagem}\n")
        sys.exit(1)
    
    print()
except Exception as e:
    print(f"   ❌ Erro: {e}\n")
    sys.exit(1)

# 5. Testar carregamento do certificado
print("5️⃣  Testando carregamento do certificado...")
try:
    test_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    test_ctx.load_cert_chain(str(cert_file), str(key_file))
    print(f"   ✅ Certificado carregado com sucesso")
    print(f"   ✅ Pronto para usar com Flask")
    print()
except Exception as e:
    print(f"   ❌ Erro ao carregar certificado: {e}\n")
    sys.exit(1)

# 6. Resumo final
print("=" * 70)
print("  ✅ DIAGNÓSTICO COMPLETO - TUDO OK!")
print("=" * 70)
print()
print("  🚀 Para iniciar o servidor:")
print("     python app.py")
print()
print("  🌐 Após iniciar, acesse:")
print("     https://localhost:8080")
print()
print("  ⚠️  Você verá um aviso de certificado (normal para auto-assinado)")
print("     Clique 'Avançado' → 'Aceitar risco' no navegador")
print()
print("=" * 70)
