"""Diagnóstico somente leitura; não chama Gemini nem altera banco."""
from sqlalchemy import func
from database import Session
from model.processo import Processo
from model.publicacao import Publicacao
from model.analise_ia import AnaliseIA

with Session() as sessao:
    print('=== DIAGNOSTICO DE PRONTIDAO DO PRAZUS ===')
    print('Publicacoes:', sessao.query(func.count(Publicacao.id)).scalar())
    print('Analises concluidas:', sessao.query(func.count(AnaliseIA.id)).filter(AnaliseIA.estado == 'concluida').scalar())
    print('Processos por tribunal (inclui campos ausentes):')
    grupos = (sessao.query(Processo.tribunal, func.count(Processo.id))
              .group_by(Processo.tribunal).order_by(func.count(Processo.id).desc()).all())
    for tribunal, qtd in grupos:
        print(f'  {tribunal or "TRIBUNAL NAO INFORMADO"}: {qtd}')
    print('Publicacoes sem data_publicacao:',
          sessao.query(func.count(Publicacao.id)).filter(Publicacao.data_publicacao.is_(None)).scalar())
print('SOMENTE LEITURA — sem chamadas Gemini, SQL INSERT/UPDATE/DELETE ou recalculos.')
