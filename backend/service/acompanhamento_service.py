from backend.database import Session
from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.service.identificacao_prazo_service import identificar_prazo


def registrar_acompanhamentos_advogado(usuario_id, aplicar=True):
    """Registra triagens, sem criar prazo judicial nem vencimento fictício.

    Idempotente pelo índice UNIQUE(publicacao_id). Não modifica prazos legados.
    Cada inserção e a transação são confirmadas juntas.
    """
    db = Session()
    try:
        publicacoes = (
            db.query(Publicacao)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .outerjoin(
                AcompanhamentoPublicacao,
                AcompanhamentoPublicacao.publicacao_id == Publicacao.id
            )
            .filter(
                Processo.usuario_id == usuario_id,
                AcompanhamentoPublicacao.id.is_(None),
            )
            .order_by(Publicacao.id)
            .all()
        )

        criados = 0
        candidatos = 0
        for pub in publicacoes:
            achado = identificar_prazo(pub.conteudo_original)
            tem_candidato = bool(achado.get("revisao_necessaria"))
            if aplicar:
                db.add(AcompanhamentoPublicacao(
                    publicacao_id=pub.id,
                    estado="pendente",
                    dias_sugeridos=achado.get("dias_sugeridos") if tem_candidato else None,
                    tipo_contagem_sugerida=(
                        achado.get("tipo_contagem_sugerida") if tem_candidato else None
                    ),
                    trecho_sugerido=achado.get("trecho_identificado") if tem_candidato else None,
                ))
            criados += 1
            candidatos += int(tem_candidato)

        if aplicar:
            db.commit()
        else:
            db.rollback()
        return {
            "acompanhamentos_criados" if aplicar else "acompanhamentos_previstos": criados,
            "candidatos_detectados": candidatos,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
