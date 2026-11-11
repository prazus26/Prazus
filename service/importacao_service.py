from repository.processo_repository import cadastrar_processo
from repository.publicacao_repository import cadastrar_publicacao
from repository.prazo_repository import cadastrar_prazo


def importar_publicacao(usuario_id, dados):
    """
    Importa uma publicação já extraída e organizada pelo DJEN.

    As datas devem ser objetos datetime.date.
    """

    numero_processo = dados.get("numero_processo")
    identificador_djen = dados.get("identificador_djen")
    data_disponibilizacao = dados.get("data_disponibilizacao")
    conteudo_original = dados.get("conteudo_original")

    if not all([
        usuario_id,
        numero_processo,
        identificador_djen,
        data_disponibilizacao,
        conteudo_original
    ]):
        raise ValueError("Dados obrigatórios da publicação não informados.")

    processo = cadastrar_processo(
        usuario_id=usuario_id,
        numero_processo=numero_processo,
        tribunal=dados.get("tribunal"),
        assunto=dados.get("assunto"),
        classe=dados.get("classe")
    )

    publicacao = cadastrar_publicacao(
        processo_id=processo.id,
        identificador_djen=identificador_djen,
        data_disponibilizacao=data_disponibilizacao,
        data_publicacao=dados.get("data_publicacao"),
        conteudo_original=conteudo_original
    )

    prazo = None

    if dados.get("data_vencimento"):
        prazo = cadastrar_prazo(
            publicacao_id=publicacao.id,
            dias_prazo=dados.get("dias_prazo"),
            tipo_contagem=dados.get("tipo_contagem", "corridos"),
            data_inicio=dados.get("data_inicio"),
            data_vencimento=dados.get("data_vencimento"),
            origem=dados.get("origem_prazo", "djen")
        )

    return {
        "processo": processo,
        "publicacao": publicacao,
        "prazo": prazo
    }
