"""Valida evidências mínimas. Não certifica prazos nem calcula vencimento."""


def validar_resultado(texto, analise):
    if hasattr(analise, "model_dump"):
        analise = analise.model_dump(mode="json")
    if not isinstance(analise, dict):
        raise ValueError("Análise não é objeto JSON.")
    if not isinstance(analise.get("prazos"), list):
        raise ValueError("Campo prazos ausente ou inválido.")
    for indice, prazo in enumerate(analise["prazos"], start=1):
        if not isinstance(prazo, dict):
            raise ValueError(f"Prazo {indice}: objeto inválido.")
        evidencia = prazo.get("evidencia")
        if not isinstance(evidencia, str) or not evidencia.strip() or evidencia.strip() not in texto:
            raise ValueError(f"Prazo {indice}: trecho literal não encontrado no documento.")
        dias = prazo.get("dias")
        if dias is not None and (type(dias) is not int or not 1 <= dias <= 3650):
            raise ValueError(f"Prazo {indice}: dias inválidos.")
        if prazo.get("contagem") not in ("uteis", "corridos", None):
            raise ValueError(f"Prazo {indice}: contagem inválida.")
    if not isinstance(analise.get("participantes", []), list):
        raise ValueError("Campo participantes inválido.")
    for parte in analise.get("participantes", []):
        evidencia = parte.get("evidencia") if isinstance(parte, dict) else None
        if evidencia and evidencia not in texto:
            raise ValueError("Participante com evidência inexistente no documento.")
    return analise
