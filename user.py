from hashlib import sha256
from hmac import compare_digest
from random import randint
import re

from conexao import Conexao


class User:
    def __init__(self):
        self.id_usuario = None
        self.nome = None
        self.tel = None
        self.email = None
        self.senha = None
        self.tipo = None
        self.logado = False
        self.aprovado = False
        self.primeiro_login = False
        self.pendente = False
        self.erro = None

    @staticmethod
    def _hash_senha(senha):
        return sha256(senha.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalizar_telefone(telefone):
        return re.sub(r"\D", "", telefone)

    def cadastrar(self, nome, telefone, email, senha, tipo="Funcionario"):
        """Cadastra um usuário aguardando aprovação do administrador."""
        self.erro = None
        tipo = tipo if tipo in ("Administrador", "Funcionario") else "Funcionario"
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor()
            email = email.strip().lower()
            telefone = self._normalizar_telefone(telefone)
            cursor.execute("SELECT id_usuario FROM tb_usuarios WHERE email = %s OR telefone = %s", (email, telefone))
            if cursor.fetchone():
                self.erro = "E-mail ou telefone já cadastrado."
                return False
            cursor.execute(
                """INSERT INTO tb_usuarios
                   (nome, email, senha, telefone, tipo_usuario, codigo_confirmacao, primeiro_login, aprovado)
                   VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE)""",
                (nome.strip(), email, self._hash_senha(senha), telefone, tipo, f"{randint(0, 9999):04d}"),
            )
            conexao.commit()
            return True
        except Exception:
            if conexao:
                conexao.rollback()
            self.erro = "Não foi possível concluir o cadastro agora."
            return False
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    def verificar_duplicidade(self, email, telefone):
        conexao = Conexao.conectar()
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT id_usuario FROM tb_usuarios WHERE email = %s OR telefone = %s", (email, self._normalizar_telefone(telefone)))
            return bool(cursor.fetchone())
        finally:
            cursor.close()
            conexao.close()

    def entrar(self, nome, telefone, senha):
        """Autentica por nome, telefone e senha, exigindo aprovação administrativa."""
        self.erro = None
        self.pendente = False
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor()
            cursor.execute(
                     """SELECT id_usuario, nome, email, senha, telefone, tipo_usuario, aprovado, primeiro_login
                   FROM tb_usuarios WHERE LOWER(nome) = LOWER(%s) AND telefone = %s""",
                (nome.strip(), self._normalizar_telefone(telefone)),
            )
            resultado = cursor.fetchone()
            if not resultado or not compare_digest(self._hash_senha(senha), resultado[3]):
                self.erro = "Nome, telefone ou senha inválidos."
                return False
            if not resultado[6]:
                self.pendente = True
                self.erro = "Seu cadastro ainda aguarda aprovação do administrador."
                return False
            self.id_usuario, self.nome, self.email, self.senha, self.tel, self.tipo, self.aprovado, self.primeiro_login = resultado
            self.logado = True
            return True
        except Exception:
            self.erro = "Não foi possível realizar o login agora."
            return False
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    def atualizar_primeiro_acesso(self, id_usuario, nome, telefone, email, senha):
        """Atualiza os dados do administrador pré-cadastrado e encerra o primeiro acesso."""
        self.erro = None
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor()
            email = email.strip().lower()
            telefone = self._normalizar_telefone(telefone)
            cursor.execute(
                """SELECT id_usuario FROM tb_usuarios
                   WHERE (email = %s OR telefone = %s) AND id_usuario <> %s""",
                (email, telefone, id_usuario),
            )
            if cursor.fetchone():
                self.erro = "E-mail ou telefone já cadastrado por outro usuário."
                return False
            cursor.execute(
                """UPDATE tb_usuarios
                   SET nome = %s, telefone = %s, email = %s, senha = %s, primeiro_login = FALSE
                   WHERE id_usuario = %s""",
                (nome.strip(), telefone, email, self._hash_senha(senha), id_usuario),
            )
            if cursor.rowcount != 1:
                self.erro = "Usuário não encontrado."
                conexao.rollback()
                return False
            conexao.commit()
            self.id_usuario = id_usuario
            self.nome = nome.strip()
            self.tel = telefone
            self.email = email
            self.primeiro_login = False
            return True
        except Exception:
            if conexao:
                conexao.rollback()
            self.erro = "Não foi possível atualizar seus dados agora."
            return False
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()