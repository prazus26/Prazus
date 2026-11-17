"""Distingue dados históricos de eventos do pipeline automático atual.

Origem 'djen' no legado não demonstra como a data foi calculada. Diferenças
entre vencimento original e atual são preservadas como ajustes históricos,
sem atribuir autoria nem declarar validação jurídica. A tabela de eventos
atuais tem rastreabilidade própria e independe de confirmação humana.
"""


def tem_confirmacao_humana(personalizado_manualmente, revisao_estado):
    return personalizado_manualmente is True or revisao_estado == 'confirmada'


def eh_triagem(personalizado_manualmente, revisao_estado):
    return not tem_confirmacao_humana(personalizado_manualmente, revisao_estado)


def tem_ajuste_historico(origem, original, atual):
    # Não inferir ajustes a partir de NULL; não promover estimativas de 5 dias.
    return (origem == 'djen' and original is not None and atual is not None
            and original != atual)


def classificar_evento(origem, personalizado_manualmente, revisao_estado,
                      data_vencimento, data_disponibilizacao, *,
                      data_vencimento_original=None):
    """Classificação exclusiva do legado; não filtra eventos_publicacao."""
    if revisao_estado == 'descartada':
        return 'triagem', data_disponibilizacao
    if origem == 'manual' or tem_confirmacao_humana(personalizado_manualmente, revisao_estado):
        return 'prazo_personalizado', data_vencimento
    if tem_ajuste_historico(origem, data_vencimento_original, data_vencimento):
        return 'prazo_ajuste_historico', data_vencimento
    return 'triagem', data_disponibilizacao


def aplicar_estado_legado(detalhes):
    tipo, _ = classificar_evento(
        detalhes.get('origem_prazo'), detalhes.get('personalizado_manualmente'),
        detalhes.get('revisao_estado'), detalhes.get('data_vencimento'),
        detalhes.get('data_disponibilizacao'),
        data_vencimento_original=detalhes.get('data_vencimento_original'))
    detalhes['triagem'] = tipo == 'triagem'
    detalhes['ajuste_historico'] = tipo == 'prazo_ajuste_historico'
