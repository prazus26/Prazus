
from uuid import uuid4

from database import Session
from model.publicacao import Publicacao
from model.analise_ia import AnaliseIA

from repository.analise_ia_repository import (
    obter_ou_criar_pendente,
    concluir_analise,
    calcular_hash_conteudo
)


texto = """
TESTE FICTICIO DE PERSISTENCIA DO PRAZUS.
Autor: Joao da Silva.
Advogada: Maria Souza.
Apresentar manifestacao em 15 dias uteis.
"""

versao = "teste-" + uuid4().hex[:12]
hash_texto = calcular_hash_conteudo(texto)

registro_id = None

try:
    # PRIMEIRA CONEXAO: GRAVAR
    with Session.begin() as sessao:
        publicacao_id = (
            sessao.query(Publicacao.id)
            .order_by(Publicacao.id)
            .limit(1)
            .scalar()
        )

        if publicacao_id is None:
            raise RuntimeError(
                "Nenhuma publicacao cadastrada."
            )

        registro, criado = obter_ou_criar_pendente(
            sessao=sessao,
            publicacao_id=publicacao_id,
            texto=texto,
            versao_analisador=versao,
            modelo_ia="simulado"
        )

        assert criado is True

        concluir_analise(
            sessao,
            registro,
            {
                "cliente_provavel": "Joao da Silva",
                "prazos": [
                    {
                        "atividade": "Apresentar manifestacao",
                        "dias": 15,
                        "contagem": "uteis"
                    }
                ]
            }
        )

        registro_id = registro.id

    print("COMMIT realizado.")
    print("Registro criado:", registro_id)

    # SEGUNDA CONEXAO: CONSULTAR
    with Session() as sessao:
        recuperado = (
            sessao.query(AnaliseIA)
            .filter(
                AnaliseIA.id == registro_id,
                AnaliseIA.hash_conteudo == hash_texto,
                AnaliseIA.versao_analisador == versao
            )
            .one()
        )

        assert recuperado.estado == "concluida"
        assert recuperado.resultado_json is not None
        assert recuperado.resultado_json[
            "cliente_provavel"
        ] == "Joao da Silva"

        print("Resultado recuperado do MySQL!")
        print("Estado:", recuperado.estado)
        print("Dados:", recuperado.resultado_json)

    print("TESTE DE PERSISTENCIA REAL PASSOU!")

finally:
    # REMOVE SOMENTE O REGISTRO DESTE TESTE
    if registro_id is not None:
        with Session.begin() as sessao:
            registro_teste = (
                sessao.query(AnaliseIA)
                .filter(
                    AnaliseIA.id == registro_id,
                    AnaliseIA.versao_analisador == versao,
                    AnaliseIA.modelo_ia == "simulado"
                )
                .one_or_none()
            )

            if registro_teste is not None:
                sessao.delete(registro_teste)
                print("Registro de teste removido.")
