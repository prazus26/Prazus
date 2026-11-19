from backend.database import Session
from backend.model.prazo import Prazo
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.acompanhamento_publicacao import AcompanhamentoPublicacao
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from sqlalchemy import or_, and_
from datetime import timedelta
from backend.service.normalizacao_processo_djen_service import completar_detalhes

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
        existente = (
            db.query(Prazo)
            .filter(Prazo.publicacao_id == publicacao_id)
            .with_for_update()
            .first()
        )

        if existente:
            if (
                existente.origem_prazo == "estimativa_prazus"
                and origem == "djen"
            ):
                existente.dias_prazo_original = dias_prazo
                existente.tipo_contagem_original = tipo_contagem
                existente.data_inicio_original = data_inicio
                existente.data_vencimento_original = data_vencimento

                pode_atualizar = (
                    existente.personalizado_manualmente is False
                    and existente.revisao_estado != "confirmada"
                )

                if pode_atualizar:
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
            status="pendente",
            personalizado_manualmente=False
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
            Publicacao.data_disponibilizacao,
            Prazo.nome_prazo,
            Prazo.origem_prazo,
            Prazo.personalizado_manualmente,
            Prazo.revisao_estado,
            AcompanhamentoPublicacao.estado,
            Prazo.dias_prazo_atual,
            Prazo.data_vencimento_original
        ).join(
            Publicacao,
            Prazo.publicacao_id == Publicacao.id
        ).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).outerjoin(
            AcompanhamentoPublicacao,
            AcompanhamentoPublicacao.publicacao_id == Publicacao.id
        ).outerjoin(
            MetadadoComunicacaoDJEN,
            MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id
        ).filter(
            Processo.usuario_id == usuario_id,
            or_(
                MetadadoComunicacaoDJEN.id.is_(None),
                and_(
                    MetadadoComunicacaoDJEN.ativo.isnot(False),
                    MetadadoComunicacaoDJEN.data_cancelamento.is_(None),
                ),
            ),
            Prazo.status == "pendente",
            Prazo.data_vencimento_atual.isnot(None)
        ).order_by(
            Prazo.data_vencimento_atual
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

        return completar_detalhes(montar_detalhes(prazo, publicacao, processo))

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
            return completar_detalhes(montar_detalhes(prazo, publicacao, processo))

        return completar_detalhes({
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
        })

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
        "data_vencimento_original": prazo.data_vencimento_original,
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
        "conteudo_original": publicacao.conteudo_original,
        "dias_sugeridos": prazo.dias_sugeridos,
        "trecho_sugerido": prazo.trecho_sugerido,
        "revisao_estado": prazo.revisao_estado,
        "personalizado_manualmente": prazo.personalizado_manualmente
    }

def alterar_exibicao_estimativa(prazo_id, usuario_id, exibir):
    db = Session()

    try:
        prazo = db.query(Prazo).join(
            Publicacao, Prazo.publicacao_id == Publicacao.id
        ).join(
            Processo, Publicacao.processo_id == Processo.id
        ).filter(
            Prazo.id == prazo_id,
            Processo.usuario_id == usuario_id,
            Prazo.origem_prazo == "estimativa_prazus"
        ).first()

        if not prazo:
            return False

        prazo.exibir_calendario = exibir
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def atualizar_dados_prazo(prazo_id, usuario_id, dados):
    db = Session()

    try:
        resultado = db.query(
            Prazo, Publicacao, Processo
        ).join(
            Publicacao,
            Prazo.publicacao_id == Publicacao.id
        ).join(
            Processo,
            Publicacao.processo_id == Processo.id
        ).filter(
            Prazo.id == prazo_id,
            Processo.usuario_id == usuario_id
        ).with_for_update().first()

        if not resultado:
            return False

        prazo, publicacao, processo = resultado

        numero_existente = db.query(Processo.id).filter(
            Processo.usuario_id == usuario_id,
            Processo.numero_processo == dados["numero_processo"],
            Processo.id != processo.id
        ).first()

        if numero_existente:
            raise ValueError(
                "Esse número de processo já está cadastrado."
            )

        processo.cliente = dados["cliente"]
        processo.numero_processo = dados["numero_processo"]
        processo.tribunal = dados["tribunal"]
        processo.vara = dados["vara"]
        processo.link_processo = dados["link_processo"]
        if "observacoes" in dados:
            processo.observacoes_usuario = dados["observacoes"]

        publicacao.data_publicacao = dados["data_publicacao"]

        # Alterar dados cadastrais nunca valida uma estimativa arbitrária.
        # Só a edição explícita do vencimento registra personalização.
        if dados.get("alterar_vencimento", False):
            if dados["data_vencimento"] is None:
                raise ValueError("Informe uma data de vencimento válida.")
            prazo.data_vencimento_atual = dados["data_vencimento"]
            prazo.personalizado_manualmente = True

        prazo.alerta_proximidade = dados["alerta_proximidade"]

        if (
            prazo.tipo_contagem_atual == "corridos"
            and prazo.data_inicio_atual
            and dados.get("alterar_vencimento", False)
            and dados["data_vencimento"]
        ):
            prazo.dias_prazo_atual = (
                dados["data_vencimento"] - prazo.data_inicio_atual
            ).days

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

