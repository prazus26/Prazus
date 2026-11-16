
from database import Session

from repository.analise_ia_repository import (
    consultar_cota_diaria,
    consumir_cota_na_transacao,
    CotaDiariaExcedida,
)

print("Cota antes:", consultar_cota_diaria())

sessao = Session()
transacao = sessao.begin()

try:
    # Simula a primeira reserva dentro de uma transação.
    consumir_cota_na_transacao(sessao, limite=1)
    print("Primeira tentativa: PERMITIDA")

    # Simula uma segunda reserva no mesmo dia.
    try:
        consumir_cota_na_transacao(sessao, limite=1)
        print("ERRO: segunda tentativa foi permitida!")

    except CotaDiariaExcedida:
        print("Segunda tentativa: BLOQUEADA CORRETAMENTE")

finally:
    # Desfaz tudo: não consome a cota de verdade.
    transacao.rollback()
    sessao.close()

print("Cota depois:", consultar_cota_diaria())
