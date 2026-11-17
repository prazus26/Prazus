
from backend.database import Session
from backend.model.publicacao import Publicacao

from backend.service.processamento_ia_service import (
    processar_publicacao_em_sessao
)


chamadas_ia = 0


def gemini_simulado(texto, nome_advogado):
    global chamadas_ia
    chamadas_ia += 1

    return {
        "numero_processo": "1001234-56.2026.8.26.0001",
        "cliente_provavel": "João da Silva",
        "participantes": [],
        "prazos": [
            {
                "atividade": "Apresentar manifestação",
                "destinatario": "parte autora",
                "dias": 15,
                "contagem": "uteis",
                "evidencia": "Apresentar manifestação em 15 dias úteis."
            }
        ]
    }


sessao = Session()

try:
    publicacao_id = (
        sessao.query(Publicacao.id)
        .order_by(Publicacao.id)
        .limit(1)
        .scalar()
    )

    if publicacao_id is None:
        raise RuntimeError("Nenhuma publicação encontrada.")

    documento = """
    DOCUMENTO FICTÍCIO PARA TESTE.
    Autor: João da Silva.
    Advogada: Maria Souza.
    Apresentar manifestação em 15 dias úteis.
    """

    parametros = {
        "sessao": sessao,
        "publicacao_id": publicacao_id,
        "texto": documento,
        "nome_advogado": "Maria Souza",
        "analisador": gemini_simulado,
        "versao_analisador": "teste-processamento-v1",
        "modelo_ia": "simulado"
    }

    primeira = processar_publicacao_em_sessao(
        **parametros
    )

    print("Primeira execução:", primeira["origem"])
    print("Chamadas à IA:", chamadas_ia)

    segunda = processar_publicacao_em_sessao(
        **parametros
    )

    print("Segunda execução:", segunda["origem"])
    print("Chamadas à IA:", chamadas_ia)

    assert primeira["origem"] == "simulacao"
    assert segunda["origem"] == "banco"
    assert primeira["resultado"] == segunda["resultado"]
    assert chamadas_ia == 1

    print("TESTE PASSOU: análise reutilizada sem nova chamada.")

finally:
    sessao.rollback()
    sessao.close()
    print("ROLLBACK executado.")
