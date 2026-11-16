
"""Calendario judicial explicito para calculos auditaveis.

Nao consulta tribunais e nao presume feriados.
Exige cobertura declarada, fonte e validacao.

Nao utilizar calendario ficticio em producao.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import FrozenSet
import json
from pathlib import Path


class CalendarioIncompletoError(ValueError):
    pass


@dataclass(frozen=True)
class CalendarioJudicial:
    orgao: str
    inicio_cobertura: date
    fim_cobertura: date
    dias_sem_expediente: FrozenSet[date]
    fonte: str
    validado_por: str

    def __post_init__(self):
        if not all((
            self.orgao.strip(),
            self.fonte.strip(),
            self.validado_por.strip(),
        )):
            raise CalendarioIncompletoError(
                "Orgao, fonte e validacao sao obrigatorios."
            )

        if self.inicio_cobertura > self.fim_cobertura:
            raise CalendarioIncompletoError(
                "Cobertura invalida."
            )

        if any(
            not self.inicio_cobertura <= dia <= self.fim_cobertura
            for dia in self.dias_sem_expediente
        ):
            raise CalendarioIncompletoError(
                "Dia sem expediente fora da cobertura."
            )

    def exige_cobertura(self, data: date):
        if not (
            self.inicio_cobertura
            <= data
            <= self.fim_cobertura
        ):
            raise CalendarioIncompletoError(
                f"{data.isoformat()} fora da cobertura "
                f"do calendario de {self.orgao}."
            )

    def dia_util(self, data: date) -> bool:
        self.exige_cobertura(data)

        return (
            data.weekday() < 5
            and data not in self.dias_sem_expediente
        )


def carregar_calendario(caminho):
    info = json.loads(
        Path(caminho).read_text(encoding="utf-8")
    )

    try:
        return CalendarioJudicial(
            orgao=info["orgao"],
            inicio_cobertura=date.fromisoformat(
                info["inicio_cobertura"]
            ),
            fim_cobertura=date.fromisoformat(
                info["fim_cobertura"]
            ),
            dias_sem_expediente=frozenset(
                date.fromisoformat(dia)
                for dia in info["dias_sem_expediente"]
            ),
            fonte=info["fonte"],
            validado_por=info["validado_por"],
        )

    except (KeyError, TypeError, ValueError) as erro:
        raise CalendarioIncompletoError(
            f"Calendario invalido: {erro}"
        ) from erro


def calcular_vencimento_verificavel(
    *,
    primeiro_dia_contagem: date,
    dias: int,
    tipo_contagem: str,
    calendario: CalendarioJudicial,
):
    """Conta o primeiro dia como dia 1.

    A data inicial precisa ter sido validada externamente.
    """

    if type(primeiro_dia_contagem) is not date:
        raise ValueError(
            "Primeiro dia precisa ser uma data comprovada."
        )

    if type(dias) is not int or dias < 1:
        raise ValueError("Quantidade de dias invalida.")

    if tipo_contagem not in ("uteis", "corridos"):
        raise ValueError("Tipo de contagem invalido.")

    if not calendario.dia_util(primeiro_dia_contagem):
        raise ValueError(
            "Primeiro dia nao e util neste calendario."
        )

    data = primeiro_dia_contagem

    if tipo_contagem == "uteis":
        restantes = dias - 1

        while restantes:
            data += timedelta(days=1)

            if calendario.dia_util(data):
                restantes -= 1

    else:
        data += timedelta(days=dias - 1)
        calendario.exige_cobertura(data)

        while not calendario.dia_util(data):
            data += timedelta(days=1)

    return data


def calcular_data_limite_antes_evento(
    *,
    data_evento: date,
    dias: int,
    tipo_contagem: str,
    calendario: CalendarioJudicial,
):
    """Calcula data candidata anterior a um evento confirmado.

    Exclui o dia do evento da contagem regressiva.

    O resultado e somente para conferencia juridica.
    Nao certifica automaticamente um vencimento.
    """

    if type(data_evento) is not date:
        raise ValueError(
            "Data do evento precisa ser comprovada."
        )

    if type(dias) is not int or dias < 1:
        raise ValueError(
            "Quantidade de dias invalida."
        )

    # Contagem regressiva em dias corridos pode depender
    # de regras especificas. Bloquear ate validacao.
    if tipo_contagem != "uteis":
        raise ValueError(
            "Contagem regressiva nao suportada "
            "para este tipo de prazo."
        )

    calendario.exige_cobertura(data_evento)

    data = data_evento
    restantes = dias

    while restantes > 0:
        data -= timedelta(days=1)

        if calendario.dia_util(data):
            restantes -= 1

    return data
