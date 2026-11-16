
from database import Session
from model.publicacao import Publicacao

from repository.analise_ia_repository import (
    obter_ou_criar_pendente,
    concluir_analise
)


sessao = Session()

try:
    publicacao_id = (
        sessao.query(Publicacao.id)
        .order_by(Publicacao.id)
        .limit(1)
        .scalar()
    )

    if publicacao_id is None:
        raise RuntimeError(
            "Não existe publicação para testar."
        )

    texto_teste = """
    DOCUMENTO FICTÍCIO PARA TESTE DE PERSISTÊNCIA.
    Autor: João da Silva.
    Advogada: Maria Souza.
    Apresentar manifestação em 15 dias úteis.
    """

    registro, criado = obter_ou_criar_pendente(
        sessao=sessao,
        publicacao_id=publicacao_id,
        texto=texto_teste,
        versao_analisador="teste-local-v1",
        modelo_ia="simulado"
    )

    print("Primeiro cadastro:", criado)
    print("Estado inicial:", registro.estado)

    segundo, criado_novamente = obter_ou_criar_pendente(
        sessao=sessao,
        publicacao_id=publicacao_id,
        texto=texto_teste,
        versao_analisador="teste-local-v1",
        modelo_ia="simulado"
    )

    print("Segundo cadastro:", criado_novamente)

    assert registro.id == segundo.id
    assert criado_novamente is False

    resultado_ficticio = {
        "cliente_provavel": "João da Silva",
        "prazos": [
            {
                "atividade": "Apresentar manifestação",
                "dias": 15,
                "contagem": "uteis"
            }
        ]
    }

    concluir_analise(
        sessao,
        registro,
        resultado_ficticio
    )

    print("Estado final:", registro.estado)
    print("Resultado salvo:", registro.resultado_json)

    assert registro.estado == "concluida"
    assert registro.resultado_json == resultado_ficticio

    print("TESTE DE PERSISTÊNCIA PASSOU!")

finally:
    sessao.rollback()
    sessao.close()
    print("Transação revertida. Teste encerrado.")
