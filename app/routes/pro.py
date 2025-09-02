from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, g, current_app
from functools import wraps
import jwt
import datetime

from app.models import Profissional, Agendamento
from app import bcrypt

pro_bp = Blueprint('pro', __name__, template_folder='../templates/pro')

def pro_token_required(f):
    """Decorator para proteger rotas do profissional."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('pro_token')
        if not token:
            flash('É necessário fazer login para acessar esta página.', 'warning')
            return redirect(url_for('main.index'))
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_pro_user = Profissional.query.get(data['profissional_id'])
            if g.current_pro_user is None:
                raise jwt.InvalidTokenError
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            flash('Sua sessão expirou ou é inválida. Faça login novamente.', 'error')
            resp = make_response(redirect(url_for('main.index')))
            resp.set_cookie('pro_token', '', expires=0)
            return resp
        return f(*args, **kwargs)
    return decorated_function

@pro_bp.route('/logout')
@pro_token_required
def logout():
    """Desloga o profissional limpando o cookie."""
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('pro_token', '', expires=0)
    flash('Você foi desconectado.', 'info')
    return response

@pro_bp.route('/dashboard')
@pro_token_required
def dashboard():
    """Busca os dados e exibe o dashboard do profissional."""
    profissional = g.current_pro_user

    # 1. Buscar e categorizar agendamentos
    todos_agendamentos = profissional.agendamentos
    agendamentos_categorizados = {
        'proximos': [ag for ag in todos_agendamentos if ag.status == 'confirmado'],
        'realizados': [ag for ag in todos_agendamentos if ag.status == 'concluido'],
        'cancelados': [ag for ag in todos_agendamentos if ag.status in ['cancelado_cliente', 'cancelado_profissional']]
    }

    # Ordenar por data
    for categoria in agendamentos_categorizados:
        agendamentos_categorizados[categoria].sort(key=lambda x: x.data_agendamento, reverse=True)

    # 2. Calcular comissões
    comissao_paga = 0.0
    comissao_pendente = 0.0

    for ag in agendamentos_categorizados['realizados']:
        comissao = (float(ag.servico.preco) * float(profissional.commission_percentage)) / 100
        if ag.commission_paid:
            comissao_paga += comissao
        else:
            comissao_pendente += comissao

    comissoes = {
        'paga': comissao_paga,
        'pendente': comissao_pendente
    }

    return render_template(
        'dashboard_pro.html',
        current_user=profissional,
        agendamentos=agendamentos_categorizados,
        comissoes=comissoes
    )
