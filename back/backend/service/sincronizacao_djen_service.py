"""Sincroniza DJEN sem gerar prazos; mantém metadados em publicações existentes."""
from datetime import date

from backend.service.djen_service import consultar_publicacoes
from backend.repository.processo_repository import cadastrar_processo
from backend.service.normalizacao_processo_djen_service import extrair_dados_processo
from backend.repository.publicacao_repository import (
    cadastrar_publicacao, buscar_publicacao_do_usuario_por_djen
)
from backend.repository.metadados_djen_repository import atualizar_metadados


def sincronizar_advogado(usuario_id, oab, uf, data_inicio, data_fim):
    resultado = consultar_publicacoes(oab=oab, uf=uf,
                                    data_inicio=data_inicio, data_fim=data_fim)
    importadas = 0
    ignoradas = 0
    metadados_atualizados = 0
    erros = []

    for pub in resultado.get('items', []):
        try:
            identificador = pub.get('id')
            if identificador is None:
                ignoradas += 1
                continue

            encontrado = buscar_publicacao_do_usuario_por_djen(usuario_id, identificador)
            # As consultas antigas podem retornar Row/tuple de (id,), não objeto Publicacao.
            existente_id = encontrado[0] if encontrado is not None else None

            if existente_id is not None:
                atualizar_metadados(existente_id, pub)
                metadados_atualizados += 1
                ignoradas += 1
                continue

            # Não importar comunicações inativas/canceladas como novas publicações.
            if pub.get('ativo') is False or pub.get('data_cancelamento'):
                ignoradas += 1
                continue

            numero_processo = (pub.get('numeroprocessocommascara')
                              or pub.get('numero_processo'))
            texto = pub.get('texto')
            disponibilizacao = pub.get('data_disponibilizacao')
            if not all([numero_processo, texto, disponibilizacao]):
                ignoradas += 1
                continue
            data_disponibilizacao = date.fromisoformat(disponibilizacao)

            dados_processo = extrair_dados_processo(
                texto,
                nome_classe=pub.get('nomeClasse'),
                tipo_documento=pub.get('tipoDocumento'),
            )
            processo = cadastrar_processo(
                usuario_id=usuario_id,
                numero_processo=numero_processo,
                tribunal=pub.get('siglaTribunal'),
                assunto=None,  # DJEN nao informa assunto especifico aqui
                classe=dados_processo['classe'],
                cliente=dados_processo['cliente'],
            )
            registro = cadastrar_publicacao(
                processo_id=processo.id,
                identificador_djen=str(identificador),
                data_disponibilizacao=data_disponibilizacao,
                conteudo_original=texto,
            )
            atualizar_metadados(registro.id, pub)
            metadados_atualizados += 1
            importadas += 1
        except Exception as erro:
            erros.append({'id_djen': pub.get('id'), 'erro': str(erro)})
    return {
        'total_encontrado': resultado.get('count', 0),
        'importadas': importadas,
        'ignoradas': ignoradas,
        'metadados_atualizados': metadados_atualizados,
        'erros': erros,
    }
