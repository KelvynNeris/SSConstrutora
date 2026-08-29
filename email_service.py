import os
import smtplib
from email.message import EmailMessage


def enviar_email_admin(id_pedido, nome_funcionario, nome_obra, material, quantidade, unidade="unidade"):
    """Envia uma notificação por e-mail para o administrador."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM")
    admin_email = os.getenv("ADMIN_EMAIL")

    if not all([host, username, password, from_email, admin_email]):
        print("Credenciais de e-mail não configuradas. O envio foi ignorado.")
        return False

    mensagem = EmailMessage()
    mensagem["Subject"] = f"Nova requisição de material #{id_pedido}"
    mensagem["From"] = from_email
    mensagem["To"] = admin_email
    mensagem.set_content(
        "Nova requisição de material\n\n"
        f"Funcionário: {nome_funcionario}\n"
        f"Obra: {nome_obra}\n"
        f"Material: {material}\n"
        f"Quantidade: {quantidade} {unidade}\n"
        f"Pedido: #{id_pedido}\n\n"
        "Acesse o painel para aprovar ou recusar."
    )

    try:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(mensagem)
        return True
    except Exception as exc:
        print(f"Erro ao enviar e-mail para o administrador: {exc}")
        return False
