
import re


def identificar_prazo(texto):
    if not texto:
        return {"identificado": False}

    texto = re.sub(r"\s+", " ", texto.lower())

    padroes = [
        r"\bprazo\s+de\s+(\d+)(?:\s*\([^)]+\))?\s+dias?\s+(úteis|corridos)\b",

        r"\bno\s+prazo\s+de\s+(\d+)(?:\s*\([^)]+\))?\s+dias?\s+(úteis|corridos)\b",

        r"\bem\s+(\d+)(?:\s*\([^)]+\))?\s+dias?\s+(úteis|corridos)\b",

        r"\b(\d+)(?:\s*\([^)]+\))?\s+dias?\s+(úteis|corridos)\s+para\b"
    ]

    for padrao in padroes:
        resultado = re.search(padrao, texto)

        if resultado:
            return {
                "identificado": True,
                "dias": int(resultado.group(1)),
                "tipo_contagem": resultado.group(2),
                "origem": "djen",
                "trecho_identificado": resultado.group(0)
            }

    return {
        "identificado": False
    }
