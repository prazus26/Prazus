import logging
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from service.rotina_diaria_service import executar_rotina_diaria

import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/rotina_diaria.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

agendador = BackgroundScheduler(
    timezone=ZoneInfo("America/Sao_Paulo")
)

def executar_rotina_agendada():
    try:
        logging.info("Iniciando rotina automática da Prazus")

        resultado = executar_rotina_diaria()

        logging.info(
            "Rotina finalizada. Advogados processados: %s",
            resultado["advogados_processados"]
        )

        for advogado in resultado["resultados"]:
            logging.info(
                "Usuário %s | DJEN: %s | Prazos: %s | Notificações: %s | Erros: %s",
                advogado["usuario_id"],
                advogado["djen"],
                advogado["prazos"],
                advogado["notificacoes"],
                advogado["erros"]
            )

    except Exception:
        logging.exception("Erro na rotina automática da Prazus")


def iniciar_agendador():
    if agendador.running:
        return

    agendador.add_job(
        executar_rotina_agendada,
        trigger="cron",
        hour=3,
        minute=0,
        id="rotina_diaria_prazus",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600
    )

    agendador.start()

    logging.info("Agendador da Prazus iniciado. Próxima execução diária às 03:00.")
