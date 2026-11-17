"""Reaproveita análises existentes sem Gemini. Usar depois da migração 008.

python -m backend.scripts.atualizar_eventos_salvos           # somente inventário
python -m backend.scripts.atualizar_eventos_salvos --aplicar # grava apenas eventos
"""
import argparse
from backend.repository.usuario_repository import buscar_advogados_para_sincronizacao
from backend.service.agenda_eventos_service import sincronizar_eventos, listar_eventos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    for usuario in buscar_advogados_para_sincronizacao():
        if args.aplicar:
            resultado = sincronizar_eventos(usuario.id)
            print({'usuario_id': usuario.id, **resultado})
        else:
            print({'usuario_id': usuario.id, 'eventos_existentes': len(listar_eventos(usuario.id)), 'somente_leitura': True})


if __name__ == '__main__':
    main()
