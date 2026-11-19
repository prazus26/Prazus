"""Teste real em MySQL com publicação existente, sem API, com limpeza no finally.
Execute apenas após migrar 004 e fazer backup. Não altera a publicação.
"""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from backend.database import Session
from backend.model.publicacao import Publicacao
from backend.model.analise_ia import AnaliseIA
from backend.repository.analise_ia_repository import (
    reservar_analise, finalizar_analise, calcular_hash_conteudo,
)

texto = "TESTE FICTÍCIO DE CONCORRÊNCIA IA, NÃO PROCESSAR COMO PRAZO JUDICIAL."
versao = "teste-" + uuid4().hex[:12]
identificador = None
try:
    with Session() as sessao:
        publicacao_id = sessao.query(Publicacao.id).order_by(Publicacao.id).limit(1).scalar()
    if publicacao_id is None:
        raise RuntimeError("Não há publicação cadastrada para satisfazer a FK.")

    def disputar(_):
        return reservar_analise(publicacao_id, texto, versao, "simulado")

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(disputar, (1, 2)))

    print("Estados das reservas:", [x["estado"] for x in resultados])
    vencedores = [x for x in resultados if x["estado"] == "reservada"]
    assert len(vencedores) == 1, "Erro: deve haver exatamente um vencedor."
    identificador = vencedores[0]["id"]
    finalizar_analise(identificador, vencedores[0]["token"], {"prazos": [], "participantes": []})
    proxima = reservar_analise(publicacao_id, texto, versao, "simulado")
    assert proxima["estado"] == "concluida"
    print("TESTE MYSQL PASSOU: um vencedor e cache persistente.")
finally:
    # Exclusão estritamente limitada à versão fictícia criada neste teste.
    with Session.begin() as sessao:
        sessao.query(AnaliseIA).filter(
            AnaliseIA.versao_analisador == versao,
            AnaliseIA.hash_conteudo == calcular_hash_conteudo(texto),
            AnaliseIA.modelo_ia == "simulado",
        ).delete(synchronize_session=False)
    print("Limpeza da análise fictícia executada.")
