"""Leitura das análises concluídas da IA para apresentações do calendário.

Não cria prazos e não chama Gemini. Só usa análise com hash de conteúdo
compatível com a publicação atual e versão de analisador conhecida.
"""
from hashlib import sha256
from database import Session
from model.analise_ia import AnaliseIA
from model.publicacao import Publicacao
from model.processo import Processo
from service.processamento_ia_service import VERSAO_ANALISADOR


def resumos_ia_para_publicacoes(usuario_id, publicacao_ids):
    """{id_publicacao: resumo} com isolamento por usuário e sem dados pessoais novos."""
    ids = sorted({int(x) for x in publicacao_ids if x is not None})
    if not ids:
        return {}
    with Session() as db:
        linhas = (
            db.query(
                Publicacao.id,
                Publicacao.conteudo_original,
                AnaliseIA.resultado_json,
                AnaliseIA.hash_conteudo,
            )
            .join(Processo, Publicacao.processo_id == Processo.id)
            .join(AnaliseIA, AnaliseIA.publicacao_id == Publicacao.id)
            .filter(
                Processo.usuario_id == usuario_id,
                Publicacao.id.in_(ids),
                AnaliseIA.estado == "concluida",
                AnaliseIA.versao_analisador == VERSAO_ANALISADOR,
            )
            .order_by(AnaliseIA.id.desc())
            .all()
        )

    saida = {}
    for publicacao_id, texto, json_resultado, hash_salvo in linhas:
        if publicacao_id in saida or not texto:
            continue
        hash_atual = sha256(texto.encode("utf-8")).hexdigest()
        if hash_atual != hash_salvo:
            continue
        if not isinstance(json_resultado, dict):
            continue
        prazos = json_resultado.get("prazos")
        if not isinstance(prazos, list):
            continue
        atividades = []
        for prazo in prazos:
            if not isinstance(prazo, dict):
                continue
            atividade = prazo.get("atividade")
            if isinstance(atividade, str) and atividade.strip():
                atividades.append(atividade.strip()[:100])
        saida[publicacao_id] = {
            "quantidade_candidatos": len(prazos),
            "atividades": atividades[:3],
        }
    return saida


def descricao_ia_triagem(resumo):
    """Texto informativo, jamais data judicial ou obrigação confirmada."""
    if not resumo:
        return "Publicação para análise"
    quantidade = resumo["quantidade_candidatos"]
    if quantidade == 0:
        return "IA: sem novo prazo identificado — conferir"
    return f"IA: {quantidade} possível(is) prazo(s) — conferir"
