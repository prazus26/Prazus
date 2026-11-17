"""Orquestra análise Gemini JÁ SALVA → avaliação → marco DJEN → cálculo → eventos prévia.

Não chama Gemini, não altera banco e não certifica prazo. Sem metadados de
comunicação e calendário oficial aplicável, não calcula qualquer vencimento.
"""
from datetime import date

from backend.service.ponte_analise_calculo_service import preparar_candidatos
from backend.service.marcos_djen_service import apurar_marcos_djen
from backend.service.calendario_judicial_service import CalendarioJudicial


def preparar_previa_agenda(*, texto: str, analise: dict, nome_advogado: str,
                         data_disponibilizacao: date, tribunal: str,
                         comunicacao_confirmada_djen: bool = False,
                         calendario: CalendarioJudicial | None = None):
    """Retorna eventos somente para hipóteses com cálculo fundamentado.

    comunicacao_confirmada_djen=True exige verificação independente da modalidade,
    jamais apenas opinião do modelo. O calendário deve se aplicar ao órgão/foro.
    """
    if type(data_disponibilizacao) is not date:
        raise ValueError('Data de disponibilização inválida')
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError('Texto da publicação inválido')

    marcos = None
    impedimentos = []
    if calendario is None:
        impedimentos.append('calendario_judicial_nao_fornecido')
    elif not isinstance(calendario, CalendarioJudicial):
        raise TypeError('Calendário deve ser CalendarioJudicial')
    elif calendario.orgao.strip().casefold() != str(tribunal).strip().casefold():
        impedimentos.append('orgao_do_calendario_incompativel')
    if comunicacao_confirmada_djen is not True:
        impedimentos.append('modalidade_de_comunicacao_nao_confirmada')

    if not impedimentos:
        try:
            marcos = apurar_marcos_djen(
                data_disponibilizacao=data_disponibilizacao,
                calendario=calendario,
                comunicacao_confirmada_djen=True,
            )
        except (ValueError, TypeError) as exc:
            impedimentos.append('marco_sem_cobertura: ' + str(exc))

    base = preparar_candidatos(
        texto, analise, nome_advogado,
        primeiro_dia_contagem=marcos.primeiro_dia_contagem if marcos else None,
        calendario=calendario if marcos else None,
    )
    eventos = []
    pendencias = []
    for candidato in base['candidatos']:
        if candidato['estado'] == 'calculado_para_conferencia' and candidato.get('vencimento_sugerido'):
            # Identificador provisório; NÃO é o ID de Prazo, nem evento publicado.
            eventos.append({
                'indice_candidato': candidato['indice'],
                'title': candidato['atividade'],
                'start': candidato['vencimento_sugerido'],
                'allDay': True,
                'extendedProps': {
                    'origem': 'gemini_mais_calculo_python',
                    'classificacao': 'calculado_para_conferencia',
                    'tribunal': tribunal,
                    'dias': candidato['dias'],
                    'contagem': candidato['contagem'],
                    'data_publicacao': marcos.data_publicacao.isoformat(),
                    'primeiro_dia_contagem': marcos.primeiro_dia_contagem.isoformat(),
                    'fonte_calendario': calendario.fonte,
                    'validado_juridicamente': False,
                },
            })
        else:
            pendencias.append({
                'indice_candidato': candidato['indice'],
                'atividade': candidato['atividade'],
                'estado': candidato['estado'],
            })

    return {
        'tribunal': tribunal,
        'representacao_identificada': base['representa'],
        'publicacao': marcos.data_publicacao.isoformat() if marcos else None,
        'primeiro_dia_contagem': marcos.primeiro_dia_contagem.isoformat() if marcos else None,
        'eventos_preview': eventos,
        'pendencias': pendencias,
        'impedimentos': impedimentos,
        'somente_leitura': True,
    }
