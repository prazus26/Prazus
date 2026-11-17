"""Extracao deterministica e conservadora dos dados do processo no DJEN.

Nao utiliza Gemini, nao estima datas judiciais e nao altera edicoes humanas.
"""
import re
import unicodedata
from html import unescape


def _limpar(texto):
    texto = unescape(str(texto or ""))
    texto = re.sub(r"<[^>]+>", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _sem_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto)
                   if not unicodedata.combining(c)).casefold()


def extrair_dados_processo(texto, nome_classe=None, tipo_documento=None,
                           nome_advogado=None):
    """Campos identificados pelo texto; None representa informacao nao comprovada.

    O cliente e identificado somente se o advogado da publicacao estiver
    explicitamente associado a AUTOR ou REU e o respectivo polo estiver no texto.
    """
    texto = _limpar(texto)
    norm = _sem_acentos(texto)
    dados = {"cliente": None, "unidade_judicial": None,
             "classe": None, "assunto": None, "tipo_documento": None}

    unidade = re.search(
        r"\b(\d{1,2}[ªaºo]\s+Vara\s+Gabinete\s+JEF\s+de\s+"
        r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]{1,90}?)(?=\s+Avenida\b|\s+Rua\b|\s+Praça\b|\s+PROCEDIMENTO\b|$)",
        texto, re.IGNORECASE)
    if unidade:
        dados["unidade_judicial"] = unidade.group(1).strip()

    classe = re.search(
        r"\b([A-ZÀ-Ÿ][A-ZÀ-Ÿ\s/-]{5,100}?)\s*\(\d{2,5}\)\s*"
        r"(?:N[º°o]\.?|NÚMERO)\s*[0-9]{5,7}[-.]",
        texto)
    if classe:
        dados["classe"] = classe.group(1).strip()
    elif nome_classe:
        dados["classe"] = _limpar(nome_classe)

    # tipoDocumento e classe processual sao conceitos diferentes.
    if tipo_documento:
        dados["tipo_documento"] = _limpar(tipo_documento)
    elif "ato ordinatorio" in norm or "a t o o r d i n a t o r i o" in norm:
        dados["tipo_documento"] = "Ato ordinatório"

    autor = re.search(r"\bAUTOR(?:A)?\s*:\s*(.*?)\s+ADVOGADO\s+do\s*\(a\)\s*AUTOR", texto, re.IGNORECASE)
    reu = re.search(r"\bR[EÉ]U\s*:\s*(.*?)(?=\s+(?:ADVOGADO\s+do\s*\(a\)\s*R[EÉ]U|A\s*T\s*O\s*O\s*R\s*D\s*I\s*N|Nos termos|$))", texto, re.IGNORECASE)
    # A legitimidade e comprovada pelo papel explicito do advogado no documento.
    adv_autor = re.search(r"\bADVOGADO\s+do\s*\(a\)\s*AUTOR\s*:", texto, re.IGNORECASE)
    adv_reu = re.search(r"\bADVOGADO\s+do\s*\(a\)\s*R[EÉ]U\s*:", texto, re.IGNORECASE)
    # Evitar escolher um polo se ha advogados de ambos os lados.
    if adv_autor and not adv_reu and autor:
        dados["cliente"] = autor.group(1).strip(" -.,")[:150]
    elif adv_reu and not adv_autor and reu:
        dados["cliente"] = reu.group(1).strip(" -.,")[:150]
    # Nao inventar assunto especifico com base na classe.
    return dados


def completar_detalhes(detalhes):
    """Complementa exibicao de registros antigos sem atualizar tabelas.

    Preserva valores humanos; reclassifica pares de importacao historica
    (nomeClasse -> assunto; tipoDocumento -> classe) na visualizacao.
    """
    extraidos = extrair_dados_processo(detalhes.get("conteudo_original"))
    detalhes["cliente"] = detalhes.get("cliente") or extraidos["cliente"]
    detalhes["unidade_judicial"] = extraidos["unidade_judicial"]
    classe_atual = detalhes.get("classe")
    assunto_atual = detalhes.get("assunto")
    tipo_extraido = extraidos["tipo_documento"]
    classe_extraida = extraidos["classe"]
    if classe_extraida and classe_atual and assunto_atual:
        # Corrige legado SOMENTE quando as duas metades coincidem com os
        # respectivos campos trocados; do contrario preserva edicoes.
        if (_sem_acentos(_limpar(assunto_atual)) == _sem_acentos(_limpar(classe_extraida))
                and _sem_acentos(_limpar(classe_atual)) in
                ("ato ordinatorio", "intimacao", "despacho", "decisao", "sentenca")):
            detalhes["classe"] = classe_extraida
            detalhes["assunto"] = None
            detalhes["tipo_documento"] = classe_atual
    if not detalhes.get("classe"):
        detalhes["classe"] = classe_extraida
    if not detalhes.get("tipo_documento"):
        detalhes["tipo_documento"] = tipo_extraido
    return detalhes
