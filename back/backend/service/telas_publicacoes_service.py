from datetime import datetime, date, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from flask import abort

from backend.repository.prazo_repository import (
    buscar_detalhes_prazo,
    buscar_detalhes_publicacao,
    atualizar_dados_prazo,
    atualizar_dados_publicacao,
    criar_prazo_confirmado_pela_advogada,
    confirmar_sugestao_prazo
)
from backend.repository.acompanhamento_repository import (
    buscar_acompanhamento_da_publicacao
)
from backend.service.estado_prazo_service import aplicar_estado_legado
from backend.service.agenda_eventos_service import listar_eventos
from backend.service.calendario_service import (
    configuracao_cores,
    definir_cor
)
from backend.service.publicacoes_consulta_service import (
    consultar_publicacoes,
    adicionar_analises_ia,
    MESES
)


def eventos_da_publicacao(usuario_id, publicacao_id):
    return listar_eventos(usuario_id, publicacao_id)


def obter_listagem(usuario_id, dia):
    publicacoes = consultar_publicacoes(usuario_id, dia=dia)
    adicionar_analises_ia(publicacoes, usuario_id)

    hoje = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    cores = configuracao_cores(usuario_id)
    eventos_por_publicacao = {}

    for evento in listar_eventos(usuario_id):
        publicacao_id = evento["extendedProps"]["publicacao_id"]
        eventos_por_publicacao.setdefault(publicacao_id, []).append(evento)

    for publicacao in publicacoes:
        eventos = eventos_por_publicacao.get(publicacao["id"], [])

        if eventos:
            pendentes = [
                evento for evento in eventos
                if evento["extendedProps"]["status"] == "pendente"
            ]

            if not pendentes and all(
                evento["extendedProps"]["status"] == "concluido"
                for evento in eventos
            ):
                publicacao["status"] = "concluido"

            elif pendentes:
                primeiro = min(pendentes, key=lambda evento: evento["start"])
                publicacao["data_vencimento"] = date.fromisoformat(
                    primeiro["start"][:10]
                )
                publicacao["nome_prazo"] = ", ".join(
                    evento["extendedProps"]["nome_prazo"]
                    for evento in pendentes
                )
                publicacao["dias_prazo"] = (
                    publicacao["data_vencimento"] - hoje
                ).days

        publicacao["cor"] = (
            "#E7E5E5"
            if publicacao["status"] == "concluido"
            else definir_cor(publicacao["data_vencimento"], cores, hoje)
        )

    return {
        "publicacoes": publicacoes,
        "data_atual": dia,
        "data_anterior": (dia - timedelta(days=1)).isoformat(),
        "data_proxima": (dia + timedelta(days=1)).isoformat(),
        "data_formatada": f"{dia.day} de {MESES[dia.month]} {dia.year}"
    }


def obter_detalhes_prazo(usuario_id, prazo_id):
    prazo = buscar_detalhes_prazo(prazo_id, usuario_id)

    if not prazo:
        abort(404)

    aplicar_estado_legado(prazo)

    acompanhamento = buscar_acompanhamento_da_publicacao(
        prazo["publicacao_id"], usuario_id
    )

    if acompanhamento:
        prazo["acompanhamento_estado"] = acompanhamento["estado"]

    return {
        "prazo": prazo,
        "eventos_automaticos": eventos_da_publicacao(
            usuario_id, prazo["publicacao_id"]
        )
    }


def obter_detalhes_publicacao(usuario_id, publicacao_id):
    prazo = buscar_detalhes_publicacao(publicacao_id, usuario_id)

    if not prazo:
        abort(404)

    aplicar_estado_legado(prazo)

    acompanhamento = buscar_acompanhamento_da_publicacao(
        publicacao_id, usuario_id
    )

    if acompanhamento:
        prazo.update({
            "acompanhamento_estado": acompanhamento["estado"],
            "dias_sugeridos": acompanhamento["dias_sugeridos"],
            "tipo_contagem_sugerida": acompanhamento["tipo_contagem_sugerida"],
            "trecho_sugerido": acompanhamento["trecho_sugerido"]
        })

    return {
        "prazo": prazo,
        "eventos_automaticos": eventos_da_publicacao(
            usuario_id, publicacao_id
        )
    }


