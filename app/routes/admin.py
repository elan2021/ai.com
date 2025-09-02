from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, g, current_app
from functools import wraps
import jwt
import datetime

from app.models import Proprietario, Loja, Servico, Profissional, Agendamento
from app.db import db
from app import bcrypt

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

def admin_token_required(f):
    """
    Decorator para proteger rotas do admin. Verifica o token JWT no cookie.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token:
            flash('É necessário fazer login para acessar esta página.', 'warning')
            return redirect(url_for('main.index'))
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # Armazena o usuário atual no 'g' do Flask para acesso fácil nas rotas
            g.current_user = Proprietario.query.get(data['proprietario_id'])
            if g.current_user is None:
                raise jwt.InvalidTokenError
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            flash('Sua sessão expirou ou é inválida. Por favor, faça login novamente.', 'error')
            # Limpa o cookie inválido e redireciona para o login
            resp = make_response(redirect(url_for('main.index')))
            resp.set_cookie('admin_token', '', expires=0)
            return resp
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/logout')
@admin_token_required
def logout():
    """Limpa o cookie de autenticação e desloga o usuário."""
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('admin_token', '', expires=0)
    flash('Você foi desconectado com sucesso.', 'info')
    return response

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_token_required
def dashboard():
    """Exibe o dashboard principal com a lista de lojas do proprietário."""
    # g.current_user é definido pelo decorator @admin_token_required
    lojas = g.current_user.lojas
    return render_template('dashboard.html', lojas=lojas, current_user=g.current_user)


@admin_bp.route('/lojas/novo', methods=['GET', 'POST'])
@admin_token_required
def add_loja():
    """Exibe o formulário e processa a criação de uma nova loja."""
    if request.method == 'POST':
        title = request.form.get('title')
        path = request.form.get('path', '').lower().strip()

        # Re-usa a mesma lógica de validação da API de lojas
        import re
        if not all([title, path]):
            flash('Título e Caminho da URL são obrigatórios.', 'error')
        elif not re.match(r'^[a-z0-9-]+$', path):
            flash('O caminho (path) deve conter apenas letras minúsculas, números e hífens.', 'error')
        elif Loja.query.filter_by(path=path).first():
            flash('Este caminho de loja já está em uso.', 'error')
        else:
            nova_loja = Loja(
                title=title,
                path=path,
                proprietario_id=g.current_user.id
            )
            db.session.add(nova_loja)
            db.session.commit()
            flash('Loja criada com sucesso!', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('add_loja.html', current_user=g.current_user)


@admin_bp.route('/loja/<int:loja_id>')
@admin_token_required
def loja_dashboard(loja_id):
    """Exibe o painel de gerenciamento para uma loja específica."""
    loja = Loja.query.get_or_404(loja_id)

    # Validação de segurança: o usuário logado é o dono da loja?
    if loja.proprietario_id != g.current_user.id:
        flash('Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Busca os dados relacionados para exibir no painel
    servicos = loja.servicos
    profissionais = loja.profissionais
    # Ordena os agendamentos por data e hora, dos mais recentes para os mais antigos
    agendamentos = sorted(loja.agendamentos, key=lambda x: (x.data_agendamento, x.horario_inicio), reverse=True)

    return render_template(
        'loja_dashboard.html',
        loja=loja,
        servicos=servicos,
        profissionais=profissionais,
        agendamentos=agendamentos,
        current_user=g.current_user
    )


@admin_bp.route('/loja/<int:loja_id>/servicos/novo', methods=['GET', 'POST'])
@admin_token_required
def add_servico(loja_id):
    """Exibe o formulário e processa a criação de um novo serviço."""
    loja = Loja.query.get_or_404(loja_id)
    if loja.proprietario_id != g.current_user.id:
        flash('Acesso não permitido.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        duracao = request.form.get('duracao')
        cobrar_sinal = request.form.get('cobrar_sinal') == 'y'
        percentual_sinal = request.form.get('percentual_sinal')

        if not nome or not preco or not duracao:
            flash('Campos básicos são obrigatórios.', 'error')
        elif cobrar_sinal and (not percentual_sinal or float(percentual_sinal) <= 0):
            flash('Se a cobrança de sinal estiver ativa, o percentual deve ser maior que zero.', 'error')
        else:
            try:
                novo_servico = Servico(
                    nome=nome,
                    preco=float(preco),
                    duracao=int(duracao),
                    loja_id=loja.id,
                    cobrar_sinal=cobrar_sinal,
                    percentual_sinal=float(percentual_sinal) if cobrar_sinal and percentual_sinal else None
                )
                db.session.add(novo_servico)
                db.session.commit()
                flash('Serviço adicionado com sucesso!', 'success')
                return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))
            except (ValueError, TypeError):
                flash('Valores numéricos inválidos.', 'error')

    return render_template('add_servico.html', loja=loja, current_user=g.current_user, servico=None)


@admin_bp.route('/loja/<int:loja_id>/servicos/<int:servico_id>/editar', methods=['GET', 'POST'])
@admin_token_required
def edit_servico(loja_id, servico_id):
    """Exibe o formulário e processa a edição de um serviço existente."""
    loja = Loja.query.get_or_404(loja_id)
    servico = Servico.query.get_or_404(servico_id)

    if loja.proprietario_id != g.current_user.id or servico.loja_id != loja.id:
        flash('Acesso não permitido.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = request.form.get('preco')
        duracao = request.form.get('duracao')
        cobrar_sinal = request.form.get('cobrar_sinal') == 'y'
        percentual_sinal = request.form.get('percentual_sinal')

        if not nome or not preco or not duracao:
            flash('Campos básicos são obrigatórios.', 'error')
        elif cobrar_sinal and (not percentual_sinal or float(percentual_sinal) <= 0):
            flash('Se a cobrança de sinal estiver ativa, o percentual deve ser maior que zero.', 'error')
        else:
            try:
                servico.nome = nome
                servico.preco = float(preco)
                servico.duracao = int(duracao)
                servico.cobrar_sinal = cobrar_sinal
                servico.percentual_sinal = float(percentual_sinal) if cobrar_sinal and percentual_sinal else None

                db.session.commit()
                flash('Serviço atualizado com sucesso!', 'success')
                return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))
            except (ValueError, TypeError):
                flash('Valores numéricos inválidos.', 'error')

    return render_template('edit_servico.html', loja=loja, servico=servico, current_user=g.current_user)


@admin_bp.route('/loja/<int:loja_id>/servicos/<int:servico_id>/deletar', methods=['POST'])
@admin_token_required
def delete_servico(loja_id, servico_id):
    """Processa a exclusão de um serviço."""
    loja = Loja.query.get_or_404(loja_id)
    servico = Servico.query.get_or_404(servico_id)

    if loja.proprietario_id != g.current_user.id or servico.loja_id != loja.id:
        flash('Ação não permitida.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Nota: Em um app real, seria importante verificar se o serviço
    # não está atrelado a agendamentos futuros antes de excluir.
    # Por simplicidade, faremos a exclusão direta.
    db.session.delete(servico)
    db.session.commit()

    flash('Serviço excluído com sucesso.', 'success')
    return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))


@admin_bp.route('/loja/<int:loja_id>/profissionais/novo', methods=['GET', 'POST'])
@admin_token_required
def add_profissional(loja_id):
    """Exibe o formulário e processa a criação de um novo profissional."""
    loja = Loja.query.get_or_404(loja_id)
    if loja.proprietario_id != g.current_user.id:
        flash('Acesso não permitido.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        username = request.form.get('username')
        password = request.form.get('password')
        commission_percentage = request.form.get('commission_percentage')
        telefone = request.form.get('telefone')
        servico_ids = request.form.getlist('servicos')

        if not all([nome, username, password, commission_percentage]):
            flash('Todos os campos são obrigatórios.', 'error')
        elif Profissional.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'error')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            novo_profissional = Profissional(
                nome=nome,
                username=username,
                telefone=telefone,
                password_hash=hashed_password,
                commission_percentage=float(commission_percentage),
                loja_id=loja.id
            )

            servicos = Servico.query.filter(Servico.id.in_(servico_ids), Servico.loja_id == loja.id).all()
            novo_profissional.servicos = servicos

            db.session.add(novo_profissional)
            db.session.commit()
            flash('Profissional adicionado com sucesso!', 'success')
            return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))

    todos_servicos = loja.servicos
    return render_template('add_profissional.html', loja=loja, todos_servicos=todos_servicos, current_user=g.current_user, profissional=None)


@admin_bp.route('/loja/<int:loja_id>/profissionais/<int:profissional_id>/editar', methods=['GET', 'POST'])
@admin_token_required
def edit_profissional(loja_id, profissional_id):
    """Exibe o formulário e processa a edição de um profissional existente."""
    loja = Loja.query.get_or_404(loja_id)
    profissional = Profissional.query.get_or_404(profissional_id)

    if loja.proprietario_id != g.current_user.id or profissional.loja_id != loja.id:
        flash('Acesso não permitido.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        username = request.form.get('username')
        password = request.form.get('password') # Pode estar em branco
        commission_percentage = request.form.get('commission_percentage')
        telefone = request.form.get('telefone')
        servico_ids = request.form.getlist('servicos')

        # Verifica se o username foi alterado e se o novo já existe
        if username != profissional.username and Profissional.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'error')
        elif not all([nome, username, commission_percentage]):
            flash('Os campos nome, usuário e comissão são obrigatórios.', 'error')
        else:
            profissional.nome = nome
            profissional.username = username
            profissional.telefone = telefone
            profissional.commission_percentage = float(commission_percentage)

            # Atualiza a senha apenas se uma nova for fornecida
            if password:
                profissional.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

            servicos = Servico.query.filter(Servico.id.in_(servico_ids), Servico.loja_id == loja.id).all()
            profissional.servicos = servicos

            db.session.commit()
            flash('Profissional atualizado com sucesso!', 'success')
            return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))

    todos_servicos = loja.servicos
    return render_template('edit_profissional.html', loja=loja, profissional=profissional, todos_servicos=todos_servicos, current_user=g.current_user)


@admin_bp.route('/loja/<int:loja_id>/profissionais/<int:profissional_id>/deletar', methods=['POST'])
@admin_token_required
def delete_profissional(loja_id, profissional_id):
    """Processa a exclusão de um profissional."""
    loja = Loja.query.get_or_404(loja_id)
    profissional = Profissional.query.get_or_404(profissional_id)

    if loja.proprietario_id != g.current_user.id or profissional.loja_id != loja.id:
        flash('Ação não permitida.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Nota: A exclusão de um profissional pode impactar agendamentos existentes.
    # Em um app real, seria ideal implementar um soft delete ou verificações adicionais.
    db.session.delete(profissional)
    db.session.commit()

    flash('Profissional excluído com sucesso.', 'success')
    return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))


@admin_bp.route('/loja/<int:loja_id>/agendamentos/<int:agendamento_id>/pagar-comissao', methods=['POST'])
@admin_token_required
def toggle_commission_status(loja_id, agendamento_id):
    """Alterna o status de pagamento da comissão de um agendamento (pago/pendente)."""
    loja = Loja.query.get_or_404(loja_id)
    agendamento = Agendamento.query.get_or_404(agendamento_id)

    if loja.proprietario_id != g.current_user.id or agendamento.loja_id != loja.id:
        flash('Ação não permitida.', 'error')
        return redirect(url_for('admin.dashboard'))

    if agendamento.status != 'concluido':
        flash('Apenas agendamentos concluídos podem ter a comissão paga.', 'error')
        return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))

    agendamento.commission_paid = not agendamento.commission_paid
    db.session.commit()

    status_text = "paga" if agendamento.commission_paid else "pendente"
    flash(f'Status da comissão atualizado para {status_text}.', 'success')
    return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))


@admin_bp.route('/loja/<int:loja_id>/config', methods=['GET', 'POST'])
@admin_token_required
def config_loja(loja_id):
    """Exibe e processa o formulário de configurações da loja (ex: Chave PIX)."""
    loja = Loja.query.get_or_404(loja_id)
    if loja.proprietario_id != g.current_user.id:
        flash('Acesso não permitido.', 'error')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        chave_pix = request.form.get('chave_pix')
        webhook_url = request.form.get('webhook_url')
        loja.chave_pix = chave_pix
        loja.webhook_url = webhook_url
        db.session.commit()
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('admin.config_loja', loja_id=loja.id))

    return render_template('config_loja.html', loja=loja, current_user=g.current_user)


@admin_bp.route('/loja/<int:loja_id>/agendamentos/<int:agendamento_id>/status', methods=['POST'])
@admin_token_required
def update_agendamento_status(loja_id, agendamento_id):
    """Atualiza o status de um agendamento específico."""
    loja = Loja.query.get_or_404(loja_id)
    agendamento = Agendamento.query.get_or_404(agendamento_id)

    if loja.proprietario_id != g.current_user.id or agendamento.loja_id != loja.id:
        flash('Ação não permitida.', 'error')
        return redirect(url_for('admin.dashboard'))

    novo_status = request.form.get('status')

    allowed_statuses = ['pendente', 'confirmado', 'cancelado_cliente', 'cancelado_profissional', 'concluido', 'nao_compareceu']
    if novo_status not in allowed_statuses:
        flash('Status inválido.', 'error')
    else:
        agendamento.status = novo_status
        db.session.commit()
        flash('Status do agendamento atualizado com sucesso.', 'success')

    return redirect(url_for('admin.loja_dashboard', loja_id=loja.id))
