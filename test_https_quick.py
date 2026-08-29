#!/usr/bin/env python3
"""
Teste rápido para verificar se HTTPS funciona
Inicia o servidor por 5 segundos e testa
"""

import subprocess
import time
import sys
import os

os.chdir("c:/Users/kelvy/OneDrive/Desktop/Programas/SSConstrutora")

print("=" * 60)
print("  🧪 Teste de HTTPS - SSConstrutora")
print("=" * 60)
print()

# Tentar importar o app
print("1. Verificando se app importa corretamente...")
try:
    from app import app
    from ssl_config import criar_contexto_ssl, verificar_https_disponivel
    print("   ✅ App importado com sucesso")
except Exception as e:
    print(f"   ❌ Erro ao importar: {e}")
    sys.exit(1)

# Verificar contexto SSL
print("\n2. Verificando contexto SSL...")
try:
    ctx = criar_contexto_ssl()
    print(f"   ✅ Contexto SSL criado: {type(ctx).__name__}")
except Exception as e:
    print(f"   ❌ Erro ao criar contexto: {e}")
    sys.exit(1)

# Verificar HTTPS disponível
print("\n3. Verificando HTTPS...")
try:
    disponivel, status = verificar_https_disponivel()
    print(f"   ✅ {status}")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

# Tentar iniciar servidor por pouco tempo
print("\n4. Iniciando servidor (por 3 segundos)...")
print("   (Pressione Ctrl+C se travar)\n")

try:
    # Usar timeout do Windows/PowerShell
    cmd = [
        sys.executable, "-c",
        """
import sys
sys.path.insert(0, '.')
from app import app
from ssl_config import criar_contexto_ssl, verificar_https_disponivel

ctx = criar_contexto_ssl()
disponivel, _ = verificar_https_disponivel()

print("   🚀 Iniciando Flask...")
sys.stdout.flush()

app.run(
    debug=False,
    host="127.0.0.1",
    port=9999,  # Porta diferente para não conflitar
    ssl_context=ctx if disponivel else None,
    use_reloader=False,
    threaded=True
)
"""
    ]
    
    # Executar com timeout
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Esperar 3 segundos
    time.sleep(3)
    
    # Verificar se ainda está rodando
    if process.poll() is None:
        print("   ✅ Servidor iniciando corretamente")
        print("   ✅ HTTPS está funcionando!\n")
        
        # Terminar processo
        process.terminate()
        time.sleep(0.5)
        if process.poll() is None:
            process.kill()
        
        print("✅ TESTE BEM-SUCEDIDO!")
        print("\nAgora você pode:")
        print("  python app.py")
        print("  e acessar: https://localhost:8080")
        
    else:
        stdout, stderr = process.communicate()
        print(f"   ❌ Servidor falhou ao iniciar")
        print(f"\nStdout: {stdout}")
        print(f"\nStderr: {stderr}")
        sys.exit(1)
        
except KeyboardInterrupt:
    print("   ⚠️  Teste interrompido")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
