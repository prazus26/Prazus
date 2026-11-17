
"""Fila de publicações com orçamento limitado de análises."""

from backend.database import Session
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.usuario import Usuario

from backend.service.processamento_ia_service import processar_publicacao


def processar_pendentes_advogado(
    usuario_id,
    limite=3,
    *,
    somente_simular=False,
    analisador=None,
):
    if not 1 <= limite <= 20:
        raise ValueError(
            "Limite por execução deve estar entre 1 e 20."
        )

    with Session() as sessao:
        itens = (
            sessao.query(
                Publicacao.id,
                Publicacao.conteudo_original,
                Usuario.nome,
            )
            .join(
                Processo,
                Publicacao.processo_id == Processo.id,
            )
            .join(
                Usuario,
                Processo.usuario_id == Usuario.id,
            )
            .filter(
                Processo.usuario_id == usuario_id,
            )
            .order_by(
                Publicacao.id.desc(),
            )
            .all()
        )

    resultados = []
    chamadas_iniciadas = 0
    cota_diaria_atingida = False

    for pub_id, texto, nome in itens:
        if not texto or not texto.strip():
            continue

        if somente_simular:
            resultados.append({
                "publicacao_id": pub_id,
                "estado": "na_fila_para_verificacao",
            })

            if len(resultados) >= limite:
                break

            continue

        if chamadas_iniciadas >= limite:
            break

        resultado = processar_publicacao(
            pub_id,
            texto,
            nome_advogado=nome,
            analisador=analisador,
        )

        resultados.append({
            "publicacao_id": pub_id,
            **resultado,
        })

        if (
            resultado.get("origem") == "gemini"
            or resultado["estado"] in (
                "falha",
                "aguardando_cota",
            )
        ):
            chamadas_iniciadas += 1

        if resultado["estado"] == "cota_diaria":
            cota_diaria_atingida = True
            break

        if resultado["estado"] == "aguardando_cota":
            break

    return {
        "publicacoes_verificadas": len(resultados),
        "chamadas_iniciadas": chamadas_iniciadas,
        "cota_diaria_atingida": cota_diaria_atingida,
        "resultados": resultados,
    }
