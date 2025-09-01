from flask import Blueprint, request, jsonify, current_app
from app.models import Proprietario
from app.db import db
from app import bcrypt
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra um novo proprietário."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password') or not data.get('nome') or not data.get('telefone'):
        return jsonify({'message': 'Faltam dados obrigatórios para o registro (nome, telefone, username, password)!'}), 400

    # Verificar se o usuário já existe
    if Proprietario.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Este nome de usuário já está em uso!'}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    novo_proprietario = Proprietario(
        nome=data.get('nome'),
        telefone=data.get('telefone'),
        username=data['username'],
        password_hash=hashed_password
    )

    db.session.add(novo_proprietario)
    db.session.commit()

    return jsonify({'message': 'Proprietário registrado com sucesso!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Autentica um proprietário e retorna um token JWT."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Credenciais (username, password) não fornecidas!'}), 400

    proprietario = Proprietario.query.filter_by(username=data['username']).first()

    if not proprietario or not bcrypt.check_password_hash(proprietario.password_hash, data['password']):
        return jsonify({'message': 'Credenciais inválidas!'}), 401

    token = jwt.encode({
        'proprietario_id': proprietario.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})
