from conexao import Conexao


class Administrador:
	@staticmethod
	def cadastro_aprovado(email):
		"""Consulta se um funcionário já foi aprovado pelo administrador."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor()
			cursor.execute(
				"""SELECT aprovado FROM tb_usuarios
				   WHERE email = %s AND tipo_usuario = 'Funcionario'""",
				(email.strip().lower(),),
			)
			resultado = cursor.fetchone()
			return bool(resultado and resultado[0])
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()

	@staticmethod
	def listar_cadastros_pendentes():
		"""Retorna os funcionários que aguardam aprovação."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor(dictionary=True)
			cursor.execute(
				"""SELECT id_usuario, nome, email, telefone, data_criacao
				   FROM tb_usuarios
				   WHERE tipo_usuario = 'Funcionario' AND aprovado = FALSE
				   ORDER BY data_criacao ASC"""
			)
			return cursor.fetchall()
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()

	@staticmethod
	def aprovar_cadastro(id_usuario):
		"""Aprova um funcionário pendente e retorna se houve alteração."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor()
			cursor.execute(
				"""UPDATE tb_usuarios
				   SET aprovado = TRUE
				   WHERE id_usuario = %s
					 AND tipo_usuario = 'Funcionario'
					 AND aprovado = FALSE""",
				(id_usuario,),
			)
			conexao.commit()
			return cursor.rowcount == 1
		except Exception:
			if conexao:
				conexao.rollback()
			raise
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()
