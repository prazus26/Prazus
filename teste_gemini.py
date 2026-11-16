
from service.analise_ia_service import analisar_publicacao


casos = [
    {
        "nome": "Dois prazos na mesma publicação",
        "advogado": "Maria Souza",
        "documento": """
        Processo nº 1001234-56.2026.8.26.0001
        Autor: João da Silva.
        Ré: Empresa ABC Ltda.
        Advogada do autor: Maria Souza.

        Intime-se a parte autora para apresentar
        manifestação em 15 dias úteis.

        Intime-se a parte ré para apresentar
        documentos em 10 dias úteis.
        """
    },
    {
        "nome": "Menção a prazo sem nova determinação",
        "advogado": "Maria Souza",
        "documento": """
        Processo nº 1001234-56.2026.8.26.0001
        Autor: João da Silva.
        Advogada do autor: Maria Souza.

        Certifico que o prazo de 15 dias anteriormente
        concedido à parte autora já transcorreu.
        Encaminhem-se os autos para conclusão.
        """
    },
    {
        "nome": "Prazo destinado à parte contrária",
        "advogado": "Maria Souza",
        "documento": """
        Processo nº 1001234-56.2026.8.26.0001
        Autor: João da Silva.
        Ré: Empresa ABC Ltda.
        Advogada do autor: Maria Souza.

        Intime-se exclusivamente a parte ré para
        apresentar documentos em 10 dias úteis.
        """
    }
]


for caso in casos:
    print(f"\n{'=' * 60}")
    print(f"TESTE: {caso['nome']}")
    print("=" * 60)

    try:
        resultado = analisar_publicacao(
            texto=caso["documento"],
            nome_advogado=caso["advogado"]
        )

        print(resultado.model_dump_json(indent=2))

    except Exception as erro:
        print(f"ERRO: {type(erro).__name__}: {erro}")
