"""Agenda persistida, sem acesso externo. Uma única fonte para telas e alertas."""
from copy import deepcopy
from hashlib import sha256
from datetime import datetime, date, timedelta
import re
import json

from backend.database import Session
from backend.model.evento_publicacao import EventoPublicacao
from backend.model.publicacao import Publicacao
from backend.model.processo import Processo
from backend.model.usuario import Usuario
from backend.model.analise_ia import AnaliseIA
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from backend.service.validacao_analise_service import validar_resultado
from backend.service.avaliacao_prazos_ia_service import avaliar_analise, _normalizar
from backend.service.eventos_automaticos_calendario_service import (
    extrair_pericia_designada, construir_eventos_provisorios,
    calendario_base_trf3_sp_2026, calcular_previa_com_calendario_base,
)
from backend.service.calculo_prazo_service import calcular_data_publicacao, calcular_data_inicio, calcular_vencimento
from backend.service.calendario_judicial_service import calcular_vencimento_verificavel
from backend.service.marcos_djen_service import apurar_marcos_djen


def data_literal(valor, evidencia):
    """Python converte somente dd/mm/aaaa literal no trecho; não aceita data inventada."""
    if not isinstance(valor, str) or not isinstance(evidencia, str) or valor not in evidencia:
        return None
    try:
        if not re.fullmatch(r'\d{2}/\d{2}/\d{4}', valor):
            return None
        return datetime.strptime(valor, '%d/%m/%Y').date()
    except ValueError:
        return None


