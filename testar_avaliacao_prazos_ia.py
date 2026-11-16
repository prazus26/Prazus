"""Demonstração local sem banco, sem Google, sem edição do calendário."""
from datetime import date
from service.avaliacao_prazos_ia_service import avaliar_analise

documento = '''Autor: João da Silva. Ré: Empresa ABC Ltda. Advogada do autor: Maria Souza.
Intime-se a parte autora para apresentar manifestação em 15 dias úteis.
Intime-se a parte ré para apresentar documentos em 10 dias úteis.'''
analise = {'participantes':[{'nome':'Maria Souza','papel':'Advogada do autor','evidencia':'Advogada do autor: Maria Souza.'}],
           'prazos':[{'atividade':'apresentar manifestação','destinatario':'parte autora', 'dias':15,'contagem':'uteis','evidencia':'Intime-se a parte autora para apresentar manifestação em 15 dias úteis.','precisa_revisao':False},
                     {'atividade':'apresentar documentos','destinatario':'parte ré','dias':10,'contagem':'uteis','evidencia':'Intime-se a parte ré para apresentar documentos em 10 dias úteis.','precisa_revisao':False}]}
resultado = avaliar_analise(documento, analise, 'Maria Souza')
for p in resultado['candidatos']:
    print(f"Candidato {p['indice'] + 1}: {p['atividade']} | {p['estado']} | vencimento={p['vencimento_sugerido']}")
print('Nenhuma chamada Gemini e nenhuma escrita MySQL.')
