from flask import Flask, render_template, jsonify
import smtplib
import os
import random
from flask import Flask, render_template, request, redirect, session, flash, url_for
import email.message
from dotenv import load_dotenv
import re
from collections import defaultdict
from datetime import timedelta
from user import User
from adm import Administrador
from security import SecurityUtils, RateLimiter, TokenRecuperacaoSenha, requer_sessao, requer_admin, requer_funcionario
from ssl_config import obter_contexto_ssl, verificar_https_disponivel

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-insecure-key')
app.permanent_session_lifetime = timedelta(hours=2)
app.session_cookie_secure = True
app.session_cookie_httponly = True
app.session_cookie_samesite = 'Lax' 

@app.before_request
def antes_requisicao():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=2)

@app.errorhandler(401)
def nao_autorizado(error):
    flash("Faça login para acessar esta página.", "erro")
    return redirect(url_for("login")), 401

@app.errorhandler(403)
def proibido(error):
    flash("Você não tem permissão para acessar esta página.", "erro")
    return redirect(url_for("login")), 403

@app.errorhandler(404)
def nao_encontrado(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def erro_interno(error):
    return render_template("500.html"), 500

@app.context_processor
def injetar_csrf():
    return dict(csrf_token=SecurityUtils.gerar_csrf_token())

@app.after_request
def adicionar_headers_seguranca(response):
    """Adiciona headers de segurança à resposta."""
    # HSTS: Força HTTPS por 1 ano
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # Previne clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Previne MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Ativa XSS protection no navegador
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Content Security Policy básica
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("login.html")
        
        # Rate limiting por e-mail ou telefone
        chave_rate_limit = f"login_{request.form.get('telefone', '')}"
        dentro_limite, tentativas_restantes, aguarde = RateLimiter.registrar_tentativa(chave_rate_limit, limite=5, janela_segundos=300)
        
        if not dentro_limite:
            flash(f"Muitas tentativas de login. Aguarde {aguarde} segundos antes de tentar novamente.", "erro")
            return render_template("login.html")
        
        usuario = User()
        nome = SecurityUtils.sanitizar_entrada(request.form.get("nome", ""), "text")
        telefone = SecurityUtils.sanitizar_entrada(request.form.get("telefone", ""), "telefone")
        senha = request.form.get("senha", "")
        
        if usuario.entrar(nome, telefone, senha):
            RateLimiter.limpar_chave(chave_rate_limit)
            session["usuario_id"] = usuario.id_usuario
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email
            session["usuario_telefone"] = usuario.tel
            session["usuario_tipo"] = usuario.tipo
            if usuario.tipo == "Administrador" and usuario.primeiro_login:
                return redirect(url_for("primeiro_acesso_administrador"))
            destino = "administrador" if usuario.tipo == "Administrador" else "funcionario"
            return redirect(url_for(destino))
        if usuario.pendente:
            return redirect(url_for("aguardando_confirmacao"))
        flash(usuario.erro + (f" Tentativas restantes: {tentativas_restantes}" if tentativas_restantes > 0 else ""), "erro")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("cadastro.html")
        
        # Validar e sanitizar entrada
        nome = SecurityUtils.sanitizar_entrada(request.form.get("nome", ""), "text")
        email = SecurityUtils.sanitizar_entrada(request.form.get("email", ""), "email")
        telefone = SecurityUtils.sanitizar_entrada(request.form.get("telefone", ""), "telefone")
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")
        
        # Validar campos obrigatórios
        if not nome or not email or not telefone or not senha:
            flash("Todos os campos são obrigatórios.", "erro")
            return render_template("cadastro.html")
        
        # Validar nome
        if not SecurityUtils.validar_nome(nome):
            flash("Nome inválido (mínimo 3 caracteres, sem números).", "erro")
            return render_template("cadastro.html")
        
        # Validar email
        if not SecurityUtils.validar_email(email):
            flash("E-mail inválido.", "erro")
            return render_template("cadastro.html")
        
        # Validar telefone
        if not SecurityUtils.validar_telefone(telefone):
            flash("Telefone inválido (mínimo 11 dígitos).", "erro")
            return render_template("cadastro.html")
        
        # Validar senha
        senha_valida, msg_senha = SecurityUtils.validar_senha(senha)
        if not senha_valida:
            flash(f"Senha fraca: {msg_senha}", "erro")
            return render_template("cadastro.html")
        
        # Validar confirmação de senha
        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
            return render_template("cadastro.html")
        
        usuario = User()
        if usuario.verificar_duplicidade(email, telefone):
            flash("E-mail ou telefone já cadastrado.", "erro")
            return render_template("cadastro.html")
        
        codigo = usuario.gerar_codigo_confirmacao(email)
        session["cadastro_dados"] = {
            "nome": nome,
            "telefone": telefone,
            "email": email,
            "senha": senha,
            "codigo": codigo,
        }
        session["cadastro_tentativas"] = 0
        return redirect(url_for("confirmar_cadastro"))

    return render_template("cadastro.html")

@app.route("/cadastro/confirmar", methods=["GET", "POST"])
def confirmar_cadastro():
    dados = session.get("cadastro_dados")
    if not dados:
        return redirect(url_for("cadastro"))

    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("confirmar_cadastro.html", email=dados.get("email", ""))
        
        codigo_digitado = SecurityUtils.sanitizar_entrada(request.form.get("codigo", ""), "numero")
        usuario = User()
        usuario.codigo_confirmacao = dados.get("codigo")
        usuario.tentativas_codigo = session.get("cadastro_tentativas", 0)

        if usuario.validar_codigo_cadastro(codigo_digitado):
            if usuario.cadastrar(
                dados.get("nome", ""),
                dados.get("telefone", ""),
                dados.get("email", ""),
                dados.get("senha", ""),
                codigo_confirmacao=dados.get("codigo"),
            ):
                session["cadastro_email"] = dados.get("email", "")
                session.pop("cadastro_dados", None)
                session.pop("cadastro_tentativas", None)
                return redirect(url_for("aguardando_confirmacao"))
            flash(usuario.erro, "erro")
            return redirect(url_for("cadastro"))

        tentativas = session.get("cadastro_tentativas", 0) + 1
        session["cadastro_tentativas"] = tentativas

        if tentativas >= 2:
            session.pop("cadastro_dados", None)
            session.pop("cadastro_tentativas", None)
            flash("Tente se cadastrar novamente", "erro")
            return redirect(url_for("inicio"))

        flash(f"Código incorreto. Você tem {2 - tentativas} tentativa(s) restante(s).", "erro")
        return redirect(url_for("confirmar_cadastro"))

    return render_template("confirmar_cadastro.html", email=dados.get("email", ""))

@app.route("/aguardando-confirmacao")
def aguardando_confirmacao():
    email = session.get("cadastro_email", "")
    return render_template("aguardando_confirmacao.html", email=email)

@app.route("/api/cadastro/status")
def status_cadastro():
    email = session.get("cadastro_email")
    if not email:
        return jsonify({"aprovado": False})
    return jsonify({"aprovado": Administrador.cadastro_aprovado(email)})

@app.route("/primeiro-acesso-administrador", methods=["GET", "POST"])
@requer_admin
def primeiro_acesso_administrador():
    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("primeiro_acesso_administrador.html", dados=request.form)
        senha = request.form.get("senha", "")
        if senha != request.form.get("confirmar_senha", ""):
            flash("As senhas não coincidem.", "erro")
            return render_template("primeiro_acesso_administrador.html", dados=request.form)
        usuario = User()
        if usuario.atualizar_primeiro_acesso(
            session["usuario_id"], request.form.get("nome", ""), request.form.get("telefone", ""),
            request.form.get("email", ""), senha,
        ):
            session["usuario_nome"] = usuario.nome
            session["usuario_email"] = usuario.email
            session["usuario_telefone"] = usuario.tel
            return redirect(url_for("administrador"))
        flash(usuario.erro, "erro")
    dados = {"nome": session.get("usuario_nome", ""), "email": session.get("usuario_email", ""), "telefone": session.get("usuario_telefone", "")}
    return render_template("primeiro_acesso_administrador.html", dados=dados)

@app.route("/requisicao", methods=["GET", "POST"])
@requer_funcionario
def requisicao():
    # Validar CSRF
    if request.method == "POST" and not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
        flash("Token de segurança inválido. Tente novamente.", "erro")
        obras = User.listar_obras_ativas()
        materiais = User.listar_materiais_ativos()
        return render_template("requisicao.html", obras=obras, materiais=materiais)
    
    obras = User.listar_obras_ativas()
    materiais = User.listar_materiais_ativos()
    if request.method == "POST":
        try:
            id_pedido = User.pedir_material(
                session["usuario_id"],
                request.form.get("obra", ""),
                int(request.form.get("material", "0")),
                float(request.form.get("quantidade", "0").replace(",", ".")),
                request.form.get("apresentacao", ""),
                request.form.get("observacao", ""),
            )
            flash(f"Requisição #{id_pedido} enviada para análise.", "sucesso")
            return redirect(url_for("requisicao"))
        except (ValueError, TypeError) as error:
            flash(str(error), "erro")
    return render_template("requisicao.html", obras=obras, materiais=materiais)

@app.route("/recuperar-senha", methods=["GET", "POST"])
def recuperar_senha():
    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("recuperar_senha.html")
        
        email = SecurityUtils.sanitizar_entrada(request.form.get("email", ""), "email")
        
        if not SecurityUtils.validar_email(email):
            flash("E-mail inválido.", "erro")
            return render_template("recuperar_senha.html")
        
        usuario = User()
        if usuario.solicitar_recuperacao_senha(email):
            flash("Se o e-mail está cadastrado, você receberá um link de recuperação em breve.", "sucesso")
            return render_template("recuperar_senha.html")
        else:
            # Não informar se o e-mail existe ou não (segurança)
            flash("Se o e-mail está cadastrado, você receberá um link de recuperação em breve.", "sucesso")
            return render_template("recuperar_senha.html")
    
    return render_template("recuperar_senha.html")

@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    usuario = User()
    id_usuario = usuario.validar_token_reset(token)
    
    if not id_usuario:
        flash("Link de recuperação inválido ou expirado.", "erro")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Validar CSRF
        if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
            flash("Token de segurança inválido. Tente novamente.", "erro")
            return render_template("redefinir_senha.html", token=token)
        
        nova_senha = request.form.get("nova_senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")
        
        # Validar senha
        senha_valida, msg_senha = SecurityUtils.validar_senha(nova_senha)
        if not senha_valida:
            flash(f"Senha fraca: {msg_senha}", "erro")
            return render_template("redefinir_senha.html", token=token)
        
        # Validar confirmação
        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
            return render_template("redefinir_senha.html", token=token)
        
        if usuario.redefinir_senha(id_usuario, nova_senha):
            flash("Senha redefinida com sucesso. Faça login com sua nova senha.", "sucesso")
            return redirect(url_for("login"))
        else:
            flash("Erro ao redefinir senha. Tente novamente.", "erro")
            return render_template("redefinir_senha.html", token=token)
    
    return render_template("redefinir_senha.html", token=token)

@app.route("/administrador")
@requer_admin
def administrador():
    requisicoes = Administrador.listar_requisicoes()
    obras = Administrador.listar_obras_ativas()
    resumo = {
        "pendentes": sum(pedido["status"] == "Pendente" for pedido in requisicoes),
        "gastos": sum(float(pedido["valor_pago"] or 0) for pedido in requisicoes),
        "obras": len({pedido["obra"] for pedido in requisicoes}),
        "itens": len(requisicoes),
    }
    return render_template(
        "administrador.html",
        nome=session.get("usuario_nome", "Administrador"),
        requisicoes=requisicoes,
        resumo=resumo,
        obras=obras,
    )

@app.route("/administrador/obras/cadastrar", methods=["POST"])
@requer_admin
def cadastrar_obra():
    # Validar CSRF
    if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
        flash("Token de segurança inválido. Tente novamente.", "erro")
        return redirect(url_for("administrador"))
    
    try:
        nome = SecurityUtils.sanitizar_entrada(request.form.get("nome", ""), "text")
        endereco = SecurityUtils.sanitizar_entrada(request.form.get("endereco", ""), "text")
        responsavel = SecurityUtils.sanitizar_entrada(request.form.get("responsavel", ""), "text")
        
        if not nome or not endereco or not responsavel:
            flash("Todos os campos são obrigatórios.", "erro")
        else:
            Administrador.cadastrar_obra(nome, endereco, responsavel, session["usuario_id"])
            flash("Obra cadastrada com sucesso.", "sucesso")
    except ValueError as error:
        flash(str(error), "erro")
    return redirect(url_for("administrador"))

@app.route("/administrador/obras/<int:id_obra>/excluir", methods=["POST"])
@requer_admin
def excluir_obra(id_obra):
    # Validar CSRF
    if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
        flash("Token de segurança inválido. Tente novamente.", "erro")
        return redirect(url_for("administrador"))
    try:
        if Administrador.excluir_obra(id_obra):
            flash("Obra removida da exibição. O histórico foi preservado.", "sucesso")
        else:
            flash("Obra não encontrada ou já removida.", "erro")
    except Exception:
        flash("Não foi possível remover a obra agora.", "erro")
    return redirect(url_for("administrador"))

@app.route("/administrador/cadastros")
@requer_admin
def cadastros_pendentes():
    cadastros = Administrador.listar_cadastros_pendentes()
    return render_template("cadastros_pendentes.html", nome=session.get("usuario_nome", "Administrador"), cadastros=cadastros)

@app.route("/administrador/cadastros/<int:id_usuario>/aprovar", methods=["POST"])
@requer_admin
def aprovar_cadastro(id_usuario):
    # Validar CSRF
    if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
        flash("Token de segurança inválido. Tente novamente.", "erro")
        return redirect(url_for("cadastros_pendentes"))
    Administrador.aprovar_cadastro(id_usuario)
    return redirect(url_for("cadastros_pendentes"))

@app.route("/requisicao/<int:id_pedido>/atualizar", methods=["POST"])
@requer_admin
def atualizar_requisicao(id_pedido):
    # Validar CSRF
    if not SecurityUtils.validar_csrf_token(request.form.get("csrf_token", "")):
        flash("Token de segurança inválido. Tente novamente.", "erro")
        return redirect(url_for("administrador"))
    try:
        Administrador.atualizar_requisicao(
            id_pedido,
            session["usuario_id"],
            request.form.get("status", "Pendente"),
            request.form.get("valor_pago", ""),
            request.form.get("loja", ""),
        )
        flash("Requisição atualizada com sucesso.", "sucesso")
    except ValueError as error:
        flash(str(error), "erro")
    return redirect(url_for("administrador"))

@app.route("/relatorio")
def relatorio():
    filtros = {
        "inicio": request.args.get("inicio", ""),
        "fim": request.args.get("fim", ""),
        "obra": request.args.get("obra", "todas"),
        "funcionario": request.args.get("funcionario", "todos")
    }
    dados_relatorio = Administrador.obter_relatorio(filtros)
    return render_template(
        "relatorio.html",
        nome=session.get("usuario_nome", "Administrador"),
        filtros=filtros,
        obras=Administrador.listar_obras_ativas(),
        funcionarios=Administrador.listar_funcionarios(),
        **dados_relatorio,
    )

@app.route("/funcionario")
@requer_funcionario
def funcionario():
    pedidos = User.listar_pedidos(session["usuario_id"], incluir_entregues=False)
    historico_pedidos = User.listar_pedidos(session["usuario_id"], incluir_entregues=True)
    resumo = {
        "analise": sum(pedido["status"] == "Pendente" for pedido in pedidos),
        "aprovados": sum(pedido["status"] == "Aprovado" for pedido in pedidos),
        "recebidos": sum(pedido["status"] in ("Atendido", "Entregue") for pedido in historico_pedidos),
    }
    obra = pedidos[0]["obra"] if pedidos else (historico_pedidos[0]["obra"] if historico_pedidos else "Nenhuma obra cadastrada")
    obra_info = User.buscar_obra(obra) if obra and obra != "Nenhuma obra cadastrada" else None
    return render_template(
        "funcionario.html",
        nome=session.get("usuario_nome", "Funcionário"),
        pedidos=pedidos,
        historico_pedidos=historico_pedidos,
        resumo=resumo,
        obra=obra,
        responsavel=(obra_info or {}).get("responsavel") or "Responsável não informado",
    )

if __name__ == "__main__":
    # Verificar e obter configuração HTTPS
    contexto_ssl = obter_contexto_ssl()
    https_disponivel, status_https = verificar_https_disponivel()
    
    if https_disponivel:
        print(f"\n🔐 HTTPS: {status_https}")
        print("📋 Iniciando servidor com HTTPS...")
    else:
        print(f"\n⚠️  HTTPS: {status_https}")
        print("   Rodando em HTTP (inseguro para produção)")
    
    print(f"🚀 Servidor iniciando em: http{'s' if https_disponivel else ''}://0.0.0.0:8080")
    print(f"\n💡 Para gerar certificado SSL: python setup_https.py\n")
    
    # Iniciar aplicação
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080,
        ssl_context=contexto_ssl if https_disponivel else None
    )