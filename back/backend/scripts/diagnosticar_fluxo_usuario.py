"""Diagnóstico U01/U02, somente leitura. Não inicia rotina nem chama Gemini/DJEN.

python -m backend.scripts.diagnosticar_fluxo_usuario --usuario 6
"""
import argparse
from collections import Counter
from datetime import datetime
import json
from zoneinfo import ZoneInfo

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from backend.database import Session
from backend.model.usuario import Usuario
from backend.model.processo import Processo
from backend.model.publicacao import Publicacao
from backend.service.fila_ia_service import diagnosticar_fila
from backend.repository.analise_ia_repository import consultar_cota_diaria
from backend.service.agenda_eventos_service import listar_eventos
from backend.service.notificacao_service import listar_notificacoes


def _erro_sql_seguro(erro):
    args = getattr(getattr(erro, 'orig', None), 'args', ())
    return {'tipo': type(erro).__name__, 'codigo_sql': args[0] if args and type(args[0]) is int else None}


def coletar_diagnostico(usuario_id):
    with Session() as db:
        usuario = db.get(Usuario, usuario_id)
        if usuario is None or usuario.tipo != 'advogado':
            raise ValueError('Informe o ID de uma conta de advogado existente.')
        processos = db.query(Processo).filter_by(usuario_id=usuario_id).count()
        tribunais = Counter(p[0] or 'nao_informado' for p in db.query(Processo.tribunal).filter_by(usuario_id=usuario_id).all())
        tabelas = set(inspect(db.get_bind()).get_table_names())
        agendamento = []
        if 'apscheduler_jobs' in tabelas:
            for id_, proxima in db.execute(text('SELECT id, next_run_time FROM apscheduler_jobs')).all():
                if str(id_).startswith('rotina_'):
                    agendamento.append({'id': id_, 'proxima_execucao_sp': datetime.fromtimestamp(
                        proxima, ZoneInfo('America/Sao_Paulo')).isoformat() if proxima is not None else None})
    fila = diagnosticar_fila(usuario_id)
    try:
        cota = consultar_cota_diaria()
    except (SQLAlchemyError, ValueError) as erro:
        cota = {'estado': 'nao_disponivel', **_erro_sql_seguro(erro)}
    eventos = listar_eventos(usuario_id)
    notificacoes = listar_notificacoes(usuario_id)
    return {'usuario_id': usuario_id, 'somente_leitura': True,
        'processos_total': processos, 'processos_por_tribunal': dict(tribunais),
        'fila_ia': fila, 'cota_diaria_global': cota,
        'eventos_visiveis_por_estado': dict(Counter(e['extendedProps']['status'] for e in eventos)),
        'notificacoes': {'atuais': sum(not n.historica for n in notificacoes),
                        'historicas': sum(n.historica for n in notificacoes)},
        'agendamento_salvo': agendamento,
        'limites_do_diagnostico': [
            'Snapshot das tabelas; não comprova que o processo agendador está rodando.',
            'Cota é global, compartilhada pelos advogados.',
            'Códigos legados com texto livre são ocultados para não expor documentos ou credenciais.',
            'Não executa sincronização, geração de eventos ou novas análises.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usuario', type=int, required=True)
    args = parser.parse_args()
    try:
        resultado = coletar_diagnostico(args.usuario)
    except ValueError as erro:
        parser.error(str(erro))
    except SQLAlchemyError as erro:
        print(json.dumps({'somente_leitura': True, 'estado': 'diagnostico_incompleto',
                          **_erro_sql_seguro(erro)}, ensure_ascii=False))
        return 1
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
