from repository.publicacao_repository import buscar_sem_prazo_por_usuario
from repository.feriado_repository import buscar_feriados_por_uf
from repository.prazo_repository import cadastrar_prazo

from service.identificacao_prazo_service import identificar_prazo
from service.calculo_prazo_service import (
    calcular_data_publicacao,
    calcular_data_inicio,
    calcular_vencimento
)


def gerar_prazos_advogado(usuario_id, uf):
    publicacoes = buscar_sem_prazo_por_usuario(usuario_id)
    
    feriados = {
        resultado[0]
        for resultado in buscar_feriados_por_uf(uf)
    }

    gerados = 0
    erros = []

    for publicacao in publicacoes:
        try:
            identificacao = identificar_prazo(
                publicacao.conteudo_original
            )

            data_publicacao = publicacao.data_publicacao

            if not data_publicacao:
                data_publicacao = calcular_data_publicacao(
                    publicacao.data_disponibilizacao,
                    feriados
                )

            data_inicio = calcular_data_inicio(
                data_publicacao,
                feriados
            )

            vencimento = calcular_vencimento(
                data_inicio,
                identificacao["dias"],
                identificacao["tipo_contagem"],
                feriados
            )

            cadastrar_prazo(
                publicacao_id=publicacao.id,
                dias_prazo=identificacao["dias"],
                tipo_contagem=identificacao["tipo_contagem"],
                data_inicio=data_inicio,
                data_vencimento=vencimento,
                origem=identificacao["origem"]
            )

            gerados += 1

        except Exception as erro:
            erros.append({
                "publicacao_id": publicacao.id,
                "erro": str(erro)
            })

    return {
        "encontradas": len(publicacoes),
        "gerados": gerados,
        "erros": erros
    }
