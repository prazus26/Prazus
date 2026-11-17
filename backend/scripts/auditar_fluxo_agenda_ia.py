"""Diagnóstico REAL do fluxo de prazos por usuário, sem API Gemini/sem SQL UPDATE.

Uso: python auditar_fluxo_agenda_ia.py --usuario-id 6
Imprime contagens por tribunal, análises concluídas, versões de texto e bloqueios.
Não expõe conteúdo, nomes de partes, OAB nem números processuais.
"""
import argparse
from collections import Counter
from hashlib import sha256

from backend.database import Session
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.analise_ia import AnaliseIA


def auditar(usuario_id):
    with Session() as s:
        linhas = (
            s.query(Publicacao.id, Publicacao.conteudo_original,
                    Publicacao.data_disponibilizacao, Publicacao.data_publicacao,
                    Processo.tribunal)
            .join(Processo, Publicacao.processo_id == Processo.id)
            .filter(Processo.usuario_id == usuario_id)
            .all()
        )
        ids = [r.id for r in linhas]
        registros = (
            s.query(AnaliseIA.publicacao_id, AnaliseIA.hash_conteudo,
                    AnaliseIA.estado, AnaliseIA.analisado_em)
            .filter(AnaliseIA.publicacao_id.in_(ids), AnaliseIA.estado == 'concluida')
            .all()
        ) if ids else []

    hashes = {}
    for r in registros:
        hashes.setdefault(r.publicacao_id, set()).add(str(r.hash_conteudo))

    tribunais = Counter(str(r.tribunal or 'SEM_TRIBUNAL') for r in linhas)
    com_analise_atual = sum(
        sha256((r.conteudo_original or '').encode('utf-8')).hexdigest() in hashes.get(r.id, set())
        for r in linhas
    )
    print('=== PRONTIDÃO REAL PARA PRAZOS AUTOMÁTICOS ===')
    print('Publicações:', len(linhas))
    print('Por tribunal:', dict(tribunais))
    print('Com análise IA concluída para o conteúdo atual:', com_analise_atual)
    print('Sem análise IA atual:', len(linhas) - com_analise_atual)
    print('Sem data de publicação persistida:', sum(r.data_publicacao is None for r in linhas))
    print('Data de disponibilização ausente:', sum(r.data_disponibilizacao is None for r in linhas))
    print('Modalidade DJEN verificada em banco: NÃO DISPONÍVEL NO MODELO ATUAL')
    print('Calendários oficiais completos no projeto: NÃO VERIFICADOS POR ESTE DIAGNÓSTICO')
    print('Próximo bloqueio: integrar modalidade real da API e calendários oficiais por órgão/unidade.')
    print('SOMENTE LEITURA — zero requisições Gemini, zero INSERT/UPDATE/DELETE.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--usuario-id', required=True, type=int)
    args = p.parse_args()
    auditar(args.usuario_id)
