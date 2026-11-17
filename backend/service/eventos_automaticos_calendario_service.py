"""Compromissos automáticos fundamentados em publicações DJEN analisadas.

Não calcula vencimentos judiciais, não escreve no banco e não chama IA.
Um compromisso datado não equivale a um prazo judicial validado.
"""
import hashlib
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from backend.service.calendario_judicial_service import (
    carregar_calendario, calcular_data_limite_antes_evento,
    CalendarioIncompletoError,
)

from backend.database import Session
from backend.model.analise_ia import AnaliseIA
from backend.model.metadado_comunicacao_djen import MetadadoComunicacaoDJEN
from backend.model.processo import Processo
from backend.model.publicacao import Publicacao
from backend.model.usuario import Usuario
from backend.service.avaliacao_prazos_ia_service import avaliar_analise
from backend.service.normalizacao_processo_djen_service import extrair_dados_processo


def _sem_acentos(texto):
    return "".join(
        caractere for caractere in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(caractere)
    ).lower()



def _cliente_do_djen_se_comprovado(texto, cliente, destinatario, oab_numero, oab_uf):
    """Complementa nome apenas na exibição, com OAB/UF do destinatário conferidas.

    Nunca altera o MySQL e nunca usa o cliente provável da IA sozinho.
    """
    if cliente:
        return cliente
    if not isinstance(destinatario, dict):
        return None
    advogado = destinatario.get("advogado", destinatario)
    if not isinstance(advogado, dict):
        return None
    numero = lambda v: re.sub(r"\D", "", str(v or ""))
    if not numero(oab_numero) or numero(advogado.get("numero_oab")) != numero(oab_numero):
        return None
    if str(advogado.get("uf_oab") or "").upper().strip() != str(oab_uf or "").upper().strip():
        return None
    # O nome do advogado destinatário deve constar no texto original.
    nome = advogado.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        return None
    if _sem_acentos(nome.strip()) not in _sem_acentos(texto or ""):
        return None
    dados = extrair_dados_processo(texto)
    return dados.get("cliente")


def extrair_pericia_designada(texto, data_disponibilizacao=None):
    """Extrai data/hora só quando vêm após 'perícia ... designada'.

    Havendo múltiplas datas distintas de perícia, não escolhe uma arbitrariamente.
    """
    if not isinstance(texto, str) or not texto.strip():
        return None

    normalizado = _sem_acentos(texto)
    padrao = re.compile(
        r"\bpericia\b.{0,110}?\bdesignad[ao]s?\b.{0,220}?"
        r"(?P<data>\d{2}/\d{2}/\d{4})"
        r"(?:\s*(?:as|a|às|á[s]?)\s*"
        r"(?P<hora>\d{1,2})\s*h\s*(?P<minuto>\d{2})\s*(?:min)?)?",
        re.DOTALL,
    )
    encontrados = set()
    for achado in padrao.finditer(normalizado):
        try:
            data = datetime.strptime(achado.group("data"), "%d/%m/%Y").date()
            hora = int(achado.group("hora")) if achado.group("hora") else None
            minuto = int(achado.group("minuto")) if achado.group("minuto") else 0
            if hora is not None and not (0 <= hora < 24 and 0 <= minuto < 60):
                continue
            if data_disponibilizacao is not None and data < data_disponibilizacao:
                continue
            encontrados.add((data, hora, minuto))
        except ValueError:
            continue

    if len(encontrados) != 1:
        return None
    data, hora, minuto = encontrados.pop()
    return datetime.combine(data, datetime.min.time()).replace(
        hour=hora or 0, minute=minuto
    ), hora is not None


