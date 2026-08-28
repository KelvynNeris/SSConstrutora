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

	@staticmethod
	def atualizar_requisicao(id_pedido, id_administrador, status, valor_pago=None, loja=""):
		"""Atualiza o status e o custo real de uma requisição."""
		status_validos = {"Pendente", "Aprovado", "Recusado", "Atendido"}
		if status not in status_validos:
			raise ValueError("Status de requisição inválido.")

		valor = None
		if valor_pago not in (None, ""):
			try:
				valor = float(str(valor_pago).replace(",", "."))
			except ValueError as error:
				raise ValueError("Informe um valor pago válido.") from error
			if valor < 0:
				raise ValueError("O valor pago não pode ser negativo.")

		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor()
			cursor.execute(
				"""UPDATE tb_pedidos
				   SET status = %s,
					   valor_pago = %s,
					   loja_fornecedora = %s,
					   id_administrador = %s,
					   data_resposta = NOW(),
					   data_pagamento = CASE WHEN %s IS NOT NULL THEN NOW() ELSE data_pagamento END
				   WHERE id_pedido = %s""",
				(status, valor, loja.strip() or None, id_administrador, valor, id_pedido),
			)
			if cursor.rowcount != 1:
				conexao.rollback()
				raise ValueError("Requisição não encontrada.")
			conexao.commit()
			return True
		except Exception:
			if conexao:
				conexao.rollback()
			raise
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()
