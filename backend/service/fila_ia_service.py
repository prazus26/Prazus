"""Seleção e execução da fila com cache, adiamentos e orçamento já existente.

Planejar/diagnosticar não reserva análise nem consome cota. A reserva MySQL
continua sendo a autoridade atômica antes de cada chamada ao provedor.
"""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import re

from backend.database import Session
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.usuario import Usuario
from backend.model.analise_ia import AnaliseIA
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from backend.service.processamento_ia_service import processar_publicacao, VERSAO_ANALISADOR


_CODIGOS = {'cota_api', 'schema_json_invalido', 'evidencia_prazo_inexistente',
    'evidencia_participante_inexistente', 'dias_invalidos', 'contagem_invalida',
    'estrutura_json_invalida', 'validacao_nao_classificada'}


def codigo_erro_seguro(valor):
    if valor in _CODIGOS:
        return valor
    if isinstance(valor, str) and re.fullmatch(r'erro_[A-Za-z_]{1,60}', valor):
        return valor
    return 'mensagem_legada_nao_exibida' if valor else None


def _planejar_fila(usuario_id, *, agora=None):
    """Snapshot de leitura. Os candidatos contêm texto: não imprimir esse retorno."""
    agora = agora or datetime.now(timezone.utc).replace(tzinfo=None)
    resumo = Counter()
    with Session() as db:
        linhas = db.query(Publicacao.id, Publicacao.conteudo_original, Usuario.nome,
            MetadadoComunicacaoDJEN.ativo, MetadadoComunicacaoDJEN.data_cancelamento).join(
            Processo, Publicacao.processo_id == Processo.id).join(
            Usuario, Processo.usuario_id == Usuario.id).outerjoin(
            MetadadoComunicacaoDJEN, MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id).filter(
            Processo.usuario_id == usuario_id).order_by(Publicacao.id.desc()).all()
        analises = db.query(AnaliseIA).join(Publicacao, AnaliseIA.publicacao_id == Publicacao.id).join(
            Processo, Publicacao.processo_id == Processo.id).filter(
            Processo.usuario_id == usuario_id, AnaliseIA.versao_analisador == VERSAO_ANALISADOR).order_by(
            AnaliseIA.id.desc()).all()
        indice = {}
        for a in analises:
            indice.setdefault((a.publicacao_id, a.hash_conteudo), dict(id=a.id, estado=a.estado,
                tentativas=a.tentativas, proxima=a.proxima_tentativa_em, expira=a.reserva_expira_em,
                codigo=codigo_erro_seguro(a.erro_resumido)))

    candidatos, falhas = [], []
    for pub_id, texto, nome, ativo, cancelamento in linhas:
        resumo['publicacoes_total'] += 1
        if ativo is False or cancelamento is not None:
            resumo['inativas_canceladas'] += 1
            continue
        if not texto or not texto.strip():
            resumo['texto_vazio'] += 1
            continue
        atual = indice.get((pub_id, sha256(texto.encode('utf-8')).hexdigest()))
        if atual is not None and atual['estado'] == 'concluida':
            resumo['concluidas_cache'] += 1
            continue
        if atual is not None and atual['estado'] in ('falha', 'aguardando_cota'):
            falhas.append(dict(publicacao_id=pub_id, analise_id=atual['id'], estado=atual['estado'],
                tentativas=atual['tentativas'], erro_codigo=atual['codigo'],
                proxima_tentativa_utc=atual['proxima'].isoformat() if atual['proxima'] else None))
        if atual is not None and atual['tentativas'] >= 5:
            resumo['limite_tentativas'] += 1
            continue
        if atual is not None and atual['estado'] == 'processando':
            if atual['expira'] is None or atual['expira'] > agora:
                resumo['reservadas_outro_processamento'] += 1
                continue
            resumo['reservas_expiradas_elegiveis'] += 1
        if atual is not None and atual['estado'] in ('falha', 'aguardando_cota') and atual['proxima'] and atual['proxima'] > agora:
            resumo['aguardando_retentativa'] += 1
            continue
        if atual is None:
            resumo['sem_analise_atual'] += 1
        resumo['elegiveis'] += 1
        candidatos.append(dict(publicacao_id=pub_id, texto=texto, nome_advogado=nome,
            estado='nao_analisada' if atual is None else atual['estado']))
    campos = ['publicacoes_total', 'concluidas_cache', 'sem_analise_atual', 'elegiveis',
        'inativas_canceladas', 'texto_vazio', 'limite_tentativas', 'aguardando_retentativa',
        'reservadas_outro_processamento', 'reservas_expiradas_elegiveis']
    return {'resumo': {c: resumo[c] for c in campos}, 'candidatos': candidatos, 'falhas': falhas}