def eventos_pericias_automaticas(usuario_id):
    """Obtém perícias da análise salva e da publicação de um único usuário."""
    with Session() as db:
        linhas = (
            db.query(
                Publicacao.id,
                Publicacao.conteudo_original,
                Publicacao.data_disponibilizacao,
                Processo.numero_processo,
                Processo.cliente,
                AnaliseIA.hash_conteudo,
                AnaliseIA.resultado_json,
                AnaliseIA.id,
                MetadadoComunicacaoDJEN.ativo,
                MetadadoComunicacaoDJEN.data_cancelamento,
                MetadadoComunicacaoDJEN.advogado_destinatario,
                Usuario.oab_numero,
                Usuario.oab_uf,
            )
            .join(Processo, Publicacao.processo_id == Processo.id)
            .join(Usuario, Processo.usuario_id == Usuario.id)
            .join(AnaliseIA, AnaliseIA.publicacao_id == Publicacao.id)
            .outerjoin(
                MetadadoComunicacaoDJEN,
                MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id,
            )
            .filter(
                Processo.usuario_id == usuario_id,
                AnaliseIA.estado == "concluida",
                AnaliseIA.versao_analisador == "gemini-v1",
            )
            .order_by(AnaliseIA.id.desc())
            .all()
        )

    eventos = []
    visitadas = set()
    for (
        publicacao_id, texto, disponibilizacao, processo, cliente,
        hash_salvo, analise, _analise_id, ativo, cancelamento,
        destinatario, oab_numero, oab_uf,
    ) in linhas:
        if publicacao_id in visitadas:
            continue
        if not texto or not isinstance(analise, dict):
            continue
        if ativo is False or cancelamento is not None:
            continue
        if hashlib.sha256(texto.encode("utf-8")).hexdigest() != hash_salvo:
            continue
        visitadas.add(publicacao_id)

        # A análise deve ter identificado uma perícia, e não apenas uma
        # data solta no texto de publicação.
        participantes = analise.get("participantes")
        menciona_perito = (
            isinstance(participantes, list)
            and any(
                isinstance(item, dict)
                and "perito" in _sem_acentos(str(item.get("papel", "")))
                for item in participantes
            )
        )
        if not menciona_perito:
            continue

        resultado = extrair_pericia_designada(texto, disponibilizacao)
        if resultado is None:
            continue
        data_hora, tem_horario = resultado
        cliente = _cliente_do_djen_se_comprovado(
            texto, cliente, destinatario, oab_numero, oab_uf
        )
        eventos.append({
            "id": f"pericia_{publicacao_id}",
            "title": f"Perícia — {cliente or processo}",
            "start": data_hora.isoformat() if tem_horario else data_hora.date().isoformat(),
            "allDay": not tem_horario,
            "backgroundColor": "#7296B8",
            "borderColor": "transparent",
            "textColor": "#FFFFFF",
            "extendedProps": {
                "tipo": "pericia",
                "publicacao_id": publicacao_id,
                "prazo_id": None,
                "numero_processo": processo,
                "cliente": cliente,
                "nome_prazo": "Perícia agendada — extraída automaticamente do DJEN",
                "origem_prazo": "djen_evento_automatico",
                "status": "evento_identificado",
                "dias_restantes": None,
            },
        })
    return eventos


# Prévia aritmética: não usa calendário judicial oficial.
# A ausência de feriados/suspensões é exibida explicitamente na agenda.
def calcular_previa_regressiva(data_evento, dias, contagem):
    """Calcula uma referência NÃO VALIDADA a partir do evento futuro.

    Exclui o próprio dia do evento. Dias úteis aqui significam somente
    segunda a sexta; feriados e suspensões ainda não foram verificados.
    """
    from datetime import date

    if type(data_evento) is not date or type(dias) is not int or not 1 <= dias <= 3650:
        raise ValueError("Evento ou quantidade de dias inválidos")
    if contagem not in ("uteis", "corridos"):
        raise ValueError("Contagem inválida")
    cursor = data_evento
    restantes = dias
    while restantes:
        cursor -= timedelta(days=1)
        if contagem == "corridos" or cursor.weekday() < 5:
            restantes -= 1
    return cursor



