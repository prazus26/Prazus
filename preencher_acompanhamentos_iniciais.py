"""Criação idempotente de acompanhamentos sem chamar a API DJEN.

Por padrão é somente simulação. Use --aplicar após criar a tabela e fazer backup.
"""
import argparse
from service.acompanhamento_service import registrar_acompanhamentos_advogado

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--usuario-id", type=int, required=True)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    if args.usuario_id < 1:
        parser.error("ID de usuário inválido")
    resultado = registrar_acompanhamentos_advogado(args.usuario_id, aplicar=args.aplicar)
    print(resultado)
    if not args.aplicar:
        print("Simulação: nenhuma linha foi criada.")
    else:
        print("Acompanhamentos criados; nenhum prazo antigo foi alterado.")
