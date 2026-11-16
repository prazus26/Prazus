from datetime import date
from pathlib import Path
from service.calendario_judicial_service import (
    carregar_calendario, calcular_vencimento_verificavel)

calendario = carregar_calendario(
    Path(__file__).parent / 'exemplos/calendario_FICTICIO_nao_usar_em_producao.json')
print('SIMULAÇÃO COM CALENDÁRIO FICTÍCIO — NÃO É VENCIMENTO JUDICIAL REAL')
print('Órgão:', calendario.orgao)
print('Primeiro dia de contagem: 13/11/2026 (hipótese fictícia)')
print('Vencimento simulado:', calcular_vencimento_verificavel(
    primeiro_dia_contagem=date(2026, 11, 13), dias=3,
    tipo_contagem='uteis', calendario=calendario).strftime('%d/%m/%Y'))
print('Nenhum acesso ao MySQL, DJEN ou Gemini.')
