import secrets
import hashlib
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import session, abort
from collections import defaultdict
import time

class SecurityUtils:
    """Utilitários de segurança para o projeto."""
    
    @staticmethod
    def gerar_csrf_token():
        """Gera um token CSRF seguro."""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return session['csrf_token']
    
    @staticmethod
    def validar_csrf_token(token_recebido):
        """Valida o token CSRF recebido."""
        token_sessao = session.get('csrf_token', '')
        return token_recebido and token_sessao and secrets.compare_digest(token_recebido, token_sessao)
    
    @staticmethod
    def validar_email(email):
        """Valida formato de e-mail."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip().lower()) is not None
    
    @staticmethod
    def validar_telefone(telefone):
        """Valida formato de telefone (11 dígitos mínimo)."""
        digitos = re.sub(r'\D', '', telefone)
        return len(digitos) >= 11
    
    @staticmethod
    def validar_nome(nome):
        """Valida nome (pelo menos 3 caracteres, sem números)."""
        nome = nome.strip()
        if len(nome) < 3:
            return False
        # Permite letras, espaços e alguns caracteres especiais
        pattern = r'^[a-zA-ZÀ-ÿ\s\-\'\.]+$'
        return re.match(pattern, nome) is not None
    
    @staticmethod
    def validar_senha(senha):
        """Valida força de senha (mínimo 8 caracteres, com números e maiúsculas)."""
        if len(senha) < 8:
            return False, "Mínimo de 8 caracteres"
        if not re.search(r'\d', senha):
            return False, "Deve conter pelo menos um número"
        if not re.search(r'[A-Z]', senha):
            return False, "Deve conter pelo menos uma letra maiúscula"
        return True, "OK"
    
    @staticmethod
    def sanitizar_entrada(valor, tipo="text"):
        """Remove caracteres perigosos da entrada."""
        if not isinstance(valor, str):
            return ""
        
        valor = valor.strip()
        
        if tipo == "email":
            # Permite apenas caracteres seguros em emails
            return re.sub(r'[^a-zA-Z0-9._%+@-]', '', valor).lower()
        elif tipo == "telefone":
            # Permite dígitos, +, -, (, ), espaço
            return re.sub(r'[^\d+\-\(\)\s]', '', valor)
        elif tipo == "numero":
            # Permite apenas dígitos, ponto e hífen
            return re.sub(r'[^\d\.\-]', '', valor)
        else:  # text
            # Remove caracteres perigosos mas permite espaços e pontuação básica
            return re.sub(r'[<>\"\'%;()&]', '', valor)


class RateLimiter:
    """Implementa proteção contra força bruta (rate limiting)."""
    
    _tentativas = defaultdict(list)
    
    @staticmethod
    def registrar_tentativa(chave, limite=5, janela_segundos=300):
        """
        Registra uma tentativa e retorna se está dentro do limite.
        
        Args:
            chave: identificador único (ex: "login_usuario@email.com")
            limite: número máximo de tentativas
            janela_segundos: janela de tempo em segundos
        
        Returns:
            (dentro_limite, tentativas_restantes, aguarde_segundos)
        """
        agora = time.time()
        
        # Remove tentativas antigas
        RateLimiter._tentativas[chave] = [
            t for t in RateLimiter._tentativas[chave]
            if agora - t < janela_segundos
        ]
        
        tentativas_atuais = len(RateLimiter._tentativas[chave])
        
        if tentativas_atuais >= limite:
            # Retorna tempo até a tentativa mais antiga expirar
            primeira_tentativa = RateLimiter._tentativas[chave][0]
            aguarde = int(janela_segundos - (agora - primeira_tentativa)) + 1
            return False, 0, aguarde
        
        # Registra nova tentativa
        RateLimiter._tentativas[chave].append(agora)
        tentativas_restantes = limite - tentativas_atuais - 1
        
        return True, tentativas_restantes, 0
    
    @staticmethod
    def limpar_chave(chave):
        """Limpa o histórico de tentativas de uma chave."""
        if chave in RateLimiter._tentativas:
            del RateLimiter._tentativas[chave]


class TokenRecuperacaoSenha:
    """Gerencia tokens para recuperação de senha."""
    
    @staticmethod
    def gerar_token():
        """Gera um token seguro para recuperação de senha."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_token(token):
        """Faz hash do token para armazenar no banco."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def validar_token(token_fornecido, token_hash_db, data_expiracao):
        """
        Valida se o token está correto e dentro do prazo.
        
        Args:
            token_fornecido: token enviado pelo usuário
            token_hash_db: hash armazenado no banco
            data_expiracao: datetime de expiração
        
        Returns:
            bool: válido ou não
        """
        if datetime.now() > data_expiracao:
            return False
        
        hash_fornecido = TokenRecuperacaoSenha.hash_token(token_fornecido)
        return secrets.compare_digest(hash_fornecido, token_hash_db)


def requer_sessao(f):
    """Decorator que requer uma sessão válida."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('usuario_id'):
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


def requer_admin(f):
    """Decorator que requer sessão de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('usuario_tipo') != 'Administrador' or not session.get('usuario_id'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def requer_funcionario(f):
    """Decorator que requer sessão de funcionário."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('usuario_tipo') != 'Funcionario' or not session.get('usuario_id'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
