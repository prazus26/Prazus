"""Sincroniza o DJEN, processa análises pendentes e atualiza notificações.

As prévias do FullCalendar são calculadas ao consultar a API do calendário;
esta rotina NÃO grava prazos fictícios nem promove candidatos a confirmados.
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from repository.usuario_repository import buscar_advogados_para_sincronizacao
from service.sincronizacao_djen_service import sincronizar_advogado
from service.acompanhamento_service import registrar_acompanhamentos_advogado
from service.notificacao_service import gerar_notificacoes
from service.fila_ia_service import processar_pendentes_advogado


def _inteiro_configurado(nome, padrao, minimo, maximo):
    try:
        valor = int(os.getenv(nome, str(padrao)))
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, valor))


def executar_rotina_diaria():
    """Execução repetível: DJEN deduplica e IA utiliza cache por hash."""
    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    # Janela móvel de recuperação: 30 dias por padrão, configurável até 365.
    # Não é checkpoint permanente: interrupções maiores exigem ampliar a janela.
    janela = _inteiro_configurado("PRAZUS_DJEN_JANELA_DIAS", 30, 3, 365)
    data_inicio = hoje - timedelta(days=janela)
    ia_habilitada = os.getenv("PRAZUS_IA_ENABLED", "0") == "1"
    limite_ia = _inteiro_configurado("PRAZUS_IA_MAX_POR_EXECUCAO", 3, 1, 20)

    resultados = []
    for advogado in buscar_advogados_para_sincronizacao():
        resultado = {
            "usuario_id": advogado.id,
            "djen": None,
            "intervalo_djen": {"inicio": data_inicio.isoformat(), "fim": hoje.isoformat()},
            "prazos": {"automaticos_criados": 0,
                       "motivo": "Eventos calculados dinamicamente pelo calendário; nenhum prazo confirmado é criado"},
            "estimativas_criadas": 0,
            "acompanhamentos": None,
            "notificacoes": None,
            "analises_ia": {"estado": "desativada" if not ia_habilitada else "pendente"},
            "erros": [],
        }
        try:
            resultado["djen"] = sincronizar_advogado(
                usuario_id=advogado.id,
                oab=advogado.oab_numero,
                uf=advogado.oab_uf,
                data_inicio=data_inicio.isoformat(),
                data_fim=hoje.isoformat(),
            )
            # Erros pontuais podem existir mesmo sem exceção do serviço.
            if resultado["djen"] and resultado["djen"].get("erros"):
                resultado["erros"].append("DJEN: algumas publicações falharam na importação")
        except Exception as erro:
            resultado["erros"].append(f"DJEN: {type(erro).__name__}")

        try:
            resultado["acompanhamentos"] = registrar_acompanhamentos_advogado(advogado.id)
        except Exception as erro:
            resultado["erros"].append(f"Acompanhamentos: {type(erro).__name__}")

        # O Gemini permanece OPT-IN: chamadas em documentos reais podem consumir
        # cota ou gerar cobrança dependendo da conta/configuração do usuário.
        if ia_habilitada:
            try:
                resultado["analises_ia"] = processar_pendentes_advogado(
                    advogado.id, limite=limite_ia
                )
            except Exception as erro:
                resultado["analises_ia"] = {"estado": "erro"}
                resultado["erros"].append(f"IA: {type(erro).__name__}")

        try:
            resultado["notificacoes"] = gerar_notificacoes(advogado.id)
        except Exception as erro:
            resultado["erros"].append(f"Notificações: {type(erro).__name__}")

        resultados.append(resultado)

    return {"advogados_processados": len(resultados), "resultados": resultados}
