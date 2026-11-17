
"""Orquestra reservas, Gemini e armazenamento das análises.

Não mantém transação aberta durante a chamada à API.
Não cria prazos automaticamente nesta camada.
"""

import os

from pydantic import ValidationError

from backend.repository.analise_ia_repository import (
    reservar_analise,
    finalizar_analise,
    registrar_falha,
)

from backend.service.validacao_analise_service import (
    validar_resultado,
)


VERSAO_ANALISADOR = "gemini-v1"


def eh_erro_de_cota(erro):
    codigo = (
        getattr(erro, "code", None)
        or getattr(erro, "status_code", None)
    )

    return (
        str(codigo) == "429"
        or "RESOURCE_EXHAUSTED" in str(erro)
    )


def classificar_erro_analise(erro):
    """
    Retorna somente códigos predefinidos.

    Nunca inclui texto original do documento,
    resposta da IA ou informações pessoais.
    """

    if eh_erro_de_cota(erro):
        return "cota_api"

    if isinstance(erro, ValidationError):
        return "schema_json_invalido"

    if isinstance(erro, ValueError):
        mensagem = str(erro).lower()

        if "trecho literal não encontrado" in mensagem:
            return "evidencia_prazo_inexistente"

        if "participante com evidência inexistente" in mensagem:
            return "evidencia_participante_inexistente"

        if "dias inválidos" in mensagem:
            return "dias_invalidos"

        if "contagem inválida" in mensagem:
            return "contagem_invalida"

        if (
            "objeto json" in mensagem
            or "campo prazos ausente" in mensagem
            or "objeto inválido" in mensagem
            or "campo participantes inválido" in mensagem
        ):
            return "estrutura_json_invalida"

        return "validacao_nao_classificada"

    return "erro_" + type(erro).__name__[:60]


def processar_publicacao(
    publicacao_id,
    texto,
    nome_advogado=None,
    *,
    analisador=None,
):
    """
    Chama o Gemini somente quando conquista
    uma reserva com orçamento disponível.
    """

    if analisador is None:
        from backend.service.analise_ia_service import (
            analisar_publicacao,
        )
        analisador = analisar_publicacao

    modelo = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.5-flash-lite"
    )

    reserva = reservar_analise(
        publicacao_id,
        texto,
        VERSAO_ANALISADOR,
        modelo,
    )

    if reserva["estado"] != "reservada":
        return {
            "estado": reserva["estado"],
            "id": reserva["id"],
            "chamada_iniciada": False,
            "origem": (
                "cache"
                if reserva["estado"] == "concluida"
                else "fila"
            ),
        }

    try:
        resposta = analisador(
            texto=texto,
            nome_advogado=nome_advogado,
        )

        resultado = validar_resultado(
            texto,
            resposta,
        )

        finalizar_analise(
            reserva["id"],
            reserva["token"],
            resultado,
        )

        return {
            "estado": "concluida",
            "id": reserva["id"],
            "origem": "gemini",
            "chamada_iniciada": True,
        }

    except Exception as erro:
        cota = eh_erro_de_cota(erro)
        codigo = classificar_erro_analise(erro)

        registrar_falha(
            reserva["id"],
            reserva["token"],
            cota=cota,
            mensagem=codigo,
        )

        return {
            "estado": (
                "aguardando_cota"
                if cota else "falha"
            ),
            "id": reserva["id"],
            "erro_tipo": type(erro).__name__,
            "erro_codigo": codigo,
            "chamada_iniciada": True,
        }
