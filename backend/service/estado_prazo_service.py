"""Classificação de eventos sem confundir triagem, candidato e prazo confirmado.

Os prazos legados de origem DJEN têm data calculada, embora não estejam
juridicamente validados. Os de origem estimativa_prazus (cinco dias
arbitrários) são triagens, salvo confirmação ou personalização.
"""


def tem_confirmacao_humana(personalizado_manualmente, revisao_estado):
    return personalizado_manualmente is True or revisao_estado == "confirmada"


def eh_triagem(personalizado_manualmente, revisao_estado):
    return not tem_confirmacao_humana(personalizado_manualmente, revisao_estado)


def classificar_evento(origem, personalizado_manualmente, revisao_estado,
                      data_vencimento, data_disponibilizacao):
    """Retorna (tipo, data). A data não atesta validade jurídica."""
    confirmado = tem_confirmacao_humana(personalizado_manualmente, revisao_estado)
    if origem == "manual" or confirmado:
        return "prazo_personalizado", data_vencimento
    if origem == "djen" and data_vencimento is not None:
        return "prazo_nao_validado", data_vencimento
    return "triagem", data_disponibilizacao
