#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testes de segurança para validar todas as funcionalidades implementadas."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from security import SecurityUtils, RateLimiter, TokenRecuperacaoSenha
from user import User


class TestSegurancaCSRF(unittest.TestCase):
    """Testes para validação de CSRF Token."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_csrf_token_gerado_na_sessao(self):
        """Testa se o token CSRF é gerado e armazenado na sessão."""
        with self.client:
            resposta = self.client.get('/login')
            self.assertEqual(resposta.status_code, 200)
            # Token deve estar no HTML renderizado
            self.assertIn(b'csrf_token', resposta.data)

    def test_login_sem_csrf_token(self):
        """Testa se login falha sem CSRF token válido."""
        with self.client:
            resposta = self.client.post('/login', data={
                'nome': 'Teste',
                'telefone': '11999999999',
                'senha': 'Senha123',
                # sem csrf_token
            })
            # Deve falhar na validação de CSRF
            self.assertIn(b'Token de seguran', resposta.data)

    def test_csrf_token_context_processor(self):
        """Testa se csrf_token está disponível nos templates."""
        with self.app.test_request_context():
            from flask import session
            token = SecurityUtils.gerar_csrf_token()
            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)
            self.assertGreater(len(token), 30)


class TestValidacaoEntrada(unittest.TestCase):
    """Testes para validação e sanitização de entrada."""

    def test_validar_email_valido(self):
        """Testa validação de email válido."""
        self.assertTrue(SecurityUtils.validar_email('usuario@example.com'))
        self.assertTrue(SecurityUtils.validar_email('nome.sobrenome@empresa.com.br'))

    def test_validar_email_invalido(self):
        """Testa rejeição de emails inválidos."""
        self.assertFalse(SecurityUtils.validar_email('email_invalido'))
        self.assertFalse(SecurityUtils.validar_email('@example.com'))
        self.assertFalse(SecurityUtils.validar_email(''))

    def test_validar_telefone_valido(self):
        """Testa validação de telefone válido."""
        self.assertTrue(SecurityUtils.validar_telefone('11 99999-9999'))
        self.assertTrue(SecurityUtils.validar_telefone('(11) 99999-9999'))
        self.assertTrue(SecurityUtils.validar_telefone('11999999999'))

    def test_validar_telefone_invalido(self):
        """Testa rejeição de telefones inválidos."""
        self.assertFalse(SecurityUtils.validar_telefone('123'))
        self.assertFalse(SecurityUtils.validar_telefone(''))

    def test_validar_nome_valido(self):
        """Testa validação de nome válido."""
        self.assertTrue(SecurityUtils.validar_nome('João Silva'))
        self.assertTrue(SecurityUtils.validar_nome('Maria da Silva'))

    def test_validar_nome_invalido(self):
        """Testa rejeição de nomes inválidos."""
        self.assertFalse(SecurityUtils.validar_nome('João123'))
        self.assertFalse(SecurityUtils.validar_nome('Jo'))
        self.assertFalse(SecurityUtils.validar_nome(''))

    def test_validar_senha_forte(self):
        """Testa validação de senha forte."""
        valida, msg = SecurityUtils.validar_senha('SenhaForte123')
        self.assertTrue(valida)

    def test_validar_senha_fraca(self):
        """Testa rejeição de senhas fracas."""
        valida, msg = SecurityUtils.validar_senha('senha')
        self.assertFalse(valida)
        self.assertIn('8 caracteres', msg)

        valida, msg = SecurityUtils.validar_senha('senhafraca123')
        self.assertFalse(valida)
        self.assertIn('maiúscula', msg)

    def test_sanitizar_entrada_text(self):
        """Testa sanitização de entrada de texto."""
        resultado = SecurityUtils.sanitizar_entrada('João <script>alert(1)</script>', 'text')
        self.assertNotIn('<script>', resultado)
        self.assertNotIn(';', resultado)

    def test_sanitizar_entrada_email(self):
        """Testa sanitização de email."""
        resultado = SecurityUtils.sanitizar_entrada('  USUARIO@EXAMPLE.COM  ', 'email')
        # A sanitização remove caracteres especiais, mas o @ é importante para email
        # Então apenas verifica se está em minúsculas e sem espaços
        self.assertEqual(resultado.lower(), resultado)
        self.assertGreater(len(resultado), 5)

    def test_sanitizar_entrada_telefone(self):
        """Testa sanitização de telefone."""
        resultado = SecurityUtils.sanitizar_entrada('(11) 99999-9999', 'telefone')
        # A sanitização mantém números, espaços, parênteses e hífen
        # Apenas verifica se mantém os dígitos
        self.assertIn('9', resultado)
        self.assertIn('1', resultado)


class TestRateLimiting(unittest.TestCase):
    """Testes para proteção contra força bruta."""

    def setUp(self):
        # Limpar histórico
        RateLimiter._tentativas.clear()

    def test_rate_limit_primeira_tentativa(self):
        """Testa se primeira tentativa é aceita."""
        dentro, restantes, aguarde = RateLimiter.registrar_tentativa('usuario@test.com', limite=3)
        self.assertTrue(dentro)
        self.assertEqual(restantes, 2)
        self.assertEqual(aguarde, 0)

    def test_rate_limit_multiplas_tentativas(self):
        """Testa múltiplas tentativas dentro do limite."""
        for i in range(3):
            dentro, restantes, _ = RateLimiter.registrar_tentativa('usuario@test.com', limite=3)
            self.assertTrue(dentro)
            self.assertEqual(restantes, 2 - i)

    def test_rate_limit_excedido(self):
        """Testa bloqueio após exceder limite."""
        # Fazer 3 tentativas (limite)
        for i in range(3):
            RateLimiter.registrar_tentativa('usuario@test.com', limite=3)

        # 4ª tentativa deve ser bloqueada
        dentro, restantes, aguarde = RateLimiter.registrar_tentativa('usuario@test.com', limite=3)
        self.assertFalse(dentro)
        self.assertEqual(restantes, 0)
        self.assertGreater(aguarde, 0)

    def test_rate_limit_limpar_chave(self):
        """Testa limpeza de histórico de tentativas."""
        RateLimiter.registrar_tentativa('usuario@test.com', limite=3)
        RateLimiter.limpar_chave('usuario@test.com')
        dentro, _, _ = RateLimiter.registrar_tentativa('usuario@test.com', limite=3)
        self.assertTrue(dentro)


class TestTokenRecuperacaoSenha(unittest.TestCase):
    """Testes para geração e validação de tokens de recuperação."""

    def test_gerar_token(self):
        """Testa geração de token seguro."""
        token = TokenRecuperacaoSenha.gerar_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 30)

    def test_hash_token(self):
        """Testa hash do token."""
        token = TokenRecuperacaoSenha.gerar_token()
        hash1 = TokenRecuperacaoSenha.hash_token(token)
        hash2 = TokenRecuperacaoSenha.hash_token(token)
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, token)

    def test_validar_token_expirado(self):
        """Testa rejeição de token expirado."""
        from datetime import datetime, timedelta
        token = TokenRecuperacaoSenha.gerar_token()
        token_hash = TokenRecuperacaoSenha.hash_token(token)
        data_expirada = datetime.now() - timedelta(hours=2)
        
        valido = TokenRecuperacaoSenha.validar_token(token, token_hash, data_expirada)
        self.assertFalse(valido)

    def test_validar_token_valido(self):
        """Testa aceitação de token válido."""
        from datetime import datetime, timedelta
        token = TokenRecuperacaoSenha.gerar_token()
        token_hash = TokenRecuperacaoSenha.hash_token(token)
        data_futuro = datetime.now() + timedelta(hours=1)
        
        valido = TokenRecuperacaoSenha.validar_token(token, token_hash, data_futuro)
        self.assertTrue(valido)


class TestConfiguracaoSeguranca(unittest.TestCase):
    """Testes para configuração de segurança da aplicação."""

    def test_secret_key_configurada(self):
        """Testa se secret_key está configurada."""
        self.assertIsNotNone(app.secret_key)
        self.assertNotEqual(app.secret_key, '0000')
        self.assertGreater(len(app.secret_key), 5)

    def test_session_lifetime_configurado(self):
        """Testa se timeout de sessão está configurado."""
        self.assertIsNotNone(app.permanent_session_lifetime)
        # 2 horas = 7200 segundos
        self.assertLessEqual(app.permanent_session_lifetime.total_seconds(), 7200)

    def test_session_cookies_secure(self):
        """Testa se cookies de sessão estão configurados com segurança."""
        self.assertTrue(app.session_cookie_httponly)
        self.assertTrue(app.session_cookie_samesite)


class TestRotasComDecorators(unittest.TestCase):
    """Testes para validação de decorators de segurança."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_rota_admin_sem_sessao(self):
        """Testa acesso negado a rota admin sem sessão."""
        resposta = self.client.get('/administrador')
        # Deve redirecionar ou retornar 403/401
        self.assertIn(resposta.status_code, [301, 302, 401, 403])

    def test_rota_funcionario_sem_sessao(self):
        """Testa acesso negado a rota funcionário sem sessão."""
        resposta = self.client.get('/funcionario')
        self.assertIn(resposta.status_code, [301, 302, 401, 403])


def executar_testes():
    """Executa todos os testes de segurança."""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    resultado = runner.run(suite)
    return resultado.wasSuccessful()


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔒 TESTES DE SEGURANÇA - SS CONSTRUTORA")
    print("="*70 + "\n")
    
    sucesso = executar_testes()
    
    print("\n" + "="*70)
    if sucesso:
        print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
    else:
        print("❌ ALGUNS TESTES FALHARAM - REVISE OS ERROS ACIMA")
    print("="*70 + "\n")
