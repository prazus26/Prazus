
import re
from html import unescape
from html.parser import HTMLParser


class ExtratorTexto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes = []
        self.ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignorar += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.ignorar:
            self.ignorar -= 1

    def handle_data(self, data):
        if not self.ignorar:
            self.partes.append(data)


def limpar_texto(texto):
    if not texto:
        return ""

    texto = unescape(str(texto))

    if re.search(r"<[a-z][^>]*>", texto, re.I):
        extrator = ExtratorTexto()
        extrator.feed(texto)
        texto = " ".join(extrator.partes)

    return re.sub(r"\s+", " ", texto).strip().lower()


def identificar_prazo(texto):
    texto = limpar_texto(texto)

    if not texto:
        return {"identificado": False}

    numero = r"(\d{1,3})"
    por_extenso = r"(?:\s*\([a-zà-ÿ\s-]+\))?"
    dias = rf"{numero}{por_extenso}\s+dias?"

    padroes = [
        rf"\b(?:no\s+)?prazo\s+de\s+{dias}\s+(úteis|corridos)\b",
        rf"\bprazo\s+legal\s+de\s+{dias}\s+(úteis|corridos)\b",
        rf"\bem\s+até\s+{dias}\s+(úteis|corridos)\b",
        rf"\b(?:dentro\s+de|em)\s+{dias}\s+(úteis|corridos)\b",
        rf"\b{dias}\s+(úteis|corridos)\s+para\b",
        rf"\b(?:concedido|fixado)\s+o\s+prazo\s+de\s+{dias}\s+(úteis|corridos)\b"
    ]

    for padrao in padroes:
        resultado = re.search(padrao, texto)

        if resultado:
            quantidade = int(resultado.group(1))
            if quantidade < 1:
                continue
            # Regex detecta apenas uma menção: não comprova o destinatário,
            # a obrigação ou a regra processual aplicável.
            return {
                "identificado": False,
                "revisao_necessaria": True,
                "dias_sugeridos": quantidade,
                "tipo_contagem_sugerida": (
                    "uteis" if resultado.group(2) == "úteis" else "corridos"
                ),
                "trecho_identificado": resultado.group(0)
            }

    # Reconhece também prazos que não informam
    # expressamente se os dias são úteis ou corridos.
    # Esses casos exigem revisão e não recebem
    # automaticamente uma contagem oficial.
    padrao_sem_contagem = (
        rf"\b(?:no\s+)?prazo\s+de\s+{dias}\b"
    )

    resultado = re.search(padrao_sem_contagem, texto)

    if resultado and int(resultado.group(1)) > 0:
        return {
            "identificado": False,
            "revisao_necessaria": True,
            "dias_sugeridos": int(resultado.group(1)),
            "trecho_identificado": resultado.group(0)
        }

    return {"identificado": False}