def diagnosticar_fila(usuario_id, *, limite=20):
    if type(limite) is not int or not 1 <= limite <= 100:
        raise ValueError('Limite de detalhes deve estar entre 1 e 100.')
    plano = _planejar_fila(usuario_id)
    return dict(usuario_id=usuario_id, somente_leitura=True, versao_analisador=VERSAO_ANALISADOR,
        resumo=plano['resumo'], falhas=plano['falhas'][:limite],
        proximas_publicacoes=[{'publicacao_id': c['publicacao_id'], 'estado': c['estado']}
                             for c in plano['candidatos'][:limite]])


def processar_pendentes_advogado(usuario_id, limite=3, *, somente_simular=False, analisador=None):
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError('Limite por execução deve estar entre 1 e 20.')
    plano = _planejar_fila(usuario_id)
    resultados, chamadas, concluidas, falhas = [], 0, 0, 0
    estado = 'sem_pendencias' if not plano['candidatos'] else 'lote_processado'
    cota_diaria = False
    if somente_simular:
        estado = 'simulacao'
        resultados = [{'publicacao_id': c['publicacao_id'], 'estado': 'na_fila_para_verificacao'}
                      for c in plano['candidatos'][:limite]]
    else:
        for candidato in plano['candidatos']:
            if chamadas >= limite:
                break
            retorno = processar_publicacao(candidato['publicacao_id'], candidato['texto'],
                nome_advogado=candidato['nome_advogado'], analisador=analisador)
            resultados.append({'publicacao_id': candidato['publicacao_id'], **retorno})
            iniciou = retorno.get('chamada_iniciada', retorno.get('origem') == 'gemini'
                or retorno['estado'] in ('falha', 'aguardando_cota'))
            chamadas += int(iniciou)
            concluidas += int(retorno['estado'] == 'concluida' and iniciou)
            falhas += int(retorno['estado'] == 'falha')
            if retorno['estado'] in ('cota_diaria', 'aguardando_cota'):
                cota_diaria = retorno['estado'] == 'cota_diaria'
                estado = 'aguardando_cota'
                break
        if falhas and estado != 'aguardando_cota':
            estado = 'falha_parcial'
        if resultados and chamadas == 0 and estado == 'lote_processado':
            estados = {r['estado'] for r in resultados}
            if 'ocupada' in estados:
                estado = 'processamento_em_andamento'
            elif estados <= {'concluida'}:
                estado = 'reaproveitado_cache'
            elif estados <= {'limite'}:
                estado = 'limite_tentativas'
    if estado == 'sem_pendencias' and plano['resumo']['aguardando_retentativa']:
        estado = 'aguardando_retentativa'
    elif estado == 'sem_pendencias' and plano['resumo']['reservadas_outro_processamento']:
        estado = 'processamento_em_andamento'
    elif estado == 'sem_pendencias' and plano['resumo']['limite_tentativas']:
        estado = 'limite_tentativas'
    return dict(estado=estado, publicacoes_verificadas=len(resultados), chamadas_iniciadas=chamadas,
        concluidas=concluidas, falhas=falhas, cota_diaria_atingida=cota_diaria,
        selecao=plano['resumo'], resultados=resultados)
