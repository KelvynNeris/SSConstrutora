#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para executar migrations de segurança no banco de dados."""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def executar_migration():
    """Executa as mudanças de schema para adicionar segurança."""
    try:
        conexao = mysql.connector.connect(
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "bd_ss"),
            port=int(os.getenv("DB_PORT", "3306")),
        )
        cursor = conexao.cursor()
        
        print("🔄 Executando migrations de segurança...")
        
        # 1. Adicionar colunas para recuperação de senha
        print("\n  [1/4] Adicionando colunas de token de reset...")
        try:
            cursor.execute(
                "ALTER TABLE tb_usuarios ADD token_reset_senha VARCHAR(255) NULL"
            )
            print("      ✅ Coluna 'token_reset_senha' criada")
        except mysql.connector.Error as e:
            if "Duplicate column" in str(e):
                print("      ✅ Coluna 'token_reset_senha' já existe")
            else:
                print(f"      ⚠️  {str(e)}")
        
        try:
            cursor.execute(
                "ALTER TABLE tb_usuarios ADD token_reset_expiracao DATETIME NULL"
            )
            print("      ✅ Coluna 'token_reset_expiracao' criada")
        except mysql.connector.Error as e:
            if "Duplicate column" in str(e):
                print("      ✅ Coluna 'token_reset_expiracao' já existe")
            else:
                print(f"      ⚠️  {str(e)}")
        
        # 2. Criar tabela de auditoria
        print("\n  [2/4] Criando tabela de auditoria...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_auditoria (
                id_auditoria INT AUTO_INCREMENT PRIMARY KEY,
                id_usuario INT NOT NULL,
                acao VARCHAR(100) NOT NULL,
                descricao TEXT,
                endereco_ip VARCHAR(45),
                data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_usuario) REFERENCES tb_usuarios(id_usuario) ON DELETE CASCADE,
                INDEX idx_usuario_data (id_usuario, data_hora)
            )
        """)
        print("      ✅ Tabela 'tb_auditoria' criada")
        
        # 3. Criar tabela de tentativas de login
        print("\n  [3/4] Criando tabela de tentativas de login...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_tentativas_login (
                id_tentativa INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(100) NOT NULL,
                endereco_ip VARCHAR(45),
                sucesso BOOLEAN,
                data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email_data (email, data_hora)
            )
        """)
        print("      ✅ Tabela 'tb_tentativas_login' criada")
        
        # 4. Verificar schema
        print("\n  [4/4] Verificando schema atualizado...")
        cursor.execute("DESCRIBE tb_usuarios")
        colunas = cursor.fetchall()
        colunas_novas = [col[0] for col in colunas if col[0] in ['token_reset_senha', 'token_reset_expiracao']]
        if colunas_novas:
            print(f"      ✅ Colunas presentes: {', '.join(colunas_novas)}")
        
        conexao.commit()
        cursor.close()
        conexao.close()
        
        print("\n✅ Migrations executadas com sucesso!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao executar migrations: {str(e)}\n")
        return False

if __name__ == "__main__":
    executar_migration()
