
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from repository.usuario_repository import (
    buscar_advogados_para_sincronizacao
)

from service.sincronizacao_djen_service import sincronizar_advogado
from service.geracao_prazo_service import gerar_prazos_advogado
from service.prazo_estimativa_service import criar_estimativas_pendentes
from service.notificacao_service import gerar_notificacoes


def executar_rotina_diaria():
    advogados = buscar_advogados_para_sincronizacao()

    resultados = []

    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date()

    data_fim = hoje
    data_inicio = hoje - timedelta(days=3)

    for advogado in advogados:
        resultado = {
            "usuario_id": advogado.id,
            "djen": None,
            "prazos": None,
            "estimativas_criadas": 0,
            "notificacoes": None,
            "erros": []
        }

        try:
            resultado["djen"] = sincronizar_advogado(
                usuario_id=advogado.id,
                oab=advogado.oab_numero,
                uf=advogado.oab_uf,
                data_inicio=data_inicio.strftime("%Y-%m-%d"),
                data_fim=data_fim.strftime("%Y-%m-%d")
            )

        except Exception as erro:
            resultado["erros"].append(
                f"DJEN: {erro}"
            )

        try:
            resultado["prazos"] = gerar_prazos_advogado(
                advogado.id,
                advogado.oab_uf
            )

        except Exception as erro:
            resultado["erros"].append(
                f"Prazos: {erro}"
            )

        try:
            resultado["estimativas_criadas"] = (
                criar_estimativas_pendentes(
                    advogado.id,
                    advogado.oab_uf
                )
            )

        except Exception as erro:
            resultado["erros"].append(
                f"Estimativas: {erro}"
            )

        try:
            resultado["notificacoes"] = gerar_notificacoes(
                advogado.id
            )

        except Exception as erro:
            resultado["erros"].append(
                f"Notificações: {erro}"
            )

        resultados.append(resultado)

    return {
        "advogados_processados": len(advogados),
        "resultados": resultados
    }
