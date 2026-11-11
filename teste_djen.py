from service.djen_service import consultar_publicacoes

resultado = consultar_publicacoes(
    oab="numero oab",
    uf="SP",
    data_inicio="2026-10-10",
    data_fim="2026-11-10"
)

print("Total encontrado:", resultado.get("count", 0))

for publicacao in resultado.get("items", []):
    print("Processo:", publicacao.get("numeroProcesso"))
    print("Conteúdo:", publicacao.get("texto", "")[:200])
    print("-" * 40)
