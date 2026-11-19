"""Utilitário opcional. Sem --aplicar: apenas listagem resumida, zero API."""
import argparse
import os
from backend.service.fila_ia_service import processar_pendentes_advogado

parser = argparse.ArgumentParser(description="Fila IA do Prazus")
parser.add_argument("--usuario-id", type=int, required=True)
parser.add_argument("--limite", type=int, default=3)
parser.add_argument("--aplicar", action="store_true")
args = parser.parse_args()

if args.aplicar:
    if os.getenv("PRAZUS_IA_ENABLED", "0") != "1":
        raise SystemExit("Defina PRAZUS_IA_ENABLED=1 somente após a migração 004 e os testes.")
    resposta = processar_pendentes_advogado(args.usuario_id, args.limite)
    print("Processamento:", {k: v for k, v in resposta.items() if k != "resultados"})
    for item in resposta["resultados"]:
        print("Publicação", item["publicacao_id"], "estado", item["estado"])
else:
    resposta = processar_pendentes_advogado(args.usuario_id, args.limite, somente_simular=True)
    print("Prévia: nenhuma chamada ao Gemini e nenhuma escrita no MySQL")
    print("Itens consultados:", resposta["publicacoes_verificadas"])
