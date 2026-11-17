"""Confere alertas salvos sem Gemini/DJEN. Padrão: somente leitura.

python -m backend.scripts.verificar_notificacoes --usuario 6
python -m backend.scripts.verificar_notificacoes --usuario 6 --atualizar
"""
import argparse
import json
from backend.repository.usuario_repository import buscar_por_id
from backend.service.notificacao_service import gerar_notificacoes, listar_notificacoes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', type=int, required=True)
    parser.add_argument('--atualizar', action='store_true', help='Gerar alertas de hoje pelos eventos e prazos já salvos.')
    args = parser.parse_args()
    usuario = buscar_por_id(args.usuario)
    if usuario is None or usuario.tipo != 'advogado':
        parser.error('Informe o ID de uma conta de advogado existente.')
    resultado = {'usuario_id': args.usuario, 'somente_leitura': not args.atualizar}
    if args.atualizar:
        resultado['atualizacao'] = gerar_notificacoes(args.usuario)
    lista = listar_notificacoes(args.usuario)
    resultado.update(notificacoes_atuais=sum(not n.historica for n in lista),
        notificacoes_historicas=sum(n.historica for n in lista),
        nao_visualizadas_atuais=sum(not n.historica and not n.visualizada for n in lista))
    print(json.dumps(resultado, ensure_ascii=False))


if __name__ == '__main__':
    main()
