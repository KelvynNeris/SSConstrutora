from flask import Flask, render_template, jsonify
import smtplib
import os
import random
from flask import Flask, render_template, request, redirect, session, flash
import email.message
from dotenv import load_dotenv
from usuario import Usuario  # Substitua pelo seu modelo de usuário
import re
from collections import defaultdict

app = Flask(__name__)
app.secret_key = '0000' 

@app.route("/")
def inicio():
    verificar_sessao()
    if 'usuario_logado' in session:
        return redirect("/principal")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)  # Define o host como localhost e a porta como 8080