# Calendário-base oficial: NÃO inclui suspensões de cada unidade/vara.
# Retornar None quando a competência não puder ser identificada com segurança.
def calendario_base_trf3_sp_2026(numero_processo, tribunal):
    numero = str(numero_processo or "")
    orgao = str(tribunal or "").upper().strip()
    # CNJ *.4.03.* = Justiça Federal 3ª Região.
    # Este calendário é específico da Seção Judiciária de SP (SJSP).
    # A origem CNJ sozinha não diferencia SP de MS: exigir tribunal
    # com qualificador SP, ou número com a subseção 63xx da SJSP.
    import re
    marcador_sjsp = bool(re.search(r"\.4\.03\.6[0-9]{3}(?:$|\D)", numero))
    tribunal_sjsp = orgao in ("SJSP", "JFSP", "TRF3-SP", "TRF3/SP")
    if not (marcador_sjsp or tribunal_sjsp):
        return None
    try:
        caminho = Path(__file__).resolve().parent.parent / "calendarios" / "trf3_sjsp_2026_base.json"
        return carregar_calendario(caminho)
    except (OSError, ValueError, CalendarioIncompletoError):
        return None


def calcular_previa_com_calendario_base(data_evento, dias, contagem, numero_processo, tribunal):
    """Retorna data e metadados de auditoria, sem declarar validação jurídica."""
    calendario = calendario_base_trf3_sp_2026(numero_processo, tribunal)
    if calendario is not None and contagem == "uteis":
        try:
            resultado = calcular_data_limite_antes_evento(
                data_evento=data_evento, dias=dias, tipo_contagem=contagem,
                calendario=calendario,
            )
            return resultado, {
                "base_calendario": "TRF3/SJSP 2026 — feriados gerais",
                "fonte_calendario": calendario.fonte,
                "status_calendario": "base_oficial_parcial",
                "aviso": (
                    "Data provisória com feriados gerais da Portaria CJF3R 764/2025. "
                    "Suspensões da unidade, atos posteriores e interpretação jurídica "
                    "ainda não verificados."
                ),
            }
        except (ValueError, CalendarioIncompletoError):
            pass
    return calcular_previa_regressiva(data_evento, dias, contagem), {
        "base_calendario": None,
        "fonte_calendario": None,
        "status_calendario": "apenas_dias_semana",
        "aviso": "Prévia: dias de semana apenas; feriados, suspensões e validade jurídica não verificados.",
    }

def construir_eventos_provisorios(*, publicacao_id, texto, disponibilizacao,
                                  numero_processo, cliente, analise,
                                  destinatario, nome_advogado, oab_numero,
                                  oab_uf, tribunal=None):
    """Cria prévias somente para candidatos da parte comprovadamente representada.

    A análise precisa trazer evidência literal presente no texto. Se não for
    possível verificar representação, data, regra ou destinatário, não cria evento.
    """
    if not isinstance(destinatario, dict) or not isinstance(analise, dict):
        return []
    pericia = extrair_pericia_designada(texto, disponibilizacao)
    if pericia is None:
        return []
    data_evento = pericia[0].date()
    try:
        avaliacao = avaliar_analise(
            texto, analise, nome_advogado,
            destinatarioadvogados=[destinatario],
            oab_numero=oab_numero, oab_uf=oab_uf,
        )
    except (ValueError, TypeError, KeyError):
        return []

    cliente = _cliente_do_djen_se_comprovado(
        texto, cliente, destinatario, oab_numero, oab_uf
    )
    eventos = []
    for item in avaliacao.get("candidatos", []):
        if not (
            item.get("estado") == "aguardando_data_evento"
            and item.get("marco_temporal") == "antes_de_evento"
            and item.get("evento_referencia") == "pericia"
        ):
            continue
        try:
            data_previa, dados_calendario = calcular_previa_com_calendario_base(
                data_evento, item.get("dias"), item.get("contagem"),
                numero_processo, tribunal,
            )
        except ValueError:
            continue
        if disponibilizacao is not None and data_previa < disponibilizacao:
            # Publicação disponibilizada depois da data-limite: requer análise humana,
            # pois a previsão automática já não é operacional.
            continue
        evidencia = str(analise.get("prazos", [])[item["indice"]].get("evidencia", ""))
        facultativo = "faculta-se" in _sem_acentos(evidencia)
        descricao = "Atividade facultativa" if facultativo else "Atividade com data-limite"
        eventos.append({
            "id": f"previa_pericia_{publicacao_id}_{item['indice']}",
            "title": f"{descricao} — prévia não validada — {cliente or numero_processo}",
            "start": data_previa.isoformat(),
            "allDay": True,
            "backgroundColor": "#F3E27A",
            "borderColor": "#B38A33",
            "textColor": "#29231D",
            "extendedProps": {
                "tipo": "prazo_provisorio",
                "natureza_atividade": "facultativa" if facultativo else "a_verificar",
                "publicacao_id": publicacao_id,
                "prazo_id": None,
                "numero_processo": numero_processo,
                "cliente": cliente,
                "nome_prazo": item.get("atividade") or "Atividade anterior à perícia",
                "origem_prazo": "gemini_previa_aritmetica",
                "status": "aguardando_calendario_judicial",
                "dias_restantes": None,
                "data_evento_referencia": data_evento.isoformat(),
                "tipo_contagem": item["contagem"],
                "quantidade_dias": item["dias"],
                "aviso": dados_calendario["aviso"],
                "status_calendario": dados_calendario["status_calendario"],
                "base_calendario": dados_calendario["base_calendario"],
                "fonte_calendario": dados_calendario["fonte_calendario"],
                "validado_juridicamente": False,
            },
        })
    return eventos


