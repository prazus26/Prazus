
import hashlib

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    abort,
    redirect,
    url_for,
)

from database import Session
from utils.autenticacao import login_obrigatorio

from model.usuario import Usuario
from model.publicacao import Publicacao
from model.processo import Processo
from model.prazo import Prazo
from model.analise_ia import AnaliseIA
from model.metadado_comunicacao_djen import (
    MetadadoComunicacaoDJEN,
)

from service.avaliacao_prazos_ia_service import avaliar_analise

from controller.calendario_controller import (
    configuracao_cores,
    definir_cor,
)


publicadosHoje_bp = Blueprint("publicadosHoje", __name__)


MESES = [
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


ESTADOS_AVALIACAO = {
    "aguardando_data_evento":
        "Aguardando data da perícia",

    "representacao_ou_destinatario_indeterminado":
        "Representação não confirmada",

    "parte_contraria":
        "Obrigação da parte contrária",

    "revisao_necessaria":
        "Revisão necessária",

    "regra_incompleta":
        "Regra de prazo incompleta",

    "aguardando_calendario_judicial":
        "Aguardando calendário judicial",

    "aguardando_marco_e_calendario":
        "Aguardando marco e calendário judicial",

    "calendario_ou_marco_invalido":
        "Calendário ou marco inválido",

    "calculado_para_conferencia":
        "Data calculada para conferência",

    "data_calculada_para_conferencia":
        "Data calculada para conferência",
}


def data_selecionada():
    valor = request.args.get("data")

    if not valor:
        return datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).date()

    try:
        return date.fromisoformat(valor)

    except ValueError:
        abort(
            400,
            description="Data inválida.",
        )


def consultar_publicacoes(
    usuario_id,
    dia=None,
    ids=None,
):
    db = Session()

    try:
        consulta = (
            db.query(
                Publicacao,
                Processo,
                Prazo,
            )
            .join(
                Processo,
                Publicacao.processo_id == Processo.id,
            )
            .outerjoin(
                Prazo,
                Prazo.publicacao_id == Publicacao.id,
            )
            .filter(
                Processo.usuario_id == usuario_id
            )
        )

        if dia is not None:
            consulta = consulta.filter(
                Publicacao.data_disponibilizacao == dia
            )

        if ids is not None:
            consulta = consulta.filter(
                Publicacao.id.in_(ids)
            )

        resultados = (
            consulta
            .order_by(Publicacao.id.desc())
            .all()
        )

        publicacoes = []

        for publicacao, processo, prazo in resultados:
            publicacoes.append({
                "id": publicacao.id,

                "numero_processo":
                    processo.numero_processo,

                "cliente":
                    processo.cliente,

                "tribunal":
                    processo.tribunal,

                "vara":
                    processo.vara,

                "nome_prazo": (
                    prazo.nome_prazo
                    if prazo and prazo.nome_prazo
                    else None
                ),

                "dias_prazo": (
                    prazo.dias_prazo_atual
                    if prazo else None
                ),

                "data_vencimento": (
                    prazo.data_vencimento_atual
                    if prazo else None
                ),

                "prazo_id": (
                    prazo.id
                    if prazo else None
                ),

                "origem_prazo": (
                    prazo.origem_prazo
                    if prazo else None
                ),

                "status": (
                    prazo.status
                    if prazo else "sem prazo"
                ),

                "revisao_estado": (
                    prazo.revisao_estado
                    if prazo else None
                ),

                "data_disponibilizacao":
                    publicacao.data_disponibilizacao,

                "data_publicacao":
                    publicacao.data_publicacao,

                "conteudo_original":
                    publicacao.conteudo_original,
            })

        return publicacoes

    finally:
        db.close()



