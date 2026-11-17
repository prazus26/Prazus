
"""Armazenamento de análises IA com reserva atômica e cota diária.

As datas de processamento são UTC sem timezone para MySQL DATETIME.
O dia da cota é definido no horário de São Paulo.

A cota conta tentativas reservadas, inclusive chamadas que falham.
Não representa necessariamente o consumo reportado pelo provedor.
"""

import os
import hashlib

from datetime import datetime, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, update, text
from sqlalchemy.dialects.mysql import insert as mysql_insert

from backend.database import Session
from backend.model.analise_ia import AnaliseIA


FUSO_COTA = ZoneInfo("America/Sao_Paulo")


class CotaDiariaExcedida(Exception):
    pass


def agora_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def dia_cota():
    return datetime.now(FUSO_COTA).date()


def obter_limite_diario():
    valor = int(os.getenv("PRAZUS_IA_LIMITE_DIARIO", "5"))

    if not 1 <= valor <= 100:
        raise ValueError(
            "PRAZUS_IA_LIMITE_DIARIO deve estar entre 1 e 100."
        )

    return valor


def calcular_hash_conteudo(texto):
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("Texto de publicação vazio.")

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()


def contar_analises():
    with Session() as sessao:
        return sessao.query(AnaliseIA).count()


def buscar_analise(publicacao_id, hash_conteudo, versao_analisador):
    """Retorna um snapshot, não um ORM com sessão encerrada."""

    with Session() as sessao:
        item = sessao.query(AnaliseIA).filter_by(
            publicacao_id=publicacao_id,
            hash_conteudo=hash_conteudo,
            versao_analisador=versao_analisador,
        ).one_or_none()

        if item is None:
            return None

        return {
            "id": item.id,
            "estado": item.estado,
            "resultado_json": item.resultado_json,
            "tentativas": item.tentativas,
        }


def consultar_cota_diaria():
    """Retorna apenas números de consumo; não acessa documentos."""

    hoje = dia_cota()
    limite = obter_limite_diario()

    with Session() as sessao:
        usado = sessao.execute(
            text(
                """
                SELECT tentativas_iniciadas
                FROM cota_ia_diaria
                WHERE dia = :dia
                """
            ),
            {"dia": hoje},
        ).scalar()

    usado = int(usado or 0)

    return {
        "dia": hoje.isoformat(),
        "limite": limite,
        "utilizadas": usado,
        "restantes": max(0, limite - usado),
    }


def consumir_cota_na_transacao(sessao, limite):
    """
    Bloqueia a linha do dia até o fim da transação.

    Precisa ser chamado DEPOIS de conquistar a reserva
    da publicação, mas ANTES de concluir essa transação.

    Se não houver cota, a exceção provoca rollback tanto
    da reserva quanto de qualquer alteração de contador.
    """

    hoje = dia_cota()

    sessao.execute(
        text(
            """
            INSERT IGNORE INTO cota_ia_diaria
                (dia, tentativas_iniciadas)
            VALUES
                (:dia, 0)
            """
        ),
        {"dia": hoje},
    )

    utilizadas = sessao.execute(
        text(
            """
            SELECT tentativas_iniciadas
            FROM cota_ia_diaria
            WHERE dia = :dia
            FOR UPDATE
            """
        ),
        {"dia": hoje},
    ).scalar_one()

    if int(utilizadas) >= limite:
        raise CotaDiariaExcedida()

    sessao.execute(
        text(
            """
            UPDATE cota_ia_diaria
            SET tentativas_iniciadas =
                tentativas_iniciadas + 1
            WHERE dia = :dia
            """
        ),
        {"dia": hoje},
    )


