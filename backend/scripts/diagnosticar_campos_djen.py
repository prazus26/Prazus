
from datetime import date, timedelta

from backend.service.djen_service import consultar_publicacoes
from backend.repository.usuario_repository import buscar_por_id


USUARIO_ID = 6

usuario = buscar_por_id(USUARIO_ID)

if usuario is None:
    raise RuntimeError("Advogado não encontrado.")

data_fim = date.today()
data_inicio = data_fim - timedelta(days=7)

resultado = consultar_publicacoes(
    usuario.oab_numero,
    usuario.oab_uf,
    data_inicio.isoformat(),
    data_fim.isoformat()
)

itens = resultado.get("items", [])

print("Total retornado:", len(itens))

if itens:
    publicacao = itens[0]

    print("\nCampos disponíveis:")
    for campo in sorted(publicacao.keys()):
        print("-", campo)

    print("\nCampos relacionados a datas:")
    for campo, valor in publicacao.items():
        if "data" in campo.lower():
            print(f"{campo}: {valor}")
else:
    print("Nenhuma publicação encontrada no período.")
