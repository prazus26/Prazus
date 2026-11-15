
from database import Session
from model.publicacao import Publicacao
from model.processo import Processo
from model.prazo import Prazo
from service.identificacao_prazo_service import identificar_prazo

db = Session()

try:
    publicacoes = (
        db.query(Publicacao)
        .join(Processo, Publicacao.processo_id == Processo.id)
        .join(Prazo, Prazo.publicacao_id == Publicacao.id)
        .filter(
            Processo.usuario_id == 6,
            Prazo.origem_prazo == "estimativa_prazus"
        )
        .all()
    )

    total = 0

    for publicacao in publicacoes:
        resultado = identificar_prazo(
            publicacao.conteudo_original
        )

        if resultado.get("revisao_necessaria"):
            total += 1

            print(f"\nPublicação ID: {publicacao.id}")
            print(
                "Dias sugeridos:",
                resultado["dias_sugeridos"]
            )
            print(
                "Trecho:",
                resultado["trecho_identificado"]
            )

    print(f"\nTotal para revisão: {total}")

finally:
    db.close()
