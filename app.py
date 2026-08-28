from flask import Flask, render_template, jsonify
import smtplib
import os
import random
from flask import Flask, render_template, request, redirect, session, flash, url_for
import email.message
from dotenv import load_dotenv
import re
from collections import defaultdict
from user import User
from adm import Administrador

app = Flask(__name__)
app.secret_key = '0000' 

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = User()
        if usuario.entrar(request.form.get("nome", ""), request.form.get("telefone", ""), request.form.get("senha", "")):
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
        flash(usuario.erro, "erro")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha != request.form.get("confirmar_senha", ""):
            flash("As senhas não coincidem.", "erro")
            return render_template("cadastro.html")
        usuario = User()
        if usuario.cadastrar(request.form.get("nome", ""), request.form.get("telefone", ""), request.form.get("email", ""), senha):
            session["cadastro_email"] = request.form.get("email", "")
            return redirect(url_for("aguardando_confirmacao"))
        flash(usuario.erro, "erro")
    return render_template("cadastro.html")

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
def primeiro_acesso_administrador():
    if session.get("usuario_tipo") != "Administrador" or not session.get("usuario_id"):
        return redirect(url_for("login"))
    if request.method == "POST":
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
def requisicao():
    if session.get("usuario_tipo") != "Funcionario" or not session.get("usuario_id"):
        return redirect(url_for("login"))
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

@app.route("/administrador")
def administrador():
    if session.get("usuario_tipo") != "Administrador" or not session.get("usuario_id"):
        return redirect(url_for("login"))
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
def cadastrar_obra():
    if session.get("usuario_tipo") != "Administrador" or not session.get("usuario_id"):
        return redirect(url_for("login"))
    try:
        Administrador.cadastrar_obra(
            request.form.get("nome", ""),
            request.form.get("endereco", ""),
            request.form.get("responsavel", ""),
            session["usuario_id"],
        )
        flash("Obra cadastrada com sucesso.", "sucesso")
    except ValueError as error:
        flash(str(error), "erro")
    return redirect(url_for("administrador"))

@app.route("/administrador/obras/<int:id_obra>/excluir", methods=["POST"])
def excluir_obra(id_obra):
    if session.get("usuario_tipo") != "Administrador" or not session.get("usuario_id"):
        return redirect(url_for("login"))
    try:
        if Administrador.excluir_obra(id_obra):
            flash("Obra removida da exibição. O histórico foi preservado.", "sucesso")
        else:
            flash("Obra não encontrada ou já removida.", "erro")
    except Exception:
        flash("Não foi possível remover a obra agora.", "erro")
    return redirect(url_for("administrador"))

@app.route("/administrador/cadastros")
def cadastros_pendentes():
    if session.get("usuario_tipo") != "Administrador":
        return redirect(url_for("login"))
    cadastros = Administrador.listar_cadastros_pendentes()
    return render_template("cadastros_pendentes.html", nome=session.get("usuario_nome", "Administrador"), cadastros=cadastros)

@app.route("/administrador/cadastros/<int:id_usuario>/aprovar", methods=["POST"])
def aprovar_cadastro(id_usuario):
    if session.get("usuario_tipo") != "Administrador":
        return redirect(url_for("login"))
    Administrador.aprovar_cadastro(id_usuario)
    return redirect(url_for("cadastros_pendentes"))

@app.route("/requisicao/<int:id_pedido>/atualizar", methods=["POST"])
def atualizar_requisicao(id_pedido):
    if session.get("usuario_tipo") != "Administrador" or not session.get("usuario_id"):
        return redirect(url_for("login"))
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
def funcionario():
    if session.get("usuario_tipo") != "Funcionario" or not session.get("usuario_id"):
        return redirect(url_for("login"))
    pedidos = User.listar_pedidos(session["usuario_id"])
    resumo = {
        "analise": sum(pedido["status"] == "Pendente" for pedido in pedidos),
        "aprovados": sum(pedido["status"] == "Aprovado" for pedido in pedidos),
        "recebidos": sum(pedido["status"] == "Atendido" for pedido in pedidos),
    }
    obra = pedidos[0]["obra"] if pedidos else "Nenhuma obra cadastrada"
    obra_info = User.buscar_obra(obra) if pedidos else None
    return render_template(
        "funcionario.html",
        nome=session.get("usuario_nome", "Funcionário"),
        pedidos=pedidos,
        resumo=resumo,
        obra=obra,
        responsavel=(obra_info or {}).get("responsavel") or "Responsável não informado",
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)  # Define o host como localhost e a porta como 8080