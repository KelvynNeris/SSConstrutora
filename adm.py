from conexao import Conexao


class Administrador:
	@staticmethod
	def listar_obras_ativas():
		"""Retorna somente obras ativas para exibição no painel."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor(dictionary=True)
			cursor.execute(
				"""SELECT id_obra, nome, endereco, responsavel, data_criacao
				   FROM tb_obras
				   WHERE ativa = TRUE
				   ORDER BY data_criacao DESC"""
			)
			return cursor.fetchall()
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()

	@staticmethod
	def excluir_obra(id_obra):
		"""Oculta uma obra sem apagar seu histórico do banco."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor()
			cursor.execute(
				"""UPDATE tb_obras
				   SET ativa = FALSE
				   WHERE id_obra = %s AND ativa = TRUE""",
				(id_obra,),
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
	def cadastrar_obra(nome, endereco, responsavel, id_administrador):
		"""Cadastra uma obra vinculada ao administrador que a registrou."""
		nome = nome.strip()
		endereco = endereco.strip()
		responsavel = responsavel.strip()
		if not nome or not endereco:
			raise ValueError("Informe o nome e o endereço da obra.")

		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor()
			cursor.execute("SELECT id_obra FROM tb_obras WHERE LOWER(nome) = LOWER(%s)", (nome,))
			if cursor.fetchone():
				raise ValueError("Já existe uma obra com esse nome.")
			cursor.execute(
				"""INSERT INTO tb_obras (nome, endereco, responsavel, id_administrador)
				   VALUES (%s, %s, %s, %s)""",
				(nome, endereco, responsavel or None, id_administrador),
			)
			id_obra = cursor.lastrowid
			conexao.commit()
			return id_obra
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
	def listar_requisicoes():
		"""Retorna as requisições com os dados do material e solicitante."""
		conexao = None
		cursor = None
		try:
			conexao = Conexao.conectar()
			cursor = conexao.cursor(dictionary=True)
			cursor.execute(
				"""SELECT p.id_pedido, p.obra, p.quantidade, p.apresentacao,
						  p.status, p.data_pedido, p.valor_pago,
						  m.nome AS material_nome, u.nome AS funcionario_nome
				   FROM tb_pedidos p
				   INNER JOIN tb_materiais m ON m.id_material = p.id_material
				   INNER JOIN tb_usuarios u ON u.id_usuario = p.id_funcionario
				   ORDER BY p.data_pedido DESC"""
			)
			return cursor.fetchall()
		finally:
			if cursor:
				cursor.close()
			if conexao:
				conexao.close()

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
