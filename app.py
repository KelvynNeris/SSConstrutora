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
    return render_template("requisicao.html")

@app.route("/administrador")
def administrador():
    return render_template("administrador.html", nome=session.get("usuario_nome", "Administrador"))

@app.route("/requisicao/<int:id_pedido>/atualizar", methods=["POST"])
def atualizar_requisicao(id_pedido):
    session[f"pedido_{id_pedido}"] = {
        "status": request.form.get("status", "Pendente"),
        "valor_pago": request.form.get("valor_pago", ""),
        "loja": request.form.get("loja", "")
    }
    return redirect(url_for("administrador"))

@app.route("/relatorio")
def relatorio():
    filtros = {
        "inicio": request.args.get("inicio", ""),
        "fim": request.args.get("fim", ""),
        "obra": request.args.get("obra", "todas"),
        "funcionario": request.args.get("funcionario", "todos")
    }
    return render_template("relatorio.html", nome=session.get("usuario_nome", "Administrador"), filtros=filtros)

@app.route("/funcionario")
def funcionario():
    return render_template("funcionario.html", nome=session.get("usuario_nome", "Funcionário"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)  # Define o host como localhost e a porta como 8080