def construir_eventos_adicionais(pub, processo, usuario, analise, meta):
    """Compromissos datados e obrigações com marco textual explícito.

    Regras incompletas continuam nos detalhes da análise; nunca recebem cinco dias.
    Calendário parcial e sinal de ambiguidade da IA não exigem aprovação humana.
    """
    texto = pub.conteudo_original
    validar_resultado(texto, analise)
    saida = []
    def adicionar(chave, nome, inicio, dias=None, contagem=None, tipo='compromisso', aviso=None):
        if inicio[:10] < pub.data_disponibilizacao.isoformat():
            return
        saida.append(dict(id=chave, title=nome, start=inicio, allDay=len(inicio)==10,
            extendedProps=dict(tipo=tipo, publicacao_id=pub.id, prazo_id=None,
                cliente=processo.cliente, numero_processo=processo.numero_processo,
                nome_prazo=nome, quantidade_dias=dias, tipo_contagem=contagem,
                validado_juridicamente=False, aviso=aviso or 'Data extraída do documento; confira os detalhes.',
                status='provisorio')))
    for item in analise.get('compromissos', []):
        evidencia = item['evidencia']
        dia = data_literal(item.get('data_textual'), evidencia)
        if dia is None:
            continue
        inicio = dia.isoformat()
        hora = item.get('hora_textual')
        if hora:
            if hora not in evidencia or not re.fullmatch(r'\d{1,2}[:h]\d{2}', hora):
                continue
            try:
                h, m = map(int, re.split('[:h]', hora))
                inicio = datetime.combine(dia, datetime.min.time()).replace(hour=h, minute=m).isoformat()
            except ValueError:
                continue
        chave = sha256((item['nome'] + evidencia).encode()).hexdigest()[:32]
        adicionar('compromisso_' + chave, item['nome'], inicio)

    avaliacao = avaliar_analise(texto, analise, usuario.nome,
        destinatarioadvogados=[meta.advogado_destinatario] if meta and meta.advogado_destinatario else None,
        oab_numero=usuario.oab_numero, oab_uf=usuario.oab_uf)
    for candidato in avaliacao['candidatos']:
        if candidato['estado'] in ('parte_contraria', 'representacao_ou_destinatario_indeterminado'):
            continue
        item = analise['prazos'][candidato['indice']]
        dias, contagem = item.get('dias'), item.get('contagem')
        # A IA identifica o marco; Python exige a menção literal correspondente.
        evidencia = item['evidencia']
        normal = _normalizar(evidencia)
        marco = item.get('marco')
        if marco in (None, 'indeterminado') and re.search(r'(?:desta|da) publica[cç][aã]o', normal):
            marco = 'publicacao'
        if marco == 'data_expressa':
            limite = data_literal(item.get('data_textual'), evidencia)
            if limite:
                adicionar('prazo_' + str(candidato['indice']), item['atividade'], limite.isoformat(), dias, contagem, 'prazo_provisorio')
            continue
        if type(dias) is not int or not 1 <= dias <= 3650 or contagem not in ('uteis', 'corridos'):
            continue
        if marco == 'antes_de_evento':
            referencia = _normalizar(item.get('evento_referencia'))
            datas = {data_literal(c.get('data_textual'), c.get('evidencia'))
                     for c in analise.get('compromissos', []) if referencia
                     and referencia in _normalizar(c.get('nome'))}
            datas.discard(None)
            if ('uteis' if contagem == 'uteis' else 'corridos') not in normal:
                continue
            if len(datas) == 1 and referencia in normal and re.search(r'\bantes\b', normal) and re.search(r'\b' + str(dias) + r'\s+dias?\b', normal):
                limite, info = calcular_previa_com_calendario_base(next(iter(datas)), dias, contagem,
                    processo.numero_processo, processo.tribunal)
                adicionar('prazo_' + str(candidato['indice']), item['atividade'], limite.isoformat(), dias,
                    contagem, 'prazo_provisorio', info['aviso'])
            continue
        if marco != 'publicacao' or not re.search(r'(?:desta|da) publica[cç][aã]o', normal):
            continue
        if not re.search(r'\b' + str(dias) + r'\s*(?:\([^)]*\)\s*)?dias?\b', normal):
            continue
        # Não inferir contagem apenas pelo campo retornado pelo modelo.
        if ('uteis' if contagem == 'uteis' else 'corridos') not in normal:
            continue
        if not meta or _normalizar(meta.meio) not in ('d', 'djen', 'diario de justica eletronico nacional'):
            continue
        if _normalizar(meta.tipo_comunicacao) not in ('intimacao', 'publicacao'):
            continue
        calendario = calendario_base_trf3_sp_2026(processo.numero_processo, processo.tribunal)
        aviso = 'Prévia aritmética: feriados e suspensões não verificados.'
        if calendario:
            try:
                marcos = apurar_marcos_djen(data_disponibilizacao=pub.data_disponibilizacao,
                    calendario=calendario, comunicacao_confirmada_djen=True)
                limite = calcular_vencimento_verificavel(primeiro_dia_contagem=marcos.primeiro_dia_contagem,
                    dias=dias, tipo_contagem=contagem, calendario=calendario)
                aviso = 'Calendário-base parcial: suspensões locais e atos posteriores não verificados. ' + calendario.fonte
            except ValueError:
                calendario = None
        if calendario is None:
            publicada = calcular_data_publicacao(pub.data_disponibilizacao, set())
            inicio = calcular_data_inicio(publicada, set())
            limite = calcular_vencimento(inicio, dias, contagem, set())
        adicionar('prazo_' + str(candidato['indice']), item['atividade'], limite.isoformat(), dias, contagem,
            'prazo_provisorio', aviso)
    return saida


