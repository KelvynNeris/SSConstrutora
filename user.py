from hashlib import sha256
from hmac import compare_digest
from random import randint
import re

from conexao import Conexao
from email_service import enviar_email_admin, enviar_email_codigo_confirmacao


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

    def gerar_codigo_confirmacao(self, email):
        """Gera e envia um código de confirmação para o e-mail do cadastro."""
        self.codigo_confirmacao = f"{randint(0, 9999):04d}"
        self.tentativas_codigo = 0
        enviar_email_codigo_confirmacao(email.strip().lower(), self.codigo_confirmacao)
        return self.codigo_confirmacao

    def validar_codigo_cadastro(self, codigo):
        """Valida o código recebido e retorna se ainda há tentativas restantes."""
        codigo = str(codigo or "").strip()
        if codigo == str(self.codigo_confirmacao or ""):
            self.tentativas_codigo = 0
            return True

        self.tentativas_codigo = (self.tentativas_codigo or 0) + 1
        return False

    def cadastrar(self, nome, telefone, email, senha, tipo="Funcionario", codigo_confirmacao=None):
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
            codigo_final = codigo_confirmacao or f"{randint(0, 9999):04d}"
            cursor.execute(
                """INSERT INTO tb_usuarios
                   (nome, email, senha, telefone, tipo_usuario, codigo_confirmacao, primeiro_login, aprovado)
                   VALUES (%s, %s, %s, %s, %s, %s, TRUE, FALSE)""",
                (nome.strip(), email, self._hash_senha(senha), telefone, tipo, codigo_final),
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

    @staticmethod
    def pedir_material(id_funcionario, obra, id_material, quantidade, apresentacao, observacao=""):
        """Registra uma requisição de material aguardando análise do administrador."""
        if not obra or not apresentacao or float(quantidade) <= 0:
            raise ValueError("Informe obra, apresentação e uma quantidade válida.")

        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor()
            cursor.execute("SELECT id_material FROM tb_materiais WHERE id_material = %s AND ativo = TRUE", (id_material,))
            if not cursor.fetchone():
                raise ValueError("Material inválido ou inativo.")
            cursor.execute(
                """INSERT INTO tb_pedidos
                   (id_funcionario, id_material, obra, quantidade, apresentacao, status, observacao_admin)
                   VALUES (%s, %s, %s, %s, %s, 'Pendente', %s)""",
                (id_funcionario, id_material, obra.strip(), quantidade, apresentacao, observacao.strip() or None),
            )
            id_pedido = cursor.lastrowid

            cursor.execute(
                """SELECT u.nome AS funcionario_nome, m.nome AS material_nome, m.unidade
                   FROM tb_usuarios u
                   CROSS JOIN tb_materiais m
                   WHERE u.id_usuario = %s AND m.id_material = %s""",
                (id_funcionario, id_material),
            )
            dados_pedido = cursor.fetchone()

            conexao.commit()

            if dados_pedido:
                enviar_email_admin(
                    id_pedido=id_pedido,
                    nome_funcionario=dados_pedido[0],
                    nome_obra=obra.strip(),
                    material=dados_pedido[1],
                    quantidade=quantidade,
                    unidade=dados_pedido[2] or "unidade",
                )

            return id_pedido
        except Exception:
            if conexao:
                conexao.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    @staticmethod
    def listar_pedidos(id_funcionario, incluir_entregues=False):
        """Retorna as requisições do funcionário com os dados do material."""
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor(dictionary=True)
            sql = """
                SELECT p.id_pedido, p.obra, p.quantidade, p.apresentacao,
                       p.status, p.data_pedido, p.valor_pago,
                       m.nome AS material_nome
                FROM tb_pedidos p
                INNER JOIN tb_materiais m ON m.id_material = p.id_material
                WHERE p.id_funcionario = %s
            """
            parametros = [id_funcionario]
            if not incluir_entregues:
                sql += " AND p.status NOT IN ('Entregue', 'Atendido') "
            sql += " ORDER BY p.data_pedido DESC"
            cursor.execute(sql, parametros)
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    @staticmethod
    def listar_obras_ativas():
        """Retorna as obras ativas disponíveis para requisições."""
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """SELECT id_obra, nome, endereco, responsavel
                   FROM tb_obras WHERE ativa = TRUE ORDER BY nome"""
            )
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    @staticmethod
    def listar_materiais_ativos():
        """Retorna os materiais ativos disponíveis para requisições."""
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """SELECT id_material, nome, unidade
                   FROM tb_materiais WHERE ativo = TRUE ORDER BY nome"""
            )
            return cursor.fetchall()
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()

    @staticmethod
    def buscar_obra(nome):
        """Busca os dados da obra ativa pelo nome salvo no pedido."""
        conexao = None
        cursor = None
        try:
            conexao = Conexao.conectar()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(
                """SELECT nome, responsavel FROM tb_obras
                   WHERE nome = %s AND ativa = TRUE LIMIT 1""",
                (nome,),
            )
            return cursor.fetchone()
        finally:
            if cursor:
                cursor.close()
            if conexao:
                conexao.close()