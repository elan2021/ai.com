from flask import Blueprint, jsonify, g, request
from app.models import Loja, Servico, Profissional, Agendamento
from app.services import calcular_horarios_disponiveis
from app.db import db
import datetime

api_bp = Blueprint('api', __name__)

@api_bp.url_value_preprocessor
def pull_loja_from_path(endpoint, values):
    """
    Captura o `loja_path` da URL, encontra a loja correspondente
    e a armazena no objeto `g` do Flask para uso nas views.
    Retorna 404 se a loja não for encontrada.
    """
    loja_path = values.pop('loja_path', None)
    if loja_path:
        g.loja = Loja.query.filter_by(path=loja_path).first_or_404(
            description=f"Nenhuma loja encontrada no caminho '{loja_path}'"
        )
    else:
        # Se nenhuma loja_path for fornecida na URL, o que não deve acontecer
        # com a configuração atual do blueprint.
        g.loja = None

@api_bp.before_request
def before_request_check():
    """Garante que uma loja foi carregada antes de cada requisição."""
    if not hasattr(g, 'loja') or g.loja is None:
        # Este é um fallback, o `first_or_404` já deve ter lidado com isso.
        return jsonify({'message': 'Caminho da loja inválido ou não fornecido.'}), 404


@api_bp.route('/servicos', methods=['GET'])
def listar_servicos():
    """Lista todos os serviços de uma loja específica."""
    servicos_loja = Servico.query.filter_by(loja_id=g.loja.id).all()

    resultado = []
    for servico in servicos_loja:
        profissionais_data = [{
            'id': p.id,
            'nome': p.nome
        } for p in servico.profissionais]

        resultado.append({
            'id': servico.id,
            'nome': servico.nome,
            'preco': f"{servico.preco:.2f}",
            'duracao': servico.duracao,
            'profissionais': profissionais_data
        })

    return jsonify(resultado)


@api_bp.route('/servicos/profissionais', methods=['GET'])
def listar_profissionais_por_servico():
    """Lista os profissionais que realizam um serviço específico."""
    servico_id = request.args.get('servico_id', type=int)
    if not servico_id:
        return jsonify({'message': 'O parâmetro `servico_id` é obrigatório e deve ser um inteiro.'}), 400

    # Garante que o serviço pertence à loja atual
    servico = Servico.query.filter_by(id=servico_id, loja_id=g.loja.id).first()

    if not servico:
        return jsonify({'message': 'Serviço não encontrado nesta loja.'}), 404

    profissionais_data = [{
        'id': p.id,
        'nome': p.nome
    } for p in servico.profissionais]

    return jsonify(profissionais_data)


@api_bp.route('/horarios-disponiveis', methods=['GET'])
def listar_horarios_disponiveis():
    """Calcula e retorna uma lista de horários disponíveis."""
    servico_id = request.args.get('servico_id', type=int)
    profissional_id = request.args.get('profissional_id', type=int)
    data = request.args.get('data')

    # Validação dos parâmetros de entrada
    if not all([servico_id, profissional_id, data]):
        return jsonify({'message': 'Os parâmetros `servico_id`, `profissional_id` e `data` (YYYY-MM-DD) são obrigatórios.'}), 400

    servico = Servico.query.filter_by(id=servico_id, loja_id=g.loja.id).first()
    if not servico:
        return jsonify({'message': 'Serviço não encontrado nesta loja.'}), 404

    profissional = Profissional.query.filter_by(id=profissional_id, loja_id=g.loja.id).first()
    if not profissional:
        return jsonify({'message': 'Profissional não encontrado nesta loja.'}), 404

    if servico not in profissional.servicos:
        return jsonify({'message': 'Este profissional não oferece o serviço selecionado.'}), 400

    # Chama a função de serviço para fazer o cálculo
    horarios = calcular_horarios_disponiveis(profissional, servico, data)

    # A função de serviço pode retornar um erro
    if isinstance(horarios, dict) and 'error' in horarios:
        return jsonify({'message': horarios['error']}), 400

    return jsonify(horarios)


@api_bp.route('/agendamentos', methods=['POST'])
def criar_agendamento():
    """Cria um novo agendamento."""
    data = request.get_json()
    required = ['servico_id', 'profissional_id', 'data_agendamento', 'horario_inicio', 'cliente_nome', 'cliente_telefone']
    if not data or not all(f in data for f in required):
        return jsonify({'message': f'Campos obrigatórios ausentes: {required}'}), 400

    servico = Servico.query.filter_by(id=data['servico_id'], loja_id=g.loja.id).first()
    if not servico: return jsonify({'message': 'Serviço não encontrado'}), 404

    profissional = Profissional.query.filter_by(id=data['profissional_id'], loja_id=g.loja.id).first()
    if not profissional: return jsonify({'message': 'Profissional não encontrado'}), 404

    if servico not in profissional.servicos:
        return jsonify({'message': 'Este profissional não oferece o serviço selecionado.'}), 400

    # Revalida se o horário está de fato disponível para evitar concorrência
    horarios_disponiveis = calcular_horarios_disponiveis(profissional, servico, data['data_agendamento'])
    if isinstance(horarios_disponiveis, dict) and 'error' in horarios_disponiveis:
         return jsonify({'message': horarios_disponiveis['error']}), 400

    is_available = any(h['value'] == data['horario_inicio'] for h in horarios_disponiveis)
    if not is_available:
        return jsonify({'message': 'O horário solicitado não está mais disponível.'}), 409

    try:
        horario_inicio_dt = datetime.datetime.strptime(data['horario_inicio'], '%H:%M').time()
        data_agendamento_dt = datetime.datetime.strptime(data['data_agendamento'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Formato de data ou hora inválido. Use YYYY-MM-DD e HH:MM.'}), 400

    duracao = datetime.timedelta(minutes=servico.duracao)
    horario_fim_dt = (datetime.datetime.combine(datetime.date.today(), horario_inicio_dt) + duracao).time()

    novo_agendamento = Agendamento(
        servico_id=servico.id, profissional_id=profissional.id, loja_id=g.loja.id,
        data_agendamento=data_agendamento_dt, horario_inicio=horario_inicio_dt, horario_fim=horario_fim_dt,
        cliente_nome=data['cliente_nome'], cliente_telefone=data['cliente_telefone'],
        cliente_email=data.get('cliente_email'), observacoes_cliente=data.get('observacoes_cliente'),
        status='pendente'
    )
    db.session.add(novo_agendamento)
    db.session.commit()

    return jsonify({'message': 'Agendamento criado com sucesso!', 'agendamento_id': novo_agendamento.id}), 201


@api_bp.route('/agendamentos/<int:agendamento_id>/status', methods=['PATCH'])
def atualizar_status_agendamento(agendamento_id):
    """Atualiza o status de um agendamento existente."""
    data = request.get_json()
    novo_status = data.get('status')

    if not novo_status:
        return jsonify({'message': 'O campo `status` é obrigatório.'}), 400

    allowed = ['pendente', 'confirmado', 'cancelado_cliente', 'cancelado_profissional', 'concluido', 'nao_compareceu']
    if novo_status not in allowed:
        return jsonify({'message': f'Status inválido. Permitidos: {allowed}'}), 400

    agendamento = Agendamento.query.filter_by(id=agendamento_id, loja_id=g.loja.id).first_or_404()
    agendamento.status = novo_status
    db.session.commit()

    return jsonify({
        'message': 'Status do agendamento atualizado com sucesso!',
        'agendamento_id': agendamento.id,
        'novo_status': agendamento.status
    })
