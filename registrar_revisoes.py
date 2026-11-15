
from database import Session
from model.publicacao import Publicacao
from model.processo import Processo
from model.prazo import Prazo

from service.identificacao_prazo_service import identificar_prazo
from repository.prazo_repository import registrar_sugestao_prazo


def executar():
    db = Session()

    try:
        publicacoes = (
            db.query(Publicacao)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .join(Prazo, Prazo.publicacao_id == Publicacao.id)
            .filter(
                Processo.usuario_id == 6,
                Prazo.origem_prazo == "estimativa_prazus",
                Prazo.status == "pendente",
                Prazo.revisao_estado.is_(None)
            )
            .all()
        )

        registradas = 0

        for publicacao in publicacoes:
            resultado = identificar_prazo(
                publicacao.conteudo_original
            )

            if not resultado.get("revisao_necessaria"):
                continue

            if registrar_sugestao_prazo(
                publicacao.id,
                resultado["dias_sugeridos"],
                resultado["trecho_identificado"]
            ):
                registradas += 1

        print("Publicações analisadas:", len(publicacoes))
        print("Sugestões registradas:", registradas)

    finally:
        db.close()


if __name__ == "__main__":
    executar()
