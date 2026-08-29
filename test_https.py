#!/usr/bin/env python3
"""
Teste rápido do servidor HTTPS
Inicia por 5 segundos e testa conexão
"""

import sys
import time
import threading
import urllib3
from pathlib import Path

# Desabilitar warnings de certificado auto-assinado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def iniciar_servidor():
    """Inicia o servidor Flask em thread separada."""
    from app import app
    from ssl_config import criar_contexto_ssl
    
    contexto_ssl = criar_contexto_ssl()
    print(f"🔐 Contexto SSL: {type(contexto_ssl).__name__}")
    
    try:
        app.run(
            debug=False,
            host="127.0.0.1",
            port=8080,
            ssl_context=contexto_ssl,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def testar_conexao():
    """Testa conexão HTTPS após alguns segundos."""
    time.sleep(3)  # Dar tempo para servidor iniciar
    
    print("\n🧪 Testando conexão HTTPS...")
    
    try:
        import urllib.request
        import ssl
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        response = urllib.request.urlopen('https://127.0.0.1:8080/login', context=ctx, timeout=5)
        html = response.read().decode('utf-8')
        
        if '<title>' in html and len(html) > 100:
            print("✅ Conexão HTTPS bem-sucedida!")
            print(f"📄 Resposta: {len(html)} bytes recebidos")
            return True
        else:
            print("❌ Resposta inválida")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  🔐 Teste de HTTPS - SSConstrutora")
    print("=" * 60)
    
    # Iniciar servidor em thread
    servidor_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor_thread.start()
    
    # Testar conexão
    sucesso = testar_conexao()
    
    # Aguardar um pouco antes de sair
    time.sleep(2)
    
    if sucesso:
        print("\n✅ HTTPS está funcionando corretamente!")
        sys.exit(0)
    else:
        print("\n❌ Problema no HTTPS")
        sys.exit(1)
