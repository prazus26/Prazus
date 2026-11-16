
"""Conecta a avaliacao da IA ao calculo judicial.

Nao grava prazos e nao chama Gemini.
"""

from datetime import date

from service.avaliacao_prazos_ia_service import avaliar_analise

from service.calendario_judicial_service import (
    calcular_vencimento_verificavel,
    calcular_data_limite_antes_evento,
    CalendarioIncompletoError,
)


def preparar_candidatos(
    texto,
    analise,
    nome_advogado,
    *,
    primeiro_dia_contagem=None,
    calendario=None,
    data_evento=None,
    data_evento_verificada=False,
    destinatarioadvogados=None,
    oab_numero=None,
    oab_uf=None,
):
    """Prepara os candidatos usando marcos comprovados.

    Dados do DJEN sao opcionais, mas necessarios
    para confirmar representacao por OAB/UF.
    """

    avaliacao = avaliar_analise(
        texto,
        analise,
        nome_advogado,
        destinatarioadvogados=destinatarioadvogados,
        oab_numero=oab_numero,
        oab_uf=oab_uf,
    )

    saida = []

    for candidato in avaliacao["candidatos"]:
        item = {
            **candidato,
            "vencimento_sugerido": None,
        }

        estado = item["estado"]

        # Prazo anterior a evento, como uma pericia.
        if estado == "aguardando_data_evento":

            if (
                data_evento is None
                or not data_evento_verificada
            ):
                item["estado"] = "aguardando_data_evento"
                saida.append(item)
                continue

            if calendario is None:
                item["estado"] = (
                    "aguardando_calendario_judicial"
                )
                saida.append(item)
                continue

            if type(data_evento) is not date:
                raise ValueError(
                    "Data do evento precisa ser date."
                )

            try:
                limite = calcular_data_limite_antes_evento(
                    data_evento=data_evento,
                    dias=item["dias"],
                    tipo_contagem=item["contagem"],
                    calendario=calendario,
                )

            except (
                CalendarioIncompletoError,
                ValueError,
            ) as erro:
                item["estado"] = (
                    "calendario_ou_marco_invalido"
                )
                item["motivo"] = type(erro).__name__

            else:
                item["estado"] = (
                    "calculado_para_conferencia"
                )
                item["vencimento_sugerido"] = (
                    limite.isoformat()
                )

            saida.append(item)
            continue

        # Obrigacoes bloqueadas por outros motivos.
        if estado != "aguardando_calendario_judicial":
            saida.append(item)
            continue

        # Prazo com marco inicial comprovado.
        if (
            calendario is None
            or primeiro_dia_contagem is None
        ):
            item["estado"] = (
                "aguardando_marco_e_calendario"
            )
            saida.append(item)
            continue

        if type(primeiro_dia_contagem) is not date:
            raise ValueError(
                "Primeiro dia precisa ser date comprovado."
            )

        try:
            vencimento = calcular_vencimento_verificavel(
                primeiro_dia_contagem=primeiro_dia_contagem,
                dias=item["dias"],
                tipo_contagem=item["contagem"],
                calendario=calendario,
            )

        except (
            CalendarioIncompletoError,
            ValueError,
        ) as erro:
            item["estado"] = (
                "calendario_ou_marco_invalido"
            )
            item["motivo"] = type(erro).__name__

        else:
            item["estado"] = (
                "calculado_para_conferencia"
            )
            item["vencimento_sugerido"] = (
                vencimento.isoformat()
            )

        saida.append(item)

    return {
        "representa": avaliacao["representa"],
        "total": len(saida),
        "candidatos": saida,
        "escreveu_banco": False,
    }
