from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models import PagamentoSinal, Agendamento
from app.db import db
from app.utils import gerar_pix_copia_e_cola

pagamento_bp = Blueprint('pagamento', __name__, template_folder='../templates/pagamento')

@pagamento_bp.route('/<string:id_publico>')
def realizar_pagamento(id_publico):
    """Exibe a página de pagamento para um sinal de agendamento."""
    pagamento = PagamentoSinal.query.filter_by(id_publico=id_publico).first_or_404()

    if pagamento.status == 'pago':
        flash('Este pagamento já foi realizado.', 'info')
        return redirect(url_for('pagamento.sucesso_pagamento'))

    agendamento = pagamento.agendamento
    loja = agendamento.loja

    pix_code = "Chave PIX não configurada pelo proprietário."
    if loja.chave_pix:
        pix_code = gerar_pix_copia_e_cola(
            chave_pix=loja.chave_pix,
            nome_loja=loja.title,
            cidade_loja="SAO PAULO", # Cidade fixa por simplicidade
            valor=float(pagamento.valor),
            txid=f"AGEND{agendamento.id}"
        )

    return render_template('pagamento.html', pagamento=pagamento, pix_code=pix_code)

@pagamento_bp.route('/<string:id_publico>/confirmar', methods=['POST'])
def confirmar_pagamento(id_publico):
    """Processa a confirmação (simulada) do pagamento."""
    pagamento = PagamentoSinal.query.filter_by(id_publico=id_publico).first_or_404()

    if pagamento.status == 'pago':
        return redirect(url_for('pagamento.sucesso_pagamento'))

    # Atualiza os status
    pagamento.status = 'pago'
    pagamento.agendamento.status = 'confirmado'
    db.session.commit()

    return redirect(url_for('pagamento.sucesso_pagamento'))

@pagamento_bp.route('/sucesso')
def sucesso_pagamento():
    """Página de sucesso após o pagamento."""
    return render_template('sucesso.html')
