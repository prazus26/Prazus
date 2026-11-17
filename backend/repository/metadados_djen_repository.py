
"""Persiste os metadados DJEN de uma publicacao existente.

Nao altera prazos ou analises do Gemini.
"""

from backend.database import Session

from backend.model.metadado_comunicacao_djen import (
    MetadadoComunicacaoDJEN,
)
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.usuario import Usuario

from backend.service.normalizacao_metadados_djen_service import (
    extrair_metadados_djen,
    extrair_advogado_destinatario,
)


CAMPOS_API = {
    "tipo_comunicacao": "tipoComunicacao",
    "meio": "meio",
    "status_djen": "status",
    "ativo": "ativo",
    "data_cancelamento": "data_cancelamento",
    "nome_orgao": "nomeOrgao",
    "id_orgao": "idOrgao",
}


def atualizar_metadados(publicacao_id, publicacao_api):
    valores = extrair_metadados_djen(
        publicacao_api
    )

    with Session.begin() as sessao:

        registro = (
            sessao.query(MetadadoComunicacaoDJEN)
            .filter(
                MetadadoComunicacaoDJEN.publicacao_id
                == publicacao_id
            )
            .with_for_update()
            .one_or_none()
        )

        if registro is None:
            registro = MetadadoComunicacaoDJEN(
                publicacao_id=publicacao_id
            )
            sessao.add(registro)

        # Preserva campos quando a API os omite.
        for campo, valor in valores.items():
            campo_api = CAMPOS_API[campo]

            if campo_api in publicacao_api:
                setattr(registro, campo, valor)

        # Destinatarios so sao atualizados quando
        # esse campo veio na resposta da API.
        if "destinatarioadvogados" not in publicacao_api:
            return

        usuario = (
            sessao.query(
                Usuario.oab_numero,
                Usuario.oab_uf,
            )
            .select_from(Publicacao)
            .join(
                Processo,
                Processo.id == Publicacao.processo_id,
            )
            .join(
                Usuario,
                Usuario.id == Processo.usuario_id,
            )
            .filter(
                Publicacao.id == publicacao_id
            )
            .one_or_none()
        )

        if usuario is None:
            raise ValueError(
                "Usuario da publicacao nao encontrado"
            )

        destinatario = extrair_advogado_destinatario(
            publicacao_api,
            usuario.oab_numero,
            usuario.oab_uf,
        )

        # Atualiza inclusive quando nao existe
        # correspondencia, evitando preservar uma
        # identificacao antiga possivelmente incorreta.
        registro.advogado_destinatario = destinatario