def registrar_sugestao_prazo(publicacao_id, dias, trecho):
    db = Session()

    try:
        prazo = db.query(Prazo).filter(
            Prazo.publicacao_id == publicacao_id,
            Prazo.origem_prazo == "estimativa_prazus",
            Prazo.status == "pendente"
        ).with_for_update().first()

        if not prazo:
            return False

        if prazo.revisao_estado in ("confirmada", "descartada"):
            return False

        prazo.dias_sugeridos = dias
        prazo.trecho_sugerido = trecho
        prazo.revisao_estado = "pendente"

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def confirmar_sugestao_prazo(prazo_id, usuario_id, dados):
    db = Session()

    try:
        resultado = db.query(Prazo).join(
            Publicacao, Prazo.publicacao_id == Publicacao.id
        ).join(
            Processo, Publicacao.processo_id == Processo.id
        ).filter(
            Prazo.id == prazo_id,
            Processo.usuario_id == usuario_id,
            Prazo.origem_prazo == "estimativa_prazus",
            Prazo.revisao_estado == "pendente",
            Prazo.status == "pendente"
        ).with_for_update().first()

        if not resultado:
            return False

        resultado.dias_prazo_atual = dados["dias"]
        resultado.tipo_contagem_atual = dados["tipo_contagem"]
        resultado.data_inicio_atual = dados["data_inicio"]
        resultado.data_vencimento_atual = dados["data_vencimento"]

        resultado.revisao_estado = "confirmada"
        resultado.exibir_calendario = True
        resultado.personalizado_manualmente = True

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def criar_prazo_confirmado_pela_advogada(publicacao_id, usuario_id, dados):
    """Cria um prazo manual após revisão. Nunca modifica texto original DJEN."""
    db = Session()
    try:
        publicacao = (
            db.query(Publicacao)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .filter(
                Publicacao.id == publicacao_id,
                Processo.usuario_id == usuario_id,
            )
            .with_for_update()
            .first()
        )
        if publicacao is None:
            return None

        existente = (
            db.query(Prazo.id)
            .filter(Prazo.publicacao_id == publicacao_id)
            .first()
        )
        if existente:
            raise ValueError(
                "Esta publicação já possui um prazo. Abra os detalhes para editar."
            )

        novo = Prazo(
            publicacao_id=publicacao_id,
            dias_prazo_original=None,
            tipo_contagem_original=None,
            data_inicio_original=None,
            data_vencimento_original=None,
            dias_prazo_atual=dados["dias"],
            tipo_contagem_atual=dados["tipo_contagem"],
            data_inicio_atual=dados["data_inicio"],
            data_vencimento_atual=dados["data_vencimento"],
            nome_prazo=dados["nome_prazo"],
            origem_prazo="manual",
            status="pendente",
            revisao_estado="confirmada",
            personalizado_manualmente=True,
        )
        db.add(novo)
        db.commit()
        db.refresh(novo)
        return novo.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def atualizar_dados_publicacao(publicacao_id, usuario_id, dados):
    """Edita processo/publicação sem exigir nem criar um prazo legado."""
    with Session.begin() as db:
        resultado = db.query(Publicacao, Processo).join(Processo).filter(
            Publicacao.id == publicacao_id, Processo.usuario_id == usuario_id).with_for_update().first()
        if not resultado:
            return False
        publicacao, processo = resultado
        duplicado = db.query(Processo.id).filter(Processo.usuario_id == usuario_id,
            Processo.numero_processo == dados['numero_processo'], Processo.id != processo.id).first()
        if duplicado:
            raise ValueError('Esse número de processo já está cadastrado.')
        for campo in ('cliente', 'numero_processo', 'tribunal', 'vara', 'link_processo'):
            setattr(processo, campo, dados[campo])
        if 'observacoes' in dados:
            processo.observacoes_usuario = dados['observacoes']
        publicacao.data_publicacao = dados['data_publicacao']
        return True