def adicionar_analises_ia(publicacoes, usuario_id):
    """
    Exibe análises existentes e identifica datas de perícia
    diretamente no texto original.

    Não chama Gemini, não grava no banco e não cria vencimentos.
    """
    import re
    import unicodedata

    def normalizar_texto(valor):
        valor = unicodedata.normalize(
            "NFKD", str(valor or "")
        )
        return "".join(
            c for c in valor
            if not unicodedata.combining(c)
        ).casefold()

    def identificar_data_pericia(texto, disponibilizacao):
        """
        Aceita uma data somente quando o contexto
        menciona uma perícia designada.

        Se houver datas candidatas diferentes,
        retorna None para evitar ambiguidade.
        """
        if not texto:
            return None

        candidatos = set()

        for ocorrencia in re.finditer(
            r"\b(\d{2}/\d{2}/\d{4})\b", texto
        ):
            inicio = ocorrencia.start()

            contexto = normalizar_texto(
                texto[max(0, inicio - 250):inicio]
            )

            # A data precisa aparecer após uma
            # referência ao agendamento da perícia.
            if "pericia" not in contexto:
                continue

            if "designad" not in contexto:
                continue

            if "data" not in contexto:
                continue

            try:
                data_evento = datetime.strptime(
                    ocorrencia.group(1),
                    "%d/%m/%Y"
                ).date()
            except ValueError:
                continue

            # Não aceitar como evento futuro uma data
            # anterior à disponibilização da publicação.
            if (
                disponibilizacao is not None
                and data_evento < disponibilizacao
            ):
                continue

            candidatos.add(data_evento)

        if len(candidatos) != 1:
            return None

        return next(iter(candidatos))

    # ==========================================
    # VALORES INICIAIS
    # ==========================================

    for publicacao in publicacoes:
        publicacao["ia_estado"] = "nao_analisada"
        publicacao["ia_resultado"] = None
        publicacao["ia_prazos"] = []
        publicacao["ia_avaliacoes"] = []
        publicacao["ia_estados_candidatos"] = []
        publicacao["ia_data_evento"] = None

    if not publicacoes:
        return

    ids = [p["id"] for p in publicacoes]

    publicacoes_por_id = {
        p["id"]: p for p in publicacoes
    }

    analises_por_id = {}
    metadados_por_id = {}

    # ==========================================
    # CONSULTAR MYSQL
    # ==========================================

    with Session() as db:
        usuario = db.get(Usuario, usuario_id)

        if usuario is None:
            abort(404)

        nome_advogado = usuario.nome
        oab_numero = usuario.oab_numero
        oab_uf = usuario.oab_uf

        analises = (
            db.query(AnaliseIA)
            .filter(
                AnaliseIA.publicacao_id.in_(ids),
                AnaliseIA.versao_analisador == "gemini-v1",
            )
            .order_by(AnaliseIA.id.desc())
            .all()
        )

        for analise in analises:
            publicacao = publicacoes_por_id.get(
                analise.publicacao_id
            )

            if publicacao is None:
                continue

            texto = publicacao["conteudo_original"] or ""

            hash_atual = hashlib.sha256(
                texto.encode("utf-8")
            ).hexdigest()

            if analise.hash_conteudo != hash_atual:
                continue

            if analise.publicacao_id in analises_por_id:
                continue

            analises_por_id[analise.publicacao_id] = {
                "estado": analise.estado,
                "resultado": analise.resultado_json,
            }

        metadados = (
            db.query(MetadadoComunicacaoDJEN)
            .filter(
                MetadadoComunicacaoDJEN.publicacao_id.in_(
                    ids
                )
            )
            .all()
        )

        for registro in metadados:
            metadados_por_id[registro.publicacao_id] = {
                "advogado_destinatario":
                    registro.advogado_destinatario,
                "ativo": registro.ativo,
                "data_cancelamento":
                    registro.data_cancelamento,
            }

    # ==========================================
    # ANÁLISES DO GEMINI
    # ==========================================

    for publicacao in publicacoes:
        analise = analises_por_id.get(publicacao["id"])

        if analise is None:
            continue

        publicacao["ia_estado"] = analise["estado"]

        if analise["estado"] != "concluida":
            continue

        resultado = analise["resultado"]

        if not isinstance(resultado, dict):
            continue

        publicacao["ia_resultado"] = resultado

        prazos = resultado.get("prazos", [])

        if isinstance(prazos, list):
            publicacao["ia_prazos"] = [
                p for p in prazos
                if isinstance(p, dict)
            ]

    # ==========================================
    # AVALIAÇÃO DAS OBRIGAÇÕES
    # ==========================================

    for publicacao in publicacoes:
        if (
            publicacao["ia_estado"] != "concluida"
            or publicacao["ia_resultado"] is None
        ):
            continue

        metadado = metadados_por_id.get(
            publicacao["id"]
        )

        # Comunicação cancelada/inativa não deve
        # receber um novo vencimento.
        if metadado and (
            metadado["ativo"] is False
            or metadado["data_cancelamento"] is not None
        ):
            publicacao["ia_estados_candidatos"] = [
                "Comunicação cancelada ou inativa"
                for _ in publicacao["ia_prazos"]
            ]
            continue

        destinatario = (
            metadado.get("advogado_destinatario")
            if metadado else None
        )

        try:
            avaliacao = avaliar_analise(
                texto=publicacao["conteudo_original"],
                analise=publicacao["ia_resultado"],
                nome_advogado=nome_advogado,
                destinatarioadvogados=(
                    [destinatario]
                    if isinstance(destinatario, dict)
                    else None
                ),
                oab_numero=oab_numero,
                oab_uf=oab_uf,
            )

        except (ValueError, TypeError, KeyError):
            publicacao["ia_estados_candidatos"] = [
                "Falha na avaliação — revisão necessária"
                for _ in publicacao["ia_prazos"]
            ]
            continue

        publicacao["ia_avaliacoes"] = (
            avaliacao["candidatos"]
        )

        # Extrair a data do texto original,
        # sem depender de nova chamada Gemini.
        data_pericia = identificar_data_pericia(
            publicacao["conteudo_original"],
            publicacao["data_disponibilizacao"],
        )

        if data_pericia is not None:
            publicacao["ia_data_evento"] = (
                data_pericia.isoformat()
            )

        estados = []

        for candidato in avaliacao["candidatos"]:
            estado = candidato["estado"]

            if estado == "aguardando_data_evento":
                if (
                    candidato.get("evento_referencia") == "pericia"
                    and data_pericia is not None
                ):
                    mensagem = (
                        "Perícia em "
                        f"{data_pericia.strftime('%d/%m/%Y')}"
                        " — aguardando validação do "
                        "calendário judicial"
                    )
                else:
                    mensagem = "Aguardando data da perícia"

            else:
                mensagem = ESTADOS_AVALIACAO.get(
                    estado,
                    "Aguardando avaliação",
                )

            estados.append(mensagem)

        publicacao["ia_estados_candidatos"] = estados


