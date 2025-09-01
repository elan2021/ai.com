from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt

from app.models import Proprietario, Loja
from app.db import db

lojas_bp = Blueprint('lojas', __name__)

def token_required(f):
    """Decorator para validar o token JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # O token é esperado no cabeçalho de autorização no formato 'Bearer <token>'
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Formato do token inválido! Use "Bearer <token>".'}), 401

        if not token:
            return jsonify({'message': 'Token de autenticação não fornecido!'}), 401

        try:
            # Decodifica o token para obter o ID do proprietário
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Proprietario.query.get(data['proprietario_id'])
            if not current_user:
                return jsonify({'message': 'Usuário do token não encontrado!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirou!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401

        # Passa o proprietário autenticado para a rota
        return f(current_user, *args, **kwargs)

    return decorated


@lojas_bp.route('/', methods=['POST'])
@token_required
def create_loja(current_user):
    """Cria uma nova loja para o proprietário autenticado."""
    data = request.get_json()

    if not data or not data.get('path') or not data.get('title'):
        return jsonify({'message': 'Dados obrigatórios (path, title) não fornecidos!'}), 400

    path = data['path'].lower().strip()

    # Validação simples para o path
    import re
    if not re.match(r'^[a-z0-9-]+$', path):
        return jsonify({'message': 'O caminho (path) deve conter apenas letras minúsculas, números e hífens.'}), 400

    if Loja.query.filter_by(path=path).first():
        return jsonify({'message': 'Este caminho de loja já está em uso!'}), 409

    nova_loja = Loja(
        path=path,
        title=data['title'],
        proprietario_id=current_user.id
    )

    db.session.add(nova_loja)
    db.session.commit()

    return jsonify({
        'message': 'Loja criada com sucesso!',
        'loja': {
            'id': nova_loja.id,
            'path': nova_loja.path,
            'title': nova_loja.title
        }
    }), 201
