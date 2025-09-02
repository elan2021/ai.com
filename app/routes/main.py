from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import jwt
import datetime

from app.models import Proprietario, Profissional
from app.db import db
from app import bcrypt
from flask import current_app

main_bp = Blueprint('main', __name__, template_folder='../templates/main')

@main_bp.route('/')
def index():
    # Esta rota irá renderizar a página unificada de login/cadastro
    return render_template("index.html")

@main_bp.route('/login', methods=['POST'])
def login():
    user_type = request.form.get('user_type')
    username = request.form.get('username')
    password = request.form.get('password')

    if user_type == 'proprietario':
        user = Proprietario.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            token = jwt.encode({
                'proprietario_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('admin_token', token, httponly=True, samesite='Lax')
            flash('Login de proprietário realizado com sucesso!', 'success')
            return response

    elif user_type == 'profissional':
        user = Profissional.query.filter_by(username=username).first()
        if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):
            token = jwt.encode({
                'profissional_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            response = make_response(redirect(url_for('pro.dashboard')))
            response.set_cookie('pro_token', token, httponly=True, samesite='Lax')
            flash('Login de profissional realizado com sucesso!', 'success')
            return response

    flash('Credenciais inválidas ou tipo de usuário incorreto.', 'error')
    return redirect(url_for('main.index'))


@main_bp.route('/register', methods=['POST'])
def register():
    """Processa o formulário de registro de um novo proprietário."""
    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    username = request.form.get('username')
    password = request.form.get('password')

    if not all([nome, telefone, username, password]):
        flash('Todos os campos de cadastro são obrigatórios.', 'error')
    elif Proprietario.query.filter_by(username=username).first():
        flash('Este nome de usuário já está em uso.', 'error')
    else:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        novo_proprietario = Proprietario(
            nome=nome,
            telefone=telefone,
            username=username,
            password_hash=hashed_password
        )
        db.session.add(novo_proprietario)
        db.session.commit()
        flash('Conta de proprietário criada com sucesso! Por favor, faça o login.', 'success')

    return redirect(url_for('main.index'))