def sincronizar_eventos(usuario_id):
    """Reaproveita análises salvas. Bloqueia publicações para serializar upserts.

    Sem remoções físicas. Alterações opcionais e estados do usuário são preservados.
    Uma publicação inválida não impede o processamento das demais.
    """
    erros, total = [], 0
    with Session() as db:
        ids = [x[0] for x in db.query(Publicacao.id).join(Processo).filter(Processo.usuario_id == usuario_id).all()]
    for pub_id in ids:
        with Session.begin() as db:
            pub = db.query(Publicacao).filter_by(id=pub_id).with_for_update().one()
            processo = db.get(Processo, pub.processo_id)
            if processo.usuario_id != usuario_id:
                continue
            usuario = db.get(Usuario, usuario_id)
            meta = db.query(MetadadoComunicacaoDJEN).filter_by(publicacao_id=pub_id).one_or_none()
            ativos = not meta or (meta.ativo is not False and meta.data_cancelamento is None)
            hash_atual = sha256(pub.conteudo_original.encode()).hexdigest()
            analise = db.query(AnaliseIA).filter_by(publicacao_id=pub_id, hash_conteudo=hash_atual,
                versao_analisador='gemini-v1', estado='concluida').order_by(AnaliseIA.id.desc()).first()
            eventos = []
            if ativos and analise:
                try:
                    validar_resultado(pub.conteudo_original, analise.resultado_json)
                    dados_ia = analise.resultado_json
                    contexto = dict(publicacao_id=pub.id, texto=pub.conteudo_original,
                        disponibilizacao=pub.data_disponibilizacao, numero_processo=processo.numero_processo,
                        cliente=processo.cliente, analise=dados_ia,
                        destinatario=meta.advogado_destinatario if meta else None,
                        nome_advogado=usuario.nome, oab_numero=usuario.oab_numero,
                        oab_uf=usuario.oab_uf, tribunal=processo.tribunal)
                    eventos = construir_eventos_provisorios(**contexto)
                    pericia = extrair_pericia_designada(pub.conteudo_original, pub.data_disponibilizacao)
                    if pericia and any('perito' in _normalizar(p.get('papel')) for p in dados_ia.get('participantes', [])):
                        inicio, horario = pericia
                        eventos.append(dict(id='pericia_' + str(pub.id), title='Perícia',
                            start=inicio.isoformat() if horario else inicio.date().isoformat(), allDay=not horario,
                            extendedProps=dict(tipo='pericia', publicacao_id=pub.id, prazo_id=None,
                                cliente=processo.cliente, numero_processo=processo.numero_processo,
                                nome_prazo='Perícia', quantidade_dias=None,
                                aviso='Compromisso extraído do documento.', validado_juridicamente=False)))
                    extras = construir_eventos_adicionais(pub, processo, usuario, analise.resultado_json, meta)
                    # A mesma perícia pode constar no schema novo e na análise antiga.
                    if not processo.cliente:
                        avaliacao = avaliar_analise(pub.conteudo_original, dados_ia, usuario.nome,
                            destinatarioadvogados=[meta.advogado_destinatario] if meta and meta.advogado_destinatario else None,
                            oab_numero=usuario.oab_numero, oab_uf=usuario.oab_uf)
                        from backend.service.avaliacao_prazos_ia_service import _lado_do_papel
                        nomes = {p['nome'] for p in dados_ia.get('participantes', [])
                            if 'advogad' not in _normalizar(p.get('papel'))
                            and _lado_do_papel(p.get('papel')) == avaliacao['representa']
                            and avaliacao['representa'] is not None
                            and p.get('nome') and p['nome'] in p.get('evidencia', '')}
                        if len(nomes) == 1:
                            cliente = next(iter(nomes))[:150]
                            for e in eventos + extras:
                                e['extendedProps']['cliente'] = cliente
                    for extra in extras:
                        if not any(e['start'] == extra['start'] and e['extendedProps']['tipo'] == 'pericia'
                                   and 'pericia' in _normalizar(extra['title']) for e in eventos):
                            eventos.append(extra)
                except (ValueError, TypeError, KeyError):
                    eventos = []
                    erros.append({'publicacao_id': pub_id, 'codigo': 'analise_invalida'})
            existentes = {e.chave_origem: e for e in db.query(EventoPublicacao).filter_by(publicacao_id=pub_id).all()}
            for evento in existentes.values():
                evento.ativo = False
            chaves_ativas = set()
            for dados in eventos:
                chave = dados['id'][:100]
                if chave.startswith(('prazo_', 'previa_pericia_')):
                    indice = int(chave.rsplit('_', 1)[-1])
                    candidato = analise.resultado_json['prazos'][indice]
                    identidade = [candidato.get(c) for c in ('atividade', 'destinatario', 'evidencia')]
                    chave = 'obrigacao_' + sha256(json.dumps(identidade, ensure_ascii=False).encode()).hexdigest()
                if chave in chaves_ativas:
                    continue
                chaves_ativas.add(chave)
                evento = existentes.get(chave)
                if evento is None:
                    evento = EventoPublicacao(publicacao_id=pub_id, chave_origem=chave)
                    db.add(evento)
                    existentes[chave] = evento
                dados['hash_conteudo'] = hash_atual
                evento.dados = dados
                evento.ativo = True
                total += 1
    return {'eventos_ativos': total, 'erros': erros}


