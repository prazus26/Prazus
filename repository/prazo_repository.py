from database import Session
from model.prazo import Prazo
from model.publicacao import Publicacao
from model.processo import Processo
from datetime import timedelta

def buscar_por_publicacao(publicacao_id):
    db = Session()
    try:
        return db.query(Prazo).filter(
            Prazo.publicacao_id == publicacao_id
        ).first()
    finally:
        db.close()


def cadastrar_prazo(publicacao_id, dias_prazo, tipo_contagem,
                    data_inicio, data_vencimento, origem):

    db = Session()

    try:
        existente = db.query(Prazo).filter(
            Prazo.publicacao_id == publicacao_id
        ).with_for_update().first()

        if existente:
            if (
                existente.origem_prazo == "estimativa_prazus"
                and origem == "djen"
            ):
                existente.dias_prazo_original = dias_prazo
                existente.tipo_contagem_original = tipo_contagem
                existente.data_inicio_original = data_inicio
                existente.data_vencimento_original = data_vencimento

                # Preserva alterações personalizadas da advogada.
                # Só atualiza os campos atuais se ainda estiverem
                # com os valores da estimativa inicial.
                estimativa_inicial = (
                    existente.dias_prazo_atual == 5
                    and existente.tipo_contagem_atual == "corridos"
                    and existente.data_inicio_atual is not None
                    and existente.data_vencimento_atual
                    == existente.data_inicio_atual + timedelta(days=5)
                )

                if estimativa_inicial:
                    existente.dias_prazo_atual = dias_prazo
                    existente.tipo_contagem_atual = tipo_contagem
                    existente.data_inicio_atual = data_inicio
                    existente.data_vencimento_atual = data_vencimento
                    existente.nome_prazo = "Prazo identificado"

                existente.origem_prazo = "djen"
                db.commit()

            return existente

        novo_prazo = Prazo(
            publicacao_id=publicacao_id,
            dias_prazo_original=dias_prazo,
            dias_prazo_atual=dias_prazo,
            tipo_contagem_original=tipo_contagem,
            tipo_contagem_atual=tipo_contagem,
            data_inicio_original=data_inicio,
            data_inicio_atual=data_inicio,
            data_vencimento_original=data_vencimento,
            data_vencimento_atual=data_vencimento,
            origem_prazo=origem,
            status="pendente"
        )

        db.add(novo_prazo)
        db.commit()
        db.refresh(novo_prazo)
        return novo_prazo

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def buscar_prazos_do_usuario(usuario_id):
    db = Session()
    try:
        return db.query(
            Publicacao.id,
            Prazo.id,
            Prazo.data_vencimento_atual,
            Prazo.status,
            Processo.numero_processo,
            Processo.cliente,
            Publicacao.data_publicacao,
            Publicacao.data_disponibilizacao
        ).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).outerjoin(
            Prazo,
            Prazo.publicacao_id == Publicacao.id
        ).filter(
            Processo.usuario_id == usuario_id
        ).all()
    finally:
        db.close()


def buscar_detalhes_prazo(prazo_id, usuario_id):
    db = Session()
    try:
        resultado = db.query(
            Prazo, Publicacao, Processo
        ).join(
            Publicacao, Prazo.publicacao_id == Publicacao.id
        ).join(
            Processo, Publicacao.processo_id == Processo.id
        ).filter(
            Prazo.id == prazo_id,
            Processo.usuario_id == usuario_id
        ).first()

        if not resultado:
            return None

        prazo, publicacao, processo = resultado

        return montar_detalhes(prazo, publicacao, processo)

    finally:
        db.close()


def buscar_detalhes_publicacao(publicacao_id, usuario_id):
    db = Session()
    try:
        resultado = db.query(
            Publicacao, Processo, Prazo
        ).join(
            Processo, Publicacao.processo_id == Processo.id
        ).outerjoin(
            Prazo, Prazo.publicacao_id == Publicacao.id
        ).filter(
            Publicacao.id == publicacao_id,
            Processo.usuario_id == usuario_id
        ).first()

        if not resultado:
            return None

        publicacao, processo, prazo = resultado

        if prazo:
            return montar_detalhes(prazo, publicacao, processo)

        return {
            "prazo_id": None,
            "publicacao_id": publicacao.id,
            "nome_prazo": None,
            "dias_prazo_original": None,
            "dias_prazo_atual": None,
            "tipo_contagem": None,
            "data_inicio": None,
            "data_vencimento": None,
            "origem_prazo": None,
            "status": "sem prazo",
            "alerta_proximidade": None,
            "numero_processo": processo.numero_processo,
            "cliente": processo.cliente,
            "tribunal": processo.tribunal,
            "vara": processo.vara,
            "link_processo": processo.link_processo,
            "assunto": processo.assunto_personalizado or processo.assunto_original,
            "classe": processo.classe_personalizada or processo.classe_original,
            "observacoes": processo.observacoes_usuario,
            "identificador_djen": publicacao.identificador_djen,
            "data_disponibilizacao": publicacao.data_disponibilizacao,
            "data_publicacao": publicacao.data_publicacao,
            "conteudo_original": publicacao.conteudo_original
        }

    finally:
        db.close()


def montar_detalhes(prazo, publicacao, processo):
    return {
        "prazo_id": prazo.id,
        "publicacao_id": publicacao.id,
        "nome_prazo": prazo.nome_prazo,
        "dias_prazo_original": prazo.dias_prazo_original,
        "dias_prazo_atual": prazo.dias_prazo_atual,
        "tipo_contagem": prazo.tipo_contagem_atual,
        "data_inicio": prazo.data_inicio_atual,
        "data_vencimento": prazo.data_vencimento_atual,
        "origem_prazo": prazo.origem_prazo,
        "status": prazo.status,
        "alerta_proximidade": prazo.alerta_proximidade,
        "numero_processo": processo.numero_processo,
        "cliente": processo.cliente,
        "tribunal": processo.tribunal,
        "vara": processo.vara,
        "link_processo": processo.link_processo,
        "assunto": processo.assunto_personalizado or processo.assunto_original,
        "classe": processo.classe_personalizada or processo.classe_original,
        "observacoes": processo.observacoes_usuario,
        "identificador_djen": publicacao.identificador_djen,
        "data_disponibilizacao": publicacao.data_disponibilizacao,
        "data_publicacao": publicacao.data_publicacao,
        "conteudo_original": publicacao.conteudo_original
    }