def reservar_analise(
    publicacao_id,
    texto,
    versao_analisador,
    modelo_ia,
    *,
    limite_tentativas=5,
    duracao_reserva_minutos=10,
):
    """
    Mantém a reserva atômica original.

    Agora também consome uma unidade da cota diária
    na mesma transação que conquista a reserva.

    Retorna:
      reservada
      concluida
      ocupada
      limite
      cota_diaria
    """

    hash_texto = calcular_hash_conteudo(texto)
    token = uuid4().hex

    agora = agora_utc()
    expira = agora + timedelta(
        minutes=duracao_reserva_minutos
    )

    limite_diario = obter_limite_diario()

    try:
        with Session.begin() as sessao:
            if sessao.bind.dialect.name != "mysql":
                raise RuntimeError(
                    "A reserva em produção exige MySQL."
                )

            ins = mysql_insert(AnaliseIA.__table__).values(
                publicacao_id=publicacao_id,
                hash_conteudo=hash_texto,
                versao_analisador=versao_analisador,
                modelo_ia=modelo_ia,
                estado="pendente",
                tentativas=0,
            ).prefix_with("IGNORE")

            sessao.execute(ins)

            base = and_(
                AnaliseIA.publicacao_id == publicacao_id,
                AnaliseIA.hash_conteudo == hash_texto,
                AnaliseIA.versao_analisador == versao_analisador,
            )

            apta = or_(
                AnaliseIA.estado == "pendente",
                and_(
                    AnaliseIA.estado.in_(
                        ["falha", "aguardando_cota"]
                    ),
                    or_(
                        AnaliseIA.proxima_tentativa_em.is_(None),
                        AnaliseIA.proxima_tentativa_em <= agora,
                    ),
                ),
                and_(
                    AnaliseIA.estado == "processando",
                    AnaliseIA.reserva_expira_em <= agora,
                ),
            )

            stmt = (
                update(AnaliseIA)
                .where(
                    base,
                    apta,
                    AnaliseIA.tentativas < limite_tentativas,
                )
                .values(
                    estado="processando",
                    reserva_token=token,
                    reserva_expira_em=expira,
                    proxima_tentativa_em=None,
                    tentativas=AnaliseIA.tentativas + 1,
                    erro_resumido=None,
                )
            )

            alteradas = sessao.execute(stmt).rowcount

            item = sessao.query(AnaliseIA).filter(
                base
            ).one()

            if alteradas == 1:
                # Só consome orçamento se a reserva foi conquistada.
                # A linha diária é bloqueada até o commit.
                consumir_cota_na_transacao(
                    sessao,
                    limite_diario,
                )

                return {
                    "estado": "reservada",
                    "id": item.id,
                    "token": token,
                }

            if item.estado == "concluida":
                return {
                    "estado": "concluida",
                    "id": item.id,
                    "resultado": item.resultado_json,
                }

            if (
                item.tentativas >= limite_tentativas
                and item.estado != "processando"
            ):
                return {
                    "estado": "limite",
                    "id": item.id,
                }

            return {
                "estado": "ocupada",
                "id": item.id,
            }

    except CotaDiariaExcedida:
        return {
            "estado": "cota_diaria",
            "id": None,
        }


def finalizar_analise(id_analise, token, resultado):
    """O token impede um processamento antigo de sobrescrever outro."""

    if not isinstance(resultado, dict):
        raise ValueError("Resultado não é um dicionário.")

    agora = agora_utc()

    with Session.begin() as sessao:
        stmt = (
            update(AnaliseIA)
            .where(
                AnaliseIA.id == id_analise,
                AnaliseIA.estado == "processando",
                AnaliseIA.reserva_token == token,
                AnaliseIA.reserva_expira_em > agora,
            )
            .values(
                estado="concluida",
                resultado_json=resultado,
                analisado_em=agora,
                reserva_token=None,
                reserva_expira_em=None,
                erro_resumido=None,
            )
        )

        if sessao.execute(stmt).rowcount != 1:
            raise RuntimeError(
                "Reserva expirou ou pertence a outro processamento; "
                "resultado descartado."
            )


def registrar_falha(
    id_analise,
    token,
    *,
    cota=False,
    mensagem="Falha na análise",
):
    agora = agora_utc()

    proxima = agora + timedelta(
        hours=24 if cota else 1
    )

    with Session.begin() as sessao:
        stmt = (
            update(AnaliseIA)
            .where(
                AnaliseIA.id == id_analise,
                AnaliseIA.estado == "processando",
                AnaliseIA.reserva_token == token,
            )
            .values(
                estado=(
                    "aguardando_cota" if cota else "falha"
                ),
                proxima_tentativa_em=proxima,
                reserva_token=None,
                reserva_expira_em=None,
                erro_resumido=str(mensagem)[:500],
            )
        )

        return sessao.execute(stmt).rowcount == 1