def editar_publicacao(
    usuario_id,
    prazo_id=None,
    publicacao_id=None,
    dados_enviados=None
):
    prazo = (
        buscar_detalhes_prazo(prazo_id, usuario_id)
        if prazo_id is not None
        else buscar_detalhes_publicacao(publicacao_id, usuario_id)
    )

    if not prazo:
        abort(404)

    prazo.setdefault("personalizado_manualmente", False)
    prazo.setdefault("revisao_estado", None)
    aplicar_estado_legado(prazo)

    eventos_automaticos = eventos_da_publicacao(
        usuario_id, prazo["publicacao_id"]
    )
    erros = []

    if dados_enviados is None:
        vencimento = None if prazo["triagem"] else prazo["data_vencimento"]
        data_alerta = ""

        if vencimento and prazo["alerta_proximidade"] is not None:
            data_alerta = (
                vencimento - timedelta(days=prazo["alerta_proximidade"])
            ).isoformat()

        dados = {
            "cliente": prazo["cliente"] or "",
            "numero_processo": prazo["numero_processo"] or "",
            "tribunal": prazo["tribunal"] or "",
            "vara": prazo["vara"] or "",
            "unidade_judicial": prazo.get("unidade_judicial") or "",
            "link_processo": prazo["link_processo"] or "",
            "data_publicacao": (
                prazo["data_publicacao"].isoformat()
                if prazo["data_publicacao"] else ""
            ),
            "data_vencimento": vencimento.isoformat() if vencimento else "",
            "data_alerta": data_alerta,
            "observacoes": prazo.get("observacoes") or ""
        }

    else:
        dados = {
            "cliente": dados_enviados.get("cliente", "").strip(),
            "numero_processo": dados_enviados.get("numero_processo", "").strip(),
            "tribunal": dados_enviados.get("tribunal", "").strip(),
            "vara": dados_enviados.get("vara", "").strip(),
            "unidade_judicial": prazo.get("unidade_judicial") or "",
            "link_processo": dados_enviados.get("link_processo", "").strip(),
            "data_publicacao": dados_enviados.get("data_publicacao", ""),
            "data_vencimento": dados_enviados.get("data_vencimento", ""),
            "data_alerta": dados_enviados.get("data_alerta", ""),
            "observacoes": dados_enviados.get(
                "observacoes", prazo.get("observacoes") or ""
            ).strip()
        }

        if not dados["numero_processo"]:
            erros.append("Informe o número do processo.")

        if len(dados["numero_processo"]) > 25:
            erros.append("Número do processo muito longo.")

        if len(dados["cliente"]) > 150:
            erros.append("Nome do cliente muito longo.")

        if len(dados["tribunal"]) > 30:
            erros.append("Nome do tribunal muito longo.")

        if dados["vara"] not in ("", "civil", "trabalhista", "federal"):
            erros.append("Selecione uma vara válida.")

        if len(dados["link_processo"]) > 500:
            erros.append("Link do processo muito longo.")

        if dados["link_processo"]:
            url = urlparse(dados["link_processo"])

            if url.scheme not in ("http", "https") or not url.hostname:
                erros.append("Link do processo inválido.")

        def converter_data(valor, campo):
            if not valor:
                return None
            try:
                return date.fromisoformat(valor)
            except ValueError:
                erros.append(f"Data inválida: {campo}.")
                return None

        data_publicacao = converter_data(
            dados["data_publicacao"], "a data da publicação"
        )
        data_vencimento = converter_data(
            dados["data_vencimento"], "a data de vencimento"
        )
        data_alerta = converter_data(
            dados["data_alerta"], "a data do alerta"
        )

        alerta_proximidade = None
        vencimento_atual = prazo["data_vencimento"]

        alterar_vencimento = (
            data_vencimento is not None
            and (prazo["triagem"] or data_vencimento != vencimento_atual)
        )

        vencimento_para_alerta = (
            data_vencimento if alterar_vencimento else vencimento_atual
        )

        if data_alerta and vencimento_para_alerta:
            if data_alerta > vencimento_para_alerta:
                erros.append("O alerta não pode ser posterior ao vencimento.")
            else:
                alerta_proximidade = (
                    vencimento_para_alerta - data_alerta
                ).days

        if (
            data_vencimento
            and prazo["data_inicio"]
            and data_vencimento < prazo["data_inicio"]
        ):
            erros.append(
                "O vencimento não pode ser anterior ao início do prazo."
            )

        if not erros:
            atualizacao = {
                "cliente": dados["cliente"] or None,
                "numero_processo": dados["numero_processo"],
                "tribunal": dados["tribunal"] or None,
                "vara": dados["vara"] or None,
                "link_processo": dados["link_processo"] or None,
                "data_publicacao": data_publicacao,
                "data_vencimento": data_vencimento,
                "alterar_vencimento": alterar_vencimento,
                "alerta_proximidade": alerta_proximidade,
                "observacoes": dados["observacoes"] or None
            }

            try:
                if prazo_id is None:
                    atualizado = atualizar_dados_publicacao(
                        publicacao_id, usuario_id, atualizacao
                    )
                else:
                    atualizado = atualizar_dados_prazo(
                        prazo_id, usuario_id, atualizacao
                    )

            except ValueError as erro:
                erros.append(str(erro))

            else:
                if not atualizado:
                    abort(404)

                return {
                    "publicacao_id": prazo["publicacao_id"],
                    "salvo": True
                }

    return {
        "prazo": prazo,
        "dados": dados,
        "erros": erros,
        "eventos_automaticos": eventos_automaticos,
        "salvo": False
    }


