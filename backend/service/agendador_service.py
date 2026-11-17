"""Agenda automática diária, com execução ao iniciar para recuperar atrasos.

Execute uma única instância de processo de agendamento em produção.
Não inicie múltiplos workers Flask com este scheduler embutido.
"""
import os
import logging
from threading import Lock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from backend.service.rotina_diaria_service import executar_rotina_diaria

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada no ambiente")

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("prazus.rotina")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    arquivo_log = logging.FileHandler("logs/rotina_diaria.log", encoding="utf-8")
    arquivo_log.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(arquivo_log)

FUSO = ZoneInfo("America/Sao_Paulo")
_TRAVA_EXECUCAO = Lock()
agendador = BackgroundScheduler(
    timezone=FUSO,
    jobstores={"default": SQLAlchemyJobStore(url=DATABASE_URL)},
    job_defaults={"max_instances": 1, "coalesce": True},
)


def executar_rotina_agendada():
    # Impede sobreposição entre execução ao iniciar e o cron das 03:00.
    if not _TRAVA_EXECUCAO.acquire(blocking=False):
        logger.info("Rotina já em execução neste processo; esta chamada foi ignorada")
        return
    try:
        logger.info("Iniciando sincronização automática Prazus")
        relatorio = executar_rotina_diaria()
        logger.info("Rotina concluída. Advogados: %s", relatorio["advogados_processados"])
        for item in relatorio["resultados"]:
            djen = item.get("djen") or {}
            ia = item.get("analises_ia") or {}
            acompanhamentos = item.get("acompanhamentos") or {}
            notificacoes = item.get("notificacoes") or {}

            logger.info(
                "Usuário id=%s | "
                "DJEN encontradas=%s, importadas=%s, ignoradas=%s | "
                "IA estado=%s, verificadas=%s | "
                "Acompanhamentos=%s | "
                "Notificações verificadas=%s, criadas=%s | "
                "Erros=%s",
                item["usuario_id"],
                djen.get("total_encontrado", 0),
                djen.get("importadas", 0),
                djen.get("ignoradas", 0),
                ia.get("estado", "habilitada"),
                ia.get("publicacoes_verificadas", 0),
                acompanhamentos.get("acompanhamentos_criados", 0),
                notificacoes.get("prazos_verificados", 0),
                notificacoes.get("notificacoes_criadas", 0),
                item.get("erros", []),
            )
    except Exception:
        logger.exception("Falha na rotina automática")
    finally:
        _TRAVA_EXECUCAO.release()


def iniciar_agendador():
    if agendador.running:
        return
    # Registrar cron antes de iniciar para impedir lacuna entre start/add_job.
    agendador.add_job(
        executar_rotina_agendada,
        trigger="cron", hour=3, minute=0,
        id="rotina_diaria_prazus", replace_existing=True,
        max_instances=1, coalesce=True, misfire_grace_time=None,
    )
    # A execução pontual permite que a agenda recupere publicações ao iniciar.
    # É idempotente quanto às publicações e análises já concluídas.
    if os.getenv("PRAZUS_SINCRONIZAR_AO_INICIAR", "1") == "1":
        agendador.add_job(
            executar_rotina_agendada,
            trigger="date",
            run_date=datetime.now(FUSO) + timedelta(seconds=10),
            id="rotina_inicial_prazus", replace_existing=True,
            max_instances=1, misfire_grace_time=3600,
        )
    agendador.start()
    proxima = agendador.get_job("rotina_diaria_prazus")
    logger.info("Agendador iniciado; próxima rotina às %s", proxima.next_run_time)
