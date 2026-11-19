
"""Normaliza metadados factuais recebidos do DJEN.

Nao infere prazos, nao chama IA e nao escreve no banco.
"""

from datetime import date, datetime


def _texto(valor, maximo):
    if valor is None:
        return None

    valor = str(valor).strip()
    return valor[:maximo] if valor else None


def _normalizar_oab(valor):
    return "".join(
        caractere
        for caractere in str(valor or "")
        if caractere.isdigit()
    )


def _normalizar_uf(valor):
    return str(valor or "").strip().upper()


def _data_cancelamento(valor):
    if valor in (None, ""):
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor[:10])
        except ValueError as erro:
            raise ValueError(
                "data_cancelamento em formato desconhecido"
            ) from erro

    raise ValueError(
        "data_cancelamento em tipo desconhecido"
    )


def extrair_metadados_djen(publicacao_api):
    if not isinstance(publicacao_api, dict):
        raise ValueError("Resposta DJEN invalida")

    ativo = publicacao_api.get("ativo")

    if ativo is not None and not isinstance(ativo, bool):
        raise ValueError(
            "Campo ativo DJEN nao e booleano"
        )

    return {
        "tipo_comunicacao": _texto(
            publicacao_api.get("tipoComunicacao"), 150
        ),
        "meio": _texto(
            publicacao_api.get("meio"), 150
        ),
        "status_djen": _texto(
            publicacao_api.get("status"), 150
        ),
        "ativo": ativo,
        "data_cancelamento": _data_cancelamento(
            publicacao_api.get("data_cancelamento")
        ),
        "nome_orgao": _texto(
            publicacao_api.get("nomeOrgao"), 255
        ),
        "id_orgao": _texto(
            publicacao_api.get("idOrgao"), 100
        ),
    }


def extrair_advogado_destinatario(
    publicacao_api,
    oab_numero,
    oab_uf,
):
    """Encontra o destinatario correspondente ao usuario.

    Retorna None se nao houver correspondencia inequívoca.

    Uma correspondencia de OAB/UF NAO comprova
    por si so qual parte o advogado representa.
    """

    numero_usuario = _normalizar_oab(oab_numero)
    uf_usuario = _normalizar_uf(oab_uf)

    if not numero_usuario or not uf_usuario:
        return None

    destinatarios = publicacao_api.get(
        "destinatarioadvogados"
    )

    if not isinstance(destinatarios, list):
        return None

    encontrados = []

    for registro in destinatarios:
        if not isinstance(registro, dict):
            continue

        advogado = registro.get("advogado")

        if not isinstance(advogado, dict):
            continue

        numero = _normalizar_oab(
            advogado.get("numero_oab")
        )
        uf = _normalizar_uf(
            advogado.get("uf_oab")
        )

        if numero != numero_usuario or uf != uf_usuario:
            continue

        nome = _texto(advogado.get("nome"), 255)

        if not nome:
            continue

        encontrados.append({
            "advogado": {
                "nome": nome,
                "numero_oab": numero,
                "uf_oab": uf,
            }
        })

    if not encontrados:
        return None

    # Registros repetidos do mesmo destinatario
    # nao causam ambiguidade.
    nomes_distintos = {
        registro["advogado"]["nome"].casefold()
        for registro in encontrados
    }

    if len(nomes_distintos) != 1:
        return None

    return encontrados[0]