def novo_prazo(usuario_id, publicacao_id, dados_enviados=None):
    detalhes = buscar_detalhes_publicacao(publicacao_id, usuario_id)

    if detalhes is None:
        abort(404)

    if detalhes["prazo_id"]:
        return {"prazo_id": detalhes["prazo_id"], "salvo": True}

    erros = []
    dados = {
        "nome_prazo": "",
        "dias": "",
        "tipo_contagem": "uteis",
        "data_inicio": "",
        "data_vencimento": ""
    }

    if dados_enviados is not None:
        dados = {
            campo: dados_enviados.get(campo, "").strip()
            for campo in dados
        }

        nome = dados["nome_prazo"]

        if not nome or len(nome) > 150:
            erros.append("Informe o nome do prazo (até 150 caracteres).")

        if dados["tipo_contagem"] not in ("uteis", "corridos"):
            erros.append("Tipo de contagem inválido.")

        try:
            dias = int(dados["dias"])
            if not 1 <= dias <= 3650:
                raise ValueError()
        except ValueError:
            dias = None
            erros.append("Informe uma quantidade de dias entre 1 e 3650.")

        try:
            inicio = date.fromisoformat(dados["data_inicio"])
            vencimento = date.fromisoformat(dados["data_vencimento"])
            if vencimento < inicio:
                erros.append("Vencimento anterior ao início.")
        except ValueError:
            inicio = vencimento = None
            erros.append("Informe datas válidas de início e vencimento.")

        if not erros:
            try:
                prazo_id = criar_prazo_confirmado_pela_advogada(
                    publicacao_id,
                    usuario_id,
                    {
                        "nome_prazo": nome,
                        "dias": dias,
                        "tipo_contagem": dados["tipo_contagem"],
                        "data_inicio": inicio,
                        "data_vencimento": vencimento
                    }
                )
            except ValueError as erro:
                erros.append(str(erro))
            else:
                if prazo_id is None:
                    abort(404)
                return {"prazo_id": prazo_id, "salvo": True}

    return {
        "publicacao": detalhes,
        "dados": dados,
        "erros": erros,
        "salvo": False
    }


def confirmar_sugestao(usuario_id, prazo_id, dados_enviados):
    prazo = buscar_detalhes_prazo(prazo_id, usuario_id)

    if not prazo:
        abort(404)

    if (
        prazo["revisao_estado"] != "pendente"
        or prazo["origem_prazo"] != "estimativa_prazus"
    ):
        abort(400)

    try:
        dias = int(dados_enviados.get("dias", ""))
        tipo = dados_enviados.get("tipo_contagem", "")
        inicio = date.fromisoformat(dados_enviados.get("data_inicio", ""))
        vencimento = date.fromisoformat(
            dados_enviados.get("data_vencimento", "")
        )
    except (ValueError, TypeError):
        abort(400, description="Dados do prazo inválidos.")

    if not 1 <= dias <= 3650:
        abort(400, description="Quantidade de dias inválida.")

    if tipo not in ("corridos", "uteis"):
        abort(400, description="Tipo de contagem inválido.")

    if vencimento < inicio:
        abort(400, description="O vencimento não pode ser anterior ao início.")

    atualizado = confirmar_sugestao_prazo(
        prazo_id,
        usuario_id,
        {
            "dias": dias,
            "tipo_contagem": tipo,
            "data_inicio": inicio,
            "data_vencimento": vencimento
        }
    )

    if not atualizado:
        abort(409, description="O prazo não está mais pendente.")

    return {"prazo_id": prazo_id}