@publicadosHoje_bp.route("/PublicadosHoje")
@login_obrigatorio
def publicadosHoje():

    usuario_id = session["usuario_id"]

    dia = data_selecionada()

    # ==========================================
    # CONSULTAR PUBLICAÇÕES
    # ==========================================

    publicacoes = consultar_publicacoes(
        usuario_id,
        dia=dia,
    )

    # ==========================================
    # ANÁLISE E AVALIAÇÃO AUTOMÁTICA
    # ==========================================

    adicionar_analises_ia(
        publicacoes,
        usuario_id,
    )

    # ==========================================
    # CORES DOS CARTÕES
    # ==========================================

    hoje = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).date()

    cores = configuracao_cores(
        usuario_id
    )

    for publicacao in publicacoes:

        vencimento = publicacao[
            "data_vencimento"
        ]

        if publicacao["status"] == "concluido":

            publicacao["cor"] = "#E7E5E5"

        else:

            publicacao["cor"] = definir_cor(
                vencimento,
                cores,
                hoje,
            )

    # ==========================================
    # RENDERIZAR PÁGINA
    # ==========================================

    return render_template(
        "publicadosHoje.html",

        publicacoes=publicacoes,

        data_atual=dia,

        data_anterior=(
            dia - timedelta(days=1)
        ).isoformat(),

        data_proxima=(
            dia + timedelta(days=1)
        ).isoformat(),

        data_formatada=(
            f"{dia.day} de "
            f"{MESES[dia.month]} "
            f"{dia.year}"
        ),
    )


# ==========================================
# IMPRIMIR PUBLICAÇÕES SELECIONADAS
# ==========================================

@publicadosHoje_bp.route(
    "/PublicadosHoje/imprimir",
    methods=["POST"],
)
@login_obrigatorio
def imprimir_publicacoes():

    usuario_id = session["usuario_id"]

    try:
        dia = date.fromisoformat(
            request.form.get(
                "data",
                datetime.now(
                    ZoneInfo("America/Sao_Paulo")
                ).date().isoformat(),
            )
        )

    except ValueError:
        abort(
            400,
            description="Data inválida.",
        )

    modo = request.form.get("modo")

    if modo == "todos":

        publicacoes = consultar_publicacoes(
            usuario_id,
            dia=dia,
        )

    elif modo == "selecionados":

        ids = request.form.getlist(
            "publicacoes"
        )

        try:
            ids = [
                int(identificador)
                for identificador in ids
            ]

        except ValueError:
            abort(400)

        if not ids:

            return redirect(
                url_for(
                    "publicadosHoje.publicadosHoje",
                    data=dia.isoformat(),
                )
            )

        publicacoes = consultar_publicacoes(
            usuario_id,
            dia=dia,
            ids=ids,
        )

    else:
        abort(400)

    return render_template(
        "publicacoes_impressao.html",
        publicacoes=publicacoes,
    )


# ==========================================
# IMPRIMIR UMA PUBLICAÇÃO
# ==========================================

@publicadosHoje_bp.route(
    "/PublicadosHoje/imprimir/<int:publicacao_id>",
)
@login_obrigatorio
def imprimir_uma_publicacao(publicacao_id):

    publicacoes = consultar_publicacoes(
        session["usuario_id"],
        ids=[publicacao_id],
    )

    if not publicacoes:
        abort(404)

    return render_template(
        "publicacoes_impressao.html",
        publicacoes=publicacoes,
    )
