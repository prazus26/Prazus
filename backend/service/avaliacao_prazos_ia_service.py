
"""Avalia candidatos de prazo extraidos pelo Gemini.

Nao consulta APIs, nao escreve no banco e nao certifica vencimentos.
A representacao pode ser comprovada usando a identificacao DJEN.
"""

import re
import unicodedata
from datetime import date

from backend.service.calculo_prazo_service import (
    calcular_data_inicio,
    calcular_vencimento,
)
from backend.service.validacao_analise_service import validar_resultado


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def _normalizar_oab(numero):
    return "".join(
        caractere
        for caractere in str(numero or "")
        if caractere.isdigit()
    )


def _lado_do_papel(papel):
    texto = _normalizar(papel)

    if re.search(
        r"\b(autor|autora|autores|requerente|reclamante)\b",
        texto,
    ):
        return "autor"

    if re.search(
        r"\b(reu|re|requerido|requerida|reclamado|reclamada)\b",
        texto,
    ):
        return "reu"

    return None


def _lado_destinatario(destinatario):
    return _lado_do_papel(destinatario)


def _lado_representado(participantes, nome_advogado):
    """Identificacao antiga por nome, preservada por compatibilidade."""

    nome = _normalizar(nome_advogado)

    if not nome:
        return None

    encontrados = set()

    for participante in participantes:
        if not isinstance(participante, dict):
            continue

        if _normalizar(participante.get("nome")) != nome:
            continue

        papel = _normalizar(participante.get("papel"))

        if "advogad" not in papel:
            continue

        lado = _lado_do_papel(papel)

        if lado:
            encontrados.add(lado)

    return (
        next(iter(encontrados))
        if len(encontrados) == 1
        else None
    )


def _lado_representado_djen(
    participantes,
    destinatarioadvogados,
    oab_numero,
    oab_uf,
):
    """Confirma a parte por OAB/UF + nome + papel processual.

    OAB/UF identificam o destinatario oficial.
    O nome liga esse destinatario ao participante da analise.
    O papel do participante indica a parte representada.

    Se houver ambiguidade, retorna None.
    """

    numero_usuario = _normalizar_oab(oab_numero)
    uf_usuario = str(oab_uf or "").strip().upper()

    if not numero_usuario or not uf_usuario:
        return None

    if not isinstance(destinatarioadvogados, list):
        return None

    nomes_confirmados = set()

    for registro in destinatarioadvogados:
        if not isinstance(registro, dict):
            continue

        advogado = registro.get("advogado")

        if not isinstance(advogado, dict):
            continue

        numero_djen = _normalizar_oab(
            advogado.get("numero_oab")
        )

        uf_djen = str(
            advogado.get("uf_oab") or ""
        ).strip().upper()

        if (
            numero_djen == numero_usuario
            and uf_djen == uf_usuario
        ):
            nome = _normalizar(advogado.get("nome"))

            if nome:
                nomes_confirmados.add(nome)

    if not nomes_confirmados:
        return None

    lados = set()

    for participante in participantes:
        if not isinstance(participante, dict):
            continue

        nome = _normalizar(participante.get("nome"))

        if nome not in nomes_confirmados:
            continue

        papel = _normalizar(participante.get("papel"))

        if "advogad" not in papel:
            continue

        lado = _lado_do_papel(papel)

        if lado:
            lados.add(lado)

    if len(lados) != 1:
        return None

    return next(iter(lados))


def _identificar_marco_temporal(prazo):
    evidencia = _normalizar(prazo.get("evidencia"))
    atividade = _normalizar(prazo.get("atividade"))

    prazo_antes = re.search(
        r"\b\d+\s+dias?\s+(?:(?:uteis|corridos)\s+)?antes\b",
        evidencia,
    )

    referencia_pericia = (
        "pericia" in evidencia
        or "pericia" in atividade
    )

    if prazo_antes and referencia_pericia:
        return {
            "tipo": "antes_de_evento",
            "evento": "pericia",
            "direcao": "regressiva",
        }

    return {
        "tipo": "marco_a_verificar",
        "evento": None,
        "direcao": None,
    }


def avaliar_analise(
    texto,
    analise,
    nome_advogado,
    *,
    data_publicacao=None,
    feriados=None,
    calendario_judicial_validado=False,
    destinatarioadvogados=None,
    oab_numero=None,
    oab_uf=None,
):
    """Classifica candidatos sem gravar prazos.

    Os novos parametros sao opcionais para manter
    compatibilidade com as chamadas anteriores.
    """

    dados = validar_resultado(texto, analise)

    participantes = dados.get("participantes", [])

    lado_por_nome = _lado_representado(
        participantes,
        nome_advogado,
    )

    lado_por_djen = _lado_representado_djen(
        participantes,
        destinatarioadvogados,
        oab_numero,
        oab_uf,
    )

    # Evidencias conflitantes nao autorizam atribuicao.
    if (
        lado_por_nome
        and lado_por_djen
        and lado_por_nome != lado_por_djen
    ):
        lado_advogado = None
    else:
        lado_advogado = lado_por_djen or lado_por_nome

    avaliados = []

    for indice, prazo in enumerate(dados["prazos"]):
        lado_destinatario = _lado_destinatario(
            prazo.get("destinatario")
        )

        marco = _identificar_marco_temporal(prazo)

        item = {
            "indice": indice,
            "atividade": str(
                prazo.get("atividade") or ""
            ).strip()[:150],
            "dias": prazo.get("dias"),
            "contagem": prazo.get("contagem"),
            "destinatario": prazo.get("destinatario"),
            "marco_temporal": marco["tipo"],
            "evento_referencia": marco["evento"],
            "direcao_contagem": marco["direcao"],
            "estado": None,
            "vencimento_sugerido": None,
        }

        if not lado_advogado or not lado_destinatario:
            item["estado"] = (
                "representacao_ou_destinatario_indeterminado"
            )

        elif lado_advogado != lado_destinatario:
            item["estado"] = "parte_contraria"

        elif prazo.get("precisa_revisao", True):
            item["estado"] = "revisao_necessaria"

        elif (
            not item["atividade"]
            or type(item["dias"]) is not int
            or item["dias"] < 1
            or item["contagem"] not in ("uteis", "corridos")
        ):
            item["estado"] = "regra_incompleta"

        elif marco["tipo"] == "antes_de_evento":
            item["estado"] = "aguardando_data_evento"

        elif not (
            calendario_judicial_validado
            and type(data_publicacao) is date
            and isinstance(feriados, (list, set, tuple))
        ):
            item["estado"] = (
                "aguardando_calendario_judicial"
            )

        else:
            inicio = calcular_data_inicio(
                data_publicacao,
                set(feriados),
            )

            vencimento = calcular_vencimento(
                inicio,
                item["dias"],
                item["contagem"],
                set(feriados),
            )

            item["estado"] = (
                "data_calculada_para_conferencia"
            )
            item["vencimento_sugerido"] = (
                vencimento.isoformat()
            )

        avaliados.append(item)

    return {
        "representa": lado_advogado,
        "candidatos": avaliados,
        "total": len(avaliados),
    }
