from datetime import date

from service.djen_service import consultar_publicacoes
from repository.processo_repository import cadastrar_processo
from repository.publicacao_repository import (
    cadastrar_publicacao,
    buscar_publicacao_do_usuario_por_djen
)

def sincronizar_advogado(usuario_id, oab, uf, data_inicio, data_fim):

    resultado = consultar_publicacoes(
        oab=oab,
        uf=uf,
        data_inicio=data_inicio,
        data_fim=data_fim
    )

    importadas = 0
    ignoradas = 0
    erros = []

    for pub in resultado.get("items", []):

        try:
            if not pub.get("ativo", True):
                ignoradas += 1
                continue
            identificador = pub.get("id")
            existente = None

            if identificador is not None:
                existente = buscar_publicacao_do_usuario_por_djen(
                usuario_id,
                identificador
                )

            if existente:
                ignoradas += 1
                continue
            numero_processo = (
                pub.get("numeroprocessocommascara")
                or pub.get("numero_processo")
            )

            identificador = pub.get("id")
            texto = pub.get("texto")
            data_disponibilizacao = pub.get("data_disponibilizacao")

            if not all([
                numero_processo,
                identificador,
                texto,
                data_disponibilizacao
            ]):
                ignoradas += 1
                continue

            data_disponibilizacao = date.fromisoformat(
                data_disponibilizacao
            )

            processo = cadastrar_processo(
                usuario_id=usuario_id,
                numero_processo=numero_processo,
                tribunal=pub.get("siglaTribunal"),
                assunto=pub.get("nomeClasse"),
                classe=pub.get("tipoDocumento")
            )

            cadastrar_publicacao(
                processo_id=processo.id,
                identificador_djen=str(identificador),
                data_disponibilizacao=data_disponibilizacao,
                conteudo_original=texto
            )

            importadas += 1

        except Exception as erro:
            erros.append({
                "id_djen": pub.get("id"),
                "erro": str(erro)
            })

    return {
        "total_encontrado": resultado.get("count", 0),
        "importadas": importadas,
        "ignoradas": ignoradas,
        "erros": erros
    }
