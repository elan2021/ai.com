import datetime
from app.models import HorarioTrabalho, Agendamento

def calcular_horarios_disponiveis(profissional, servico, data_str):
    """
    Calcula os horários disponíveis para um profissional, serviço e data.
    A lógica é:
    1. Pega o horário de trabalho do profissional no dia da semana.
    2. Pega todos os agendamentos existentes para ele na data.
    3. Itera sobre o expediente em intervalos fixos (ex: 15 min).
    4. Para cada intervalo, verifica se um novo agendamento (com a duração do serviço)
       cabe sem colidir com os agendamentos existentes.
    """
    try:
        data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        # Retorna um dicionário de erro para ser tratado na view
        return {'error': 'Formato de data inválido. Use YYYY-MM-DD.'}

    dia_da_semana = data.weekday()  # 0=Segunda, ..., 6=Domingo

    horario_trabalho = HorarioTrabalho.query.filter_by(
        profissional_id=profissional.id,
        dia_da_semana=dia_da_semana
    ).first()

    if not horario_trabalho:
        return []  # Profissional não trabalha neste dia

    agendamentos_existentes = Agendamento.query.filter_by(
        profissional_id=profissional.id,
        data_agendamento=data
    ).order_by(Agendamento.horario_inicio).all()

    horarios_disponiveis = []
    duracao_servico = datetime.timedelta(minutes=servico.duracao)

    horario_atual = datetime.datetime.combine(data, horario_trabalho.hora_inicio)
    fim_expediente = datetime.datetime.combine(data, horario_trabalho.hora_fim)

    # Itera sobre o dia em intervalos de 15 minutos
    while horario_atual + duracao_servico <= fim_expediente:
        horario_fim_slot = horario_atual + duracao_servico

        slot_livre = True
        for agendamento in agendamentos_existentes:
            inicio_agendamento = datetime.datetime.combine(data, agendamento.horario_inicio)
            fim_agendamento = datetime.datetime.combine(data, agendamento.horario_fim)

            # Checa se há qualquer sobreposição entre o slot candidato e o agendamento existente
            if max(horario_atual, inicio_agendamento) < min(horario_fim_slot, fim_agendamento):
                slot_livre = False
                break

        if slot_livre:
            horarios_disponiveis.append({
                "value": horario_atual.strftime('%H:%M'),
                "label": f"{horario_atual.strftime('%H:%M')} - {horario_fim_slot.strftime('%H:%M')}"
            })

        # Avança para o próximo slot potencial
        horario_atual += datetime.timedelta(minutes=15)

    return horarios_disponiveis
