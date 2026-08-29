import os
import smtplib
from email.message import EmailMessage


def _enviar_email(destinatario, assunto, corpo):
    """Envia uma mensagem via SMTP usando as variáveis de e-mail do projeto."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM")

    if not all([host, username, password, from_email, destinatario]):
        print("Credenciais de e-mail não configuradas. O envio foi ignorado.")
        return False

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = from_email
    mensagem["To"] = destinatario
    mensagem.set_content(corpo)

    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(mensagem)
        return True
    except Exception as exc:
        print(f"Erro ao enviar e-mail: {exc}")
        return False


def enviar_email_admin(id_pedido, nome_funcionario, nome_obra, material, quantidade, unidade="unidade"):
    """Envia uma notificação por e-mail para o administrador."""
    admin_email = os.getenv("ADMIN_EMAIL")
    assunto = f"Nova requisição de material #{id_pedido}"
    corpo = (
        "Nova requisição de material\n\n"
        f"Funcionário: {nome_funcionario}\n"
        f"Obra: {nome_obra}\n"
        f"Material: {material}\n"
        f"Quantidade: {quantidade} {unidade}\n"
        f"Pedido: #{id_pedido}\n\n"
        "Acesse o painel para aprovar ou recusar."
    )
    return _enviar_email(admin_email, assunto, corpo)


def enviar_email_codigo_confirmacao(email_destino, codigo):
    """Envia o código de confirmação do cadastro para o e-mail informado."""
    assunto = "Confirme seu cadastro na SS Construtora"
    corpo = (
        "Seu código de confirmação é: "
        f"{codigo}\n\n"
        "Use este código para concluir o cadastro na plataforma da SS Construtora."
    )
    return _enviar_email(email_destino, assunto, corpo)


def enviar_email_funcionario(id_pedido, nome_funcionario, email_funcionario, nome_obra, material, quantidade, status, unidade="unidade", observacao=None):
    """Envia uma atualização da requisição para o funcionário responsável."""
    status_legivel = {
        "Pendente": "pendente",
        "Aprovado": "aprovada",
        "Recusado": "recusada",
        "Atendido": "atendida",
        "Entregue": "entregue",
    }.get(status, str(status or "atualizada").lower())

    assunto = f"Atualização da requisição #{id_pedido}: {status}"
    detalhes = f"Observação: {observacao}\n" if observacao else ""
    corpo = (
        f"Olá, {nome_funcionario}!\n\n"
        f"Sua requisição #{id_pedido} foi atualizada para o status: {status}.\n\n"
        f"Obra: {nome_obra}\n"
        f"Material: {material}\n"
        f"Quantidade: {quantidade} {unidade}\n"
        f"Status: {status_legivel}\n"
        f"{detalhes}"
        "Acompanhe o andamento no sistema da SS Construtora."
    )
    return _enviar_email(email_funcionario, assunto, corpo)
