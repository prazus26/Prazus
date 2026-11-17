
from backend.repository.analise_ia_repository import contar_analises


try:
    total = contar_analises()

    print("Conexão com analises_ia funcionando!")
    print(f"Total de análises: {total}")

except Exception as erro:
    print(f"Erro: {type(erro).__name__}: {erro}")