def listar_eventos(usuario_id, publicacao_id=None):
    """GET somente leitura. Filtro de cancelamento e hash também vale antes da rotina."""
    with Session() as db:
        consulta = db.query(EventoPublicacao, Publicacao, Processo).join(Publicacao,
            EventoPublicacao.publicacao_id == Publicacao.id).join(Processo).outerjoin(
            MetadadoComunicacaoDJEN, MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id).filter(
            Processo.usuario_id == usuario_id, EventoPublicacao.ativo.is_(True))
        if publicacao_id is not None:
            consulta = consulta.filter(Publicacao.id == publicacao_id)
        resultado = []
        for evento, pub, processo in consulta.all():
            meta = db.query(MetadadoComunicacaoDJEN).filter_by(publicacao_id=pub.id).one_or_none()
            if meta and (meta.ativo is False or meta.data_cancelamento is not None):
                continue
            dados = deepcopy(evento.dados)
            if dados.get('hash_conteudo') and dados['hash_conteudo'] != sha256(pub.conteudo_original.encode()).hexdigest():
                continue
            dados['id'] = 'evento_' + str(evento.id)
            dados['start'] = evento.inicio_personalizado or dados['start']
            dados['allDay'] = len(dados['start']) == 10
            p = dados['extendedProps']
            p.update(evento_id=evento.id, status=evento.status, alerta_proximidade=evento.alerta_proximidade)
            if processo.cliente:
                p['cliente'] = processo.cliente
            p['numero_processo'] = processo.numero_processo
            p['nome_prazo'] = evento.nome_personalizado or p['nome_prazo']
            p['personalizado'] = bool(evento.inicio_personalizado or evento.nome_personalizado)
            dados['url'] = '/publicacao/' + str(pub.id)
            resultado.append(dados)
        return resultado


_NAO_INFORMADO = object()


def _normalizar_inicio(inicio):
    if inicio in (None, ''):
        return None
    if not isinstance(inicio, str):
        raise ValueError('Data ou horário inválido.')
    try:
        valor = inicio.strip()
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', valor):
            return date.fromisoformat(valor).isoformat()
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?', valor):
            raise ValueError()
        return datetime.fromisoformat(valor).isoformat(timespec='seconds')
    except ValueError:
        raise ValueError('Data ou horário inválido.') from None


def editar_evento(evento_id, usuario_id, *, inicio=_NAO_INFORMADO,
                  nome=_NAO_INFORMADO, status=_NAO_INFORMADO, alerta=_NAO_INFORMADO):
    """Atualização parcial. Campo omitido preserva; campo vazio restaura o automático.

    Salvar o valor automático sem alteração não congela a próxima sincronização.
    """
    if status is not _NAO_INFORMADO and status not in ('pendente', 'concluido', 'cancelado'):
        raise ValueError('Estado inválido.')
    if nome is not _NAO_INFORMADO and nome is not None:
        if not isinstance(nome, str) or len(nome.strip()) > 150:
            raise ValueError('Informe um nome de até 150 caracteres.')
        nome = nome.strip() or None
    if inicio is not _NAO_INFORMADO:
        inicio = _normalizar_inicio(inicio)
    if alerta is not _NAO_INFORMADO and alerta is not None and (type(alerta) is not int or not 0 <= alerta <= 3650):
        raise ValueError('Antecedência inválida.')
    with Session.begin() as db:
        evento = db.query(EventoPublicacao).join(Publicacao).join(Processo).filter(
            EventoPublicacao.id == evento_id, Processo.usuario_id == usuario_id).with_for_update().first()
        if evento is None:
            return None
        if inicio is not _NAO_INFORMADO:
            original = _normalizar_inicio(evento.dados['start'])
            evento.inicio_personalizado = inicio if inicio != original else None
        if nome is not _NAO_INFORMADO:
            original = evento.dados['extendedProps']['nome_prazo']
            evento.nome_personalizado = nome if nome != original else None
        if status is not _NAO_INFORMADO:
            evento.status = status
        if alerta is not _NAO_INFORMADO:
            evento.alerta_proximidade = alerta
        return evento.publicacao_id