def eventos_prazos_provisorios_automaticos(usuario_id):
    """Consulta somente publicações do usuário, sem IA externa nem escrita SQL."""
    with Session() as db:
        registros = (
            db.query(
                Publicacao.id,
                Publicacao.conteudo_original,
                Publicacao.data_disponibilizacao,
                Processo.numero_processo,
                Processo.cliente,
                Processo.tribunal,
                AnaliseIA.hash_conteudo,
                AnaliseIA.resultado_json,
                AnaliseIA.id,
                MetadadoComunicacaoDJEN.ativo,
                MetadadoComunicacaoDJEN.data_cancelamento,
                MetadadoComunicacaoDJEN.advogado_destinatario,
                Usuario.nome,
                Usuario.oab_numero,
                Usuario.oab_uf,
            )
            .join(Processo, Publicacao.processo_id == Processo.id)
            .join(Usuario, Processo.usuario_id == Usuario.id)
            .join(AnaliseIA, AnaliseIA.publicacao_id == Publicacao.id)
            .outerjoin(
                MetadadoComunicacaoDJEN,
                MetadadoComunicacaoDJEN.publicacao_id == Publicacao.id,
            )
            .filter(
                Usuario.id == usuario_id,
                AnaliseIA.estado == "concluida",
                AnaliseIA.versao_analisador == "gemini-v1",
            )
            .order_by(AnaliseIA.id.desc())
            .all()
        )

    eventos = []
    processadas = set()
    for (publicacao_id, texto, disponibilizacao, processo, cliente, tribunal,
         hash_salvo, analise, _analise_id, ativo, cancelamento,
         destinatario, nome_advogado, oab_numero, oab_uf) in registros:
        if publicacao_id in processadas:
            continue
        if ativo is False or cancelamento is not None:
            continue
        if not isinstance(texto, str) or not isinstance(analise, dict):
            continue
        if hashlib.sha256(texto.encode("utf-8")).hexdigest() != hash_salvo:
            continue
        # Seleciona a análise vigente mais recente, mesmo sem prazos relevantes.
        processadas.add(publicacao_id)
        eventos.extend(construir_eventos_provisorios(
            publicacao_id=publicacao_id,
            texto=texto,
            disponibilizacao=disponibilizacao,
            numero_processo=processo,
            cliente=cliente,
            analise=analise,
            destinatario=destinatario,
            nome_advogado=nome_advogado,
            oab_numero=oab_numero,
            oab_uf=oab_uf,
            tribunal=tribunal,
        ))
    return eventos
