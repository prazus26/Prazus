"""Determina marcos básicos de uma publicação DJEN, sem gravar no banco.

Não serve para comunicações do Domicílio Judicial Eletrônico, citações ou
comunicações com disciplina específica. Requer calendário judicial verificado.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from backend.service.calendario_judicial_service import CalendarioJudicial


@dataclass(frozen=True)
class MarcosDJEN:
    data_disponibilizacao: date
    data_publicacao: date
    primeiro_dia_contagem: date
    orgao: str
    fonte_calendario: str


def _proximo_util(depois_de: date, calendario: CalendarioJudicial) -> date:
    data = depois_de
    while True:
        data += timedelta(days=1)
        if calendario.dia_util(data):
            return data


def apurar_marcos_djen(*, data_disponibilizacao: date,
                       calendario: CalendarioJudicial,
                       comunicacao_confirmada_djen: bool) -> MarcosDJEN:
    """Apura publicação e início em regra geral do art. 4º, §§ 3º/4º.

    A confirmação DJEN deve vir de uma classificação independente da IA.
    Não fornece vencimento; não confunde data_publicacao com disponibilização.
    """
    if type(data_disponibilizacao) is not date:
        raise ValueError('Data de disponibilização inválida.')
    if not isinstance(calendario, CalendarioJudicial):
        raise TypeError('Informe um CalendarioJudicial verificado.')
    if comunicacao_confirmada_djen is not True:
        raise ValueError('Comunicação não confirmada como publicação DJEN comum.')
    calendario.exige_cobertura(data_disponibilizacao)
    publicada = _proximo_util(data_disponibilizacao, calendario)
    inicio = _proximo_util(publicada, calendario)
    return MarcosDJEN(
        data_disponibilizacao=data_disponibilizacao,
        data_publicacao=publicada,
        primeiro_dia_contagem=inicio,
        orgao=calendario.orgao,
        fonte_calendario=calendario.fonte,
    )
