def gerar_pix_copia_e_cola(chave_pix, nome_loja, cidade_loja, valor, txid="***"):
    """
    Gera uma string de PIX Copia e Cola **SIMULADA**.
    Esta função não gera um código válido para transações reais,
    apenas imita o formato padrão do BR Code para fins de demonstração.
    """
    # Remove caracteres especiais e limita o tamanho dos campos
    nome_loja_fmt = ''.join(e for e in nome_loja if e.isalnum() or e.isspace()).upper()[:25]
    cidade_loja_fmt = ''.join(e for e in cidade_loja if e.isalnum() or e.isspace()).upper()[:15]

    # Formata o valor para ter duas casas decimais
    valor_fmt = f"{valor:.2f}"

    # Função auxiliar para montar um campo TLV (Tag-Length-Value)
    def tlv(tag, value):
        return str(tag).zfill(2) + str(len(value)).zfill(2) + value

    # Monta os campos do payload BR Code
    payload_format_indicator = tlv('00', '01')
    merchant_account_information = tlv('26', tlv('00', 'br.gov.bcb.pix') + tlv('01', chave_pix))
    merchant_category_code = tlv('52', '0000') # 0000 para "Não especificado"
    transaction_currency = tlv('53', '986') # 986 = BRL
    transaction_amount = tlv('54', valor_fmt)
    country_code = tlv('58', 'BR')
    merchant_name = tlv('59', nome_loja_fmt)
    merchant_city = tlv('60', cidade_loja_fmt)

    # TXID é tipicamente usado para conciliação
    additional_data_field = tlv('62', tlv('05', txid))

    # Junta todos os campos
    payload = f"{payload_format_indicator}{merchant_account_information}{merchant_category_code}{transaction_currency}{transaction_amount}{country_code}{merchant_name}{merchant_city}{additional_data_field}"

    # Adiciona o campo de CRC16 no final
    payload += '6304'

    # Calcula um CRC16 "fake" para a demonstração
    # Um cálculo real seria mais complexo
    crc16 = 0xFFFF
    for byte in payload.encode('utf-8'):
        crc16 ^= (byte << 8)
        for _ in range(8):
            if (crc16 & 0x8000):
                crc16 = (crc16 << 1) ^ 0x1021
            else:
                crc16 <<= 1

    crc_fmt = format(crc16 & 0xFFFF, '04X')

    return payload + crc_fmt


import requests
import threading
import json
from flask import current_app

def _send_webhook_in_background(url, data):
    """Função executada em segundo plano para enviar o webhook."""
    try:
        requests.post(url, data=json.dumps(data, default=str), headers={'Content-Type': 'application/json'}, timeout=10)
    except requests.exceptions.RequestException as e:
        # Em um app real, um sistema de logging robusto seria ideal.
        # Para este exemplo, apenas imprimimos o erro no console do servidor.
        print(f"ERRO DE WEBHOOK: Falha ao enviar para {url}. Erro: {e}")

def disparar_webhook_agendamento(agendamento):
    """Prepara os dados e dispara o webhook de agendamento em uma thread separada."""
    if not agendamento.loja.webhook_url:
        return

    dados_webhook = {
        "evento": "novo_agendamento",
        "agendamento_id": agendamento.id,
        "data_agendamento": agendamento.data_agendamento,
        "horario_inicio": agendamento.horario_inicio,
        "cliente": {
            "nome": agendamento.cliente_nome,
            "telefone": agendamento.cliente_telefone,
            "email": agendamento.cliente_email
        },
        "servico": {
            "id": agendamento.servico.id,
            "nome": agendamento.servico.nome,
            "preco": agendamento.servico.preco
        },
        "profissional": {
            "id": agendamento.profissional.id,
            "nome": agendamento.profissional.nome,
            "telefone": agendamento.profissional.telefone
        }
    }

    # Inicia a thread para enviar o webhook sem bloquear a requisição principal
    thread = threading.Thread(
        target=_send_webhook_in_background,
        args=(agendamento.loja.webhook_url, dados_webhook)
    )
    thread.start()
