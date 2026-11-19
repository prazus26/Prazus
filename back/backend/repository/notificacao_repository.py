
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from backend.model.evento_publicacao import EventoPublicacao
from backend.model.prazo import Prazo
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from backend.service.estado_prazo_service import classificar_evento
from sqlalchemy import or_
from backend.database import Session
from backend.model.notificacao import Notificacao


def cadastrar_notificacao(usuario_id, prazo_id, chave_evento, titulo, mensagem, evento_id=None):
    db = Session()

    try:
        existente = db.query(Notificacao).filter(
            Notificacao.usuario_id == usuario_id,
            Notificacao.chave_evento == chave_evento
        ).first()

        if existente:
            return False

        nova = Notificacao(
            usuario_id=usuario_id,
            prazo_id=prazo_id,
            evento_id=evento_id,
            chave_evento=chave_evento,
            titulo=titulo,
            mensagem=mensagem,
            data_notificacao=datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None),
            visualizada=False
        )

        db.add(nova)
        db.commit()

        return True

    except IntegrityError:
        db.rollback()
        if db.query(Notificacao.id).filter_by(usuario_id=usuario_id, chave_evento=chave_evento).first():
            return False
        raise
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def _alerta_legado_historico(notificacao, prazo, hoje):
    if prazo is None or prazo.status != 'pendente' or prazo.data_vencimento_atual is None:
        return True
    tipo, _ = classificar_evento(prazo.origem_prazo, prazo.personalizado_manualmente,
        prazo.revisao_estado, prazo.data_vencimento_atual, None,
        data_vencimento_original=prazo.data_vencimento_original)
    if tipo == 'triagem':
        return True
    prefixo = f'prazo_{prazo.id}_{prazo.data_vencimento_atual.isoformat()}_'
    chave = notificacao.chave_evento or ''
    if not chave.startswith(prefixo):
        return True
    regra = chave[len(prefixo):]
    dias = {'vence_hoje': 0, 'vence_amanha': 1, 'vencido': -1}.get(regra)
    if regra.startswith('alerta_'):
        try:
            dias = int(regra[len('alerta_'):])
        except ValueError:
            return True
    return dias is None or (prazo.data_vencimento_atual - hoje).days != dias


def buscar_notificacoes(usuario_id, *, somente_nao_visualizadas=False):
    """Preserva alertas antigos, identificando os que não descrevem o estado atual.

    A classificação é somente leitura; não marca registros como visualizados.
    """
    from backend.service.agenda_eventos_service import listar_eventos
    hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
    with Session() as db:
        consulta = db.query(Notificacao, EventoPublicacao.publicacao_id, Prazo).outerjoin(
            EventoPublicacao, Notificacao.evento_id == EventoPublicacao.id).outerjoin(
            Prazo, Notificacao.prazo_id == Prazo.id).filter(Notificacao.usuario_id == usuario_id)
        if somente_nao_visualizadas:
            consulta = consulta.filter(Notificacao.visualizada.is_(False))
        linhas = consulta.order_by(Notificacao.data_notificacao.desc()).all()
        eventos = {e['extendedProps']['evento_id']: e for e in listar_eventos(usuario_id)} if any(n.evento_id for n, _, _ in linhas) else {}
        publicacoes = {pub_id or (prazo.publicacao_id if prazo else None) for _, pub_id, prazo in linhas}
        publicacoes.discard(None)
        canceladas = {linha[0] for linha in db.query(MetadadoComunicacaoDJEN.publicacao_id).filter(
            MetadadoComunicacaoDJEN.publicacao_id.in_(publicacoes),
            or_(MetadadoComunicacaoDJEN.ativo.is_(False), MetadadoComunicacaoDJEN.data_cancelamento.isnot(None))).all()} if publicacoes else set()
        saida = []
        for notificacao, publicacao_id, prazo in linhas:
            notificacao.publicacao_id = publicacao_id or (prazo.publicacao_id if prazo else None)
            notificacao.historica = False
            if notificacao.evento_id:
                evento = eventos.get(notificacao.evento_id)
                if evento is None or evento['extendedProps']['status'] != 'pendente':
                    notificacao.historica = True
                else:
                    prefixo = f"evento_{notificacao.evento_id}_{evento['start']}_"
                    chave = notificacao.chave_evento or ''
                    try:
                        dias_alerta = int(chave[len(prefixo):]) if chave.startswith(prefixo) else None
                    except ValueError:
                        dias_alerta = None
                    dias_atuais = (datetime.fromisoformat(evento['start']).date() - hoje).days
                    notificacao.historica = dias_alerta is None or dias_alerta != dias_atuais
            elif notificacao.prazo_id:
                notificacao.historica = _alerta_legado_historico(notificacao, prazo, hoje)
            if notificacao.publicacao_id in canceladas:
                notificacao.historica = True
            saida.append(notificacao)
        return saida


def marcar_como_visualizada(notificacao_id, usuario_id):
    db = Session()

    try:
        notificacao = db.query(Notificacao).filter(
            Notificacao.id == notificacao_id,
            Notificacao.usuario_id == usuario_id
        ).first()

        if not notificacao:
            return False

        notificacao.visualizada = True
        db.commit()

        return True

    except:
        db.rollback()
        raise

    finally:
        db.close()

def contar_notificacoes_nao_visualizadas(usuario_id):
    return sum(not item.historica for item in buscar_notificacoes(usuario_id, somente_nao_visualizadas=True))
